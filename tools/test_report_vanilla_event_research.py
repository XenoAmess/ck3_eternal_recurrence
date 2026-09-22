"""Focused offline tests for research metadata reporting, not gameplay evidence."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import report_vanilla_event_research as reporter


def catalog():
    return {
        "contracts": {"health.1001": {"options": (0, 6)}, "yearly.0003": {}},
        "analysis": {
            "health.1001": {"source_sha256": {"events/health.txt": "A" * 64}},
            "yearly.0003": {},
        },
        "observations": {
            "health.1001": {"exemplars": [{"kind": "pre-selection-live-red", "selection_attempted": False}]},
            "yearly.0003": {"exemplars": [{"kind": "legacy-live-binding"}]},
        },
    }


def report(data=None, **kwargs):
    return reporter.build_report(
        catalog() if data is None else data,
        ck3_build="test-build", ck3_exe_sha256="B" * 64, **kwargs,
    )


class ResearchReportTests(unittest.TestCase):
    def test_counts_and_digests_follow_catalog_changes(self):
        data = catalog()
        before = report(data)
        data["contracts"]["new.0100"] = {}
        data["analysis"]["new.0100"] = {}
        data["observations"]["new.0100"] = {"exemplars": []}
        after = report(data)
        self.assertEqual(after["catalog"]["registered_events"], 3)
        self.assertEqual(after["catalog"]["nonlegacy_observation_metadata_coverage"]["percent"], 33.33)
        self.assertNotEqual(before["catalog"]["digests"]["catalog"], after["catalog"]["digests"]["catalog"])
        self.assertNotIn("selected_events", after)

    def test_zero_denominator_is_unavailable_not_zero_or_complete(self):
        result = report({"contracts": {}, "analysis": {}, "observations": {}})
        for field in ("valid_source_hash_field_coverage", "nonlegacy_observation_metadata_coverage"):
            self.assertEqual(result["catalog"][field]["count"], 0)
            self.assertIsNone(result["catalog"][field]["percent"])
        self.assertIn("N/A", reporter.render_report(result, "markdown"))

    def test_invalid_hashes_do_not_count_as_valid_coverage(self):
        for hashes in ({"x": "Z" * 64}, {"x": "A" * 63}, {"x": " A" * 32}, {"": "A" * 64}, {"x": "A" * 64, "y": "bad"}, "A" * 64, None):
            with self.subTest(hashes=hashes):
                data = catalog()
                data["analysis"]["health.1001"]["source_sha256"] = hashes
                summary = report(data)["catalog"]
                self.assertEqual(summary["valid_source_hash_field_coverage"]["count"], 0)
                self.assertEqual(summary["source_hash_field_counts"]["invalid"], 1)

    def test_red_observation_is_only_nonlegacy_metadata(self):
        result = report(event_keys=["health.1001"])
        self.assertEqual(result["selected_events"][0]["observation_metadata_status"], "nonlegacy_present")
        text = reporter.render_report(result, "json")
        self.assertNotIn('"live_success"', text)
        self.assertNotIn("GREEN", text)
        self.assertNotIn('"source-reviewed"', text)
        self.assertIn("does not prove a successful action", text)

    def test_missing_empty_and_unclassified_observations_are_separate(self):
        for value, status in ((None, "invalid"), ({"exemplars": []}, "empty"), ({"exemplars": [{}]}, "unclassified")):
            data = catalog()
            data["observations"]["health.1001"] = value
            self.assertEqual(report(data)["catalog"]["observation_metadata_counts"][status], 1)
        data = catalog()
        del data["observations"]["health.1001"]
        self.assertEqual(report(data)["catalog"]["observation_metadata_counts"]["missing"], 1)

    def test_order_independent_deterministic_report_and_detached_input(self):
        data = catalog()
        original = deepcopy(data)
        first = report(data, event_keys=["yearly.0003", "health.1001", "health.1001"])
        reversed_data = {name: dict(reversed(list(table.items()))) for name, table in reversed(list(data.items()))}
        second = report(reversed_data, event_keys=["health.1001", "yearly.0003"])
        for format_name in ("json", "markdown"):
            self.assertEqual(reporter.render_report(first, format_name), reporter.render_report(second, format_name))
        self.assertEqual(data, original)
        self.assertEqual(reporter.canonical_bytes({1: "x"}), reporter.canonical_bytes({"1": "x"}))
        with self.assertRaisesRegex(ValueError, "colliding"):
            reporter.canonical_bytes({1: "x", "1": "y"})

    def test_filters_use_exact_namespaces_and_intersection(self):
        selected = report(namespaces=["health"])
        self.assertEqual(selected["catalog"]["registered_events"], 2)
        self.assertEqual(selected["selected"]["registered_events"], 1)
        self.assertEqual(selected["selected_events"][0]["event_definition_key"], "health.1001")
        self.assertEqual(report(event_keys=["yearly.0003"], namespaces=["health"])["selected"]["registered_events"], 0)
        for filters in ({"event_keys": ["missing.1"]}, {"namespaces": ["heal"]}, {"event_keys": [""]}):
            with self.subTest(filters=filters), self.assertRaises(ValueError):
                report(**filters)

    def test_unregistered_metadata_is_rejected(self):
        data = catalog()
        data["analysis"]["unknown.1"] = {}
        with self.assertRaisesRegex(ValueError, "unregistered"):
            report(data)

    @mock.patch.object(reporter, "_repository_head", return_value="C" * 40)
    @mock.patch.object(reporter, "load_catalog", side_effect=lambda: (catalog(), "test-build", "B" * 64))
    def test_cli_stdout_and_explicit_output_never_overwrites(self, load, head):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(reporter.main(["--event-key", "health.1001"]), 0)
        self.assertEqual(json.loads(stdout.getvalue())["selected"]["registered_events"], 1)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "report.md"
            self.assertEqual(reporter.main(["--format", "markdown", "--namespace", "health", "--output", str(output)]), 0)
            original = output.read_bytes()
            self.assertIn(b"health.1001", original)
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                reporter.main(["--output", str(output)])
            self.assertEqual(error.exception.code, 2)
            self.assertEqual(output.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
