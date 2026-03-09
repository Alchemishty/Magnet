"""Verify all expected API routes are registered on the app."""

from app.main import app

EXPECTED_PATHS = [
    "/api/projects",
    "/api/projects/{project_id}",
    "/api/projects/{project_id}/game-profile",
    "/api/projects/{project_id}/briefs",
    "/api/projects/{project_id}/concepts",
    "/api/briefs/{brief_id}",
    "/api/projects/{project_id}/assets",
    "/api/assets/{asset_id}",
    "/api/briefs/{brief_id}/jobs",
    "/api/jobs/{job_id}",
    "/health",
]


def _registered_paths() -> set[str]:
    return {route.path for route in app.routes if hasattr(route, "path")}


def test_all_expected_paths_registered():
    registered = _registered_paths()
    for path in EXPECTED_PATHS:
        assert path in registered, f"Missing route: {path}"


def test_no_duplicate_route_paths():
    seen = set()
    for route in app.routes:
        if not hasattr(route, "methods"):
            continue
        for method in route.methods:
            key = (route.path, method)
            assert key not in seen, f"Duplicate: {method} {route.path}"
            seen.add(key)
