from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.m5_war_cash_resource_v1 import (
    observe_aggregate_active_war_cash_resource_v1,
    observe_active_war_cash_resource_v1,
    require_complete_aggregate_war_cash_resource_v1,
    require_complete_war_cash_resource_v1,
)

FRAME = {
    "played_character_id": 29829,
    "native_revision": 3,
    "date_raw": 53217624,
    "snapshot_id": "native:3",
    "revision": 4,
    "episode_run_id": "native-29829-2bc2d599f7f9",
}
WAR_ID = 16777231


def snapshot() -> dict[str, object]:
    return {
        **FRAME, "paused": True, "map_ready": True,
        "played_character_gold": {"raw": 111_861_020, "scale": 100_000},
        "active_wars": [{"war_id": WAR_ID}],
    }


def amount(raw: int, source: str) -> dict[str, object]:
    return {"raw": raw, "scale": 100_000, "source": source,
            "source_frame": dict(FRAME), "war_id": WAR_ID}


def complete_inputs() -> dict[str, object]:
    return {
        "source_frame": dict(FRAME), "war_id": WAR_ID,
        "pending_war_cash_raw": amount(2_000_000, "test-same-frame-pending"),
        "immediate_war_action_cost_raw": amount(1_000_000, "test-fee"),
        "future_war_cost_upper_raw": amount(6_000_000, "test-horizon-bound"),
        "future_risk_budget_raw": amount(2_000_000, "test-risk-allowance"),
        "policy_minimum_gold_reserve_raw": amount(3_000_000, "test-policy"),
        "horizon_days": 7,
        "future_bound_assumptions": ["synthetic seven-day bound"],
    }


SECOND_WAR_ID = WAR_ID + 1
AMOUNT_NAMES = (
    "pending_war_cash_raw", "immediate_war_action_cost_raw",
    "future_war_cost_upper_raw", "future_risk_budget_raw",
    "policy_minimum_gold_reserve_raw",
)


def multiwar_snapshot() -> dict[str, object]:
    result = snapshot()
    result["active_wars"].append({"war_id": SECOND_WAR_ID})
    return result


def multiwar_inputs(war_id: int) -> dict[str, object]:
    result = complete_inputs()
    result["war_id"] = war_id
    for name in AMOUNT_NAMES:
        row = result[name]
        row["war_id"] = war_id
        shared = name in {
            "future_war_cost_upper_raw", "future_risk_budget_raw",
            "policy_minimum_gold_reserve_raw",
        }
        kind = ("actor_war_reserve" if name == "policy_minimum_gold_reserve_raw"
                else "actor_military_maintenance" if shared else "war_action")
        row["resource_components"] = [{
            "resource_kind": kind,
            "resource_id": name if shared else f"{war_id}:{name}",
            "owner_character_id": FRAME["played_character_id"],
            "war_ids": [WAR_ID, SECOND_WAR_ID] if shared else [war_id],
            "raw": row["raw"], "scale": 100_000,
            "source": row["source"], "source_frame": dict(FRAME),
        }]
    result["resource_claims"] = {
        "source": "synthetic-observed-war-occupation",
        "source_frame": dict(FRAME), "war_id": war_id,
        "army_ids": [71], "ally_character_ids": [41003],
        "character_ids": [29829], "commitment_keys": [f"active-war:{war_id}"],
    }
    return result


def multiwar_receipts() -> list[dict[str, object]]:
    return [observe_active_war_cash_resource_v1(
        snapshot=multiwar_snapshot(), war_id=war_id, inputs=multiwar_inputs(war_id),
    ) for war_id in (WAR_ID, SECOND_WAR_ID)]


class WarCashResourceTests(unittest.TestCase):
    def test_h2825_evidence_yields_typed_missing_not_zero(self) -> None:
        receipt = observe_active_war_cash_resource_v1(
            snapshot=snapshot(), war_id=WAR_ID,
            inputs={"source_frame": FRAME, "war_id": WAR_ID},
        )
        self.assertEqual(receipt["status"], "incomplete")
        self.assertEqual(receipt["observed_treasury_raw"], 111_861_020)
        self.assertIsNone(receipt["existing_shared_gold_commitment_raw"])
        self.assertIsNone(receipt["war_future_gold_cost_raw"])
        self.assertIn("future_war_cost_upper_raw", receipt["missing"])
        self.assertIn("policy_minimum_gold_reserve_raw", receipt["missing"])
        with self.assertRaisesRegex(ValueError, "complete same-frame"):
            require_complete_war_cash_resource_v1(
                receipt, frame=FRAME, war_id=WAR_ID,
            )

    def test_complete_resource_separates_pending_action_and_future_reserve(self) -> None:
        receipt = observe_active_war_cash_resource_v1(
            snapshot=snapshot(), war_id=WAR_ID, inputs=complete_inputs(),
        )
        self.assertEqual(receipt["status"], "complete")
        self.assertEqual(receipt["existing_shared_gold_commitment_raw"], 2_000_000)
        self.assertEqual(receipt["immediate_war_action_cost_raw"], 1_000_000)
        self.assertEqual(receipt["war_future_gold_cost_raw"], 8_000_000)
        self.assertEqual(receipt["joint_gold_reserve_raw"], 11_000_000)
        self.assertEqual(receipt["horizon_days"], 7)
        self.assertEqual(
            receipt["amount_observations"]["future_war_cost_upper_raw"]["source_frame"],
            FRAME,
        )
        self.assertEqual(
            require_complete_war_cash_resource_v1(
                receipt, frame=FRAME, war_id=WAR_ID,
            )["war_id"], WAR_ID,
        )

    def test_stale_frame_and_wrong_war_are_rejected(self) -> None:
        inputs = complete_inputs()
        inputs["source_frame"] = {**FRAME, "revision": 5}
        with self.assertRaisesRegex(ValueError, "full paused frame"):
            observe_active_war_cash_resource_v1(
                snapshot=snapshot(), war_id=WAR_ID, inputs=inputs,
            )
        inputs = complete_inputs()
        inputs["war_id"] = WAR_ID + 1
        with self.assertRaisesRegex(ValueError, "WarID"):
            observe_active_war_cash_resource_v1(
                snapshot=snapshot(), war_id=WAR_ID, inputs=inputs,
            )
        inputs = complete_inputs()
        inputs["future_war_cost_upper_raw"]["source_frame"]["revision"] = 5
        with self.assertRaisesRegex(ValueError, "same-frame sourced"):
            observe_active_war_cash_resource_v1(
                snapshot=snapshot(), war_id=WAR_ID, inputs=inputs,
            )

    def test_unproved_zero_and_forged_reserve_are_rejected(self) -> None:
        inputs = complete_inputs()
        inputs["pending_war_cash_raw"] = 0
        with self.assertRaisesRegex(ValueError, "sourced nonnegative"):
            observe_active_war_cash_resource_v1(
                snapshot=snapshot(), war_id=WAR_ID, inputs=inputs,
            )
        receipt = observe_active_war_cash_resource_v1(
            snapshot=snapshot(), war_id=WAR_ID, inputs=complete_inputs(),
        )
        forged = deepcopy(receipt)
        forged["joint_gold_reserve_raw"] = 0
        with self.assertRaisesRegex(ValueError, "does not balance"):
            require_complete_war_cash_resource_v1(
                forged, frame=FRAME, war_id=WAR_ID,
            )

    def test_receipt_rechecks_each_amount_frame_war_and_source(self) -> None:
        receipt = observe_active_war_cash_resource_v1(
            snapshot=snapshot(), war_id=WAR_ID, inputs=complete_inputs(),
        )
        for name, value in (
            ("source_frame", {**FRAME, "revision": 5}),
            ("war_id", WAR_ID + 1),
            ("source", "changed-source"),
            ("raw", 6_000_001),
        ):
            forged = deepcopy(receipt)
            forged["amount_observations"]["future_war_cost_upper_raw"][name] = value
            with self.subTest(name=name), self.assertRaisesRegex(
                ValueError, "lost same-frame provenance",
            ):
                require_complete_war_cash_resource_v1(
                    forged, frame=FRAME, war_id=WAR_ID,
                )

    def test_future_amount_without_horizon_is_not_a_bound(self) -> None:
        inputs = complete_inputs()
        inputs.pop("horizon_days")
        receipt = observe_active_war_cash_resource_v1(
            snapshot=snapshot(), war_id=WAR_ID, inputs=inputs,
        )
        self.assertEqual(receipt["status"], "incomplete")
        self.assertIsNone(receipt["war_future_gold_cost_raw"])
        self.assertIsNone(receipt["joint_gold_reserve_raw"])
        self.assertEqual(receipt["missing"]["horizon_days"],
                         "bounded_future_war_horizon_not_observed")


class MultiwarCashResourceTests(unittest.TestCase):
    def test_shared_actor_costs_count_once_and_immediate_fees_remain_alternatives(self):
        receipt = observe_aggregate_active_war_cash_resource_v1(
            snapshot=multiwar_snapshot(), receipts=multiwar_receipts(),
        )
        self.assertEqual(receipt["status"], "complete")
        self.assertEqual(receipt["existing_shared_gold_commitment_raw"], 4_000_000)
        self.assertEqual(receipt["war_future_gold_cost_raw"], 8_000_000)
        self.assertEqual(receipt["joint_gold_reserve_raw"], 11_000_000)
        self.assertEqual(receipt["immediate_war_action_costs_raw"], {
            str(WAR_ID): 1_000_000, str(SECOND_WAR_ID): 1_000_000,
        })
        self.assertEqual(receipt["existing_resource_claims"], {
            "army_ids": [71], "ally_character_ids": [41003],
            "character_ids": [29829],
            "commitment_keys": [f"active-war:{WAR_ID}", f"active-war:{SECOND_WAR_ID}"],
        })
        self.assertEqual(require_complete_aggregate_war_cash_resource_v1(
            receipt, frame=FRAME, war_ids=[SECOND_WAR_ID, WAR_ID],
        ), receipt)
        self.assertFalse(receipt["formal_action_ready"])

    def test_shared_army_cost_identity_also_counts_once(self):
        receipts = []
        for war_id in (WAR_ID, SECOND_WAR_ID):
            inputs = multiwar_inputs(war_id)
            component = inputs["future_war_cost_upper_raw"]["resource_components"][0]
            component["resource_kind"] = "army_maintenance"
            component["resource_id"] = "native-carmy:33554449"
            receipts.append(observe_active_war_cash_resource_v1(
                snapshot=multiwar_snapshot(), war_id=war_id, inputs=inputs,
            ))
        result = observe_aggregate_active_war_cash_resource_v1(
            snapshot=multiwar_snapshot(), receipts=receipts,
        )
        self.assertEqual(result["war_future_gold_cost_raw"], 8_000_000)

    def test_legacy_amounts_without_attribution_stay_unknown(self):
        receipts = []
        for war_id in (WAR_ID, SECOND_WAR_ID):
            inputs = multiwar_inputs(war_id)
            for name in AMOUNT_NAMES:
                inputs[name].pop("resource_components")
            receipts.append(observe_active_war_cash_resource_v1(
                snapshot=multiwar_snapshot(), war_id=war_id, inputs=inputs,
            ))
        result = observe_aggregate_active_war_cash_resource_v1(
            snapshot=multiwar_snapshot(), receipts=receipts,
        )
        self.assertEqual(result["status"], "incomplete")
        self.assertIsNone(result["existing_shared_gold_commitment_raw"])
        self.assertIsNone(result["joint_gold_reserve_raw"])
        self.assertIn(f"war:{WAR_ID}:pending_war_cash_raw:resources", result["missing"])

    def test_missing_receipt_does_not_cover_only_one_war(self):
        result = observe_aggregate_active_war_cash_resource_v1(
            snapshot=multiwar_snapshot(), receipts=multiwar_receipts()[:1],
        )
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["war_ids"], [WAR_ID, SECOND_WAR_ID])
        self.assertIn(f"war:{SECOND_WAR_ID}:receipt", result["missing"])
        self.assertIsNone(result["existing_shared_gold_commitment_raw"])
        self.assertIsNone(result["existing_resource_claims"])

    def test_duplicate_inactive_stale_or_treasury_mismatched_receipts_rejected(self):
        receipts = multiwar_receipts()
        for rows in ([receipts[0], receipts[0]],
                     [{**receipts[0], "war_id": SECOND_WAR_ID + 1}],
                     [{**receipts[0], "source_frame": {**FRAME, "revision": 99}}],
                     [{**receipts[0], "observed_treasury_raw": 0}]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                observe_aggregate_active_war_cash_resource_v1(
                    snapshot=multiwar_snapshot(), receipts=rows,
                )

    def test_conflicting_shared_resource_amount_rejected(self):
        inputs = multiwar_inputs(SECOND_WAR_ID)
        inputs["future_war_cost_upper_raw"]["raw"] += 1
        inputs["future_war_cost_upper_raw"]["resource_components"][0]["raw"] += 1
        changed = observe_active_war_cash_resource_v1(
            snapshot=multiwar_snapshot(), war_id=SECOND_WAR_ID, inputs=inputs,
        )
        with self.assertRaisesRegex(ValueError, "observations disagree"):
            observe_aggregate_active_war_cash_resource_v1(
                snapshot=multiwar_snapshot(), receipts=[multiwar_receipts()[0], changed],
            )

    def test_missing_declared_resource_membership_is_incomplete(self):
        inputs = multiwar_inputs(SECOND_WAR_ID)
        inputs["future_war_cost_upper_raw"]["resource_components"][0].update(
            resource_id="independent-second-war-cost", war_ids=[SECOND_WAR_ID])
        changed = observe_active_war_cash_resource_v1(
            snapshot=multiwar_snapshot(), war_id=SECOND_WAR_ID, inputs=inputs,
        )
        result = observe_aggregate_active_war_cash_resource_v1(
            snapshot=multiwar_snapshot(), receipts=[multiwar_receipts()[0], changed],
        )
        self.assertEqual(result["status"], "incomplete")
        self.assertIsNone(result["war_future_gold_cost_raw"])
        self.assertIn("cost_resource_missing_from_declared_war_receipt",
                      result["missing"].values())

    def test_horizon_mismatch_or_missing_occupation_stays_incomplete(self):
        for update in ({"horizon_days": 14}, {"resource_claims": None}):
            inputs = multiwar_inputs(SECOND_WAR_ID)
            inputs.update(update)
            changed = observe_active_war_cash_resource_v1(
                snapshot=multiwar_snapshot(), war_id=SECOND_WAR_ID, inputs=inputs,
            )
            result = observe_aggregate_active_war_cash_resource_v1(
                snapshot=multiwar_snapshot(), receipts=[multiwar_receipts()[0], changed],
            )
            self.assertEqual(result["status"], "incomplete")
            self.assertFalse(result["formal_action_ready"])
            if "horizon_days" in update:
                self.assertIsNone(result["joint_gold_reserve_raw"])
            else:
                self.assertIsNone(result["existing_resource_claims"])

    def test_explicit_sourced_zero_is_complete(self):
        receipts = []
        for war_id in (WAR_ID, SECOND_WAR_ID):
            inputs = multiwar_inputs(war_id)
            for name in AMOUNT_NAMES:
                inputs[name].update(raw=0, resource_components=[])
            receipts.append(observe_active_war_cash_resource_v1(
                snapshot=multiwar_snapshot(), war_id=war_id, inputs=inputs,
            ))
        result = observe_aggregate_active_war_cash_resource_v1(
            snapshot=multiwar_snapshot(), receipts=receipts,
        )
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["joint_gold_reserve_raw"], 0)

    def test_component_total_and_active_war_attribution_are_checked(self):
        for update in ({"raw": 0}, {"war_ids": [SECOND_WAR_ID]},
                       {"war_ids": [WAR_ID, SECOND_WAR_ID + 1]}):
            inputs = multiwar_inputs(WAR_ID)
            inputs["future_war_cost_upper_raw"]["resource_components"][0].update(update)
            with self.subTest(update=update), self.assertRaises(ValueError):
                observe_active_war_cash_resource_v1(
                    snapshot=multiwar_snapshot(), war_id=WAR_ID, inputs=inputs,
                )

    def test_current_rate_or_net_income_does_not_supply_future_bound(self):
        inputs = {"source_frame": FRAME, "war_id": WAR_ID,
                  "player_monthly_net_income_raw": 5_000_000,
                  "native_maintenance_resource_slots": [2_000_000] * 10}
        receipt = observe_active_war_cash_resource_v1(
            snapshot=multiwar_snapshot(), war_id=WAR_ID, inputs=inputs,
        )
        result = observe_aggregate_active_war_cash_resource_v1(
            snapshot=multiwar_snapshot(), receipts=[receipt],
        )
        self.assertIsNone(result["war_future_gold_cost_raw"])
        self.assertIsNone(result["joint_gold_reserve_raw"])
        self.assertEqual(result["status"], "incomplete")


if __name__ == "__main__":
    unittest.main()
