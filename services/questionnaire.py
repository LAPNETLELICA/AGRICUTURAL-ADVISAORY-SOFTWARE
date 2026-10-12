"""Adaptive, knowledge-first farmer questionnaire."""

from dataclasses import dataclass, field
from typing import Any

from engine.models.requests import EvidenceInput, MobileAdvisoryRequest


@dataclass(frozen=True, slots=True)
class QuestionnaireStep:
    key: str
    prompt: str
    options: list[str] = field(default_factory=list)
    accepts_free_text: bool = True
    known_context: dict[str, Any] = field(default_factory=dict)


class QuestionnaireService:
    def __init__(self, knowledge: Any) -> None:
        self._knowledge = knowledge

    def start(
        self, *, profile_level: str, region: str | None = None, locality: str | None = None
    ) -> QuestionnaireStep:
        del profile_level
        context = self._known_context(region, locality)
        return QuestionnaireStep(
            key="intent",
            prompt="What do you need help with today? You may also type your own question.",
            options=["Start farming", "Existing crop problem", "Improve soil", "When to plant"],
            known_context=context,
        )

    def answer(self, context: dict[str, Any], answer: str) -> QuestionnaireStep:
        known = self._known_context(context.get("region"), context.get("locality"))
        normalized_answer = answer.casefold()
        if any(word in normalized_answer for word in ("spot", "leaf", "leaves", "yellow", "pest")):
            return QuestionnaireStep(
                key="crop_problem",
                prompt="Please describe when the problem started. You can also add a picture if available.",
                options=["Less than one week", "More than one week", "I do not know"],
                known_context=known,
            )
        if answer == "start_farming" and not known:
            return QuestionnaireStep(
                key="topography",
                prompt="I do not have terrain information for your locality. Is your land flat, sloping, or low/wet?",
                options=["Flat", "Sloping", "Low/wet", "I do not know"],
            )
        if answer == "start_farming":
            return QuestionnaireStep(
                key="previous_crop",
                prompt="What crop was cultivated here before, and what manure or fertiliser do you usually use?",
                options=["No previous crop", "Poultry manure", "Cattle manure", "Compost", "I do not know"],
                known_context=known,
            )
        return QuestionnaireStep(
            key="free_text",
            prompt="Please describe your issue, or choose an option above.",
            known_context=known,
        )

    def complete(self, context: dict[str, Any]) -> MobileAdvisoryRequest:
        """Map collected answers to the unchanged mobile advisory contract."""
        practices = {"usual_manure": context["usual_manure"]} if context.get("usual_manure") else {}
        return MobileAdvisoryRequest(
            farmer_id=str(context["farmer_id"]),
            crop_id=context.get("crop_id"),
            crop_description=context.get("crop_description"),
            crop_discovery=bool(context.get("crop_discovery", False)),
            question=str(context["question"]),
            region=context.get("region"),
            locality=context.get("locality"),
            evidence=EvidenceInput(practices=practices),
        )

    def _known_context(self, region: str | None, locality: str | None) -> dict[str, Any]:
        raw = self._knowledge.locality_context(region, locality)
        if not raw:
            return {}
        return {
            "topography": {"altitude_m": raw.get("altitude_m")},
            "soil_types": raw.get("sols", []),
            "local_risks": raw.get("risques_locaux", []),
            "agricultural_profile": raw.get("profil_agricole"),
        }
