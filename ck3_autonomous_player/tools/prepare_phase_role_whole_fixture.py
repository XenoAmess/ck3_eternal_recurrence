"""Root-only whole V2 DTO seed for the new loaded-event role FIRST.

Reuse the held fixture's base operands, not a generated calendar leaf. Only
identity cases are changed. No EXE, process, game or service is opened here.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from prepare_phase_calendar_whole_fixture import _cpp_seed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()
    saved = json.loads(args.base.read_text(encoding="utf-8-sig"))
    body = copy.deepcopy(saved["frame"]["combat_simulation_inputs"])
    first = body["armies"][0]
    members = first["knights"]["members"]
    members[0]["character_id"] = first["commander"]["character_id"]
    members[1]["character_id"] = 0
    members[2]["character_id"] = 0x05007485
    args.out_dir.mkdir(parents=True, exist_ok=True)
    seed = _cpp_seed(body).replace("SeedPhaseCalendarWholeV2Fixture", "SeedPhaseRoleWholeV2Fixture")
    (args.out_dir / "phase-role-base-seed.inc").write_text(seed, encoding="utf-8")
    (args.out_dir / "FIXTURE-PROVENANCE.json").write_text(json.dumps({
        "schema_version": 1, "source_base": str(args.base),
        "source_only_fixture": True, "actual4_live_observation": False,
        "loaded_role_operands": [0, 1, 7, 1],
        "scenes": ["available", "partial_row2", "null_singleton"],
        "identity_cases": ["same Character Commander and Knight", "FullCharacterID zero", "generation-bearing FullCharacterID 0x05007485"],
        "base_completeness_and_model_gaps_modified": False,
        "calendar_collector_executed": False,
    }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
