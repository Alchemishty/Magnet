"""Base template renderer with shared frame-to-video encoding."""

import subprocess
from typing import Protocol

from PIL import Image


class TemplateRenderer(Protocol):
    def generate_frames(
        self,
        params: dict,
        duration: float,
        resolution: tuple[int, int],
        fps: int,
    ) -> list[Image.Image]: ...

    def render(
        self,
        params: dict,
        duration: float,
        resolution: tuple[int, int],
        fps: int,
    ) -> bytes: ...


def frames_to_video(
    frames: list[Image.Image],
    fps: int,
    resolution: tuple[int, int],
) -> bytes:
    """Pipe PIL Image frames through FFmpeg to produce MP4 bytes."""
    width, height = resolution
    cmd = [
        "ffmpeg",
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{width}x{height}",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "pipe:0",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "ultrafast",
        "-f", "mp4",
        "-movflags", "frag_keyframe+empty_moov",
        "pipe:1",
    ]

    raw_bytes = b""
    for frame in frames:
        rgb = frame.convert("RGB").resize((width, height))
        raw_bytes += rgb.tobytes()

    result = subprocess.run(
        cmd,
        input=raw_bytes,
        capture_output=True,
        timeout=60,
    )

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {result.stderr.decode()}")

    return result.stdout


def _load_font(font_path: str | None, font_size: int):
    """Load a TTF font or fall back to PIL default."""
    from PIL import ImageFont

    if font_path:
        try:
            return ImageFont.truetype(font_path, font_size)
        except OSError:
            pass
    return ImageFont.load_default(size=font_size)
