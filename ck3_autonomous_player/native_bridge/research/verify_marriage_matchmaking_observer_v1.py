#!/usr/bin/env python3
"""Verify the private marriage matchmaking observer source contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"RED: {message}")


def _load(path: Path) -> dict[str, Any]:
    _require(path.is_file(), f"missing JSON file: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"RED: cannot parse {path}: {exc}") from exc
    _require(isinstance(value, dict), f"JSON root is not an object: {path}")
    return value


def _verify_source(native_root: Path, contract: dict[str, Any]) -> None:
    files = contract.get("files", {})
    header = (native_root / files.get("header", "")).read_text(encoding="utf-8")
    implementation = (native_root / files.get("implementation", "")).read_text(
        encoding="utf-8"
    )
    unit_test = (native_root / files.get("unit_test", "")).read_text(
        encoding="utf-8"
    )
    for token in contract.get("required_header_tokens", []):
        _require(token in header, f"header token missing: {token}")
    for token in contract.get("required_implementation_tokens", []):
        _require(token in implementation, f"implementation token missing: {token}")
    for token in contract.get("required_test_tokens", []):
        _require(token in unit_test, f"unit-test token missing: {token}")

    private_source = "\n".join((header, implementation, unit_test))
    for capability in contract.get("forbidden_public_capabilities", []):
        _require(capability not in private_source, f"public capability leaked: {capability}")


def _verify_abi(abi: dict[str, Any]) -> None:
    _require(
        abi.get("private_key") == "marriage_matchmaking_observer_v1",
        "wrong private key",
    )
    _require(
        abi.get("status") == "static-ready-private-core-unwired",
        "wrong private-core status",
    )
    _require(abi.get("visibility") == "private-not-advertised", "observer is public")
    exact = abi.get("exact_build", {})
    _require(exact.get("product_version") == "1.19.0.6", "wrong game version")
    _require(exact.get("executable_sha256") == EXE_SHA256, "wrong executable hash")

    row = abi.get("ranked_row_layout", {})
    _require(row.get("stride_bytes") == 16, "ranked row stride drifted")
    _require(row.get("candidate_character_id_offset") == 8, "candidate ID offset drifted")
    _require(row.get("native_candidate_score_offset") == 12, "score offset drifted")
    _require(row.get("maximum_rows") == 8, "candidate limit drifted")

    readiness = abi.get("readiness", {})
    for key in (
        "private_core_implemented",
        "exact_build_entry_points_bound",
        "ranked_candidate_contract",
        "pair_character_id_contract",
        "native_score_contract",
        "complete_can_send_contract",
        "recipient_ai_accept_contract",
        "recipient_answer_contract",
        "predicted_outcome_contract",
        "same_frame_double_sample",
    ):
        _require(readiness.get(key) is True, f"expected ready field is false: {key}")
    for key in (
        "native_strategy_adapter_bound",
        "native_pair_context_adapter_bound",
        "public_capability_registered",
        "production_query_live",
        "relationship_postcondition_ready",
        "alliance_pair_postcondition_ready",
        "planner_ready",
    ):
        _require(readiness.get(key) is False, f"unearned readiness is true: {key}")

    religion = abi.get("religion_boundary", {})
    _require(
        religion.get("projection") == "native final results only",
        "religion projection expanded",
    )
    _require(
        "Python reimplementation of religious marriage legality"
        in religion.get("forbidden", []),
        "religion implementation boundary missing",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--native-root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    args = parser.parse_args()
    native_root = args.native_root.resolve()
    research = native_root / "research"
    contract = _load(
        research / "fixtures/marriage_matchmaking_observer_v1_source_contract.json"
    )
    abi = _load(research / "marriage_matchmaking_observer_v1_abi.json")
    _verify_source(native_root, contract)
    _verify_abi(abi)
    print("GREEN: marriage-matchmaking-observer-v1 source contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
