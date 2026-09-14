#!/usr/bin/env python3
"""Verify COUNCIL6's private steward-candidate reader source contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXPECTED_EXE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
PRIVATE_KEY = "g2_council_composition_steward_candidates_reader_v1"
PUBLIC_CAPABILITY = "game.query.council-composition-candidates-v1"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _unsigned_id(value: int) -> int:
    return value & 0xFFFFFFFF


def check(root: Path) -> None:
    native = root / "ck3_autonomous_player/native_bridge"
    research = native / "research"
    source_contract = _load(
        research
        / "fixtures/council_composition_steward_candidates_reader_v1_source_contract.json"
    )
    abi = _load(
        research / "council_composition_steward_candidates_reader_v1_abi.json"
    )
    fixture = _load(
        research
        / "fixtures/council_composition_steward_candidates_reader_v1_fixture.json"
    )
    live = _load(
        research
        / "fixtures/council_composition_steward_r684_live_capture_v1.json"
    )

    files = source_contract["files"]
    header = (native / files["header"]).read_text(encoding="utf-8")
    implementation = (native / files["implementation"]).read_text(
        encoding="utf-8"
    )
    unit_test = (native / files["unit_test"]).read_text(encoding="utf-8")
    doc = (root / "docs/ck3-native-ai/council-composition-ai.md").read_text(
        encoding="utf-8"
    )

    _require(source_contract["schema_version"] == 1, "source schema drifted")
    _require(source_contract["private_key"] == PRIVATE_KEY, "private key drifted")
    for token in source_contract["required_header_tokens"]:
        _require(token in header, f"missing header token: {token}")
    for token in source_contract["required_implementation_tokens"]:
        _require(token in implementation, f"missing implementation token: {token}")
    for token in source_contract["required_test_tokens"]:
        _require(token in unit_test, f"missing unit-test token: {token}")
    _require(PUBLIC_CAPABILITY not in header, "header advertises public capability")
    _require(
        PUBLIC_CAPABILITY not in implementation,
        "implementation advertises public capability",
    )

    producer_at = implementation.index("access.produce(")
    release_at = implementation.index("access.release(access.context, vector)")
    after_frame_at = implementation.index("Frame after{}")
    publish_at = implementation.index("Publish(before")
    _require(
        producer_at < release_at < after_frame_at < publish_at,
        "producer/copy-release/after-frame/publish order drifted",
    )
    _require(
        implementation.count("access.release(access.context, vector)") == 1,
        "core must have one release site for every producer invocation",
    )

    _require(abi["schema_version"] == 1, "ABI schema drifted")
    _require(abi["private_key"] == PRIVATE_KEY, "ABI private key drifted")
    _require(
        abi["status"] == "static-ready-private-core-unbound",
        "private readiness drifted",
    )
    _require(
        abi["exact_build"]["executable_sha256"] == EXPECTED_EXE_SHA256,
        "ABI executable identity drifted",
    )
    _require(
        abi["coverage"]["position_keys"] == ["councillor_steward"],
        "reader coverage expanded beyond evidence",
    )
    _require(
        abi["native_seam"]["producer_rva"] == "0x293BD00"
        and abi["native_seam"]["gui_eligibility_mode"] is True
        and abi["native_seam"]["row_stride_bytes"] == 8
        and abi["native_seam"]["maximum_published_rows"] == 64,
        "native seam drifted",
    )
    readiness = abi["readiness"]
    _require(readiness["private_core_implemented"] is True, "core not ready")
    _require(
        readiness["native_binding_registered"] is False
        and readiness["public_capability_registered"] is False
        and readiness["production_query_live"] is False
        and readiness["planner_ready"] is False,
        "static core was promoted beyond evidence",
    )
    _require(
        abi["forbidden_public_capability"] == PUBLIC_CAPABILITY,
        "public capability boundary drifted",
    )

    _require(fixture["schema_version"] == 1, "fixture schema drifted")
    _require(fixture["offline_fixture"] is True, "fixture claims live execution")
    _require(
        fixture["exact_build"]["executable_sha256"] == EXPECTED_EXE_SHA256,
        "fixture executable identity drifted",
    )
    live_rows = live["candidate_vector"]["rows"]
    live_ids = [row["character_id"] for row in live_rows]
    _require(
        fixture["input"]["native_character_ids"] == live_ids,
        "reader fixture no longer projects the R684 identities",
    )
    _require(
        fixture["input"]["native_count"] == len(live_ids) == 11,
        "R684 fixture count drifted",
    )
    _require(
        fixture["input"]["owner_identity_round_trip"] is True
        and fixture["input"]["active_task_identity_round_trip"] is True
        and fixture["input"]["candidate_identity_round_trip"] is True,
        "full-generation identity round-trip boundary drifted",
    )
    expected_rows = fixture["expected_available_output"]["candidates"]
    expected_ids = [row["character_id"] for row in expected_rows]
    _require(
        expected_ids == sorted(live_ids, key=_unsigned_id),
        "published candidate order is not unsigned full-CharacterID order",
    )
    live_ordinal_by_id = {
        row["character_id"]: row["native_collection_ordinal"]
        for row in live_rows
    }
    _require(
        all(
            row["native_collection_ordinal"]
            == live_ordinal_by_id[row["character_id"]]
            for row in expected_rows
        ),
        "native ordinals no longer round-trip",
    )
    _require(
        fixture["expected_available_output"]["temporary_vector_released"]
        is True,
        "success fixture omitted vector release",
    )
    _require(
        fixture["failure_contract"]
        == {
            "post_producer_failures_release_once": True,
            "unavailable_candidate_count": 0,
            "partial_rows_published": False,
        },
        "failure atomicity drifted",
    )
    _require(
        fixture["public_abi_changed"] is False
        and fixture["public_readiness_changed"] is False,
        "fixture changed public readiness",
    )

    for token in (
        "COUNCIL6",
        PRIVATE_KEY,
        "static-ready private core",
        "同一 transaction",
        "生产绑定尚未注册",
        "planner-ready 仍为 false",
    ):
        _require(token in doc, f"documentation missing COUNCIL6 token: {token}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[3]
    )
    args = parser.parse_args()
    check(args.root.resolve())
    print("council-composition-steward-reader-source-contract: GREEN_STATIC")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
