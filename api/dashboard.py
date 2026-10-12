"""Built-in zero-build management dashboard and phone SMS simulator receiver."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["dashboard"])
_DASHBOARD = Path(__file__).resolve().parent.parent / "dashboard" / "index.html"
_RECEIVER = Path(__file__).resolve().parent.parent / "dashboard" / "receiver.html"


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
def dashboard() -> str:
    return _DASHBOARD.read_text(encoding="utf-8")


@router.get("/dashboard/sms-receiver", response_class=HTMLResponse, include_in_schema=False)
def sms_receiver() -> str:
    return _RECEIVER.read_text(encoding="utf-8")
