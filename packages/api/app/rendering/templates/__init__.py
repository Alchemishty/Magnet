"""Template registry for programmatic scene renderers."""

from app.rendering.templates.endcard import EndcardRenderer
from app.rendering.templates.text_hook import TextHookRenderer

TEMPLATE_REGISTRY: dict = {
    "text_hook": TextHookRenderer(),
    "endcard": EndcardRenderer(),
}


def get_template(name: str):
    """Look up a template renderer by name."""
    if name not in TEMPLATE_REGISTRY:
        raise ValueError(
            f"Unknown template '{name}'. "
            f"Available: {sorted(TEMPLATE_REGISTRY)}"
        )
    return TEMPLATE_REGISTRY[name]
