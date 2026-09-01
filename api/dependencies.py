"""FastAPI dependency accessors."""

from typing import Annotated

from fastapi import Depends, Request

from engine.bootstrap import ApplicationContainer


def get_container(request: Request) -> ApplicationContainer:
    container: ApplicationContainer = request.app.state.container
    return container


ContainerDependency = Annotated[ApplicationContainer, Depends(get_container)]
