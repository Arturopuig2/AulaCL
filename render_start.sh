#!/bin/bash

echo "Running Render Start Script..."

# Set up persistent directories
echo "Ensuring persistent directories exist..."
mkdir -p /var/lib/aulacl_data/texts
mkdir -p /var/lib/aulacl_data/audio
mkdir -p /var/lib/aulacl_data/images

# Fix permissions for persistent disk (critical for uploads)
chmod -R 777 /var/lib/aulacl_data || echo "Warning: Could not chmod /var/lib/aulacl_data"

# Optional: Sync initial data if disk is empty
# This handles the case where we want the default repo files to be available on the persistent disk
if [ -z "$(ls -A /var/lib/aulacl_data/texts)" ]; then
   echo "Populating texts from repository..."
   cp -r data/texts/* /var/lib/aulacl_data/texts/ 2>/dev/null || :
fi

if [ -z "$(ls -A /var/lib/aulacl_data/audio)" ]; then
   echo "Populating audio from repository..."
   cp -r static/audio/* /var/lib/aulacl_data/audio/ 2>/dev/null || :
fi

# Run Schema Update (Migration)
echo "Running database schema update..."
python update_db_schema.py

# Start Gunicorn
echo "Starting Application..."
exec gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
