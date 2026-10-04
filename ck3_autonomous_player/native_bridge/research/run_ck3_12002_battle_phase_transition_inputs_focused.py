"""Run only the new two-case current phase input reader/serializer/parser fixture."""
from __future__ import annotations

import argparse
import unittest
import copy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time


TOOL = "ck3_query_battle_control_snapshot_v1"
CAPABILITY = "game.command.query-battle-control-snapshot-v1-N"
KEY = "current_phase_transition_inputs_v1"


def require(condition: object, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def require_equal(actual: object, expected: object, path: str) -> None:
    require(type(actual) is type(expected), f"{path}: JSON value type changed")
    if isinstance(expected, dict):
        require(actual.keys() == expected.keys(), f"{path}: JSON field set changed")
        for key in expected:
            require_equal(actual[key], expected[key], path + "." + key)
    elif isinstance(expected, list):
        require(len(actual) == len(expected), f"{path}: JSON row count changed")
        for index, item in enumerate(expected):
            require_equal(actual[index], item, f"{path}[{index}]")
    else:
        require(actual == expected, f"{path}: JSON value changed")


def pin(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def compiler_path(path: Path) -> str:
    """Use Cygwin's native path spelling for compiler file arguments."""
    absolute = path.resolve()
    drive = absolute.drive
    if len(drive) == 2 and drive[1] == ":":
        return "/cygdrive/" + drive[0].lower() + absolute.as_posix()[2:]
    return str(absolute)


def build_native(args: argparse.Namespace, output: Path, executable: Path,
                 sources: list[Path], includes: list[Path], report: dict
                 ) -> dict[str, str]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    if args.compiler is not None and args.compiler.name.lower() != "cl.exe":
        environment["PATH"] = (str(args.compiler.resolve().parent) + os.pathsep +
                               environment.get("PATH", ""))
        command = [str(args.compiler.resolve()), "-std=c++20", "-O2", "-DNDEBUG",
                   "-Wall", "-Wextra", "-Werror", "-ffunction-sections", "-fdata-sections",
                   *["-D" + value for value in args.define],
                   *["-I" + compiler_path(path) for path in includes],
                   *[compiler_path(path) for path in sources],
                   "-Wl,--gc-sections", "-luser32", "-o", compiler_path(executable)]
        report["compiler_argv"] = command
        built = subprocess.run(command, cwd=output, env=environment,
                               capture_output=True, timeout=180,
                               creationflags=creation_flags)
        (output / "compile.log").write_bytes(built.stdout + built.stderr)
        report.update(compile_exit=built.returncode, compile_log=pin(output / "compile.log"))
        require(built.returncode == 0, "strict focused native compile failed")
        return environment

    helper_path = args.project_root.resolve() / "tools/run_native_msvc.py"
    helper = load_module("phase_transition_msvc_bootstrap", helper_path)
    environment = helper.child_environment(output)
    environment, compiler = helper.initialize_msvc(
        helper.visual_studio_installation(None, environment), output, environment)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    cl = str(args.compiler.resolve()) if args.compiler is not None else compiler["cl"]
    prefix = [cl, "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX", "/O2",
              "/DNDEBUG", "/utf-8", "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN",
              "/DUNICODE", "/D_UNICODE", "/Gy",
              *["/D" + value for value in args.define],
              *["/I" + str(path) for path in includes]]
    report.update(compiler_helper=pin(helper_path), compile_parallelism=min(len(sources),8))
    require(len({source.stem for source in sources}) == len(sources),
            "focused translation units have duplicate object names")

    def compile_one(source: Path) -> dict[str, object]:
        object_path = output / (source.stem + ".obj")
        log = output / (source.stem + ".compile.log")
        command = prefix + ["/c", str(source), "/Fo" + str(object_path)]
        try:
            result = subprocess.run(command, cwd=output, env=environment,
                                    capture_output=True, timeout=180,
                                    creationflags=creation_flags)
            log.write_bytes(result.stdout + result.stderr)
            return {"source": str(source), "command": command,
                    "exit_code": result.returncode, "log": pin(log),
                    "object_path": str(object_path)}
        except Exception as error:
            log.write_text(repr(error) + "\n", encoding="utf-8")
            return {"source": str(source), "command": command,
                    "exit_code": -1, "log": pin(log), "object_path": str(object_path)}

    if args.reuse_object_dir is not None:
        prior_path=args.reuse_object_dir.resolve()/"RESULT.json"
        prior=json.loads(prior_path.read_text(encoding="utf-8"))
        require(prior.get("compile_exit")==0 and prior.get("link_exit")==0,
                "reuse requires prior strict compile/link GREEN")
        prior_rows={str(Path(row["source"]).resolve()):row for row in prior["compile_commands"]}
        prior_pins={str(Path(row["path"]).resolve()):row["sha256"] for row in prior["source_pins"]}
        compiled=[]
        for source in sources:
            if source.name=="ck3_12002_battle_phase_transition_inputs_test.cpp":
                compiled.append(compile_one(source))
                continue
            key=str(source.resolve())
            require(key in prior_rows and prior_pins.get(key)==pin(source)["sha256"],
                    "unchanged production source does not match prior compiled object")
            row=dict(prior_rows[key],reused=True)
            require(Path(row["object_path"]).is_file(),"prior production object missing")
            compiled.append(row)
        require(sum(bool(row.get("reused")) for row in compiled)==7,
                "targeted correction must reuse exactly seven production objects")
        report.update(compile_parallelism=1,recompiled_translation_units=1,
                      reused_production_objects=7,reuse_receipt=pin(prior_path))
    else:
        with ThreadPoolExecutor(max_workers=min(len(sources),8)) as pool:
            compiled = list(pool.map(compile_one, sources))
    report["compile_commands"] = compiled
    report["compile_exit"] = next((item["exit_code"] for item in compiled
                                   if item["exit_code"] != 0), 0)
    require(report["compile_exit"] == 0, "strict focused native translation-unit compile failed")
    link = [str(Path(cl).parent / "link.exe"), "/nologo", "/OPT:REF",
            *[item["object_path"] for item in compiled],
            "/OUT:" + str(executable), "kernel32.lib", "user32.lib"]
    linked = subprocess.run(link, cwd=output, env=environment,
                            capture_output=True, timeout=60, creationflags=creation_flags)
    (output / "link.log").write_bytes(linked.stdout + linked.stderr)
    report.update(link_command=link, link_exit=linked.returncode,
                  link_log=pin(output / "link.log"))
    require(linked.returncode == 0, "strict focused native link failed")
    return environment


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None,
            f"cannot import fixture dependency: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module



def python_check(args):
    require(sys.flags.optimize>0,"formal parser checks require Python -O")
    sys.path.insert(0,str(args.project_root.resolve()/"ck3_autonomous_player/src"))
    import xar_autoplayer.bridge
    contract=args.python_projection_root.resolve()/"ck3_autonomous_player/src/xar_autoplayer/bridge/battle_control_contract.py"
    load_module("xar_autoplayer.bridge.battle_control_contract",contract)
    test_path=args.fixture_root.resolve()/"ck3_autonomous_player/tests/unit/test_battle_current_phase_transition_inputs.py"
    native=args.native_dir.resolve()/"phase_transition_input_cases.json"
    module=load_module("test_battle_current_phase_transition_inputs",test_path)
    document=json.loads(native.read_text(encoding="utf-8"))
    result=unittest.TextTestRunner(verbosity=2).run(module.make_phase_transition_suite(document))
    summary={"status":"GREEN" if result.wasSuccessful() and result.testsRun==2 else "RED",
        "tests_run":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),
        "python_optimization":sys.flags.optimize,"native_cases":2,"native_frames":2,
        "native_json":pin(native),"contract":pin(contract),"new_test":pin(test_path),
        "old_cases_run":0,"game_calls":0,"window_operations":0}
    args.python_result.resolve().write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return 0 if summary["status"]=="GREEN" else 1

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root",type=Path,required=True)
    parser.add_argument("--python-projection-root",type=Path,required=True)
    parser.add_argument("--fixture-root",type=Path,required=True)
    parser.add_argument("--build-dir",type=Path)
    parser.add_argument("--compiler",type=Path)
    parser.add_argument("--reuse-object-dir",type=Path)
    parser.add_argument("--source",action="append",type=Path,default=[])
    parser.add_argument("--include-dir",action="append",type=Path,default=[])
    parser.add_argument("--define",action="append",default=[])
    parser.add_argument("--python-check-only",action="store_true")
    parser.add_argument("--native-dir",type=Path)
    parser.add_argument("--python-result",type=Path)
    args=parser.parse_args()
    if args.python_check_only:
        require(args.native_dir is not None and args.python_result is not None,"Python output paths required")
        return python_check(args)
    require(args.build_dir is not None and len(args.source)==8,"exact focused 8 TU sources required")
    output=args.build_dir.resolve(); output.mkdir(parents=True,exist_ok=False)
    wire=output/"wire"; wire.mkdir()
    sources=[path.resolve() for path in args.source]
    includes=[path.resolve() for path in args.include_dir]
    fallback=args.project_root.resolve()/"ck3_autonomous_player/native_bridge/include"
    if fallback not in includes: includes.append(fallback)
    executable=output/"battle-phase-transition-inputs-focused.exe"
    report={"schema":"battle-current-phase-transition-inputs-focused/v1","status":"HARNESS-RED",
        "readiness":"research","source_pins":[pin(path) for path in sources],
        "runner":pin(Path(__file__).resolve()),"compile_exit":None,"run_exit":None,"python_exit":None,
        "native_cases":2,"native_frames":2,"whole_dll_built":False,"game_calls":0,
        "sdk_pipe_calls":0,"window_operations":0,"shared_writes":0,"git_mutations":0,"old_cases_run":0}
    started=time.perf_counter()
    try:
        environment=build_native(args,output,executable,sources,includes,report)
        report["status"]="FIXTURE-RED"
        native_arg=compiler_path(wire) if args.compiler is not None and args.compiler.name.lower()!="cl.exe" else str(wire)
        ran=subprocess.run([str(executable),native_arg],cwd=output,env=environment,capture_output=True,
            timeout=30,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        (output/"run.log").write_bytes(ran.stdout+ran.stderr)
        report.update(run_exit=ran.returncode,run_log=pin(output/"run.log"),executable=pin(executable))
        require(ran.returncode==0,"new current phase native reader fixture failed")
        command=[sys.executable,"-O",str(Path(__file__).resolve()),"--python-check-only",
            "--project-root",str(args.project_root.resolve()),
            "--python-projection-root",str(args.python_projection_root.resolve()),
            "--fixture-root",str(args.fixture_root.resolve()),"--native-dir",str(wire),
            "--python-result",str(output/"FORMAL-PYTHON-RESULT.json")]
        checked=subprocess.run(command,cwd=output,env=environment,capture_output=True,timeout=60,
            creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        (output/"python.log").write_bytes(checked.stdout+checked.stderr)
        report.update(python_argv=command,python_exit=checked.returncode,python_log=pin(output/"python.log"))
        require(checked.returncode==0,"new formal Python phase input cases failed")
        report.update(status="GREEN",readiness="static-ready",
            formal_python_result=pin(output/"FORMAL-PYTHON-RESULT.json"),
            native_json=pin(wire/"phase_transition_input_cases.json"))
    except Exception as error: report["error"]=repr(error)
    report["elapsed_seconds"]=time.perf_counter()-started
    receipt=output/"RESULT.json"
    receipt.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"receipt":pin(receipt),"error":report.get("error")}))
    return 0 if report["status"]=="GREEN" else 1

if __name__=="__main__":
    raise SystemExit(main())
