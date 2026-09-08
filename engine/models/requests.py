"""Validated external request models and internal normalization."""

from __future__ import annotations

from typing import Any, Self
from uuid import uuid4

from pydantic import Field, field_validator, model_validator

from engine.models.domain import IDENTIFIER_PATTERN, StrictModel
from engine.models.enums import Channel, Objective


class EvidenceInput(StrictModel):
    soil: dict[str, Any] = Field(default_factory=dict)
    topography: dict[str, Any] = Field(default_factory=dict)
    weather: dict[str, Any] = Field(default_factory=dict)
    observations: dict[str, Any] = Field(default_factory=dict)
    practices: dict[str, Any] = Field(default_factory=dict)
    image_references: list[str] = Field(default_factory=list, max_length=10)
    future: dict[str, Any] = Field(default_factory=dict)

    @field_validator("image_references")
    @classmethod
    def reject_local_file_references(cls, values: list[str]) -> list[str]:
        for value in values:
            if value.lower().startswith("file:"):
                raise ValueError("local file references are not accepted")
            if len(value) > 1000:
                raise ValueError("image reference is too long")
        return values


class MobileAdvisoryRequest(StrictModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()), pattern=IDENTIFIER_PATTERN)
    farmer_id: str = Field(pattern=IDENTIFIER_PATTERN)
    crop_id: str | None = Field(default=None, pattern=IDENTIFIER_PATTERN)
    crop_description: str | None = Field(default=None, min_length=2, max_length=300)
    crop_discovery: bool = False
    passport_id: str | None = Field(default=None, pattern=IDENTIFIER_PATTERN)
    plot_ref: str = Field(default="default-plot", pattern=IDENTIFIER_PATTERN)
    current_stage: str | None = Field(default=None, max_length=100)
    question: str = Field(min_length=3, max_length=2000)
    objective: Objective = Objective.YIELD_IMPROVEMENT
    region: str | None = Field(default=None, max_length=200)
    locality: str | None = Field(default=None, max_length=200)
    language: str = Field(default="en", pattern=r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})?$")
    evidence: EvidenceInput = Field(default_factory=EvidenceInput)
    history: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_crop_target(self) -> Self:
        if not self.crop_id and not self.crop_description:
            raise ValueError("crop_id or crop_description is required")
        if not self.crop_id and not self.crop_discovery:
            raise ValueError("crop_discovery must be true when crop_id is unknown")
        return self


class SMSAdvisoryRequest(StrictModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()), pattern=IDENTIFIER_PATTERN)
    recipient_id: str = Field(pattern=IDENTIFIER_PATTERN)
    crop_id: str = Field(pattern=IDENTIFIER_PATTERN)
    farmer_id: str | None = Field(default=None, pattern=IDENTIFIER_PATTERN)
    passport_id: str | None = Field(default=None, pattern=IDENTIFIER_PATTERN)
    plot_ref: str = Field(default="default-plot", pattern=IDENTIFIER_PATTERN)
    current_stage: str | None = Field(default=None, max_length=100)
    cultivation_period: str | None = Field(default=None, max_length=200)
    region: str = Field(min_length=1, max_length=200)
    locality: str | None = Field(default=None, max_length=200)
    language: str = Field(default="en", pattern=r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})?$")
    evidence: EvidenceInput = Field(default_factory=EvidenceInput)
    history: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AdvisoryRequest(StrictModel):
    """Channel-neutral request consumed by the inference engine."""

    request_id: str = Field(pattern=IDENTIFIER_PATTERN)
    channel: Channel
    crop_id: str = Field(pattern=IDENTIFIER_PATTERN)
    crop_description: str | None = None
    crop_discovery: bool = False
    farmer_id: str | None = Field(default=None, pattern=IDENTIFIER_PATTERN)
    recipient_id: str | None = Field(default=None, pattern=IDENTIFIER_PATTERN)
    passport_id: str | None = Field(default=None, pattern=IDENTIFIER_PATTERN)
    plot_ref: str = Field(default="default-plot", pattern=IDENTIFIER_PATTERN)
    current_stage: str | None = None
    question: str | None = None
    objective: Objective
    cultivation_period: str | None = None
    region: str | None = None
    locality: str | None = None
    language: str = "en"
    evidence: EvidenceInput = Field(default_factory=EvidenceInput)
    history: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_mobile(cls, request: MobileAdvisoryRequest) -> AdvisoryRequest:
        return cls(
            request_id=request.request_id,
            channel=Channel.MOBILE,
            crop_id=request.crop_id or "crop-discovery",
            crop_description=request.crop_description,
            crop_discovery=request.crop_discovery,
            farmer_id=request.farmer_id,
            passport_id=request.passport_id,
            plot_ref=request.plot_ref,
            current_stage=request.current_stage,
            question=request.question,
            objective=request.objective,
            region=request.region,
            locality=request.locality,
            language=request.language,
            evidence=request.evidence,
            history=request.history,
            metadata=request.metadata,
        )

    @classmethod
    def from_sms(cls, request: SMSAdvisoryRequest) -> AdvisoryRequest:
        return cls(
            request_id=request.request_id,
            channel=Channel.SMS,
            crop_id=request.crop_id,
            farmer_id=request.farmer_id,
            recipient_id=request.recipient_id,
            passport_id=request.passport_id,
            plot_ref=request.plot_ref,
            current_stage=request.current_stage,
            objective=Objective.RISK,
            cultivation_period=request.cultivation_period,
            region=request.region,
            locality=request.locality,
            language=request.language,
            evidence=request.evidence,
            history=request.history,
            metadata=request.metadata,
        )


class SMSDeliveryRequest(StrictModel):
    recipient_id: str = Field(pattern=IDENTIFIER_PATTERN)
    crop_id: str = Field(pattern=IDENTIFIER_PATTERN)
    message: str = Field(min_length=1, max_length=918)
    recommendation_id: str | None = Field(default=None, pattern=IDENTIFIER_PATTERN)

