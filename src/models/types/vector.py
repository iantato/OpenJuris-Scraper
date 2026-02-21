import json

from sqlalchemy import func, TypeDecorator, LargeBinary, case, null
from sqlalchemy.types import UserDefinedType


class VectorType(TypeDecorator):
    """
    libsql/SQLite Vector type using F32_BLOB.
    See also https://turso.tech/blog/turso-brings-native-vector-search-to-sqlite

    Usage:
        embedding = Column(VectorType(dim=384))
    """

    impl = LargeBinary
    cache_ok = True

    def __init__(self, dim: int):
        self.dim = dim
        super().__init__()

    def load_dialect_impl(self, dialect):
        dim = self.dim

        class F32_BLOB_Impl(UserDefinedType):
            cache_ok = True

            def get_col_spec(self):
                return f"F32_BLOB({dim})"

        return F32_BLOB_Impl()

    def bind_processor(self, dialect):
        """Convert Python list/tuple to JSON string for the database."""
        def process(value):
            if value is None:
                return None
            if isinstance(value, (list, tuple)):
                return json.dumps(value)
            if isinstance(value, str):
                return value
            return value
        return process

    def result_processor(self, dialect, coltype):
        """Convert database value back to Python list."""
        def process(value):
            if value is None:
                return None
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, ValueError):
                    return value
            if isinstance(value, bytes):
                try:
                    return json.loads(value.decode("utf-8"))
                except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
                    return value
            return value
        return process

    def bind_expression(self, bindvalue):
        """Wrap non-NULL values with vector() function."""
        return case((bindvalue.is_(None), null()), else_=func.vector(bindvalue))

    def __repr__(self):
        return f"VectorType(dim={self.dim})"