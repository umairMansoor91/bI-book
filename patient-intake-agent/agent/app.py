import asyncio
import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import requests
import os

from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import VoicePipelineAgent
from livekit.plugins import deepgram, openai, silero

INTAKE_PROMPT = """You are a patient intake assistant for a clinic demo.
Your goals:
1. Greet the patient and ask for their full name and date of birth.
2. Ask for their chief complaint and symptom duration.
3. Confirm allergies and current medications.
4. Ask for consent to share the intake summary with the clinician.
5. Provide a concise summary at the end.
Be empathetic, avoid medical diagnosis, and keep responses brief.
"""

INTAKE_STORAGE_ENV = "INTAKE_STORAGE_PATH"
DEFAULT_STORAGE_PATH = "./intake_submissions.json"
INTAKE_QUEUE_ENV = "INTAKE_QUEUE_PATH"
DEFAULT_QUEUE_PATH = "./intake_queue.jsonl"
EHR_FORMAT_ENV = "EHR_PAYLOAD_FORMAT"
DEFAULT_EHR_FORMAT = "fhir"
MAX_EHR_RETRIES = 3
RETRY_BACKOFF_SECONDS = 1.5


@dataclass
class IntakeSubmission:
    created_at: float
    participant_id: Optional[str]
    participant_identity: Optional[str]
    fields: Dict[str, Any] = field(default_factory=dict)


def load_storage_path() -> Path:
    return Path(os.getenv(INTAKE_STORAGE_ENV, DEFAULT_STORAGE_PATH))


def load_queue_path() -> Path:
    return Path(os.getenv(INTAKE_QUEUE_ENV, DEFAULT_QUEUE_PATH))


def safe_load_json_list(storage_path: Path) -> list[Dict[str, Any]]:
    if not storage_path.exists():
        return []
    try:
        existing = json.loads(storage_path.read_text())
        if isinstance(existing, list):
            return existing
    except json.JSONDecodeError:
        pass
    backup_path = storage_path.with_suffix(f".corrupt.{int(time.time())}.json")
    storage_path.rename(backup_path)
    return []


def persist_submission(submission: IntakeSubmission) -> None:
    storage_path = load_storage_path()
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    existing = safe_load_json_list(storage_path)
    existing.append(asdict(submission))
    storage_path.write_text(json.dumps(existing, indent=2))


def payload_for_ehr(submission: IntakeSubmission) -> Dict[str, Any]:
    payload_format = os.getenv(EHR_FORMAT_ENV, DEFAULT_EHR_FORMAT).lower()
    if payload_format == "raw":
        return asdict(submission)
    patient_name = submission.fields.get("name") or submission.fields.get("full_name")
    dob = submission.fields.get("dob") or submission.fields.get("date_of_birth")
    observations = []
    for key, value in submission.fields.items():
        if key in {"name", "full_name", "dob", "date_of_birth"}:
            continue
        observations.append(
            {
                "resourceType": "Observation",
                "status": "final",
                "code": {"text": key},
                "valueString": str(value),
            }
        )
    patient_resource = {
        "resourceType": "Patient",
        "id": submission.participant_id or "unknown",
        "name": [{"text": patient_name}] if patient_name else [],
        "birthDate": dob,
    }
    return {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [{"resource": patient_resource}] + [
            {"resource": obs} for obs in observations
        ],
    }


def send_to_ehr(submission: IntakeSubmission) -> None:
    ehr_url = os.getenv("EHR_API_URL")
    if not ehr_url:
        return
    token = os.getenv("EHR_API_TOKEN")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.post(
        ehr_url, json=payload_for_ehr(submission), headers=headers, timeout=10
    )
    response.raise_for_status()


def append_to_queue(submission: IntakeSubmission) -> None:
    queue_path = load_queue_path()
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(asdict(submission))
    with queue_path.open("a", encoding="utf-8") as handle:
        handle.write(payload + "\n")


def flush_queue() -> None:
    queue_path = load_queue_path()
    if not queue_path.exists():
        return
    remaining: list[str] = []
    for line in queue_path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            submission = IntakeSubmission(**data)
            send_with_retry(submission)
        except Exception:
            remaining.append(line)
    if remaining:
        queue_path.write_text("\n".join(remaining) + "\n")
    else:
        queue_path.unlink()


def send_with_retry(submission: IntakeSubmission) -> None:
    for attempt in range(1, MAX_EHR_RETRIES + 1):
        try:
            send_to_ehr(submission)
            return
        except requests.RequestException as exc:
            if attempt == MAX_EHR_RETRIES:
                raise exc
            time.sleep(RETRY_BACKOFF_SECONDS * attempt)


def save_and_send(submission: IntakeSubmission) -> None:
    persist_submission(submission)
    try:
        send_with_retry(submission)
    except requests.RequestException as exc:
        append_to_queue(submission)
        print(f"Failed to send intake to EHR: {exc}")


def parse_intake_payload(raw_payload: bytes) -> Optional[Tuple[str, Dict[str, Any]]]:
    try:
        payload = json.loads(raw_payload.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    payload_type = payload.get("type")
    if payload_type not in {"intake.update", "intake.replace", "intake.clear"}:
        return None
    fields = payload.get("fields")
    if not isinstance(fields, dict):
        return None
    return payload_type, fields


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect(auto_subscribe=True)

    intake_fields: Dict[str, Any] = {}
    current_participant: Dict[str, Optional[str]] = {"id": None, "identity": None}
    loop = asyncio.get_running_loop()

    def schedule_save() -> None:
        if not intake_fields:
            return
        submission = IntakeSubmission(
            created_at=time.time(),
            participant_id=current_participant["id"],
            participant_identity=current_participant["identity"],
            fields=dict(intake_fields),
        )
        loop.run_in_executor(None, save_and_send, submission)

    def handle_data(packet: Any) -> None:
        raw_payload = getattr(packet, "data", None)
        if raw_payload is None:
            return
        parsed = parse_intake_payload(raw_payload)
        if not parsed:
            return
        payload_type, fields = parsed
        if payload_type == "intake.replace":
            intake_fields.clear()
            intake_fields.update(fields)
        elif payload_type == "intake.clear":
            for key in fields.keys():
                intake_fields.pop(key, None)
        else:
            intake_fields.update(fields)
        participant = getattr(packet, "participant", None)
        if participant:
            current_participant["id"] = getattr(participant, "sid", None)
            current_participant["identity"] = getattr(participant, "identity", None)
        schedule_save()

    if hasattr(ctx.room, "on"):
        try:
            ctx.room.on("data_received", handle_data)
        except TypeError:
            pass

    agent = VoicePipelineAgent(
        vad=silero.VAD.load(),
        stt=deepgram.STT(),
        llm=openai.LLM(model="gpt-4o-mini", temperature=0.2),
        tts=openai.TTS(),
        system_prompt=INTAKE_PROMPT,
    )

    agent.start(ctx.room)
    await agent.say(
        "Hi, I'm the clinic intake assistant. I can help collect a few quick details to share with the clinician."
    )

    loop.run_in_executor(None, flush_queue)

    async def periodic_flush() -> None:
        while True:
            await asyncio.sleep(30)
            loop.run_in_executor(None, flush_queue)

    flush_task = asyncio.create_task(periodic_flush())
    await ctx.room.wait_for_disconnect()
    flush_task.cancel()

    if intake_fields:
        schedule_save()
    loop.run_in_executor(None, flush_queue)


if __name__ == "__main__":
    load_dotenv()

    required = ["LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET", "OPENAI_API_KEY"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}")

    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
