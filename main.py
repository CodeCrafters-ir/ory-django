#!/usr/bin/env python3
import requests
import json
import time
import urllib.parse
import secrets
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Configuration
KRATOS_PUBLIC_URL = "http://localhost:4433"
KRATOS_ADMIN_URL = "http://localhost:4434"
HYDRA_PUBLIC_URL = "http://localhost:4444"
HYDRA_ADMIN_URL = "http://localhost:4445"
REDIRECT_URI = "http://localhost:8000/callback"
CLIENT_ID = None  # Will be set after client creation
CLIENT_SECRET = None  # Will be set after client creation
STATE = secrets.token_urlsafe(16)
CODE_VERIFIER = secrets.token_urlsafe(64)

# Store tokens
tokens = {}
auth_code = None
callback_received = threading.Event()

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        if self.path.startswith('/callback'):
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)

            if 'code' in params:
                auth_code = params['code'][0]
                self.wfile.write(b"<html><body><h1>Authorization successful!</h1><p>You can close this window now.</p></body></html>")
                callback_received.set()
            else:
                self.wfile.write(b"<html><body><h1>Authorization failed!</h1></body></html>")
        else:
            self.wfile.write(b"<html><body><h1>Unknown endpoint</h1></body></html>")

def start_callback_server():
    server = HTTPServer(('localhost', 8000), CallbackHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    return server

def create_hydra_client():
    global CLIENT_ID, CLIENT_SECRET

    print("Creating OAuth2 client in Hydra...")
    client_data = {
        "grant_types": ["authorization_code", "refresh_token"],
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
        client_info = response.json()
        CLIENT_ID = client_info["client_id"]
        CLIENT_SECRET = client_info["client_secret"]
        print(f"Client created successfully. ID: {CLIENT_ID}")
        return True
    else:
        print(f"Failed to create client: {response.text}")
        return False

def create_kratos_user(email, password):
    print(f"Creating user with email: {email}...")
    print(f"Creating user with password: {password}...")

    # Get registration flow
    flow_response = requests.get(f"{KRATOS_PUBLIC_URL}/self-service/registration/api")
    if flow_response.status_code != 200:
        print(f"Failed to initialize registration flow: {flow_response.text}")
        return False

    flow = flow_response.json()
    flow_id = flow["id"]

    # Extract CSRF token if present
    csrf_token = None
    for node in flow["ui"]["nodes"]:
        if node["attributes"].get("name") == "csrf_token":
            csrf_token = node["attributes"].get("value")
            break

    # Complete registration
    registration_data = {
        "method": "password",
        "password": password,
        "traits": {
            "email": email,
            "name": {
                "first": "Test",
                "last": "User"
            }
        }
    }

    # Add CSRF token if found
    if csrf_token:
        registration_data["csrf_token"] = csrf_token

    register_response = requests.post(
        f"{KRATOS_PUBLIC_URL}/self-service/registration?flow={flow_id}",
        json=registration_data
    )

    if register_response.status_code == 200:
        user_data = register_response.json()
        print(f"User created successfully. ID: {user_data['identity']['id']}")
        return user_data["session_token"]
    else:
        print(f"Failed to create user: {register_response.text}")
        return False

def login_kratos_user(email, password):
    print(f"Logging in user with email: {email}...")

    # Get login flow
    flow_response = requests.get(f"{KRATOS_PUBLIC_URL}/self-service/login/api")
    if flow_response.status_code != 200:
        print(f"Failed to initialize login flow: {flow_response.text}")
        return False

    flow = flow_response.json()
    flow_id = flow["id"]

    # Extract CSRF token if present
    csrf_token = None
    for node in flow["ui"]["nodes"]:
        if node["attributes"].get("name") == "csrf_token":
            csrf_token = node["attributes"].get("value")
            break

    # Complete login
    login_data = {
        "method": "password",
        "password": password,
        "identifier": email,
    }

    # Add CSRF token if found
    if csrf_token:
        login_data["csrf_token"] = csrf_token

    login_response = requests.post(
        f"{KRATOS_PUBLIC_URL}/self-service/login?flow={flow_id}",
        json=login_data
    )

    if login_response.status_code == 200:
        session_data = login_response.json()
        print(f"User logged in successfully.")
        return session_data["session_token"]
    else:
        print(f"Failed to login: {login_response.text}")
        return False

def get_oauth_tokens(session_token):
    global auth_code

    # Start callback server
    server = start_callback_server()

    print("Starting OAuth2 flow...")

    # Create authorization URL
    auth_url = (
        f"{HYDRA_PUBLIC_URL}/oauth2/auth"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
        f"&scope=openid%20offline"
        f"&state={STATE}"
        f"&code_challenge_method=plain"
        f"&code_challenge={CODE_VERIFIER}"
    )

    # Open browser for authorization
    print(f"Opening browser for authorization: {auth_url}")
    webbrowser.open(auth_url)

    # Wait for callback
    print("Waiting for authorization callback...")
    callback_received.wait(timeout=60)

    if not auth_code:
        print("No authorization code received!")
        server.shutdown()
        return False

    print(f"Authorization code received: {auth_code}")

    # Exchange code for tokens
    token_data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code_verifier": CODE_VERIFIER
    }

    token_response = requests.post(
        f"{HYDRA_PUBLIC_URL}/oauth2/token",
        data=token_data
    )

    server.shutdown()

    if token_response.status_code == 200:
        tokens = token_response.json()
        print("\n=== OAuth2 Tokens ===")
        print(f"Access Token: {tokens['access_token']}")
        print(f"Refresh Token: {tokens['refresh_token']}")
        print(f"ID Token: {tokens['id_token']}")
        print(f"Expires in: {tokens['expires_in']} seconds")
        print("====================\n")
        return tokens
    else:
        print(f"Failed to get tokens: {token_response.text}")
        return False

def refresh_access_token(refresh_token):
    print("Refreshing access token...")

    refresh_data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }

    refresh_response = requests.post(
        f"{HYDRA_PUBLIC_URL}/oauth2/token",
        data=refresh_data
    )

    if refresh_response.status_code == 200:
        new_tokens = refresh_response.json()
        print("\n=== Refreshed OAuth2 Tokens ===")
        print(f"New Access Token: {new_tokens['access_token']}")
        print(f"New Refresh Token: {new_tokens['refresh_token']}")
        print(f"Expires in: {new_tokens['expires_in']} seconds")
        print("============================\n")
        return new_tokens
    else:
        print(f"Failed to refresh token: {refresh_response.text}")
        return False

def logout(token):
    print("Logging out...")

    logout_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "token": token
    }

    logout_response = requests.post(
        f"{HYDRA_PUBLIC_URL}/oauth2/revoke",
        data=logout_data
    )

    if logout_response.status_code == 200:
        print("Successfully logged out")
        return True
    else:
        print(f"Failed to logout: {logout_response.text}")
        return False

def create_kratos_user_admin(email, password):
    """
    Alternative method to create user via admin API
    """
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
        print(f"User created successfully via admin API. ID: {identity['id']}")
        return True
    else:
        print(f"Failed to create user via admin API: {response.text}")
        return False

def main():
    # Create a unique email for testing
    timestamp = int(time.time())
    email = f"test-user-{timestamp}@example.com"
    # Using a more complex password that's unlikely to be in breach databases
    password = f"Unique$Complex{timestamp}P@ssw0rd"

    # Create Hydra client
    if not create_hydra_client():
        return

    # Create user in Kratos
    session_token = create_kratos_user(email, password)
    if not session_token:
        # Try creating via admin API
        print("Trying admin API for user creation...")
        if create_kratos_user_admin(email, password):
            # After admin creation, we need to log in to get a session
            session_token = login_kratos_user(email, password)
            if not session_token:
                return
        else:
            return

    # Get OAuth2 tokens
    tokens = get_oauth_tokens(session_token)
    if not tokens:
        return

    # Refresh token
    time.sleep(2)  # Wait a bit before refreshing
    new_tokens = refresh_access_token(tokens["refresh_token"])
    if not new_tokens:
        return

    # Logout
    logout(new_tokens["access_token"])

if __name__ == "__main__":
    main()