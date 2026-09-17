"""Farmer data export/deletion operations for V1 privacy controls."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from sqlalchemy import delete, or_, select

from integrations.database.connection import Database
from integrations.database.tables import (
    CropPassportRow,
    HistoryEventRow,
    RecommendationRow,
    SMSDeliveryRow,
    TraceRecordRow,
)
from services.media import MediaService


@dataclass(frozen=True, slots=True)
class PrivacyDeletionResult:
    crop_passports: int
    history_events: int
    recommendations: int
    traces: int
    sms_deliveries: int
    media: int

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


class PrivacyService:
    def __init__(self, database: Database | None, media: MediaService) -> None:
        self._database = database
        self._media = media

    def export_farmer(self, farmer_id: str) -> dict[str, Any]:
        result: dict[str, Any] = {
            "farmer_id": farmer_id,
            "crop_passports": [],
            "history_events": [],
            "recommendations": [],
            "traces": [],
            "sms_deliveries": [],
            "media": [asdict(item) for item in self._media.list_for_farmer(farmer_id)],
        }
        if self._database is None:
            return result

        with self._database.sessions() as session:
            passports = session.scalars(
                select(CropPassportRow).where(CropPassportRow.farmer_id == farmer_id)
            ).all()
            history = session.scalars(
                select(HistoryEventRow).where(HistoryEventRow.farmer_id == farmer_id)
            ).all()
            recommendations = session.scalars(
                select(RecommendationRow).where(RecommendationRow.farmer_id == farmer_id)
            ).all()
            traces = session.scalars(
                select(TraceRecordRow).where(TraceRecordRow.farmer_id == farmer_id)
            ).all()
            sms = session.scalars(
                select(SMSDeliveryRow).where(
                    or_(
                        SMSDeliveryRow.farmer_id == farmer_id,
                        SMSDeliveryRow.recipient_id == farmer_id,
                    )
                )
            ).all()

            result["crop_passports"] = [row.payload for row in passports]
            result["history_events"] = [row.payload for row in history]
            result["recommendations"] = [row.payload for row in recommendations]
            result["traces"] = [row.payload for row in traces]
            result["sms_deliveries"] = [row.payload for row in sms]
        return result

    def delete_farmer(self, farmer_id: str) -> PrivacyDeletionResult:
        media = self._media.delete_farmer_media(farmer_id)
        if self._database is None:
            return PrivacyDeletionResult(0, 0, 0, 0, 0, media)

        with self._database.sessions.begin() as session:
            history = (
                session.execute(
                    delete(HistoryEventRow).where(HistoryEventRow.farmer_id == farmer_id)
                ).rowcount
                or 0
            )
            recommendations = (
                session.execute(
                    delete(RecommendationRow).where(RecommendationRow.farmer_id == farmer_id)
                ).rowcount
                or 0
            )
            traces = (
                session.execute(
                    delete(TraceRecordRow).where(TraceRecordRow.farmer_id == farmer_id)
                ).rowcount
                or 0
            )
            passports = (
                session.execute(
                    delete(CropPassportRow).where(CropPassportRow.farmer_id == farmer_id)
                ).rowcount
                or 0
            )
            sms = (
                session.execute(
                    delete(SMSDeliveryRow).where(
                        or_(
                            SMSDeliveryRow.farmer_id == farmer_id,
                            SMSDeliveryRow.recipient_id == farmer_id,
                        )
                    )
                ).rowcount
                or 0
            )

        return PrivacyDeletionResult(
            crop_passports=passports,
            history_events=history,
            recommendations=recommendations,
            traces=traces,
            sms_deliveries=sms,
            media=media,
        )
