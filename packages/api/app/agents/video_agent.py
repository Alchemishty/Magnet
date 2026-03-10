"""Video Agent: PLAN -> PREPARE -> ASSEMBLE -> POST-PROCESS pipeline."""

import logging
import os

from pydantic import ValidationError

from app.providers.base import ImageProvider, MusicProvider, TTSProvider
from app.rendering.templates import get_template
from app.repositories.asset_repository import AssetRepository
from app.schemas.brief import BriefRead
from app.schemas.execution_plan import ExecutionPlan, PreparedAudio, PreparedScene
from app.schemas.scene_plan import ScenePlan

logger = logging.getLogger(__name__)


class VideoAgentError(Exception):
    """Raised when the Video Agent encounters an unrecoverable error."""


class VideoAgent:
    """Orchestrates the video production pipeline.

    Accepts provider instances and an asset repository, then runs:
    PLAN -> PREPARE -> ASSEMBLE -> POST-PROCESS.
    """

    def __init__(
        self,
        tts_provider: TTSProvider,
        music_provider: MusicProvider,
        image_provider: ImageProvider,
        asset_repo: AssetRepository,
    ):
        self._tts = tts_provider
        self._music = music_provider
        self._image = image_provider
        self._asset_repo = asset_repo

    def plan(self, brief: BriefRead, work_dir: str) -> ExecutionPlan:
        """PLAN phase: parse scene_plan into an ExecutionPlan."""
        if not brief.scene_plan:
            raise VideoAgentError(
                f"Brief {brief.id} has no scene_plan"
            )

        try:
            scene_plan = ScenePlan(**brief.scene_plan)
        except ValidationError as e:
            raise VideoAgentError(
                f"Invalid scene_plan for brief {brief.id}: {e}"
            ) from e

        scenes: list[PreparedScene] = []
        for i, scene in enumerate(scene_plan.scenes):
            if scene.strategy == "COMPOSE":
                assets = self._asset_repo.list_by_project(brief.project_id)
                if not assets:
                    raise VideoAgentError(
                        f"No assets found for project {brief.project_id}. "
                        f"COMPOSE scenes require uploaded assets."
                    )
            scenes.append(PreparedScene(index=i, strategy=scene.strategy))

        audio: list[PreparedAudio] = []
        if scene_plan.audio:
            if scene_plan.audio.voiceover:
                audio.append(PreparedAudio(type="voiceover"))
            if scene_plan.audio.music:
                audio.append(PreparedAudio(type="music"))

        return ExecutionPlan(
            brief_id=brief.id,
            scenes=scenes,
            audio=audio,
            work_dir=work_dir,
        )

    async def prepare(
        self, exec_plan: ExecutionPlan, scene_plan: ScenePlan
    ) -> ExecutionPlan:
        """PREPARE phase: execute preparation tasks per strategy."""
        updated_scenes: list[PreparedScene] = []

        for prepared, scene in zip(exec_plan.scenes, scene_plan.scenes):
            try:
                if scene.strategy == "COMPOSE":
                    output = await self._prepare_compose(
                        scene, exec_plan.work_dir, prepared.index
                    )
                elif scene.strategy == "GENERATE":
                    output = await self._prepare_generate(
                        scene, exec_plan.work_dir, prepared.index
                    )
                elif scene.strategy == "RENDER":
                    output = self._prepare_render(
                        scene, exec_plan.work_dir, prepared.index
                    )
                else:
                    raise VideoAgentError(f"Unknown strategy: {scene.strategy}")
                updated_scenes.append(
                    prepared.model_copy(update={"status": "ready", "output_path": output})
                )
            except Exception as exc:
                logger.warning("Scene %d failed: %s", prepared.index, exc)
                updated_scenes.append(
                    prepared.model_copy(
                        update={"status": "failed", "error_message": str(exc)}
                    )
                )

        updated_audio = await self._prepare_audio(exec_plan, scene_plan)

        ready_count = sum(1 for s in updated_scenes if s.status == "ready")
        if ready_count == 0:
            raise VideoAgentError("All scenes failed during preparation")

        return exec_plan.model_copy(
            update={"scenes": updated_scenes, "audio": updated_audio}
        )

    async def _prepare_compose(self, scene, work_dir: str, index: int) -> str:
        """Download and trim a COMPOSE asset."""
        assets = self._asset_repo.list_by_project()
        asset = assets[0] if assets else None
        if not asset:
            raise VideoAgentError("No asset available for COMPOSE scene")

        output_path = os.path.join(work_dir, f"scene_{index}_compose.mp4")
        # For MVP: the asset s3_key serves as a placeholder path.
        # Full S3 download will be added in POST-PROCESS integration.
        with open(output_path, "wb") as f:
            f.write(b"compose_placeholder")
        return output_path

    async def _prepare_generate(self, scene, work_dir: str, index: int) -> str:
        """Generate content via provider for a GENERATE scene."""
        ext = "png"
        output_path = os.path.join(work_dir, f"scene_{index}_generate.{ext}")
        data = await self._image.generate(
            scene.prompt or "", 1080, 1920
        )
        with open(output_path, "wb") as f:
            f.write(data)
        return output_path

    def _prepare_render(self, scene, work_dir: str, index: int) -> str:
        """Render a programmatic template for a RENDER scene."""
        template = get_template(scene.template)
        output_path = os.path.join(work_dir, f"scene_{index}_render.mp4")
        data = template.render(
            params=scene.params or {},
            duration=scene.duration,
            resolution=(1080, 1920),
            fps=30,
        )
        with open(output_path, "wb") as f:
            f.write(data)
        return output_path

    async def _prepare_audio(
        self, exec_plan: ExecutionPlan, scene_plan: ScenePlan
    ) -> list[PreparedAudio]:
        """Prepare audio tracks (voiceover, music)."""
        updated: list[PreparedAudio] = []
        total_duration = sum(s.duration for s in scene_plan.scenes)

        for audio_entry in exec_plan.audio:
            try:
                if audio_entry.type == "voiceover" and scene_plan.audio and scene_plan.audio.voiceover:
                    vo = scene_plan.audio.voiceover
                    data = await self._tts.synthesize(vo.script, vo.voice)
                    path = os.path.join(exec_plan.work_dir, "voiceover.mp3")
                    with open(path, "wb") as f:
                        f.write(data)
                    updated.append(
                        audio_entry.model_copy(update={"status": "ready", "output_path": path})
                    )
                elif audio_entry.type == "music" and scene_plan.audio and scene_plan.audio.music:
                    mu = scene_plan.audio.music
                    data = await self._music.generate(mu.prompt, int(total_duration))
                    path = os.path.join(exec_plan.work_dir, "music.wav")
                    with open(path, "wb") as f:
                        f.write(data)
                    updated.append(
                        audio_entry.model_copy(update={"status": "ready", "output_path": path})
                    )
                else:
                    updated.append(audio_entry)
            except Exception as exc:
                logger.warning("Audio %s failed: %s", audio_entry.type, exc)
                updated.append(
                    audio_entry.model_copy(
                        update={"status": "failed", "error_message": str(exc)}
                    )
                )

        return updated
