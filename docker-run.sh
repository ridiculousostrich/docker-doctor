#!/bin/bash
set -e

echo "Starting Docker Doctor (production mode)..."

# Ensure config directory exists
mkdir -p /app/config

# Start both Flask API server and scheduler as supervised processes
cd /app

# Verify config file exists or use defaults
if [ -f "/app/config.yaml" ]; then
    echo "Using mounted config.yaml"
else
    echo "No mounted config.yaml found, using defaults"
fi

# Start Flask API server (port 8586)
echo "Starting Flask API server..."
python backend/api/app.py &

# Start the scheduler
echo "Starting Docker Doctor scheduler..."
python src/scheduler.py &

# Wait for both processes to complete
wait
