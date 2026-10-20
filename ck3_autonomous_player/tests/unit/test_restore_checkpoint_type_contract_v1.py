"""Exercise the real restore functions without starting a driver or creating files."""
from __future__ import annotations

import ast
import copy
from enum import IntEnum
import inspect
import json
from pathlib import Path
import sys
from types import FunctionType
import unittest

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "src"))

from xar_autoplayer.bridge.restore_checkpoint_type_contract_v1 import (
    checkpoint_identity_v1, process_replacement_identity_v1, same_nullable_integer_v1,
)
from xar_autoplayer.bridge.succession_transition_contract import (
    freeze_succession_expectation_v1, legacy_rogue_one_life_binding_v1,
    normalize_succession_expectation_v1, normalize_succession_lifecycle_binding_v1,
    reconcile_succession_transition_v1,
)


class Numeric(IntEnum):
    ONE = 1
    TWO = 2
    TWELVE = 12


def obj(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise AssertionError("expected JSON object")
    return {key: item for key, item in value.items()}


def text(value: object) -> str:
    return json.dumps(value, sort_keys=True)


def round_trip(value: object) -> object:
    result: object = json.loads(text(value))
    return result


def fixture() -> dict[str, object]:
    checkpoint: dict[str, object] = {
        "name": "xar_checkpoint.ck3", "sha256": "a" * 64, "size": 1,
        "date_raw": 1, "history_index": 1,
        "episode_character_id": 1, "episode_run_id": "run",
    }
    return {
        "format_version": 2, "pipe_name": "pipe", "bridge_pid": 12,
        "episode_character_id": 1, "episode_run_id": "run",
        "last_checkpoint": checkpoint, "rollback_war_failures": [],
        "command_history": [{"index": 1, "command": "save-checkpoint", "ok": True,
                             "result": {"checkpoint": copy.deepcopy(checkpoint)}}],
        "managed_restore_transaction": {
            "status": "awaiting_checkpoint_rebind", "request_id": "restore-test",
            "source_bridge_pid": 11, "replacement_bridge_pid": 12,
            "checkpoint_sha256": "a" * 64, "checkpoint_size": 1,
            "checkpoint_date_raw": 1, "history_index": 1,
            "episode_character_id": 1, "episode_run_id": "run",
        },
    }


def saved(payload: dict[str, object]) -> dict[str, object]:
    history = payload["command_history"]
    if not isinstance(history, list):
        raise AssertionError("expected history")
    return obj(obj(obj(history[0])["result"])["checkpoint"])


class Harness:
    def __init__(self, history: object) -> None:
        self.save_dir = Path(".")
        self._command_history = history


def functions() -> dict[str, object]:
    source = (PROJECT / "src/xar_autoplayer/bridge/native_driver.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = {
        "load_native_driver_state_for_resume_payload", "_normalize_rollback_war_failure",
        "_bounded_rollback_war_failures", "_normalize_managed_restore_transaction",
        "_checkpoint_history_index", "_proven_restore_lineage_row",
        "_same_restore_process_replacement", "_positive_native_id",
        "_resume_command_history_projection", "_compact_war_progress_history_in_place",
    }
    methods = {"_matching_checkpoint_history_index", "_cold_candidate_ready"}
    constants = {
        "_CHECKPOINT_ANCHOR_STEPS", "_NATIVE_DRIVER_STATE_VERSION",
        "_MANAGED_RESTORE_TRANSACTION_STATUS", "_PHASE2_SOURCE_CHECKPOINT_STAGE_STEP",
        "_RESTORE_CHECKPOINT_STEP", "_COLD_RESTORE_SOURCE",
    }
    nodes: list[ast.stmt] = [ast.parse("from __future__ import annotations").body[0]]
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id in constants for target in node.targets
        ):
            nodes.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name in names:
            nodes.append(node)
        elif isinstance(node, ast.ClassDef) and node.name == "NativeHeadlessGameplayDriver":
            nodes.extend(item for item in node.body
                         if isinstance(item, ast.FunctionDef) and item.name in methods)
    found = [node.name for node in nodes if isinstance(node, ast.FunctionDef)]
    if sorted(found) != sorted(names | methods):
        raise AssertionError("restore function selection changed")
    namespace: dict[str, object] = {
        "copy": copy, "checkpoint_identity_v1": checkpoint_identity_v1,
        "process_replacement_identity_v1": process_replacement_identity_v1,
        "same_nullable_integer_v1": same_nullable_integer_v1,
        "normalize_succession_lifecycle_binding_v1": normalize_succession_lifecycle_binding_v1,
        "legacy_rogue_one_life_binding_v1": legacy_rogue_one_life_binding_v1,
        "normalize_succession_expectation_v1": normalize_succession_expectation_v1,
    }
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(PROJECT / "src/native_driver.py"), "exec"),
         namespace)
    return namespace


def invoke(namespace: dict[str, object], name: str, *args: object, **kwargs: object) -> object:
    # The bounded AST selection above is the sole dynamic test boundary.
    function = namespace[name]
    if not isinstance(function, FunctionType):
        raise AssertionError("expected selected Python function")
    inspect.signature(function).bind(*args, **kwargs)
    result: object = function(*args, **kwargs)
    return result


def component(value: object) -> dict[str, object]:
    return {"status": "available", "value": value, "unavailable_reason": None}


def bundle(actor: int, heir: int, sid: str, revision: int) -> dict[str, object]:
    return {
        "schema": "xar.ck3.turn-bundle/v1", "status": "available",
        "binding": {"snapshot_id": sid, "revision": revision,
                    "native_revision": revision, "date_raw": revision},
        "ruler_state": component({"character_id": actor, "alive": True}),
        "succession_state": component({
            "primary_title_heir_character_id": component(heir),
            "partition": component({"title_heirs": [{
                "title": {"title_id": 10}, "first_heir_character_id": heir, "primary": True,
            }], "risk_state": "single_successor"}),
        }),
    }


class RestoreCheckpointTypeTests(unittest.TestCase):
    namespace: dict[str, object]

    @classmethod
    def setUpClass(cls) -> None:
        cls.namespace = functions()

    def call(self, name: str, *args: object, **kwargs: object) -> object:
        return invoke(self.namespace, name, *args, **kwargs)

    def consume(self, payload: object, *, full: bool = False) -> dict[str, object]:
        return obj(self.call("load_native_driver_state_for_resume_payload", payload,
                             "pipe", include_command_history=full))

    def test_valid_legacy_versions_null_and_json_round_trip(self) -> None:
        for version in (1, 2):
            for bound in (False, True):
                for full in (False, True):
                    payload = fixture()
                    payload["format_version"] = version
                    if not bound:
                        payload.update(episode_character_id=None, episode_run_id=None,
                                       last_checkpoint=None, managed_restore_transaction=None,
                                       command_history=[])
                    payload = obj(round_trip(payload))
                    before = text(payload)
                    result = self.consume(payload, full=full)
                    self.assertIs(type(result["format_version"]), int)
                    self.assertEqual(result["format_version"], version)
                    self.assertIs(result["succession_lifecycle_migration_required"], True)
                    self.assertEqual("command_history" in result, full)
                    self.assertEqual(text(payload), before)
        payload = fixture()
        payload["succession_lifecycle"] = None
        with self.assertRaises(ValueError):
            self.consume(payload)

    def test_eight_nested_wrong_json_types_and_enums(self) -> None:
        for scope, key in (("tx", "episode_character_id"), ("cp", "episode_character_id"),
                           ("saved", "size"), ("saved", "date_raw")):
            for bad in (True, 1.0, Numeric.ONE):
                with self.subTest(scope=scope, key=key, bad=repr(bad)):
                    payload = fixture()
                    target = (obj(payload["managed_restore_transaction"]) if scope == "tx"
                              else obj(payload["last_checkpoint"]) if scope == "cp" else saved(payload))
                    target[key] = bad
                    if scope == "tx":
                        payload["managed_restore_transaction"] = target
                    elif scope == "cp":
                        payload["last_checkpoint"] = target
                    else:
                        history = payload["command_history"]
                        if not isinstance(history, list):
                            raise AssertionError("expected history")
                        obj_row = obj(history[0])
                        obj_result = obj(obj_row["result"])
                        obj_result["checkpoint"] = target
                        obj_row["result"] = obj_result
                        history[0] = obj_row
                    candidates = [payload] if isinstance(bad, IntEnum) else [payload, obj(round_trip(payload))]
                    for candidate in candidates:
                        before = text(candidate)
                        result = self.consume(candidate)
                        if scope == "tx":
                            self.assertIsNone(result["managed_restore_transaction"])
                        else:
                            self.assertIs(self.call("_cold_candidate_ready",
                                          Harness(candidate["command_history"]), candidate), False)
                        self.assertEqual(text(candidate), before)

    def test_resume_rejects_integer_enums_and_equal_nonintegers(self) -> None:
        for field, bads in (("bridge_pid", (12.0, Numeric.TWELVE)),
                            ("episode_character_id", (True, 1.0, Numeric.ONE))):
            for bad in bads:
                payload = fixture()
                payload[field] = bad
                with self.assertRaises(ValueError):
                    self.consume(payload)
        for bad in (True, 1.0, 2.0, Numeric.ONE, Numeric.TWO):
            payload = fixture()
            payload["format_version"] = bad
            self.assertIsNone(self.call("load_native_driver_state_for_resume_payload", payload, "pipe"))

    def test_legacy_anchor_and_strict_saved_identity(self) -> None:
        payload = fixture()
        checkpoint = obj(payload["last_checkpoint"])
        for field in ("history_index", "episode_character_id", "episode_run_id"):
            checkpoint.pop(field)
        harness = Harness(payload["command_history"])
        self.assertEqual(self.call("_matching_checkpoint_history_index", harness, checkpoint), 1)
        for field in ("size", "date_raw"):
            for bad in (True, 1.0, Numeric.ONE):
                wrong = dict(checkpoint)
                wrong[field] = bad
                self.assertIsNone(checkpoint_identity_v1(wrong))
                self.assertIsNone(self.call("_matching_checkpoint_history_index", harness, wrong))
        self.assertTrue(same_nullable_integer_v1(None, None))
        for bad in (False, 0, 0.0, Numeric.ONE):
            self.assertFalse(same_nullable_integer_v1(bad, None))

    def test_lineage_and_process_identity(self) -> None:
        checkpoint = obj(fixture()["last_checkpoint"])
        result: dict[str, object] = {
            "step": "restore-checkpoint", "accepted": True, "status": "restored",
            "backend_id": "native-headless", "source": "native-session-cold-start",
            "restored_date_raw": 1, "map_ready": True, "checkpoint": checkpoint,
            "lifecycle": {"previous_pid": 11, "pid": 12},
        }
        row: dict[str, object] = {"command": "restore-checkpoint", "ok": True, "result": result}
        self.assertIs(self.call("_proven_restore_lineage_row", row, checkpoint), True)
        self.assertIs(self.call("_same_restore_process_replacement", result, round_trip(result)), True)
        bad: object
        for bad in (True, 1.0, Numeric.ONE):
            wrong = dict(result)
            wrong["restored_date_raw"] = bad
            self.assertIs(self.call("_proven_restore_lineage_row",
                                   {**row, "result": wrong}, checkpoint), False)
        for bad in (12.0, Numeric.TWELVE, None):
            wrong = {**result, "lifecycle": {"previous_pid": 11, "pid": bad}}
            self.assertIsNone(process_replacement_identity_v1(wrong["lifecycle"]))
            self.assertIs(self.call("_same_restore_process_replacement", result, wrong), False)

    def test_succession_risk_reaches_value_error_through_resume(self) -> None:
        expectation = freeze_succession_expectation_v1(
            bundle(1, 2, "pre", 0), episode_run_id="run", episode_character_id=1)
        bad: object
        for bad in ([], {}):
            payload = fixture()
            payload["succession_expectation"] = {**expectation, "risk_state": bad}
            before = text(payload)
            with self.assertRaises(ValueError):
                self.consume(round_trip(payload))
            self.assertEqual(text(payload), before)

    def test_reconciliation_rejects_raw_equal_wrong_types(self) -> None:
        expectation = freeze_succession_expectation_v1(
            bundle(1, 2, "pre", 0), episode_run_id="run", episode_character_id=1)
        post = bundle(2, 3, "post", 1)
        snapshot: dict[str, object] = {
            "snapshot_id": "post", "revision": 1, "native_revision": 1, "date_raw": 1,
            "paused": True, "played_character": {"character_id": 2, "alive": True},
            "episode_character_id": 1, "one_life_terminal": True,
            "one_life_terminal_reason": "played_character_changed",
        }
        canonical = round_trip([expectation, snapshot, post])
        if not isinstance(canonical, list):
            raise AssertionError("expected JSON triple")
        before = text(canonical)
        self.assertEqual(reconcile_succession_transition_v1(*canonical)["verdict"], "matched")
        self.assertEqual(text(canonical), before)
        for key in ("episode_character_id", "revision", "native_revision", "date_raw"):
            for bad in (True, 1.0, Numeric.ONE):
                wrong = {**snapshot, key: bad}
                with self.assertRaises(ValueError):
                    reconcile_succession_transition_v1(expectation, wrong, post)
        for bad in (2.0, Numeric.TWO):
            wrong = {**post, "ruler_state": component({"character_id": bad, "alive": True})}
            with self.assertRaises(ValueError):
                reconcile_succession_transition_v1(expectation, snapshot, wrong)
