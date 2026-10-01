#!/usr/bin/env python3
"""Record the bounded physician .1000 source migration; never accesses CK3."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from ck3_12002_nonwar_event_sources import SourceTree, compare_block


EVENT = "physician_epidemic_events.1000"
EXE_SHA256 = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"
REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "ck3_autonomous_player/src/xar_autoplayer/vanilla_events/data"
BLOCKS = (
    ("events/dlc/ce1/physician_epidemic_events.txt", EVENT),
    ("common/on_action/ce1_on_actions.txt", "epidemic_ongoing_events"),
    ("common/scripted_effects/06_dlc_ce1_epidemics_effects.txt", "get_random_nearby_realm_epidemic"),
    ("common/scripted_effects/00_relation_effects.txt", "progress_towards_rival_effect"),
    ("common/modifiers/06_ce1_modifiers.txt", "ce1_non_heretical_solution"),
    ("common/modifiers/06_ce1_modifiers.txt", "ce1_unorthodox_epidemic_treatment"),
    ("common/script_values/00_stress_values.txt", "medium_stress_impact_gain"),
    ("common/script_values/00_stress_values.txt", "minor_stress_impact_gain"),
    ("common/script_values/00_stress_values.txt", "minor_stress_impact_loss"),
)


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-game-root", type=Path, default=Path(
        "Z:/Crusader Kings III/Crusader Kings III_1.19.0.6_20260604/game"))
    parser.add_argument("--new-game-root", type=Path, default=Path(
        "Z:/SteamLibrary/steamapps/common/Crusader Kings III/game"))
    parser.add_argument("--artifact-dir", type=Path, default=Path(
        "Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/events12002/physician1000"))
    args = parser.parse_args()
    old, new = SourceTree(args.old_game_root), SourceTree(args.new_game_root)
    rows = {key: compare_block(old, new, path, key) for path, key in BLOCKS}
    compatibility_path = DATA / "source_compatibility_1_20_0_2.json"
    compatibility = json.loads(compatibility_path.read_text(encoding="utf-8"))
    prior = compatibility["events"][EVENT]
    event = rows[EVENT]
    if compatibility["ck3_exe_sha256"] != EXE_SHA256:
        raise ValueError("existing compatibility ledger is not the frozen 1.20.0.2 build")
    for version in ("old_definition", "new_definition"):
        if event[version] != prior[version]:
            raise ValueError(f"event source differs from reviewed {version}")
    if event["token_differences"] != prior["token_differences"]:
        raise ValueError("event token differences drifted from existing source review")
    if prior.get("policy_contract_compatible") is not True:
        raise ValueError("existing bounded consumer contract has not been reviewed")
    for path, expected_hash in prior["source_file_sha256"].items():
        if digest(args.new_game_root.joinpath(path).read_bytes()) != expected_hash:
            raise ValueError(f"installed source differs from existing exact snapshot: {path}")
    expected = [{"old_tokens": ["stress_impact"],
                 "new_tokens": ["stress_and_fulfillment_impact"]}] * 2
    observed = [{"old_tokens": row["old_tokens"], "new_tokens": row["new_tokens"]}
                for row in event["token_differences"]]
    if observed != expected:
        raise ValueError("expected only the two reviewed effect replacements")
    relation_path = "common/scripted_effects/00_relation_effects.txt"
    relation_key = "progress_towards_rival_effect"
    relation_old = old.definition(relation_path, relation_key)["tokens"]
    relation_new = new.definition(relation_path, relation_key)["tokens"]
    saved_target = ["$CHARACTER$", "=", "{", "save_scope_as", "=", "target_char", "}"]
    if relation_new[3:10] != saved_target:
        raise ValueError("rival helper target binding differs from the reviewed refactor")
    normalized = relation_new[:3] + relation_new[10:]
    normalized = [token.replace("scope:target_char", "$CHARACTER$") for token in normalized]
    positive = ["$CHARACTER$", "=", "{", "highest_held_title_tier", ">", "tier_barony", "}"]
    negated = ["NOT", "=", "{", "$CHARACTER$", "=", "{", "highest_held_title_tier", "<=", "tier_barony", "}", "}"]
    start = next(i for i in range(len(normalized)) if normalized[i:i + len(positive)] == positive)
    normalized[start:start + len(positive)] = negated
    if normalized != relation_old:
        raise ValueError("rival helper has changes beyond target binding and valid-target tier comparison")
    # These direct blocks are source inputs, not a transitive engine proof.
    source_blocks = {}
    for path, key in BLOCKS:
        definition = new.definition(path, key)
        _, text, _ = new.read(path)
        source_blocks[key] = "\n".join(text.splitlines()[
            definition["line"] - 1:definition["end_line"]])
    report = {
        "schema": "xar.ck3.event12002.physician-epidemic-events-1000-source-review.v1",
        "ck3_build": "1.20.0.2",
        "ck3_exe_sha256": EXE_SHA256,
        "source_roots": {"old": str(args.old_game_root), "new": str(args.new_game_root),
                         "new_source_hashes_match_existing_exact_snapshot": True},
        "status": "source-reviewed-bounded-consumer-reuse",
        "readiness": "static-ready",
        "live_acceptance_performed": False,
        "production_code_changed": False,
        "consumer_tests_rerun": False,
        "existing_compatibility": {
            "path": compatibility_path.relative_to(REPO).as_posix(),
            "file_sha256": digest(compatibility_path.read_bytes()),
            "dataset_sha256": compatibility["dataset_sha256"],
            "event_review": prior["manual_review"],
        },
        "direct_blocks": rows,
        "new_source_blocks": source_blocks,
        "verification": {
            "event_matches_existing_review": True,
            "only_two_stress_operation_replacements": True,
            "rival_helper_refactor_normalized_tokens_equal": True,
            "rival_helper_equivalence_boundary": "Valid CHARACTER resolution only; no missing-target, relation-trigger, or full transitive engine equality claim.",
            "unchanged_direct_blocks": [key for key, row in rows.items()
                                        if row["classification"] == "unchanged-ordered-tokens"],
            "full_transitive_dependency_compatibility_proven": False,
        },
        "consumer_inputs": {
            "semantic_choice": {
                "event_identity": EVENT,
                "root": "current played CharacterID; exact typed identity",
                "saved_scopes": {"epidemic": "epidemic (opaque)",
                                 "epidemic_scope": "epidemic (opaque)",
                                 "physician": "character; distinct non-player",
                                 "zealous_courtier": "character; distinct non-player"},
                "snapshot_option_count": 3,
                "enabled_rendered_native_indices": [1, 2],
                "selected_native_index": 1,
                "selected_authored_number": 2,
                "projection": "same paused snapshot/revision/date and unique current event window",
                "boundary": "reuse bounded continuation; no complete effect or global optimum claim",
            },
            "independent_material": {
                "resistance": "fixed modifier presence before/after; old 1.19 provider is not migrated by this source review",
                "stress": "current Snapshot stress_points may independently read counters; authored delta requires trait/immunity/cap context",
                "fulfillment": "current signed Q100000 spiritual_fulfillment_raw before/after via new religion context; fixture-ready, paused and MCP integration qualification tracked by its owner",
                "relationship": "physician/opponent existing rivalry state or progress, independent before/after; not supplied by event disappearance",
                "duration": "five years is authored; remaining_days ABI unverified",
            },
        },
        "rival_helper": {
            "actor": "scope:zealous_courtier",
            "target": "scope:physician saved to target_char at helper entry",
            "inputs": ["full actor/target identity", "highest_held_title_tier", "family/consort/heir relation",
                       "grudge/potential_rival/rival state", "native can_set_relation predicates"],
            "branches": [
                "social-rank exclusion: create grudge; existing grudge adds -20 grudge opinion",
                "existing potential rival and native can_set_relation_rival: create rival",
                "otherwise native may create potential rival; OPINION=0 suppresses the hate-opinion branch",
            ],
            "boundary": "The event asks to progress the relation, not a guarantee that full rivalry is created.",
        },
        "legacy_live_boundary": {
            "run": "R0089",
            "event_instance_id": 21,
            "root_character_id": 36403,
            "date_raw": 53350560,
            "selected_native_index": 1,
            "status": "natural-production-generic-fallback-red",
            "artifact_sha256": "79661336F22CEEA10A21FA41B84654BA86087EF44492CD1FFABE64ABD4E3C9FC",
            "modifier_stress_rivalry_material_proven": False,
            "new_build_live_proven": False,
        },
    }
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    output = args.artifact_dir / "source-review.json"
    payload = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    output.write_bytes(payload)
    print(json.dumps({"status": "GREEN", "source_review": str(output),
                      "sha256": digest(payload),
                      "unchanged_direct_blocks": report["verification"]["unchanged_direct_blocks"],
                      "changed_direct_blocks": [key for key, row in rows.items()
                                                if row["classification"] != "unchanged-ordered-tokens"]},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
