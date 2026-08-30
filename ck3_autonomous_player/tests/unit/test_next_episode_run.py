from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.environment import EnvironmentSpec  # noqa: E402
from xar_autoplayer.errors import AgentError  # noqa: E402
import xar_autoplayer.next_episode_run as runner_module  # noqa: E402
from xar_autoplayer.runtime import NativeBridgeLaunchConfig  # noqa: E402


class NextEpisodeRunTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(
            prefix="xar-next-episode-run-"
        )
        root = Path(self.temporary.name)
        self.spec = EnvironmentSpec(root / "state", root / "game")
        self.config = NativeBridgeLaunchConfig(
            mode="native-headless",
            pipe_name=r"\\.\pipe\next-episode-test",
            dll_path=root / "xar_ck3_bridge.dll",
            injector_path=root / "xar_ck3_bridge_injector.exe",
        )
        self.config.dll_path.write_bytes(b"dll")
        self.config.injector_path.write_bytes(b"injector")
        save_dir = self.spec.profile_dir / "save games"
        save_dir.mkdir(parents=True)
        self.checkpoint_path = save_dir / "xar_checkpoint.ck3"
        self.checkpoint_path.write_bytes(b"source checkpoint")
        self.seed_path = save_dir / "xar_episode_seed.ck3"
        self.seed_path.write_bytes(b"episode seed")
        native_dir = self.spec.state_dir / "native-session"
        native_dir.mkdir(parents=True)
        self.driver_state_path = native_dir / "driver-state.json"
        self.driver_state_path.write_text("{}", encoding="utf-8")
        self.seed_metadata_path = native_dir / "episode-seed.json"
        self.seed_metadata_path.write_text("{}", encoding="utf-8")
        strategy_path = self.spec.state_dir / "strategy" / "one-life-history.json"
        strategy_path.parent.mkdir(parents=True)
        strategy_path.write_text("{}", encoding="utf-8")
        logs_dir = self.spec.profile_dir / "logs"
        logs_dir.mkdir(parents=True)
        (logs_dir / "error.log").write_text("no errors", encoding="utf-8")
        self.checkpoint = {
            "name": self.checkpoint_path.name,
            "load_save_name": "xar_checkpoint",
            "path": str(self.checkpoint_path.resolve()),
            "size": self.checkpoint_path.stat().st_size,
            "sha256": hashlib.sha256(
                self.checkpoint_path.read_bytes()
            ).hexdigest(),
            "saved_date_raw": 53_287_296,
            "history_index": 6321,
        }
        self.seed = {
            "format_version": 1,
            "name": self.seed_path.name,
            "path": str(self.seed_path.resolve()),
            "size": self.seed_path.stat().st_size,
            "sha256": hashlib.sha256(self.seed_path.read_bytes()).hexdigest(),
            "date_raw": 53_211_552,
            "character_id": 29_829,
            "source_run_id": "native-29829-source",
            "immutable": True,
            "metadata_path": str(self.seed_metadata_path.resolve()),
        }

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_success_archives_inputs_outputs_and_sidecars(self) -> None:
        core = {
            "format_version": 1,
            "kind": "ck3_native_auto_run",
            "started_at": "2026-08-30T09:00:00Z",
            "finished_at": "2026-08-30T09:01:00Z",
            "status": "next_episode_checkpointed",
            "outcome": "qualified",
            "ok": True,
            "completion_contract": "next_episode",
            "fixed_seed": self.checkpoint,
            "terminal": {"status": "verified", "score": 14.8},
            "next_episode": {
                "transition": {
                    "status": "verified",
                    "episode_run_id": "native-29829-next",
                },
                "visible_gameplay_turns": 1,
                "checkpoint": {
                    "status": "saved",
                    "episode_run_id": "native-29829-next",
                },
            },
            "first_blocker": None,
            "cleanup": {"ok": True},
        }
        with mock.patch.object(
            runner_module,
            "validate_cold_start_checkpoint_for_pipe",
            return_value=self.checkpoint,
        ), mock.patch.object(
            runner_module,
            "validate_episode_seed_for_state",
            return_value=self.seed,
        ), mock.patch.object(
            runner_module, "native_auto_run", return_value=core
        ) as auto_run:
            report = runner_module.native_next_episode_run(
                self.spec,
                max_turns=30,
                timeout_seconds=1800,
                readiness_timeout_seconds=300,
                native_bridge=self.config,
            )

        self.assertTrue(report["ok"])
        self.assertTrue(report["finalized"])
        self.assertEqual(report["kind"], "ck3_native_next_episode_run")
        self.assertEqual(report["preflight"]["episode_seed"], self.seed)
        auto_run.assert_called_once_with(
            self.spec,
            turn_count=30,
            timeout_seconds=1800,
            readiness_timeout_seconds=300,
            cold_start_checkpoint=True,
            native_bridge=self.config,
            checkpoint_every_eligible_advances=1,
            completion_contract="next_episode",
            route_contact_timeline_speed=3,
            allow_route_contact_high_speed_ab=False,
            allow_stationary_objective_hold_sentinel_canary=False,
        )
        run_dir = Path(report["run_dir"])
        persisted = json.loads(
            (run_dir / "report.json").read_text(encoding="utf-8")
        )
        self.assertTrue(persisted["ok"])
        self.assertTrue((run_dir / "terminal-settlement.json").is_file())
        self.assertTrue((run_dir / "next-episode.json").is_file())
        self.assertIn("checkpoint", report["artifacts"]["inputs"])
        self.assertIn("episode_seed", report["artifacts"]["inputs"])
        self.assertIn("checkpoint", report["artifacts"]["outputs"])
        self.assertIn("log_error_log", report["artifacts"]["outputs"])

    def test_preflight_failure_is_finalized_without_starting_ck3(self) -> None:
        with mock.patch.object(
            runner_module,
            "validate_cold_start_checkpoint_for_pipe",
            return_value=self.checkpoint,
        ), mock.patch.object(
            runner_module,
            "validate_episode_seed_for_state",
            side_effect=AgentError("episode seed bytes differ"),
        ), mock.patch.object(runner_module, "native_auto_run") as auto_run:
            report = runner_module.native_next_episode_run(
                self.spec,
                max_turns=30,
                timeout_seconds=1800,
                readiness_timeout_seconds=300,
                native_bridge=self.config,
            )

        auto_run.assert_not_called()
        self.assertFalse(report["ok"])
        self.assertTrue(report["finalized"])
        self.assertEqual(report["status"], "runner_error")
        self.assertEqual(
            report["first_blocker"]["kind"], "next_episode_runner_failed"
        )


if __name__ == "__main__":
    unittest.main()
