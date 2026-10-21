from __future__ import annotations
import ast
import copy
import hashlib
import json
from pathlib import Path
from threading import RLock
import sys
from types import SimpleNamespace
from typing import Literal
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests/unit"))
from xar_autoplayer.bridge import player_lifestyle_private_transport_v1 as T
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver as N
import test_lifestyle_focus_private_observation as F
import test_lifestyle_martial_private_observation as M
import test_lifestyle_diplomacy_private_observation as D
Kind = Literal["focus", "martial", "diplomacy"]
OLD_AST = "fdd2528529cd3b541a4627b0ace01d3434ddc010a837f25b12157446a08f6434"
FULL: object = N.take_snapshot
FINITE: object = N.take_snapshot_without_native_command_history
HISTORY: object = N._history_snapshot
def obj(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TypeError("dict required")
    out: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise TypeError("key type")
        out[key] = item
    return out
def invoke(function: object, *args: object, **kwargs: object) -> object:
    if not callable(function):
        raise TypeError("method required")
    result: object = function(*args, **kwargs)
    return result
def legacy_query() -> object:
    source = Path(T.__file__).read_text(encoding="utf-8")
    node = next(n for n in ast.walk(ast.parse(source))
                if isinstance(n, ast.FunctionDef)
                and n.name == "query_player_lifestyle_focus_private_v1")
    node = copy.deepcopy(node)
    class Reads(ast.NodeTransformer):
        def visit_Call(self, value: ast.Call) -> ast.AST:
            if isinstance(value.func, ast.Name) and value.func.id == "_lifestyle_metadata_snapshot_v1":
                return ast.Call(func=ast.Attribute(value=ast.Name(id="driver", ctx=ast.Load()),
                    attr="take_snapshot", ctx=ast.Load()), args=[], keywords=[])
            return self.generic_visit(value)
    updated = Reads().visit(node)
    if not isinstance(updated, ast.FunctionDef):
        raise TypeError("query AST changed")
    node = updated
    body: list[ast.stmt] = []
    for statement in node.body:
        if (isinstance(statement, ast.Assign) and isinstance(statement.value, ast.Call)
                and isinstance(statement.value.func, ast.Name)
                and statement.value.func.id == "_lifestyle_focus_request_v1"):
            call = statement.value
            if len(call.args) != 3:
                raise ValueError("request recipe differs")
            send = ast.parse("driver.endpoint.send({})").body[0]
            if not isinstance(send, ast.Expr) or not isinstance(send.value, ast.Call):
                raise TypeError("send AST")
            send.value.args = [call.args[1]]
            wait = ast.parse("response = driver.state.wait_for_command_result(request_id, driver.command_timeout_seconds)").body[0]
            body.extend([send, wait])
        else:
            body.append(statement)
    node.body = body
    if hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest() != OLD_AST:
        raise ValueError("original AST differs")
    namespace: dict[str, object] = dict(vars(T))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
                 "<original-query>", "exec"), namespace)
    return namespace["query_player_lifestyle_focus_private_v1"]
class Marker:
    def __init__(self, owner: Provider) -> None:
        self.owner = owner
    def __deepcopy__(self, memo: dict[int, object]) -> dict[str, bool]:
        self.owner.history_clones += 1
        return {"retained": True}
class Provider:
    allow_private_lifestyle_formal_trial = True
    command_timeout_seconds: float = 1.0
    def __init__(self, kind: Kind = "focus", mode: str = "valid") -> None:
        self.kind, self.mode = kind, mode
        self.endpoint = self
        self.state = self
        self.events: list[str] = []
        self.history_clones = 0
        self.snapshot_count = 0
        self.last_request: dict[str, object] | None = None
        self._driver_state_lock = RLock()
        self._history_lock = RLock()
        self._rollback_war_failures: list[dict[str, object]] = [{"r": 1}]
        self._command_history: list[dict[str, object]] = [{"payload": Marker(self)}]
    def take_internal_semantic_snapshot(self) -> dict[str, object]:
        self.events.append("snapshot")
        self.snapshot_count += 1
        if self.mode == "snapshot_error" and self.snapshot_count == 2:
            raise RuntimeError("snapshot-original-error")
        raw = obj(F._frame() if self.kind == "focus" else M.frame() if self.kind == "martial" else D.frame())
        frame = copy.deepcopy(raw)
        frame.update(map_ready=True, revision=4,
                     played_character={"character_id": raw["played_character_id"]})
        if self.mode == "date_drift" and self.snapshot_count == 2:
            date = frame["date_raw"]
            if type(date) is not int:
                raise TypeError("fixture date")
            frame["date_raw"] = date + 24
        if self.mode == "revision_drift" and self.snapshot_count == 2:
            frame["revision"] = 5
        if self.mode == "pre_unpaused":
            frame["paused"] = False
        return frame
    def take_snapshot(self, *, include_native_command_history: bool = True) -> dict[str, object]:
        return obj(invoke(FULL, self, include_native_command_history=include_native_command_history))
    def take_snapshot_without_native_command_history(self) -> dict[str, object]:
        return obj(invoke(FINITE, self))
    def _history_snapshot(self) -> list[dict[str, object]]:
        result = invoke(HISTORY, self)
        if not isinstance(result, list):
            raise TypeError("history type")
        return [obj(row) for row in result]
    def send(self, request: dict[str, object]) -> None:
        self.events.append("send")
        self.last_request = copy.deepcopy(request)
        if self.mode == "send_error":
            raise RuntimeError("send-original-error")
    def wait_for_command_result(self, request_id: str, timeout: float) -> dict[str, object] | None:
        self.events.append("wait")
        if self.mode == "wait_error":
            raise RuntimeError("wait-original-error")
        if self.mode == "missing_response":
            return None
        result = obj(F._response() if self.kind == "focus" else M.response() if self.kind == "martial" else D.response())
        result["request_id"] = request_id
        return result
def query(function: object, provider: object) -> dict[str, object]:
    kind = getattr(provider, "kind", None)
    if not isinstance(kind, str):
        raise TypeError("kind")
    step = {"focus": T.FOCUS_QUERY_STEP, "martial": T.MARTIAL_QUERY_STEP,
            "diplomacy": T.DIPLOMACY_QUERY_STEP}[kind]
    with patch.object(T.uuid, "uuid4", return_value=SimpleNamespace(hex="a" * 32)):
        return obj(invoke(function, provider, expected_revision=4, query_step=step))
class MetadataTests(unittest.TestCase):
    original: object
    @classmethod
    def setUpClass(cls) -> None:
        original = legacy_query()
        if not callable(original):
            raise TypeError("legacy query")
        cls.original = staticmethod(original)
    def equivalent(self, kind: Kind = "focus", mode: str = "valid") -> tuple[dict[str, object], Provider, Provider]:
        old, new = Provider(kind, mode), Provider(kind, mode)
        before = query(self.original, old)
        after = query(T.query_player_lifestyle_focus_private_v1, new)
        self.assertEqual(before, after)
        self.assertEqual(json.loads(json.dumps(before)), json.loads(json.dumps(after)))
        self.assertEqual(old.last_request, new.last_request)
        self.assertEqual(old.events, new.events)
        self.assertEqual(new.history_clones, 0)
        self.assertEqual(old.history_clones, old.snapshot_count)
        return after, old, new
    def test_real_native_snapshot_methods(self) -> None:
        result, old, new = self.equivalent()
        self.assertEqual(result["status"], "observed")
        self.assertEqual((old.history_clones, new.history_clones), (2, 0))
        self.assertEqual(new.events, ["snapshot", "send", "wait", "snapshot"])
        a, b = old.take_snapshot(), new.take_snapshot_without_native_command_history()
        for key in ("native_rollback_war_failure", "native_rollback_war_failures"):
            self.assertEqual(a[key], b[key])
    def test_martial_actual_consumer_keeps_native_illegal(self) -> None:
        result, _, _ = self.equivalent("martial")
        self.assertIs(result["native_legal"], False)
    def test_diplomacy_actual_consumer(self) -> None:
        result, _, _ = self.equivalent("diplomacy")
        self.assertEqual(result["status"], "observed")
    def test_independent_date_drift_still_rejected(self) -> None:
        result, _, _ = self.equivalent(mode="date_drift")
        self.assertEqual(result["status"], "red")
    def test_public_revision_drift_still_rejected(self) -> None:
        result, _, _ = self.equivalent(mode="revision_drift")
        self.assertEqual(result["status"], "red")
    def test_unpaused_precondition_sends_nothing(self) -> None:
        result, _, new = self.equivalent(mode="pre_unpaused")
        self.assertEqual(result["status"], "paused_frame_unavailable")
        self.assertNotIn("send", new.events)
    def test_missing_result_is_not_replayed(self) -> None:
        _, _, new = self.equivalent(mode="missing_response")
        self.assertEqual(new.events.count("send"), 1)
        self.assertEqual(new.events.count("wait"), 1)
    def test_provider_exceptions_propagate_without_retry(self) -> None:
        for mode in ("send_error", "wait_error", "snapshot_error"):
            old, new = Provider(mode=mode), Provider(mode=mode)
            for function, provider in ((self.original, old), (T.query_player_lifestyle_focus_private_v1, new)):
                with self.subTest(mode=mode), self.assertRaisesRegex(RuntimeError, "original-error"):
                    query(function, provider)
            self.assertEqual(old.events, new.events)
            self.assertEqual(old.last_request, new.last_request)
            self.assertEqual(new.events.count("send"), 1)
    def test_legacy_snapshot_fallback(self) -> None:
        provider = Provider()
        legacy = SimpleNamespace(kind="focus", allow_private_lifestyle_formal_trial=True,
            command_timeout_seconds=1.0, endpoint=provider, state=provider,
            take_snapshot=provider.take_snapshot)
        result = query(T.query_player_lifestyle_focus_private_v1, legacy)
        self.assertEqual(result["status"], "observed")
        self.assertEqual(provider.history_clones, 2)
    def test_lean_provider_contract_is_enforced(self) -> None:
        for reader in (None, False, lambda: None, lambda: {1: None}):
            provider = Provider()
            setattr(provider, "take_snapshot_without_native_command_history", reader)
            with self.assertRaises(TypeError):
                query(T.query_player_lifestyle_focus_private_v1, provider)
            self.assertEqual(provider.events, [])
    def test_bad_timeout_rejected_before_send(self) -> None:
        for value in (True, None, -1.0, float("nan"), float("inf")):
            provider = Provider()
            setattr(provider, "command_timeout_seconds", value)
            with self.subTest(value=value), self.assertRaises((TypeError, ValueError)):
                query(T.query_player_lifestyle_focus_private_v1, provider)
            self.assertNotIn("send", provider.events)
    def test_trial_off_does_not_read_or_send(self) -> None:
        provider = Provider()
        provider.allow_private_lifestyle_formal_trial = False
        result = query(T.query_player_lifestyle_focus_private_v1, provider)
        self.assertEqual(result["status"], "trial_off")
        self.assertEqual(provider.events, [])
if __name__ == "__main__":
    unittest.main()
