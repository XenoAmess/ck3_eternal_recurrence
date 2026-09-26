#!/usr/bin/env python3
"""Bind a day-05 maiming replay's native branches to its next save.

The three random-list choices are read from paused engine objects. Dynamic
weights were not captured at the selector entry; only the selected branches
and the static entry weights are direct observations.
"""

from __future__ import annotations

import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from xar_autoplayer.simulation.combat_core import DrawState, weighted_choice_index
from project_native_phase_event_save_feedback import _character_snapshot


GAME_EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
RAKALY_EXE_SHA256 = "E154AF990AAED2C2F44284946772188C9749AD3F6B641B41F6C23456A6F1633D"
SOURCE_SAVE_SHA256 = "D978D75A2212604CFDD9BF7FBDEF3424E85E39C5092D7245D04590694017FA01"
POST_SAVE_SHA256 = "9ACACDE3E2D1987180EFE5FFDDC32B092146E6116779AF0D4BEBC7C97B9B7F9A"
EXPECTED = {
    8: ([60, 30, 10], 0, "knight_increase_prowess_chance_effect", "no_prowess_gain"),
    15: ([4, 2, 4, 4], 0, "maimed_in_battle_effect", "one_legged_and_wound"),
    49: ([10, 50], 1, "safe_wound_treatment_effect", "delayed_treatment_failure"),
}


def digest(path: Path) -> str:
    checksum = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(chunk)
    return checksum.hexdigest().upper()


def project(attempt: Path, source_save: Path, rakaly: Path, game_root: Path) -> dict:
    summary_path = attempt / "one-day-summary.json"
    memory_path = attempt / "random-lists-memory.json"
    classification_path = attempt / "random-list-classification.json"
    response_path = attempt / "ck3-output/interactive-requests-responses/007-finish.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    memory = json.loads(memory_path.read_text(encoding="utf-8"))
    classification = json.loads(classification_path.read_text(encoding="utf-8"))
    assert digest(source_save) == SOURCE_SAVE_SHA256 == summary["source_checkpoint_sha256"].upper()
    assert digest(attempt / "d06-postevent-immutable.ck3") == POST_SAVE_SHA256 == summary["post_event_save_sha256"].upper()
    assert digest(rakaly) == RAKALY_EXE_SHA256
    assert digest(game_root / "binaries/ck3.exe") == GAME_EXE_SHA256 == memory["game_executable_sha256"]
    assert digest(response_path) == summary["trace_response_sha256"] == memory["trace_response_sha256"]
    assert digest(classification_path) == memory["classification_sha256"]
    assert classification["trace_response_sha256"] == summary["trace_response_sha256"]
    assert classification["status"] == summary["trace_status"] == "bounded_trace_available"
    assert classification["failure_flags"] == summary["trace_failure_flags"] == 0
    assert summary["final_capture_flags"] == 0
    events = summary["appended_events"]
    assert [(item["side_index"], item["stable_key"], item["left_character_id"], item["right_character_id"])
            for item in events] == [
                (0, "knight_wounded_by_enemy", 47029, 33435),
                (1, "knight_maimed_by_enemy", 34333, 47032),
            ]

    sources = {
        "knight": game_root / "game/common/combat_phase_events/00_knight_phase_events.txt",
        "commander": game_root / "game/common/scripted_effects/00_commander_effects.txt",
        "health": game_root / "game/common/scripted_effects/20_health_effects.txt",
    }
    scripts = {key: path.read_text(encoding="utf-8-sig") for key, path in sources.items()}
    for needle in ("knight_maimed_by_enemy", "maimed_in_battle_effect = yes",
                   "knight_increase_prowess_chance_effect = yes"):
        assert needle in scripts["knight"]
    for needle in ("knight_increase_prowess_chance_effect = {", "60 = {", "30 = {",
                   "10 = {", "add_prowess_skill = 1"):
        assert needle in scripts["commander"]
    for needle in ("maimed_in_battle_effect = {", "add_trait_force_tooltip = one_legged",
                   "increase_wounds_effect = { REASON = fight }", "safe_wound_treatment_effect = {",
                   "50 = { #Failure", "id = health.0101"):
        assert needle in scripts["health"]

    nodes = {item["random_list_node"]["call_index"]: item
             for item in classification["random_list_nodes"]}
    receipts = {item["call_index"]: item for item in memory["random_lists"]}
    assert set(nodes) == set(receipts) == set(EXPECTED)
    choices = []
    for call, (weights, selected, effect, branch) in EXPECTED.items():
        node = nodes[call]
        root = node["random_list_node"]
        receipt = receipts[call]
        assert root["side_index"] == receipt["side_index"] == 1
        assert root["native_event_load_index"] == receipt["native_event_load_index"] == 10
        assert root["node_vtable_rva"] == 0x44782B0
        assert root["node_identity_token"] == receipt["node_identity_token"]
        assert root["node_hash"] == receipt["node_hash"]
        assert (root["counter_before"], root["counter_after"]) == (
            receipt["node_counter_before"], receipt["node_counter_after"])
        assert len(node["direct_children"]) == 1
        child = node["direct_children"][0]
        assert child["node_vtable_rva"] == 0x4478388
        assert child["node_identity_token"] == receipt["selected_entry_identity_token"]
        assert receipt["selected_source_order_index"] == selected
        assert receipt["weights_native_int32"] == weights
        assert receipt["entry_count"] == len(weights)
        assert receipt["static_total_native_int32"] == sum(weights)
        assert receipt["flags_bc_bd"] == [0, 1]
        assert receipt["selected_entry_identity_token"].lower() == (
            "process-local-" + receipt["entry_identity_tokens"][selected]).lower()
        for name, sha in receipt["raw_sha256"].items():
            assert digest(attempt / name) == sha
        draw, after = DrawState(root["counter_before"], root["salt_before"]).draw31()
        assert after.counter == root["counter_after"] and after.salt == root["salt_after"]
        choices.append({
            "call_index": call, "effect": effect, "branch": branch,
            "counter_before": root["counter_before"], "counter_after": root["counter_after"],
            "draw31": draw, "static_base_weights": weights,
            "selected_index_direct": selected,
            "static_weights_projection_index": weighted_choice_index(tuple(weights), draw),
            "adjusted_weights_directly_observed": False,
            "raw_sha256": receipt["raw_sha256"],
        })

    snapshots = {}
    melted = {}
    for day in (5, 6):
        path = attempt / ("d05-replay-source-melted.ck3" if day == 5 else "d06-melted.ck3")
        melted[day] = digest(path)
        content = path.read_text(encoding="utf-8-sig")
        snapshots[day] = {character_id: _character_snapshot(content, character_id)
                          for character_id in (34333, 47032, 47029, 33435)}
    target_before, target_after = snapshots[5][34333], snapshots[6][34333]
    assert "one_legged" not in target_before["trait_keys"]
    assert set(target_after["trait_keys"]) - set(target_before["trait_keys"]) == {"one_legged", "wounded_1"}
    assert (target_before["wounded_rank"], target_after["wounded_rank"]) == (0, 1)
    assert target_before["alive_data_present"] and target_after["alive_data_present"]
    opponent_before, opponent_after = snapshots[5][47032], snapshots[6][47032]
    assert opponent_before["trait_keys"] == opponent_after["trait_keys"]
    assert opponent_before["base_skill_values"] == opponent_after["base_skill_values"]
    prestige_delta = Decimal(opponent_after["prestige_currency"]) - Decimal(opponent_before["prestige_currency"])
    assert prestige_delta == 150
    wound_before, wound_after = snapshots[5][47029], snapshots[6][47029]
    assert wound_before["trait_keys"] == wound_after["trait_keys"]
    assert wound_before["wounded_rank"] == wound_after["wounded_rank"] == 1

    return {
        "schema": "ck3.native_knight_maim_replay.v1",
        "game_version": "1.19.0.6", "game_executable_sha256": GAME_EXE_SHA256,
        "source_save_sha256": SOURCE_SAVE_SHA256, "post_save_sha256": POST_SAVE_SHA256,
        "rakaly_exe_sha256": RAKALY_EXE_SHA256,
        "melted_save_sha256_by_day": {str(day): sha for day, sha in melted.items()},
        "source_script_sha256": {key: digest(path) for key, path in sources.items()},
        "trace_response_sha256": digest(response_path),
        "classification_sha256": digest(classification_path),
        "memory_receipt_sha256": digest(memory_path),
        "event_log": events,
        "random_list_choices": choices,
        "characters_by_day": {str(day): {str(key): value for key, value in rows.items()}
                              for day, rows in snapshots.items()},
        "directly_observed_maim_target_trait_delta": ["one_legged", "wounded_1"],
        "directly_observed_maim_opponent_prestige_delta": str(prestige_delta),
        "directly_observed_maim_opponent_base_prowess_delta": 0,
        "separate_wound_event_target_unchanged_in_next_save": True,
        "complete_effect_write_set_proven": False,
        "runtime_adjusted_random_list_weights_observed": False,
        "planner_usable_as_full_phase_transition": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-root", required=True, type=Path)
    parser.add_argument("--source-save", required=True, type=Path)
    parser.add_argument("--rakaly-exe", required=True, type=Path)
    parser.add_argument("--game-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    assert not args.output.exists(), f"refusing to overwrite {args.output}"
    report = project(args.attempt_root, args.source_save, args.rakaly_exe, args.game_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output),
                      "choices": [(row["call_index"], row["selected_index_direct"])
                                  for row in report["random_list_choices"]]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
