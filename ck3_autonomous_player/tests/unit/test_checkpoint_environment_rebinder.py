from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.environment import EnvironmentSpec, sha256_file
from xar_autoplayer.errors import AgentError
from xar_autoplayer.bridge.succession_transition_contract import (
    bind_succession_lifecycle_from_environment_v1,
)
import xar_autoplayer.checkpoint_environment_rebinder as rebinder
import xar_autoplayer.one_generation_preflight as preflight


class CheckpointEnvironmentRebinderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="xar-environment-rebind-")
        root = Path(self.temporary.name)
        self.spec = EnvironmentSpec(root / "target-state", root / "game")
        self.pipe = r"\\.\pipe\checkpoint-environment-rebind-test"
        self.manifest = {
            "environment_sha256": "b" * 64,
            "rules": {"profile": [{"rule": "xar_enabled", "setting": "xar_on"}]},
        }
        source_manifest = copy.deepcopy(self.manifest)
        source_manifest["environment_sha256"] = "a" * 64
        binding = bind_succession_lifecycle_from_environment_v1(
            source_manifest, lifecycle="rogue_one_life"
        )
        self.save = self.spec.profile_dir / "save games" / "xar_checkpoint.ck3"
        self.save.parent.mkdir(parents=True)
        self.save.write_bytes(
            b"SAV0101e741a8ef0000864d\nU1\x01\x00\x03\x00\x8f\x05\x01\x00"
            + b"opaque-game-state\x00\xff" * 8
        )
        checkpoint = {
            "name": self.save.name,
            "size": self.save.stat().st_size,
            "sha256": sha256_file(self.save),
            "date_raw": 53_169_096,
            "history_index": 3,
            "episode_character_id": 29_829,
            "episode_run_id": "native-29829-fixture",
            "succession_lifecycle": copy.deepcopy(binding),
        }
        self.source = {
            "format_version": 2,
            "pipe_name": self.pipe,
            "bridge_pid": 42_424,
            "episode_character_id": 29_829,
            "episode_run_id": "native-29829-fixture",
            "last_checkpoint": copy.deepcopy(checkpoint),
            "command_history": [
                {"index": 1, "command": "pause", "ok": True, "result": {"paused": True}},
                {"index": 2, "command": "snapshot", "ok": True, "result": {"observation": "retained"}},
                {"index": 3, "command": "save-checkpoint", "ok": True, "result": {"checkpoint": copy.deepcopy(checkpoint)}},
            ],
            "succession_lifecycle": binding,
            "rollback_war_failure": None,
            "rollback_war_failures": [],
            "managed_restore_transaction": None,
            "succession_expectation": None,
            "campaign_goal": None,
        }
        self.driver = self.spec.state_dir / "native-session" / "driver-state.json"
        self.driver.parent.mkdir(parents=True)
        self.driver.write_text(json.dumps(self.source), encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _preflight(self) -> dict[str, object]:
        with (
            mock.patch.object(preflight, "ck3_process_inventory", return_value={"processes": []}),
            mock.patch.object(preflight, "verify_profile", return_value=self.manifest),
        ):
            return preflight.native_one_generation_preflight(
                self.spec, pipe_name=self.pipe, expected_character_id=29_829,
                expected_episode_run_id="native-29829-fixture",
                expected_checkpoint_sha256=sha256_file(self.save),
                expected_driver_state_sha256=sha256_file(self.driver),
            )

    def _rebind(self) -> dict[str, object]:
        with mock.patch.object(rebinder, "verify_profile", return_value=self.manifest):
            return rebinder.rebind_checkpoint_environment_v1(
                self.spec, expected_source_environment_sha256="a" * 64,
                expected_pipe_name=self.pipe,
            )

    def test_production_preflight_red_to_rebind_to_green_retains_complete_pair(self) -> None:
        save_before = hashlib.sha256(self.save.read_bytes()).hexdigest()
        before = self._preflight()
        self.assertFalse(before["ok"])
        self.assertIn("driver lifecycle differs from the prepared profile", before["error"])
        receipt = self._rebind()
        self.assertTrue(receipt["ok"])
        self.assertEqual(receipt["driver_state"]["target_sha256"], sha256_file(self.driver))
        self.assertEqual(receipt["driver_state"]["target_size"], self.driver.stat().st_size)
        self.assertEqual(sha256_file(self.save), save_before)
        after = json.loads(self.driver.read_text(encoding="utf-8"))
        restored_source = copy.deepcopy(after)
        for binding in (
            restored_source["succession_lifecycle"],
            restored_source["last_checkpoint"]["succession_lifecycle"],
            restored_source["command_history"][2]["result"]["checkpoint"]["succession_lifecycle"],
        ):
            self.assertEqual(binding["environment_sha256"], "b" * 64)
            binding["environment_sha256"] = "a" * 64
        self.assertEqual(restored_source, self.source)
        self.assertTrue(self._preflight()["ok"])

    def test_rule_change_cannot_reclassify_existing_rogue_lifecycle(self) -> None:
        before = self.driver.read_bytes()
        self.manifest["rules"]["profile"][0]["setting"] = "xar_off"
        with self.assertRaisesRegex(AgentError, "target lifecycle profile differs"):
            self._rebind()
        self.assertEqual(self.driver.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
