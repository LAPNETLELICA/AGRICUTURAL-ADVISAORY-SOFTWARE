"""Minimal access/audit log stored separately from advisory traces."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from integrations.database.connection import Database
from integrations.database.tables import AuditEventRow


class AuditService:
    def __init__(self, database: Database | None, retention_days: int) -> None:
        self._database = database
        self._retention_days = retention_days

    def record(
        self,
        *,
        actor_id: str | None,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        success: bool = True,
        details: dict[str, Any] | None = None,
    ) -> None:
        if self._database is None:
            return
        now = datetime.now(UTC)
        with self._database.sessions.begin() as session:
            session.add(
                AuditEventRow(
                    actor_id=actor_id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    success=success,
                    created_at=now,
                    expires_at=now + timedelta(days=self._retention_days),
                    details=details or {},
                )
            )
