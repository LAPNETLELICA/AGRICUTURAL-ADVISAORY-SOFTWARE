"""Stable vocabulary shared by the engine, API, and knowledge files."""

from enum import StrEnum


class Channel(StrEnum):
    MOBILE = "mobile"
    SMS = "sms"
    VOICE = "voice"


class TreeId(StrEnum):
    CROP_PROFILE = "T1"
    SOIL = "T2"
    REGION = "T3"
    TOPOGRAPHY = "T4"
    WEATHER = "T5"
    TIMING = "T6"
    PRACTICES_RISKS = "T7"


class RuleStatus(StrEnum):
    DRAFT = "draft"
    VALIDATED = "validated"
    DEPRECATED = "deprecated"
    TEST_ONLY = "test_only"


class ConditionMode(StrEnum):
    ALL = "all"
    ANY = "any"


class ConditionOperator(StrEnum):
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    BETWEEN = "between"


class ConstraintKind(StrEnum):
    HARD = "hard"
    SOFT = "soft"


class ConstraintEffect(StrEnum):
    EXCLUDE_IF = "exclude_if"
    REQUIRE = "require"
    PENALIZE_IF = "penalize_if"


class EvaluationOutcome(StrEnum):
    MATCHED = "matched"
    NOT_MATCHED = "not_matched"
    INSUFFICIENT = "insufficient_evidence"


class Objective(StrEnum):
    SUITABILITY = "suitability"
    SOIL_IMPROVEMENT = "soil_improvement"
    YIELD_IMPROVEMENT = "yield_improvement"
    PLANTING = "planting"
    RISK = "risk"
    EDUCATION = "education"
    CROP_DISCOVERY = "crop_discovery"


class RecommendationType(StrEnum):
    SOIL_ACTION = "soil_action"
    PRACTICE = "practice"
    TIMING = "timing"
    ADVISORY = "advisory"
    RISK_ALERT = "risk_alert"


class DeliveryStatus(StrEnum):
    QUEUED = "queued"
    DELIVERED = "delivered"
    FAILED = "failed"

