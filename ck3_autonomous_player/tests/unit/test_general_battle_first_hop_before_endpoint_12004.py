from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest
from unittest import mock


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.war_contract import (
    QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY,
    normalize_route_contact_horizon,
    query_combat_simulation_inputs_step,
    query_route_contact_horizon_step,
)
from xar_autoplayer.strategy import _general_battle_forecast_ingress


def _snapshot() -> dict[str, object]:
    # Synthetic current frame; no dated campaign opponent is reused here.
    return {
        "paused": True,
        "snapshot_id": "first-hop-frame-12004",
        "revision": 7,
        "native_revision": 9,
        "date_raw": 1_000,
        "episode_run_id": "first-hop-12004",
        "diagnostics": {"connection_generation": 3},
        "player_armies": [{"army_id": 11, "current_province_id": 30}],
        "active_wars": [{
            "war_id": 1,
            "allied_armies": [{
                "army_id": 11, "current_province_id": 30, "controllable": True,
            }],
            "enemy_armies": [{
                "army_id": 21, "current_province_id": 31, "army_state": "sieging",
            }],
        }],
    }


def _preview(target: int, route: list[int], index: int) -> dict[str, object]:
    return {
        "index": index,
        "command": f"preview-move-army-11-to-{target}",
        "ok": True,
        "result": {"route_preview": {
            "status": "available",
            "army_id": 11,
            "origin_province_id": 30,
            "target_province_id": target,
            "previewed_date_raw": 1_000,
            "route_province_ids": route,
        }},
    }


def _horizon(
    target: int, route: list[int], index: int, *, conflict: bool = False,
) -> dict[str, object]:
    conflicts = [{
        "kind": "same_province",
        "hostile_army_id": 21,
        "province_id": target,
        "overlap_start_date_raw": 1_012,
        "overlap_end_date_raw": 1_024,
    }] if conflict else []
    raw = {
        "status": "available",
        "date_raw": 1_000,
        "snapshot_revision": 9,
        "subject_army_id": 11,
        "target_province_id": target,
        "hostile_army_ids": [21],
        "subject_route": {
            "timeline_observable": True,
            "army_id": 11,
            "current_province_id": 30,
            "effective_origin_province_id": 30,
            "route_province_ids": route,
            "arrival_date_raws": [1_012 + 36 * n for n in range(len(route))],
        },
        "hostile_routes": [{
            "timeline_observable": True,
            "army_id": 21,
            "current_province_id": 31,
            "effective_origin_province_id": 31,
            "route_province_ids": [target] if conflict and target != 31 else [],
            "arrival_date_raws": [1_012] if conflict and target != 31 else [],
        }],
        "horizon_start_date_raw": 1_000,
        "horizon_end_date_raw": 1_024,
        "one_day_contact_free": not conflict,
        "conflicts": conflicts,
    }
    # Exercise the production native DTO normalizer before history joins;
    # neither fresh-reader helper nor the planner branch is mocked.
    normalized = normalize_route_contact_horizon(
        raw, expected_subject_army_id=11, expected_target_province_id=target,
        expected_hostile_army_ids=[21], expected_date_raw=1_000,
        expected_snapshot_revision=9,
    )
    return {
        "index": index,
        "command": query_route_contact_horizon_step(11, target, (21,)),
        "ok": True,
        "result": {
            "route_contact_horizon": normalized,
            "queried_snapshot_id": "first-hop-frame-12004",
            "queried_revision": 7,
            "queried_native_revision": 9,
            "queried_connection_generation": 3,
            "queried_episode_run_id": "first-hop-12004",
        },
    }


def _call(commands: list[dict[str, object]], *, endpoint_query: bool = False):
    steps = {
        "preview-move-army-11-to-31", "move-army-11-to-31",
        "preview-move-army-11-to-40", "move-army-11-to-40",
        query_route_contact_horizon_step(11, 31, (21,)),
        query_route_contact_horizon_step(11, 40, (21,)),
    }
    return _general_battle_forecast_ingress(
        {"policy": "one-life-turn-v1", "phase": "native_war_route",
         "selected_step": "move-army-11-to-31"},
        commands=commands, snapshot=_snapshot(), action_steps=steps,
        bridge_capabilities=(
            {QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY} if endpoint_query else set()
        ),
    )


class FirstHopBeforeEndpoint12004Tests(unittest.TestCase):
    def test_current_normalized_h1_reaches_first_hop_before_endpoint_forecast(self):
        commands = [
            _preview(31, [30, 40, 31], 1),
            _horizon(31, [40, 31], 2),
            _preview(40, [30, 40], 3),
            _horizon(40, [40], 4),
        ]
        with mock.patch(
            "xar_autoplayer.strategy.forecast_fixed_contact",
            side_effect=AssertionError("endpoint forecast demanded before safe hop"),
        ) as model:
            with self.subTest("fresh safe hop, absent endpoint cache and capability"):
                plan = _call(commands)
                self.assertEqual(plan["phase"], "native_war_general_battle_short_move")
                self.assertEqual(plan["selected_step"], "move-army-11-to-40")
                self.assertIs(plan["general_battle_forecast_used_for_decision"], False)
                self.assertIs(plan["future_contact_authorized"], False)
                self.assertNotIn("battle_forecast", plan)
                self.assertNotIn("contact_admission", plan)
                self.assertEqual(plan["route_contact_horizon"]["target_province_id"], 40)

            with self.subTest("missing first-hop H1 asks for that existing query"):
                plan = _call(commands[:-1])
                self.assertEqual(plan["phase"], "native_war_general_battle_short_contact_query")
                self.assertEqual(plan["selected_step"], query_route_contact_horizon_step(11, 40, (21,)))

            with self.subTest("stale native frame retains the first-hop query"):
                stale = copy.deepcopy(commands)
                stale[-1]["result"]["queried_native_revision"] = 8
                plan = _call(stale)
                self.assertEqual(plan["selected_step"], query_route_contact_horizon_step(11, 40, (21,)))
                self.assertEqual(plan["phase"], "native_war_general_battle_short_contact_query")

            with self.subTest("independently observed first-hop contact prevents this hop"):
                blocked = [*commands[:-1], _horizon(40, [40], 4, conflict=True)]
                plan = _call(blocked)
                self.assertEqual(plan["phase"], "native_war_general_battle_short_contact_blocked")
                self.assertIsNone(plan["selected_step"])

            with self.subTest("single-hop contact still demands endpoint combat inputs"):
                endpoint = [_preview(31, [31], 1), _horizon(31, [31], 2, conflict=True)]
                plan = _call(endpoint, endpoint_query=True)
                self.assertEqual(plan["phase"], "native_war_general_battle_inputs_query")
                self.assertEqual(plan["selected_step"], query_combat_simulation_inputs_step(31, 30, [11], [21]))
                self.assertNotEqual(plan["selected_step"], "move-army-11-to-31")
            model.assert_not_called()


if __name__ == "__main__":
    unittest.main()
