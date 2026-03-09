"""Tests for SQLAlchemy base model configuration."""

from app.models.base import Base, BaseModel


class TestBase:
    def test_base_is_declarative_base(self):
        assert hasattr(Base, "metadata")
        assert hasattr(Base, "registry")

    def test_base_model_has_id_column(self):
        annotations = BaseModel.__annotations__

        assert "id" in annotations

    def test_base_model_has_timestamps(self):
        annotations = BaseModel.__annotations__

        assert "created_at" in annotations
        assert "updated_at" in annotations

    def test_base_model_is_abstract(self):
        assert BaseModel.__abstract__ is True
