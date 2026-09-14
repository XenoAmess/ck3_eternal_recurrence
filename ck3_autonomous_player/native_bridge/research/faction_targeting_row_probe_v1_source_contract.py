#!/usr/bin/env python3
"""Verify the FACTION7 private faction-targeting probe contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXPECTED_BUILD = "1.19.0.6"
EXPECTED_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
EXPECTED_STATUS = "static-ready-private-probe-pending-shared-wiring"
EXPECTED_NEXT_SEAM = (
    "wire_faction_targeting_row_probe_v1_into_shared_bridge_private_heartbeat"
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"JSON root must be an object: {path}")
    return value


def _walk_keys(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _check_tokens(text: str, tokens: list[str], owner: str) -> None:
    for token in tokens:
        _require(token in text, f"{owner} token missing: {token}")


def _check_cpp_string_tokens(text: str, tokens: list[str], owner: str) -> None:
    for token in tokens:
        escaped = token.replace('"', '\\"')
        _require(
            token in text or escaped in text,
            f"{owner} token missing: {token}",
        )


def _check_fixture_common(fixture: dict[str, Any], case: str) -> None:
    _require(fixture["schema_version"] == 1, f"{case} fixture schema drifted")
    _require(
        fixture["schema"] == "g2_faction_targeting_row_probe_v1",
        f"{case} fixture private schema drifted",
    )
    _require(fixture["case"] == case, f"{case} fixture case drifted")
    _require(fixture["offline_fixture"] is True, f"{case} must remain offline")
    _require(
        fixture["exact_build"]
        == {
            "product_version": EXPECTED_BUILD,
            "executable_sha256": EXPECTED_SHA256,
        },
        f"{case} exact-build binding drifted",
    )
    _require(
        fixture["required_binding"]
        == {
            "paused": True,
            "proof_epoch": 42,
            "snapshot_revision": 412,
            "date_raw": 777,
            "player_character_id": 29829,
        },
        f"{case} required paused binding drifted",
    )
    for field in (
        "raw_pointers_persisted",
        "raw_pointer_fields_persisted",
        "raw_row_bytes_persisted",
        "raw_member_row_bytes_persisted",
        "public_readiness_changed",
    ):
        _require(fixture[field] is False, f"{case} private boundary drifted: {field}")
    prohibited = {
        "module_base",
        "owner_pointer",
        "data_pointer",
        "row_pointer",
        "member_row_pointer",
        "member_data_pointer",
        "pointer_hash",
        "raw_row_bytes",
        "raw_member_row_bytes",
    }
    _require(
        prohibited.isdisjoint(set(_walk_keys(fixture))),
        f"{case} fixture leaked a process-local pointer or raw row",
    )


def check(root: Path) -> None:
    native = root / "ck3_autonomous_player" / "native_bridge"
    research = native / "research"
    fixtures = research / "fixtures"

    abi = _load(research / "faction_targeting_row_probe_v1_abi.json")
    contract = _load(
        fixtures / "faction_targeting_row_probe_v1_source_contract.json"
    )
    ready = _load(fixtures / "faction_targeting_row_probe_v1_ready_fixture.json")
    known_empty = _load(
        fixtures / "faction_targeting_row_probe_v1_known_empty_fixture.json"
    )
    unavailable = _load(
        fixtures / "faction_targeting_row_probe_v1_unavailable_fixture.json"
    )
    observer_abi = _load(research / "faction_targeting_row_observer_v1_abi.json")
    observer_contract = _load(
        fixtures / "faction_targeting_row_observer_v1_source_contract.json"
    )
    observer_fixture = _load(
        fixtures / "faction_targeting_row_observer_v1_capture_fixture.json"
    )

    header = (native / contract["implementation"]["header"]).read_text(
        encoding="utf-8"
    )
    source = (native / contract["implementation"]["source"]).read_text(
        encoding="utf-8"
    )
    serializer_header = (
        native / contract["implementation"]["serializer_header"]
    ).read_text(encoding="utf-8")
    serializer_source = (
        native / contract["implementation"]["serializer_source"]
    ).read_text(encoding="utf-8")
    test = (native / contract["implementation"]["test"]).read_text(
        encoding="utf-8"
    )
    observer_source = (
        native / "src/faction_targeting_row_observer_v1.cpp"
    ).read_text(encoding="utf-8")
    docs = (root / "docs/ck3-native-ai/factions-and-rebellions.md").read_text(
        encoding="utf-8"
    )

    _require(abi["schema_version"] == 1, "probe ABI schema drifted")
    _require(contract["schema_version"] == 1, "source contract schema drifted")
    _require(
        abi["status"] == contract["status"] == EXPECTED_STATUS,
        "probe static readiness status drifted",
    )
    for item in (abi, contract):
        exact_build = item.get("exact_build") or item.get("game_build")
        _require(
            exact_build["product_version"] == EXPECTED_BUILD
            and exact_build["executable_sha256"] == EXPECTED_SHA256,
            "probe exact-build identity drifted",
        )
        _require(
            item["unique_next_reverse_engineering_entry"] == EXPECTED_NEXT_SEAM,
            "probe next seam drifted",
        )

    _require(
        observer_abi["status"] == contract["upstream"]["required_status"]
        and observer_contract["status"] == contract["upstream"]["required_status"],
        "FACTION6 upstream status drifted",
    )
    for key in contract["upstream"]["required_private_readiness"]:
        _require(
            observer_abi["readiness"][key] is True,
            f"FACTION6 private readiness was demoted: {key}",
        )
    for key in contract["upstream"]["required_public_false"]:
        _require(
            observer_abi["readiness"][key] is False,
            f"FACTION6 live/public boundary was over-promoted: {key}",
        )
    _require(
        observer_fixture["capture"]["published_generation"] == 2
        and observer_fixture["capture"]["proof_epoch"] == 42
        and observer_fixture["capture"]["snapshot_revision"] == 412
        and observer_fixture["capture"]["date_raw"] == 777
        and observer_fixture["capture"]["player_character_id"] == 29829,
        "FACTION6 fixture join input drifted",
    )

    _check_tokens(header, contract["required_header_tokens"], "probe header")
    _check_tokens(source, contract["required_implementation_tokens"], "probe source")
    _check_tokens(
        observer_source,
        contract["required_upstream_snapshot_tokens"],
        "observer transactional snapshot",
    )
    _check_tokens(
        serializer_header,
        ["SerializeFactionTargetingRowProbeV1"],
        "probe serializer header",
    )
    _check_cpp_string_tokens(
        serializer_source,
        contract["required_serializer_tokens"],
        "probe serializer",
    )
    _check_cpp_string_tokens(test, contract["required_test_tokens"], "probe test")

    _require(
        abi["binding"]["paused_required"] is True
        and abi["binding"]["exact_match_fields"]
        == ["proof_epoch", "snapshot_revision", "date_raw", "player_character_id"]
        and abi["binding"]["generation"]["nonzero_required"] is True
        and abi["binding"]["generation"]["even_required"] is True,
        "paused/four-key/stable-even binding contract drifted",
    )
    _require(
        abi["terminal_contract"]["all_rows_or_unavailable"] is True
        and abi["terminal_contract"]["legal_empty_is_not_unavailable"] is True,
        "terminal completeness contract drifted",
    )
    _require(
        abi["capture_shape"]["member_ids_nonzero_sorted_unique"] is True
        and abi["capture_shape"]["member_count_bounded"] is True
        and abi["capture_shape"]["no_partial_rows_on_unavailable"] is True,
        "member identity/completeness shape contract drifted",
    )
    _require(
        abi["observer_failure_passthrough"]["typed"] is True
        and abi["observer_failure_passthrough"]["nonzero_forces_unavailable"]
        is True,
        "observer failure passthrough drifted",
    )

    readiness = abi["readiness"]
    _require(
        readiness["private_probe_core_ready"] is True
        and readiness["private_serializer_ready"] is True
        and readiness["deterministic_terminal_fixtures_ready"] is True,
        "private probe static readiness drifted",
    )
    for key in (
        "paused_live_artifact_ready",
        "shared_bridge_wiring_ready",
        "heartbeat_private_probe_ready",
        "public_targeting_rows_ready",
        "public_mcp_ready",
        "public_schema_ready",
    ):
        _require(readiness[key] is False, f"probe boundary over-promoted: {key}")
    for key in (
        "public_abi_changed",
        "public_capability_changed",
        "heartbeat_payload_changed",
        "public_schema_changed",
        "ck3_started",
    ):
        _require(abi["scope"][key] is False, f"scope boundary drifted: {key}")
    for key in (
        "raw_pointer_fields_persisted",
        "raw_pointer_hashes_persisted",
        "raw_row_bytes_persisted",
        "raw_member_row_bytes_persisted",
    ):
        _require(
            abi["pointer_boundary"][key] is False,
            f"ABI pointer boundary drifted: {key}",
        )
    _require(
        abi["pointer_boundary"]["owned_scalar_identities_only"] is True,
        "ABI owned scalar identity boundary drifted",
    )

    _check_fixture_common(ready, "ready")
    _check_fixture_common(known_empty, "known_empty")
    _check_fixture_common(unavailable, "upstream_observer_failure")

    expected_rows = [
        {
            "faction_id": 7,
            "target_character_id": 29829,
            "leader_character_id": None,
            "leader_present_in_character_members": False,
            "character_member_ids": [],
        },
        {
            "faction_id": 42,
            "target_character_id": 29829,
            "leader_character_id": 4001,
            "leader_present_in_character_members": True,
            "character_member_ids": [4001, 4002],
        },
    ]
    _require(
        ready["source_diagnostics"]["factions"] == expected_rows
        and ready["expected_result"]["factions"] == expected_rows
        and ready["expected_result"]["terminal_token"] == "ready"
        and ready["expected_result"]["wire_terminal"] == "ready"
        and ready["expected_result"]["faction_count"] == 2
        and ready["expected_result"]["unavailable_reasons"] == 0,
        "ready fixture drifted",
    )
    _require(
        known_empty["source_diagnostics"]["campaign_root_targeting_faction_count"]
        == 0
        and known_empty["source_diagnostics"]["faction_count"] == 0
        and known_empty["expected_result"]["terminal_token"] == "known_empty"
        and known_empty["expected_result"]["wire_terminal"] == "known-empty"
        and known_empty["expected_result"]["factions"] == []
        and known_empty["known_empty_is_observed_zero"] is True,
        "known-empty fixture drifted",
    )
    _require(
        unavailable["source_diagnostics"]["failure_flags"] == 786432
        and unavailable["expected_result"]["terminal_token"] == "unavailable"
        and unavailable["expected_result"]["wire_terminal"] == "unavailable"
        and unavailable["expected_result"]["unavailable_reasons"] == 2
        and unavailable["expected_result"]["observer_failure_flags"] == 786432
        and unavailable["expected_result"]["faction_count"] == 0
        and unavailable["expected_result"]["factions"] == []
        and unavailable["partial_rows_suppressed"] is True,
        "typed unavailable fixture drifted",
    )

    for fixture in (ready, known_empty, unavailable):
        expected = fixture["expected_result"]
        _require(
            expected["required_binding"] == fixture["required_binding"],
            f"{fixture['case']} required binding output drifted",
        )
        _require(
            expected["observed_binding"]["paused"] is True
            and expected["published_generation"] > 0
            and expected["published_generation"] % 2 == 0,
            f"{fixture['case']} observed stable-even binding drifted",
        )

    _require(
        "### FACTION7-PROBE:" in docs
        and EXPECTED_STATUS in docs
        and EXPECTED_NEXT_SEAM in docs,
        "FACTION7 documentation increment is missing",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[3]
    )
    arguments = parser.parse_args()
    check(arguments.root.resolve())
    print("faction-targeting-row-probe-source-contract: GREEN_STATIC")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
