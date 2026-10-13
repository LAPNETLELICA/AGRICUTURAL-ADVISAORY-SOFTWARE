"""Canonical recommendations, trace records, and delivery responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import Field

from engine.models.domain import (
    ConflictRecord,
    ConstraintDecision,
    RuleEvaluation,
    ScoreContribution,
    StrictModel,
    utc_now,
)
from engine.models.enums import (
    Channel,
    DeliveryStatus,
    RecommendationType,
    TreeId,
)


class CanonicalRecommendationItem(StrictModel):
    candidate_id: str
    type: RecommendationType
    name: str
    summary: str
    score: float
    rank: int
    rule_id: str | None = None


class CandidateScoreRecord(StrictModel):
    candidate_id: str
    score: float
    rank: int
    breakdown: list[ScoreContribution] = Field(default_factory=list)


class ContactRecommendation(StrictModel):
    specialist_required: bool = False
    vendor_required: bool = False
    specialist_reason: str | None = None
    vendor_reason: str | None = None
    specialist_category: str | None = None
    vendor_category: str | None = None


class ActionGuidance(StrictModel):
    action: str
    title: str
    recommended_materials: list[str] = Field(default_factory=list)
    application_steps: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)


class Recommendation(StrictModel):
    recommendation_id: str = Field(default_factory=lambda: str(uuid4()))
    request_id: str
    crop_id: str
    channel: Channel
    primary: CanonicalRecommendationItem
    alternatives: list[CanonicalRecommendationItem] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    selected_trees: list[TreeId] = Field(default_factory=list)
    rule_references: list[str] = Field(default_factory=list)
    score_breakdown: list[CandidateScoreRecord] = Field(default_factory=list)
    trace_id: str
    uncertainty: list[str] = Field(default_factory=list)
    contact_recommendation: ContactRecommendation | None = None
    action_guidance: list[ActionGuidance] = Field(default_factory=list)
    presentation: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class TraceRecord(StrictModel):
    trace_id: str = Field(default_factory=lambda: str(uuid4()))
    request_id: str
    crop_id: str
    channel: Channel
    context_used: dict[str, Any]
    relevant_history_used: dict[str, Any]
    present_conditions_used: dict[str, Any]
    future_conditions_used: dict[str, Any]
    selected_trees: list[TreeId]
    evaluated_rules: list[RuleEvaluation]
    constraints: list[ConstraintDecision]
    score_components: list[CandidateScoreRecord]
    ranked_candidates: list[str]
    conflicts: list[ConflictRecord]
    final_recommendation: str
    reasons: list[str]
    warnings: list[str]
    actions: list[str]
    started_at: datetime
    completed_at: datetime = Field(default_factory=utc_now)


class DeliveryReceipt(StrictModel):
    delivery_id: str = Field(default_factory=lambda: str(uuid4()))
    recipient_id: str
    crop_id: str
    message: str
    status: DeliveryStatus = DeliveryStatus.DELIVERED
    recommendation_id: str | None = None
    delivered_at: datetime = Field(default_factory=utc_now)


class SMSAdvisoryResponse(StrictModel):
    recommendation: Recommendation
    message: str
    delivery: DeliveryReceipt


class RecommendationDetail(StrictModel):
    recommendation: Recommendation
    trace: TraceRecord


class HealthResponse(StrictModel):
    status: str
    version: str
    environment: str
    knowledge_loaded: bool
