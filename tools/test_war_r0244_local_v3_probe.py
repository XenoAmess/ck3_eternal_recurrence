"""No-launch checks for the local R0244 same-frame rehearsal boundary."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import war_r0244_local_v3_probe as probe


SCENE = {
    "date_raw": 53144520, "character_id": 29829, "war_id": 4,
    "attacker_army_id": 18, "origin_province_id": 2619,
    "defender_army_id": 24, "target_province_id": 2638,
    "hostile_army_ids": [24, 30],
}


def snapshot() -> dict:
    return {
        "paused": True, "date_raw": 53144520, "snapshot_id": "native:3",
        "revision": 4, "native_revision": 3, "episode_run_id": "run-x",
        "pending_character_interaction": None, "active_event": None,
        "played_character": {"character_id": 29829},
        "active_wars": [{"war_id": 4,
                         "allied_armies": [{"army_id": 18, "current_province_id": 2619,
                                             "route_province_ids": [], "move_target_province_id": None,
                                             "controllable": True, "retreating": False}],
                         "enemy_armies": [{"army_id": 24, "current_province_id": 2638, "retreating": False},
                                           {"army_id": 30, "current_province_id": 2639, "retreating": False}]}],
    }


class LocalV3ProbeTest(unittest.TestCase):
    def test_same_frame_scene_and_v3_accept_only_exact_read_only_inputs(self) -> None:
        before = snapshot()
        probe.require_scene(before, SCENE)
        step = "query-combat-simulation-inputs-v3-2638-2643-a-1-18-d-1-24"
        result = {
            "step": step, "status": "available", "accepted": True,
            "queried_snapshot_id": "native:3", "queried_revision": 4,
            "queried_native_revision": 3, "queried_episode_run_id": "run-x",
            "combat_simulation_inputs": {
                "schema_version": 3, "rules_manifest_sha256": "ABC",
                "completeness": {"input_observation_ready": True},
                "base_inputs": {"target_province_id": 2638,
                                "scenario": {"attacker_entry_province_id": 2643,
                                             "attacker_army_ids": [18], "defender_army_ids": [24]}},
            },
        }
        self.assertTrue(probe.require_v3(result, before, SCENE, 2643, step)["input_observation_ready"])
        for field, value in (("queried_revision", 5), ("queried_native_revision", 4),
                             ("queried_snapshot_id", "native:4"), ("queried_episode_run_id", "other")):
            changed = {**result, field: value}
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "same-frame mismatch"):
                probe.require_v3(changed, before, SCENE, 2643, step)
        result["combat_simulation_inputs"]["base_inputs"]["scenario"]["defender_army_ids"] = [30]
        with self.assertRaisesRegex(ValueError, "scenario or completeness"):
            probe.require_v3(result, before, SCENE, 2643, step)
        before["pending_character_interaction"] = {"id": 1}
        with self.assertRaisesRegex(ValueError, "pending"):
            probe.require_scene(before, SCENE)

    def test_preflight_freezes_local_assets_but_cannot_launch_game(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.ck3"
            source.write_bytes(b"test-save")
            source_hash = hashlib.sha256(source.read_bytes()).hexdigest().upper()
            receipt = root / "receipt.json"
            receipt.write_text(json.dumps({"result": "CALL_COMPLETED", "body": {"checkpoint": {
                "status": "saved", "sha256": source_hash, "date_raw": 53144520,
                "succession_lifecycle": {"source": "pure-vanilla-enabled-mods-empty", "xar_enabled": "xar_off"}}}}), encoding="utf-8")
            observed = root / "snapshot.json"
            observed.write_text(json.dumps({"result": "CALL_COMPLETED", "body": snapshot()}), encoding="utf-8")
            bridge = root / "bridge.dll"
            bridge.write_bytes(b"test-bridge")
            injector = root / "injector.exe"
            injector.write_bytes(b"test-injector")
            game = root / "ck3.exe"
            game.write_bytes(b"test-game")
            cache = root / "shadercache"
            cache.mkdir()
            assets = {name: {"path": str(path), "sha256": probe.sha256(path)} for name, path in
                      (("ck3_exe", game), ("checkpoint", source), ("checkpoint_receipt", receipt),
                       ("source_snapshot", observed),
                       ("bridge_dll", bridge), ("bridge_injector", injector))}
            config_path = root / "source-manifest.json"
            config_path.write_text(json.dumps({"schema": "xar.ck3.war-r0244-local-v3-source/v1",
                                               "assets": assets, "shader_cache_source": str(cache),
                                               "game_dir": str(root), "pipe_prefix": "test-", "scene": SCENE}), encoding="utf-8")
            attempt = root / "new-attempt"
            plan = probe.preflight(attempt, config_path)
            self.assertEqual(plan["live_status"], "NOT_STARTED")
            self.assertFalse((attempt / "ck3-output").exists())
            self.assertFalse((attempt / "ck3-state").exists())
            self.assertEqual(plan["capture_argv"][-1], "--capture")
            self.assertIn("steam-offline-receipt.json", plan["capture_argv"][-2])
            self.assertEqual(plan["source_hashes"]["checkpoint"], source_hash)
            with self.assertRaises(FileExistsError):
                probe.preflight(attempt, config_path)
            bridge.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "bridge_dll SHA-256 mismatch"):
                probe.preflight(root / "another-attempt", config_path)


if __name__ == "__main__":
    unittest.main()
