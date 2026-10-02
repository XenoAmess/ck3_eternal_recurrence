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


DATE = combined.EXPECTED_DATE_RAW


def _army(army_id: int, owner: int, province: int, *, controllable: bool,
          route: list[int] | None = None) -> dict[str, object]:
    route = [] if route is None else route
    return {
        "army_id": army_id, "owner_character_id": owner,
        "current_province_id": province,
        "move_target_province_id": route[-1] if route else None,
        "move_target_observable": bool(route), "route_province_ids": route,
        "route_read_status": "complete_nonempty" if route else "complete_empty",
        "route_source_count": len(route),
        "army_state": "moving" if route else "regular",
        "army_state_code": 7 if route else 1,
        "in_combat": False, "retreating": False,
        "controllable": controllable,
    }


def _frame() -> dict[str, object]:
    player = _army(combined.ARMY_ID, 29829, 2610, controllable=True)
    return {
        "snapshot_id": "native:4", "revision": 5, "native_revision": 4,
        "date_raw": DATE,
        "route_contact_horizon_supported": True,
        "episode_run_id": combined.EXPECTED_EPISODE_RUN_ID,
        "episode_character_id": 29829, "paused": True, "map_ready": True,
        "diagnostics": {"connection_generation": 1},
        "played_character": {"character_id": 29829},
        "active_event": None, "pending_character_interaction": None,
        "player_armies": [player],
        "active_wars": [{
            "war_id": 16777231, "player_side": "defender",
            "objective_province_states": [],
            "allied_armies": [copy.deepcopy(player)],
            "enemy_armies": [
                _army(40001, 30097, 2629, controllable=False),
                _army(40002, 35357, 2630, controllable=False,
                      route=[2631, 2610]),
            ],
        }],
        "native_command_history": [{"command": "restore-checkpoint", "ok": True}],
    }


def _province_result(*, partial: bool = False) -> dict[str, object]:
    return {
        "step": "query-province-local-siege-v1-2610",
        "accepted": True, "status": "partial" if partial else "available",
        "query_sequence": 1, "snapshot_revision": 4, "date_raw": DATE,
        "province_state": {
            "province_id": 2610, "occupation_observable": True,
            "is_occupied": False, "occupying_character_id": None,
            "fort_level": 2, "garrison_size": 500, "besieging_strength": 0,
            "siege_observable": not partial, "active_siege": None,
        },
        "backend_id": "native-headless",
    }


def _timed_route(army_id: int, province: int,
                 route: list[int], arrivals: list[int]) -> dict[str, object]:
    return {
        "timeline_observable": True, "army_id": army_id,
        "current_province_id": province,
        "effective_origin_province_id": province,
        "route_province_ids": route, "arrival_date_raws": arrivals,
    }


def _contact_result(step: str) -> dict[str, object]:
    return {
        "step": step, "accepted": True, "status": "available",
        # Native query_sequence counters are per query family, not global.
        "query_sequence": 1, "snapshot_revision": 4,
        "backend_id": "native-headless",
        "queried_snapshot_id": "native:4", "queried_revision": 5,
        "queried_native_revision": 4,
        "queried_connection_generation": 1,
        "queried_episode_run_id": combined.EXPECTED_EPISODE_RUN_ID,
        "route_contact_horizon": {
            "status": "available", "date_raw": DATE,
            "snapshot_revision": 4, "subject_army_id": combined.ARMY_ID,
            "target_province_id": 2610, "hostile_army_ids": [40001, 40002],
            "subject_route": _timed_route(combined.ARMY_ID, 2610, [], []),
            "hostile_routes": [
                _timed_route(40001, 2629, [], []),
                _timed_route(40002, 2630, [2631, 2610],
                             [DATE + 24, DATE + 48]),
            ],
            "horizon_start_date_raw": DATE,
            "horizon_end_date_raw": DATE + 24,
            "one_day_contact_free": True, "conflicts": [],
        },
    }


def _after(before: dict[str, object], step: str,
           result: dict[str, object]) -> dict[str, object]:
    frame = copy.deepcopy(before)
    frame["native_command_history"].append({
        "command": step, "ok": True, "result": copy.deepcopy(result),
    })
    return frame


class H3937CombinedReadOnlyQueriesTests(unittest.TestCase):
    def test_disabled_gate_precedes_snapshot_and_queries(self) -> None:
        service = SimpleNamespace(snapshot=Mock(), execute_step=Mock())
        with self.assertRaisesRegex(combined.AgentError, "no live authorization"):
            combined.collect_h3937_combined_reads_in_session(service)
        service.snapshot.assert_not_called()
        service.execute_step.assert_not_called()

    def test_dynamic_nonhistorical_hostiles_two_queries_same_frame(self) -> None:
        first = _frame()
        province = _province_result()
        middle = _after(first, province["step"], province)
        contact_step = combined.query_route_contact_horizon_step(
            combined.ARMY_ID, 2610, [40001, 40002])
        contact = _contact_result(contact_step)
        last = _after(middle, contact_step, contact)
        service = SimpleNamespace(
            snapshot=Mock(side_effect=[first, middle, last]),
            execute_step=Mock(side_effect=[province, contact]),
        )
        with patch.object(combined, "H3937_COMBINED_LIVE_AUTHORIZED", True):
            result = combined.collect_h3937_combined_reads_in_session(service)
        self.assertTrue(result["observed"], result["error"])
        self.assertEqual(result["query_attempts"], 2)
        self.assertEqual(result["steps"], [province["step"], contact_step])
        self.assertEqual(result["scope"]["query_eligible_hostile_army_ids"],
                         [40001, 40002])
        self.assertFalse(result["physical_army_inventory_completeness_proven"])
        self.assertFalse(result["outer_session_cleanup_verified"])
        self.assertFalse(result["action_authorized"])
        self.assertFalse(result["date_advance_authorized"])
        self.assertEqual(service.execute_step.call_args_list[1].kwargs,
                         {"expected_revision": 5})

    def test_contact_current_or_route_must_match_same_frame_war_rows(self) -> None:
        for mutation in ("current_province", "route_province"):
            with self.subTest(mutation=mutation):
                first = _frame()
                province = _province_result()
                middle = _after(first, province["step"], province)
                contact_step = combined.query_route_contact_horizon_step(
                    combined.ARMY_ID, 2610, [40001, 40002])
                contact = _contact_result(contact_step)
                hostile_route = contact["route_contact_horizon"]["hostile_routes"][1]
                if mutation == "current_province":
                    hostile_route["current_province_id"] = 2632
                    hostile_route["effective_origin_province_id"] = 2632
                else:
                    hostile_route["route_province_ids"] = [2632, 2610]
                last = _after(middle, contact_step, contact)
                service = SimpleNamespace(
                    snapshot=Mock(side_effect=[first, middle, last]),
                    execute_step=Mock(side_effect=[province, contact]),
                )
                with patch.object(combined, "H3937_COMBINED_LIVE_AUTHORIZED", True):
                    result = combined.collect_h3937_combined_reads_in_session(service)
                self.assertFalse(result["observed"])
                self.assertEqual(result["query_attempts"], 2)
                self.assertFalse(result["checks"]["dynamic_contact_bound"])
                self.assertFalse(result["action_authorized"])
                self.assertFalse(result["date_advance_authorized"])

    def test_unresolved_route_stops_before_any_query(self) -> None:
        first = _frame()
        first["active_wars"][0]["enemy_armies"][1]["route_read_status"] = (
            "unresolved_entry")
        service = SimpleNamespace(
            snapshot=Mock(return_value=first), execute_step=Mock())
        with patch.object(combined, "H3937_COMBINED_LIVE_AUTHORIZED", True):
            result = combined.collect_h3937_combined_reads_in_session(service)
        self.assertFalse(result["observed"])
        self.assertEqual(result["query_attempts"], 0)
        service.execute_step.assert_not_called()

    def test_player_moving_stops_before_any_query(self) -> None:
        first = _frame()
        moving = _army(combined.ARMY_ID, 29829, 2610,
                       controllable=True, route=[2614])
        first["player_armies"] = [moving]
        first["active_wars"][0]["allied_armies"] = [copy.deepcopy(moving)]
        service = SimpleNamespace(
            snapshot=Mock(return_value=first), execute_step=Mock())
        with patch.object(combined, "H3937_COMBINED_LIVE_AUTHORIZED", True):
            result = combined.collect_h3937_combined_reads_in_session(service)
        self.assertFalse(result["observed"])
        self.assertEqual(result["query_attempts"], 0)
        service.execute_step.assert_not_called()

    def test_partial_province_stops_before_contact(self) -> None:
        first = _frame()
        province = _province_result(partial=True)
        middle = _after(first, province["step"], province)
        service = SimpleNamespace(
            snapshot=Mock(side_effect=[first, middle]),
            execute_step=Mock(return_value=province))
        with patch.object(combined, "H3937_COMBINED_LIVE_AUTHORIZED", True):
            result = combined.collect_h3937_combined_reads_in_session(service)
        self.assertFalse(result["observed"])
        self.assertEqual(result["query_attempts"], 1)
        self.assertEqual(service.execute_step.call_count, 1)

    def test_missing_route_contact_capability_stops_after_province(self) -> None:
        first = _frame()
        first["route_contact_horizon_supported"] = False
        province = _province_result()
        middle = _after(first, province["step"], province)
        service = SimpleNamespace(
            snapshot=Mock(side_effect=[first, middle]),
            execute_step=Mock(return_value=province))
        with patch.object(combined, "H3937_COMBINED_LIVE_AUTHORIZED", True):
            result = combined.collect_h3937_combined_reads_in_session(service)
        self.assertFalse(result["observed"])
        self.assertEqual(result["query_attempts"], 1)
        self.assertFalse(result["checks"]["route_contact_capability_advertised"])
        self.assertEqual(service.execute_step.call_count, 1)

    def test_changed_roster_after_province_stops_before_contact(self) -> None:
        first = _frame()
        province = _province_result()
        middle = _after(first, province["step"], province)
        middle["active_wars"][0]["enemy_armies"][0]["current_province_id"] = 2610
        service = SimpleNamespace(
            snapshot=Mock(side_effect=[first, middle]),
            execute_step=Mock(return_value=province))
        with patch.object(combined, "H3937_COMBINED_LIVE_AUTHORIZED", True):
            result = combined.collect_h3937_combined_reads_in_session(service)
        self.assertFalse(result["observed"])
        self.assertEqual(result["query_attempts"], 1)
        self.assertFalse(result["checks"]["province_scope_unchanged"])
        self.assertEqual(service.execute_step.call_count, 1)


if __name__ == "__main__":
    unittest.main()
