"""Focused offline contract for an isolated mainline wartime perk action."""

from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "src"))

from run_player_lifestyle_three_query_readback import preflight
from run_player_lifestyle_wartime_perk_trial import (
    SCHEMA, choose_one_wartime_perk, finalize_postflight,
)


EPISODE = "native-29829-r0171-test"
DATE = 53194440
HISTORY = 1333


def life_snapshot() -> dict[str, object]:
    return {
        "status": "available", "snapshot_id": "native:3",
        "episode_run_id": EPISODE, "public_revision": 3,
        "native_revision": 3, "proof_epoch": 3,
        "date_raw": DATE, "player_character_id": 29829,
        "current_focus": {"presence": "present",
                          "key": "stewardship_wealth_focus",
                          "lifestyle_key": "stewardship_lifestyle"},
        "current_lifestyle_progress": {"presence": "present",
            "lifestyle_key": "stewardship_lifestyle",
            "unspent_perk_points": 2, "used_perk_points": 4},
        "owned_perk_keys": [],
        "legal_perk_candidates": {"status": "available", "items": [{
            "key": "cutting_corners_perk",
            "lifestyle_key": "stewardship_lifestyle",
        }]},
        "readiness": {key: True for key in (
            "current_focus_ready", "lifestyle_progress_ready",
            "owned_perks_ready", "legal_perk_candidates_ready", "same_frame_ready",
        )},
    }


class Driver:
    def __init__(self) -> None:
        self.frame = {
            "snapshot_id": "native:3", "native_revision": 3, "revision": 3,
            "date_raw": DATE, "paused": True, "map_ready": True,
            "played_character": {"character_id": 29829, "alive": True},
            "episode_run_id": EPISODE,
            "active_wars": [{"war_id": 16777250}, {"war_id": 95}],
            "native_command_history": [],
            "active_event": None, "pending_character_interaction": None,
        }
        self.life = life_snapshot()
        self.submits = 0
        self.selected_target: str | None = None

    def take_snapshot(self) -> dict[str, object]:
        return copy.deepcopy(self.frame)

    def execute_step(self, step: str, *, expected_revision: int) -> dict[str, object]:
        assert step == "query-campaign-root-context-v1" and expected_revision == 3
        self.frame["native_command_history"].append({
            "command": step, "ok": True,
            "result": {"campaign_root_context": {
                "status": "available", "snapshot_revision": 3,
                "date_raw": DATE, "player_character_id": 29829,
                "government": {"key": "feudal_government",
                               "flags": ["government_is_feudal"]},
            }},
        })
        return {"accepted": True}

    def query_player_lifestyle_formal_private_v1(
        self, *, expected_revision: int,
    ) -> dict[str, object]:
        assert expected_revision == 3
        return {"status": "available", "formal_precondition_status": "ready",
                "snapshot": copy.deepcopy(self.life)}

    def submit_player_lifestyle_perk_private_v1(
        self, *, query: dict[str, object], action: dict[str, object],
        expected_revision: int,
    ) -> dict[str, object]:
        assert expected_revision == 3
        assert query["snapshot"]["current_lifestyle_progress"][
            "unspent_perk_points"
        ] > 0
        assert action["target_key"] == query["snapshot"][
            "legal_perk_candidates"
        ]["items"][0]["key"]
        assert action["expected"]["expected_player_character_id"] == 29829
        self.submits += 1
        self.selected_target = action["target_key"]
        self.frame.update(snapshot_id="native:4", native_revision=4, revision=4)
        return {"status": "submitted_verification_pending",
                "action_request_id": "life-perk-once",
                "target_key": self.selected_target}

    def query_player_lifestyle_receipt_private_v1(
        self, *, pending: dict[str, object], expected_revision: int,
    ) -> dict[str, object]:
        assert pending["action_request_id"] == "life-perk-once"
        assert expected_revision == 4
        return {"status": "applied", "action_request_id": "life-perk-once",
                "target_key": self.selected_target, "kind": "perk",
                "post_target_perk_owned": True, "postcondition_verified": True}


def manifest() -> dict[str, object]:
    return {
        "expected_actor_id": 29829, "episode_run_id": EPISODE,
        "expected_date_raw": DATE, "expected_history_index": HISTORY,
        "source_save_sha256": "a" * 64,
        "source_driver_sha256": "b" * 64,
    }


class WartimePerkTrialTests(unittest.TestCase):
    def test_third_perk_uses_fresh_final_legality_and_one_typed_checkpoint(self) -> None:
        driver = Driver()
        driver.life["owned_perk_keys"] = [
            "cutting_corners_perk", "professional_workforce_perk",
        ]
        driver.life["current_lifestyle_progress"].update(
            unspent_perk_points=1, used_perk_points=6,
        )
        driver.life["legal_perk_candidates"]["items"] = [{
            "key": "centralization_perk",
            "lifestyle_key": "stewardship_lifestyle",
        }]
        post = copy.deepcopy(driver.life)
        post.update(snapshot_id="native:4", native_revision=4,
                    public_revision=4, proof_epoch=4)
        post["owned_perk_keys"].append("centralization_perk")
        post["current_lifestyle_progress"].update(
            unspent_perk_points=0, used_perk_points=7,
        )
        checkpoint = {"status": "saved", "sha256": "d" * 64,
                      "history_index": HISTORY + 4, "date_raw": DATE}
        with patch(
            "xar_autoplayer.bridge.player_lifestyle_private_transport_v1."
            "query_player_lifestyle_private_v1",
            return_value={"status": "available", "snapshot": post},
        ):
            result = choose_one_wartime_perk(
                driver, manifest(), wait_for_post=lambda pending: None,
                save_paired_checkpoint=lambda: checkpoint,
                plan_current_turn=lambda: {"plan": {"selected_step": None}},
                plan_following_turn=lambda: {"plan": {
                    "lifestyle_receipt_consumed": {
                        "action_request_id": "life-perk-once",
                        "postcondition_verified": True,
                    },
                }},
                expected_target="centralization_perk",
            )
        self.assertEqual(result["status"], "perk_checkpointed")
        self.assertEqual(result["target_key"], "centralization_perk")
        self.assertEqual(result["post_points"], {"unspent": 0, "used": 7})
        self.assertEqual(result["checkpoint"]["sha256"], "d" * 64)
        self.assertEqual(driver.submits, 1)
        self.assertFalse(result["date_advanced"])

        no_legal = Driver()
        no_legal.life = copy.deepcopy(driver.life)
        no_legal.life["legal_perk_candidates"]["items"] = []
        rejected = choose_one_wartime_perk(
            no_legal, manifest(), wait_for_post=lambda pending: None,
            save_paired_checkpoint=lambda: self.fail("no checkpoint"),
            plan_current_turn=lambda: self.fail("no formal plan"),
            plan_following_turn=lambda: self.fail("no following plan"),
            expected_target="centralization_perk",
        )
        self.assertEqual(rejected["status"], "no_legal_wartime_perk")
        self.assertEqual(no_legal.submits, 0)

    def test_second_perk_uses_fresh_formal_query_and_paired_checkpoint(self) -> None:
        driver = Driver()
        driver.life["owned_perk_keys"] = ["cutting_corners_perk"]
        driver.life["current_lifestyle_progress"].update(
            unspent_perk_points=2, used_perk_points=5,
        )
        driver.life["legal_perk_candidates"]["items"] = [{
            "key": "professional_workforce_perk",
            "lifestyle_key": "stewardship_lifestyle",
        }]
        post = copy.deepcopy(driver.life)
        post.update(snapshot_id="native:4", native_revision=4,
                    public_revision=4, proof_epoch=4)
        post["owned_perk_keys"].append("professional_workforce_perk")
        post["current_lifestyle_progress"].update(
            unspent_perk_points=1, used_perk_points=6,
        )
        checkpoint = {"status": "saved", "sha256": "c" * 64,
                      "history_index": HISTORY + 4, "date_raw": DATE}
        with patch(
            "xar_autoplayer.bridge.player_lifestyle_private_transport_v1."
            "query_player_lifestyle_private_v1",
            return_value={"status": "available", "snapshot": post},
        ):
            result = choose_one_wartime_perk(
                driver, manifest(), wait_for_post=lambda pending: None,
                save_paired_checkpoint=lambda: checkpoint,
                plan_current_turn=lambda: {"plan": {"selected_step": None}},
                plan_following_turn=lambda: {"plan": {
                    "lifestyle_receipt_consumed": {
                        "action_request_id": "life-perk-once",
                        "postcondition_verified": True,
                    },
                }},
                expected_target="professional_workforce_perk",
            )
        self.assertEqual(result["status"], "perk_checkpointed")
        self.assertEqual(result["target_key"], "professional_workforce_perk")
        self.assertEqual(result["post_points"], {"unspent": 1, "used": 6})
        self.assertEqual(driver.submits, 1)
        self.assertEqual(result["checkpoint"]["sha256"], "c" * 64)

        wrong_target = Driver()
        wrong_target.life = copy.deepcopy(driver.life)
        rejected = choose_one_wartime_perk(
            wrong_target, manifest(), wait_for_post=lambda pending: None,
            save_paired_checkpoint=lambda: self.fail("no checkpoint"),
            plan_current_turn=lambda: self.fail("no formal plan"),
            plan_following_turn=lambda: self.fail("no following plan"),
        )
        self.assertEqual(rejected["status"], "no_legal_wartime_perk")
        self.assertEqual(wrong_target.submits, 0)

    def test_r0175_timeout_does_not_misclassify_reclaimed_process(self) -> None:
        result = {
            "status": "red", "red": {"reason": "TimeoutError: no later frame"},
            "cleanup": {"ok": True, "tree_gone": True},
            "postflight": {
                "ck3_inventory": {"processes": []},
                "source_save_sha256": "a" * 64,
                "wall_seconds": 603.8,
            },
        }
        source = {"source_save_sha256": "a" * 64,
                  "bounds": {"overall_seconds": 600}}
        finalize_postflight(result, source)
        self.assertTrue(result["ck3_reclaimed"])
        self.assertFalse(result["wall_bound_ok"])
        self.assertEqual(result["status"], "red_wall_bound")
        self.assertIn("TimeoutError", result["red"]["reason"])

    def test_checkpointed_perk_still_fails_overall_wall_bound(self) -> None:
        digest = "c" * 64
        result = {
            "status": "perk_checkpointed",
            "trial": {"checkpoint": {"sha256": digest}},
            "cleanup": {"ok": True},
            "postflight": {
                "ck3_inventory": {"processes": []},
                "source_save_sha256": "a" * 64,
                "prepared_save_sha256": digest,
                "paired_checkpoint": {"sha256": digest},
                "wall_seconds": 601,
            },
        }
        finalize_postflight(result, {"source_save_sha256": "a" * 64,
                                     "bounds": {"overall_seconds": 600}})
        self.assertTrue(result["ck3_reclaimed"])
        self.assertEqual(result["status"], "red_wall_bound")

    def test_one_typed_perk_keeps_war_red_and_creates_resume_pair(self) -> None:
        driver = Driver()
        post = life_snapshot()
        post.update(snapshot_id="native:4", native_revision=4,
                    public_revision=4, proof_epoch=4)
        post["owned_perk_keys"] = ["cutting_corners_perk"]
        post["current_lifestyle_progress"]["unspent_perk_points"] = 1
        post["current_lifestyle_progress"]["used_perk_points"] = 5
        checkpoint = {"status": "saved", "sha256": "c" * 64,
                      "history_index": HISTORY + 4, "date_raw": DATE}
        following = {"plan": {
            "selected_step": None,
            "phase": "native_war_defender_siege_relief_observation_blocked",
            "required_observation": "complete-matching-active-native-move-intent-route",
            "lifestyle_receipt_consumed": {
                "action_request_id": "life-perk-once",
                "postcondition_verified": True,
            },
        }}
        with patch(
            "xar_autoplayer.bridge.player_lifestyle_private_transport_v1."
            "query_player_lifestyle_private_v1",
            return_value={"status": "available", "snapshot": post},
        ):
            result = choose_one_wartime_perk(
                driver, manifest(), wait_for_post=lambda pending: None,
                save_paired_checkpoint=lambda: checkpoint,
                plan_current_turn=lambda: {"plan": {
                    "phase": "native_war_defender_siege_relief_observation_blocked",
                    "selected_step": None,
                }},
                plan_following_turn=lambda: following,
            )
        self.assertEqual(result["status"], "perk_checkpointed")
        self.assertEqual(driver.submits, 1)
        self.assertEqual(result["post_points"], {"unspent": 1, "used": 5})
        self.assertEqual(result["checkpoint"]["history_index"], HISTORY + 4)
        self.assertEqual(result["war_ids_after"], [16777250, 95])
        self.assertFalse(result["date_advanced"])
        self.assertEqual(
            result["war_red_preserved"]["required_observation"],
            "complete-matching-active-native-move-intent-route",
        )

    def test_old_legal_readback_cannot_replace_fresh_final_legality(self) -> None:
        driver = Driver()
        driver.life["legal_perk_candidates"]["items"] = []
        result = choose_one_wartime_perk(
            driver, manifest(), wait_for_post=lambda pending: None,
            save_paired_checkpoint=lambda: self.fail("no checkpoint"),
            plan_current_turn=lambda: self.fail("no formal plan"),
            plan_following_turn=lambda: self.fail("no following plan"),
        )
        self.assertEqual(result["status"], "no_legal_wartime_perk")
        self.assertEqual(driver.submits, 0)

    def test_formal_war_action_keeps_perk_unsubmitted(self) -> None:
        driver = Driver()
        result = choose_one_wartime_perk(
            driver, manifest(), wait_for_post=lambda pending: None,
            save_paired_checkpoint=lambda: self.fail("no checkpoint"),
            plan_current_turn=lambda: {"plan": {
                "selected_step": "move-army-to-province-45",
            }},
            plan_following_turn=lambda: self.fail("no following plan"),
        )
        self.assertEqual(result["status"], "war_action_pending")
        self.assertEqual(driver.submits, 0)

    def test_action_preflight_rejects_old_read_only_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "candidate-manifest.json").write_text(
                '{"schema":"xar.ck3.g2_m4_lifestyle_three_query_candidate_v1",'
                '"status":"ready-no-launch","read_only":true}',
                encoding="utf-8",
            )
            with patch.dict("os.environ", {"TEMP": directory, "TMP": directory}):
                with self.assertRaises(RuntimeError):
                    preflight(
                        root, expected_schema=SCHEMA,
                        expected_read_only=False,
                    )


if __name__ == "__main__":
    unittest.main()
