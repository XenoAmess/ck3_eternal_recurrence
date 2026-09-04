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


def main(prefix: Path, *, expected_seed_lineage_id: str) -> int:
    result = preflight_endgame_source_capture_prefix(
        prefix,
        expected_seed_lineage_id=expected_seed_lineage_id,
    )
    print(
        json.dumps(
            {
                "schema_version": 1,
                "result": "GREEN",
                "readiness": "live-pending-endgame-source",
                "seed_lineage_id": result["seed_lineage_id"],
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
    parser.add_argument("--expected-seed-lineage-id", required=True)
    arguments = parser.parse_args()
    try:
        raise SystemExit(
            main(
                arguments.prefix,
                expected_seed_lineage_id=arguments.expected_seed_lineage_id,
            )
        )
    except EndgameSourceCaptureError as error:
        print(json.dumps(error.evidence, ensure_ascii=False, sort_keys=True))
        raise SystemExit(1)
