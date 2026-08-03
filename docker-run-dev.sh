#!/bin/bash
set -e

echo "Starting Docker Doctor (development mode)..."

# Start Flask with hot reload on port 8586
# Serve React dev server on port 3000 (separate port for local dev)
cd /app

echo "Flask API server starting on port 8586..."
python backend/api/app.py &

echo "React dev server starting on port 3000..."
cd frontend
npx react-scripts start --port 3000 &

echo "Flask API:  http://localhost:8586"
echo "React Dev:  http://localhost:3000"
echo "React Proxy: set REACT_APP_API_URL=http://localhost:8586"

wait
