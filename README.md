# Ori-Relay

A tiny secure message relay for Ori-to-Ori communication.

## Overview

Two Ori instances (on different machines) communicate via a relay server. Each Ori instance has its own API key. Messages are encrypted at rest with a shared symmetric key.

**Do not put real API keys, encryption keys, or private host addresses in this repository.** Use `.env` (see `.env.example`).

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt
# or: pip install fastapi uvicorn cryptography

# Configure keys (local only)
cp .env.example .env
# Edit .env with generated keys — never commit .env

# Run
uvicorn relay.main:app --host 0.0.0.0 --port 18792
```

Generate secrets:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Architecture

- **POST /message** — send a message to a recipient
- **GET /messages** — retrieve messages for this Ori
- **GET /inbox** — list conversations
- **GET /health** — health check

All endpoints require `Authorization: Bearer <api_key>`.

## Security

- Per-Ori API keys (env vars, never in code or docs as real values)
- Messages encrypted at rest (Fernet)
- Each Ori can only read its own inbox
- Timestamps and sender IDs on every message
- Rotate keys if they were ever exposed in git history or chat

## Setup for a second Ori

See [SETUP_GUIDE.md](SETUP_GUIDE.md) (placeholders only).
