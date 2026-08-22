#!/bin/bash
# Docker Build Script for Docker Doctor v2.1
# Run this script to build and push the Docker image

echo "=============================================="
echo "DOCKER DOCTOR v2.1 BUILD SCRIPT"
echo "=============================================="

# Check if docker is installed and available
if ! command -v docker &> /dev/null; then
    echo "❌ ERROR: Docker is not installed or not in PATH"
    exit 1
fi

echo "✓ Docker is available"
echo "✓ Building image for ridiculousostrich/docker-doctor:v2.1"

# Build the Docker image
echo "Building Docker image..."
docker build --build-arg AI_PROVIDER=ollama -t ridiculousostrich/docker-doctor:v2.1 .
docker tag ridiculousostrich/docker-doctor:v2.1 ridiculousostrich/docker-doctor:latest

if [ $? -eq 0 ]; then
    echo "✅ SUCCESS: Docker image built successfully"
    echo ""

    # Show image details
    echo "=== IMAGE DETAILS ==="
    docker images | grep ridiculousostrich/docker-doctor

    echo ""
    echo "=== PUSH TO DOCKER HUB ==="
    echo "docker push ridiculousostrich/docker-doctor:v2.1"
    echo "docker push ridiculousostrich/docker-doctor:latest"
    echo ""
    echo "=== USAGE EXAMPLE ==="
    echo "docker run -d \\"
    echo "  --name docker-doctor \\"
    echo "  -p 8586:8586 \\"
    echo "  -v /var/run/docker.sock:/var/run/docker.sock:ro \\"
    echo "  -v \$(pwd)/config.yaml:/app/config.yaml:ro \\"
    echo "  -v doctor-data:/app/data \\"
    echo "  ridiculousostrich/docker-doctor:v2.1"
else
    echo "❌ FAILED: Docker build failed"
    exit 1
fi
