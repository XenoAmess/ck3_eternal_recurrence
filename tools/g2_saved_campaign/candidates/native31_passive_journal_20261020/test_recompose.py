"""Portable contract tests; only the last case needs optional Git history."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

import recompose as source

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]


def manifest_v1() -> source.ManifestV1:
    return source.ManifestV1("fixture-machine", "2026-10-20T19:39:37+00:00",
        source.SOURCE_PINS_V1, source.EVIDENCE_PINS_V1, source.BASELINE_PINS_V1,
        source.OUTPUT_PINS_V1, source.QualificationV1())


def document_v1() -> dict[str, object]:
    raw: object = json.loads(source.encode_manifest_v1(manifest_v1()))
    if not isinstance(raw, dict):
        raise AssertionError("actual encoder returned nonobject")
    return {str(key): value for key, value in raw.items()}


def decode_v1(value: object) -> source.ManifestV1:
    return source.decode_manifest_v1(json.dumps(value).encode())


def first_pin_v1(doc: dict[str, object]) -> dict[str, object]:
    rows = doc["source_inputs"]
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
        raise AssertionError("actual encoded source array required")
    result: dict[str, object] = {}
    for key, value in rows[0].items():
        if not isinstance(key, str):
            raise AssertionError("actual text key required")
        result[key] = value
    rows[0] = result
    return result


class SourcePackageV1Tests(unittest.TestCase):
    def test_json_roundtrip_preserves_model_and_array_domain(self) -> None:
        original = manifest_v1()
        encoded = source.encode_manifest_v1(original)
        self.assertEqual(source.decode_manifest_v1(encoded), original)
        self.assertIsInstance(document_v1()["source_inputs"], list)

    def test_missing_extra_null_and_wrong_root_fields(self) -> None:
        values: tuple[object, ...] = (None, [], 1, True, {})
        for value in values:
            with self.subTest(value=value), self.assertRaises(ValueError):
                decode_v1(value)
        doc = document_v1()
        del doc["schema"]
        with self.assertRaises(ValueError):
            decode_v1(doc)
        doc = document_v1()
        doc["extra"] = None
        with self.assertRaises(ValueError):
            decode_v1(doc)

    def test_integer_domain_rejects_bool_float_null_and_text(self) -> None:
        for value in (True, False, 4565.0, None, "4565"):
            doc = document_v1()
            first_pin_v1(doc)["bytes"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                decode_v1(doc)

    def test_pin_contract_rejects_missing_extra_drift_and_paths(self) -> None:
        for key, value in (("sha256", "0" * 64), ("name", "../outside.py"),
                           ("name", "C:/outside.py"), ("name", "native/./a.py")):
            doc = document_v1()
            first_pin_v1(doc)[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                decode_v1(doc)
        for key in ("sha256", "bytes", "name"):
            doc = document_v1()
            del first_pin_v1(doc)[key]
            with self.assertRaises(ValueError):
                decode_v1(doc)
        doc = document_v1()
        first_pin_v1(doc)["alias"] = "not accepted"
        with self.assertRaises(ValueError):
            decode_v1(doc)

    def test_empty_null_and_duplicate_arrays_stay_distinct(self) -> None:
        values: tuple[object, ...] = ([], None, {})
        for value in values:
            doc = document_v1()
            doc["source_inputs"] = value
            with self.assertRaises(ValueError):
                decode_v1(doc)
        doc = document_v1()
        rows = doc["source_inputs"]
        if not isinstance(rows, list):
            raise AssertionError("encoder array required")
        rows.append(rows[0])
        with self.assertRaises(ValueError):
            decode_v1(doc)

    def test_qualification_cannot_be_promoted_or_bool_as_count(self) -> None:
        for key, value in (("original_producer_postcheck", "PASS"),
                           ("runtime_admission_granted", True),
                           ("clean_native_build_verified", True),
                           ("game_calls_by_packaging", False),
                           ("game_calls_by_packaging", 0.0)):
            doc = document_v1()
            qual = doc["qualification"]
            if not isinstance(qual, dict):
                raise AssertionError("encoder qualification required")
            qual[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                decode_v1(doc)

    def test_missing_git_history_fails_without_head_or_network_fallback(self) -> None:
        failure = subprocess.CompletedProcess(["git"], 128, b"", b"missing object")
        with patch("recompose.subprocess.run", return_value=failure) as run:
            with self.assertRaisesRegex(source.MissingFrozenBaselineV1, "no network or HEAD fallback"):
                source.read_git_baseline_v1(REPO, manifest_v1())
        self.assertEqual(run.call_count, 1)
        args = run.call_args.args[0]
        self.assertEqual(args[:3], ["git", "cat-file", "blob"])
        self.assertNotIn("fetch", args)
        self.assertNotIn("HEAD", args)

    def test_model_pin_mutation_cannot_bypass_decoder(self) -> None:
        bad = replace(manifest_v1(), baseline_inputs=())
        with self.assertRaises(ValueError):
            source.recompose_source_v1(bad, {}, {})
        with self.assertRaises(ValueError):
            source.encode_manifest_v1(bad)

    def test_bad_input_bytes_are_rejected_before_legacy_execution(self) -> None:
        baseline = {pin.name: b"" for pin in source.BASELINE_PINS_V1}
        files = {pin.name: b"" for pin in source.SOURCE_PINS_V1}
        with self.assertRaisesRegex(ValueError, "immutable source bytes"):
            source.recompose_source_v1(manifest_v1(), baseline, files)

    def test_utc_requires_explicit_offset(self) -> None:
        for value in ("2026-10-20T19:00:00", "2026-10-20T19:00:00+08:00", None):
            doc = document_v1()
            doc["observed_at_utc"] = value
            with self.assertRaises(ValueError):
                decode_v1(doc)

    def test_local_actual_source_recomposition_if_history_available(self) -> None:
        manifest = source.decode_manifest_v1((ROOT / "MANIFEST.json").read_bytes())
        files = source.read_verified_inputs_v1(ROOT, manifest)
        try:
            baseline = source.read_git_baseline_v1(REPO, manifest)
        except source.MissingFrozenBaselineV1:
            self.skipTest("optional immutable Git history absent; CLI must fail closed until operator supplies it")
        out = source.recompose_source_v1(manifest, baseline, files)
        self.assertEqual(set(out), {pin.name for pin in source.OUTPUT_PINS_V1})
        for pin in source.OUTPUT_PINS_V1:
            self.assertEqual(len(out[pin.name]), pin.bytes)
            self.assertEqual(hashlib.sha256(out[pin.name]).hexdigest(), pin.sha256)


if __name__ == "__main__":
    unittest.main()

