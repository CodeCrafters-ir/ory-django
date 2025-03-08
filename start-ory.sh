#!/bin/bash

echo "Starting Ory Hydra, Kratos, and Simple UI..."

# Make sure the Postgres init script is executable
chmod +x scripts/init-multiple-postgres-dbs.sh

# Start all services
docker compose up -d

echo ""
echo "Services are starting up..."
echo "You can access the UI at: http://localhost:3000"
echo "Kratos API is available at: http://localhost:4433"
echo "Hydra API is available at: http://localhost:4444"
