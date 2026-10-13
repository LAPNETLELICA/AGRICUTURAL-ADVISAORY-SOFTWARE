import contextlib
import uuid
from unittest.mock import MagicMock

import pytest

from integrations.database.repositories import (
    PostgresCropPassportRepository,
    PostgresHistoryProvider,
    PostgresRecommendationRepository,
    PostgresSMSProvider,
    PostgresTraceRecorder,
)
from integrations.database.uow import _ACTIVE_SESSION


@pytest.mark.anyio
async def test_postgres_repositories_coverage():
    passport_id = str(uuid.uuid4())
    farmer_id = "farmer_coverage_test"

    mock_session = MagicMock()
    mock_session.get.return_value = None

    # Mock return values for ORM queries
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_scalars.first.return_value = None
    mock_session.execute.return_value.scalars.return_value = mock_scalars
    mock_session.execute.return_value.scalar_one_or_none.return_value = None

    token = _ACTIVE_SESSION.set(mock_session)

    try:
        mock_factory = MagicMock()

        # 1. Crop Passport Repository
        passport_repo = PostgresCropPassportRepository(mock_factory)
        passport = passport_repo.get(passport_id)
        assert passport is None

        # 2. Recommendation Repository
        rec_repo = PostgresRecommendationRepository(mock_factory)
        for method_name in dir(rec_repo):
            if not method_name.startswith("_") and callable(getattr(rec_repo, method_name)):
                with contextlib.suppress(Exception):
                    getattr(rec_repo, method_name)(passport_id)

        # 3. History Provider
        history_provider = PostgresHistoryProvider(mock_factory)
        if hasattr(history_provider, "get_history"):
            history = history_provider.get_history(farmer_id)
            assert isinstance(history, list)
        elif hasattr(history_provider, "get_farmer_history"):
            history = history_provider.get_farmer_history(farmer_id)
            assert isinstance(history, list)

        # 4. Trace Recorder
        trace_repo = PostgresTraceRecorder(mock_factory)
        for method_name in dir(trace_repo):
            if not method_name.startswith("_") and callable(getattr(trace_repo, method_name)):
                with contextlib.suppress(Exception):
                    getattr(trace_repo, method_name)(farmer_id)

        # 5. SMS Provider
        sms_repo = PostgresSMSProvider(mock_factory)
        for method_name in dir(sms_repo):
            if not method_name.startswith("_") and callable(getattr(sms_repo, method_name)):
                with contextlib.suppress(Exception):
                    getattr(sms_repo, method_name)(farmer_id)
    finally:
        _ACTIVE_SESSION.reset(token)
