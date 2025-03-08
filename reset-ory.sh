#!/bin/bash

echo "Completely resetting Ory environment..."

# Stop all running containers
docker compose down

# Remove all volumes
docker volume rm $(docker volume ls -q) 2>/dev/null || true

# Clean up any networks
docker network prune -f

# Remove any existing directories
rm -rf config scripts ory-ui simple-ory-ui

# Create the network
docker network create ory_network

echo "Reset complete. You can now start fresh with your setup."
