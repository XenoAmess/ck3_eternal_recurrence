"""One finite deterministic qualification; no Game/Native/RPC or real waits."""
from __future__ import annotations

import ast
from datetime import datetime, timezone
import ctypes
from ctypes import wintypes
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace, ModuleType
import unittest

import prepare_candidate as prepare

MACHINE = "xenoamess-full-tower-eb9d2c1186"
CARD = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01/G2-PARALLEL-SOURCE-QUALIFICATION1MiB0630-ADMITTED01.json")
CARD_PIN = {"bytes": 4539, "sha256": "0d279e0bcc91159536b4e2c86a8079f24db195df9456a5c819d7a773ecdae1d4"}
OUT = CARD.parent / "G2-PARALLEL-QUALIFICATION0630-01/performance"
DEADLINE = datetime(2026, 10, 20, 6, 30, tzinfo=timezone.utc)
SOURCE_NAMES = ("CONTRACT.md", "exact_day_private_progress_wait_v1.py", "prepare_candidate.py", "qualify_candidate.py")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def allocated(path):
    class Standard(ctypes.Structure):
        _fields_ = [("allocation", ctypes.c_longlong), ("size", ctypes.c_longlong),
                    ("links", wintypes.DWORD), ("delete", wintypes.BOOLEAN),
                    ("directory", wintypes.BOOLEAN)]
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                       ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    create.restype = wintypes.HANDLE
    query = kernel.GetFileInformationByHandleEx
    query.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    query.restype = wintypes.BOOL
    close = kernel.CloseHandle
    close.argtypes = [wintypes.HANDLE]
    close.restype = wintypes.BOOL
    handle = create(str(path.resolve()), 0x80, 7, None, 3, 0x02000000, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        value = Standard()
        if not query(handle, 1, ctypes.byref(value), ctypes.sizeof(value)):
            raise ctypes.WinError(ctypes.get_last_error())
        return value.allocation
    finally:
        close(handle)


class Clock:
    def __init__(self):
        self.now = 0.0
    def monotonic(self):
        return self.now


class Condition:
    """Deterministic Condition.wait_for model, including repeated notifications."""
    def __init__(self, state, events):
        self.state, self.events, self.calls = state, list(events), []
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def wait_for(self, predicate, timeout):
        self.calls.append(timeout)
        end = self.state.clock.now + timeout
        if predicate():
            return True
        while self.events and self.events[0][0] <= end:
            at, action = self.events.pop(0)
            self.state.clock.now = at
            action(self.state)
            if predicate():
                return True
        self.state.clock.now = end
        return predicate()


class State:
    def __init__(self, events):
        self.clock = Clock()
        self._connected, self._connection_generation = True, 4
        self._hello = {"pid": 182100}
        self._public_revision = 1
        self._last_heartbeat = {"sequence": 100, "pid": 182100}
        self.date_raw, self.native_revision = 53274624, 10
        self._condition = Condition(self, events)
    def snapshot_supported(self):
        return True
    def snapshot(self):
        if not self._connected or self._hello["pid"] != 182100 or self._connection_generation != 4:
            raise ConnectionError("existing semantic read rejects connection boundary")
        return {"revision": self._public_revision, "native_revision": self.native_revision,
                "date_raw": self.date_raw, "paused": False,
                "episode_character_id": 40526, "episode_run_id": "native-40526-1bec95182886",
                "diagnostics": {"bridge_pid": self._hello["pid"],
                    "connection_generation": self._connection_generation,
                    "last_heartbeat": dict(self._last_heartbeat)}}


def heartbeat(sequence):
    def apply(state):
        state._last_heartbeat = {"sequence": sequence, "pid": 182100}
    return apply


def semantic(state):
    state.date_raw += 24
    state.native_revision += 1
    state._public_revision += 1


def selected_driver(raw):
    nodes = prepare.function_nodes(raw)
    state_wait = nodes["NativeProtocolState.wait_for_public_change"]
    env = {"__name__": "qualified_exact_day_driver", "__package__": "qualified_exact_day",
           "math": math, "Callable": object, "time": None,
           "start_army_timing": lambda *a, **k: None,
           "finish_army_timing": lambda *a, **k: None}
    selected = [nodes[name] for name in ("_validate_revision", "_positive_seconds")]
    methods = [nodes["NativeHeadlessGameplayDriver." + name] for name in
               ("_wait_for_life_advance_change", "_wait_for_life_advance_snapshot")]
    owner = ast.ClassDef(name="SelectedDriver", bases=[], keywords=[], body=methods,
                         decorator_list=[])
    future = ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)
    tree = ast.fix_missing_locations(ast.Module(body=[future, *selected, owner], type_ignores=[]))
    exec(compile(tree, "actual-selected-generated-methods", "exec"), env)
    state_env = {}
    tree = ast.fix_missing_locations(ast.Module(body=[state_wait], type_ignores=[]))
    exec(compile(tree, "unchanged-public-condition-method", "exec"), state_env)
    State.wait_for_public_change = state_env["wait_for_public_change"]
    return env["SelectedDriver"], env


def driver_case(cls, env, events, *, enabled=True):
    state = State(events)
    driver = cls()
    driver.state, driver.frames = state, []
    first = state.snapshot()
    progress = SimpleNamespace(identity=(182100, 4, 40526, "native-40526-1bec95182886"),
                               generation=576, closed=False, flags=0)
    progress.observed = []
    progress.observe_candidate = lambda frame: progress.observed.append(frame)
    progress.note_callback_error = lambda: (_ for _ in ()).throw(AssertionError("callback error"))
    driver._exact_clock_wait_progress_v1 = progress if enabled else None
    def snapshot():
        frame = state.snapshot()
        driver.frames.append(frame)
        return frame
    driver.take_internal_semantic_snapshot = snapshot
    env["time"] = state.clock
    return driver, state, first, progress


def main():
    if os.name != "nt" or datetime.now(timezone.utc) >= DEADLINE:
        raise RuntimeError("this machine qualification requires current Windows admission")
    card_raw = CARD.read_bytes()
    if prepare.pin(card_raw) != CARD_PIN:
        raise ValueError("actual Root budget card differs")
    card = json.loads(card_raw)
    lane = card["lanes"]["performance"]
    if (card["machine_id"] != MACHINE or lane["source_hard_bytes"] != 65536
            or lane["artifact_hard_bytes"] != 196608
            or Path(lane["artifact_root"]).resolve() != OUT.resolve()):
        raise ValueError("assigned performance lane differs")
    source_pins = {name: prepare.pin((prepare.OWN / name).read_bytes()) for name in SOURCE_NAMES}
    source_allocated = sum(allocated(prepare.OWN / name) for name in SOURCE_NAMES)
    source_overhead_bound = 4096 * (len(SOURCE_NAMES) + 1)
    if source_allocated + source_overhead_bound > 65536:
        raise ValueError("source allocation and filesystem overhead exceed lane")
    if OUT.exists():
        raise FileExistsError("unique qualification lane already exists; do not blind retry")
    OUT.mkdir(parents=True, exist_ok=False)
    original = prepare.read_input()
    outputs, patch, changed = prepare.compose(original)
    package = ModuleType("qualified_exact_day")
    package.__path__ = []
    sys.modules[package.__name__] = package
    helper = load(package.__name__ + ".exact_day_private_progress_wait_v1",
                  prepare.OWN / prepare.HELPER)
    cls, env = selected_driver(outputs["native_driver.py"])
    old_cls, old_env = selected_driver(original)
    observations = {}

    class Tests(unittest.TestCase):
        def test_01_exact_source_scope(self):
            self.assertEqual(changed, [prepare.CHANGED])
            self.assertEqual(outputs["native_driver.py"].replace(prepare.AFTER, prepare.BEFORE, 1), original)
            for name in ("NativeProtocolState.wait_for_public_change",
                         "NativeHeadlessGameplayDriver._advance_exact_day_with_sentinel",
                         "NativeHeadlessGameplayDriver._wait_for_life_advance_snapshot"):
                self.assertEqual(ast.dump(prepare.function_nodes(original)[name]),
                                 ast.dump(prepare.function_nodes(outputs["native_driver.py"])[name]))

        def test_02_counterexample_heartbeat_is_not_game_progress(self):
            events = [(n / 4, heartbeat(100 + n)) for n in range(1, 121)]
            results = []
            for current_cls, current_env in ((old_cls, old_env), (cls, env)):
                driver, state, first, progress = driver_case(current_cls, current_env, events)
                final = driver._wait_for_life_advance_snapshot(first,
                    lambda frame: frame["date_raw"] > first["date_raw"], timeout_seconds=30.0)
                self.assertEqual(final["date_raw"], first["date_raw"])
                self.assertEqual(final["revision"], 1)
                self.assertEqual(state.clock.now, 30.0)
                self.assertEqual(progress.flags, 0)
                results.append({"elapsed_seconds": state.clock.now, "candidate_reads": len(driver.frames),
                    "date_advance": 0, "public_revision": state._public_revision})
            self.assertEqual(results[0]["candidate_reads"], 1)
            self.assertEqual(results[1]["candidate_reads"], 120)
            observations["unchanged_cache_counterexample"] = {"original": results[0], "candidate": results[1],
                "game_advance_or_throughput_credit": 0}

        def test_03_actual_semantic_change_already_wakes_original(self):
            events = [(0.25, heartbeat(101)), (0.5, heartbeat(102)), (1.2, semantic)]
            times = []
            for current_cls, current_env in ((old_cls, old_env), (cls, env)):
                driver, state, first, _ = driver_case(current_cls, current_env, events)
                final = driver._wait_for_life_advance_snapshot(first,
                    lambda frame: frame["date_raw"] > first["date_raw"], timeout_seconds=30.0)
                self.assertEqual(final["date_raw"] - first["date_raw"], 24)
                times.append(state.clock.now)
            self.assertEqual(times, [1.2, 1.2])
            observations["semantic_change_wake_seconds"] = times

        def test_04_non_exact_wait_preserved(self):
            driver, state, first, _ = driver_case(cls, env,
                [(0.25, heartbeat(101)), (0.5, heartbeat(102))], enabled=False)
            driver._wait_for_life_advance_change(1, timeout_seconds=2.0, before_snapshot=first)
            self.assertEqual(state.clock.now, 2.0)
            self.assertEqual(len(driver.frames), 1)

        def test_05_no_lost_wake_or_repeated_immediate_wake(self):
            driver, state, first, _ = driver_case(cls, env, [])
            state._last_heartbeat = {"sequence": 101, "pid": 182100}
            second = driver._wait_for_life_advance_change(1, timeout_seconds=2.0, before_snapshot=first)
            self.assertEqual(state.clock.now, 0.0)
            driver._wait_for_life_advance_change(1, timeout_seconds=2.0, before_snapshot=second)
            self.assertEqual(state.clock.now, 2.0)

        def test_06_scope_or_missing_field_uses_original(self):
            for damage in ("identity", "closed", "generation", "heartbeat"):
                with self.subTest(damage=damage):
                    driver, state, first, progress = driver_case(cls, env, [(0.1, heartbeat(101))])
                    if damage == "identity": progress.identity = (1, 4, 40526, "wrong")
                    if damage == "closed": progress.closed = True
                    if damage == "generation": progress.generation = 0
                    if damage == "heartbeat": first["diagnostics"]["last_heartbeat"] = {}
                    driver._wait_for_life_advance_change(1, timeout_seconds=2.0, before_snapshot=first)
                    self.assertEqual(state.clock.now, 2.0)
                    self.assertEqual(progress.flags, 0)

        def test_07_connection_boundary_not_success(self):
            def disconnect(state):
                state._connected = False
            def new_connection(state):
                state._connection_generation += 1
                state._hello = {"pid": 182101}
            for action in (disconnect, new_connection):
                with self.subTest(action=action.__name__):
                    driver, state, first, _ = driver_case(cls, env, [(0.5, action)])
                    with self.assertRaisesRegex(ConnectionError, "existing semantic read"):
                        driver._wait_for_life_advance_change(1, timeout_seconds=30.0, before_snapshot=first)
                    self.assertEqual(state.clock.now, 0.5)

        def test_08_duplicate_heartbeat_does_not_wake(self):
            driver, state, first, _ = driver_case(cls, env, [(0.2, heartbeat(100))])
            driver._wait_for_life_advance_change(1, timeout_seconds=2.0, before_snapshot=first)
            self.assertEqual(state.clock.now, 2.0)

        def test_09_foreign_heartbeat_does_not_wake(self):
            def foreign(state):
                state._last_heartbeat = {"sequence": 101, "pid": 999}
            driver, state, first, _ = driver_case(cls, env, [(0.2, foreign)])
            driver._wait_for_life_advance_change(1, timeout_seconds=2.0, before_snapshot=first)
            self.assertEqual(state.clock.now, 2.0)

    started = time.perf_counter()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    duration = time.perf_counter() - started
    (OUT / "DIFF.patch").write_bytes(patch)
    proof = {"schema": "xar.exact-day-private-receipt-wait-qualification/v1", "machine_id": MACHINE,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(), "review_at_utc": DEADLINE.isoformat(),
        "status": "SOURCE_QUALIFIED_NOT_ADOPTED" if result.wasSuccessful() else "QUALIFICATION_FAILED",
        "budget_card": {"path": str(CARD), **CARD_PIN}, "input_commit": prepare.COMMIT,
        "input_Driver": prepare.pin(original), "actual_Driver_Git_body_reads": 1,
        "output_RAM_pins": {name: prepare.pin(raw) for name, raw in outputs.items()},
        "changed_functions": changed, "full_inverse_verified": True, "unowned_function_ASTs_unchanged": True,
        "patch": {"path": str(OUT / "DIFF.patch"), **prepare.pin(patch)},
        "source_pins": source_pins, "source_allocated_bytes": source_allocated,
        "source_filesystem_overhead_bound": source_overhead_bound,
        "source_with_overhead_bound": source_allocated + source_overhead_bound,
        "tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "details": [{"test": str(test), "traceback": detail} for test, detail in result.failures + result.errors],
        "duration_seconds": duration, "observations": observations,
        "scope": "selected actual methods plus actual unchanged public Condition method; deterministic in-memory Condition model",
        "B_collector_flags_or_DTO_changed": False, "public_revision_or_public_wait_changed": False,
        "timeout_pause_cleanup_or_real_predicate_changed": False, "new_poll_or_RPC": 0,
        "SDK_adoption_or_actual_clock_fix_credit": 0, "actual_performance_credit": 0,
        "Game_Native_MCP_Task_desktop_calls": 0, "full_Driver_disk_copies": 0,
        "synthetic_fixture_files": 0, "temporary_bytes": 0, "cleanup_needed": False,
        "allocation_note": "Actual FileStandardInfo allocation; conservative4096 per new file/directory for filesystem metadata. No physical refund credit."}
    proof_raw = json.dumps(proof, ensure_ascii=False, separators=(",", ":")).encode()
    if len(proof_raw) > 65536 or len(patch) > 8192:
        raise ValueError("finite evidence bounds exceeded")
    with (OUT / "QUALIFICATION.json").open("xb") as stream:
        stream.write(proof_raw)
    evidence_allocated = sum(allocated(OUT / name) for name in ("DIFF.patch", "QUALIFICATION.json"))
    artifact_bound = evidence_allocated + 3 * 4096
    if artifact_bound > 196608:
        raise ValueError("artifact lane allocation plus overhead exceeded")
    print(json.dumps({"status": proof["status"], "machine_id": MACHINE,
        "proof": {"path": str(OUT / "QUALIFICATION.json"), **prepare.pin(proof_raw)},
        "patch": proof["patch"], "tests": result.testsRun, "failures": len(result.failures),
        "errors": len(result.errors), "duration_seconds": duration,
        "source_logical_bytes": sum(v["bytes"] for v in source_pins.values()),
        "source_allocated_bytes": source_allocated, "source_highwater_with_overhead_bound": source_allocated + source_overhead_bound,
        "artifact_logical_bytes": len(proof_raw) + len(patch), "artifact_allocated_bytes": evidence_allocated,
        "artifact_highwater_with_overhead_bound": artifact_bound, "scratch_bytes": 0,
        "observations": observations}, ensure_ascii=False))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
