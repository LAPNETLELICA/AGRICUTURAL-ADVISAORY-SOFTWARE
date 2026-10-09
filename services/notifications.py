"""V1 SMS sandbox orchestration.

This is intentionally a test-triggered service rather than a hidden production
scheduler. It uses the existing deterministic engine to generate each message,
then sends it through the configured SMS boundary.
"""

from __future__ import annotations

import json
from pathlib import Path
from threading import RLock
from typing import Any

from engine.models.requests import AdvisoryRequest, EvidenceInput, SMSAdvisoryRequest


class NotificationService:
    def __init__(self, container: Any, store_path: Path) -> None:
        self._container = container
        self._store_path = store_path
        self._lock = RLock()
        self._subscriptions: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if self._store_path.exists():
            try:
                data = json.loads(self._store_path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self._subscriptions = data
            except (OSError, json.JSONDecodeError):
                pass

    def _save(self) -> None:
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        temp = self._store_path.with_suffix(".tmp")
        temp.write_text(json.dumps(self._subscriptions, indent=2), encoding="utf-8")
        temp.replace(self._store_path)

    def subscribe(self, payload: dict[str, Any]) -> dict[str, Any]:
        recipient = str(payload["recipient_id"])
        crop_id = str(payload["crop_id"])
        profile = self._container.knowledge.get_crop_profile(crop_id)
        if profile is None:
            raise ValueError("unknown crop")
        record = {
            "recipient_id": recipient,
            "farmer_id": str(payload.get("farmer_id") or recipient),
            "crop_id": crop_id,
            "region": str(payload.get("region") or "unknown"),
            "locality": payload.get("locality"),
            "language": str(payload.get("language") or "en"),
            "cultivation_period": payload.get("cultivation_period"),
            "current_stage": payload.get("current_stage"),
            "enabled": bool(payload.get("enabled", True)),
        }
        with self._lock:
            self._subscriptions[recipient] = record
            self._save()
        return record

    def list_subscriptions(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(value) for _, value in sorted(self._subscriptions.items())]

    def trigger(self, recipient_id: str) -> dict[str, Any]:
        with self._lock:
            subscription = self._subscriptions.get(recipient_id)
        if not subscription or not subscription.get("enabled"):
            raise ValueError("active notification subscription not found")
        request = SMSAdvisoryRequest(
            recipient_id=subscription["recipient_id"],
            farmer_id=subscription["farmer_id"],
            crop_id=subscription["crop_id"],
            current_stage=subscription.get("current_stage"),
            cultivation_period=subscription.get("cultivation_period"),
            region=subscription["region"],
            locality=subscription.get("locality"),
            language=subscription["language"],
            evidence=EvidenceInput(),
            metadata={"source": "notification-sandbox", "trigger": "manual"},
        )
        recommendation = self._container.engine.advise(AdvisoryRequest.from_sms(request))
        message = self._container.sms_formatter.format(recommendation)
        if request.language.lower() != "en":
            message = self._container.translator.translate(message, request.language)
        # Re-enforce channel length after translation.
        if len(message) > self._container.settings.sms_max_length:
            message = message[: self._container.settings.sms_max_length - 1].rstrip() + "…"
        receipt = self._container.sms.send(
            request.recipient_id, request.crop_id, message, recommendation.recommendation_id
        )
        return {
            "recommendation": recommendation.model_dump(mode="json"),
            "message": message,
            "delivery": receipt.model_dump(mode="json"),
        }
