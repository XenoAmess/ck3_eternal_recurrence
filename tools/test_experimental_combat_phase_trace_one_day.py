"""Focused contract checks for the disposable original trace runner."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from experimental_combat_phase_trace_one_day import (  # noqa: E402
    BEGIN,
    CAPABILITY,
    FINISH,
    run_bounded_original_phase_event_day,
    verify_official_no_launch_pair,
)


class FakeDriver:
    def __init__(self, checkpoint: Path, *, bad_combat: bool = False,
                 bad_checkpoint: bool = False, ending_delta: int = 24):
        self.checkpoint = checkpoint
        self.bad_combat = bad_combat
        self.bad_checkpoint = bad_checkpoint
        self.ending_delta = ending_delta
        self.calls: list[str] = []
        self.running = False
        self.paused_after = False

    def capabilities(self) -> dict[str, object]:
        return {
            "bridge_capabilities": [CAPABILITY],
            "native_session_control": {
                "driver_state_restored": True,
                "driver_state_restore_kind": "cold_checkpoint",
                "driver_state_error": None,
            },
        }

    def take_snapshot(self) -> dict[str, object]:
        date = 53192304 + (self.ending_delta if self.running else 0)
        return {
            "paused": not self.running or self.paused_after,
            "revision": 4 if self.running else 3,
            "native_revision": 4 if self.running else 3,
            "date_raw": date,
            "episode_run_id": "native-29829-2bc2d599f7f9",
            "played_character": {"character_id": 29829},
        }

    def execute_step(self, step: str, **_: object) -> dict[str, object]:
        self.calls.append(step)
        if step.startswith("query-battle-control-snapshot-v1-"):
            return {"status": "available", "queried_native_revision": 3,
                    "battle_control_snapshot": {
                "combat_id": 738197509 if self.bad_combat else 738197508,
                "observed_date_raw": 53192304,
                "subject_public_cunit_id": 83886367,
                "battle_control_ready": True,
            }}
        if step == "save-checkpoint":
            return {
                "checkpoint": {
                    "status": "saved", "path": str(self.checkpoint),
                    "size": self.checkpoint.stat().st_size,
                    "sha256": "0" * 64 if self.bad_checkpoint else hashlib.sha256(
                        self.checkpoint.read_bytes()).hexdigest().upper(),
                    "date_raw": 53192304,
                },
                "submission": {"sequence": 1, "date_raw": 53192304},
            }
        if step == "resume-map":
            self.running = True
        if step == "pause-map":
            self.paused_after = True
        return {"step": step, "accepted": True}

    def _execute_primitive_step(self, step: str, **fields: object) -> dict[str, object]:
        self.calls.append(step)
        token = fields["request_fields"]["managed_daily_sequence_token"]
        if step == BEGIN:
            return {"step": step, "accepted": True, "status": "armed",
                    "managed_daily_sequence_token": token}
        assert step == FINISH
        return {
            "step": step, "accepted": True,
            "status": "bounded_trace_available" if self.ending_delta == 24 else "trace_unavailable",
            "managed_trace": {"managed_checkpoint": {
                "recoverable_checkpoint_created": True,
                "exact_one_day_observed": self.ending_delta == 24,
                "detours_uninstalled": True,
                "before": {"combat_id": 738197508},
                "after": {"combat_id": 738197508},
            }},
        }


class BoundedTraceContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.checkpoint = Path(self.temp.name) / "xar_checkpoint.ck3"
        self.checkpoint.write_bytes(b"independent research checkpoint")
        self.index = {
            "episode": "native-29829-2bc2d599f7f9",
            "date_raw": 53192304, "actor": 29829,
            "files": {"prepared_save": {"sha256": "A" * 64}},
        }

    def test_one_exact_day_retains_research_only_status(self) -> None:
        driver = FakeDriver(self.checkpoint)
        result = run_bounded_original_phase_event_day(
            driver, official_index=self.index, combat_id=738197508,
            subject_army_id=83886367,
            daily_token=7,
        )
        self.assertEqual(result["ending_date_raw"], 53192328)
        self.assertFalse(result["production_trace_ready"])
        self.assertFalse(result["win_probability_available"])
        self.assertTrue(result["requires_controlled_stop_and_new_official_restore"])
        self.assertLess(driver.calls.index(BEGIN), driver.calls.index("resume-map"))
        self.assertLess(driver.calls.index("pause-map"), driver.calls.index(FINISH))

    def test_invalid_checkpoint_never_arms_or_resumes(self) -> None:
        driver = FakeDriver(self.checkpoint, bad_checkpoint=True)
        with self.assertRaisesRegex(ValueError, "checkpoint SHA"):
            run_bounded_original_phase_event_day(
                driver, official_index=self.index, combat_id=738197508,
                subject_army_id=83886367,
                daily_token=7,
            )
        self.assertNotIn(BEGIN, driver.calls)
        self.assertNotIn("resume-map", driver.calls)

    def test_missing_same_combat_proof_never_saves_or_resumes(self) -> None:
        driver = FakeDriver(self.checkpoint, bad_combat=True)
        with self.assertRaisesRegex(ValueError, "same-CombatID"):
            run_bounded_original_phase_event_day(
                driver, official_index=self.index, combat_id=738197508,
                subject_army_id=83886367,
                daily_token=7,
            )
        self.assertNotIn("save-checkpoint", driver.calls)
        self.assertNotIn("resume-map", driver.calls)

    def test_short_day_finishes_detours_and_stays_red(self) -> None:
        driver = FakeDriver(self.checkpoint, ending_delta=0)
        with self.assertRaisesRegex(ValueError, "one exact bounded day"):
            run_bounded_original_phase_event_day(
                driver, official_index=self.index, combat_id=738197508,
                subject_army_id=83886367,
                daily_token=7, deadline_seconds=0.01,
            )
        self.assertIn(FINISH, driver.calls)

    def test_overshoot_finishes_detours_and_stays_red(self) -> None:
        driver = FakeDriver(self.checkpoint, ending_delta=48)
        with self.assertRaisesRegex(ValueError, "one exact bounded day"):
            run_bounded_original_phase_event_day(
                driver, official_index=self.index, combat_id=738197508,
                subject_army_id=83886367,
                daily_token=7,
            )
        self.assertIn(FINISH, driver.calls)

    def test_official_pair_requires_exact_files_and_lifecycle(self) -> None:
        files = {}
        for name in ("manifest", "preflight", "semantic", "rebind",
                     "prepared_save", "prepared_driver", "exe", "dll", "injector"):
            path = Path(self.temp.name) / name
            if name == "preflight":
                path.write_text(json.dumps({
                    "ok": True, "status": "ready", "ck3_launch_attempted": False,
                    "expected": {
                        "xar_enabled": "xar_off",
                        "succession_lifecycle": "ordinary_campaign_succession",
                        "episode_character_id": 29829,
                        "episode_run_id": "native-29829-2bc2d599f7f9",
                        "checkpoint_sha256": hashlib.sha256(b"prepared_save").hexdigest(),
                        "driver_state_sha256": hashlib.sha256(b"prepared_driver").hexdigest(),
                    },
                }), encoding="utf-8")
            else:
                path.write_bytes(name.encode("ascii"))
            files[name] = {"path": str(path), "sha256": hashlib.sha256(
                path.read_bytes()).hexdigest().upper()}
        index = {
            "status": "NO_LAUNCH_READY",
            "profile": "ordinary_campaign_succession/xar_off",
            "actor": 29829, "episode": "native-29829-2bc2d599f7f9",
            "files": files,
        }
        path = Path(self.temp.name) / "ready.json"
        path.write_text(json.dumps(index), encoding="utf-8")
        digest = hashlib.sha256(path.read_bytes()).hexdigest().upper()
        self.assertEqual(verify_official_no_launch_pair(path, digest), index)
        files["prepared_save"]["sha256"] = "0" * 64
        path.write_text(json.dumps(index), encoding="utf-8")
        digest = hashlib.sha256(path.read_bytes()).hexdigest().upper()
        with self.assertRaisesRegex(ValueError, "prepared_save SHA"):
            verify_official_no_launch_pair(path, digest)


if __name__ == "__main__":
    unittest.main()
