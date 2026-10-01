"""Compare only health.1101 and its direct recovery/schedule dependencies.

This is a source proof. It does not operate CK3 or confer current-build live
qualification on the historical R0085/R0086 artifacts.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ck3_12002_nonwar_event_sources import (
    SourceTree,
    assignments,
    canonical_bytes,
    compare_block,
    sha256,
    token_diff,
    values,
)

OLD_EXE = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
NEW_EXE = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"
EFFECTS = "common/scripted_effects/20_health_effects.txt"


def ill_schedule(tree: SourceTree, key: str) -> dict[str, object]:
    definition = tree.definition(EFFECTS, key)
    candidates = []

    def visit(body):
        if len(body) < 4 or body[2].value != "{":
            return
        for name, child in assignments(body[3:-1]):
            tokens = values(child)
            if (name in {"if", "else_if"} and "health.1101" in tokens
                    and "flag:ill" in tokens):
                candidates.append(child)
            visit(child)

    visit(definition["token_objects"])
    if not candidates:
        raise ValueError(f"No reviewed ill schedule in {key}")
    # Select the nearest enclosing authored condition, not the full disease
    # lifecycle or unrelated scheduling branches.
    branch = min(candidates, key=len)
    tokens = values(branch)
    if len([token for token in tokens if token == "health.1101"]) != 1:
        raise ValueError(f"Ambiguous health.1101 schedule in {key}")
    return {
        "relative_path": EFFECTS,
        "enclosing_effect": key,
        "line": branch[0].line,
        "end_line": branch[-1].line,
        "file_sha256": definition["file_sha256"],
        "ordered_token_sha256": sha256(canonical_bytes(tokens)),
        "tokens": tokens,
    }


def generate(old_root: Path, new_root: Path, source_root: Path):
    old_tree, new_tree = SourceTree(old_root), SourceTree(new_root)
    compatibility_path = source_root / (
        "ck3_autonomous_player/src/xar_autoplayer/vanilla_events/data/"
        "source_compatibility_1_20_0_2.json")
    compatibility = json.loads(compatibility_path.read_bytes())
    old_indexed = compatibility["events"]["health.1101"]
    event = compare_block(old_tree, new_tree, "events/health_events.txt", "health.1101")
    for side in ("old_definition", "new_definition"):
        if event[side] != old_indexed[side]:
            raise ValueError(f"{side} does not match existing frozen compatibility")
    expected_effect_files = old_indexed["caller_candidate_files"][0]
    if expected_effect_files["relative_path"] != EFFECTS:
        raise ValueError("Existing direct caller file changed")
    for tree, expected in ((old_tree, expected_effect_files["old_file_sha256"]),
                           (new_tree, expected_effect_files["new_file_sha256"])):
        if sha256(tree.read(EFFECTS)[0]) != expected:
            raise ValueError("Effect file does not match frozen compatibility")

    specs = [(EFFECTS, name) for name in (
        "recover_from_disease_effect",
        "recover_from_disease_notify_effect",
        "remove_disease_treatment_effect",
    )]
    specs += [("common/scripted_triggers/20_health_triggers.txt", name) for name in (
        "has_treatable_disease_trigger", "inform_about_relative_recovery_trigger")]
    specs += [("common/script_values/10_health_values.txt", name) for name in (
        "minimum_recovery_time", "ill_recovery_min", "ill_recovery_max")]
    specs.append(("common/script_values/00_basic_values.txt", "death_chance_dying_health"))
    blocks = {name: compare_block(old_tree, new_tree, path, name)
              for path, name in specs}
    schedules = {}
    for key in ("contract_disease_effect", "recover_from_disease_notify_effect"):
        old, new = ill_schedule(old_tree, key), ill_schedule(new_tree, key)
        schedules[key] = {
            "classification": ("unchanged-ordered-tokens"
                               if old["tokens"] == new["tokens"]
                               else "changed-ordered-tokens"),
            "old": old,
            "new": new,
            "token_differences": token_diff(old["tokens"], new["tokens"]),
        }
    unchanged = event["classification"] == "unchanged-ordered-tokens" and all(
        row["classification"] == "unchanged-ordered-tokens"
        for row in [*blocks.values(), *schedules.values()])
    doc = {
        "schema": "xar.ck3.event12002.health1101.source-proof.v1",
        "event_definition_key": "health.1101",
        "old_build": {"version": "1.19.0.6", "exe_sha256": OLD_EXE},
        "current_build": {"version": "1.20.0.2", "steam_build_id": 25588574,
                          "exe_sha256": NEW_EXE},
        "existing_compatibility_file_sha256": sha256(compatibility_path.read_bytes()),
        "comparison": "ordered tokens; comments/whitespace ignored, strings and order preserved",
        "event": event,
        "direct_blocks": blocks,
        "ill_schedules": schedules,
        "reviewed_narrow_dependencies_unchanged": unchanged,
        "full_transitive_dependency_graph_proven": False,
        "scope": "event body, direct recovery/cleanup/notify effects, ill schedule conditions/delays, direct cleanup/notification eligibility and recovery values",
        "consumer": {
            "reuse": "existing health.1101 exact saved-scope contract and direct variant consumer",
            "played_character_required": True,
            "root_equals_played_character": True,
            "sick_character_equals_played_character": True,
            "scope_variants": [
                {"names": ["physician", "sick_character", "disease_type"],
                 "types": {"physician": "character", "sick_character": "character", "disease_type": "flag"},
                 "physician_differs_from_played_character": True},
                {"names": ["sick_character", "disease_type"],
                 "types": {"sick_character": "character", "disease_type": "flag"},
                 "physician_required": False},
            ],
            "disease_flag_value": "opaque; no inferred identity from unavailable payload",
            "snapshot_option_count": 1,
            "sole_shown_enabled_native_option": 0,
            "selected_authored_option_number": 1,
            "new_source_requires_additional_consumer_input": False,
            "runtime_binding": ["current played character", "same-frame instance/date/native revision", "typed root/saved scopes", "current shown/enabled option projection", "active event snapshot option count"],
            "implementation_paths": [
                "ck3_autonomous_player/src/xar_autoplayer/vanilla_events/records_manager_a.py",
                "ck3_autonomous_player/src/xar_autoplayer/vanilla_events/policy.py",
                "ck3_autonomous_player/src/xar_autoplayer/vanilla_events/migration_1_20_0_2.py",
            ],
        },
        "historical_evidence": {
            "R0085": {"build": "1.19.0.6", "qualification": "natural paused RED", "selection_attempted": False,
                      "failure": "registered_contract_requires_extended_consumer", "artifact_sha256": "500EACF9BCDC43375EE2EDF27D0AF61E436EDBDB5DCE5652B5DC3825CEBFC14D"},
            "R0086": {"build": "1.19.0.6", "qualification": "production event-modal continuity", "manifest_sha256": "B4044ABAB75ACB8540B441C6BDB503BB8A65E1BD8A36DDF578DEA2EC2D2BB677",
                      "postcondition": "instance17 absent on independent next paused frame, next formal turn consumed absence without replay",
                      "independent_ill_trait_readback": False},
        },
        "current_readiness": "static-ready" if unchanged else "source-change-review-required",
        "live_acceptance_performed": False,
        "remaining": [
            "Current-build natural health.1101 exact projection and one typed acknowledgement, independent instance absence and next formal turn.",
            "No independent ill-trait or health gain claim; removal is immediate before option selection.",
            "Historical actual caller unresolved; no dedicated natural-event waiting worker.",
        ],
    }
    doc["dataset_sha256"] = sha256(canonical_bytes(doc))
    return doc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-game-root", type=Path, required=True)
    parser.add_argument("--new-game-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()
    document = generate(args.old_game_root, args.new_game_root, args.source_root)
    payload = (json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(payload)
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    args.artifact_dir.joinpath(args.output.name).write_bytes(payload)
    receipt = {
        "schema": "xar.ck3.event12002.health1101.source-comparison-receipt.v1",
        "script_sha256": sha256(Path(__file__).read_bytes()),
        "output_sha256": sha256(payload),
        "dataset_sha256": document["dataset_sha256"],
        "old_game_root": str(args.old_game_root),
        "new_game_root": str(args.new_game_root),
        "reviewed_block_count": 1 + len(document["direct_blocks"]),
        "reviewed_ill_schedule_count": len(document["ill_schedules"]),
        "reviewed_narrow_dependencies_unchanged": document["reviewed_narrow_dependencies_unchanged"],
        "live_acceptance_performed": False,
        "readiness": document["current_readiness"],
    }
    args.artifact_dir.joinpath("source-comparison-receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
