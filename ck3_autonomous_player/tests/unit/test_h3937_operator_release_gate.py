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
            "nonce_bound_watchdog_scans": [[], []],
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
            ("nonce_bound_watchdog_scans", [[], [{"pid": 8056}]]),
        ]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                facts = self.facts()
                facts[key] = value
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


if __name__ == "__main__":
    unittest.main()
