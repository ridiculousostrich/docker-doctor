#!/bin/bash
# Docker Build Script for Docker Doctor v1.1.0
# Run this script to build the Docker image for your repository

echo "=============================================="
echo "DOCKER DOCTOR v1.1.0 BUILD SCRIPT"
echo "=============================================="

# Check if docker is installed and available
if ! command -v docker &> /dev/null; then
    echo "❌ ERROR: Docker is not installed or not in PATH"
    exit 1
fi

echo "✓ Docker is available"
echo "✓ Building image for ridiculousostrich/docker-doctor:v1.1"

# Build the Docker image
echo "Building Docker image..."
docker build -t ridiculousostrich/docker-doctor:v1.1 .

if [ $? -eq 0 ]; then
    echo "✅ SUCCESS: Docker image built successfully as ridiculousostrich/docker-doctor:v1.1"
    
    # Show image details
    echo ""
    echo "=== IMAGE DETAILS ==="
    docker images | grep ridiculousostrich/docker-doctor
    
    echo ""
    echo "=== READY TO PUSH ==="
    echo "Run: docker push ridiculousostrich/docker-doctor:v1.1"
    echo ""
    echo "=== USAGE EXAMPLE ==="
    echo "docker run -d \\"
    echo "  --name docker-doctor \\"
    echo "  --privileged \\"
    echo "  -p 8585:8585 \\"
    echo "  -p 8586:8586 \\"
    echo "  -v /var/run/docker.sock:/var/run/docker.sock \\"
    echo "  -v /opt/docker-doctor/data:/data \\"
    echo "  ridiculousostrich/docker-doctor:v1.1"
else
    echo "❌ FAILED: Docker build failed"
    exit 1
fi