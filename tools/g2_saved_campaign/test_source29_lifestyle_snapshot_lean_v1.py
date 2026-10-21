from __future__ import annotations
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from typing import Literal
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from tools.g2_saved_campaign.write_source27_canonical_ref_v1 import parse_ref
from tools.g2_saved_campaign.prepare_source29_lifestyle_snapshot_lean_v1 import (
    AFTER_BYTES, AFTER_SHA, BEFORE_BYTES, BEFORE_SHA, FUNCTION_PINS,
    patch_service_functions_v1,
)
_BEFORE: bytes | None = None
_AFTER: bytes | None = None
Kind = Literal["perks", "martial"]
Case = Literal["valid", "unavailable", "badsource", "drift",
               "query_error", "snapshot_error", "off"]
FRAME: dict[str, object] = {
    "paused": True, "snapshot_id": "native:1", "revision": 2, "native_revision": 1,
    "date_raw": 53274624, "episode_run_id": "native-40526-unit",
    "played_character": {"character_id": 40526}}
FOCUS: dict[str, object] = {"key": "wealth", "lifestyle_key": "stewardship"}
def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("expected an object")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError("non-string object key")
        result[key] = item
    return result
def _functions(source: bytes) -> dict[str, object]:
    tree = ast.parse(source.decode("utf-8"))
    nodes = [node for node in ast.walk(tree)
             if isinstance(node, ast.FunctionDef) and node.name in FUNCTION_PINS]
    if len(nodes) != 2 or {node.name for node in nodes} != set(FUNCTION_PINS):
        raise ValueError("source must contain the two unique lifestyle methods")
    namespace: dict[str, object] = {"PERK_TARGETS": {"x", "y"}}
    module = ast.Module(body=list(nodes), type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), "<actual-service-functions>", "exec"),
         namespace)
    return namespace

def source_pair_v1(source: bytes) -> tuple[bytes, bytes]:
    """Accept one whole installation state and prove the exact real recipe."""
    text = source.decode("utf-8")
    nodes = [node for node in ast.walk(ast.parse(text))
             if isinstance(node, ast.FunctionDef) and node.name in FUNCTION_PINS]
    if len(nodes) != 2 or {node.name for node in nodes} != set(FUNCTION_PINS):
        raise ValueError("two unique lifestyle source methods required")
    installed: list[bool] = []
    replacements: list[tuple[str, str]] = []
    for node in nodes:
        calls = [value for value in ast.walk(node)
                 if isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute)
                 and isinstance(value.func.value, ast.Name)
                 and value.func.value.id == "self" and value.func.attr == "snapshot"]
        if len(calls) != 1 or calls[0].args:
            raise ValueError("one exact semantic snapshot call required")
        call = calls[0]
        omitted = (len(call.keywords) == 1
                   and call.keywords[0].arg == "include_native_command_history"
                   and isinstance(call.keywords[0].value, ast.Constant)
                   and call.keywords[0].value.value is False)
        if call.keywords and not omitted:
            raise ValueError("unsupported semantic snapshot arguments")
        installed.append(omitted)
        segment = ast.get_source_segment(text, node)
        call_text = ast.get_source_segment(text, call)
        if segment is None or call_text is None or segment.count(call_text) != 1:
            raise ValueError("one reversible method segment required")
        replacements.append((segment, segment.replace(call_text, "self.snapshot()", 1)))
    if installed == [False, False]:
        return source, patch_service_functions_v1(source)
    if installed != [True, True]:
        raise ValueError("partly installed lifestyle optimization")
    for old, new in replacements:
        if text.count(old) != 1:
            raise ValueError("one installed method segment required")
        text = text.replace(old, new, 1)
    before = text.encode()
    if patch_service_functions_v1(before) != source:
        raise ValueError("installed service differs from the exact forward recipe")
    return before, source

class Probe:
    def __init__(self, case: Case) -> None:
        self.case = case
        self.driver = self
        self.allow_private_lifestyle_formal_trial = case != "off"
        self.full_exports = 0
        self.finite_exports = 0
        self.calls: list[int] = []
        self._opening_martial_episode_v1: str | None = None
        self._opening_martial_observation_v1: dict[str, object] | None = None
    def _read(self, *, expected_revision: int) -> dict[str, object]:
        self.calls.append(expected_revision)
        if self.case == "query_error":
            raise RuntimeError("unit-query-failure")
        if self.case == "unavailable":
            return {"status": "native_query_unavailable",
                    "native_error": "private_lifestyle_executor_or_completion_state_red"}
        source = {key: FRAME[key] for key in
                  ("snapshot_id", "revision", "native_revision", "date_raw")}
        source["player_character_id"] = 40526
        if self.case == "badsource":
            source["date_raw"] = 53274648
        return {
            "status": "available", "episode_run_id": FRAME["episode_run_id"],
            "source_frame": source, "native_legal": False,
            "snapshot": {
                "readiness": {"same_frame_ready": True,
                              "legal_perk_candidates_ready": True, "owned_perks_ready": True},
                "legal_perk_candidates": {
                    "status": "available", "scope": "policy_target",
                    "items": [{"key": "x", "lifestyle_key": "stewardship"}]},
                "owned_perk_keys": ["y"], "current_focus": copy.deepcopy(FOCUS)}}
    def query_player_lifestyle_formal_private_v1(
        self, *, expected_revision: int,
    ) -> dict[str, object]:
        return self._read(expected_revision=expected_revision)
    def query_player_lifestyle_martial_authority_private_v1(
        self, *, expected_revision: int,
    ) -> dict[str, object]:
        return self._read(expected_revision=expected_revision)
    def snapshot(
        self, *, include_native_command_history: bool = True,
    ) -> dict[str, object]:
        if type(include_native_command_history) is not bool:
            raise ValueError("history inclusion must be bool")
        self.full_exports += int(include_native_command_history)
        self.finite_exports += int(not include_native_command_history)
        if self.case == "snapshot_error":
            raise RuntimeError("unit-snapshot-failure")
        frame = copy.deepcopy(FRAME)
        if self.case == "drift":
            frame["native_revision"] = 2
        frame["native_command_history"] = (
            [{"unused_nested_history": {"request_id": "retained", "ack": None}}]
            if include_native_command_history else [])
        if not include_native_command_history:
            frame["native_command_history_export"] = {
                "mode": "omitted", "included_count": 0, "total_count": 5278}
        return frame
def _invoke(function: object, probe: Probe, kind: Kind) -> dict[str, object] | None:
    if not callable(function):
        raise ValueError("actual source did not produce a callable")
    result: object
    if kind == "perks":
        result = function(probe, before=copy.deepcopy(FRAME), focus=copy.deepcopy(FOCUS),
                          revision=2)
    else:
        result = function(probe, before=copy.deepcopy(FRAME), revision=2)
    return None if result is None else _object(result)
class LifestyleSnapshotLeanTests(unittest.TestCase):
    old: dict[str, object]
    new: dict[str, object]
    @classmethod
    def setUpClass(cls) -> None:
        if _BEFORE is None:
            source = (REPO_ROOT / "ck3_autonomous_player/src/xar_autoplayer/bridge/service.py").read_bytes()
            before, after = source_pair_v1(source)
        else:
            before = _BEFORE
            if _AFTER is None or patch_service_functions_v1(before) != _AFTER:
                raise ValueError("exact explicit before/after source pair required")
            after = _AFTER
        cls.old, cls.new = _functions(before), _functions(after)
        tree = ast.parse(after.decode("utf-8"))
        seen = 0
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef) or node.name not in FUNCTION_PINS:
                continue
            calls = [value for value in ast.walk(node)
                     if isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute)
                     and value.func.attr == "snapshot"]
            if len(calls) != 1:
                raise AssertionError("each actual function must perform one semantic read")
            keywords = calls[0].keywords
            if (len(keywords) != 1 or keywords[0].arg != "include_native_command_history"
                    or not isinstance(keywords[0].value, ast.Constant)
                    or keywords[0].value.value is not False):
                raise AssertionError("candidate snapshot must omit history explicitly")
            seen += 1
        if seen != 2:
            raise AssertionError("candidate did not cover both functions")
    def _case(self, kind: Kind, case: Case) -> None:
        name = ("_observe_opening_lifestyle_perks_v1" if kind == "perks"
                else "_observe_opening_martial_authority_v1")
        old_probe, new_probe = Probe(case), Probe(case)
        old = _invoke(self.old[name], old_probe, kind)
        new = _invoke(self.new[name], new_probe, kind)
        self.assertEqual(old, new)
        self.assertEqual(json.loads(json.dumps(old)), json.loads(json.dumps(new)))
        self.assertEqual(old_probe.calls, new_probe.calls)
        self.assertEqual(new_probe.calls, [] if case == "off" else [2])
        self.assertEqual(new_probe.full_exports, 0)
        expected_reads = 0 if case in {"query_error", "off"} else 1
        self.assertEqual(old_probe.full_exports, expected_reads)
        self.assertEqual(new_probe.finite_exports, expected_reads)
        if new is None:
            self.assertEqual((kind, case), ("martial", "off"))
            return
        if case in {"query_error", "snapshot_error"}:
            self.assertEqual(new.get("query_status") if kind == "perks" else new.get("status"),
                             "query_error")
            self.assertEqual(new.get("error_type"), "RuntimeError")
        if case == "drift":
            self.assertEqual(new.get("query_status") if kind == "perks" else new.get("issue"),
                             "paused_frame_mismatch" if kind == "perks" else "opening_frame_changed")
        if case == "badsource":
            self.assertEqual(new.get("query_status"), "paused_frame_mismatch")
        if kind == "martial":
            self.assertEqual(old_probe._opening_martial_episode_v1,
                             new_probe._opening_martial_episode_v1)
            self.assertEqual(old_probe._opening_martial_observation_v1,
                             new_probe._opening_martial_observation_v1)
    def test_perks_valid(self) -> None: self._case("perks", "valid")
    def test_perks_unavailable(self) -> None: self._case("perks", "unavailable")
    def test_perks_wrong_source(self) -> None: self._case("perks", "badsource")
    def test_perks_frame_drift(self) -> None: self._case("perks", "drift")
    def test_perks_query_exception(self) -> None: self._case("perks", "query_error")
    def test_perks_trial_off(self) -> None: self._case("perks", "off")
    def test_martial_valid(self) -> None: self._case("martial", "valid")
    def test_martial_unavailable(self) -> None: self._case("martial", "unavailable")
    def test_martial_snapshot_exception(self) -> None: self._case("martial", "snapshot_error")
    def test_martial_frame_drift(self) -> None: self._case("martial", "drift")
    def test_martial_query_exception(self) -> None: self._case("martial", "query_error")
    def test_martial_trial_off(self) -> None: self._case("martial", "off")
class FileRefContractTests(unittest.TestCase):
    def test_shared_ref_roundtrip_and_rejections(self) -> None:
        ref: dict[str, object] = {"path": "/service.py", "bytes": 1, "sha256": "0" * 64}
        self.assertEqual(parse_ref(json.loads(json.dumps(ref))), ref)
        bad = [dict(ref, bytes=True), dict(ref, bytes=1.0), dict(ref, path=None),
               dict(ref, git_mode="100644"), {"bytes": 1, "sha256": "0" * 64}]
        for value in bad:
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                parse_ref(value)

    def test_real_service_recipe_roundtrip_rejects_mixed_or_changed_calls(self) -> None:
        source = (REPO_ROOT / "ck3_autonomous_player/src/xar_autoplayer/bridge/service.py").read_bytes()
        before, after = source_pair_v1(source)
        self.assertEqual(source_pair_v1(before), (before, after))
        self.assertEqual(source_pair_v1(after), (before, after))
        text = after.decode()
        nodes = [node for node in ast.walk(ast.parse(text))
                 if isinstance(node, ast.FunctionDef) and node.name in FUNCTION_PINS]
        segment = ast.get_source_segment(text, nodes[0])
        if segment is None:
            raise AssertionError("actual function segment required")
        call = "self.snapshot(include_native_command_history=False)"
        self.assertEqual(segment.count(call), 1)
        cases = [
            text.replace(segment, segment.replace(call, "self.snapshot()", 1), 1),
            text.replace(segment, segment.replace(call,
                "self.snapshot(include_native_command_history=True)", 1), 1),
            text + "\n" + segment + "\n",
        ]
        for value in cases:
            with self.subTest(length=len(value)), self.assertRaises(ValueError):
                source_pair_v1(value.encode())

def main() -> int:
    global _BEFORE, _AFTER
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", type=Path)
    parser.add_argument("--after", type=Path)
    args = parser.parse_args()
    if (args.before is None) != (args.after is None):
        parser.error("--before and --after must be supplied together")
    if args.before is not None and args.after is not None:
        before, after = args.before.read_bytes(), args.after.read_bytes()
        _BEFORE, _AFTER = before, after
        if (len(before) != BEFORE_BYTES or hashlib.sha256(before).hexdigest() != BEFORE_SHA
                or len(after) != AFTER_BYTES or hashlib.sha256(after).hexdigest() != AFTER_SHA):
            raise ValueError("canonical qualification requires exact Source28 before/after pins")
        if patch_service_functions_v1(before) != after:
            raise ValueError("candidate contains changes beyond the two exact snapshot seams")
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(LifestyleSnapshotLeanTests)
    result = unittest.TextTestRunner(stream=sys.stderr, verbosity=1).run(suite)
    if not result.wasSuccessful() or result.testsRun != 12:
        return 1
    print(json.dumps({
        "schema": "xar.Source28-lifestyle-snapshot-lean-qualification/v1",
        "status": "PASS", "runtime_cases_passed": result.testsRun,
        "full_history_exports_per_exercised_pair_before": 2,
        "full_history_exports_per_exercised_pair_after": 0,
        "native_query_count_unchanged": True, "frame_guards_preserved": True,
        "query_and_snapshot_exception_paths_preserved": True,
        "json_roundtrip_equal": True, "runtime_calls": 0, "new_campaign_credit": 0,
        "actual_game_performance_measured": False}, sort_keys=True, separators=(",", ":")))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
