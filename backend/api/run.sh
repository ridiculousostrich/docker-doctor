#!/bin/bash

echo "Starting Docker Doctor services..."
echo "Starting Flask API server on port 8586..."

# Start the Flask API server in the background
python /app/backend/api/app.py &

# Wait a moment for the API server to start
sleep 2

echo "Starting React frontend server on port 8585..."

# Start the React frontend server
npx serve -s /app/public -p 8585
