"""Validate published typed scripted-template fixtures without native execution.

The fixture and mutants are OFFLINE ABI evidence. They do not identify a stock
branch in a game run, read a parameterized cache root, or close global state.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re

WRAPPER_VT = 0x44CF0F8
WRAPPER_EXECUTE = 0x3381DB0
TEMPLATE_VT = 0x44DCD38


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def integer(value: object, label: str, minimum: int = 0) -> int:
    require(type(value) is int and value >= minimum, label)
    return value


def boolean(value: object, label: str) -> bool:
    require(type(value) is bool, label)
    return value


def token(value: object, label: str) -> int:
    require(type(value) is str and re.fullmatch(r"process-local-0x[0-9a-f]+", value) is not None, label)
    return int(value.removeprefix("process-local-0x"), 16)


def exact_object(value: object, fields: set[str], label: str) -> dict:
    require(type(value) is dict and set(value) == fields, label)
    return value


def check_metadata(row: dict) -> dict:
    require(integer(row["node_vtable_rva"], "wrapper type") == WRAPPER_VT, "wrapper type")
    require(integer(row["node_original_execute_rva"], "wrapper execute") == WRAPPER_EXECUTE, "wrapper execute")
    require(token(row["node_identity_token"], "wrapper token") > 0, "wrapper null")
    d = exact_object(row["scripted_effect_definition"], {
        "read", "object_token", "vtable_rva", "key", "parameter_count_raw",
        "invocation_argument_count_raw", "default_root",
        "default_root_selected_by_empty_arguments", "parameterized_active_cache_root_read",
    }, "definition fields")
    require(boolean(d["read"], "definition read") is True, "definition unavailable")
    require(token(d["object_token"], "definition token") > 0, "definition null")
    require(integer(d["vtable_rva"], "template type") == TEMPLATE_VT, "template type")
    key = d["key"]
    require(type(key) is str and 0 < len(key) < 128 and
            all(0x20 < ord(c) < 128 and c not in '\\"' for c in key), "definition key")
    integer(d["parameter_count_raw"], "template parameter count")
    argument_count = integer(d["invocation_argument_count_raw"], "invocation argument count")
    require(boolean(d["default_root_selected_by_empty_arguments"], "root selection flag") ==
            (argument_count == 0), "root selection source")
    require(boolean(d["parameterized_active_cache_root_read"], "cache read flag") is False,
            "parameterized active cache root not supported")
    root = exact_object(d["default_root"], {"read", "node_identity_token", "node_vtable_rva",
                                          "node_hash", "node_original_execute_rva"}, "root fields")
    root_token = token(root["node_identity_token"], "default root token")
    present = boolean(root["read"], "root read")
    vt = integer(root["node_vtable_rva"], "root type")
    execute = integer(root["node_original_execute_rva"], "root execute")
    integer(root["node_hash"], "root hash")
    if root_token:
        require(present and 0 < vt < 0x6000000 and 0 < execute < 0x6000000, "nonnull root identity")
    else:
        require(not present and vt == 0 and execute == 0 and root["node_hash"] == 0,
                "null root must be explicit and unread")
    return d


def evaluate_fixture(fixture: dict) -> dict:
    require(type(fixture) is dict and type(fixture["records"]) is list, "fixture records")
    rows = fixture["records"]
    pairs = {}
    seen_sequences = set()
    for row in rows:
        require(type(row) is dict, "record object")
        sequence = integer(row["sequence"], "sequence")
        require(sequence not in seen_sequences, "duplicate sequence")
        seen_sequences.add(sequence)
        require(integer(row["failure_flags"], "failure flags") == 0, "failed record")
        if row["node_vtable_rva"] != WRAPPER_VT:
            require("scripted_effect_definition" not in row, "untyped definition publication")
            continue
        invocation = integer(row["invocation"], "invocation", 1)
        boundary = row["boundary"]
        require(boundary in ("effect_enter", "effect_return"), "definition boundary")
        check_metadata(row)
        pair = pairs.setdefault(invocation, {})
        require(boundary not in pair, "duplicate invocation edge")
        pair[boundary] = row
    require(pairs, "no actual scripted definition fixture pair")
    results = []
    for invocation, pair in pairs.items():
        require(set(pair) == {"effect_enter", "effect_return"}, "incomplete pair")
        before, after = pair["effect_enter"], pair["effect_return"]
        require(before["sequence"] < after["sequence"], "pair ordering")
        for field in ("parent_invocation", "thread_id", "native_date_raw", "combat_id",
                      "phase_day", "side_index", "native_event_load_index", "depth", "node_vtable_rva",
                      "node_hash", "node_original_execute_rva"):
            integer(before[field], field)
            integer(after[field], field)
            require(before[field] == after[field], "pair identity " + field)
        require(before["node_identity_token"] == after["node_identity_token"], "wrapper changed")
        require(before["scripted_effect_definition"] == after["scripted_effect_definition"],
                "definition metadata changed")
        d = before["scripted_effect_definition"]
        results.append({"invocation": invocation, "key": d["key"],
                        "default_root_present": d["default_root"]["read"],
                        "default_root_selected_by_empty_arguments": d["default_root_selected_by_empty_arguments"],
                        "parameterized_active_cache_root_read": False})
    return {"scripted_pairs": results, "OFFLINE_ABI_FIXTURE_NOT_GAME_TRUTH": True,
            "named_stock_domain_closed": False, "global_mutable_bundle_complete": False}


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    out = {}
    for key, value in pairs:
        require(key not in out, "duplicate JSON key")
        out[key] = value
    return out


def parse_compiled_stdout(raw: bytes) -> dict:
    """Read the single labeled JSON line emitted after native diagnostics."""
    lines = raw.decode("utf-8").splitlines()
    candidates = [line for line in lines if line.startswith('{"kind":"OFFLINE_FIXTURE_NOT_NATIVE_GAME_TRUTH",')]
    require(len(candidates) == 1, "exactly one labeled native offline fixture JSON line")
    value = json.loads(candidates[0], object_pairs_hook=reject_duplicate_keys)
    require(type(value) is dict and value.get("kind") == "OFFLINE_FIXTURE_NOT_NATIVE_GAME_TRUTH",
            "native offline fixture envelope")
    require(all(not line.lstrip().startswith(("{", "[")) or line == candidates[0] for line in lines),
            "unexpected extra JSON output")
    return value


def regression_cases(fixture: dict) -> list[dict]:
    candidates = [n for n, row in enumerate(fixture["records"]) if row["node_vtable_rva"] == WRAPPER_VT]
    index = candidates[0]
    mutations = [
        ("read_int", ["scripted_effect_definition", "read"], 1),
        ("read_false", ["scripted_effect_definition", "read"], False),
        ("null_definition", ["scripted_effect_definition", "object_token"], "process-local-0x0"),
        ("wrong_template", ["scripted_effect_definition", "vtable_rva"], TEMPLATE_VT + 8),
        ("boolean_template", ["scripted_effect_definition", "vtable_rva"], True),
        ("empty_key", ["scripted_effect_definition", "key"], ""),
        ("key_type", ["scripted_effect_definition", "key"], 42),
        ("overbound_key", ["scripted_effect_definition", "key"], "x" * 128),
        ("whitespace_key", ["scripted_effect_definition", "key"], "growth empty"),
        ("quote_key", ["scripted_effect_definition", "key"], 'growth"empty'),
        ("slash_key", ["scripted_effect_definition", "key"], "growth\\empty"),
        ("negative_param", ["scripted_effect_definition", "parameter_count_raw"], -1),
        ("boolean_param", ["scripted_effect_definition", "parameter_count_raw"], False),
        ("negative_arguments", ["scripted_effect_definition", "invocation_argument_count_raw"], -1),
        ("boolean_arguments", ["scripted_effect_definition", "invocation_argument_count_raw"], True),
        ("cache_claim", ["scripted_effect_definition", "parameterized_active_cache_root_read"], True),
        ("cache_int", ["scripted_effect_definition", "parameterized_active_cache_root_read"], 0),
        ("selection_false", ["scripted_effect_definition", "default_root_selected_by_empty_arguments"], False),
        ("selection_int", ["scripted_effect_definition", "default_root_selected_by_empty_arguments"], 1),
        ("root_boolean_hash", ["scripted_effect_definition", "default_root", "node_hash"], True),
        ("root_false_nonnull", ["scripted_effect_definition", "default_root", "read"], False),
        ("root_int_read", ["scripted_effect_definition", "default_root", "read"], 1),
        ("root_zero_type", ["scripted_effect_definition", "default_root", "node_vtable_rva"], 0),
        ("root_outside_execute", ["scripted_effect_definition", "default_root", "node_original_execute_rva"], 0x6000000),
        ("pseudo_null", ["scripted_effect_definition", "default_root", "node_identity_token"], "process-local-0x0"),
        ("wrong_wrapper_execute", ["node_original_execute_rva"], 0x3380EC0),
        ("boolean_sequence", ["sequence"], False),
        ("boolean_flags", ["failure_flags"], False),
        ("real_flags", ["failure_flags"], 1),
        ("foreign_thread", ["thread_id"], 1),
        ("foreign_day", ["native_date_raw"], 53146872),
        ("generation_changed", ["combat_id"], 0x02000002),
    ]
    cases = [{"case": "compiled_original_positive", "status": "PASS",
              "result": evaluate_fixture(fixture)}]
    for name, fields, replacement in mutations:
        mutated = copy.deepcopy(fixture)
        target = mutated["records"][index]
        for field in fields[:-1]:
            target = target[field]
        target[fields[-1]] = replacement
        try:
            evaluate_fixture(mutated)
        except (ValueError, KeyError, TypeError) as error:
            cases.append({"case": name, "status": "PASS_REJECTED", "reason": str(error)})
        else:
            raise ValueError("Mutation accepted: " + name)
    for name in ("missing_key", "missing_default_root", "changed_definition", "duplicate_edge", "duplicate_key_parser"):
        mutated = copy.deepcopy(fixture)
        entry = mutated["records"][index]
        try:
            if name == "missing_key":
                del entry["scripted_effect_definition"]["key"]
            elif name == "missing_default_root":
                del entry["scripted_effect_definition"]["default_root"]
            elif name == "changed_definition":
                entry["scripted_effect_definition"]["object_token"] = "process-local-0x12345"
            elif name == "duplicate_edge":
                extra = copy.deepcopy(entry)
                extra["sequence"] = max(r["sequence"] for r in mutated["records"]) + 1
                mutated["records"].append(extra)
            else:
                json.loads('{"read":true,"read":false}', object_pairs_hook=reject_duplicate_keys)
            evaluate_fixture(mutated)
        except (ValueError, KeyError, TypeError) as error:
            cases.append({"case": name, "status": "PASS_REJECTED", "reason": str(error)})
        else:
            raise ValueError("Mutation accepted: " + name)
    return cases


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-stdout", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    raw = args.fixture_stdout.read_bytes()
    fixture_doc = parse_compiled_stdout(raw)
    fixture = fixture_doc["scripted_definition_layout_fixture"]
    cases = regression_cases(fixture)
    result = {"schema_version": 1, "status": "PASS", "case_count": len(cases), "cases": cases,
              "original_compiled_stdout": {"path": str(args.fixture_stdout), "bytes": len(raw),
                                           "sha256": hashlib.sha256(raw).hexdigest().upper()},
              "evaluator": {"path": str(Path(__file__).resolve()),
                            "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest().upper()},
              "OFFLINE_ABI_FIXTURE_NOT_GAME_TRUTH": True,
              "old_runtime_backfill": False, "global_mutable_bundle_complete": False}
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(json.dumps({"path": str(args.output), "bytes": args.output.stat().st_size,
                      "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest().upper(),
                      "case_count": len(cases), "status": "PASS"}))


if __name__ == "__main__":
    main()
