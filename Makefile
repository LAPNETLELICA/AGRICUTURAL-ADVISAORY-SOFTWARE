.PHONY: install run test test-fast coverage lint typecheck check-structure validate-knowledge demo smoke offline-check

install:
	uv sync --extra dev

run:
	uv run uvicorn api.app:app --reload --host 0.0.0.0 --port 8000

test:
	uv run pytest

test-fast:
	uv run pytest -m "not scenario"

coverage:
	uv run pytest --cov=api --cov=engine --cov=integrations --cov=languages --cov-report=term-missing --cov-report=html

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run mypy

check-structure:
	python scripts/check_structure.py

validate-knowledge:
	uv run python scripts/validate_knowledge.py knowledge --allow-status draft --allow-status validated

demo:
	uv run python scripts/demo_request.py

smoke:
	uv run python scripts/smoke_test.py

offline-check:
	PYTHONPATH=. python scripts/self_test.py
