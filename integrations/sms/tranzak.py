"""Tranzak SMS gateway adapter."""

from __future__ import annotations

from typing import Any

import requests

from engine.models.responses import DeliveryReceipt


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

    @staticmethod
    def _payload(response: Any) -> dict[str, Any]:
        response.raise_for_status()
        payload = response.json()
        if payload.get("success") is not True:
            raise ValueError(str(payload.get("errorMsg") or "Tranzak rejected the SMS request"))
        return payload

    def _auth(self) -> str:
        if not self._token:
            response = self._session.post(
                f"{self._base_url}/auth/token",
                json={"appId": self._app_id, "appKey": self._app_key},
                timeout=self._timeout,
            )
            self._token = str(self._payload(response)["data"]["token"])
        return self._token

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
        self._payload(response)
        return DeliveryReceipt(
            recipient_id=recipient_id,
            crop_id=crop_id,
            message=message,
            recommendation_id=recommendation_id,
        )

    def inbox(self, recipient_id: str) -> list[DeliveryReceipt]:
        return []
