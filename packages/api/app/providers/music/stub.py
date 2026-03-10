"""Stub music provider — generates silent WAV audio."""

import wave
from io import BytesIO


class StubMusicProvider:
    """MusicProvider stub that returns silent WAV audio of the requested duration."""

    async def generate(self, prompt: str, duration: int) -> bytes:
        sample_rate = 44100
        num_frames = sample_rate * duration
        buf = BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(b"\x00\x00" * num_frames)
        return buf.getvalue()

    async def aclose(self) -> None:
        pass
