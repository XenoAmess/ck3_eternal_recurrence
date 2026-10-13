"""Connected fresh SDK handshake checks using fake processes and MCP only."""

from __future__ import annotations

import argparse
from contextlib import asynccontextmanager
import copy
import ctypes
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest import mock

from g2_saved_campaign import sdk_process_custody as custody


QUEUE_SOURCE = SUPERVISOR_SOURCE = ARTIFACT_ROOT = None
REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_EXECUTABLE = str(Path(sys._base_executable).resolve())
DEPENDENCY_ROOT = str((Path(sys.prefix) / "Lib/site-packages").resolve())
PAIR = [
    {"role": "sdk_queue", "pid": 4101, "creation_filetime": 134363025952867701,
     "executable": BASE_EXECUTABLE},
    {"role": "sdk_application", "pid": 4102, "creation_filetime": 134363025952867702,
     "executable": BASE_EXECUTABLE},
]


def load_source(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class FreshSdkHandshakeTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        if None in (QUEUE_SOURCE, SUPERVISOR_SOURCE, ARTIFACT_ROOT):
            raise unittest.SkipTest("explicit queue/supervisor/artifact paths required")
        with mock.patch.object(ctypes, "WinDLL", create=True,
                               side_effect=AssertionError("native API forbidden during import")), \
                mock.patch.object(subprocess, "Popen",
                                  side_effect=AssertionError("process launch forbidden during import")):
            cls.queue_module = load_source("g2_handshake_queue_under_test", QUEUE_SOURCE)
            cls.supervisor = load_source("g2_handshake_supervisor_under_test", SUPERVISOR_SOURCE)

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(dir=ARTIFACT_ROOT, prefix="fake-handshake-")
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.events = []
        self.generations = []
        self.pair = {}
        self.initialize_count = 0
        self.clock = datetime.now(timezone.utc)
        original_path = list(sys.path)
        self.addCleanup(lambda: sys.path.__setitem__(slice(None), original_path))
        for target, attribute in ((ctypes, "WinDLL"), (subprocess, "Popen"),
                                  (subprocess, "run")):
            self.patch(target, attribute, create=True,
                       side_effect=AssertionError("real process or Win32 access forbidden"))
        for name, value in {"N": self.root, "Q": self.root / "sdk-session01",
                            "INBOX": self.root / "requests", "OUTBOX": self.root / "responses",
                            "FLAGS_SOURCE": self.root / "flags.py"}.items():
            self.patch(self.queue_module, name, value)
        self.patch(self.supervisor, "N", self.root)
        self.patch(self.queue_module, "now", lambda: self.clock)
        self.patch(self.supervisor, "now", lambda: self.clock)
        self.patch(self.queue_module.os, "getpid", lambda: PAIR[0]["pid"])
        self.patch_modules({"root_fresh_supervisor": self.supervisor})
        self.write_json("ROOT-FINAL-SDK-FREEZE.json", {
            "source_root": str(self.root / "sdk-source/src")})
        self.write_json("ROOT-CLEAN-SOURCE-FROZEN.json", {"repo": str(REPO_ROOT)})
        (self.root / "flags.py").write_text("FLAGS = []\n", encoding="utf-8")
        self.generation_type = self.fake_generation_type()
        original_write = self.supervisor.write

        def observed_write(path, value):
            if path.name == "ROOT-ACTUAL-SDK-PROCESSES-PINNED.json":
                self.events.append("pin_written")
                self.assertEqual(set(self.pair), {"sdk_queue", "sdk_application"})
                self.assertTrue(all(generation.live_checked for generation in self.pair.values()))
            return original_write(path, value)

        self.patch(self.supervisor, "write", observed_write)

    def patch(self, target, attribute, *args, **kwargs):
        patcher = mock.patch.object(target, attribute, *args, **kwargs)
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def patch_modules(self, values):
        patcher = mock.patch.dict(sys.modules, values)
        patcher.start()
        self.addCleanup(patcher.stop)

    def write_json(self, name, value):
        (self.root / name).write_text(json.dumps(value), encoding="utf-8")

    def read_json(self, name):
        return json.loads((self.root / name).read_text(encoding="utf-8"))

    def fake_generation_type(self):
        owner = self

        class FakeGeneration:
            def __init__(self, identity):
                self.row = copy.deepcopy(identity)
                self.live_checked = False
                self.closed = 0
                self.signaled = False
                self.exit_code = 259

            @classmethod
            def capture(cls, pid, *, expected_executable=None, expected_creation_filetime=None):
                owner.events.append(f"capture:{pid}")
                row = next(value for value in PAIR if value["pid"] == pid)
                owner.assertEqual(expected_executable, row["executable"])
                if expected_creation_filetime is not None:
                    owner.assertEqual(expected_creation_filetime, row["creation_filetime"])
                generation = cls(row)
                owner.generations.append(generation)
                return generation

            def identity(self, role):
                return {**self.row, "role": role}

            def require_live(self):
                owner.events.append(f"live:{self.row['pid']}")
                owner.assertFalse(self.signaled)
                self.live_checked = True
                return self.observe()

            def observe(self):
                return {key: value for key, value in self.row.items() if key != "role"} | {
                    "kernel_exit_observed": self.signaled, "wait_result": 0 if self.signaled else 258,
                    "exit_code": self.exit_code, "observation_error": None}

            def close(self):
                self.closed += 1

            def __enter__(self):
                return self

            def __exit__(self, *args):
                self.close()

        return FakeGeneration

    def retain_pair(self):
        self.write_json("ROOT-ACTUAL-SDK-PROCESS-GENERATIONS.json", {"processes": PAIR})
        self.supervisor.retain_sdk_pair(self.pair, self.generation_type)

    async def run_main(self, pin_mode):
        owner = self
        capture = SimpleNamespace(generation=None)

        def require_generation():
            if capture.generation is None:
                raise AssertionError("stdio child was not captured")
            return capture.generation

        capture.require_generation = require_generation

        @asynccontextmanager
        async def retained(stdio, *, expected_executable):
            owner.assertEqual(expected_executable, BASE_EXECUTABLE)
            try:
                yield capture
            finally:
                if capture.generation is not None:
                    capture.generation.close()

        @asynccontextmanager
        async def stdio_client(parameters, *, errlog):
            owner.events.append("stdio_child_created")
            owner.assertEqual(parameters.command, BASE_EXECUTABLE)
            owner.assertEqual(parameters.args[:4], ["-B", "-S", "-X", "utf8"])
            owner.assertEqual(parameters.env, {"XAR_FRESH_SDK_DEPENDENCY_ROOT": DEPENDENCY_ROOT})
            capture.generation = owner.generation_type.capture(
                PAIR[1]["pid"], expected_executable=BASE_EXECUTABLE)
            yield (object(), object())
            owner.events.append("stdio_context_closed")

        class FakeClientSession:
            def __init__(self, *streams):
                owner.assertEqual(len(streams), 2)

            async def __aenter__(self):
                owner.events.append("session_entered")
                return self

            async def __aexit__(self, *args):
                owner.events.append("session_closed")

            async def initialize(self):
                owner.initialize_count += 1
                owner.events.append("initialize")
                owner.supervisor.validate_sdk_pin(PAIR, owner.read_json(
                    "ROOT-ACTUAL-SDK-PROCESSES-PINNED.json"))
                (owner.root / "sdk-session01/EXIT-SDK").write_text("fixture stop", encoding="utf-8")
                return SimpleNamespace(model_dump=lambda **kwargs: {"fixture": True})

        class FakeQueue:
            def __init__(self, args):
                self.launch = {"pipe": r"\\.\pipe\fixture-handshake", "pid": 9001,
                               "creation_date": "fixture-only-not-a-process-observation"}
                self.flags = []
                self.frozen_head = "0" * 40
                self.deadline = owner.clock + timedelta(seconds=1)
                self.admission = {"review_at_utc": "2026-10-13T16:58:39.018273+00:00"}
                self.next_sequence = 1
                self.held_control = self.halted = None

            def guard(self, **kwargs):
                raise AssertionError("fixture exits before gameplay loop")

        fake_mcp = ModuleType("mcp")
        fake_mcp.ClientSession = FakeClientSession
        fake_mcp.StdioServerParameters = lambda **kwargs: SimpleNamespace(**kwargs)
        fake_client = ModuleType("mcp.client")
        fake_stdio = ModuleType("mcp.client.stdio")
        fake_stdio.stdio_client = stdio_client
        fake_client.stdio = fake_stdio
        fake_mcp.client = fake_client
        self.patch_modules({"mcp": fake_mcp,
            "mcp.client": fake_client, "mcp.client.stdio": fake_stdio})
        self.patch(custody, "RetainedProcessGeneration", self.generation_type)
        self.patch(custody, "retain_mcp_stdio_process", retained)
        self.patch(self.queue_module, "FreshQueue", FakeQueue)
        original_atomic = self.queue_module.atomic

        def connected_atomic(path, value, **kwargs):
            original_atomic(path, value, **kwargs)
            if path.name == "ROOT-ACTUAL-SDK-PROCESS-GENERATIONS.json":
                self.events.append("generations_written")
                self.assertIs(value["rpc_started"], False)
                self.assertEqual(value["processes"], PAIR)
                if pin_mode != "missing":
                    self.supervisor.retain_sdk_pair(self.pair, self.generation_type)
                if pin_mode == "mismatch":
                    ack = self.read_json("ROOT-ACTUAL-SDK-PROCESSES-PINNED.json")
                    ack["processes"][1]["creation_filetime"] += 1
                    self.write_json("ROOT-ACTUAL-SDK-PROCESSES-PINNED.json", ack)

        async def advance_clock(seconds):
            self.clock += timedelta(seconds=seconds)

        self.patch(self.queue_module, "atomic", connected_atomic)
        self.patch(self.queue_module.asyncio, "sleep", advance_clock)
        args = SimpleNamespace(environment_manifest=self.root / "environment.json")
        with mock.patch("sys.stdout", new=io.StringIO()):
            return await self.queue_module.main(args)

    async def test_actual_main_initializes_only_after_exact_supervisor_pin(self):
        self.assertEqual(await self.run_main("valid"), 0)
        self.assertEqual(self.initialize_count, 1)
        self.assertLess(self.events.index("generations_written"), self.events.index("pin_written"))
        self.assertLess(self.events.index("pin_written"), self.events.index("initialize"))
        self.assertEqual(len(self.generations), 4)
        self.assertEqual(self.read_json("sdk-session01/ROOT-FRESH-SDK-ARGV.json")["argv"][:5],
                         [BASE_EXECUTABLE, "-B", "-S", "-X", "utf8"])
        self.assertTrue((self.root / "sdk-session01/ROOT-FRESH-SDK-INITIALIZED.json").is_file())
        self.assertIs(self.read_json("sdk-session01/ROOT-QUEUE-CLOSED.json")[
            "sdk_application_exit_code_observed"], False)

    async def test_actual_main_mismatched_pin_submits_zero_initialize(self):
        self.assertEqual(await self.run_main("mismatch"), 1)
        self.assertEqual(self.initialize_count, 0)
        self.assertNotIn("session_entered", self.events)
        self.assertFalse((self.root / "sdk-session01/ROOT-FRESH-SDK-INITIALIZED.json").exists())
        self.assertIs(self.read_json("sdk-session01/ROOT-QUEUE-HALTED.json")["replay_allowed"], False)

    async def test_actual_main_missing_pin_submits_zero_initialize(self):
        self.assertEqual(await self.run_main("missing"), 1)
        self.assertEqual(self.initialize_count, 0)
        self.assertEqual(self.pair, {})
        self.assertNotIn("session_entered", self.events)
        self.assertEqual(self.read_json("sdk-session01/ROOT-QUEUE-HALTED.json")["error_type"], "TimeoutError")

    async def test_supervisor_opens_both_generations_before_ack_without_reopening(self):
        self.retain_pair()
        ack = self.read_json("ROOT-ACTUAL-SDK-PROCESSES-PINNED.json")
        self.assertTrue(self.supervisor.validate_sdk_pin(PAIR, ack))
        self.assertEqual(self.events, ["capture:4101", "capture:4102", "live:4101", "live:4102", "pin_written"])
        self.supervisor.retain_sdk_pair(self.pair, self.generation_type)
        self.assertEqual(len(self.generations), 2)

    async def test_queue_exit_zero_with_application_live_emits_no_exit_receipt(self):
        self.assertEqual(await self.run_main("valid"), 0)
        self.pair["sdk_queue"].signaled = True
        self.pair["sdk_queue"].exit_code = 0
        self.assertIsNone(self.supervisor.observe_retained_sdk_exit(self.pair))
        self.assertFalse((self.root / "ROOT-ACTUAL-SDK-PROCESSES-EXITED.json").exists())
        self.assertEqual(len(self.generations), 4)

    async def test_both_signals_with_actual_nonzero_exit_are_observed_abnormal(self):
        self.retain_pair()
        for generation in self.pair.values():
            generation.signaled = True
            generation.exit_code = 0
        self.pair["sdk_application"].exit_code = 259
        result = self.supervisor.observe_retained_sdk_exit(self.pair)
        self.assertEqual(result["status"], "ACTUAL_BOTH_SDK_EXITS_OBSERVED")
        self.assertIs(result["normal"], False)
        receipt = self.read_json("ROOT-ACTUAL-SDK-PROCESSES-EXITED.json")
        self.assertIs(receipt["wrapper_exit_inferred"], False)
        self.assertTrue(all(row["kernel_exit_observed"] for row in receipt["processes"]))
        self.assertEqual(receipt["processes"][1]["exit_code"], 259)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue-source", type=Path, required=True)
    parser.add_argument("--supervisor-source", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--storage-admission", type=Path, required=True)
    args, remaining = parser.parse_known_args()
    QUEUE_SOURCE = args.queue_source.resolve(strict=True)
    SUPERVISOR_SOURCE = args.supervisor_source.resolve(strict=True)
    ARTIFACT_ROOT = args.artifact_root.resolve()
    admission = json.loads(args.storage_admission.read_text(encoding="utf-8-sig"))
    review = datetime.fromisoformat(admission["review_at_utc"].replace("Z", "+00:00"))
    if review.tzinfo is None or datetime.now(timezone.utc) >= review:
        raise RuntimeError("original storage admission expired; no extension")
    if not any(ARTIFACT_ROOT.is_relative_to(Path(root).resolve())
               for root in admission["approved_output_roots"]):
        raise RuntimeError("test artifacts must remain within original admitted root")
    volume_root = ARTIFACT_ROOT
    while not volume_root.exists():
        volume_root = volume_root.parent
    free_start = shutil.disk_usage(volume_root).free
    required = sum(admission[key] for key in ("this_write_peak", "other_unspent_reservations",
                                              "system_growth_reserve", "safety_margin"))
    if admission.get("status") != "ADMITTED" or free_start < required:
        raise RuntimeError("original capacity reservation is no longer satisfied")
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    if any(ARTIFACT_ROOT.iterdir()):
        raise RuntimeError("a new empty handshake attempt directory is required")
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromNames(remaining) if remaining else \
        unittest.defaultTestLoader.loadTestsFromTestCase(FreshSdkHandshakeTests)
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    log = stream.getvalue()
    receipt = {"status": "GREEN" if result.wasSuccessful() else "RED", "tests_run": result.testsRun,
        "failures": len(result.failures), "errors": len(result.errors),
        "at_utc": datetime.now(timezone.utc).isoformat(), "game_sdk_steam_window_executed": False,
        "scope": "actual queue main and supervisor retain/observe; fake custody/MCP/session; tiny temporary files",
        "source_pins": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in (QUEUE_SOURCE, SUPERVISOR_SOURCE, Path(__file__))},
        "review_at_utc_unchanged": admission["review_at_utc"], "runtime_credit": False,
        "capacity": {"free_bytes_start": free_start, "required_free_bytes": required,
                     "free_bytes_close": shutil.disk_usage(ARTIFACT_ROOT).free,
                     "original_peak_bytes_unchanged": admission["this_write_peak"]}}
    encoded = json.dumps(receipt, indent=2) + "\n"
    if len(log.encode("utf-8")) + len(encoded.encode("utf-8")) > 1024**2:
        raise RuntimeError("handshake evidence exceeds 1 MiB lane cap")
    for name, payload in (("unittest.log", log), ("result.json", encoded)):
        with (ARTIFACT_ROOT / name).open("x", encoding="utf-8") as output:
            output.write(payload)
    print(log, end="")
    print(encoded, end="")
    raise SystemExit(0 if result.wasSuccessful() else 1)
