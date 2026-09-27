"""Hash-bound read-only 098/105 counter timing audit, never a forecast parity gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

from xar_autoplayer.bridge.battle_control_contract import (  # noqa: E402
    normalize_battle_control_snapshot_v1,
)
from xar_autoplayer.simulation.active_counter_current_basis import (  # noqa: E402
    project_current_counter_attack_raw,
)
from xar_autoplayer.simulation.combat_core import (  # noqa: E402
    FIXED_SCALE, outgoing_damage_raw,
)

DEFAULT_ROOT = Path(r"D:\workspace\ck3_native_war_ai_promo_work")
FIXTURE = (ROOT / "ck3_autonomous_player" / "src" / "xar_autoplayer" /
           "simulation" / "data" / "ck3_1_19_0_6_counter_105_retrospective_gate.json")
EXE_SHA = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
SAVE_SHA = "3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953"
INPUTS = {
    "098": {
        "directory": "episode01-active-counter-output-attempt-098",
        "input-freeze.json": "DD0C346F046DB059C56B880A2F9C31686B83C3D5A104934DBB7AEF7D13B64C5C",
        "ck3-output/preflight.json": "3886CC56B2B96A7BC3F5B39DA771DC2CB887702882FBBA887F7F34C5C97B114D",
        "before-control": "2244E1144D7F5708B19BD2DE50311BCCA38481EFD0BC98165FC48AEA8C0602AA",
        "after-control": "236E67C10CFABBABEDE2822A40074458ABF8EFCA019CE54A3C88CC669EA217EC",
        "trace-finish": "6B158A07A6071D058DE6F3E8994CA0065F09B2311EF79004EB1DDD445B1B8198",
    },
    "105": {
        "directory": "episode01-active-advantage-reinforcement-attempt-105",
        "input-freeze.json": "1182947A0FF7375E9761F27E1BBB045E0DBD4E3D0658BED166AAD0B6CDD1DCF8",
        "ck3-output/preflight.json": "AB98E3EC33D531F870CFEA2B0FD40483FED6ECAA445A9C0254D73C2D6ECE532A",
        "before-control": "BEC16EE07718D3E483474E0488B45C80A49FAB89A08019BFD09F371EDB03363F",
        "after-control": "BAFB9090085360D4A7D914B2499FB91C592AAD7F7BC257A612BC50D7EFE71B57",
        "trace-finish": "4BC6B5B9CC9417574F8B92063090A8A6D25152B85448C044454E280FDD2F76B9",
    },
}


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def read_exact(path: Path, sha: str) -> dict:
    raw = path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest().upper()
    require(actual == sha, f"{path.name} source SHA drift: {actual}")
    result = json.loads(raw)
    require(isinstance(result, dict), f"{path.name} is not an object")
    return result


def frame_projection(response: dict) -> dict:
    require(response.get("result") == "CALL_COMPLETED", "control query did not complete")
    raw = response["body"]["battle_control_snapshot"]
    frame = normalize_battle_control_snapshot_v1(
        raw,
        expected_subject_public_cunit_id=raw["subject_public_cunit_id"],
        expected_observed_date_raw=raw["observed_date_raw"],
        expected_snapshot_revision=raw["snapshot_revision"],
    )
    require(frame["phase"] == "main" and frame["winner_side"] == "none"
            and frame["side_scope"] == "full_side", "not an active full-side main frame")
    attack, retention = project_current_counter_attack_raw(frame)
    sides = (frame["attacker"], frame["defender"])
    outgoing = [outgoing_damage_raw(
        attack[i], advantage_multiplier_raw=FIXED_SCALE,
        final_combat_width=frame["final_combat_width"],
        side_current_fighting_men_raw=sides[i]["stored_current_fighting_raw"],
    ) for i in (0, 1)]
    return {
        "combat_id": frame["combat_id"],
        "observed_date_raw": frame["observed_date_raw"],
        "phase_day": frame["phase_day"],
        "final_combat_width": frame["final_combat_width"],
        "subject_public_cunit_id": frame["subject_public_cunit_id"],
        "side_native_army_ids": [
            [row["native_carmy_id"] for row in side["ordered_armies"]]
            for side in sides
        ],
        "side_maa_counts": [len(side["men_at_arms_entries"]) for side in sides],
        "context_raw": [row["context_scale_raw"] for row in
                        frame["active_counter_inputs_v1"]["contexts"]],
        "current_frame_retention_raw": [list(row) for row in retention],
        "current_frame_counter_attack_raw": list(attack),
        "current_frame_neutral_advantage_outgoing_raw": outgoing,
    }


def read_attempt(base: Path, tag: str) -> dict:
    source = INPUTS[tag]
    attempt = base / source["directory"]
    freeze = read_exact(attempt / "input-freeze.json", source["input-freeze.json"])
    preflight = read_exact(attempt / "ck3-output" / "preflight.json",
                           source["ck3-output/preflight.json"])
    require(freeze["exe_sha256"] == preflight["game"]["sha256"] == EXE_SHA,
            f"{tag} exact EXE identity disagrees")
    require(freeze["source"]["sha256"] ==
            preflight["checkpoint_source"]["save"]["sha256"] == SAVE_SHA,
            f"{tag} frozen day-11 save identity disagrees")
    require(freeze["bridge"]["sha256"] == preflight["bridge_dll"]["sha256"],
            f"{tag} bridge identity disagrees")
    responses = attempt / "ck3-output" / "interactive-requests-responses"
    controls = {}
    for name in ("before-control", "after-control"):
        response = read_exact(responses / f"c{tag}-{name}.json", source[name])
        controls[name] = frame_projection(response)
    finish = read_exact(responses / f"c{tag}-trace-finish.json",
                        source["trace-finish"])
    require(finish.get("result") == "CALL_COMPLETED", f"{tag} trace query did not complete")
    trace = finish["body"]["managed_trace"]["trace"]
    native = trace["runtime_counter_output"]
    require(native["pair_complete"] is True and native["count"] == 2,
            f"{tag} counter numerical pair missing")
    require([row["side_index"] for row in native["sides"]] == [0, 1],
            f"{tag} counter sides reversed")
    return {
        "source": {
            "attempt": int(tag),
            "exe_sha256": EXE_SHA,
            "frozen_save_sha256": SAVE_SHA,
            "bridge_sha256": freeze["bridge"]["sha256"],
            "input_sha256": {key: source[key] for key in (
                "input-freeze.json", "ck3-output/preflight.json",
                "before-control", "after-control", "trace-finish",
            )},
        },
        "before": controls["before-control"],
        "after": controls["after-control"],
        "trace": {
            "status": trace["status"],
            "failure_flags": trace["failure_flags"],
            "exact_boundary_sequence": trace["readiness"]["exact_boundary_sequence"],
            "side_and_return_site_identity": trace["readiness"]["side_and_return_site_identity"],
            "bounded_capture_complete": trace["readiness"]["bounded_capture_complete"],
            "runtime_join_full_entries_captured": (
                isinstance(trace.get("runtime_join_full_entries"), dict)
                and trace["runtime_join_full_entries"].get("status") == "captured"
            ),
            "native_retention_raw": [row["retention_raw"] for row in native["sides"]],
            "native_counter_entry_counts": [row["countered_entry_count"] for row in native["sides"]],
            "native_post_counter_attack_raw": [
                trace["post_counter_attack"]["side0_raw"],
                trace["post_counter_attack"]["side1_raw"],
            ],
            "native_outgoing_damage_raw": [
                trace["outgoing_damage"]["side0_raw"],
                trace["outgoing_damage"]["side1_raw"],
            ],
        },
    }


def project(base: Path) -> dict:
    results = {tag: read_attempt(base, tag) for tag in ("098", "105")}
    for tag, result in results.items():
        before, after, trace = result["before"], result["after"], result["trace"]
        require(before["combat_id"] == after["combat_id"] == 16777218,
                f"{tag} CombatID changed")
        require((before["observed_date_raw"], after["observed_date_raw"]) ==
                (53146488, 53146512), f"{tag} is not day11 to day12")
        require((before["phase_day"], after["phase_day"]) == (7, 8),
                f"{tag} phase-day drift")
        require((before["side_maa_counts"], after["side_maa_counts"]) ==
                ([18, 14], [24, 14]), f"{tag} reinforcement census drift")
        require(22 not in before["side_native_army_ids"][0]
                and 22 in after["side_native_army_ids"][0],
                f"{tag} Army 22 timing drift")
        require(before["current_frame_retention_raw"] != trace["native_retention_raw"],
                f"{tag} before frame unexpectedly equals next-day native vector")
        require(after["current_frame_retention_raw"] == trace["native_retention_raw"],
                f"{tag} after frame no longer numerically equals native vector")
    require(results["098"]["before"] == results["105"]["before"]
            and results["098"]["after"] == results["105"]["after"],
            "same-save controls no longer agree numerically")
    require(results["098"]["trace"]["native_retention_raw"] ==
            results["105"]["trace"]["native_retention_raw"]
            and results["098"]["trace"]["native_post_counter_attack_raw"] ==
            results["105"]["trace"]["native_post_counter_attack_raw"]
            and results["098"]["trace"]["native_outgoing_damage_raw"] ==
            results["105"]["trace"]["native_outgoing_damage_raw"],
            "same-source numerical trace fields drift")
    require(results["098"]["trace"]["status"] == "captured"
            and results["098"]["trace"]["failure_flags"] == 0
            and results["098"]["trace"]["runtime_join_full_entries_captured"],
            "098 reference trace no longer GREEN")
    require(results["105"]["trace"]["status"] == "failed"
            and results["105"]["trace"]["failure_flags"] == 0x410
            and not results["105"]["trace"]["exact_boundary_sequence"]
            and not results["105"]["trace"]["side_and_return_site_identity"]
            and not results["105"]["trace"]["bounded_capture_complete"]
            and not results["105"]["trace"]["runtime_join_full_entries_captured"],
            "105 trace failure gate unexpectedly changed")
    return {
        "schema": "ck3.counter_105_retrospective_gate.v1",
        "scope": "same-frame-conditional-readout-only; no next-day prediction",
        "attempts": results,
        "assessment": {
            "same_source_control_numeric_agreement": True,
            "same_source_native_numerical_fields_agree": True,
            "before_side1_class1_retention_raw": results["105"]["before"]["current_frame_retention_raw"][1][1],
            "after_side1_class1_retention_raw": results["105"]["after"]["current_frame_retention_raw"][1][1],
            "native_tick_side1_class1_retention_raw": results["105"]["trace"]["native_retention_raw"][1][1],
            "formal_native_parity_098": "single_tick_counter_vector_only",
            "formal_native_parity_105": "red_trace_identity_and_final_query",
            "day11_to_day12_forecast_validated": False,
            "day12_after_frame_equals_prefire_operands_proven": False,
            "whole_battle_win_probability": None,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true")
    group.add_argument("--write-fixture", action="store_true")
    args = parser.parse_args()
    result = project(args.root)
    rendered = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if args.check:
        require(FIXTURE.read_bytes() == rendered, "checked-in retrospective fixture drift")
    elif args.write_fixture:
        require(not FIXTURE.exists(), "refuse to overwrite prior fixture")
        FIXTURE.write_bytes(rendered)
    else:
        sys.stdout.buffer.write(rendered)
    print(json.dumps({
        "readout": "checked" if args.check else "written" if args.write_fixture else "projected",
        "formal_native_parity_105": "RED",
        "day11_to_day12_forecast_validated": False,
    }))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, KeyError, TypeError, ValueError) as exc:
        print(f"counter 105 retrospective audit RED: {exc}", file=sys.stderr)
        raise SystemExit(1)
