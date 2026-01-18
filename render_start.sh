#!/bin/bash

echo "Running Render Start Script..."

# Set up persistent directories
echo "Ensuring persistent directories exist..."
mkdir -p /var/lib/aulacl_data/texts
mkdir -p /var/lib/aulacl_data/audio
mkdir -p /var/lib/aulacl_data/images

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

# Run Gunicorn
echo "Starting Application..."
exec gunicorn -k uvicorn.workers.UvicornWorker app.main:app
