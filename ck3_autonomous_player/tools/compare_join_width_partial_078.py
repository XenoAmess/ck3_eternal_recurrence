"""Project the simulator's width residuals against frozen 078 join boundaries.

The before-join calculation is a cache-consistency check, not an assertion
that CK3 invoked its updater at wrapper entry. No phase-fire width is inferred.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
from xar_autoplayer.simulation.combat_core import update_combat_width  # noqa: E402


OBSERVATION_SHA256 = "FCC6402187B91682B3C053CDFB9684D962602376974430AF00ABED2558325E86"
TERRAIN_WIDTH_RAW = 90000


def compare(raw: bytes) -> dict[str, object]:
    if hashlib.sha256(raw).hexdigest().upper() != OBSERVATION_SHA256:
        raise ValueError("078 observation fixture SHA-256 mismatch")
    observation = json.loads(raw)
    if (observation["schema"] != "ck3.native_join_width_partial_observation.v1"
            or observation["source"]["attempt"] != 78
            or observation["collector_status"] != "failed"
            or observation["combat_id"] != 16777218
            or observation["candidate_joining_army_id"] != 22
            or observation["native_date_raw"] != 53146512
            or observation["three_boundary_complete"] is not False
            or observation["fire_width"] is not None
            or len(observation["boundaries"]) != 2):
        raise ValueError("078 evidence boundary changed")

    previous = observation["boundaries"][0]["base_width"]
    rows = []
    for index, row in enumerate(observation["boundaries"]):
        totals = row["side_fighting_total_raw"]
        predicted_base, predicted_final = update_combat_width(
            totals[0], totals[1], previous_base_width=previous,
            terrain_width_multiplier_raw=TERRAIN_WIDTH_RAW,
        )
        rows.append({
            "boundary": index,
            "role": "cache_consistency_before_join" if index == 0 else "join_return_candidate",
            "previous_base_width_input": previous,
            "side_fighting_total_raw": totals,
            "native_base_width": row["base_width"],
            "native_final_width": row["final_width"],
            "model_base_width": predicted_base,
            "model_final_width": predicted_final,
            "model_minus_native_base": predicted_base - row["base_width"],
            "model_minus_native_final": predicted_final - row["final_width"],
        })
        previous = row["base_width"]
    return {
        "schema": "ck3.native_join_width_partial_model_parity.v1",
        "source_observation_sha256": OBSERVATION_SHA256,
        "source_finish_sha256": observation["source"]["finish_sha256"],
        "combat_id": observation["combat_id"],
        "native_date_raw": observation["native_date_raw"],
        "candidate_joining_army_id": observation["candidate_joining_army_id"],
        "terrain": {
            "province_id": 2633,
            "key": "forest",
            "width_multiplier_raw": TERRAIN_WIDTH_RAW,
            "source_kind": "stock_script_static_not_attempt_078_runtime_field",
            "province_terrain_source_sha256": "922A5B8BA73007B18E95F1CCFCDBE075A03F5DE61CBF8FF8F66698BEDBB3BE3C",
            "terrain_types_source_sha256": "39D79AD120BF85B49D6EE8D96FE4D94EDBBABC190A41662DBA8ECA8DE0ACE64E",
        },
        "rows": rows,
        "base_width_zero_residual_count": sum(row["model_minus_native_base"] == 0 for row in rows),
        "final_width_zero_residual_count": sum(row["model_minus_native_final"] == 0 for row in rows),
        "three_boundary_complete": False,
        "fire_width": None,
        "join_policy_reconstructed": False,
        "phase_fire_argument_observed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observation", type=Path, required=True)
    parser.add_argument("--fixture", type=Path)
    args = parser.parse_args()
    result = compare(args.observation.read_bytes())
    if args.fixture is not None:
        expected = json.loads(args.fixture.read_text(encoding="utf-8"))
        if result != expected:
            raise ValueError("078 width model parity fixture mismatch")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
