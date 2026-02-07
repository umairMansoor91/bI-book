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
- `EHR_API_URL` (optional, enables intake handoff to EHR)
- `EHR_API_TOKEN` (optional, bearer token for EHR API)
- `EHR_PAYLOAD_FORMAT` (optional, `fhir` or `raw`, defaults to `fhir`)
- `INTAKE_STORAGE_PATH` (optional, defaults to `./intake_submissions.json`)
- `INTAKE_QUEUE_PATH` (optional, defaults to `./intake_queue.jsonl`)

## Intake payloads

Send patient-provided fields over the LiveKit data channel as:

```json
{ "type": "intake.update", "fields": { "name": "Jordan Lee", "dob": "1991-03-14" } }
```

The agent stores these fields locally and forwards them to the EHR endpoint if configured.
Set `EHR_PAYLOAD_FORMAT=raw` to send the raw intake submission payload or leave the default
`fhir` to emit a basic FHIR Bundle.
Failed EHR deliveries are queued in `INTAKE_QUEUE_PATH` and retried periodically.
