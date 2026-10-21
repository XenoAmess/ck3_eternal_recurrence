"""Real Source31 producers and consumers, composed in RAM; no Game, SDK process or disk state."""
from __future__ import annotations

import argparse
import ast
import copy
import importlib
import json
import sys
import types
import unittest
from collections.abc import Iterator
from contextlib import contextmanager
from enum import IntEnum
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_wartime_sway_opportunity_v1 import BASELINE, HELPER, NEW_LEAF, compose_wartime_sway_opportunity_v1

SOURCE_ROOT: Path | None = None
_NAMES = ("xar_autoplayer.bridge.war_stationary_sway_opportunity_v1",
          "xar_autoplayer.sway_formal_consumer", "xar_autoplayer.ordinary_sway_schedule_v1",
          "xar_autoplayer.bridge.ordinary_sway_service_v1")


def _mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or any(type(key) is not str for key in value):
        raise AssertionError("expected string-keyed object")
    return value


def _rows(value: object) -> list[object]:
    if not isinstance(value, list):
        raise AssertionError("expected JSON array")
    return value


@contextmanager
def _composed(root: Path) -> Iterator[tuple[types.ModuleType, types.ModuleType, types.ModuleType, types.ModuleType]]:
    sys.path.insert(0, str(root))
    # Import every original dependency before replacing precisely the four leaves.
    for name in _NAMES[1:]:
        importlib.import_module(name)
    originals = {name: sys.modules.get(name) for name in _NAMES}
    sources = compose_wartime_sway_opportunity_v1({name: (root / name).read_bytes() for name in BASELINE})
    loaded: list[types.ModuleType] = []
    try:
        for name in _NAMES:
            module = types.ModuleType(name)
            module.__package__ = name.rpartition(".")[0]
            sys.modules[name] = module
            exec(compile(sources[name.replace(".", "/") + ".py"], name, "exec"), module.__dict__)
            loaded.append(module)
        yield loaded[0], loaded[2], loaded[3], loaded[1]
    finally:
        for name, original in originals.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original
        sys.path.remove(str(root))


def _frame() -> dict[str, object]:
    # The real canonical army normalizer supplies these field names; it has no gathering bool.
    from xar_autoplayer.bridge.war_contract import normalize_armies
    army = normalize_armies([{"army_id": 101, "owner_character_id": 12, "soldiers": None,
        "current_province_id": 9, "move_target_province_id": None, "move_target_observable": False,
        "controllable": True, "army_state": "regular", "in_combat": False, "retreating": False,
        "route_read_status": "complete_empty", "route_source_count": 0, "route_province_ids": []}])[0]
    return {"snapshot_id": "native:50", "revision": 51, "native_revision": 50, "date_raw": 12000,
        "episode_run_id": "test-current-12", "episode_character_id": 12,
        "played_character": {"character_id": 12, "alive": True}, "paused": True, "map_ready": True,
        "one_life_terminal": False, "one_life_terminal_reason": None, "episode_identity_pending": False,
        "active_event": None, "pending_character_interaction": None,
        "top_exclusive_modal_choice_hint": {"status": "absent", "owner_verified": True},
        "diagnostics": {"bridge_pid": 111, "connection_generation": 1},
        "player_armies": [army], "active_wars": [{"war_id": 88, "enemy_armies": [{"army_id": 202}]}]}


def _root(frame: dict[str, object]) -> dict[str, object]:
    return {"campaign_root_context": {"status": "available", "player_character_id": 12,
        "player_character_alive": True, "snapshot_revision": frame["native_revision"],
        "date_raw": frame["date_raw"], "direct_landed_vassal_character_ids": [55]}}


def _proof() -> dict[str, object]:
    def route(army: int, province: int) -> dict[str, object]:
        return {"timeline_observable": True, "army_id": army, "current_province_id": province,
            "effective_origin_province_id": province, "route_province_ids": [], "arrival_date_raws": []}
    return {"status": "available", "date_raw": 12000, "snapshot_revision": 50,
        "subject_army_id": 101, "target_province_id": 9, "hostile_army_ids": [202],
        "subject_route": route(101, 9), "hostile_routes": [route(202, 20)],
        "horizon_start_date_raw": 12000, "horizon_end_date_raw": 12024,
        "one_day_contact_free": True, "conflicts": []}


def _ledger() -> dict[str, object]:
    from xar_autoplayer.bridge.version_identity import CK3_12004
    identity = {"action_id": "retained-old-sway", "actor_character_id": 12,
        "target_character_id": 55, "scheme_instance_id": 83887164, "scheme_instance_generation": 5}
    native = {"schema": "xar.ck3.sway_completion.v1", "available": True, **identity,
        "snapshot_revision": 40, "date_raw": 11000, "instance_source_observed": True,
        "instance_present": False, "storage_slot_reused": True, "exact_instance_join_ready": False,
        "native_status_observed": False, "native_terminal_state_observed": False, "native_status_raw": None,
        "exact_ck3_build": CK3_12004.game_version, "exe_sha256": CK3_12004.executable_sha256}
    observation = {**identity, "source_native_revision": 40, "source_date_raw": 11000,
        "tracked_instance_active": False, "instance_terminal_outcome_observed": False,
        "native_observation": native, "exact_ck3_build": CK3_12004.game_version,
        "exe_sha256": CK3_12004.executable_sha256}
    return {"schema": "xar.ck3.active-scheme-sway-formal-private.v1", "pending": None,
        "resolved": {"status": "applied", "postcondition_verified": True, **identity,
            "post_native_revision": 10, "post_date_raw": 10000,
            "pre_capture_epoch": 1, "post_capture_epoch": 3,
            "native_receipt": {"schema": "active-scheme-sway-formal-private-v1", "stage": "applied",
                "postcondition_verified": True, "action_id": identity["action_id"],
                "scheme_instance_id": identity["scheme_instance_id"], "scheme_instance_generation": 5,
                "post_capture_epoch": 2, "post_date_raw": 10000,
                "exact_ck3_build": CK3_12004.game_version, "exe_sha256": CK3_12004.executable_sha256},
            "applied_instance_observation": {**identity}, "latest_instance_observation": observation,
            "terminal_intervention": {"instance_terminal_outcome_observed": False, "terminal_cause": "unknown"}}}


def _state() -> dict[str, object]:
    return {"actor_character_id": 12, "last_target_character_id": 55, "no_operation_count": 0,
        "last_check_date_raw": 11000, "next_check_date_raw": 11720, "frontier_membership": [55],
        "last_observation_attempt_action_id": "retained-old-sway", "last_terminal_action_id": None,
        "last_job_kind": "observe_applied"}


def _read() -> dict[str, object]:
    return {"schema": "active-scheme-sway-private-read-v1", "queried_revision": 51,
        "queried_native_revision": 50, "snapshot_revision": 50, "date_raw": 12000,
        "actor_character_id": 12, "target_character_id": 55, "capture_epoch": 10, "container_generation": 11,
        "target_opinion_of_actor": 0, "active_scheme_count": 0, "active_sway_instances": [],
        "matching_sway_active": False, "native_complete_can_send": True, "native_legal_now": True,
        "exact_ck3_build": "1.20.0.4",
        "exe_sha256": "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"}


class _Driver:
    allow_private_active_scheme_sway_query = True
    allow_private_active_scheme_sway_action = True
    allow_private_active_scheme_sway_completion_query = True
    state_dir = Path("RAM-only-no-file-operation")
    submits = 0

    def query_active_scheme_sway_target_private_v1(self, *, expected_revision: int,
            target_character_id: int) -> dict[str, object]:
        if expected_revision != 51 or target_character_id != 55:
            raise AssertionError("wrong target read binding")
        return _read()

    def submit_active_scheme_sway_private_v1(self, *, readback: dict[str, object],
            action_id: str) -> dict[str, object]:
        from xar_autoplayer.bridge.driver import BridgeUnavailableError
        self.submits += 1
        raise BridgeUnavailableError("test boundary: unknown native result retained; never successful business credit")


class _Service:
    def _strategy_state_dir(self) -> Path:
        return Path("RAM-only-no-file-operation")

    def __init__(self, frame: dict[str, object]) -> None:
        self.driver = _Driver()
        self.frame = frame
        self.snapshots = 0
        self.following = 0

    def snapshot(self, *, include_native_command_history: bool = False) -> dict[str, object]:
        self.snapshots += 1
        return copy.deepcopy(self.frame)

    def _plan_turn_internal(self) -> dict[str, object]:
        self.following += 1
        return {"plan": {"selected_step": "fresh-normal-replan"}}

    def _execute_planned_turn(self, planned: dict[str, object], *, before_submit: object = None) -> dict[str, object]:
        return {"status": "executed", "selected_step": "fresh-normal-replan", "result": {}}



@contextmanager
def _pure_helper() -> Iterator[types.ModuleType]:
    """Compile unchanged production AST that has no SDK dependency; no fake native provider."""
    names = {"_Frame", "_mapping", "_integer", "_positive", "_text", "_binding",
        "_quiet", "project_safety_inputs_v1", "object_v1"}
    nodes: list[ast.stmt] = [node for node in ast.parse(HELPER).body if
        isinstance(node, (ast.Import, ast.ImportFrom)) and getattr(node, "level", 0) == 0
        or isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
    name = "_portable_wartime_sway_contract_v1"
    original = sys.modules.get(name)
    module = types.ModuleType(name)
    sys.modules[name] = module
    try:
        exec(compile(ast.Module(body=nodes, type_ignores=[]), name, "exec"), module.__dict__)
        yield module
    finally:
        if original is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = original


class WartimeSwayContractTests(unittest.TestCase):
    def test_exact_integer_binding(self) -> None:
        with _pure_helper() as helper:
            frame = {"snapshot_id": "native:1", "revision": 1, "native_revision": 1, "date_raw": 24,
                "episode_run_id": "pure-e", "played_character": {"character_id": 12},
                "diagnostics": {"bridge_pid": 44, "connection_generation": 1}}
            self.assertIsNotNone(helper._binding(frame))
            class Revision(IntEnum):
                ONE = 1
            for key in ("revision", "native_revision", "date_raw"):
                for invalid in (True, 1.0, Revision.ONE, None, "1"):
                    self.assertIsNone(helper._binding({**frame, key: invalid}), (key, invalid))
            self.assertIsNone(helper._mapping({True: "wrong JSON key"}))

    def test_small_projection_preserves_missing_and_null(self) -> None:
        with _pure_helper() as helper:
            result = helper.project_safety_inputs_v1({
                "diagnostics": {"bridge_pid": 44, "connection_generation": 1, "opaque": 2**64-1},
                "top_exclusive_modal_choice_hint": {"status": "absent", "owner_verified": True, "huge": "x"*1024}})
            self.assertEqual(set(result["diagnostics"]), {"bridge_pid", "connection_generation"})
            self.assertEqual(set(result["top_exclusive_modal_choice_hint"]), {"status", "owner_verified"})
            self.assertNotIn("diagnostics", helper.project_safety_inputs_v1({}))
            self.assertIsNone(helper.project_safety_inputs_v1({"diagnostics": None})["diagnostics"])
            self.assertEqual(helper.project_safety_inputs_v1({"diagnostics": {}})["diagnostics"], {})


class WartimeSwayTests(unittest.TestCase):
    root: Path
    @classmethod
    def setUpClass(cls) -> None:
        if SOURCE_ROOT is None:
            raise unittest.SkipTest("requires explicit --source-root immutable Source31 export")
        cls.root = SOURCE_ROOT

    def _plan(self, service: types.ModuleType, frame: dict[str, object] | None = None) -> dict[str, object]:
        frame = _frame() if frame is None else frame
        return {"snapshot_id": frame["snapshot_id"], "revision": frame["revision"],
            "planning_source_frame": {"schema": "xar.ck3.planning-source-frame/v1", "status": "complete",
                **{k: frame[k] for k in ("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id")},
                "actor_character_id": 12, "bridge_pid": 111, "connection_generation": 1},
            "_ordinary_sway_input_v1": service.project_ordinary_sway_input_v1(frame, _root(frame)),
            "plan": {"phase": "native_war_stationary_contact_horizon_progress",
                "selected_step": "advance-route-contact-horizon-v1-101-to-9-h-1-202",
                "route_audit": {"status": "safe_one_day_stationary_contact_horizon", "contact_horizon": _proof()}}}

    def test_finite_preimage_guard(self) -> None:
        data = {name: (self.root / name).read_bytes() for name in BASELINE}
        self.assertEqual(set(compose_wartime_sway_opportunity_v1(data)), {*BASELINE, NEW_LEAF})
        name = next(iter(data))
        with self.assertRaises(ValueError):
            compose_wartime_sway_opportunity_v1({**data, name: data[name] + b"\n"})
        with self.assertRaises(ValueError):
            compose_wartime_sway_opportunity_v1({**data, "unknown.py": b""})

    def test_actual_projection_window_schedule_and_json_roundtrip(self) -> None:
        with _composed(self.root) as (helper, scheduler, service, _):
            plan = self._plan(service)
            window = helper.build_window_v1(plan)
            self.assertIsNotNone(window)
            self.assertEqual(helper.parse_window_v1(json.loads(json.dumps(window))), window)
            source = _mapping(_mapping(plan["_ordinary_sway_input_v1"])["snapshot"])
            job = scheduler.plan_ordinary_sway_schedule_v1(source,
                selected_step=_mapping(plan["plan"])["selected_step"], root=_root(_frame())["campaign_root_context"],
                ledger=_ledger(), state=_state(), war_stationary_window=window)
            self.assertEqual(job["job"], "query_selected_target")
            self.assertIs(job["submit_allowed"], False)
            self.assertIs(_mapping(_mapping(_ledger()["resolved"])["terminal_intervention"])["instance_terminal_outcome_observed"], False)

    def test_original_route_query_preserved(self) -> None:
        with _composed(self.root) as (_, _, service, _):
            plan = self._plan(service)
            _mapping(plan["plan"])["phase"] = "native_war_stationary_contact_horizon"
            _mapping(plan["plan"])["selected_step"] = "query-route-contact-horizon-v1-101-to-9-h-1-202"
            instance = _Service(_frame())
            with patch.object(service, "_inputs", side_effect=AssertionError("query must not read optional state")):
                self.assertIs(service.stage_ordinary_sway_v1(instance, plan), plan)

    def test_missing_wrong_types_conflicts_and_binding_rejected(self) -> None:
        with _composed(self.root) as (helper, _, service, _):
            class Revision(IntEnum):
                ONE = 1
            for outer in (True, 1.0, Revision.ONE):
                frame = _frame()
                frame["revision"] = 1
                planned = self._plan(service, frame)
                planned["revision"] = outer
                self.assertIsNone(helper.build_window_v1(planned))
            window = helper.build_window_v1(self._plan(service))
            self.assertIsNotNone(window)
            for key in ("revision", "native_revision", "date_raw", "actor_character_id", "bridge_pid", "connection_generation"):
                for bad in (True, 1.0, None, "1"):
                    value = copy.deepcopy(window)
                    _mapping(value)[key] = bad
                    self.assertIsNone(helper.parse_window_v1(value), (key, bad))
            for key in _mapping(window):
                value = copy.deepcopy(window)
                del _mapping(value)[key]
                self.assertIsNone(helper.parse_window_v1(value), key)
            value = copy.deepcopy(window)
            _mapping(_mapping(value)["contact_horizon"])["one_day_contact_free"] = False
            self.assertIsNone(helper.parse_window_v1(value))
            for key in ("revision", "date_raw", "episode_run_id"):
                frame = _frame()
                frame[key] = 999 if key != "episode_run_id" else "other"
                self.assertFalse(helper.require_current_window_v1(window, frame))

    def test_military_modal_route_and_unknown_inputs_keep_priority(self) -> None:
        with _composed(self.root) as (helper, _, service, _):
            for key, bad in (("in_combat", True), ("retreating", True), ("army_state", "gathering"),
                    ("army_state", None), ("route_read_status", None), ("route_province_ids", [10]),
                    ("move_target_observable", True)):
                frame = _frame()
                _mapping(_rows(frame["player_armies"])[0])[key] = bad
                self.assertIsNone(helper.build_window_v1(self._plan(service, frame)), (key, bad))
            for key, frame_bad in (("paused", False), ("episode_identity_pending", True),
                    ("top_exclusive_modal_choice_hint", None),
                    ("active_context", {"active_event": {"id": 1}, "pending_character_interaction": None})):
                frame = _frame()
                frame[key] = frame_bad
                self.assertIsNone(helper.build_window_v1(self._plan(service, frame)), key)

    def test_monthly_gate_pending_and_no_root_are_not_bypassed(self) -> None:
        with _composed(self.root) as (helper, schedule, service, _):
            plan = self._plan(service)
            source = _mapping(_mapping(plan["_ordinary_sway_input_v1"])["snapshot"])
            window = helper.build_window_v1(plan)
            args = {"selected_step": _mapping(plan["plan"])["selected_step"], "ledger": _ledger(),
                "root": _root(_frame())["campaign_root_context"], "war_stationary_window": window}
            state = _state()
            state["next_check_date_raw"] = 13000
            self.assertIsNone(schedule.plan_ordinary_sway_schedule_v1(source, state=state, **args)["job"])
            self.assertEqual(schedule.plan_ordinary_sway_schedule_v1(source, state=_state(), **{**args, "root": None})["reason"],
                "same_frame_root_unavailable")
            ledger = _ledger()
            ledger["pending"] = {"actor_character_id": 12, "target_character_id": 55, "action_id": "original-pending"}
            job = schedule.plan_ordinary_sway_schedule_v1(source, state=_state(), **{**args, "ledger": ledger})
            self.assertEqual(job["job"], "reconcile_pending")
            self.assertIs(job["submit_allowed"], False)

    def test_consumer_guard_rejects_after_native_target_query(self) -> None:
        with _composed(self.root) as (helper, _, service, consumer):
            instance = _Service(_frame())
            window = helper.build_window_v1(self._plan(service))
            read = instance.driver.query_active_scheme_sway_target_private_v1(expected_revision=51, target_character_id=55)
            _mapping(_rows(instance.frame["player_armies"])[0])["in_combat"] = True
            writes: list[object] = []
            with patch.object(consumer, "read_sway_ledger", return_value=_ledger()), \
                    patch.object(consumer, "_write", side_effect=lambda *args: writes.append(args)):
                result = consumer.consume_sway_private_once(instance.driver, target_character_id=55,
                    snapshot=_frame(), readback=read,
                    pre_submit_admission=lambda: helper.require_current_window_v1(window, instance.snapshot()))
            self.assertEqual(result["status"], "wartime_opportunity_no_longer_admitted")
            self.assertEqual(instance.driver.submits, 0)
            self.assertEqual(writes, [])

    def test_real_stage_execute_consumer_unknown_submit_never_replayed(self) -> None:
        with _composed(self.root) as (_, _, service, consumer):
            frame, ledger, state = _frame(), _ledger(), _state()
            instance = _Service(frame)
            writes: list[object] = []
            def write_ram(directory: Path, value: dict[str, object]) -> None:
                ledger.clear()
                ledger.update(copy.deepcopy(value))
                writes.append(copy.deepcopy(value))
            with patch.object(service, "_inputs", side_effect=lambda _: (Path("RAM"), state, ledger)), \
                    patch.object(service, "write_json_atomic", side_effect=lambda *args: None), \
                    patch.object(consumer, "read_sway_ledger", side_effect=lambda _: copy.deepcopy(ledger)), \
                    patch.object(consumer, "_write", side_effect=write_ram):
                planned = service.stage_ordinary_sway_v1(instance, self._plan(service))
                self.assertEqual(planned["plan"]["selected_step"], service.STEP)
                result = service.execute_ordinary_sway_v1(instance, planned)
                self.assertEqual(instance.driver.submits, 1)
                self.assertGreaterEqual(instance.snapshots, 2)
                self.assertIsNotNone(ledger["pending"])
                self.assertEqual(result["selected_step"], "fresh-normal-replan")
                self.assertEqual(result["ordinary_sway_optional"]["outcome"], "pending")
                consumer.consume_sway_private_once(instance.driver, target_character_id=55,
                    snapshot=frame, readback=_read(), pre_submit_admission=lambda: True)
                self.assertEqual(instance.driver.submits, 1)
                self.assertEqual(_mapping(_mapping(ledger["resolved"])["terminal_intervention"])["terminal_cause"], "unknown")


def main() -> None:
    global SOURCE_ROOT
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()
    SOURCE_ROOT = args.source_root
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(cls)
        for cls in (WartimeSwayTests, WartimeSwayContractTests))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()

