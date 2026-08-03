#!/bin/bash
# Verify the docker-doctor setup and configuration

echo "=== Docker Doctor Verification Script ==="

# Check if required files exist
echo "1. Verifying core files exist..."
if [ -f "Dockerfile" ]; then
    echo "   ✓ Dockerfile exists"
else
    echo "   ✗ Dockerfile missing"
fi

if [ -f "docker-run.sh" ]; then
    echo "   ✓ docker-run.sh exists"
else
    echo "   ✗ docker-run.sh missing"
fi

if [ -f "config.example.yaml" ]; then
    echo "   ✓ config.example.yaml exists"
else
    echo "   ✗ config.example.yaml missing"
fi

# Check for the specific issues in the roadmap
echo "2. Checking for known issues..."

# Check for hardcoded data in Dockerfile
if grep -q "data/logs.db" Dockerfile; then
    echo "   ⚠ Dockerfile still contains hardcoded data reference"
else
    echo "   ✓ Dockerfile doesn't reference hardcoded data"
fi

# Check for openssh-client in Dockerfile
if grep -q "openssh-client" Dockerfile; then
    echo "   ⚠ Dockerfile still contains openssh-client (vestigial)"
else
    echo "   ✓ Dockerfile doesn't contain openssh-client"
fi

# Check if the scheduler is wired
if [ -f "src/scheduler.py" ]; then
    echo "   ✓ Scheduler script exists"
else
    echo "   ✗ Scheduler script missing"
fi

# Check for hard-coded frontend URLs
echo "3. Checking frontend URLs..."
FRONTEND_URLS=$(find frontend -name "*.js" -exec grep -l "localhost:8586" {} \; 2>/dev/null)
if [ -n "$FRONTEND_URLS" ]; then
    echo "   ⚠ Hardcoded frontend URLs found in:"
    echo "      $FRONTEND_URLS"
else
    echo "   ✓ No hardcoded frontend URLs found"
fi

echo "4. Verification complete"