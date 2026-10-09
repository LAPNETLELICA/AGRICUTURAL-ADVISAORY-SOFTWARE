"""FastAPI dependency accessors."""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from engine.bootstrap import ApplicationContainer


def get_container(request: Request) -> ApplicationContainer:
    return request.app.state.container


ContainerDependency = Annotated[ApplicationContainer, Depends(get_container)]


def get_db(container: ContainerDependency) -> Generator[Session, None, None]:
    """Yield an application-owned SQLAlchemy session when PostgreSQL is configured."""
    if container.database is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database persistence is not configured",
        )
    with container.database.sessions() as session:
        yield session
