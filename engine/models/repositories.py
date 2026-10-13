"""Thread-safe in-memory V1 stores, replaceable behind repository interfaces."""

from __future__ import annotations

from datetime import UTC, datetime
from threading import RLock
from copy import deepcopy

from engine.models.conversations import AdvisoryConversation, ConversationMessage
from engine.models.domain import CropPassport, User
from engine.models.responses import Recommendation, TraceRecord


class InMemoryTraceRecorder:
    def __init__(self) -> None:
        self._items: dict[str, TraceRecord] = {}
        self._lock = RLock()

    def record(self, trace: TraceRecord) -> None:
        with self._lock:
            self._items[trace.trace_id] = trace.model_copy(deep=True)

    def get(self, trace_id: str) -> TraceRecord | None:
        with self._lock:
            item = self._items.get(trace_id)
            return item.model_copy(deep=True) if item else None


class InMemoryRecommendationRepository:
    def __init__(self) -> None:
        self._items: dict[str, Recommendation] = {}
        self._lock = RLock()

    def save(self, recommendation: Recommendation) -> None:
        with self._lock:
            self._items[recommendation.recommendation_id] = recommendation.model_copy(deep=True)

    def get(self, recommendation_id: str) -> Recommendation | None:
        with self._lock:
            item = self._items.get(recommendation_id)
            return item.model_copy(deep=True) if item else None


class InMemoryCropPassportRepository:
    def __init__(self) -> None:
        self._items: dict[str, CropPassport] = {}
        self._lock = RLock()

    def get(self, passport_id: str) -> CropPassport | None:
        with self._lock:
            item = self._items.get(passport_id)
            return item.model_copy(deep=True) if item else None

    def find(self, farmer_id: str, crop_id: str, plot_ref: str) -> CropPassport | None:
        with self._lock:
            for item in self._items.values():
                if (
                    item.farmer_id == farmer_id
                    and item.crop_id == crop_id
                    and item.plot_ref == plot_ref
                ):
                    return item.model_copy(deep=True)
        return None

    def save(self, passport: CropPassport) -> None:
        with self._lock:
            self._items[passport.passport_id] = passport.model_copy(deep=True)

class InMemoryUserRepository:
    def __init__(self) -> None:
        self._users: dict[str, User] = {}

    def get_by_email(self, email: str) -> User | None:
        return next((u for u in self._users.values() if u.email == email), None)

    def save(self, user: User) -> User:
        self._users[user.id] = user


class InMemoryConversationRepository:
    """Conversation store used when PostgreSQL is not configured."""

    def __init__(self) -> None:
        self._items: dict[str, AdvisoryConversation] = {}
        self._messages: dict[str, list[ConversationMessage]] = {}
        self._lock = RLock()

    def create(self, conversation: AdvisoryConversation) -> AdvisoryConversation:
        with self._lock:
            self._items[conversation.conversation_id] = conversation.model_copy(deep=True)
            self._messages.setdefault(conversation.conversation_id, [])
            return conversation.model_copy(deep=True)

    def get(self, conversation_id: str) -> AdvisoryConversation | None:
        with self._lock:
            item = self._items.get(conversation_id)
            return item.model_copy(deep=True) if item else None

    def latest_open(self, farmer_id: str) -> AdvisoryConversation | None:
        with self._lock:
            matches = [
                item for item in self._items.values()
                if item.farmer_id == farmer_id and item.status == "open"
            ]
            if not matches:
                return None
            return max(matches, key=lambda item: item.updated_at).model_copy(deep=True)

    def save(self, conversation: AdvisoryConversation) -> AdvisoryConversation:
        with self._lock:
            stored = conversation.model_copy(update={"updated_at": datetime.now(UTC)}, deep=True)
            self._items[stored.conversation_id] = stored
            return stored.model_copy(deep=True)

    def append_message(self, conversation_id: str, message: ConversationMessage) -> None:
        with self._lock:
            if conversation_id not in self._items:
                raise KeyError(conversation_id)
            messages = self._messages.setdefault(conversation_id, [])
            if messages and message.sequence <= messages[-1].sequence:
                raise ValueError("conversation message sequence must increase")
            messages.append(message.model_copy(deep=True))
            self._items[conversation_id] = self._items[conversation_id].model_copy(
                update={"updated_at": datetime.now(UTC)}
            )

    def list_messages(self, conversation_id: str) -> list[ConversationMessage]:
        with self._lock:
            return deepcopy(self._messages.get(conversation_id, []))
