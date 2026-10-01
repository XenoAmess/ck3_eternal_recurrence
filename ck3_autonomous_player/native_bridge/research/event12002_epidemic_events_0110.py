#!/usr/bin/env python3
"""Index existing .0110 source migration and its actual material input gap.

File-only: reuse the reviewed narrow dependency ledger. Do not regenerate
event policy, inspect a process, or reinterpret old live outcomes as 1.20 live.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


BUILD = "1.20.0.2"
EXE_SHA256 = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"
EVENT = "epidemic_events.0110"
LEGACY_EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def source_pin(repo: Path, path: str) -> dict[str, object]:
    payload = repo.joinpath(path).read_bytes()
    return {"path": path, "sha256": digest(payload), "size_bytes": len(payload)}


def generate(repo: Path, game_root: Path) -> dict[str, object]:
    compatibility_path = "ck3_autonomous_player/src/xar_autoplayer/vanilla_events/data/source_compatibility_1_20_0_2.json"
    payload = repo.joinpath(compatibility_path).read_bytes()
    ledger = json.loads(payload)
    event = ledger["events"][EVENT]
    narrow = ledger["epidemic_events_0110_narrow_dependency_review"]
    reviewed_source_files = event["source_file_sha256"]
    file_checks = []
    for relative, expected in sorted(reviewed_source_files.items()):
        path = game_root / relative
        actual = digest(path.read_bytes()) if path.is_file() else None
        if actual is not None and actual != expected.upper():
            raise ValueError(f"Frozen source differs from reviewed ledger: {relative}")
        file_checks.append({
            "path": relative, "reviewed_sha256": expected.upper(),
            "local_sha256": actual,
            "validation": "hash_match" if actual is not None else "not_in_partial_frozen_tree",
        })

    legacy_path = "ck3_autonomous_player/native_bridge/src/player_epidemic_recovery_v1.cpp"
    legacy = repo.joinpath(legacy_path).read_text(encoding="utf-8-sig")
    addresses = {name: value for name, value in re.findall(
        r"constexpr std::uintptr_t (k\w+) = (0x[0-9A-F]+);", legacy)}
    required_legacy = {
        "kVariableContextForScopeRva": "0x3329A40",
        "kGetVariableIdentifierTableRva": "0x3B971A0",
        "kLookupVariableIdentifierRva": "0x3B97020",
        "kVariableIdentifierNameRva": "0x3B97090",
        "kLandedTitleStoreSlotRva": "0x570C410",
        "kCountyModifierGetterRva": "0x1942CB0",
        "kModifierDatabaseRva": "0x88F370",
        "kStableKeyHashRva": "0x3B8B000",
        "kModifierLookupRva": "0xA41F10",
        "kModifierFallbackSlotRva": "0x570C968",
    }
    if addresses != required_legacy:
        raise ValueError("Legacy provider changed; update this bounded handoff before reuse")

    phase_path = "ck3_autonomous_player/native_bridge/include/xar_bridge/ck3_12002_phase_definitions.hpp"
    phase = repo.joinpath(phase_path).read_text(encoding="utf-8-sig")
    phase_addresses = {}
    for name in ("kPhaseVariableContextRva", "kPhaseVariableIdentifierTableRva",
                 "kPhaseVariableIdentifierLookupRva", "kPhaseVariableIdentifierNameRva"):
        match = re.search(rf"{name} = (0x[0-9A-F]+);", phase)
        if match is None:
            raise ValueError(f"Missing migrated shared variable binding: {name}")
        phase_addresses[name] = match.group(1)

    reviewed_blocks = {key: {
        "classification": row["classification"],
        "new_definition": row["new_definition"],
    } for key, row in sorted(narrow["blocks"].items())}
    if len(reviewed_blocks) != 13 or len(narrow["on_province_recovered_callers"][BUILD]["hooks"]) != 7:
        raise ValueError("Expected the existing 13-block / 7-hook narrow review")
    if event.get("policy_contract_compatible") is not True:
        raise ValueError("Existing bounded policy source contract is not reusable")

    reusable_paths = [
        "docs/ck3-native-ai/ck3-1.20.0.2-nonwar-events.md",
        "ck3_autonomous_player/native_bridge/research/ck3_12002_nonwar_event_sources.py",
        compatibility_path,
        "ck3_autonomous_player/src/xar_autoplayer/epidemic_recovery_formal_observer.py",
        "ck3_autonomous_player/src/xar_autoplayer/bridge/epidemic_recovery_private_transport.py",
        "ck3_autonomous_player/src/xar_autoplayer/vanilla_events/policy.py",
        legacy_path,
        "ck3_autonomous_player/native_bridge/src/player_epidemic_recovery_v1_mailbox.cpp",
        phase_path,
    ]
    return {
        "schema": "xar.event12002.epidemic-0110-source-handoff.v1",
        "build": BUILD, "executable_sha256": EXE_SHA256,
        "event_definition_key": EVENT,
        "status": "source-static-ready-material-provider-migration-pending",
        "source_contract_reused": True, "production_code_changed": False,
        "live_executed": False, "new_g2_credit": 0,
        "definition": event["new_definition"],
        "source_files": file_checks,
        "manual_review": event["manual_review"],
        "reviewed_blocks": reviewed_blocks,
        "recovered_province_hooks": narrow["on_province_recovered_callers"][BUILD],
        "reviewed_semantics": narrow["reviewed_semantics"],
        "input_contract": {
            "finite_choice": {
                "root": "same paused living played CharacterID",
                "saved_scopes": "required epidemic; optional new_preferred_capital",
                "supported_shown_enabled_native_options": [1, 2],
                "selected_authored_option": 3, "selected_native_option_index": 2,
                "selected_step": "select-event-option-3",
                "unqualified_projection": [0, 1, 2],
            },
            "before": [
                "same paused snapshot/native revision, date, episode and event instance",
                "formerly_infected_counties full-generation LandedTitleIDs",
                "each county minor_present and tiny_present",
                "same played character current player_legitimacy_v1 raw Q100000",
            ],
            "after": [
                "independent newer paused revision on same date/episode/CharacterID",
                "old event instance absent",
                "explicit frozen LandedTitleID queries after the source clears the list",
                "each county minor/tiny presence and same-character legitimacy",
                "next formal turn and paired checkpoint",
            ],
            "remaining_days": "unavailable; pre-existing presence cannot prove renewal",
            "legitimacy_expectation": "conditional authored -20; new scripted eligibility is narrower, never an unconditional delta assertion",
        },
        "material_provider_gap": {
            "legacy_provider": source_pin(repo, legacy_path),
            "legacy_executable_sha256": LEGACY_EXE_SHA256,
            "legacy_addresses": addresses,
            "legacy_offsets": {
                "character_full_id": "0x18", "title_full_id": "0x10",
                "title_definition": "0x160", "definition_tier": "0x5C",
                "variable_list_rows": "0x30", "variable_list_count": "0x3C",
                "variable_list_stride": "0x48", "elements_stride": "0x10",
            },
            "existing_12002_variable_bindings": phase_addresses,
            "existing_variable_binding_scope": "identifier/context only; does not establish list rows or county-modifier presence ABI",
            "current_12002_registration": "No CE1 replacement in RegisterNonwarMailboxExecutorsV1; legacy CE1 route/mailbox still uses BindCurrentProcess and old ReadSnapshot",
            "next_work": "Bind actual 12002 county list/full-title identity/modifier-definition lookup/county-presence getter to the existing same-day observer and shared 12002 mailbox",
            "policy_or_new_gate_required": False,
        },
        "historical_evidence": {
            "R0099": "optional_scope_types projection RED before submit; historical consumer fix already exists",
            "R0101": "natural authored3/native2 action and instance removal; no same-day county/legitimacy pair",
            "R0113_R0116": "283 to 263 legitimacy over fifteen game days, not exclusive material attribution",
            "current_natural_scene_available": False,
        },
        "reused_repository_evidence": [source_pin(repo, path) for path in reusable_paths],
        "validation": "One bounded file/hash and existing-source-contract check; no replay of previously passed policy/ABI matrices",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = generate(args.repo.resolve(), args.game_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output.read_bytes()),
                      "status": result["status"], "reviewed_blocks": len(result["reviewed_blocks"]),
                      "hooks": len(result["recovered_province_hooks"]["hooks"]),
                      "production_code_changed": False, "live_executed": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
