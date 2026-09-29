from __future__ import annotations

import copy
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import xar_autoplayer.h3937_combined_readonly_queries as combined
import xar_autoplayer.h3937_target_readonly_queries as target
from xar_autoplayer.bridge.war_contract import army_strength_scope
from ck3_autonomous_player.tests.unit.test_h3937_combined_readonly_queries import (
    _after, _contact_result, _frame, _province_result, _timed_route,
)


def _strength_result(frame: dict[str, object]) -> dict[str, object]:
    rows = []
    for scope in army_strength_scope(frame):
        rows.append({
            "status": "available", "army_id": scope["army_id"],
            "native_carmy_id": scope["army_id"],
            "scope_role": scope["scope_role"], "war_ids": scope["war_ids"],
            "regiment_count": 1, "current_soldiers": 1000,
            "maximum_soldiers": 1100,
            "ai_base_power_raw": 100000000,
            "ai_base_power_scale": 100000, "unavailable_reason": None,
        })
    return {
        "step": "query-army-strengths-v1", "accepted": True,
        "status": "available", "query_sequence": 1,
        "army_strengths": rows, "backend_id": "native-headless",
        "queried_snapshot_id": frame["snapshot_id"],
        "queried_revision": frame["revision"],
        "queried_native_revision": frame["native_revision"],
    }


def _target_province_result() -> dict[str, object]:
    result = _province_result()
    result["step"] = "query-province-local-siege-v1-2629"
    result["query_sequence"] = 2
    result["province_state"]["province_id"] = 2629
    return result


def _preview_result(frame: dict[str, object]) -> dict[str, object]:
    army_id = target.ARMY_ID
    return {
        "step": f"preview-move-army-{army_id}-to-2629",
        "accepted": True, "status": "available", "backend_id": "native-headless",
        "route_preview": {
            "status": "available", "army_id": army_id,
            "origin_province_id": 2610, "target_province_id": 2629,
            "route_province_ids": [2614, 2629],
            "previewed_date_raw": target.EXPECTED_DATE_RAW,
        },
        "queried_snapshot_id": frame["snapshot_id"],
        "queried_revision": frame["revision"],
        "queried_native_revision": frame["native_revision"],
        "queried_connection_generation": 1,
        "queried_episode_run_id": target.EXPECTED_EPISODE_RUN_ID,
    }


def _target_contact_result(frame: dict[str, object]) -> dict[str, object]:
    step = target.query_route_contact_horizon_step(
        target.ARMY_ID, 2629, (40001, 40002))
    result = _contact_result(step)
    horizon = result["route_contact_horizon"]
    horizon["target_province_id"] = 2629
    result["query_sequence"] = 2
    horizon["subject_route"] = _timed_route(
        target.ARMY_ID, 2610, [2614, 2629],
        [target.EXPECTED_DATE_RAW + 48, target.EXPECTED_DATE_RAW + 96],
    )
    return result


def _sequence() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    first = _frame()
    war = first["active_wars"][0]
    war["player_is_primary_war_leader"] = True
    war["player_relative_war_score"] = -21
    siege_enemy = war["enemy_armies"][0]
    siege_enemy["army_state"] = "sieging"
    siege_enemy["army_state_code"] = 3
    province_home = _province_result()
    middle = _after(first, province_home["step"], province_home)
    contact_home = _contact_result(target.query_route_contact_horizon_step(
        target.ARMY_ID, 2610, (40001, 40002)))
    last_local = _after(middle, contact_home["step"], contact_home)
    strengths = _strength_result(last_local)
    after_strengths = _after(last_local, strengths["step"], strengths)
    after_strengths.update({
        "army_strengths_status": "available",
        "army_strengths": copy.deepcopy(strengths["army_strengths"]),
        "army_strengths_query_sequence": strengths["query_sequence"],
        "army_strengths_queried_snapshot_id": first["snapshot_id"],
        "army_strengths_queried_revision": first["revision"],
    })
    province_target = _target_province_result()
    after_target = _after(after_strengths, province_target["step"], province_target)
    preview = _preview_result(after_target)
    after_preview = _after(after_target, preview["step"], preview)
    contact_target = _target_contact_result(after_preview)
    final = _after(after_preview, contact_target["step"], contact_target)
    return (
        [first, middle, last_local, copy.deepcopy(last_local),
         after_strengths, after_target, after_preview, final],
        [province_home, contact_home, strengths,
         province_target, preview, contact_target],
    )


def _run(
    frames: list[dict[str, object]], results: list[dict[str, object]],
) -> tuple[dict[str, object], SimpleNamespace]:
    service = SimpleNamespace(
        snapshot=Mock(side_effect=frames),
        execute_step=Mock(side_effect=results),
    )
    with patch.object(target, "H3937_TARGET_LIVE_AUTHORIZED", True), patch.object(
        combined, "H3937_COMBINED_LIVE_AUTHORIZED", True
    ):
        receipt = target.collect_h3937_target_reads_in_session(service)
    return receipt, service


class H3937TargetReadOnlyQueriesTests(unittest.TestCase):
    def test_disabled_gate_makes_no_service_call(self) -> None:
        service = SimpleNamespace(snapshot=Mock(), execute_step=Mock())
        with self.assertRaisesRegex(target.AgentError, "no live authorization"):
            target.collect_h3937_target_reads_in_session(service)
        service.snapshot.assert_not_called()
        service.execute_step.assert_not_called()

    def test_dynamic_target_four_extra_reads_remain_read_only(self) -> None:
        frames, results = _sequence()
        receipt, service = _run(frames, results)
        self.assertTrue(receipt["observed"], receipt["error"])
        self.assertEqual(receipt["query_attempts"], 6)
        self.assertEqual(receipt["selected_siege"]["target_province_id"], 2629)
        self.assertEqual(receipt["target_route_province_ids"], [2614, 2629])
        self.assertEqual(service.execute_step.call_count, 6)
        self.assertFalse(receipt["first_hop_contact_observed"])
        self.assertFalse(receipt["physical_army_inventory_completeness_proven"])
        self.assertFalse(receipt["action_authorized"])
        self.assertFalse(receipt["date_advance_authorized"])

    def test_no_current_sieging_enemy_stops_after_strengths(self) -> None:
        frames, results = _sequence()
        for frame in frames:
            frame["active_wars"][0]["enemy_armies"][0]["army_state"] = "regular"
            frame["active_wars"][0]["enemy_armies"][0]["army_state_code"] = 1
        receipt, service = _run(frames, results)
        self.assertFalse(receipt["observed"])
        self.assertEqual(receipt["query_attempts"], 3)
        self.assertIsNone(receipt["selected_siege"])
        self.assertEqual(service.execute_step.call_count, 3)

    def test_partial_strength_stops_before_target_query(self) -> None:
        frames, results = _sequence()
        results[2]["status"] = "partial"
        frames[4]["native_command_history"][-1]["result"]["status"] = "partial"
        receipt, service = _run(frames, results)
        self.assertFalse(receipt["observed"])
        self.assertEqual(receipt["query_attempts"], 3)
        self.assertFalse(receipt["checks"]["strengths_same_frame_cache"])
        self.assertEqual(service.execute_step.call_count, 3)

    def test_target_contact_route_disagrees_with_preview(self) -> None:
        frames, results = _sequence()
        subject = results[-1]["route_contact_horizon"]["subject_route"]
        subject["route_province_ids"] = [2615, 2629]
        frames[-1]["native_command_history"][-1]["result"] = copy.deepcopy(results[-1])
        receipt, service = _run(frames, results)
        self.assertFalse(receipt["observed"])
        self.assertEqual(receipt["query_attempts"], 6)
        self.assertFalse(receipt["checks"]["target_contact_bound"])
        self.assertFalse(receipt["action_authorized"])

    def test_stale_strength_cache_stops_before_target_query(self) -> None:
        frames, results = _sequence()
        frames[4]["army_strengths_queried_snapshot_id"] = "native:old"
        receipt, service = _run(frames, results)
        self.assertFalse(receipt["observed"])
        self.assertEqual(receipt["query_attempts"], 3)
        self.assertFalse(receipt["checks"]["strengths_same_frame_cache"])
        self.assertEqual(service.execute_step.call_count, 3)

    def test_partial_target_province_stops_before_preview(self) -> None:
        frames, results = _sequence()
        results[3]["status"] = "partial"
        results[3]["province_state"]["siege_observable"] = False
        frames[5]["native_command_history"][-1]["result"] = copy.deepcopy(results[3])
        receipt, service = _run(frames, results)
        self.assertFalse(receipt["observed"])
        self.assertEqual(receipt["query_attempts"], 4)
        self.assertFalse(receipt["checks"]["target_province_available"])
        self.assertEqual(service.execute_step.call_count, 4)

    def test_stale_target_preview_stops_before_contact(self) -> None:
        frames, results = _sequence()
        results[4]["queried_native_revision"] = 3
        frames[6]["native_command_history"][-1]["result"] = copy.deepcopy(results[4])
        receipt, service = _run(frames, results)
        self.assertFalse(receipt["observed"])
        self.assertEqual(receipt["query_attempts"], 5)
        self.assertFalse(receipt["checks"]["full_target_preview_bound"])
        self.assertEqual(service.execute_step.call_count, 5)

    def test_contact_with_wrong_hostile_position_stays_red(self) -> None:
        frames, results = _sequence()
        hostile = results[-1]["route_contact_horizon"]["hostile_routes"][1]
        hostile["current_province_id"] = 2632
        hostile["effective_origin_province_id"] = 2632
        frames[-1]["native_command_history"][-1]["result"] = copy.deepcopy(results[-1])
        receipt, _ = _run(frames, results)
        self.assertFalse(receipt["observed"])
        self.assertFalse(receipt["checks"]["target_contact_bound"])
        self.assertFalse(receipt["date_advance_authorized"])

    def test_invalid_physical_mailbox_candidate_stays_red(self) -> None:
        frames, results = _sequence()
        results[-1]["physical_army_inventory_check"] = {
            "valid": False, "date_or_action_authorized": False,
        }
        frames[-1]["native_command_history"][-1]["result"] = copy.deepcopy(results[-1])
        receipt, _ = _run(frames, results)
        self.assertFalse(receipt["observed"])
        self.assertFalse(receipt["checks"]["target_contact_bound"])
        self.assertFalse(receipt["physical_army_inventory_completeness_proven"])

    def test_current_target_is_not_historical_2629_literal(self) -> None:
        frames, results = _sequence()
        for frame in frames:
            enemies = frame["active_wars"][0]["enemy_armies"]
            enemies[0]["current_province_id"] = 2640
        results[1]["route_contact_horizon"]["hostile_routes"][0]["current_province_id"] = 2640
        results[1]["route_contact_horizon"]["hostile_routes"][0]["effective_origin_province_id"] = 2640
        results[-1]["route_contact_horizon"]["hostile_routes"][0]["current_province_id"] = 2640
        results[-1]["route_contact_horizon"]["hostile_routes"][0]["effective_origin_province_id"] = 2640
        results[3]["step"] = "query-province-local-siege-v1-2640"
        results[3]["province_state"]["province_id"] = 2640
        results[4]["step"] = f"preview-move-army-{target.ARMY_ID}-to-2640"
        results[4]["route_preview"]["target_province_id"] = 2640
        results[4]["route_preview"]["route_province_ids"] = [2614, 2640]
        results[5]["step"] = target.query_route_contact_horizon_step(
            target.ARMY_ID, 2640, (40001, 40002))
        results[5]["route_contact_horizon"]["target_province_id"] = 2640
        results[5]["route_contact_horizon"]["subject_route"]["route_province_ids"] = [2614, 2640]
        for frame in frames[1:]:
            history = frame["native_command_history"]
            for index, result in enumerate(results[:len(history) - 1], start=1):
                history[index]["command"] = result["step"]
                history[index]["result"] = copy.deepcopy(result)
        receipt, service = _run(frames, results)
        self.assertTrue(receipt["observed"], receipt["error"])
        self.assertEqual(receipt["selected_siege"]["target_province_id"], 2640)
        self.assertEqual(service.execute_step.call_args_list[3].args[0],
                         "query-province-local-siege-v1-2640")
        self.assertFalse(receipt["action_authorized"])

    def test_intervening_query_after_combined_stops_before_strengths(self) -> None:
        frames, results = _sequence()
        frames[3]["native_command_history"].append({
            "command": "query-unrelated-v1", "ok": True,
        })
        receipt, service = _run(frames, results)
        self.assertFalse(receipt["observed"])
        self.assertEqual(receipt["query_attempts"], 2)
        self.assertFalse(receipt["checks"]["combined_final_snapshot_reobserved"])
        self.assertEqual(service.execute_step.call_count, 2)


if __name__ == "__main__":
    unittest.main()
