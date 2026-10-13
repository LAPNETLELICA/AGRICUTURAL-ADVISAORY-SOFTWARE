#!/usr/bin/env python3
"""Smoke-test a running API using only the Python standard library."""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from typing import Any


def request_json(base_url: str, path: str, payload: dict[str, Any] | None = None) -> Any:
    body = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST" if body is not None else "GET",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        if response.status != 200:
            raise RuntimeError(f"{path} returned {response.status}")
        return json.load(response)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    try:
        health = request_json(args.base_url, "/api/v1/health")
        crops = request_json(args.base_url, "/api/v1/crops")
        recommendation = request_json(
            args.base_url,
            "/api/v1/advisory/mobile",
            {
                "farmer_id": "smoke-farmer",
                "crop_id": "irish-potato",
                "question": "How can I improve my yield?",
                "region": "West",
                "locality": "Bafoussam",
                "evidence": {
                    "soil": {"drainage": "poor"},
                    "weather": {"rainfall_class": "heavy", "consecutive_rain_days": 3},
                    "future": {"month": 8},
                },
            },
        )
        detail = request_json(
            args.base_url,
            f"/api/v1/recommendations/{recommendation['recommendation_id']}",
        )
    except (urllib.error.URLError, KeyError, RuntimeError) as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    assert health["status"] == "ok"
    assert any(crop["crop_id"] == "irish-potato" for crop in crops)
    assert detail["trace"]["trace_id"] == recommendation["trace_id"]
    print("SMOKE TEST PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
