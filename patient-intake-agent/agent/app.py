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


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect(auto_subscribe=True)

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


if __name__ == "__main__":
    load_dotenv()

    required = ["LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET", "OPENAI_API_KEY"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}")

    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
