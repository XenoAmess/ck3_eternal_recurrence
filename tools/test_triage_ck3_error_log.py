"""Synthetic offline contracts for the universal CK3 error-log triage CLI."""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import triage_ck3_error_log as triage


def script_record(time: str, error: str, caller: str = "events/test_event.txt") -> str:
    return (
        f"[{time}][E][script_system.cpp:100]: Script system error!\n"
        f"  Error: {error}\n"
        "  Script location: file: common/script_values/test_value.txt line: 18 (script value)\n"
        "\n"
        f"    file: {caller} line: 28 (event immediate effect)\n"
        f"    file: {caller} line: 28 (event immediate effect)\n"
    )


class TriageTests(unittest.TestCase):
    def test_multiline_grouping_and_all_caller_rankings(self) -> None:
        first = script_record("10:00:00", "Invalid scope none")
        payload = (
            "preamble\n" + first
            + script_record("10:00:01", "Invalid scope none", "events/other_event.txt")
            + script_record("10:00:02", "Unknown key 1851")
            + "[10:00:03][I][system.cpp:9]: Reached frontend\n"
        ).encode()
        report = triage.triage_bytes(payload)
        self.assertEqual((report["record_count"], report["error_record_count"]), (4, 3))
        self.assertEqual(report["level_record_counts"], {"E": 3, "I": 1})
        self.assertEqual(report["group_count"], 2)
        group = report["groups"][0]
        self.assertEqual(group["record_count"], 2)
        self.assertEqual(group["error"], "Invalid scope none")
        self.assertEqual(group["representative"]["raw_text"], first)
        self.assertEqual(group["occurrence_line_ranges"], [[2, 7], [8, 13]])
        self.assertEqual(len(group["representative"]["locations"]), 3)
        self.assertEqual(report["script_locations"]["primary"][0]["record_count"], 3)
        callers = report["script_locations"]["caller"]
        self.assertEqual([(row["file"], row["record_count"]) for row in callers], [
            ("events/test_event.txt", 2), ("events/other_event.txt", 1),
        ])
        self.assertEqual(report["parse_evidence"]["preamble_line_count"], 1)

    def test_literal_ids_positions_and_contexts_are_not_normalized(self) -> None:
        payload = (
            script_record("t", "Unknown key 1851") + script_record("t", "Unknown key 1852")
            + script_record("t", "Unknown key 1851").replace("line: 18", "line: 19")
            + script_record("t", "Unknown key 1851").replace("(script value)", "(effect)")
        ).encode()
        report = triage.triage_bytes(payload)
        self.assertEqual(report["group_count"], 4)
        self.assertEqual(len(report["script_locations"]["primary"]), 3)
        self.assertEqual([group["record_count"] for group in report["groups"]], [1] * 4)
        self.assertEqual(triage.triage_bytes(payload), report)

    def test_cap_threshold_uses_error_count_and_never_confirms_engine_configuration(self) -> None:
        payload = (
            "[t][I][system.cpp:1]: Identifier 100000\n"
            "[t][E][lexer.cpp:1]: Error number 100000\n"
            "[t][W][logger.cpp:1]: Synthetic cap marker\n"
        ).encode()
        unspecified = triage.triage_bytes(payload)["cap_evidence"]
        self.assertIsNone(unspecified["error_records_reach_declared_cap"])
        self.assertEqual(unspecified["marker_line_count"], 0)
        reached = triage.triage_bytes(payload, declared_error_cap=1, cap_marker_literal="Synthetic cap marker")
        evidence = reached["cap_evidence"]
        self.assertTrue(evidence["error_records_reach_declared_cap"])
        self.assertIsNone(evidence["engine_cap_confirmed"])
        self.assertEqual(evidence["marker_line_count"], 1)
        self.assertEqual(evidence["marker_lines"][0]["line"], 3)
        self.assertFalse(triage.triage_bytes(payload, declared_error_cap=3)["cap_evidence"]["error_records_reach_declared_cap"])

    def test_parse_limits_empty_file_decode_and_unterminated_tail(self) -> None:
        empty = triage.triage_bytes(b"")
        self.assertEqual((empty["record_count"], empty["line_count"]), (0, 0))
        self.assertIsNone(empty["record_boundaries"]["last"])
        self.assertTrue(empty["parse_evidence"]["final_line_terminated"])
        unsupported = triage.triage_bytes(b"before\n[t][ERROR][engine]: unsupported\n")
        self.assertEqual(unsupported["record_count"], 0)
        self.assertEqual(unsupported["parse_evidence"]["preamble_line_count"], 2)
        self.assertEqual(unsupported["parse_evidence"]["unsupported_header_like_lines"][0]["line"], 2)
        invalid = triage.triage_bytes(b"[t][E][engine:1]: broken \xff")
        self.assertIsNotNone(invalid["parse_evidence"]["decode_error"])
        self.assertFalse(invalid["parse_evidence"]["final_line_terminated"])
        self.assertEqual(invalid["parse_evidence"]["error_records_without_primary_location"], 1)

    def test_existing_diagnostics_header_without_emitter_and_multiple_errors(self) -> None:
        report = triage.triage_bytes(b"[t][E] Generic heading\n Error: first\n Error: second\n[t][F]: fatal\n")
        self.assertEqual(report["level_record_counts"], {"E": 1, "F": 1})
        self.assertEqual(report["groups"][0]["emitter"], "")
        self.assertEqual(report["groups"][0]["error_messages"], ["first", "second"])
        self.assertEqual(report["parse_evidence"]["error_records_with_multiple_error_lines"], 1)

    def test_changed_reads_rejected_before_output_creation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / "error.log", root / "attempt"
            source.write_bytes(b"original")
            with patch.object(Path, "open", side_effect=[io.BytesIO(b"one"), io.BytesIO(b"two")]):
                with self.assertRaisesRegex(ValueError, "changed between reads"):
                    triage.write_triage(source, output)
            self.assertFalse(output.exists())
            self.assertEqual(source.read_bytes(), b"original")

    def test_cli_exact_frozen_bytes_repeatability_csv_and_existing_output_refusal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, first, second = root / "error.log", root / "a01", root / "a02"
            payload = b"\xef\xbb\xbf" + script_record("t", "Invalid scope none").replace("\n", "\r\n").encode()
            source.write_bytes(payload)
            argv = [sys.executable, str(Path(triage.__file__)), "--source", str(source), "--output-dir", str(first), "--declared-error-cap", "1"]
            command = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(command.returncode, 0, command.stderr)
            report = json.loads((first / "triage.json").read_text(encoding="utf-8"))
            self.assertEqual((first / "source.log").read_bytes(), payload)
            self.assertEqual(report["source_sha256"], hashlib.sha256(payload).hexdigest())
            self.assertTrue(report["source"]["two_reads_equal"])
            self.assertEqual(report["tool"]["sha256"], hashlib.sha256(Path(triage.__file__).read_bytes()).hexdigest())
            with (first / "groups.csv").open(encoding="utf-8", newline="") as stream:
                groups = list(csv.DictReader(stream))
            self.assertEqual((groups[0]["record_count"], groups[0]["line"]), ("1", "18"))
            with (first / "script-locations.csv").open(encoding="utf-8", newline="") as stream:
                positions = list(csv.DictReader(stream))
            self.assertEqual([row["role"] for row in positions], ["primary", "caller"])
            triage.write_triage(source, second, declared_error_cap=1)
            for name in ("source.log", "triage.json", "groups.csv", "script-locations.csv"):
                self.assertEqual((first / name).read_bytes(), (second / name).read_bytes())
            frozen = {path.name: path.read_bytes() for path in first.iterdir()}
            source.write_bytes(b"different later log")
            refused = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(refused.returncode, 2)
            self.assertIn("output already exists", refused.stderr)
            self.assertEqual({path.name: path.read_bytes() for path in first.iterdir()}, frozen)
            self.assertEqual(source.read_bytes(), b"different later log")

    def test_invalid_options_and_bound_are_explicit(self) -> None:
        for options in ({"declared_error_cap": 0}, {"cap_marker_literal": ""}, {"cap_marker_literal": "a\nb"}, {"cap_marker_literal": "a\0b"}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                triage.triage_bytes(b"", **options)
        with patch.object(triage, "MAX_LOG_BYTES", 3):
            with self.assertRaises(ValueError):
                triage.triage_bytes(b"four")
            with patch.object(Path, "open", return_value=io.BytesIO(b"four")):
                with self.assertRaises(ValueError):
                    triage.read_stable_bytes(Path("synthetic.log"))


if __name__ == "__main__":
    unittest.main()
