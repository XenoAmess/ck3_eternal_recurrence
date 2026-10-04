"""Run one strict native loss-input fixture and its registered MCP parser check.

The native fixture supplies synthetic memory observations. The Python check calls
the existing registered battle-control tool in process and retains old-body
compatibility. Checks use runtime exceptions so Python -O and C++ NDEBUG keep
the verification active. This runner does not build or load the native DLL.
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
GLOBAL_RAW_KEYS = (
    "stored_advantage_damage_factor_raw", "runtime_damage_scaling_raw",
    "runtime_main_hard_conversion_raw", "runtime_pursuit_hard_conversion_raw",
    "province_winter_hard_conversion_modifier_raw",
)
SIDE_RAW_KEYS = (
    "outgoing_advantage_factor_raw", "own_hard_conversion_modifier_raw",
    "opposing_hard_conversion_modifier_raw",
)
EFFECTIVE_ENTRY_KEYS = (
    "effective_max_size", "effective_siege_raw", "effective_damage_raw",
    "effective_toughness_raw", "effective_pursuit_raw", "effective_screen_raw",
)


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
    helper = load_module("effective_loss_msvc_bootstrap", helper_path)
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
        return {"format_version": 1, "backend_id": "effective-loss-fixture",
                "source": "named-pipe", "snapshot": True,
                "wait_for_change": False, "action_steps": [self.step],
                "bridge_capabilities": [CAPABILITY]}

    def take_snapshot(self) -> dict[str, object]:
        return {"format_version": 1, "snapshot_id": "effective-loss-fixture:4",
                "revision": 4, "native_revision": self.frame["snapshot_revision"],
                "source": "named-pipe", "backend_id": "effective-loss-fixture",
                "date_raw": self.frame["observed_date_raw"], "paused": True,
                "episode_run_id": "effective-loss-fixture",
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
                  "backend_id": "effective-loss-fixture",
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
    # Native frames are passed through the real registered route. The old-body
    # check removes only the additive block from an otherwise identical frame.
    return check_loss_cases(args)


def check_loss_cases(args: argparse.Namespace) -> int:
    native_path = args.native_dir.resolve() / "effective_loss_input_cases.json"
    document = json.loads(native_path.read_text(encoding="utf-8"))
    require(type(document.get("schema_version")) is int and document["schema_version"] == 1,
            "new native fixture schema is not version 1")
    require(type(document.get("actual")) is int and document["actual"] == 0,
            "focused fixture must identify its synthetic observations")
    cases = document.get("cases")
    require(isinstance(cases, list) and len(cases) > 0,
            "new native fixture emitted no loss-input cases")
    normalized_cases = []
    signed_q = []
    unavailable_values = 0
    effective_rows_checked = 0
    baseline = None

    for case in cases:
        require(isinstance(case, dict) and isinstance(case.get("name"), str),
                "native fixture case has no name")
        name = case["name"]
        frame = case.get("battle_control_snapshot")
        require(isinstance(frame, dict) and LOSS_KEY in frame,
                name + ": native frame omitted the additive input block")
        require("expected_loss_inputs_v1" in case,
                name + ": native fixture omitted its independent expected values")
        expected = case["expected_loss_inputs_v1"]
        require_equal(frame[LOSS_KEY], expected, name + ".native_expected")
        if expected is None:
            unavailable_values += 1
        else:
            require(isinstance(expected, dict), name + ": invalid expected input block")
            require(type(expected.get("scale")) is int and expected["scale"] == 100000,
                    name + ": native Q scale changed")
            require_equal(expected["source_combat_id"], frame["combat_id"],
                          name + ".source_combat_id")
            require_equal(expected["source_target_province_id"], frame["province_id"],
                          name + ".source_target_province_id")
            sides = expected.get("sides")
            require(isinstance(sides, list) and len(sides) == 2,
                    name + ": native input block lost either ordered side")
            raw_values = [expected[key] for key in GLOBAL_RAW_KEYS]
            for index, side in enumerate(sides):
                require(isinstance(side, dict), name + ": native side is not an object")
                require_equal(side.get("side_index"), index,
                              f"{name}.sides[{index}].side_index")
                raw_values.extend(side[key] for key in SIDE_RAW_KEYS)
            for raw in raw_values:
                if raw is None:
                    unavailable_values += 1
                else:
                    require(type(raw) is int and -(1 << 63) <= raw < (1 << 63),
                            name + ": native Q is not an exact signed int64")
                    signed_q.append(raw)
            require(type(expected.get("province_has_holding")) is bool,
                    name + ": native holding value is not a boolean")
            if not expected["province_has_holding"]:
                require_equal(expected["province_winter_hard_conversion_modifier_raw"], 0,
                              name + ".nonholding_winter_zero")

        payload = asyncio.run(registered_query(frame))
        normalized = payload["battle_control_snapshot"]
        require(LOSS_KEY in normalized, name + ": registered route dropped new inputs")
        require_equal(normalized[LOSS_KEY], expected, name + ".registered_inputs")
        if baseline is None:
            baseline = copy.deepcopy(normalized)
        for side_name in ("attacker", "defender"):
            original_side = frame[side_name]
            projected_side = normalized[side_name]
            for bucket in ("levy_entries", "men_at_arms_entries"):
                original_rows = original_side[bucket]
                projected_rows = projected_side[bucket]
                require(len(projected_rows) == len(original_rows),
                        name + ": existing entry count changed")
                for index, original in enumerate(original_rows):
                    for field in EFFECTIVE_ENTRY_KEYS:
                        require_equal(projected_rows[index][field], original[field],
                                      f"{name}.{side_name}.{bucket}[{index}].{field}")
                    effective_rows_checked += 1
        normalized_cases.append({"name": name, "status": "GREEN",
                                 "loss_inputs": normalized[LOSS_KEY],
                                 "existing_battle_control_ready": payload["battle_control_ready"]})

    require(any(raw < 0 for raw in signed_q), "new fixture did not cover signed negative Q")
    require(any(raw == 0 for raw in signed_q), "new fixture did not cover observed zero Q")
    require(unavailable_values > 0, "new fixture did not cover native unavailable values")
    old_frame = copy.deepcopy(cases[0]["battle_control_snapshot"])
    del old_frame[LOSS_KEY]
    old_payload = asyncio.run(registered_query(old_frame))
    old_normalized = old_payload["battle_control_snapshot"]
    require(LOSS_KEY not in old_normalized,
            "old body gained an invented null loss-input field")
    require(isinstance(baseline, dict), "native cases produced no baseline body")
    del baseline[LOSS_KEY]
    require_equal(old_normalized, baseline, "additive_old_body_compatibility")
    result = {"status": "GREEN", "readiness": "static-ready", "python_optimized": True,
              "registered_tool": TOOL, "capability": CAPABILITY,
              "registered_mcp_client_calls": len(cases) + 1,
              "native_cases": normalized_cases, "old_body_compatibility": "GREEN",
              "negative_q_observed": True, "zero_q_observed": True,
              "native_unavailable_values": unavailable_values,
              "existing_effective_rows_checked": effective_rows_checked,
              "semantics": "Current paused native casualty-allocation inputs; no previous-tick measured damage.",
              "native_json": pin(native_path), "live_game_calls": 0,
              "python_adapter": pin(args.python_projection_root.resolve() /
                  "ck3_autonomous_player/src/xar_autoplayer/bridge/battle_control_contract.py"),
              "old_test_cases_run": 0, "window_operations": 0}
    args.python_result.resolve().write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "GREEN", "native_cases": len(cases),
                      "old_body_compatibility": "GREEN", "result": pin(args.python_result.resolve())}))
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
    executable = output / "battle-effective-loss-inputs-focused.exe"
    sources = [path.resolve() for path in args.source]
    includes = [path.resolve() for path in args.include_dir]
    fallback_include = args.project_root.resolve() / "ck3_autonomous_player/native_bridge/include"
    if fallback_include not in includes:
        includes.append(fallback_include)
    report = {"schema": "ck3-12003-battle-effective-loss-inputs-focused/v1",
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
