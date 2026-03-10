"""Image provider factory."""

from app.providers.image.stub import StubImageProvider


def get_image_provider() -> StubImageProvider:
    """Create an image provider instance.

    Currently only the stub provider is available.
    Future: read IMAGE_PROVIDER env var to select real implementations.
    """
    return StubImageProvider()
