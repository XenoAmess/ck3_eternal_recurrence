from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest
from unittest import mock


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.combat_contract import (
    QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY,
    query_combat_simulation_inputs_step,
)
from xar_autoplayer.bridge.projected_contact_contract import (
    PROJECTED_CONTACT_SCOPE_KIND,
    QUERY_PROJECTED_CONTACT_SCOPE_V1_CAPABILITY,
    query_projected_contact_scope_v1_step,
)
from xar_autoplayer.bridge.war_contract import (
    normalize_route_contact_horizon,
    query_route_contact_horizon_step,
)
from xar_autoplayer.strategy import _general_battle_forecast_ingress


def _snapshot():
    return {
        "paused": True, "snapshot_id": "normal-contact-frame-12004",
        "revision": 7, "native_revision": 9, "date_raw": 1_000,
        "episode_run_id": "normal-contact-12004",
        "diagnostics": {"connection_generation": 3},
        "player_armies": [{
            "army_id": 11, "current_province_id": 30,
            "owner_character_id": 29829, "controllable": True,
        }],
        "active_wars": [{
            "war_id": 1,
            "allied_armies": [{"army_id": 11, "current_province_id": 30}],
            "enemy_armies": [
                {"army_id": army_id, "current_province_id": 31, "army_state": "sieging"}
                for army_id in (21, 22)
            ],
        }],
    }


def _capture():
    snapshot = _snapshot()
    return {
        "queried_snapshot_id": snapshot["snapshot_id"],
        "queried_revision": snapshot["revision"],
        "queried_native_revision": snapshot["native_revision"],
        "queried_connection_generation": 3,
        "queried_episode_run_id": snapshot["episode_run_id"],
    }


def _route_history():
    horizon = normalize_route_contact_horizon({
        "status": "available", "date_raw": 1_000, "snapshot_revision": 9,
        "subject_army_id": 11, "target_province_id": 31,
        "hostile_army_ids": [21, 22],
        "subject_route": {
            "timeline_observable": True, "army_id": 11,
            "current_province_id": 30, "effective_origin_province_id": 30,
            "route_province_ids": [31], "arrival_date_raws": [1_012],
        },
        "hostile_routes": [{
            "timeline_observable": True, "army_id": army_id,
            "current_province_id": 31, "effective_origin_province_id": 31,
            "route_province_ids": [], "arrival_date_raws": [],
        } for army_id in (21, 22)],
        "horizon_start_date_raw": 1_000, "horizon_end_date_raw": 1_024,
        "one_day_contact_free": True, "conflicts": [],
    }, expected_subject_army_id=11, expected_target_province_id=31,
       expected_hostile_army_ids=[21, 22], expected_date_raw=1_000,
       expected_snapshot_revision=9)
    return [{
        "index": 1, "command": "preview-move-army-11-to-31", "ok": True,
        "result": {"route_preview": {
            "status": "available", "army_id": 11, "origin_province_id": 30,
            "target_province_id": 31, "previewed_date_raw": 1_000,
            "route_province_ids": [31],
        }},
    }, {
        "index": 2, "command": query_route_contact_horizon_step(11, 31, (21, 22)),
        "ok": True, "result": {"route_contact_horizon": horizon, **_capture()},
    }]


def _contact_row(transition="create_new", side="attacker"):
    none = transition == "none"
    join = transition == "join_existing"
    attackers = [] if none else [11] if side == "attacker" else [22, 21]
    defenders = [] if none else [22, 21] if side == "attacker" else [11]
    return {
        "index": 3, "command": query_projected_contact_scope_v1_step(11, 31, 30),
        "ok": True, "result": {
            **_capture(),
            "projected_contact_scope": {
                "status": "available", "scope_kind": PROJECTED_CONTACT_SCOPE_KIND,
                "snapshot_revision": 9, "date_raw": 1_000,
                "subject_army_id": 11, "subject_native_carmy_id": 111,
                "subject_owner_character_id": 29829, "subject_current_province_id": 30,
                "target_province_id": 31, "incoming_entry_province_id": 30,
                "observed_target_public_cunit_ids": [22, 21],
                "observed_target_combat_ids": [77] if join else [],
                "transition_kind": transition,
                "selected_current_combat_id": 77 if join else None,
                "selected_current_combat_array_index": 0 if join else None,
                "projected_subject_side": "none" if none else side,
                "projected_initiator_is_defender_observable": not none and not join,
                "projected_initiator_is_defender": None if none or join else side == "defender",
                "incoming_adjacency_kind_raw": 1,
                "projected_attacker_army_ids": attackers,
                "projected_defender_army_ids": defenders,
                "contact_projection_inputs_complete": True,
            },
        },
    }


def _call(contact_row, *, advertised=True):
    history = _route_history()
    if contact_row is not None:
        history.append(contact_row)
    before = copy.deepcopy(history)
    capabilities = {QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY}
    if advertised:
        capabilities.add(QUERY_PROJECTED_CONTACT_SCOPE_V1_CAPABILITY)
    plan = _general_battle_forecast_ingress(
        {"policy": "one-life-turn-v1", "phase": "native_war_route",
         "selected_step": "move-army-11-to-31"},
        commands=history, snapshot=_snapshot(),
        action_steps={"preview-move-army-11-to-31", "move-army-11-to-31",
                      query_route_contact_horizon_step(11, 31, (21, 22))},
        bridge_capabilities=capabilities,
    )
    return plan, history == before


class NormalArmyProjectedContact12004Tests(unittest.TestCase):
    def test_whole_current_contact_history_enters_normal_army_endpoint_decision(self):
        # Whole synthetic query results enter the production strict normalizer
        # and real policy hook. This does not borrow a native/live qualification.
        outputs = []
        with mock.patch("xar_autoplayer.strategy.forecast_fixed_contact",
                        side_effect=AssertionError("this case has no numeric combat inputs")) as model:
            with self.subTest("ordered native new-attacker sides replace snapshot ordering"):
                plan, intact = _call(_contact_row())
                self.assertTrue(intact)
                self.assertEqual(plan["selected_step"],
                                 query_combat_simulation_inputs_step(31, 30, [11], [22, 21]))
                self.assertEqual(plan["encounter"]["defender_army_ids"], [22, 21])
                self.assertEqual(plan["projected_contact_scope"]["transition_kind"], "create_new")
                outputs.append({"case": "native_order", "plan": plan})

            with self.subTest("complete none preserves legal ordinary one-hop movement"):
                plan, intact = _call(_contact_row("none"))
                self.assertTrue(intact)
                self.assertEqual(plan["phase"], "native_war_general_battle_projected_no_contact")
                self.assertEqual(plan["selected_step"], "move-army-11-to-31")
                self.assertEqual(plan["encounter"]["attacker_army_ids"], [])
                self.assertIs(plan["future_contact_authorized"], False)
                self.assertIs(plan["general_battle_forecast_used_for_decision"], False)
                outputs.append({"case": "complete_none", "plan": plan})

            with self.subTest("stale native frame requests existing projected query"):
                stale = _contact_row()
                stale["result"]["queried_native_revision"] = 8
                plan, intact = _call(stale)
                self.assertTrue(intact)
                self.assertEqual(plan["phase"], "native_war_general_battle_projected_contact_query")
                self.assertEqual(plan["selected_step"], query_projected_contact_scope_v1_step(11, 31, 30))
                outputs.append({"case": "stale_capture", "plan": plan})

            with self.subTest("incoming defender uses native constructor zero and preserves ordered roles"):
                plan, intact = _call(_contact_row(side="defender"))
                self.assertTrue(intact)
                self.assertEqual(plan["phase"], "native_war_general_battle_inputs_query")
                self.assertEqual(plan["encounter"]["attacker_army_ids"], [22, 21])
                self.assertEqual(plan["encounter"]["defender_army_ids"], [11])
                self.assertEqual(plan["selected_step"], query_combat_simulation_inputs_step(
                    31, None, [22, 21], [11], constructor_adjacency_kind_raw=0))
                self.assertIsNone(plan["encounter"]["attacker_entry_province_id"])
                self.assertEqual(plan["projected_contact_scope"]["incoming_adjacency_kind_raw"], 1)
                outputs.append({"case": "incoming_defender", "plan": plan})

            with self.subTest("join existing keeps selected Combat binding and resume frontier"):
                plan, intact = _call(_contact_row("join_existing"))
                self.assertTrue(intact)
                self.assertEqual(plan["phase"], "native_war_active_combat_resume_unavailable")
                self.assertEqual(plan["projected_contact_scope"]["selected_current_combat_id"], 77)
                self.assertIsNone(plan["selected_step"])
                outputs.append({"case": "join_existing", "plan": plan})

            with self.subTest("unadvertised Contact capability retains existing endpoint path"):
                plan, intact = _call(None, advertised=False)
                self.assertTrue(intact)
                self.assertEqual(plan["selected_step"],
                                 query_combat_simulation_inputs_step(31, 30, [11], [21, 22]))
                self.assertNotIn("projected_contact_scope", plan)
                outputs.append({"case": "legacy_capability", "plan": plan})
            model.assert_not_called()
        for output in outputs:
            print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
