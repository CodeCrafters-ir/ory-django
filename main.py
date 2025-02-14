import aiohttp
import asyncio
from typing import Optional, Dict, Any


class OryAuth:
    def __init__(self, public_url: str = "http://localhost:4444"):
        self.public_url = public_url
        self.client_id = "test-client"
        self.client_secret = "test-secret"

    async def generate_token(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        url = f"{self.public_url}/oauth2/token"
        data = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": username,
            "password": password,
            "scope": "openid offline",
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    print(f"Error generating token: {response.status} - {error}")
                    return None

    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        url = f"{self.public_url}/oauth2/token"
        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    print(f"Error refreshing token: {response.status} - {error}")
                    return None

    async def invalidate_token(self, token: str) -> bool:
        url = f"{self.public_url}/oauth2/revoke"
        data = {"token": token}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data, headers=headers) as response:
                return response.status == 200

    async def check_token(self, token: str) -> Optional[Dict[str, Any]]:
        url = f"{self.public_url}/oauth2/introspect"
        data = {"token": token}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    print(f"Error checking token: {response.status} - {error}")
                    return None


async def main():
    ory_auth = OryAuth()

    # Example credentials (replace with actual values)
    username = "user@example.com"
    password = "password"

    # Generate token
    token = await ory_auth.generate_token(username, password)
    if not token:
        print("Failed to generate token")
        return

    print("Token generated:", token["access_token"])

    # Refresh token
    refreshed_token = await ory_auth.refresh_token(token["refresh_token"])
    if refreshed_token:
        print("Refreshed token:", refreshed_token["access_token"])

    # Check token
    token_info = await ory_auth.check_token(token["access_token"])
    if token_info:
        print("Token active:", token_info.get("active", False))

    # Invalidate token
    if await ory_auth.invalidate_token(token["access_token"]):
        print("Token invalidated")


if __name__ == "__main__":
    asyncio.run(main())
