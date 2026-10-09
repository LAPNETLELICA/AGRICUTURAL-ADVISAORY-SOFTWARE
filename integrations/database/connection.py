"""PostgreSQL engine and session management."""

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker


class Database:
    """Own the SQLAlchemy engine and database session factory."""

    def __init__(self, database_url: str) -> None:
        self.engine: Engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
        self.sessions: sessionmaker[Session] = sessionmaker(
            bind=self.engine,
            class_=Session,
            expire_on_commit=False,
        )

    def ping(self) -> None:
        """Verify that PostgreSQL can be reached."""
        with self.engine.connect() as connection:
            connection.execute(text("SELECT 1"))

    def close(self) -> None:
        """Close every connection managed by the engine."""
        self.engine.dispose()
