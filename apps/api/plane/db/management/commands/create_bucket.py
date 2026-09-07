# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

# Python imports
import os
import boto3
from botocore.exceptions import ClientError

# Django imports
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = "Create the default bucket for the instance"

    def handle(self, *args, **options):
        endpoint_url = os.environ.get("AWS_S3_ENDPOINT_URL")
        bucket_name = os.environ.get("AWS_S3_BUCKET_NAME")
        use_minio = os.environ.get("USE_MINIO", "0")

        # Cleanly skip if storage is disabled or not configured
        if use_minio != "1" and not endpoint_url and not bucket_name:
            self.stdout.write(self.style.NOTICE("S3 / MinIO storage is not configured. Skipping bucket setup."))
            return

        if not bucket_name:
            self.stdout.write(self.style.NOTICE("AWS_S3_BUCKET_NAME is not set. Skipping bucket setup."))
            return

        # Create a session using credentials with fast connect timeout
        try:
            s3_client = boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
                region_name=os.environ.get("AWS_REGION"),
                config=boto3.session.Config(
                    signature_version="s3v4",
                    connect_timeout=3,
                    read_timeout=3,
                ),
            )
            self.stdout.write(self.style.NOTICE("Checking bucket..."))
            # Check if the bucket exists
            s3_client.head_bucket(Bucket=bucket_name)
            # If the bucket exists, print a success message
            self.stdout.write(self.style.SUCCESS(f"Bucket '{bucket_name}' exists."))
            return
        except ClientError as e:
            error_code = int(e.response["Error"]["Code"])
            bucket_name = os.environ.get("AWS_S3_BUCKET_NAME")
            if error_code == 404:
                # Bucket does not exist, create it
                self.stdout.write(self.style.WARNING(f"Bucket '{bucket_name}' does not exist. Creating bucket..."))
                try:
                    s3_client.create_bucket(Bucket=bucket_name)
                    self.stdout.write(self.style.SUCCESS(f"Bucket '{bucket_name}' created successfully."))

                # Handle the exception if the bucket creation fails
                except ClientError as create_error:
                    self.stdout.write(self.style.ERROR(f"Failed to create bucket: {create_error}"))

            # Handle the exception if access to the bucket is forbidden
            elif error_code == 403:
                # Access to the bucket is forbidden
                self.stdout.write(
                    self.style.ERROR(f"Access to the bucket '{bucket_name}' is forbidden. Check permissions.")
                )
            else:
                # Another ClientError occurred
                self.stdout.write(self.style.ERROR(f"Failed to check bucket: {e}"))
        except Exception as ex:
            # Handle any other exception
            self.stdout.write(self.style.ERROR(f"An error occurred: {ex}"))
