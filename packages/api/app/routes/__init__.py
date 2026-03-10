from app.routes.assets import router as assets_router
from app.routes.briefs import router as briefs_router
from app.routes.jobs import router as jobs_router
from app.routes.projects import router as projects_router
from app.routes.ws import router as ws_router

__all__ = [
    "assets_router",
    "briefs_router",
    "jobs_router",
    "projects_router",
    "ws_router",
]
