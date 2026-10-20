"""Portable A17 contracts; software fixtures are not runtime admission evidence.

The SDK addition and Queue seam come from the actual producers. The small
projection fixture tests the insertion seam; full frozen Queue qualification
belongs to the separate preparation receipt. No external SDK or machine asset
is read, and no game/endpoint is constructed.
"""
from __future__ import annotations

import ast
from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime
from enum import IntEnum
import hashlib
import inspect
import json
from pathlib import Path
import re
import sys
from types import FunctionType, ModuleType
from typing import Protocol, TypeGuard, cast, get_type_hints
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SDK = HERE.parents[1] / "ck3_autonomous_player/src"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(SDK))
import prepare_source29_a17_cold_union_v1 as producer
import prepare_war_termination_optional_unavailable_v1 as war_producer
from owner_response_contract_v1 import (
    decode_canonical_owner_response_v1, require_json_object_v1,
)
from owner_response_json_once_v1 import prepare_success_response_row_v1
from xar_autoplayer.bridge import war_contract

Doc = dict[str, object]
STEP = "query-war-termination-options-88"


class Number(IntEnum):
    ONE = 1


def is_record(value: object) -> TypeGuard[Doc]:
    return isinstance(value, dict) and all(type(k) is str for k in value)


def record(value: object) -> Doc:
    if not is_record(value):
        raise AssertionError("fixture requires text-keyed object")
    return value


class Classify(Protocol):
    def __call__(self, body_value: object, *, initial_frame: object,
                 current_frame: object, game_pid: object) -> Mapping[str, object] | None: ...


class Metrics(Protocol):
    def __call__(self, observation_value: object, before_value: object,
                 after_value: object) -> None: ...


class Unavailable(Protocol):
    def __call__(self, *, step: str, native_error: str, native_request_id: object,
                 request: object, response: object, starting: object,
                 current: object) -> Mapping[str, object] | None: ...


def function(scope: Doc, name: str, parameters: tuple[str, ...]) -> FunctionType:
    value = scope[name]
    if not isinstance(value, FunctionType) or tuple(inspect.signature(value).parameters) != parameters:
        raise AssertionError("actual production callable signature differs: " + name)
    return value


def source_frame() -> Doc:
    return {
        "snapshot_id": "native:90", "revision": 90, "native_revision": 90,
        "date_raw": 1000, "episode_run_id": "portable-episode", "paused": True,
        "map_ready": True, "played_character": {"character_id": 707, "alive": True},
        "diagnostics": {"bridge_pid": 123, "connection_generation": 1},
        "active_wars": [{"war_id": 88, "player_side": "attacker",
            "player_is_primary_war_leader": True, "primary_opponent_character_id": 808,
            "player_relative_war_score": 17, "targeted_title_ids": [2254]}],
    }


def metrics() -> Doc:
    return {"actor_character_id": 707, "date_raw": 1000,
            "episode_run_id": "portable-episode"}


class QueueRuntime:
    def __init__(self) -> None:
        # This is the actual DTO addition used to produce the next SDK. It is
        # executed in an isolated module so current SDK imports stay unchanged.
        self.contract = ModuleType("_a17_portable_war_contract")
        vars(self.contract).update(vars(war_contract))
        self.contract.__name__ = "_a17_portable_war_contract"
        self.scope: Doc = dict(vars(self.contract))
        exec(compile(war_producer.WAR_CONTRACT_ADDITION_V1,
                     "<actual SDK war addition>", "exec"), self.scope)
        vars(self.contract).update(self.scope)
        self.unavailable = cast(Unavailable, function(self.scope,
            "war_termination_optional_unavailable_v1",
            ("step", "native_error", "native_request_id", "request", "response", "starting", "current")))
        self.queue: Doc = {"__name__": "_a17_portable_queue"}
        exec(compile(producer.WAR_OPTIONAL_QUEUE_V1, "<actual Queue addition>", "exec"),
             self.queue)
        self.classify = cast(Classify, function(self.queue, "classify_source29_war_optional_v1",
            ("body_value", "initial_frame", "current_frame", "game_pid")))
        self.verify = cast(Metrics, function(self.queue, "verify_source29_war_optional_metrics_v1",
            ("observation_value", "before_value", "after_value")))

    def body(self) -> Doc:
        request: Doc = {"type": "execute_step", "protocol_version": 1,
            "request_id": "step-5-61e52e058ce3", "step": STEP, "expected_revision": 90}
        response: Doc = {"type": "command_result", "protocol_version": 1,
            "request_id": request["request_id"], "ok": False,
            "error": "war-termination completion snapshot read failed"}
        first = source_frame()
        result = self.unavailable(step=STEP, native_error=str(response["error"]),
            native_request_id=request["request_id"], request=request, response=response,
            starting=first, current=deepcopy(first))
        if result is None:
            raise AssertionError("actual producer rejected valid fixture")
        return {"status": "executed", "selected_step": STEP,
                "plan": {"selected_step": STEP}, "result": dict(result)}

    def classify_body(self, body: object, *, initial: object = None,
                      current: object = None, pid: object = 123) -> Mapping[str, object] | None:
        # Local import in the actual Queue uses the genuine projected SDK parser.
        with patch.dict(sys.modules, {"xar_autoplayer.bridge.war_contract": self.contract}):
            return self.classify(body, initial_frame=metrics() if initial is None else initial,
                current_frame=metrics() if current is None else current, game_pid=pid)


class A17Contracts(unittest.TestCase):
    runtime: QueueRuntime

    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime = QueueRuntime()

    def plan(self) -> Doc:
        reference: Doc = {"path": str(Path(producer.__file__).resolve()), "bytes": 1,
                          "sha256": "a" * 64}
        # Shape-only parser fixtures never assert that a ref was admitted.
        row: Doc = {key: deepcopy(reference) for key in producer.PlanV1.__annotations__}
        row.update(schema="xar.Source29-A17-complete-cold-input/v1",
            machine_id=producer.MACHINE, execution_owner="Root",
            root_direct_execution_release=True, observed_at_utc="2026-01-01T00:00:00+00:00",
            attempt_nonce="a" * 32, task_nonce="b" * 32,
            screen_admission_path=str(HERE / "portable-a17-screen.json"))
        return row

    def parse(self, value: object) -> Doc:
        with patch.object(producer, "SCREEN", HERE / "portable-a17-screen.json"):
            return dict(producer.parse_plan(value))

    def test_plan_json_roundtrip_and_public_annotations(self) -> None:
        row = self.plan()
        before = deepcopy(row)
        parsed = self.parse(json.loads(producer.enc(row)))
        self.assertEqual(parsed, before)
        self.assertEqual(row, before)
        self.assertEqual(set(parsed), set(producer.PlanV1.__annotations__))
        for method in (producer.parse_plan, producer.history_view_v1):
            hints = get_type_hints(method)
            self.assertIn("return", hints)
            self.assertTrue(all(p in hints for p in inspect.signature(method).parameters))

    def test_plan_missing_unknown_and_legacy_schema(self) -> None:
        for key in self.plan():
            row = self.plan()
            del row[key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                self.parse(row)
        for extra in ("task_sequence", "SOURCE28", "current_next_sequence"):
            row = self.plan()
            row[extra] = 10541
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                self.parse(row)
        row = self.plan()
        row["schema"] = "xar.Source28-A15-complete-cold-input/v1"
        with self.assertRaises(ValueError):
            self.parse(row)

    def test_plan_exact_authority_nonce_time_and_screen(self) -> None:
        cases: list[tuple[str, object]] = [
            ("root_direct_execution_release", 1), ("root_direct_execution_release", 1.0),
            ("root_direct_execution_release", None), ("machine_id", "other-machine"),
            ("execution_owner", "worker"), ("attempt_nonce", "b" * 32),
            ("task_nonce", True), ("observed_at_utc", None),
            ("observed_at_utc", "not-time"), ("screen_admission_path", "relative.json"),
        ]
        for key, value in cases:
            row = self.plan()
            row[key] = value
            with self.subTest(key=key, value=value), self.assertRaises((ValueError, TypeError)):
                self.parse(row)

    def test_ref_integer_domain_fields_and_json_arrays(self) -> None:
        value: object
        for value in (True, 1.0, Number.ONE, None, 0, -1, 2 ** 53):
            row = self.plan()
            record(row["sdk_base_ref"])["bytes"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.parse(row)
        for value in (None, [], "source"):
            row = self.plan()
            row["canonical_anchor_ref"] = value
            with self.subTest(shape=value), self.assertRaises(ValueError):
                self.parse(row)
        row = self.plan()
        record(row["sdk_base_ref"])["old_sha"] = "a" * 64
        with self.assertRaises(ValueError):
            self.parse(row)

    def test_historical_view_is_explicit_nonmutating_and_not_current(self) -> None:
        current: Doc = {"next_sequence": 10552, "pending": None, "rows": []}
        original = deepcopy(current)
        history = producer.history_view_v1(json.loads(producer.enc(current)))
        self.assertEqual(history, {**current, "next_sequence": 10541})
        self.assertEqual(current, original)
        self.assertIsNot(history, current)
        for invalid in (10541, 10552.0, True, Number.ONE, None, 10553):
            with self.subTest(value=invalid), self.assertRaises(ValueError):
                producer.history_view_v1({**current, "next_sequence": invalid})
        with self.assertRaises(ValueError):
            producer.history_view_v1({"task_sequence": 10552})

    def test_real_response_producer_decoder_and_queue_zero_credit(self) -> None:
        body = require_json_object_v1(self.runtime.body())
        canonical = require_json_object_v1({"meta": None, "content": [],
            "structured_content": body, "is_error": False, "result_type": "complete"})
        _, encoded = prepare_success_response_row_v1(started_at_utc="before",
            ended_at_utc="after", elapsed_seconds=0.0, request={}, result=canonical)
        decoded = decode_canonical_owner_response_v1(json.loads(encoded))
        observation = self.runtime.classify_body(decoded)
        self.assertIsNotNone(observation)
        result = dict(observation or {})
        self.assertEqual(result["category"], "war_termination_optional_unavailable")
        self.assertTrue(result["typed_nonmaterial_observation"])
        for key in ("game_action_credit", "game_day_credit", "business_success_inferred",
                    "primitive_accepted", "submitted_pending", "replay_allowed",
                    "fresh_native_completion_proved"):
            self.assertIs(result[key], False)
        self.runtime.verify(json.loads(json.dumps(result)), metrics(), metrics())

    def test_queue_rejects_plan_game_and_identity_drift(self) -> None:
        value: object
        for value in (True, 123.0, Number.ONE, None, 0, 2 ** 32, 999):
            with self.subTest(pid=value), self.assertRaises(ValueError):
                self.runtime.classify_body(self.runtime.body(), pid=value)
        for key, value in (("actor_character_id", 808), ("date_raw", 1001),
                           ("episode_run_id", "other"), ("actor_character_id", 707.0),
                           ("date_raw", True), ("episode_run_id", None)):
            changed = metrics()
            changed[key] = value
            with self.subTest(field=key, value=value), self.assertRaises(ValueError):
                self.runtime.classify_body(self.runtime.body(), current=changed)
        for target, key, value in (("outer", "status", "failed"),
                                  ("outer", "selected_step", "query-war-termination-options-89"),
                                  ("plan", "selected_step", None)):
            body = self.runtime.body()
            row = body if target == "outer" else record(body[target])
            row[key] = value
            with self.subTest(target=target, key=key), self.assertRaises(ValueError):
                self.runtime.classify_body(body)

    def test_queue_parser_rejects_unknown_and_mutated_unavailability(self) -> None:
        self.assertIsNone(self.runtime.classify_body({"result": {"schema": "future"}}))
        for key, value in (("accepted", True), ("war_id", 88.0),
                           ("war_termination_options", []), ("read_only", 1),
                           ("replay_allowed", None), ("schema", "future")):
            body = self.runtime.body()
            record(body["result"])[key] = value
            with self.subTest(key=key):
                self.assertIsNone(self.runtime.classify_body(body))
        body = self.runtime.body()
        del record(body["result"])["accepted"]
        self.assertIsNone(self.runtime.classify_body(body))

    def test_paired_metrics_forbid_day_credit_or_identity_changes(self) -> None:
        observation = self.runtime.classify_body(self.runtime.body())
        self.assertIsNotNone(observation)
        for key, value in (("date_raw", 1001), ("actor_character_id", 808),
                           ("episode_run_id", "other"), ("date_raw", 1000.0),
                           ("actor_character_id", True), ("date_raw", None)):
            for side in ("before", "after"):
                before, after = metrics(), metrics()
                (before if side == "before" else after)[key] = value
                with self.subTest(side=side, key=key), self.assertRaises(ValueError):
                    self.runtime.verify(observation, before, after)

    def test_queue_patch_uses_actual_seam_and_rejects_second_install(self) -> None:
        # This bounded syntax fixture wraps the producer's actual accepted seam.
        # It does not stand in for a full frozen Queue check_after qualification.
        seam = producer.QUEUE_CHECK_AFTER_BEFORE_V1
        fixture = ("def classify_ordinary_auto_outcome_v1(): pass\n"
            "def check_after(self, body, ordinary_state, classifier, pending, before, after):\n"
            "    if True:\n        if True:\n            observation = None\n" +
            seam + "                    body)\n"
            "    if True:\n        if True:\n            if True:\n"
            '                observation = pending["observation"]\n')
        patched = producer.patch_queue_war_optional_v1(fixture.encode())
        tree = ast.parse(patched)
        calls = [n.func.id for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
        self.assertIn("classify_source29_war_optional_v1", calls)
        self.assertIn("verify_source29_war_optional_metrics_v1", calls)
        self.assertIn("classifier", calls)
        with self.assertRaises(ValueError):
            producer.patch_queue_war_optional_v1(patched)
        with self.assertRaises(ValueError):
            producer.patch_queue_war_optional_v1(fixture.replace("= classifier(", "= unknown_classifier(").encode())

    def metadata(self, *, performance: bool = False) -> tuple[Doc, Doc, Doc, Doc, Doc]:
        names = ["xar_autoplayer/bridge/native_driver.py",
                 "xar_autoplayer/bridge/war_contract.py", "xar_autoplayer/strategy.py"]
        if performance:
            names.append("xar_autoplayer/bridge/service.py")
        rows: list[Doc] = [{"relative": name, "bytes": 1, "sha256": "a" * 64}
                          for name in names + [f"portable/{i}.py" for i in range(1464 - len(names))]]
        old: Doc = {"files": deepcopy(rows)}
        for row in rows[:len(names)]:
            row["sha256"] = "b" * 64
        history_anchor: Doc = {"path": str(HERE / "source28-anchor.json"),
                              "bytes": 1, "sha256": "c" * 64}
        history_base: Doc = {"path": str(HERE / "source28-base.json"),
                            "bytes": 1, "sha256": "d" * 64}
        encoded = json.dumps(rows, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False).encode()
        anchor: Doc = {"schema": "xar.source29.canonical-git-anchor/v1",
            "machine_id": "portable", "status": "CANONICAL_REF_CREATED_NOT_DEPLOYED",
            "parent": "442beeae4676bad9a9d53cb7070a01f06e965761",
            "actual_Source28_anchor": history_anchor, "actual_Source28_BASE": history_base,
            "canonical_variant": "WAR_AND_METADATA_SNAPSHOT" if performance else "WAR_ONLY",
            "performance_candidate": {key: deepcopy(history_anchor) for key in
                ("manifest_ref", "producer_ref", "qualification_ref")} if performance else None,
            "output_pins": deepcopy(rows[:len(names)]), "canonical_patch_rows": [None] * len(names),
            "complete_rows_JSON": {"bytes": len(encoded), "sha256": hashlib.sha256(encoded).hexdigest()},
            "source_file_count": 1464, "source_bytes": 1464, "commit": "e" * 40}
        base: Doc = {"schema": "root.ck3.final-sdk-freeze/v1", "machine_id": "portable",
            "status": "FINAL_SOURCE_FROZEN", "runtime_admitted": False, "files": rows,
            "business_source_commit": "e" * 40, "source29_canonical_anchor": history_anchor}
        return base, anchor, old, history_anchor, history_base

    def validate_metadata(self, parts: tuple[Doc, Doc, Doc, Doc, Doc]) -> Doc:
        return producer.validate_source29_metadata_v1(*parts, machine_id="portable")

    def test_new_sdk_metadata_keeps_historical_basis_separate(self) -> None:
        parts = self.metadata()
        original = deepcopy(parts)
        loaded: object = json.loads(json.dumps(parts))
        if not isinstance(loaded, list) or len(loaded) != 5:
            raise AssertionError("five metadata inputs required")
        restored = (record(loaded[0]), record(loaded[1]), record(loaded[2]),
                    record(loaded[3]), record(loaded[4]))
        self.assertEqual(self.validate_metadata(restored), parts[1])
        self.assertEqual(parts, original)
        for target, key, value in ((0, "runtime_admitted", True),
                (0, "business_source_commit", "f" * 40),
                (1, "actual_Source28_BASE", parts[3]),
                (1, "canonical_variant", "future"), (1, "source_file_count", 1464.0)):
            changed = deepcopy(parts)
            changed[target][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.validate_metadata(changed)
        changed = deepcopy(parts)
        changed[0]["canonical_preload_policy"] = {}
        with self.assertRaises(ValueError):
            self.validate_metadata(changed)


    def test_metadata_performance_variant_requires_exact_fourth_leaf(self) -> None:
        parts = self.metadata(performance=True)
        self.assertEqual(self.validate_metadata(parts), parts[1])
        candidate = record(parts[1]["performance_candidate"])
        record(candidate["manifest_ref"])["bytes"] = True
        with self.assertRaises(ValueError):
            self.validate_metadata(parts)


    def test_actual_cold_owner_projection_reads_only_a15_freeze(self) -> None:
        originals: list[tuple[str, ast.FunctionDef]] = []
        for filename in ("prepare_c23_a08_union_v1.py", "prepare_c23_a05_union_v1.py"):
            raw = (HERE / filename).read_text(encoding="utf-8")
            nodes = [n for n in ast.parse(raw).body
                     if isinstance(n, ast.FunctionDef) and n.name == "cold_owner"]
            self.assertEqual(len(nodes), 1)
            originals.append((raw, nodes[0]))
        outer = ast.get_source_segment(*originals[0])
        inner = ast.get_source_segment(*originals[1])
        if outer is None or inner is None:
            raise AssertionError("actual cold owner source required")
        outer = outer.replace("A08", "A17").replace("a08", "a17")
        patched = producer.patch_cold_owner_freeze_lookup_v1(outer)
        owner = ast.parse(patched).body[0]
        if not isinstance(owner, ast.FunctionDef):
            raise AssertionError("actual outer function required")
        assignments = [n for n in owner.body if isinstance(n, ast.Assign)
                       and any(isinstance(t, ast.Name) and t.id == "source" for t in n.targets)]
        scope: Doc = {"ast": ast, "text": originals[1][0], "node": originals[1][1]}
        exec(compile(ast.Module(body=list[ast.stmt](assignments[:2]), type_ignores=[]),
                     "<actual two cold-owner projections>", "exec"), scope)
        expected = inner.replace("A05", "A17").replace("a05", "a17")
        old = "ROOT-FINAL-SDK-FREEZE-P37C23-A17.json"
        new = "ROOT-FINAL-SDK-FREEZE-P37C23-A15.json"
        self.assertEqual(expected.count(old), 1)
        self.assertEqual(scope["source"], expected.replace(old, new))
        for invalid in (patched, outer.replace("seam=", "foreign_seam=")):
            with self.subTest(source=invalid[:40]), self.assertRaises(ValueError):
                producer.patch_cold_owner_freeze_lookup_v1(invalid)


if __name__ == "__main__":
    unittest.main()
