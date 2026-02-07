# Patient Intake Token Server

This lightweight FastAPI server issues LiveKit access tokens for the demo UI.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../agent/.env.example .env
```

Ensure the following are set in `.env`:

- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `LIVEKIT_DEFAULT_ROOM` (optional)

## Run

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

The UI can request tokens from `http://localhost:8000/token?identity=<name>`.
