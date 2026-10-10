"""Actual4 record-release stage joined to an explicit numerical-stage prefix.

Current caller, direct body and selected canonical raw-buffer callback source
are closed. Existing count-driven kernels preserve unknown dynamic receivers.
The adapter returns a conditional postimage and executes no native writes.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from xar_autoplayer.bridge.army_daily_assault_normal_return_release_projection import (
    project_current_daily_assault_normal_return_release_v1,
)
from xar_autoplayer.bridge.army_daily_assault_queue_append_projection import (
    project_current_daily_assault_queue_append_v1,
)


EXECUTABLE_SHA256 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"
DIRECT_RELEASE_SHA256 = "d04dbf98b0753f1ebdd1ca022537661ad1967759e8965f61f33ae762c9d96ca9"
CONSUMER_RVA = "0x2A97EB0"
RELEASE_CALL_RVA = "0x2A981A9"
RELEASE_RVA = "0x9D11F0"
CURRENT_CANONICAL_CALLBACK_EFFECTS_CLOSED = True
CALLBACK_SOURCE = {
    "source_contract_game_version": "1.20.0.4",
    "source_dispatch_rva": "0x8571C0",
    "source_dispatch_sha256": "91d7d32779f253808d1b32fbe3f24e2b26346d59174c39952cffc39c81dc2060",
    "source_chain_rvas": ["0x8571C0", "0x40EC530", "0x423543C", "0x424E364"],
    "terminal_import_rva": "0x43DA748",
    "terminal_import": "KERNEL32.dll!HeapFree",
    "effect_boundary": "canonical_logical_normal_return_raw_buffer_deallocation",
}
CALLBACK_RECEIVERS = {
    "Army": {"singleton_rva": "0x54E0570", "vtable_rva": "0x44E61F8", "vtable_slot_rva": "0x44E6208"},
    "ArRg": {"singleton_rva": "0x54DEB68", "vtable_rva": "0x449C468", "vtable_slot_rva": "0x449C478"},
}


def _bind_current_release_source(release: Mapping) -> dict:
    """Bind source-ready canonical calls; preserve unknown dynamic suffixes."""
    result = deepcopy(dict(release))
    result["reused_release_kernel_contract_version"] = result["source_contract_game_version"]
    result["source_contract_game_version"] = "1.20.0.4"
    result["source_direct_release_rva"] = RELEASE_RVA
    result["source_direct_release_sha256"] = DIRECT_RELEASE_SHA256
    result["current_callback_source_closed"] = CURRENT_CANONICAL_CALLBACK_EFFECTS_CLOSED
    result["normal_return_premise"] = "explicit_same_capture_stage_reaches_cleanup; selected_canonical_callbacks_return_normally"
    for record in result["record_release_prefix"]:
        for vector in record["vectors"]:
            request = vector.get("buffer_release_call_request")
            if isinstance(request, dict) and request.get("actual_canonical_receiver") is True:
                request["current_callback_source"] = deepcopy(CALLBACK_SOURCE)
                request["current_receiver_source"] = deepcopy(CALLBACK_RECEIVERS[vector["role"]])
    return result


def project_army_assault_group_release_stage_12004(
    army: Mapping, *, numerical_stage: Mapping, stage: Mapping,
) -> dict:
    """Join current raw record headers to one source-bound conditional stage.

    ``numerical_stage`` is continuation37's output. ``stage`` independently
    declares the observed query capture, manager and predecessor identity,
    plus fixed table headers/controls through the numerical prefix. This is
    a conditional premise, never actual capture certification. A partial
    numerical prefix stays partial even when release is source-ready.
    """
    result = {
        "projection_kind": "conditional_explicit_stage_assault_group_release_12004",
        "source_contract_game_version": "1.20.0.4",
        "source_executable_sha256": EXECUTABLE_SHA256,
        "source_consumer_rva": CONSUMER_RVA,
        "source_release_call_rva": RELEASE_CALL_RVA,
        "source_direct_release_rva": RELEASE_RVA,
        "source_direct_release_sha256": DIRECT_RELEASE_SHA256,
        "army_id": army.get("army_id"), "stage_id": stage.get("stage_id"),
        "capture_id": stage.get("capture_id"),
        "observed_input_capture_id": stage.get("observed_input_capture_id"),
        "manager_identity": stage.get("manager_identity"),
        "prior_stage_id": stage.get("prior_stage_id"),
        "input_basis": stage.get("basis"),
        "status": "unavailable", "stage_input_ready": False,
        "missing_inputs": [], "numerical_prefix": None,
        "conditional_pre_release_queue": None, "release_prefix": None,
        "conditional_cleanup_frame": None,
        "current_callback_source_closed": CURRENT_CANONICAL_CALLBACK_EFFECTS_CLOSED,
        "native_writes_executed": 0, "actual_record_release": False,
        "actual_effects": False, "actual_post_manager_frame": None,
        "next_actual_manager_frame_ready": False,
        "queue_drain_replayed": False, "Army_removal_replayed": False,
        "next_pre_date_groups_constructed": False,
        "full_daily_assault_ready": False, "full_monthly_ready": False,
        "live": False,
    }
    table = army.get("current_daily_assault_table_v1")
    if not isinstance(table, Mapping):
        return {**result, "missing_inputs": ["current_daily_assault_table_v1"]}
    for name in ("stage_id", "capture_id", "observed_input_capture_id", "manager_identity", "prior_stage_id", "basis"):
        if not stage.get(name):
            result["missing_inputs"].append(name)
    if stage.get("executable_sha256") != EXECUTABLE_SHA256:
        result["missing_inputs"].append("stage_exact_actual4_source_pin")
    if stage.get("manager_identity") != table.get("manager_identity") or stage.get("manager_identity") != numerical_stage.get("manager_identity"):
        result["missing_inputs"].append("same_manager_identity")
    if stage.get("capture_id") != numerical_stage.get("capture_id") or stage.get("capture_id") != stage.get("observed_input_capture_id"):
        result["missing_inputs"].append("same_capture_identity")
    if stage.get("prior_stage_id") != numerical_stage.get("stage_id"):
        result["missing_inputs"].append("exact_numerical_predecessor_stage")
    if numerical_stage.get("source_contract_game_version") != "1.20.0.4" or numerical_stage.get("source_consumer_rva") != CONSUMER_RVA:
        result["missing_inputs"].append("actual4_numerical_source_binding")
    if numerical_stage.get("stage_input_ready") is not True or not isinstance(numerical_stage.get("numerical_prefix"), Mapping):
        result["missing_inputs"].append("numerical_stage_known_prefix")
    if stage.get("table_headers_and_controls_fixed_through_numerical_prefix") is not True:
        result["missing_inputs"].append("table_header_control_stage_premise")
    if result["missing_inputs"]:
        return result
    numeric = numerical_stage["numerical_prefix"]
    queue = project_current_daily_assault_queue_append_v1(army, numeric)
    queue["reused_queue_kernel_contract_version"] = queue["source_contract_game_version"]
    queue["source_contract_game_version"] = "1.20.0.4"
    queue["source_consumer_rva"] = CONSUMER_RVA
    release = _bind_current_release_source(project_current_daily_assault_normal_return_release_v1(army, queue))
    numerical_complete = numeric.get("sequential_numeric_ready") is True and numeric.get("queue_requests_ready") is True
    cleanup_frame = None
    if release["conditional_table_cleanup_ready"] is True:
        cleanup_frame = {
            "capture_id": stage["capture_id"], "stage_id": stage["stage_id"],
            "manager_identity": stage["manager_identity"],
            "basis": "conditional_cleanup_normal_return_postimage",
            "occupied_count_raw_i32": release["conditional_occupied_count_raw_i32"],
            "physical_controls": deepcopy(release["conditional_physical_controls"]),
            "record_release_prefix": deepcopy(release["record_release_prefix"]),
            "header_partial_fields": deepcopy(release["header_partial_fields"]),
            "pending_prefix_ready": release["conditional_post_release_pending_prefix_ready"],
            "pending_prefix": deepcopy(release["conditional_post_release_pending_prefix"]),
            "pending_sequence_ready": release["conditional_post_release_pending_sequence_ready"],
            "pending_sequence": deepcopy(release["conditional_post_release_pending_sequence"]),
            "numerical_prefix_complete": numerical_complete,
            "numerical_physical_chunks": deepcopy(numeric.get("conditional_physical_chunks")),
            "numerical_regiment_currents": deepcopy(numeric.get("conditional_regiment_currents")),
            "actual": False,
        }
    return {**result, "status": release["status"], "stage_input_ready": True,
        "missing_inputs": deepcopy(release["missing_inputs"]),
        "numerical_prefix": deepcopy(numeric),
        "conditional_pre_release_queue": queue, "release_prefix": release,
        "conditional_cleanup_frame": cleanup_frame}
