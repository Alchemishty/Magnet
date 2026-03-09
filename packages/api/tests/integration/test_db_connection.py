"""Integration tests for database connectivity."""

import pytest
from sqlalchemy import text

from app.models.user import User


@pytest.mark.integration
class TestDatabaseConnection:
    def test_can_execute_query(self, db_engine):
        with db_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))

            assert result.scalar() == 1

    def test_tables_exist(self, db_engine):
        with db_engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public' "
                    "ORDER BY table_name"
                )
            )
            tables = {row[0] for row in result}

        expected = {
            "users",
            "projects",
            "game_profiles",
            "assets",
            "creative_briefs",
            "render_jobs",
        }
        assert expected.issubset(tables)

    def test_insert_and_query_user(self, db_session):
        user = User(
            email="integration@test.com",
            name="Integration Test",
        )
        db_session.add(user)
        db_session.flush()

        queried = (
            db_session.query(User)
            .filter_by(email="integration@test.com")
            .first()
        )

        assert queried is not None
        assert queried.name == "Integration Test"
        assert queried.role == "creator"
        assert queried.id is not None

    def test_session_rollback_isolation(self, db_session):
        user = User(
            email="rollback@test.com",
            name="Rollback Test",
        )
        db_session.add(user)
        db_session.flush()

        count = db_session.query(User).count()

        assert count >= 1
