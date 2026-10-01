"""Production planner regression: an unavailable faction root is domain scoped."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from test_m5_peacetime_proposal_sources_v1 import (
    _Driver, _FRAME, _construction, _snapshot,
)
from xar_autoplayer.m5_formal_proposal_collector import plan_m5_formal_query_only
from xar_autoplayer.lifestyle_formal_consumer import ROOT_QUERY_STEP


def unavailable_root_history() -> list[dict[str, object]]:
    return [{
        "command": ROOT_QUERY_STEP, "ok": True,
        "result": {
            "step": ROOT_QUERY_STEP, "accepted": True,
            "status": "unavailable",
            "snapshot_revision": _FRAME["native_revision"],
            "campaign_root_context": {
                "status": "unavailable",
                "snapshot_revision": _FRAME["native_revision"],
                "date_raw": _FRAME["date_raw"],
                "player_character_id": None,
                "unavailable_reason": "state_changed",
            },
        },
    }]


class M5IndependentBuildingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.temporary.name) / "state"
        self.state_dir.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def plan(self, *, building: dict[str, object],
             history: list[dict[str, object]] | None = None,
             baseline_step: str = "life-advance") -> tuple[dict[str, object], _Driver, object]:
        snapshot = _snapshot()
        snapshot["native_command_history"] = deepcopy(
            unavailable_root_history() if history is None else history)
        driver = _Driver(self.state_dir, snapshot=snapshot)
        with mock.patch(
            "xar_autoplayer.m5_peacetime_proposal_sources_v1.query_construction_private",
            return_value=building,
        ) as reader:
            planned = plan_m5_formal_query_only(
                driver,
                {"revision": _FRAME["revision"], "plan": {
                    "policy": "one-life-turn-v1", "phase": "peace_growth",
                    "selected_step": baseline_step,
                }},
                snapshot=driver.take_snapshot(),
                history=snapshot["native_command_history"],
                available_steps={"life-advance", ROOT_QUERY_STEP},
            )
        return planned, driver, reader

    def test_available_peace_building_survives_unavailable_faction_root(self) -> None:
        building = _construction()
        building["candidate"]["authored_monthly_income_hundredths"] = 35
        planned, driver, reader = self.plan(building=building)
        plan = planned["plan"]
        self.assertEqual(plan["selected_step"], "private-submit-player-construction-v1")
        self.assertEqual(plan["construction_private_query"], building)
        collection = plan["m5_joint_query_only"]
        self.assertEqual(collection["incomplete_domains"], ["diplomacy"])
        self.assertEqual(collection["producer_faction_status"], "same_frame_root_unavailable")
        self.assertEqual(collection["collected_domains"], ["building"])
        reservation = collection["dispatch"]["reservation"]
        self.assertEqual(reservation["commitments_after"]["gold_raw"], 3_000_000)
        self.assertEqual(reservation["commitments_after"]["pending_war_slots"], 0)
        self.assertEqual(driver.source_reads, 1)
        self.assertEqual(driver.faction_reads, 0)
        reader.assert_called_once()

    def test_no_independent_proposal_does_not_release_date_hold(self) -> None:
        planned, driver, reader = self.plan(
            building=_construction(status="no_legal_budgeted_building"))
        plan = planned["plan"]
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(plan["phase"], "m5_joint_root_unavailable_independent_family")
        self.assertEqual(plan["m5_joint_query_only"]["incomplete_domains"], ["diplomacy"])
        self.assertFalse(plan["m5_joint_formal_action_ready"])
        self.assertEqual(driver.faction_reads, 0)
        reader.assert_called_once()

    def test_unqueried_root_still_uses_existing_query_before_comparison(self) -> None:
        planned, driver, reader = self.plan(building=_construction(), history=[])
        self.assertEqual(planned["plan"]["selected_step"], ROOT_QUERY_STEP)
        self.assertEqual(driver.source_reads, 0)
        reader.assert_not_called()

    def test_on_send_pending_marriage_roles_are_reserved_once(self) -> None:
        pending = {
            "episode_run_id": _FRAME["episode_run_id"],
            "played_character_id": 29829,
            "heir_character_id": 38988,
            "candidate_character_id": 37909,
            "recipient_character_id": 34332,
            "claimed_character_ids": [29829, 38988, 37909, 34332],
            "selected_value_projection": {
                "generic_costs": {"gold_raw": 0, "application_timing": "on_send"},
                "possible_alliance_pairs": [{
                    "first_character_id": 29829, "second_character_id": 37909,
                    "would_attempt_if_accepted": False,
                }],
            },
        }
        path = self.state_dir / "player-child-default-formal-v1.json"
        ledger = {"schema": "xar.ck3.player-child-default-formal.v1",
                  "pending": pending, "resolved": None}
        path.write_text(json.dumps(ledger), encoding="utf-8")
        before = path.read_bytes()
        building = _construction()
        building["candidate"]["authored_monthly_income_hundredths"] = 35
        planned, driver, reader = self.plan(building=building)
        self.assertEqual(planned["plan"]["selected_step"],
                         "private-submit-player-construction-v1")
        after = planned["plan"]["m5_joint_query_only"]["dispatch"]["reservation"]["commitments_after"]
        self.assertEqual(after["character_ids"], [34332, 37909, 38988])
        self.assertEqual(after["gold_raw"], 3_000_000)
        self.assertEqual(after["commitment_keys"], [
            "building-slot:501:1", "player-child-default-marriage:38988"])
        self.assertEqual(path.read_bytes(), before)

    def test_existing_war_or_receipt_step_keeps_its_own_priority(self) -> None:
        for step in ("query-war-termination-options-16777231", "save-checkpoint"):
            with self.subTest(step=step):
                planned, driver, reader = self.plan(
                    building=_construction(), baseline_step=step)
                self.assertEqual(planned["plan"]["selected_step"], step)
                self.assertEqual(driver.source_reads, 0)
                reader.assert_not_called()

    def test_existing_first_heir_roles_survive_submit_opt_out(self) -> None:
        pending = {
            "episode_run_id": _FRAME["episode_run_id"],
            "played_character_id": 29829,
            "heir_character_id": 38822,
            "candidate_character_id": 38718,
            "recipient_character_id": 32897,
            "preproposal_realm_alliance_attempt_if_accepted": False,
        }
        path = self.state_dir / "first-heir-marriage-formal-v1.json"
        path.write_text(json.dumps({
            "schema": "xar.ck3.first-heir-marriage-formal.v1",
            "pending": pending, "resolved": None,
        }), encoding="utf-8")
        before = path.read_bytes()
        building = _construction()
        building["candidate"]["authored_monthly_income_hundredths"] = 35
        planned, driver, reader = self.plan(building=building)
        self.assertFalse(driver.allow_private_family_marriage_formal_trial)
        self.assertEqual(driver.family_reads, 0)
        reservation = planned["plan"]["m5_joint_query_only"]["dispatch"]["reservation"]
        claims = reservation["commitments_after"]
        self.assertEqual(claims["character_ids"], [32897, 38718, 38822])
        self.assertEqual(claims["ally_character_ids"], [])
        self.assertEqual(claims["commitment_keys"], [
            "building-slot:501:1", "first-heir-marriage:38822"])
        self.assertEqual(claims["gold_raw"], 3_000_000)
        self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
