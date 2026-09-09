# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from django.core.management.base import BaseCommand
from plane.license.utils.infisical import sync_secrets_into_runtime, get_infisical_credentials


class Command(BaseCommand):
    help = "Directly fetch and synchronize secrets from Infisical into runtime (no plane.env write)"

    def handle(self, *args, **options):
        creds = get_infisical_credentials()
        self.stdout.write(f"Connecting to Infisical at {creds['host']} targeting {creds['environment']}...")
        try:
            count = sync_secrets_into_runtime()
            if count > 0:
                self.stdout.write(self.style.SUCCESS(f"Successfully fetched and synced {count} secrets directly from Infisical."))
            else:
                self.stdout.write(self.style.WARNING("No secrets retrieved from Infisical (check credentials or target env)."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to sync from Infisical: {e}"))
