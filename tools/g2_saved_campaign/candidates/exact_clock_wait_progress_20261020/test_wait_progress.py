"""Five focused nodes over actual generated methods and immutable exception types."""
from __future__ import annotations
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
import types
import unittest

ROOT = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compile_classes(raw, selected, namespace):
    tree = ast.parse(raw)
    nodes = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name in selected:
            if selected[node.name] is not None:
                node.body = [n for n in node.body if isinstance(n, ast.FunctionDef) and n.name in selected[node.name]]
            nodes.append(node)
    future = ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[future, *nodes], type_ignores=[])), "Source24-selected-real-classes", "exec"), namespace)
    return namespace


def heartbeat(sequence=100, owner=1000, completed=1000):
    return {"type": "heartbeat", "protocol_version": 1, "sequence": sequence, "pid": 30852,
            "monotonic_ms": 1000 + sequence * 250,
            "main_thread_query_mailbox_v1": {"pump_epochs": owner, "owner_verified_pump_epochs": owner - 100},
            "snapshot_observer_12002": {"completed_ms": completed}}


def snapshot():
    return {"revision": 6, "native_revision": 4367, "date_raw": 53274600, "paused": False,
            "episode_character_id": 40526, "episode_run_id": "owned-episode",
            "diagnostics": {"bridge_pid": 30852, "connection_generation": 4,
                            "last_heartbeat": heartbeat()}}


class Clock:
    def __init__(self): self.ms = 0
    def __call__(self): return self.ms * 1_000_000


def cases(inputs):
    prepare = load("wait_progress_candidate_prepare", ROOT / "prepare_candidate.py")
    outputs, diff, changed = prepare.compose(inputs)
    helper = load("wait_progress_candidate_helper", ROOT / "exact_clock_wait_progress_v1.py")
    # One extra immutable qualification-only input; actual Source24 type, no guessed mock ABI.
    contract = subprocess.run(["git", "show", prepare.COMMIT + ":" + prepare.PREFIX + "driver.py"],
                              check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
    blob = hashlib.sha1(b"blob " + str(len(contract)).encode() + b"\0" + contract).hexdigest()
    if len(contract) != 20571 or blob != "92c52c0aee1f8cf42ed9fd3517355d5de7029d11":
        raise ValueError("actual Source24 error contract differs")
    error_ns = compile_classes(contract, {"BridgeUnavailableError": None, "StepPostconditionError": None}, {})
    package = types.ModuleType("wait_progress_candidate_package")
    package.__path__ = []
    error_module = types.ModuleType(package.__name__ + ".driver")
    error_module.StepPostconditionError = error_ns["StepPostconditionError"]
    sys.modules[package.__name__] = package
    sys.modules[error_module.__name__] = error_module
    sys.modules[package.__name__ + ".exact_clock_wait_progress_v1"] = helper
    dto = types.ModuleType(package.__name__ + ".exact_clock_failure_diagnostic_v1")
    dto.__package__ = package.__name__
    exec(compile(outputs["exact_clock_failure_diagnostic_v1.py"], "generated-DTO", "exec"), dto.__dict__)
    class Endpoint:
        def __init__(self): self.sent = []
        def send(self, packet): self.sent.append(packet)
    def build(raw):
        namespace = {"threading": threading, "copy": copy, "PROTOCOL_VERSION": 1,
                     "uuid": types.SimpleNamespace(uuid4=lambda: types.SimpleNamespace(hex="owned")),
                     "BridgeUnavailableError": error_ns["BridgeUnavailableError"],
                     "start_army_timing": lambda *a, **k: None, "finish_army_timing": lambda *a, **k: None,
                     "_validate_revision": lambda *a, **k: None, "_positive_seconds": lambda v, n: v}
        compile_classes(raw, {"NativeProtocolState": {"__init__", "ingest", "mark_disconnected", "wait_for_public_change"},
                         "NativeHeadlessGameplayDriver": {"_ingest", "_mark_bridge_disconnected_v1",
                                                          "_wait_for_life_advance_change", "_wait_for_life_advance_snapshot"}}, namespace)
        state = namespace["NativeProtocolState"]("owned-software-fixture")
        state.ingest({"type": "hello", "protocol_version": 1, "pid": 30852,
                      "capabilities": [], "connection_generation": 4})
        driver = namespace["NativeHeadlessGameplayDriver"]()
        driver.state, driver.endpoint, driver._request_sequence = state, Endpoint(), 0
        driver._adopt_bridge_session = lambda pid: None
        driver._invalidate_player_heir_provider_v1 = lambda reason: None
        return driver, namespace

    class Focused(unittest.TestCase):
        def test_early64_vs_continuous_with_only_two_candidates(self):
            summaries = []
            for early in (True, False):
                driver, _ = build(outputs["native_driver.py"])
                clock = Clock()
                progress = helper.WaitProgressV1(snapshot(), 576, clock=clock)
                setattr(driver, helper.KEY, progress)
                real_received = progress.received
                def received(*args):
                    self.assertFalse(driver.state._condition._is_owned())
                    return real_received(*args)
                progress.received = received
                for i in range(1, 121):
                    clock.ms = i * 250
                    delta = min(64, i * 32) if early else 64 * i // 120
                    driver._ingest(heartbeat(100 + i, 1000 + delta, 1500))
                # Heartbeat notifications never advance the actual state public revision.
                self.assertEqual(driver.state._public_revision, 1)
                result = helper.finish_wait_progress_v1(driver, progress, snapshot())
                self.assertEqual(result["heartbeats"], 120)
                self.assertEqual(result["candidates"], 2)
                self.assertEqual(result["metrics"]["owner"][4], 64)
                self.assertEqual(result["flags"], 0)
                self.assertLessEqual(len(json.dumps(result, separators=(",", ":")).encode()), 2048)
                summaries.append(result)
            self.assertEqual(summaries[0]["metrics"]["owner"][2], 500)
            self.assertEqual(summaries[1]["metrics"]["owner"][2], 30000)
            self.assertEqual(sum(row[1] for row in summaries[0]["buckets"][1:]), 0)
            self.assertGreater(sum(row[1] for row in summaries[1]["buckets"][1:]), 0)
            self.assertTrue(summaries[0]["empty_bucket_means_unobserved"])

        def test_missing_reset_identity_and_transport_boundaries_are_unknown(self):
            def make():
                clock = Clock()
                return helper.WaitProgressV1(snapshot(), 576, clock=clock), clock
            with self.subTest("missing"):
                progress, clock = make(); clock.ms = 250
                frame = heartbeat(); del frame["main_thread_query_mailbox_v1"]["pump_epochs"]
                progress.received("heartbeat", frame, (True, 4, 30852))
                self.assertTrue(progress.freeze(snapshot())["flags"] & 4)
            with self.subTest("reset"):
                progress, clock = make(); clock.ms = 250
                progress.received("heartbeat", heartbeat(99, 500, 900), (True, 4, 30852))
                self.assertTrue(progress.freeze(snapshot())["flags"] & 8)
            for change in ("token", "actor", "hello", "disconnect"):
                with self.subTest(change):
                    progress, clock = make(); clock.ms = 250
                    if change == "token": progress.received("heartbeat", heartbeat(), (True, 5, 30852))
                    elif change == "actor":
                        other = snapshot(); other["episode_character_id"] += 1; progress.observe_candidate(other)
                    elif change == "hello": progress.received("hello", {}, (True, 4, 30852))
                    else: progress.boundary()
                    self.assertTrue(progress.freeze(snapshot())["flags"] & 2)
            progress, clock = make(); clock.ms = -1
            progress.received("heartbeat", heartbeat(), (True, 4, 30852))
            self.assertTrue(progress.freeze(snapshot())["flags"] & 16)

        def test_receiver_callback_exception_does_not_change_original_state_or_exception(self):
            old, _ = build(inputs["native_driver.py"])
            new, _ = build(outputs["native_driver.py"])
            class Bad:
                error = False
                def received(self, *args): raise RuntimeError("diagnostic callback")
                def note_callback_error(self): self.error = True
            bad = Bad(); setattr(new, helper.KEY, bad)
            packet = heartbeat(101)
            self.assertIsNone(old._ingest(packet)); self.assertIsNone(new._ingest(packet))
            self.assertEqual(old.state._last_heartbeat, new.state._last_heartbeat)
            self.assertTrue(bad.error)
            for driver in (old, new):
                with self.assertRaisesRegex(ValueError, "heartbeat is malformed"):
                    driver._ingest({"type": "heartbeat", "protocol_version": 1, "sequence": False})
            progress = helper.WaitProgressV1(snapshot(), 576)
            setattr(new, helper.KEY, progress)
            new._mark_bridge_disconnected_v1()
            self.assertFalse(new.state._connected)
            self.assertTrue(progress.freeze(snapshot())["flags"] & 2)

        def test_original_wait_calls_and_cleanup_exclusion(self):
            traces = []
            marker = error_ns["BridgeUnavailableError"]("original wait error")
            for raw in (inputs["native_driver.py"], outputs["native_driver.py"]):
                driver, namespace = build(raw)
                class State:
                    def snapshot_supported(self): return True
                    def wait_for_public_change(self, revision, timeout): trace.append((revision, timeout))
                class Bad:
                    def observe_candidate(self, value): raise RuntimeError("optional")
                    def note_callback_error(self): trace.append("diagnostic_unknown")
                trace = []; driver.state = State()
                driver.take_internal_semantic_snapshot = snapshot
                setattr(driver, helper.KEY, Bad())
                result = driver._wait_for_life_advance_change(6, timeout_seconds=30.0)
                self.assertEqual(result, snapshot())
                traces.append([v for v in trace if v != "diagnostic_unknown"])
                driver.state.wait_for_public_change = lambda *a: (_ for _ in ()).throw(marker)
                with self.assertRaises(type(marker)) as caught:
                    driver._wait_for_life_advance_change(6, timeout_seconds=30.0)
                self.assertIs(caught.exception, marker)
                # Real original/generated outer wait is byte-identical; run both against one unchanging candidate.
                clock_values = iter((0.0, 0.0, 30.0))
                namespace["time"] = types.SimpleNamespace(monotonic=lambda: next(clock_values))
                calls = []
                driver._wait_for_life_advance_change = lambda *a, **k: calls.append((a, k)) or snapshot()
                result = driver._wait_for_life_advance_snapshot(snapshot(), lambda s: s["paused"] is True, timeout_seconds=30.0)
                self.assertEqual(len(calls), 1)
                self.assertEqual(calls[0][1]["timeout_seconds"], 30.0)
            self.assertEqual(traces[0], traces[1])
            driver, _ = build(outputs["native_driver.py"])
            progress = helper.WaitProgressV1(snapshot(), 576)
            setattr(driver, helper.KEY, progress)
            frozen = helper.finish_wait_progress_v1(driver, progress, snapshot())
            before = json.dumps(frozen, sort_keys=True)
            driver._ingest(heartbeat(999, 9999))  # Normal cleanup traffic after retirement.
            progress.received("heartbeat", heartbeat(1000, 10000), (True, 4, 30852))
            self.assertIs(frozen, progress.freeze(snapshot()))
            self.assertEqual(before, json.dumps(frozen, sort_keys=True))
            self.assertIsNone(getattr(driver, helper.KEY))

        def test_inverse_dto_real_type_and_fixed_shape(self):
            for name, hunks in (("native_driver.py", prepare.DRIVER_HUNKS),
                                ("exact_clock_failure_diagnostic_v1.py", prepare.DTO_HUNKS)):
                self.assertEqual(prepare.transfer(outputs[name], hunks, inverse=True), inputs[name])
            progress = helper.WaitProgressV1(snapshot(), 576).freeze(snapshot())
            original = error_ns["BridgeUnavailableError"](dto.MESSAGE)
            payload = dto.build_exact_clock_failure_v1(original_error=original,
                starting_date_raw=53274600, target_date_raw=53274624, speed=3,
                arm_status={"generation": 576}, starting=snapshot(), last_frame=snapshot(),
                cleanup_before_frame=None, actions=[], action_start=0, cleanup_start=0, wait_progress=progress)
            error = error_ns["StepPostconditionError"](str(original), selected_step="life-advance-one-day", step_result=payload)
            projected = dto.exact_clock_failure_diagnostic_v1(error)
            self.assertIsNotNone(projected)
            self.assertEqual(projected["wait_progress"]["arm_generation"], 576)
            self.assertFalse(projected["stop_credit"])
            self.assertFalse(projected["normal_status_query_attempted"])
            self.assertTrue(projected["never_replay"])
            self.assertLessEqual(len(dto._encode(projected)), 8192)
            foreign = error_ns["BridgeUnavailableError"](dto.MESSAGE); foreign.step_result = payload
            self.assertIsNone(dto.exact_clock_failure_diagnostic_v1(foreign))
            wrong = error_ns["StepPostconditionError"](str(original), selected_step="other", step_result=payload)
            self.assertIsNone(dto.exact_clock_failure_diagnostic_v1(wrong))
            invalid = dict(progress, history=["must not survive"])
            self.assertIsNone(helper.project_wait_progress_v1(invalid))
            self.assertEqual(set(projected), set(dto._DIAGNOSTIC))

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Focused)
    result = unittest.TestResult()
    started = time.perf_counter()
    suite.run(result)
    report = {"tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
              "duration_seconds": time.perf_counter() - started,
              "details": [{"test": str(test), "trace": text[-4000:]} for test, text in result.failures + result.errors],
              "inputs_read_logical_bytes": sum(len(v) for v in inputs.values()) + len(contract),
              "contract": {**prepare.pin(contract), "git_blob_sha1": blob},
              "changed_Driver_function_ASTs": changed, "output_pins": {k: prepare.pin(v) for k,v in outputs.items()},
              "scope": "5 focused nodes/actual selected generated methods + actual Source24 exception classes; no full Driver import, SDK adoption or Native calls"}
    print(json.dumps({"focused_result_before_seal": report}), flush=True)
    sealer = load("wait_progress_source_sealer", ROOT / "seal_candidate.py")
    return sealer.seal(inputs, outputs, diff, report)


run = cases
