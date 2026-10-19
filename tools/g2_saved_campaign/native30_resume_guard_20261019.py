"""Read-only qualification of the failed Native30 attempt's reusable inputs."""
import argparse
import ctypes as C
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
ROOT = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-native30-camera01")
NATIVE = "ck3_autonomous_player/native_bridge"
COMMIT = "704bdd3362bdc282ed5f5f8cf31fd3f50b90d747"
BASE_SHA = "db51b7e5b37083cf803f4b1611dd714dec197f4e0c559a688d22781f2ef07c00"
CLOSED_SHA = "5b9b052bc07c25fa55ef0c11186324257ef6b2cf099c5084eb6fdf175bdfd7c4"
PLAN = REPO / "docs/ck3-native-ai/evidence/native30-wholeclean-producer-plan-2026-10-19.json"

def baseline():
    path = REPO / "tools/g2_saved_campaign/build_native30_wholeclean_20261019.py"
    if hashlib.sha256(path.read_bytes()).hexdigest() != BASE_SHA:
        raise RuntimeError("frozen baseline producer changed")
    spec = importlib.util.spec_from_file_location("native30_frozen_guard", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def windows_argv(command):
    shell = C.WinDLL("shell32", use_last_error=True)
    shell.CommandLineToArgvW.argtypes = [C.c_wchar_p, C.POINTER(C.c_int)]
    shell.CommandLineToArgvW.restype = C.POINTER(C.c_wchar_p)
    kernel = C.WinDLL("kernel32", use_last_error=True)
    kernel.LocalFree.argtypes, kernel.LocalFree.restype = [C.c_void_p], C.c_void_p
    count = C.c_int()
    pointer = shell.CommandLineToArgvW(command, C.byref(count))
    if not pointer: raise C.WinError(C.get_last_error())
    try:
        return [pointer[i] for i in range(count.value)]
    finally:
        kernel.LocalFree(pointer)

def output_from_command(row):
    if row.get("output"): return Path(row["output"])
    arguments = row.get("arguments") or windows_argv(row["command"])
    found = []
    for index, argument in enumerate(arguments):
        if argument.lower().startswith(("/fo", "-fo")):
            found.append(argument[3:] or arguments[index + 1])
    if len(found) != 1: raise RuntimeError("one explicit compiler object output required")
    return Path(found[0])

def zero_selected_outputs(base, graph, build):
    outputs, artifacts = [], []
    for row in graph["selected_compile_rows"]:
        output = output_from_command(row)
        output = output if output.is_absolute() else Path(row["directory"]) / output
        output = output.resolve()
        match = re.search(r"CMakeFiles[\\/]([^\\/]+)\.dir", str(output))
        base.require(match and base.inside(output, build / "CMakeFiles" / (match.group(1) + ".dir")),
                     "object output outside selected target directory")
        base.require(not output.exists(), "production/fixture object already exists: " + str(output))
        outputs.append(str(output))
    forbidden = {".obj", ".o", ".lib", ".a", ".dll", ".exe", ".pdb", ".ilk"}
    for target in graph["targets"]:
        descriptor = base.load(Path(target["fileapi"]["path"]))
        for row in descriptor.get("artifacts", []):
            path = (build / row["path"]).resolve()
            base.require(base.inside(path, build) and not path.exists(), "selected artifact already exists")
            artifacts.append(str(path))
        directory = build / "CMakeFiles" / (target["name"] + ".dir")
        base.require(not any(path.is_file() and path.suffix.lower() in forbidden for path in directory.rglob("*")),
                     "compiled file in selected target directory")
    probes = []
    show_source = build / "CMakeFiles/ShowIncludes/main.c"
    show_header = build / "CMakeFiles/ShowIncludes/foo.h"
    show_valid = (show_source.is_file() and show_source.stat().st_size <= 128 and show_header.is_file()
        and show_header.stat().st_size <= 16 and [line.strip() for line in show_source.read_text().splitlines()]
        == ['#include "foo.h"', 'int main(){}'])
    for path in build.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in forbidden | {".bin"}: continue
        relative = path.relative_to(build).as_posix()
        allowed = bool(re.fullmatch(r"CMakeFiles/[0-9][0-9A-Za-z.+_-]*/CMakeDetermineCompilerABI_CXX\.bin", relative)
            or re.fullmatch(r"CMakeFiles/[0-9][0-9A-Za-z.+_-]*/CompilerIdCXX/(?:[^/]+/)*[^/]+", relative)
            or re.fullmatch(r"CMakeFiles/CMakeScratch/TryCompile-[A-Za-z0-9]+/(?:[^/]+/)*[^/]+", relative)
            or (relative == "CMakeFiles/ShowIncludes/main.obj" and show_valid))
        base.require(allowed, "unexpected old binary outside compiler probes: " + relative)
        probes.append(base.pin(path))
    return {"selected_object_outputs": len(set(outputs)), "selected_artifacts": len(artifacts),
            "all_selected_outputs_absent": True, "compiler_probes": probes,
            "show_includes_probe_sources": [base.pin(show_source), base.pin(show_header)] if show_valid else []}

def preflight():
    base = baseline()
    build, source = ROOT / "build", ROOT / "source" / NATIVE
    base.require(base.digest(ROOT / "evidence/FILES-CLOSED.json") == CLOSED_SHA, "prior closed manifest changed")
    old = base.load(ROOT / "evidence/RESULT.json")
    base.require(old["status"] == "FAILED" and old["error"]["type"] == "KeyboardInterrupt" and not old["phases"],
                 "different previous failed attempt")
    plan = base.load(PLAN)
    base.read_macro_contract(plan, source)
    freeze = base.load(ROOT / "evidence/source-freeze.json")
    rows = freeze["files"]
    entries = base.tree_entries(COMMIT)
    base.require(freeze["commit"] == COMMIT and
                 [(x["path"], x["git_blob"], x["bytes"]) for x in rows] == entries,
                 "frozen inputs differ from exact Native+four-tools Git tree")
    base.source_intact(ROOT, rows)
    selected = base.PRODUCTION + [row["target"] for row in plan["fixtures"]]
    graph = base.graph(build, source, selected, plan["required_target_defines"],
                       plan["allowed_system_roots"], plan["required_source_defines"], plan["assertion_targets"])
    actual_sources = {(target["name"], str((source / row["path"]).resolve()))
        for target in graph["targets"] for row in base.load(Path(target["fileapi"]["path"])).get("sources", [])
        if "compileGroupIndex" in row}
    for target, names in plan["required_sources"].items():
        base.require(all((target, str((source / value).resolve())) in actual_sources for value in names),
                     "required component source missing")
    empty = zero_selected_outputs(base, graph, build)
    cache = (build / "CMakeCache.txt").read_text(encoding="utf-8")
    base.require("CMAKE_BUILD_TYPE:STRING=Release" in cache, "existing production configuration is not Release")
    config = base.load(ROOT / "evidence/configure/native-msvc-result.json")
    base.require(config["configured"] and not config["built"] and config["configuration"] == "Release",
                 "old configure helper did not produce the expected configured-only state")
    paths = {**config["tools"]}
    paths.update({name: str(Path(paths["cl"]).with_name(name + ".exe"))
                  for name in ("link", "lib", "dumpbin", "vctip", "mspdbsrv")})
    tools = {name: base.pin(path) for name, path in paths.items()}
    records = {"cache": base.pin(build / "CMakeCache.txt"), "ninja": base.pin(build / "build.ninja"),
               "compile_commands": base.pin(build / "compile_commands.json"), "index": graph["index"],
               "targets": [row["fileapi"] for row in graph["targets"]]}
    result = {"schema": "native30-reuse-preflight-v1", "machine_id": old["machine_id"],
        "observed_at_utc": datetime.now(timezone.utc).isoformat(), "status": "REUSE_INPUTS_QUALIFIED_SOURCE_ONLY",
        "budget_root": str(ROOT), "protected_prior_evidence": str(ROOT / "evidence"),
        "source_commit": COMMIT, "source_files": len(rows), "source_eof_bytes": sum(row["bytes"] for row in rows),
        "source_freeze": base.pin(ROOT / "evidence/source-freeze.json"), "prior_closed": base.pin(ROOT / "evidence/FILES-CLOSED.json"),
        "graph_targets": len(graph["targets"]), "compile_rows": len(graph["selected_compile_rows"]),
        "source_count": graph["source_count"], "matched_macro_sources": graph["matched_macro_sources"],
        "configuration_inputs": records, "zero_outputs": empty, "tool_pins": tools,
        "cache_configuration_lines": [line for line in cache.splitlines() if line.startswith(("CMAKE_BUILD_TYPE:",
            "CMAKE_TRY_COMPILE_CONFIGURATION:", "CMAKE_CXX_FLAGS_DEBUG:", "CMAKE_CXX_FLAGS_RELEASE:"))],
        "future_probe_Release_is_not_applied_to_this_cache": True, "build_or_configure_started": False,
        "old_evidence_or_source_written": False, "Game_calls": 0}
    return result, graph, rows, plan, tools

def macro_delta():
    base = baseline()
    plan = base.load(PLAN)
    reply = ROOT / "build/.cmake/api/v1/reply"
    source = ROOT / "source" / NATIVE
    base.read_macro_contract(plan, source)
    differences = []
    for key, expected in plan["required_source_defines"].items():
        target, relative = key.split(":", 1)
        paths = list(reply.glob("target-" + target + "-Release-*.json"))
        base.require(len(paths) == 1, "one actual target FileAPI required")
        descriptor = base.load(paths[0])
        rows = [row for row in descriptor["sources"] if "compileGroupIndex" in row and
                (source / row["path"]).resolve() == (source / relative).resolve()]
        base.require(len(rows) == 1, "one actual source occurrence required")
        group = descriptor["compileGroups"][rows[0]["compileGroupIndex"]]
        actual = {row["define"] for row in group.get("defines", [])}
        differences.append({"key": key, "target_fileapi": base.pin(paths[0]),
            "expected_count": len(expected), "actual_count": len(actual),
            "missing": sorted(set(expected) - actual), "extra": sorted(actual - set(expected)),
            "compile_fragments": [row["fragment"] for row in group.get("compileCommandFragments", [])]})
    return {"schema": "native30-actual-source-macro-delta-v1",
        "machine_id": base.load(ROOT / "evidence/RESULT.json")["machine_id"],
        "observed_at_utc": datetime.now(timezone.utc).isoformat(), "source_commit": COMMIT,
        "prior_preflight_failure": "required source macro missing: xar_ck3_12002_runtime:src/ck3_12002.cpp",
        "differences": differences, "configure_or_build_started": False, "old_inputs_written": False}

def inventory_only():
    """Inventory with exactly two known missing macros, never execution admission."""
    base, plan = baseline(), None
    plan = base.load(PLAN)
    source, build = ROOT / "source" / NATIVE, ROOT / "build"
    base.read_macro_contract(plan, source)
    delta = macro_delta()
    key = "xar_ck3_12002_runtime:src/ck3_12002.cpp"
    missing = {"XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1=1",
               "XAR_CK3_ENABLE_G2_PLAYER_RELIGION_PERSONAL_PARAMETERS_PRIVATE_QUERY_V1=1"}
    base.require(all(set(row["missing"]) == (missing if row["key"] == key else set())
                     for row in delta["differences"]), "different macro defect; inventory exception not applicable")
    inventory_defines = {name: [value for value in values if name != key or value not in missing]
                         for name, values in plan["required_source_defines"].items()}
    graph = base.graph(build, source, base.PRODUCTION + [row["target"] for row in plan["fixtures"]],
        plan["required_target_defines"], plan["allowed_system_roots"], inventory_defines, plan["assertion_targets"])
    empty = zero_selected_outputs(base, graph, build)
    config = base.load(ROOT / "evidence/configure/native-msvc-result.json")
    tools = dict(config["tools"])
    tools.update({name: str(Path(tools["cl"]).with_name(name + ".exe"))
                  for name in ("link", "lib", "dumpbin", "vctip", "mspdbsrv")})
    script_paths = [Path(tools["vcvars64"]), Path(tools["vcvars64"]).with_name("vcvarsall.bat"),
                    Path(tools["vcvars64"]).parents[3] / "Common7/Tools/VsDevCmd.bat"]
    scripts = []
    for path in script_paths:
        base.require(path.stat().st_size <= 32768, "named MSVC script bound")
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        relevant = [line[:200] for line in text.splitlines() if any(token.lower() in line.lower()
            for token in ("vcvarsall", "VsDevCmd", "telemetry", "vctip", "mspdb", "try_compile"))]
        scripts.append({**base.pin(path), "relevant_line_total": len(relevant),
                        "relevant_lines_first8": relevant[:8], "projection_truncated": len(relevant) > 8})
    cache = (build / "CMakeCache.txt").read_text(encoding="utf-8")
    return {"schema": "native30-existing-config-inventory-only-v1", "machine_id": delta["machine_id"],
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "INVENTORY_ONLY_ORIGINAL_SOURCE_MACRO_GUARD_STILL_RED",
        "production_guard_relaxed": False, "inventory_only_known_missing_macros": sorted(missing),
        "graph_targets": len(graph["targets"]), "compile_rows": len(graph["selected_compile_rows"]),
        "source_count": graph["source_count"], "index": graph["index"],
        "target_fileapi": [row["fileapi"] for row in graph["targets"]], "zero_outputs": empty,
        "cache": base.pin(build / "CMakeCache.txt"), "ninja": base.pin(build / "build.ninja"),
        "compile_commands": base.pin(build / "compile_commands.json"),
        "tool_pins": {name: base.pin(path) for name, path in tools.items()}, "MSVC_script_review": scripts,
        "cache_configuration_lines": [line for line in cache.splitlines() if line.startswith(("CMAKE_BUILD_TYPE:",
            "CMAKE_TRY_COMPILE_CONFIGURATION:", "CMAKE_CXX_FLAGS_DEBUG:", "CMAKE_CXX_FLAGS_RELEASE:"))],
        "configure_or_build_started": False, "old_inputs_written": False}

def auxiliary_binding_only():
    base = baseline()
    policy_path = Path(__file__).with_name("native30_msvc_auxiliary_policy_20261019.py")
    spec = importlib.util.spec_from_file_location("native30_auxiliary_binding_review", policy_path)
    policy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(policy)
    inventory = base.load(REPO / "docs/ck3-native-ai/evidence/native30-existing-config-output-inventory-2026-10-19.json")
    binding = policy.bind_auxiliaries(inventory["tool_pins"]["cl"]["path"])
    prior_path = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-fresh1066-v20261019-prepare01/native30-build-owner01/owner-spec/CONFIGURE-OWNED-DIAG01.json")
    prior = base.load(prior_path)["owners"]["child"]["named_private_jobs"][0]["member_identities"]
    expected_ids = {Path(row["image"]).name.lower(): row["image_file_id"] for row in prior}
    for name, actual in binding["auxiliaries"].items():
        base.require(actual["file_id"] == expected_ids[name] and
            actual["sha256"] == inventory["tool_pins"][Path(name).stem]["sha256"], "actual auxiliary binding differs")
    return {"schema": "native30-msvc-auxiliary-file-binding-v1", "machine_id": base.machine(),
        "observed_at_utc": datetime.now(timezone.utc).isoformat(), "binding": binding,
        "prior_owned_process_evidence": base.pin(prior_path), "process_started_or_terminated": False,
        "CPlusPlus_qualification": "NOTRUN"}

def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--macro-only", action="store_true")
    parser.add_argument("--inventory-only", action="store_true")
    parser.add_argument("--bind-auxiliary-tools", action="store_true")
    args = parser.parse_args()
    if sum((args.inventory_only, args.macro_only, args.bind_auxiliary_tools)) > 1:
        parser.error("one read-only review mode at a time")
    if args.bind_auxiliary_tools:
        result = auxiliary_binding_only()
    elif args.inventory_only:
        result = inventory_only()
    elif args.macro_only:
        result = macro_delta()
    else:
        result, _, _, _, _ = preflight()
    body = json.dumps(result, indent=2).encode()
    if len(body) > 24576: raise RuntimeError("small preflight proof bound")
    with args.report.open("xb") as output: output.write(body)
    print(json.dumps({"report": str(args.report), "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
                      "status": result.get("status", result["schema"]), "compile_rows": result.get("compile_rows")}))

if __name__ == "__main__": main()
