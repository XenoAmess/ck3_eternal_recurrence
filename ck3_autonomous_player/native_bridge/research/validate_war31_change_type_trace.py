#!/usr/bin/env python3
"""Validate a future War31 setup/resolve change-type trace without launching CK3.

This checks structure and source-supplied identity, not capture authenticity,
action authorization, or any persisted surrender terms.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
REQUEST_ID = "WAR-INPUT-R0221-WAR31-20260927"
WAR_ID = 16777231
EPISODE_RUN_ID = "native-29829-2bc2d599f7f9"
SCHEMA = "xar.ck3.war31.change_type_two_point_trace.v1"
SITES = (
    ("0x2E9F746", "488BF0", "setup_change_scope_resolved"),
    ("0x2EC4410", "83B86802000017", "resolve_type_comparison"),
)
SAME_ACTION_FIELDS = (
    "process_instance_id", "thread_id", "action_attempt_id", "effect_invocation_id",
    "frame_token", "war_id", "episode_run_id", "date_raw", "checkpoint_sha256",
    "bridge_dll_sha256", "raw_capture_sha256",
)


def _hash(value: object, field: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9A-Fa-f]{64}", value) is None:
        raise ValueError(f"{field} must be a 64-digit SHA-256 hex string")
    return value.upper()


def _pointer(value: object, field: str) -> int:
    if not isinstance(value, str) or re.fullmatch(r"0x[0-9A-Fa-f]{1,16}", value) is None:
        raise ValueError(f"{field} must be a nonzero 64-bit hex pointer")
    pointer = int(value, 16)
    if pointer == 0 or pointer % 8:
        raise ValueError(f"{field} must be a nonzero eight-byte-aligned pointer")
    return pointer


def _positive_int(value: object, field: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{field} must be a positive integer")
    return value


def validate(payload: dict[str, object]) -> dict[str, object]:
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        raise ValueError("wrong War31 two-point trace schema")
    if payload.get("request_id") != REQUEST_ID:
        raise ValueError("wrong War31 request identity")
    if _hash(payload.get("ck3_exe_sha256"), "ck3_exe_sha256") != EXE_SHA256:
        raise ValueError("wrong exact CK3 executable")
    samples = payload.get("samples")
    if not isinstance(samples, list) or len(samples) != 2:
        raise ValueError("exactly two ordered setup/resolve samples are required")
    for ordinal, (sample, (rva, opcode, phase)) in enumerate(zip(samples, SITES), start=1):
        if not isinstance(sample, dict):
            raise ValueError(f"sample {ordinal} must be an object")
        if (sample.get("site_rva"), sample.get("instruction_bytes"),
                sample.get("site_phase")) != (rva, opcode, phase):
            raise ValueError(f"sample {ordinal} has the wrong exact pre-instruction site")
        if sample.get("capture_timing") != "before_instruction":
            raise ValueError(f"sample {ordinal} must precede its site instruction")
        if sample.get("memory_read_status") != "ok":
            raise ValueError(f"sample {ordinal} lacks a successful memory read")
        if sample.get("war_id") != WAR_ID or sample.get("episode_run_id") != EPISODE_RUN_ID:
            raise ValueError(f"sample {ordinal} has the wrong War31 episode")
        for field in ("bridge_dll_sha256", "checkpoint_sha256", "raw_capture_sha256"):
            _hash(sample.get(field), f"sample {ordinal} {field}")
        for field in ("process_instance_id", "action_attempt_id", "effect_invocation_id", "frame_token"):
            if not isinstance(sample.get(field), str) or not sample[field].strip():
                raise ValueError(f"sample {ordinal} lacks {field}")
        for field in ("thread_id", "date_raw", "event_ordinal"):
            _positive_int(sample.get(field), f"sample {ordinal} {field}")
        _pointer(sample.get("rax_change_pointer"), f"sample {ordinal} rax_change_pointer")
        type_value = sample.get("change_type_dword")
        if type(type_value) is not int or not 0 <= type_value <= 0xFFFFFFFF:
            raise ValueError(f"sample {ordinal} change_type_dword must be an unsigned dword")
    first, second = samples
    for field in SAME_ACTION_FIELDS:
        if first[field] != second[field]:
            raise ValueError(f"cross-action or cross-frame pair: {field} differs")
    if first["event_ordinal"] >= second["event_ordinal"]:
        raise ValueError("resolve must follow setup in the same capture stream")
    if _pointer(first["rax_change_pointer"], "setup pointer") != _pointer(
        second["rax_change_pointer"], "resolve pointer"
    ):
        raise ValueError("setup and resolve reference different change objects")

    return {
        "schema": "xar.ck3.war31.change_type_two_point_validation.v1",
        "status": "STRUCTURAL_PAIR_ONLY",
        "request_id": REQUEST_ID,
        "war_id": WAR_ID,
        "episode_run_id": EPISODE_RUN_ID,
        "ck3_exe_sha256": EXE_SHA256,
        "bridge_dll_sha256": _hash(first["bridge_dll_sha256"], "bridge_dll_sha256"),
        "raw_capture_sha256": _hash(first["raw_capture_sha256"], "raw_capture_sha256"),
        "setup_type_dword": first["change_type_dword"],
        "resolve_type_dword": second["change_type_dword"],
        "resolve_cmp_equals_0x17": second["change_type_dword"] == 0x17,
        "source_capture_authenticity": "NOT_VERIFIED_BY_THIS_VALIDATOR",
        "actual_taken_branch": None,
        "persisted_surrender_terms": None,
        "ck3_launched_by_validator": False,
        "gameplay_action_submitted_by_validator": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path, help="Existing two-point capture JSON")
    args = parser.parse_args()
    print(json.dumps(validate(json.loads(args.trace.read_text(encoding="utf-8"))),
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
