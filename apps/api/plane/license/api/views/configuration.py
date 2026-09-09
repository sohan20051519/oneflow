# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

# Python imports
from smtplib import (
    SMTPAuthenticationError,
    SMTPConnectError,
    SMTPRecipientsRefused,
    SMTPSenderRefused,
    SMTPServerDisconnected,
)

# Django imports
from django.core.mail import BadHeaderError, EmailMultiAlternatives, get_connection
from django.db.models import Q, Case, When, Value

# Third party imports
from rest_framework import status
from rest_framework.response import Response

# Module imports
from .base import BaseAPIView
from plane.license.api.permissions import InstanceAdminPermission
from plane.license.models import InstanceConfiguration
from plane.license.api.serializers import InstanceConfigurationSerializer
from plane.license.utils.encryption import encrypt_data
from plane.utils.cache import cache_response, invalidate_cache
from plane.license.utils.instance_value import get_email_configuration


class InstanceConfigurationEndpoint(BaseAPIView):
    permission_classes = [InstanceAdminPermission]

    @cache_response(60 * 60 * 2, user=False)
    def get(self, request):
        instance_configurations = InstanceConfiguration.objects.all()
        serializer = InstanceConfigurationSerializer(instance_configurations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @invalidate_cache(path="/api/instances/configurations/", user=False)
    @invalidate_cache(path="/api/instances/", user=False)
    def patch(self, request):
        existing_configurations = {c.key: c for c in InstanceConfiguration.objects.filter(key__in=request.data.keys())}

        bulk_update = []
        bulk_create = []
        result_configurations = []

        for key, raw_value in request.data.items():
            value = "" if raw_value is None else str(raw_value).strip()
            is_secret = any(term in key.lower() for term in ["secret", "token", "password"])

            if key in existing_configurations:
                configuration = existing_configurations[key]
                if configuration.is_encrypted:
                    configuration.value = encrypt_data(value)
                else:
                    configuration.value = value
                bulk_update.append(configuration)
                result_configurations.append(configuration)
            else:
                new_conf = InstanceConfiguration(
                    key=key,
                    value=encrypt_data(value) if is_secret else value,
                    category="INFISICAL" if "INFISICAL" in key else "CUSTOM",
                    is_encrypted=is_secret,
                )
                bulk_create.append(new_conf)
                result_configurations.append(new_conf)

        if bulk_update:
            InstanceConfiguration.objects.bulk_update(bulk_update, ["value"], batch_size=100)
        if bulk_create:
            InstanceConfiguration.objects.bulk_create(bulk_create, batch_size=100)

        serializer = InstanceConfigurationSerializer(result_configurations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DisableEmailFeatureEndpoint(BaseAPIView):
    permission_classes = [InstanceAdminPermission]

    @invalidate_cache(path="/api/instances/", user=False)
    def delete(self, request):
        try:
            InstanceConfiguration.objects.filter(
                Q(
                    key__in=[
                        "EMAIL_HOST",
                        "EMAIL_HOST_USER",
                        "EMAIL_HOST_PASSWORD",
                        "ENABLE_SMTP",
                        "EMAIL_PORT",
                        "EMAIL_FROM",
                    ]
                )
            ).update(value=Case(When(key="ENABLE_SMTP", then=Value("0")), default=Value("")))
            return Response(status=status.HTTP_200_OK)
        except Exception:
            return Response(
                {"error": "Failed to disable email configuration"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class EmailCredentialCheckEndpoint(BaseAPIView):
    def post(self, request):
        receiver_email = request.data.get("receiver_email", False)
        if not receiver_email:
            return Response(
                {"error": "Receiver email is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        (
            EMAIL_HOST,
            EMAIL_HOST_USER,
            EMAIL_HOST_PASSWORD,
            EMAIL_PORT,
            EMAIL_USE_TLS,
            EMAIL_USE_SSL,
            EMAIL_FROM,
        ) = get_email_configuration()

        # Configure all the connections
        connection = get_connection(
            host=EMAIL_HOST,
            port=int(EMAIL_PORT),
            username=EMAIL_HOST_USER,
            password=EMAIL_HOST_PASSWORD,
            use_tls=EMAIL_USE_TLS == "1",
            use_ssl=EMAIL_USE_SSL == "1",
        )
        # Prepare email details
        subject = "Email Notification from one flow"
        message = "This is a sample email notification sent from one flow application."
        # Send the email
        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=EMAIL_FROM,
                to=[receiver_email],
                connection=connection,
            )
            msg.send(fail_silently=False)
            return Response({"message": "Email successfully sent."}, status=status.HTTP_200_OK)
        except BadHeaderError:
            return Response({"error": "Invalid email header."}, status=status.HTTP_400_BAD_REQUEST)
        except SMTPAuthenticationError:
            return Response(
                {"error": "Invalid credentials provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except SMTPConnectError:
            return Response(
                {"error": "Could not connect with the SMTP server."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except SMTPSenderRefused:
            return Response(
                {"error": "From address is invalid."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except SMTPServerDisconnected:
            return Response(
                {"error": "SMTP server disconnected unexpectedly."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except SMTPRecipientsRefused:
            return Response(
                {"error": "All recipient addresses were refused."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except TimeoutError:
            return Response(
                {"error": "Timeout error while trying to connect to the SMTP server."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ConnectionError:
            return Response(
                {"error": "Network connection error. Please check your internet connection."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return Response(
                {"error": "Could not send email. Please check your configuration"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class InfisicalConnectionCheckEndpoint(BaseAPIView):
    permission_classes = [InstanceAdminPermission]

    def post(self, request):
        import urllib.request
        import json

        host = (request.data.get("host") or "https://config.cubeone.in").rstrip("/")
        project_id = request.data.get("project_id") or "f10e0d79-aa86-4c35-862a-e44ed0f482e3"
        environment = request.data.get("environment") or "prod"
        client_id = request.data.get("client_id")
        client_secret = request.data.get("client_secret")
        token = request.data.get("token")

        try:
            req = urllib.request.Request(f"{host}/api/v1/health", headers={"User-Agent": "OneFlow/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                pass
        except Exception as e:
            return Response(
                {"error": f"Cannot connect to Infisical host at {host}: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if client_id and client_secret:
            try:
                login_url = f"{host}/api/v1/auth/universal-auth/login"
                payload = json.dumps({"clientId": client_id, "clientSecret": client_secret}).encode("utf-8")
                req = urllib.request.Request(login_url, data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    token = data.get("accessToken")
            except Exception as e:
                return Response(
                    {"error": f"Infisical Universal Auth failed: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(
            {
                "status": "success",
                "message": f"Successfully connected to Self-Hosted Infisical ({host}) targeting Production ({environment}).",
            },
            status=status.HTTP_200_OK,
        )
