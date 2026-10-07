import copy
import hashlib
import json
from pathlib import Path
from unittest import TestCase, mock

from xar_autoplayer.bridge.combat_phase_contract import query_combat_simulation_inputs_v3_step
from xar_autoplayer.strategy import (
    _general_battle_forecast_ingress,
    query_route_contact_horizon_step,
)


_CHECK = TestCase()


def _frame():
    return {
        "paused": True,
        "snapshot_id": "battle-frame-1",
        "revision": 5,
        "native_revision": 9,
        "date_raw": 100,
        "player_armies": [{"army_id": 11, "current_province_id": 30}],
        "active_wars": [{"war_id": 1, "allied_armies": [
            {"army_id": 11, "current_province_id": 30, "controllable": True}
        ], "enemy_armies": [
            {"army_id": 21, "current_province_id": 31, "army_state": "sieging"}
        ]}],
        "combat_simulation_inputs_v3": {"base_inputs": {}, "completeness": {}},
        "combat_simulation_inputs_v3_status": "available",
        "combat_simulation_inputs_v3_target_province_id": 31,
        "combat_simulation_inputs_v3_attacker_entry_province_id": 30,
        "combat_simulation_inputs_v3_attacker_army_ids": [11],
        "combat_simulation_inputs_v3_defender_army_ids": [21],
        "combat_simulation_inputs_v3_queried_snapshot_id": "battle-frame-1",
        "combat_simulation_inputs_v3_queried_revision": 5,
    }


def _call(frame, *, query_history=True, entry=30, extra_steps=(),
          bridge_capabilities=None, baseline=None, action_steps=None):
    query = query_combat_simulation_inputs_v3_step(31, entry, [11], [21])
    commands = [{
        "index": 1, "command": query, "ok": True,
        "result": {
            "queried_snapshot_id": "battle-frame-1",
            "queried_revision": 5,
            "queried_native_revision": 9,
            "status": "available",
        },
    }] if query_history else []
    return _general_battle_forecast_ingress(
        baseline or {"policy": "one-life-turn-v1", "phase": "native_war_route", "selected_step": "move-army-11-to-31"},
        commands=commands, snapshot=frame,
        # The production driver excludes parameterized v3 literals from its
        # advertised action list.  The planner must construct this read-only
        # query from the observed encounter and check the bridge capability.
        action_steps=(
            {"move-army-11-to-31", "preview-move-army-11-to-31", *extra_steps}
            if action_steps is None else action_steps
        ),
        bridge_capabilities=(
            {"game.command.query-combat-simulation-inputs-v3-N"}
            if bridge_capabilities is None else bridge_capabilities
        ),
    )


def test_proposed_hostile_contact_consumes_model_even_without_native_parity():
    frame = _frame()
    forecast = {"status": "estimated", "native_parity": False, "sample_count": 256}
    contact = {"conflicts": [{"province_id": 31, "hostile_army_id": 21}],
               "subject_route": {"arrival_date_raws": [101]}}
    with (
        mock.patch("xar_autoplayer.strategy._fresh_move_route_preview", return_value={
            "status": "available", "route_province_ids": [31],
        }),
        mock.patch("xar_autoplayer.strategy._fresh_route_contact_horizon", return_value=contact),
        mock.patch("xar_autoplayer.strategy.forecast_fixed_contact", return_value=forecast) as model,
        mock.patch("xar_autoplayer.strategy.contact_admission", return_value={"admitted": True}),
    ):
        plan = _call(frame)
        assert plan["selected_step"] == "move-army-11-to-31"
        assert plan["general_battle_forecast_used_for_decision"] is True
        assert plan["general_battle_forecast"]["native_parity"] is False
        model.assert_called_once()


def test_observed_unmodeled_inbound_enemy_route_blocks_only_final_contact():
    frame = _frame()
    frame["active_wars"][0]["enemy_armies"].append({
        "army_id": 22, "current_province_id": 32,
        "army_state": "moving", "route_province_ids": [40, 31, 33],
    })
    contact = {"conflicts": [{"province_id": 31, "hostile_army_id": 21}],
               "subject_route": {"arrival_date_raws": [101]}}
    forecast = {"status": "estimated", "native_parity": False, "sample_count": 256}
    with (
        mock.patch("xar_autoplayer.strategy._fresh_move_route_preview", return_value={
            "status": "available", "route_province_ids": [31],
        }),
        mock.patch("xar_autoplayer.strategy._fresh_route_contact_horizon", return_value=contact),
        mock.patch("xar_autoplayer.strategy.forecast_fixed_contact", return_value=forecast) as model,
        mock.patch("xar_autoplayer.strategy.contact_admission", return_value={"admitted": True}),
    ):
        result = _call(frame)
    model.assert_called_once()
    _CHECK.assertEqual(result["phase"], "native_war_general_battle_observed_inbound_reinforcement")
    _CHECK.assertIsNone(result["selected_step"])
    _CHECK.assertEqual(result["battle_forecast"], forecast)
    _CHECK.assertEqual(result["observed_unmodeled_inbound_enemy_army_ids"], [22])
    _CHECK.assertIs(result["inbound_arrival_before_battle_resolution_proven"], False)


def test_observed_inbound_route_does_not_block_contact_free_first_waypoint():
    frame = _frame()
    frame["combat_simulation_inputs_v3_attacker_entry_province_id"] = 40
    frame["active_wars"][0]["enemy_armies"].append({
        "army_id": 22, "current_province_id": 32,
        "army_state": "moving", "route_province_ids": [31],
    })

    def preview(*args, **kwargs):
        return {"status": "available", "route_province_ids": (
            [40, 31] if kwargs["target_province_id"] == 31 else [40]
        )}

    def contact(*args, **kwargs):
        return ({"one_day_contact_free": True, "conflicts": [
            {"province_id": 31, "hostile_army_id": 21},
        ]} if kwargs["target_province_id"] == 31 else
            {"one_day_contact_free": True, "conflicts": []})

    with (
        mock.patch("xar_autoplayer.strategy._fresh_move_route_preview", side_effect=preview),
        mock.patch("xar_autoplayer.strategy._fresh_route_contact_horizon", side_effect=contact),
        mock.patch("xar_autoplayer.strategy.forecast_fixed_contact", return_value={"status": "estimated"}) as model,
        mock.patch("xar_autoplayer.strategy.contact_admission", return_value={"admitted": True}),
    ):
        result = _call(frame, entry=40, extra_steps={
            "preview-move-army-11-to-40", "move-army-11-to-40",
            query_route_contact_horizon_step(11, 40, (21, 22)),
        })
    model.assert_not_called()
    assert result["phase"] == "native_war_general_battle_short_move"
    assert result["selected_step"] == "move-army-11-to-40"


def test_model_risk_rejection_stops_contact_and_absent_input_queries_it():
    frame = _frame()
    contact = {"conflicts": [{"province_id": 31, "hostile_army_id": 21}],
               "subject_route": {"arrival_date_raws": [101]}}
    with (
        mock.patch("xar_autoplayer.strategy._fresh_move_route_preview", return_value={
            "status": "available", "route_province_ids": [31],
        }),
        mock.patch("xar_autoplayer.strategy._fresh_route_contact_horizon", return_value=contact),
        mock.patch("xar_autoplayer.strategy.forecast_fixed_contact", return_value={"status": "estimated"}),
        mock.patch("xar_autoplayer.strategy.contact_admission", return_value={"admitted": False}),
    ):
        rejected = _call(frame)
        assert rejected["selected_step"] is None
        assert rejected["phase"] == "native_war_general_battle_model_rejected"
        query = _call(frame, query_history=False)
        assert query["phase"] == "native_war_general_battle_inputs_query"
        assert query["selected_step"] == query_combat_simulation_inputs_v3_step(31, 30, [11], [21])


def test_missing_v3_capability_keeps_parameterized_query_blocked():
    frame = _frame()
    with (
        mock.patch("xar_autoplayer.strategy._fresh_move_route_preview", return_value={
            "status": "available", "route_province_ids": [31],
        }),
        mock.patch("xar_autoplayer.strategy._fresh_route_contact_horizon", return_value={
            "conflicts": [{"province_id": 31, "hostile_army_id": 21}],
        }),
    ):
        result = _call(frame, query_history=False, bridge_capabilities=set())
    assert result["phase"] == "native_war_general_battle_inputs_query"
    assert result["selected_step"] is None


def test_stale_native_revision_cannot_reuse_a_cached_battle_estimate():
    frame = _frame()
    frame["native_revision"] = 10
    with (
        mock.patch("xar_autoplayer.strategy._fresh_move_route_preview", return_value={
            "status": "available", "route_province_ids": [31],
        }),
        mock.patch("xar_autoplayer.strategy._fresh_route_contact_horizon", return_value={
            "conflicts": [{"province_id": 31, "hostile_army_id": 21}],
        }),
        mock.patch("xar_autoplayer.strategy.forecast_fixed_contact") as model,
    ):
        result = _call(frame)
        _CHECK.assertEqual(result["phase"], "native_war_general_battle_inputs_query")
        model.assert_not_called()


def test_long_route_advances_one_contact_free_waypoint_before_forecast():
    frame = _frame()
    frame["combat_simulation_inputs_v3_attacker_entry_province_id"] = 40

    def preview(*args, **kwargs):
        return {"status": "available", "route_province_ids": (
            [40, 31] if kwargs["target_province_id"] == 31 else [40]
        )}

    def contact(*args, **kwargs):
        if kwargs["target_province_id"] == 31:
            return {"one_day_contact_free": True, "conflicts": [
                {"province_id": 31, "hostile_army_id": 21},
            ]}
        return {"one_day_contact_free": True, "conflicts": []}

    with (
        mock.patch("xar_autoplayer.strategy._fresh_move_route_preview", side_effect=preview),
        mock.patch("xar_autoplayer.strategy._fresh_route_contact_horizon", side_effect=contact),
        mock.patch("xar_autoplayer.strategy.forecast_fixed_contact", return_value={"status": "estimated"}),
        mock.patch("xar_autoplayer.strategy.contact_admission", return_value={"admitted": True}),
    ):
        result = _call(
            frame, entry=40,
            extra_steps={
                "preview-move-army-11-to-40", "move-army-11-to-40",
                query_route_contact_horizon_step(11, 40, (21,)),
            },
        )
        _CHECK.assertEqual(result["phase"], "native_war_general_battle_short_move")
        _CHECK.assertEqual(result["selected_step"], "move-army-11-to-40")
        _CHECK.assertIs(result["general_battle_forecast_used_for_decision"], False)


def test_long_route_with_origin_prefix_uses_first_travel_waypoint():
    frame = _frame()
    frame["combat_simulation_inputs_v3_attacker_entry_province_id"] = 40

    def preview(*args, **kwargs):
        return {"status": "available", "route_province_ids": (
            [30, 40, 31] if kwargs["target_province_id"] == 31 else [30, 40]
        )}

    def contact(*args, **kwargs):
        if kwargs["target_province_id"] == 31:
            return {"one_day_contact_free": True, "conflicts": [
                {"province_id": 31, "hostile_army_id": 21},
            ]}
        return {"one_day_contact_free": True, "conflicts": []}

    with (
        mock.patch("xar_autoplayer.strategy._fresh_move_route_preview", side_effect=preview),
        mock.patch("xar_autoplayer.strategy._fresh_route_contact_horizon", side_effect=contact),
        mock.patch("xar_autoplayer.strategy.forecast_fixed_contact", return_value={"status": "estimated"}),
        mock.patch("xar_autoplayer.strategy.contact_admission", return_value={"admitted": True}),
    ):
        result = _call(
            frame, entry=40,
            extra_steps={
                "preview-move-army-11-to-40", "move-army-11-to-40",
                query_route_contact_horizon_step(11, 40, (21,)),
            },
        )
    assert result["phase"] == "native_war_general_battle_short_move"
    assert result["selected_step"] == "move-army-11-to-40"


def _distant_one_hop_contact():
    # R0284's native timeline has the same shape: 2634 -> 2640, arrival in
    # six days, while the current one-day horizon is contact-free.
    return {
        "one_day_contact_free": True,
        "conflicts": [],
        "hostile_army_ids": [21],
        "horizon_start_date_raw": 100,
        "horizon_end_date_raw": 124,
        "subject_route": {
            "timeline_observable": True,
            "army_id": 11,
            "current_province_id": 30,
            "route_province_ids": [31],
            "arrival_date_raws": [244],
        },
    }


def test_distant_one_hop_contact_starts_only_a_daily_rechecked_route():
    frame = _frame()
    contact = _distant_one_hop_contact()
    with (
        mock.patch("xar_autoplayer.strategy._fresh_move_route_preview", return_value={
            "status": "available", "route_province_ids": [31],
        }),
        mock.patch("xar_autoplayer.strategy._fresh_route_contact_horizon", return_value=contact),
        mock.patch("xar_autoplayer.strategy.forecast_fixed_contact", return_value={"status": "estimated"}),
        mock.patch("xar_autoplayer.strategy.contact_admission", return_value={"admitted": True}),
    ):
        plan = _call(frame)
    _CHECK.assertEqual(plan["phase"], "native_war_general_battle_distant_route_start", plan)
    _CHECK.assertEqual(plan["selected_step"], "move-army-11-to-31")
    _CHECK.assertEqual(plan["future_arrival_date_raw"], 244)
    _CHECK.assertEqual(plan["source_war_id"], 1)
    _CHECK.assertIs(plan["contact_recheck_required_before_each_day"], True)
    _CHECK.assertIs(plan["future_contact_authorized"], False)


def test_distant_one_hop_contact_fails_closed_without_exact_first_day_proof():
    frame = _frame()
    for mutation in (
        {"one_day_contact_free": False},
        {"conflicts": [{"province_id": 31, "hostile_army_id": 21}]},
        {"horizon_start_date_raw": 99},
        {"horizon_end_date_raw": 148},
        {"subject_route": {**_distant_one_hop_contact()["subject_route"], "army_id": 12}},
        {"subject_route": {**_distant_one_hop_contact()["subject_route"], "route_province_ids": [40, 31]}},
        {"subject_route": {**_distant_one_hop_contact()["subject_route"], "arrival_date_raws": []}},
    ):
        contact = {**_distant_one_hop_contact(), **mutation}
        with (
            mock.patch("xar_autoplayer.strategy._fresh_move_route_preview", return_value={
                "status": "available", "route_province_ids": [31],
            }),
            mock.patch("xar_autoplayer.strategy._fresh_route_contact_horizon", return_value=contact),
            mock.patch("xar_autoplayer.strategy.forecast_fixed_contact", return_value={"status": "estimated"}),
            mock.patch("xar_autoplayer.strategy.contact_admission", return_value={"admitted": True}),
        ):
            plan = _call(frame)
        _CHECK.assertEqual(plan["phase"], "native_war_general_battle_arrival_blocked")
        _CHECK.assertIsNone(plan["selected_step"])
    frame["active_wars"].append({"war_id": 2, "enemy_armies": []})
    with (
        mock.patch("xar_autoplayer.strategy._fresh_move_route_preview", return_value={
            "status": "available", "route_province_ids": [31],
        }),
        mock.patch("xar_autoplayer.strategy._fresh_route_contact_horizon", return_value=_distant_one_hop_contact()),
        mock.patch("xar_autoplayer.strategy.forecast_fixed_contact", return_value={"status": "estimated"}),
        mock.patch("xar_autoplayer.strategy.contact_admission", return_value={"admitted": True}),
    ):
        plan = _call(frame)
    _CHECK.assertEqual(plan["phase"], "native_war_general_battle_arrival_blocked")
    _CHECK.assertIsNone(plan["selected_step"])


def test_distant_one_hop_requires_subject_and_full_hostile_roster_in_same_war():
    for change in (
        lambda frame, contact: frame["active_wars"][0].pop("allied_armies"),
        lambda frame, contact: frame["active_wars"][0]["allied_armies"][0].update({"army_id": 12}),
        lambda frame, contact: frame["active_wars"][0]["allied_armies"][0].update({"current_province_id": 29}),
        lambda frame, contact: frame["active_wars"][0]["allied_armies"][0].update({"controllable": False}),
        lambda frame, contact: frame["active_wars"][0].update({"war_id": 0}),
        lambda frame, contact: contact.update({"hostile_army_ids": [22]}),
        lambda frame, contact: contact.update({"hostile_army_ids": None}),
    ):
        frame = _frame()
        contact = _distant_one_hop_contact()
        change(frame, contact)
        with (
            mock.patch("xar_autoplayer.strategy._fresh_move_route_preview", return_value={
                "status": "available", "route_province_ids": [31],
            }),
            mock.patch("xar_autoplayer.strategy._fresh_route_contact_horizon", return_value=contact),
            mock.patch("xar_autoplayer.strategy.forecast_fixed_contact", return_value={"status": "estimated"}),
            mock.patch("xar_autoplayer.strategy.contact_admission", return_value={"admitted": True}),
        ):
            plan = _call(frame)
        _CHECK.assertEqual(plan["phase"], "native_war_general_battle_arrival_blocked", plan)
        _CHECK.assertIsNone(plan["selected_step"])


def test_distant_one_hop_requires_typed_move_and_exact_target_preview():
    frame = _frame()
    with (
        mock.patch("xar_autoplayer.strategy._fresh_move_route_preview", return_value={
            "status": "available", "route_province_ids": [31],
        }),
        mock.patch("xar_autoplayer.strategy._fresh_route_contact_horizon", return_value=_distant_one_hop_contact()),
        mock.patch("xar_autoplayer.strategy.forecast_fixed_contact", return_value={"status": "estimated"}),
        mock.patch("xar_autoplayer.strategy.contact_admission", return_value={"admitted": True}),
    ):
        unavailable = _call(frame, action_steps={"preview-move-army-11-to-31"})
    _CHECK.assertEqual(unavailable["phase"], "native_war_general_battle_arrival_blocked")
    _CHECK.assertIsNone(unavailable["selected_step"])
    with (
        mock.patch("xar_autoplayer.strategy._fresh_move_route_preview", return_value={
            "status": "available", "route_province_ids": [32],
        }),
        mock.patch("xar_autoplayer.strategy.forecast_fixed_contact") as model,
    ):
        wrong_target = _call(frame)
    _CHECK.assertEqual(wrong_target["phase"], "native_war_general_battle_route_blocked")
    _CHECK.assertIsNone(wrong_target["selected_step"])
    model.assert_not_called()


def test_r0284_frozen_native_rows_reach_only_route_start():
    evidence_path = (
        Path(__file__).parents[3]
        / "docs/autonomous-agent-progress/coordination/war-requests/evidence"
        / "WAR-ROBERT-R0284-CONTACT-20260928.blocker-excerpt.json"
    )
    frozen_bytes = evidence_path.read_bytes()
    _CHECK.assertEqual(
        hashlib.sha256(frozen_bytes).hexdigest().upper(),
        "71995745DBC64576701A2F5F838E46A0B127DE2ED48AB3634F9D0F45A2336D5A",
    )
    frozen = json.loads(frozen_bytes)
    source = frozen["formal"]
    preview = frozen["route_preview_h928"]
    contact = frozen["contact_horizon_h930"]
    contact_binding = frozen["contact_query_binding_h930"]
    v3 = frozen["v3_query_h932"]
    army_id = preview["army_id"]
    target_id = preview["target_province_id"]
    enemy_id = contact["hostile_army_ids"][0]
    _CHECK.assertEqual(preview["origin_province_id"], 2634)
    _CHECK.assertEqual(target_id, 2640)
    _CHECK.assertEqual(contact["subject_route"]["arrival_date_raws"], [source["date_raw"] + 144])
    frame = {
        "paused": True,
        "snapshot_id": source["snapshot_id"],
        "revision": source["revision"],
        "native_revision": source["native_revision"],
        "date_raw": source["date_raw"],
        "episode_run_id": source["episode_run_id"],
        "diagnostics": {"connection_generation": contact_binding["queried_connection_generation"]},
        "player_armies": [{"army_id": army_id, "current_province_id": preview["origin_province_id"]}],
        "active_wars": [{"war_id": source["war_ids"][0], "allied_armies": [
            {"army_id": army_id, "current_province_id": preview["origin_province_id"],
             "controllable": True}
        ], "enemy_armies": [
            {"army_id": enemy_id, "current_province_id": target_id, "army_state": "sieging"}
        ]}],
        "combat_simulation_inputs_v3": {"base_inputs": {}, "completeness": {}},
        "combat_simulation_inputs_v3_status": v3["status"],
        "combat_simulation_inputs_v3_target_province_id": target_id,
        "combat_simulation_inputs_v3_attacker_entry_province_id": preview["origin_province_id"],
        "combat_simulation_inputs_v3_attacker_army_ids": [army_id],
        "combat_simulation_inputs_v3_defender_army_ids": [enemy_id],
        "combat_simulation_inputs_v3_queried_snapshot_id": v3["queried_snapshot_id"],
        "combat_simulation_inputs_v3_queried_revision": v3["queried_revision"],
    }
    preview_step = f"preview-move-army-{army_id}-to-{target_id}"
    move_step = f"move-army-{army_id}-to-{target_id}"
    contact_step = query_route_contact_horizon_step(army_id, target_id, (enemy_id,))
    commands = [
        {"index": 928, "command": preview_step, "ok": True, "result": {
            "route_preview": preview, **contact_binding,
        }},
        {"index": 930, "command": contact_step, "ok": True, "result": {
            "route_contact_horizon": contact, **contact_binding,
        }},
        {"index": 932, "command": v3["command"], "ok": True, "result": {
            "status": v3["status"],
            "queried_snapshot_id": v3["queried_snapshot_id"],
            "queried_revision": v3["queried_revision"],
            "queried_native_revision": v3["queried_native_revision"],
        }},
    ]
    with (
        mock.patch("xar_autoplayer.strategy.forecast_fixed_contact", return_value={"status": "estimated"}),
        mock.patch("xar_autoplayer.strategy.contact_admission", return_value={"admitted": True}),
    ):
        plan = _general_battle_forecast_ingress(
            {"policy": "one-life-turn-v1", "phase": "native_war_route", "selected_step": move_step},
            commands=commands, snapshot=frame,
            action_steps={preview_step, contact_step, move_step},
            bridge_capabilities={"game.command.query-combat-simulation-inputs-v3-N"},
        )
    _CHECK.assertEqual(plan["phase"], "native_war_general_battle_distant_route_start", plan)
    _CHECK.assertEqual(plan["selected_step"], move_step)
    _CHECK.assertIs(plan["future_contact_authorized"], False)
    stale = {**frame, "native_revision": source["native_revision"] + 1}
    stale_plan = _general_battle_forecast_ingress(
        {"policy": "one-life-turn-v1", "phase": "native_war_route", "selected_step": move_step},
        commands=commands, snapshot=stale,
        action_steps={preview_step, contact_step, move_step},
        bridge_capabilities={"game.command.query-combat-simulation-inputs-v3-N"},
    )
    _CHECK.assertEqual(stale_plan["phase"], "native_war_general_battle_contact_query")
    _CHECK.assertEqual(stale_plan["selected_step"], contact_step)
    changed_roster = copy.deepcopy(frame)
    changed_roster["active_wars"][0]["enemy_armies"].append({
        "army_id": enemy_id + 1,
        "current_province_id": target_id + 1,
        "army_state": "moving",
    })
    changed_plan = _general_battle_forecast_ingress(
        {"policy": "one-life-turn-v1", "phase": "native_war_route", "selected_step": move_step},
        commands=commands, snapshot=changed_roster,
        action_steps={preview_step, contact_step, move_step},
        bridge_capabilities={"game.command.query-combat-simulation-inputs-v3-N"},
    )
    _CHECK.assertEqual(changed_plan["phase"], "native_war_general_battle_contact_query")
    _CHECK.assertIsNone(changed_plan["selected_step"])


def test_nullable_enemy_roster_does_not_crash_generic_contact_review():
    frame = _frame()
    frame["active_wars"].append({"war_id": 2, "enemy_armies": None})
    with mock.patch("xar_autoplayer.strategy._fresh_move_route_preview", return_value=None):
        result = _call(frame)
    assert result["phase"] == "native_war_general_battle_route_query"


def test_active_subject_cannot_use_fixed_contact_or_request_precontact_inputs():
    frame = _frame()
    frame["player_armies"][0].update({"in_combat": True, "army_state": "combat"})
    with (
        mock.patch("xar_autoplayer.strategy._fresh_move_route_preview") as preview,
        mock.patch("xar_autoplayer.strategy.forecast_fixed_contact") as model,
    ):
        result = _call(frame, query_history=False)
    assert result["phase"] == "native_war_active_combat_resume_unavailable"
    assert result["selected_step"] is None
    assert result["active_combat_forecast_status"] == "unavailable"
    assert result["active_combat_subject_army_id"] == 11
    assert result["active_combat_defender_army_ids"] == []
    preview.assert_not_called()
    model.assert_not_called()


def test_active_defender_cannot_be_treated_as_fresh_contact_even_with_cached_v3():
    frame = _frame()
    frame["combat_simulation_inputs_v3"]["base_inputs"]["ongoing_combats"] = []
    frame["active_wars"][0]["enemy_armies"][0].update(
        {"in_combat": True, "army_state": "combat"}
    )
    with (
        mock.patch("xar_autoplayer.strategy._fresh_move_route_preview") as preview,
        mock.patch("xar_autoplayer.strategy.forecast_fixed_contact") as model,
    ):
        result = _call(frame, baseline={
            "policy": "one-life-turn-v1",
            "phase": "native_war_siege_forecast_move",
            "selected_step": "move-army-11-to-31",
            "qualified_forecast": {"status": "ready"},
        })
    assert result["phase"] == "native_war_active_combat_resume_unavailable"
    assert result["selected_step"] is None
    assert result["active_combat_forecast_status"] == "unavailable"
    assert result["active_combat_subject_army_id"] is None
    assert result["active_combat_defender_army_ids"] == [21]
    preview.assert_not_called()
    model.assert_not_called()
