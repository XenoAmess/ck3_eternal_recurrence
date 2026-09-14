#!/usr/bin/env python3
"""Verify the private character-interaction preview core and fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
ALLOWLIST = [
    "gift_interaction",
    "recruit_guest_interaction",
    "invite_to_court_interaction",
    "offer_vassalization_interaction",
    "demand_payment_interaction",
]
RESOURCE_KEYS = [
    "gold",
    "prestige",
    "piety",
    "renown",
    "influence",
    "herd",
    "treasury",
    "treasury_or_gold",
    "merit",
    "barter_goods",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"RED: {message}")


def load_object(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing JSON file: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"RED: cannot parse {path}: {exc}") from exc
    require(isinstance(value, dict), f"JSON root is not an object: {path}")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def verify_source_contract(native_root: Path, contract: dict[str, Any]) -> None:
    files = contract.get("files", {})
    header = (native_root / files.get("header", "")).read_text(encoding="utf-8")
    implementation = (native_root / files.get("implementation", "")).read_text(
        encoding="utf-8"
    )
    unit_test = (native_root / files.get("unit_test", "")).read_text(
        encoding="utf-8"
    )
    for token in contract.get("required_header_tokens", []):
        require(token in header, f"header token missing: {token}")
    for token in contract.get("required_implementation_tokens", []):
        require(token in implementation, f"implementation token missing: {token}")
    for token in contract.get("required_test_tokens", []):
        require(token in unit_test, f"unit-test token missing: {token}")
    private_core = header + "\n" + implementation
    for token in contract.get("forbidden_mutation_tokens", []):
        require(token not in private_core, f"mutation token entered private core: {token}")


def verify_fixture(fixture: dict[str, Any]) -> None:
    require(fixture.get("private_build") is True, "fixture is not private")
    require(fixture.get("read_only") is True, "fixture is not read-only")
    require(fixture.get("advertised") is False, "fixture is advertised")
    require(
        fixture.get("action_surface_present") is False,
        "fixture exposes an action surface",
    )
    require(fixture.get("status") == "available", "fixture is unavailable")
    definition = fixture.get("definition", {})
    require(
        definition.get("canonical_key") == "gift_interaction",
        "fixture definition key drifted",
    )
    require(
        definition.get("deterministic_key_hash") == 3512641005,
        "fixture definition hash drifted",
    )
    roles = fixture.get("roles", {})
    require(roles.get("actor_character_id") == 16777218, "actor ID drifted")
    require(
        roles.get("recipient_character_id") == 33554435,
        "recipient ID drifted",
    )
    require(fixture.get("can_send") is True, "fixture Can Send is false")
    costs = fixture.get("costs", {})
    require(costs.get("raw_scale") == 100000, "cost scale drifted")
    require(costs.get("payer_role") == "actor", "cost payer drifted")
    require(costs.get("application_timing") == "on_send", "cost timing drifted")
    entries = costs.get("entries", [])
    require(
        [entry.get("resource_key") for entry in entries] == RESOURCE_KEYS,
        "cost resource order drifted",
    )
    require(entries[3].get("raw") == -100000, "signed cost was clamped")
    acceptance = fixture.get("acceptance", {})
    require(acceptance.get("kind") == "ai_final", "acceptance kind drifted")
    require(
        acceptance.get("recipient_raw") == 12500000,
        "recipient raw acceptance drifted",
    )
    require(
        acceptance.get("outer_final_status_raw") == 0,
        "outer final acceptance drifted",
    )
    require(
        acceptance.get("would_accept_now") is True,
        "final acceptance projection drifted",
    )
    require(
        all(fixture.get("readiness", {}).values()),
        "fixture readiness is incomplete",
    )


def verify_abi(abi: dict[str, Any]) -> None:
    require(
        abi.get("private_key") == "character_interaction_preview_v1",
        "wrong private key",
    )
    require(
        abi.get("status") == "static-ready-private-core-unwired",
        "wrong implementation status",
    )
    exact = abi.get("exact_build", {})
    require(exact.get("product_version") == "1.19.0.6", "wrong product version")
    require(exact.get("executable_sha256") == EXE_SHA256, "wrong executable hash")
    require(
        abi.get("request", {}).get("first_allowlist") == ALLOWLIST,
        "preview allowlist drifted",
    )
    entries = abi.get("native_entry_contract", {})
    expected_entries = {
        "character_storage_slot_rva": "0x570C130",
        "definition_database_getter_rva": "0x831890",
        "stable_key_hash_rva": "0x3B8B000",
        "loaded_definition_lookup_rva": "0x997930",
        "construct_two_role_context_rva": "0x2C3EE50",
        "refresh_context_rva": "0x2C40950",
        "finalize_context_rva": "0x2C40B20",
        "final_can_send_rva": "0x2C43F00",
        "generic_cost_evaluator_rva": "0x2CDB7B0",
        "intermediary_raw_rva": "0x2C44220",
        "recipient_raw_rva": "0x2C44320",
        "outer_final_answer_rva": "0x2C43B40",
        "destroy_context_rva": "0x2C3F380",
    }
    for key, value in expected_entries.items():
        require(entries.get(key) == value, f"native entry drifted: {key}")
    readiness = abi.get("readiness", {})
    for key in (
        "private_core_implemented",
        "definition_lookup_entry_closed",
        "generation_bearing_character_lookup_implemented",
        "finalized_two_role_context_entry_closed",
        "final_can_send_entry_closed",
        "generic_cost_entry_closed",
        "final_acceptance_entry_closed",
        "same_frame_double_sample",
    ):
        require(readiness.get(key) is True, f"expected ready field is false: {key}")
    for key in (
        "native_binding_registered",
        "public_capability_registered",
        "action_surface_registered",
        "production_query_live",
        "planner_ready",
    ):
        require(readiness.get(key) is False, f"unearned readiness is true: {key}")


def verify_diplomatic_dependency(research: Path) -> None:
    contract = load_object(research / "core_diplomatic_proposals_v1_contract.json")
    spans = {
        row.get("name"): row for row in contract.get("native_pipeline", {}).get("spans", [])
    }
    expected = {
        "get_character_interaction_database": "0x831890",
        "pure_stable_key_hash": "0x3B8B000",
        "loaded_character_interaction_lookup_by_hash": "0x997930",
        "construct_two_role_character_interaction_context": "0x2C3EE50",
        "refresh_character_interaction_context": "0x2C40950",
        "finalize_character_interaction_context": "0x2C40B20",
        "validate_character_interaction_context": "0x2C43F00",
        "intermediary_ai_raw": "0x2C44220",
        "recipient_ai_raw": "0x2C44320",
        "outer_final_answer": "0x2C43B40",
    }
    for name, rva in expected.items():
        require(spans.get(name, {}).get("rva_start") == rva, f"DIPLO1 span drifted: {name}")


def verify_exact_build(abi: dict[str, Any], exe: Path) -> None:
    exact = abi["exact_build"]
    require(exe.is_file(), f"exact-build executable missing: {exe}")
    require(exe.stat().st_size == exact["executable_size"], "executable size mismatch")
    require(sha256(exe) == exact["executable_sha256"], "executable hash mismatch")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--native-root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--exe", type=Path)
    args = parser.parse_args()

    native_root = args.native_root.resolve()
    research = native_root / "research"
    contract = load_object(
        research / "fixtures/character_interaction_preview_v1_source_contract.json"
    )
    abi = load_object(research / "character_interaction_preview_v1_abi.json")
    fixture = load_object(
        research / "fixtures/character_interaction_preview_v1_available.json"
    )
    verify_source_contract(native_root, contract)
    verify_fixture(fixture)
    verify_abi(abi)
    verify_diplomatic_dependency(research)
    combined = json.dumps(contract, sort_keys=True) + json.dumps(abi, sort_keys=True)
    require("Z:\\" not in combined, "machine-specific path entered contract")
    require("Crusader Kings III" not in combined, "repository-relative game path entered contract")
    if args.exe is not None:
        verify_exact_build(abi, args.exe.resolve())
    print("GREEN: character-interaction-preview-v1 source/fixture contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
