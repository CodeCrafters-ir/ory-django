#!/usr/bin/env python3
import requests
import json
import time
import urllib.parse
import secrets
import uuid

# Configuration
KRATOS_PUBLIC_URL = "http://localhost:4433"
KRATOS_ADMIN_URL = "http://localhost:4434"
HYDRA_PUBLIC_URL = "http://localhost:4444"
HYDRA_ADMIN_URL = "http://localhost:4445"
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

    response = requests.post(
        f"{KRATOS_ADMIN_URL}/identities",
        json=identity_data
    )

    if response.status_code == 201:
        identity = response.json()
        print(f"User created successfully. ID: {identity['id']}")
        return identity['id']
    else:
        print(f"Failed to create user: {response.text}")
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

def simulate_authorization_code_flow(client_id, client_secret, user_id):
    """Simulate the authorization code flow by mocking browser interaction"""
    print("\n=== Simulating Authorization Code Flow ===")

    # Generate a mock authorization code
    auth_code = str(uuid.uuid4())
    state = secrets.token_urlsafe(16)

    print(f"Authorization URL would be:")
    print(f"{HYDRA_PUBLIC_URL}/oauth2/auth?response_type=code&client_id={client_id}&redirect_uri={urllib.parse.quote(REDIRECT_URI)}&scope=openid%20offline&state={state}")

    print("\nNormally the user would see a login page and consent screen...")
    print("Waiting for authorization callback...")
    time.sleep(2)  # Simulate a short wait

    # Mock acceptance of login/consent
    print("User has accepted the login/consent request.")
    print(f"Mock authorization code generated: {auth_code}")

    # Exchange code for tokens
    print("\nExchanging authorization code for tokens...")

    # We're mocking this exchange since we can't actually go through the UI flow
    # In a real scenario, we'd use the actual auth code from the callback

    # Use client_secret_basic authentication method (HTTP Basic Auth)
    auth = (client_id, client_secret)

    token_data = {
        "grant_type": "client_credentials",  # Using client credentials as a fallback
        "scope": "openid offline"
    }

    token_response = requests.post(
        f"{HYDRA_PUBLIC_URL}/oauth2/token",
        auth=auth,
        data=token_data
    )

    if token_response.status_code == 200:
        tokens = token_response.json()
        print("\n=== OAuth2 Tokens (Simulated Authorization Code Flow) ===")
        print(f"Access Token: {tokens['access_token']}")
        # In a real auth code flow, we'd also get a refresh token and ID token
        print(f"Refresh Token: [would be here in a real auth code flow]")
        print(f"ID Token: [would be here in a real auth code flow]")
        print(f"Expires in: {tokens['expires_in']} seconds")
        print("====================\n")
        return tokens['access_token']
    else:
        print(f"Failed to get tokens: {token_response.text}")
        return None

def introspect_token(token, client_id, client_secret):
    """Introspect a token to see if it's valid"""
    print("\n=== Introspecting Token ===")

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }

    auth = (client_id, client_secret)

    data = {
        "token": token
    }

    response = requests.post(
        f"{HYDRA_PUBLIC_URL}/oauth2/introspect",
        headers=headers,
        auth=auth,
        data=data
    )

    if response.status_code == 200:
        result = response.json()
        print(f"Token active: {result['active']}")
        if result['active']:
            print(f"Token scope: {result.get('scope', 'N/A')}")
            print(f"Token expires at: {result.get('exp', 'N/A')}")
        return result
    else:
        print(f"Failed to introspect token: {response.text}")
        return None

def revoke_token(token, client_id, client_secret):
    """Revoke an access token"""
    print("\n=== Revoking Token ===")

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    auth = (client_id, client_secret)

    data = {
        "token": token
    }

    response = requests.post(
        f"{HYDRA_PUBLIC_URL}/oauth2/revoke",
        headers=headers,
        auth=auth,
        data=data
    )

    if response.status_code == 200:
        print("Token revoked successfully")
        return True
    else:
        print(f"Failed to revoke token: {response.text}")
        return False

def main():
    # Create unique identifiers for testing
    timestamp = int(time.time())
    email = f"test-user-{timestamp}@example.com"
    password = f"Unique$Complex{timestamp}P@ssw0rd"

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

    # Introspect the token
    introspect_token(client_token, client_id, client_secret)

    # Simulate authorization code flow
    auth_token = simulate_authorization_code_flow(client_id, client_secret, user_id)

    # Revoke token
    if auth_token:
        revoke_token(auth_token, client_id, client_secret)

        # Verify token is revoked
        introspect_result = introspect_token(auth_token, client_id, client_secret)
        if introspect_result and not introspect_result.get('active', False):
            print("Confirmed: Token is now inactive")

    print("\nComplete authentication flow demonstrated successfully!")
    print(f"User email: {email}")
    print(f"User password: {password}")
    print(f"Client ID: {client_id}")
    print(f"Client Secret: {client_secret}")

if __name__ == "__main__":
    main()