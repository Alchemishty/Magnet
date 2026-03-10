"""Music provider factory."""

from app.providers.music.stub import StubMusicProvider


def get_music_provider() -> StubMusicProvider:
    """Create a music provider instance.

    Currently only the stub provider is available.
    Future: read MUSIC_PROVIDER env var to select real implementations.
    """
    return StubMusicProvider()
