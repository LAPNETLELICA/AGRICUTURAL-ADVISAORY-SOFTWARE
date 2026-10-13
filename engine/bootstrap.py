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
from engine.interfaces.providers import (
    CropPassportRepository,
    HistoryProvider,
    RecommendationRepository,
    SMSProvider,
    SpeechProvider,
    TraceRecorder,
    TranscriptionProvider,
    TranslationProvider,
    WeatherProvider,
)
from engine.models.history import InMemoryHistoryProvider
from engine.models.repositories import (
    InMemoryConversationRepository,
    InMemoryCropPassportRepository,
    InMemoryRecommendationRepository,
    InMemoryTraceRecorder,
)
from integrations.cameroon_knowledge import CameroonKnowledgeProvider
from integrations.database import (
    Database,
    PostgresCropPassportRepository,
    PostgresHistoryProvider,
    PostgresRecommendationRepository,
    PostgresSMSProvider,
    PostgresTraceRecorder,
)
from integrations.database.uow import DatabaseUnitOfWork
from integrations.presentation import MobileFormatter, SMSFormatter, VoiceFormatter
from integrations.sms.simulator import SMSSimulator
from integrations.sms.tranzak import TranzakSMSProvider
from integrations.speech.disabled import DisabledSpeechProvider, DisabledTranscriptionProvider
from integrations.speech.fish_audio import FishAudioSpeechProvider
from integrations.speech.groq import GroqTranscriptionProvider
from integrations.translation.passthrough import PassthroughTranslator
from integrations.weather.providers import UnavailableWeatherProvider
from integrations.weather.openweathermap import OpenWeatherMapProvider


def _configured_key(value: str | None) -> bool:
    """Reject sample values while allowing only real provider credentials."""
    return bool(value) and not value.startswith(("your_actual_", "gsk_your_actual"))


def _configured_tranzak(settings: Settings) -> bool:
    return (
        settings.sms_provider == "tranzak"
        and all(
            _configured_key(value)
            for value in (
                settings.tranzak_app_id,
                settings.tranzak_app_key,
                settings.tranzak_sender_id,
            )
        )
    )


@dataclass(slots=True)
class ApplicationContainer:
    settings: Settings
    database: Database | None
    engine: AdvisoryEngine
    knowledge: CameroonKnowledgeProvider
    recommendations: RecommendationRepository
    traces: TraceRecorder
    passports: CropPassportRepository
    history: HistoryProvider
    sms: SMSProvider
    translator: TranslationProvider
    speech: SpeechProvider
    transcription: TranscriptionProvider
    mobile_formatter: MobileFormatter
    sms_formatter: SMSFormatter
    voice_formatter: VoiceFormatter
    conversations: InMemoryConversationRepository


def build_container(
    settings: Settings,
    *,
    weather_provider: WeatherProvider | None = None,
    translation_provider: TranslationProvider | None = None,
    speech_provider: SpeechProvider | None = None,
    transcription_provider: TranscriptionProvider | None = None,
    sms_provider: SMSProvider | None = None,
) -> ApplicationContainer:
    knowledge = CameroonKnowledgeProvider(settings.knowledge_path)

    database: Database | None = None

    recommendations: RecommendationRepository
    traces: TraceRecorder
    passports: CropPassportRepository
    history: HistoryProvider
    sms: SMSProvider

    transaction_manager: DatabaseUnitOfWork | None = None
    configured_sms = sms_provider or (
        TranzakSMSProvider(
            settings.tranzak_app_id or "",
            settings.tranzak_app_key or "",
            settings.tranzak_sender_id or "",
            base_url=settings.tranzak_base_url,
            timeout=settings.tranzak_timeout_seconds,
        )
        if _configured_tranzak(settings)
        else None
    )

    if settings.database_url:
        database = Database(settings.database_url)
        database.ping()
        transaction_manager = DatabaseUnitOfWork(database.sessions)

        recommendations = PostgresRecommendationRepository(database.sessions)
        traces = PostgresTraceRecorder(database.sessions)
        passports = PostgresCropPassportRepository(database.sessions)
        history = PostgresHistoryProvider(database.sessions)
        sms = configured_sms or PostgresSMSProvider(database.sessions)
    else:
        recommendations = InMemoryRecommendationRepository()
        traces = InMemoryTraceRecorder()
        passports = InMemoryCropPassportRepository()
        history = InMemoryHistoryProvider()
        sms = configured_sms or SMSSimulator()

    translator = translation_provider or PassthroughTranslator()
    speech = speech_provider or (
        FishAudioSpeechProvider(settings.fish_audio_api_key)
        if settings.speech_provider == "fish_audio" and _configured_key(settings.fish_audio_api_key)
        else DisabledSpeechProvider()
    )
    transcription = transcription_provider or (
        GroqTranscriptionProvider(settings.groq_api_key)
        if settings.transcription_provider == "groq" and _configured_key(settings.groq_api_key)
        else DisabledTranscriptionProvider()
    )
    evaluator = RuleEvaluator()
    passport_service = CropPassportService(passports)

    context_builder = CropContextBuilder(
        crop_provider=knowledge,
        history_provider=history,
        weather_provider=(
            weather_provider
            or (
                OpenWeatherMapProvider(settings.openweathermap_api_key)
                if settings.weather_provider == "openweathermap"
                and _configured_key(settings.openweathermap_api_key)
                else UnavailableWeatherProvider()
            )
        ),
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
        transaction_manager=transaction_manager,
    )

    return ApplicationContainer(
        settings=settings,
        database=database,
        engine=engine,
        knowledge=knowledge,
        recommendations=recommendations,
        traces=traces,
        passports=passports,
        history=history,
        sms=sms,
        translator=translator,
        speech=speech,
        transcription=transcription,
        mobile_formatter=MobileFormatter(),
        sms_formatter=SMSFormatter(settings.sms_max_length),
        voice_formatter=VoiceFormatter(),
        conversations=InMemoryConversationRepository(),
    )
