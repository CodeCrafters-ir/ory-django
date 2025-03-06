#!/usr/bin/env python3
"""
Simplified Ory Hydra and Kratos integration example.
This version uses a more direct approach with the Python requests library
instead of relying on the SDK structure.
"""

import os
import json
import time
import uuid
import requests
import traceback
from typing import Dict, Any, Optional


class OryIntegration:
    def __init__(self) -> None:
        """Initialize Ory Hydra and Kratos endpoint URLs."""
        # Hydra URLs - use container names by default for Docker networking
        self.hydra_admin_url = os.environ.get("HYDRA_ADMIN_URL", "http://hydra:4445")
        self.hydra_public_url = os.environ.get("HYDRA_PUBLIC_URL", "http://hydra:4444")

        # Kratos URLs - use container names by default for Docker networking
        self.kratos_admin_url = os.environ.get("KRATOS_ADMIN_URL", "http://kratos:4434")
        self.kratos_public_url = os.environ.get("KRATOS_PUBLIC_URL", "http://kratos:4433")

        print(f"Using Hydra Admin URL: {self.hydra_admin_url}")
        print(f"Using Hydra Public URL: {self.hydra_public_url}")
        print(f"Using Kratos Admin URL: {self.kratos_admin_url}")
        print(f"Using Kratos Public URL: {self.kratos_public_url}")

        # Verify URLs don't contain localhost inside Docker
        for url_name, url in [
            ("Hydra Admin", self.hydra_admin_url),
            ("Hydra Public", self.hydra_public_url),
            ("Kratos Admin", self.kratos_admin_url),
            ("Kratos Public", self.kratos_public_url)
        ]:
            if "localhost" in url:
                print(f"WARNING: {url_name} URL contains 'localhost' which may cause connection issues in Docker: {url}")

    def create_oauth2_client(self, name: str, redirect_uris: list = None) -> Dict[str, Any]:
        """
        Create a new OAuth2 client in Hydra using direct API calls.

        Args:
            name: Name of the client
            redirect_uris: List of allowed redirect URIs

        Returns:
            dict: Created OAuth2 client details
        """
        if redirect_uris is None:
            redirect_uris = ["http://localhost:8080/callback"]

        try:
            # Prepare client creation request
            client_data = {
                "client_name": name,
                "redirect_uris": redirect_uris,
                "grant_types": ["authorization_code", "refresh_token", "client_credentials"],
                "response_types": ["code", "id_token"],
                "scope": "openid offline",
                "token_endpoint_auth_method": "client_secret_post"
            }

            # Explicitly create the full URL to avoid any string interpolation issues
            url = f"{self.hydra_admin_url}/clients"
            print(f"Creating OAuth2 client at URL: {url}")

            # Make the API request
            response = requests.post(url, json=client_data)
            response.raise_for_status()

            client = response.json()
            print(f"Created OAuth2 client: {client['client_id']}")
            return client

        except requests.RequestException as e:
            print(f"Error creating OAuth2 client: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            raise

    def create_user(self, email: str, password: str, traits: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new user identity in Kratos using direct API calls.

        Args:
            email: User's email
            password: User's password
            traits: Additional user traits

        Returns:
            dict: Created identity details
        """
        if traits is None:
            traits = {}

        # Ensure we have at least email in traits
        if "email" not in traits:
            traits["email"] = email

        try:
            # Prepare identity creation request
            identity_data = {
                "schema_id": "default",
                "traits": traits,
                "credentials": {
                    "password": {
                        "config": {
                            "password": password
                        }
                    }
                }
            }

            # Explicitly create the full URL
            url = f"{self.kratos_admin_url}/identities"
            print(f"Creating user at URL: {url}")

            # Make the API request
            response = requests.post(url, json=identity_data)
            response.raise_for_status()

            identity = response.json()
            print(f"Created user with ID: {identity['id']}")
            return identity

        except requests.RequestException as e:
            print(f"Error creating user: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            raise

    def get_jwt_token(self, client_id: str, client_secret: str, scope: str = "openid offline") -> Dict[str, Any]:
        """
        Get a JWT token using the client credentials flow.

        Args:
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            scope: Requested scopes

        Returns:
            dict: Token response with access_token, refresh_token, etc.
        """
        try:
            # Build the token request
            token_url = f"{self.hydra_public_url}/oauth2/token"
            print(f"Getting JWT token from URL: {token_url}")

            payload = {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": scope
            }

            # Request the token
            response = requests.post(token_url, data=payload)
            response.raise_for_status()

            token_data = response.json()
            print(f"Generated JWT token (expires in {token_data.get('expires_in')} seconds)")
            return token_data

        except requests.RequestException as e:
            print(f"Error getting JWT token: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            raise

    def introspect_token(self, token: str, client_id: str, client_secret: str) -> Dict[str, Any]:
        """
        Introspect a token to validate it and get its metadata.

        Args:
            token: The JWT token to introspect
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret

        Returns:
            dict: Token introspection response
        """
        try:
            # Build the introspection request
            introspect_url = f"{self.hydra_public_url}/oauth2/introspect"
            print(f"Introspecting token at URL: {introspect_url}")

            payload = {
                "token": token,
                "client_id": client_id,
                "client_secret": client_secret,
            }

            # Make the introspection request
            response = requests.post(introspect_url, data=payload)
            response.raise_for_status()

            introspection_data = response.json()
            if introspection_data.get("active", False):
                print(f"Token is valid, expires at: {introspection_data.get('exp')}")
            else:
                print("Token is invalid or expired")

            return introspection_data

        except requests.RequestException as e:
            print(f"Error introspecting token: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            raise

    def list_users(self) -> list:
        """
        List all users in Kratos.

        Returns:
            list: List of user identities
        """
        try:
            url = f"{self.kratos_admin_url}/identities"
            print(f"Listing users from URL: {url}")

            response = requests.get(url)
            response.raise_for_status()

            identities = response.json()
            print(f"Found {len(identities)} users")
            return identities

        except requests.RequestException as e:
            print(f"Error listing users: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            raise

    def list_clients(self) -> list:
        """
        List all OAuth2 clients in Hydra.

        Returns:
            list: List of OAuth2 clients
        """
        try:
            url = f"{self.hydra_admin_url}/clients"
            print(f"Listing clients from URL: {url}")

            response = requests.get(url)
            response.raise_for_status()

            clients = response.json()
            print(f"Found {len(clients)} OAuth2 clients")
            return clients

        except requests.RequestException as e:
            print(f"Error listing OAuth2 clients: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            raise

    def health_check(self) -> Dict[str, bool]:
        """
        Check if Ory services are available.

        Returns:
            dict: Health status of each service
        """
        health = {
            "hydra_admin": False,
            "hydra_public": False,
            "kratos_admin": False,
            "kratos_public": False
        }

        try:
            # Check Hydra Admin
            url = f"{self.hydra_admin_url}/health/ready"
            print(f"Checking Hydra Admin health at URL: {url}")
            response = requests.get(url)
            health["hydra_admin"] = response.status_code == 200
        except requests.RequestException as e:
            print(f"Error checking Hydra Admin health: {e}")

        try:
            # Check Hydra Public
            url = f"{self.hydra_public_url}/health/ready"
            print(f"Checking Hydra Public health at URL: {url}")
            response = requests.get(url)
            health["hydra_public"] = response.status_code == 200
        except requests.RequestException as e:
            print(f"Error checking Hydra Public health: {e}")

        try:
            # Check Kratos Admin
            url = f"{self.kratos_admin_url}/health/ready"
            print(f"Checking Kratos Admin health at URL: {url}")
            response = requests.get(url)
            health["kratos_admin"] = response.status_code == 200
        except requests.RequestException as e:
            print(f"Error checking Kratos Admin health: {e}")

        try:
            # Check Kratos Public
            url = f"{self.kratos_public_url}/health/ready"
            print(f"Checking Kratos Public health at URL: {url}")
            response = requests.get(url)
            health["kratos_public"] = response.status_code == 200
        except requests.RequestException as e:
            print(f"Error checking Kratos Public health: {e}")

        print("Health check:")
        for service, status in health.items():
            print(f"  {service}: {'OK' if status else 'Not available'}")

        return health


def main() -> None:
    """Main function to demonstrate Ory integration capabilities."""
    try:
        # Initialize the Ory integration
        ory = OryIntegration()

        # Perform health check
        health = ory.health_check()

        # Continue only if services are available
        if not health["hydra_admin"] or not health["hydra_public"]:
            print("Warning: Some Hydra services are not available. Continuing anyway...")

        if not health["kratos_admin"] or not health["kratos_public"]:
            print("Warning: Some Kratos services are not available. Continuing anyway...")

        # Try to create an OAuth2 client
        client_name = f"example-client-{uuid.uuid4()}"
        client = ory.create_oauth2_client(
            name=client_name,
            redirect_uris=["http://localhost:8080/callback", "http://localhost:8888/callback"]
        )
        client_id = client["client_id"]
        client_secret = client["client_secret"]

        # Create a user
        user_email = f"user-{uuid.uuid4()}@example.com"
        user_password = f"Password-{uuid.uuid4()}"
        user = ory.create_user(
            email=user_email,
            password=user_password,
            traits={
                "email": user_email,
                "name": {
                    "first": "Example",
                    "last": "User"
                }
            }
        )

        # Generate a JWT token
        token_response = ory.get_jwt_token(client_id, client_secret)
        access_token = token_response.get("access_token")

        # Validate the token
        ory.introspect_token(access_token, client_id, client_secret)

        # List existing clients and users
        ory.list_clients()
        ory.list_users()

        print("\nTest data:")
        print(f"Client ID: {client_id}")
        print(f"Client Secret: {client_secret}")
        print(f"User Email: {user_email}")
        print(f"User Password: {user_password}")
        print(f"Access Token: {access_token}")

    except Exception as e:
        print(f"Error occurred during the demo: {e}")
        print("Check if all Ory services are running and configured correctly.")
        print("Stack trace:")
        traceback.print_exc()


if __name__ == "__main__":
    # Wait a bit to ensure Ory services are ready
    print("Waiting for Ory services to be ready...")
    time.sleep(15)
    main()