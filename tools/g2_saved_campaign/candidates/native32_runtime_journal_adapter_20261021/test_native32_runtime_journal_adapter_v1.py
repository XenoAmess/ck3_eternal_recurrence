"""Software-only Native32 contract regression. No Game, RPC, DLL load or runtime grant."""
from __future__ import annotations
import ast
import asyncio
import copy
from datetime import datetime, timezone
from enum import IntEnum
import importlib.util
import json
from pathlib import Path
import sys
import time
import types
import unittest
from unittest.mock import patch
from typing import Callable, Protocol
import observer_journal_runtime_v1 as api
import native32_mcp_extension_v1 as extension
ORIGINAL_CONTROL_V1 = 'from __future__ import annotations\nfrom typing import Protocol,Literal\nclass _N31ToolResultV1(Protocol):\n    def model_dump(self, *, mode: Literal["json"]) -> dict[str,object]: ...\n\nclass _N31SessionV1(Protocol):\n    async def call_tool(self, name: str, arguments: dict[str,object], *,\n                       read_timeout_seconds: float) -> _N31ToolResultV1: ...\n\nclass _N31QueueV1(Protocol):\n    halted: object\n    current_attempt: object\n    full_loop_state: object\n    checkpoint_bootstrap_verified: bool\n    initial_save: object\n    next_sequence: int\n    def consume_sequence(self, request: dict[str,object]) -> int: ...\n\nasync def observe_native31_journal_root_v1(\n        queue: _N31QueueV1, session: _N31SessionV1,\n        request: dict[str,object], path: Path) -> None:\n    expected = {"schema", "sequence", "command", "execution_owner", "root_direct_execution_release"}\n    if (set(request) != expected or request.get("schema") != "xar.native31.root-journal-observation/v1"\n            or request.get("command") != "observe_native31_journal"\n            or request.get("execution_owner") != "Root"\n            or request.get("root_direct_execution_release") is not True\n            or type(request.get("sequence")) is not int\n            or request["sequence"] != queue.next_sequence\n            or not queue.checkpoint_bootstrap_verified or queue.initial_save is None\n            or path != INBOX / f"{queue.next_sequence:04d}-1-result.json"):\n        raise ValueError("one exact Root journal observation after cold bind required")\n    halted, attempt, state = queue.halted, queue.current_attempt, queue.full_loop_state\n    sequence = queue.next_sequence\n    response = OUTBOX / path.name\n    inflight = Q / f"INFLIGHT-{sequence:04d}.json"\n    if response.exists() or inflight.exists():\n        raise FileExistsError("journal observation already attempted; no retry")\n    context = {"request": request, "observed_at_utc": now().isoformat(),\n               "readonly_journal": True, "replay_allowed": False,\n               "ordinary_cycle_credit": 0, "day_credit": 0}\n    atomic(inflight, context, limit=16384)\n    queue.consume_sequence(request)\n    started, mono = now().isoformat(), time.monotonic()\n    row: dict[str,object] = {"request": request, "started_at_utc": started,\n        "readonly_journal": True, "replay_allowed": False,\n        "ordinary_cycle_credit": 0, "day_credit": 0,\n        "original_halt_retained": halted is not None}\n    try:\n        result = await session.call_tool("ck3_observe_native31_time_command_journal_v1", {},\n                                         read_timeout_seconds=30.0)\n        row["result"] = result.model_dump(mode="json")\n    except Exception as error:\n        row["client_error"] = repr(error)[:4096]\n    row["ended_at_utc"] = now().isoformat()\n    row["elapsed_seconds"] = time.monotonic() - mono\n    if (queue.halted is not halted or queue.current_attempt is not attempt\n            or queue.full_loop_state is not state):\n        raise RuntimeError("journal observation changed retained Queue objects")\n    atomic(response, row, limit=262144)\n\nasync def run_request_loop(queue, session):\n    """Finish normal admission inside ClientSession so its cleanup sees no error."""\n    while True:\n        try:\n            try:\n                queue.guard(reserve=False)\n                queue.recording_paused = False\n            except RecordingPaused as paused:\n                queue.recording_paused = True\n                pause_path = Q / "ROOT-RECORDING-PAUSED.json"\n                if not pause_path.exists():\n                    atomic(pause_path, {"at_utc": now().isoformat(), "reason": str(paused),\n                        "same_game_retained": True, "same_sdk_retained": True,\n                        "new_gameplay_admitted": False, "replay_allowed": False}, limit=16384)\n            pending = _control_call_v1("pending_paths", pending_request_paths,INBOX, OUTBOX, queue.next_sequence,\n                                            held_control=getattr(queue, "held_control", None))\n            if len(pending) > 1:\n                raise RuntimeError("only one outstanding Root request is permitted")\n            if pending:\n                path = pending[0]\n                request = read(path, 16384)\n                if path.name != f"{request.get(\'sequence\'):04d}-1-result.json":\n                    raise ValueError("actual inbox filename/sequence mismatch")\n                try:\n                    command = request.get("command")\n                    if command is not None and command != "observe_native31_journal" and getattr(queue, "halted", None) is None:\n                        dispatch_state = getattr(queue, "full_loop_state", None)\n                        dispatch_attempt = getattr(queue, "current_attempt", None)\n                        if isinstance(dispatch_state, dict) and isinstance(dispatch_attempt, dict):\n                            dispatch_row = dispatch_attempt.get("row")\n                            dispatch_request = dispatch_attempt.get("request")\n                            if (all(dispatch_state.get(k) is None for k in ("pending_cycle", "pending_checkpoint",\n                                    "terminal", "pending_natural_succession", "pending_unsafe_route_halt"))\n                                    and isinstance(dispatch_request, dict) and isinstance(dispatch_row, dict)\n                                    and dispatch_request.get("tool") in {SEMANTIC, METRICS}\n                                    and dispatch_row.get("request") == dispatch_request\n                                    and dispatch_row.get("client_error") is None\n                                    and isinstance(dispatch_row.get("result"), dict)\n                                    and dispatch_row["result"].get("result_type") == "complete"\n                                    and dispatch_row["result"].get("is_error") is False):\n                                queue.current_attempt = None\n                    if command == "clear_zero_rpc_preflight_rejection" and "tool" not in request:\n                        from root_saved_campaign_preflight import recover_zero_rpc_preflight\n                        recovery_env = dict(globals())\n                        recovery_env["CURRENT_HALT_NAME"] = "ROOT-CURRENT-HALT-" + Q.name.removesuffix("-queue").upper() + ".json"\n                        await recover_zero_rpc_preflight(queue, session, request, path, recovery_env)\n                    elif command == "attach_recording_segment" and "tool" not in request:\n                        queue.attach_recording_segment(request, path)\n                    elif queue.recording_paused:\n                        raise ValueError("recording paused; only a reviewed same-Game segment attachment is admitted")\n                    elif command == "resume_recording_pause" and "tool" not in request:\n                        await queue.resume_recording_pause(session, request, path)\n                    elif command == "observe_native31_journal" and "tool" not in request:\n                        await observe_native31_journal_root_v1(queue, session, request, path)\n                    elif command == "observe_original_start" and "tool" not in request:\n                        await queue.observe_original_start(session, request, path)\n                    elif command == "collect_original_declarable" and "tool" not in request:\n                        await queue.collect_original(session, request, path)\n                    elif command == "install_result_classifier" and "tool" not in request:\n                        await queue.install_result_classifier(session, request, path)\n                    elif command == "reconsume_original_response" and "tool" not in request:\n                        await queue.reconsume_original_response(session, request, path)\n                    elif command == "clear_blocked_no_action" and "tool" not in request:\n                        await queue.clear_blocked_no_action(session, request, path)\n                    elif command == "recover_partial_life_advance" and "tool" not in request:\n                        await queue.recover_partial_life_advance(session, request, path)\n                    elif command == "recover_known_owner_1024" and "tool" not in request:\n                        from root_p37_known_owner_recovery import recover as recover_known_owner\n                        await recover_known_owner(queue, session, request, path, globals())\n                    elif command == "full_loop" and "tool" not in request:\n                        await queue.full_loop(session, request, path)\n                    elif command is not None:\n                        raise ValueError("unknown local Root command")\n                    else:\n                        await queue.call(session, request, path)\n                except AdmissionEnded:\n                    raise\n                except Exception as error:\n                    preserve_first_exception(error, stage="request_dispatch", request=request,\n                        guard=getattr(queue, "last_guard_observation", None))\n                    try:\n                        queue.halt_request(error, request, path)\n                    except Exception as halt_error:\n                        raise ExceptionGroup("original request failure and halt receipt failure",\n                                             [error, halt_error]) from error\n            await asyncio.sleep(.25)\n        except AdmissionEnded as ended:\n            for path in sorted(INBOX.glob("*.json")):\n                if not (OUTBOX / path.name).exists():\n                    request = read(path, 16384)\n                    atomic(OUTBOX / path.name, {"ended_at_utc": now().isoformat(), "request": request,\n                        "status": "control_ended_at_admission_close" if "command" in request else "not_submitted_admission_closed",\n                        "no_new_rpc_after_admission_close": True, "replay_allowed": False}, limit=16384)\n            atomic(Q / "ROOT-REQUEST-ADMISSION-CLOSED-C23.json", {"at_utc": now().isoformat(),\n                "reason": str(ended), "sdk_context_exit_is_normal": True,\n                "unresolved_original_request": queue.halted is not None}, limit=16384)\n            return "request_admission_ended"\n        except Exception as error:\n            # Capture while still inside ClientSession/stdio; their TaskGroups\n            # can wrap this caller exception during context teardown.\n            preserve_first_exception(error, stage="request_loop_outer",\n                guard=getattr(queue, "last_guard_observation", None))\n            raise'
HERE = Path(__file__).resolve().parent
class IdentityEnum(IntEnum):
    same = 101

MACHINE = "unit-fixture-not-runtime"
PID = 101
BIRTH = 134370118417378359
DLL = "a" * 64
REQUEST = "n32journal.fixture"

def fixture_functions() -> dict[str, object]:
    path = HERE.parent / "native32_passive_journal_diagnostics_20261021/cold/test_observer_journal_v1.py"
    source = path.read_text(encoding="utf-8")
    namespace: dict[str, object] = {"STEP": api.STEP, "SCHEMA": api.SCHEMA, "HIGH": (1 << 53) + 19}
    nodes = [node for node in ast.parse(source).body
             if isinstance(node, ast.FunctionDef) and node.name in ("event_v1", "frame_v1")]
    if len(nodes) != 2:
        raise ValueError("two actual sealed fixture producers required")
    for node in nodes:
        segment = ast.get_source_segment(source, node)
        if segment is None:
            raise ValueError("actual fixture source absent")
        exec(compile("from __future__ import annotations\n" + segment, str(path), "exec"), namespace)
    return namespace


FIXTURE = fixture_functions()


def call_fixture(name: str, *arguments: object) -> dict[str, object]:
    function = FIXTURE[name]
    if not callable(function):
        raise ValueError("real fixture callable required")
    return api._obj(function(*arguments))


def native_frame(count: int = 2) -> dict[str, object]:
    events = [call_fixture("event_v1", 7 if index % 2 else 8, index)
              for index in range(1, count + 1)]
    frame = call_fixture("frame_v1", events)
    frame["request_id"] = REQUEST
    result = api._obj(frame["result"])
    result["process_id"], result["process_birth"] = PID, str(BIRTH)
    frame["result"] = result
    return frame


def reference(name: str) -> api.ExactRefV1:
    return {"path": str(HERE / name), "bytes": 1, "sha256": "b" * 64}


def binding_fixture() -> api.ProductionBindingV2:
    wire: api.ProductionBindingWireV2 = {
        "schema": "xar.native32.source31-production-observer-binding/v2", "machine_id": MACHINE,
        "status": "COLD_SOURCE_BOUND_NOT_RUNTIME_ADMITTED",
        "sdk_base_ref": reference("software-base.json"),
        "sdk_anchor_ref": reference("software-anchor.json"),
        "production_result_ref": reference("software-production.json"),
        "production_input_manifest_ref": reference("software-input.json"),
        "dll": {**reference("software-not-a-dll"), "sha256": DLL},
        "sealed_parser_source": reference("software-parser.py")}
    return api.ProductionBindingV2(wire, HERE)


class Endpoint:
    def __init__(self) -> None:
        self.sent: list[dict[str, object]] = []
        self.pipe_name = "software-fixture"
    def send(self, frame: dict[str, object]) -> None:
        self.sent.append(frame)


class State:
    def __init__(self, frame: object) -> None:
        self.frame = frame
        self.waits: list[tuple[str, float]] = []
    def diagnostics(self) -> dict[str, object]:
        return {"connected": True, "hello": {"pid": PID, "connection_generation": 9},
                "connection_generation": 9}
    def wait_for_command_result(self, request_id: str, timeout_seconds: float) -> object:
        self.waits.append((request_id, timeout_seconds))
        return self.frame


class Driver:
    def __init__(self, frame: object) -> None:
        self.endpoint, self.state, self.pipe_name = Endpoint(), State(frame), "software-fixture"


class Owner:
    def __init__(self, provider: object) -> None:
        self._player_heir_loaded_provider_v1 = provider


def software_result(count: int = 2) -> api.Native32ResultV1:
    """Only the transport context seam is a fixture; no runtime proof is issued."""
    driver = Driver(native_frame(count))
    provider = object()
    owner = Owner(provider)
    context = api.RuntimeContextV1(binding_fixture(), api.ExpectedGameV1(MACHINE, PID, BIRTH),
                                  9, driver.pipe_name, provider)
    with patch.object(api, "require_native32_context_v1", return_value=context), patch.object(api, "_same_holder32"):
        result = api.read_native32_once_v1(owner, driver, binding_value=None,
            machine_id=MACHINE, request_id=REQUEST, selection=api.AllNativeObservedHistoryV1())
    if len(driver.endpoint.sent) != 1 or driver.state.waits != [(REQUEST, 2.0)]:
        raise AssertionError("one fixed software transport request required")
    command = driver.endpoint.sent[0]
    if command.get("step") != "observe-time-command-journal-v1" or command.get("expected_revision") != 0:
        raise AssertionError("transport broadened the fixed readonly command")
    return result


def envelope(value: object) -> dict[str, object]:
    return {"meta": None, "content": [], "structured_content": value,
            "is_error": False, "result_type": "complete"}


class Native32RuntimeContracts(unittest.TestCase):
    def test_sealed_parser_unchanged_and_runtime_gate_rejects(self) -> None:
        import hashlib
        original = HERE.parent / "native32_passive_journal_diagnostics_20261021/cold/observer_journal_v1.py"
        self.assertEqual(original.read_bytes(), (HERE / "observer_journal_runtime_v1.py").read_bytes()[:api.SEALED_PARSER_BYTES])
        self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(), api.SEALED_PARSER_SHA256)
        with self.assertRaises(ValueError):
            api.require_runtime_qualification_v1()
        invalid: tuple[object, ...] = (None, {}, [], {"schema": "host-pass"})
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                api.qualify_native32_binding_v1(value, machine_id=MACHINE)

        wire: dict[str, object] = dict(binding_fixture().wire)
        for key, bad_binding in (("schema", "xar.native32.production-observer-binding/v1"), ("machine_id", "foreign-machine"), ("status", "host-pass"),
                                 ("production_result_ref", None), ("dll", {}),
                                 ("sealed_parser_source", {"path": str(HERE), "bytes": True, "sha256": DLL})):
            with self.subTest(binding_key=key), self.assertRaises(ValueError):
                api.qualify_native32_binding_v1({**wire, key: bad_binding}, machine_id=MACHINE)

    def test_no_production_fact_no_issuer_or_native_request(self) -> None:
        calls: list[object] = []
        owner = object()
        driver = Driver(None)
        setattr(driver, "_player_heir_candidate_owner_v1", owner)
        registered: list[Callable[[], dict[str, object]]] = []
        def register(callback: Callable[[], dict[str, object]]) -> object:
            registered.append(callback)
            return callback
        def ensure(value: object) -> object:
            calls.append(value)
            return None
        callback = extension.register_native32_journal_v1(register, owner=owner, driver=driver,
            machine_id=MACHINE, binding_value=None, existing_ensure=ensure)
        self.assertEqual(len(registered), 1)
        self.assertEqual(calls, [])
        with self.assertRaises(ValueError):
            callback()
        self.assertEqual(calls, [])
        self.assertEqual(driver.endpoint.sent, [])
        self.assertEqual(driver.state.waits, [])

    def test_producer_consumer_json_roundtrip_and_empty_selection(self) -> None:
        result = software_result()
        wire: object = json.loads(json.dumps(result, allow_nan=False))
        parsed = api.parse_native32_result_v1(wire, machine_id=MACHINE,
            game_pid=PID, creation_filetime=BIRTH, native_dll_sha256=DLL)
        self.assertEqual(parsed, result)
        summary = parsed["summary"]
        self.assertIsNotNone(summary)
        if summary is None:
            self.fail("summary missing")
        self.assertIs(summary["runtime_admission_granted"], False)
        self.assertEqual(parsed["ordinary_cycle_credit"], 0)
        journal = api.parse_journal_v1(native_frame(), request_id=REQUEST,
            expected=api.ExpectedGameV1(MACHINE, PID, BIRTH))
        empty = api.result_payload_v1(journal, api.RequestedIdsV1(()),
            api.ExpectedGameV1(MACHINE, PID, BIRTH))
        self.assertEqual(empty["native_observed_execute_pairs"], [])

    def test_result_and_canonical_envelope_reject_identity_type_drift(self) -> None:
        result = software_result()
        for key, bad in (("game_pid", True), ("game_pid", float(PID)),
                         ("game_creation_filetime", BIRTH), ("connection_generation", 9),
                         ("ordinary_cycle_credit", False), ("drain_fence", True),
                         ("native_dll_sha256", "c"*64), ("summary", {})):
            bad_result: object = {**result, key: bad}
            with self.subTest(key=key, bad=bad), self.assertRaises(ValueError):
                api.parse_native32_result_v1(bad_result, machine_id=MACHINE, game_pid=PID,
                    creation_filetime=BIRTH, native_dll_sha256=DLL)
        game = {"machine_id": MACHINE, "pid": PID, "creation_filetime": BIRTH}
        with patch.object(extension, "qualify_native32_binding_v1", return_value=binding_fixture()):
            self.assertEqual(extension.validate_native32_mcp_result_v1(envelope(result),
                actual_game=game, binding_value=None, machine_id=MACHINE), result)
            for bad_envelope in ({**envelope(result), "resultType": "complete"},
                        {**envelope(result), "result_type": None},
                        {**envelope(result), "is_error": True},
                        {**envelope(result), "structured_content": None}):
                with self.subTest(bad=bad_envelope), self.assertRaises(ValueError):
                    extension.validate_native32_mcp_result_v1(bad_envelope, actual_game=game,
                        binding_value=None, machine_id=MACHINE)
            for pid in (True, float(PID), IdentityEnum.same):
                with self.subTest(pid=pid), self.assertRaises(ValueError):
                    extension.validate_native32_mcp_result_v1(envelope(result),
                        actual_game={**game, "pid": pid}, binding_value=None, machine_id=MACHINE)

    def test_64_events_wide_uint64_and_raw_source_cap(self) -> None:
        result = software_result(64)
        encoded = json.dumps(envelope(result), ensure_ascii=True, allow_nan=False).encode()
        self.assertLess(len(encoded), 262144)
        frame = api._obj(json.loads(str(result["original_parsed_frame_json"])))
        events = api._obj(frame["result"])["events"]
        if not isinstance(events, list):
            self.fail("actual native events list absent")
        self.assertEqual(len(events), 64)
        value = {**result, "original_parsed_frame_json": "x" * 98305}
        with self.assertRaises(ValueError):
            api.parse_native32_result_v1(value, machine_id=MACHINE, game_pid=PID,
                creation_filetime=BIRTH, native_dll_sha256=DLL)

    def test_queue_patch_original_functions_and_invalid_preimages(self) -> None:
        changed = api.patch_queue_control_v1(ORIGINAL_CONTROL_V1.encode(),
            production_binding_basename="NATIVE32-PRODUCTION-BINDING.json")
        self.assertIn(b"by_alias=False", changed)
        self.assertIn(b"validate_native32_mcp_result_v1", changed)
        self.assertNotIn(b"observe_native31_journal", changed)
        for raw in (changed, ORIGINAL_CONTROL_V1.replace("read_timeout_seconds=30.0", "read_timeout_seconds=5.0").encode(), b""):
            with self.subTest(raw=raw[:50]), self.assertRaises(ValueError):
                api.patch_queue_control_v1(raw, production_binding_basename="NATIVE32-PRODUCTION-BINDING.json")
        for name in ("../escape.json", "a/b.json", "a\\b.json", "", "x.py"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                api.patch_queue_control_v1(ORIGINAL_CONTROL_V1.encode(), production_binding_basename=name)

    def test_actual_full_run_request_loop_four_ticks_and_single_timeout(self) -> None:
        asyncio.run(queue_fixture_v1(self))


class AdmissionEnded(Exception):
    pass


class RecordingPaused(Exception):
    pass


class Queue:
    def __init__(self) -> None:
        self.halted: object = {"unknown": 10565}
        self.current_attempt: object = {"original": 10565}
        self.full_loop_state: object = {"pending_cycle": {"unknown": True}}
        self.checkpoint_bootstrap_verified = True
        self.initial_save: object = {"software_fixture": True}
        self.next_sequence, self.ticks, self.consumed = 600, 0, 0
    def guard(self, *, reserve: bool) -> None:
        if reserve is not False:
            raise AssertionError("unexpected reserve")
        self.ticks += 1
        if self.ticks == 4:
            raise AdmissionEnded("software fixture stops after four actual loop ticks")
    def consume_sequence(self, request: dict[str, object]) -> int:
        if request["sequence"] != self.next_sequence:
            raise AssertionError("sequence differs")
        old = self.next_sequence
        self.next_sequence += 1
        self.consumed += 1
        return old
    def halt_request(self, *unused: object) -> None:
        raise AssertionError("original unknown HALT must not be rewritten")


class Result:
    def model_dump(self, *, mode: str, by_alias: bool) -> dict[str, object]:
        if mode != "json" or by_alias is not False:
            raise AssertionError("canonical serialization required")
        return envelope(software_result())


class Session:
    def __init__(self, fail: bool = False) -> None:
        self.calls, self.fail = 0, fail
    async def call_tool(self, name: str, arguments: dict[str, object], *,
                        read_timeout_seconds: float) -> Result:
        if (name != "ck3_observe_native32_time_command_journal_v1" or arguments
                or read_timeout_seconds != 30.0):
            raise AssertionError("only fixed zero-argument read with client30 allowed")
        self.calls += 1
        if self.fail:
            raise TimeoutError("software fixture client wait; no hard end-to-end claim")
        return Result()


async def queue_fixture_v1(test: unittest.TestCase) -> None:
    """Execute the mechanically retained full actual Queue loop, never its main."""
    inbox, outbox, q = HERE / "unit-in", HERE / "unit-out", HERE / "unit-q"
    memory: dict[Path, object] = {}
    def atomic(path: Path, value: object, *, limit: int) -> None:
        if len(json.dumps(value, allow_nan=False).encode()) > limit:
            raise ValueError("bounded persisted software row exceeded")
        memory[path] = copy.deepcopy(value)
    def read(path: Path, limit: int) -> object:
        if limit <= 0:
            raise ValueError("positive read bound required")
        return copy.deepcopy(memory[path])
    def pending(*unused: object, **keywords: object) -> list[Path]:
        return [inbox / "0600-1-result.json"] if outbox / "0600-1-result.json" not in memory else []
    async def sleep(seconds: float) -> None:
        if seconds < 0:
            raise AssertionError("negative sleep")
    def control(label: str, function: Callable[..., object], *args: object, **kwargs: object) -> object:
        return function(*args, **kwargs)
    env: dict[str, object] = {
        "INBOX": inbox, "OUTBOX": outbox, "Q": q, "N": HERE, "MACHINE": MACHINE,
        "Path": Path, "now": lambda: datetime.now(timezone.utc), "time": time,
        "atomic": atomic, "read": read, "asyncio": types.SimpleNamespace(sleep=sleep),
        "AdmissionEnded": AdmissionEnded, "RecordingPaused": RecordingPaused,
        "pending_request_paths": pending, "_control_call_v1": control,
        "preserve_first_exception": lambda *args, **kwargs: None}
    projected = api.patch_queue_control_v1(ORIGINAL_CONTROL_V1.encode(),
        production_binding_basename="NATIVE32-PRODUCTION-BINDING.json")
    exec(compile(projected, "<actual-full-Queue-Native32-software-only>", "exec"), env)
    loop, observe = env["run_request_loop"], env["observe_native32_journal_root_v1"]
    if not callable(loop) or not callable(observe):
        raise ValueError("actual Queue functions missing")
    request: dict[str, object] = {"schema": "xar.native32.root-journal-observation/v1",
        "sequence": 600, "command": "observe_native32_journal", "execution_owner": "Root",
        "root_direct_execution_release": True}
    def reset() -> Queue:
        memory.clear()
        memory[inbox / "0600-1-result.json"] = copy.deepcopy(request)
        memory[HERE / "ROOT-ACTUAL-GAME-LAUNCH-C23.json"] = {
            "machine_id": MACHINE, "pid": PID, "creation_filetime": BIRTH}
        memory[HERE / "NATIVE32-PRODUCTION-BINDING.json"] = None
        return Queue()
    queue = reset()
    session = Session()
    retained = queue.halted, queue.current_attempt, queue.full_loop_state
    with patch.object(extension, "qualify_native32_binding_v1", return_value=binding_fixture()):
        await loop(queue, session)
    test.assertEqual((queue.ticks, queue.consumed, session.calls, queue.next_sequence), (4, 1, 1, 601))
    test.assertTrue(all(a is b for a, b in zip(retained, (queue.halted, queue.current_attempt, queue.full_loop_state))))
    row = api._obj(memory[outbox / "0600-1-result.json"])
    test.assertIs(row["native32_result_validated"], True)
    test.assertEqual(row["ordinary_cycle_credit"], 0)
    for bad in ({**request, "sequence": True}, {**request, "sequence": 600.0},
                {**request, "arguments": {}}, {**request, "schema": "xar.native31.root-journal-observation/v1"}):
        queue, session = reset(), Session()
        with test.subTest(bad=bad), test.assertRaises(ValueError):
            await observe(queue, session, bad, inbox / "0600-1-result.json")
        test.assertEqual((queue.consumed, session.calls), (0, 0))
    queue, session = reset(), Session(True)
    await observe(queue, session, request, inbox / "0600-1-result.json")
    test.assertEqual((queue.consumed, session.calls), (1, 1))
    test.assertIn("client_error", api._obj(memory[outbox / "0600-1-result.json"]))


if __name__ == "__main__":
    unittest.main()
