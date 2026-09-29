"""The next H3937 operator must decide release before touching task-bus."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer.h3937_operator_release_gate import assess_screen_release  # noqa: E402


class ScreenReleaseDecisionTests(unittest.TestCase):
    def facts(self) -> dict[str, object]:
        return {
            "child_started": True,
            "child_exited": True,
            "target_processes_gone": True,
            "child_completion": {
                "outer_report_sha256": "A" * 64,
                "outer_cleanup_proven": True,
            },
            "outer_report": {
                "outer_session_cleanup_verified": True,
                "cleanup": {"cleanup_proven": True},
            },
            "outer_report_sha256": "A" * 64,
            "pre_native_launch_proven": False,
            "unsafe_marker_absent": True,
            "expected_watchdog_nonce": "exact-nonce",
            "expected_watchdog_parent_pid": 456,
            "nonce_bound_watchdog_scans": [
                {"schema": "xar.watchdog-nonce-scan.v1", "nonce": "exact-nonce",
                 "parent_pid": 456, "wmi_toolhelp_cross_checked": True,
                 "captured_monotonic_ns": tick, "identities": []}
                for tick in (1, 2)
            ],
            "watchdog_scan_error": None,
            "unique_owned_screen_lease": True,
        }

    def test_release_requires_all_native_and_watchdog_gates(self) -> None:
        self.assertTrue(assess_screen_release(**self.facts())["may_release"])
        cases = [
            ("child_exited", False),
            ("target_processes_gone", False),
            ("unsafe_marker_absent", False),
            ("unique_owned_screen_lease", False),
            ("watchdog_scan_error", "WMI unavailable"),
            ("nonce_bound_watchdog_scans", None),
            ("nonce_bound_watchdog_scans", [[]]),
        ]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                facts = self.facts()
                facts[key] = value
                self.assertFalse(assess_screen_release(**facts)["may_release"])
        facts = self.facts()
        facts["nonce_bound_watchdog_scans"][1]["identities"].append({"pid": 8056})
        self.assertFalse(assess_screen_release(**facts)["may_release"])

    def test_a13_shape_never_releases_lease(self) -> None:
        facts = self.facts()
        facts["child_completion"] = {
            "outer_report_sha256": "A" * 64,
            "outer_cleanup_proven": False,
        }
        facts["outer_report"] = {
            "outer_session_cleanup_verified": False,
            "cleanup": {"cleanup_proven": False},
        }
        facts["unsafe_marker_absent"] = False
        decision = assess_screen_release(**facts)
        self.assertFalse(decision["may_release"])
        self.assertIn("unsafe marker present or unreadable", decision["failures"])
        self.assertIn("child native cleanup not proven", decision["failures"])

    def test_red_delivery_can_release_after_proven_cleanup(self) -> None:
        facts = self.facts()
        facts["outer_report"] = {
            **facts["outer_report"], "status": "RED", "query_actions": 1,
        }
        self.assertTrue(assess_screen_release(**facts)["may_release"])

    def test_no_child_requires_pre_native_phase_proof(self) -> None:
        facts = self.facts()
        facts["child_started"] = False
        facts["child_completion"] = None
        facts["outer_report"] = None
        self.assertFalse(assess_screen_release(**facts)["may_release"])
        facts["pre_native_launch_proven"] = True
        self.assertTrue(assess_screen_release(**facts)["may_release"])

    def test_outer_digest_and_native_fields_must_match(self) -> None:
        for mutation in (
            {"outer_report_sha256": "B" * 64},
            {"child_completion": {"outer_report_sha256": "A" * 64,
                                  "outer_cleanup_proven": False}},
            {"outer_report": {"outer_session_cleanup_verified": True,
                              "cleanup": {"cleanup_proven": False}}},
        ):
            with self.subTest(mutation=mutation):
                facts = self.facts()
                facts.update(mutation)
                self.assertFalse(assess_screen_release(**facts)["may_release"])

    def test_malformed_proofs_never_authorize_release(self) -> None:
        cases = [
            ("child_started", "false"),
            ("child_exited", "true"),
            ("target_processes_gone", "true"),
            ("unsafe_marker_absent", "false"),
            ("unique_owned_screen_lease", "true"),
            ("watchdog_scan_error", ""),
            ("nonce_bound_watchdog_scans", [{}, {}]),
            ("nonce_bound_watchdog_scans", [None, None]),
            ("nonce_bound_watchdog_scans", ["", ""]),
            ("nonce_bound_watchdog_scans", [[], [], []]),
            ("nonce_bound_watchdog_scans", ""),
            ("expected_watchdog_nonce", ""),
            ("expected_watchdog_parent_pid", "456"),
            ("child_completion", "not a report"),
            ("outer_report", "not a report"),
        ]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                facts = self.facts()
                facts[key] = value
                self.assertFalse(assess_screen_release(**facts)["may_release"])
        for mutation in (
            {"nonce": "wrong-nonce"},
            {"parent_pid": 1456},
            {"wmi_toolhelp_cross_checked": "true"},
            {"captured_monotonic_ns": 1},
            {"identities": None},
            {"schema": "other-schema"},
        ):
            with self.subTest(scan_mutation=mutation):
                facts = self.facts()
                facts["nonce_bound_watchdog_scans"][1].update(mutation)
                self.assertFalse(assess_screen_release(**facts)["may_release"])


if __name__ == "__main__":
    unittest.main()
