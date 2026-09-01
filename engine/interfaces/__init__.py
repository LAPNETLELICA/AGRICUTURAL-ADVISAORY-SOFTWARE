"""Stable interfaces between engine, knowledge, and integrations."""

from engine.interfaces.providers import (
    CropPassportRepository,
    CropProvider,
    HistoryProvider,
    KnowledgeProvider,
    RecommendationRepository,
    SMSProvider,
    SpeechProvider,
    TraceRecorder,
    TranslationProvider,
    WeatherProvider,
)

__all__ = [
    "CropPassportRepository",
    "CropProvider",
    "HistoryProvider",
    "KnowledgeProvider",
    "RecommendationRepository",
    "SMSProvider",
    "SpeechProvider",
    "TraceRecorder",
    "TranslationProvider",
    "WeatherProvider",
]
