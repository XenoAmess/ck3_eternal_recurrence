"""Portable optional-war-query tests; no SDK/RPC writes."""
from __future__ import annotations

import ast
from collections.abc import Iterable, Mapping
from copy import deepcopy
from contextlib import ExitStack
import inspect
from enum import IntEnum
import json
from pathlib import Path
import sys
from types import FunctionType, ModuleType
from typing import Protocol, TypeGuard, cast, get_type_hints
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SDK = REPO / "ck3_autonomous_player/src"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(SDK))
import prepare_war_termination_optional_unavailable_v1 as producer
from xar_autoplayer import strategy as old_strategy
from xar_autoplayer.bridge import native_driver as old_driver
from xar_autoplayer.bridge import war_contract as old_contract

Doc = dict[str, object]
STEP = "query-war-termination-options-88"
ERROR = "war-termination completion snapshot read failed"


class Number(IntEnum):
    ONE = 1


def is_record(value: object) -> TypeGuard[Doc]:
    return isinstance(value, dict) and all(type(key) is str for key in value)


def record(value: object) -> Doc:
    if not is_record(value):
        raise AssertionError("text-keyed fixture object required")
    return value


def put(row: Doc, path: tuple[str, ...], value: object) -> None:
    target = row
    for key in path[:-1]:
        target = record(target[key])
    target[path[-1]] = value


def frame() -> Doc:
    return {
        "snapshot_id": "native:90", "revision": 90, "native_revision": 90,
        "date_raw": 1000, "episode_run_id": "portable-episode", "source": "native-headless",
        "phase": "map_hud", "paused": True, "map_ready": True,
        "played_character": {"character_id": 707, "alive": True},
        "diagnostics": {"bridge_pid": 123, "connection_generation": 1},
        "active_wars": [{
            "war_id": 88, "player_side": "attacker", "player_is_primary_war_leader": True,
            "primary_opponent_character_id": 808, "player_relative_war_score": 17,
            "targeted_title_ids": [2254], "war_duration_days": 203,
            "allied_armies": [], "enemy_armies": [],
            "war_objective_province_ids": [], "objective_province_states": [],
        }],
        "player_armies": [], "war_termination_options": None,
    }


def war(snapshot: Doc) -> Doc:
    rows = snapshot["active_wars"]
    if not isinstance(rows, list) or not rows:
        raise AssertionError("fixture wars required")
    return record(rows[0])


def request() -> Doc:
    return {"type": "execute_step", "protocol_version": 1,
            "request_id": "step-5-61e52e058ce3", "step": STEP, "expected_revision": 90}


def response() -> Doc:
    return {"type": "command_result", "protocol_version": 1,
            "request_id": "step-5-61e52e058ce3", "ok": False, "error": ERROR}


class Unavailable(Protocol):
    def __call__(self, *, step: str, native_error: str, native_request_id: object,
                 request: object, response: object, starting: object,
                 current: object) -> Mapping[str, object] | None: ...


class Deferred(Protocol):
    def __call__(self, snapshot: object, war: object,
                 recent_records: Iterable[object]) -> Mapping[str, object] | None: ...


class ParseStored(Protocol):
    def __call__(self, value: object) -> Mapping[str, object] | None: ...


class WarStep(Protocol):
    def __call__(self, driver: object, step: str, *, starting: Doc,
                 selected_revision: int, query_war_id: int | None,
                 surrender_war_id: int | None, white_peace_war_id: int | None,
                 explicit_surrender: bool = False) -> Doc: ...


class Execute(Protocol):
    def __call__(self, driver: object, step: str, *,
                 expected_revision: int | None = None) -> Doc: ...


class Plan(Protocol):
    def __call__(self, commands: list[Doc], *, snapshot: Doc | None = None,
                 action_steps: Iterable[str] | None = None,
                 bridge_capabilities: Iterable[str] | None = None,
                 next_run_plan: Doc | None = None,
                 battle_speed_readiness: Doc | None = None) -> Doc: ...


def checked_function(scope: Doc, name: str, arguments: tuple[str, ...]) -> FunctionType:
    value = scope[name]
    if not isinstance(value, FunctionType) or tuple(inspect.signature(value).parameters) != arguments:
        raise AssertionError("actual projected function signature differs: " + name)
    return value


def definitions(raw: bytes, names: set[str]) -> ast.Module:
    tree = ast.parse(raw)
    scopes: list[ast.Module | ast.ClassDef] = [tree, *(node for node in tree.body if isinstance(node, ast.ClassDef)
                      and node.name == "NativeHeadlessGameplayDriver")]
    nodes = [node for scope in scopes for node in scope.body
             if isinstance(node, ast.FunctionDef) and node.name in names]
    if {node.name for node in nodes} != names or len(nodes) != len(names):
        raise AssertionError("unique actual source functions required")
    return ast.Module(body=list[ast.stmt](nodes), type_ignores=[])


def no_timing(*args: object, **kwargs: object) -> None:
    return None



class Project(Protocol):
    def __call__(self, native_driver: bytes, strategy: bytes,
                 war_contract: bytes) -> producer.CandidateSourcesV1: ...


def producer_seams_v1() -> dict[str, list[tuple[str, str]]]:
    """Read the real recipe without duplicating its before/after literals."""
    seams: dict[str, list[tuple[str, str]]] = {"native_driver": [], "strategy": []}

    def trace(source: str, before: str, after: str) -> str:
        key = {"# driver\n": "native_driver", "# strategy\n": "strategy"}.get(source)
        if key is None:
            raise AssertionError("unexpected recipe source")
        seams[key].append((before, after))
        return source

    tree = ast.parse(inspect.getsource(producer.project_war_optional_query_unavailable_v1))
    scope: Doc = dict(vars(producer))
    scope["_one"] = trace
    exec(compile(tree, "<actual recipe seam recorder>", "exec"), scope)
    project = cast(Project, checked_function(scope,
        "project_war_optional_query_unavailable_v1",
        ("native_driver", "strategy", "war_contract")))
    project(b"# driver\n", b"# strategy\n", b"")
    if [len(seams[name]) for name in ("native_driver", "strategy")] != [3, 2]:
        raise AssertionError("the actual producer recipe changed")
    return seams


def source_views_v1(driver: bytes, strategy: bytes, contract: bytes
                    ) -> tuple[producer.CandidateSourcesV1, producer.CandidateSourcesV1, bool]:
    current: producer.CandidateSourcesV1 = {
        "native_driver": driver, "strategy": strategy, "war_contract": contract}
    seams = producer_seams_v1()
    addition = producer.WAR_CONTRACT_ADDITION_V1.encode()
    installed = b"WarTerminationUnavailableV1" in contract
    originals: dict[str, bytes] = {}
    for name, rows in seams.items():
        body = current["native_driver"] if name == "native_driver" else current["strategy"]
        text = body.decode("utf-8")
        if installed:
            for original_text, installed_text in reversed(rows):
                text = producer._one(text, installed_text, original_text)
        elif any(after in text for _, after in rows):
            raise ValueError("partly installed war query sources")
        originals[name] = text.encode()
    if installed:
        if not contract.endswith(addition) or contract.count(addition) != 1:
            raise ValueError("unique exact installed war contract suffix required")
        contract = contract[:-len(addition)]
    before: producer.CandidateSourcesV1 = {"native_driver": originals["native_driver"],
        "strategy": originals["strategy"], "war_contract": contract}
    projected = producer.project_war_optional_query_unavailable_v1(
        before["native_driver"], before["strategy"], before["war_contract"])
    if installed and projected != current:
        raise ValueError("installed war sources differ from the real forward recipe")
    return before, projected, installed

class Runtime:
    def __init__(self) -> None:
        raw_driver = (SDK / "xar_autoplayer/bridge/native_driver.py").read_bytes()
        raw_strategy = (SDK / "xar_autoplayer/strategy.py").read_bytes()
        raw_contract = (SDK / "xar_autoplayer/bridge/war_contract.py").read_bytes()
        before, projected, installed = source_views_v1(raw_driver, raw_strategy, raw_contract)
        self.before_driver = before["native_driver"]
        self.before_strategy = before["strategy"]
        self.driver_raw = projected["native_driver"]
        self.strategy_raw = projected["strategy"]
        self.contract_raw = projected["war_contract"]
        self._owns_contract = not installed
        self._timing_stack = ExitStack()
        if installed:
            self.contract = old_contract
        else:
            self.contract = ModuleType("_war_optional_portable_contract")
            vars(self.contract).update(vars(old_contract))
            self.contract.__name__ = "_war_optional_portable_contract"
            sys.modules[self.contract.__name__] = self.contract
            exec(compile(producer.WAR_CONTRACT_ADDITION_V1, "<actual war DTO addition>", "exec"),
                 vars(self.contract))
        scope: Doc = dict(vars(self.contract))
        # Verify the real signatures before narrowing exec-boundary callables.
        self.unavailable = cast(Unavailable, checked_function(scope,
            "war_termination_optional_unavailable_v1",
            ("step", "native_error", "native_request_id", "request", "response", "starting", "current")))
        self.deferred = cast(Deferred, checked_function(scope,
            "war_termination_optional_query_defer_v1", ("snapshot", "war", "recent_records")))
        self.parse_stored = cast(ParseStored, checked_function(scope,
            "parse_war_termination_optional_unavailable_v1", ("value",)))

        driver_scope: Doc
        strategy_scope: Doc
        if installed:
            # Invoke installed function objects; replace only optional timing I/O.
            driver_scope = dict(vars(old_driver.NativeHeadlessGameplayDriver))
            strategy_scope = dict(vars(old_strategy))
            self._timing_stack.enter_context(patch.object(old_driver, "finish_army_timing", no_timing))
            self._timing_stack.enter_context(patch.object(old_driver, "start_army_timing", no_timing))
        else:
            driver_scope = dict(vars(old_driver))
            driver_scope["war_termination_optional_unavailable_v1"] = self.unavailable
            driver_scope["finish_army_timing"] = no_timing
            driver_scope["start_army_timing"] = no_timing
            names = {"_execute_war_termination_step", "execute_step"}
            exec(compile(definitions(self.driver_raw, names), "<actual projected Driver functions>", "exec"),
                 driver_scope)
            strategy_scope = dict(vars(old_strategy))
            strategy_scope["war_termination_optional_query_defer_v1"] = self.deferred
            exec(compile(definitions(self.strategy_raw, {"_choose_one_life_turn_core"}),
                         "<actual projected strategy>", "exec"), strategy_scope)
        self.war_step = cast(WarStep, checked_function(driver_scope,
            "_execute_war_termination_step", ("self", "step", "starting", "selected_revision",
            "query_war_id", "surrender_war_id", "white_peace_war_id", "explicit_surrender")))
        self.execute = cast(Execute, checked_function(driver_scope,
            "execute_step", ("self", "step", "expected_revision")))
        self.plan = cast(Plan, checked_function(strategy_scope,
            "_choose_one_life_turn_core", ("commands", "snapshot", "action_steps",
            "bridge_capabilities", "next_run_plan", "battle_speed_readiness")))

    def close(self) -> None:
        self._timing_stack.close()
        if self._owns_contract:
            sys.modules.pop(self.contract.__name__, None)

    def unavailable_result(self, *, start: Doc | None = None, current: Doc | None = None) -> Doc:
        first = frame() if start is None else start
        value = self.unavailable(step=STEP, native_error=ERROR,
            native_request_id="step-5-61e52e058ce3", request=request(), response=response(),
            starting=first, current=deepcopy(first) if current is None else current)
        if value is None:
            raise AssertionError("valid explicit rejection was not projected")
        return dict(value)


def rejection(*, message: str = ERROR, asked: Doc | None = None,
              replied: Doc | None = None) -> Exception:
    value: object = old_driver._NativeCommandRejectedError(
        message, native_request_id="step-5-61e52e058ce3",
        native_request_frame=request() if asked is None else asked,
        native_command_result_frame=response() if replied is None else replied)
    if not isinstance(value, Exception):
        raise AssertionError("actual native exception required")
    return value


class DriverFixture:
    def __init__(self, runtime: Runtime, error: Exception, *, current: Doc | None = None) -> None:
        self.runtime = runtime
        self.error = error
        self.starting = frame()
        self.current = deepcopy(self.starting) if current is None else current
        self.calls = 0
        self.snapshot_reads = 0
        self.history: list[Doc] = []

    def _execute_primitive_step(self, step: str, **kwargs: object) -> Doc:
        self.calls += 1
        raise self.error

    def take_internal_semantic_snapshot(self) -> Doc:
        self.snapshot_reads += 1
        return deepcopy(self.current)

    def _execute_step_unrecorded(self, step: str, *, expected_revision: int | None = None) -> Doc:
        return self.runtime.war_step(self, step, starting=self.starting,
            selected_revision=90, query_war_id=88, surrender_war_id=None, white_peace_war_id=None)

    def _record_command(self, step: str, *, ok: bool, result: Doc | None = None,
                        error: str | None = None) -> None:
        self.history.append({"index": len(self.history) + 1, "command": step,
                             "ok": ok, "result": deepcopy(result), "error": error})


class WarOptionalTests(unittest.TestCase):
    runtime: Runtime

    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime = Runtime()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.runtime.close()

    def call(self, *, step: str = STEP, error: str = ERROR, rid: object = "step-5-61e52e058ce3",
             asked: object = None, replied: object = None, start: object = None,
             current: object = None) -> Mapping[str, object] | None:
        first = frame() if start is None else start
        return self.runtime.unavailable(step=step, native_error=error, native_request_id=rid,
            request=request() if asked is None else asked, response=response() if replied is None else replied,
            starting=first, current=deepcopy(first) if current is None else current)

    def retained(self) -> list[Doc]:
        return [{"step": STEP, "ok": False, "result": self.runtime.unavailable_result()}]

    def test_actual_driver_rejection_history_and_real_strategy_pipeline(self) -> None:
        fixture = DriverFixture(self.runtime, rejection())
        result = self.runtime.execute(fixture, STEP, expected_revision=90)
        self.assertEqual(fixture.calls, 1)
        self.assertEqual(fixture.snapshot_reads, 1)
        self.assertFalse(fixture.history[-1]["ok"])
        self.assertIs(result["accepted"], False)
        self.assertIsNone(result["war_termination_options"])
        self.assertIs(result["fresh_native_completion_proved"], False)
        wire = record(json.loads(json.dumps(result)))
        self.assertEqual(dict(self.runtime.parse_stored(wire) or {}), result)
        baseline = self.runtime.plan([], snapshot=frame(), action_steps=(STEP, "life-advance"))
        after = self.runtime.plan(fixture.history, snapshot=frame(), action_steps=(STEP, "life-advance"))
        self.assertEqual(baseline["selected_step"], STEP)
        self.assertNotEqual(after["selected_step"], STEP)
        summaries = after.get("active_wars")
        self.assertIsInstance(summaries, list)
        if not isinstance(summaries, list):
            self.fail("real planner war summary required")
        self.assertIn("war_termination_optional_query_defer", record(summaries[0]))
        self.assertEqual(fixture.calls, 1)

    def test_standalone_helpers_reflect_and_roundtrip(self) -> None:
        value = self.runtime.unavailable_result()
        self.assertEqual(dict(self.runtime.parse_stored(json.loads(json.dumps(value))) or {}), value)
        deferred = self.runtime.deferred(frame(), war(frame()), self.retained())
        self.assertIsNotNone(deferred)
        if deferred is None:
            self.fail("same-day scheduling defer required")
        self.assertIs(deferred["native_negative_assessment"], False)
        self.assertIs(deferred["business_submission"], False)
        self.assertIsNone(deferred["war_termination_options"])
        for function in (self.runtime.unavailable, self.runtime.deferred, self.runtime.parse_stored):
            self.assertIn("return", get_type_hints(function))

    def test_wrong_error_timeout_foreign_exception_and_unknown_remain_exceptions(self) -> None:
        errors = (rejection(message="other native error"), RuntimeError(ERROR), TimeoutError("timeout"))
        for error in errors:
            with self.subTest(error=type(error).__name__):
                fixture = DriverFixture(self.runtime, error)
                with self.assertRaises(type(error)) as caught:
                    self.runtime.execute(fixture, STEP, expected_revision=90)
                self.assertIs(caught.exception, error)
                self.assertEqual(fixture.calls, 1)
                self.assertEqual(fixture.snapshot_reads, 0)
                self.assertIs(fixture.history[-1]["ok"], False)
                self.assertIsNone(fixture.history[-1]["result"])

    def test_real_driver_rejects_frame_or_request_drift_without_replay(self) -> None:
        changed = frame()
        changed["date_raw"] = 1024
        bad_request = request()
        bad_request["protocol_version"] = True
        for error, current in ((rejection(), changed), (rejection(asked=bad_request), frame())):
            fixture = DriverFixture(self.runtime, error, current=current)
            with self.assertRaises(type(error)) as caught:
                self.runtime.execute(fixture, STEP, expected_revision=90)
            self.assertIs(caught.exception, error)
            self.assertEqual(fixture.calls, 1)
            self.assertIsNone(fixture.history[-1]["result"])

    def test_only_canonical_read_query_is_projected(self) -> None:
        for step in ("surrender-war-88", "offer-white-peace-88", "query-war-termination-options-088",
                     "query-war-termination-options-0", "query-war-termination-options-2147483648",
                     "query-war-termination-options-\uff18\uff18", STEP + " ", " " + STEP):
            with self.subTest(step=step):
                self.assertIsNone(self.call(step=step))
        self.assertIsNone(self.call(error="war-termination completion snapshot read failed; extra"))
        for value in (None, True, 1.0, 7, "", "other"):
            with self.subTest(request_id=value):
                self.assertIsNone(self.call(rid=value))

    def test_request_and_response_fields_are_exact(self) -> None:
        result: object
        for make, argument in ((request, "asked"), (response, "replied")):
            for key in make():
                value = make()
                del value[key]
                with self.subTest(argument=argument, missing=key):
                    self.assertIsNone((self.call(asked=value) if argument == "asked" else self.call(replied=value)))
            value = make()
            value["unexpected"] = None
            self.assertIsNone((self.call(asked=value) if argument == "asked" else self.call(replied=value)))
        for proto in (True, 1.0, Number.ONE, None, 2, "1"):
            for argument, make in (("asked", request), ("replied", response)):
                value = make()
                value["protocol_version"] = proto
                self.assertIsNone((self.call(asked=value) if argument == "asked" else self.call(replied=value)))
        for ok in (True, 0, None, "false"):
            value = response()
            value["ok"] = ok
            self.assertIsNone(self.call(replied=value))
        for result in (None, {}, [], False):
            value = response()
            value["result"] = result
            self.assertIsNone(self.call(replied=value))

    def test_frame_identity_types_missing_null_and_drift(self) -> None:
        value: object
        paths = (
            ("revision",), ("native_revision",), ("date_raw",),
            ("played_character", "character_id"), ("diagnostics", "bridge_pid"),
            ("diagnostics", "connection_generation"),
        )
        for path in paths:
            for value in (None, True, 1.0, Number.ONE, 0, -1, 2**53, "1"):
                changed = frame()
                put(changed, path, value)
                with self.subTest(path=path, value=value):
                    self.assertIsNone(self.call(start=changed, current=deepcopy(changed)))
            changed = frame()
            parent = changed if len(path) == 1 else record(changed[path[0]])
            del parent[path[-1]]
            self.assertIsNone(self.call(start=changed, current=deepcopy(changed)))
        for path, value in ((("snapshot_id",), "different"), (("episode_run_id",), "other"),
                            (("paused",), False), (("map_ready",), False),
                            (("played_character", "alive"), False)):
            changed = frame()
            put(changed, path, value)
            self.assertIsNone(self.call(current=changed))
        for value in (None, [], "", 0):
            self.assertIsNone(self.runtime.unavailable(step=STEP, native_error=ERROR,
                native_request_id="step-5-61e52e058ce3", request=request(), response=response(),
                starting=value, current=value))

    def test_war_signature_exact_types_and_nullable_presence(self) -> None:
        value: object
        for key in ("war_id", "primary_opponent_character_id", "player_relative_war_score"):
            for value in (True, 1.0, Number.ONE, "1"):
                changed = frame()
                war(changed)[key] = value
                self.assertIsNone(self.call(start=changed, current=deepcopy(changed)))
        for key in ("player_is_primary_war_leader", "primary_opponent_character_id"):
            changed = frame()
            war(changed)[key] = None
            self.assertIsNotNone(self.call(start=changed, current=deepcopy(changed)))
            del war(changed)[key]
            self.assertIsNone(self.call(start=changed, current=deepcopy(changed)))
        for value in (None, (2254,), [True], [1.0], [2254, 2254]):
            changed = frame()
            war(changed)["targeted_title_ids"] = value
            self.assertIsNone(self.call(start=changed, current=deepcopy(changed)))

    def test_same_day_same_source_defer_and_changed_scope_requeries(self) -> None:
        value: object
        retained = self.retained()
        variants = (
            (("date_raw",), 1024), (("episode_run_id",), "other"),
            (("played_character", "character_id"), 708),
            (("diagnostics", "bridge_pid"), 124),
            (("diagnostics", "connection_generation"), 2),
        )
        for path, value in variants:
            current = frame()
            put(current, path, value)
            self.assertIsNone(self.runtime.deferred(current, war(current), retained))
        for key, value in (("player_side", "defender"), ("player_is_primary_war_leader", False),
                           ("primary_opponent_character_id", 809), ("player_relative_war_score", 18),
                           ("targeted_title_ids", [2255])):
            current = frame()
            war(current)[key] = value
            self.assertIsNone(self.runtime.deferred(current, war(current), retained))
        current = frame()
        current.update(snapshot_id="native:91", revision=91, native_revision=91)
        self.assertIsNotNone(self.runtime.deferred(current, war(current), retained))
        next_day = frame()
        next_day["date_raw"] = 1024
        history = [{"command": STEP, "ok": False, "result": retained[0]["result"]}]
        plan = self.runtime.plan(history, snapshot=next_day, action_steps=(STEP, "life-advance"))
        self.assertEqual(plan["selected_step"], STEP)

    def test_mutation_unknown_and_failed_records_invalidate_defer(self) -> None:
        records: list[Doc]
        for step in ("offer-white-peace-88", "surrender-war-88", "war-enforce-demands",
                     "enforce-demands-war-88", "restore-checkpoint", "load-checkpoint"):
            records = [{"step": step, "ok": True}, *self.retained()]
            with self.subTest(step=step):
                self.assertIsNone(self.runtime.deferred(frame(), war(frame()), records))
        for flag in (None, False, 0, 1):
            records = [{"step": "move-army-1-to-2", "ok": flag}, *self.retained()]
            self.assertIsNone(self.runtime.deferred(frame(), war(frame()), records))
        records = [{"step": "move-army-1-to-2", "ok": True}, *self.retained()]
        self.assertIsNotNone(self.runtime.deferred(frame(), war(frame()), records))
        for flag in (None, True, 0):
            records = self.retained()
            records[0]["ok"] = flag
            self.assertIsNone(self.runtime.deferred(frame(), war(frame()), records))

    def test_stored_json_literals_and_null_are_not_python_numeric_equality(self) -> None:
        value: object
        bad: object
        for key in ("accepted", "available", "business_submission", "replay_allowed",
                    "read_only", "replan_required", "semantic_publication_rechecked",
                    "fresh_native_completion_proved"):
            for bad in (0, 1, None):
                value = self.runtime.unavailable_result()
                value[key] = bad
                self.assertIsNone(self.runtime.parse_stored(value))
        for value in (None, {}, [], "", False):
            self.assertIsNone(self.runtime.parse_stored(value))
        for bad in ([], {}, False):
            value = self.runtime.unavailable_result()
            value["war_termination_options"] = bad
            self.assertIsNone(self.runtime.parse_stored(value))
        value = self.runtime.unavailable_result()
        del value["war_termination_options"]
        self.assertIsNone(self.runtime.parse_stored(value))

    def test_history_scan_is_bounded(self) -> None:
        good: Doc = {"step": "query-other", "ok": True}
        self.assertIsNotNone(self.runtime.deferred(frame(), war(frame()),
            [good] * 511 + self.retained()))
        self.assertIsNone(self.runtime.deferred(frame(), war(frame()),
            [good] * 512 + self.retained()))

    def test_driver_mutation_branch_is_unchanged(self) -> None:
        name = "_execute_war_termination_step"
        original = definitions(self.runtime.before_driver, {name})
        projected = deepcopy(definitions(self.runtime.driver_raw, {name}))
        handlers = [node for node in ast.walk(projected) if isinstance(node, ast.ExceptHandler)
                    and any(isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                            and call.func.id == "war_termination_optional_unavailable_v1"
                            for call in ast.walk(node))]
        self.assertEqual(len(handlers), 1)
        inserted = handlers[0].body.pop(0)
        self.assertIsInstance(inserted, ast.If)
        self.assertEqual(ast.dump(original, include_attributes=False),
                         ast.dump(projected, include_attributes=False))



    def test_real_source_recipe_accepts_whole_states_and_rejects_partial_install(self) -> None:
        driver, strategy, contract = (self.runtime.driver_raw,
                                     self.runtime.strategy_raw, self.runtime.contract_raw)
        original, projected, installed = source_views_v1(driver, strategy, contract)
        self.assertTrue(installed)
        self.assertEqual(projected, {"native_driver": driver, "strategy": strategy,
                                     "war_contract": contract})
        self.assertEqual(original["native_driver"], self.runtime.before_driver)
        self.assertEqual(original["strategy"], self.runtime.before_strategy)
        restored, forward, installed = source_views_v1(
            original["native_driver"], original["strategy"], original["war_contract"])
        self.assertFalse(installed)
        self.assertEqual(restored, original)
        self.assertEqual(forward, projected)
        invalid: list[tuple[bytes, bytes, bytes]] = [
            (original["native_driver"], strategy, contract),
            (driver, original["strategy"], contract),
            (driver, strategy, original["war_contract"]),
            (driver + driver, strategy, contract),
            (driver, strategy + strategy, contract),
            (driver, strategy, contract + b"\n# foreign suffix\n"),
            (driver, strategy, contract + producer.WAR_CONTRACT_ADDITION_V1.encode()),
        ]
        for values in invalid:
            with self.subTest(lengths=[len(item) for item in values]), self.assertRaises(ValueError):
                source_views_v1(*values)

if __name__ == "__main__":
    unittest.main()
