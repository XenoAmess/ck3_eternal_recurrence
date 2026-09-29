from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer import strategy
from xar_autoplayer.bridge.h3937_date_hold import (
    H3937_EPISODE_RUN_ID,
    H3937_SOURCE_DATE_RAW,
    h3937_date_hold_active,
    is_date_control_step,
)
from xar_autoplayer.bridge.war_contract import (
    BATTLE_DECISION_EPOCH_ADVANCE_STEP,
    COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP,
    WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP,
    advance_route_contact_horizon_step,
    battle_decision_epoch_advance_step,
    committed_route_sentinel_advance_step,
    query_route_contact_horizon_step,
    war_objective_hold_sentinel_advance_step,
)


def _h3937_snapshot(*, episode_run_id: str = H3937_EPISODE_RUN_ID,
                    date_raw: int = H3937_SOURCE_DATE_RAW) -> dict[str, object]:
    return {
        "episode_run_id": episode_run_id,
        "date_raw": date_raw,
        "played_character": {"character_id": 29_829, "alive": True},
        "active_wars": [{"war_id": 16_777_231}],
        "player_armies": [{"army_id": 83_886_367}],
        "paused": True,
    }


class H3937DateHoldTests(unittest.TestCase):
    def test_episode_binding_stays_closed_after_date_or_identity_drift(self) -> None:
        self.assertTrue(h3937_date_hold_active(_h3937_snapshot()))
        drifted = _h3937_snapshot(date_raw=H3937_SOURCE_DATE_RAW + 24)
        drifted["played_character"] = {"character_id": 1}
        drifted["active_wars"] = []
        drifted["player_armies"] = []
        self.assertTrue(h3937_date_hold_active(drifted))
        self.assertFalse(
            h3937_date_hold_active(
                _h3937_snapshot(episode_run_id="native-29829-prior")
            )
        )

    def test_date_control_classifier_keeps_read_only_query(self) -> None:
        date_steps = (
            "life-advance",
            "resume-map",
            "set-speed-3",
            BATTLE_DECISION_EPOCH_ADVANCE_STEP,
            COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP,
            WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP,
            battle_decision_epoch_advance_step(H3937_SOURCE_DATE_RAW + 24),
            committed_route_sentinel_advance_step(
                83_886_367, 2610, H3937_SOURCE_DATE_RAW + 24
            ),
            war_objective_hold_sentinel_advance_step(
                16_777_231, 83_886_367, 2610, H3937_SOURCE_DATE_RAW + 24
            ),
            advance_route_contact_horizon_step(83_886_367, 2610, (31,)),
        )
        for step in date_steps:
            with self.subTest(step=step):
                self.assertTrue(is_date_control_step(step))
        self.assertFalse(is_date_control_step("pause-map"))
        self.assertFalse(
            is_date_control_step(
                query_route_contact_horizon_step(83_886_367, 2610, (31,))
            )
        )

    def test_final_planner_denies_generic_sentinel_and_route_dates(self) -> None:
        date_steps = (
            "life-advance",
            BATTLE_DECISION_EPOCH_ADVANCE_STEP,
            COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP,
            WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP,
            committed_route_sentinel_advance_step(
                83_886_367, 2610, H3937_SOURCE_DATE_RAW + 24
            ),
            war_objective_hold_sentinel_advance_step(
                16_777_231, 83_886_367, 2610, H3937_SOURCE_DATE_RAW + 24
            ),
            advance_route_contact_horizon_step(83_886_367, 2610, (31,)),
        )
        with (
            mock.patch.object(strategy, "plan_raiktor_formal_exit", return_value=None),
            mock.patch.object(
                strategy, "_primary_defender_siege_forecast_ingress",
                side_effect=lambda plan, **_kwargs: plan,
            ),
            mock.patch.object(
                strategy, "_general_battle_forecast_ingress",
                side_effect=lambda plan, **_kwargs: plan,
            ),
            mock.patch.object(
                strategy, "_annotate_active_combat_resume_input",
                side_effect=lambda plan, _snapshot: plan,
            ),
            mock.patch.object(
                strategy, "observe_primary_defender_de_jure_exit",
                return_value=None,
            ),
        ):
            for step in date_steps:
                with self.subTest(step=step):
                    proposed = {"phase": "candidate", "selected_step": step}
                    with mock.patch.object(
                        strategy, "_choose_one_life_turn_core",
                        return_value=proposed,
                    ):
                        held = strategy.choose_one_life_turn(
                            [], snapshot=_h3937_snapshot(), action_steps=(step,)
                        )
                        self.assertIsNone(held["selected_step"])
                        self.assertEqual(held["blocked_date_step"], step)
                        self.assertEqual(
                            held["phase"],
                            "h3937_war_date_hold_pending_inventory_and_cash_policy",
                        )
                        old = strategy.choose_one_life_turn(
                            [],
                            snapshot=_h3937_snapshot(
                                episode_run_id="native-29829-prior"
                            ),
                            action_steps=(step,),
                        )
                        if step.startswith("advance-route-contact-horizon-"):
                            self.assertEqual(
                                old["phase"],
                                "native_war_route_contact_physical_inventory_unproven",
                            )
                        else:
                            self.assertEqual(old["selected_step"], step)


if __name__ == "__main__":
    unittest.main()
