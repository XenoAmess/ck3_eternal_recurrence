"""One offline production-reader/serializer/normalizer/public-emitter fixture.

The native wire file is produced by context_source_inputs_12003_fixture.cpp.
No CK3 process, SDK or game action is created by this runner.
"""
from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
import sys
from types import ModuleType


def check(condition: object, name: str, checks: list[str]) -> None:
    if not condition:
        raise RuntimeError(name)
    checks.append(name)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--native-wire", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--baseline-source-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    roots = [args.source_root, args.baseline_source_root]
    for name, suffix in (("xar_autoplayer", ""), ("xar_autoplayer.bridge", "bridge"),
                         ("xar_autoplayer.simulation", "simulation")):
        module = ModuleType(name)
        module.__path__ = [str(root / "xar_autoplayer" / suffix) for root in roots]
        sys.modules[name] = module
    contract = importlib.import_module("xar_autoplayer.bridge.battle_context_source_inputs_contract")
    calls: dict[str, int] = {}

    def profile(frame, event, _arg):
        if event == "call" and frame.f_code.co_name in {
            "normalize_current_context_source_inputs",
            "emit_291e210_requests_from_current_source_inputs_12003",
            "emit_291e210_contribution_requests_12003",
        }:
            name = frame.f_code.co_name
            calls[name] = calls.get(name, 0) + 1

    native = json.loads(args.native_wire.read_text(encoding="utf-8-sig"))
    raw = native["current_context_source_inputs"]
    sys.setprofile(profile)
    try:
        normalized = contract.normalize_current_context_source_inputs(raw)
        requests = contract.emit_291e210_requests_from_current_source_inputs_12003(normalized)
    finally:
        sys.setprofile(None)
    checks: list[str] = []
    branch = normalized["branch_291e210"]
    check(normalized == raw, "actual native section preserved by production normalizer", checks)
    check(branch["ready"] is True and branch["status"] == "available",
          "A current consumed source operands available", checks)
    check(normalized["character_id"] == 29829, "actor identity retained", checks)
    check(branch["first_relation_resolution"] == {
        "status": "native_fallback", "requested_full_id": 0x01000003,
        "selected_full_id": 0x03000004, "reason": "full_id_mismatch"},
        "full generation mismatch selects actual first fallback", checks)
    check(branch["house_resolution"] == branch["first_relation_resolution"],
          "native repeated first-object resolution retains full identity", checks)
    check(branch["second_relation_resolution"] == {
        "status": "resolved", "requested_full_id": 0x02000002,
        "selected_full_id": 0x02000002, "reason": None},
        "second-object full identity resolves from selected fallback", checks)
    spans = [branch[key] for key in (
        "selected_lifestyle_span", "selected_dynasty_span", "selected_house_span",
        "selected_house_extra_span")]
    check([span["selected_source"] for span in spans] == [
        "component+188", "second_relation+140", "first_relation+168", "first_relation+200"],
        "four actual selected source headers in native order", checks)
    check([span["count"] for span in spans] == [4, 1, 3, 2],
          "actual signed source counts retained", checks)
    check([[row["native_index"] for row in span["rows"]] for span in spans] == [
        [0, 1, 2, 3], [0], [0, 1, 2], [0, 1]], "native row order unchanged", checks)
    check([[row["weight_q64"] for row in span["rows"]] for span in spans] == [
        [(1 << 63) - 1, 1, 0, -3], [5], [-2, 2, -1], [17, -4]],
        "native raw signed Q64 words retained", checks)
    blocks = {item["definition_identity"]: item["properties"]
              for item in branch["definition_blocks"]}
    check(list(blocks) == ["d0", "d1", "d2"], "distinct snapshot definitions retain native first-use order", checks)
    check(blocks["d0"]["keys_u16"] == [44, 3]
          and blocks["d0"]["values_q64"] == [-10, -(1 << 63) + 8],
          "actual Def+40 unsorted keys and signed values retained", checks)
    check(blocks["d1"]["keys_count"] == 0 and blocks["d1"]["values_count"] is None
          and blocks["d1"]["keys_u16"] == [] and blocks["d1"]["values_q64"] == [],
          "empty A property skips unread values header and remains available", checks)
    check(native["poison_read_attempts"] == [0, 0, 0, 0, 0],
          "actual reader never consumes empty A headers or unused fallback headers", checks)
    expected = [
        (1, "lifestyle", 0, 2, "d0", -(1 << 63)),
        (1, "lifestyle", 2, 1, "d1", 0),
        (1, "lifestyle", 3, 1, "d0", -3),
        (2, "dynasty", 0, 1, "d0", 5),
        (3, "house", 0, 2, "d2", 0),
        (3, "house", 2, 1, "d0", -1),
        (4, "house_extra", 0, 1, "d0", 17),
        (4, "house_extra", 1, 1, "d1", -4),
    ]
    actual = [(item.source_ordinal, item.source_name, item.first_row_index,
               item.row_count, item.definition_identity, item.weight_q64) for item in requests]
    check(actual == expected, "adopted emitter preserves consecutive/nonadjacent/cross-span runs and wrap64", checks)
    check(all(item.base_property_block is blocks[item.definition_identity] for item in requests),
          "actual Def+40 blocks passed by reference including zero-weight empty request", checks)
    check(calls == {
        "normalize_current_context_source_inputs": 1,
        "emit_291e210_requests_from_current_source_inputs_12003": 1,
        "emit_291e210_contribution_requests_12003": 1,
    }, "one actual normalizer/adapter/adopted emitter invocation", checks)
    branch_b = normalized["branch_291d7e0"]
    check(normalized["ready"] is False and normalized["status"] == "partial"
          and branch_b["base_inputs_ready"] is True and branch_b["ready"] is False,
          "A requests available independently of honest B partial readiness", checks)
    check(branch_b["selected_source"] == "component+220" and branch_b["source_count"] == 1,
          "B current ordered source census observed", checks)
    source = branch_b["source_rows"][0]
    check(source["native_index"] == 0 and source["source_identity"] == "s0",
          "B source identity and native index retained", checks)
    check(source["base_properties"] == {
        "keys_count": 0, "values_count": 1, "keys_u16": [], "values_q64": [-37], "reason": None},
        "B basecopy independently reads positive values despite zero keys", checks)
    check(source["auxiliary_410_provenance"] == "unobserved_shape_source+410"
          and source["auxiliary_retained_present"] is False
          and source["auxiliary_retained_identity"] is None and source["auxiliary_tag_u32"] == 55,
          "B unknown auxiliary width stays unclaimed while consumed fields retain provenance", checks)
    check(branch_b["conditional_a_fallback_properties"] == {
        "keys_count": 1, "values_count": 1, "keys_u16": [8], "values_q64": [-70], "reason": None},
        "actual current B A-fallback property block retained", checks)
    check(source["conditional_a_count"] == 1
          and source["conditional_a_rows"][0]["admitted"] is None
          and source["conditional_a_rows"][0]["reason"] == "conditional_a_selector_not_observed"
          and source["conditional_b_count"] == 0 and source["conditional_b_rows"] == [],
          "B unavailable selector admission remains null beside observed empty rows", checks)
    c_rows = source["conditional_c_rows"]
    check(source["conditional_c_count"] == 4
          and [row["source_key_u32"] for row in c_rows] == [0xAA000000, 0xBB000001, 0xCC000002, 0xDD000008]
          and [row["masked_index_u32"] for row in c_rows] == [0, 1, 2, 8]
          and [row["resolver_count_i32"] for row in c_rows] == [3, 3, 3, 3]
          and [row["selected_native_fallback"] for row in c_rows] == [False, False, False, True],
          "B full source keys resolve by native mask and actual fallback gate without token aliases", checks)
    check([row["condition_source"] for row in c_rows] == [
        "registry+30/index", "registry+30/index", "registry+30/index", "static+5DC1368"]
          and [row["condition_bytes"] for row in c_rows] == [
              list(b"-"), list(b"known"), list(b"missing"), list(b"-fallback")]
          and branch_b["condition_registry_guard"] == -2 and branch_b["condition_fallback_guard"] == -2,
          "B actual prepared inline conditions and fallback string provenance retained", checks)
    check([row["condition_token_id"] for row in c_rows] == [0, -9, None, 0]
          and [row["token_origin"] for row in c_rows] == [
              "native_early_zero_hyphen", "existing_token_lookup", "existing_token_lookup", "native_early_zero_hyphen"]
          and [row["lookup_status"] for row in c_rows] == ["", "found", "miss", ""],
          "B actual early-zero and signed lookup tokens retained while miss stays null", checks)
    check([row["classifier_mode_i32"] for row in c_rows] == [None, 0, 0, None]
          and [row["classifier_result_i32"] for row in c_rows] == [None, 0, 0, None],
          "B default classifier provenance retains actual consumed gates", checks)
    check([row["admitted"] for row in c_rows] == [True, True, None, False]
          and c_rows[2]["reason"] == "token_not_currently_interned_would_intern"
          and branch_b["government_token_ids_i32"] == [-9, 0],
          "B signed membership and invert observed without inventing miss admission", checks)
    check(native["lookup_abi_ok"] is True and native["lookup_calls"] == 2
          and native["government_calls"] == 1 and native["fixture_failed_reads"] == 0,
          "exact Slice16 Cursor8 map-header ABI and native record reads exercised without read errors", checks)
    output = {
        "normalized_section": normalized,
        "requests": [{
            "source_ordinal": row.source_ordinal, "source_name": row.source_name,
            "first_row_index": row.first_row_index, "row_count": row.row_count,
            "definition_identity": row.definition_identity, "weight_q64": row.weight_q64,
            "base_property_block": row.base_property_block,
        } for row in requests],
    }
    (args.output_dir / "OUTPUT.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    result = {
        "schema": "v85-current-context-source-inputs-focused-result/v1",
        "state": "FIRST_GREEN", "unique_new_cases": 1, "explicit_check_count": len(checks),
        "checks": checks, "calls": calls, "request_count": len(requests),
        "fixture_memory_reads": native["fixture_memory_reads"],
        "fixture_failed_reads": native["fixture_failed_reads"],
        "readiness": "static-ready / fixture-offline", "production_live": False,
        "full_future_context_ready": False, "entry_refresh_ready": False,
        "old_tests_run": 0, "SDK": 0, "game_process": 0, "window": 0,
    }
    (args.output_dir / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
