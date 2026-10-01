#!/usr/bin/env python3
"""Freeze the narrow .5007 source migration proof without using CK3."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from ck3_12002_nonwar_event_sources import (
    SourceTree, assignments, portable_definition, section_comparison, sha256,
    values,
)


EVENT = "epidemic_events.5007"
EVENT_PATH = "events/dlc/ce1/epidemic_events.txt"
NEW_EXE = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"
ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "ck3_autonomous_player/src/xar_autoplayer/vanilla_events/data"
DEFAULT_ARCHIVE = Path(r"Z:\ck3_mod_rewrite\artifacts\migrations\2026-09-30\post-update-1.20.0.2\installation\game")
DEFAULT_CURRENT = Path(r"Z:\SteamLibrary\steamapps\common\Crusader Kings III\game")
DEFAULT_OLD = Path(r"Z:\Crusader Kings III\Crusader Kings III_1.19.0.6_20260604\game")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def generate(old_root: Path, archive_root: Path, current_root: Path) -> dict:
    old, archive, current = (SourceTree(path) for path in (old_root, archive_root, current_root))
    compatibility_path = DATA / "source_compatibility_1_20_0_2.json"
    compatibility = json.loads(compatibility_path.read_text(encoding="utf-8"))
    reviewed = compatibility["events"][EVENT]
    before, after = old.definition(EVENT_PATH, EVENT), archive.definition(EVENT_PATH, EVENT)
    for expected, actual, label in ((reviewed["old_definition"], before, "old"),
                                    (reviewed["new_definition"], after, "current")):
        for key in ("file_sha256", "ordered_token_sha256", "line", "end_line"):
            require(actual[key] == expected[key], f"{label} reviewed {key} differs")

    fields = section_comparison(before, after)
    changed = [(row["field"], row["ordinal"]) for row in fields
               if row["classification"] != "unchanged-ordered-tokens"]
    require(changed == [("option", 0), ("option", 1), ("option", 2), ("trigger", 0)],
            f"Unexpected changed event fields: {changed}")
    for row in fields:
        if row["field"] == "option":
            require(len(row["token_differences"]) == 1, "Additional option change")
            delta = row["token_differences"][0]
            require(delta["old_tokens"] == ["stress_impact"]
                    and delta["new_tokens"] == ["stress_and_fulfillment_impact"],
                    "Option change is not the reviewed operation rename")

    caller_path = "common/on_action/ce1_on_actions.txt"
    caller_tree = archive if archive.root.joinpath(caller_path).is_file() else current
    old_payload, _, _ = old.read(caller_path)
    new_payload, _, _ = caller_tree.read(caller_path)
    require(sha256(old_payload) == sha256(new_payload)
            == reviewed["source_file_sha256"][caller_path], "Caller bytes differ")
    caller = caller_tree.definition(caller_path, "epidemic_ongoing_events")
    require("epidemic_events.5007" in caller["tokens"], "Caller no longer lists .5007")

    dependencies = {}
    for path, key in (
        ("common/scripted_triggers/00_relation_triggers.txt", "can_set_relation_potential_friend_trigger"),
        ("common/scripted_triggers/00_relation_triggers.txt", "can_set_relation_friend_trigger"),
        ("common/script_values/00_stress_values.txt", "minor_stress_impact_gain"),
        ("common/script_values/00_stress_values.txt", "miniscule_stress_impact_loss"),
    ):
        first, second = old.definition(path, key), archive.definition(path, key)
        require(first["tokens"] == second["tokens"], f"Selected-option dependency changed: {key}")
        dependencies[key] = {"old": portable_definition(first), "current": portable_definition(second),
                             "ordered_tokens_unchanged": True}

    religious_path = "common/scripted_triggers/00_religious_triggers.txt"
    religious = {}
    for stem in ("trait_is_shunned_or_criminal_in_", "trait_is_shunned_in_", "trait_is_criminal_in_"):
        first = old.definition(religious_path, stem + "faith_trigger")
        second = archive.definition(religious_path, stem + "rite_trigger")
        religious[stem + "rite_trigger"] = {
            "old": portable_definition(first), "current": portable_definition(second),
            "current_witch_parameter_tokens": [token for token in second["tokens"]
                                                if "witch" in token],
            "boundary": "Authored Rite crime/shunning gate only; native virtue evaluation is not reimplemented.",
        }

    sys.path.insert(0, str(ROOT / "ck3_autonomous_player/src"))
    from xar_autoplayer.vanilla_events.registry import query_vanilla_event_knowledge_v1
    from xar_autoplayer.vanilla_events.policy import _epidemic_5007_stress_effect_profile
    knowledge = query_vanilla_event_knowledge_v1(EVENT, "1.20.0.2")
    require(knowledge["status"] == "available", "Existing current-build consumer unavailable")
    require(knowledge["ck3_exe_sha256"] == NEW_EXE, "Existing consumer EXE identity differs")
    profile = _epidemic_5007_stress_effect_profile(knowledge, {"effect_indicators": {
        "status": "available", "coverage": "played-character-event-icon-indicators-1.20.0.2-v1",
        "complete_effect_set": False, "rows": [{"kind": "stress", "direction": "increase",
            "magnitude": {"status": "unavailable"}, "affected_by_trait": True, "critical": False}]}}, 2)
    require(profile is not None and profile["complete_effect_set"] is False,
            "Existing bounded stress-facet consumer no longer binds")

    return {
        "schema": "xar.ck3.event12002.epidemic-events-5007.source-proof.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(), "ck3_build": "1.20.0.2",
        "ck3_exe_sha256": NEW_EXE, "event_definition_key": EVENT,
        "old_source_root": str(old_root), "frozen_current_source_root": str(archive_root),
        "caller_source_root": str(caller_tree.root), "caller_archive_file_absent": caller_tree is current,
        "event": {"old": portable_definition(before), "current": portable_definition(after),
                  "changed_fields": [list(pair) for pair in changed],
                  "option_changes": "Each option changes only stress_impact to stress_and_fulfillment_impact"},
        "caller": portable_definition(caller), "caller_file_bytes_unchanged": True,
        "selected_option_dependencies": dependencies, "authored_religious_gates": religious,
        "existing_compatibility_file_sha256": sha256(compatibility_path.read_bytes()),
        "current_consumer_probe": {"knowledge_available": True, "stress_facet_profile": profile,
                                    "type": "synthetic direct-profile probe; no game or action"},
        "readiness": "static-ready", "production_changes_needed": False,
        "live_acceptance_performed": False, "natural_r0092_material_red_closed": False,
        "remaining": ["Current-build natural paused event projection, one typed selection, independent material state and next turn.",
                      "Accuser opinion, potential-friend relation and fulfillment material results are not supplied by this event consumer."],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-game-root", type=Path, default=DEFAULT_OLD)
    parser.add_argument("--archive-game-root", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--current-game-root", type=Path, default=DEFAULT_CURRENT)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = generate(args.old_game_root, args.archive_game_root, args.current_game_root)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "source-proof.json"
    output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": "GREEN", "proof_path": str(output),
                      "proof_sha256": sha256(output.read_bytes()), "readiness": result["readiness"],
                      "production_changes_needed": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
