"""Future-C19 source overlay and in-memory actual WAL integration qualification.

Only immutable source bytes are read. Synthetic Driver bytes live in a Python
dictionary; no temporary SDK, file, Game, RPC, or storage benchmark is created.
"""
from copy import deepcopy
import ast
import hashlib
import json
from pathlib import Path
import sys
import threading
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player/src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from xar_autoplayer.bridge import native_driver as nd
from xar_autoplayer.bridge.driver_state_history_json import DriverStateHistoryJsonCache
from xar_autoplayer.bridge.bounded_multiday_wal_v1 import (
    OWNER_KEY, eligible_bounded_multiday_delta_v1, owner_proof_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12004
from bounded_multiday_wal_source_v1 import (
    METHODS, method_fingerprints, transform_driver_bytes_v1, reverse_driver_bytes_v1,
)

SOURCE_ROOT = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/sdk-v20261019-candidate/src14/xar_autoplayer/bridge")
PINS = {
    "native_driver.py": (1637048, "cc60c9af670c37ef2085f66d07db17a2bd309660fcb60c05a5340df7720874ab"),
    "driver_state_wal_v1.py": (23998, "8a738446148f33dd92d0e3489dfb002c675fb50b23e00320df11cbfad855324d"),
}


def source(name):
    value = (SOURCE_ROOT / name).read_bytes()
    size, sha = PINS[name]
    if len(value) != size or hashlib.sha256(value).hexdigest() != sha:
        raise ValueError("immutable qualification source changed: " + name)
    return value


def frame(date=2400, native=1, revision=1):
    return {
        "backend_id": "native-headless", "source": "injected-dll-named-pipe",
        "paused": True, "map_ready": True, "revision": revision,
        "native_revision": native, "snapshot_id": f"native:{native}", "date_raw": date,
        "played_character": {"character_id": 7, "alive": True},
        "episode_character_id": 7, "episode_run_id": "native-7-c19-test",
        "local_player_id": 1, "diagnostics": {
            "connected": True, "bridge_pid": 12345, "connection_generation": 2,
            "hello": {"ck3_build_match": True,
                      "expected_ck3_version": CK3_12004.game_version,
                      "expected_ck3_sha256": CK3_12004.executable_sha256}},
    }


def advance(days=8, start=2400):
    end = start + 24 * days
    common = dict(generation=4, starting_date_raw=start, target_date_raw=end,
                  mode="terminal_or_sentinel", speed=5, army_count=0, combat_count=0,
                  terminal_observed=False, abnormal=False)
    armed = dict(common, state="armed", completed_daily_ticks=0, last_observed_date_raw=start)
    stopped = dict(common, state="triggered", completed_daily_ticks=days,
                   last_observed_date_raw=end, trigger_date_raw=end,
                   signed_date_delta_from_target_raw=0, overshoot_days=0,
                   intermediate_pause_count=0, trigger_reasons=["date_deadline"],
                   trigger_flags=1, pause_wrapper_called=True, pause_observed=True)
    return dict(step="life-advance", starting_date_raw=start, ending_date_raw=end,
                elapsed_days=days, requested_horizon_days=days, paused=True,
                progress_status="postcondition", final_screen="map_hud", timeline_speed=5,
                active_event=None, pending_character_interaction=None, ordinary_events=[],
                campaign_deadline_v1={"target_date_raw": end},
                campaign_deadline_native_clock_v1={
                    "schema": "xar.ck3.campaign-native-date-clock/v1",
                    "scope": "campaign_date_deadline", "starting_date_raw": start,
                    "target_date_raw": end, "armed": armed, "stopped": stopped,
                    "early_boundary_cancel": None, "exact_one_day_qualification_claimed": False},
                **{OWNER_KEY: owner_proof_v1(frame(start), frame(end, 2, 2))})


def change(value, path, replacement):
    current = value
    for key in path[:-1]:
        current = current[key]
    current[path[-1]] = replacement


class MemoryPath:
    def __init__(self, memory, name):
        self.memory, self.name = memory, name

    def with_name(self, name):
        return MemoryPath(self.memory, name)

    def read_bytes(self):
        if self.name not in self.memory.files:
            raise FileNotFoundError(self.name)
        return self.memory.files[self.name][0]

    def stat(self):
        data = self.read_bytes()
        generation = self.memory.files[self.name][1]
        return SimpleNamespace(st_dev=1, st_ino=generation, st_size=len(data),
                               st_mtime_ns=generation, st_ctime_ns=generation)

    def unlink(self, missing_ok=False):
        if self.name not in self.memory.files and not missing_ok:
            raise FileNotFoundError(self.name)
        self.memory.files.pop(self.name, None)

    def __str__(self):
        return "memory-only/" + self.name


class MemoryFS:
    def __init__(self):
        self.files, self.writes, self.counter = {}, [], 0
        self.base = MemoryPath(self, "driver-state.json")
        self.fail_full = False
        self.fail_journal = False

    def exists(self, path):
        if not isinstance(path, MemoryPath):
            raise ValueError("test attempted an unowned path")
        return path.name in self.files

    def write(self, path, data, **unused):
        if not isinstance(path, MemoryPath):
            raise ValueError("test attempted a real write")
        if self.fail_full and path.name == self.base.name:
            raise OSError("injected full barrier failure")
        if self.fail_journal and path.name != self.base.name:
            raise OSError("injected journal publication failure")
        self.counter += 1
        self.files[path.name] = (bytes(data), self.counter)
        self.writes.append(path.name)


def methods_from(data, names, namespace):
    result = {}
    tree = ast.parse(data)
    for name in names:
        matches = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name]
        if len(matches) != 1:
            raise ValueError("test method boundary changed: " + name)
        module = ast.fix_missing_locations(ast.Module(body=[matches[0]], type_ignores=[]))
        exec(compile(module, "<immutable-c19-methods>", "exec"), namespace)
        result[name] = namespace[name]
    return result


def make_driver(candidate, memory, *, enabled=True):
    namespace = dict(vars(nd))
    namespace.update(os=SimpleNamespace(path=SimpleNamespace(lexists=memory.exists)),
                     write_bytes_atomic=memory.write, start_army_timing=lambda *a, **k: None,
                     finish_army_timing=lambda *a, **k: None)
    names = ("_record_command", "_route_horizon_wal_eligible_v1",
             "_driver_state_wal_scalar_fields_locked_v1", "_try_persist_driver_state_wal_append_v1",
             "_persist_driver_state", "_encode_driver_state_locked")
    attrs = methods_from(candidate, names, namespace)
    attrs["_native_driver_state_path"] = lambda self: memory.base
    cls = type("SourceBoundMemoryDriver", (nd.NativeHeadlessGameplayDriver,), attrs)
    obj = cls.__new__(cls)
    obj.state_dir = object()
    obj.pipe_name = "synthetic-c19-wal"
    obj._driver_state_lock = threading.RLock()
    obj._history_lock = obj._driver_state_lock
    obj._driver_state_write_lock = threading.Lock()
    obj._driver_state_history_json = DriverStateHistoryJsonCache()
    obj._driver_state_dirty, obj._driver_state_error = False, None
    obj.allow_driver_state_wal_v1 = enabled
    obj._driver_state_wal_document = None
    obj._driver_state_wal_committed_rows = 0
    obj._driver_state_wal_replay_status = None
    obj._driver_state_wal_base_stat = obj._driver_state_wal_base_sha256 = None
    obj._driver_state_wal_base_version = None
    obj._driver_state_wal_barrier_required = True
    obj._driver_state_wal_barrier_generation = 0
    obj._session_bridge_pid = 12345
    obj._episode_character_id, obj._episode_run_id = 7, "native-7-c19-test"
    obj._last_checkpoint, obj._command_history = None, []
    obj._rollback_war_failures, obj._rollback_war_failures_migration_required = [], False
    obj._managed_restore_transaction = obj._succession_expectation = None
    obj._succession_lifecycle, obj._campaign_goal = None, None
    obj._natural_successor_persistence_unconfirmed = False
    return obj


class BoundedMultidaySourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = source("native_driver.py")
        cls.candidate = transform_driver_bytes_v1(cls.original)
        cls.wal = ModuleType("xar_autoplayer.bridge.driver_state_wal_v1")
        exec(compile(source("driver_state_wal_v1.py"), "<immutable-wal-source>", "exec"), vars(cls.wal))

    def test_exact_source_inverse_and_old_branches_are_unchanged(self):
        self.assertEqual(reverse_driver_bytes_v1(self.candidate), self.original)
        self.assertEqual(method_fingerprints(self.original), METHODS)
        with self.assertRaises(ValueError):
            transform_driver_bytes_v1(self.candidate)
        changed = self.original.replace(b"# Reuse the exact-day native clock proof.", b"# Drifted native clock proof.")
        # A comment alone keeps AST but the literal anchor still refuses it.
        with self.assertRaises(ValueError):
            transform_driver_bytes_v1(changed)
        before, after = ast.parse(self.original), ast.parse(self.candidate)
        old_methods = {n.name: ast.dump(n, include_attributes=False) for n in ast.walk(before)
                       if isinstance(n, ast.FunctionDef) and n.name not in METHODS}
        new_methods = {n.name: ast.dump(n, include_attributes=False) for n in ast.walk(after)
                       if isinstance(n, ast.FunctionDef) and n.name not in METHODS}
        self.assertEqual(old_methods, new_methods)

    def test_owner_capture_is_typed_isolated_and_same_owner(self):
        start, end = frame(), frame(2592, 2, 2)
        saved = deepcopy((start, end))
        proof = owner_proof_v1(start, end)
        self.assertIsNotNone(proof)
        self.assertEqual((start, end), saved)
        start["played_character"]["character_id"] = 88
        self.assertEqual(proof["starting"]["actor_id"], 7)
        cases = [("episode_run_id", "foreign"), ("local_player_id", True),
                 ("native_revision", 1), ("paused", False), ("snapshot_id", "native:9")]
        for key, value in cases:
            with self.subTest(key=key):
                self.assertIsNone(owner_proof_v1(frame(), {**frame(2592, 2, 2), key: value}))
        end = frame(2592, 2, 2)
        end["diagnostics"]["connection_generation"] = 3
        self.assertIsNone(owner_proof_v1(frame(), end))
        end = frame(2592, 2, 2)
        end["diagnostics"]["hello"]["ck3_build_match"] = False
        self.assertIsNone(owner_proof_v1(frame(), end))

    def test_bounded_1_6_8_45_days_are_storage_eligible_without_mutation(self):
        for days in (1, 6, 8, 45):
            with self.subTest(days=days):
                result = advance(days)
                saved = deepcopy(result)
                self.assertTrue(eligible_bounded_multiday_delta_v1(
                    "life-advance", result, expected_owner=(12345, 7, "native-7-c19-test")))
                self.assertEqual(saved, result)
        for days in (0, 46):
            self.assertFalse(eligible_bounded_multiday_delta_v1(
                "life-advance", advance(days), expected_owner=(12345, 7, "native-7-c19-test")))

    def test_early_unknown_mismatched_and_untyped_results_are_rejected(self):
        clock = "campaign_deadline_native_clock_v1"
        cases = [(("elapsed_days",), True), (("requested_horizon_days",), 7),
            (("progress_status",), "unknown"), (("paused",), False),
            (("ordinary_events",), [{"event": "resolved"}]), (("active_event",), {}),
            (("event_resolution",), {"status": "resolved"}),
            ((clock, "early_boundary_cancel"), {"status": "canceled"}),
            ((clock, "stopped", "overshoot_days"), 1),
            ((clock, "stopped", "completed_daily_ticks"), 7),
            ((clock, "stopped", "trigger_reasons"), ["date_deadline", "native_pause"]),
            ((clock, "stopped", "trigger_flags"), True),
            ((clock, "stopped", "pause_observed"), False),
            ((clock, "stopped", "generation"), 5),
            ((clock, "armed", "speed"), 3),
            ((clock, "stopped", "target_date_raw"), 9999),
            ((OWNER_KEY, "ending", "connection_generation"), 99),
            ((OWNER_KEY, "starting", "date_raw"), 1),
            ((OWNER_KEY, "ending", "actor_id"), True),
            (("campaign_deadline_v1", "target_date_raw"), 9999)]
        for path, value in cases:
            with self.subTest(path=path):
                result = advance()
                change(result, path, value)
                self.assertFalse(eligible_bounded_multiday_delta_v1(
                    "life-advance", result, expected_owner=(12345, 7, "native-7-c19-test")))
        result = advance()
        result.pop(OWNER_KEY)
        self.assertFalse(eligible_bounded_multiday_delta_v1(
            "life-advance", result, expected_owner=(12345, 7, "native-7-c19-test")))
        self.assertFalse(eligible_bounded_multiday_delta_v1(
            "life-advance", advance(), expected_owner=(999, 7, "native-7-c19-test")))

    def test_exact_emitted_tail_uses_only_existing_frames_and_is_default_off(self):
        tree = ast.parse(self.candidate)
        method = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                      and n.name == "_execute_life_advance")
        tail = next(n for n in method.body if isinstance(n, ast.If)
                    and isinstance(n.test, ast.Compare) and isinstance(n.test.left, ast.Name)
                    and n.test.left.id == "campaign_clock_receipt")
        args = ast.arguments(posonlyargs=[], args=[ast.arg(arg=x) for x in
            ("self", "starting", "current", "result", "campaign_clock_receipt")],
            kwonlyargs=[], kw_defaults=[], defaults=[])
        f = ast.FunctionDef(name="emit", args=args, body=[tail, ast.Return(value=ast.Name(id="result", ctx=ast.Load()))], decorator_list=[])
        namespace = {"__package__": "xar_autoplayer.bridge"}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[f], type_ignores=[])), "<exact-timeline-result-tail>", "exec"), namespace)
        receipt = advance()["campaign_deadline_native_clock_v1"]
        original = {"step": "life-advance", "campaign_deadline_native_clock_v1": receipt}
        for enabled in (False, True):
            result = namespace["emit"](SimpleNamespace(allow_driver_state_wal_v1=enabled),
                                      frame(), frame(2592, 2, 2), {"step": "life-advance"}, receipt)
            if enabled:
                self.assertEqual(result[OWNER_KEY], owner_proof_v1(frame(), frame(2592, 2, 2)))
            else:
                self.assertEqual(result, original)

    def contexts(self, memory, **options):
        obj = make_driver(self.candidate, memory, **options)
        return obj, patch.dict(sys.modules, {self.wal.__name__: self.wal})

    def test_real_record_append_prefix_and_cold_replay_equal_full_state(self):
        memory = MemoryFS()
        obj, context = self.contexts(memory)
        with context:
            obj._persist_driver_state(persistence_reason="synthetic_initial")
            obj._record_command("life-advance", ok=True, result=advance(8))
            sealed = memory.base.read_bytes()
            memory.writes.clear()
            obj._record_command("query-small-observation", ok=True, result={"status": "unknown"})
            obj._record_command("life-advance", ok=True, result=advance(6, 2592))
            obj._record_command("life-advance", ok=True, result=advance(45, 2736))
            self.assertEqual(memory.base.read_bytes(), sealed)
            self.assertEqual(memory.writes, [self.wal.FILENAME, self.wal.FILENAME])
            journal = memory.base.with_name(self.wal.FILENAME).read_bytes()
            restored, status = self.wal.replay(sealed, journal)
            self.assertEqual(status, "replayed")
            self.assertEqual(restored["command_history"], obj._command_history)
            self.assertEqual(restored, json.loads(obj._encode_driver_state_locked()))
            corrupt = json.loads(journal)
            corrupt["entries"][-1]["history_rows"][0]["index"] = 99
            with self.assertRaises(self.wal.JournalInvalid):
                self.wal.replay(sealed, json.dumps(corrupt).encode())
            with self.assertRaises(self.wal.JournalInvalid):
                self.wal.replay(sealed, None)

    def test_default_off_and_scalar_prefix_changes_use_complete_barrier(self):
        for scenario in ("off", "owner", "prefix"):
            with self.subTest(scenario=scenario):
                memory = MemoryFS()
                obj, context = self.contexts(memory, enabled=scenario != "off")
                with context:
                    obj._persist_driver_state()
                    obj._record_command("life-advance", ok=True, result=advance())
                    if scenario == "owner":
                        obj._campaign_goal = {"new_metadata": True}
                    if scenario == "prefix":
                        obj._command_history = list(obj._command_history)
                    obj._record_command("life-advance", ok=True, result=advance(6, 2592))
                    self.assertEqual(json.loads(memory.base.read_bytes())["format_version"], 2)
                    self.assertFalse(memory.exists(memory.base.with_name(self.wal.FILENAME)))
                    self.assertEqual(json.loads(memory.base.read_bytes())["command_history"], obj._command_history)

    def test_noneligible_save_unknown_once_and_sticky_failure_remain_barriers(self):
        for command, ok, result in (("save-checkpoint", True, {}),
                                     ("submit-once-action", False, None),
                                     ("life-advance", True, {"status": "unknown"})):
            with self.subTest(command=command):
                memory = MemoryFS()
                memory.files["once.claim.json"] = (b"UNKNOWN-never-replay", 0)
                obj, context = self.contexts(memory)
                with context:
                    obj._persist_driver_state()
                    obj._record_command("life-advance", ok=True, result=advance())
                    memory.fail_full = True
                    obj._record_command(command, ok=ok, result=result)
                    self.assertTrue(obj._driver_state_wal_barrier_required)
                    self.assertIsNotNone(obj._driver_state_error)
                    memory.fail_full = False
                    obj._record_command("life-advance", ok=True, result=advance(6, 2592))
                    self.assertEqual(json.loads(memory.base.read_bytes())["format_version"], 2)
                    self.assertFalse(memory.exists(memory.base.with_name(self.wal.FILENAME)))
                    self.assertEqual(memory.files["once.claim.json"][0], b"UNKNOWN-never-replay")
                    self.assertEqual(json.loads(memory.base.read_bytes())["command_history"], obj._command_history)

    def test_existing_delta_capacity_falls_back_to_full_without_history_loss(self):
        memory = MemoryFS()
        obj, context = self.contexts(memory)
        with context, patch.object(self.wal, "MAX_DELTA_BYTES", 500):
            obj._persist_driver_state()
            obj._record_command("life-advance", ok=True, result=advance(45))
            self.assertEqual(json.loads(memory.base.read_bytes())["format_version"], 2)
            self.assertFalse(memory.exists(memory.base.with_name(self.wal.FILENAME)))
            self.assertEqual(json.loads(memory.base.read_bytes())["command_history"], obj._command_history)

    def test_multiday_publication_failure_keeps_dirty_sticky_and_never_replays(self):
        memory = MemoryFS()
        obj, context = self.contexts(memory)
        with context:
            obj._persist_driver_state()
            obj._record_command("life-advance", ok=True, result=advance())
            committed = memory.base.with_name(self.wal.FILENAME).read_bytes()
            memory.fail_journal = True
            obj._record_command("life-advance", ok=True, result=advance(6, 2592))
            self.assertTrue(obj._driver_state_dirty)
            self.assertTrue(obj._driver_state_wal_barrier_required)
            self.assertIsNotNone(obj._driver_state_error)
            self.assertEqual(len(obj._command_history), 2)
            self.assertEqual(memory.base.with_name(self.wal.FILENAME).read_bytes(), committed)
            memory.fail_journal = False
            obj._persist_driver_state(persistence_reason="synthetic_recovery_barrier")
            self.assertEqual(json.loads(memory.base.read_bytes())["command_history"], obj._command_history)
            self.assertEqual(json.loads(memory.base.read_bytes())["format_version"], 2)
            self.assertIsNone(obj._driver_state_error)


if __name__ == "__main__":
    unittest.main()
