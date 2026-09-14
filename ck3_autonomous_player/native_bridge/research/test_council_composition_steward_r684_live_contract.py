#!/usr/bin/env python3
"""Verify the frozen R684 steward candidate capture and its next reader boundary."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


EXPECTED_EXE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
EXPECTED_CANDIDATE_COMMIT = "bb5911cedc7af70c43312d16a88c75ec50aac4f6"
EXPECTED_ARTIFACT_HASHES = {
    "candidate_manifest_sha256": "AEFA4B431F28AD23BA4B1C3D52444464DCF38FAC38922A962888963CE74E8191",
    "report_sha256": "9215C1FED4EF164C5F4272250BB412E047DE1223A03BA93C9A71A3CEB58F9B6F",
    "capture_sha256": "F19AA907292EA53EB3D2F69658F59A871D34B5960200FA5F0DE68FEC096F3CAB",
    "raw_rows_sha256": "328BB46BAA038A3021E0A94C802C0B8C3AF675B8B27C1A07E9244FD67B4EA50E",
    "post_trigger_screenshot_sha256": "14BFA16A57A99F2A700307DE1CD145678FC54C1C214E6D85828066D0F07E0458",
}
EXPECTED_CHARACTER_IDS = [
    30784,
    33437,
    33888,
    35637,
    57582,
    33435,
    34333,
    34867,
    32440,
    43706,
    33433,
]
PUBLIC_CAPABILITY = "game.query.council-composition-candidates-v1"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from _strings(key)
            yield from _strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _strings(child)


def check(root: Path) -> None:
    research = root / "ck3_autonomous_player/native_bridge/research"
    fixture = _load(
        research
        / "fixtures/council_composition_steward_r684_live_capture_v1.json"
    )
    abi = _load(research / "council_composition_candidate_observer_v1_abi.json")
    source_contract = _load(
        research
        / "fixtures/council_composition_candidate_observer_v1_source_contract.json"
    )
    doc = (root / "docs/ck3-native-ai/council-composition-ai.md").read_text(
        encoding="utf-8"
    )

    _require(fixture["schema_version"] == 1, "live fixture schema drifted")
    _require(
        fixture["status"]
        == "private-live-capture-green-production-reader-pending",
        "live readiness claim drifted",
    )
    exact = fixture["exact_build"]
    _require(exact["product_version"] == "1.19.0.6", "game version drifted")
    _require(
        exact["executable_sha256"] == EXPECTED_EXE_SHA256,
        "executable identity drifted",
    )
    _require(
        exact["candidate_source_commit"] == EXPECTED_CANDIDATE_COMMIT,
        "candidate source commit drifted",
    )
    seam = exact["observer_seam"]
    _require(
        seam
        == {
            "producer_call_rva": "0x105820A",
            "post_return_rva": "0x105820F",
            "producer_rva": "0x293BD00",
            "row_stride_bytes": 8,
        },
        "live seam projection drifted",
    )
    _require(
        abi["exact_build"]["executable_sha256"] == EXPECTED_EXE_SHA256,
        "observer ABI executable identity drifted",
    )
    _require(
        abi["seam"]["call_rva"] == seam["producer_call_rva"]
        and abi["seam"]["continue_rva"] == seam["post_return_rva"]
        and abi["seam"]["producer_rva"] == seam["producer_rva"],
        "live evidence no longer matches the frozen observer ABI",
    )
    _require(
        source_contract["forbidden_public_capability"] == PUBLIC_CAPABILITY,
        "private observer publication boundary drifted",
    )

    artifact = fixture["source_artifact"]
    _require(
        artifact["stem"]
        == "g2-m4-r684-council-composition-observer-live-bb5911c",
        "artifact stem drifted",
    )
    for key, expected in EXPECTED_ARTIFACT_HASHES.items():
        _require(artifact[key] == expected, f"artifact hash drifted: {key}")
        _require(bool(re.fullmatch(r"[0-9A-F]{64}", artifact[key])), key)

    binding = fixture["paused_binding"]
    observer = fixture["observer"]
    _require(binding["paused"] is True, "capture was not paused")
    _require(binding["episode_character_id"] == 29829, "episode identity drifted")
    _require(binding["owner_character_id"] == 29829, "owner identity drifted")
    _require(binding["active_task_id"] == 7159, "active task identity drifted")
    _require(
        binding["position_key"] == "councillor_steward",
        "captured position drifted",
    )
    _require(
        binding["ui_thread_id"] == binding["callback_thread_id"] != 0,
        "capture did not run on the observed UI thread",
    )
    _require(
        observer["private_build"] is True
        and observer["read_only"] is True
        and observer["advertised"] is False
        and observer["installed"] is True,
        "observer privacy/read-only contract drifted",
    )
    _require(
        observer["failure_flags"] == 0
        and observer["capture_failure_flags"] == 0,
        "R684 failure flags are nonzero",
    )
    _require(
        observer["capture_status"] == "captured"
        and observer["call_count"] == 1
        and observer["accepted_count"] == 1
        and observer["rejected_count"] == 0
        and observer["ignored_after_capture_count"] == 0
        and observer["consistent"] is True
        and observer["complete"] is True,
        "R684 bounded single-capture evidence drifted",
    )

    vector = fixture["candidate_vector"]
    rows = vector["rows"]
    _require(vector["count"] == 11, "candidate count drifted")
    _require(vector["captured_row_count"] == len(rows) == 11, "row count drifted")
    _require(vector["capacity"] >= vector["count"], "invalid vector span")
    _require(vector["duplicate_character_id_count"] == 0, "duplicate count drifted")
    _require(
        [row["native_collection_ordinal"] for row in rows] == list(range(11)),
        "native collection ordinals drifted",
    )
    ids = [row["character_id"] for row in rows]
    _require(ids == EXPECTED_CHARACTER_IDS, "captured full CharacterIDs drifted")
    _require(len(set(ids)) == len(ids), "captured CharacterIDs are not unique")

    raw_rows: list[bytes] = []
    for row in rows:
        raw = bytes.fromhex(row["raw_row_bytes_hex"])
        _require(len(raw) == seam["row_stride_bytes"], "row stride drifted")
        _require(
            hashlib.sha256(raw).hexdigest().upper() == row["raw_row_sha256"],
            "row SHA-256 drifted",
        )
        raw_rows.append(raw)
    raw_blob = b"".join(raw_rows)
    _require(len(raw_blob) == vector["raw_size"] == 88, "raw blob size drifted")
    _require(
        hashlib.sha256(raw_blob).hexdigest().upper() == vector["raw_sha256"]
        == EXPECTED_ARTIFACT_HASHES["raw_rows_sha256"],
        "raw blob SHA-256 drifted",
    )

    non_mutation = fixture["non_mutation"]
    _require(
        non_mutation
        == {
            "date_advance": False,
            "save_mutation": False,
            "council_action_submit": False,
            "source_save_unchanged": True,
            "target_save_unchanged": True,
            "cleanup_proven": True,
            "final_ck3_inventory_empty": True,
        },
        "R684 non-mutation or cleanup proof drifted",
    )

    next_contract = fixture["next_implementation_contract"]
    _require(
        next_contract["coverage_position_keys"] == ["councillor_steward"],
        "first reader coverage expanded without evidence",
    )
    _require(
        next_contract["execution"] == "application-main paused mailbox transaction",
        "reader execution boundary drifted",
    )
    _require(
        next_contract["public_capability_ready"] is False
        and next_contract["planner_ready"] is False,
        "private capture was promoted to public/planner readiness",
    )
    _require(
        "temporary producer output released in the same transaction"
        in next_contract["required_gates"],
        "temporary-vector lifetime gate missing",
    )
    _require(
        {"native pointers", "raw row bytes"}.issubset(
            set(next_contract["forbidden_output_fields"])
        ),
        "native row privacy boundary drifted",
    )
    _require(
        all(not value.startswith(("Z:\\", "C:\\", "/home/")) for value in _strings(fixture)),
        "committed fixture contains a machine-bound absolute path",
    )

    for token in (
        "R684",
        artifact["stem"],
        "11 个唯一",
        "private-live capture GREEN",
        "councillor_steward",
        "生产 reader",
        "仍未实现",
        "同一 transaction 内释放",
    ):
        _require(token in doc, f"documentation missing live boundary token: {token}")
    _require(
        "[static-confirmed / live probe pending]" not in doc,
        "documentation still labels the completed probe as pending",
    )
    _require(
        "当前唯一下一 probe" not in doc,
        "documentation still schedules the completed observer probe",
    )

    production_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for base in (
            root / "ck3_autonomous_player/src",
            root / "ck3_autonomous_player/native_bridge/src",
        )
        for path in base.rglob("*")
        if path.is_file()
        and path.suffix in {".py", ".cpp", ".hpp"}
        and "test" not in path.stem.lower()
    )
    _require(
        PUBLIC_CAPABILITY not in production_text,
        "private capture was accidentally advertised by production code",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[3]
    )
    args = parser.parse_args()
    check(args.root.resolve())
    print("council-composition-steward-r684-live-contract: GREEN_STATIC")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
