"""V1 local authentication API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from api.security import PrincipalDependency
from services.auth import AuthError

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class Credentials(BaseModel):
    username: str = Field(min_length=1, max_length=100, pattern=r"^[-A-Za-z0-9_.:@]+$")
    password: str = Field(min_length=10, max_length=200)


@router.post("/register")
def register(payload: Credentials, request: Request) -> dict[str, str]:
    try:
        request.app.state.auth_service.register_farmer(payload.username, payload.password)
        token = request.app.state.auth_service.authenticate(payload.username, payload.password)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return {"access_token": token, "token_type": "bearer", "role": "farmer"}


@router.post("/login")
def login(payload: Credentials, request: Request) -> dict[str, str]:
    try:
        token = request.app.state.auth_service.authenticate(payload.username, payload.password)
        principal = request.app.state.auth_service.verify(token)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return {"access_token": token, "token_type": "bearer", "role": principal.role}


@router.get("/me")
def me(principal: PrincipalDependency) -> dict[str, str]:
    return {"subject": principal.subject, "role": principal.role}
