#!/bin/bash

# Install and enable Docker Doctor systemd service

set -e

echo "Installing Docker Doctor systemd service..."

cp /workspace/docker-doctor/docker-doctor.service /etc/systemd/system/

# Reload systemd daemon
systemctl daemon-reload

# Enable and start the service
systemctl enable docker-doctor.service
systemctl start docker-doctor.service

echo "Docker Doctor service installed and started!"

echo "Check status with: systemctl status docker-doctor.service"
echo "View logs with: journalctl -u docker-doctor.service -f"

# Test the service
if systemctl is-active --quiet docker-doctor; then
    echo "✓ Service is running"
else
    echo "✗ Service is not running!" >&2
    exit 1
fi