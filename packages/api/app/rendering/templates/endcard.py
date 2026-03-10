"""Endcard template — CTA text and game name on a colored background."""

from PIL import Image, ImageDraw

from app.rendering.templates.base import _load_font, frames_to_video


class EndcardRenderer:
    """Renders a static endcard with CTA text and optional game name."""

    def generate_frames(
        self,
        params: dict,
        duration: float,
        resolution: tuple[int, int],
        fps: int,
    ) -> list[Image.Image]:
        cta_text = params.get("cta_text")
        if not cta_text:
            raise ValueError("'cta_text' is required in params")

        font_path = params.get("font")
        bg_color = params.get("bg_color", (20, 20, 30))
        text_color = (255, 255, 255)
        game_name = params.get("game_name")

        width, height = resolution
        cta_font = _load_font(font_path, 64)
        name_font = _load_font(font_path, 48)
        total_frames = max(1, int(duration * fps))

        base = Image.new("RGB", (width, height), bg_color)
        draw = ImageDraw.Draw(base)

        cta_bbox = draw.textbbox((0, 0), cta_text, font=cta_font)
        cta_w = cta_bbox[2] - cta_bbox[0]
        cta_x = (width - cta_w) // 2
        cta_y = int(height * 0.6)
        draw.text((cta_x, cta_y), cta_text, font=cta_font, fill=text_color)

        if game_name:
            name_bbox = draw.textbbox((0, 0), game_name, font=name_font)
            name_w = name_bbox[2] - name_bbox[0]
            name_x = (width - name_w) // 2
            name_y = int(height * 0.35)
            draw.text(
                (name_x, name_y), game_name, font=name_font, fill=text_color
            )

        return [base.copy() for _ in range(total_frames)]

    def render(
        self,
        params: dict,
        duration: float,
        resolution: tuple[int, int],
        fps: int,
    ) -> bytes:
        frames = self.generate_frames(params, duration, resolution, fps)
        return frames_to_video(frames, fps, resolution)
