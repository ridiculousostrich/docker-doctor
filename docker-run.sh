#!/bin/bash
set -e

echo "Starting Docker Doctor (production mode)..."

# Start Flask API server (port 8586) and serve React on port 8585
cd /app
exec python backend/api/app.py
