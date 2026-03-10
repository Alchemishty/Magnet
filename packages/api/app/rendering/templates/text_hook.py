"""Text hook template — animated text on a colored background."""

from PIL import Image, ImageDraw

from app.rendering.templates.base import _load_font, frames_to_video


class TextHookRenderer:
    """Renders animated text on a solid background for hook scenes."""

    def generate_frames(
        self,
        params: dict,
        duration: float,
        resolution: tuple[int, int],
        fps: int,
    ) -> list[Image.Image]:
        text = params.get("text")
        if not text:
            raise ValueError("'text' is required in params")

        font_path = params.get("font")
        font_size = params.get("font_size", 72)
        bg_color = params.get("bg_color", (0, 0, 0))
        text_color = params.get("text_color", (255, 255, 255))
        animation = params.get("animation", "fade_in")

        width, height = resolution
        font = _load_font(font_path, font_size)
        total_frames = int(duration * fps)
        frames: list[Image.Image] = []

        for i in range(total_frames):
            progress = i / max(total_frames - 1, 1)
            frame = Image.new("RGB", (width, height), bg_color)
            draw = ImageDraw.Draw(frame)

            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            x = (width - text_w) // 2
            y_center = (height - text_h) // 2

            if animation == "fade_in":
                alpha = int(255 * min(progress * 3, 1.0))
                color = (*text_color[:3], alpha) if len(text_color) >= 3 else text_color
                txt_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
                txt_draw = ImageDraw.Draw(txt_layer)
                txt_draw.text((x, y_center), text, font=font, fill=color)
                frame = frame.convert("RGBA")
                frame = Image.alpha_composite(frame, txt_layer)
                frame = frame.convert("RGB")
            elif animation == "slide_up":
                offset = int((1 - min(progress * 3, 1.0)) * height * 0.3)
                draw.text(
                    (x, y_center + offset), text, font=font, fill=text_color
                )
            else:
                draw.text((x, y_center), text, font=font, fill=text_color)

            frames.append(frame)

        return frames

    def render(
        self,
        params: dict,
        duration: float,
        resolution: tuple[int, int],
        fps: int,
    ) -> bytes:
        frames = self.generate_frames(params, duration, resolution, fps)
        return frames_to_video(frames, fps, resolution)
