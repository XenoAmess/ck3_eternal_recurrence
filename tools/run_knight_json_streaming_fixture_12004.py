#!/usr/bin/env python3
"""One bounded offline old/new serializer comparison; never builds a bridge.

Retained production function bodies are extracted unchanged. Only namespaces
and preprocessor symbol aliases outside those bodies isolate their linkage.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import statistics
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import register_project_exe_exclusions as defender
import run_native_msvc as msvc

OLD = "652e873ab164cfb78b654854c0dc2ca35ef816b3"
NEW = "d90d5e79ac7d22b3376ca70f3fccebd3faef516f"
NATIVE = "ck3_autonomous_player/native_bridge/"


def pin(path: Path) -> dict:
    data = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def git_text(commit: str, path: str) -> str:
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT).decode("utf-8")


def function_span(source: str, name: str) -> str:
    match = re.search(r"^(?:std::string|void) " + re.escape(name) + r"\(", source, re.M)
    if not match:
        raise ValueError(f"Missing production function: {name}")
    start = source.index("{", match.end())
    depth, state, escaped, index = 1, "code", False, start + 1
    while index < len(source):
        char, pair = source[index], source[index:index + 2]
        if state in ("string", "char"):
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == ('"' if state == "string" else "'"):
                state = "code"
        elif state == "line":
            if char == "\n": state = "code"
        elif state == "block":
            if pair == "*/": state, index = "code", index + 1
        elif pair == "//": state, index = "line", index + 1
        elif pair == "/*": state, index = "block", index + 1
        elif char == '"': state = "string"
        elif char == "'": state = "char"
        elif char == "{": depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0: return source[match.start():index + 1] + "\n"
        index += 1
    raise ValueError(f"Unclosed production function: {name}")


def helpers(source: str, first: str) -> str:
    start = source.index(first)
    return source[start:source.index("\n} // namespace", start)] + "\n"


def isolated(namespace: str, aliases: dict[str, str], imports: list[str], body: str) -> str:
    define = "".join(f"#define {name} {alias}\n" for name, alias in aliases.items())
    undef = "".join(f"#undef {name}\n" for name in aliases)
    using = "".join(f"using {name};\n" for name in imports)
    return f"namespace {namespace} {{\nusing namespace xar::ck3_12004;\n" + using + define + body + undef + "}\n"


def produce_source(destination: Path) -> dict:
    source_root = destination / "source"
    include_root = source_root / "include"
    include_root.mkdir(parents=True)
    files, spans, headers = {}, [], []
    names = ["ck3_12004_person_six_stage_capture.cpp", "person_callback_entry_inputs_12004.cpp",
             "ck3_12004_knight_stat_consumption_serializer.cpp", "person_current_input_outcome_binding_12004.cpp"]
    for commit in (OLD, NEW):
        for name in names:
            text = git_text(commit, NATIVE + "src/" + name)
            files[commit, name] = text
            spans.append({"commit": commit, "path": NATIVE + "src/" + name,
                          "whole_source_utf8_sha256": hashlib.sha256(text.encode()).hexdigest()})
    if files[OLD, names[3]] != files[NEW, names[3]]:
        raise ValueError("Shared unchanged binding serializer source changed")
    pending = ["xar_bridge/knight_stat_consumption_12004.hpp"]
    seen = set()
    while pending:
        name = pending.pop()
        if name in seen: continue
        seen.add(name)
        text = git_text(NEW, NATIVE + "include/" + name)
        output = include_root / name
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8", newline="\n")
        headers.append({"commit": NEW, "original": NATIVE + "include/" + name, **pin(output)})
        for dependency in re.findall(r'^#include "([^"]+)"', text, re.M):
            if dependency.startswith("xar_bridge/"): pending.append(dependency)
        if len(seen) > 64: raise ValueError("Unexpected header-closure expansion")
    shared_source = files[NEW, names[3]]
    shared_body = helpers(shared_source, "void JsonString") + function_span(shared_source, "SerializePersonCurrentInputOutcomeBinding12004")
    output = isolated("shared_binding", {"SerializePersonCurrentInputOutcomeBinding12004": "SharedBinding"}, [], shared_body)
    for commit, label, prefix in ((OLD, "baseline", "Old"), (NEW, "candidate", "New")):
        capture = files[commit, names[0]]
        functions = (["WritePersonSixStageCapture12004"] if commit == NEW else []) + ["SerializePersonSixStageCapture12004", "SerializePersonSixStageQuery12004"]
        body = helpers(capture, "void String") + "\n".join(function_span(capture, name) for name in functions)
        aliases = {"SerializePersonSixStageCapture12004": prefix + "Capture", "SerializePersonSixStageQuery12004": prefix + "Query"}
        if commit == NEW: aliases["WritePersonSixStageCapture12004"] = "NewWriteCapture"
        output += isolated(label + "_capture", aliases, [], body)
        entry = files[commit, names[1]]
        functions = (["WritePersonCallbackEntryInputs12004"] if commit == NEW else []) + ["SerializePersonCallbackEntryInputs12004"]
        body = helpers(entry, "void JsonString") + "\n".join(function_span(entry, name) for name in functions)
        aliases = {"SerializePersonSixStageCapture12004": prefix + "Capture", "SerializePersonCallbackEntryInputs12004": prefix + "Entry"}
        imports = [label + "_capture::" + prefix + "Capture"]
        if commit == NEW:
            aliases.update(WritePersonSixStageCapture12004="NewWriteCapture", WritePersonCallbackEntryInputs12004="NewWriteEntry")
            imports.append("candidate_capture::NewWriteCapture")
        output += isolated(label + "_entry", aliases, imports, body)
        knight = files[commit, names[2]]
        body = knight[knight.index("namespace {\n"):knight.rindex("\n} // namespace xar::ck3_12004")]
        aliases = {"SerializePersonSixStageCapture12004": prefix + "Capture", "SerializePersonCallbackEntryInputs12004": prefix + "Entry",
                   "SerializePersonCurrentInputOutcomeBinding12004": "SharedBinding", "SerializeKnightStatConsumptionQuery12004": prefix + "Knight"}
        imports = [label + "_capture::" + prefix + "Capture", label + "_entry::" + prefix + "Entry", "shared_binding::SharedBinding"]
        if commit == NEW:
            aliases.update(WritePersonSixStageCapture12004="NewWriteCapture", WritePersonCallbackEntryInputs12004="NewWriteEntry")
            imports.extend(["candidate_capture::NewWriteCapture", "candidate_entry::NewWriteEntry"])
        output += isolated(label + "_knight", aliases, imports, body + "\n")
    inc = source_root / "serializer-spans.inc"
    inc.write_text(output, encoding="utf-8", newline="\n")
    template = ROOT / (NATIVE + "tests/knight_json_streaming_12004_fixture_main.cpp.in")
    main = source_root / "knight-json-streaming-fixture.cpp"
    main.write_bytes(template.read_bytes())
    return {"source_root": str(source_root), "production_source_pins": spans,
            "typed_header_pins": headers, "harness_template": pin(template),
            "generated_source": [pin(main), pin(inc)],
            "extraction_boundary": "All selected production body/helper bytes unchanged; namespace imports and preprocessor symbol aliases outside bodies only"}


def logged(command: list[str], log: Path, env: dict, cwd: Path, timeout: int = 60) -> dict:
    started = time.perf_counter()
    result = subprocess.run(command, cwd=cwd, env=env, capture_output=True,
                            timeout=timeout, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    log.write_bytes(result.stdout + result.stderr)
    return {"argv": command, "exit_code": result.returncode,
            "elapsed_seconds": time.perf_counter() - started, "log": pin(log)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--storage-child", type=Path, required=True)
    parser.add_argument("--dll-fallback", action="store_true")
    args = parser.parse_args()
    run = args.output_root.resolve()
    child = json.loads(args.storage_child.read_text(encoding="utf-8-sig"))
    approved_root = Path(child["approved_child_output_root"]).resolve()
    if not run.is_relative_to(approved_root):
        raise ValueError("Output root is not within the actual storage-child approved root")
    run.mkdir(parents=True, exist_ok=False)
    report = {"schema": "xar.ck3.knight-json-streaming-executable-equivalence/v1",
              "machine_id": subprocess.check_output([sys.executable, str(ROOT / "tools/ck3_live_run_id.py"), "machine"], text=True).strip(),
              "observed_at_utc": datetime.now(timezone.utc).isoformat(), "status": "SOURCE_PREPARED",
              "baseline_commit": OLD, "candidate_cpp_commit": NEW,
              "storage_child": pin(args.storage_child), "producer": pin(Path(__file__)),
              "expected_peak_bytes": 67108864, "hard_limit_bytes": 536870912,
              "game_native_mcp_calls": 0, "bridge_rebuild_or_runtime_changes": False}
    try:
        report["source"] = produce_source(run)
        source = Path(report["source"]["source_root"])
        build = run / "build"
        build.mkdir()
        environment = msvc.child_environment(build)
        installation = msvc.visual_studio_installation(None, environment)
        environment, tools = msvc.initialize_msvc(installation, build, environment)
        report["environment_producer"] = pin(ROOT / "tools/run_native_msvc.py")
        report["compiler"] = pin(Path(tools["cl"]))
        report["tools"] = tools
        common = [tools["cl"], "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX", "/O2", "/MD", "/utf-8", "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN",
                  "/I" + str(source / "include"), "/I" + str(source), "/c", str(source / "knight-json-streaming-fixture.cpp")]
        obj = build / "serializer-fixture.obj"
        compile_command = common + ["/Fo" + str(obj), "/sourceDependencies", str(build / "dependencies.json")]
        report["compile"] = logged(compile_command, build / "compile.log", environment, build)
        if report["compile"]["exit_code"] != 0: raise RuntimeError("Offline serializer harness compile failed")
        report["object"] = pin(obj)
        exe = build / "knight-json-streaming-fixture.exe"
        link = [str(Path(tools["cl"]).parent / "link.exe"), "/nologo", "/OPT:REF", str(obj), "/OUT:" + str(exe), "bcrypt.lib"]
        report["link"] = logged(link, build / "link.log", environment, build)
        if report["link"]["exit_code"] != 0: raise RuntimeError("Offline serializer harness link failed")
        report["executable"] = pin(exe)
        report["defender"] = defender.after_successful_command_build(
            ROOT, source, build, link, [exe], external_candidate="knight-json-streaming-equivalence-12004 fixed production spans",
            return_code=0, source_commands=[{"argv": compile_command, "return_code": 0}])
        fixture_result = run / "FIXTURE-RESULT.json"
        if report["defender"]["status"] == "verified":
            report["run"] = logged([str(exe), str(fixture_result)], build / "run.log", environment, build, 60)
            report["execution_kind"] = "registered_project_exe"
        elif args.dll_fallback:
            dll_obj, dll = build / "serializer-fixture-dll.obj", build / "knight-json-streaming-fixture.dll"
            dll_compile = common + ["/DXAR_SERIALIZER_FIXTURE_DLL=1", "/Fo" + str(dll_obj)]
            report["dll_compile"] = logged(dll_compile, build / "dll-compile.log", environment, build)
            if report["dll_compile"]["exit_code"] != 0: raise RuntimeError("DLL fallback compile failed")
            dll_link = [link[0], "/nologo", "/DLL", "/OPT:REF", str(dll_obj), "/OUT:" + str(dll), "bcrypt.lib"]
            report["dll_link"] = logged(dll_link, build / "dll-link.log", environment, build)
            if report["dll_link"]["exit_code"] != 0: raise RuntimeError("DLL fallback link failed")
            report["dll"] = pin(dll)
            loader = run / "load_offline_fixture.py"
            loader.write_text("import ctypes, sys\nfrom pathlib import Path\ndll = ctypes.CDLL(str(Path(sys.argv[1]).resolve()))\nrun = dll.XarRunKnightJsonStreamingFixture12004\nrun.argtypes = [ctypes.c_char_p]\nrun.restype = ctypes.c_int\nraise SystemExit(run(str(Path(sys.argv[2]).resolve()).encode('utf-8')))\n", encoding="utf-8")
            report["loader"] = pin(loader)
            report["run"] = logged([sys.executable, "-B", str(loader), str(dll), str(fixture_result)], build / "dll-run.log", environment, build, 60)
            report["execution_kind"] = "ordinary_child_python_ctypes_isolated_dll_no_game_connection"
        else:
            report["status"] = "OBJECT_COMPILED_EXECUTION_NOTRUN_DEFENDER_UNAVAILABLE"
        if "run" in report:
            if report["run"]["exit_code"] != 0: raise RuntimeError("C++ serializer byte equivalence fixture failed")
            fixture = json.loads(fixture_result.read_text(encoding="utf-8"))
            report["fixture_result"] = pin(fixture_result)
            report["fixture"] = fixture
            report["timing_median_ns"] = {name: statistics.median(fixture["timing"][name + "_ns"]) for name in ("baseline", "candidate")}
            report["status"] = "PASS_EXECUTABLE_BYTE_EQUIVALENCE_SYNTHETIC_TIMING"
    except Exception as error:
        report["status"] = "RED"
        report["error"] = repr(error)
    report["closed_at_utc"] = datetime.now(timezone.utc).isoformat()
    report["output_files"] = [{"relative_path": str(path.relative_to(run)), "bytes": path.stat().st_size}
                              for path in run.rglob("*") if path.is_file()]
    report["actual_output_bytes_before_final_receipt"] = sum(row["bytes"] for row in report["output_files"])
    report["whole_child_bytes_before_final_receipt"] = sum(path.stat().st_size for path in approved_root.rglob("*") if path.is_file())
    if report["whole_child_bytes_before_final_receipt"] >= report["hard_limit_bytes"]:
        report["status"] = "RED_CAPACITY_LIMIT"
    result = run / "RESULT.json"
    result.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "receipt": pin(result), "error": report.get("error")}, ensure_ascii=False))
    return 0 if report["status"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
