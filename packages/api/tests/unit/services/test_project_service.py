"""Unit tests for ProjectService."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.errors import NotFoundError, ValidationError
from app.schemas.project import (
    GameProfileCreate,
    GameProfileUpdate,
    ProjectCreate,
    ProjectUpdate,
)
from app.services.project_service import ProjectService

MODULE = "app.services.project_service"


# ── helpers ──────────────────────────────────────────────────────────


def _make_service(mock_project_repo_cls, mock_profile_repo_cls):
    """Build a ProjectService with mocked repository classes."""
    session = MagicMock()
    service = ProjectService(session)
    return (
        service,
        mock_project_repo_cls.return_value,
        mock_profile_repo_cls.return_value,
    )


# ── create_project ───────────────────────────────────────────────────


@patch(f"{MODULE}.GameProfileRepository")
@patch(f"{MODULE}.ProjectRepository")
def test_create_project(mock_proj_repo, mock_prof_repo):
    service, proj_repo, _ = _make_service(mock_proj_repo, mock_prof_repo)
    mock_project = MagicMock()
    proj_repo.create_from_schema.return_value = mock_project

    data = ProjectCreate(name="My Game", user_id=uuid4())
    result = service.create_project(data)

    assert result == mock_project
    proj_repo.create_from_schema.assert_called_once_with(data)


# ── get_project ──────────────────────────────────────────────────────


@patch(f"{MODULE}.GameProfileRepository")
@patch(f"{MODULE}.ProjectRepository")
def test_get_project_found(mock_proj_repo, mock_prof_repo):
    service, proj_repo, _ = _make_service(mock_proj_repo, mock_prof_repo)
    mock_project = MagicMock()
    project_id = uuid4()
    proj_repo.get_by_id.return_value = mock_project

    result = service.get_project(project_id)

    assert result == mock_project
    proj_repo.get_by_id.assert_called_once_with(project_id)


@patch(f"{MODULE}.GameProfileRepository")
@patch(f"{MODULE}.ProjectRepository")
def test_get_project_not_found(mock_proj_repo, mock_prof_repo):
    service, proj_repo, _ = _make_service(mock_proj_repo, mock_prof_repo)
    project_id = uuid4()
    proj_repo.get_by_id.return_value = None

    with pytest.raises(NotFoundError) as exc_info:
        service.get_project(project_id)

    assert exc_info.value.entity_name == "Project"
    assert exc_info.value.entity_id == project_id


# ── list_projects ────────────────────────────────────────────────────


@patch(f"{MODULE}.GameProfileRepository")
@patch(f"{MODULE}.ProjectRepository")
def test_list_projects(mock_proj_repo, mock_prof_repo):
    service, proj_repo, _ = _make_service(mock_proj_repo, mock_prof_repo)
    mock_list = [MagicMock(), MagicMock()]
    user_id = uuid4()
    proj_repo.list_by_user.return_value = mock_list

    result = service.list_projects(user_id, offset=10, limit=50)

    assert result == mock_list
    proj_repo.list_by_user.assert_called_once_with(user_id, offset=10, limit=50)


@patch(f"{MODULE}.GameProfileRepository")
@patch(f"{MODULE}.ProjectRepository")
def test_list_projects_defaults(mock_proj_repo, mock_prof_repo):
    service, proj_repo, _ = _make_service(mock_proj_repo, mock_prof_repo)
    user_id = uuid4()
    proj_repo.list_by_user.return_value = []

    service.list_projects(user_id)

    proj_repo.list_by_user.assert_called_once_with(user_id, offset=0, limit=100)


# ── update_project ───────────────────────────────────────────────────


@patch(f"{MODULE}.GameProfileRepository")
@patch(f"{MODULE}.ProjectRepository")
def test_update_project(mock_proj_repo, mock_prof_repo):
    service, proj_repo, _ = _make_service(mock_proj_repo, mock_prof_repo)
    mock_project = MagicMock()
    project_id = uuid4()
    proj_repo.update_from_schema.return_value = mock_project

    data = ProjectUpdate(name="New Name")
    result = service.update_project(project_id, data)

    assert result == mock_project
    proj_repo.update_from_schema.assert_called_once_with(project_id, data)


@patch(f"{MODULE}.GameProfileRepository")
@patch(f"{MODULE}.ProjectRepository")
def test_update_project_not_found(mock_proj_repo, mock_prof_repo):
    service, proj_repo, _ = _make_service(mock_proj_repo, mock_prof_repo)
    project_id = uuid4()
    proj_repo.update_from_schema.return_value = None

    with pytest.raises(NotFoundError) as exc_info:
        service.update_project(project_id, ProjectUpdate(name="X"))

    assert exc_info.value.entity_name == "Project"
    assert exc_info.value.entity_id == project_id


# ── delete_project ───────────────────────────────────────────────────


@patch(f"{MODULE}.GameProfileRepository")
@patch(f"{MODULE}.ProjectRepository")
def test_delete_project(mock_proj_repo, mock_prof_repo):
    service, proj_repo, _ = _make_service(mock_proj_repo, mock_prof_repo)
    project_id = uuid4()
    proj_repo.delete.return_value = True

    service.delete_project(project_id)

    proj_repo.delete.assert_called_once_with(project_id)


@patch(f"{MODULE}.GameProfileRepository")
@patch(f"{MODULE}.ProjectRepository")
def test_delete_project_not_found(mock_proj_repo, mock_prof_repo):
    service, proj_repo, _ = _make_service(mock_proj_repo, mock_prof_repo)
    project_id = uuid4()
    proj_repo.delete.return_value = False

    with pytest.raises(NotFoundError) as exc_info:
        service.delete_project(project_id)

    assert exc_info.value.entity_name == "Project"
    assert exc_info.value.entity_id == project_id


# ── create_game_profile ──────────────────────────────────────────────


@patch(f"{MODULE}.GameProfileRepository")
@patch(f"{MODULE}.ProjectRepository")
def test_create_game_profile(mock_proj_repo, mock_prof_repo):
    service, proj_repo, prof_repo = _make_service(mock_proj_repo, mock_prof_repo)
    project_id = uuid4()
    proj_repo.get_by_id.return_value = MagicMock()  # project exists
    prof_repo.get_by_project_id.return_value = None  # no existing profile
    mock_profile = MagicMock()
    prof_repo.create_from_schema.return_value = mock_profile

    data = GameProfileCreate(project_id=project_id, genre="RPG")
    result = service.create_game_profile(data)

    assert result == mock_profile
    proj_repo.get_by_id.assert_called_once_with(project_id)
    prof_repo.create_from_schema.assert_called_once_with(data)


@patch(f"{MODULE}.GameProfileRepository")
@patch(f"{MODULE}.ProjectRepository")
def test_create_game_profile_project_not_found(mock_proj_repo, mock_prof_repo):
    service, proj_repo, prof_repo = _make_service(mock_proj_repo, mock_prof_repo)
    project_id = uuid4()
    proj_repo.get_by_id.return_value = None

    data = GameProfileCreate(project_id=project_id, genre="RPG")

    with pytest.raises(NotFoundError) as exc_info:
        service.create_game_profile(data)

    assert exc_info.value.entity_name == "Project"
    assert exc_info.value.entity_id == project_id
    prof_repo.create_from_schema.assert_not_called()


@patch(f"{MODULE}.GameProfileRepository")
@patch(f"{MODULE}.ProjectRepository")
def test_create_game_profile_duplicate(mock_proj_repo, mock_prof_repo):
    service, proj_repo, prof_repo = _make_service(
        mock_proj_repo, mock_prof_repo
    )
    project_id = uuid4()
    proj_repo.get_by_id.return_value = MagicMock()
    prof_repo.get_by_project_id.return_value = MagicMock()  # exists

    data = GameProfileCreate(project_id=project_id, genre="RPG")

    with pytest.raises(ValidationError):
        service.create_game_profile(data)

    prof_repo.create_from_schema.assert_not_called()


# ── get_game_profile ─────────────────────────────────────────────────


@patch(f"{MODULE}.GameProfileRepository")
@patch(f"{MODULE}.ProjectRepository")
def test_get_game_profile(mock_proj_repo, mock_prof_repo):
    service, _, prof_repo = _make_service(mock_proj_repo, mock_prof_repo)
    project_id = uuid4()
    mock_profile = MagicMock()
    prof_repo.get_by_project_id.return_value = mock_profile

    result = service.get_game_profile(project_id)

    assert result == mock_profile
    prof_repo.get_by_project_id.assert_called_once_with(project_id)


@patch(f"{MODULE}.GameProfileRepository")
@patch(f"{MODULE}.ProjectRepository")
def test_get_game_profile_not_found(mock_proj_repo, mock_prof_repo):
    service, _, prof_repo = _make_service(mock_proj_repo, mock_prof_repo)
    project_id = uuid4()
    prof_repo.get_by_project_id.return_value = None

    with pytest.raises(NotFoundError) as exc_info:
        service.get_game_profile(project_id)

    assert exc_info.value.entity_name == "GameProfile"
    assert exc_info.value.entity_id == project_id


# ── update_game_profile ──────────────────────────────────────────────


@patch(f"{MODULE}.GameProfileRepository")
@patch(f"{MODULE}.ProjectRepository")
def test_update_game_profile(mock_proj_repo, mock_prof_repo):
    service, _, prof_repo = _make_service(mock_proj_repo, mock_prof_repo)
    project_id = uuid4()
    mock_profile = MagicMock()
    mock_profile.id = uuid4()
    prof_repo.get_by_project_id.return_value = mock_profile
    updated_profile = MagicMock()
    prof_repo.update_from_schema.return_value = updated_profile

    data = GameProfileUpdate(genre="Strategy")
    result = service.update_game_profile(project_id, data)

    assert result == updated_profile
    prof_repo.get_by_project_id.assert_called_once_with(project_id)
    prof_repo.update_from_schema.assert_called_once_with(mock_profile.id, data)


@patch(f"{MODULE}.GameProfileRepository")
@patch(f"{MODULE}.ProjectRepository")
def test_update_game_profile_not_found(mock_proj_repo, mock_prof_repo):
    service, _, prof_repo = _make_service(mock_proj_repo, mock_prof_repo)
    project_id = uuid4()
    prof_repo.get_by_project_id.return_value = None

    with pytest.raises(NotFoundError) as exc_info:
        service.update_game_profile(project_id, GameProfileUpdate(genre="X"))

    assert exc_info.value.entity_name == "GameProfile"
    assert exc_info.value.entity_id == project_id
    prof_repo.update_from_schema.assert_not_called()
