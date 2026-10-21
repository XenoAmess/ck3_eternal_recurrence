"""Real MCP registration regression. Optional physical SDK mode never changes runtime."""
from __future__ import annotations

import argparse
import ast
import asyncio
from collections.abc import Awaitable, Callable
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import importlib
import inspect
import json
import os
from pathlib import Path
import sys
import textwrap
from types import FrameType
from typing import Protocol, cast
import unittest
from unittest.mock import patch

OWN = Path(__file__).resolve().parents[2]
REPO = OWN.parent.parent
PRODUCER = OWN / "prepare_source31_a18_cold_union_v1.py"
CANDIDATE = OWN / "candidates/native32_runtime_journal_adapter_20261021"
TOOL = "ck3_observe_native32_time_command_journal_v1"
BEFORE = "from xar_autoplayer.mcp_server import _forbid_unknown_tool_arguments_v1"
AFTER = "from xar_autoplayer.bridge.mcp_server import _forbid_unknown_tool_arguments_v1"
BINDING = "ROOT-NATIVE32-PRODUCTION-BINDING01.json"
Doc = dict[str, object]
DLL_HANDLES: list[object] = []

class Dynamic(Protocol):
    def __call__(self, *args: object, **kwargs: object) -> object: ...

def obj(value: object) -> Doc:
    if not isinstance(value, dict):
        raise ValueError("JSON object required")
    out: Doc = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("text key required")
        out[key] = item
    return out

def method(value: object, name: str) -> Dynamic:
    found: object = getattr(value, name, None)
    if not callable(found):
        raise ValueError("callable runtime boundary: " + name)
    return cast(Dynamic, found)  # Checked optional MCP boundary.

def encoded(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()

def reference(path: Path, raw: bytes) -> Doc:
    return {"path": str(path.resolve()), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}

def render_registration_v1(source: str) -> str:
    """Execute the actual producer's three bounded render expressions."""
    node = next(n for n in ast.parse(source).body
                if isinstance(n, ast.FunctionDef) and n.name == "native32_source_stage_v2")
    selected: list[ast.stmt] = [n for n in node.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id in
                        ("expected", "pins_literal", "registration") for t in n.targets)]
    if len(selected) != 3:
        raise ValueError("three exact producer expressions required")
    module = ast.Module(body=selected, type_ignores=[])
    ast.fix_missing_locations(module)
    namespace: Doc = {"NATIVE32_OBSERVER_BINDING_NAME": BINDING}
    exec(compile(module, "<actual Native32 producer render>", "exec"), namespace)
    result = namespace["registration"]
    if type(result) is not str:
        raise ValueError("generated registration text required")
    return textwrap.dedent(result)

@dataclass(frozen=True)
class Fixture:
    sdk_root: Path
    runtime_root: Path
    machine_id: str
    physical: bool = False

FIXTURE = Fixture(REPO / "ck3_autonomous_player/src", CANDIDATE,
                  "software-registration-fixture")

async def awaited(value: object) -> object:
    if not inspect.isawaitable(value):
        raise ValueError("actual MCP async result required")
    result: object = await value
    return result

class Native32EntryRegistrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = FIXTURE
        self.runtime = self.fixture.runtime_root.resolve(strict=True)
        sys.path[:0] = [str(self.runtime), str(self.fixture.sdk_root.resolve(strict=True))]
        self.sdk = importlib.import_module("xar_autoplayer.bridge.mcp_server")
        origin: object = getattr(self.sdk, "__file__", None)
        if type(origin) is not str:
            raise ValueError("actual SDK file origin required")
        self.assertEqual(Path(origin).resolve(),
                         self.fixture.sdk_root.resolve() / "xar_autoplayer/bridge/mcp_server.py")
        self.server_module = importlib.import_module("mcp.server")
        self.source = PRODUCER.read_text(encoding="utf8")
        self.assertEqual(self.source.count(AFTER), 1)
        self.assertEqual(self.source.count(BEFORE), 0)
        self.registration = render_registration_v1(self.source)
        self.old = render_registration_v1(self.source.replace(AFTER, BEFORE))
        self.assertEqual(self.registration, self.old.replace(BEFORE, AFTER))
        self.calls: list[str] = []
        self.previous_profile = sys.getprofile()
        sys.setprofile(self.profile)

    def tearDown(self) -> None:
        sys.setprofile(self.previous_profile)
        self.assertEqual(self.calls, [])

    def profile(self, frame: FrameType, event: str, argument: object) -> None:
        if event == "call" and frame.f_code.co_name in (
                "ensure_received_provider_v1", "qualify_native32_binding_v1",
                "read_native32_once_v1"):
            self.calls.append(frame.f_code.co_name)

    def server(self) -> object:
        return method(self.server_module, "MCPServer")(
            name="Native32 generated registration software fixture", version="1")

    def run_registration(self, source: str, server: object, *, owner_present: bool = True) -> None:
        @dataclass
        class Owner:
            machine: str
        @dataclass
        class Driver:
            _player_heir_candidate_owner_v1: object
        owner = Owner(self.fixture.machine_id)
        driver = Driver(owner if owner_present else None)
        scope: Doc = {"N": self.runtime, "Path": Path, "json": json, "driver": driver,
                      "_canonical": object(), "server": server}
        # CI has real physical SDK/adapter/MCP modules. Only the two JSON inputs
        # are in memory; physical mode reads every input from its actual path.
        raw_binding = encoded({
            "schema": "xar.native32.source31-production-observer-binding/v2",
            "machine_id": self.fixture.machine_id,
            "status": "COLD_SOURCE_BOUND_NOT_RUNTIME_ADMITTED",
            **{name: reference(CANDIDATE / "native32_mcp_extension_v1.py",
                              (CANDIDATE / "native32_mcp_extension_v1.py").read_bytes())
               for name in ("sdk_base_ref", "sdk_anchor_ref", "production_result_ref",
                            "production_input_manifest_ref", "dll", "sealed_parser_source")}})
        records = {self.runtime / BINDING: raw_binding,
                   self.runtime / "ROOT-NATIVE30-NATIVE-PIN-C23-A15.json":
                       encoded({"native32_observer_binding":
                                reference(self.runtime / BINDING, raw_binding)})}
        original = Path.read_bytes
        def read(path: Path) -> bytes:
            return records[path] if path in records else original(path)
        context = nullcontext() if self.fixture.physical else patch.object(Path, "read_bytes", read)
        with context:
            exec(compile(source, "<actual emitted Native32 registration>", "exec"), scope)

    def test_old_generated_import_is_red(self) -> None:
        server = self.server()
        with self.assertRaises(ModuleNotFoundError) as caught:
            self.run_registration(self.old, server)
        self.assertEqual(caught.exception.name, "xar_autoplayer.mcp_server")
        manager: object = getattr(server, "_tool_manager")
        self.assertIsNone(method(manager, "get_tool")(TOOL))

    def test_actual_sdk_registration_and_extra_arguments(self) -> None:
        server = self.server()
        self.run_registration(self.registration, server)
        manager: object = getattr(server, "_tool_manager")
        tool = method(manager, "get_tool")(TOOL)
        self.assertIsNotNone(tool)
        parameters = obj(getattr(tool, "parameters"))
        self.assertIs(parameters["additionalProperties"], False)
        self.assertEqual(parameters.get("properties", {}), {})
        errors = importlib.import_module("mcp.server.mcpserver.exceptions")
        error_type: object = getattr(errors, "ToolError")
        self.assertTrue(isinstance(error_type, type) and issubclass(error_type, Exception))
        try:
            asyncio.run(awaited(method(server, "call_tool")(TOOL, {"step": "forbidden"})))
        except Exception as error:
            self.assertIs(type(error), error_type)
            self.assertIn("extra_forbidden", str(error))
        else:
            self.fail("real MCP accepted an extra public argument")

    def test_missing_original_owner_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "original canonical owner"):
            self.run_registration(self.registration, self.server(), owner_present=False)

def main() -> None:
    global FIXTURE
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--sdk-base", type=Path)
    parser.add_argument("--runtime-root", type=Path)
    args = parser.parse_args()
    if bool(args.sdk_base) != bool(args.runtime_root):
        raise ValueError("physical mode needs both actual BASE and runtime paths")
    if args.sdk_base is not None and args.runtime_root is not None:
        base = obj(json.loads(args.sdk_base.read_bytes()))
        if (base.get("schema") != "root.ck3.final-sdk-freeze/v1"
                or base.get("status") != "FINAL_SOURCE_FROZEN"
                or type(base.get("source_file_count")) is not int
                or base["source_file_count"] != 1466 or base.get("runtime_admitted") is not False):
            raise ValueError("actual single Source31 BASE required")
        root = base.get("source_root")
        machine = base.get("machine_id")
        if type(root) is not str or type(machine) is not str or not machine:
            raise ValueError("Source31 source/machine identity required")
        FIXTURE = Fixture(Path(root), args.runtime_root, machine, True)
        freeze = obj(json.loads((args.runtime_root / "ROOT-FINAL-SDK-FREEZE-P37C23-A15.json").read_bytes()))
        policy_ref = obj(freeze["canonical_preload_policy"])
        policy_path = policy_ref.get("path")
        if type(policy_path) is not str:
            raise ValueError("exact policy path required")
        policy = obj(json.loads(Path(policy_path).read_bytes()))
        dependency = policy.get("dependency_root")
        if type(dependency) is not str:
            raise ValueError("actual dependency root required")
        sys.path.insert(0, dependency)
    if os.name == "nt" and sys.flags.no_site:
        site = Path(sys.executable).parent / "Lib/site-packages"
        sys.path[:0] = [str(site), str(site / "win32"), str(site / "win32/lib")]
        DLL_HANDLES.append(os.add_dll_directory(str(site / "pywin32_system32")))
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(Native32EntryRegistrationTest))
    if FIXTURE.physical:
        print(json.dumps({"machine_id": FIXTURE.machine_id,
            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            "scope": "actual physical SDK generated-registration regression only",
            "sdk_root": str(FIXTURE.sdk_root), "runtime_inputs": str(FIXTURE.runtime_root),
            "tests": result.testsRun, "errors": len(result.errors), "failures": len(result.failures),
            "runtime_qualification_granted": False, "runtime_files_modified": 0,
            "native_queries_or_Game_Task_calls": 0}, sort_keys=True))
    raise SystemExit(not result.wasSuccessful())

if __name__ == "__main__":
    main()
