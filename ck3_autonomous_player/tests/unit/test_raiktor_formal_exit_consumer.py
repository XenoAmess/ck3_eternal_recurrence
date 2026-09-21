from __future__ import annotations

from copy import deepcopy
import unittest

from xar_autoplayer.bridge.war_contract import (
    query_war_termination_options_step,
    offer_white_peace_step,
)
from xar_autoplayer.bridge.war_entry_contract import query_war_entry_assessments_step
from xar_autoplayer.raiktor_formal_exit import (
    _opponent_terminal_control_input,
    _utility_comparison_trace,
    plan_raiktor_formal_exit,
)
from test_native_bridge_driver import _termination_options


WAR_ID = 33_554_473
OPPONENT = 28_551
OPTIONS = query_war_termination_options_step(WAR_ID)
POWER = query_war_entry_assessments_step([OPPONENT])


def _snapshot() -> dict[str, object]:
    return {
        "paused": True,
        "snapshot_id": "native:3",
        "revision": 4,
        "native_revision": 3,
        "date_raw": 53_192_352,
        "episode_run_id": "native-29829-fixture",
        "diagnostics": {"connection_generation": 1},
        "active_event": None,
        "pending_character_interaction": None,
        "active_wars": [{
            "war_id": WAR_ID,
            "player_side": "attacker",
            "player_is_primary_war_leader": True,
            "primary_opponent_character_id": OPPONENT,
            "player_relative_war_score": -41,
        }],
        "war_termination_options": [{
            "war_id": WAR_ID,
            "active_casus_belli_identity": {"canonical_key": "raiktor_claim_cb"},
        }],
        "war_entry_assessments_two_read_trace_v1": [],
    }


def _query_row(step: str, snapshot: dict[str, object]) -> dict[str, object]:
    return {
        "command": step,
        "ok": True,
        "result": {
            "queried_snapshot_id": snapshot["snapshot_id"],
            "queried_revision": snapshot["revision"],
            "queried_native_revision": snapshot["native_revision"],
            "queried_connection_generation": snapshot["diagnostics"]["connection_generation"],
            "queried_episode_run_id": snapshot["episode_run_id"],
        },
    }


def _options_result(
    snapshot: dict[str, object], *, score: int, war_duration_days: int = 203
) -> dict[str, object]:
    result = _query_row(OPTIONS, snapshot)["result"]
    result["war_termination_options"] = _termination_options(
        WAR_ID,
        score=score,
        casus_belli_database_index=411,
        casus_belli_key="raiktor_claim_cb",
        war_duration_days=war_duration_days,
    )
    return result


def _white_projection_frame() -> dict[str, object]:
    return {
        "white_peace_observation": {
            "frame": {
                "snapshot_id": "native:3",
                "snapshot_revision": 4,
                "native_revision": 3,
                "date_raw": 53_192_352,
                "connection_id": "connection-generation:1",
                "episode_id": "native-29829-fixture",
                "ck3_pid": 92_612,
                "paused": True,
                "war_id": WAR_ID,
                "active_casus_belli_database_index": 411,
                "active_casus_belli_key": "raiktor_claim_cb",
                "primary_attacker_character_id": 29_829,
                "primary_defender_character_id": OPPONENT,
                "claimant_character_id": 29_829,
            }
        }
    }


class RaiktorFormalExitConsumerTests(unittest.TestCase):
    def test_builds_frame_bound_minus_100_terminal_control(self) -> None:
        snapshot = _snapshot()
        war = snapshot["active_wars"][0]
        war["player_relative_war_score"] = -100

        control = _opponent_terminal_control_input(
            war=war,
            war_id=WAR_ID,
            opponent_character_id=OPPONENT,
            options_query=_options_result(snapshot, score=-100),
            white_peace_projection=_white_projection_frame(),
        )

        self.assertTrue(control["opponent_terminal_control"])
        self.assertEqual(control["attacker_war_score"], -100)
        self.assertEqual(control["defender_war_score"], 100)
        self.assertEqual(control["war_duration_days"], 203)
        self.assertEqual(control["frame"]["war_id"], WAR_ID)

    def test_minus_99_is_complete_but_not_terminal_control(self) -> None:
        snapshot = _snapshot()
        war = snapshot["active_wars"][0]
        war["player_relative_war_score"] = -99

        control = _opponent_terminal_control_input(
            war=war,
            war_id=WAR_ID,
            opponent_character_id=OPPONENT,
            options_query=_options_result(snapshot, score=-99),
            white_peace_projection=_white_projection_frame(),
        )

        self.assertFalse(control["opponent_terminal_control"])

    def test_incomplete_absolute_scores_fail_closed(self) -> None:
        snapshot = _snapshot()
        war = snapshot["active_wars"][0]
        war["player_relative_war_score"] = -100
        options = _options_result(snapshot, score=-100)
        options["war_termination_options"][
            "absolute_war_scores_observable"
        ] = False
        options["war_termination_options"]["attacker_war_score"] = None
        options["war_termination_options"]["defender_war_score"] = None

        with self.assertRaisesRegex(ValueError, "incomplete or drifted"):
            _opponent_terminal_control_input(
                war=war,
                war_id=WAR_ID,
                opponent_character_id=OPPONENT,
                options_query=options,
                white_peace_projection=_white_projection_frame(),
            )

    def test_own_plus_100_keeps_enforce_demands_priority(self) -> None:
        snapshot = _snapshot()
        snapshot["active_wars"][0]["player_relative_war_score"] = 100

        plan = plan_raiktor_formal_exit(
            snapshot, [], action_steps=[], bridge_capabilities=[]
        )

        self.assertIsNone(plan)

    def test_success_certificate_records_threeway_legality_and_margin(self) -> None:
        certificate = {
            "utility_unit": "strategy_utility_q100000",
            "options": {
                "continue": {
                    "eligible": True, "utility_raw": -20,
                    "hard_budget_breaches": [], "execution_blockers": [],
                    "measured_power_relation": "opponent_stronger",
                    "tail_risk_penalty_raw": 20,
                    "tail_risk_base_penalty_raw": 20,
                    "tail_risk_power_scale_applied": True,
                    "observed_war_duration_days": 804,
                    "observed_player_relative_war_score": -3,
                    "measured_power_ratio_raw": 228560,
                    "measured_power_ratio_scale": 100000,
                    "ignored_internal_character_id": 97531,
                },
                "white_peace": {
                    "eligible": True, "utility_raw": 14,
                    "hard_budget_breaches": [], "execution_blockers": [],
                    "uncertainty_penalty_raw": 6,
                },
                "surrender": {
                    "eligible": False, "utility_raw": 35,
                    "hard_budget_breaches": ["gold_budget_breached"],
                    "execution_blockers": [], "uncertainty_penalty_raw": 2,
                },
            },
            "comparison": {
                "status": "static_recommendation_available",
                "eligible_options": ["continue", "white_peace"],
                "winning_margin_raw": 34,
                "minimum_switch_margin_raw": 10,
            },
        }

        trace = _utility_comparison_trace(certificate)

        self.assertEqual(set(trace["options"]), {"continue", "white_peace", "surrender"})
        self.assertEqual(trace["options"]["white_peace"]["utility_raw"], 14)
        self.assertFalse(trace["options"]["surrender"]["eligible"])
        self.assertEqual(trace["comparison"]["winning_margin_raw"], 34)
        self.assertNotIn("ignored_internal_character_id", trace["options"]["continue"])
        self.assertTrue(
            trace["options"]["continue"]["tail_risk_power_scale_applied"]
        )
        self.assertEqual(
            trace["options"]["continue"]["measured_power_ratio_raw"], 228560
        )

    def test_requests_two_actual_power_reads_before_terms(self) -> None:
        snapshot = _snapshot()
        steps = [OPTIONS, POWER]
        first = plan_raiktor_formal_exit(snapshot, [], action_steps=steps, bridge_capabilities=[])
        self.assertEqual(first["selected_step"], OPTIONS)
        rows = [_query_row(OPTIONS, snapshot)]
        second = plan_raiktor_formal_exit(snapshot, rows, action_steps=steps, bridge_capabilities=[])
        self.assertEqual(second["selected_step"], POWER)
        snapshot["war_entry_assessments_two_read_trace_v1"] = [{"target_character_id": OPPONENT}]
        third = plan_raiktor_formal_exit(snapshot, rows, action_steps=steps, bridge_capabilities=[])
        self.assertEqual(third["selected_step"], POWER)

    def test_rejects_pre_restore_query_and_unconfirmed_terminal(self) -> None:
        snapshot = _snapshot()
        old = _query_row(OPTIONS, snapshot)
        rows = [old, {"command": "restore-checkpoint", "ok": True}]
        plan = plan_raiktor_formal_exit(snapshot, rows, action_steps=[OPTIONS, POWER], bridge_capabilities=[])
        self.assertEqual(plan["selected_step"], OPTIONS)
        fresh = _query_row(OPTIONS, snapshot)
        fresh["result"]["queried_connection_generation"] = 99
        plan = plan_raiktor_formal_exit(snapshot, [fresh], action_steps=[OPTIONS, POWER], bridge_capabilities=[])
        self.assertEqual(plan["selected_step"], OPTIONS)
        snapshot["active_wars"][0]["player_relative_war_score"] = -100
        submitted = deepcopy(rows)
        submitted.append({"command": offer_white_peace_step(WAR_ID), "ok": True})
        plan = plan_raiktor_formal_exit(snapshot, submitted, action_steps=[OPTIONS, POWER], bridge_capabilities=[])
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(plan["reason"], "previous_terminal_submission_requires_fresh_status")
