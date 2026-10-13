"""Models for farmer-owned advisory conversations."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import Field

from engine.models.domain import StrictModel


class ConversationStatus(StrEnum):
    OPEN = "open"
    COMPLETED = "completed"


class ConversationSender(StrEnum):
    FARMER = "farmer"
    ASSISTANT = "assistant"


class ConversationMessage(StrictModel):
    sequence: int = Field(ge=1)
    sender: ConversationSender
    text: str = Field(min_length=1, max_length=2000)
    facts: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def farmer(cls, sequence: int, text: str) -> "ConversationMessage":
        return cls(sequence=sequence, sender=ConversationSender.FARMER, text=text)

    @classmethod
    def assistant(cls, sequence: int, text: str) -> "ConversationMessage":
        return cls(sequence=sequence, sender=ConversationSender.ASSISTANT, text=text)


class AdvisoryConversation(StrictModel):
    conversation_id: str = Field(default_factory=lambda: str(uuid4()))
    farmer_id: str
    status: ConversationStatus = ConversationStatus.OPEN
    intent: str | None = None
    expected_field: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)
    recommendation: dict[str, Any] | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(cls, farmer_id: str, **context: Any) -> "AdvisoryConversation":
        return cls(farmer_id=farmer_id, context=deepcopy(context))
