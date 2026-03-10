class DatabaseError(Exception):
    """Wraps SQLAlchemy errors at the repository boundary."""

    def __init__(self, message: str = "A database error occurred"):
        self.message = message
        super().__init__(self.message)


class NotFoundError(Exception):
    """Raised when an entity is not found by ID."""

    def __init__(self, entity_name: str, entity_id: object):
        self.entity_name = entity_name
        self.entity_id = entity_id
        self.message = f"{entity_name} with id {entity_id} not found"
        super().__init__(self.message)


class ValidationError(Exception):
    """Raised when a business rule is violated."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ExternalProviderError(Exception):
    """Raised when an external provider API call fails."""

    def __init__(self, provider_name: str, message: str):
        self.provider_name = provider_name
        self.message = message
        super().__init__(f"{provider_name}: {message}")


class StorageError(Exception):
    """Wraps S3/storage errors at the repository boundary."""

    def __init__(self, message: str = "A storage error occurred"):
        self.message = message
        super().__init__(self.message)
