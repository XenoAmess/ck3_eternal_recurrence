"""Sole FIRST: whole ctor0 input enters the registered ordinary Service/model.

Native/game envelopes and the proposed endpoint move are synthetic. Service,
NativeDriver query/cache/history, strict contracts, forecast and admission are
real. This grants no native capture, movement, contact or live qualification.
"""
from __future__ import annotations

import asyncio
import copy
import json
import os
from pathlib import Path
from unittest import mock

from test_combat_simulation_inputs_bridge import FakeEndpoint, _fixture_result
from test_normal_army_projected_contact_consumer_12004 import _contact_row, _route_history
from xar_autoplayer.bridge.combat_contract import (
    QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY,
    parse_query_combat_simulation_inputs_step,
    query_combat_simulation_inputs_step,
)
from xar_autoplayer.bridge.combat_phase_contract import (
    QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY,
    parse_query_combat_simulation_inputs_v3_step,
    query_combat_simulation_inputs_v3_step,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.projected_contact_contract import QUERY_PROJECTED_CONTACT_SCOPE_V1_CAPABILITY
from xar_autoplayer.simulation.combat_input import freeze_combat_simulation_input
from xar_autoplayer.strategy import _general_battle_forecast_ingress


ROOT = Path(__file__).resolve().parents[2]
BASELINE = {"policy": "one-life-turn-v1", "phase": "native_war_route",
            "selected_step": "move-army-11-to-31"}
SHA = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"


def _game_frame():
    player = {"army_id": 11, "current_province_id": 30,
              "owner_character_id": 29829, "controllable": True, "soldiers": 1000}
    return {"type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": "incoming-defender-native-9", "revision": 9,
            "state": {
                "phase": "map_hud", "date": "1066.9.15", "date_raw": 1000,
                "speed": 1, "paused": True, "map_ready": True, "history": [],
                "active_event": None, "pending_character_interaction": None,
                "played_character": {"character_id": 29829, "alive": True},
                "one_life_settlement": None, "player_armies": [player],
                "active_wars": [{"war_id": 1, "player_side": "defender",
                    "primary_opponent_character_id": 30097,
                    "player_is_primary_war_leader": True,
                    "player_relative_war_score": 0, "allied_armies": [player],
                    "enemy_armies": [{"army_id": value,
                        "owner_character_id": 30097, "controllable": False,
                        "soldiers": 800, "current_province_id": 31,
                        "army_state": "sieging"} for value in (21, 22)]}],
            }}


def _whole_base(*, defender):
    """Copy a checked-in producer shape into a declared three-army fixture."""
    base = _fixture_result()["combat_simulation_inputs"]
    templates = copy.deepcopy(base["armies"])
    armies = []
    # Preserve intentionally non-sorted opponent order on its physical side.
    ordered = [(22, templates[1]), (21, templates[1]), (11, templates[0])] if defender else [
        (11, templates[0]), (22, templates[1]), (21, templates[1])]
    for offset, (public_id, template) in enumerate(ordered):
        army = copy.deepcopy(template)
        friendly = public_id == 11
        army.update(army_id=public_id, native_carmy_id=111 + offset,
                    encounter_role="defender" if (friendly == defender) else "attacker",
                    scope_role="player" if friendly else "active_war_enemy",
                    war_ids=[1], current_province_id=30 if friendly else 31)
        army["owner"]["character_id"] = 29829 if friendly else 30097
        army["commander"]["battle_context"]["source_target_province_id"] = 31
        for index, regiment in enumerate(army["regiments"]):
            regiment["regiment_id"] = 100 + offset * 10 + index
            regiment["effective_stats"]["source_target_province_id"] = 31
        # Knight population is not a required change for this consumer seam.
        army["knights"]["members"] = []
        armies.append(army)
    attackers, defenders = ([22, 21], [11]) if defender else ([11], [22, 21])
    scenario = base["scenario"]
    scenario.update(attacker_entry_province_id=None if defender else 30,
                    attacker_army_ids=attackers, defender_army_ids=defenders,
                    attacker_side="enemy" if defender else "player_or_allied",
                    defender_side="player_or_allied" if defender else "enemy",
                    attacker_position_policy="fixed_at_target_hypothetical" if defender else "fixed_at_entry_hypothetical")
    if defender:
        scenario.update(contact_geometry_mode="native_defender_constructor_zero",
                        constructor_adjacency_kind_raw=0)
    base.update(target_province_id=31, armies=armies, ongoing_combats=[])
    target = base["target_province"]
    target["province_id"] = 31
    target["defender_context"]["defender_side"] = scenario["defender_side"]
    # These are current coalition owner outputs, independent of physical role.
    for row in base["counter_resolutions"]:
        row["countered_modifier_owner_character_id"] = 29829 if row["countered_side"] == "player_or_allied" else 30097
        row["countering_modifier_owner_character_id"] = 29829 if row["countering_side"] == "player_or_allied" else 30097
    return base


def _seed_history(driver, side):
    current = driver.take_snapshot()
    diagnostics = current["diagnostics"]
    capture = {"queried_snapshot_id": current["snapshot_id"],
               "queried_revision": current["revision"],
               "queried_native_revision": current["native_revision"],
               "queried_connection_generation": diagnostics["connection_generation"],
               "queried_episode_run_id": current["episode_run_id"]}
    rows = _route_history() + [_contact_row(side=side)]
    for row in rows:
        row["result"].update(capture)
    with driver._history_lock:
        # Retain an already obtained whole combat-query result across role
        # changes; only replace this fixture's route/projection observations.
        combat_rows = [row for row in driver._command_history if
            parse_query_combat_simulation_inputs_step(row.get("command")) is not None
            or parse_query_combat_simulation_inputs_v3_step(row.get("command")) is not None]
        driver._command_history = [*rows, *combat_rows]
        for index, row in enumerate(driver._command_history, 1):
            row["index"] = index
    return current


def test_registered_incoming_defender_whole_query_cache_model_and_role_change(tmp_path):
    from mcp import Client

    records = []

    def proposed_move(commands, *, snapshot, action_steps, bridge_capabilities, **unused):
        # Only the proposed move baseline is synthetic; the production
        # endpoint consumer chooses query/model/admission without stubs.
        return _general_battle_forecast_ingress(copy.deepcopy(BASELINE),
            commands=commands, snapshot=snapshot, action_steps=set(action_steps),
            bridge_capabilities=set(bridge_capabilities))

    async def scene(version):
        endpoint = FakeEndpoint()
        state = tmp_path / f"v{version}"
        state.mkdir()
        driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
            state_dir=state, command_timeout_seconds=0.1)
        driver.require_initial_lifestyle_focus_before_date_advance = False
        capability = QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY if version == 3 else QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY
        endpoint.publish({"type": "hello", "protocol_version": 1,
            "bridge_version": "0.1.0", "pid": 4242, "session_generation": 0,
            "game_version": "1.20.0.4", "executable_sha256": SHA,
            "capabilities": ["game.state.snapshot", capability,
                             QUERY_PROJECTED_CONTACT_SCOPE_V1_CAPABILITY]})
        endpoint.publish(_game_frame())
        original_capabilities = driver.capabilities
        def capabilities():
            value = original_capabilities()
            return {**value, "action_steps": [*value["action_steps"],
                "move-army-11-to-31", "preview-move-army-11-to-31"]}
        driver.capabilities = capabilities
        builder = query_combat_simulation_inputs_v3_step if version == 3 else query_combat_simulation_inputs_step
        parser = parse_query_combat_simulation_inputs_v3_step if version == 3 else parse_query_combat_simulation_inputs_step

        def answer(request):
            if request.get("type") != "execute_step":
                return
            parsed = parser(request.get("step"))
            assert parsed is not None, request
            base = _whole_base(defender=parsed[1] is None)
            if version == 3:
                result = json.loads((ROOT / "native_bridge/research/fixtures/combat_simulation_inputs_v3_production_unavailable.json").read_text(encoding="utf-8"))["result"]
                result["combat_simulation_inputs"]["base_inputs"] = base
                result["status"] = "unavailable"
            else:
                result = _fixture_result()
                result["combat_simulation_inputs"] = base
            result.update(step=request["step"], query_sequence=len(endpoint.frames))
            endpoint.publish({"type": "command_result", "protocol_version": 1,
                "request_id": request["request_id"], "ok": True, "result": result})
        endpoint.send_hook = answer
        _seed_history(driver, "defender")
        async with Client(create_server(driver)) as client:
            before = await client.call_tool("ck3_plan_turn", {})
            assert not before.is_error, before.content
            query = before.structured_content["plan"]
            expected = builder(31, None, [22, 21], [11], constructor_adjacency_kind_raw=0)
            assert query["selected_step"] == expected
            assert query["encounter"]["attacker_entry_province_id"] is None
            assert query["encounter"]["attacker_army_ids"] == [22, 21]
            assert query["projected_contact_scope"]["incoming_entry_province_id"] == 30
            assert query["projected_contact_scope"]["incoming_adjacency_kind_raw"] == 1
            snapshot = driver.take_snapshot()
            tool = "ck3_query_combat_simulation_inputs_v3" if version == 3 else "ck3_query_combat_simulation_inputs"
            read = await client.call_tool(tool, {"target_province_id": 31,
                "attacker_entry_province_id": None, "constructor_adjacency_kind_raw": 0,
                "attacker_army_ids": [22, 21], "defender_army_ids": [11],
                "expected_revision": snapshot["revision"]})
            assert not read.is_error, read.content
            cache = "combat_simulation_inputs_v3" if version == 3 else "combat_simulation_inputs"
            current = driver.take_snapshot()
            assert current[f"{cache}_attacker_entry_province_id"] is None
            base = current[cache]["base_inputs"] if version == 3 else current[cache]
            frozen = freeze_combat_simulation_input(base, capture=current)
            assert frozen.encounter.attacker_entry_province_id is None
            assert frozen.encounter.attacker_side == "enemy"
            assert frozen.encounter.defender_side == "player_or_allied"
            # Raw0 does not overwrite the nonzero supplied commander input.
            assert next(army for army in frozen.armies if army.public_army_id == 11).commander.generic_advantage_points == 3
            after = await client.call_tool("ck3_plan_turn", {})
            assert not after.is_error, after.content
            plan = after.structured_content["plan"]
            forecast = plan.get("battle_forecast", plan.get("general_battle_forecast"))
            assert forecast["status"] == "estimated", plan
            assert forecast["native_parity"] is False
            assert forecast["sample_count"] == 256
            assert forecast["advantage_input"]["source"] == "generic_commander_and_stock_static_approximation"
            assert forecast["character_death_risk_status"] == "unmodeled_phase_events"
            records.append({"scene": f"v{version}-defender-null-entry", "query": expected,
                            "forecast": forecast, "phase": plan["phase"]})

            # Same-frame roles can change independently of route geometry.
            # The previous ctor0 cache must not match the attacker request.
            _seed_history(driver, "attacker")
            attacker = await client.call_tool("ck3_plan_turn", {})
            assert not attacker.is_error, attacker.content
            assert attacker.structured_content["plan"]["selected_step"] == builder(31, 30, [11], [22, 21])
            read = await client.call_tool(tool, {"target_province_id": 31,
                "attacker_entry_province_id": 30, "attacker_army_ids": [11],
                "defender_army_ids": [22, 21], "expected_revision": current["revision"]})
            assert not read.is_error, read.content
            positive = driver.take_snapshot()[cache]
            positive_base = positive["base_inputs"] if version == 3 else positive
            assert "contact_geometry_mode" not in positive_base["scenario"]
            _seed_history(driver, "defender")
            replaced = await client.call_tool("ck3_plan_turn", {})
            assert not replaced.is_error, replaced.content
            assert replaced.structured_content["plan"]["selected_step"] == expected
            records.append({"scene": f"v{version}-role-change", "positive_entry": 30,
                            "fresh_defender_query": expected,
                            "readonly_query_count": sum(row.get("type") == "execute_step" for row in endpoint.frames)})
        driver.close()

    async def run():
        with mock.patch("xar_autoplayer.bridge.service.choose_one_life_turn", side_effect=proposed_move):
            await scene(2)
            await scene(3)

    asyncio.run(run())
    output_path = os.environ.get("XAR_INCOMING_DEFENDER_SERVICE_OUTPUT")
    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({"schema": "xar.incoming-defender-service-first12004.v1",
            "boundary": "synthetic game/native envelopes and proposed move; real registered Service, Driver, strict cache/history and forecast",
            "scenes": records, "production_live": False, "actual_movement": False,
            "native_parity": False}, indent=2) + "\n", encoding="utf-8")
