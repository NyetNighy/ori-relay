"""
Ori-Relay — Secure message relay for Ori-to-Ori communication.
"""
import os
import json
import time
import uuid
import secrets
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from cryptography.fernet import Fernet
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# === Config ===
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "").encode()
ALPHA_KEY = os.getenv("ORI_ALPHA_KEY", "")
BETA_KEY = os.getenv("ORI_BETA_KEY", "")

ALLOWED_KEYS = {ALPHA_KEY, BETA_KEY} - {""}

fernet = Fernet(ENCRYPTION_KEY) if ENCRYPTION_KEY else None


# === Helpers ===
def encrypt(plaintext: str) -> str:
    if not fernet:
        return plaintext
    return fernet.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    if not fernet:
        return ciphertext
    return fernet.decrypt(ciphertext.encode()).decode()


def get_inbox_path(api_key: str) -> Path:
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
    return DATA_DIR / f"inbox_{key_hash}.json"


def load_inbox(api_key: str) -> list:
    path = get_inbox_path(api_key)
    if not path.exists():
        return []
    try:
        raw = path.read_text()
        if fernet:
            raw = decrypt(raw)
        return json.loads(raw)
    except Exception:
        return []


def save_inbox(api_key: str, messages: list):
    path = get_inbox_path(api_key)
    raw = json.dumps(messages)
    if fernet:
        raw = encrypt(raw)
    path.write_text(raw)


def get_identity(api_key: str) -> str:
    """Name this Ori based on which key it matches."""
    if api_key == ALPHA_KEY:
        return "alpha"
    if api_key == BETA_KEY:
        return "beta"
    return "unknown"


# === Pydantic models ===
class MessageIn(BaseModel):
    recipient: str  # "alpha" or "beta"
    text: str
    metadata: Optional[dict] = None


class MessageOut(BaseModel):
    id: str
    sender: str
    recipient: str
    text: str
    timestamp: str
    read: bool
    metadata: Optional[dict] = None


class DeliveryReport(BaseModel):
    delivered: bool
    recipient: str
    message_id: str


# === FastAPI app ===
app = FastAPI(title="Ori-Relay")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_key(authorization: str) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")
    token = authorization[7:]
    if token not in ALLOWED_KEYS:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return token


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "relay": "ori-relay",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ori_instances": len(ALLOWED_KEYS),
    }


@app.post("/message", response_model=DeliveryReport)
async def send_message(message: MessageIn, authorization: str = Header(...)):
    api_key = verify_key(authorization)
    sender = get_identity(api_key)

    if message.recipient not in ("alpha", "beta"):
        raise HTTPException(status_code=400, detail="Invalid recipient")

    # Build the message
    msg = {
        "id": str(uuid.uuid4()),
        "sender": sender,
        "recipient": message.recipient,
        "text": message.text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "read": False,
        "metadata": message.metadata or {},
    }

    # Write to recipient's inbox
    recipient_key = ALPHA_KEY if message.recipient == "alpha" else BETA_KEY
    if recipient_key:
        recipient_inbox = load_inbox(recipient_key)
        recipient_inbox.insert(0, msg)  # Prepend for newest-first
        save_inbox(recipient_key, recipient_inbox)

    return DeliveryReport(
        delivered=True,
        recipient=message.recipient,
        message_id=msg["id"],
    )


@app.get("/messages", response_model=list[MessageOut])
async def get_messages(authorization: str = Header(...), unread_only: bool = False):
    api_key = verify_key(authorization)
    inbox = load_inbox(api_key)
    messages = inbox

    if unread_only:
        messages = [m for m in messages if not m.get("read", False)]

    # Mark retrieved unread messages as read
    if unread_only:
        for m in messages:
            m["read"] = True
        save_inbox(api_key, inbox)

    return messages


@app.get("/inbox")
async def get_inbox(authorization: str = Header(...)):
    api_key = verify_key(authorization)
    inbox = load_inbox(api_key)
    unread = [m for m in inbox if not m.get("read", False)]
    return {
        "total": len(inbox),
        "unread": len(unread),
        "latest": inbox[0] if inbox else None,
    }


@app.post("/messages/mark-read")
async def mark_read(message_id: str, authorization: str = Header(...)):
    api_key = verify_key(authorization)
    inbox = load_inbox(api_key)
    for m in inbox:
        if m["id"] == message_id:
            m["read"] = True
            save_inbox(api_key, inbox)
            return {"ok": True}
    raise HTTPException(status_code=404, detail="Message not found")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("RELAY_PORT", "18792"))
    host = os.getenv("RELAY_HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)