"""One admitted Native27 attempt: one original router recipe, one offline fixture.

Never loads the production DLL, copies archives/old objects, or contacts Game.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import time

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_native26_performance_20261019 as b
from close_native26_performance_20261019 import exports

PLAN = REPO / "docs/ck3-native-ai/evidence/native27-router-registration-plan-2026-10-19.json"
PLAN_SHA = "cc6e6385ad982f911afa1f5cd135eac45d2cfb16504ad6e3fe1bf767ac9dd6bf"
ADMISSION_SHA = "8e5b6d23c97a7599eaa6dd31fc287d1da7d271675ade3900c64b9a4f38779ea7"
ROUTER = "source/src/ck3_12002_nonwar_router.cpp"
RECIPE = "build/jobs/9d165a6c1cfd/attempt01/COMPILE-RESULT.json"
OLDOBJ = "build/jobs/9d165a6c1cfd/attempt01/9d165a6c1cfd.obj"
DEPS = "build/jobs/9d165a6c1cfd/attempt01/dependencies.json"


def require(value, message):
    if not value: raise ValueError(message)


def checked(pin):
    actual = b.pin(pin["path"])
    require(actual["bytes"] == pin["bytes"] and actual["sha256"] == pin["sha256"], "pin changed: " + pin["path"])
    return actual


def coff_function_relocations(path, function):
    raw = Path(path).read_bytes()
    sections, symptr, symbols, optional = struct.unpack_from("<HIIH", raw, 2)[0], struct.unpack_from("<I", raw, 8)[0], struct.unpack_from("<I", raw, 12)[0], struct.unpack_from("<H", raw, 16)[0]
    require(optional == 0, "unexpected COFF optional header")
    strings = symptr + 18 * symbols
    names, records = {}, []
    index = 0
    while index < symbols:
        offset = symptr + index * 18
        short, value, section, kind, storage, aux = struct.unpack_from("<8sIhHBB", raw, offset)
        if short[:4] == b"\0\0\0\0":
            start = strings + struct.unpack_from("<I", short, 4)[0]
            name = raw[start:raw.index(b"\0", start)].decode("utf-8")
        else: name = short.rstrip(b"\0").decode("utf-8")
        names[index] = name
        records.append({"index": index, "name": name, "value": value, "section": section, "kind": kind, "storage": storage})
        index += 1 + aux
    matches = [row for row in records if row["name"].startswith("?" + function + "@") and row["section"] > 0]
    require(len(matches) == 1, "ambiguous/missing COFF function " + function)
    selected = matches[0]
    offset = 20 + (selected["section"] - 1) * 40
    require(selected["section"] <= sections, "COFF section overflow")
    size, ptr, relocptr = struct.unpack_from("<III", raw, offset + 16)
    count = struct.unpack_from("<H", raw, offset + 32)[0]
    relocs = []
    for i in range(count):
        address, symbol, kind = struct.unpack_from("<IIH", raw, relocptr + i * 10)
        relocs.append({"offset": address, "symbol": names[symbol], "type": kind})
    return {"function_symbol": selected["name"], "section": selected["section"], "function_value": selected["value"],
            "section_bytes": size, "section_sha256": hashlib.sha256(raw[ptr:ptr + size]).hexdigest(), "relocations": relocs}


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--admission", type=Path, required=True)
    args = parser.parse_args()
    require(b.sha(PLAN) == PLAN_SHA and PLAN.stat().st_size == 12090, "plan changed")
    require(b.sha(args.admission) == ADMISSION_SHA and args.admission.stat().st_size == 3601, "admission changed")
    plan, admission = b.read(PLAN), b.read(args.admission)
    machine = subprocess.check_output([sys.executable, "-B", str(REPO / "tools/ck3_live_run_id.py"), "machine"], text=True).strip()
    require(machine == plan["machine_id"] == admission["machine_id"], "machine mismatch")
    require(admission["status"] == "ADMITTED" and admission["hard_limit_bytes"] == 1024 ** 3, "not admitted exact1GiB")
    require(datetime.now(timezone.utc) < datetime.fromisoformat(admission["review_at_utc"]), "admission expired")
    root, old = Path(admission["approved_root"]), Path(plan["baseline_root"])
    require(b.norm(root) == b.norm(plan["proposed_new_root"]) and not root.exists(), "root must be exact and fresh")
    require(admission["source_plan"]["sha256"] == PLAN_SHA and admission["attempt_limit"] == admission["workers"] == 1, "wrong scope")
    root.mkdir()
    (root / "build").mkdir(); (root / "source/src").mkdir(parents=True)
    (root / "producer-used.py").write_bytes(Path(__file__).read_bytes())
    (root / "INPUT-PLAN.json").write_bytes(PLAN.read_bytes())
    (root / "ADMISSION.json").write_bytes(args.admission.read_bytes())
    hard, phase = admission["hard_limit_bytes"], "prepare"
    refs, windows = {}, []

    def watch(scratch=0):
        actual = b.occupied(root)
        require(actual + scratch <= hard, "child allocation/next scratch exceeds exact ceiling")
        require(not list(root.rglob("*.pdb")) and not list(root.rglob("*.ilk")), "unexpected PDB/ILK; stop")
        return actual

    def ref(pin):
        result = checked(pin)
        stat = Path(pin["path"]).stat()
        refs[b.norm(pin["path"])] = (stat.st_size, stat.st_mtime_ns)
        return result

    def unchanged():
        for path, expected in refs.items():
            stat = Path(path).stat()
            require((stat.st_size, stat.st_mtime_ns) == expected, "retained input changed: " + path)

    def run(argv, cwd, env, log, scratch=0, timeout=600):
        watch(scratch); unchanged()
        started, tick = b.now(), time.perf_counter()
        log = Path(log)
        require(not log.exists(), "single-attempt log already exists")
        with log.open("xb") as stream:
            process = subprocess.Popen(list(map(str, argv)), cwd=cwd, env=env, stdout=stream,
                stderr=subprocess.STDOUT, creationflags=b.LOW_FLAGS)
            try:
                while process.poll() is None:
                    watch()
                    if time.perf_counter() - tick > timeout: raise TimeoutError("bounded tool timeout")
                    time.sleep(0.2)
                code = process.returncode
            except BaseException:
                process.kill(); process.wait(timeout=30); raise
        result = {"argv": list(map(str, argv)), "started_at_utc": started, "ended_at_utc": b.now(),
                  "exit_code": code, "wall_seconds": time.perf_counter() - tick, "priority": "BELOW_NORMAL", "log": b.pin(log)}
        windows.append({"phase": phase, **{k: result[k] for k in ("started_at_utc", "ended_at_utc", "wall_seconds", "exit_code")}})
        b.write(log.with_suffix(".result.json"), result)
        watch()
        require(code == 0, "tool failed; first attempt retained: " + str(log))
        return result

    def newenv(env, path):
        path.mkdir(parents=True, exist_ok=True)
        child = env.copy(); child["TEMP"] = child["TMP"] = str(path)
        return child

    def compile_argv(argv, source, target, deps):
        original_source = [item for item in argv if item.lower().endswith(".cpp")]
        require(len(original_source) == 1, "source token ambiguity")
        result = []
        for i, value in enumerate(argv):
            lower = value.lower()
            if value == original_source[0]: result.append(str(source))
            elif lower.startswith("/fo"): result.append("/Fo" + str(target))
            elif lower.startswith("/fd"): result.append("/Fd" + str(target.parent / "compiler.pdb"))
            elif i and argv[i - 1].lower() == "/sourcedependencies": result.append(str(deps))
            else: result.append(value)
        require(not any(value.lower() in ("/zi", "/zi", "/z7", "/debug") for value in result), "debug prohibited")
        return result

    try:
        baseline = {}
        for relative, (size, digest) in plan["baseline_pins_relative_to_baseline_root"].items():
            baseline[relative] = ref({"path": str(old / relative), "bytes": size, "sha256": digest})
        closed = b.read(old / "FILES-CLOSED.json")
        closedpins = {b.norm(row["path"]): row for row in closed["files_excluding_this_manifest"]}
        def old_metadata(relative):
            path = old / relative
            ref(closedpins[b.norm(path)])
            return b.read(path)
        retained = old_metadata("RETAINED-INPUTS.json")
        expected = {b.norm(row["path"]): row for row in retained["direct"]}
        expected.update(closedpins)
        response = old / "build/native26-link.rsp"
        direct = [value for value in b.tokens(response) if value.lower().endswith(".obj")]
        require(len(direct) == 356, "direct count drift")
        directpins = [ref(expected[b.norm(value)]) for value in direct]
        oldplan, dependencies = b.read(old / "INPUT-PLAN.json"), b.read(old / DEPS)
        includes = dependencies["Data"]["Includes"]
        wanted = {b.norm(row["path"]): row for row in oldplan["frozen_project_header_versions"]}
        wanted.update({key: value for key, value in closedpins.items() if "\\source\\include\\" in key})
        project = sorted({b.norm(path) for path in includes if "xar_bridge" in b.norm(path) or "ck3_autonomous_player" in b.norm(path) or "frozen" in b.norm(path)})
        headerpins = [{"path": path, "bytes": ref(wanted[path])["bytes"], "sha256": wanted[path]["sha256"]} for path in project]
        digest = hashlib.sha256(b.canonical(headerpins)).hexdigest()
        require(len(project) == 546 and len(includes) == 799 and digest == plan["router_header_closure"]["observed_project_header_digest"], "header closure drift")
        source = (old / ROUTER).read_bytes()
        change = plan["source_change"]
        anchor = (change["after_exact_line"] + "\n").encode()
        require(source.count(anchor) == 1, "source anchor ambiguity")
        candidate = source.replace(anchor, anchor + (change["add_exact_line"] + "\n").encode())
        require(len(candidate) == change["expected_candidate_bytes"] and hashlib.sha256(candidate).hexdigest() == change["expected_candidate_sha256"], "single-line delta mismatch")
        newsource = root / ROUTER; newsource.write_bytes(candidate)
        env, tools = b.environment(root)
        cl = ref({"path": str(Path(tools["cl"])), "bytes": 893288, "sha256": plan["minimal_build_after_separate_admission"]["compiler_baseline_sha256"]})
        linker = Path(b.read(old / "LINK-RESULT.json")["argv"][0])
        toolpins = {"compiler": cl, "linker_fresh": b.pin(linker), "dumpbin_fresh": b.pin(linker.parent / "dumpbin.exe")}
        ref(toolpins["linker_fresh"]); ref(toolpins["dumpbin_fresh"])
        b.write(root / "PREPARED.json", {"machine_id": machine, "at_utc": b.now(), "plan": b.pin(PLAN),
            "admission": b.pin(args.admission), "source": b.pin(newsource), "baseline_exact_pins": baseline,
            "direct_inputs": directpins, "runtime_archive_reused_without_copy": baseline["build/native26-runtime.lib"],
            "headers": headerpins, "header_digest": digest, "tools": toolpins,
            "tool_pin_scope": "compiler historical exact; linker/dumpbin exact original-version folder freshly pinned, historical body pin not supplied in Native26 receipt",
            "archive_rebuilds": 0, "old_input_copies": 0, "whole_master_native_used": False})
        print(json.dumps({"phase": "prepare_PASS", "at_utc": b.now(), "logical_bytes": watch()}), flush=True)
        phase = "compile_production"
        attempt = root / "build/router/attempt01"; attempt.mkdir(parents=True)
        obj, deps = attempt / "nonwar12004.obj", attempt / "dependencies.json"
        recipe = b.read(old / RECIPE)
        argv = compile_argv(recipe["argv"], newsource, obj, deps)
        compile_result = run(argv, attempt, newenv(env, attempt / "temp"), attempt / "compile.log", 128 * b.MIB)
        require([b.norm(x) for x in b.read(deps)["Data"]["Includes"]] == [b.norm(x) for x in includes], "compiled includes changed")
        oldrel = coff_function_relocations(old / OLDOBJ, "PopulateNonwarRouterExecutors12004")
        newrel = coff_function_relocations(obj, "PopulateNonwarRouterExecutors12004")
        target = "ExecuteSwayCompletionTerminationMailboxV1"
        require(not any(target in row["symbol"] for row in oldrel["relocations"]), "old .4 already had target relocation")
        require(sum(target in row["symbol"] for row in newrel["relocations"]) == 1, "new .4 exact registration relocation absent/ambiguous")
        dump = run([linker.parent / "dumpbin.exe", "/DISASM", "/RELOCATIONS", obj], attempt, env, attempt / "production-router-disassembly.log")
        b.write(root / "COMPILE-RESULT.json", {"machine_id": machine, "result": compile_result, "object": b.pin(obj),
            "dependencies": b.pin(deps), "same799Includes": True, "new546HeaderDigest": digest,
            "actual_exact4_registration": newrel, "baseline_exact4_registration": oldrel, "disassembly": dump})
        print(json.dumps({"phase": "compile_PASS", "at_utc": b.now(), "logical_bytes": watch()}), flush=True)
        phase = "link_production"
        lines = response.read_text(encoding="utf-8-sig").splitlines()
        hits = [i for i, value in enumerate(lines) if b.norm(value.strip('"')) == b.norm(old / OLDOBJ)]
        require(len(hits) == 1, "old router replacement count")
        lines[hits[0]] = str(obj)
        for prefix, suffix, count in (("/OUT:", "dll", 1), ("/PDB:", "pdb", 1), ("/IMPLIB:", "lib", 1), ("/MAP:", "map", 2)):
            found = [i for i, value in enumerate(lines) if value.upper().startswith(prefix)]
            require(len(found) == count, "output switch count")
            for i in found: lines[i] = prefix + str(root / ("build/native27." + suffix))
        rsp = root / "build/native27-link.rsp"; rsp.write_text("\n".join(lines) + "\n", encoding="utf-8")
        link_result = run([linker, "@" + str(rsp)], root / "build", newenv(env, root / "build/link-temp"), root / "build/link.log", 768 * b.MIB)
        dll, mapfile = root / "build/native27.dll", root / "build/native27.map"
        require(exports(dll) == exports(old / "build/native26.dll"), "export names/ordinals changed")
        maplines = []
        with mapfile.open(encoding="utf-8-sig") as stream:
            for line in stream:
                if "PopulateNonwarRouterExecutors12004" in line or target in line: maplines.append(line.strip())
        require(any("PopulateNonwarRouterExecutors12004" in line and "nonwar12004.obj" in line for line in maplines), "new .4 map owner mismatch")
        require(any(target in line and "native26-runtime:native-p0473.obj" in line for line in maplines), "retained executor map owner mismatch")
        export_dump = run([linker.parent / "dumpbin.exe", "/EXPORTS", dll], root / "build", env, root / "build/exports.log")
        export_rows = [{"ordinal": int(o), "rva_hex": r, "name": n} for o, r, n in re.findall(r"^\s*(\d+)\s+[0-9A-F]+\s+([0-9A-F]+)\s+(Xar\w+)\s*$", (root / "build/exports.log").read_text(), re.M)]
        require([{k: row[k] for k in ("ordinal", "name")} for row in export_rows] == exports(dll), "export RVA readback mismatch")
        b.write(root / "LINK-RESULT.json", {"machine_id": machine, "result": link_result, "DLL": b.pin(dll), "map": b.pin(mapfile),
            "map_selected_lines": maplines, "exports": export_rows, "export_dump": export_dump,
            "direct_router_replacements": 1, "other355_direct_and_archive_unchanged": True, "archive_members_retained": 612})
        print(json.dumps({"phase": "link_PASS", "at_utc": b.now(), "logical_bytes": watch()}), flush=True)
        phase = "offline_fixture"
        offline = root / "offline01"; offline.mkdir()
        offline_env = newenv(env, offline / "temp")
        fixture_text = (old / "offline04/termination-route-fixture.cpp").read_text(encoding="utf-8-sig")
        fixture_anchor = 'extern "C" __declspec(dllexport) int RunNative26TerminationRouteFixture() {\n  using namespace xar;\n  using namespace xar::ck3_12002;\n'
        require(fixture_text.count(fixture_anchor) == 1, "fixture anchor ambiguity")
        assertion = "  NonwarMailboxExecutorsV1 registered{};\n  PopulateNonwarRouterExecutors12004(registered);\n  Check(registered.sway_completion_termination == &ExecuteSwayCompletionTerminationMailboxV1,\n        \"exact .4 termination executor pointer registered\");\n"
        fixture_text = fixture_text.replace(fixture_anchor, fixture_anchor + assertion)
        fixture_source = offline / "termination-route-fixture.cpp"; fixture_source.write_text(fixture_text, encoding="utf-8", newline="\n")
        prior_offline = old_metadata("offline04/RESULT.json")["checks"]["termination_route"]
        fixture_objects = []
        fixture_compiles = []
        for key, source, filename in (("compile", fixture_source, "termination-route-test.obj"),
                                     ("exact_production_source_compile", newsource, "termination-route-production.obj")):
            output = offline / filename
            argv = compile_argv(prior_offline[key]["argv"], source, output, output.with_name(output.stem + "-dependencies.json"))
            fixture_compiles.append(run(argv, offline, offline_env, output.with_name(output.stem + "-compile.log"), 128 * b.MIB))
            fixture_objects.append(output)
        replacements = {b.norm(prior_offline["compile"]["object"]["path"]): str(fixture_objects[0]),
                        b.norm(prior_offline["exact_production_source_compile"]["object"]["path"]): str(fixture_objects[1])}
        fixture_dll = offline / "termination-route.dll"
        fixture_argv = []
        for value in prior_offline["link"]["argv"]:
            if b.norm(value) in replacements: fixture_argv.append(replacements[b.norm(value)])
            elif value.upper().startswith("/OUT:"): fixture_argv.append("/OUT:" + str(fixture_dll))
            else: fixture_argv.append(value)
        fixture_link = run(fixture_argv, offline, offline_env, offline / "fixture-link.log", 768 * b.MIB)
        loader_pin = prior_offline["loader"]; ref(loader_pin)
        loader_run = run([sys.executable, "-B", loader_pin["path"], fixture_dll], offline, offline_env, offline / "fixture-run.log", timeout=120)
        b.write(offline / "RESULT.json", {"machine_id": machine, "status": "PASS_EXACT4_REGISTRATION_AND_ORIGINAL_ROUTE_NEGATIVES",
            "source": b.pin(fixture_source), "compiles": fixture_compiles, "fixture_link": fixture_link,
            "fixture_DLL": b.pin(fixture_dll), "run": loader_run, "new_objects": [b.pin(path) for path in fixture_objects],
            "retained_ABI_objects": [baseline["offline04/termination-abi3.obj"], baseline["offline04/termination-abi4.obj"]],
            "scope": "Pointer installation and original router spies only; no actual termination/event/cause/benefit claim; production DLL not loaded."})
        phase = "close"
        unchanged(); watch()
        b.write(root / "QUALIFICATION.json", {"schema": "xar.ck3.native27-registration-qualification/v1", "machine_id": machine,
            "observed_at_utc": b.now(), "status": "BUILD_AND_OFFLINE_PASS_NOT_DEPLOYED", "label": "Native27 termination executor registration",
            "source": b.pin(newsource), "baseline_DLL": baseline["build/native26.dll"], "candidate_DLL": b.pin(dll),
            "plan": b.pin(PLAN), "admission": b.pin(args.admission), "compile": b.pin(root / "COMPILE-RESULT.json"),
            "link": b.pin(root / "LINK-RESULT.json"), "offline": b.pin(offline / "RESULT.json"), "exports": export_rows,
            "production_objects_compiled": 1, "fixture_objects_compiled": 2, "headers_or_ABI_changed": False,
            "M4_public_ABI_adopted": False, "old_input_copies": 0, "archive_rebuilds": 0,
            "tool_windows": windows, "production_DLL_loaded": False, "Game_or_RPC_calls": 0, "new_EXE_outputs": 0,
            "review_at_utc": admission["review_at_utc"], "future_writes_bytes": 0, "owned_subprocesses_remaining": 0,
            "live_termination_or_performance_qualified": False})
        status = "PASS"
    except BaseException as error:
        b.write(root / "FAILED01.json", {"machine_id": machine, "observed_at_utc": b.now(), "phase": phase,
            "status": "RED_SINGLE_ATTEMPT_RETAINED", "error": repr(error), "tool_windows": windows,
            "Game_or_RPC_calls": 0, "production_DLL_loaded": False, "automatic_retry": False})
        status = "RED"
    files = [b.pin(path) | {"relative_path": str(path.relative_to(root))} for path in sorted(root.rglob("*")) if path.is_file()]
    closed = {"schema": "xar.storage.native27-files-closed/v1", "machine_id": machine, "observed_at_utc": b.now(),
        "root": str(root), "status": status, "files_excluding_this_manifest": files,
        "logical_bytes_excluding_manifest": sum(row["bytes"] for row in files), "allocated_bytes": None,
        "future_writes_bytes": 0, "owned_build_or_fixture_subprocesses_remaining": 0,
        "review_at_utc": admission["review_at_utc"], "parent_or_child_budget_credit_released": False}
    for _ in range(12):
        encoded = json.dumps(closed, ensure_ascii=True, indent=2).encode() + b"\n"
        total = closed["logical_bytes_excluding_manifest"] + len(encoded)
        if closed.get("logical_bytes_including_manifest") == total: break
        closed["logical_bytes_including_manifest"] = total
    else: raise ValueError("manifest fixed point failed")
    require(total <= hard, "closed total exceeds admission")
    (root / "FILES-CLOSED.json").write_bytes(encoded)
    print(json.dumps({"status": status, "manifest": b.pin(root / "FILES-CLOSED.json"), "logical_bytes": total,
                      "files": len(files) + 1, "last_phase": phase}), flush=True)
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
