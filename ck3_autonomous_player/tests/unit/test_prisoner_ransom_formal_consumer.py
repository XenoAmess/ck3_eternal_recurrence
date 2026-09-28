"""The H3446 offer comparison must preserve war and custody value inputs."""

import copy
import json
import tempfile
import unittest
from pathlib import Path

from xar_autoplayer.prisoner_ransom_formal_consumer import (
    plan_ransom_private,
    read_ransom_receipt_private,
    select_ransom_candidate,
    submit_ransom_private,
)


class RansomChoiceTest(unittest.TestCase):
    def setUp(self):
        self.snapshot = {
            "paused": True, "map_ready": True, "native_revision": 3,
            "date_raw": 53219112, "played_character": {"character_id": 29829},
            "active_wars": [{"war_id": 16777231}],
        }
        self.rows = [
            {"source_ordinal": 0, "prisoner_character_id": 34486,
             "jailer_character_id": 29829, "custody_relation_verified": True,
             "primary_title_tier_raw": None, "same_dynasty": False,
             "is_child_of_played_character": False},
            {"source_ordinal": 1, "prisoner_character_id": 44484,
             "jailer_character_id": 29829, "custody_relation_verified": True,
             "primary_title_tier_raw": 1, "same_dynasty": False,
             "is_child_of_played_character": False},
            {"source_ordinal": 2, "prisoner_character_id": 47028,
             "jailer_character_id": 29829, "custody_relation_verified": True,
             "primary_title_tier_raw": None, "same_dynasty": False,
             "is_child_of_played_character": False},
        ]
        for index, amount in ((0, 5_000_000), (1, 3_000_000)):
            self.rows[index]["ransom_quote_preview"] = {
                "status": "available", "definition_key": "ransom_interaction",
                "jailer_character_id": 29829,
                "prisoner_character_id": self.rows[index]["prisoner_character_id"],
                "payer_character_id": 30470 if index == 0 else 44484,
                "native_revision": 3, "date_raw": 53219112,
                "selected_option": "gold", "can_send": True,
                "would_accept_now": True, "recipient_answer_status_raw": 0,
                "quoted_gold_raw": amount, "raw_scale": 100_000,
            }
        self.rows[2]["ransom_quote_preview"] = {
            "status": "unavailable", "unavailable_reason": "option_mask_unexpected"}
        self.reads = []
        for ordinal in range(3):
            self.reads.append({
                "status": "available", "snapshot_revision": 3,
                "query_sequence": ordinal + 1,
                "player_prisoner_collection": {
                    "status": "available", "played_character_id": 29829,
                    "played_dynasty_id": 174,
                    "date_raw": 53219112, "collection_complete": True,
                    "prisoners": copy.deepcopy(self.rows),
                },
            })
        self.war = [{
            "snapshot_revision": 3,
            "war_prisoner_release_pairs_proof": {
                "war_id": 16777231, "date_raw": 53219112,
                "same_frame_stable": True, "full_participant_scan": True,
                "primary_and_first_three_successors_scanned": True,
                "active_casus_belli_key": "individual_county_de_jure_cb",
                "release_pairs": [],
                "attacker_release_candidate_ids": [30097, 34729, 31729, 31044],
                "defender_release_candidate_ids": [29829, 38822, 38988, 38293],
            },
        }]

    def test_landless_outside_dynasty_gold_offer_is_chosen(self):
        choice = select_ransom_candidate(self.snapshot, self.reads, self.war)
        self.assertEqual(choice["prisoner_character_id"], 34486)
        self.assertEqual(choice["payer_character_id"], 30470)
        self.assertEqual(choice["quoted_gold_raw"], 5_000_000)

    def test_war_release_candidate_cannot_be_ransomed(self):
        self.war[0]["war_prisoner_release_pairs_proof"][
            "attacker_release_candidate_ids"].append(34486)
        self.assertIsNone(select_ransom_candidate(
            self.snapshot, self.reads, self.war))

    def test_unknown_war_source_is_not_assumed_empty(self):
        self.war[0]["war_prisoner_release_pairs_proof"][
            "full_participant_scan"] = False
        self.assertIsNone(select_ransom_candidate(
            self.snapshot, self.reads, self.war))

    def test_cold_pending_receipt_precedes_a_war_step_and_needs_material_reads(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temporary:
            state_dir = Path(temporary)
            pending = {
                "stage": "receipt_pending", "pre_native_revision": 3,
                "pre_date_raw": 53219112, "player_character_id": 29829,
                "prisoner_character_id": 34486, "payer_character_id": 30470,
                "selected_option": "gold", "quoted_gold_raw": 5_000_000,
                "pre_player_gold_raw": 10_000_000,
                "last_checked_native_revision": None,
            }
            (state_dir / "player-prisoner-ransom-formal-v1.json").write_text(
                json.dumps({"schema": "xar.ck3.prisoner-ransom-formal.v1",
                            "pending": pending, "resolved": None}),
                encoding="utf-8",
            )
            snapshot = {**self.snapshot, "native_revision": 4,
                        "date_raw": 53219113, "revision": 5,
                        "played_character_gold": {"raw": 15_000_000,
                                                  "scale": 100_000}}

            class Driver:
                allow_private_prisoner_ransom_action = True

                def __init__(self):
                    self.state_dir = state_dir

                def take_snapshot(self):
                    return snapshot

                def query_player_prisoner_collection_private_v1(
                    self, *, expected_revision, ransom_ordinal=None,
                ):
                    assert expected_revision == 5
                    return {"snapshot_revision": 4,
                            "player_prisoner_collection": {
                                "collection_complete": True,
                                "played_character_id": 29829,
                                "date_raw": 53219113,
                                "prisoners": []}}

            driver = Driver()
            planned = plan_ransom_private(
                driver, {"plan": {"selected_step": "move-army-1-to-2"}},
                snapshot,
            )
            self.assertEqual(planned["plan"]["selected_step"],
                             "private-read-player-prisoner-ransom-receipt-v1")
            receipt = read_ransom_receipt_private(
                driver, pending=planned["plan"]["prisoner_ransom_pending"])
            self.assertEqual(receipt["status"], "applied")
            self.assertTrue(receipt["postcondition_verified"])

    def test_missing_gold_gain_never_resolves_custody_loss(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temporary:
            state_dir = Path(temporary)
            pending = {"pre_native_revision": 3, "pre_date_raw": 53219112,
                       "player_character_id": 29829,
                       "prisoner_character_id": 34486,
                       "quoted_gold_raw": 5_000_000,
                       "pre_player_gold_raw": 10_000_000}
            (state_dir / "player-prisoner-ransom-formal-v1.json").write_text(
                json.dumps({"schema": "xar.ck3.prisoner-ransom-formal.v1",
                            "pending": pending, "resolved": None}),
                encoding="utf-8",
            )

            class Driver:
                def __init__(self):
                    self.state_dir = state_dir

                def take_snapshot(self):
                    return {**self_snapshot, "native_revision": 4,
                            "date_raw": 53219113, "revision": 5,
                            "played_character_gold": {"raw": 10_000_000,
                                                      "scale": 100_000}}

                def query_player_prisoner_collection_private_v1(
                    self, *, expected_revision, ransom_ordinal=None,
                ):
                    return {"snapshot_revision": 4,
                            "player_prisoner_collection": {
                                "collection_complete": True,
                                "played_character_id": 29829,
                                "date_raw": 53219113, "prisoners": []}}

            self_snapshot = self.snapshot
            receipt = read_ransom_receipt_private(Driver(), pending=pending)
            self.assertEqual(receipt["status"], "ambiguous")
            self.assertFalse(receipt["material_result"])

    def test_unresolved_fence_is_durable_before_native_submit(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temporary:
            state_dir = Path(temporary)
            seen = []

            class Driver:
                def __init__(self):
                    self.state_dir = state_dir

                def take_snapshot(self):
                    return {**self_snapshot, "revision": 4,
                            "played_character_gold": {"raw": 10_000_000,
                                                      "scale": 100_000}}

                def submit_player_prisoner_ransom_private_v1(
                    self, *, collection, prisoner_character_id,
                ):
                    ledger = json.loads((state_dir /
                        "player-prisoner-ransom-formal-v1.json").read_text(
                            encoding="utf-8"))
                    seen.append(ledger["pending"]["stage"])
                    return {"status": "submitted_verification_pending",
                            "material_result": False,
                            "pre_native_revision": 3}

            self_snapshot = self.snapshot
            choice = {"collection": self.reads[0],
                      "prisoner_character_id": 34486,
                      "payer_character_id": 30470,
                      "selected_option": "gold",
                      "quoted_gold_raw": 5_000_000}
            pending = submit_ransom_private(
                Driver(), plan={"prisoner_ransom_choice": choice})
            self.assertEqual(seen, ["submission_unresolved"])
            self.assertEqual(pending["stage"], "receipt_pending")
            with self.assertRaisesRegex(ValueError, "unresolved"):
                submit_ransom_private(
                    Driver(), plan={"prisoner_ransom_choice": choice})


if __name__ == "__main__":
    unittest.main()
