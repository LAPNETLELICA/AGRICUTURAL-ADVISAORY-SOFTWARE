"""Composition root for the modular monolith."""

from __future__ import annotations

from dataclasses import dataclass

from engine.advisory.conflict import ConflictResolver
from engine.advisory.constraints import ConstraintProcessor
from engine.advisory.context import CropContextBuilder
from engine.advisory.engine import AdvisoryEngine
from engine.advisory.evaluator import RuleEvaluator
from engine.advisory.passport import CropPassportService
from engine.advisory.ranking import Ranker
from engine.advisory.recommendation import RecommendationBuilder
from engine.advisory.scoring import (
    MobileScoringStrategy,
    SMSPriorityScoringStrategy,
)
from engine.advisory.selector import CropTreeSelector
from engine.config import Settings
from engine.interfaces.providers import WeatherProvider
from engine.models.history import InMemoryHistoryProvider
from engine.models.repositories import (
    InMemoryCropPassportRepository,
    InMemoryRecommendationRepository,
    InMemoryTraceRecorder,
)
from integrations.knowledge import JSONKnowledgeProvider
from integrations.sms.simulator import SMSSimulator
from integrations.speech.disabled import DisabledSpeechProvider
from integrations.translation.passthrough import PassthroughTranslator
from integrations.weather.providers import UnavailableWeatherProvider
from languages.formatters import MobileFormatter, SMSFormatter, VoiceFormatter


@dataclass(slots=True)
class ApplicationContainer:
    settings: Settings
    engine: AdvisoryEngine
    knowledge: JSONKnowledgeProvider
    recommendations: InMemoryRecommendationRepository
    traces: InMemoryTraceRecorder
    passports: InMemoryCropPassportRepository
    history: InMemoryHistoryProvider
    sms: SMSSimulator
    translator: PassthroughTranslator
    speech: DisabledSpeechProvider
    mobile_formatter: MobileFormatter
    sms_formatter: SMSFormatter
    voice_formatter: VoiceFormatter


def build_container(
    settings: Settings,
    *,
    weather_provider: WeatherProvider | None = None,
) -> ApplicationContainer:
    knowledge = JSONKnowledgeProvider(
        settings.knowledge_path,
        allowed_statuses=settings.allowed_knowledge_statuses,
    )
    recommendations = InMemoryRecommendationRepository()
    traces = InMemoryTraceRecorder()
    passports = InMemoryCropPassportRepository()
    history = InMemoryHistoryProvider()
    sms = SMSSimulator()
    translator = PassthroughTranslator()
    speech = DisabledSpeechProvider()
    evaluator = RuleEvaluator()
    passport_service = CropPassportService(passports)
    context_builder = CropContextBuilder(
        crop_provider=knowledge,
        history_provider=history,
        weather_provider=weather_provider or UnavailableWeatherProvider(),
        passport_repository=passports,
    )
    engine = AdvisoryEngine(
        context_builder=context_builder,
        tree_selector=CropTreeSelector(),
        knowledge_provider=knowledge,
        evaluator=evaluator,
        constraint_processor=ConstraintProcessor(evaluator),
        mobile_scoring=MobileScoringStrategy(),
        sms_scoring=SMSPriorityScoringStrategy(),
        ranker=Ranker(),
        conflict_resolver=ConflictResolver(),
        recommendation_builder=RecommendationBuilder(),
        trace_recorder=traces,
        recommendation_repository=recommendations,
        history_provider=history,
        passport_service=passport_service,
    )
    return ApplicationContainer(
        settings=settings,
        engine=engine,
        knowledge=knowledge,
        recommendations=recommendations,
        traces=traces,
        passports=passports,
        history=history,
        sms=sms,
        translator=translator,
        speech=speech,
        mobile_formatter=MobileFormatter(),
        sms_formatter=SMSFormatter(settings.sms_max_length),
        voice_formatter=VoiceFormatter(),
    )
