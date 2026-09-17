"""Ambient PostgreSQL transaction coordination for atomic advisory persistence."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from sqlalchemy.orm import Session, sessionmaker

_ACTIVE_SESSION: ContextVar[Session | None] = ContextVar("agrisense_db_session", default=None)


class DatabaseUnitOfWork:
    """Coordinate repository writes in one SQLAlchemy transaction.

    Existing repositories still work independently. When the advisory engine opens this
    unit-of-work, all repository writes reuse the same session and therefore commit or
    roll back together.
    """

    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    @contextmanager
    def transaction(self) -> Iterator[None]:
        active = _ACTIVE_SESSION.get()
        if active is not None:
            yield
            return

        with self._sessions() as session:
            token = _ACTIVE_SESSION.set(session)
            try:
                with session.begin():
                    yield
            finally:
                _ACTIVE_SESSION.reset(token)


@contextmanager
def repository_session(
    sessions: sessionmaker[Session], *, write: bool = False
) -> Iterator[Session]:
    """Return the ambient UoW session or open an independent repository session."""

    active = _ACTIVE_SESSION.get()
    if active is not None:
        yield active
        return

    if write:
        with sessions.begin() as session:
            yield session
    else:
        with sessions() as session:
            yield session
