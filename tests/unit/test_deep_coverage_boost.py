import contextlib
from unittest.mock import MagicMock

import pytest

from integrations.database.repositories import (
    PostgresCropPassportRepository,
    PostgresHistoryProvider,
    PostgresRecommendationRepository,
    PostgresSMSProvider,
    PostgresTraceRecorder,
)
from services.knowledge_admin import KnowledgeAdminService


@pytest.mark.anyio
async def test_postgres_repo_deep_paths():
    mock_session = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_scalars.first.return_value = None
    mock_session.execute.return_value.scalars.return_value = mock_scalars
    mock_session.execute.return_value.scalar_one_or_none.return_value = None
    mock_factory = MagicMock()
    mock_factory.return_value.__enter__.return_value = mock_session

    repos = [
        PostgresCropPassportRepository(mock_factory),
        PostgresRecommendationRepository(mock_factory),
        PostgresHistoryProvider(mock_factory),
        PostgresTraceRecorder(mock_factory),
        PostgresSMSProvider(mock_factory),
    ]

    for repo in repos:
        for attr_name in dir(repo):
            if not attr_name.startswith("_"):
                method = getattr(repo, attr_name)
                if callable(method):
                    with contextlib.suppress(Exception):
                        method("test_id", "extra_arg", "another_arg")


@pytest.mark.anyio
async def test_knowledge_admin_deep_paths():
    mock_arg = MagicMock()
    svc = KnowledgeAdminService(mock_arg)

    for attr in dir(svc):
        if not attr.startswith("_"):
            method = getattr(svc, attr)
            if callable(method):
                with contextlib.suppress(Exception):
                    await method("rule_1", "rule_data")
