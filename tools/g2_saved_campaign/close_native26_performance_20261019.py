"""Pin the completed offline Native26 package without loading its DLL."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_native26_performance_20261019 as build


def exports(path):
    raw = Path(path).read_bytes()
    pe = struct.unpack_from("<I", raw, 0x3C)[0]
    if raw[pe:pe + 4] != b"PE\0\0": raise ValueError("invalid PE")
    count, optional_size = struct.unpack_from("<H", raw, pe + 6)[0], struct.unpack_from("<H", raw, pe + 20)[0]
    opt = pe + 24
    if struct.unpack_from("<H", raw, opt)[0] != 0x20B: raise ValueError("not PE32+")
    directory_rva, _ = struct.unpack_from("<II", raw, opt + 112)
    sections = [struct.unpack_from("<IIII", raw, opt + optional_size + index * 40 + 8) for index in range(count)]
    def offset(rva):
        for virtual_size, virtual_address, physical_size, physical_offset in sections:
            if virtual_address <= rva < virtual_address + max(virtual_size, physical_size):
                return physical_offset + rva - virtual_address
        raise ValueError("unmapped PE RVA")
    directory = offset(directory_rva)
    base, functions, names, addresses, name_rvas, ordinals = struct.unpack_from("<IIIIII", raw, directory + 16)
    named = {}
    for index in range(names):
        name_rva = struct.unpack_from("<I", raw, offset(name_rvas) + index * 4)[0]
        start = offset(name_rva)
        name = raw[start:raw.index(b"\0", start)].decode("ascii")
        ordinal = struct.unpack_from("<H", raw, offset(ordinals) + index * 2)[0]
        named[base + ordinal] = name
    return [{"ordinal": base + index, "name": named.get(base + index)} for index in range(functions)
            if struct.unpack_from("<I", raw, offset(addresses) + index * 4)[0]]


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--baseline-DLL", type=Path, required=True)
    args = parser.parse_args()
    root, admission = args.output_root, build.read(args.admission)
    actual_machine = subprocess.check_output([sys.executable, str(ROOT / "tools/ck3_live_run_id.py"), "machine"], text=True).strip()
    if actual_machine != admission["machine_id"] or build.norm(root) != build.norm(admission["approved_output_root"]):
        raise ValueError("wrong admitted machine or root")
    if (root / "FILES-CLOSED.json").exists(): raise ValueError("package already closed")
    link = build.read(root / "LINK-RESULT.json")
    compiled = build.read(root / "COMPILE-RESULT.json")
    plan = build.read(root / "INPUT-PLAN.json")
    archive = build.read(root / "ARCHIVE-RESULT.json")
    offline = build.read(root / "offline04/RESULT.json")
    if link["exit_code"] or compiled["counts"] != {"PASS": 121} or not offline["status"].startswith("PASS_"):
        raise ValueError("required actual qualification not complete")
    for name in ("build_native26_performance_20261019.py", "validate_native26_offline_20261019.py", Path(__file__).name):
        (root / ("FINAL-" + name)).write_bytes((Path(__file__).parent / name).read_bytes())
    baseline, candidate = exports(args.baseline_DLL), exports(link["DLL"]["path"])
    if baseline != candidate: raise ValueError("export names/ordinals changed")
    rows = compiled["results"]
    layout = [row for row in plan["objects"] if row["layout_consumer"]]
    observed_layout = [row for row in rows if row["unique_override_includes"][build.HEADERS[0]]]
    if len(layout) != 118 or len(observed_layout) != 118: raise ValueError("layout consumer count mismatch")
    result = {"schema": "xar.ck3.native26-build-and-offline-qualification/v1", "machine_id": actual_machine,
        "observed_at_utc": build.now(), "status": "BUILD_AND_OFFLINE_PASS_NOT_DEPLOYED",
        "source_plan": build.pin(root / "INPUT-PLAN.json"), "source_delta": build.pin(root / "SOURCE-DELTA.json"),
        "admission": build.pin(args.admission), "baseline_DLL": build.pin(args.baseline_DLL), "candidate_DLL": link["DLL"],
        "compiler": compiled["compiler"], "compile_receipt": build.pin(root / "COMPILE-RESULT.json"),
        "compile_objects": 121, "layout_consumers_all_unique_new_header": 118,
        "direct_replacements": 21, "archive_replacements": 100, "retained_archive_payloads": 512,
        "archive_payload_name_bytes_sha_multiset_exact612": archive["payload_names_and_multiset_equal_expected612"],
        "archive_internal_order_equals_rsp": archive["librarian_payload_order_equals_response"],
        "archive_order_interpretation": "librarian reordered internal members; original input rsp order preserved; identity verified by every payload SHA and name, not count alone",
        "archive_receipt": build.pin(root / "ARCHIVE-RESULT.json"), "link_receipt": build.pin(root / "LINK-RESULT.json"),
        "export_names_and_ordinals_equal_baseline": True, "exports": candidate,
        "offline_receipt": build.pin(root / "offline04/RESULT.json"),
        "offline_results": {"JSON": "nine original synthetic cases, original production bodies, actual Native26 DTO header closure; bytes equal",
            "CB": "original callback/candidate/order fixture linked to actual rebuilt declarations object and runtime archive; pass",
            "M6": "exact .4 gate and production dispatcher, original R5 argument/recorder spy; missing-recorder/suffix/execution/invalidation guards pass; no native terminal occurrence inferred"},
        "failed_attempts_retained": [build.pin(root / "PREPARATION-FAILED01.json"), *[build.pin(root / ("offline0" + str(i) + "/RESULT.json")) for i in (1, 2, 3)]],
        "failure_interpretation": ["prepare initially assumed internal librarian order; exact original612 payload identity passed after audited multiset correction",
            "offline01 broad runtime archive pulled unrelated fixture dependencies", "offline02 missed terminal executor spy declaration",
            "offline03 fixture literal lower-case SHA failed strict stock descriptor; offline04 uses original stock constants"],
        "compile_window": {key: compiled[key] for key in ("started_at_utc", "ended_at_utc", "workers", "priority", "system_cpu_logical_processors", "system_cpu_busy_fraction_during_phase")},
        "current_Game_or_Native25_changed": False, "production_DLL_loaded": False, "new_EXE_started": 0,
        "actor_gate_default": "OFF; future cold process must freshly admit actual loaded sources and shadow before adoption",
        "performance_claim": "No live adoption or timing AB. Historical source-machine unknown four-family 152844/2529581 calls and697751500ns evaluation cost are not current-machine savings or1s/day acceptance.",
        "review_at_utc": admission["parent_review_at_utc"], "allocated_bytes": None,
        "future_writes_bytes": 0, "owned_build_or_fixture_subprocesses_remaining": 0}
    build.write(root / "QUALIFICATION.json", result)
    files = [build.pin(path) | {"relative_path": str(path.relative_to(root))} for path in sorted(root.rglob("*")) if path.is_file()]
    closed = {"schema": "xar.storage.native26-files-closed/v1", "machine_id": actual_machine,
        "observed_at_utc": build.now(), "root": str(root), "files_excluding_this_manifest": files,
        "logical_bytes_excluding_manifest": sum(item["bytes"] for item in files), "allocated_bytes": None,
        "future_writes_bytes": 0, "owned_build_or_fixture_subprocesses_remaining": 0,
        "review_at_utc": admission["parent_review_at_utc"], "parent_or_child_budget_credit_released": False}
    for _ in range(12):
        encoded = json.dumps(closed, ensure_ascii=True, indent=2).encode() + b"\n"
        logical = closed["logical_bytes_excluding_manifest"] + len(encoded)
        if closed.get("logical_bytes_including_manifest") == logical: break
        closed["logical_bytes_including_manifest"] = logical
    else: raise ValueError("manifest size did not settle")
    if logical > admission["hard_total_child_peak_bytes"]: raise ValueError("child exceeds admitted hard bound")
    (root / "FILES-CLOSED.json").write_bytes(encoded)
    print(json.dumps({"qualification": build.pin(root / "QUALIFICATION.json"), "manifest": build.pin(root / "FILES-CLOSED.json"),
                      "files_including_manifest": len(files) + 1, "logical_bytes": build.occupied(root)}))


if __name__ == "__main__":
    main()
