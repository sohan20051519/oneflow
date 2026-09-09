# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

# Python imports
import os
import requests
import logging
from datetime import datetime, timedelta
from urllib.parse import urlencode, urlparse
import pytz
import jwt
from jwt import PyJWKClient

from django.core.cache import cache
from django.utils import timezone

# Module imports
from plane.authentication.adapter.oauth import OauthAdapter
from plane.license.utils.instance_value import get_configuration_value
from plane.authentication.utils.host import base_host
from plane.authentication.adapter.error import (
    AUTHENTICATION_ERROR_CODES,
    AuthenticationException,
)

logger = logging.getLogger("plane.authentication")


def get_discovery_doc(discovery_url):
    if not discovery_url:
        return None
    doc = cache.get(f"oidc_discovery_doc_{discovery_url}")
    if doc:
        return doc
    try:
        response = requests.get(discovery_url, timeout=10)
        response.raise_for_status()
        doc = response.json()
        cache.set(f"oidc_discovery_doc_{discovery_url}", doc, 86400)
        return doc
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch OIDC discovery doc from {discovery_url}: {e}")
        return None


class OIDCOAuthProvider(OauthAdapter):
    provider = "oidc"

    def authentication_error_code(self):
        return "OIDC_PROVIDER_ERROR"

    def __init__(self, request, code=None, state=None, callback=None):
        (
            IS_OIDC_ENABLED,
            OIDC_CLIENT_ID,
            OIDC_CLIENT_SECRET,
            OIDC_AUTHORIZE_URL,
            OIDC_TOKEN_URL,
            OIDC_USERINFO_URL,
            OIDC_LOGOUT_URL,
            KEYCLOAK_ISSUER_URL,
            KEYCLOAK_DISCOVERY_URL,
            KEYCLOAK_CLIENT_ID,
            KEYCLOAK_CLIENT_SECRET,
            KEYCLOAK_SCOPES,
        ) = get_configuration_value(
            [
                {
                    "key": "IS_OIDC_ENABLED",
                    "default": os.environ.get("IS_OIDC_ENABLED", "1"),
                },
                {
                    "key": "OIDC_CLIENT_ID",
                    "default": os.environ.get("OIDC_CLIENT_ID"),
                },
                {
                    "key": "OIDC_CLIENT_SECRET",
                    "default": os.environ.get("OIDC_CLIENT_SECRET"),
                },
                {
                    "key": "OIDC_AUTHORIZE_URL",
                    "default": os.environ.get("OIDC_AUTHORIZE_URL"),
                },
                {
                    "key": "OIDC_TOKEN_URL",
                    "default": os.environ.get("OIDC_TOKEN_URL"),
                },
                {
                    "key": "OIDC_USERINFO_URL",
                    "default": os.environ.get("OIDC_USERINFO_URL"),
                },
                {
                    "key": "OIDC_LOGOUT_URL",
                    "default": os.environ.get("OIDC_LOGOUT_URL"),
                },
                {
                    "key": "KEYCLOAK_ISSUER_URL",
                    "default": os.environ.get("KEYCLOAK_ISSUER_URL"),
                },
                {
                    "key": "KEYCLOAK_DISCOVERY_URL",
                    "default": os.environ.get("KEYCLOAK_DISCOVERY_URL"),
                },
                {
                    "key": "KEYCLOAK_CLIENT_ID",
                    "default": os.environ.get("KEYCLOAK_CLIENT_ID"),
                },
                {
                    "key": "KEYCLOAK_CLIENT_SECRET",
                    "default": os.environ.get("KEYCLOAK_CLIENT_SECRET"),
                },
                {
                    "key": "KEYCLOAK_SCOPES",
                    "default": os.environ.get("KEYCLOAK_SCOPES", "openid profile email"),
                },
            ]
        )

        # Check if explicitly disabled
        if str(IS_OIDC_ENABLED).strip() in ("0", "false", "False"):
            raise AuthenticationException(
                error_code=AUTHENTICATION_ERROR_CODES["OIDC_NOT_CONFIGURED"],
                error_message="OIDC_NOT_CONFIGURED",
            )

        client_id = (
            OIDC_CLIENT_ID
            or KEYCLOAK_CLIENT_ID
            or os.environ.get("OAUTH2_PROXY_CLIENT_ID")
            or ""
        ).strip()

        client_secret = (
            OIDC_CLIENT_SECRET
            or KEYCLOAK_CLIENT_SECRET
            or os.environ.get("OAUTH2_PROXY_CLIENT_SECRET")
            or ""
        ).strip()

        # Derive issuer_url
        issuer_url = (KEYCLOAK_ISSUER_URL or os.environ.get("OAUTH2_PROXY_OIDC_ISSUER_URL") or "").strip()
        if not issuer_url and OIDC_AUTHORIZE_URL:
            if "/protocol/" in OIDC_AUTHORIZE_URL:
                issuer_url = OIDC_AUTHORIZE_URL.split("/protocol/")[0]
            else:
                parsed = urlparse(OIDC_AUTHORIZE_URL)
                issuer_url = f"{parsed.scheme}://{parsed.netloc}"

        # Derive discovery_url
        discovery_url = (KEYCLOAK_DISCOVERY_URL or "").strip()
        if not discovery_url and issuer_url:
            discovery_url = f"{issuer_url.rstrip('/')}/.well-known/openid-configuration"

        discovery_doc = get_discovery_doc(discovery_url) if discovery_url else None

        authorization_endpoint = (
            OIDC_AUTHORIZE_URL
            or (discovery_doc.get("authorization_endpoint") if discovery_doc else None)
        )
        token_url = (
            OIDC_TOKEN_URL
            or (discovery_doc.get("token_endpoint") if discovery_doc else None)
        )
        userinfo_url = (
            OIDC_USERINFO_URL
            or (discovery_doc.get("userinfo_endpoint") if discovery_doc else None)
        )

        if discovery_doc:
            self.jwks_uri = discovery_doc.get("jwks_uri")
            self.issuer_url = discovery_doc.get("issuer") or issuer_url
        else:
            self.jwks_uri = f"{issuer_url.rstrip('/')}/protocol/openid-connect/certs" if issuer_url else None
            self.issuer_url = issuer_url

        self.scope = KEYCLOAK_SCOPES or "openid profile email"

        if not (client_id and client_secret and authorization_endpoint and token_url):
            logger.warning(
                f"OIDC not fully configured: client_id={bool(client_id)}, client_secret={bool(client_secret)}, "
                f"auth_endpoint={bool(authorization_endpoint)}, token_url={bool(token_url)}"
            )
            raise AuthenticationException(
                error_code=AUTHENTICATION_ERROR_CODES["OIDC_NOT_CONFIGURED"],
                error_message="OIDC_NOT_CONFIGURED",
            )

        # Standard callback URI
        origin = base_host(request=request, is_app=True).rstrip("/")
        if origin.startswith("http://") and "localhost" not in origin and "127.0.0.1" not in origin:
            origin = origin.replace("http://", "https://", 1)

        is_space = "/spaces/" in getattr(request, "path", "") or "/space" in getattr(request, "path", "")
        if is_space:
            redirect_uri = f"{origin}/auth/spaces/oidc/callback/"
        else:
            redirect_uri = f"{origin}/auth/oidc/callback/"

        url_params = {
            "client_id": client_id,
            "scope": self.scope,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "state": state,
        }
        auth_url = f"{authorization_endpoint}?{urlencode(url_params)}"

        super().__init__(
            request,
            self.provider,
            client_id,
            self.scope,
            redirect_uri,
            auth_url,
            token_url,
            userinfo_url,
            client_secret,
            code,
            callback=callback,
        )

    def set_token_data(self):
        data = {
            "code": self.code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }
        token_response = self.get_user_token(data=data)

        id_token = token_response.get("id_token")

        if id_token and self.jwks_uri:
            try:
                jwks_client = PyJWKClient(self.jwks_uri, timeout=10)
                signing_key = jwks_client.get_signing_key_from_jwt(id_token)

                unverified_header = jwt.get_unverified_header(id_token)
                alg = unverified_header.get("alg", "RS256")

                # Verify token signature and expiration
                jwt.decode(
                    id_token,
                    signing_key.key,
                    algorithms=[alg, "RS256"],
                    options={
                        "verify_signature": True,
                        "verify_exp": True,
                        "verify_aud": False,
                        "verify_iss": False,
                    },
                )
            except Exception as e:
                self.logger.warning(f"OIDC Token Validation Failed: {str(e)}")
                raise AuthenticationException(
                    error_code=AUTHENTICATION_ERROR_CODES["OIDC_PROVIDER_ERROR"],
                    error_message=f"INVALID_ID_TOKEN: {str(e)}",
                )

        super().set_token_data(
            {
                "access_token": token_response.get("access_token"),
                "refresh_token": token_response.get("refresh_token", None),
                "access_token_expired_at": (
                    timezone.now() + timedelta(seconds=int(token_response.get("expires_in")))
                    if token_response.get("expires_in")
                    else None
                ),
                "refresh_token_expired_at": (
                    timezone.now() + timedelta(seconds=int(token_response.get("refresh_expires_in")))
                    if token_response.get("refresh_expires_in")
                    else None
                ),
                "id_token": id_token or "",
            }
        )

    def set_user_data(self):
        try:
            user_info_response = self.get_user_response()
            if not isinstance(user_info_response, dict):
                user_info_response = {}
        except Exception as e:
            self.logger.warning(f"Failed to fetch userinfo response: {e}")
            user_info_response = {}

        # Fall back to id_token claims if userinfo endpoint didn't provide email
        id_token_claims = {}
        if hasattr(self, "token_data") and self.token_data and self.token_data.get("id_token"):
            try:
                id_token_claims = jwt.decode(
                    self.token_data.get("id_token"),
                    options={"verify_signature": False},
                )
            except Exception:
                id_token_claims = {}

        email = (
            user_info_response.get("email")
            or id_token_claims.get("email")
            or user_info_response.get("preferred_username")
            or id_token_claims.get("preferred_username")
        )

        if not email:
            raise AuthenticationException(
                error_code=AUTHENTICATION_ERROR_CODES["OAUTH_PROVIDER_UNVERIFIED_EMAIL"],
                error_message="OAUTH_PROVIDER_UNVERIFIED_EMAIL",
            )

        first_name = (
            user_info_response.get("given_name")
            or id_token_claims.get("given_name")
            or user_info_response.get("name")
            or id_token_claims.get("name")
            or email.split("@")[0]
        )
        last_name = (
            user_info_response.get("family_name")
            or id_token_claims.get("family_name")
            or ""
        )
        provider_id = (
            user_info_response.get("sub")
            or id_token_claims.get("sub")
            or email
        )

        user_data = {
            "email": email,
            "user": {
                "avatar": user_info_response.get("picture") or id_token_claims.get("picture"),
                "first_name": first_name,
                "last_name": last_name,
                "provider_id": provider_id,
                "is_password_autoset": True,
            },
        }
        super().set_user_data(user_data)
