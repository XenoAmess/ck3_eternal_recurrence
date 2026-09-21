from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT / "src"
RESEARCH_ROOT = ROOT / "native_bridge" / "research"
for candidate in (PACKAGE_ROOT, RESEARCH_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

SCRIPT = RESEARCH_ROOT / "run_gen034_d_candidate_continuation.py"
SPEC = importlib.util.spec_from_file_location(
    "gen034_d_candidate_continuation_tested", SCRIPT
)
assert SPEC is not None and SPEC.loader is not None
RUNNER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUNNER
SPEC.loader.exec_module(RUNNER)

from xar_autoplayer.environment import EnvironmentSpec  # noqa: E402


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class Gen034DCandidateContinuationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(
            prefix="xar-gen034-d-continuation-"
        )
        self.root = Path(self.temporary.name)
        self.source_capture = self.root / "source-capture.json"
        self.source_checkpoint = self.root / "source-checkpoint.ck3"
        self.source_driver = self.root / "source-driver.json"
        self.source_capture.write_text("{}\n", encoding="utf-8")
        self.source_checkpoint.write_bytes(b"opaque-checkpoint" * 32)
        self.pipe_name = r"\\.\pipe\gen034-d-continuation-test"
        self.source_driver.write_text(
            json.dumps(
                {
                    "format_version": 2,
                    "pipe_name": self.pipe_name,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        self.profile_settings = self.root / "pdx_settings.txt"
        self.profile_settings.write_text("settings", encoding="utf-8")
        self.manifest = self.root / "live-manifest.json"
        self.manifest.write_text("{}\n", encoding="utf-8")
        self.runtime_manifest = self.root / "runtime-manifest.json"
        self.runtime_manifest.write_text("{}\n", encoding="utf-8")
        self.expected_war_id = 16_777_285
        self.attempt = self.root / "attempt-01"
        self.args = argparse.Namespace(
            attempt_dir=self.attempt,
            manifest=self.manifest,
            runtime_root=RUNNER.REPOSITORY_ROOT,
            source_capture=self.source_capture,
            expected_source_capture_sha256=_sha256(self.source_capture),
            source_checkpoint=self.source_checkpoint,
            expected_checkpoint_sha256=_sha256(self.source_checkpoint),
            source_driver_state=self.source_driver,
            expected_driver_state_sha256=_sha256(self.source_driver),
            expected_war_id=self.expected_war_id,
            profile_settings_template=self.profile_settings,
            expected_profile_settings_sha256="B" * 64,
            expected_shadercache_tree_sha256="C" * 64,
            game_root=None,
            game_executable=None,
            bookmark_events=None,
            capture_executable=None,
            bridge_dll=None,
            bridge_injector=None,
            candidate_turn_limit=256,
            candidate_timeout=1800.0,
            readiness_timeout=720.0,
            execute_terminal_action=False,
            authorize_private_live=True,
        )
        self.paths = RUNNER.adapter.AdapterPaths(
            game_executable=self.root / "game" / "binaries" / "ck3.exe",
            capture_executable=self.root / "capture.exe",
            bridge_dll=self.root / "xar_ck3_bridge.dll",
            bridge_injector=self.root / "xar_ck3_bridge_injector.exe",
            bookmark_events=self.root / "game" / "events" / "bookmark_events.txt",
        )
        self.timeouts = RUNNER.adapter.AdapterTimeouts(
            process_discovery_seconds=30.0,
            main_menu_seconds=30,
            main_menu_stage_seconds=(30,),
            private_attach_seconds=30.0,
            map_hud_seconds=30.0,
            natural_event_seconds=30.0,
            observer_timeout_ms=30_000,
            post_selection_seconds=30.0,
            bridge_attach_seconds=30.0,
        )
        self.checked = {
            "runtime_manifest": {
                "path": str(self.runtime_manifest),
                "sha256": "A" * 64,
            }
        }
        self.spec = EnvironmentSpec(
            self.attempt.with_name(f"{self.attempt.name}-formal-state"),
            self.root / "game",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _normalized(self, war_id: int | None = None) -> dict[str, object]:
        return {
            "status": "normalized_private_capture",
            "source_set": {
                "war_id": self.expected_war_id if war_id is None else war_id,
            },
        }

    def _happy_candidate(self) -> dict[str, object]:
        return {
            "ok": True,
            "status": "candidate_terminal_intercepted",
            "outcome": "candidate_intercepted",
            "candidate_interception": {},
        }

    def _happy_same_session_candidate(self) -> dict[str, object]:
        return {
            "ok": True,
            "status": "candidate_terminal_resolved",
            "outcome": "candidate_resolved",
            "candidate_interception": {},
            "first_blocker": None,
            "error": None,
            "cleanup": {"ok": True},
            "candidate_resolution": {
                "ok": True,
                "status": "verified",
                "route": "surrender",
                "exit_action_commands": [
                    f"surrender-war-{self.expected_war_id}"
                ],
                "checks": {
                    "exactly_one_exit_action": True,
                    "checkpoint_cold_restore_verified": True,
                },
                "postcondition": {
                    "status": "verified",
                    "action_submitted": True,
                    "postcondition_verified": True,
                    "checkpoint_cold_restore_verified": True,
                    "gen034_closed": True,
                    "blockers": [],
                },
                "gen034_closed": True,
            },
        }

    def _patches(
        self,
        *,
        candidate_report: dict[str, object] | None = None,
        normalized: dict[str, object] | None = None,
        native_side_effect: object | None = None,
    ) -> contextlib.ExitStack:
        stack = contextlib.ExitStack()
        stack.enter_context(
            mock.patch.object(
                RUNNER,
                "_clean_runtime_root",
                return_value={
                    "status": "clean",
                    "path": str(RUNNER.REPOSITORY_ROOT),
                    "git_revision": "1" * 40,
                    "repo_root_equals_runtime_root": True,
                },
            )
        )
        stack.enter_context(
            mock.patch.object(
                RUNNER.adapter,
                "_load_manifest",
                return_value=(
                    {"schema": "fixture-live-manifest"},
                    self.paths,
                    self.timeouts,
                    self.checked,
                ),
            )
        )
        stack.enter_context(
            mock.patch.object(
                RUNNER,
                "normalize_raiktor_source_specific_capture",
                return_value=normalized or self._normalized(),
            )
        )
        stack.enter_context(
            mock.patch.object(
                RUNNER.action_runner,
                "_load_source_capture",
                return_value={},
            )
        )
        stack.enter_context(
            mock.patch.object(
                RUNNER.adapter,
                "prepare_formal_candidate_state",
                return_value=(
                    self.spec,
                    {
                        "status": "GREEN",
                        "native_auto_run_ready": True,
                    },
                ),
            )
        )
        stack.enter_context(
            mock.patch.object(
                RUNNER,
                "validate_cold_start_checkpoint_for_pipe",
                return_value={"status": "valid-cold-checkpoint"},
            )
        )
        stack.enter_context(
            mock.patch.object(
                RUNNER.adapter,
                "verify_runtime_file_manifest",
                return_value={"status": "verified"},
            )
        )
        if native_side_effect is None:
            stack.enter_context(
                mock.patch.object(
                    RUNNER.adapter,
                    "native_auto_run",
                    return_value=candidate_report or self._happy_candidate(),
                )
            )
        else:
            stack.enter_context(
                mock.patch.object(
                    RUNNER.adapter,
                    "native_auto_run",
                    side_effect=native_side_effect,
                )
            )
        stack.enter_context(
            mock.patch.object(
                RUNNER.adapter,
                "_freeze_action_runner_input",
                return_value={
                    "status": "frozen-before-terminal-submit",
                    "action_submitted": False,
                },
            )
        )
        return stack

    def test_happy_path_reuses_frozen_inputs_and_freezes_action_runner(self) -> None:
        before = {
            "capture": self.source_capture.read_bytes(),
            "checkpoint": self.source_checkpoint.read_bytes(),
            "driver": self.source_driver.read_bytes(),
        }
        with self._patches() as stack:
            load_manifest = RUNNER.adapter._load_manifest
            verify_runtime = RUNNER.adapter.verify_runtime_file_manifest
            prepare = RUNNER.adapter.prepare_formal_candidate_state
            freeze = RUNNER.adapter._freeze_action_runner_input
            native = RUNNER.adapter.native_auto_run
            report, exit_code = RUNNER.run_continuation(self.args)

            self.assertEqual(exit_code, 0)
            self.assertEqual(report["status"], "CANDIDATE_FROZEN")
            self.assertTrue(report["source_immutability"]["all_unchanged"])
            self.assertFalse(report["boundaries"]["natural_event_repeated"])
            self.assertFalse(report["boundaries"]["terminal_action_submitted"])
            self.assertTrue(report["boundaries"]["action_runner_input_ready"])
            self.assertEqual(
                json.loads((self.attempt / "report.json").read_text())["status"],
                "CANDIDATE_FROZEN",
            )
            self.assertTrue(
                (self.attempt / "candidate-native-auto-run-report.json").is_file()
            )
            self.assertEqual(self.source_capture.read_bytes(), before["capture"])
            self.assertEqual(self.source_checkpoint.read_bytes(), before["checkpoint"])
            self.assertEqual(self.source_driver.read_bytes(), before["driver"])
            load_manifest.assert_called_once()
            self.assertEqual(
                load_manifest.call_args.kwargs["repo_root"],
                RUNNER.REPOSITORY_ROOT.resolve(),
            )
            self.assertEqual(
                load_manifest.call_args.kwargs["runtime_root"],
                RUNNER.REPOSITORY_ROOT.resolve(),
            )
            verify_runtime.assert_called_once_with(
                self.runtime_manifest.resolve(),
                runtime_root=RUNNER.REPOSITORY_ROOT.resolve(),
                expected_manifest_sha256="A" * 64,
            )
            self.assertEqual(
                prepare.call_args.kwargs["source_checkpoint"],
                (self.attempt / "inputs" / "xar_checkpoint.ck3").resolve(),
            )
            freeze.assert_called_once()
            self.assertEqual(
                freeze.call_args.kwargs["profile_settings_template"],
                self.profile_settings,
            )
            self.assertEqual(
                freeze.call_args.kwargs["expected_profile_settings_sha256"],
                "B" * 64,
            )
            self.assertEqual(
                freeze.call_args.kwargs["expected_shadercache_tree_sha256"],
                "C" * 64,
            )
            self.assertEqual(
                native.call_args.kwargs["readiness_timeout_seconds"],
                720.0,
            )
            self.assertIsNone(native.call_args.kwargs["after_intercept"])
            stack.close()

    def test_same_session_mode_closes_without_freezing_second_runner(self) -> None:
        self.args.execute_terminal_action = True
        resolved = self._happy_same_session_candidate()
        with self._patches(candidate_report=resolved):
            freeze = RUNNER.adapter._freeze_action_runner_input
            native = RUNNER.adapter.native_auto_run
            report, exit_code = RUNNER.run_continuation(self.args)

        self.assertEqual(exit_code, 0)
        self.assertEqual(report["status"], "GEN034_CLOSED")
        self.assertTrue(report["boundaries"]["terminal_action_submitted"])
        self.assertFalse(report["boundaries"]["action_runner_input_ready"])
        self.assertTrue(report["boundaries"]["gen034_closed"])
        self.assertEqual(
            report["candidate_resolution"]["route"], "surrender"
        )
        self.assertTrue(callable(native.call_args.kwargs["after_intercept"]))
        freeze.assert_not_called()

    def test_same_session_malformed_green_is_rejected(self) -> None:
        self.args.execute_terminal_action = True
        malformed = self._happy_same_session_candidate()
        malformed["candidate_resolution"]["postcondition"][
            "checkpoint_cold_restore_verified"
        ] = False

        with self._patches(candidate_report=malformed):
            report, exit_code = RUNNER.run_continuation(self.args)

        self.assertEqual(exit_code, 2)
        self.assertEqual(report["status"], "RED")
        self.assertIn("complete same-session", report["error"])
        self.assertTrue(report["boundaries"]["terminal_action_submitted"])
        self.assertFalse(report["boundaries"]["gen034_closed"])

    def test_same_session_red_does_not_claim_unknown_submission_state(self) -> None:
        self.args.execute_terminal_action = True
        failed = {
            "ok": False,
            "status": "stopped_on_error",
            "outcome": "failed",
            "candidate_interception": {},
            "candidate_resolution": {
                "ok": False,
                "status": "red",
                "sequence_error": "fixture-red",
                "gen034_closed": False,
            },
        }
        with self._patches(candidate_report=failed):
            report, exit_code = RUNNER.run_continuation(self.args)

        self.assertEqual(exit_code, 2)
        self.assertEqual(report["status"], "RED")
        self.assertIsNone(report["boundaries"]["terminal_action_submitted"])
        self.assertFalse(report["boundaries"]["gen034_closed"])

    def test_same_session_native_exception_keeps_submission_unknown(self) -> None:
        self.args.execute_terminal_action = True

        with self._patches(native_side_effect=RuntimeError("fixture crash")):
            report, exit_code = RUNNER.run_continuation(self.args)

        self.assertEqual(exit_code, 2)
        self.assertEqual(report["status"], "RED")
        self.assertIsNone(report["candidate_native_auto_run"])
        self.assertIsNone(report["boundaries"]["terminal_action_submitted"])
        self.assertFalse(report["boundaries"]["gen034_closed"])

    def test_candidate_timeout_must_exceed_readiness_timeout(self) -> None:
        self.args.candidate_timeout = 600.0

        with self.assertRaisesRegex(
            RUNNER.ContinuationError,
            "candidate timeout must be greater than readiness timeout",
        ):
            RUNNER.run_continuation(self.args)

        self.assertFalse(self.attempt.exists())

    def test_candidate_red_is_persisted_and_never_freezes_action_input(self) -> None:
        failed = {
            "ok": False,
            "status": "failed",
            "outcome": "session_exit",
            "blocker": "fixture-session-exit",
        }
        with self._patches(candidate_report=failed):
            freeze = RUNNER.adapter._freeze_action_runner_input
            report, exit_code = RUNNER.run_continuation(self.args)

            self.assertEqual(exit_code, 2)
            self.assertEqual(report["status"], "RED")
            self.assertIn("fixture-session-exit", report["error"])
            self.assertFalse(report["boundaries"]["action_runner_input_ready"])
            persisted_candidate = json.loads(
                (self.attempt / "candidate-native-auto-run-report.json").read_text()
            )
            self.assertEqual(persisted_candidate, failed)
            self.assertEqual(
                json.loads((self.attempt / "report.json").read_text())["status"],
                "RED",
            )
            freeze.assert_not_called()

    def test_capture_war_id_mismatch_blocks_before_formal_state(self) -> None:
        with self._patches(normalized=self._normalized(self.expected_war_id + 1)):
            prepare = RUNNER.adapter.prepare_formal_candidate_state
            native = RUNNER.adapter.native_auto_run
            report, exit_code = RUNNER.run_continuation(self.args)

            self.assertEqual(exit_code, 2)
            self.assertEqual(report["status"], "RED")
            self.assertIn("WarID differs", report["error"])
            prepare.assert_not_called()
            native.assert_not_called()

    def test_source_mutation_after_native_run_blocks_action_input_freeze(self) -> None:
        def mutate_source(*_args: object, **_kwargs: object) -> dict[str, object]:
            self.source_checkpoint.write_bytes(b"mutated")
            return self._happy_candidate()

        with self._patches(native_side_effect=mutate_source):
            freeze = RUNNER.adapter._freeze_action_runner_input
            report, exit_code = RUNNER.run_continuation(self.args)

            self.assertEqual(exit_code, 2)
            self.assertEqual(report["status"], "RED")
            self.assertIn("frozen source files changed", report["error"])
            self.assertFalse(report["source_immutability"]["all_unchanged"])
            self.assertTrue(
                (self.attempt / "candidate-native-auto-run-report.json").is_file()
            )
            freeze.assert_not_called()

    def test_same_session_resolver_revalidates_and_executes_live_frame(self) -> None:
        authorization_sha256 = "D" * 64
        interception = {
            "selected_step": f"surrender-war-{self.expected_war_id}",
            "plan": {
                "war_exit_decision": {
                    "war_id": self.expected_war_id,
                    "opponent_character_id": 35_991,
                    "recommended_outcome": "surrender",
                }
            },
            "after_checkpoint": {
                "played_character": {"character_id": 29_829},
                "date_raw": 53_190_816,
            },
        }
        source = {"schema": "fixture-source"}
        with mock.patch.object(
            RUNNER,
            "terminal_authorization_v1",
            return_value={
                "payload": {
                    "selected_step": interception["selected_step"],
                    "recommended_outcome": "surrender",
                },
                "sha256": authorization_sha256,
            },
        ), mock.patch.object(
            RUNNER.action_runner,
            "_run_mcp_sequence",
            new=mock.AsyncMock(
                return_value={
                    "ok": True,
                    "status": "verified",
                    "gen034_closed": True,
                }
            ),
        ) as run_sequence:
            resolver = RUNNER._same_session_terminal_resolver(
                expected_war_id=self.expected_war_id,
                source_capture=source,
                source_capture_sha256="A" * 64,
                runtime_manifest=self.runtime_manifest,
                runtime_root=RUNNER.REPOSITORY_ROOT,
                expected_runtime_manifest_sha256="B" * 64,
            )
            result = resolver(object(), interception)

        self.assertTrue(result["ok"])
        self.assertEqual(
            result["candidate_authorization"]["sha256"],
            authorization_sha256,
        )
        self.assertEqual(
            run_sequence.await_args.kwargs["expected_terminal_step"],
            interception["selected_step"],
        )
        self.assertEqual(
            run_sequence.await_args.kwargs["expected_character_id"], 29_829
        )


if __name__ == "__main__":
    unittest.main()
