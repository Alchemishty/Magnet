"""Tests for database session configuration."""

import os
from unittest.mock import patch

from sqlalchemy import Engine
from sqlalchemy.orm import Session


class TestDatabaseConfig:
    def test_engine_is_created(self):
        from app.db import engine

        assert isinstance(engine, Engine)

    def test_session_local_produces_session(self):
        from app.db import SessionLocal

        session = SessionLocal()

        assert isinstance(session, Session)
        session.close()

    def test_get_db_yields_session(self):
        from app.db import get_db

        gen = get_db()
        session = next(gen)

        assert isinstance(session, Session)

        try:
            next(gen)
        except StopIteration:
            pass

    def test_database_url_from_env(self):
        test_url = "postgresql://test:test@testhost:5432/testdb"
        with patch.dict(os.environ, {"DATABASE_URL": test_url}):
            import importlib

            import app.db

            importlib.reload(app.db)

            url = app.db.engine.url
            assert url.host == "testhost"
            assert url.database == "testdb"
            assert url.username == "test"

        importlib.reload(app.db)

    def test_database_url_default(self):
        with patch.dict(os.environ, {}, clear=True):
            import importlib

            import app.db

            importlib.reload(app.db)

            url = app.db.engine.url
            assert url.database == "magnet"
            assert url.host == "localhost"

        importlib.reload(app.db)
