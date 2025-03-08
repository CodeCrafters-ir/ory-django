#!/bin/bash

echo "Setting up Ory UI App..."

# Navigate to the ory-ui directory
cd ory-ui

# For development - install dependencies and start the development server
echo "Installing dependencies..."
npm install

echo ""
echo "You can now start the development server with:"
echo "cd ory-ui && npm start"
echo ""
echo "Or build and run the Docker container with:"
echo "cd ory-ui && docker compose up -d"
