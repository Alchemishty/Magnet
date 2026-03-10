from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.errors import DatabaseError

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Generic base repository providing CRUD operations."""

    def __init__(self, session: Session, model_class: type[T]):
        self._session = session
        self._model_class = model_class

    def create(self, data: dict) -> T:
        """Create a new entity from a dict of attributes."""
        try:
            instance = self._model_class(**data)
            self._session.add(instance)
            self._session.flush()
            return instance
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to create {self._model_class.__name__}") from e

    def get_by_id(self, entity_id: UUID) -> T | None:
        """Fetch an entity by primary key. Returns None if not found."""
        try:
            return self._session.get(self._model_class, entity_id)
        except SQLAlchemyError as e:
            raise DatabaseError(
                f"Failed to fetch {self._model_class.__name__} with id {entity_id}"
            ) from e

    def list(
        self,
        filters: dict | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[T]:
        """List entities with optional equality filters and pagination."""
        try:
            query = self._session.query(self._model_class)
            if filters:
                for key, value in filters.items():
                    if not hasattr(self._model_class, key):
                        raise DatabaseError(
                            f"Invalid filter key '{key}' for "
                            f"{self._model_class.__name__}"
                        )
                    query = query.filter(getattr(self._model_class, key) == value)
            return query.offset(offset).limit(limit).all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to list {self._model_class.__name__}") from e

    def update(self, entity_id: UUID, data: dict) -> T | None:
        """Update an entity by ID with a dict of changes.

        Returns the updated entity or None if not found.
        """
        try:
            instance = self._session.get(self._model_class, entity_id)
            if instance is None:
                return None
            for key, value in data.items():
                if not hasattr(instance, key):
                    raise DatabaseError(
                        f"Invalid attribute '{key}' for {self._model_class.__name__}"
                    )
                setattr(instance, key, value)
            self._session.flush()
            return instance
        except SQLAlchemyError as e:
            raise DatabaseError(
                f"Failed to update {self._model_class.__name__} with id {entity_id}"
            ) from e

    def delete(self, entity_id: UUID) -> bool:
        """Delete an entity by ID. Returns True if deleted, False if not found."""
        try:
            instance = self._session.get(self._model_class, entity_id)
            if instance is None:
                return False
            self._session.delete(instance)
            self._session.flush()
            return True
        except SQLAlchemyError as e:
            raise DatabaseError(
                f"Failed to delete {self._model_class.__name__} with id {entity_id}"
            ) from e
