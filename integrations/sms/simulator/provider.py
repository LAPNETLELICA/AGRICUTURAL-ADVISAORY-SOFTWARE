"""SMS provider simulator with virtual recipient inboxes."""

from __future__ import annotations

from collections import defaultdict
from threading import RLock

from engine.models.responses import DeliveryReceipt


class SMSSimulator:
    def __init__(self) -> None:
        self._messages: dict[str, list[DeliveryReceipt]] = defaultdict(list)
        self._lock = RLock()

    def send(
        self,
        recipient_id: str,
        crop_id: str,
        message: str,
        recommendation_id: str | None = None,
    ) -> DeliveryReceipt:
        receipt = DeliveryReceipt(
            recipient_id=recipient_id,
            crop_id=crop_id,
            message=message,
            recommendation_id=recommendation_id,
        )
        with self._lock:
            self._messages[recipient_id].append(receipt)
        return receipt.model_copy(deep=True)

    def inbox(self, recipient_id: str) -> list[DeliveryReceipt]:
        with self._lock:
            return [item.model_copy(deep=True) for item in self._messages.get(recipient_id, [])]

