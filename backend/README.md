# Backend (FastAPI + Python)

This is the backend for the AI Energy Switcher app.

## Features

- REST API for voice and provider research
- WebSocket for real-time conversation
- Integrations: LiveKit.io, OpenAI Whisper, Check24

## Tech Stack

- FastAPI
- Python 3.10+
- WebSockets
- Asyncio

## Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## Development

- API routes: `app/api/`
- Core logic: `app/core/`
- Models: `app/models/`
- Services: `app/services/`
- Utilities: `app/utils/`
