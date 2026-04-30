"""
Ori-Relay client library.
Usage:
    from client import OriClient
    client = OriClient("https://kali-ip:18792", "your_api_key")
    client.send("beta", "Hello from alpha!")
    messages = client.get_messages()
"""
import requests
from typing import Optional


class OriClient:
    def __init__(self, relay_url: str, api_key: str):
        self.url = relay_url.rstrip("/")
        self.key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"}

    def send(self, recipient: str, text: str, metadata: Optional[dict] = None) -> dict:
        """Send a message to another Ori."""
        resp = requests.post(
            f"{self.url}/message",
            json={"recipient": recipient, "text": text, "metadata": metadata},
            headers=self.headers,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def get_messages(self, unread_only: bool = False) -> list:
        """Retrieve messages for this Ori."""
        params = {"unread_only": "1"} if unread_only else {}
        resp = requests.get(
            f"{self.url}/messages",
            params=params,
            headers=self.headers,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def get_inbox(self) -> dict:
        """Get inbox summary."""
        resp = requests.get(
            f"{self.url}/inbox",
            headers=self.headers,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def mark_read(self, message_id: str) -> dict:
        """Mark a message as read."""
        resp = requests.post(
            f"{self.url}/messages/mark-read?message_id={message_id}",
            headers=self.headers,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def health(self) -> dict:
        """Check relay health."""
        resp = requests.get(f"{self.url}/health", timeout=5)
        resp.raise_for_status()
        return resp.json()