"""Portable core-admission regression; no runtime, capacity query or card write."""
from __future__ import annotations

from copy import deepcopy
from enum import IntEnum
import inspect
import json
from pathlib import Path
import sys
from typing import TypeGuard, get_type_hints
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from cold_runtime_admission_contract_v1 import (
    MAX_SAFE_INTEGER, parse_cold_runtime_admission_core_v1,
)

Doc = dict[str, object]
MACHINE = "portable-admission-fixture"


class Number(IntEnum):
    ONE = 1


def is_record(value: object) -> TypeGuard[Doc]:
    return isinstance(value, dict) and all(type(key) is str for key in value)


def record(value: object) -> Doc:
    if not is_record(value):
        raise AssertionError("fixture text-keyed object required")
    return value


def card() -> Doc:
    reference: Doc = {"path": str(Path(__file__).resolve()),
                      "bytes": 1, "sha256": "a" * 64}
    return {
        "schema": "xar.Source29-A17-runtime-prepare-admission/v1",
        "machine_id": MACHINE, "owner": "Root", "status": "ADMITTED",
        "root_direct_execution_release": True,
        "plan": deepcopy(reference), "quote": deepcopy(reference),
        "full_storage_ref": deepcopy(reference),
        "canonical_capacity_review_passed": True,
        "runtime_hard_bytes": 3145728,
        "capacity": {"D_free_floor_bytes": 855064299492,
                     "Z_free_floor_bytes": 147416969216},
        "qualification": {"preserved": True},
    }


class ColdRuntimeAdmissionCoreTests(unittest.TestCase):
    def test_valid_current_core_roundtrip_and_detached_projection(self) -> None:
        raw = card()
        original = deepcopy(raw)
        result = parse_cold_runtime_admission_core_v1(
            json.loads(json.dumps(raw)), expected_machine_id=MACHINE)
        self.assertEqual(result["runtime_hard_bytes"], 3145728)
        self.assertIs(result["canonical_capacity_review_passed"], True)
        self.assertNotIn("qualification", result)
        self.assertEqual(raw, original)
        self.assertEqual(parse_cold_runtime_admission_core_v1(
            json.loads(json.dumps(result)), expected_machine_id=MACHINE), result)
        result["capacity"]["D_free_floor_bytes"] = 1
        self.assertEqual(record(raw["capacity"])["D_free_floor_bytes"], 855064299492)

    def test_real_243_missing_review_flag_regression(self) -> None:
        raw = card()
        del raw["canonical_capacity_review_passed"]
        with self.assertRaisesRegex(ValueError, "canonical_capacity_review_passed"):
            parse_cold_runtime_admission_core_v1(raw, expected_machine_id=MACHINE)

    def test_every_required_core_field_is_required(self) -> None:
        for key in set(card()) - {"qualification"}:
            raw = card()
            del raw[key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                parse_cold_runtime_admission_core_v1(raw, expected_machine_id=MACHINE)
        for key in ("D_free_floor_bytes", "Z_free_floor_bytes"):
            raw = card()
            del record(raw["capacity"])[key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                parse_cold_runtime_admission_core_v1(raw, expected_machine_id=MACHINE)

    def test_flags_are_actual_true_and_authority_is_exact(self) -> None:
        for key in ("canonical_capacity_review_passed", "root_direct_execution_release"):
            for value in (False, None, 0, 1, 1.0, Number.ONE, "true"):
                raw = card()
                raw[key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    parse_cold_runtime_admission_core_v1(raw, expected_machine_id=MACHINE)
        for key, value in (("machine_id", "other"), ("owner", "root"),
                           ("status", "REJECTED"), ("schema", "future")):
            raw = card()
            raw[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                parse_cold_runtime_admission_core_v1(raw, expected_machine_id=MACHINE)

    def test_integer_domain_for_hard_limit_and_both_floors(self) -> None:
        for key in ("runtime_hard_bytes", "D_free_floor_bytes", "Z_free_floor_bytes"):
            for value in (True, 1.0, Number.ONE, None, 0, -1, MAX_SAFE_INTEGER + 1):
                raw = card()
                target = raw if key == "runtime_hard_bytes" else record(raw["capacity"])
                target[key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    parse_cold_runtime_admission_core_v1(raw, expected_machine_id=MACHINE)

    def test_legacy_names_never_substitute_or_shadow_current_fields(self) -> None:
        for retain_current in (True, False):
            raw = card()
            raw["hard_bytes"] = raw["runtime_hard_bytes"]
            if not retain_current:
                del raw["runtime_hard_bytes"]
            with self.subTest(retain=retain_current), self.assertRaises(ValueError):
                parse_cold_runtime_admission_core_v1(raw, expected_machine_id=MACHINE)
            raw = card()
            capacity = record(raw["capacity"])
            capacity["D_conservative_floor_bytes"] = capacity["D_free_floor_bytes"]
            if not retain_current:
                del capacity["D_free_floor_bytes"]
            with self.subTest(floor_retain=retain_current), self.assertRaises(ValueError):
                parse_cold_runtime_admission_core_v1(raw, expected_machine_id=MACHINE)

    def test_refs_use_one_shared_shape_and_strict_bytes(self) -> None:
        value: object
        for key in ("plan", "quote", "full_storage_ref"):
            for value in (None, [], "ref", {"path": "relative", "bytes": 1, "sha256": "a" * 64}):
                raw = card()
                raw[key] = value
                with self.subTest(key=key, shape=value), self.assertRaises(ValueError):
                    parse_cold_runtime_admission_core_v1(raw, expected_machine_id=MACHINE)
            for field in ("path", "bytes", "sha256"):
                raw = card()
                del record(raw[key])[field]
                with self.subTest(key=key, missing=field), self.assertRaises(ValueError):
                    parse_cold_runtime_admission_core_v1(raw, expected_machine_id=MACHINE)
            for value in (True, 1.0, Number.ONE, None, 0):
                raw = card()
                record(raw[key])["bytes"] = value
                with self.subTest(key=key, size=value), self.assertRaises(ValueError):
                    parse_cold_runtime_admission_core_v1(raw, expected_machine_id=MACHINE)
            raw = card()
            record(raw[key])["old_digest"] = "a" * 64
            with self.subTest(extra=key), self.assertRaises(ValueError):
                parse_cold_runtime_admission_core_v1(raw, expected_machine_id=MACHINE)

    def test_json_root_capacity_and_nonfinite_are_rejected(self) -> None:
        value: object
        for value in (None, [], "card", True):
            with self.subTest(root=value), self.assertRaises(ValueError):
                parse_cold_runtime_admission_core_v1(value, expected_machine_id=MACHINE)
            raw = card()
            raw["capacity"] = value
            with self.subTest(capacity=value), self.assertRaises(ValueError):
                parse_cold_runtime_admission_core_v1(raw, expected_machine_id=MACHINE)
        raw = card()
        raw["runtime_hard_bytes"] = float("nan")
        with self.assertRaises(ValueError):
            parse_cold_runtime_admission_core_v1(raw, expected_machine_id=MACHINE)

    def test_public_callable_has_complete_runtime_resolvable_annotations(self) -> None:
        method = parse_cold_runtime_admission_core_v1
        annotations = get_type_hints(method)
        self.assertEqual(set(annotations), {*inspect.signature(method).parameters, "return"})


if __name__ == "__main__":
    unittest.main()
