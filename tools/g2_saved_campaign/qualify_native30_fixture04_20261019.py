"""Separately admitted fixture repair; successful Native30 production is read-only."""
import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-native30-camera01")
ATTEMPT = ROOT / "attempt04"
COPY = ROOT / "build/native30-fixture04/camera_tracking_v1_test.cpp"
TEST = "xar_ck3_camera_tracking_v1_test"
FIXTURE = "ck3_autonomous_player/native_bridge/src/camera_tracking_v1_test.cpp"
OLD = b'std::strcpy(r.provinces[0].title_key, "b_fixture")'
NEW = b'std::memcpy(r.provinces[0].title_key, "b_fixture", sizeof("b_fixture"))'

def require(value, message):
    if not value: raise RuntimeError(message)

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

def fixture_delta(original, fixed):
    require(original.count(OLD) == 1 and original.count(NEW) == 0, "one original unsafe fixture copy")
    require(fixed == original.replace(OLD, NEW), "fixture change exceeds literal memcpy with NUL")

def rows_by_target(graph, guard):
    result = {}
    for row in graph["selected_compile_rows"]:
        output = str(guard.output_from_command(row))
        match = re.search(r"CMakeFiles[\\/]([^\\/]+)\.dir", output)
        require(match, "selected compiler target absent")
        target = match.group(1)
        key = (target, os.path.normcase(str(Path(row["file"]).resolve())))
        require(key not in result, "duplicate selected source")
        result[key] = row
    return result

def argv(row, guard):
    return row.get("arguments") or guard.windows_argv(row["command"])

def exact_graph_delta(before, after, guard, old_source, new_source):
    require(before["link_contract"] == after["link_contract"], "link/archive/artifact contract changed")
    left, right = rows_by_target(before, guard), rows_by_target(after, guard)
    old_key = (TEST, os.path.normcase(str(Path(old_source).resolve())))
    new_key = (TEST, os.path.normcase(str(Path(new_source).resolve())))
    require(old_key in left and new_key in right and new_key not in left and old_key not in right,
            "exactly one test source replacement required")
    require(set(left) - {old_key} == set(right) - {new_key}, "other selected source changed")
    for key in set(left) - {old_key}:
        require(argv(left[key], guard) == argv(right[key], guard), "unadmitted compile argv change: " + repr(key))
    old_args, new_args = argv(left[old_key], guard), argv(right[new_key], guard)
    old_out, new_out = str(guard.output_from_command(left[old_key])), str(guard.output_from_command(right[new_key]))
    old_file, new_file = str(left[old_key]["file"]), str(right[new_key]["file"])
    def normalize(arguments, source, output):
        canonical = lambda value: os.path.normcase(value.replace("\\", "/"))
        result = []
        for value in arguments:
            if canonical(value) == canonical(source): result.append("$FIXTURE_SOURCE")
            elif value[:3].lower() in ("/fo", "-fo") and canonical(value[3:]) == canonical(output):
                result.append(value[:3] + "$FIXTURE_OBJECT")
            else: result.append(value)
        return result
    require(normalize(old_args, old_file, old_out) == normalize(new_args, new_file, new_out),
            "fixture flags/includes/tool changed beyond source/object paths")
    return {"selected_commands": len(left), "production_and_other_fixture_argv_identical": True,
            "old_fixture_argv": old_args, "new_fixture_argv": new_args}

def production_rows(graph, guard, production):
    return [row for (target, _), row in rows_by_target(graph, guard).items() if target in production]

def validate_card(base, card, plan, args):
    require(card["status"] == "ADMITTED" and card["machine_id"] == base.machine(), "same-machine ADMITTED card")
    require(Path(card["root"]).resolve() == ROOT.resolve() and
            Path(card["attempt_root"]).resolve() == ATTEMPT.resolve(), "exact aggregate/attempt04 roots")
    require(not ATTEMPT.exists() and not COPY.parent.exists(), "new attempt/copy must be absent; no replay")
    require(card["hard_bytes"] == 1610612736 and card["source_charge_cap_bytes"] == 100663296 and
            type(card["jobs"]) is int and 1 <= card["jobs"] <= 4, "aggregate cap/source96/jobs")
    require(card["aggregate_includes_prior_retained"] is True and card["prior_retained_allocation_bytes"] == 659564464
            and card["new_reservation_bytes"] == 0, "retained attempt02 is included without a second reservation")
    require(card["source_commit"] == "704bdd3362bdc282ed5f5f8cf31fd3f50b90d747", "unchanged original source commit")
    require(card["producer_sha256"] == base.digest(Path(__file__)) and card["plan_sha256"] == base.digest(args.plan),
            "new producer/plan pins")
    require(base.digest(args.admission) == args.admission_sha256, "new exact admission SHA")
    require(card["minimum_free_bytes"] >= 2*1024**3 and card["quota_remaining_bytes"] >= card["hard_bytes"], "fresh floor/quota")
    require(datetime.fromisoformat(card["deadline_utc"].replace("Z", "+00:00")) > datetime.now(timezone.utc), "card expired")
    commit = card["implementation_commit"]
    require(re.fullmatch(r"[0-9a-f]{40}", commit), "full implementation commit")
    for relative in list(plan["helper_pins"]) + [Path(__file__).resolve().relative_to(REPO).as_posix(),
                                               args.plan.resolve().relative_to(REPO).as_posix()]:
        require(hashlib.sha256(base.git("show", commit + ":" + relative)).hexdigest() == base.digest(REPO / relative),
                "implementation commit mismatch: " + relative)

def prior_output_boundary(relative, size, mtime, index, start, end):
    previous = index.get(relative.replace("\\", "/"))
    require(previous is not None and previous["eof"] == size, "output does not match the prior closed inventory")
    require(start-1 <= mtime <= end+1, "output write time is outside the successful production window")

def link_without_pdb(command):
    flags = re.findall(r'(?i)(?:^|\s)/(out|pdb|debug|debugtype|incremental)(?::([^\s"]+))?(?=\s|"|$)', command)
    values = {}
    for key, value in flags: values.setdefault(key.lower(), []).append(value.lower())
    require(values.get("out") == ["xar_ck3_bridge.dll"] and values.get("pdb") == ["xar_ck3_bridge.pdb"],
            "exact historical DLL/PDB link options required")
    require(not values.get("debug") and not values.get("debugtype"), "debug option contradicts known no-PDB output")
    require(values.get("incremental") and all(value == "no" for value in values["incremental"]),
            "historical nonincremental link required")
    return values

def closed_link_proof(base, path):
    matches = []
    with Path(path).open("rb") as stream:
        for number, raw in enumerate(stream, 1):
            require(number <= 10000 and len(raw) <= 131072, "finite closed command metadata bound")
            text = raw.decode("utf-8")
            if re.search(r'(?i)(?:^|\s)/out:xar_ck3_bridge\.dll(?=\s|"|$)', text):
                matches.append({"line": number, "line_sha256": hashlib.sha256(raw).hexdigest(),
                    "line_bytes": len(raw), "link_options": link_without_pdb(text)})
    require(len(matches) == 1, "exactly one historical bridge link command required")
    return {"source_log": base.pin(path), **matches[0]}

def classify_artifact(target, relative, exists, prior_present, link_proof):
    if target == "xar_ck3_bridge" and relative == "xar_ck3_bridge.pdb":
        require(not exists and not prior_present, "known predicted PDB was actually generated")
        require(link_proof.get("line_sha256") and link_proof["link_options"].get("pdb") == [relative],
                "predicted PDB lacks actual historical no-debug link proof")
        require(not link_proof["link_options"].get("debug") and not link_proof["link_options"].get("debugtype"),
                "PDB cannot be absent under a debug link contract")
        return "known_not_generated"
    require(exists, "required production artifact absent: " + target + ":" + relative)
    return "required"

def checked_artifact_path(base, build, relative):
    path = (build / relative).resolve()
    require(base.inside(path, build), "FileAPI artifact outside build: " + str(path))
    return path

def retain_outputs(base, files, paths, handles, prior_index, start, end):
    import win32file
    class Identity(ctypes.Structure):
        _fields_ = [("volume", ctypes.c_uint64), ("value", ctypes.c_ubyte * 16)]
    result = []
    for path in paths:
        path = Path(path).resolve()
        require(base.inside(path, ROOT / "build") and path.is_file(), "production output outside build or absent: " + str(path))
        handle = win32file.CreateFile(str(path), 0x80000000, 1, None, 3, 0x80, None)
        handles.append(handle)
        identity = Identity()
        require(files.k.GetFileInformationByHandleEx(int(handle), 18, ctypes.byref(identity), ctypes.sizeof(identity)),
                "production FileID unavailable")
        pinned = base.pin(path)
        prior_output_boundary(path.relative_to(ROOT).as_posix(), pinned["bytes"], path.stat().st_mtime,
                              prior_index, start, end)
        result.append({**pinned, "file_id": {"volume_serial": str(identity.volume),
            "file_id": bytes(identity.value).hex()}, "held_share_read_only": True})
    return result

def assert_no_work(text):
    require(text.strip() == "ninja: no work to do.", "successful production would be rebuilt; stop before fixtures")

def final_artifacts(base, resume, guard_module, plan, graph, run, tools, build, source):
    dll, archive, map_file = (build / plan[key] for key in ("dll_artifact", "runtime_artifact", "map_artifact"))
    exports_log = ATTEMPT / "exports.log"
    run([tools["dumpbin"], "/exports", str(dll)], ROOT, exports_log)
    exports = re.findall(r"^\s*\d+\s+[0-9A-F]+\s+([0-9A-F]{8})\s+(\w+)\s*$", exports_log.read_text(), re.M)
    require(sorted(name for _, name in exports) == sorted(plan["exports"]), "five exports changed")
    symbols = plan["required_map_symbols"] + ["?BindImage@player_heir_candidate_v1@ck3_12004"]
    require(all(value in map_file.read_text() for value in symbols), "required component symbol missing")
    member_log = ATTEMPT / "runtime-members.log"
    run([tools["lib"], "/LIST", str(archive)], ROOT, member_log)
    require(all(value in member_log.read_text() for value in plan["required_runtime_members"]), "component member absent")
    payloads, components = resume.archive_payloads(archive), []
    for relative in plan["required_sources"]["xar_ck3_12002_runtime"]:
        path = (source / relative).resolve()
        rows = [row for row in production_rows(graph, guard_module, ["xar_ck3_12002_runtime"])
                if Path(row["file"]).resolve() == path]
        require(len(rows) == 1, "one production component object")
        output = guard_module.output_from_command(rows[0])
        output = output if output.is_absolute() else Path(rows[0]["directory"]) / output
        pinned = base.pin(output)
        match = [row for row in payloads if Path(row["name"]).name.lower() == output.name.lower()]
        require(len(match) == 1 and match[0]["bytes"] == pinned["bytes"] and match[0]["sha256"] == pinned["sha256"],
                "component archive is not the unique already-clean object payload")
        components.append({"source": base.pin(path), "object": pinned, "payload": match[0]})
    require(not list(build.rglob("*.pdb")) and not list(build.rglob("*.ilk")), "whole build no-PDB/ILK guard")
    return {"DLL": base.pin(dll), "runtime_archive": base.pin(archive), "map": base.pin(map_file),
            "exports": exports, "component_objects": components, "deployed": False,
            "actual_Game_provider_or_camera_qualification": "NOTRUN"}

def execute(args):
    import win32file
    handles = []
    try:
        handles.append(win32file.CreateFile(str(args.plan), 0x80000000, 1, None, 3, 0x80, None))
        repair = json.loads(args.plan.read_bytes())
        for relative, expected in repair["helper_pins"].items():
            path = REPO / relative
            handles.append(win32file.CreateFile(str(path), 0x80000000, 1, None, 3, 0x80, None))
            require(hashlib.sha256(path.read_bytes()).hexdigest() == expected, "qualification helper changed")
        resume = load_module("native30_frozen_resume04", HERE / "build_native30_resume_20261019.py")
        guard_module = load_module("native30_frozen_guard04", HERE / "native30_resume_guard_20261019.py")
        auxiliary = load_module("native30_frozen_aux04", HERE / "native30_msvc_auxiliary_policy_20261019.py")
        base = guard_module.baseline()
        card = base.load(args.admission)
        validate_card(base, card, repair, args)
        for row in repair["prior_pins"]:
            require(base.digest(row["path"]) == row["sha256"], "prior completed/failed evidence changed")
        previous = base.load(ROOT / "attempt02/RESULT.json")
        require(previous["status"] == "FAILED" and previous["error"]["text"] == "original command exit 1"
                and previous["owned_active_after"] == 0 and previous["future_writes"] == 0, "different prior failure")
        successful = [row for row in previous["phases"] if "--target" in row["argv"] and
            row["argv"][row["argv"].index("--target")+1:] == base.PRODUCTION]
        require(len(successful) == 1 and successful[0]["returncode"] == 0 and successful[0]["owned_active_after"] == 0,
                "three production targets were not previously root0/Job0")
        old_plan = base.load(guard_module.PLAN)
        source, build = ROOT / "source" / guard_module.NATIVE, ROOT / "build"
        base.read_macro_contract(old_plan, source)
        rows = base.load(ROOT / "evidence/source-freeze.json")["files"]
        require([(row["path"], row["git_blob"], row["bytes"]) for row in rows] == base.tree_entries(card["source_commit"]),
                "original exact Git blob tree changed")
        base.source_intact(ROOT, rows)
        fixed = (REPO / FIXTURE).read_bytes()
        fixture_delta((ROOT / "source" / FIXTURE).read_bytes(), fixed)
        before = base.load(ROOT / "attempt02/selected-fileapi-graph.json")
        for target in before["targets"]:
            require(base.digest(target["fileapi"]["path"]) == target["fileapi"]["sha256"], "production configuration changed")
        before["link_contract"] = resume.link_contract(base, before)
        targets = base.PRODUCTION + [row["target"] for row in old_plan["fixtures"]]
        current = base.graph(build, source, targets, old_plan["required_target_defines"],
            old_plan["allowed_system_roots"], old_plan["required_source_defines"], old_plan["assertion_targets"])
        require(current["selected_compile_rows"] == before["selected_compile_rows"], "actual pre-reuse compile commands differ")
        old_inventory = base.load(REPO / repair["inventory"])
        for row in old_inventory["tool_pins"].values(): require(base.digest(row["path"]) == row["sha256"], "tool changed")
        for row in old_inventory["MSVC_script_review"]: require(base.digest(row["path"]) == row["sha256"], "MSVC script changed")
        tools = {key: row["path"] for key, row in old_inventory["tool_pins"].items()}
        binding = auxiliary.bind_auxiliaries(tools["cl"])
        expected = base.load(REPO / repair["binding"])["binding"]
        require(auxiliary.same_image(binding["compiler"], expected["compiler"]), "compiler FileID/SHA changed")
        require(all(auxiliary.same_image(value, expected["auxiliaries"][key])
                    for key, value in binding["auxiliaries"].items()), "auxiliary FileID/SHA changed")
        budget = base.Guard(ROOT, card, base.FileAPI())
        budget(256*base.MIB)
        require(not list(build.rglob("*.pdb")) and not list(build.rglob("*.ilk")), "pre-reuse no-PDB/ILK guard")
        production = production_rows(before, guard_module, base.PRODUCTION)
        outputs = []
        for row in production:
            path = guard_module.output_from_command(row)
            outputs.append(path if path.is_absolute() else Path(row["directory"]) / path)
        prior_manifest = ROOT / "attempt02/FILES-CLOSED.json"
        require(prior_manifest.stat().st_size <= 2*1024**2, "finite prior inventory metadata bound")
        previous_rows = base.load(prior_manifest)["files_before_this_manifest"]["files"]
        require(len(previous_rows) <= 30000, "prior inventory row cap")
        prior_index = {row["path"].replace("\\", "/"): row for row in previous_rows}
        require(len(prior_index) == len(previous_rows), "duplicate prior inventory name")
        link_proof = closed_link_proof(base, ROOT / "attempt02/actual-generated-commands.log")
        artifacts = [build / old_plan[key] for key in ("dll_artifact", "runtime_artifact", "map_artifact")]
        known_not_generated = []
        for target in before["targets"]:
            if target["name"] in base.PRODUCTION:
                for row in base.load(target["fileapi"]["path"]).get("artifacts", []):
                    path = checked_artifact_path(base, build, row["path"])
                    relative = path.relative_to(build).as_posix()
                    prior_key = path.relative_to(ROOT).as_posix()
                    role = classify_artifact(target["name"], relative, path.is_file(), prior_key in prior_index, link_proof)
                    if role == "required": artifacts.append(path)
                    else: known_not_generated.append({"target": target["name"], "path": str(path), "role": role,
                        "observed_absent": True, "prior_closed_inventory_absent": True,
                        "FileAPI_prediction": target["fileapi"], "actual_link": link_proof})
        outputs = sorted(set(path.resolve() for path in outputs + artifacts))
        start = datetime.fromisoformat(successful[0]["start_utc"]).timestamp()
        end = datetime.fromisoformat(successful[0]["end_utc"]).timestamp()
        pinned_outputs = retain_outputs(base, auxiliary.WindowsFiles(), outputs, handles, prior_index, start, end)
        source_identities = [{"source": base.pin(row["file"]),
            "argv_sha256": hashlib.sha256(json.dumps(argv(row, guard_module), ensure_ascii=False).encode()).hexdigest(),
            "output": str(guard_module.output_from_command(row))} for row in production]
        protected = [base.pin(path) for parent in (ROOT / "evidence", ROOT / "attempt02")
                     for path in parent.rglob("*") if path.is_file()]
        flags = resume.cache_flags(build / "CMakeCache.txt")
        ATTEMPT.mkdir(exist_ok=False)
        result = {"schema": "native30-fixture04-result-v1", "machine_id": card["machine_id"],
            "start_utc": base.utc(), "status": "FAILED", "phases": [], "command_attempts": [],
            "admission": base.pin(args.admission), "plan": base.pin(args.plan), "Game_calls": 0,
            "production_recompiled": False, "DLL_loaded": False, "known_not_generated": known_not_generated}
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1", GIT_CEILING_DIRECTORIES=str(ROOT / "source"))
        for name in ("CL", "_CL_", "LINK", "CMAKE_BUILD_PARALLEL_LEVEL"): environment.pop(name, None)
        temporary = ATTEMPT / ".msvc-temp/environment"
        temporary.mkdir(parents=True)
        environment.update(TEMP=str(temporary), TMP=str(temporary))
        def run(command, cwd, log, timeout=1800):
            state = {}
            result["command_attempts"].append(state)
            phase = auxiliary.run_owned(base, command, cwd, environment, log, budget, binding, timeout=timeout, state=state)
            result["phases"].append(phase)
            return phase
        try:
            base.write(ATTEMPT / "reused-production.json", {"prior_result": base.pin(ROOT / "attempt02/RESULT.json"),
                "source_commit": card["source_commit"], "compile_rows": source_identities, "outputs": pinned_outputs,
                "original_graph": base.pin(ROOT / "attempt02/selected-fileapi-graph.json"),
                "known_not_generated": known_not_generated})
            COPY.parent.mkdir(exist_ok=False)
            with COPY.open("xb") as output: output.write(fixed)
            handles.append(win32file.CreateFile(str(COPY), 0x80000000, 1, None, 3, 0x80, None))
            overlay = ATTEMPT / "fixture-only-override.cmake"
            with overlay.open("xb") as output: output.write((REPO / repair["overlay"]).read_bytes())
            common = [sys.executable, "-B", str(ROOT / "source/tools/run_native_msvc.py"), "--source-dir", str(source),
                "--build-dir", str(build), "--configuration", "Release", "--jobs", str(card["jobs"]),
                "--defender-external-candidate", "native30-fixture04"]
            stage = ATTEMPT / "configure"
            stage.mkdir()
            run(common + ["--evidence-dir", str(stage), "--configure", "--cmake-define", "CMAKE_PROJECT_INCLUDE=" + str(overlay)],
                ROOT, stage / "producer.log")
            base.temp_closed(build, stage)
            require(resume.cache_flags(build / "CMakeCache.txt") == flags, "XAR/options/Release changed")
            after = base.graph(build, source, targets, old_plan["required_target_defines"], old_plan["allowed_system_roots"],
                old_plan["required_source_defines"], old_plan["assertion_targets"])
            after["link_contract"] = resume.link_contract(base, after)
            comparison = exact_graph_delta(before, after, guard_module, ROOT / "source" / FIXTURE, COPY)
            base.write(ATTEMPT / "only-fixture-graph-delta.json", comparison)
            dry = ATTEMPT / "production-no-work.log"
            run([tools["ninja"], "-C", str(build), "-n", *base.PRODUCTION], ROOT, dry)
            text = dry.read_text().splitlines()
            assert_no_work("\n".join(line for line in text if not line.startswith("ninja: Entering directory")))
            for number, fixture in enumerate(old_plan["fixtures"], 1):
                budget(256*base.MIB)
                base.source_intact(ROOT, rows)
                require(base.digest(COPY) == hashlib.sha256(fixed).hexdigest(), "fixed generated fixture changed")
                stage = ATTEMPT / ("fixture-%02d" % number)
                stage.mkdir()
                run(common + ["--evidence-dir", str(stage), "--build", "--target", fixture["target"]], ROOT, stage / "producer.log")
                base.temp_closed(build, stage)
                sys.path.insert(0, str(ROOT / "source/tools"))
                import register_project_exe_exclusions as defender
                manifest, receipt = stage / "project-exe-manifest.json", stage / "project-exe-receipt.json"
                base.write(manifest, defender.collect_manifest(REPO, source, build, "Release", [fixture["target"]], "native30-fixture04"))
                run([sys.executable, "-B", str(ROOT / "source/tools/register_project_exe_exclusions.py"), "--manifest", str(manifest),
                     "--receipt", str(receipt)], ROOT, stage / "registration.log", timeout=240)
                registered, image = base.load(receipt), (build / fixture["artifact"]).resolve()
                verified = {os.path.normcase(str(Path(path).resolve())) for path in registered.get("verified_requested_paths", [])}
                require(registered.get("status") == "verified" and base.inside(image, build) and image.is_file()
                        and os.path.normcase(str(image)) in verified, "exact fixture Defender readback missing")
                arguments = [value.replace("$MACHINE_ID", card["machine_id"]).replace("$OBSERVED_UTC", base.utc())
                             for value in fixture.get("args", [])]
                run([str(image), *arguments], build, stage / "fixture.log", timeout=120)
                if fixture.get("postcheck"):
                    require(fixture["postcheck"] in base.TOOLS, "postchecker outside frozen tools")
                    run([sys.executable, "-B", str(ROOT / "source" / fixture["postcheck"]), str(stage / "fixture.log")],
                        ROOT, stage / "postcheck.log")
            capture = temporary / "actual-ninja-deps.txt"
            run([tools["ninja"], "-C", str(build), "-t", "deps"], ROOT, capture)
            base.write(ATTEMPT / "actual-dependencies.json", base.dependencies(build, capture, source, old_plan["allowed_system_roots"]))
            capture.unlink()
            delivery = final_artifacts(base, resume, guard_module, old_plan, after, run, tools, build, source)
            require(all(base.digest(row["path"]) == row["sha256"] for row in pinned_outputs), "read-only production output changed")
            require(all(base.digest(row["path"]) == row["sha256"] for row in protected), "prior failed evidence changed")
            base.source_intact(ROOT, rows)
            base.write(ATTEMPT / "production-delivery.json", {**delivery, "source_commit": card["source_commit"],
                "fixed_fixture": base.pin(COPY), "production_reused_from_attempt02": True, "prior_failures_requalified": False})
            result["status"] = "OFFLINE_QUALIFIED_NOT_DEPLOYED"
        except BaseException as error:
            result["error"] = {"type": type(error).__name__, "text": str(error)}
        finally:
            active = [row.get("owned_active_after") for row in result["command_attempts"]]
            owned_active = sum(active) if all(type(value) is int for value in active) else None
            future = 0 if owned_active == 0 else None
            result.update(end_utc=base.utc(), sampled_peak_eof=budget.peak_eof, sampled_peak_allocation=budget.peak_allocation,
                          guard_samples=budget.samples, owned_active_after=owned_active, future_writes=future)
            base.write(ATTEMPT / "RESULT.json", result)
            base.write(ATTEMPT / "FILES-CLOSED.json", {"machine_id": card["machine_id"], "utc": base.utc(),
                "files_before_this_manifest": base.inventory(ROOT, budget.api), "future_writes": future,
                "sampled_peak_is_not_continuous_peak": True, "shared_budget_root": str(ROOT)})
            closed = budget()
            print(json.dumps({"closed": base.pin(ATTEMPT / "FILES-CLOSED.json"), "aggregate_final_eof": closed["eof"],
                "aggregate_final_allocation": closed["allocation"], "future_writes": future, "owned_active_after": owned_active}))
        return 0 if result["status"] == "OFFLINE_QUALIFIED_NOT_DEPLOYED" else 1
    finally:
        for handle in handles: handle.Close()

def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--admission-sha256", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    require(os.name == "nt" and args.execute, "explicit Windows execute required")
    return execute(args)

if __name__ == "__main__": raise SystemExit(main())
