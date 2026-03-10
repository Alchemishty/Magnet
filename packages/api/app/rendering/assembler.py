"""FFmpeg assembler — builds and runs FFmpeg commands from Composition JSON."""

import subprocess

from app.schemas.composition import Composition


class AssemblerError(Exception):
    """Raised when FFmpeg assembly fails."""


def assemble(
    composition: Composition,
    asset_map: dict[str, str],
    output_path: str,
) -> str:
    """Assemble a video from a Composition and prepared asset files.

    Args:
        composition: The layered timeline description.
        asset_map: Maps asset_id references to local file paths.
        output_path: Where to write the final MP4.

    Returns:
        The output_path on success.

    Raises:
        AssemblerError: If an asset is missing or FFmpeg fails.
    """
    video_layers = [ly for ly in composition.layers if ly.type == "video"]
    audio_layers = [ly for ly in composition.layers if ly.type == "audio"]
    text_layers = [ly for ly in composition.layers if ly.type == "text"]
    image_layers = [ly for ly in composition.layers if ly.type == "image"]

    cmd: list[str] = ["ffmpeg", "-y"]
    input_indices: dict[str, int] = {}
    idx = 0

    for layer in video_layers + image_layers + audio_layers:
        if layer.asset_id and layer.asset_id not in asset_map:
            raise AssemblerError(
                f"Asset '{layer.asset_id}' not found in asset_map"
            )
        if layer.asset_id:
            path = asset_map[layer.asset_id]
            if path not in input_indices:
                cmd.extend(["-i", path])
                input_indices[path] = idx
                idx += 1

    width, height = composition.resolution
    filter_parts: list[str] = []
    current_video = None

    if not video_layers and not image_layers:
        cmd.extend([
            "-f", "lavfi",
            "-i",
            f"color=c=black:s={width}x{height}"
            f":d={composition.duration}:r={composition.fps}",
        ])
        current_video = f"[{idx}:v]"
        idx += 1

    for i, layer in enumerate(video_layers):
        path = asset_map[layer.asset_id]
        in_idx = input_indices[path]
        stream = f"[{in_idx}:v]"

        if layer.trim:
            start, end = layer.trim
            trim_label = f"[vtrim{i}]"
            filter_parts.append(
                f"{stream}trim=start={start}:end={end},setpts=PTS-STARTPTS,"
                f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2{trim_label}"
            )
            stream = trim_label
        else:
            scale_label = f"[vscale{i}]"
            filter_parts.append(
                f"{stream}scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2{scale_label}"
            )
            stream = scale_label

        if current_video is None:
            current_video = stream
        else:
            out_label = f"[vcat{i}]"
            filter_parts.append(
                f"{current_video}{stream}concat=n=2:v=1:a=0{out_label}"
            )
            current_video = out_label

    for i, layer in enumerate(image_layers):
        path = asset_map[layer.asset_id]
        in_idx = input_indices[path]
        dur = layer.end - layer.start
        img_label = f"[img{i}]"
        filter_parts.append(
            f"[{in_idx}:v]loop=loop=-1:size=1:start=0,"
            f"setpts=PTS-STARTPTS,"
            f"trim=duration={dur},"
            f"scale={width}:{height}:"
            f"force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
            f"{img_label}"
        )
        if current_video is None:
            current_video = img_label
        else:
            out_label = f"[imgcat{i}]"
            filter_parts.append(
                f"{current_video}{img_label}"
                f"concat=n=2:v=1:a=0{out_label}"
            )
            current_video = out_label

    for i, layer in enumerate(text_layers):
        if current_video is None:
            continue
        text = layer.content or ""
        escaped = text.replace("'", "'\\''").replace(":", "\\:")
        x, y = _resolve_text_position(layer.position, width, height)
        enable = f"between(t,{layer.start},{layer.end})"
        out_label = f"[txt{i}]"
        filter_parts.append(
            f"{current_video}drawtext=text='{escaped}':"
            f"fontsize=64:fontcolor=white:"
            f"x={x}:y={y}:enable='{enable}'{out_label}"
        )
        current_video = out_label

    audio_streams: list[str] = []
    for i, layer in enumerate(audio_layers):
        path = asset_map[layer.asset_id]
        in_idx = input_indices[path]
        vol = layer.volume if layer.volume is not None else 1.0
        alabel = f"[a{i}]"
        filter_parts.append(f"[{in_idx}:a]volume={vol}{alabel}")
        audio_streams.append(alabel)

    final_audio = None
    if audio_streams:
        if len(audio_streams) == 1:
            final_audio = audio_streams[0]
        else:
            final_audio = "[aout]"
            filter_parts.append(
                f"{''.join(audio_streams)}amix=inputs={len(audio_streams)}"
                f":duration=longest{final_audio}"
            )

    if filter_parts:
        cmd.extend(["-filter_complex", ";".join(filter_parts)])
        if current_video:
            cmd.extend(["-map", current_video])
        if final_audio:
            cmd.extend(["-map", final_audio])

    cmd.extend([
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "ultrafast",
        "-r", str(composition.fps),
        "-t", str(composition.duration),
        "-f", "mp4",
        output_path,
    ])

    result = subprocess.run(cmd, capture_output=True, timeout=300)

    if result.returncode != 0:
        error_msg = result.stderr.decode(errors="replace").strip()
        raise AssemblerError(f"FFmpeg failed: {error_msg}")

    return output_path


def probe_duration(file_path: str) -> float:
    """Get the duration of a media file using ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path,
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=30)
    if result.returncode != 0:
        error_msg = result.stderr.decode(errors="replace").strip()
        raise AssemblerError(f"ffprobe failed for {file_path}: {error_msg}")
    return float(result.stdout.decode().strip())


def _resolve_text_position(
    position: list[int] | str | None,
    width: int,
    height: int,
) -> tuple[str, str]:
    """Convert position spec to FFmpeg x/y expressions."""
    if isinstance(position, list) and len(position) == 2:
        return str(position[0]), str(position[1])

    positions = {
        "top_center": ("(w-text_w)/2", "h*0.1"),
        "center": ("(w-text_w)/2", "(h-text_h)/2"),
        "bottom_center": ("(w-text_w)/2", "h*0.85"),
        "top_left": ("w*0.05", "h*0.1"),
        "top_right": ("w*0.95-text_w", "h*0.1"),
    }

    key = position if isinstance(position, str) else "center"
    return positions.get(key, positions["center"])
