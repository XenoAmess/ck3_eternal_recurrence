#!/usr/bin/env python3
"""Freeze the narrow .1100 source migration proof without CK3 or a process API."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from ck3_12002_nonwar_event_sources import (
    SourceTree, assignments, canonical_bytes, compare_block,
    portable_definition, sha256, values,
)

KEY = "epidemic_events.1100"
EVENT_PATH = "events/dlc/ce1/epidemic_events.txt"
EXE_SHA256 = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"
ADDED = ["pam_epidemic_arrival_spiritual_fulfillment_loss_effect", "=", "yes"]
DEPENDENCIES = [
    ("common/scripted_effects/06_dlc_ce1_epidemics_effects.txt", "notify_holders_and_above"),
    ("common/scripted_effects/06_dlc_ce1_epidemics_effects.txt", "add_plague_county_modifiers"),
    ("common/scripted_effects/06_dlc_ce1_legitimacy_effects.txt", "epidemic_outbreak_legitimacy_effect"),
    ("common/scripted_effects/07_dlc_ep3_scripted_effects.txt", "increase_governance_effect"),
]


def nested_assignment(tree: SourceTree, path: str, key: str) -> dict:
    payload, _, tokens = tree.read(path)
    matches = []
    for position, token in enumerate(tokens[:-2]):
        if token.value == key and tokens[position + 1].value == "=":
            matches.append(assignments(tokens[position:])[0][1])
    if len(matches) != 1:
        raise ValueError(f"Expected one assignment for {key}, found {len(matches)}")
    body = matches[0]
    return {"relative_path": path, "file_sha256": sha256(payload),
            "line": body[0].line, "end_line": body[-1].line,
            "tokens": values(body),
            "ordered_token_sha256": sha256(canonical_bytes(values(body)))}


def generate(repo: Path, old_root: Path, new_root: Path) -> dict:
    old, new = SourceTree(old_root), SourceTree(new_root)
    data = repo / "ck3_autonomous_player/src/xar_autoplayer/vanilla_events/data"
    compatibility_path = data / "source_compatibility_1_20_0_2.json"
    frozen = json.loads(compatibility_path.read_text(encoding="utf-8-sig"))["events"][KEY]
    event = compare_block(old, new, EVENT_PATH, KEY)
    checks = []

    def check(name: str, passed: bool) -> None:
        checks.append({"name": name, "passed": passed})

    for build in ("old", "new"):
        check(f"{build}_body_matches_existing_migration_evidence",
              event[f"{build}_definition"] == frozen[f"{build}_definition"])
    changes = event["token_differences"]
    check("only_three_identical_additive_option_effects", len(changes) == 3 and all(
        row["kind"] == "insert" and row["old_tokens"] == []
        and row["new_tokens"] == ADDED for row in changes))
    changed_fields = [(row["field"], row["ordinal"]) for row in event["fields"]
                      if row["classification"] != "unchanged-ordered-tokens"]
    check("only_option_fields_changed", changed_fields == [("option", 0), ("option", 1), ("option", 2)])
    dependencies = {key: compare_block(old, new, path, key) for path, key in DEPENDENCIES}
    for key, row in dependencies.items():
        check(f"{key}_ordered_tokens_unchanged", row["classification"] == "unchanged-ordered-tokens")
    defaults = {}
    for key in ("DEFAULT_HOLDER_INFECTION_EVENT", "DEFAULT_LIEGE_INFECTION_EVENT"):
        first = nested_assignment(old, "common/defines/00_defines.txt", key)
        second = nested_assignment(new, "common/defines/00_defines.txt", key)
        defaults[key] = {"old": first, "new": second}
        check(f"{key}_unchanged", first["tokens"] == second["tokens"])
    effects = {}
    for key in ("pam_epidemic_arrival_spiritual_fulfillment_loss_effect",
                "pam_epidemic_spiritual_fulfillment_loss_effect"):
        row = new.definition("common/scripted_effects/pam_effects.txt", key)
        effects[key] = {**portable_definition(row), "tokens": row["tokens"]}
    scalar_values = {}
    for size, amount in (("medium", 5), ("major", 10), ("massive", 20)):
        value_key = f"{size}_spiritual_fulfillment_value"
        loss_key = f"{size}_spiritual_fulfillment_loss"
        value = new.definition("common/script_values/pam_values.txt", value_key)
        loss = new.definition("common/script_values/pam_values.txt", loss_key)
        scalar_values[value_key] = {**portable_definition(value), "tokens": value["tokens"]}
        scalar_values[loss_key] = {**portable_definition(loss), "tokens": loss["tokens"]}
        check(f"{size}_loss_resolves_to_minus_{amount}",
              value["tokens"] == [value_key, "=", str(amount)]
              and loss["tokens"] == [loss_key, "=", "{", "add", "=", value_key,
                                     "multiply", "=", "-1", "}"])
    gate = effects["pam_epidemic_spiritual_fulfillment_loss_effect"]["tokens"]
    check("playable_and_both_exemptions_absent_gate", gate == [
        "pam_epidemic_spiritual_fulfillment_loss_effect", "=", "{", "if", "=", "{",
        "limit", "=", "{", "is_playable_character", "=", "yes", "NOR", "=", "{",
        "rite", "=", "{", "rite_has_parameter", "=", "no_epidemic_fulfillment_loss_active", "}",
        "has_personal_tenet_flag", "=", "no_epidemic_fulfillment_loss_personal_active", "}", "}",
        "change_spiritual_fulfillment", "=", "$AMOUNT$", "}", "}"])
    arrival = effects["pam_epidemic_arrival_spiritual_fulfillment_loss_effect"]["tokens"]
    check("ordered_intensity_mapping_apocalyptic_major_else", arrival == [
        "pam_epidemic_arrival_spiritual_fulfillment_loss_effect", "=", "{", "if", "=", "{",
        "limit", "=", "{", "scope:epidemic", "=", "{", "outbreak_intensity", "=", "apocalyptic", "}", "}",
        "pam_epidemic_spiritual_fulfillment_loss_effect", "=", "{", "AMOUNT", "=", "massive_spiritual_fulfillment_loss", "}", "}",
        "else_if", "=", "{", "limit", "=", "{", "scope:epidemic", "=", "{", "outbreak_intensity", "=", "major", "}", "}",
        "pam_epidemic_spiritual_fulfillment_loss_effect", "=", "{", "AMOUNT", "=", "major_spiritual_fulfillment_loss", "}", "}",
        "else", "=", "{", "pam_epidemic_spiritual_fulfillment_loss_effect", "=", "{",
        "AMOUNT", "=", "medium_spiritual_fulfillment_loss", "}", "}", "}"])
    paths = ["ck3_autonomous_player/src/xar_autoplayer/vanilla_events/records_embedded_a.py",
             "ck3_autonomous_player/src/xar_autoplayer/vanilla_events/records_analysis_embedded_a.py",
             "ck3_autonomous_player/src/xar_autoplayer/vanilla_events/policy.py",
             "ck3_autonomous_player/src/xar_autoplayer/vanilla_events/data/source_compatibility_reviews_1_20_0_2.json"]
    return {"schema": "xar.event12002.epidemic-events-1100.source-migration.v1",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "ck3_build": "1.20.0.2 Crozier / Steam25588574", "ck3_exe_sha256": EXE_SHA256,
            "executable_pin_evidence": "Reused coordinator frozen exact-build pin; no executable or process accessed.",
            "old_root": str(old_root), "new_root": str(new_root),
            "existing_migration_file_sha256": sha256(compatibility_path.read_bytes()),
            "existing_review_reused": True, "event": event,
            "unchanged_direct_dependencies": dependencies, "default_selector_assignments": defaults,
            "new_additive_effect_definitions": effects, "new_additive_script_values": scalar_values,
            "source_semantics": {"apocalyptic_delta": -20, "major_delta": -10, "other_delta": -5,
                "gate": "Playable character; neither Rite parameter nor personal-tenet exemption active.",
                "all_options_share_effect": True, "existing_native_0_contract_reusable": True,
                "actual_engine_clamp_and_material_result_proven": False},
            "consumer_source_sha256": {path: sha256((repo / path).read_bytes()) for path in paths},
            "checks": checks, "result": "GREEN" if all(row["passed"] for row in checks) else "RED",
            "readiness": "static-ready source contract; new-build paused/action/material pending",
            "live_acceptance_performed": False, "policy_or_registry_changed": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--old-game-root", type=Path,
                        default=Path("Z:/Crusader Kings III/Crusader Kings III_1.19.0.6_20260604/game"))
    parser.add_argument("--new-game-root", type=Path,
                        default=Path("Z:/ck3_mod_rewrite/artifacts/migrations/2026-09-30/post-update-1.20.0.2/installation/game"))
    parser.add_argument("--artifact-dir", type=Path,
                        default=Path("Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/events12002/epidemic1100"))
    args = parser.parse_args()
    document = generate(args.repo, args.old_game_root, args.new_game_root)
    document["research_script_sha256"] = sha256(Path(__file__).read_bytes())
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    output = args.artifact_dir / "source-proof.json"
    payload = (json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    output.write_bytes(payload)
    print(json.dumps({"result": document["result"], "checks": len(document["checks"]),
                      "failed_checks": [row["name"] for row in document["checks"] if not row["passed"]],
                      "artifact": str(output), "artifact_sha256": sha256(payload)}, ensure_ascii=False))
    return 0 if document["result"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
