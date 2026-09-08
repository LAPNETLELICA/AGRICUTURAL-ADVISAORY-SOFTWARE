#!/usr/bin/env python3
"""Offline core validation when package installation is unavailable.

This is intentionally independent of FastAPI, pytest, and network access. The normal
test suite remains authoritative after development dependencies are installed.
"""

from __future__ import annotations

from pathlib import Path

from engine.advisory.conflict import ConflictResolver
from engine.advisory.constraints import ConstraintProcessor
from engine.advisory.evaluator import RuleEvaluator
from engine.advisory.ranking import Ranker
from engine.advisory.scoring import (
    MobileScoringStrategy,
    SMSPriorityScoringStrategy,
)
from engine.bootstrap import build_container
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
from engine.models.enums import Channel, RuleStatus, TreeId
from engine.models.requests import (
    AdvisoryRequest,
    EvidenceInput,
    MobileAdvisoryRequest,
    SMSAdvisoryRequest,
)
from integrations.knowledge import JSONKnowledgeProvider
from integrations.weather import StaticWeatherProvider


def _rule(
    source: SourceReference,
    *,
    rule_id: str,
    candidate_id: str,
    score: float,
    group: str | None = None,
    constraint: ConstraintSpec | None = None,
) -> Rule:
    return Rule(
        rule_id=rule_id,
        crop_id="test-crop",
        domain=TreeId.CROP_PROFILE,
        version="test",
        priority=100,
        status=RuleStatus.TEST_ONLY,
        source=source,
        candidate=CandidateTemplate(
            candidate_id=candidate_id,
            type="advisory",
            name=candidate_id,
            summary="Offline test candidate",
            score_components={"crop_fit": score, "future_risk": score},
            conflict_group=group,
            constraints=[constraint] if constraint else [],
        ),
    )


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    knowledge_path = root / "knowledge"
    provider = JSONKnowledgeProvider(knowledge_path, {"draft", "validated", "test_only"})
    assert provider.metadata()["crop_count"] == 1
    assert provider.metadata()["rule_count"] == 5
    assert JSONKnowledgeProvider(knowledge_path, {"validated"}).metadata()["rule_count"] == 0

    settings = Settings(environment="test", knowledge_path=knowledge_path, cors_origins=())
    container = build_container(
        settings,
        weather_provider=StaticWeatherProvider(
            current={"rainfall_class": "heavy", "consecutive_rain_days": 3},
            forecast={"month": 8},
        ),
    )
    evidence = EvidenceInput(
        soil={"drainage": "poor"},
        topography={"landform": "flatland"},
        weather={"rainfall_class": "heavy", "consecutive_rain_days": 3},
        future={"month": 8},
    )
    mobile_request = MobileAdvisoryRequest(
        farmer_id="offline-farmer",
        crop_id="irish-potato",
        plot_ref="offline-plot",
        current_stage="pre-planting",
        question="How should I improve this plot?",
        region="West",
        locality="Bafoussam",
        evidence=evidence,
    )
    mobile = container.engine.advise(AdvisoryRequest.from_mobile(mobile_request))
    assert mobile.primary.name == "late_blight_watch"
    assert mobile.selected_trees == list(TreeId)
    assert {item.type.value for item in mobile.alternatives} >= {"soil_action", "timing"}
    assert container.traces.get(mobile.trace_id) is not None
    passport = container.passports.find("offline-farmer", "irish-potato", "offline-plot")
    assert passport and mobile.recommendation_id in passport.recommendation_ids

    sms_request = SMSAdvisoryRequest(
        recipient_id="offline-phone",
        crop_id="irish-potato",
        region="West",
        cultivation_period="August",
        evidence=evidence,
    )
    sms = container.engine.advise(AdvisoryRequest.from_sms(sms_request))
    assert sms.primary.rule_id == mobile.primary.rule_id
    assert sms.primary.score > mobile.primary.score
    text = container.sms_formatter.format(sms)
    assert len(text) <= settings.sms_max_length
    receipt = container.sms.send("offline-phone", "irish-potato", text, sms.recommendation_id)
    assert container.sms.inbox("offline-phone") == [receipt]

    source = SourceReference(title="Offline test")
    profile = CropProfile(
        crop_id="test-crop",
        name="Test crop",
        family="Testaceae",
        cycle_length_days=90,
        version="test",
        status="test_only",
        source=source,
    )
    context = AgriculturalContext(
        request_id="offline-request",
        crop_id="test-crop",
        channel=Channel.MOBILE,
        crop_profile=profile,
        present={"soil": {"drainage": "poor"}},
        future={"month": 8},
    )
    evaluator = RuleEvaluator()
    evidence_result = evaluator.evaluate_condition(
        Condition(field="future.month", operator="between", value=[7, 9]), context
    )
    assert evidence_result.matched

    soft_constraint = ConstraintSpec(
        constraint_id="soft-offline",
        kind="soft",
        effect="penalize_if",
        condition=Condition(field="present.soil.drainage", operator="eq", value="poor"),
        reason="Offline test penalty",
        penalty=1.5,
    )
    first = evaluator.evaluate(
        _rule(
            source,
            rule_id="offline.rule.1",
            candidate_id="offline-candidate-1",
            score=3,
            group="choice",
            constraint=soft_constraint,
        ),
        context,
    )
    second = evaluator.evaluate(
        _rule(
            source,
            rule_id="offline.rule.2",
            candidate_id="offline-candidate-2",
            score=1,
            group="choice",
        ),
        context,
    )
    eligible, decisions, penalties = ConstraintProcessor(evaluator).apply([first, second], context)
    assert decisions[0].penalty == 1.5
    mobile_scored = MobileScoringStrategy().score(eligible, penalties)
    sms_scored = SMSPriorityScoringStrategy().score(eligible, penalties)
    assert mobile_scored[0].score == 1.5
    assert sms_scored[0].score == 1.5
    resolution = ConflictResolver().resolve(Ranker().rank(mobile_scored))
    assert len(resolution.active) == 1
    assert len(resolution.suppressed) == 1
    assert len(resolution.conflicts) == 1

    print("OFFLINE CORE SELF-TEST PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
