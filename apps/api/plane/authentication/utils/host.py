# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

# Django imports
from django.conf import settings
from django.http import HttpRequest

# Third party imports
from rest_framework.request import Request

# Module imports
from plane.utils.ip_address import get_client_ip


def base_host(
    request: Request | HttpRequest,
    is_admin: bool = False,
    is_space: bool = False,
    is_app: bool = False,
) -> str:
    """Utility function to return host / origin from the request"""
    # Prefer actual request origin if available
    request_origin = None
    if request:
        try:
            scheme = "https" if request.is_secure() else "http"
            host = request.get_host()
            if host:
                request_origin = f"{scheme}://{host}"
        except Exception:
            request_origin = None

    base_origin = request_origin or settings.WEB_URL or settings.APP_BASE_URL or "http://localhost"

    # Admin redirection
    if is_admin:
        admin_base_path = getattr(settings, "ADMIN_BASE_PATH", None)
        if not isinstance(admin_base_path, str):
            admin_base_path = "/god-mode/"
        if not admin_base_path.startswith("/"):
            admin_base_path = "/" + admin_base_path
        if not admin_base_path.endswith("/"):
            admin_base_path += "/"

        admin_base_url = settings.ADMIN_BASE_URL
        if admin_base_url and not any(dev_port in admin_base_url for dev_port in [":3001", ":8000"]):
            return admin_base_url + admin_base_path
        else:
            return base_origin + admin_base_path

    # Space redirection
    if is_space:
        space_base_path = getattr(settings, "SPACE_BASE_PATH", None)
        if not isinstance(space_base_path, str):
            space_base_path = "/spaces/"
        if not space_base_path.startswith("/"):
            space_base_path = "/" + space_base_path
        if not space_base_path.endswith("/"):
            space_base_path += "/"

        space_base_url = settings.SPACE_BASE_URL
        if space_base_url and not any(dev_port in space_base_url for dev_port in [":3002", ":8000"]):
            return space_base_url + space_base_path
        else:
            return base_origin + space_base_path

    # App Redirection
    if is_app:
        app_base_url = settings.APP_BASE_URL
        if app_base_url and not any(dev_port in app_base_url for dev_port in [":3000", ":8000"]):
            return app_base_url
        else:
            return base_origin

    return base_origin


def user_ip(request: Request | HttpRequest) -> str:
    return get_client_ip(request=request)
