"""Synthetic M5 scenarios for the observed valid public CUnitID zero."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.m5_joint_budget_selector import select_m5_assessed_candidate
from xar_autoplayer.m5_joint_dispatch import M5FrameDispatcher
from xar_autoplayer.m5_observed_opportunity_selector import (
    active_defensive_war_continuation_proposal,
    select_observed_m5_opportunity,
)
from xar_autoplayer.m5_war_cash_resource_v1 import (
    observe_active_war_cash_resource_v1,
    observe_aggregate_active_war_cash_resource_v1,
    require_complete_aggregate_war_cash_resource_v1,
)


FRAME = {
    "played_character_id": 29829, "native_revision": 9,
    "date_raw": 53178264, "snapshot_id": "native:9", "revision": 14,
    "episode_run_id": "synthetic-army-zero-m5",
}
WAR = 16777231
AMOUNTS = {
    "pending_war_cash_raw": 100,
    "immediate_war_action_cost_raw": 20,
    "future_war_cost_upper_raw": 300,
    "future_risk_budget_raw": 50,
    "policy_minimum_gold_reserve_raw": 200,
}


def snapshot(war_ids: tuple[int, ...] = (WAR,)) -> dict[str, object]:
    return {
        **FRAME, "paused": True, "map_ready": True,
        "played_character": {"character_id": FRAME["played_character_id"]},
        "played_character_gold": {"raw": 1_000_000, "scale": 100_000},
        "active_wars": [{
            "war_id": war_id, "player_side": "defender",
            "player_is_primary_war_leader": True,
        } for war_id in war_ids],
        "player_armies": [{"army_id": 0, "controllable": True}],
    }


def commitments() -> dict[str, object]:
    return {
        "frame": dict(FRAME), "gold_raw": 0, "pending_war_slots": 0,
        "army_ids": [], "ally_character_ids": [], "character_ids": [],
        "commitment_keys": [],
    }


def cash_inputs(war_id: int, war_ids: tuple[int, ...]) -> dict[str, object]:
    result: dict[str, object] = {
        "source_frame": dict(FRAME), "war_id": war_id, "horizon_days": 7,
        "future_bound_assumptions": ["synthetic bounded amounts only"],
        "resource_claims": {
            "source": "synthetic-current-occupation",
            "source_frame": dict(FRAME), "war_id": war_id,
            "army_ids": [0], "ally_character_ids": [],
            "character_ids": [], "commitment_keys": [],
        },
    }
    for name, raw in AMOUNTS.items():
        result[name] = {
            "raw": raw, "scale": 100_000, "source": "synthetic-amount",
            "source_frame": dict(FRAME), "war_id": war_id,
            "resource_components": [{
                "resource_kind": f"synthetic-shared-{name}",
                "resource_id": str(FRAME["played_character_id"]),
                "owner_character_id": FRAME["played_character_id"],
                "war_ids": list(war_ids), "raw": raw, "scale": 100_000,
                "source": "synthetic-amount", "source_frame": dict(FRAME),
            }],
        }
    return result


def continuation_inputs() -> tuple[dict[str, object], dict[str, object]]:
    current = snapshot()
    plan = {
        "policy": "one-life-turn-v1", "phase": "native_war_termination_query",
        "selected_step": f"query-war-termination-options-{WAR}",
        "war_id": WAR, "active_wars": deepcopy(current["active_wars"]),
    }
    observation = {
        "status": "available", "read_only": True,
        "source_frame": dict(FRAME), "war_id": WAR,
        "army_ids": [0], "ally_character_ids": [], "character_ids": [],
        "army_war_bindings": [{"army_id": 0, "war_id": WAR}],
        "projected_supply_margin_raw": 1,
        "incremental_gold_cost_raw": AMOUNTS["immediate_war_action_cost_raw"],
        "minimum_gold_reserve_raw": 550,
        "war_cash_resource": observe_active_war_cash_resource_v1(
            snapshot=current, war_id=WAR, inputs=cash_inputs(WAR, (WAR,)),
        ),
    }
    return plan, observation


def continuation() -> dict[str, object]:
    plan, observation = continuation_inputs()
    return active_defensive_war_continuation_proposal(
        frame=FRAME, snapshot=snapshot(), plan=plan, observation=observation,
    )


def assessed_inputs() -> tuple[dict[str, object], list[dict[str, object]]]:
    candidates = [{"candidate_id": f"war:synthetic:{index}", "domain": "war"}
                  for index in range(5)]
    intake = {**FRAME, "policy": "g2-m5-same-frame-intake-v1",
              "candidates": candidates}
    rows = [{
        **FRAME, "candidate_id": candidate["candidate_id"],
        "benefit_units": index + 1, "war_cost_units": 0,
        "family_cost_units": 0, "diplomacy_cost_units": 0,
        "supply_cost_units": 0, "long_term_cost_units": 0,
        "gold_raw": 0, "projected_supply_margin_units": 1,
        "army_ids": [0], "ally_character_ids": [], "character_ids": [],
        "commitment_keys": [],
    } for index, candidate in enumerate(candidates)]
    return intake, rows


class PublicArmyZeroClaimsTests(unittest.TestCase):
    def test_shared_zero_army_cash_occupation_and_amounts_count_once(self) -> None:
        war_ids = (WAR, WAR + 1)
        current = snapshot(war_ids)
        receipts = [observe_active_war_cash_resource_v1(
            snapshot=current, war_id=war_id, inputs=cash_inputs(war_id, war_ids),
        ) for war_id in war_ids]
        result = observe_aggregate_active_war_cash_resource_v1(
            snapshot=current, receipts=receipts,
        )
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["existing_resource_claims"]["army_ids"], [0])
        self.assertEqual(result["amount_values_raw"], AMOUNTS)
        self.assertTrue(all(len(rows) == 1 for rows in result["amount_resources"].values()))
        self.assertEqual(require_complete_aggregate_war_cash_resource_v1(
            result, frame=FRAME, war_ids=war_ids,
        ), result)
        self.assertFalse(result["formal_action_ready"])

    def test_continuation_reserves_zero_army_and_competing_claim_conflicts(self) -> None:
        proposal = continuation()
        self.assertEqual(proposal["army_ids"], [0])
        dispatcher = M5FrameDispatcher(
            snapshot=snapshot(), existing_commitments=commitments(),
        )
        first = dispatcher.choose_observed(
            snapshot=snapshot(), proposals=[proposal],
            gold_reserve_raw=0, max_active_wars=1,
        )
        self.assertEqual(first["status"], "reserved_observed_analytic")
        reserved = first["reservation"]["commitments_after"]
        self.assertEqual(reserved["army_ids"], [0])
        competing = {**proposal, "candidate_id": "war:competing-army-claim",
                     "commitment_keys": ["synthetic-other-operation"]}
        second = M5FrameDispatcher(
            snapshot=snapshot(), existing_commitments=reserved,
        ).choose_observed(
            snapshot=snapshot(), proposals=[competing],
            gold_reserve_raw=0, max_active_wars=1,
        )
        self.assertEqual(second["status"], "wait")
        self.assertEqual(second["analysis"]["evaluated"][0]["reason"],
                         "existing_commitment_conflict")
        self.assertFalse(first["formal_action_ready"])

    def test_assessed_selection_preserves_zero_army_and_occupied_zero_conflicts(self) -> None:
        intake, rows = assessed_inputs()
        args = {
            "intake": intake, "snapshot": snapshot(), "assessments": rows,
            "commitments": commitments(), "gold_reserve_raw": 0,
            "max_active_wars": 2,
        }
        result = select_m5_assessed_candidate(**args)
        self.assertEqual(result["selected_candidate_id"], "war:synthetic:4")
        self.assertEqual(result["evaluated"][-1]["claims"]["army_ids"], [0])
        args["commitments"]["army_ids"] = [0]
        result = select_m5_assessed_candidate(**args)
        self.assertEqual(result["status"], "wait")
        self.assertTrue(all(row["reason"] == "existing_commitment_conflict"
                            for row in result["evaluated"]))

    def test_invalid_claims_still_fail_at_each_public_consumer(self) -> None:
        cases = (("army_ids", [-1]), ("army_ids", [False]),
                 ("army_ids", [0, 0]), ("character_ids", [0]),
                 ("ally_character_ids", [0]))
        proposal = continuation()
        for kind, values in cases:
            with self.subTest(kind=kind, values=values):
                inputs = cash_inputs(WAR, (WAR,))
                inputs["resource_claims"][kind] = values
                with self.assertRaises(ValueError):
                    observe_active_war_cash_resource_v1(
                        snapshot=snapshot(), war_id=WAR, inputs=inputs,
                    )
                invalid_commitments = commitments()
                invalid_commitments[kind] = values
                with self.assertRaises(ValueError):
                    M5FrameDispatcher(snapshot=snapshot(),
                                      existing_commitments=invalid_commitments)
                invalid_proposal = {**proposal, kind: values}
                with self.assertRaises(ValueError):
                    select_observed_m5_opportunity(
                        snapshot=snapshot(), proposals=[invalid_proposal],
                        commitments=commitments(), gold_reserve_raw=0,
                        max_active_wars=1,
                    )
                intake, rows = assessed_inputs()
                rows[0][kind] = values
                with self.assertRaises(ValueError):
                    select_m5_assessed_candidate(
                        intake=intake, snapshot=snapshot(), assessments=rows,
                        commitments=commitments(), gold_reserve_raw=0,
                        max_active_wars=2,
                    )
                plan, observation = continuation_inputs()
                observation[kind] = values
                with self.assertRaises(ValueError):
                    active_defensive_war_continuation_proposal(
                        frame=FRAME, snapshot=snapshot(), plan=plan,
                        observation=observation,
                    )

    def test_zero_war_remains_invalid(self) -> None:
        with self.assertRaises(ValueError):
            observe_active_war_cash_resource_v1(
                snapshot=snapshot((0,)), war_id=0,
                inputs=cash_inputs(0, (0,)),
            )


if __name__ == "__main__":
    unittest.main()
