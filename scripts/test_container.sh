#!/bin/bash

set -e

IMAGE_NAME="wishlist-app:latest"
CONTAINER_NAME="test-wishlist-app"

echo "=== Container Security Tests ==="

if ! docker images | grep -q "wishlist-app"; then
    echo "Building image..."
    docker build -t $IMAGE_NAME .
fi

echo ""
echo "1. Testing non-root user..."
USER_ID=$(docker run --rm $IMAGE_NAME id -u)
echo "   Container user ID: $USER_ID"

if [ "$USER_ID" = "0" ]; then
    echo "   ❌ FAIL: Container running as root!"
    exit 1
fi
echo "   ✓ PASS: Running as non-root (UID: $USER_ID)"

echo ""
echo "2. Testing file permissions..."
docker run --rm $IMAGE_NAME ls -la /app | head -n 5

echo ""
echo "3. Checking Python environment..."
docker run --rm $IMAGE_NAME python --version
docker run --rm $IMAGE_NAME pip list | grep -E "(fastapi|uvicorn|sqlalchemy)"

echo ""
echo "4. Testing healthcheck configuration..."
HEALTHCHECK=$(docker inspect $IMAGE_NAME | grep -i healthcheck -A 10 || echo "none")
if echo "$HEALTHCHECK" | grep -q "Test"; then
    echo "   ✓ Healthcheck configured"
else
    echo "   ❌ WARNING: No healthcheck found"
fi

echo ""
echo "5. Starting container for runtime test..."
docker run -d --name $CONTAINER_NAME -p 8001:8000 $IMAGE_NAME

sleep 5

echo ""
echo "6. Checking container status..."
STATUS=$(docker inspect -f '{{.State.Status}}' $CONTAINER_NAME)
echo "   Container status: $STATUS"

if [ "$STATUS" != "running" ]; then
    echo "   ❌ Container not running"
    docker logs $CONTAINER_NAME
    docker rm -f $CONTAINER_NAME
    exit 1
fi

echo ""
echo "7. Testing health endpoint..."
for i in {1..10}; do
    if curl -f http://localhost:8001/health 2>/dev/null; then
        echo "   ✓ Health endpoint responding"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "   ❌ Health endpoint not responding after 10 attempts"
        docker logs $CONTAINER_NAME
        docker rm -f $CONTAINER_NAME
        exit 1
    fi
    sleep 2
done

echo ""
echo "8. Checking process user inside container..."
PROC_USER=$(docker exec $CONTAINER_NAME ps aux | grep uvicorn | grep -v grep | awk '{print $1}')
echo "   Process running as: $PROC_USER"
if [ "$PROC_USER" = "root" ]; then
    echo "   ❌ FAIL: Process running as root!"
    docker rm -f $CONTAINER_NAME
    exit 1
fi
echo "   ✓ PASS: Process running as non-root user"

echo ""
echo "Cleaning up..."
docker rm -f $CONTAINER_NAME > /dev/null

echo ""
echo "=== All tests passed! ==="

