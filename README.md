# Ori-Relay

A tiny secure message relay for Ori-to-Ori communication.

## Overview

Two Ori instances (on different machines) communicate via a relay server. The relay runs on this machine (Kali/100.75.11.44). Each Ori instance has its own API key. Messages are encrypted at rest with a shared symmetric key.

## Quick Start

```bash
# Install dependencies
pip install fastapi uvicorn cryptography

# Configure keys (replace with real values)
cp .env.example .env
# Edit .env with your keys

# Run
uvicorn relay.main:app --host 0.0.0.0 --port 18792
```

## Architecture

- **POST /message** — send a message to a recipient
- **GET /messages** — retrieve messages for this Ori
- **GET /inbox** — list conversations
- **GET /health** — health check

All endpoints require `Authorization: Bearer <api_key>`.

## Security

- Per-Ori API keys (env vars, never in code)
- Messages encrypted at rest (Fernet)
- Each Ori can only read its own inbox
- Timestamps and sender IDs on every message