"""Channel-specific rendering performed after canonical reasoning."""

from __future__ import annotations

from engine.models.responses import Recommendation


class MobileFormatter:
    def format(self, recommendation: Recommendation) -> dict[str, object]:
        return recommendation.model_dump(mode="json")


class SMSFormatter:
    def __init__(self, max_length: int = 160) -> None:
        self._max_length = max_length

    def format(self, recommendation: Recommendation) -> str:
        sections = [
            f"{recommendation.crop_id}: {recommendation.primary.summary}",
        ]
        if recommendation.actions:
            sections.append(f"Action: {recommendation.actions[0]}")
        if recommendation.warnings:
            sections.append(f"Warning: {recommendation.warnings[0]}")
        return self._truncate(" ".join(sections))

    def _truncate(self, text: str) -> str:
        if len(text) <= self._max_length:
            return text
        cutoff = max(1, self._max_length - 3)
        shortened = text[:cutoff].rsplit(" ", 1)[0]
        return f"{shortened or text[:cutoff]}..."


class VoiceFormatter:
    def format(self, recommendation: Recommendation) -> str:
        sections = [recommendation.primary.summary]
        if recommendation.reasons:
            sections.append(f"Reason: {recommendation.reasons[0]}")
        if recommendation.actions:
            sections.append(f"Action: {recommendation.actions[0]}")
        if recommendation.warnings:
            sections.append(f"Warning: {recommendation.warnings[0]}")
        return " ".join(sections)

