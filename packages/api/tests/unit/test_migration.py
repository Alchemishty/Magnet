"""Structural tests for database schema and migration."""

from pathlib import Path


class TestMigrationSetup:
    def test_migration_file_exists(self):
        migration = Path("alembic/versions/001_create_initial_tables.py")

        assert migration.exists()

    def test_alembic_ini_exists(self):
        assert Path("alembic.ini").exists()

    def test_alembic_env_exists(self):
        assert Path("alembic/env.py").exists()

    def test_all_tables_in_metadata(self):
        from app.models import Base

        table_names = set(Base.metadata.tables.keys())
        expected = {
            "users",
            "projects",
            "game_profiles",
            "assets",
            "creative_briefs",
            "render_jobs",
        }

        assert expected == table_names

    def test_foreign_keys_exist(self):
        from app.models import Base

        tables = Base.metadata.tables

        projects_fks = {str(fk.column) for fk in tables["projects"].foreign_keys}
        assert "users.id" in projects_fks

        profiles_fks = {str(fk.column) for fk in tables["game_profiles"].foreign_keys}
        assert "projects.id" in profiles_fks

        assets_fks = {str(fk.column) for fk in tables["assets"].foreign_keys}
        assert "projects.id" in assets_fks

        briefs_fks = {str(fk.column) for fk in tables["creative_briefs"].foreign_keys}
        assert "projects.id" in briefs_fks

        jobs_fks = {str(fk.column) for fk in tables["render_jobs"].foreign_keys}
        assert "creative_briefs.id" in jobs_fks

    def test_indexes_on_foreign_keys(self):
        from app.models import Base

        tables = Base.metadata.tables

        asset_indexes = {idx.name for idx in tables["assets"].indexes}
        assert any("project_id" in n for n in asset_indexes)

        brief_indexes = {idx.name for idx in tables["creative_briefs"].indexes}
        assert any("project_id" in n for n in brief_indexes)

        job_indexes = {idx.name for idx in tables["render_jobs"].indexes}
        assert any("brief_id" in n for n in job_indexes)
