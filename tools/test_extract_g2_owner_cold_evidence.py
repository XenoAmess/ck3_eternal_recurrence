import copy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import extract_g2_owner_cold_evidence as tool


def receipts():
    goal = dict(goal_key="dynasty_continuity", campaign_id="campaign",
                current_character_id=7, origin_character_id=6,
                format_version=1, progress={"reconciled_successions": 1})
    checkpoint = dict(name="checkpoint.ck3", size=1000, sha256="a" * 64,
                      date_raw=24, history_index=7,
                      episode_character_id=7, episode_run_id="episode")
    owner = dict(pid=20, old_save_loaded=True, load_save_name="checkpoint",
                 command=["ck3.exe", "-loadsave=checkpoint"])
    inputs = dict(checkpoint=checkpoint, canonical_save_sha256="a" * 64,
                  source_game_identity={"pid": 10},
                  old_game_actual_exit_verified=True,
                  old_game_normal_close_qualified=False, old_game_actual_exit_code=1,
                  old_game_close_classification="FORCED_OWNED_GAME_CLEANUP")
    relocated = dict(checkpoint)
    relocated["saved_date_raw"] = relocated.pop("date_raw")
    relocated["load_save_name"] = "checkpoint"
    frame = dict(snapshot_id="native:2", date_raw=24, paused=True, map_ready=True,
                 episode_character_id=7, episode_run_id="episode",
                 played_character={"character_id": 7, "alive": True},
                 diagnostics={"bridge_pid": 20}, campaign_goal=goal)
    return owner, inputs, {"checkpoint": relocated}, {
        "result": {"structured_content": frame}}


class OwnerColdCompounds(unittest.TestCase):
    def test_owner_checkpoint_frame_goal_and_unknown_closure(self):
        values = receipts()
        report = tool.summarize(*values)
        self.assertEqual(report["owner_chain_state"], "consistent_supplied_fields")
        self.assertEqual(report["prior_exit"]["old_game_actual_exit_code"], 1)
        self.assertIs(report["prior_exit"]["old_game_normal_close_qualified"], False)
        self.assertIsNone(report["initial_control"]["native_session_control"])
        del values[1]["old_game_actual_exit_verified"]
        report = tool.summarize(*values)
        self.assertEqual(report["owner_chain_state"], "incomplete_observations")
        self.assertIsNone(report["checks"]["prior_game_exit_observed"])

    def test_wrong_named_load_sha_or_size_is_not_consistent(self):
        for field, value in (("load_save_name", "wrong"),
                             ("sha256", "b" * 64), ("size", 999)):
            values = receipts()
            target = values[0] if field == "load_save_name" else values[2]["checkpoint"]
            target[field] = value
            with self.subTest(field=field):
                self.assertEqual(tool.summarize(*values)["owner_chain_state"],
                                 "observed_mismatch")

    def test_hot_plan_camera_and_oversize_refused_before_read(self):
        values = receipts()
        hot = copy.deepcopy(values[3])
        control = {"request": {"tool": "ck3_get_capabilities"}, "result": {
            "structured_content": {"native_session_control": {
                "driver_state_restored": True,
                "driver_state_restore_kind": "same_pid_hot",
                "episode_binding_state": "active_resumed"}}}}
        camera = {"request": {"tool": "root_initialize_campaign_camera_v1"},
                  "result": {"structured_content": {"status": "centered"}}}
        plan = {"normal_plan_goal_used": {"value":
                values[3]["result"]["structured_content"]["campaign_goal"]}}
        report = tool.summarize(*values, initial_capabilities=camera,
                                hot_semantic=hot, hot_capabilities=control,
                                plan=plan,
                                plan_pointer="/normal_plan_goal_used/value")
        self.assertIsNone(report["initial_control"]["native_session_control"])
        self.assertEqual(set(report["optional_checks"].values()), {True})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "closed.json"
            path.write_text("{}", encoding="utf-8")
            with patch.object(Path, "stat", return_value=SimpleNamespace(
                    st_size=tool.MAX_INPUT + 1)), patch.object(
                    Path, "read_bytes", side_effect=RuntimeError("must not read")) as reader:
                with self.assertRaises(ValueError):
                    tool.read_receipt(path)
                reader.assert_not_called()


if __name__ == "__main__":
    unittest.main()
