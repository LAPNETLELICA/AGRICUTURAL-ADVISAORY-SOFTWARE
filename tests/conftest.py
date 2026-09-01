from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from engine.bootstrap import ApplicationContainer, build_container
from engine.config import Settings
from engine.models.domain import (
    AgriculturalContext,
    CandidateTemplate,
    Condition,
    ConstraintSpec,
    CropProfile,
    Rule,
    SourceReference,
)
from engine.models.enums import (
    Channel,
    ConditionMode,
    RecommendationType,
    RuleStatus,
    TreeId,
)
from integrations.weather import StaticWeatherProvider


@pytest.fixture
def source() -> SourceReference:
    return SourceReference(title="Test agronomy source")


@pytest.fixture
def crop_profile(source: SourceReference) -> CropProfile:
    return CropProfile(
        crop_id="test-crop",
        name="Test crop",
        family="Testaceae",
        cycle_length_days=90,
        version="test-1",
        status=RuleStatus.TEST_ONLY,
        source=source,
    )


@pytest.fixture
def context(crop_profile: CropProfile) -> AgriculturalContext:
    return AgriculturalContext(
        request_id="request-1",
        crop_id="test-crop",
        channel=Channel.MOBILE,
        farmer_id="farmer-1",
        crop_profile=crop_profile,
        region="West",
        locality="Bafoussam",
        past={"history": []},
        present={
            "objective": "yield_improvement",
            "soil": {"drainage": "poor", "ph": 5.5},
            "topography": {"landform": "flatland"},
            "weather": {"rainfall_class": "heavy", "consecutive_rain_days": 3},
            "observations": {"symptom": "spots"},
            "practices": {},
        },
        future={"month": 8},
    )


@pytest.fixture
def make_rule(source: SourceReference):
    def factory(
        *,
        rule_id: str = "test.rule.1",
        candidate_id: str = "test.candidate.1",
        domain: TreeId = TreeId.CROP_PROFILE,
        conditions: list[Condition] | None = None,
        condition_mode: ConditionMode = ConditionMode.ALL,
        constraints: list[ConstraintSpec] | None = None,
        score_components: dict[str, float] | None = None,
        conflict_group: str | None = None,
        priority: int = 100,
        status: RuleStatus = RuleStatus.TEST_ONLY,
        source_override: SourceReference | None = None,
        requires_trees: list[TreeId] | None = None,
    ) -> Rule:
        return Rule(
            rule_id=rule_id,
            crop_id="test-crop",
            domain=domain,
            version="test-1",
            priority=priority,
            status=status,
            source=source_override or source,
            condition_mode=condition_mode,
            conditions=conditions or [],
            candidate=CandidateTemplate(
                candidate_id=candidate_id,
                type=RecommendationType.ADVISORY,
                name=candidate_id,
                summary=f"Summary for {candidate_id}",
                reasons=["reason"],
                warnings=["warning"],
                actions=["action"],
                score_components=score_components or {},
                conflict_group=conflict_group,
                constraints=constraints or [],
            ),
            requires_trees=requires_trees or [],
        )

    return factory


@pytest.fixture
def container() -> ApplicationContainer:
    project_root = Path(__file__).resolve().parents[1]
    settings = Settings(
        environment="test",
        knowledge_path=project_root / "knowledge",
        cors_origins=(),
    )
    weather = StaticWeatherProvider(
        current={"rainfall_class": "heavy", "consecutive_rain_days": 3},
        forecast={"month": 8},
    )
    return build_container(settings, weather_provider=weather)


def full_mobile_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "farmer_id": "farmer-1",
        "crop_id": "irish-potato",
        "question": "How can I improve my yield?",
        "objective": "yield_improvement",
        "region": "West",
        "locality": "Bafoussam",
        "current_stage": "pre-planting",
        "evidence": {
            "soil": {"drainage": "poor"},
            "topography": {"landform": "flatland"},
            "weather": {"rainfall_class": "heavy", "consecutive_rain_days": 3},
            "future": {"month": 8},
        },
    }
    payload.update(overrides)
    return payload
