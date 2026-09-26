from unittest import mock

from xar_autoplayer.bridge.combat_phase_contract import query_combat_simulation_inputs_v3_step
from xar_autoplayer.strategy import (
    _general_battle_forecast_ingress,
    query_route_contact_horizon_step,
)


def _frame():
    return {
        "paused": True,
        "snapshot_id": "battle-frame-1",
        "revision": 5,
        "native_revision": 9,
        "date_raw": 100,
        "player_armies": [{"army_id": 11, "current_province_id": 30}],
        "active_wars": [{"war_id": 1, "enemy_armies": [
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


def _call(frame, *, query_history=True, entry=30, extra_steps=()):
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
        {"policy": "one-life-turn-v1", "phase": "native_war_route", "selected_step": "move-army-11-to-31"},
        commands=commands, snapshot=frame,
        action_steps={query, "move-army-11-to-31", "preview-move-army-11-to-31", *extra_steps},
        bridge_capabilities={"game.command.query-combat-simulation-inputs-v3-N"},
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
        assert result["phase"] == "native_war_general_battle_inputs_query"
        model.assert_not_called()


def test_long_route_uses_forecast_only_to_advance_one_contact_free_waypoint():
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
        assert result["phase"] == "native_war_general_battle_short_move"
        assert result["selected_step"] == "move-army-11-to-40"
        assert result["general_battle_forecast_used_for_decision"] is True


def test_nullable_enemy_roster_does_not_crash_generic_contact_review():
    frame = _frame()
    frame["active_wars"].append({"war_id": 2, "enemy_armies": None})
    with mock.patch("xar_autoplayer.strategy._fresh_move_route_preview", return_value=None):
        result = _call(frame)
    assert result["phase"] == "native_war_general_battle_route_query"
