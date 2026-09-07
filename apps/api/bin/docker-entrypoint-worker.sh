#!/bin/bash
set -e

python manage.py wait_for_db
# Wait for migrations
python manage.py wait_for_migrations
# Run Celery worker with embedded beat (-B) to eliminate the separate beat container on low-memory hosts
celery -A plane worker -B -l info --concurrency="${CELERY_WORKERS:-1}" --max-tasks-per-child="${CELERY_MAX_TASKS_PER_CHILD:-50}"