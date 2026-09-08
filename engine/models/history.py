"""In-memory history adapter with crop/family filtering."""

from __future__ import annotations

from collections import defaultdict
from threading import RLock
from typing import Any


class InMemoryHistoryProvider:
    def __init__(self) -> None:
        self._events: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._lock = RLock()

    def get_relevant_history(
        self,
        farmer_id: str | None,
        crop_id: str,
        crop_family: str | None,
    ) -> list[dict[str, Any]]:
        if not farmer_id:
            return []
        with self._lock:
            events = [dict(event) for event in self._events.get(farmer_id, [])]
        return [
            event
            for event in events
            if event.get("crop_id") == crop_id
            or (crop_family and event.get("crop_family") == crop_family)
        ]

    def append(self, farmer_id: str | None, event: dict[str, Any]) -> None:
        if not farmer_id:
            return
        with self._lock:
            self._events[farmer_id].append(dict(event))

