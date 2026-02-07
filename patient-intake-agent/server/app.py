import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from livekit import api

load_dotenv()

app = FastAPI(title="Patient Intake Token Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/token")
async def create_token(identity: str, room: Optional[str] = None) -> dict:
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    if not api_key or not api_secret:
        raise HTTPException(status_code=500, detail="Missing LiveKit API credentials")

    room_name = room or os.getenv("LIVEKIT_DEFAULT_ROOM", "intake-demo")
    grants = api.VideoGrants(room_join=True, room=room_name)
    token = (
        api.AccessToken(api_key, api_secret)
        .with_identity(identity)
        .with_name(identity)
        .with_grants(grants)
        .to_jwt()
    )
    return {"token": token, "room": room_name}
