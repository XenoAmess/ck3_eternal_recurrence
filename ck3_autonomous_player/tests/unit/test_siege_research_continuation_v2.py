"""Portable actual265 source replay through public production policy and Service.

The missing old baseline pursuit dictionary is reconstructed from the actual
AUTO's war/target. First-hop replies in the staged test are counterfactual;
actual259/261 replies, native identities and strength amounts are unchanged.
"""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest import mock

from xar_autoplayer import strategy
from xar_autoplayer.bridge import native_driver
from xar_autoplayer.bridge.driver import CallbackGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.siege_research_continuation_v2 import continue_siege_research_v2
from xar_autoplayer.war_mercenary_consumer_v1 import annotate_war_decision_reason_v1
from test_native_bridge_driver import FakeEndpoint, _hello, _snapshot, _army, _war, _tactical_sentinel_status

FIXTURE = Path(__file__).parents[1] / "fixtures/p55_actual265_route_projection.json"


def material():
    packet = json.loads(FIXTURE.read_text(encoding="utf-8"))
    frame = packet["actual_prefix_frame"]
    observed = packet["actual_observed_plan"]
    results = {row["sequence"]: row for row in packet["actual_read_results"]}
    strength = results[257]["result"]
    assert strength["source"] == {"revision": frame["revision"], "native_revision": frame["native_revision"]}
    # Explicit projection join: the compact native reply omits scope_role and
    # war_ids; same-frame SEM supplies membership, not invented soldier counts.
    own_ids = {army["army_id"] for army in frame["player_armies"]}
    rows = []
    for actual in strength["armies"]:
        army_id = actual["army_id"]
        war_ids = [war["war_id"] for war in frame["active_wars"]
                   if army_id in own_ids or any(enemy["army_id"] == army_id for enemy in war["enemy_armies"])]
        rows.append({**actual, "scope_role": "player" if army_id in own_ids else "active_war_enemy", "war_ids": war_ids})
    frame.update(army_strengths=rows, army_strengths_status=strength["status"],
                 army_strengths_profile=strength["army_strengths_profile"],
                 army_strengths_query_sequence=strength["query_sequence"],
                 army_strengths_queried_snapshot_id=frame["snapshot_id"],
                 army_strengths_queried_revision=frame["revision"])
    baseline = {"phase": observed["baseline_phase"], "selected_step": observed["baseline_selected_step"],
                "pursuit": {"war_id": observed["siege_relief"]["war_id"],
                            "target_province_id": observed["siege_relief"]["target_province_id"]}}
    history = [{"index": index, "command": results[seq]["step"], "ok": True,
                "result": results[seq]["result"]} for index, seq in enumerate((259, 261), 1)]
    caps = {native_driver.PREVIEW_MOVE_ARMY_CAPABILITY, native_driver.MOVE_ARMY_CAPABILITY,
            native_driver.QUERY_ROUTE_CONTACT_HORIZON_CAPABILITY, strategy.QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY}
    steps = {row["command"] for row in history} | {baseline["selected_step"], strategy.QUERY_ARMY_STRENGTHS_STEP}
    steps |= native_driver._fresh_preview_first_hop_steps(frame, history, steps, caps)
    return baseline, observed, frame, history, steps, caps


def review(baseline, observed, frame, history, steps, caps):
    return continue_siege_research_v2(baseline, observed, commands=history, snapshot=frame,
        action_steps=steps, bridge_capabilities=caps, review_general=strategy._general_battle_forecast_ingress)


def add_first_hop(history, observed, frame):
    """Counterfactual future readonly replies, explicitly not an actual source."""
    lease = {key: history[0]["result"][key] for key in (
        "queried_snapshot_id", "queried_revision", "queried_native_revision",
        "queried_connection_generation", "queried_episode_run_id")}
    preview = copy.deepcopy(observed["route_preview"])
    preview.update(target_province_id=2622, route_province_ids=[2622])
    history.append({"index": 3, "command": strategy.preview_move_army_step(167772577, 2622), "ok": True,
                    "result": {**lease, "route_preview": preview}})
    horizon = copy.deepcopy(observed["route_contact_horizon"])
    horizon["target_province_id"] = 2622
    horizon["subject_route"].update(route_province_ids=[2622], arrival_date_raws=[53358672])
    history.append({"index": 4, "command": strategy.query_route_contact_horizon_step(
        167772577, 2622, (285213101, 402653372, 436207707)), "ok": True,
        "result": {**lease, "route_contact_horizon": horizon}})


class SiegeResearchContinuationTests(unittest.TestCase):
    def test_native_passive_hold_stops_after_enemy_enters_combat_without_attack_authorization(self):
        endpoint = FakeEndpoint()
        driver = native_driver.NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
            command_timeout_seconds=.1, life_advance_timeout_seconds=.1)
        endpoint.publish(_hello("game.state.snapshot", "game.command.set-speed-3", "game.command.resume-map",
            "game.command.pause-map", "game.command.research-arm-tactical-daily-sentinel-v1-N",
            "game.command.research-query-tactical-daily-sentinel-v1"))
        start, stop = 53358576, 53358600
        target = start + 168
        player = _army(167772577, province_id=8755, army_state="regular", army_state_code=1,
            route_province_ids=[], owner_character_id=40695, in_combat=False, retreating=False)
        enemy = _army(285213101, province_id=2623, army_state="moving", army_state_code=7,
            route_province_ids=[8755], move_target_province_id=8755, owner_character_id=36445,
            controllable=False, in_combat=False, retreating=False)
        war = _war(100663323, allied_armies=[player], enemy_armies=[enemy], war_objective_province_ids=[8755])
        war.update(player_side="defender", player_is_primary_war_leader=True, player_relative_war_score=-12)
        played = {"character_id": 40695, "alive": True}
        endpoint.publish(_snapshot(1, date_raw=start, played_character=played, active_wars=[war], player_armies=[player]))
        armed = _tactical_sentinel_status(state="armed", generation=55, starting_date_raw=start,
            target_date_raw=target, observed_date_raw=start, speed=3, mode="decision_epoch", army_count=1, combat_count=0)
        fired = _tactical_sentinel_status(state="triggered", generation=55, starting_date_raw=start,
            target_date_raw=target, observed_date_raw=stop, speed=3, mode="decision_epoch", army_count=1,
            combat_count=0, completed_daily_ticks=1, trigger_flags=1 << 3, trigger_reasons=["combat_transition"],
            overshoot_days=0, pause_wrapper_called=True, pause_observed=True)
        contacted = {**player, "army_state": "combat", "army_state_code": 2, "in_combat": True}
        after_war = {**war, "allied_armies": [contacted]}
        def answer(frame):
            if frame.get("type") != "execute_step": return
            step = frame["step"]; result = {"step": step, "accepted": True, "status": "available"}
            if step.startswith("research-arm-tactical-daily-sentinel-v1-"): result["tactical_daily_sentinel"] = armed
            elif step == "research-query-tactical-daily-sentinel-v1": result["tactical_daily_sentinel"] = fired
            endpoint.publish({"type": "command_result", "protocol_version": 1,
                "request_id": frame["request_id"], "ok": True, "result": result})
            if step == "set-speed-3": endpoint.publish(_snapshot(2, date_raw=start, speed=3,
                played_character=played, active_wars=[war], player_armies=[player]))
            elif step == "resume-map": endpoint.publish(_snapshot(3, date_raw=stop, speed=3, paused=True,
                played_character=played, active_wars=[after_war], player_armies=[contacted]))
        endpoint.send_hook = answer
        try:
            result = driver.execute_step(strategy.war_objective_hold_sentinel_advance_step(
                100663323, 167772577, 8755, target))
            self.assertEqual(result["elapsed_days"], 1)
            self.assertEqual(result["trigger_reasons"], ["combat_transition"])
            self.assertEqual(result["war_objective_hold_admission"]["status"], "matched")
            self.assertEqual(result["war_objective_hold_post_stop"]["status"], "invalidated")
            self.assertEqual(result["external_pause_count"], 0)
            self.assertTrue(result["paused"])
            sent = [frame["step"] for frame in endpoint.frames if frame.get("type") == "execute_step"]
            self.assertFalse(any(step.startswith(("move-army-", "query-combat-simulation")) for step in sent))
        finally:
            driver.close()

    def test_actual_r3_reason_separates_cash_priority_555_from_shared_hostile_4783(self):
        packet = json.loads(FIXTURE.read_text(encoding="utf-8"))
        original = packet["actual_r3_finance_reason_example"]["actual_plan"]
        result = annotate_war_decision_reason_v1(original)
        self.assertEqual(result["selected_step"], "move-army-167772577-to-2622")
        self.assertEqual(result["reason"], original["reason"])  # Machine contract is unchanged.
        # Exercise the actual compact feed and display formatter. Neither
        # import invokes a desktop, process, SDK, or live overlay operation.
        root = Path(__file__).parents[3]
        modules = []
        for name in ("decision_observation_feed", "live_decision_overlay"):
            path = root / "tools/g2_saved_campaign" / (name + ".py")
            spec = importlib.util.spec_from_file_location("war_reason_test_" + name, path)
            module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
            modules.append(module)
        compact = modules[0].compact_plan(result)
        self.assertEqual(compact["reason"], original["reason"])
        rendered = modules[1].reason_text(compact)
        self.assertIn("我军1357", rendered)
        self.assertIn("优先保地战敌555", rendered)
        self.assertIn("全部主导战争敌军4783（去重）", rendered)
        self.assertIn("雇佣报价与抵达未核实", rendered)
        self.assertNotIn("合同172", rendered)
        # A later LIFE consumer may select a different action; old bound war
        # wording must not describe that action as the earlier movement.
        superseded = {**result, "phase": "lifestyle_private_selection", "selected_step": "private-life-perk",
                      "reason": "spend the native legal perk", "lifestyle_deferred_war_red": {
                          "reason": "route input unavailable"}}
        projected = modules[0].compact_plan(superseded)
        self.assertNotIn("war_decision_presentation_v1", projected)
        self.assertEqual(modules[1].reason_text(projected), "spend the native legal perk")
        self.assertEqual(modules[1].reason_text(superseded), "spend the native legal perk")
        self.assertEqual(result["war_decision_reason_scope_v1"]["primary_war_ids"], [100663323, 134217796])
        self.assertIsNone(result["war_decision_reason_scope_v1"]["battle_win_probability"])

    def test_actual_original_siege_ingress_then_general_uses_full_three_enemy_scope(self):
        b, o, s, h, steps, caps = material()
        with mock.patch.object(strategy, "forecast_fixed_contact", side_effect=AssertionError("no large model input needed")):
            original = strategy._primary_defender_siege_forecast_ingress(
                b, commands=h, snapshot=s, action_steps=steps, bridge_capabilities=caps)
            self.assertEqual(original["phase"], "native_war_siege_forecast_inputs_query")
            result = review(b, original, s, h, steps, caps)
        self.assertEqual(result["selected_step"], "preview-move-army-167772577-to-2622")
        self.assertEqual(result["phase"], "native_war_general_battle_short_preview")
        self.assertFalse(result["active_attack_allowed"])
        self.assertEqual(result["route_contact_horizon"]["hostile_army_ids"], [285213101, 402653372, 436207707])
        self.assertEqual(next(row for row in s["army_strengths"] if row["army_id"] == 285213101)["current_soldiers"], 4228)

    def test_first_hop_stages_require_exact_preview_fresh_full_hostile_h1_and_native_identity(self):
        b, o, s, h, steps, caps = material()
        add_first_hop(h, o, s)
        s["history"] = h
        first = review(b, o, s, h[:-1], steps, caps)
        self.assertEqual(first["phase"], "native_war_general_battle_short_contact_query")
        self.assertIn("285213101", first["selected_step"])
        result = review(b, o, s, h, steps, caps)
        self.assertEqual(result["selected_step"], "move-army-167772577-to-2622")
        self.assertFalse(result["future_contact_authorized"])
        self.assertFalse(result["siege_research_continuation_v2"]["full_hop_safety_proven"])
        for change in ("contact", "missing_hostile", "stale_h1", "wrong_hop", "no_admitted_move", "no_carmy", "stale_carmy", "duplicate_carmy"):
            hh, ss, st = copy.deepcopy((h, s, steps))
            if change == "contact": hh[-1]["result"]["route_contact_horizon"].update(one_day_contact_free=False, conflicts=[{"province_id": 2622, "hostile_army_id": 285213101}])
            elif change == "missing_hostile": hh[-1]["result"]["route_contact_horizon"]["hostile_army_ids"] = [402653372, 436207707]
            elif change == "stale_h1": hh[-1]["result"]["queried_revision"] -= 1
            elif change == "wrong_hop": hh[-2]["result"]["route_preview"]["route_province_ids"] = [2623, 2622]
            elif change == "no_admitted_move": st.remove("move-army-167772577-to-2622")
            elif change == "no_carmy": ss["army_strengths"][0]["native_carmy_id"] = None
            elif change == "stale_carmy": ss["army_strengths_queried_revision"] -= 1
            elif change == "duplicate_carmy": ss["army_strengths"].append(copy.deepcopy(ss["army_strengths"][0]))
            with self.subTest(change=change):
                rejected = review(b, o, ss, hh, st, caps)
                self.assertNotEqual(rejected.get("selected_step"), "move-army-167772577-to-2622")
                if "carmy" in change: self.assertEqual(rejected["selected_step"], strategy.QUERY_ARMY_STRENGTHS_STEP)

    def test_whole_choose_and_service_admit_only_original_general_first_hop(self):
        b, o, s, h, steps, caps = material()
        add_first_hop(h, o, s)
        s["history"] = h
        driver = CallbackGameplayDriver(backend_id="native-headless", snapshot=lambda: copy.deepcopy(s),
            execute=lambda *_: {}, action_steps=tuple(steps))
        original_caps = driver.capabilities
        driver.capabilities = lambda: {**original_caps(), "bridge_capabilities": list(caps)}
        service = GameplayBridgeService(driver)
        original_ingress = strategy._primary_defender_siege_forecast_ingress
        with mock.patch.object(strategy, "_choose_one_life_turn_core", return_value=b), \
             mock.patch.object(strategy, "_primary_defender_siege_forecast_ingress", wraps=original_ingress) as ingress, \
             mock.patch.object(strategy, "_general_battle_forecast_ingress", wraps=strategy._general_battle_forecast_ingress) as general:
            planned = service.plan_turn()
        self.assertGreater(ingress.call_count, 0)
        self.assertGreaterEqual(general.call_count, 2)  # restored proposal, then ordinary post-processing
        self.assertEqual(planned["plan"]["selected_step"], "move-army-167772577-to-2622")
        self.assertFalse(planned["plan"]["active_attack_allowed"])

    def test_original_passive_hold_uses_native_predicate_and_keeps_seven_day_daily_stop(self):
        b, o, s, h, steps, caps = material()
        b = {"phase": "native_war_stationary_objective_hold_sentinel", "selected_step":
             strategy.war_objective_hold_sentinel_advance_step(100663323, 167772577, 8755, s["date_raw"] + 168)}
        # A contact prediction can be adverse. A passive hold grants no new move
        # and has the same Native combat-transition interrupt as ordinary defense.
        o["route_contact_horizon"].update(one_day_contact_free=False, conflicts=[{"province_id": 8755, "hostile_army_id": 285213101}])
        result = review(b, o, s, h, steps, caps)
        self.assertEqual(result["selected_step"], b["selected_step"])
        proof = result["siege_research_passive_defense_v2"]
        self.assertEqual(proof["native_hold_admission"]["status"], "matched")
        self.assertEqual(proof["maximum_days"], 7)
        self.assertFalse(proof["first_day_contact_free_proven"])
        self.assertTrue(proof["enemy_initiated_contact_possible"])
        for change in ("moving", "combat", "wrong_objective", "window", "stale_carmy"):
            ss = copy.deepcopy(s)
            if change == "moving": ss["player_armies"][0]["move_target_province_id"] = 2622
            elif change == "combat": ss["player_armies"][0]["in_combat"] = True
            elif change == "wrong_objective": ss["player_armies"][0]["current_province_id"] = 2622
            elif change == "window": ss["top_exclusive_modal_choice_hint"] = {"status": "present"}
            elif change == "stale_carmy": ss["army_strengths_queried_revision"] -= 1
            with self.subTest(change=change):
                self.assertNotEqual(review(b, o, ss, h, steps, caps).get("selected_step"), b["selected_step"])

    def test_admitted_attack_future_formal_observation_and_unrelated_block_keep_priority(self):
        b, o, s, h, steps, caps = material()
        for change in ("attack", "formal", "v3", "different_block", "other_army"):
            bb, oo, ss, cc = copy.deepcopy((b, o, s, caps))
            if change == "attack": oo["active_attack_allowed"] = True
            elif change == "formal":
                oo["phase"] = "native_war_siege_forecast_inputs_query";ss["combat_entry_eu_v1"] = {}
            elif change == "v3": cc.add(strategy.QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY)
            elif change == "different_block": oo.update(phase="native_war_siege_forecast_observation_blocked", reason="different unresolved read")
            elif change == "other_army": bb["selected_step"] = "move-army-99-to-2619"
            with self.subTest(change=change): self.assertIs(review(bb, oo, ss, h, steps, cc), oo)
