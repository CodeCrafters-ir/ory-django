#!/usr/bin/env python3
import requests
import json
import time
import urllib.parse
import secrets
import uuid
import sys

# Configuration with container names for internal Docker communication
KRATOS_PUBLIC_URL = "http://ory_kratos:4433"
KRATOS_ADMIN_URL = "http://ory_kratos:4434"
HYDRA_PUBLIC_URL = "http://ory_hydra:4444"
HYDRA_ADMIN_URL = "http://ory_hydra:4445"
REDIRECT_URI = "http://localhost:8000/callback"

def create_hydra_client():
    """Create an OAuth2 client in Hydra"""
    print("Creating OAuth2 client in Hydra...")
    client_id = f"test-client-{int(time.time())}"
    client_secret = str(uuid.uuid4())
    
    client_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_types": ["authorization_code", "refresh_token", "client_credentials"],
        "response_types": ["code", "id_token"],
        "scope": "openid offline",
        "redirect_uris": [REDIRECT_URI],
        "token_endpoint_auth_method": "client_secret_basic"
    }
    
    try:
        response = requests.post(
            f"{HYDRA_ADMIN_URL}/clients",
            json=client_data
        )
        
        if response.status_code == 201:
            print(f"Client created successfully.")
            print(f"Client ID: {client_id}")
            print(f"Client Secret: {client_secret}")
            return client_id, client_secret
        else:
            print(f"Failed to create client: {response.text}")
            return None, None
    except Exception as e:
        print(f"Exception while creating client: {str(e)}")
        return None, None

def create_user_admin(email, password):
    """Create a user via Kratos admin API"""
    print(f"Creating user with admin API, email: {email}...")
    
    # Create identity with admin API
    identity_data = {
        "schema_id": "default",
        "traits": {
            "email": email,
            "name": {
                "first": "Test",
                "last": "User"
            }
        },
        "credentials": {
            "password": {
                "config": {
                    "password": password
                }
            }
        }
    }
    
    try:
        print(f"Sending request to: {KRATOS_ADMIN_URL}/identities")
        response = requests.post(
            f"{KRATOS_ADMIN_URL}/identities",
            json=identity_data
        )
        
        print(f"Response status code: {response.status_code}")
        
        if response.status_code == 201:
            identity = response.json()
            print(f"User created successfully. ID: {identity['id']}")
            return identity['id']
        else:
            print(f"Failed to create user: {response.text}")
            return None
    except Exception as e:
        print(f"Exception while creating user: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return None

def get_client_credentials_token(client_id, client_secret):
    """Get an access token using client credentials grant"""
    print("Getting access token using client credentials...")
    
    # Use client_secret_basic authentication method (HTTP Basic Auth)
    auth = (client_id, client_secret)
    
    token_data = {
        "grant_type": "client_credentials",
        "scope": "openid offline"
    }
    
    try:
        token_response = requests.post(
            f"{HYDRA_PUBLIC_URL}/oauth2/token",
            auth=auth,
            data=token_data
        )
        
        if token_response.status_code == 200:
            tokens = token_response.json()
            print("\n=== Client Credentials Token ===")
            print(f"Access Token: {tokens['access_token']}")
            print(f"Expires in: {tokens['expires_in']} seconds")
            print("====================\n")
            return tokens['access_token']
        else:
            print(f"Failed to get token: {token_response.text}")
            return None
    except Exception as e:
        print(f"Exception while getting token: {str(e)}")
        return None

def main():
    # Create unique identifiers for testing
    timestamp = int(time.time())
    email = f"test-user-{timestamp}@example.com"
    password = f"Unique$Complex{timestamp}P@ssw0rd"
    
    # Print these first in case of errors later
    print("\n=== User Credentials ===")
    print(f"User email: {email}")
    print(f"User password: {password}")
    print("========================\n")
    
    # Test connectivity first
    try:
        print("Testing connection to Kratos admin API...")
        response = requests.get(f"{KRATOS_ADMIN_URL}/health/ready")
        print(f"Kratos health check response: {response.status_code}")
        
        print("Testing connection to Hydra admin API...")
        response = requests.get(f"{HYDRA_ADMIN_URL}/health/ready")
        print(f"Hydra health check response: {response.status_code}")
    except Exception as e:
        print(f"Connectivity test failed: {str(e)}")
        sys.exit(1)
    
    # Create Hydra client
    client_id, client_secret = create_hydra_client()
    if not client_id or not client_secret:
        return
    
    # Create user in Kratos
    user_id = create_user_admin(email, password)
    if not user_id:
        return
    
    # Get client credentials token
    client_token = get_client_credentials_token(client_id, client_secret)
    if not client_token:
        return
    
    print("\nComplete setup done successfully!")
    print(f"User ID: {user_id}")
    print(f"\nLog in at http://localhost:3000 with:")
    print(f"Email: {email}")
    print(f"Password: {password}")

if __name__ == "__main__":
    main()
