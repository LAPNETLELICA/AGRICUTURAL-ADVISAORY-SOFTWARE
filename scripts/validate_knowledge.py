#!/usr/bin/env python3
"""Validate the authoritative Cameroon agricultural knowledge base."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from engine.exceptions import KnowledgeValidationError
from integrations.cameroon_knowledge import CameroonKnowledgeProvider


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        type=Path,
        nargs="?",
        default=Path("BASE_CONNAISSANCES_AGRICOLES"),
        help="Cameroon knowledge-base root",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        provider = CameroonKnowledgeProvider(args.path)
    except (KnowledgeValidationError, ValueError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"valid": True, **provider.metadata()}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
