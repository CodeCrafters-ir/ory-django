#!/bin/bash

echo "Checking if services are running..."
if ! docker ps | grep -q ory_kratos; then
  echo "Services are not running. Please run ./setup-ory.sh first."
  exit 1
fi

echo "Running user creation script inside Docker network..."

docker run --rm -it \
  --network ory_network \
  -v $(pwd)/ory-script.py:/app/script.py \
  python:3.9-slim \
  bash -c "apt update && apt install -y curl iputils-ping && \
    pip install requests && \
    echo 'Testing connectivity:' && \
    echo 'Pinging kratos...' && \
    ping -c 2 ory_kratos && \
    echo 'Pinging hydra...' && \
    ping -c 2 ory_hydra && \
    echo 'Checking Kratos health...' && \
    curl -s -o /dev/null -w '%{http_code}\n' http://ory_kratos:4433/health/ready && \
    echo 'Checking Hydra health...' && \
    curl -s -o /dev/null -w '%{http_code}\n' http://ory_hydra:4444/health/ready && \
    echo 'Running script...' && \
    python /app/script.py"

echo "Script execution completed"
