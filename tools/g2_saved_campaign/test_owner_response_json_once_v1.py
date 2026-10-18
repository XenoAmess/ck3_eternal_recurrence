"""Seven portable source-fixture tests and one Windows atomic-writer test.

No local SDK, campaign path, Driver, large payload or Native binary is required.
The original Path.rename create-only behavior is Windows-specific; its dedicated
test is skipped on other platforms rather than changing the production writer.
"""
from __future__ import annotations

import ast
import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock
import uuid

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from owner_response_json_once_v1 import prepare_success_response_row_v1
from owner_response_source_transform_v1 import transform_owner_source_v1

SOURCE = HERE / "fixtures/owner_response_encoding_source.py"
RAW = SOURCE.read_bytes()
SHA = hashlib.sha256(RAW).hexdigest()
NEW = transform_owner_source_v1(RAW, expected_source_sha256=SHA)
MEASUREMENTS = []


def pin(path):
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def source_nodes(raw):
    tree = ast.parse(raw.decode("utf-8-sig"))
    names = {"atomic", "atomic_payload_v1", "decoded", "call"}
    return [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and n.name in names and (n.name != "call" or any(
                isinstance(item, ast.Name) and item.id in {
                    "dumped", "_owner_response_success_row_once_v1"} for item in ast.walk(n)))]


def make_globals(raw, root, events):
    for directory in (root, root / "out", root / "queue", root / "display-responses"):
        directory.mkdir(exist_ok=True)
    ticks = iter([100 + i * .25 for i in range(100)])
    result = {"json": json, "os": os, "uuid": uuid,
        "time": types.SimpleNamespace(monotonic=lambda: next(ticks), sleep=lambda _: None),
        "REPLY_RESERVE": 1 << 20, "N": root, "Q": root / "queue", "OUTBOX": root / "out",
        "AUTO": "ck3_auto_turn", "INITIAL_CAMERA": "initial-camera",
        "now": lambda: datetime(2020, 1, 1, tzinfo=timezone.utc),
        "preserve_first_exception": lambda *a, **kw: events.append("preserve_exception"),
        "display_projection": lambda row, body: {"status": body.get("status")},
        "_owner_response_success_row_once_v1": prepare_success_response_row_v1,
        "print": lambda *a, **kw: None}
    module = ast.Module(body=source_nodes(raw), type_ignores=[])
    exec(compile(module, str(SOURCE), "exec"), result)
    return result


def fixture_result():
    return {"structured_content": {"status": "executed", "selected_step": "synthetic-hold",
        "result": {"accepted": True, "status": "completed", "postcondition_verified": True,
            "date_raw": 1000, "query_sequence": 2**63 + 8,
            "companies": [{"id": 0}, {"id": 0xffffffff}],
            "terms": [-(2**63), 2**63 - 1, 33_000_001], "readonly": False,
            "text": "完整原生字段，不能删减\n\\\"🪶", "optional": None}},
        "content": [{"type": "text", "text": "已完成"}], "is_error": False}


async def run_call(raw, root, *, rpc_error=False, reject_after=False, existing=False):
    events = []
    globals_ = make_globals(raw, root, events)
    complete = fixture_result()
    stats = {"calls": 0, "full_result_encoding_traversals": 0}
    real_dumps = json.dumps

    def observed_dumps(value, *args, **kwargs):
        if value is complete or (isinstance(value, dict) and value.get("result") is complete):
            stats["full_result_encoding_traversals"] += 1
        return real_dumps(value, *args, **kwargs)

    class Session:
        async def call_tool(self, tool, arguments, *, read_timeout_seconds):
            stats["calls"] += 1
            events.append("call_tool")
            if rpc_error:
                raise RuntimeError("synthetic original outcome unknown")
            return types.SimpleNamespace(model_dump=lambda **kw: complete)

    class Owner:
        last_auto_observation = {"days": 1, "NativeACK": "synthetic-only"}
        def check_before(self, *args):
            events.append("check_before")
        def call_budget(self, tool):
            return 300
        def consume_sequence(self, request):
            return request["sequence"]
        def check_after(self, *args):
            events.append("check_after")
            if reject_after:
                raise ValueError("synthetic classifier rejects")

    overlay = types.ModuleType("owner_response_fixture_observer")
    overlay.relay_compact = lambda *args: events.append("relay")
    overlay.error_projection = lambda row: {"error": True}
    response = root / "out/0007-1-result.json"
    if existing:
        response.write_bytes(b"protected original")
    owner = Owner()
    request = {"sequence": 7, "tool": "ck3_auto_turn", "arguments": {}, "source": "synthetic"}
    error = None
    with (mock.patch.dict(sys.modules, {overlay.__name__: overlay}),
          mock.patch.object(json, "dumps", side_effect=observed_dumps)):
        try:
            await globals_["call"](owner, Session(), request, Path("synthetic-request.json"))
        except Exception as caught:
            error = (type(caught).__name__, str(caught))
    return {"events": events, "stats": stats, "error": error,
        "response": response.read_bytes() if response.exists() else None,
        "ordinary_credit": (root / "queue/0007-ordinary-result-credit.json").exists(),
        "original_result": complete}


class OwnerResponseTests(unittest.TestCase):
    def temp(self):
        holder = tempfile.TemporaryDirectory()
        resolved = Path(holder.name).resolve()
        assert resolved.is_relative_to(Path(tempfile.gettempdir()).resolve())
        self.addCleanup(holder.cleanup)
        return resolved

    def test_exact_JSON_bytes_and_all_fields_and_numbers(self):
        for result in (fixture_result(), {"zero": 0, "false": False, "negative_zero": -0.0},
                       {"nested": [{"emoji": "🪶", "literal": '雪\\\"\n'}], "empty": {}}):
            before = deepcopy(result)
            row, payload = prepare_success_response_row_v1(started_at_utc="a", ended_at_utc="b",
                elapsed_seconds=.125, request={"sequence": 1, "arguments": {}}, result=result)
            self.assertEqual(payload, json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode())
            self.assertEqual(row["mcp_result_projection_json_utf8_bytes"],
                len(json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode()))
            self.assertEqual(json.loads(payload), row)
            self.assertEqual(result, before)
            self.assertIs(row["result"], result)

    def test_real_production_call_and_atomic_success_identical(self):
        root = self.temp()
        old = asyncio.run(run_call(RAW, root / "old"))
        new = asyncio.run(run_call(NEW, root / "new"))
        self.assertEqual(old["response"], new["response"])
        self.assertEqual(old["events"], new["events"])
        self.assertEqual(old["error"], new["error"])
        self.assertIsNone(new["error"])
        self.assertEqual(new["events"].count("check_before"), 1)
        self.assertEqual(new["events"].count("check_after"), 1)
        self.assertEqual(old["stats"]["calls"], new["stats"]["calls"])
        self.assertEqual(new["stats"]["calls"], 1)
        self.assertTrue(new["ordinary_credit"])
        self.assertEqual(old["stats"]["full_result_encoding_traversals"], 2)
        self.assertEqual(new["stats"]["full_result_encoding_traversals"], 1)
        MEASUREMENTS.append({"synthetic_authoritative_response_bytes": len(new["response"]),
            "byte_identical": True, "full_result_encoding_traversals_before": 2,
            "full_result_encoding_traversals_after": 1,
            "RPC_count_before_and_after": 1, "before_and_after_checks_preserved": True,
            "wall_speedup_measured": False})

    def test_existing_response_remains_protected_before_RPC(self):
        root = self.temp()
        for raw, name in ((RAW, "old"), (NEW, "new")):
            result = asyncio.run(run_call(raw, root / name, existing=True))
            self.assertEqual(result["response"], b"protected original")
            self.assertEqual(result["stats"]["calls"], 0)
            self.assertEqual(result["error"][0], "FileExistsError")

    def test_unknown_outcome_retained_once_without_post_credit(self):
        root = self.temp()
        old = asyncio.run(run_call(RAW, root / "old", rpc_error=True))
        new = asyncio.run(run_call(NEW, root / "new", rpc_error=True))
        self.assertEqual(old["response"], new["response"])
        self.assertEqual(old["events"], new["events"])
        self.assertEqual(old["error"], new["error"])
        self.assertEqual(new["stats"]["calls"], 1)
        self.assertNotIn("check_after", new["events"])
        self.assertFalse(new["ordinary_credit"])
        self.assertIs(json.loads(new["response"])["replay_allowed"], False)

    def test_post_classifier_refusal_preserves_original_receipt_no_credit(self):
        root = self.temp()
        old = asyncio.run(run_call(RAW, root / "old", reject_after=True))
        new = asyncio.run(run_call(NEW, root / "new", reject_after=True))
        self.assertEqual(old["response"], new["response"])
        self.assertEqual(old["events"], new["events"])
        self.assertEqual(old["error"], new["error"])
        self.assertEqual(new["stats"]["calls"], 1)
        self.assertFalse(new["ordinary_credit"])

    @unittest.skipUnless(os.name == "nt", "original atomic Path.rename create-only semantics require Windows")
    def test_actual_atomic_limits_create_only_replace_and_partial_cleanup(self):
        root = self.temp()
        for raw, name in ((RAW, "old"), (NEW, "new")):
            g = make_globals(raw, root / name, [])
            target = root / name / "receipt.json"
            value = {"text": "雪", "full": [-(2**63), 2**63 - 1]}
            encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()
            with self.assertRaises(ValueError):
                g["atomic"](target, value, limit=len(encoded) - 1)
            self.assertFalse(target.exists())
            g["atomic"](target, value, limit=len(encoded))
            self.assertEqual(target.read_bytes(), encoded)
            with self.assertRaises(FileExistsError):
                g["atomic"](target, {"replacement": True}, limit=1024)
            self.assertEqual(target.read_bytes(), encoded)
            g["atomic"](target, {"replacement": True}, replace=True, limit=1024)
            self.assertEqual(target.read_bytes(), b'{"replacement":true}')
            self.assertEqual(list(target.parent.glob("*.pending")), [])

    def test_other_fixture_functions_and_postcheck_tail_stay_identical(self):
        before, after = ast.parse(RAW.decode("utf-8-sig")), ast.parse(NEW.decode("utf-8-sig"))
        def functions(tree):
            result = {}
            for n in ast.walk(tree):
                if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if n.name in {"atomic", "atomic_payload_v1"}:
                    continue
                if n.name == "call" and any(isinstance(item, ast.Name) and item.id == "dumped"
                                             for item in ast.walk(n)):
                    continue
                result.setdefault(n.name, []).append(ast.dump(n))
            return result
        self.assertEqual(functions(before), functions(after))
        old_call = next(n for n in source_nodes(RAW) if n.name == "call")
        new_call = next(n for n in source_nodes(NEW) if n.name == "call")
        old_tail = next(i for i, n in enumerate(old_call.body)
            if isinstance(n, ast.Assign) and any(isinstance(t, ast.Attribute)
                and t.attr == "current_attempt" for t in n.targets) and i > 1)
        new_tail = next(i for i, n in enumerate(new_call.body)
            if isinstance(n, ast.Assign) and any(isinstance(t, ast.Attribute)
                and t.attr == "current_attempt" for t in n.targets) and i > 1)
        self.assertEqual([ast.dump(n) for n in old_call.body[old_tail:]],
                         [ast.dump(n) for n in new_call.body[new_tail:]])

    def test_source_hash_and_shape_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "SHA mismatch"):
            transform_owner_source_v1(RAW, expected_source_sha256="0" * 64)
        changed = RAW.replace(b'len(json.dumps(dumped, ensure_ascii=False,',
                              b'len(json.dumps(dumped, ensure_ascii=True,', 1)
        with self.assertRaisesRegex(ValueError, "owner call required"):
            transform_owner_source_v1(changed, expected_source_sha256=hashlib.sha256(changed).hexdigest())
        with self.assertRaisesRegex(ValueError, "identifier required"):
            transform_owner_source_v1(RAW, expected_source_sha256=SHA, helper_module="os; bad")


if __name__ == "__main__":
    unittest.main()
