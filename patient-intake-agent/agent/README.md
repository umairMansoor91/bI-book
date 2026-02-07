# LiveKit Patient Intake Agent

This worker connects to a LiveKit room and runs a voice-based patient intake flow.

## Features

- Collects patient demographics and chief complaint
- Confirms consent and privacy disclaimer
- Summarizes intake to the clinician

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

## Environment variables

- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `OPENAI_API_KEY`
- `DEEPGRAM_API_KEY` (optional)
