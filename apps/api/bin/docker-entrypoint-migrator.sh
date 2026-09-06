#!/bin/bash
set -e

python manage.py wait_for_db $1

echo "Applying database migrations..."
max_retries=5
count=0
until python manage.py migrate $1; do
    count=$((count + 1))
    if [ $count -ge $max_retries ]; then
        echo "Error: Database migrations failed after $max_retries attempts."
        exit 1
    fi
    echo "Migration attempt $count failed, retrying in 3 seconds..."
    sleep 3
done
echo "Database migrations applied successfully."