"""Run the two new primary levy-damage paths through the existing registered MCP.

Synthetic native observations use the production reader and serializer. Runtime
checks remain active under Python -O and C++ NDEBUG. The existing MSVC bootstrap
compiles seven translation units with six workers; no DLL or game is loaded.
"""
from __future__ import annotations

import argparse
import asyncio
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
LOSS_KEY = "current_loss_inputs_v1"


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
    helper = load_module("primary_levy_damage_msvc_bootstrap", helper_path)
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
    report.update(compiler_helper=pin(helper_path), compile_parallelism=6)
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

    with ThreadPoolExecutor(max_workers=6) as pool:
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


class RegisteredDriver:
    """A paused synthetic driver; the service and registered tool stay real."""

    def __init__(self, frame: dict[str, object]) -> None:
        self.frame = copy.deepcopy(frame)
        self.subject = int(frame["subject_public_cunit_id"])
        self.step = f"query-battle-control-snapshot-v1-{self.subject}"
        self.calls: list[str] = []

    def capabilities(self) -> dict[str, object]:
        return {"format_version": 1, "backend_id": "primary-levy-damage-fixture",
                "source": "named-pipe", "snapshot": True,
                "wait_for_change": False, "action_steps": [self.step],
                "bridge_capabilities": [CAPABILITY]}

    def take_snapshot(self) -> dict[str, object]:
        return {"format_version": 1, "snapshot_id": "primary-levy-damage-fixture:4",
                "revision": 4, "native_revision": self.frame["snapshot_revision"],
                "source": "named-pipe", "backend_id": "primary-levy-damage-fixture",
                "date_raw": self.frame["observed_date_raw"], "paused": True,
                "episode_run_id": "primary-levy-damage-fixture",
                "diagnostics": {"hello": {
                    "game_version": "1.20.0.3",
                    "executable_sha256": "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"}}}

    def execute_step(self, step: str, *, expected_revision: int | None = None
                     ) -> dict[str, object]:
        require(step == self.step and expected_revision == 4,
                "registered service changed the bound query/revision")
        self.calls.append(step)
        frame = copy.deepcopy(self.frame)
        result = {"step": step, "accepted": True, "status": "available",
                  "query_sequence": 41,
                  "snapshot_revision": frame["snapshot_revision"],
                  "backend_id": "primary-levy-damage-fixture",
                  "battle_control_snapshot": frame}
        for key in ("selected_public_cunit_id", "selected_native_carmy_id",
                    "selected_owner_character_id", "combat_province_id",
                    "side_index", "side_scope",
                    "affected_public_cunit_ids_in_stored_order",
                    "unaffected_same_side_public_cunit_ids_in_stored_order",
                    "side_flags", "legality"):
            result[key] = copy.deepcopy(frame[key])
        return result

    def wait_for_change(self, after_revision: int, *, timeout_seconds: float
                        ) -> dict[str, object]:
        raise RuntimeError("read-only loss-input fixture attempted to advance time")


async def registered_query(frame: dict[str, object]) -> dict[str, object]:
    from mcp import Client
    from xar_autoplayer.bridge.mcp_server import create_server

    driver = RegisteredDriver(frame)
    require(CAPABILITY in driver.capabilities()["bridge_capabilities"],
            "existing battle-control capability missing")
    async with Client(create_server(driver)) as client:
        listed = await client.list_tools()
        require(TOOL in {tool.name for tool in listed.tools},
                "existing battle-control MCP tool is not registered")
        result = await client.call_tool(TOOL, {
            "subject_army_id": driver.subject, "expected_revision": 4})
    require(not result.is_error, "registered loss-input query returned an MCP error")
    payload = result.structured_content
    require(isinstance(payload, dict), "registered query has no structured payload")
    require(payload.get("battle_control_ready") is True,
            "additive loss inputs changed existing battle-control readiness")
    require(driver.calls == [driver.step],
            "registered query did not invoke exactly one existing query step")
    require(isinstance(payload.get("battle_control_snapshot"), dict),
            "registered query dropped its existing nested body")
    return payload


def python_check(args: argparse.Namespace) -> int:
    require(sys.flags.optimize > 0, "registered parser checks must run under Python -O")
    project = args.project_root.resolve()
    sys.path.insert(0, str(project / "ck3_autonomous_player/src"))
    import xar_autoplayer.bridge

    adapter = (args.python_projection_root.resolve() /
               "ck3_autonomous_player/src/xar_autoplayer/bridge/battle_control_contract.py")
    load_module("xar_autoplayer.bridge.battle_control_contract", adapter)
    # Native frames pass through the real registered route. P1 already verified
    # old side-key absence with this canonical module; do not repeat that case.
    return check_loss_cases(args)


def check_loss_cases(args: argparse.Namespace) -> int:
    native_path = args.native_dir.resolve() / "primary_levy_damage_input_cases.json"
    document = json.loads(native_path.read_text(encoding="utf-8"))
    require(type(document.get("schema_version")) is int and document["schema_version"] == 1,
            "new native fixture schema is not version 1")
    require(type(document.get("actual")) is int and document["actual"] == 0,
            "focused fixture must identify its synthetic observations")
    cases = document.get("cases")
    require(isinstance(cases, list) and len(cases) == 2,
            "primary getter fixture must contain exactly its two bounded cases")
    names = ["resolved_primary_getter_zero_and_nonzero",
             "unbound_primary_getter_preserves_existing_inputs"]
    normalized_cases = []
    observed_zero = False
    observed_nonzero = False
    null_rows = 0
    for case_index, case in enumerate(cases):
        require(isinstance(case, dict) and case.get("name") == names[case_index],
                "native primary getter case order changed")
        name = case["name"]
        frame = case.get("battle_control_snapshot")
        expected = case.get("expected_loss_inputs_v1")
        require(isinstance(frame, dict) and isinstance(expected, dict),
                name + ": missing complete native loss-input body")
        require_equal(frame.get(LOSS_KEY), expected, name + ".native_expected")
        require_equal(expected["scale"], 100000, name + ".native_q_scale")
        require_equal(expected["source_combat_id"], frame["combat_id"], name + ".combat")
        require_equal(expected["source_target_province_id"], frame["province_id"], name + ".province")
        require(isinstance(expected.get("sides"), list) and len(expected["sides"]) == 2,
                name + ": actual side order missing")
        for side_index, side in enumerate(expected["sides"]):
            side_name = "attacker" if side_index == 0 else "defender"
            require_equal(side["side_index"], side_index, name + ".side_index")
            require_equal(side["primary_participant_character_id"],
                          frame[side_name]["primary_participant_character_id"],
                          name + ".primary_full_id")
            raw = side["levy_damage_raw"]
            if case_index == 0:
                require(type(raw) is int and -(1 << 63) <= raw < (1 << 63),
                        name + ": resolved getter did not preserve signed int64")
                observed_zero = observed_zero or raw == 0
                observed_nonzero = observed_nonzero or raw != 0
            else:
                require(raw is None, name + ": unbound getter invented a zero")
                null_rows += 1
        payload = asyncio.run(registered_query(frame))
        normalized = payload["battle_control_snapshot"]
        require_equal(normalized.get(LOSS_KEY), expected, name + ".registered_inputs")
        for side_name in ("attacker", "defender"):
            require_equal(normalized[side_name]["stored_levy_current_fighting_raw"],
                          frame[side_name]["stored_levy_current_fighting_raw"],
                          name + ".observed_side_A0")
        normalized_cases.append({"name": name, "status": "GREEN",
                                 "loss_inputs": normalized[LOSS_KEY],
                                 "existing_battle_control_ready": payload["battle_control_ready"]})
    require(observed_zero and observed_nonzero,
            "resolved primary fixture did not retain zero and nonzero getters")
    require(null_rows == 2, "unbound primary getter null rows missing")
    result = {"status": "GREEN", "readiness": "static-ready", "python_optimized": True,
              "registered_tool": TOOL, "capability": CAPABILITY,
              "registered_mcp_client_calls": 2, "native_cases": normalized_cases,
              "zero_getter_observed": observed_zero,
              "nonzero_getter_observed": observed_nonzero,
              "unbound_getter_null_rows": null_rows,
              "semantics": "Readonly primary levy-damage getter and observed side+A0 current inputs; no outgoing routine or historical loss claim.",
              "unresolved_primary_available_frame_claimed": False,
              "old_pair_absence_validation": "reused P1 sole focused receipt; no duplicate compatibility query",
              "native_json": pin(native_path), "live_game_calls": 0,
              "python_adapter": pin(args.python_projection_root.resolve() /
                  "ck3_autonomous_player/src/xar_autoplayer/bridge/battle_control_contract.py"),
              "old_test_cases_run": 0, "window_operations": 0}
    args.python_result.resolve().write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "GREEN", "native_cases": 2,
                     "registered_mcp_client_calls": 2,
                     "result": pin(args.python_result.resolve())}))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--python-projection-root", type=Path, required=True)
    parser.add_argument("--build-dir", type=Path)
    parser.add_argument("--compiler", type=Path,
                        help="optional compiler override; default is the existing MSVC bootstrap")
    parser.add_argument("--source", action="append", type=Path, default=[])
    parser.add_argument("--include-dir", action="append", type=Path, default=[])
    parser.add_argument("--define", action="append", default=[])
    parser.add_argument("--python-check-only", action="store_true")
    parser.add_argument("--native-dir", type=Path)
    parser.add_argument("--python-result", type=Path)
    args = parser.parse_args()
    if args.python_check_only:
        require(args.native_dir is not None and args.python_result is not None,
                "Python check requires native-dir and python-result")
        return python_check(args)
    require(args.build_dir is not None and args.source,
            "native run requires build-dir and source translation units")
    output = args.build_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    wire = output / "wire"
    wire.mkdir()
    executable = output / "battle-primary-levy-damage-inputs-focused.exe"
    sources = [path.resolve() for path in args.source]
    includes = [path.resolve() for path in args.include_dir]
    fallback_include = args.project_root.resolve() / "ck3_autonomous_player/native_bridge/include"
    if fallback_include not in includes:
        includes.append(fallback_include)
    report = {"schema": "ck3-12003-battle-primary-levy-damage-inputs-focused/v1",
              "status": "HARNESS-RED", "readiness": "source-ready",
              "source_pins": [pin(path) for path in sources],
              "runner": pin(Path(__file__).resolve()), "compile_exit": None,
              "run_exit": None, "python_exit": None, "whole_dll_built": False,
              "local_ck3_touched": False, "live_game_calls": 0, "window_operations": 0,
              "git_mutations": 0}
    started = time.perf_counter()
    try:
        environment = build_native(args, output, executable, sources, includes, report)
        report["status"] = "FIXTURE-RED"
        native_wire_arg = (compiler_path(wire) if args.compiler is not None and
                           args.compiler.name.lower() != "cl.exe" else str(wire))
        ran = subprocess.run([str(executable), native_wire_arg], cwd=output, env=environment,
                             capture_output=True, timeout=30,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        (output / "run.log").write_bytes(ran.stdout + ran.stderr)
        report.update(run_exit=ran.returncode, run_log=pin(output / "run.log"),
                      executable=pin(executable))
        require(ran.returncode == 0, "production loss-input native fixture failed")
        python_command = [sys.executable, "-O", str(Path(__file__).resolve()),
                          "--python-check-only", "--project-root", str(args.project_root.resolve()),
                          "--python-projection-root", str(args.python_projection_root.resolve()),
                          "--native-dir", str(wire),
                          "--python-result", str(output / "REGISTERED-MCP-RESULT.json")]
        checked = subprocess.run(python_command, cwd=output, env=environment,
                                 capture_output=True, timeout=60,
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        (output / "python.log").write_bytes(checked.stdout + checked.stderr)
        report.update(python_argv=python_command, python_exit=checked.returncode,
                      python_log=pin(output / "python.log"))
        require(checked.returncode == 0, "registered Python -O parser fixture failed")
        report["registered_mcp_result"] = pin(output / "REGISTERED-MCP-RESULT.json")
        report["native_json"] = [pin(path) for path in sorted(wire.glob("*.json"))]
        report.update(status="GREEN", readiness="static-ready")
    except Exception as error:
        report["error"] = repr(error)
    report["elapsed_seconds"] = time.perf_counter() - started
    receipt = output / "RESULT.json"
    receipt.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "receipt": pin(receipt),
                      "error": report.get("error")}, indent=2))
    return 0 if report["status"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
