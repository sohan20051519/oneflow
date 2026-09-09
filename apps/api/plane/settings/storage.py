# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

# Python imports
import os
import uuid

# Third party imports
import boto3
from botocore.exceptions import ClientError
from urllib.parse import quote

# Module imports
from plane.utils.exception_logger import log_exception
from storages.backends.s3boto3 import S3Boto3Storage


class S3Storage(S3Boto3Storage):
    def url(self, name, parameters=None, expire=None, http_method=None):
        return name

    """S3 storage class to generate presigned URLs for S3 objects"""

    def _get_config_value(self, key, default=None):
        val = os.environ.get(key)
        if val and val.strip():
            return val.strip()
        try:
            from plane.license.models import InstanceConfiguration
            from plane.license.utils.encryption import decrypt_data
            item = InstanceConfiguration.objects.filter(key=key).first()
            if item and item.value:
                res = decrypt_data(item.value) if item.is_encrypted else item.value
                if res and res.strip():
                    return res.strip()
        except Exception:
            pass
        return default

    def __init__(self, request=None):
        # Get the AWS credentials and bucket name from environment or instance configurations
        self.aws_access_key_id = self._get_config_value("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = self._get_config_value("AWS_SECRET_ACCESS_KEY")
        self.aws_storage_bucket_name = (
            self._get_config_value("AWS_STORAGE_BUCKET_NAME")
            or self._get_config_value("AWS_S3_BUCKET_NAME")
            or self._get_config_value("BUCKET_NAME")
        )
        self.aws_region = self._get_config_value("AWS_REGION", "ap-south-1")
        endpoint = self._get_config_value("AWS_S3_ENDPOINT_URL") or self._get_config_value("MINIO_ENDPOINT_URL")
        self.aws_s3_endpoint_url = endpoint if endpoint and endpoint.strip() else None
        self.signed_url_expiration = int(self._get_config_value("SIGNED_URL_EXPIRATION", "3600"))

        if os.environ.get("USE_MINIO") == "1":
            # Determine protocol based on environment variable
            if os.environ.get("MINIO_ENDPOINT_SSL") == "1":
                endpoint_protocol = "https"
            else:
                endpoint_protocol = request.scheme if request else "http"
            # Create an S3 client for MinIO
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region,
                endpoint_url=(f"{endpoint_protocol}://{request.get_host()}" if request else self.aws_s3_endpoint_url),
                config=boto3.session.Config(signature_version="s3v4", connect_timeout=3, read_timeout=3),
            )
        else:
            # Create an S3 client for AWS S3
            endpoint_url = self.aws_s3_endpoint_url
            if not endpoint_url and self.aws_region:
                endpoint_url = f"https://s3.{self.aws_region}.amazonaws.com"
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region,
                endpoint_url=endpoint_url,
                config=boto3.session.Config(
                    signature_version="s3v4",
                    s3={"addressing_style": "virtual"},
                    connect_timeout=3,
                    read_timeout=3,
                ),
            )

    def generate_presigned_post(self, object_name, file_type, file_size, expiration=None):
        """Generate a presigned URL to upload an S3 object"""
        if expiration is None:
            expiration = self.signed_url_expiration
        fields = {"Content-Type": file_type}

        max_size = max(int(file_size or 0), int(os.environ.get("FILE_SIZE_LIMIT", "5242880")))

        # Allow flexible content type matching to prevent S3 policy rejection
        content_type_prefix = file_type.split(";")[0] if file_type else ""

        conditions = [
            {"bucket": self.aws_storage_bucket_name},
            ["content-length-range", 1, max_size],
            ["starts-with", "$Content-Type", content_type_prefix.split("/")[0] if "/" in content_type_prefix else ""],
        ]

        # Add condition for the object name (key)
        if object_name.startswith("${filename}"):
            conditions.append(["starts-with", "$key", object_name[: -len("${filename}")]])
        else:
            fields["key"] = object_name

        # Generate the presigned POST URL
        try:
            # Generate a presigned URL for the S3 object
            response = self.s3_client.generate_presigned_post(
                Bucket=self.aws_storage_bucket_name,
                Key=object_name,
                Fields=fields,
                Conditions=conditions,
                ExpiresIn=expiration,
            )
        # Handle errors
        except (ClientError, Exception) as e:
            print(f"Error generating presigned POST URL: {e}")
            return None

        return response

    def _get_content_disposition(self, disposition, filename=None):
        """Helper method to generate Content-Disposition header value"""
        if filename is None:
            filename = uuid.uuid4().hex

        if filename:
            # Encode the filename to handle special characters
            encoded_filename = quote(filename)
            return f"{disposition}; filename*=UTF-8''{encoded_filename}"
        return disposition

    def generate_presigned_url(
        self,
        object_name,
        expiration=None,
        http_method="GET",
        disposition="inline",
        filename=None,
    ):
        """Generate a presigned URL to share an S3 object"""
        if expiration is None:
            expiration = self.signed_url_expiration
        content_disposition = self._get_content_disposition(disposition, filename)
        try:
            response = self.s3_client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.aws_storage_bucket_name,
                    "Key": str(object_name),
                    "ResponseContentDisposition": content_disposition,
                },
                ExpiresIn=expiration,
                HttpMethod=http_method,
            )
        except (ClientError, Exception) as e:
            log_exception(e)
            return None

        # The response contains the presigned URL
        return response

    def get_object_metadata(self, object_name):
        """Get the metadata for an S3 object"""
        try:
            response = self.s3_client.head_object(Bucket=self.aws_storage_bucket_name, Key=object_name)
        except (ClientError, Exception) as e:
            log_exception(e)
            return None

        return {
            "ContentType": response.get("ContentType"),
            "ContentLength": response.get("ContentLength"),
            "LastModified": (response.get("LastModified").isoformat() if response.get("LastModified") else None),
            "ETag": response.get("ETag"),
            "Metadata": response.get("Metadata", {}),
        }

    def copy_object(self, object_name, new_object_name):
        """Copy an S3 object to a new location"""
        try:
            response = self.s3_client.copy_object(
                Bucket=self.aws_storage_bucket_name,
                CopySource={"Bucket": self.aws_storage_bucket_name, "Key": object_name},
                Key=new_object_name,
            )
        except (ClientError, Exception) as e:
            log_exception(e)
            return None

        return response

    def upload_file(
        self,
        file_obj,
        object_name: str,
        content_type: str = None,
        extra_args: dict = {},
    ) -> bool:
        """Upload a file directly to S3"""
        try:
            if content_type:
                extra_args["ContentType"] = content_type

            self.s3_client.upload_fileobj(
                file_obj,
                self.aws_storage_bucket_name,
                object_name,
                ExtraArgs=extra_args,
            )
            return True
        except (ClientError, Exception) as e:
            log_exception(e)
            return False

    def delete_files(self, object_names):
        """Delete an S3 object"""
        try:
            self.s3_client.delete_objects(
                Bucket=self.aws_storage_bucket_name,
                Delete={"Objects": [{"Key": object_name} for object_name in object_names]},
            )
            return True
        except (ClientError, Exception) as e:
            log_exception(e)
            return False
