"""One native-reader/wire/normalizer/public-B prefix fixture, without CK3."""
from __future__ import annotations

import argparse
from dataclasses import asdict
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
    normalizer = importlib.import_module("xar_autoplayer.bridge.battle_context_source_inputs_contract")
    composer = importlib.import_module("xar_autoplayer.simulation.battle_context_preparation_branch_291d7e0_12003")
    native = json.loads(args.native_wire.read_text(encoding="utf-8-sig"))
    raw = native["current_context_source_inputs"]
    provenance = {"scope": "readonly-current-B-source-prefix", "unit_contract_sha256":
                  "7a10be179170eae2226f878a97e731cb138455332aaa3816963d0fc134d30c83"}
    calls: dict[str, int] = {}

    def profile(frame, event, _arg):
        if event == "call" and frame.f_code.co_name in {
            "normalize_current_context_source_inputs",
            "compose_291d7e0_current_contributions_12003",
            "emit_291e210_requests_from_current_source_inputs_12003",
            "emit_291e210_contribution_requests_12003",
        }:
            name = frame.f_code.co_name
            calls[name] = calls.get(name, 0) + 1

    sys.setprofile(profile)
    try:
        normalized = normalizer.normalize_current_context_source_inputs(raw)
        result = composer.compose_291d7e0_current_contributions_12003(
            normalized, source_provenance=provenance)
    finally:
        sys.setprofile(None)

    checks: list[str] = []
    check(normalized == raw, "actual native wire retained by production normalizer", checks)
    check(normalized["character_id"] == result.character_id == 29829,
          "current actor identity retained", checks)
    check(normalized["branch_291e210"]["ready"] is True,
          "independent empty A census remains available", checks)
    branch = normalized["branch_291d7e0"]
    sources = branch["source_rows"]
    check(branch["selected_source"] == "component+220" and branch["source_count"] == 4
          and [s["native_index"] for s in sources] == [0, 1, 2, 3]
          and [s["source_identity"] for s in sources] == ["s0", "s1", "s2", "s3"],
          "actual four-source census preserves native order and identities", checks)
    check(normalized["ready"] is False and normalized["status"] == "partial"
          and branch["base_inputs_ready"] is True and branch["ready"] is False,
          "observed base copies coexist with honest conditional partial readiness", checks)
    check(sources[0]["base_properties"]["keys_u16"] == [3, 9, 65535]
          and sources[0]["base_properties"]["values_q64"] == [(1 << 63) - 1, 20, 99],
          "raw base retains signed maximum and full-copy FFFF", checks)
    check(sources[1]["base_properties"] == {"keys_count": 0, "values_count": 1,
          "keys_u16": [], "values_q64": [-37], "reason": None}
          and all(sources[1][f"conditional_{kind}_count"] == 0 for kind in "abc"),
          "zero keys independently copies positive raw values before weighted skip", checks)

    a_rows = sources[0]["conditional_a_rows"]
    check(sources[0]["conditional_a_count"] == 4
          and [r["native_index"] for r in a_rows] == [0, 1, 2, 3]
          and [r["admitted"] for r in a_rows] == [False, True, True, False],
          "A exact pointer membership observes true and false native rows", checks)
    check(branch["selector_a_stage1"] == {"status": "resolved", "requested_full_id":
          0x04000003, "selected_full_id": 0x04000003, "reason": None}
          and branch["selector_a_stage2"] == {"status": "resolved", "requested_full_id":
          0x05000002, "selected_full_id": 0x05000002, "reason": None},
          "A first two selector stages preserve full generation identities", checks)
    check(branch["selector_a_stage3"] == {"status": "native_fallback", "requested_full_id":
          0x06000004, "selected_full_id": 0x08000005, "reason": "full_id_mismatch"}
          and branch["selector_a_selected_source"] == "initial_fallback5C67670",
          "A third-stage miss selects initial fallback after successful earlier stages", checks)
    check(branch["selector_a_key_count"] == 2
          and branch["selector_a_key_identities"] == [a_rows[2]["key_identity"], a_rows[1]["key_identity"]]
          and a_rows[0]["key_identity"] != a_rows[1]["key_identity"],
          "unsorted membership pointers remain distinct despite same full DWORD ID", checks)
    check(a_rows[1]["property_source"] == "first_full_id_match"
          and a_rows[1]["property_source_native_index"] == 0
          and a_rows[1]["property_block"]["keys_u16"] == [3, 7, 65535]
          and a_rows[1]["property_block"]["values_q64"] == [1, 0, 500],
          "admitted A row consumes first-ID PC from earlier unadmitted row", checks)
    check(a_rows[2]["key_object_magic"] == 0
          and a_rows[2]["property_source"] == "static5DC21B0"
          and a_rows[2]["property_source_native_index"] is None
          and a_rows[2]["property_block"]["keys_u16"] == [2]
          and a_rows[2]["property_block"]["values_q64"] == [-5],
          "invalid A magic consumes actual nonempty fallback PC", checks)

    b_rows = sources[0]["conditional_b_rows"]
    check(branch["selector_b_resolution"] == {"status": "resolved", "requested_full_id":
          0x09000003, "selected_full_id": 0x09000003, "reason": None}
          and branch["selector_b_primary_keys"]["keys_i32"] == [-10, 4, 8]
          and branch["selector_b_nested_count"] == 1
          and [r["keys_i32"] for r in branch["selector_b_nested_keys"]] == [[7]],
          "B selected native signed primary and demanded nested arrays retained", checks)
    check([r["key_i32"] for r in b_rows] == [-10, 7, 5]
          and [r["admitted"] for r in b_rows] == [True, True, False]
          and [r["admission_source"] for r in b_rows] == ["primary", "nested", "absent"]
          and [r["admission_nested_native_index"] for r in b_rows] == [None, 0, None],
          "B signed lower-bound primary-before-nested admission preserves row order", checks)
    check(b_rows[2]["property_block"]["keys_u16"] == [401]
          and b_rows[2]["property_block"]["values_q64"] == [2000]
          and native["poison_read_attempts"] == [0],
          "raw false-B inline PC observed while unused default classifier table remains unread", checks)

    c_rows = sources[0]["conditional_c_rows"]
    unknown = sources[2]["conditional_c_rows"][0]
    check(branch["condition_registry_guard"] == -2
          and branch["government_token_ids_i32"] == [-9, 0]
          and [r["source_key_u32"] for r in c_rows] == [0xAA000000, 0xAA000001, 0xAA000002]
          and [r["masked_index_u32"] for r in c_rows] == [0, 1, 2]
          and unknown["source_key_u32"] == 0xBB000003 and unknown["masked_index_u32"] == 3,
          "prepared negative guard and full condition keys retain actual masked indices", checks)
    check([r["condition_token_id"] for r in c_rows] == [-9, 0, 0]
          and [r["token_origin"] for r in c_rows] == ["existing_token_lookup",
          "native_early_zero_classifier", "native_early_zero_hyphen"]
          and [r["admitted"] for r in c_rows] == [True, False, True],
          "alternate locale lookup, classifier-zero and hyphen-zero preserve invert semantics", checks)
    check([r["classifier_mode_i32"] for r in c_rows] == [1, 1, None]
          and [r["classifier_result_i32"] for r in c_rows] == [0, 4, None]
          and c_rows[2]["locale_classification"] is None,
          "hyphen bypass remains separate from actual alternate classifier operands", checks)
    locale_rows = [c_rows[0]["locale_classification"], c_rows[1]["locale_classification"],
                   unknown["locale_classification"]]
    check(all(r["crt_index"] == 23 and r["cached_value_api_status"] == "existing_fls"
          and r["thread_state_source"] == "existing_fls_value"
          and r["locale_source"] == "global_locale_selected_without_sync"
          and r["thread_locale_flags"] == 0 and r["flags_mask"] == 1 for r in locale_rows),
          "decoded prepared getter reads exact global-selected current locale without sync", checks)
    check([r["ready"] for r in locale_rows] == [True, True, False]
          and [r["table_element_u16"] for r in locale_rows] == [0, 4, None]
          and [r["result_i32"] for r in locale_rows] == [0, 4, None],
          "actual alternate U16 table values unlock ASCII classification", checks)
    check(unknown["condition_bytes"] == [0xE4, 0xB8, 0xAD]
          and unknown["first_signed_byte"] == -28
          and unknown["locale_classification"]["locale_max_multibyte"] == 2
          and unknown["condition_token_id"] is None and unknown["admitted"] is None
          and unknown["reason"] == "classifier_unavailable_locale_multibyte_path",
          "same current image retains UTF8 multibyte branch as typed partial", checks)
    check(native["lookup_abi_ok"] is True and native["lookup_calls"] == 1
          and native["government_calls"] == 1 and native["fixture_failed_reads"] == 0,
          "actual reader exercises exact existing lookup ABI without read errors", checks)
    check(native["locale_value_getter_calls"] == native["locale_get_error_calls"]
          == native["locale_set_error_calls"] == 3 and native["locale_last_error"] == 77,
          "all three needed prepared locale reads preserve LastError", checks)

    check(calls == {"normalize_current_context_source_inputs": 1,
                   "compose_291d7e0_current_contributions_12003": 1},
          "one actual normalizer and new public B invocation", checks)
    check(result.status == "partial" and result.contributions_ready is False
          and result.ready is False and result.verified_source_count == 2
          and result.stopped_source_native_index == 2
          and result.deferred_source_native_indices == (3,),
          "public B preserves verified source prefix and stops before unknown source", checks)
    check(len(result.contributions) == 1 and result.contributions[0].native_source_index == 0
          and result.contributions[0].source_identity == "s0"
          and result.contributions[0].weight_q64 == 100000,
          "only verified nonempty source emits one native-order unit-Q request", checks)
    properties = result.contributions[0].properties
    check(properties.keys_u16 == (2, 3, 4, 6, 7, 9, 65535)
          and properties.values_q64 == (-5, (1 << 63) - 1, 0, 7, 0, -10, 99)
          and properties.count == 7,
          "independent hand composite proves wrap, new-key zero, lower-bound order and FFFF semantics", checks)
    check([r["status"] for r in result.source_results] == ["emitted", "zero_key_count_skip", "partial_frontier"]
          and [r["native_source_index"] for r in result.source_results] == [0, 1, 2]
          and result.missing_inputs == ("branch_291d7e0.source_rows[2].conditional_c_rows[0].admitted",),
          "ledger skips actual empty source then records one precise partial frontier", checks)
    check(result.source_provenance is provenance and result.full_future_context_ready is False
          and result.native_write_performed is False and result.actual_game_days_advanced == 0,
          "current logical prefix retains provenance and honest offline boundaries", checks)

    (args.output_dir / "OUTPUT.json").write_text(json.dumps({"normalized_section": normalized,
          "public_B_result": asdict(result)}, indent=2) + "\n", encoding="utf-8")
    report = {"schema": "v86-current-B-prefix-focused-result/v1", "state": "GREEN",
              "unique_new_cases": 1, "explicit_check_count": len(checks), "checks": checks,
              "calls": calls, "contribution_count": len(result.contributions),
              "verified_source_count": result.verified_source_count,
              "stopped_source_native_index": result.stopped_source_native_index,
              "fixture_memory_reads": native["fixture_memory_reads"],
              "fixture_failed_reads": native["fixture_failed_reads"],
              "readiness": "static-ready / fixture-offline", "production_live": False,
              "full_future_context_ready": False, "entry_refresh_ready": False,
              "old_tests_run": 0, "SDK": 0, "game_process": 0, "window": 0}
    (args.output_dir / "RESULT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
