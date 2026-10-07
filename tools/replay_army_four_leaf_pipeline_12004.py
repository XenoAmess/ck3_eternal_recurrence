"""FIRST_NOTRUN: native four-family fragments through real registered ArmyService.

The enclosing strength row and memory backend are existing fixtures. New family
bytes come unchanged from native_four_leaf_fixture.cpp's real Read/Append calls.
This consumer does not exercise a whole native Strength producer or live CK3.
"""
from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
import json
from pathlib import Path
import sys

_RAW = (
    "future_daily_supply_schedule_inputs_v1", "current_detachment_callback_inputs_v1",
    "current_detachment_store_inputs_v1", "current_character_detachment_inputs_v1",
)
_DERIVED = (
    "same_input_conditional_future_daily_supply_schedule_v1",
    "conditional_current_detachment_callback_v1", "current_detachment_store_admission_v1",
    "current_character_detachment_suffix_v1",
)
_ACTUAL_FALSE = (
    "actual_callback_observed", "actual_resource_return_observed",
    "actual_after_state_observed", "full_detachment_transition_ready",
    "full_daily_ready", "full_monthly_ready",
)
_PROVENANCE = "synthetic_new_collector_serializer_fragments_not_whole_native_strength"


def _check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)


def _false(value: dict, fields: tuple[str, ...]) -> None:
    for field in fields:
        _check(value[field] is False, field + " must remain false")


def _projection(returned: dict, key: str) -> dict:
    rows = returned[key]
    _check(len(rows) == 1 and rows[0]["army_id"] == 11, key + " same Army association")
    return rows[0]["projection"]


def _check_new_behavior(returned: dict, scene: str, fragments: dict) -> None:
    schedule, callback, store, character = [
        _projection(returned, key) for key in _DERIVED]
    _check(schedule["prospective_frames"] == [], "no invented future date/D frames")
    _check(schedule["observed_matching_phases"] == [], "observed empty all30 membership")
    _check(schedule["selected_phase_index_i32"] == 7, "observed storedD7 phase preserved")
    _check(len(fragments[_RAW[0]]["phases"]) == 30, "native all30 phases preserved")
    _check(all(phase["ready"] and phase["count_raw_i32"] == 0
        and phase["matching_positions"] == [] for phase in fragments[_RAW[0]]["phases"]),
        "native zero/null buckets remain available")
    _false(schedule, ("calendar_derived", "actual_future_callback_observed",
        "future_bucket_mutations_reconstructed", "future_supply_eligibility_ready",
        "future_stock_or_strength_ready", "full_daily_supply_transition_ready", "full_monthly_ready"))

    _check(callback["ready"] and len(callback["incoming"]) == 2, "independent null DATA callbacks")
    for incoming in callback["incoming"]:
        _check(incoming["branch"] == "null_data_skips_cleanup_and_resource", "null DATA source branch")
        _check(incoming["record_cleanup_required"] is False
            and incoming["resource_call_required"] is False, "unselected callback/helper/allocator")
        after = incoming["conditional_direct_after_header"]
        _check(after["data_count_2c_raw_i32"] == -2 and after["data_capacity_28_raw_i32"] == 7,
            "null DATA preserves independently observed signed count/capacity")
        _false(incoming, _ACTUAL_FALSE)
    _false(callback, _ACTUAL_FALSE)

    _check(store["admission_ready"] and len(store["requests"]) == 2, "two current matching store requests")
    for request in store["requests"]:
        _check(request["admitted"] and request["pre_callback_updates_ready"], "current store admission")
        writes = {write["field"]: write for write in request["pre_callback_updates"]}
        _check(writes["active_count_3c_raw_u32"]["before"] == 0
            and writes["active_count_3c_raw_u32"]["after"] == 0xFFFFFFFF, "same-current3C0 unsigned wrap")
        _check(writes["registry_mark_4a_raw_u8"]["after"] == 1, "source mark4A1")
        _check(all(write["executed"] is False for write in writes.values()), "conditional stores only")
        _false(request, _ACTUAL_FALSE)
    _false(store, _ACTUAL_FALSE)

    rows = character["requests"]
    _check(character["ready"] and len(rows) == 2, "Character requests preserved without dedup")
    _check([row["seed_incoming_native_index"] for row in rows] == [0, 1], "incoming source order")
    _check(len({row["observed_current_character_identity"] for row in rows}) == 1,
        "same current Character retained twice")
    _check(len({row["passed_province_identity"] for row in rows}) == 2, "distinct passed Provinces retained")
    for row in rows:
        if scene == "skip":
            _check(row["no_suffix"] and row["branch"] == "null_current_character1b8_no_suffix",
                "observed null extension independently completes no-suffix")
            _check(row["source_defined_reset_descriptors"] == [] and row["remaining_stage_inputs"] == [],
                "null branch does not select later reset/date stages")
        else:
            _check(not row["current_source_chain_ready"] and row["reset_inputs_ready"],
                "partial chain does not gate known reset descriptor")
            resets = row["source_defined_reset_descriptors"]
            _check([item["target_role"] for item in resets] == [
                "captured_initial_extension", "fresh_character1B8_reload_if_nonnull"], "source reset roles")
            _check(resets[0]["target_identity"] == row["observed_current_extension"]["identity"],
                "initial extension target is current observation")
            _check(resets[0]["source_defined_after_raw_u32"] == 0xFFFFFFFF, "source F8 reset constant")
            _check(resets[1]["target_identity"] is None and resets[1]["source_defined_after_raw64"]
                == 0xFFFFFFFF029C77F8 - (1 << 64), "fresh reload stays unobserved; full signed sentinel")
            _check(all(item["source_reached"] is False and item["actual_write_observed"] is False
                for item in resets), "source descriptors are not observed reset execution")
        _false(row, (*_ACTUAL_FALSE, "actual_reset_observed", "post_reset_origin_ready",
            "full_character_detachment_suffix_ready", "future_date_ready"))
    _false(character, (*_ACTUAL_FALSE, "actual_reset_observed", "post_reset_origin_ready",
        "full_character_detachment_suffix_ready", "future_date_ready"))


async def _consume(args: argparse.Namespace) -> None:
    # Project imports and MCP SDK use occur only when Root explicitly runs FIRST.
    for suffix in ("tests/unit", "tests", "src"):
        sys.path.insert(0, str(args.project_root / suffix))
    from test_current_detachment_data_service_compound import _Driver, strength_row
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.version_identity import CK3_12004

    class FixtureDriver(_Driver):
        def take_snapshot(self) -> dict:
            snapshot = super().take_snapshot()
            snapshot["snapshot_id"] = "offline-four-new-leaves-12004-FIRST"
            snapshot["date_raw"] = self.source[_RAW[0]]["current_date_raw_i32"]
            snapshot["diagnostics"]["hello"] = {
                "game_version": CK3_12004.game_version,
                "executable_sha256": CK3_12004.executable_sha256,
            }
            return snapshot

    args.output_dir.mkdir(parents=True, exist_ok=True)
    report_path = args.output_dir / "four-leaf-registered-service.json"
    report = {"status": "RUNNING", "wire": str(args.wire), "project_root": str(args.project_root),
        "native_input_scope": _PROVENANCE, "whole_native_strength_producer": False,
        "registered_consumer": "ck3_query_army_strengths -> GameplayBridgeService.query_army_strengths -> whole Army normalizer and four projections",
        "backend": "existing memory fixture _Driver", "live_queries": 0,
        "native_getter_reset_mutator_calls": 0, "scenes": []}

    def persist() -> None:
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    persist()
    try:
        bundle = json.loads(args.wire.read_text(encoding="utf-8"))
        _check(set(bundle) == {"schema_version", "subject_army_id", "subject_native_carmy_id",
            "scene_order", "samples", "provenance"}, "frozen native fixture bundle fields")
        _check(bundle["schema_version"] == 1 and bundle["provenance"] == _PROVENANCE, "native fixture provenance")
        _check((bundle["subject_army_id"], bundle["subject_native_carmy_id"]) == (11, 12), "native subject IDs")
        _check(bundle["scene_order"] == ["skip", "selected"]
            and set(bundle["samples"]) == {"skip", "selected"}, "frozen two native scenes")
        for scene in bundle["scene_order"]:
            report["active_scene"] = scene
            fragments = bundle["samples"][scene]
            _check(set(fragments) == set(_RAW), "four actual native Read/Append fragments")
            source = strength_row(maximum=120)
            source.update(deepcopy(fragments))
            before = deepcopy(source)
            driver = FixtureDriver(source)
            server = create_server(driver)
            registered = server._tool_manager._tools["ck3_query_army_strengths"].fn
            _check(registered.__module__ == "xar_autoplayer.bridge.mcp_server", "real registered callable")
            result = await server.call_tool("ck3_query_army_strengths", {
                "army_ids": [11], "expected_revision": 42})
            _check(result.is_error is False, "registered tool succeeded")
            returned = result.structured_content
            _check(isinstance(returned, dict) and returned["status"] == "available", "whole Service result")
            _check(driver.calls == [("query-army-strengths-v1", 42)], "one existing query; no new game action")
            _check(source == before, "native family fragments and current source unchanged")
            _check(returned["native_readiness"] == {"current_strength": True, "full_monthly": False},
                "independent siblings do not replace global native readiness")
            _check(returned["army_strengths"][0]["current_soldiers"] == 160, "whole strength row retained")
            for key in _RAW:
                _check(returned["army_strengths"][0][key] == fragments[key], key + " survived whole normalizer")
            _check_new_behavior(returned, scene, fragments)
            _check(len(result.content) == 1, "one compact MCP text block")
            summary = json.loads(result.content[0].text)
            _check(summary["result_location"] == "structuredContent" and summary["army_ids"] == [11],
                "compact summary points to complete structured content")
            wire = result.model_dump_json(by_alias=True)
            _check(json.loads(wire)["structuredContent"] == returned, "complete MCP JSON roundtrip")
            destination = args.output_dir / (scene + "-registered-mcp-result.json")
            destination.write_text(wire + "\n", encoding="utf-8")
            report["scenes"].append({"scene": scene, "registered_tool_calls": 1,
                "backend_query_calls": driver.calls, "whole_normalizer_preserved_families": list(_RAW),
                "derived_keys": list(_DERIVED), "complete_structured_roundtrip": True,
                "compact_text_bytes": len(result.content[0].text.encode("utf-8")),
                "result_artifact": str(destination)})
            persist()
        report["status"] = "GREEN"
        persist()
    except BaseException as error:
        report.update(status="RED", failure=f"{type(error).__name__}: {error}")
        persist()
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path,
        help="Adopted repository root containing ck3_autonomous_player")
    parser.add_argument("--wire", required=True, type=Path, help="Absolute native fixture JSON output")
    parser.add_argument("--output-dir", required=True, type=Path, help="External FIRST artifact directory")
    args = parser.parse_args()
    args.source_root = args.source_root.resolve()
    args.project_root = (args.source_root / "ck3_autonomous_player").resolve()
    args.wire = args.wire.resolve()
    args.output_dir = args.output_dir.resolve()
    asyncio.run(_consume(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
