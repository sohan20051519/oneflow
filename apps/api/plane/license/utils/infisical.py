# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import json
import logging
import os
import urllib.request
import urllib.error

from django.conf import settings
from plane.license.models import InstanceConfiguration
from plane.license.utils.encryption import encrypt_data, decrypt_data

logger = logging.getLogger("plane.license.infisical")

SENSITIVE_KEY_SUBSTRINGS = (
    "SECRET",
    "PASSWORD",
    "KEY",
    "TOKEN",
    "CREDENTIAL",
    "PRIVATE",
    "AUTH",
    "SALT",
)


def is_sensitive_key(key: str) -> bool:
    upper = key.upper()
    return any(sub in upper for sub in SENSITIVE_KEY_SUBSTRINGS)


def get_infisical_credentials():
    """Retrieve Infisical connection metadata from DB or environment."""
    configs = {
        item["key"]: (
            decrypt_data(item["value"]) if item["is_encrypted"] else item["value"]
        )
        for item in InstanceConfiguration.objects.filter(
            key__startswith="INFISICAL_"
        ).values("key", "value", "is_encrypted")
    }

    host = (
        configs.get("INFISICAL_HOST")
        or os.environ.get("INFISICAL_HOST")
        or "https://config.cubeone.in"
    ).rstrip("/")
    project_id = (
        configs.get("INFISICAL_PROJECT_ID")
        or os.environ.get("INFISICAL_PROJECT_ID")
        or "f10e0d79-aa86-4c35-862a-e44ed0f482e3"
    )
    environment = (
        configs.get("INFISICAL_ENV")
        or os.environ.get("INFISICAL_ENV")
        or "prod"
    )
    client_id = configs.get("INFISICAL_CLIENT_ID") or os.environ.get("INFISICAL_CLIENT_ID", "")
    client_secret = (
        configs.get("INFISICAL_CLIENT_SECRET")
        or os.environ.get("INFISICAL_CLIENT_SECRET", "")
    )
    token = configs.get("INFISICAL_TOKEN") or os.environ.get("INFISICAL_TOKEN", "")

    return {
        "host": host,
        "project_id": project_id,
        "environment": environment,
        "client_id": client_id,
        "client_secret": client_secret,
        "token": token,
    }


def authenticate_infisical(host: str, client_id: str, client_secret: str) -> str:
    """Acquire bearer token from Infisical Universal Auth."""
    if not (client_id and client_secret):
        return ""

    login_url = f"{host}/api/v1/auth/universal-auth/login"
    payload = json.dumps({"clientId": client_id, "clientSecret": client_secret}).encode("utf-8")
    req = urllib.request.Request(
        login_url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "OneFlow/1.0"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("accessToken", "")


def fetch_raw_secrets_from_infisical(
    host: str = None,
    project_id: str = None,
    environment: str = None,
    client_id: str = None,
    client_secret: str = None,
    token: str = None,
) -> dict:
    """Directly fetch secrets from Infisical without writing to any file."""
    creds = get_infisical_credentials()
    host = (host or creds["host"]).rstrip("/")
    project_id = project_id or creds["project_id"]
    environment = environment or creds["environment"]
    client_id = client_id or creds["client_id"]
    client_secret = client_secret or creds["client_secret"]
    token = token or creds["token"]

    auth_token = token
    if not auth_token and client_id and client_secret:
        auth_token = authenticate_infisical(host, client_id, client_secret)

    if not auth_token:
        logger.warning("No Infisical auth token or credentials available; skipping direct fetch.")
        return {}

    env_candidates = [environment]
    if environment in ("prod", "production"):
        env_candidates = ["prod", "production"]
    elif environment in ("staging", "stage"):
        env_candidates = ["staging", "stage"]

    secrets_dict = {}
    for candidate in env_candidates:
        url = f"{host}/api/v3/secrets/raw?workspaceId={project_id}&environment={candidate}&secretPath=/"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {auth_token}",
                "User-Agent": "OneFlow/1.0",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                raw_list = data.get("secrets", [])
                if raw_list:
                    for s in raw_list:
                        k = s.get("secretKey")
                        v = s.get("secretValue", "")
                        if k:
                            secrets_dict[k] = v
                    break
        except Exception as e:
            logger.warning(f"Error fetching from Infisical candidate '{candidate}': {e}")

    return secrets_dict


def sync_secrets_into_runtime(secrets: dict = None) -> int:
    """Fetch secrets directly from Infisical and apply into os.environ and InstanceConfiguration (0 file write)."""
    if secrets is None:
        secrets = fetch_raw_secrets_from_infisical()

    if not secrets:
        return 0

    applied_count = 0
    for key, value in secrets.items():
        if not key:
            continue

        # 1. Update in-memory runtime environment directly
        os.environ[key] = str(value)

        # 2. Upsert into InstanceConfiguration database model
        sensitive = is_sensitive_key(key)
        encrypted_val = encrypt_data(str(value)) if sensitive else str(value)

        obj, created = InstanceConfiguration.objects.get_or_create(
            key=key,
            defaults={
                "value": encrypted_val,
                "is_encrypted": sensitive,
                "category": "INFISICAL_SYNC",
            },
        )
        if not created:
            obj.value = encrypted_val
            obj.is_encrypted = sensitive
            obj.save(update_fields=["value", "is_encrypted"])

        applied_count += 1

    logger.info(f"Successfully synchronized {applied_count} secrets directly from Infisical into runtime.")
    return applied_count
