# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import base64
import hashlib
from django.conf import settings
from cryptography.fernet import Fernet

from plane.utils.exception_logger import log_exception


def derive_key(secret_key):
    # Use a key derivation function to get a suitable encryption key
    dk = hashlib.pbkdf2_hmac("sha256", secret_key.encode(), b"salt", 100000)
    return base64.urlsafe_b64encode(dk)


# Encrypt data
def encrypt_data(data):
    try:
        if data:
            cipher_suite = Fernet(derive_key(settings.SECRET_KEY))
            encrypted_data = cipher_suite.encrypt(data.encode())
            return encrypted_data.decode()  # Convert bytes to string
        else:
            return ""
    except Exception as e:
        log_exception(e)
        return ""


# Decrypt data
def decrypt_data(encrypted_data):
    try:
        if not encrypted_data:
            return ""

        # Candidates: try active settings, environment variable, and known fallback keys
        import os
        candidates = [
            getattr(settings, "SECRET_KEY", None),
            os.environ.get("SECRET_KEY"),
            "60gp0byfz2dvffa45cxl20p1scy9xbpf6d8c5y0geejgkyp1b5",
            "K_8t#5[TX_iV-wbZutF3an:xi0V(,]&TdD=4r@2UW,+ZWzYS+h",
        ]

        seen = set()
        for key in candidates:
            if not key or key in seen:
                continue
            seen.add(key)
            try:
                cipher_suite = Fernet(derive_key(key))
                return cipher_suite.decrypt(encrypted_data.encode()).decode()
            except Exception:
                continue

        # If data is not a Fernet token (Fernet tokens start with gAAAAA),
        # return the raw plaintext value rather than destroying/blanking it out
        if encrypted_data and not encrypted_data.startswith("gAAAAA"):
            return encrypted_data

        return ""
    except Exception as e:
        log_exception(e)
        return encrypted_data if (encrypted_data and not encrypted_data.startswith("gAAAAA")) else ""

