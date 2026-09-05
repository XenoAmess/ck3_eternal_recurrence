"""Typed private capture contract for Raiktor source-created war armies.

The input is the existing standalone, default-OFF `spawn_army` breakpoint
artifact.  Normalization proves only the six-execution source-origin shape and
measured creation-time soldiers.  A later same-lifecycle current/postwar join
is still required before publishing a source-specific loss.
"""

from __future__ import annotations

import hashlib
import json
import re


CONTRACT = "raiktor-source-specific-war-loss-attribution-provider-v1"
CAPTURE_SCHEMA = "raiktor-war-bound-private-capture-v1"
EXPECTED_EXE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
EXPECTED_ARM_SHA256 = (
    "B7DC28B0B9EDB0F8A03E5DB2F03AD6CA1E3B649648BAE161B6A487063735B9B8"
)
EXPECTED_STOP_RVA = "0x2e7f951"
EXPECTED_WINDOW_END_RVA = "0x2e7f9a6"
EXPECTED_EVENT = "bookmark.1071"
EXPECTED_OPTION = "bookmark.1071.a"
EXPECTED_EXECUTIONS = 6
_SHA256_RE = re.compile(r"^[0-9A-F]{64}$")


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


def normalize_raiktor_source_specific_capture(
    value: object, *, capture_sha256: str
) -> dict[str, object]:
    capture = _dict(value, "capture")
    capture_hash = _sha256(capture_sha256, "capture_sha256")
    if (
        capture.get("schema") != CAPTURE_SCHEMA
        or capture.get("status") != "private_test_only"
        or capture.get("result") != "GREEN"
        or capture.get("reason")
        != "six-action-bound-source-executions-captured"
        or capture.get("read_only") is not True
        or capture.get("public_bridge_abi_changed") is not False
        or capture.get("production_detour_installed") is not False
        or capture.get("readiness_promotion") is not False
        or capture.get("exe_sha256") != EXPECTED_EXE_SHA256
        or _hex(capture.get("observation_stop_rva"), "stop_rva")
        != EXPECTED_STOP_RVA
        or _hex(capture.get("observation_window_end_rva_exclusive"), "window_end")
        != EXPECTED_WINDOW_END_RVA
        or capture.get("arm_proof_sha256") != EXPECTED_ARM_SHA256
        or capture.get("event_definition_key") != EXPECTED_EVENT
        or capture.get("option_key") != EXPECTED_OPTION
        or capture.get("option_index") != 0
        or capture.get("source_execution_count") != EXPECTED_EXECUTIONS
        or capture.get("breakpoint_installed") is not True
        or capture.get("original_breakpoint_byte_restored") is not True
        or capture.get("attach_mode") is not True
        or capture.get("debugger_detached") is not True
        or capture.get("process_terminated") is not False
    ):
        raise ValueError("private source capture boundary drifted")

    pid = _positive_int(capture.get("pid"), "pid")
    image_base = _hex(capture.get("image_base"), "image_base")
    war_id = _full_id(capture.get("exact_raiktor_war_id"), "war_id")
    rows = capture.get("executions")
    if not isinstance(rows, list) or len(rows) != EXPECTED_EXECUTIONS:
        raise ValueError("source executions must contain exactly six rows")

    loaded_nodes: set[str] = set()
    army_ids: set[int] = set()
    current_ids: set[int] = set()
    persistent_ids: set[int] = set()
    normalized_rows: list[dict[str, object]] = []
    measured_total = 0
    for index, row_value in enumerate(rows, start=1):
        row = _dict(row_value, f"executions[{index - 1}]")
        sequence = _positive_int(row.get("sequence"), "sequence")
        if sequence != index:
            raise ValueError("source execution sequence drifted")
        loaded_node = _hex(row.get("loaded_node"), "loaded_node")
        created_army = _hex(row.get("created_army"), "created_army")
        army_id = _full_id(row.get("army_generation_id"), "army_generation_id")
        if (
            row.get("war_id") != war_id
            or row.get("evaluated_name") != "norman_highwaymen"
            or loaded_node in loaded_nodes
            or army_id in army_ids
        ):
            raise ValueError("source execution identity drifted")
        loaded_nodes.add(loaded_node)
        army_ids.add(army_id)

        current_rows = row.get("current_regiments")
        persistent_rows = row.get("persistent_regiments")
        if (
            not isinstance(current_rows, list)
            or not current_rows
            or not isinstance(persistent_rows, list)
            or not persistent_rows
        ):
            raise ValueError("source generation rows must be nonempty")
        normalized_current: list[dict[str, int]] = []
        execution_current_ids: set[int] = set()
        execution_soldiers = 0
        for current_value in current_rows:
            current = _dict(current_value, "current_regiment")
            current_id = _full_id(current.get("generation_id"), "current_id")
            soldiers = _nonnegative_int(
                current.get("current_soldiers"), "current_soldiers"
            )
            if current_id in current_ids:
                raise ValueError("current generation is duplicated")
            current_ids.add(current_id)
            execution_current_ids.add(current_id)
            execution_soldiers += soldiers
            normalized_current.append(
                {"generation_id": current_id, "current_soldiers": soldiers}
            )
        initial_soldiers = _nonnegative_int(
            row.get("initial_soldiers"), "initial_soldiers"
        )
        if execution_soldiers != initial_soldiers:
            raise ValueError("execution soldier aggregate drifted")

        normalized_persistent: list[dict[str, object]] = []
        mapped_current_ids: set[int] = set()
        for persistent_value in persistent_rows:
            persistent = _dict(persistent_value, "persistent_regiment")
            persistent_id = _full_id(
                persistent.get("generation_id"), "persistent_id"
            )
            if persistent_id in persistent_ids or persistent.get("war_id") != war_id:
                raise ValueError("persistent generation identity drifted")
            persistent_ids.add(persistent_id)
            mapped = persistent.get("current_regiment_ids")
            if not isinstance(mapped, list) or not mapped:
                raise ValueError("persistent current mapping must be nonempty")
            mapped_ids = [_full_id(item, "mapped current_id") for item in mapped]
            if len(mapped_ids) != len(set(mapped_ids)):
                raise ValueError("persistent current mapping contains duplicates")
            if mapped_current_ids.intersection(mapped_ids):
                raise ValueError("current generation maps to multiple persistent rows")
            mapped_current_ids.update(mapped_ids)
            normalized_persistent.append(
                {
                    "generation_id": persistent_id,
                    "war_id": war_id,
                    "current_regiment_ids": mapped_ids,
                }
            )
        if mapped_current_ids != execution_current_ids:
            raise ValueError("persistent/current generation mapping drifted")
        measured_total += initial_soldiers
        normalized_rows.append(
            {
                "sequence": sequence,
                "thread_id": _positive_int(row.get("thread_id"), "thread_id"),
                "loaded_node": loaded_node,
                "created_army": created_army,
                "army_generation_id": army_id,
                "war_id": war_id,
                "initial_soldiers": initial_soldiers,
                "evaluated_name": "norman_highwaymen",
                "current_regiments": normalized_current,
                "persistent_regiments": normalized_persistent,
            }
        )

    source_set = {
        "war_id": war_id,
        "executions": normalized_rows,
        "persistent_generation_ids": sorted(persistent_ids),
        "current_generation_ids": sorted(current_ids),
        "army_generation_ids": sorted(army_ids),
        "measured_initial_soldiers": measured_total,
    }
    return {
        "schema_version": 1,
        "contract": CONTRACT,
        "status": "normalized_private_capture",
        "capture_sha256": capture_hash,
        "exact_build_sha256": EXPECTED_EXE_SHA256,
        "capture_pid": pid,
        "image_base": image_base,
        "source_set_sha256": canonical_sha256(source_set),
        "source_set": source_set,
        "readiness": {
            "exact_callsite_shape_ready": True,
            "action_arm_bound": True,
            "six_source_executions_ready": True,
            "source_origin_shape_ready": True,
            "measured_initial_soldiers_ready": True,
            "private_live_evidence_classified": False,
            "action_bound_current_ready": False,
            "postwar_cleanup_ready": False,
            "source_specific_loss_ready": False,
            "comparison_input_ready": False,
        },
        "boundaries": {
            "evaluated_name_is_standalone_selector": False,
            "authored_3000_used": False,
            "generic_r3_rows_retroactively_attributed": False,
            "public_readiness_promoted": False,
            "action_readiness_promoted": False,
            "decision_ready": False,
            "automatic_surrender_ready": False,
            "gen034_closed": False,
        },
    }


def _dict(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _sha256(value: object, name: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{name} must be an uppercase SHA-256")
    return value


def _hex(value: object, name: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"0x[0-9A-Fa-f]+", value) is None:
        raise ValueError(f"{name} must be a hexadecimal address")
    parsed = int(value, 16)
    if parsed <= 0 or parsed > 2**64 - 1:
        raise ValueError(f"{name} is outside positive uint64")
    return f"0x{parsed:x}"


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _nonnegative_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def _full_id(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 0
        or value > 2**31 - 1
    ):
        raise ValueError(f"{name} must be a nonnegative full-generation ID")
    return value


__all__ = [
    "CAPTURE_SCHEMA",
    "CONTRACT",
    "EXPECTED_ARM_SHA256",
    "EXPECTED_EXE_SHA256",
    "canonical_sha256",
    "normalize_raiktor_source_specific_capture",
]
