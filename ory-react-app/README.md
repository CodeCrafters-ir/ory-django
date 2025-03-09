# Ory React Application

This is a React application integrated with Ory Kratos for authentication and identity management.

## Prerequisites

- Node.js and npm installed
- Ory Kratos running (see docker-compose.yml in your setup)

## Getting Started

1. Install dependencies:
   ```
   npm install
   ```

2. Configure environment variables:
   Edit the `.env` file to match your Ory Kratos setup.

3. Start the development server:
   ```
   npm start
   ```

4. Open [http://localhost:3000](http://localhost:3000) to view the application in your browser.

## Features

- User registration and login
- Protected routes requiring authentication
- User dashboard with profile information
- Session management

## Project Structure

- `src/components/auth`: Authentication components (Login, Registration)
- `src/contexts`: React contexts including AuthContext for user session management
- `src/pages`: Application pages
- `src/services`: Service layer for API interactions
- `src/hooks`: Custom React hooks
- `src/utils`: Utility functions
