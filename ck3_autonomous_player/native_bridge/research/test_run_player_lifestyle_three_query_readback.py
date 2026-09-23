"""Focused no-CK3 shape tests for the bounded private M4 readback entry."""

from __future__ import annotations

import copy
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from run_player_lifestyle_current_state_read import PRIVATE_STEP as STATE_STEP
from run_player_lifestyle_current_state_read import _frame as life2_frame
from run_player_lifestyle_three_query_readback import (
    FOCUS_STEP,
    PERK_STEP,
    PROFESSIONAL_STEP,
    _frame,
    _manifest_source_identities,
    _new_bound_driver,
    _ordinary_binding,
    _query,
    _verify_ordinary_profile,
    parser,
    run_three_queries,
    run_professional_workforce_query,
)
from test_run_player_lifestyle_current_state_read import typed_state


EPISODE = "native-29829-example"


def paused_frame() -> dict[str, object]:
    return {
        "snapshot_id": "native:3",
        "native_revision": 3,
        "date_raw": 53_178_312,
        "paused": True,
        "map_ready": True,
        "played_character": {"character_id": 29_829, "alive": True},
        "episode_run_id": EPISODE,
    }


class FakeEndpoint:
    def __init__(self) -> None:
        self.sent: list[dict[str, object]] = []

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(request)


class FakeState:
    def __init__(self, endpoint: FakeEndpoint) -> None:
        self.endpoint = endpoint
        self.frame = paused_frame()
        self.focus_status = "observed_native_legal"
        self.focus_progress_presence = "present"
        self.perk_status = "available"
        self.perk_error: str | None = None
        self.progress_presence = "present"
        self.professional_status = "observed_native_legal"
        self.professional_owned = False

    def semantic_snapshot(self) -> dict[str, object]:
        return copy.deepcopy(self.frame)

    def wait_for_command_result(
        self, request_id: str, timeout_seconds: float
    ) -> dict[str, object]:
        request = self.endpoint.sent[-1]
        if request["request_id"] != request_id or timeout_seconds <= 0:
            raise RuntimeError("fake native read binding lost")
        step = request["step"]
        result: dict[str, object] = {
            "step": step,
            "private_build": True,
            "advertised": False,
            "episode_run_id": EPISODE,
        }
        if step == STATE_STEP:
            snapshot = typed_state()
            if self.progress_presence == "absent":
                snapshot["current_lifestyle_progress"] = {"presence": "absent"}
            result.update(status="available", snapshot=snapshot)
        elif step == PERK_STEP:
            if self.perk_error is not None:
                return {
                    "type": "command_result",
                    "protocol_version": 1,
                    "request_id": request_id,
                    "ok": False,
                    "error": self.perk_error,
                }
            snapshot = typed_state()
            snapshot["legal_perk_candidates"] = {
                "status": self.perk_status,
                "scope": "policy_target",
                "items": [{"key": "cutting_corners_perk", "lifestyle_key": "stewardship_lifestyle"}],
            }
            snapshot["readiness"]["legal_perk_candidates_ready"] = (
                self.perk_status == "available"
            )
            result.update(
                status="available",
                formal_precondition_status="permitted",
                snapshot=snapshot,
            )
        elif step == FOCUS_STEP:
            result.update(
                status=self.focus_status,
                read_only=True,
                policy_scoped=True,
                target_key="stewardship_wealth_focus",
                snapshot_id="native:3",
            )
            if self.focus_status in {
                "observed_native_legal", "observed_native_illegal"
            }:
                result.update(
                    native_legal=self.focus_status == "observed_native_legal",
                    scanned_database_rows=16,
                    target_lifestyle_key="stewardship_lifestyle",
                    target_lifestyle_progress=(
                        {
                            "presence": "present", "source": "exact_native_getters",
                            "xp_total_raw": 0, "xp_within_level_raw": 0,
                            "xp_per_level": 1000, "unspent_perk_points": 0,
                            "used_perk_points": 0,
                        }
                        if self.focus_progress_presence == "present" else
                        {"presence": "unavailable", "reason": "target_native_getters_unavailable"}
                    ),
                )
        elif step == PROFESSIONAL_STEP:
            result.update(
                status=self.professional_status,
                read_only=True,
                policy_scoped=True,
                snapshot_id="native:3",
                native_revision=3,
                date_raw=53_178_312,
                played_character_id=29_829,
                target_key="professional_workforce_perk",
            )
            if self.professional_status in {
                "observed_native_legal", "observed_native_illegal"
            }:
                result.update(
                    lifestyle_key="stewardship_lifestyle",
                    native_legal=self.professional_status == "observed_native_legal",
                    target_perk_owned=self.professional_owned,
                    unspent_perk_points=1,
                    used_perk_points=5,
                    xp_total_raw=213125,
                    xp_within_level_raw=13125,
                    xp_per_level=1000,
                    validator_invoked_twice=True,
                    scanned_database_rows=96,
                )
        else:
            raise RuntimeError("test sent an unexpected step")
        return {
            "type": "command_result",
            "protocol_version": 1,
            "request_id": request_id,
            "ok": True,
            "result": result,
        }


class FakeDriver:
    def __init__(self) -> None:
        self.endpoint = FakeEndpoint()
        self.state = FakeState(self.endpoint)

    def take_internal_semantic_snapshot(self) -> dict[str, object]:
        return self.state.semantic_snapshot()


class LifeThreeQueryTest(unittest.TestCase):
    def test_professional_readback_is_one_bound_read_only_query(self) -> None:
        driver = FakeDriver()
        with tempfile.TemporaryDirectory() as temp:
            result = run_professional_workforce_query(
                driver, self.manifest(), Path(temp),
                deadline=time.monotonic() + 120,
            )
            self.assertTrue((Path(temp) / f"{PROFESSIONAL_STEP}.json").exists())
        self.assertEqual(result["status"], "professional_workforce_observed")
        self.assertEqual(result["steps"][0]["native_legal"], True)
        self.assertEqual(result["gameplay_actions"], 0)
        self.assertFalse(result["date_advanced"])
        self.assertEqual(
            [item["step"] for item in driver.endpoint.sent],
            [PROFESSIONAL_STEP],
        )
        self.assertEqual(result["starting_frame"], result["ending_frame"])

    def test_professional_native_denial_and_unavailable_remain_distinct(self) -> None:
        driver = FakeDriver()
        driver.state.professional_status = "observed_native_illegal"
        with tempfile.TemporaryDirectory() as temp:
            result = run_professional_workforce_query(
                driver, self.manifest(), Path(temp),
                deadline=time.monotonic() + 120,
            )
        self.assertEqual(result["status"], "professional_workforce_observed")
        self.assertFalse(result["steps"][0]["native_legal"])
        driver.state.professional_status = "unavailable_state"
        with tempfile.TemporaryDirectory() as temp:
            result = run_professional_workforce_query(
                driver, self.manifest(), Path(temp),
                deadline=time.monotonic() + 120,
            )
        self.assertEqual(result["status"], "evidence_insufficient")

    def test_professional_mode_requires_explicit_runner_flag(self) -> None:
        ordinary = parser().parse_args(["--candidate-root", "Z:/candidate"])
        targeted = parser().parse_args([
            "--candidate-root", "Z:/candidate", "--professional-workforce",
        ])
        self.assertFalse(ordinary.professional_workforce)
        self.assertTrue(targeted.professional_workforce)

    def test_professional_owned_target_cannot_be_reported_legal(self) -> None:
        driver = FakeDriver()
        driver.state.professional_owned = True
        with tempfile.TemporaryDirectory() as temp:
            result = run_professional_workforce_query(
                driver, self.manifest(), Path(temp),
                deadline=time.monotonic() + 120,
            )
        self.assertEqual(result["status"], "red")
        self.assertEqual(
            result["steps"][0]["issue"], "professional_final_legality_untyped"
        )

    def test_r0146_legacy_manifest_is_rejected_before_native_commit_keyerror(
        self,
    ) -> None:
        legacy = {
            "source_repo": "Z:/legacy-python-source",
            "python_source_commit": "7" * 40,
        }
        with self.assertRaisesRegex(
            RuntimeError, "native_source_commit must be a full Git SHA"
        ):
            _manifest_source_identities(legacy)

    def test_source_identities_bind_python_and_native_commits(self) -> None:
        repo = Path(__file__).resolve().parents[3]
        native = repo / "ck3_autonomous_player"
        manifest = {
            "source_repo": str(repo),
            "python_source_commit": "7" * 40,
            "native_source_repo": str(native),
            "native_source_commit": "8" * 40,
        }
        with patch(
            "run_player_lifestyle_three_query_readback._source_commit",
            side_effect=lambda path: "7" * 40 if path == repo else "8" * 40,
        ), patch(
            "run_player_lifestyle_three_query_readback._source_dirty",
            return_value=False,
        ):
            identities = _manifest_source_identities(manifest)
        self.assertEqual(identities["python_source_commit"], "7" * 40)
        self.assertEqual(identities["native_source_commit"], "8" * 40)

    def test_prepare_mode_requires_explicit_source_and_pair_inputs(self) -> None:
        args = parser().parse_args(
            [
                "--candidate-root", "Z:/candidate", "--prepare-only",
                "--python-source-repo", "Z:/python-source",
                "--native-source-repo", "Z:/native-source",
                "--expected-python-source-commit", "7" * 40,
                "--expected-native-source-commit", "8" * 40,
                "--source-save", "Z:/pair/xar_checkpoint.ck3",
                "--source-driver", "Z:/pair/driver-state.json",
                "--expected-source-save-sha256", "a" * 64,
                "--expected-source-driver-sha256", "b" * 64,
                "--game-dir", "Z:/game", "--bridge-dll", "Z:/native/a.dll",
                "--bridge-injector", "Z:/native/i.exe",
                "--cmake-cache", "Z:/native/CMakeCache.txt",
                "--pipe", r"\\.\pipe\xar-g2-r782-ordinary-xar-off-seed",
                "--expected-actor-id", "36403",
                "--expected-date-raw", "53368176",
                "--expected-history-index", "1094",
            ]
        )
        self.assertTrue(args.prepare_only)
        self.assertFalse(args.preflight_only)
        self.assertEqual(args.expected_history_index, 1094)

    def test_ordinary_binding_matches_frozen_checkpoint(self) -> None:
        profile = {
            "rules": {"profile": [{"rule": "xar_enabled", "setting": "xar_off"}]},
            "environment_sha256": "a" * 64,
        }
        binding = _ordinary_binding(
            profile,
            {
                "succession_lifecycle": {
                    "schema": "xar.ck3.succession-lifecycle-binding/v1",
                    "lifecycle": "ordinary_campaign_succession",
                    "xar_enabled": "xar_off",
                    "pact_contract": "absent_by_fresh_campaign_xar_off_contract",
                    "source": "prepared-environment-manifest",
                    "environment_sha256": "a" * 64,
                }
            },
        )
        self.assertEqual(binding["lifecycle"], "ordinary_campaign_succession")
        with self.assertRaisesRegex(RuntimeError, "checkpoint lifecycle differs"):
            _ordinary_binding(profile, {"succession_lifecycle": None})

    def test_driver_receives_frozen_ordinary_lifecycle(self) -> None:
        spec = SimpleNamespace(
            state_dir=Path("state"), profile_dir=Path("state/profile")
        )
        binding = {"lifecycle": "ordinary_campaign_succession"}
        with patch(
            "xar_autoplayer.bridge.native_driver.NativeHeadlessGameplayDriver"
        ) as driver_type:
            driver = _new_bound_driver(spec, {"pipe": "private-test-pipe"}, binding)
        self.assertIs(driver, driver_type.return_value)
        driver_type.assert_called_once_with(
            "private-test-pipe",
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
            succession_lifecycle_binding=binding,
        )

    def test_preflight_verifies_ordinary_xar_off_profile(self) -> None:
        spec = object()
        expected = {"environment_sha256": "profile-bound"}
        with patch(
            "xar_autoplayer.environment.verify_profile", return_value=expected
        ) as verify:
            self.assertIs(_verify_ordinary_profile(spec), expected)
        verify.assert_called_once_with(spec, xar_enabled="xar_off")

    def manifest(self) -> dict[str, object]:
        return {
            "expected_actor_id": 29_829,
            "expected_date_raw": 53_178_312,
            "episode_run_id": EPISODE,
            "bounds": {"native_query_seconds": 20},
        }

    def test_three_read_only_queries_preserve_one_independent_frame(self) -> None:
        driver = FakeDriver()
        with tempfile.TemporaryDirectory() as temp:
            result = run_three_queries(
                driver,
                self.manifest(),
                Path(temp),
                deadline=time.monotonic() + 120,
            )
            self.assertTrue((Path(temp) / "paused-life2-current-state.json").exists())
            self.assertTrue((Path(temp) / f"{PERK_STEP}.json").exists())
            self.assertTrue((Path(temp) / f"{FOCUS_STEP}.json").exists())
        self.assertEqual(result["status"], "three_queries_observed")
        self.assertEqual(result["gameplay_actions"], 0)
        self.assertFalse(result["date_advanced"])
        self.assertEqual(
            [item["step"] for item in driver.endpoint.sent],
            [STATE_STEP, FOCUS_STEP, PERK_STEP],
        )
        self.assertEqual(result["starting_frame"], result["ending_frame"])
        self.assertEqual(
            _frame(driver.take_internal_semantic_snapshot())["episode_run_id"], EPISODE
        )
        self.assertNotIn("episode_run_id", life2_frame(driver.state.semantic_snapshot()))

    def test_formal_unavailable_is_not_legal_candidate_evidence(self) -> None:
        driver = FakeDriver()
        driver.state.perk_status = "unavailable"
        with tempfile.TemporaryDirectory() as temp:
            result = run_three_queries(
                driver,
                self.manifest(),
                Path(temp),
                deadline=time.monotonic() + 120,
            )
        self.assertEqual(result["status"], "evidence_insufficient")
        self.assertEqual(result["steps"][2]["status"], "native_unavailable")

    def test_focus_target_progress_unavailable_is_evidence_insufficient(self) -> None:
        driver = FakeDriver()
        driver.state.focus_progress_presence = "unavailable"
        with tempfile.TemporaryDirectory() as temp:
            result = run_three_queries(
                driver, self.manifest(), Path(temp),
                deadline=time.monotonic() + 120,
            )
        self.assertEqual(result["status"], "evidence_insufficient")
        self.assertEqual(result["steps"][1]["status"], "native_unavailable")
        self.assertNotIn("target_lifestyle_progress", result["steps"][1])
        self.assertEqual(result["gameplay_actions"], 0)
        self.assertFalse(result["date_advanced"])

    def test_focus_source_read_failure_stays_red(self) -> None:
        driver = FakeDriver()
        driver.state.focus_status = "unavailable_database"
        with tempfile.TemporaryDirectory() as temp:
            result = run_three_queries(
                driver, self.manifest(), Path(temp),
                deadline=time.monotonic() + 120,
            )
        self.assertEqual(result["status"], "red")
        self.assertEqual(result["steps"][1]["native_status"], "unavailable_database")
        self.assertEqual(
            [item["step"] for item in driver.endpoint.sent],
            [STATE_STEP, FOCUS_STEP],
        )

    def test_absent_progress_and_exact_perk_error_are_typed_unavailable(self) -> None:
        driver = FakeDriver()
        driver.state.progress_presence = "absent"
        driver.state.perk_error = "native_lifestyle_windowless_policy_perk_unavailable_state"
        with tempfile.TemporaryDirectory() as temp:
            result = run_three_queries(
                driver,
                self.manifest(),
                Path(temp),
                deadline=time.monotonic() + 120,
            )
        self.assertEqual(result["status"], "evidence_insufficient")
        self.assertEqual(
            [item["step"] for item in driver.endpoint.sent],
            [STATE_STEP, FOCUS_STEP, PERK_STEP],
        )
        self.assertEqual(
            [item["status"] for item in result["steps"]],
            ["native_unavailable", "observed", "typed_legal_unavailable"],
        )
        self.assertEqual(
            result["steps"][2]["basis"],
            "same_frame_life2_current_lifestyle_progress_absent",
        )
        self.assertNotIn("native_legal", result["steps"][2])
        self.assertEqual(result["starting_frame"], result["ending_frame"])
        self.assertEqual(result["gameplay_actions"], 0)

    def test_same_perk_error_with_progress_present_stays_red(self) -> None:
        driver = FakeDriver()
        driver.state.perk_error = "native_lifestyle_windowless_policy_perk_unavailable_state"
        with tempfile.TemporaryDirectory() as temp:
            result = run_three_queries(
                driver,
                self.manifest(),
                Path(temp),
                deadline=time.monotonic() + 120,
            )
        self.assertEqual(result["status"], "red")
        self.assertEqual(result["steps"][2]["status"], "red")

    def test_other_perk_error_with_progress_absent_stays_red(self) -> None:
        driver = FakeDriver()
        driver.state.progress_presence = "absent"
        driver.state.perk_error = "native_lifestyle_windowless_policy_perk_read_failed"
        with tempfile.TemporaryDirectory() as temp:
            result = run_three_queries(
                driver,
                self.manifest(),
                Path(temp),
                deadline=time.monotonic() + 120,
            )
        self.assertEqual(result["status"], "red")
        self.assertEqual(result["steps"][2]["status"], "red")

    def test_independent_frame_drift_is_red(self) -> None:
        driver = FakeDriver()
        source = _frame(driver.take_internal_semantic_snapshot())
        original_wait = driver.state.wait_for_command_result

        def drift(request_id: str, timeout_seconds: float) -> dict[str, object]:
            reply = original_wait(request_id, timeout_seconds)
            driver.state.frame["date_raw"] += 1
            return reply

        driver.state.wait_for_command_result = drift
        result = _query(driver, step=FOCUS_STEP, source_frame=source, timeout_seconds=20)
        self.assertEqual(result["status"], "red")
        self.assertEqual(result["issue"], "paused_frame_drift")

    def test_action_step_is_rejected_before_transport(self) -> None:
        driver = FakeDriver()
        source = _frame(driver.take_internal_semantic_snapshot())
        with self.assertRaisesRegex(RuntimeError, "non-read-only"):
            _query(driver, step="private-submit-player-lifestyle-perk-v1", source_frame=source, timeout_seconds=20)
        self.assertEqual(driver.endpoint.sent, [])


if __name__ == "__main__":
    unittest.main()
