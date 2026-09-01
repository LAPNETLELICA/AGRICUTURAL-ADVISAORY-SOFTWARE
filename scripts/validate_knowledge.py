#!/usr/bin/env python3
"""Validate a Developer 2 knowledge directory against shared Pydantic contracts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from engine.exceptions import KnowledgeValidationError
from integrations.knowledge import JSONKnowledgeProvider


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        type=Path,
        help="Section 14 knowledge root containing crops/ and the T1-T7 rule folders",
    )
    parser.add_argument(
        "--allow-status",
        action="append",
        choices=["draft", "validated", "deprecated", "test_only"],
        dest="statuses",
        help="Status to load; repeat this option as needed",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    statuses = set(args.statuses or ["validated"])
    try:
        provider = JSONKnowledgeProvider(args.path, statuses)
    except (KnowledgeValidationError, ValueError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"valid": True, **provider.metadata()}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
