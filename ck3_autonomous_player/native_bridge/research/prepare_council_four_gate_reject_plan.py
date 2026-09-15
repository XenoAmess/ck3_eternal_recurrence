"""Freeze a private rejection plan from one actual paused native gate terminal."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from council_four_gate_reject_v1 import PositiveSceneMissing, select


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene-terminal", type=Path, required=True)
    parser.add_argument("--scene-terminal-sha256", required=True)
    parser.add_argument("--gate", choices=("guest", "candidate_pending",
                                           "replacement_fireability_denial"),
                        required=True)
    parser.add_argument("--output-plan", type=Path, required=True)
    args = parser.parse_args()
    if args.output_plan.exists():
        raise ValueError("frozen rejection plan already exists; do not overwrite")
    try:
        plan = select(args.scene_terminal, args.scene_terminal_sha256, args.gate)
    except PositiveSceneMissing as error:
        print(json.dumps({"status": "evidence_insufficient",
                          "ck3_launched": False, "reason": str(error)},
                         sort_keys=True))
        return 2
    args.output_plan.parent.mkdir(parents=True, exist_ok=True)
    args.output_plan.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n",
                                encoding="utf-8")
    print(json.dumps({"status": "plan_sealed_no_launch", "gate": plan["gate"],
                      "candidate_character_id": plan["candidate_character_id"],
                      "scene_terminal_sha256": plan["terminal_sha256"],
                      "typed_action_verified": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
