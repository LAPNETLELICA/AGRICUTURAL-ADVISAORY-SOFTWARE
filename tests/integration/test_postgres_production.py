"""Production PostgreSQL reliability checks.

Set TEST_DATABASE_URL to an ephemeral PostgreSQL database. The suite intentionally does
not run against DATABASE_URL so a developer cannot accidentally modify production data.
"""

from __future__ import annotations

import os
import subprocess
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select, text

from integrations.database.connection import Database
from integrations.database.tables import AuditEventRow
from integrations.database.uow import DatabaseUnitOfWork, repository_session

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="TEST_DATABASE_URL is required for ephemeral PostgreSQL integration tests",
)


@pytest.fixture(scope="module")
def postgres_database() -> Database:
    assert TEST_DATABASE_URL is not None
    environment = os.environ.copy()
    environment["DATABASE_URL"] = TEST_DATABASE_URL
    subprocess.run(["alembic", "upgrade", "head"], check=True, env=environment)
    database = Database(TEST_DATABASE_URL)
    yield database
    database.close()


def test_postgres_migration_and_ping(postgres_database: Database) -> None:
    postgres_database.ping()
    with postgres_database.engine.connect() as connection:
        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    assert revision == "9b81c2276e10"


def test_postgres_uow_rolls_back_atomically(postgres_database: Database) -> None:
    uow = DatabaseUnitOfWork(postgres_database.sessions)
    now = datetime.now(UTC)
    before: int
    with postgres_database.sessions() as session:
        before = session.scalar(select(func.count()).select_from(AuditEventRow)) or 0

    with pytest.raises(RuntimeError, match="rollback"), uow.transaction():
        with repository_session(postgres_database.sessions, write=True) as session:
            session.add(
                AuditEventRow(
                    actor_id="integration-test",
                    action="uow.test",
                    resource_type="test",
                    resource_id="rollback",
                    success=True,
                    created_at=now,
                    expires_at=now + timedelta(days=1),
                    details={},
                )
            )
        raise RuntimeError("rollback")

    with postgres_database.sessions() as session:
        after = session.scalar(select(func.count()).select_from(AuditEventRow)) or 0
    assert after == before
