"""Video Agent: PLAN -> PREPARE -> ASSEMBLE -> POST-PROCESS pipeline."""

from pydantic import ValidationError

from app.providers.base import ImageProvider, MusicProvider, TTSProvider
from app.repositories.asset_repository import AssetRepository
from app.schemas.brief import BriefRead
from app.schemas.execution_plan import ExecutionPlan, PreparedAudio, PreparedScene
from app.schemas.scene_plan import ScenePlan


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
