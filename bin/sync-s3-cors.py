#!/usr/bin/env python3
"""
Sync AWS S3 Bucket CORS configuration based on canonical ONEFLOW_DOMAIN.
Reads:
  - ONEFLOW_DOMAIN (e.g. http://SERVER_IP or https://oneflow.example.com)
  - AWS_STORAGE_BUCKET_NAME (or AWS_S3_BUCKET_NAME)
  - AWS_REGION
"""

import os
import sys
import boto3
from botocore.config import Config
from urllib.parse import urlparse

def get_env_var(name, default=""):
    val = os.environ.get(name, "")
    if not val and os.path.exists(".env"):
        try:
            with open(".env") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f"{name}="):
                        val = line.split("=", 1)[1].strip().strip('"\'')
                        break
        except Exception:
            pass
    return val or default

def sync_s3_cors(custom_domain=None):
    domain = custom_domain or get_env_var("ONEFLOW_DOMAIN") or get_env_var("WEB_URL")
    if not domain:
        print("ERROR: ONEFLOW_DOMAIN or WEB_URL is required.")
        sys.exit(1)

    domain = domain.strip().rstrip("/")
    if not (domain.startswith("http://") or domain.startswith("https://")):
        domain = f"http://{domain}"

    bucket = get_env_var("AWS_STORAGE_BUCKET_NAME") or get_env_var("AWS_S3_BUCKET_NAME", "oneflow-staging-uploads")
    region = get_env_var("AWS_REGION", "ap-south-1")

    # Allowed origins: the canonical domain + localhost origins for dev
    allowed_origins = [domain, "http://localhost", "http://localhost:3000", "http://127.0.0.1"]
    # De-duplicate
    allowed_origins = list(dict.fromkeys(allowed_origins))

    cors_configuration = {
        "CORSRules": [
            {
                "AllowedHeaders": ["*"],
                "AllowedMethods": ["GET", "POST", "PUT", "HEAD", "DELETE"],
                "AllowedOrigins": allowed_origins,
                "ExposeHeaders": ["ETag"],
                "MaxAgeSeconds": 3600,
            }
        ]
    }

    client = boto3.client(
        "s3",
        region_name=region,
        config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
    )

    print(f"Setting CORS for S3 bucket '{bucket}' in region '{region}'...")
    print(f"Allowed Origins: {allowed_origins}")
    client.put_bucket_cors(Bucket=bucket, CORSConfiguration=cors_configuration)
    print("S3 CORS updated successfully.")

if __name__ == "__main__":
    domain_arg = sys.argv[1] if len(sys.argv) > 1 else None
    sync_s3_cors(domain_arg)
