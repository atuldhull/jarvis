"""JARVIS — live conversational voice (LiveKit): turn-taking, interruptions, streamed speech.

Runs entirely locally on your mic + speakers — no LiveKit server or cloud account needed:

    py jarvis_live.py console

LiveKit handles the natural-conversation layer (voice-activity detection, turn detection,
barge-in / interruptions, audio streaming). JARVIS's own brain (memory + specialist
departments + task-based key routing + multilingual replies) and voice (Sarvam/Piper) are
plugged in via voice/livekit_adapters.py — so you keep everything we built.
"""

import sys

sys.stdout.reconfigure(encoding="utf-8")

from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli
from livekit.plugins import silero

from agents.orchestrator import Orchestrator
from voice.livekit_adapters import JarvisSTT, JarvisLLM, JarvisTTS


async def entrypoint(ctx: JobContext):
    await ctx.connect()
    ears = JarvisSTT()
    session = AgentSession(
        vad=silero.VAD.load(),         # local voice-activity detection (free)
        stt=ears,
        llm=JarvisLLM(Orchestrator(), ears),
        tts=JarvisTTS(),
    )
    await session.start(
        agent=Agent(instructions="You are JARVIS. Your real persona and brain are the orchestrator."),
        room=ctx.room,
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
