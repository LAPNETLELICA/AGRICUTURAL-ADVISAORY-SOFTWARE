"""Authentication dependencies and ownership helpers."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from services.auth import AuthError, AuthService, Principal

bearer = HTTPBearer(auto_error=False)


def get_auth(request: Request) -> AuthService:
    return request.app.state.auth_service


def current_principal(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    auth: Annotated[AuthService, Depends(get_auth)],
) -> Principal:
    settings = request.app.state.container.settings
    if credentials is None:
        if not settings.auth_required:
            return Principal("development-user", "admin")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication required"
        )
    try:
        return auth.verify(credentials.credentials)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


PrincipalDependency = Annotated[Principal, Depends(current_principal)]


def require_admin(principal: PrincipalDependency) -> Principal:
    if not principal.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin role required")
    return principal


AdminDependency = Annotated[Principal, Depends(require_admin)]


def enforce_owner(principal: Principal, owner_id: str | None) -> None:
    if owner_id and not principal.is_admin and principal.subject != owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="resource ownership required"
        )
