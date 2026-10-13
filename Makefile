.PHONY: test validate run lint format-check typecheck

test:
	pytest

validate:
	python -m scripts.validate_knowledge

run:
	uvicorn api.app:app --reload

lint:
	ruff check .

format-check:
	ruff format --check .

typecheck:
	mypy
