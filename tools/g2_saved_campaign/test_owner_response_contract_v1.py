"""Pure canonical-response contracts; no backend, Game or temporary files."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from enum import IntEnum
import json
from pathlib import Path
import sys
import unittest
from typing import get_type_hints

from mcp.types import CallToolResult

sys.path.insert(0, str(Path(__file__).resolve().parent))
from owner_response_contract_v1 import (
    ClientUnknownV1, JsonObject, JsonValue, ToolFailureV1, ToolSuccessV1,
    decode_canonical_owner_response_v1, parse_canonical_tool_result_v1,
    parse_owner_response_v1, require_json_object_v1,
)
from owner_response_json_once_v1 import prepare_success_response_row_v1
from owner_response_source_transform_v1 import canonical_decoder_source_v1


def canonical(*, body: JsonValue = None, error: bool = False) -> JsonObject:
    dumped: object = CallToolResult(
        content=[], structured_content=body, is_error=error,
    ).model_dump(mode="json", by_alias=False)
    return require_json_object_v1(dumped)


def returned(result: JsonObject) -> tuple[JsonObject, bytes]:
    row, encoded = prepare_success_response_row_v1(
        started_at_utc="2026-10-20T00:00:00+00:00",
        ended_at_utc="2026-10-20T00:00:01+00:00",
        elapsed_seconds=1.0, request={"sequence": 7, "arguments": {}}, result=result,
    )
    decoded: object = json.loads(encoded)
    actual = require_json_object_v1(decoded)
    if actual != row:
        raise AssertionError("canonical row JSON roundtrip")
    return actual, encoded


class Number(IntEnum):
    ZERO = 0


class CanonicalOwnerResponseTests(unittest.TestCase):
    def test_real_sdk_dump_roundtrip_and_absent_error(self) -> None:
        original = canonical(body={"optional": None, "zero": 0, "false": False})
        row, encoded = returned(original)
        self.assertNotIn("error", row)
        self.assertNotIn("client_error", row)
        self.assertEqual(set(original), {"meta", "content", "structured_content", "is_error", "result_type"})
        self.assertEqual(encoded, json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode())
        outcome = parse_owner_response_v1(row)
        self.assertIsInstance(outcome, ToolSuccessV1)
        if not isinstance(outcome, ToolSuccessV1):
            self.fail("returned tool success")
        self.assertIs(outcome.row, row)
        self.assertEqual(outcome.result.structured_content, original["structured_content"])
        self.assertEqual(decode_canonical_owner_response_v1(row), original["structured_content"])
        with self.assertRaises(FrozenInstanceError):
            setattr(outcome.result, "is_error", True)

    def test_protocol_json_values_and_null_empty_distinction(self) -> None:
        bodies: tuple[JsonValue, ...] = (None, {}, [], [None, True, 0, 1.25, "text"],
                                         True, 0, 1.25, "body")
        meta: JsonValue
        for body in bodies:
            for meta in (None, {}):
                with self.subTest(body=body, meta=meta):
                    wire = canonical(body=body)
                    wire["meta"] = meta
                    outcome = parse_canonical_tool_result_v1(wire)
                    self.assertEqual(outcome.structured_content, body)
                    self.assertEqual(outcome.meta, meta)
                    self.assertIs(outcome.structured_content, wire["structured_content"])
        self.assertEqual(decode_canonical_owner_response_v1({"result": canonical(body={})}), {})

    def test_tool_error_remains_returned_error_not_client_unknown(self) -> None:
        wire = canonical(body={"error_type": "Synthetic", "wait_progress": None}, error=True)
        before = deepcopy(wire)
        row, _ = returned(wire)
        result = parse_owner_response_v1(row)
        self.assertIsInstance(result, ToolFailureV1)
        self.assertNotIn("client_error", row)
        self.assertEqual(wire, before)
        with self.assertRaisesRegex(RuntimeError, "SDK error; original result retained"):
            decode_canonical_owner_response_v1(row)

    def test_noncomplete_is_persisted_before_consumer_rejection(self) -> None:
        for tag in (None, "input_required", "future_result", True, 1):
            wire = canonical(body={"optional": None})
            wire["result_type"] = tag
            row, encoded = returned(wire)
            self.assertEqual(require_json_object_v1(json.loads(encoded))["result"], wire)
            self.assertNotIn("client_error", row)
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                parse_owner_response_v1(row)

    def test_boolean_flag_missing_null_number_string_and_aliases_rejected(self) -> None:
        good = canonical(body={})
        bad: object
        for bad in (None, 0, 1, 0.0, "false", "true", [], {}, Number.ZERO):
            wire: dict[str, object] = {**good, "is_error": bad}
            with self.subTest(flag=repr(bad)), self.assertRaises(ValueError):
                parse_owner_response_v1({"result": wire})
        for field in good:
            missing = dict(good)
            del missing[field]
            with self.subTest(missing=field), self.assertRaises(ValueError):
                parse_owner_response_v1({"result": missing})
        for alias, value in (("isError", False), ("structuredContent", {}),
                             ("resultType", "complete"), ("_meta", None)):
            wire = {**good, alias: value}
            with self.subTest(alias=alias), self.assertRaises(ValueError):
                parse_owner_response_v1({"result": wire})

    def test_conflicting_and_equal_duplicate_names_are_both_rejected(self) -> None:
        good = canonical(body={"status": "observed"})
        for flag in (False, True):
            with self.subTest(flag=flag), self.assertRaises(ValueError):
                parse_owner_response_v1({"result": {**good, "isError": flag}})
        for body in ({}, {"status": "observed"}, None):
            with self.subTest(body=body), self.assertRaises(ValueError):
                parse_owner_response_v1({"result": {**good, "structuredContent": body}})

    def test_meta_content_shapes_and_finite_json_boundary(self) -> None:
        bad: object
        good = canonical(body={})
        for field, bad in (("meta", []), ("meta", "meta"), ("content", None),
                           ("content", {}), ("content", [None]), ("content", ["text"])):
            with self.subTest(field=field, value=bad), self.assertRaises(ValueError):
                parse_owner_response_v1({"result": {**good, field: bad}})
        cycle: list[object] = []
        cycle.append(cycle)
        for bad in (cycle, (1, 2), {1: "bad key"}, float("nan"), float("inf"), object()):
            with self.subTest(value=type(bad).__name__), self.assertRaises(ValueError):
                require_json_object_v1({"bad": bad})

    def test_client_unknown_presence_is_separate_and_forbids_replay(self) -> None:
        row: JsonObject = {"request": {"sequence": 7}, "client_error": "original outcome unknown",
                           "replay_allowed": False}
        outcome = parse_owner_response_v1(row)
        self.assertIsInstance(outcome, ClientUnknownV1)
        self.assertIs(outcome.row, row)
        self.assertNotIn("result", row)
        with self.assertRaisesRegex(RuntimeError, "original request must not be resent"):
            decode_canonical_owner_response_v1(row)
        error: object
        for error in (None, False, 0, "", []):
            with self.subTest(client_error=error), self.assertRaises(ValueError):
                parse_owner_response_v1({**row, "client_error": error})
        for changed in ({**row, "result": canonical()}, {**row, "replay_allowed": 0},
                        {**row, "replay_allowed": True}, {"client_error": "unknown"}):
            with self.assertRaises(ValueError):
                parse_owner_response_v1(changed)

    def test_returned_projection_is_supported_and_error_is_never_an_alias(self) -> None:
        row: JsonObject = {"request": {}, "result": canonical(body={})}
        self.assertIsInstance(parse_owner_response_v1(row), ToolSuccessV1)
        bad: object
        for bad in (None, False, {}, "error"):
            with self.subTest(error=bad), self.assertRaises(ValueError):
                parse_owner_response_v1({**row, "error": bad})
        bad_row: object
        for bad_row in (None, [], "row", {}, {"client_error": None}):
            with self.subTest(row=bad_row), self.assertRaises(ValueError):
                parse_owner_response_v1(bad_row)

    def test_text_fallback_retains_object_only_business_boundary(self) -> None:
        wire = canonical()
        wire["content"] = [{"type": "text", "text": '{"status":"observed","optional":null}'}]
        expected: JsonObject = {"status": "observed", "optional": None}
        self.assertEqual(decode_canonical_owner_response_v1({"result": wire}), expected)
        for text in ("[]", "null", "not-json"):
            wire["content"] = [{"type": "text", "text": text}]
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, "no actual decoded object"):
                decode_canonical_owner_response_v1({"result": wire})
        wire["content"] = [{"type": "text"}]
        with self.assertRaises(ValueError):
            decode_canonical_owner_response_v1({"result": wire})

    def test_public_and_generated_annotations_resolve(self) -> None:
        for function in (parse_owner_response_v1, parse_canonical_tool_result_v1,
                         decode_canonical_owner_response_v1, prepare_success_response_row_v1):
            with self.subTest(function=function.__name__):
                self.assertIn("return", get_type_hints(function))
        namespace: dict[str, object] = {}
        exec(compile(canonical_decoder_source_v1(), "future-owner-reflection", "exec"), namespace)
        self.assertIn("return", get_type_hints(namespace["decoded"]))


if __name__ == "__main__":
    unittest.main()
