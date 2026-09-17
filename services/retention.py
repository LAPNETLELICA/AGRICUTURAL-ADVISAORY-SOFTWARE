"""Retention enforcement for farmer operational data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select

from engine.config import Settings
from integrations.database.connection import Database
from integrations.database.tables import (
    AuditEventRow,
    HistoryEventRow,
    RecommendationRow,
    SMSDeliveryRow,
    TraceRecordRow,
)
from services.media import MediaService


@dataclass(frozen=True, slots=True)
class RetentionResult:
    media: int = 0
    traces: int = 0
    history: int = 0
    sms: int = 0
    audit: int = 0


class RetentionService:
    def __init__(self, database: Database | None, media: MediaService, settings: Settings) -> None:
        self._database = database
        self._media = media
        self._settings = settings

    def cleanup(self, now: datetime | None = None) -> RetentionResult:
        moment = now or datetime.now(UTC)
        media_count = self._media.purge_expired(moment)
        if self._database is None:
            return RetentionResult(media=media_count)

        cutoffs = {
            "traces": moment - timedelta(days=self._settings.trace_retention_days),
            "history": moment - timedelta(days=self._settings.history_retention_days),
            "sms": moment - timedelta(days=self._settings.sms_retention_days),
            "audit": moment - timedelta(days=self._settings.audit_retention_days),
        }
        with self._database.sessions.begin() as session:
            old_trace_ids = session.scalars(
                select(TraceRecordRow.trace_id).where(
                    TraceRecordRow.completed_at < cutoffs["traces"]
                )
            ).all()
            if old_trace_ids:
                session.execute(
                    delete(RecommendationRow).where(RecommendationRow.trace_id.in_(old_trace_ids))
                )
                trace_ids = (
                    session.execute(
                        delete(TraceRecordRow).where(TraceRecordRow.trace_id.in_(old_trace_ids))
                    ).rowcount
                    or 0
                )
            else:
                trace_ids = 0
            history = (
                session.execute(
                    delete(HistoryEventRow).where(HistoryEventRow.recorded_at < cutoffs["history"])
                ).rowcount
                or 0
            )
            sms = (
                session.execute(
                    delete(SMSDeliveryRow).where(SMSDeliveryRow.delivered_at < cutoffs["sms"])
                ).rowcount
                or 0
            )
            audit = (
                session.execute(
                    delete(AuditEventRow).where(AuditEventRow.created_at < cutoffs["audit"])
                ).rowcount
                or 0
            )
        return RetentionResult(
            media=media_count,
            traces=trace_ids,
            history=history,
            sms=sms,
            audit=audit,
        )
