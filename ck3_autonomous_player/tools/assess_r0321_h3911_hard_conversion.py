"""Audit H3911's private native hard-conversion readout without CK3 actions.

The frozen source row is a hypothetical precontact observation.  This script
never produces a forecast, original-trace parity claim, or attack permission.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from xar_autoplayer.bridge.combat_phase_contract import (  # noqa: E402
    normalize_combat_simulation_inputs_v3,
)
from xar_autoplayer.simulation.hard_conversion_diagnostic import (  # noqa: E402
    assess_precontact_hard_conversion,
)


SOURCE_SHA256 = "865EA7B7AC1B4A680E2BE3A1D84012C67CF9550474075E4A917EFE043CCCDD51"
DRIVER_SHA256 = "DE09EA8B3648FAE89F90E5459991BC66AE52154971948DB39C353D05EEAAEE33"
STEP = "query-combat-simulation-inputs-v3-2629-2630-a-1-83886367-d-2-50331920-83886484"
ATTACKERS = (83886367,)
DEFENDERS = (50331920, 83886484)
WAR_ID = 16777231


def assess_source(raw: bytes, driver_raw: bytes | None = None) -> dict[str, object]:
    digest = hashlib.sha256(raw).hexdigest().upper()
    if digest != SOURCE_SHA256 or len(raw) != 2_080_166:
        raise ValueError("H3911 excerpt bytes differ from frozen WAR transfer")
    source = json.loads(raw)
    row = source.get("command_row")
    if not (
        isinstance(row, dict) and row.get("index") == 3920
        and row.get("ok") is True and row.get("command") == STEP
        and source.get("source_driver", {}).get("sha256") == DRIVER_SHA256
    ):
        raise ValueError("H3911 command row/source driver claim differs")
    parent_driver_verified = False
    if driver_raw is not None:
        if hashlib.sha256(driver_raw).hexdigest().upper() != DRIVER_SHA256 or len(driver_raw) != 46_002_331:
            raise ValueError("H3911 parent driver bytes differ from frozen transfer")
        driver = json.loads(driver_raw)
        history = driver.get("command_history")
        if not isinstance(history, list) or len(history) <= 3919 or history[3919] != row:
            raise ValueError("H3911 excerpt row differs from parent driver")
        parent_driver_verified = True
    result = row.get("result")
    if not (
        isinstance(result, dict) and result.get("accepted") is True
        and result.get("status") == "available" and result.get("step") == STEP
        and result.get("queried_snapshot_id") == "native:23"
        and result.get("queried_revision") == 24
        and result.get("queried_native_revision") == 23
        and result.get("query_sequence") == 1
    ):
        raise ValueError("H3911 query wrapper identity differs")
    payload = result.get("combat_simulation_inputs")
    base = payload.get("base_inputs") if isinstance(payload, dict) else None
    armies = base.get("armies") if isinstance(base, dict) else None
    if not isinstance(armies, list) or len(armies) != 3:
        raise ValueError("H3911 army census differs")
    selected_scope = []
    for army, army_id, expected_role in zip(
        armies, (*ATTACKERS, *DEFENDERS),
        ("player", "active_war_enemy", "active_war_enemy"), strict=True,
    ):
        if not (
            isinstance(army, dict) and army.get("army_id") == army_id
            and army.get("scope_role") == expected_role
            and army.get("war_ids") == [WAR_ID]
            and army.get("status") == "available"
        ):
            raise ValueError("H3911 same-war ordered army identity differs")
        selected_scope.append({
            "army_id": army_id, "scope_role": expected_role,
            "war_ids": [WAR_ID],
        })
    scope = {
        "army_ids": [*ATTACKERS, *DEFENDERS],
        "attacker_army_ids": list(ATTACKERS),
        "defender_army_ids": list(DEFENDERS),
        "selected_scope": selected_scope,
        "attacker_scope": selected_scope[:1],
        "defender_scope": selected_scope[1:],
        "attacker_side": "player_or_allied",
        "defender_side": "enemy",
        "common_war_ids": [WAR_ID],
    }
    normalized = normalize_combat_simulation_inputs_v3(
        payload, expected_target_province_id=2629,
        expected_attacker_entry_province_id=2630,
        expected_encounter_scope=scope,
    )
    diagnostic = assess_precontact_hard_conversion(
        normalized, target_province_id=2629,
        attacker_entry_province_id=2630,
        attacker_army_ids=ATTACKERS, defender_army_ids=DEFENDERS,
    )
    return {
        "schema": "xar.r0321-h3911-precontact-hard-conversion-audit.v1",
        "source_excerpt_sha256": digest,
        "source_driver_sha256_claim": DRIVER_SHA256,
        "parent_driver_semantic_equality_receiver_verified": parent_driver_verified,
        "same_frame_episode_and_generation_in_command_row": False,
        "war_id": WAR_ID,
        "snapshot_id": "native:23",
        "public_revision": 24,
        "native_revision": 23,
        "diagnostic": diagnostic,
        "whole_battle_probability_available": False,
        "planner_usable": False,
        "active_attack_allowed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--excerpt", type=Path, required=True)
    parser.add_argument("--driver", type=Path,
                        help="Optional exact 46,002,331-byte source driver for parent-row equality")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("refusing to overwrite an existing audit")
    result = assess_source(
        args.excerpt.read_bytes(),
        args.driver.read_bytes() if args.driver is not None else None,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({
        "output": str(args.output),
        "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest().upper(),
        "diagnostic_status": result["diagnostic"]["status"],
        "planner_usable": False,
    }))


if __name__ == "__main__":
    main()
