"""One focused compile of the production projected reader and serializer."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=BASE.parent)
    parser.add_argument("--baseline-root", type=Path)
    parser.add_argument("--fixture-source", type=Path)
    parser.add_argument("--attempt", default="focused-attempt-01")
    parser.add_argument("--reuse", type=Path)
    parser.add_argument("--case")
    parser.add_argument("--native-only", action="store_true")
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    args = parser.parse_args()
    args.baseline_root = args.baseline_root or args.source_root
    build = BASE / args.attempt
    build.mkdir(exist_ok=False)
    common = args.baseline_root / "ck3_autonomous_player/native_bridge"
    source = args.source_root / "ck3_autonomous_player/native_bridge"
    units = {
        "production-reader": source / "src/ck3_12002_routes.cpp",
        "production-serializer": source / "src/projected_contact_scope_v1_serializer.cpp",
        "focused-case": args.fixture_source or (
            BASE / "projected_contact_scope_v1_production_test.cpp"
            if (BASE / "projected_contact_scope_v1_production_test.cpp").exists()
            else source / "src/projected_contact_scope_v1_production_test.cpp"),
    }
    report = {
        "status": "RED", "source_root": str(args.source_root),
        "exact_ck3": "1.20.0.3/Steam25652598",
        "exe_sha256": "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6",
        "scope": "new projected production reader -> production serializer -> Python normalizer/driver/service -> registered MCP",
        "full_dll_build": False, "game_contacted": False, "window_operations": 0,
        "old_test_cases_rerun": False, "compile_commands": {}, "reused_objects": [],
        "sources": [{"name": name, "path": str(path),
                     "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                    for name, path in units.items()],
    }
    try:
        memory_source = common / "src/ck3_12002_routes_test.cpp"
        memory_text = memory_source.read_text(encoding="utf-8-sig")
        helper_prefix, marker, _old_main = memory_text.partition("int main() {")
        if not marker:
            raise RuntimeError("baseline routes memory helper/main boundary is missing")
        memory_header = build / "projected_contact_memory_fixture.hpp"
        memory_header.write_text(helper_prefix, encoding="utf-8", newline="\n")
        report["memory_helper"] = {"source": str(memory_source),
                                   "source_sha256": hashlib.sha256(memory_source.read_bytes()).hexdigest(),
                                   "imported_prefix_sha256": hashlib.sha256(memory_header.read_bytes()).hexdigest(),
                                   "old_main_imported_or_invoked": False}
        helper_path = args.baseline_root / "tools/run_native_msvc.py"
        spec = importlib.util.spec_from_file_location("projected_contact_msvc", helper_path)
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        env = helper.child_environment(build)
        env, compiler = helper.initialize_msvc(helper.visual_studio_installation(None, env), build, env)
        prefix = [compiler["cl"], "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX", "/O2",
                  "/DNDEBUG", "/utf-8", "/MT", "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN"]
        previous = {}
        if args.reuse:
            old = json.loads((args.reuse / "RESULT.json").read_text(encoding="utf-8"))
            previous = {row["name"]: row for row in old["sources"]}

        def compile_one(item: tuple[str, Path]) -> str:
            name, path = item
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            old_object = args.reuse / (name + ".obj") if args.reuse else None
            if name in previous and previous[name]["sha256"] == digest and old_object.is_file():
                shutil.copyfile(old_object, build / (name + ".obj"))
                report["reused_objects"].append(name)
                return name
            command = prefix + ["/I" + str(source / "include"), "/I" + str(common / "include"),
                                "/I" + str(build), "/c", str(path),
                                "/Fo" + str(build / (name + ".obj"))]
            report["compile_commands"][name] = command
            helper.run_logged(command, build / (name + ".compile.log"), env, build)
            return name

        with ThreadPoolExecutor(max_workers=3) as pool:
            report["compiled_or_reused"] = list(pool.map(compile_one, units.items()))
        exe = build / "projected-contact.exe"
        command = [str(Path(compiler["cl"]).parent / "link.exe"), "/nologo",
                   *[str(build / (name + ".obj")) for name in units],
                   "/out:" + str(exe), "kernel32.lib", "/INCREMENTAL:NO"]
        report["link_command"] = command
        helper.run_logged(command, build / "link.log", env, build)
        wire = build / "wire"
        wire.mkdir()
        command = [str(exe), str(wire)] + ([args.case] if args.case else [])
        native = subprocess.run(command, cwd=build, env=env, capture_output=True, text=True, encoding="utf-8")
        (build / "native.fixture.log").write_text(native.stdout + native.stderr, encoding="utf-8")
        report["native_exit_code"] = native.returncode
        report["native_cases_green"] = sum(line.endswith(" GREEN") for line in native.stdout.splitlines())
        report["native_wire"] = [{"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                                 for path in sorted(wire.glob("*.json"))]
        if native.returncode:
            raise RuntimeError("focused native fixture failed; retained first RED log")
        expected_count = 1 if args.case else 10
        if report["native_cases_green"] != expected_count:
            raise RuntimeError("focused native fixture did not execute the expected new cases")
        if args.native_only:
            report["status"] = "GREEN"
            report["registered_mcp_pending"] = True
            report["readiness"] = "static-ready"
            report["live"] = False
            (build / "RESULT.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(json.dumps({"status": "GREEN", "native_cases_green": report["native_cases_green"],
                              "registered_mcp_pending": True, "report": str(build / "RESULT.json")}, indent=2))
            return 0
        registered_runner = (BASE / "run_registered_mcp.py" if (BASE / "run_registered_mcp.py").exists()
                             else BASE / "test_registered_projected_contact_scope.py")
        command = [str(args.python), str(registered_runner),
                   "--source-root", str(args.source_root), "--baseline-root", str(args.baseline_root),
                   "--wire-dir", str(wire), "--result", str(build / "REGISTERED-MCP-RESULT.json")]
        if args.case:
            command += ["--case", args.case]
        report["registered_mcp_command"] = command
        python = subprocess.run(command, cwd=build, env=env, capture_output=True, text=True, encoding="utf-8")
        (build / "registered-mcp.log").write_text(python.stdout + python.stderr, encoding="utf-8")
        report["registered_mcp_exit_code"] = python.returncode
        if python.returncode:
            raise RuntimeError("registered MCP fixture failed; retained first RED result")
        report["status"] = "GREEN"
        report["readiness"] = "static-ready"
        report["live"] = False
    except Exception as error:
        report["error"] = type(error).__name__ + ": " + str(error)
    (build / "RESULT.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(build / "RESULT.json"),
                      "error": report.get("error")}, indent=2))
    return 0 if report["status"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
