"""Host consumers for public V2 exit receipts and completed process lifecycle.

These functions do not query a process or grant business/normal-Quit credit.
The host's original native-zero cleanup predicate remains the lifecycle authority.
"""
from __future__ import annotations

from typing import Literal, TypedDict

from .normal_exit_public_wire_v2 import (
    UINT64_MAX, parse_normal_exit_public_result_v2,
    parse_normal_exit_public_revision_v2, validate_normal_exit_public_revision_v2,
)

NORMAL_EXIT_REVISION_TOOLS = frozenset({
    "ck3_query_normal_exit_context_v1", "ck3_request_normal_exit_v1",
})


def normal_exit_revision_from_snapshot_v2(value: object) -> str:
    """Encode an exact Python snapshot revision without a numeric JSON roundtrip."""
    if type(value) is not int or not isinstance(value, int) or not 1 <= value <= UINT64_MAX:
        raise ValueError("normal-exit snapshot revision requires an exact positive uint64 integer")
    return validate_normal_exit_public_revision_v2(str(value))


def _object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict) or any(type(key) is not str for key in value):
        raise ValueError(label + " requires a string-keyed object")
    return {key: item for key, item in value.items()}


def terminal_normal_exit_result_v2(tool_name: object, arguments: object, result: object) -> bool:
    """Only validated terminal public receipts suppress an alive after-snapshot."""
    if tool_name not in ("ck3_request_normal_exit_v1", "ck3_observe_normal_exit_v1"):
        return False
    args = _object(arguments, "normal-exit tool arguments")
    if tool_name == "ck3_request_normal_exit_v1" and args.get("action") != "confirm_desktop":
        return False
    row = _object(result, "normal-exit terminal result")
    expected = ("ck3-normal-exit-request-result-v2" if tool_name == "ck3_request_normal_exit_v1"
                else "ck3-normal-exit-process-observation-result-v2")
    if row.get("schema") != expected:
        raise ValueError("host normal-exit terminal consumer requires the matching public V2 schema")
    parsed = parse_normal_exit_public_result_v2(row)
    if parsed.action != "confirm_desktop" or row.get("snapshot_after_required") is not False:
        raise ValueError("public normal-exit receipt does not allow an alive after-snapshot")
    if tool_name == "ck3_request_normal_exit_v1" and "expected_revision" in args:
        if parse_normal_exit_public_revision_v2(args["expected_revision"]) != parsed.public_revision:
            raise ValueError("normal-exit terminal receipt crossed its requested public revision")
    if tool_name == "ck3_observe_normal_exit_v1" and args:
        raise ValueError("normal-exit observation cannot select a caller process or handle")
    return True


class CompletedProcessFinalObservation(TypedDict):
    schema: Literal["ck3-host-terminal-final-observation-v1"]
    status: Literal["not_applicable"]
    reason: Literal["finished_native_process_exit_zero_cleanup_proven"]
    pid: int
    process_exit_code: Literal[0]
    failed_step_ids: list[str]
    host_error: str | None
    failure_preserved: bool
    alive_or_business_credit: Literal[False]
    business_pass: Literal[False]
    normal_close_qualified: Literal[False]


def completed_process_final_observation_v1(process_proof: object, *, host_error: object,
        step_rows: object) -> CompletedProcessFinalObservation:
    """Project failure-preserving metadata after the original proof has succeeded."""
    proof = _object(process_proof, "original completed native-process proof")
    pid = proof.get("pid")
    if (proof.get("status") != "not_applicable"
            or proof.get("reason") != "finished_native_process_exit_zero_cleanup_proven"
            or proof.get("managed_session_done") is not True
            or proof.get("alive_or_business_credit") is not False
            or type(pid) is not int or not isinstance(pid, int) or pid <= 0
            or type(proof.get("process_exit_code")) is not int
            or proof.get("process_exit_code") != 0):
        raise ValueError("original completed native-zero process proof required")
    if host_error is not None and (type(host_error) is not str or not host_error):
        raise ValueError("host error must retain a nonempty string or null")
    if not isinstance(step_rows, list):
        raise ValueError("original host step rows must be a list")
    failed: list[str] = []
    for value in step_rows:
        row = _object(value, "original host step row")
        identity = row.get("id")
        if type(identity) is not str or not isinstance(identity, str) or not identity or type(row.get("ok")) is not bool:
            raise ValueError("original host step identity and exact boolean outcome required")
        if row["ok"] is False:
            failed.append(identity)
    if not isinstance(pid, int) or (host_error is not None and not isinstance(host_error, str)):
        raise ValueError("validated terminal metadata type drift")
    return {"schema": "ck3-host-terminal-final-observation-v1", "status": "not_applicable",
        "reason": "finished_native_process_exit_zero_cleanup_proven", "pid": pid,
        "process_exit_code": 0, "failed_step_ids": failed, "host_error": host_error,
        "failure_preserved": bool(failed) or host_error is not None,
        "alive_or_business_credit": False, "business_pass": False, "normal_close_qualified": False}
