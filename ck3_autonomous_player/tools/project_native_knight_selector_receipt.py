"""Reconstruct one original CK3 knight-kill draw from immutable native receipts.

The report is deliberately one combat/day scoped.  It validates the candidate
source vector, native tail-swap filtering, the selector's recorded RNG state,
and the selected character token.  It does not infer other effect-local draws
or a complete character/regiment write set.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from xar_autoplayer.simulation.combat_core import DrawState  # noqa: E402
from xar_autoplayer.simulation.phase_event_manifest import (  # noqa: E402
    load_stock_phase_event_manifest,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def response(attempt: Path, name: str) -> tuple[dict[str, object], str]:
    path = attempt / "ck3-output/interactive-requests-responses" / name
    source = json.loads(path.read_text(encoding="utf-8"))
    require(source["result"] == "CALL_COMPLETED" and source["body"]["accepted"] is True,
            f"{name} original response")
    return source["body"], digest(path)


def token_value(value: str) -> int:
    prefix = "process-local-0x"
    require(isinstance(value, str) and value.startswith(prefix), "opaque token format")
    return int(value[len(prefix):], 16)


def project(attempt: Path) -> dict[str, object]:
    launch = json.loads((attempt / "launch-argv.json").read_text(encoding="utf-8"))
    argv = launch["argv"]
    source_save = Path(argv[argv.index("--checkpoint-save") + 1])
    original_checkpoint_sha = digest(source_save)
    v3, v3_sha = response(attempt, "004-v3.json")
    finish, finish_sha = response(attempt, "007-finish.json")
    post_save, post_save_sha = response(attempt, "008-after-save.json")
    summary = json.loads((attempt / "one-day-summary.json").read_text(encoding="utf-8"))
    require(summary["trace_response_sha256"] == finish_sha
            and summary["post_event_save_response_sha256"] == post_save_sha,
            "run summary response SHA")
    require(digest(attempt / "d27-postevent-immutable.ck3")
            == summary["post_event_save_sha256"].upper()
            == post_save["checkpoint"]["sha256"].upper(),
            "post-event immutable checkpoint SHA")
    payload = v3["combat_simulation_inputs"]["phase_event_inputs"]
    require(payload["status"] == "available", "pre-event native input status")
    matches = [row for row in payload["evaluation_contexts"]
               if row["root_character_id"] == 33437]
    require(len(matches) == 1, "unique native target context")
    context = matches[0]
    require(context["combat_side_index"] == 1
            and context["root_source_regiment_id"] == 65,
            "target side and regiment identity")
    source_proof = context["candidate_source_proof"]
    require(source_proof["source_vector_equivalence"] is True,
            "native source-vector equivalence")
    source_knights = [row["character_id"] for row in source_proof["ordered_sources"]
                      if row["role"] == "knight"]
    rows = context["candidate_rows"]
    require([row["character_id"] for row in rows] == source_knights,
            "candidate rows match original source vector")

    # Exact-build 0x19F4760 compacts a failed predicate by copying the current
    # vector tail over that index, then rechecking it.  The relevant stock
    # knight_killed branch filters on >= root opponent threshold and has no
    # candidate weight clause, so 0x33E8D40 takes the modulo-count path.
    candidates = list(rows)
    index = 0
    predicate = "derived.candidate_prowess_at_or_above_root_opponent_threshold_without_alive_filter"
    while index < len(candidates):
        if candidates[index]["candidate_refs"][predicate] is True:
            index += 1
        else:
            candidates[index] = candidates.pop()
    compacted = [row["character_id"] for row in candidates]

    manifest = load_stock_phase_event_manifest()
    events = [row for row in manifest.event_rows if row.key == "knight_killed"]
    require(len(events) == 1 and events[0].global_load_index == 11,
            "stock knight_killed load identity")
    selector_nodes = [step for step in events[0].effect_ast["steps"]
                      if step.get("op") == "select_side_knight"]
    require(len(selector_nodes) == 1
            and selector_nodes[0]["weight"]["op"] == "const_fixed"
            and selector_nodes[0]["weight"]["raw"] == 100000,
            "stock unweighted enemy knight source clause")

    trace = finish["managed_trace"]["trace"]
    require(finish["status"] == "bounded_trace_available"
            and trace["failure_flags"] == 0,
            "bounded original trace")
    roots = [row for row in trace["effect_roots"]
             if row["side_index"] == 1 and row["native_event_load_index"] == 11]
    selects = [row for row in trace["knight_selects"]
               if row["side_index"] == 1 and row["native_event_load_index"] == 11]
    require(len(roots) == len(selects) == 1, "one selected kill root and knight draw")
    root, select = roots[0], selects[0]
    require(root["node_hash"] == 3689483501
            and root["counter_after"] == root["counter_before"] + 1,
            "exact-build root observation")
    require(select["candidate_count"] == len(compacted) == 14,
            "native candidate count and reconstructed compaction")
    draw, next_state = DrawState(
        select["counter_before"], select["salt_before"]
    ).draw31()
    require(next_state.counter == select["counter_after"]
            and next_state.salt == select["salt_after"],
            "selector consumes exactly one local draw")
    selected_index = draw % len(compacted)
    selected_character_id = token_value(select["selected_candidate_word1_token"])
    require(token_value(select["selected_candidate_word0_token"]) == 4
            and selected_index == select["selected_index"]
            and compacted[selected_index] == selected_character_id == 34120,
            "uniform index, compacted candidate and native target token")
    before_events = trace["records"][4]["battle_events"]
    after_events = trace["records"][5]["battle_events"]
    require(after_events[:len(before_events)] == before_events
            and len(after_events) == len(before_events) + 1,
            "one new battle event on the effect boundary")
    battle_event = after_events[-1]
    require(battle_event["stable_key"] == "knight_killed_by_enemy"
            and battle_event["left_character_id"] == 33437
            and battle_event["right_character_id"] == selected_character_id,
            "battle event binds selected enemy character")

    return {
        "schema": "ck3.native_knight_kill_selector_parity.v1",
        "game_build": "1.19.0.6",
        "combat_id": 16777218,
        "source_day": 26,
        "source_checkpoint_sha256": original_checkpoint_sha,
        "v3_response_sha256": v3_sha,
        "trace_response_sha256": finish_sha,
        "post_save_response_sha256": post_save_sha,
        "post_event_save_sha256": summary["post_event_save_sha256"].upper(),
        "source_vector_sequence_sha256": source_proof["sequence_sha256"],
        "stock_event_manifest_sha256": manifest.canonical_manifest_sha256,
        "native_event_load_index": 11,
        "root_character_id": 33437,
        "root_source_regiment_id": 65,
        "root_node_hash": root["node_hash"],
        "root_rng_counter_before": root["counter_before"],
        "root_rng_counter_after": root["counter_after"],
        "source_knight_character_ids": source_knights,
        "compacted_candidate_character_ids": compacted,
        "selection_mode": "native_unweighted_modulo_count",
        "selector_counter_before": select["counter_before"],
        "selector_salt_before": select["salt_before"],
        "selector_draw31": draw,
        "candidate_count": len(compacted),
        "selected_index": selected_index,
        "selected_character_id": selected_character_id,
        "battle_event": battle_event,
        "selector_consumed_exactly_one_draw": True,
        "full_effect_write_set_proven": False,
        "other_effect_local_draws_observed": False,
        "whole_battle_win_probability_available": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = project(args.attempt)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output),
                      "selected_character_id": report["selected_character_id"]}))


if __name__ == "__main__":
    main()
