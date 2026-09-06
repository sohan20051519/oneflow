# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import time
from django.db import connections
from django.db.utils import OperationalError
from django.core.management import BaseCommand


class Command(BaseCommand):
    """Django command to pause execution until db is available"""

    def handle(self, *args, **options):
        self.stdout.write("Waiting for database connection...")
        db_conn = False
        attempts = 0
        while not db_conn:
            try:
                conn = connections["default"]
                conn.cursor()
                db_conn = True
            except (OperationalError, Exception) as exc:
                attempts += 1
                self.stdout.write(f"Database unavailable ({exc}), waiting 2 seconds (attempt {attempts})...")
                time.sleep(2)

        self.stdout.write(self.style.SUCCESS("Database available!"))
