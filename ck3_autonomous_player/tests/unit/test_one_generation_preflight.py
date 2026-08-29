from __future__ import annotations

import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer import cli  # noqa: E402
from xar_autoplayer.environment import EnvironmentSpec  # noqa: E402
from xar_autoplayer.one_generation_preflight import (  # noqa: E402
    native_one_generation_preflight,
)
import xar_autoplayer.one_generation_preflight as preflight_module  # noqa: E402


class NativeOneGenerationPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(
            prefix="xar-one-generation-preflight-"
        )
        root = Path(self.temporary.name)
        self.spec = EnvironmentSpec(root / "state", root / "game")
        self.pipe_name = r"\\.\pipe\one-generation-preflight-test"
        self.character_id = 29_829
        self.episode_run_id = "native-29829-fixture"
        self.checkpoint_sha256 = "a" * 64
        self.driver_path = (
            self.spec.state_dir / "native-session" / "driver-state.json"
        )
        self.driver_path.parent.mkdir(parents=True)
        self.driver_path.write_text(
            json.dumps(
                {
                    "format_version": 2,
                    "pipe_name": self.pipe_name,
                    "bridge_pid": 4_242,
                    "episode_character_id": self.character_id,
                    "episode_run_id": self.episode_run_id,
                    "command_history": [],
                }
            ),
            encoding="utf-8",
        )
        self.driver_sha256 = hashlib.sha256(
            self.driver_path.read_bytes()
        ).hexdigest()
        self.checkpoint = {
            "name": "xar_checkpoint.ck3",
            "load_save_name": "xar_checkpoint",
            "path": str(root / "xar_checkpoint.ck3"),
            "size": 92_642_200,
            "sha256": self.checkpoint_sha256,
            "saved_date_raw": 53_279_256,
            "history_index": 6_159,
        }
        self.manifest = {
            "profile_dir": str(self.spec.profile_dir),
            "environment_sha256": "environment-hash",
            "agent_runtime": {
                "sha256": "runtime-hash",
                "git": {"selected_runtime_revision": "runtime-revision"},
            },
            "game": {"executable_sha256": "ck3-hash"},
            "mod": {"production_tree_sha256": "production-hash"},
            "rules": {"profile_sha256": "rules-hash"},
        }

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _run(self, **overrides: object) -> dict[str, object]:
        arguments: dict[str, object] = {
            "pipe_name": self.pipe_name,
            "expected_character_id": self.character_id,
            "expected_episode_run_id": self.episode_run_id,
            "expected_checkpoint_sha256": self.checkpoint_sha256.upper(),
            "expected_driver_state_sha256": self.driver_sha256.upper(),
        }
        arguments.update(overrides)
        with mock.patch.object(
            preflight_module,
            "ck3_process_inventory",
            return_value={
                "tasklist_returncode": 0,
                "tasklist_pids": [],
                "wmi_pids": [],
                "processes": [],
            },
        ), mock.patch.object(
            preflight_module,
            "verify_profile",
            return_value=self.manifest,
        ), mock.patch.object(
            preflight_module,
            "validate_cold_start_checkpoint_for_pipe",
            return_value=self.checkpoint,
        ):
            return native_one_generation_preflight(
                self.spec, **arguments
            )

    def test_green_report_binds_profile_episode_and_both_artifacts(self) -> None:
        report = self._run()

        self.assertTrue(report["ok"])
        self.assertEqual(report["status"], "ready")
        self.assertFalse(report["desktop_interaction"])
        self.assertFalse(report["ck3_launch_attempted"])
        self.assertEqual(
            report["resume_anchor"]["checkpoint"]["sha256"],
            self.checkpoint_sha256,
        )
        driver = report["resume_anchor"]["driver_state"]
        self.assertEqual(driver["sha256"], self.driver_sha256)
        self.assertEqual(driver["episode_character_id"], self.character_id)
        self.assertEqual(driver["episode_run_id"], self.episode_run_id)
        persisted = json.loads(
            Path(report["report_path"]).read_text(encoding="utf-8")
        )
        self.assertEqual(persisted, report)

    def test_expected_identity_mismatch_is_a_persisted_red(self) -> None:
        report = self._run(expected_character_id=999)

        self.assertFalse(report["ok"])
        self.assertEqual(report["status"], "blocked")
        self.assertIn("episode CharacterID differs", report["error"])
        self.assertEqual(
            report["resume_anchor"]["driver_state"][
                "episode_character_id"
            ],
            self.character_id,
        )
        persisted = json.loads(
            Path(report["report_path"]).read_text(encoding="utf-8")
        )
        self.assertEqual(persisted, report)

    def test_running_ck3_blocks_before_profile_or_checkpoint_reads(self) -> None:
        with mock.patch.object(
            preflight_module,
            "ck3_process_inventory",
            return_value={"processes": [{"pid": 123, "name": "ck3.exe"}]},
        ), mock.patch.object(
            preflight_module, "verify_profile"
        ) as profile_mock, mock.patch.object(
            preflight_module, "validate_cold_start_checkpoint_for_pipe"
        ) as checkpoint_mock:
            report = native_one_generation_preflight(
                self.spec,
                pipe_name=self.pipe_name,
                expected_character_id=self.character_id,
                expected_episode_run_id=self.episode_run_id,
                expected_checkpoint_sha256=self.checkpoint_sha256,
                expected_driver_state_sha256=self.driver_sha256,
            )

        self.assertFalse(report["ok"])
        self.assertIn("requires zero running ck3.exe", report["error"])
        self.assertEqual(
            report["process_inventory"]["processes"][0]["pid"], 123
        )
        profile_mock.assert_not_called()
        checkpoint_mock.assert_not_called()

    def test_missing_bridge_pid_is_consumer_compatible_red(self) -> None:
        payload = json.loads(self.driver_path.read_text(encoding="utf-8"))
        payload.pop("bridge_pid")
        self.driver_path.write_text(json.dumps(payload), encoding="utf-8")

        report = self._run()

        self.assertFalse(report["ok"])
        self.assertIn("not consumer-compatible", report["error"])
        self.assertIn("bridge_pid is malformed", report["error"])

    def test_corrupt_non_anchor_history_row_is_consumer_compatible_red(
        self,
    ) -> None:
        payload = json.loads(self.driver_path.read_text(encoding="utf-8"))
        payload["command_history"] = [
            {"index": 999, "command": "", "ok": "not-a-boolean"}
        ]
        self.driver_path.write_text(json.dumps(payload), encoding="utf-8")

        report = self._run()

        self.assertFalse(report["ok"])
        self.assertIn("not consumer-compatible", report["error"])
        self.assertIn("command history is malformed", report["error"])

    def test_invalid_expected_digest_is_a_persisted_red(
        self,
    ) -> None:
        report = native_one_generation_preflight(
            self.spec,
            pipe_name=self.pipe_name,
            expected_character_id=self.character_id,
            expected_episode_run_id=self.episode_run_id,
            expected_checkpoint_sha256="not-a-digest",
            expected_driver_state_sha256=self.driver_sha256,
        )

        self.assertFalse(report["ok"])
        self.assertIn(
            "expected_checkpoint_sha256 must be", report["error"]
        )
        persisted = json.loads(
            Path(report["report_path"]).read_text(encoding="utf-8")
        )
        self.assertEqual(persisted, report)

    def test_cli_dispatch_and_exit_code_follow_preflight_report(self) -> None:
        for ok, expected_code in ((True, 0), (False, 1)):
            with self.subTest(ok=ok):
                stdout = io.StringIO()
                with mock.patch.object(
                    cli, "make_spec", return_value=self.spec
                ), mock.patch.object(
                    cli,
                    "configure_native_bridge_launch_environment",
                    return_value=None,
                ) as configure_mock, mock.patch.object(
                    preflight_module,
                    "native_one_generation_preflight",
                    return_value={"ok": ok, "status": "fixture"},
                ) as preflight_mock, contextlib.redirect_stdout(stdout):
                    code = cli.main(
                        [
                            "--bridge-pipe",
                            self.pipe_name,
                            "native-one-generation-preflight",
                            "--expected-character-id",
                            str(self.character_id),
                            "--expected-episode-run-id",
                            self.episode_run_id,
                            "--expected-checkpoint-sha256",
                            self.checkpoint_sha256,
                            "--expected-driver-state-sha256",
                            self.driver_sha256,
                        ]
                    )

                self.assertEqual(code, expected_code)
                configure_mock.assert_not_called()
                preflight_mock.assert_called_once_with(
                    self.spec,
                    pipe_name=self.pipe_name,
                    expected_character_id=self.character_id,
                    expected_episode_run_id=self.episode_run_id,
                    expected_checkpoint_sha256=self.checkpoint_sha256,
                    expected_driver_state_sha256=self.driver_sha256,
                )
                self.assertIn(
                    f'"ok": {str(ok).lower()}', stdout.getvalue()
                )


if __name__ == "__main__":
    unittest.main()
