"""Default-option child proposal stays bound to its native proof and pair."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from xar_autoplayer.bridge import player_child_matrilineal_private_action_v1 as action


FRAME = {"paused": True, "map_ready": True, "native_revision": 3,
         "date_raw": 53219928,
         "played_character": {"character_id": 29829, "alive": True}}


class Driver:
    allow_private_player_child_default_action = True

    def take_snapshot(self) -> dict[str, object]:
        return dict(FRAME)

    def query_player_child_marriage_subject_private_v1(
        self, **_: object,
    ) -> dict[str, object]:
        return {"player_child_verified": True}


def legality() -> dict[str, object]:
    return {"schema": "xar.ck3.player-child-marriage-subject.v1",
            "status": "available", "player_child_verified": True,
            "native_revision": 3, "played_character_id": 29829,
            "subject_character_id": 38988, "query_sequence": 1,
            "native_legal_candidates": [{"candidate_character_id": 39380,
                                         "recipient_matchmaker_character_id": 30549}]}


def value() -> dict[str, object]:
    return {"schema": "xar.ck3.player-child-marriage-value.v1",
            "status": "available", "read_only": True,
            "advertised": False, "native_revision": 3,
            "legality_query_sequence": 1,
            "played_character_id": 29829,
            "subject_character_id": 38988,
            "candidate_character_id": 39380,
            "request_matrilineal_option": False,
            "row": {"actor_character_id": 29829,
                    "heir_character_id": 38988,
                    "candidate_character_id": 39380,
                    "recipient_character_id": 30549,
                    "requested_matrilineal_option": False,
                    "selected_option_readback": None,
                    "matrilineal_option_selected": False,
                    "effective_matrilineal_if_accepted": False,
                    "final_legality_sampled": True,
                    "complete_can_send": True,
                    "recipient_answer_status_raw": 0,
                    "recipient_ai_accept_raw": 900000}}


class DefaultChildTransportTest(unittest.TestCase):
    def test_submit_only_returns_pending_receipt(self) -> None:
        driver = Driver()
        reply = {"step": action.DEFAULT_SUBMIT_STEP, "accepted": True,
                 "private_build": True, "advertised": False,
                 "status": "receipt_pending", "material_result": False,
                 "pre_native_revision": 3, "played_character_id": 29829,
                 "heir_character_id": 38988,
                 "candidate_character_id": 39380,
                 "recipient_character_id": 30549,
                 "matrilineal_option_selected": False}
        with (patch.object(action, "_command", return_value=reply) as command,
              patch.object(action, "_require_same_paused_frame")):
            receipt = action.submit_player_child_matrilineal_private_v1(
                driver, legality=legality(), value=value(), default_route=True)
        self.assertEqual(receipt["schema"], action.DEFAULT_SCHEMA)
        self.assertEqual(receipt["status"], "receipt_pending")
        self.assertIs(receipt["material_result"], False)
        self.assertEqual(command.call_args.args[1], action.DEFAULT_SUBMIT_STEP)

    def test_default_route_rejects_maternal_projection_and_permission(self) -> None:
        driver = Driver()
        changed = value()
        changed["row"]["matrilineal_option_selected"] = True
        with patch.object(action, "_require_same_paused_frame"):
            with self.assertRaisesRegex(Exception, "selected native final proof"):
                action.submit_player_child_matrilineal_private_v1(
                    driver, legality=legality(), value=changed,
                    default_route=True)
        driver.allow_private_player_child_default_action = False
        with self.assertRaisesRegex(Exception, "disabled"):
            action.submit_player_child_matrilineal_private_v1(
                driver, legality=legality(), value=value(), default_route=True)

    def test_cold_pending_does_not_become_rejection(self) -> None:
        driver = Driver()
        pending = {"schema": action.DEFAULT_SCHEMA,
                   "status": "receipt_pending",
                   "played_character_id": 29829,
                   "heir_character_id": 38988,
                   "candidate_character_id": 39380,
                   "recipient_character_id": 30549,
                   "pre_native_revision": 3,
                   "source_date_raw": 53219928,
                   "matrilineal_option_selected": False}
        result = {"step": action.DEFAULT_RESULT_STEP,
                  "accepted": True, "private_build": True,
                  "advertised": False, "status": "pending",
                  "material_result": False, "cold_recovery": True,
                  "post_native_revision": 3,
                  "pre_native_revision": 0,
                  "heir_character_id": 38988,
                  "candidate_character_id": 39380,
                  "recipient_character_id": 30549,
                  "matrilineal_option_selected": False,
                  "outbound_pending_state": "absent"}
        with (patch.object(action, "_command", return_value=result) as command,
              patch.object(action, "_require_same_paused_frame")):
            observed = action.query_player_child_matrilineal_result_private_v1(
                driver, pending=pending, cold=True, default_route=True)
        self.assertEqual(command.call_args.args[1], action.DEFAULT_RESULT_STEP)
        self.assertEqual(observed["status"], "pending")
        self.assertIs(observed["cold_absent_relation_unresolved"], True)

    def test_later_bilateral_result_is_distinct_from_ack(self) -> None:
        driver = Driver()
        pending = {"schema": action.DEFAULT_SCHEMA,
                   "status": "receipt_pending", "played_character_id": 29829,
                   "heir_character_id": 38988,
                   "candidate_character_id": 39380,
                   "recipient_character_id": 30549,
                   "pre_native_revision": 3,
                   "source_date_raw": 53219928,
                   "matrilineal_option_selected": False}
        reply = {"step": action.DEFAULT_RESULT_STEP,
                 "accepted": True, "private_build": True,
                 "advertised": False, "status": "betrothal",
                 "material_result": True, "cold_recovery": False,
                 "post_native_revision": 4, "pre_native_revision": 3,
                 "heir_character_id": 38988,
                 "candidate_character_id": 39380,
                 "recipient_character_id": 30549,
                 "matrilineal_option_selected": False}
        later = {**FRAME, "native_revision": 4, "date_raw": 53219929}
        with (patch.object(action, "_paused", return_value=later),
              patch.object(action, "_command", return_value=reply)):
            observed = action.query_player_child_matrilineal_result_private_v1(
                driver, pending=pending, default_route=True)
        self.assertEqual(observed["status"], "betrothal")
        self.assertIs(observed["material_result"], True)

        cold_reply = {**reply, "cold_recovery": True,
                      "pre_native_revision": 0,
                      "outbound_pending_state": "not_applicable"}
        with (patch.object(action, "_paused", return_value=later),
              patch.object(action, "_command", return_value=cold_reply)):
            recovered = action.query_player_child_matrilineal_result_private_v1(
                driver, pending=pending, cold=True, default_route=True)
        self.assertEqual(recovered["status"], "betrothal")
        self.assertIs(recovered["cold_absent_relation_unresolved"], False)


if __name__ == "__main__":
    unittest.main()
