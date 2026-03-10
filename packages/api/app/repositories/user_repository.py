from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.errors import DatabaseError
from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.user import UserCreate, UserUpdate


class UserRepository(BaseRepository[User]):
    """Repository for User entity operations."""

    def __init__(self, session: Session):
        super().__init__(session, User)

    def get_by_email(self, email: str) -> User | None:
        """Find a user by email address."""
        try:
            return self._session.query(User).filter(User.email == email).first()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to fetch user by email {email}") from e

    def get_by_clerk_id(self, clerk_id: str) -> User | None:
        """Find a user by Clerk authentication ID."""
        try:
            return self._session.query(User).filter(User.clerk_id == clerk_id).first()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to fetch user by clerk_id {clerk_id}") from e

    def create_from_schema(self, schema: UserCreate) -> User:
        """Create a user from a UserCreate schema."""
        return self.create(schema.model_dump())

    def update_from_schema(self, entity_id: UUID, schema: UserUpdate) -> User | None:
        """Update a user from a UserUpdate schema."""
        return self.update(entity_id, schema.model_dump(exclude_unset=True))
