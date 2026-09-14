#!/usr/bin/env python3
"""Verify the private player-lifestyle snapshot source/fixture contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"RED: {message}")


def _load_json(path: Path) -> dict[str, Any]:
    _require(path.is_file(), f"missing JSON file: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"RED: cannot parse {path}: {exc}") from exc
    _require(isinstance(value, dict), f"JSON root is not an object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _verify_fixture_semantics(normal: dict[str, Any], no_focus: dict[str, Any]) -> None:
    _require(normal.get("status") == "available", "normal fixture is unavailable")
    _require(normal.get("current_focus", {}).get("presence") == "present", "normal focus is not present")
    _require(normal.get("current_lifestyle_progress", {}).get("presence") == "present", "normal progress is not present")
    _require(normal.get("owned_perk_keys") == sorted(normal.get("owned_perk_keys", [])), "normal perks are not canonical")
    _require(normal.get("legal_focus_candidates", {}).get("status") == "available", "normal focus candidates are unavailable")
    _require(len(normal.get("legal_focus_candidates", {}).get("items", [])) > 0, "normal focus candidate list is empty")
    _require(normal.get("legal_perk_candidates", {}).get("status") == "available", "normal perk candidates are unavailable")
    _require(len(normal.get("legal_perk_candidates", {}).get("items", [])) > 0, "normal perk candidate list is empty")
    _require(all(normal.get("readiness", {}).values()), "normal fixture readiness is incomplete")

    _require(no_focus.get("status") == "available", "no-focus fixture is unavailable")
    _require(no_focus.get("current_focus") == {"presence": "absent"}, "no-focus fixture does not encode known absence")
    _require(no_focus.get("current_lifestyle_progress") == {"presence": "absent"}, "no-focus progress does not encode known absence")
    _require(no_focus.get("owned_perk_keys") == [], "known-empty owned perks are not []")
    _require(no_focus.get("legal_perk_candidates") == {"status": "available", "items": []}, "known-empty legal perks are not available []")
    _require(all(no_focus.get("readiness", {}).values()), "no-focus fixture readiness is incomplete")


def _verify_source_contract(native_root: Path, contract: dict[str, Any]) -> None:
    files = contract.get("files", {})
    header = (native_root / files.get("header", "")).read_text(encoding="utf-8")
    implementation = (native_root / files.get("implementation", "")).read_text(encoding="utf-8")
    unit_test = (native_root / files.get("unit_test", "")).read_text(encoding="utf-8")
    for token in contract.get("required_header_tokens", []):
        _require(token in header, f"header token missing: {token}")
    for token in contract.get("required_implementation_tokens", []):
        _require(token in implementation, f"implementation token missing: {token}")
    for token in contract.get("required_test_tokens", []):
        _require(token in unit_test, f"unit-test token missing: {token}")


def _verify_abi(abi: dict[str, Any]) -> None:
    _require(abi.get("private_key") == "g2_player_lifestyle_snapshot_v1", "wrong private key")
    _require(abi.get("status") == "static-ready-private-core-unwired", "wrong implementation status")
    exact = abi.get("exact_build", {})
    _require(exact.get("product_version") == "1.19.0.6", "wrong product version")
    _require(exact.get("executable_sha256") == EXE_SHA256, "wrong executable hash in ABI")
    readiness = abi.get("readiness", {})
    for key in (
        "private_core_implemented",
        "current_focus_native_path",
        "current_lifestyle_progress_native_path",
        "owned_perks_native_path",
        "stable_key_parser",
        "same_frame_double_sample",
    ):
        _require(readiness.get(key) is True, f"expected ready field is false: {key}")
    for key in (
        "legal_focus_candidates_native_path",
        "legal_perk_candidates_native_path",
        "native_binding_registered",
        "public_capability_registered",
        "production_query_live",
        "planner_ready",
    ):
        _require(readiness.get(key) is False, f"unearned readiness is true: {key}")
    boundary = abi.get("candidate_boundary", {})
    _require(boundary.get("production_status") == "unavailable", "candidate boundary is not unavailable")
    _require(boundary.get("reason") == "lifestyle_window_unavailable", "candidate boundary reason changed")


def _verify_exact_build(abi: dict[str, Any], exe: Path, game_root: Path) -> None:
    exact = abi["exact_build"]
    _require(exe.is_file(), f"exact-build executable missing: {exe}")
    _require(exe.stat().st_size == exact["executable_size"], "exact-build executable size mismatch")
    _require(_sha256(exe) == exact["executable_sha256"], "exact-build executable hash mismatch")
    for evidence in abi.get("source_evidence", []):
        path = game_root / Path(evidence["path"])
        _require(path.is_file(), f"exact-build source missing: {path}")
        _require(path.stat().st_size == evidence["size"], f"source size mismatch: {evidence['path']}")
        _require(_sha256(path) == evidence["sha256"], f"source hash mismatch: {evidence['path']}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--native-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--exe", type=Path)
    parser.add_argument("--game-root", type=Path)
    args = parser.parse_args()
    _require((args.exe is None) == (args.game_root is None), "--exe and --game-root must be supplied together")

    native_root = args.native_root.resolve()
    research = native_root / "research"
    contract = _load_json(research / "fixtures/player_lifestyle_snapshot_v1_source_contract.json")
    abi = _load_json(research / "player_lifestyle_snapshot_v1_abi.json")
    normal = _load_json(research / "fixtures/player_lifestyle_snapshot_v1_normal.json")
    no_focus = _load_json(research / "fixtures/player_lifestyle_snapshot_v1_no_focus.json")
    _verify_source_contract(native_root, contract)
    _verify_abi(abi)
    _verify_fixture_semantics(normal, no_focus)
    if args.exe is not None and args.game_root is not None:
        _verify_exact_build(abi, args.exe.resolve(), args.game_root.resolve())
    print("GREEN: player-lifestyle-snapshot-v1 source/fixture contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
