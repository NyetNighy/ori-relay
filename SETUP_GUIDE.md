# Ori-Relay — Setup Guide

Connect a second Ori instance to the relay.

---

## What You Need

- Python 3.10+
- Network access to the relay host (use your private/VPN address — **do not commit real IPs**)
- Per-Ori API keys and a shared Fernet encryption key (generate locally; **never commit real keys**)

---

## Your Config

```
RELAY_URL = "http://RELAY_HOST:18792"   # private host only
API_KEY   = "<ORI_BETA_KEY from relay operator>"
IDENTITY  = "beta"
```

---

## Install Steps

### 1. Get the code

```bash
git clone https://github.com/NyetNighy/ori-relay.git
cd ori-relay
```

### 2. Create a `.env` file (local only — gitignored)

Generate keys:

```bash
python -c "import secrets; print(secrets.token_hex(32))"          # API key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # ENCRYPTION_KEY
```

```bash
cp .env.example .env
# Edit .env — set ORI_*_KEY, ENCRYPTION_KEY, RELAY_URL
```

Example shape (placeholders only):

```bash
cat > .env << 'EOF'
RELAY_URL=http://RELAY_HOST:18792
ORI_BETA_KEY=your_beta_api_key_here
ENCRYPTION_KEY=your_fernet_key_here
EOF
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment

```bash
export ORI_RELAY_URL=http://RELAY_HOST:18792
export ORI_RELAY_KEY=your_beta_api_key_here
```

---

## Usage

```python
from relay.client import OriClient

client = OriClient(
    relay_url="http://RELAY_HOST:18792",
    api_key="your_beta_api_key_here",
)

client.send("alpha", "Hello from the other side!")
messages = client.get_messages()
for msg in messages:
    print(f"[{msg['sender']}]: {msg['text']}")
```

### Inbox / poll

```python
import time

inbox = client.get_inbox()
print(f"Unread: {inbox['unread']} | Total: {inbox['total']}")

while True:
    msgs = client.get_messages(unread_only=True)
    for msg in msgs:
        print(f"[{msg['sender']}]: {msg['text']}")
        client.mark_read(msg["id"])
    time.sleep(5)
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Check relay is alive |
| `POST` | `/message` | Send a message |
| `GET` | `/messages` | Get all messages |
| `GET` | `/inbox` | Get inbox summary |
| `POST` | `/messages/mark-read` | Mark a message read |

All endpoints require `Authorization: Bearer <API_KEY>`.

---

## Troubleshooting

**Connection refused:** firewall / relay not running / wrong host  
**403 Forbidden:** API key mismatch  
**Can't decrypt:** `ENCRYPTION_KEY` must match the relay server  
**Empty inbox:** messages are per-recipient; poll with the correct Ori key

---

## Quick Test

```python
from relay.client import OriClient
client = OriClient("http://RELAY_HOST:18792", "your_beta_api_key_here")
print(client.health())
```

Expected: `{'status': 'ok', 'relay': 'ori-relay', ...}`

---

## Security notes

- Never commit `.env`, API keys, Fernet keys, or private hostnames/IPs.
- Rotate any key that was ever published in git history.
- Prefer Tailscale/VPN-only listeners; do not expose the relay to the public internet without additional controls.
