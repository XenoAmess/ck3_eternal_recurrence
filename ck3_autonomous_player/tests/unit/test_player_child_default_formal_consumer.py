"""The split-successor default proposal consumes only a paired native result."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from xar_autoplayer import player_child_default_formal_consumer as consumer
from xar_autoplayer.native_auto_run import (
    _verify_pending_family_marriage_checkpoint,
)


def _frame(*, native_revision: int = 3,
           selected_step: str | None = None) -> dict[str, object]:
    return {
        "paused": True, "map_ready": True, "revision": native_revision + 1,
        "native_revision": native_revision,
        "snapshot_id": f"native:{native_revision}",
        "date_raw": 53219928,
        "episode_run_id": "native-29829-test",
        "played_character": {"character_id": 29829, "alive": True},
        "active_event": None, "pending_character_interaction": None,
        "active_wars": [{"war_id": 16777231}],
    }


def _legality() -> dict[str, object]:
    return {
        "schema": "xar.ck3.player-child-marriage-subject.v1",
        "status": "available", "player_child_verified": True,
        "native_revision": 3, "played_character_id": 29829,
        "subject_character_id": 38988, "query_sequence": 7,
        "betrothed_character_id": None, "primary_spouse_character_id": None,
        "spouse_character_ids": [],
        "native_legal_candidates": [
            {"candidate_character_id": 37909,
             "recipient_matchmaker_character_id": 34332},
            {"candidate_character_id": 37571,
             "recipient_matchmaker_character_id": 32897},
        ],
    }


def _value(candidate_id: int, *, heir_selector: int = 0
           ) -> dict[str, object]:
    recipient = {37909: 34332, 37571: 32897}[candidate_id]
    return {
        "schema": "xar.ck3.player-child-marriage-value.v1",
        "status": "available", "native_revision": 3,
        "legality_query_sequence": 7,
        "request_matrilineal_option": False,
        "candidate_character_id": candidate_id,
        "row": {
            "actor_character_id": 29829, "heir_character_id": 38988,
            "candidate_character_id": candidate_id,
            "recipient_character_id": recipient,
            "heir_sex_selector_raw": heir_selector,
            "candidate_sex_selector_raw": 1,
            "requested_matrilineal_option": False,
            "matrilineal_option_selected": False,
            "effective_matrilineal_if_accepted": False,
        },
    }


class Driver:
    def __init__(self, state_dir: Path) -> None:
        self.state_dir = state_dir
        self.frame = _frame()
        self.queried_values: list[int] = []
        self.submissions = 0
        self.result_status = "pending"
        # R0395 has four non-primary titles inherited by the primary heir;
        # only title 2173 actually splits to Guy.
        self.partition = [
            {"primary": False, "first_heir_character_id": 38822,
             "title": {"title_id": title_id}}
            for title_id in (2102, 2111, 2115)
        ] + [
            {"primary": True, "first_heir_character_id": 38822,
             "title": {"title_id": 2141}},
            {"primary": False, "first_heir_character_id": 38822,
             "title": {"title_id": 2142}},
            {"primary": False, "first_heir_character_id": 38988,
             "title": {"title_id": 2173}},
        ]

    def _execute_campaign_root_context_v1_query(
        self, *, expected_revision: int,
    ) -> dict[str, object]:
        frame = self.frame
        assert expected_revision == frame["revision"]
        return {
            "status": "available",
            "queried_revision": frame["revision"],
            "queried_native_revision": frame["native_revision"],
            "queried_snapshot_id": frame["snapshot_id"],
            "campaign_root_context": {
                "player_character_id": 29829,
                "held_title_partition": self.partition,
            },
        }

    def query_player_child_marriage_subject_private_v1(
        self, *, expected_native_revision: int, subject_character_id: int,
    ) -> dict[str, object]:
        assert expected_native_revision == self.frame["native_revision"]
        assert subject_character_id == 38988
        return {**_legality(), "native_revision": expected_native_revision}

    def query_player_child_marriage_value_private_v1(
        self, *, legality: dict[str, object],
        candidate_character_id: int, request_matrilineal_option: bool,
    ) -> dict[str, object]:
        assert legality["subject_character_id"] == 38988
        assert request_matrilineal_option is False
        self.queried_values.append(candidate_character_id)
        return {**_value(candidate_character_id),
                "native_revision": self.frame["native_revision"]}

    def submit_player_child_default_private_v1(
        self, *, legality: dict[str, object], value: dict[str, object],
    ) -> dict[str, object]:
        self.submissions += 1
        row = value["row"]
        return {
            "schema": consumer.ACTION_SCHEMA,
            "status": "receipt_pending", "material_result": False,
            "pre_native_revision": self.frame["native_revision"],
            "played_character_id": 29829, "heir_character_id": 38988,
            "candidate_character_id": value["candidate_character_id"],
            "recipient_character_id": row["recipient_character_id"],
            "matrilineal_option_selected": False,
        }

    def query_player_child_default_result_private_v1(
        self, *, pending: dict[str, object], cold: bool,
    ) -> dict[str, object]:
        return {
            "status": self.result_status,
            "material_result": self.result_status in {"marriage", "betrothal"},
            "post_native_revision": self.frame["native_revision"],
            "heir_character_id": pending["heir_character_id"],
            "candidate_character_id": pending["candidate_character_id"],
            "recipient_character_id": pending["recipient_character_id"],
            "cold_recovery": cold,
            "outbound_pending_state": (
                "active" if self.result_status == "pending" else "not_applicable"),
        }

    def query_player_child_default_alliance_private_v1(
        self, *, resolved: dict[str, object],
    ) -> dict[str, object]:
        return {
            "schema": "xar.ck3.player-child-default-alliance-result.v1",
            "alliance_status": "not_allied",
            "played_has_recipient_alliance": False,
            "recipient_has_played_alliance": False,
            "heir_character_id": resolved["heir_character_id"],
            "candidate_character_id": resolved["candidate_character_id"],
        }


def _policy(_legality: object, values: object, *,
            split_successor_verified: bool,
            rejected_candidate_ids: frozenset[int] = frozenset()
            ) -> dict[str, object]:
    ids = [row["candidate_character_id"] for row in values]
    if (split_successor_verified and ids == [37909, 37571]
            and not rejected_candidate_ids):
        return {"status": "selected",
                "selected_candidate_character_id": 37909,
                "evaluated": [{"candidate_character_id": value}
                              for value in ids],
                "reason": "bounded_positive"}
    return {"status": "no_positive_value",
            "selected_candidate_character_id": None,
            "evaluated": [], "reason": "incomplete"}


class ChildDefaultFormalTest(unittest.TestCase):
    def test_zero_or_two_distinct_split_successors_remain_ineligible(self) -> None:
        driver = Driver(Path("."))
        original = driver.partition[:]
        driver.partition = [
            row for row in original
            if row["first_heir_character_id"] == 38822
        ]
        self.assertIsNone(consumer._split_successor(driver, driver.frame))
        driver.partition = original
        driver.partition.append({
            "primary": False, "first_heir_character_id": 39000,
            "title": {"title_id": 2174},
        })
        self.assertIsNone(consumer._split_successor(driver, driver.frame))

    def test_war_red_reads_complete_split_child_pair_and_fences_receipt(self) -> None:
        with tempfile.TemporaryDirectory(
            dir=os.environ.get("XAR_TEST_TEMP_ROOT")
        ) as folder:
            driver = Driver(Path(folder))
            planned = {"plan": {
                "selected_step": None,
                "phase": "native_war_contact_prediction_red",
                "reason": "observed contact forecast RED",
            }}
            with (
                patch.object(consumer, "bridge_process_identity",
                             return_value=(100, "submit")),
                patch.object(consumer,
                             "shortlist_specified_child_default_candidates",
                             return_value=[37909, 37571]) as shortlist,
                patch.object(consumer, "choose_specified_child_default_value",
                             side_effect=_policy),
            ):
                selected = consumer.plan_child_default_private(
                    driver, planned, driver.frame)
                shortlist.assert_called_once_with(_legality(), limit=2)
                plan = selected["plan"]
                self.assertEqual(plan["selected_step"], consumer.SUBMIT_STEP)
                self.assertEqual(driver.queried_values, [37909, 37571])
                self.assertEqual(plan["child_default_displaced_plan"], planned["plan"])
                self.assertEqual(
                    plan["child_default_observation"]["full_value_candidate_ids"],
                    [37909, 37571])
                pending = consumer.submit_child_default_private(
                    driver, plan=plan, snapshot=driver.frame)
                self.assertEqual(driver.queried_values, [
                    37909, 37571, 37909, 37571, 37909])
                self.assertEqual(pending["heir_character_id"], 38988)
                self.assertEqual(pending["candidate_character_id"], 37909)
                self.assertIs(pending["matrilineal_option_selected"], False)
                self.assertEqual(driver.submissions, 1)
                checkpoint = {
                    "status": "saved", "episode_run_id": "native-29829-test",
                    "date_raw": 53219928}
                fence = _verify_pending_family_marriage_checkpoint(
                    checkpoint, snapshot=driver.frame,
                    submitted_result=pending,
                    ledger=consumer.read_child_default_ledger(driver.state_dir),
                    expected_step=consumer.SUBMIT_STEP)
                self.assertIs(fence["matrilineal_option_selected"], False)
                self.assertIs(
                    consumer.plan_child_default_private(
                        driver, planned, driver.frame)["plan"]["selected_step"],
                    None)
                self.assertEqual(driver.submissions, 1)

    def test_missing_or_swapped_full_comparator_cannot_submit(self) -> None:
        with tempfile.TemporaryDirectory(
            dir=os.environ.get("XAR_TEST_TEMP_ROOT")
        ) as folder:
            driver = Driver(Path(folder))
            planned = {"plan": {"selected_step": "life-advance"}}
            with (
                patch.object(consumer, "bridge_process_identity",
                             return_value=(100, "submit")),
                patch.object(consumer,
                             "shortlist_specified_child_default_candidates",
                             return_value=[37909, 37571]),
                patch.object(consumer, "choose_specified_child_default_value",
                             side_effect=_policy),
            ):
                selected = consumer.plan_child_default_private(
                    driver, planned, driver.frame)["plan"]
                for changed in (
                    selected["child_default_full_values"][:1],
                    list(reversed(selected["child_default_full_values"])),
                ):
                    with self.subTest(ids=[
                        row["candidate_character_id"] for row in changed]):
                        with self.assertRaisesRegex(
                            ValueError, "split or value changed"):
                            consumer.submit_child_default_private(
                                driver,
                                plan={**selected,
                                      "child_default_full_values": changed},
                                snapshot=driver.frame)
                self.assertEqual(driver.submissions, 0)
                self.assertIsNone(
                    consumer.read_child_default_ledger(driver.state_dir)["pending"])

    def test_existing_action_or_modal_is_not_displaced(self) -> None:
        with tempfile.TemporaryDirectory(
            dir=os.environ.get("XAR_TEST_TEMP_ROOT")
        ) as folder:
            driver = Driver(Path(folder))
            action = {"plan": {"selected_step": "move-army-16777231"}}
            self.assertIs(
                consumer.plan_child_default_private(driver, action, driver.frame),
                action)
            war_query = {"plan": {
                "selected_step": "query-war-termination-options-16777231",
                "phase": "native_war_termination_query",
                "reason": "read exact native terms",
            }}
            self.assertIs(
                consumer.plan_child_default_private(
                    driver, war_query, driver.frame),
                war_query)
            modal = {**driver.frame, "active_event": {"instance_id": 1}}
            war_red = {"plan": {"selected_step": None,
                                "phase": "native_war_red", "reason": "RED"}}
            self.assertIs(
                consumer.plan_child_default_private(driver, war_red, modal),
                war_red)
            self.assertEqual(driver.queried_values, [])

    def test_lineality_mismatch_cannot_reach_submit(self) -> None:
        with tempfile.TemporaryDirectory(
            dir=os.environ.get("XAR_TEST_TEMP_ROOT")
        ) as folder:
            driver = Driver(Path(folder))
            planned = {"plan": {"selected_step": "life-advance"}}
            with (
                patch.object(consumer, "bridge_process_identity",
                             return_value=(100, "submit")),
                patch.object(consumer,
                             "shortlist_specified_child_default_candidates",
                             return_value=[37909, 37571]),
                patch.object(consumer, "choose_specified_child_default_value",
                             side_effect=_policy),
                patch.object(driver, "query_player_child_marriage_value_private_v1",
                             side_effect=[_value(37909, heir_selector=1),
                                          _value(37571)]),
            ):
                selected = consumer.plan_child_default_private(
                    driver, planned, driver.frame)
                self.assertEqual(selected["plan"]["selected_step"],
                                 "life-advance")
                self.assertIsNone(
                    consumer.read_child_default_ledger(driver.state_dir)["pending"])

    def test_pending_cold_result_and_material_recheck_never_resubmit(self) -> None:
        with tempfile.TemporaryDirectory(
            dir=os.environ.get("XAR_TEST_TEMP_ROOT")
        ) as folder:
            driver = Driver(Path(folder))
            pending = {
                "schema": consumer.ACTION_SCHEMA, "status": "receipt_pending",
                "submission_state": "receipt_pending", "material_result": False,
                "episode_run_id": "native-29829-test",
                "played_character_id": 29829, "heir_character_id": 38988,
                "candidate_character_id": 37909,
                "recipient_character_id": 34332,
                "matrilineal_option_selected": False,
                "pre_native_revision": 3, "source_date_raw": 53219928,
                "source_bridge_pid": 100,
                "source_bridge_creation_date": "submit",
            }
            consumer._write(driver.state_dir, {
                "schema": consumer.LEDGER_SCHEMA,
                "pending": pending, "resolved": None})
            driver.frame = _frame(native_revision=4)
            planned = {"plan": {"selected_step": None,
                                "phase": "native_war_red", "reason": "RED"}}
            with patch.object(consumer, "bridge_process_identity",
                              return_value=(200, "cold")):
                first = consumer.plan_child_default_private(
                    driver, planned, driver.frame)
                self.assertEqual(first["plan"]["selected_step"],
                                 consumer.RESULT_STEP)
                self.assertIs(first["plan"]["child_default_cold_recovery"], True)
                result = consumer.query_child_default_result_private(
                    driver, pending=pending, cold=True)
                self.assertEqual(result["status"], "pending")
                again = consumer.plan_child_default_private(
                    driver, planned, driver.frame)
                self.assertIsNone(again["plan"]["selected_step"])
                driver.frame = _frame(native_revision=5)
                driver.result_status = "betrothal"
                later = consumer.plan_child_default_private(
                    driver, planned, driver.frame)
                self.assertEqual(later["plan"]["selected_step"],
                                 consumer.RESULT_STEP)
                self.assertIs(later["plan"]["child_default_cold_recovery"], True)
                consumer.query_child_default_result_private(
                    driver, pending=later["plan"]["child_default_pending"],
                    cold=True)
                ledger = consumer.read_child_default_ledger(driver.state_dir)
                self.assertIsNone(ledger["pending"])
                self.assertEqual(ledger["resolved"]["status"], "betrothal")
            with patch.object(consumer, "bridge_process_identity",
                              return_value=(300, "next-cold")):
                recheck = consumer.plan_child_default_private(
                    driver, planned, driver.frame)
                self.assertEqual(recheck["plan"]["selected_step"],
                                 consumer.RESULT_STEP)
                self.assertIs(recheck["plan"]["child_default_material_recheck"],
                              True)
                consumer.query_child_default_result_private(
                    driver, pending=recheck["plan"]["child_default_pending"],
                    cold=True, material_recheck=True)
                self.assertEqual(driver.submissions, 0)
                self.assertIs(
                    consumer.read_child_default_ledger(
                        driver.state_dir)["resolved"]["cold_recovery_verified"],
                    True)

    def test_pending_result_checkpoint_releases_base_turn_and_preserves_rereads(self) -> None:
        with tempfile.TemporaryDirectory(
            dir=os.environ.get("XAR_TEST_TEMP_ROOT")
        ) as folder:
            driver = Driver(Path(folder))
            pending = {
                "schema": consumer.ACTION_SCHEMA, "status": "receipt_pending",
                "episode_run_id": "native-29829-test",
                "played_character_id": 29829, "heir_character_id": 38988,
                "candidate_character_id": 37909, "recipient_character_id": 34332,
                "pre_native_revision": 3, "source_date_raw": 53219928,
                "source_bridge_pid": 100, "source_bridge_creation_date": "submit",
            }
            consumer._write(driver.state_dir, {
                "schema": consumer.LEDGER_SCHEMA,
                "pending": pending, "resolved": None})
            driver.frame = _frame(native_revision=4)
            before = dict(driver.frame)
            with patch.object(consumer, "bridge_process_identity",
                              return_value=(100, "submit")):
                consumer.query_child_default_result_private(
                    driver, pending=pending, cold=False)
                read_ledger = consumer.read_child_default_ledger(driver.state_dir)
                driver.frame = _frame(native_revision=5)
                consumer.consume_child_default_result_checkpoint(
                    driver, ledger=read_ledger, before=before, snapshot=driver.frame)
                consumed = consumer.read_child_default_ledger(driver.state_dir)
                self.assertEqual(consumed["pending"]["last_checked_native_revision"], 4)
                self.assertEqual(consumed["pending"][
                    "last_consumed_checkpoint_native_revision"], 5)
                for step in ("life-advance", "query-army-strengths-v1", None):
                    baseline = {"plan": {"selected_step": step,
                                         "phase": "native_war_red", "reason": "RED"}}
                    planned = consumer.plan_child_default_private(
                        driver, baseline, driver.frame)
                    self.assertEqual(planned["plan"]["selected_step"], step)
                    self.assertEqual(planned["plan"]["child_default_status"],
                                     "await_later_paused_frame")
                baseline = {"plan": {"selected_step": "life-advance"}}
                driver.frame = {**_frame(native_revision=5), "date_raw": 53219952}
                later_date = consumer.plan_child_default_private(
                    driver, baseline, driver.frame)
                self.assertEqual(later_date["plan"]["selected_step"], consumer.RESULT_STEP)
                driver.frame = _frame(native_revision=6)
                later_frame = consumer.plan_child_default_private(
                    driver, baseline, driver.frame)
                self.assertEqual(later_frame["plan"]["selected_step"], consumer.RESULT_STEP)
            driver.frame = _frame(native_revision=3)
            with patch.object(consumer, "bridge_process_identity",
                              return_value=(200, "cold")):
                cold = consumer.plan_child_default_private(driver, baseline, driver.frame)
                self.assertEqual(cold["plan"]["selected_step"], consumer.RESULT_STEP)
                self.assertIs(cold["plan"]["child_default_cold_recovery"], True)
            self.assertEqual(driver.submissions, 0)

    def test_material_betrothal_reads_actual_alliance_without_resubmission(self) -> None:
        with tempfile.TemporaryDirectory(
            dir=os.environ.get("XAR_TEST_TEMP_ROOT")
        ) as folder:
            driver = Driver(Path(folder))
            pending = {
                "schema": consumer.ACTION_SCHEMA, "status": "receipt_pending",
                "submission_state": "receipt_pending", "material_result": False,
                "episode_run_id": "native-29829-test",
                "played_character_id": 29829, "heir_character_id": 38988,
                "candidate_character_id": 37909,
                "recipient_character_id": 34332,
                "matrilineal_option_selected": False,
                "pre_native_revision": 3, "source_date_raw": 53219928,
                "source_bridge_pid": 100,
                "source_bridge_creation_date": "submit",
            }
            consumer._write(driver.state_dir, {
                "schema": consumer.LEDGER_SCHEMA,
                "pending": pending, "resolved": None})
            driver.frame = _frame(native_revision=4)
            driver.result_status = "betrothal"
            baseline = {"plan": {"selected_step": "life-advance"}}
            with patch.object(consumer, "bridge_process_identity",
                              return_value=(100, "submit")):
                planned = consumer.plan_child_default_private(
                    driver, baseline, driver.frame)
                self.assertEqual(planned["plan"]["selected_step"],
                                 consumer.RESULT_STEP)
                result = consumer.query_child_default_result_private(
                    driver, pending=planned["plan"]["child_default_pending"],
                    cold=False)
                self.assertEqual(result["status"], "betrothal")
                alliance_plan = consumer.plan_child_default_private(
                    driver, baseline, driver.frame)
                self.assertEqual(alliance_plan["plan"]["selected_step"],
                                 consumer.ALLIANCE_RESULT_STEP)
                actual = consumer.query_child_default_alliance_private(
                    driver, resolved=alliance_plan["plan"][
                        "child_default_resolved"])
                self.assertEqual(actual["alliance_status"], "not_allied")
                finished = consumer.plan_child_default_private(
                    driver, baseline, driver.frame)
                self.assertEqual(finished["plan"]["selected_step"],
                                 "life-advance")
                self.assertEqual(driver.submissions, 0)


    def test_warm_refusal_reconsiders_only_remaining_compared_candidate(self) -> None:
        with tempfile.TemporaryDirectory(
            dir=os.environ.get("XAR_TEST_TEMP_ROOT")
        ) as folder:
            driver = Driver(Path(folder))
            driver.frame = _frame(native_revision=4)
            rejected = {
                "status": "refused", "material_result": False,
                "episode_run_id": driver.frame["episode_run_id"],
                "heir_character_id": 38988,
                "candidate_character_id": 37909,
                "recipient_character_id": 34332,
                "post_bridge_pid": 100,
                "post_bridge_creation_date": "same-pid",
                "source_pending": {
                    "played_character_id": 29829,
                    "heir_character_id": 38988,
                    "candidate_character_id": 37909,
                    "recipient_character_id": 34332,
                    "episode_run_id": driver.frame["episode_run_id"],
                },
            }
            consumer._write(driver.state_dir, {
                "schema": consumer.LEDGER_SCHEMA,
                "pending": None, "resolved": rejected,
            })
            planned = {"plan": {"selected_step": "life-advance"}}

            def choose_remaining(_legality: object, values: object, *,
                                 split_successor_verified: bool,
                                 rejected_candidate_ids: frozenset[int] = frozenset()
                                 ) -> dict[str, object]:
                ids = [row["candidate_character_id"] for row in values]
                if (split_successor_verified
                        and ids == [37909, 37571]
                        and rejected_candidate_ids == frozenset({37909})):
                    return {"status": "selected",
                            "selected_candidate_character_id": 37571,
                            "evaluated": [{"candidate_character_id": 37571}],
                            "reason": "bounded_positive"}
                return {"status": "no_positive_value",
                        "selected_candidate_character_id": None,
                        "evaluated": [], "reason": "not_remaining"}

            with (
                patch.object(consumer, "bridge_process_identity",
                             return_value=(100, "same-pid")),
                patch.object(consumer,
                             "shortlist_specified_child_default_candidates",
                             return_value=[37909, 37571]),
                patch.object(consumer, "choose_specified_child_default_value",
                             side_effect=choose_remaining),
            ):
                choice = consumer.plan_child_default_private(
                    driver, planned, driver.frame)["plan"]
                self.assertEqual(choice["selected_step"], consumer.SUBMIT_STEP)
                self.assertEqual(choice["child_default_value"]["candidate_character_id"],
                                 37571)
                self.assertEqual(driver.queried_values, [37909, 37571])
                pending = consumer.submit_child_default_private(
                    driver, plan=choice, snapshot=driver.frame)
                self.assertEqual(pending["candidate_character_id"], 37571)
                self.assertEqual(pending["prior_rejected_candidate_ids"],
                                 [37909])
                self.assertEqual(driver.queried_values,
                                 [37909, 37571, 37909, 37571, 37571])
                waiting = consumer.plan_child_default_private(
                    driver, planned, driver.frame)["plan"]
                self.assertEqual(waiting["selected_step"], "life-advance")
                driver.frame = _frame(native_revision=5)
                driver.result_status = "refused"
                read_plan = consumer.plan_child_default_private(
                    driver, planned, driver.frame)["plan"]
                self.assertEqual(read_plan["selected_step"], consumer.RESULT_STEP)
                consumer.query_child_default_result_private(
                    driver, pending=read_plan["child_default_pending"], cold=False)
            resolved = consumer.read_child_default_ledger(driver.state_dir)["resolved"]
            self.assertEqual(resolved["rejected_candidate_ids"], [37571, 37909])
            self.assertEqual(driver.submissions, 1)

    def test_cold_restored_refusal_reconsiders_without_rejected_resend(self) -> None:
        with tempfile.TemporaryDirectory(
            dir=os.environ.get("XAR_TEST_TEMP_ROOT")
        ) as folder:
            driver = Driver(Path(folder))
            driver.frame = _frame(native_revision=4)
            rejected = {
                "status": "refused", "material_result": False,
                "episode_run_id": driver.frame["episode_run_id"],
                "heir_character_id": 38988,
                "candidate_character_id": 37909,
                "recipient_character_id": 34332,
                "post_bridge_pid": 100,
                "post_bridge_creation_date": "old-pid",
                "source_pending": {
                    "played_character_id": 29829,
                    "heir_character_id": 38988,
                    "candidate_character_id": 37909,
                    "recipient_character_id": 34332,
                    "episode_run_id": driver.frame["episode_run_id"],
                },
            }
            consumer._write(driver.state_dir, {
                "schema": consumer.LEDGER_SCHEMA,
                "pending": None, "resolved": rejected,
            })
            def choose_remaining(_legality: object, values: object, *,
                                 split_successor_verified: bool,
                                 rejected_candidate_ids: frozenset[int] = frozenset()
                                 ) -> dict[str, object]:
                ids = [row["candidate_character_id"] for row in values]
                if (split_successor_verified and ids == [37909, 37571]
                        and rejected_candidate_ids == frozenset({37909})):
                    return {"status": "selected",
                            "selected_candidate_character_id": 37571,
                            "evaluated": [{"candidate_character_id": value}
                                          for value in ids],
                            "reason": "bounded_positive"}
                return {"status": "no_positive_value",
                        "selected_candidate_character_id": None,
                        "evaluated": [], "reason": "not_remaining"}
            with (
                patch.object(consumer, "bridge_process_identity",
                             return_value=(200, "restored-pid")),
                patch.object(consumer,
                             "shortlist_specified_child_default_candidates",
                             return_value=[37909, 37571]),
                patch.object(consumer, "choose_specified_child_default_value",
                             side_effect=choose_remaining),
            ):
                choice = consumer.plan_child_default_private(
                    driver, {"plan": {"selected_step": "life-advance"}},
                    driver.frame)["plan"]
            self.assertEqual(choice["selected_step"], consumer.SUBMIT_STEP)
            self.assertEqual(choice["child_default_value"]["candidate_character_id"],
                             37571)
            self.assertEqual(driver.queried_values, [37909, 37571])
            self.assertEqual(driver.submissions, 0)


if __name__ == "__main__":
    unittest.main()
