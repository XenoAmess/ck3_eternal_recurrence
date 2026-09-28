"""No-process tests for the opt-in formal query passive sampler hook."""

from __future__ import annotations

import inspect
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from xar_autoplayer.native_auto_run import native_auto_run
from xar_autoplayer.cli import parser
from xar_autoplayer.war_cash_formal_query_passive_topbar_v1 import (
    MAX_READ, RECEIPT_NAME, capture_formal_query_passive_topbar,
)


FRAME = {
    "played_character_id": 29829,
    "native_revision": 3,
    "date_raw": 53219928,
    "snapshot_id": "native:3",
    "revision": 4,
    "episode_run_id": "native-29829-2bc2d599f7f9",
}


def candidate(frame: dict[str, object] | None = None) -> dict[str, object]:
    identity = dict(FRAME if frame is None else frame)
    return {
        "status": "same_paused_query_postcheck_passed",
        "source_frame_before": dict(identity),
        "source_frame_after": dict(identity),
        "process_pid": 7711,
        "process_created_filetime": 133_700_000,
        "treasury_after_raw": 120_644_281,
        "loaded_game_exe_sha256": "A" * 64,
    }


def sample(*, first: object = 1024, second: object = 2048,
           pid: object = 7711) -> dict[str, object]:
    return {
        "status": "stable_supplied_bytes_diagnostic_only",
        "pid": pid,
        "process_created_filetime": 133_700_000,
        "process_exe_sha256": "A" * 64,
        "sampler_exit_code": 0,
        "same_native_frame_before_after_proven_by_this_tool": False,
        "formal_cash_eligible": False,
        "game_code_called": False,
        "game_memory_written": False,
        "diagnostic": {
            "status": "stable_supplied_bytes_diagnostic_only",
            "first": {"target_memory_bytes_read": first},
            "second": {"target_memory_bytes_read": second},
            "total_target_memory_bytes_read": first + second,
            "formal_cash_eligible": False,
        },
    }


class FormalQueryPassiveTopbarTests(unittest.TestCase):
    def test_default_is_disabled(self) -> None:
        parameter = inspect.signature(native_auto_run).parameters[
            "formal_war_query_passive_topbar"
        ]
        self.assertIs(parameter.default, False)
        parsed = parser().parse_args(["native-auto-run", "--turns", "1"])
        self.assertIs(parsed.formal_war_query_passive_topbar, False)
        opted = parser().parse_args([
            "native-auto-run", "--turns", "1",
            "--formal-war-query-passive-topbar",
        ])
        self.assertIs(opted.formal_war_query_passive_topbar, True)

    def _run(self, *, query: dict[str, object] | None = None,
             post: dict[str, object] | None = None,
             sampler=None):
        with tempfile.TemporaryDirectory() as directory:
            attempt = Path(directory)
            (attempt / "intent.json").write_bytes(b"formal attempt")
            def bound_sample(pid: int, path: Path) -> dict[str, object]:
                result = (sampler(pid, path) if sampler is not None else sample())
                result.setdefault("session_receipt", str(path / "intent.json"))
                result.setdefault("session_receipt_sha256", hashlib.sha256(
                    (path / "intent.json").read_bytes()).hexdigest().upper())
                return result
            receipt, after = capture_formal_query_passive_topbar(
                attempt_dir=attempt,
                candidate=candidate() if query is None else query,
                postcheck=lambda: candidate() if post is None else post,
                sampler=bound_sample,
            )
            raw = (attempt / RECEIPT_NAME).read_bytes()
            body = json.loads(raw)
            self.assertEqual(receipt["sha256"], hashlib.sha256(raw).hexdigest().upper())
            self.assertFalse(body["formal_cash_eligible"])
            for key in (
                "pending_war_cash_raw", "immediate_war_action_cost_raw",
                "future_war_cost_upper_raw", "future_risk_budget_raw",
                "minimum_war_gold_reserve_raw",
            ):
                self.assertIsNone(body[key])
            self.assertEqual(body["status"], "RED_diagnostic_only")
            repeated, _ = capture_formal_query_passive_topbar(
                attempt_dir=attempt, candidate=candidate(),
                postcheck=candidate,
                sampler=lambda _pid, _dir: sample(),
            )
            self.assertEqual(repeated["status"],
                             "RED_observer_receipt_write_failed")
            self.assertEqual((attempt / RECEIPT_NAME).read_bytes(), raw)
            return receipt, after, body

    def test_stable_same_pid_is_still_diagnostic_red(self) -> None:
        receipt, post, body = self._run()
        self.assertTrue(receipt["post_sample_formal_query_check_passed"])
        self.assertEqual(post["source_frame_after"], FRAME)
        self.assertEqual(body["missing_reasons"], [
            "gui_cache_natural_refresh_and_military_cash_composition_unproven"
        ])

    def test_changed_native_frame_fails_closed(self) -> None:
        changed = dict(FRAME, native_revision=4)
        receipt, _, body = self._run(post=candidate(changed))
        self.assertFalse(receipt["post_sample_formal_query_check_passed"])
        self.assertIn("post_sample_same_pid_or_six_field_frame_unproven",
                      body["missing_reasons"])

    def test_permission_error_is_isolated(self) -> None:
        def deny(_pid: int, _dir: Path):
            raise PermissionError("read denied")
        receipt, _, body = self._run(sampler=deny)
        self.assertTrue(receipt["post_sample_formal_query_check_passed"])
        self.assertIn("passive_read_failed:PermissionError", body["missing_reasons"])

    def test_sampler_exception_does_not_skip_postcheck(self) -> None:
        observed = []
        def fail(_pid: int, _dir: Path):
            raise RuntimeError("sampler failed")
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "intent.json").write_bytes(b"formal attempt")
            receipt, post = capture_formal_query_passive_topbar(
                attempt_dir=Path(directory), candidate=candidate(),
                postcheck=lambda: observed.append("post") or candidate(),
                sampler=fail,
            )
            self.assertEqual(observed, ["post"])
            self.assertTrue(receipt["post_sample_formal_query_check_passed"])
            self.assertEqual(post["status"], "same_paused_query_postcheck_passed")

    def test_postcheck_exception_is_typed_red(self) -> None:
        def fail():
            raise OSError("postcheck failed")
        with tempfile.TemporaryDirectory() as directory:
            attempt = Path(directory)
            (attempt / "intent.json").write_bytes(b"formal attempt")
            receipt, post = capture_formal_query_passive_topbar(
                attempt_dir=attempt, candidate=candidate(),
                postcheck=fail, sampler=lambda _pid, _dir: sample(),
            )
            self.assertIsNone(post)
            self.assertFalse(receipt["post_sample_formal_query_check_passed"])
            self.assertIn("post_sample_frame_check_failed:OSError",
                          receipt["missing_reasons"])

    def test_read_budget_and_pid_are_strict(self) -> None:
        for abnormal in (
            sample(first=MAX_READ + 1), sample(second=MAX_READ + 1),
            sample(first=False), sample(pid=7712),
        ):
            with self.subTest(abnormal=abnormal):
                _, _, body = self._run(
                    sampler=lambda _pid, _dir: abnormal,
                )
                self.assertIn(
                    "read_only_pid_or_64k_budget_or_cache_diagnostic_unproven",
                    body["missing_reasons"],
                )

    def test_missing_six_field_candidate_never_reads(self) -> None:
        invalid = candidate()
        invalid["source_frame_after"].pop("native_revision")
        def should_not_read(_pid: int, _dir: Path):
            self.fail("invalid frame reached memory reader")
        receipt, post, body = self._run(query=invalid, sampler=should_not_read)
        self.assertIsNone(post)
        self.assertFalse(receipt["post_sample_formal_query_check_passed"])
        self.assertIn("candidate_frame_or_pid_incomplete", body["missing_reasons"])


if __name__ == "__main__":
    unittest.main()
