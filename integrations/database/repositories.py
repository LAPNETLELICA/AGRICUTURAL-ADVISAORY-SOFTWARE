"""PostgreSQL implementations of the V1 repository interfaces."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import TypeAdapter
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, sessionmaker

from engine.models.domain import CropPassport
from engine.models.responses import (
    DeliveryReceipt,
    Recommendation,
    TraceRecord,
)
from integrations.database.tables import (
    CropPassportRow,
    HistoryEventRow,
    RecommendationRow,
    SMSDeliveryRow,
    TraceRecordRow,
)
from integrations.database.uow import repository_session

_JSON_DICTIONARY = TypeAdapter(dict[str, Any])


def _text_value(value: object) -> str:
    """Return the value of an enum or the string form of another object."""
    enum_value = getattr(value, "value", value)
    return str(enum_value)


def _event_time(value: object) -> datetime:
    """Convert a history timestamp into a timezone-aware datetime."""
    if isinstance(value, datetime):
        result = value
    elif isinstance(value, str):
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        result = datetime.now(UTC)

    if result.tzinfo is None:
        result = result.replace(tzinfo=UTC)

    return result


def _trace_recommendation_id(trace: TraceRecord) -> str:
    """Read the final recommendation ID from the trace model."""
    value = getattr(trace, "final_recommendation_id", None)

    if value is None:
        value = getattr(trace, "final_recommendation", None)

    if value is None:
        raise ValueError("TraceRecord has no final recommendation ID")

    return str(value)


class PostgresCropPassportRepository:
    def __init__(
        self,
        sessions: sessionmaker[Session],
    ) -> None:
        self._sessions = sessions

    def save(self, passport: CropPassport) -> None:
        payload = passport.model_dump(mode="json")

        current_stage = (
            _text_value(passport.current_stage) if passport.current_stage is not None else None
        )

        with repository_session(self._sessions, write=True) as session:
            session.merge(
                CropPassportRow(
                    passport_id=passport.passport_id,
                    farmer_id=passport.farmer_id,
                    crop_id=passport.crop_id,
                    plot_ref=passport.plot_ref,
                    current_stage=current_stage,
                    opened_at=passport.opened_at,
                    updated_at=passport.updated_at,
                    payload=payload,
                )
            )

    def get(
        self,
        passport_id: str,
    ) -> CropPassport | None:
        with repository_session(self._sessions) as session:
            row = session.get(
                CropPassportRow,
                passport_id,
            )

            if row is None:
                return None

            return CropPassport.model_validate(row.payload)

    def find(
        self,
        farmer_id: str,
        crop_id: str,
        plot_ref: str,
    ) -> CropPassport | None:
        statement = select(CropPassportRow).where(
            CropPassportRow.farmer_id == farmer_id,
            CropPassportRow.crop_id == crop_id,
            CropPassportRow.plot_ref == plot_ref,
        )

        with repository_session(self._sessions) as session:
            row = session.scalars(statement).first()

            if row is None:
                return None

            return CropPassport.model_validate(row.payload)


class PostgresTraceRecorder:
    def __init__(
        self,
        sessions: sessionmaker[Session],
    ) -> None:
        self._sessions = sessions

    def record(self, trace: TraceRecord) -> None:
        payload = trace.model_dump(mode="json")

        with repository_session(self._sessions, write=True) as session:
            session.merge(
                TraceRecordRow(
                    trace_id=trace.trace_id,
                    request_id=trace.request_id,
                    farmer_id=(
                        str(trace.context_used.get("farmer_id"))
                        if isinstance(trace.context_used, dict)
                        and trace.context_used.get("farmer_id")
                        else None
                    ),
                    crop_id=trace.crop_id,
                    channel=_text_value(trace.channel),
                    final_recommendation_id=(_trace_recommendation_id(trace)),
                    started_at=trace.started_at,
                    completed_at=trace.completed_at,
                    payload=payload,
                )
            )

    def get(
        self,
        trace_id: str,
    ) -> TraceRecord | None:
        with repository_session(self._sessions) as session:
            row = session.get(
                TraceRecordRow,
                trace_id,
            )

            if row is None:
                return None

            return TraceRecord.model_validate(row.payload)


class PostgresRecommendationRepository:
    def __init__(
        self,
        sessions: sessionmaker[Session],
    ) -> None:
        self._sessions = sessions

    def save(
        self,
        recommendation: Recommendation,
    ) -> None:
        payload = recommendation.model_dump(mode="json")

        with repository_session(self._sessions, write=True) as session:
            trace_row = session.get(TraceRecordRow, recommendation.trace_id)
            farmer_id = trace_row.farmer_id if trace_row is not None else None
            session.merge(
                RecommendationRow(
                    recommendation_id=(recommendation.recommendation_id),
                    request_id=recommendation.request_id,
                    farmer_id=farmer_id,
                    crop_id=recommendation.crop_id,
                    channel=_text_value(recommendation.channel),
                    trace_id=recommendation.trace_id,
                    created_at=recommendation.created_at,
                    payload=payload,
                )
            )

    def get(
        self,
        recommendation_id: str,
    ) -> Recommendation | None:
        with repository_session(self._sessions) as session:
            row = session.get(
                RecommendationRow,
                recommendation_id,
            )

            if row is None:
                return None

            return Recommendation.model_validate(row.payload)


class PostgresHistoryProvider:
    def __init__(
        self,
        sessions: sessionmaker[Session],
    ) -> None:
        self._sessions = sessions

    def append(
        self,
        farmer_id: str | None,
        event: dict[str, Any],
    ) -> None:
        if not farmer_id:
            return

        crop_id = event.get("crop_id")
        if not isinstance(crop_id, str) or not crop_id:
            raise ValueError("History event requires a crop_id")

        crop_family_value = event.get("crop_family")
        crop_family = str(crop_family_value) if crop_family_value is not None else None

        event_type = str(event.get("event_type", "event"))
        recorded_at = _event_time(event.get("recorded_at"))

        payload = _JSON_DICTIONARY.dump_python(
            event,
            mode="json",
        )
        payload.setdefault("farmer_id", farmer_id)
        payload.setdefault(
            "recorded_at",
            recorded_at.isoformat(),
        )

        recommendation_value = event.get("recommendation_id")
        trace_value = event.get("trace_id")

        with repository_session(self._sessions, write=True) as session:
            session.add(
                HistoryEventRow(
                    farmer_id=farmer_id,
                    crop_id=crop_id,
                    crop_family=crop_family,
                    event_type=event_type,
                    recommendation_id=(
                        str(recommendation_value) if recommendation_value is not None else None
                    ),
                    trace_id=(str(trace_value) if trace_value is not None else None),
                    recorded_at=recorded_at,
                    payload=payload,
                )
            )

    def get_relevant_history(
        self,
        farmer_id: str | None,
        crop_id: str,
        crop_family: str | None,
    ) -> list[dict[str, Any]]:
        if not farmer_id:
            return []

        crop_condition = HistoryEventRow.crop_id == crop_id

        if crop_family:
            crop_condition = or_(
                crop_condition,
                HistoryEventRow.crop_family == crop_family,
            )

        statement = (
            select(HistoryEventRow)
            .where(
                HistoryEventRow.farmer_id == farmer_id,
                crop_condition,
            )
            .order_by(HistoryEventRow.recorded_at)
        )

        with repository_session(self._sessions) as session:
            rows = session.scalars(statement).all()
            return [dict(row.payload) for row in rows]


class PostgresSMSProvider:
    def __init__(
        self,
        sessions: sessionmaker[Session],
    ) -> None:
        self._sessions = sessions

    def send(
        self,
        recipient_id: str,
        crop_id: str,
        message: str,
        recommendation_id: str | None = None,
    ) -> DeliveryReceipt:
        receipt = DeliveryReceipt(
            recipient_id=recipient_id,
            crop_id=crop_id,
            message=message,
            recommendation_id=recommendation_id,
        )

        payload = receipt.model_dump(mode="json")

        with repository_session(self._sessions, write=True) as session:
            farmer_id: str | None = None
            if recommendation_id:
                recommendation_row = session.get(RecommendationRow, recommendation_id)
                if recommendation_row is not None:
                    farmer_id = recommendation_row.farmer_id
            session.merge(
                SMSDeliveryRow(
                    delivery_id=receipt.delivery_id,
                    recipient_id=receipt.recipient_id,
                    farmer_id=farmer_id,
                    crop_id=receipt.crop_id,
                    recommendation_id=(receipt.recommendation_id),
                    status=_text_value(receipt.status),
                    message=receipt.message,
                    delivered_at=receipt.delivered_at,
                    payload=payload,
                )
            )

        return receipt

    def inbox(
        self,
        recipient_id: str,
    ) -> list[DeliveryReceipt]:
        statement = (
            select(SMSDeliveryRow)
            .where(SMSDeliveryRow.recipient_id == recipient_id)
            .order_by(SMSDeliveryRow.delivered_at)
        )

        with repository_session(self._sessions) as session:
            rows = session.scalars(statement).all()

            return [DeliveryReceipt.model_validate(row.payload) for row in rows]
