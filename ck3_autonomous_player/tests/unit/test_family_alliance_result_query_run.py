"""Focused frozen-pair admission for the private actual-alliance query."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer import cli
from xar_autoplayer.errors import AgentError
from xar_autoplayer.runtime import NativeBridgeLaunchConfig
import xar_autoplayer.family_alliance_result_query_run as subject
from xar_autoplayer.family_alliance_result_query_run import (
    bind_frozen_family_proposal,
)


class FrozenPairTest(unittest.TestCase):
    def test_selected_frozen_row_binds_material_cold_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state"
            state.mkdir()
            resolved = {
                "status": "betrothal", "material_result": True,
                "episode_run_id": "native-29829-test",
                "heir_character_id": 38822,
                "candidate_character_id": 38710,
                "source_pending": {
                    "played_character_id": 29829,
                    "episode_run_id": "native-29829-test",
                    "heir_character_id": 38822,
                    "candidate_character_id": 38710,
                },
            }
            (state / "first-heir-marriage-formal-v1.json").write_text(
                json.dumps({"schema": "xar.ck3.first-heir-marriage-formal.v1",
                            "pending": None, "resolved": resolved}), encoding="utf-8")
            report = root / "proposal.json"
            report.write_text(json.dumps({"auto_run": {"turns": [{"plan": {
                "selected_step": "submit-observed-first-heir-marriage-v1-private",
                "family_marriage_choice": {"candidate_character_id": 38710},
                "family_marriage_private_diagnostic": {
                    "selected_candidate_character_id": 38710,
                    "rows": [{"status": "available",
                              "actor_character_id": 29829,
                              "heir_character_id": 38822,
                              "candidate_character_id": 38710,
                              "recipient_character_id": 32266}],
                },
            }}]}}), encoding="utf-8")
            digest = hashlib.sha256(report.read_bytes()).hexdigest()
            bound = bind_frozen_family_proposal(
                state_dir=state, proposal_report=report,
                expected_report_sha256=digest,
                recipient_character_id=32266,
                episode_character_id=29829,
                episode_run_id="native-29829-test")
            self.assertEqual(bound["recipient_character_id"], 32266)
            self.assertEqual(bound["resolved"], resolved)
            for recipient, sha in ((32267, digest), (32266, "0" * 64)):
                with self.assertRaises(AgentError):
                    bind_frozen_family_proposal(
                        state_dir=state, proposal_report=report,
                        expected_report_sha256=sha,
                        recipient_character_id=recipient,
                        episode_character_id=29829,
                        episode_run_id="native-29829-test")
            saved = json.loads((state / "first-heir-marriage-formal-v1.json")
                               .read_text(encoding="utf-8"))
            self.assertEqual(saved["resolved"], resolved)

    def test_cli_is_explicit_query_only(self) -> None:
        args = cli.parser().parse_args([
            "--state-dir", "Z:/fixture-state", "--game-dir", "Z:/fixture-game",
            "--bridge-mode", "native-headless", "--bridge-pipe", "fixture",
            "--bridge-dll", "Z:/fixture.dll", "--bridge-injector", "Z:/fixture.exe",
            "native-query-first-heir-marriage-alliance-result-v1",
            "--cold-start-checkpoint", "--ownership-round-id", "R0999",
            "--proposal-report", "Z:/proposal.json",
            "--proposal-report-sha256", "a" * 64,
            "--recipient-character-id", "32266",
        ])
        self.assertTrue(args.cold_start_checkpoint)
        self.assertEqual(args.recipient_character_id, 32266)
        self.assertEqual(args.command,
                         "native-query-first-heir-marriage-alliance-result-v1")

    def test_managed_session_queries_once_without_date_or_action(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile = root / "profile"
            save = profile / "save games" / "xar_checkpoint.ck3"
            state = root / "native-session" / "driver-state.json"
            save.parent.mkdir(parents=True)
            state.parent.mkdir(parents=True)
            save.write_bytes(b"paired-checkpoint")
            state.write_text(json.dumps({"episode_character_id": 29829,
                                         "episode_run_id": "native-29829-test"}),
                             encoding="utf-8")
            spec = SimpleNamespace(state_dir=root, profile_dir=profile)
            config = NativeBridgeLaunchConfig(
                mode="native-headless", pipe_name=r"\\.\pipe\family-query-test",
                dll_path=root / "bridge.dll", injector_path=root / "injector.exe")
            frame = {"snapshot_id": "native:7", "revision": 8,
                     "native_revision": 7, "date_raw": 53155728,
                     "bridge_pid": 12345,
                     "paused": True, "map_ready": True,
                     "played_character": {"character_id": 29829}}
            observed = []
            driver_options = {}

            class Driver:
                def __init__(self, *args, **kwargs):
                    driver_options.update(kwargs)

                def _execute_campaign_root_context_v1_query(self, **kwargs):
                    return {"status": "available", "held_title_partition": [
                        {"primary": True, "first_heir_character_id": 38822}]}

                def query_observed_first_heir_marriage_alliance_result_private_v1(
                    self, **kwargs,
                ):
                    observed.append(kwargs)
                    return {"step": subject.QUERY_STEP, "read_only": True,
                            "advertised": False, "relationship_status": "betrothal",
                            "alliance_status": "not_allied"}

                def close(self):
                    pass

            class Service:
                def __init__(self, driver):
                    pass

                def snapshot(self):
                    return dict(frame)

            def managed_session(*args, stop_event: threading.Event, **kwargs):
                self.assertEqual(kwargs["prepared_xar_enabled"], "xar_off")
                self.assertTrue(stop_event.wait(2))
                return {"ok": True}

            with (mock.patch.object(subject, "ensure_state_path_safe"),
                  mock.patch.object(subject,
                      "validate_native_bridge_launch_config", return_value=config),
                  mock.patch.object(subject,
                      "validate_cold_start_checkpoint_for_pipe",
                      return_value={"sha256": subject._sha256(save),
                                    "succession_lifecycle": {
                                        "xar_enabled": "xar_off"}}),
                  mock.patch.object(subject, "bind_frozen_family_proposal",
                      return_value={"resolved": {"status": "betrothal"},
                                    "proposal_report": str(root / "c10.json"),
                                    "proposal_report_sha256": "a" * 64,
                                    "heir_character_id": 38822,
                                    "candidate_character_id": 38710}),
                  mock.patch.object(subject, "NativeHeadlessGameplayDriver", Driver),
                  mock.patch.object(subject, "GameplayBridgeService", Service),
                  mock.patch.object(subject, "_wait_for_readiness",
                                    return_value=frame),
                  mock.patch.object(subject, "_process_windows_minimized",
                                    return_value=True),
                  mock.patch.object(subject, "native_session",
                                    side_effect=managed_session),
                  mock.patch.object(subject, "_cleanup_report",
                                    return_value={"ok": True})):
                report = subject.query_first_heir_marriage_alliance_once(
                    spec, timeout_seconds=30, readiness_timeout_seconds=10,
                    ownership_round_id="R0999", cold_start_checkpoint=True,
                    proposal_report=root / "c10.json",
                    proposal_report_sha256="a" * 64,
                    recipient_character_id=32266, native_bridge=config,
                    readiness_stable_seconds=0)
            self.assertTrue(report["ok"])
            self.assertEqual(driver_options["succession_lifecycle_binding"],
                             {"xar_enabled": "xar_off"})
            self.assertEqual(report["query_envelope"]["alliance_status"],
                             "not_allied")
            self.assertEqual(report["before"]["frame"]["date_raw"],
                             report["after"]["frame"]["date_raw"])
            self.assertEqual(len(observed), 1)
            self.assertEqual(observed[0]["recipient_character_id"], 32266)
            self.assertGreater(observed[0]["timeout_seconds"], 0)
            self.assertLessEqual(observed[0]["timeout_seconds"], 30)


if __name__ == "__main__":
    unittest.main()
