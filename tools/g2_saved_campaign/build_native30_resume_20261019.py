"""A separately admitted attempt reusing only frozen source and unbuilt configuration."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
from datetime import datetime, timezone

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-native30-camera01")
ATTEMPT = ROOT / "attempt02"
TEMP_RELATIVE = ".msvc-temp/environment"
RESTORED = {
    "XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1=1",
    "XAR_CK3_ENABLE_G2_PLAYER_RELIGION_PERSONAL_PARAMETERS_PRIVATE_QUERY_V1=1",
}

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def source_defines_only(before, after, guard):
    """All selected compile argv remain identical except two admitted source defines."""
    def indexed(graph):
        result = {}
        for row in graph["selected_compile_rows"]:
            output = str(guard.output_from_command(row))
            target = re.search(r"CMakeFiles[\\/]([^\\/]+)\.dir", output)
            if not target: raise RuntimeError("selected command target absent")
            key = (target.group(1), os.path.normcase(str(Path(row["file"]).resolve())))
            if key in result: raise RuntimeError("duplicate selected source occurrence")
            result[key] = row.get("arguments") or guard.windows_argv(row["command"])
        return result
    if before.get("link_contract") != after.get("link_contract"):
        raise RuntimeError("selected link/artifact contract changed")
    left, right = indexed(before), indexed(after)
    if left.keys() != right.keys(): raise RuntimeError("selected compile-source set changed")
    changed = []
    for key, arguments in right.items():
        is_main = key[0] == "xar_ck3_12002_runtime" and Path(key[1]).name == "ck3_12002.cpp"
        clean, removed = [], []
        for argument in arguments:
            if is_main and argument.startswith(("/D", "-D")) and argument[2:] in RESTORED:
                removed.append(argument[2:])
            else:
                clean.append(argument)
        if is_main:
            if sorted(removed) != sorted(RESTORED): raise RuntimeError("two restored source definitions not unique")
            changed.append(key)
        if clean != left[key]: raise RuntimeError("unadmitted selected compile argv change: " + repr(key))
    if len(changed) != 1: raise RuntimeError("one runtime source restoration required")
    return {"selected_commands": len(left), "only_changed_source": list(changed[0]),
            "restored_definitions": sorted(RESTORED)}

def link_contract(base, graph):
    def semantic(value):
        if isinstance(value, dict): return {key: semantic(item) for key, item in value.items() if key != "backtrace"}
        if isinstance(value, list): return [semantic(item) for item in value]
        return value
    result = {}
    for target in graph["targets"]:
        row = base.load(Path(target["fileapi"]["path"]))
        result[target["name"]] = semantic({"type": row["type"], "link": row.get("link"),
            "archive": row.get("archive"), "artifacts": row.get("artifacts", [])})
    return result

def cache_flags(path):
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([A-Za-z0-9_]+):[^=]+=(.*)", line)
        if match and (match[1].startswith("XAR_") or match[1] in ("BUILD_TESTING", "CMAKE_BUILD_TYPE")):
            result[match[1]] = match[2]
    return result

def archive_payloads(path):
    """Native26's streaming COFF payload check, with explicit size/name bounds."""
    result, long_names = [], b""
    with Path(path).open("rb") as stream:
        if stream.read(8) != b"!<arch>\n": raise RuntimeError("invalid COFF archive")
        while True:
            header = stream.read(60)
            if not header: break
            if len(header) != 60 or header[58:] != b"`\n": raise RuntimeError("invalid archive header")
            name, size = header[:16].decode("ascii").strip(), int(header[48:58])
            if not 0 <= size <= 1610612736: raise RuntimeError("archive member bound")
            digest, remaining, table = hashlib.sha256(), size, []
            while remaining:
                block = stream.read(min(remaining, 1048576))
                if not block: raise RuntimeError("truncated archive member")
                digest.update(block)
                remaining -= len(block)
                if name == "//": table.append(block)
            if name == "//": long_names = b"".join(table)
            if name not in {"/", "//", "/SYM64/"}:
                if name.startswith("/") and name[1:].isdigit():
                    offset = int(name[1:])
                    if offset >= len(long_names): raise RuntimeError("archive long-name offset")
                    payload_name = long_names[offset:].split(b"\0", 1)[0].split(b"/\n", 1)[0].decode("utf-8")
                else:
                    payload_name = name.rstrip("/")
                result.append({"name": payload_name, "bytes": size, "sha256": digest.hexdigest()})
            if size % 2 and stream.read(1) != b"\n": raise RuntimeError("archive padding")
    return result

def validate_card(base, card, plan, args):
    base.require(card["status"] == "ADMITTED" and card["machine_id"] == base.machine(), "ADMITTED same machine")
    base.require(Path(card["root"]).resolve() == ROOT.resolve() and Path(card["attempt_root"]).resolve() == ATTEMPT.resolve(),
                 "exact shared budget/unique attempt roots")
    base.require(not ATTEMPT.exists(), "new attempt must be absent; no replay")
    base.require(card["hard_bytes"] == 1610612736 and card["source_charge_cap_bytes"] == 100663296 and
                 type(card["jobs"]) is int and 1 <= card["jobs"] <= 4, "aggregate 1.5GiB/source96/jobs contract")
    base.require(card["source_commit"] == "704bdd3362bdc282ed5f5f8cf31fd3f50b90d747", "exact frozen Native commit")
    base.require(card["aggregate_includes_prior_retained"] is True and
                 card["prior_retained_allocation_bytes"] == 117360240 and card["new_reservation_bytes"] == 0,
                 "same aggregate hold includes old retained allocation")
    base.require(card["producer_sha256"] == base.digest(Path(__file__)) and
                 card["plan_sha256"] == base.digest(args.plan), "new producer/plan pins")
    base.require(base.digest(ROOT / "evidence/FILES-CLOSED.json") == plan["prior_closed_sha256"], "prior failure immutable")
    base.require(card["minimum_free_bytes"] >= 2*1024**3 and card["quota_remaining_bytes"] >= card["hard_bytes"],
                 "fresh global floor and quota")
    base.require(datetime.fromisoformat(card["deadline_utc"].replace("Z", "+00:00")) > datetime.now(timezone.utc),
                 "admission expired")
    base.require(base.digest(args.admission) == args.admission_sha256, "new admission SHA")
    implementation = card["implementation_commit"]
    base.require(re.fullmatch(r"[0-9a-f]{40}", implementation), "full implementation Git commit")
    code_paths = list(plan["helper_pins"]) + [Path(__file__).resolve().relative_to(REPO).as_posix(),
                                             args.plan.resolve().relative_to(REPO).as_posix()]
    for relative in code_paths:
        body = base.git("show", implementation + ":" + relative)
        base.require(hashlib.sha256(body).hexdigest() == base.digest(REPO / relative),
                     "implementation commit/source mismatch: " + relative)

def execute(args):
    # Importing the old module is only reuse of its pure guards and low-level Job;
    # its execute/mkdir path is never called or monkey-patched.
    import win32file
    leases = []
    try:
        leases.append(win32file.CreateFile(str(args.plan), 0x80000000, 1, None, 3, 0x80, None))
        repair = json.loads(args.plan.read_bytes())
        for name, expected in repair["helper_pins"].items():
            path = REPO / name
            handle = win32file.CreateFile(str(path), 0x80000000, 1, None, 3, 0x80, None)
            leases.append(handle)
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected: raise RuntimeError("repair helper changed")
        guard_module = load_module("native30_resume_guard_runtime", HERE / "native30_resume_guard_20261019.py")
        auxiliary = load_module("native30_auxiliary_runtime", HERE / "native30_msvc_auxiliary_policy_20261019.py")
        base = guard_module.baseline()
        card = base.load(args.admission)
        validate_card(base, card, repair, args)
        old_plan = base.load(guard_module.PLAN)
        source, build = ROOT / "source" / guard_module.NATIVE, ROOT / "build"
        base.read_macro_contract(old_plan, source)
        base.require(base.digest(REPO / repair["inventory"]["path"]) == repair["inventory"]["sha256"], "inventory proof pin")
        inventory = base.load(REPO / repair["inventory"]["path"])
        for name in ("cache", "ninja", "compile_commands"):
            row = inventory[name]
            base.require(base.digest(row["path"]) == row["sha256"], "preexisting configuration changed")
        for row in inventory["target_fileapi"]:
            base.require(base.digest(row["path"]) == row["sha256"], "preexisting target graph changed")
        old_graph_defines = {key: [value for value in values if not
            (key == "xar_ck3_12002_runtime:src/ck3_12002.cpp" and value in RESTORED)]
            for key, values in old_plan["required_source_defines"].items()}
        targets = base.PRODUCTION + [row["target"] for row in old_plan["fixtures"]]
        before_graph = base.graph(build, source, targets, old_plan["required_target_defines"],
            old_plan["allowed_system_roots"], old_graph_defines, old_plan["assertion_targets"])
        before_graph["link_contract"] = link_contract(base, before_graph)
        guard_module.zero_selected_outputs(base, before_graph, build)
        protected = [base.pin(path) for path in (ROOT / "evidence").rglob("*") if path.is_file()]
        freeze = base.load(ROOT / "evidence/source-freeze.json")
        rows = freeze["files"]
        base.require(freeze["commit"] == card["source_commit"] and
            [(row["path"], row["git_blob"], row["bytes"]) for row in rows] == base.tree_entries(card["source_commit"]),
            "same exact frozen Git blob tree")
        base.source_intact(ROOT, rows)
        for row in inventory["tool_pins"].values():
            base.require(base.digest(row["path"]) == row["sha256"], "qualified tool changed")
        for row in inventory["MSVC_script_review"]:
            base.require(base.digest(row["path"]) == row["sha256"], "MSVC environment script changed")
        tools = {name: row["path"] for name, row in inventory["tool_pins"].items()}
        binding = auxiliary.bind_auxiliaries(tools["cl"])
        reference = repair["auxiliary_binding"]
        base.require(base.digest(REPO / reference["path"]) == reference["sha256"], "auxiliary binding proof pin")
        expected_binding = base.load(REPO / reference["path"])["binding"]
        base.require(auxiliary.same_image(binding["compiler"], expected_binding["compiler"]), "compiler binding changed")
        for name, identity in binding["auxiliaries"].items():
            base.require(identity["sha256"] == inventory["tool_pins"][Path(name).stem]["sha256"] and
                auxiliary.same_image(identity, expected_binding["auxiliaries"][name]), "exact auxiliary FileID/SHA")
        flags_before = cache_flags(build / "CMakeCache.txt")
        ATTEMPT.mkdir(exist_ok=False)
        guard = base.Guard(ROOT, card, base.FileAPI())
        result = {"schema": "native30-resume-result-v1", "machine_id": card["machine_id"],
            "start_utc": base.utc(), "status": "FAILED", "phases": [], "command_attempts": [],
            "admission": base.pin(args.admission),
            "repair_plan": base.pin(args.plan), "prior_closed": base.pin(ROOT / "evidence/FILES-CLOSED.json"),
            "source_commit": card["source_commit"], "Game_calls": 0, "DLL_loaded": False,
            "auxiliary_binding": binding}
        def run(argv, cwd, log, timeout=1800):
            state = {}
            result["command_attempts"].append(state)
            row = auxiliary.run_owned(base, argv, cwd, environment, log, guard, binding, timeout=timeout, state=state)
            result["phases"].append(row)
            return row
        try:
            guard(256*base.MIB)
            prior_view = ATTEMPT / "prior-configuration-inputs"
            prior_view.mkdir()
            prior_pins = []
            for original in [build / "CMakeCache.txt"] + [Path(row["path"]) for row in inventory["target_fileapi"]]:
                copy = prior_view / original.name
                with copy.open("xb") as output: output.write(original.read_bytes())
                prior_pins.append({"original": base.pin(original), "snapshot": base.pin(copy)})
            base.write(ATTEMPT / "pre-configure-selected-graph.json", before_graph)
            base.write(ATTEMPT / "prior-configuration-snapshots.json", prior_pins)
            overlay = ATTEMPT / "runtime-source-macro-restore.cmake"
            source_overlay = REPO / repair["overlay"]["path"]
            base.require(base.digest(source_overlay) == repair["overlay"]["sha256"], "overlay source pin")
            with overlay.open("xb") as output: output.write(source_overlay.read_bytes())
            result["source_overlay"] = base.pin(overlay)
            common = [sys.executable, "-B", str(ROOT / "source/tools/run_native_msvc.py"),
                "--source-dir", str(source), "--build-dir", str(build), "--configuration", "Release",
                "--jobs", str(card["jobs"]), "--defender-external-candidate", "native30-resume02"]
            environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1",
                               GIT_CEILING_DIRECTORIES=str(ROOT / "source"))
            for name in ("CL", "_CL_", "LINK", "CMAKE_BUILD_PARALLEL_LEVEL"): environment.pop(name, None)
            temporary = ATTEMPT / TEMP_RELATIVE
            temporary.mkdir(parents=True)
            environment.update(TEMP=str(temporary), TMP=str(temporary))
            stage = ATTEMPT / "configure"
            stage.mkdir()
            # This reconfigure restores two audited source definitions, not a
            # probe-only optimization. No try_compile override or option loss.
            run(common + ["--evidence-dir", str(stage), "--configure", "--cmake-define",
                "CMAKE_PROJECT_INCLUDE=" + str(overlay)], ROOT, stage / "producer.log")
            base.temp_closed(build, stage)
            base.require(cache_flags(build / "CMakeCache.txt") == flags_before, "XAR/options configuration changed")
            qualified, graph, _, _, _ = guard_module.preflight()
            graph["link_contract"] = link_contract(base, graph)
            result["source_define_comparison"] = source_defines_only(before_graph, graph, guard_module)
            base.write(ATTEMPT / "selected-fileapi-graph.json", graph)
            base.write(ATTEMPT / "post-configure-qualification.json", qualified)
            run([tools["ninja"], "-C", str(build), "-t", "commands", *targets],
                ROOT, ATTEMPT / "actual-generated-commands.log")
            for number, selected in enumerate([base.PRODUCTION] + [[row["target"]] for row in old_plan["fixtures"]]):
                guard(256*base.MIB)
                stage = ATTEMPT / ("phase-%02d" % number)
                stage.mkdir()
                base.source_intact(ROOT, rows)
                for row in inventory["tool_pins"].values():
                    base.require(base.digest(row["path"]) == row["sha256"], "tool changed between phases")
                run(common + ["--evidence-dir", str(stage), "--build", "--target", *selected],
                    ROOT, stage / "producer.log")
                base.temp_closed(build, stage)
                if number:
                    sys.path.insert(0, str(ROOT / "source/tools"))
                    import register_project_exe_exclusions as defender
                    manifest, receipt = stage / "project-exe-manifest.json", stage / "project-exe-receipt.json"
                    base.write(manifest, defender.collect_manifest(REPO, source, build, "Release", selected, "native30-resume02"))
                    run([sys.executable, "-B", str(ROOT / "source/tools/register_project_exe_exclusions.py"),
                        "--manifest", str(manifest), "--receipt", str(receipt)],
                        ROOT, stage / "registration.log", timeout=240)
                    verified = base.load(receipt)
                    fixture = old_plan["fixtures"][number - 1]
                    image = (build / fixture["artifact"]).resolve()
                    paths = {os.path.normcase(str(Path(value).resolve())) for value in verified.get("verified_requested_paths", [])}
                    base.require(verified.get("status") == "verified" and base.inside(image, build) and image.is_file()
                        and os.path.normcase(str(image)) in paths, "exact fixture EXE Defender readback unavailable")
                    arguments = [value.replace("$MACHINE_ID", card["machine_id"]).replace("$OBSERVED_UTC", base.utc())
                                 for value in fixture.get("args", [])]
                    run([str(image), *arguments], build, stage / "fixture.log", timeout=120)
                    if fixture.get("postcheck"):
                        base.require(fixture["postcheck"] in base.TOOLS, "postchecker outside frozen inputs")
                        run([sys.executable, "-B", str(ROOT / "source" / fixture["postcheck"]), str(stage / "fixture.log")],
                            ROOT, stage / "postcheck.log")
            capture = temporary / "actual-ninja-deps.txt"
            run([tools["ninja"], "-C", str(build), "-t", "deps"], ROOT, capture)
            base.write(ATTEMPT / "actual-dependencies.json",
                       base.dependencies(build, capture, source, old_plan["allowed_system_roots"]))
            capture.unlink()  # Exact reproducible successful derivative only.
            dll, archive, map_file = (build / old_plan[key] for key in ("dll_artifact", "runtime_artifact", "map_artifact"))
            export_log, member_log = ATTEMPT / "exports.log", ATTEMPT / "runtime-members.log"
            run([tools["dumpbin"], "/exports", str(dll)], ROOT, export_log)
            exports = re.findall(r"^\s*\d+\s+[0-9A-F]+\s+([0-9A-F]{8})\s+(\w+)\s*$",
                                 export_log.read_text(encoding="utf-8"), re.M)
            base.require(sorted(name for _, name in exports) == sorted(old_plan["exports"]), "five exports changed")
            base.require(all(value in map_file.read_text(encoding="utf-8")
                             for value in old_plan["required_map_symbols"]), "required component missing from map")
            run([tools["lib"], "/LIST", str(archive)], ROOT, member_log)
            members = member_log.read_text(encoding="utf-8")
            base.require(all(value in members for value in old_plan["required_runtime_members"]), "component archive member absent")
            payloads, component_objects = archive_payloads(archive), []
            for relative in old_plan["required_sources"]["xar_ck3_12002_runtime"]:
                source_path = (source / relative).resolve()
                occurrences = [row for row in graph["selected_compile_rows"] if Path(row["file"]).resolve() == source_path
                    and "CMakeFiles/xar_ck3_12002_runtime.dir" in str(guard_module.output_from_command(row)).replace("\\", "/")]
                base.require(len(occurrences) == 1, "one fresh runtime component object")
                object_path = guard_module.output_from_command(occurrences[0])
                object_path = object_path if object_path.is_absolute() else Path(occurrences[0]["directory"]) / object_path
                matches = [row for row in payloads if Path(row["name"]).name.lower() == object_path.name.lower()]
                object_pin = base.pin(object_path)
                base.require(len(matches) == 1 and matches[0]["sha256"] == object_pin["sha256"] and
                    matches[0]["bytes"] == object_pin["bytes"], "runtime archive payload not the fresh object exactly once")
                component_objects.append({"source": base.pin(source_path), "object": object_pin, "archive_payload": matches[0]})
            base.require(all(value in map_file.read_text(encoding="utf-8")
                             for value in repair["additional_map_symbols"]), "additional component symbol absent")
            base.source_intact(ROOT, rows)
            base.require(all(base.digest(row["path"]) == row["sha256"] for row in protected),
                         "original failed evidence changed")
            base.require(not list(build.rglob("*.pdb")) and not list(build.rglob("*.ilk")),
                         "original whole-build no-PDB/ILK guard")
            base.write(ATTEMPT / "production-delivery.json", {"DLL": base.pin(dll), "exports": exports,
                "map": base.pin(map_file), "runtime_archive": base.pin(archive), "source_commit": card["source_commit"],
                "source_freeze": base.pin(ROOT / "evidence/source-freeze.json"), "source_overlay": base.pin(overlay),
                "component_objects": component_objects, "deployed": False, "original_failure_requalified": False})
            result["status"] = "BUILT_FIXTURES_PASS_NOT_DEPLOYED"
        except BaseException as error:
            result["error"] = {"type": type(error).__name__, "text": str(error)}
        finally:
            active = [row.get("owned_active_after") for row in result["command_attempts"]]
            owned_active = sum(active) if all(type(value) is int for value in active) else None
            future_writes = 0 if owned_active == 0 else None
            result.update(end_utc=base.utc(), sampled_peak_eof=guard.peak_eof,
                sampled_peak_allocation=guard.peak_allocation, guard_samples=guard.samples,
                owned_active_after=owned_active, future_writes=future_writes)
            base.write(ATTEMPT / "RESULT.json", result)
            base.write(ATTEMPT / "FILES-CLOSED.json", {"machine_id": card["machine_id"], "utc": base.utc(),
                "files_before_this_manifest": base.inventory(ROOT, guard.api), "future_writes": future_writes,
                "sampled_peak_is_not_continuous_peak": True, "shared_budget_root": str(ROOT)})
            closed = guard()
            print(json.dumps({"closed": base.pin(ATTEMPT / "FILES-CLOSED.json"),
                "aggregate_final_eof": closed["eof"], "aggregate_final_allocation": closed["allocation"],
                "future_writes": future_writes, "owned_active_after": owned_active}))
        return 0 if result["status"] == "BUILT_FIXTURES_PASS_NOT_DEPLOYED" else 1
    finally:
        for handle in leases: handle.Close()

def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--admission-sha256", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute or os.name != "nt": raise RuntimeError("explicit Windows execute required")
    return execute(args)

if __name__ == "__main__": raise SystemExit(main())
