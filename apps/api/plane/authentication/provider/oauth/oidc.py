# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

# Python imports
import os
import requests
from datetime import datetime, timedelta
from urllib.parse import urlencode
import pytz
import jwt
from jwt import PyJWKClient

from django.core.cache import cache
from django.utils import timezone

# Module imports
from plane.authentication.adapter.oauth import OauthAdapter
from plane.license.utils.instance_value import get_configuration_value
from plane.authentication.adapter.error import (
    AUTHENTICATION_ERROR_CODES,
    AuthenticationException,
)


def get_discovery_doc(discovery_url):
    doc = cache.get(f"oidc_discovery_doc_{discovery_url}")
    if doc:
        return doc
    try:
        response = requests.get(discovery_url, timeout=10)
        response.raise_for_status()
        doc = response.json()
        cache.set(f"oidc_discovery_doc_{discovery_url}", doc, 86400)
        return doc
    except requests.RequestException:
        raise AuthenticationException(
            error_code=AUTHENTICATION_ERROR_CODES["OIDC_PROVIDER_ERROR"],
            error_message="FAILED_TO_FETCH_OIDC_DISCOVERY",
        )


class OIDCOAuthProvider(OauthAdapter):
    provider = "oidc"

    def authentication_error_code(self):
        return "OIDC_PROVIDER_ERROR"

    def __init__(self, request, code=None, state=None, callback=None):
        (
            KEYCLOAK_ISSUER_URL,
            KEYCLOAK_DISCOVERY_URL,
            KEYCLOAK_CLIENT_ID,
            KEYCLOAK_CLIENT_SECRET,
            KEYCLOAK_SCOPES,
        ) = get_configuration_value(
            [
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

        if not (KEYCLOAK_ISSUER_URL and KEYCLOAK_DISCOVERY_URL and KEYCLOAK_CLIENT_ID and KEYCLOAK_CLIENT_SECRET):
            # Fallback to older env names if standard Keycloak ones aren't provided
            KEYCLOAK_CLIENT_ID = os.environ.get("OAUTH2_PROXY_CLIENT_ID", KEYCLOAK_CLIENT_ID)
            KEYCLOAK_CLIENT_SECRET = os.environ.get("OAUTH2_PROXY_CLIENT_SECRET", KEYCLOAK_CLIENT_SECRET)
            KEYCLOAK_ISSUER_URL = os.environ.get("OAUTH2_PROXY_OIDC_ISSUER_URL", KEYCLOAK_ISSUER_URL)
            if KEYCLOAK_ISSUER_URL and not KEYCLOAK_DISCOVERY_URL:
                KEYCLOAK_DISCOVERY_URL = f"{KEYCLOAK_ISSUER_URL}/.well-known/openid-configuration"

        if not (KEYCLOAK_ISSUER_URL and KEYCLOAK_CLIENT_ID and KEYCLOAK_CLIENT_SECRET):
            raise AuthenticationException(
                error_code=AUTHENTICATION_ERROR_CODES["OIDC_NOT_CONFIGURED"],
                error_message="OIDC_NOT_CONFIGURED",
            )

        self.issuer_url = KEYCLOAK_ISSUER_URL
        client_id = KEYCLOAK_CLIENT_ID
        client_secret = KEYCLOAK_CLIENT_SECRET
        self.scope = KEYCLOAK_SCOPES
        
        discovery_doc = get_discovery_doc(KEYCLOAK_DISCOVERY_URL)
        self.jwks_uri = discovery_doc.get("jwks_uri")

        token_url = discovery_doc.get("token_endpoint")
        userinfo_url = discovery_doc.get("userinfo_endpoint")
        authorization_endpoint = discovery_doc.get("authorization_endpoint")

        # Frontend sends callback as /auth/oidc/callback/
        redirect_uri = f"""{"https" if request.is_secure() else "http"}://{request.get_host()}/auth/oidc/callback/"""
        
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
                
                # Validates signature, issuer, audience, and expiration
                jwt.decode(
                    id_token,
                    signing_key.key,
                    algorithms=["RS256"],
                    audience=self.client_id,
                    issuer=self.issuer_url,
                    options={
                        "verify_signature": True,
                        "verify_aud": True,
                        "verify_iss": True,
                        "verify_exp": True,
                    }
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
        user_info_response = self.get_user_response()
        
        email = user_info_response.get("email")
        if not email:
            raise AuthenticationException(
                error_code=AUTHENTICATION_ERROR_CODES["OAUTH_PROVIDER_UNVERIFIED_EMAIL"],
                error_message="OAUTH_PROVIDER_UNVERIFIED_EMAIL",
            )
            
        user_data = {
            "email": email,
            "user": {
                "avatar": user_info_response.get("picture"),
                "first_name": user_info_response.get("given_name", user_info_response.get("name", "")),
                "last_name": user_info_response.get("family_name", ""),
                "provider_id": user_info_response.get("sub"), # Use 'sub' as stable ID per instructions
                "is_password_autoset": True,
            },
        }
        super().set_user_data(user_data)
