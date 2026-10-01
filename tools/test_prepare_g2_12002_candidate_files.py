"""New-manifest consumption and file-only dispatch checks; no game fixtures."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest import mock

import prepare_g2_12002_candidate_files as candidate
import stage_nonwar_12002_pair_files as staging
from xar_autoplayer.bridge.mcp_server import parser as mcp_parser
from xar_autoplayer.cli import parser as agent_parser


class CandidateFileTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary_root = candidate.REPO / ".task-tmp/g2-candidate-file-tests"
        temporary_root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=temporary_root)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        config = candidate.offline.read_object(candidate.CONFIG)
        flags = config["native_candidate_required_on"] + config["native_candidate_required_off"]
        builds = {}
        for label in ("selected_private", "shipping"):
            bundle = {"flags": {flag: "ON" if label == "selected_private" and
                                 flag in config["native_candidate_required_on"] else "OFF"
                                 for flag in flags}}
            for name in ("dll", "injector"):
                path = self.root / f"fake-{label}-{name}"
                path.write_bytes(f"fixture {label} {name}".encode())
                bundle[name] = {"path": str(path), "bytes": path.stat().st_size,
                                "sha256": candidate.offline.digest(path)}
            builds[label] = bundle
        self.manifest = self.root / "new-frozen-manifest.json"
        candidate.write_json(self.manifest, {
            "schema": "xar.g2.offline.central-native-build.v1",
            "source_head": "a" * 40, "build": builds})
        seed = self.root / "fake-seed-metadata"
        seed.mkdir()
        self.identity = {"game_version": "1.20.0.2", "episode_character_id": 100,
                         "episode_run_id": "fake-g2-not-live-100", "checkpoint_sha256": "c" * 64,
                         "driver_state_sha256": "d" * 64, "date_raw": 1234,
                         "history_index": 1, "pipe": r"\\.\pipe\fake_g2_file_only"}
        candidate.write_json(seed / "SEED-IDENTITY.json", self.identity)
        self.args = candidate.parser().parse_args([
            "--integration-manifest", str(self.manifest),
            "--integration-manifest-sha256", candidate.offline.digest(self.manifest),
            "--game-dir", str(self.root / "absent-game"),
            "--state-dir", str(self.root / "new-state"),
            "--canonical-seed-root", str(seed), "--output-dir", str(self.root / "new-output"),
            "--ordinary-sample-dir", str(self.root / "absent-ordinary-sample"),
            "--live-run-state-root", str(self.root / "absent-allocator")])
        self.git = mock.patch.object(candidate.subprocess, "run",
                                     return_value=mock.Mock(stdout="a" * 40 + "\n"))
        self.git.start()
        self.addCleanup(self.git.stop)

    def test_new_manifest_build_inputs_and_default_plan_do_not_prepare_profile_or_pair(self) -> None:
        with (mock.patch.object(candidate.offline, "prepare_profile_files") as core,
              mock.patch.object(staging, "stage") as pair):
            receipt = candidate.prepare(self.args)
        core.assert_not_called()
        pair.assert_not_called()
        self.assertEqual(receipt["status"], "PASS_FROZEN_BUILD_COMMAND_PLAN")
        self.assertEqual(receipt["formal_consumer_trials_enabled"], [])
        self.assertEqual(len([flag for flag, value in receipt["selected_private_flags"].items()
                              if value == "ON"]), 40)
        self.assertFalse(self.args.state_dir.exists())
        self.assertFalse(self.args.game_dir.exists())
        self.assertFalse(self.args.live_run_state_root.exists())
        ordinary = candidate.offline.read_object(self.args.output_dir / "ordinary-plan-only/operator-manifest.json")
        self.assertNotEqual(Path(ordinary["state_dir"]), self.args.state_dir)
        plan = candidate.offline.read_object(self.args.output_dir / "rogue/OFFLINE-RUNNER-PLAN.json")
        self.assertTrue(plan["frozen_native_build"]["binary_files_read_or_verified"])
        self.assertEqual(receipt["g2_completed_increment"], 0)

    def test_explicit_mode_prepares_rogue_profile_then_preserves_pair_and_skips_next_prepare(self) -> None:
        self.args.prepare_profile_files = True
        calls = []

        def profile_core(parsed, manifest):
            calls.append("profile")
            self.assertEqual(manifest["xar_enabled"], "xar_on")
            env_path = self.args.state_dir / "profile/xar-autoplayer-environment.json"
            env_path.parent.mkdir(parents=True)
            candidate.write_json(env_path, {"environment_sha256": "e" * 64,
                                 "agent_runtime": {"sha256": "f" * 64},
                                 "mod": {"production_tree_sha256": "1" * 64,
                                         "production_file_count": 86}})
            return {"status": "profile-files-prepared", "pairing_or_cold_preflight_complete": False}

        def pair_files(parsed):
            calls.append("pair")
            self.assertTrue(parsed.into_prepared_profile)
            self.assertEqual(parsed.expected_episode_run_id, self.identity["episode_run_id"])
            self.assertEqual(parsed.pipe, self.identity["pipe"])
            candidate.write_json(self.args.state_dir / "SEED-IDENTITY.json", self.identity)
            receipt = {"status": "PASS_STATIC_FILE_PAIR", "fixture_only": True}
            candidate.write_json(self.args.state_dir / "PAIR-FILES-QUALIFICATION.json", receipt)
            return receipt

        with (mock.patch.object(candidate.offline, "prepare_profile_files", side_effect=profile_core),
              mock.patch.object(staging, "stage", side_effect=pair_files)):
            receipt = candidate.prepare(self.args)
        self.assertEqual(calls, ["profile", "pair"])
        self.assertEqual(receipt["status"], "PASS_STATIC_PROFILE_AND_FILE_PAIR")
        self.assertFalse(receipt["ordinary_state_prepared"])
        self.assertFalse(receipt["official_zero_process_preflight_completed"])
        self.assertFalse(receipt["real_game_cold_restore_completed"])
        self.assertEqual(receipt["robert_durable_days_increment"], 0)
        phases = candidate.offline.read_object(self.args.output_dir / "NEXT-LIVE-PHASES.json")
        self.assertNotIn("official-prepare-and-pair", [row["id"] for row in phases["commands"]])
        self.assertTrue(phases["next_episode_requires_verified_terminal_settlement"])

    def test_query_permits_parse_on_real_mcp_cli_without_enabling_formal_action(self) -> None:
        candidate.prepare(self.args)
        query = candidate.offline.read_object(self.args.output_dir / "MCP-READONLY-NEXT-PLAN.json")
        parsed = mcp_parser().parse_args(query["argv"][3:])
        self.assertEqual(parsed.driver, "native-headless")
        self.assertEqual(parsed.transport, "stdio")
        self.assertEqual(parsed.pipe_name, self.identity["pipe"])
        self.assertTrue(parsed.private_council_query)
        self.assertTrue(parsed.private_faction_gift_query)
        self.assertFalse(parsed.private_faction_gift_action)
        self.assertFalse(parsed.private_council_action)
        self.assertFalse(parsed.private_realm_law_crown_action)
        self.assertFalse(parsed.private_active_scheme_sway_action)
        self.assertTrue(parsed.private_active_scheme_sway_query)
        self.assertTrue(parsed.private_realm_law_paused_query)
        self.assertTrue(parsed.private_government_runtime_adapter_query)
        self.assertTrue(parsed.private_prisoner_collection_query)
        self.assertTrue(parsed.private_activity_feast_queries)
        self.assertTrue(parsed.private_family_obligations_query)
        self.assertFalse(query["formal_action_permits_enabled"])

    def test_supervised_cold_session_uses_real_cli_without_autonomous_lifetime(self) -> None:
        candidate.prepare(self.args)
        session = candidate.offline.read_object(self.args.output_dir / "PAUSED-MCP-SUPERVISION-PLAN.json")
        parsed = agent_parser().parse_args(session["session_argv"][3:])
        self.assertEqual(parsed.command, "native-session")
        self.assertTrue(parsed.cold_start_checkpoint)
        self.assertEqual(parsed.xar_enabled, "xar_on")
        self.assertEqual(parsed.timeout, 3600)
        phases = candidate.offline.read_object(self.args.output_dir / "NEXT-LIVE-PHASES.json")
        ids = [row["id"] for row in phases["commands"]]
        self.assertIn("root-supervised-cold-native-session", ids)
        self.assertNotIn("full-lifetime", ids)
        self.assertNotIn("next-episode-after-settlement", ids)

    def test_r2_config_adds_only_readonly_religion_permit_to_41_flag_candidate(self) -> None:
        self.args.config = candidate.REPO / "ck3_autonomous_player/configs/ck3-1.20.0.2-g2-religion-readonly-runner.json"
        config = candidate.offline.read_object(self.args.config)
        manifest = candidate.offline.read_object(self.manifest)
        new_flag = "XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1"
        manifest["build"]["selected_private"]["flags"][new_flag] = "ON"
        manifest["build"]["shipping"]["flags"][new_flag] = "OFF"
        candidate.write_json(self.manifest, manifest)
        self.args.integration_manifest_sha256 = candidate.offline.digest(self.manifest)
        receipt = candidate.prepare(self.args)
        self.assertEqual(len(config["native_candidate_required_on"]), 41)
        self.assertEqual(len(config["native_candidate_required_off"]), 4)
        self.assertEqual(receipt["formal_consumer_trials_enabled"], [])
        query = candidate.offline.read_object(self.args.output_dir / "MCP-READONLY-NEXT-PLAN.json")
        parsed = mcp_parser().parse_args(query["argv"][3:])
        self.assertTrue(parsed.private_player_religion_context_query)
        self.assertFalse(parsed.private_faction_gift_action)
        self.assertFalse(parsed.private_council_action)
        self.assertFalse(parsed.private_realm_law_crown_action)
        self.assertFalse(parsed.private_active_scheme_sway_action)
        self.assertFalse(query["formal_action_permits_enabled"])
        supervision = candidate.offline.read_object(self.args.output_dir / "PAUSED-MCP-SUPERVISION-PLAN.json")
        self.assertTrue(supervision["religion_context_read_query_wired"])
        self.assertFalse(supervision["religion_research_authorized_but_not_yet_wired"])
        self.assertFalse(supervision["war_private_permits_added"])
        self.assertTrue(supervision["native_session_has_no_autonomous_policy_loop"])


if __name__ == "__main__":
    unittest.main()
