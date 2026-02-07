# Patient Intake Demo (LiveKit Agent + React UI)

This repo contains a demo **patient intake agent** built on LiveKit Agents alongside a **React-based UI** for a sample clinic intake flow.

## Contents

- `agent/` — LiveKit Agent worker for voice/text intake and routing.
- `ui/` — React UI for patient details, symptoms, and consent capture.
- `server/` — Token server for issuing LiveKit access tokens to the UI.

## Quick start

1. **Agent**
   ```bash
   cd agent
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   python app.py
   ```

2. **UI**
   ```bash
   cd ui
   npm install
   npm run dev
   ```

3. **Token server (optional)**
   ```bash
   cd server
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn app:app --host 0.0.0.0 --port 8000
   ```

## Notes

- This is a demo-only project and does not store PHI.
- Update `.env` files with your LiveKit credentials and OpenAI/ASR provider keys.
- The agent listens for LiveKit data channel payloads of the form:
  ```json
  { "type": "intake.update", "fields": { "name": "Jordan Lee", "dob": "1991-03-14" } }
  ```
  `type` can be `intake.update`, `intake.replace`, or `intake.clear`.
  Collected fields are persisted to `INTAKE_STORAGE_PATH`, queued in `INTAKE_QUEUE_PATH` on failure,
  and sent to `EHR_API_URL` (FHIR by default) if configured.
