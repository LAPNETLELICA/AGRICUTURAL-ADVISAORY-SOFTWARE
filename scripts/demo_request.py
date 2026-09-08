#!/usr/bin/env python3
"""Run the conception book's Bafoussam/Irish-potato scenario without HTTP."""

from __future__ import annotations

from pathlib import Path

from engine.bootstrap import build_container
from engine.config import Settings
from engine.models.requests import (
    AdvisoryRequest,
    EvidenceInput,
    MobileAdvisoryRequest,
)
from integrations.weather import StaticWeatherProvider


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    container = build_container(
        Settings(environment="development", knowledge_path=root / "knowledge"),
        weather_provider=StaticWeatherProvider(
            current={"rainfall_class": "heavy", "consecutive_rain_days": 3},
            forecast={"month": 8},
        ),
    )
    request = MobileAdvisoryRequest(
        farmer_id="demo-farmer",
        crop_id="irish-potato",
        question="How can I improve yield and prepare this plot?",
        objective="yield_improvement",
        region="West",
        locality="Bafoussam",
        current_stage="pre-planting",
        evidence=EvidenceInput(
            soil={"drainage": "poor"},
            topography={"landform": "flatland"},
            weather={"rainfall_class": "heavy", "consecutive_rain_days": 3},
            future={"month": 8},
        ),
    )
    recommendation = container.engine.advise(AdvisoryRequest.from_mobile(request))
    print(recommendation.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
