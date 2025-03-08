#!/bin/bash

echo "Running Ory script inside Docker network..."

docker run --rm -it \
  --network ory_network \
  -v $(pwd)/ory-script.py:/app/script.py \
  python:3.9-slim \
  bash -c "pip install requests && echo 'Testing connectivity:' && \
  echo 'Pinging kratos...' && \
  ping -c 2 ory_kratos && \
  echo 'Pinging hydra...' && \
  ping -c 2 ory_hydra && \
  echo 'Running script...' && \
  python /app/script.py"

echo "Script execution completed"
