#!/usr/bin/env python3
"""Read-only preflight for the live ``zg361we.356`` source capture input."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from zg361_phase2_cross_cycle_endgame_source_capture import (
    EndgameSourceCaptureError,
    preflight_endgame_source_capture_prefix,
)


def main(
    prefix: Path,
    *,
    expected_seed_lineage_id: str | None = None,
    expected_lineage_set_id: str | None = None,
) -> int:
    result = preflight_endgame_source_capture_prefix(
        prefix,
        expected_seed_lineage_id=expected_seed_lineage_id,
        expected_lineage_set_id=expected_lineage_set_id,
    )
    identity = (
        {"lineage_set_id": result["lineage_set_id"]}
        if "lineage_set_id" in result
        else {"seed_lineage_id": result["seed_lineage_id"]}
    )
    print(
        json.dumps(
            {
                "schema_version": 1,
                "result": "GREEN",
                "readiness": "live-pending-endgame-source",
                **identity,
                "validated_handlers": result["handlers"],
                "entry_count": result["entry_count"],
                "ck3_launched": False,
                "fixture_used": False,
                "console_used": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", required=True, type=Path)
    identity_group = parser.add_mutually_exclusive_group(required=True)
    identity_group.add_argument("--expected-seed-lineage-id")
    identity_group.add_argument("--expected-lineage-set-id")
    arguments = parser.parse_args()
    try:
        raise SystemExit(
            main(
                arguments.prefix,
                expected_seed_lineage_id=arguments.expected_seed_lineage_id,
                expected_lineage_set_id=arguments.expected_lineage_set_id,
            )
        )
    except EndgameSourceCaptureError as error:
        print(json.dumps(error.evidence, ensure_ascii=False, sort_keys=True))
        raise SystemExit(1)
