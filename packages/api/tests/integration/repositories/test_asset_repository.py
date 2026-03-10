import pytest

from app.repositories.asset_repository import AssetRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.user_repository import UserRepository
from app.schemas.asset import AssetCreate, AssetUpdate
from app.schemas.project import ProjectCreate
from app.schemas.user import UserCreate


@pytest.mark.integration
class TestAssetRepositoryIntegration:
    def _create_user_and_project(self, db_session):
        user_repo = UserRepository(db_session)
        user = user_repo.create_from_schema(
            UserCreate(
                email=f"asset-user-{id(db_session)}@example.com",
                name="Asset User",
            )
        )
        project_repo = ProjectRepository(db_session)
        project = project_repo.create_from_schema(
            ProjectCreate(name="Asset Game", user_id=user.id)
        )
        return user, project

    def test_create_and_get_by_id(self, db_session):
        _, project = self._create_user_and_project(db_session)
        repo = AssetRepository(db_session)

        asset = repo.create_from_schema(
            AssetCreate(
                project_id=project.id,
                asset_type="gameplay",
                s3_key="uploads/test.mp4",
                filename="test.mp4",
            )
        )

        assert asset.id is not None
        fetched = repo.get_by_id(asset.id)
        assert fetched is not None
        assert fetched.filename == "test.mp4"

    def test_list_by_project_all(self, db_session):
        _, project = self._create_user_and_project(db_session)
        repo = AssetRepository(db_session)

        repo.create_from_schema(
            AssetCreate(
                project_id=project.id,
                asset_type="gameplay",
                s3_key="uploads/a.mp4",
                filename="a.mp4",
            )
        )
        repo.create_from_schema(
            AssetCreate(
                project_id=project.id,
                asset_type="logo",
                s3_key="uploads/b.png",
                filename="b.png",
            )
        )

        assets = repo.list_by_project(project.id)

        assert len(assets) == 2

    def test_list_by_project_filtered_by_type(self, db_session):
        _, project = self._create_user_and_project(db_session)
        repo = AssetRepository(db_session)

        repo.create_from_schema(
            AssetCreate(
                project_id=project.id,
                asset_type="gameplay",
                s3_key="uploads/a.mp4",
                filename="a.mp4",
            )
        )
        repo.create_from_schema(
            AssetCreate(
                project_id=project.id,
                asset_type="logo",
                s3_key="uploads/b.png",
                filename="b.png",
            )
        )

        assets = repo.list_by_project(project.id, asset_type="logo")

        assert len(assets) == 1
        assert assets[0].asset_type == "logo"

    def test_update_asset(self, db_session):
        _, project = self._create_user_and_project(db_session)
        repo = AssetRepository(db_session)

        asset = repo.create_from_schema(
            AssetCreate(
                project_id=project.id,
                asset_type="gameplay",
                s3_key="uploads/test.mp4",
                filename="test.mp4",
            )
        )

        updated = repo.update_from_schema(asset.id, AssetUpdate(size_bytes=2048))

        assert updated is not None
        assert updated.size_bytes == 2048

    def test_delete_asset(self, db_session):
        _, project = self._create_user_and_project(db_session)
        repo = AssetRepository(db_session)

        asset = repo.create_from_schema(
            AssetCreate(
                project_id=project.id,
                asset_type="gameplay",
                s3_key="uploads/del.mp4",
                filename="del.mp4",
            )
        )

        result = repo.delete(asset.id)

        assert result is True
        assert repo.get_by_id(asset.id) is None
