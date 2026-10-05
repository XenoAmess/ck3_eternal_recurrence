"""Reproduce the actual Arta holding-only assault consumer gap offline."""

from __future__ import annotations

import copy
import unittest

from test_native_bridge_driver import FakeEndpoint, _active_siege, _hello, _snapshot, _war
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import (
    NativeHeadlessGameplayDriver, _life_advance_horizon_days,
    _life_advance_timeline_policy, _native_open_assault_lifecycles,
    _native_unobservable_started_assaults, _with_fresh_holding_siege_states,
)
from xar_autoplayer.bridge.version_identity import CK3_12003
from xar_autoplayer.bridge.war_occupation_targets_contract import query_war_occupation_targets_v1_step


class HoldingAssaultConsumerTests(unittest.IsolatedAsyncioTestCase):
    async def test_registered_nonobjective_start_stop_use_independent_holding_flags(self):
        from mcp import Client

        war_id, province_id, siege_id = 117440524, 473, 503316540
        query_step = query_war_occupation_targets_v1_step(war_id)
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=0.1,
        )
        hello = _hello(
            "game.state.snapshot", "game.state.war-primary-opponent",
            "game.state.war-objectives", "game.state.war-objective-siege-progress",
            "game.state.war-objective-assault", "game.command.start-assault-N",
            "game.command.stop-assault-N", "game.command.query-war-occupation-targets-v1-N",
        )
        hello.update(expected_ck3_version=CK3_12003.game_version,
                     expected_ck3_sha256=CK3_12003.executable_sha256)
        endpoint.publish(hello)
        war = _war(war_id, war_objective_province_ids=[470, 3711, 472])
        active, native_revision = False, 690

        def publish_snapshot():
            endpoint.publish(_snapshot(
                native_revision, date_raw=53270736, active_wars=[war],
                played_character={"character_id": 29829, "alive": True},
            ))

        def holding_collection():
            # Arta's observed IDs/values are taken from cached Root 405. The
            # one-row territory, ACKs and flag transitions around it are an
            # explicit synthetic offline transport fixture, not a live run.
            siege = _active_siege(
                siege_id=siege_id, army_id=268435481, breach_level=2,
                assault_observable=True, assault_in_progress=active,
                can_start_assault=not active, can_stop_assault=active,
                progress_raw=62081, current_work_raw=27391190,
                total_work_raw=44121250, days_left=57,
                assault_daily_progress_raw=1006696, assault_daily_casualties=36,
            )
            return {
                "schema": "xar.ck3.war-occupation-targets.v1", "schema_version": 1,
                "game_version": CK3_12003.game_version,
                "executable_sha256": CK3_12003.executable_sha256,
                "available": True, "status": "available", "collection_complete": True,
                "unavailable_reason": None, "war_id": war_id,
                "actor_character_id": 29829, "player_side": "attacker",
                "primary_attacker_character_id": 29829, "primary_defender_character_id": 35991,
                "snapshot_revision": native_revision, "date_raw": 53270736,
                "side_counts": [
                    {"territory_side": "attacker", "eligible": 0, "occupied": 0,
                     "native_candidate_count": 0, "collection_complete": True},
                    {"territory_side": "defender", "eligible": 1, "occupied": 0,
                     "native_candidate_count": 1, "collection_complete": True},
                ],
                "rows": [{
                    "holding_title_id": 1314, "county_title_id": 1313, "province_id": province_id,
                    "legal_holder_character_id": 34180, "territory_side": "defender",
                    "occupation_observable": True, "is_occupied": False,
                    "occupying_character_id": None, "occupier_side": "none",
                    "counted_occupied_by_opposing_side": False,
                    "fort_level": 5, "garrison_size": 404, "besieging_strength": 3690,
                    "siege_observable": True, "active_siege": siege,
                }],
            }

        def answer(request):
            nonlocal active, native_revision
            if request.get("type") != "execute_step":
                return
            step = request["step"]
            if step == query_step:
                result = {"step": step, "accepted": True, "status": "available",
                          "query_sequence": len(endpoint.frames),
                          "war_occupation_targets_v1": holding_collection()}
            elif step == f"start-assault-{siege_id}":
                active = True
                result = {"step": step, "accepted": True, "status": "start_submitted"}
            elif step == f"stop-assault-{siege_id}":
                active = False
                result = {"step": step, "accepted": True, "status": "stop_submitted"}
            else:
                raise RuntimeError("unexpected fixture request: " + step)
            endpoint.publish({"type": "command_result", "protocol_version": 1,
                              "request_id": request["request_id"], "ok": True, "result": result})
            # Changing a holding outside the objective projection need not
            # change this snapshot. Only the independent query exposes flags.

        endpoint.send_hook = answer
        publish_snapshot()
        original_wars = copy.deepcopy(driver.take_snapshot()["active_wars"])
        self.assertNotIn(f"start-assault-{siege_id}", driver.capabilities()["action_steps"])
        async with Client(create_server(driver)) as client:
            queried = await client.call_tool("ck3_query_war_occupation_targets_v1", {
                "war_id": war_id, "expected_revision": driver.take_snapshot()["revision"],
            })
            self.assertFalse(queried.is_error, queried.content)
            self.assertIn(f"start-assault-{siege_id}", driver.capabilities()["action_steps"])
            started = await client.call_tool("ck3_start_assault", {
                "siege_id": siege_id, "expected_revision": driver.take_snapshot()["revision"],
            })
            self.assertFalse(started.is_error, started.content)
            result = started.structured_content
            self.assertEqual(result["assault_action"]["status"], "assault_started")
            self.assertEqual(result["assault_action"]["observation_source"], "war_occupation_query")
            self.assertEqual(result["assault_action"]["war_id"], war_id)
            self.assertEqual(result["assault_action"]["province_id"], province_id)
            self.assertTrue(result["active_siege"]["assault_in_progress"])
            active_view = _with_fresh_holding_siege_states(
                driver.take_snapshot(), driver._history_snapshot())
            self.assertEqual(_native_unobservable_started_assaults(
                active_view, driver._history_snapshot()), [])
            self.assertEqual(_life_advance_horizon_days(active_view), 1)
            self.assertEqual(_life_advance_timeline_policy(
                active_view, horizon_days=1, exact_one_day=False), (1, "player_assault"))
            self.assertIn(f"stop-assault-{siege_id}", driver.capabilities()["action_steps"])
            stopped = await client.call_tool("ck3_stop_assault", {
                "siege_id": siege_id, "expected_revision": driver.take_snapshot()["revision"],
            })
            self.assertFalse(stopped.is_error, stopped.content)
            self.assertEqual(stopped.structured_content["assault_action"]["status"], "assault_stopped")
            self.assertFalse(stopped.structured_content["active_siege"]["assault_in_progress"])
        self.assertEqual(driver.take_snapshot()["active_wars"], original_wars)
        self.assertEqual(driver.take_snapshot()["date_raw"], 53270736)
        self.assertEqual(driver.take_snapshot()["native_revision"], 690)
        self.assertEqual(_native_open_assault_lifecycles(driver._history_snapshot()), [])
        self.assertEqual([request["step"] for request in endpoint.frames
                          if request.get("type") == "execute_step"], [
            query_step, f"start-assault-{siege_id}", query_step,
            f"stop-assault-{siege_id}", query_step,
        ])
        self.__class__.validation_evidence = {
            "synthetic_offline_transport": True,
            "requests": copy.deepcopy(endpoint.frames),
            "start": started.structured_content,
            "stop": stopped.structured_content,
            "objective_projection": original_wars,
            "final_snapshot": driver.take_snapshot_without_native_command_history(),
        }
        driver.close()


if __name__ == "__main__":
    unittest.main()
