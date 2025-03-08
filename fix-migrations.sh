#!/bin/bash

echo "Fixing Ory database migrations..."

# Stop all services
docker compose down

# Remove any existing volumes to start fresh
docker volume rm $(docker volume ls -q | grep postgres-data) 2>/dev/null || true

# Start just the postgres container
docker compose up -d postgres

echo "Waiting for PostgreSQL to be ready..."
sleep 10

# Create the hydra database manually
echo "Creating hydra database..."
docker exec -it ory_postgres psql -U ory -c "CREATE DATABASE hydra;" || true
docker exec -it ory_postgres psql -U ory -c "GRANT ALL PRIVILEGES ON DATABASE hydra TO ory;" || true

# Create the kratos database manually
echo "Creating kratos database..."
docker exec -it ory_postgres psql -U ory -c "CREATE DATABASE kratos;" || true
docker exec -it ory_postgres psql -U ory -c "GRANT ALL PRIVILEGES ON DATABASE kratos TO ory;" || true

# Run migrations directly
echo "Running Hydra migrations..."
docker run --rm \
  --network ory_network \
  -e DSN=postgres://ory:ory_password@ory_postgres:5432/hydra?sslmode=disable \
  oryd/hydra:v2.2.0 \
  migrate sql -e --yes

echo "Running Kratos migrations..."
docker run --rm \
  --network ory_network \
  -v $(pwd)/config/kratos:/etc/config/kratos \
  -e DSN=postgres://ory:ory_password@ory_postgres:5432/kratos?sslmode=disable \
  oryd/kratos:v1.0.0 \
  migrate sql -e --yes

echo "Starting remaining services..."
docker compose up -d

echo "Setup complete! Waiting for services to be ready..."
sleep 15

echo "All services should be running now."
