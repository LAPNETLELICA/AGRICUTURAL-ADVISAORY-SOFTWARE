"""Tranzak SMS gateway adapter."""

from __future__ import annotations

import time
from typing import Any

import requests

from engine.models.responses import DeliveryReceipt

# Tranzak per-message status codes (official docs):
#   2 = submitted, 3 = processing, 5 = processed
#   -1 = failed,   -10 = rejected
_FAILURE_STATUSES = frozenset({-1, -10})


class TranzakSMSProvider:
    def __init__(
        self,
        app_id: str,
        app_key: str,
        sender_id: str,
        *,
        base_url: str = "https://sandbox.dsapi.tranzak.me",
        timeout: float = 10,
        session: Any = requests,
    ) -> None:
        self._app_id = app_id
        self._app_key = app_key
        self._sender_id = sender_id
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = session
        self._token: str | None = None
        self._token_expires_at: float = 0.0

    @staticmethod
    def _payload(response: Any) -> dict[str, Any]:
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        if payload.get("success") is not True:
            raise ValueError(str(payload.get("errorMsg") or "Tranzak rejected the SMS request"))
        return payload

    def _auth(self) -> str:
        # Tranzak tokens are short-lived (expiresIn seconds). Refresh before
        # expiry, honouring Tranzak's guidance to reuse a token for at most 3/4
        # of its validity so the long-running alert worker never sends a stale
        # bearer token.
        if self._token and time.monotonic() < self._token_expires_at:
            return self._token
        response = self._session.post(
            f"{self._base_url}/auth/token",
            json={"appId": self._app_id, "appKey": self._app_key},
            timeout=self._timeout,
        )
        data = self._payload(response).get("data")
        if not isinstance(data, dict):
            raise ValueError("Tranzak auth response did not include a token")
        token = data.get("token")
        if not token:
            raise ValueError("Tranzak auth response did not include a token")
        expires_in = data.get("expiresIn")
        if isinstance(expires_in, (int, float)) and expires_in > 0:
            self._token_expires_at = time.monotonic() + float(expires_in) * 0.75
        self._token = str(token)
        return self._token

    @staticmethod
    def _raise_on_failure_status(payload: dict[str, Any]) -> None:
        # Tranzak returns HTTP 200 + success:true at transport level even when
        # an individual message failed. Per-message entries live under
        # data.sms / data.messages with status -1 (failed) or -10 (rejected).
        data = payload.get("data")
        entries: Any = None
        if isinstance(data, dict):
            entries = data.get("sms", data.get("messages"))
        elif isinstance(data, list):
            entries = data
        if entries is None:
            entries = payload.get("sms", payload.get("messages"))
        if not isinstance(entries, list):
            return
        failures: list[str] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            status = entry.get("status")
            try:
                code = int(status) if status is not None else None
            except (TypeError, ValueError):
                continue
            if code in _FAILURE_STATUSES:
                detail = entry.get("errorMsg") or entry.get("message") or f"status {code}"
                phone = entry.get("phone") or entry.get("phones") or "unknown recipient"
                failures.append(f"{phone}: {detail}")
        if failures:
            raise ValueError("Tranzak rejected the SMS: " + "; ".join(failures))

    def send(
        self,
        recipient_id: str,
        crop_id: str,
        message: str,
        recommendation_id: str | None = None,
    ) -> DeliveryReceipt:
        response = self._session.post(
            f"{self._base_url}/dn088/v1/sms/api/send-v2",
            headers={"Authorization": f"Bearer {self._auth()}"},
            json={"phones": recipient_id, "msg": message, "senderId": self._sender_id},
            timeout=self._timeout,
        )
        payload = self._payload(response)
        self._raise_on_failure_status(payload)
        return DeliveryReceipt(
            recipient_id=recipient_id,
            crop_id=crop_id,
            message=message,
            recommendation_id=recommendation_id,
        )

    def inbox(self, recipient_id: str) -> list[DeliveryReceipt]:
        return []
