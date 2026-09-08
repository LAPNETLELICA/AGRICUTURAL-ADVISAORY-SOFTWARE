#!/usr/bin/env python3
"""Verify the repository ownership layout required by conception-book Section 14."""

from __future__ import annotations

from pathlib import Path


REQUIRED_DIRECTORIES = (
    "engine/advisory",
    "engine/models",
    "engine/interfaces",
    "knowledge/crops",
    "knowledge/soils",
    "knowledge/regional",
    "knowledge/topography",
    "knowledge/climate",
    "knowledge/timing",
    "knowledge/practices",
    "knowledge/risks",
    "knowledge/rules",
    "integrations/weather",
    "integrations/translation",
    "integrations/speech",
    "integrations/sms/simulator",
    "languages",
    "api",
    "tests/engine",
    "tests/rules",
    "tests/integrations",
    "tests/scenarios",
)

REQUIRED_FILES = (
    "engine/advisory/engine.py",
    "engine/advisory/evaluator.py",
    "engine/advisory/scoring.py",
    "engine/advisory/recommendation.py",
    "engine/advisory/selector.py",
    "engine/advisory/constraints.py",
    "engine/advisory/ranking.py",
    "engine/advisory/conflict.py",
    "api/mobile.py",
    "api/sms.py",
)

FORBIDDEN_PATHS = (
    "src/agricultural_advisory",
    "knowledge/demo",
)


def validate_layout(root: Path) -> list[str]:
    """Return human-readable alignment failures for a repository root."""
    failures = [
        f"missing required directory: {path}"
        for path in REQUIRED_DIRECTORIES
        if not (root / path).is_dir()
    ]
    failures.extend(
        f"missing required file: {path}"
        for path in REQUIRED_FILES
        if not (root / path).is_file()
    )
    failures.extend(
        f"legacy path must not exist: {path}"
        for path in FORBIDDEN_PATHS
        if (root / path).exists()
    )
    return failures


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    failures = validate_layout(root)
    if failures:
        print("SECTION 14 STRUCTURE CHECK FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("SECTION 14 STRUCTURE CHECK PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
