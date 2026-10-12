"""Tranzak SMS gateway adapter."""

from __future__ import annotations

from typing import Any

import requests

from engine.models.responses import DeliveryReceipt


class TranzakSMSProvider:
    def __init__(self, app_id: str, app_key: str, sender_id: str, *, base_url: str = "https://sandbox.dsapi.tranzak.me", timeout: float = 10, session: Any = requests) -> None:
        self._app_id, self._app_key, self._sender_id = app_id, app_key, sender_id
        self._base_url, self._timeout, self._session, self._token = base_url.rstrip("/"), timeout, session, None

    def _auth(self) -> str:
        if not self._token:
            response = self._session.post(f"{self._base_url}/auth/token", json={"appId": self._app_id, "appKey": self._app_key}, timeout=self._timeout)
            response.raise_for_status()
            self._token = str(response.json()["token"])
        return self._token

    def send(self, recipient_id: str, crop_id: str, message: str, recommendation_id: str | None = None) -> DeliveryReceipt:
        response = self._session.post(f"{self._base_url}/dn088/v1/sms/api/send-v2", headers={"Authorization": f"Bearer {self._auth()}"}, json={"phones": recipient_id, "msg": message, "senderId": self._sender_id}, timeout=self._timeout)
        response.raise_for_status()
        return DeliveryReceipt(recipient_id=recipient_id, crop_id=crop_id, message=message, recommendation_id=recommendation_id)

    def inbox(self, recipient_id: str) -> list[DeliveryReceipt]:
        return []
