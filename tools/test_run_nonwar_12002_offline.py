"""Fake-only checks for reusable operator/lifetime argv preparation."""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

import g2_preview_operator as operator
import run_nonwar_12002_offline as offline

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "ck3_autonomous_player/src"))
from xar_autoplayer.cli import parser as agent_parser  # noqa: E402
from xar_autoplayer import environment  # noqa: E402


class OfflineRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        temp_root = REPO / ".task-tmp" / "nonwar-offline-runner-tests"
        temp_root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=temp_root)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def argv(self, lane: str = "ordinary") -> list[str]:
        return ["--lane", lane, "--source-repo", str(REPO),
                "--python", sys.executable,
                "--game-dir", str(self.root / "nonexistent-game"),
                "--state-dir", str(self.root / "nonexistent-state"),
                "--dll", str(self.root / "absent-bridge.dll"),
                "--injector", str(self.root / "absent-injector.exe"),
                "--sample-dir", str(self.root / "nonexistent-sample"),
                "--output-dir", str(self.root / "metadata"),
                "--live-run-state-root", str(self.root / "nonexistent-allocator"),
                "--pipe", r"\\.\pipe\xar_nonwar_offline_fake",
                "--dll-sha256", "a" * 64, "--injector-sha256", "b" * 64]

    def test_ordinary_uses_official_prepare_rebind_and_formal_run(self) -> None:
        manifest, result = offline.plan(offline.parser().parse_args(self.argv()))
        self.assertEqual(manifest["xar_enabled"], "xar_off")
        self.assertTrue(manifest["ordinary_campaign_no_pact"])
        prepare, run = result["commands"]
        prepare_args = operator.parser().parse_args(prepare["argv"][3:])
        run_args = operator.parser().parse_args(run["argv"][3:])
        self.assertEqual(prepare_args.handler, operator.command_prepare_state)
        self.assertEqual(run_args.handler, operator.command_run)
        self.assertEqual(run_args.turns, 20)
        self.assertFalse(run_args.private_family_marriage_formal_trial)
        self.assertFalse(run_args.private_lifestyle_formal_trial)
        self.assertFalse(result["historical_robert_continuation"])
        self.assertEqual(result["history"]["robert_durable_days"], 3153)
        self.assertEqual(result["history"]["robert_checkpoint_history"], 4025)
        self.assertEqual(result["new_g2_completed"], 0)
        self.assertEqual(result["new_durable_days"], 0)

    def test_rogue_matches_real_preflight_lifetime_and_next_episode_cli(self) -> None:
        seed = self.root / "seed-identity.json"
        seed.write_text(json.dumps({"game_version": "1.20.0.2",
                                   "episode_character_id": 100,
                                   "episode_run_id": "fake-not-live-100",
                                   "checkpoint_sha256": "c" * 64,
                                   "driver_state_sha256": "d" * 64}), encoding="utf-8")
        args = offline.parser().parse_args([*self.argv("rogue"),
                                            "--seed-identity", str(seed)])
        manifest, result = offline.plan(args)
        self.assertEqual(manifest["xar_enabled"], "xar_on")
        commands = {row["id"]: row for row in result["commands"]}
        for label, expected in (("exact-lifetime-preflight", "native-one-generation-preflight"),
                                ("full-lifetime", "native-one-generation"),
                                ("next-episode-after-settlement", "native-next-episode")):
            parsed = agent_parser().parse_args(commands[label]["argv"][3:])
            self.assertEqual(parsed.command, expected)
            self.assertEqual(parsed.bridge_mode, "native-headless")
        parsed = agent_parser().parse_args(commands["exact-lifetime-preflight"]["argv"][3:])
        self.assertEqual(parsed.expected_character_id, 100)
        self.assertEqual(parsed.succession_lifecycle, "rogue_one_life")
        self.assertEqual(len([row for row in result["commands"] if row.get("writes_live_allocator")]), 2)
        self.assertEqual(result["open_kaishek_precheck"]["status"], "not-applicable")

    def test_metadata_write_never_reads_or_creates_game_pair_state_or_allocator(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(offline.main(self.argv()), 0)
        for name in ("nonexistent-game", "nonexistent-state", "nonexistent-sample",
                     "nonexistent-allocator", "absent-bridge.dll", "absent-injector.exe"):
            self.assertFalse((self.root / name).exists(), name)
        result = offline.read_object(self.root / "metadata/OFFLINE-RUNNER-PLAN.json")
        self.assertFalse(result["actual_ck3_access"])
        self.assertFalse(result["actual_save_or_driver_read_or_copied"])
        self.assertFalse(result["ck3_launch_attempted"])
        self.assertEqual(result["status"], "static-ready-command-plan")
        manifest = operator.load_manifest(self.root / "metadata/operator-manifest.json")
        self.assertEqual(manifest["game_version"], "1.20.0.2")

    def test_legacy_seed_cannot_be_relabelled_as_new_lifetime(self) -> None:
        seed = self.root / "historical-robert-metadata.json"
        seed.write_text(json.dumps({"game_version": "1.19.0.6"}), encoding="utf-8")
        args = offline.parser().parse_args([*self.argv("rogue"),
                                            "--seed-identity", str(seed)])
        with self.assertRaisesRegex(ValueError, "1.20.0.2 pair"):
            offline.plan(args)

    def test_incomplete_lane_cannot_silently_change_lifecycle(self) -> None:
        config = offline.read_object(offline.CONFIG)
        config["ordinary"]["xar_enabled"] = "xar_on"
        path = self.root / "bad-config.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        args = offline.parser().parse_args([*self.argv(), "--config", str(path)])
        with self.assertRaisesRegex(ValueError, "lifecycle fields"):
            offline.plan(args)

    def test_file_only_mode_uses_existing_core_without_process_inventory_or_pair_copy(self) -> None:
        prepared = {
            "profile_dir": str(self.root / "nonexistent-state/profile"),
            "environment_sha256": "e" * 64,
            "game": {"executable_sha256": offline.read_object(offline.CONFIG)["game_executable_sha256"]},
            "mod": {"production_tree_sha256": "f" * 64},
        }
        with (mock.patch.object(environment, "_prepare_profile_locked", return_value=prepared) as core,
              mock.patch.object(environment, "ck3_processes", side_effect=RuntimeError("process access forbidden")),
              mock.patch.object(environment, "ck3_process_inventory", side_effect=RuntimeError("process access forbidden")),
              contextlib.redirect_stdout(io.StringIO())):
            self.assertEqual(offline.main([*self.argv(), "--prepare-profile-files"]), 0)
        self.assertEqual(core.call_count, 1)
        spec = core.call_args.args[0]
        self.assertEqual(spec.expected_game_version, "1.20.0.2")
        self.assertEqual(core.call_args.kwargs["xar_enabled"], "xar_off")
        self.assertFalse((self.root / "nonexistent-sample").exists())
        self.assertFalse((self.root / "nonexistent-state/native-session/driver-state.json").exists())
        result = offline.read_object(self.root / "metadata/OFFLINE-RUNNER-PLAN.json")
        self.assertTrue(result["actual_profile_prepared"])
        self.assertFalse(result["profile_file_preparation"]["pairing_or_cold_preflight_complete"])
        self.assertFalse(result["profile_file_preparation"]["process_inventory_called"])

    def test_file_only_mode_does_not_refresh_an_existing_state(self) -> None:
        args = offline.parser().parse_args(self.argv())
        args.state_dir.mkdir()
        manifest, _ = offline.plan(args)
        with mock.patch.object(environment, "_prepare_profile_locked") as core:
            with self.assertRaisesRegex(ValueError, "fresh nonexistent"):
                offline.prepare_profile_files(args, manifest)
        core.assert_not_called()


if __name__ == "__main__":
    unittest.main()
