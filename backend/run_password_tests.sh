#!/bin/bash
# Script to run password policy tests

echo "🧪 Running Password Policy Tests"
echo "================================"
echo ""

# Check if running in Docker
if [ -f /.dockerenv ] || [ -n "$DOCKER_CONTAINER" ]; then
    echo "Running in Docker container..."
    pytest tests/test_password_policy.py -v
else
    # Check if Docker is available
    if command -v docker-compose &> /dev/null; then
        echo "Running tests via Docker Compose..."
        docker-compose -f ../docker-compose.prod.yml exec backend pytest tests/test_password_policy.py -v
    elif command -v docker &> /dev/null; then
        echo "Running tests via Docker..."
        docker exec -it industrace-backend-1 pytest tests/test_password_policy.py -v || \
        docker exec -it backend pytest tests/test_password_policy.py -v
    else
        echo "Running tests directly (requires pytest and dependencies)..."
        pytest tests/test_password_policy.py -v
    fi
fi

echo ""
echo "✅ Tests completed!"
