"""Pure completion and Queue transform contracts."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import sys
from typing import Literal, Protocol, runtime_checkable
import unittest

from mcp.client.session import _CallToolResultAdapter
from mcp.types import CallToolResult

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from tools.g2_saved_campaign.patch_complete_tool_result_v1 import transform
from xar_autoplayer.bridge.mcp_tool_result_contract_v1 import (
    require_complete_tool_result,
)


def snapshot(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


class McpToolResultContractTests(unittest.TestCase):
    def accepted(self, value: dict[str, object]) -> Literal["complete"]:
        before = snapshot(value)
        result = require_complete_tool_result(value)
        self.assertEqual(snapshot(value), before)
        self.assertEqual(result, "complete")
        return result

    def rejected(self, value: dict[str, object]) -> None:
        before = snapshot(value)
        with self.assertRaisesRegex(ValueError, "non-complete MCP result"):
            require_complete_tool_result(value)
        self.assertEqual(snapshot(value), before)

    def test_complete_aliases(self) -> None:
        rows: tuple[dict[str, object], ...] = (
            {}, {"result_type": "complete"}, {"resultType": "complete"},
            {"result_type": "complete", "resultType": "complete"},
        )
        for row in rows:
            with self.subTest(row=row):
                self.accepted(row)

    def test_bad_tags(self) -> None:
        bad: tuple[object, ...] = (
            None, True, 1, 1.0, "input_required", "future_result", [], {},
        )
        for key in ("result_type", "resultType"):
            for value in bad:
                with self.subTest(key=key, value=value):
                    self.rejected({key: value})

    def test_conflicting_aliases(self) -> None:
        for bad in (None, "input_required", "future_result"):
            self.rejected({"result_type": "complete", "resultType": bad})
            self.rejected({"result_type": bad, "resultType": "complete"})

    def test_sdk_complete_nullable(self) -> None:
        body: dict[str, object] = {"status": "synthetic", "optional": None}
        parsed = _CallToolResultAdapter.validate_python({
            "content": [], "structuredContent": body,
            "isError": False, "resultType": "complete",
        }, by_name=False)
        if not isinstance(parsed, CallToolResult):
            self.fail("wrong SDK arm")
        for aliases in (False, True):
            wire: dict[str, object] = parsed.model_dump(mode="json", by_alias=aliases)
            self.accepted(wire)
            self.assertEqual(wire.get("structured_content", wire.get("structuredContent")), body)

    def test_sdk_noncomplete(self) -> None:
        for tag in ("input_required", "future_result"):
            parsed = _CallToolResultAdapter.validate_python({
                "content": [], "structuredContent": {"status": "synthetic"},
                "isError": False, "resultType": tag, "requestState": "synthetic-token",
            }, by_name=False)
            if not isinstance(parsed, CallToolResult):
                self.fail("wrong SDK arm")
            for aliases in (False, True):
                self.rejected(parsed.model_dump(mode="json", by_alias=aliases))

    def test_error_nullable(self) -> None:
        result = CallToolResult(content=[], is_error=True, structured_content={
            "diagnostics": {"synthetic_failure": {"wait_progress": None}},
        })
        for aliases in (False, True):
            wire: dict[str, object] = result.model_dump(mode="json", by_alias=aliases)
            self.accepted(wire)
            self.assertIs(wire.get("is_error", wire.get("isError")), True)


OLD_DECODER = b'''def decoded(row):
    if row.get("client_error"):
        raise RuntimeError("client outcome unknown; original request must not be resent")
    result = row.get("result")
    if not isinstance(result, dict) or result.get("is_error", result.get("isError", False)):
        raise RuntimeError("SDK error; original result retained; no automatic retry")
    value = result.get("structured_content", result.get("structuredContent"))
    if isinstance(value, dict):
        return value
    for block in result.get("content", []):
        if isinstance(block, dict) and block.get("type") == "text":
            try:
                value = json.loads(block["text"])
            except (TypeError, ValueError):
                continue
            if isinstance(value, dict):
                return value
    raise ValueError("SDK returned no actual decoded object")
'''


@runtime_checkable
class Decoder(Protocol):
    def __call__(self, row: dict[str, object]) -> object: ...


def compiled_decoder() -> Decoder:
    tree = ast.parse(transform(OLD_DECODER))
    namespace: dict[str, object] = {"json": json}
    exec(compile(ast.Module(body=[tree.body[0]], type_ignores=[]), "<RAM>", "exec"), namespace)
    value = namespace["decoded"]
    if not isinstance(value, Decoder):
        raise AssertionError("not callable")
    return value


class CompleteDecoderTransformTests(unittest.TestCase):
    def test_pinned_context(self) -> None:
        self.assertEqual(hashlib.sha256(OLD_DECODER).hexdigest(),
                         "9256c2059269d892ee14d4cdc0e7835d2ea0f7f6162525410d6a6532e7fca1ba")
        prefix = b"import json\nKEPT=17\n"
        suffix = b"\nAFTER=False\nif __name__=='__main__':\n raise AssertionError('no main')\n"
        changed = transform(prefix + OLD_DECODER + suffix)
        self.assertEqual(changed[:len(prefix)], prefix)
        self.assertEqual(changed[-len(suffix):], suffix)
        body = changed[len(prefix):-len(suffix)]
        self.assertEqual(len(body), 996)
        self.assertEqual(hashlib.sha256(body).hexdigest(),
                         "745bff4ba6d5e2b561144bf70a79bae5ddd34332402ed078bfdddca916e5098d")

    def test_patch_rejections(self) -> None:
        rows = (
            b"pass\n", OLD_DECODER + OLD_DECODER,
            OLD_DECODER.replace(b"SDK error;", b"foreign error;", 1),
            OLD_DECODER.replace(b"    value = result.get(", b"    value = object(", 1),
            transform(OLD_DECODER), b"@staticmethod\n" + OLD_DECODER,
        )
        for index, row in enumerate(rows):
            with self.subTest(index=index), self.assertRaises(ValueError):
                transform(row)

    def test_sdk_decoder(self) -> None:
        decode = compiled_decoder()
        body: dict[str, object] = {"optional": None}
        for tag in ("legacy", "complete", "input_required", "future_result"):
            parsed = _CallToolResultAdapter.validate_python({
                "content": [], "structuredContent": body, "isError": False,
                "resultType": "complete" if tag == "legacy" else tag,
                "requestState": "synthetic-token",
            }, by_name=False)
            if not isinstance(parsed, CallToolResult):
                self.fail("wrong SDK arm")
            for aliases in (False, True):
                wire: dict[str, object] = parsed.model_dump(mode="json", by_alias=aliases)
                if tag == "legacy":
                    wire.pop("result_type", None)
                    wire.pop("resultType", None)
                row: dict[str, object] = {"result": wire}
                before = snapshot(row)
                if tag in ("legacy", "complete"):
                    self.assertEqual(snapshot(decode(row)), snapshot(body))
                else:
                    with self.assertRaises(ValueError):
                        decode(row)
                self.assertEqual(snapshot(row), before)
        error = CallToolResult(content=[], is_error=True, result_type="future_result",
                               structured_content=body)
        with self.assertRaisesRegex(RuntimeError, "SDK error"):
            decode({"result": error.model_dump(mode="json")})
