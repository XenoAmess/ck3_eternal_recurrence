from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.war_cash_no_selected_action_v1 import (
    observe_no_selected_war_action_fee_v1,
)


FRAME = {
    "played_character_id": 29829, "native_revision": 3,
    "date_raw": 53219496, "snapshot_id": "native:3", "revision": 4,
    "episode_run_id": "native-29829-2bc2d599f7f9",
}
WAR_ID = 16777231


def snapshot() -> dict[str, object]:
    return {
        **FRAME, "paused": True, "map_ready": True,
        "played_character": {"character_id": 29829},
        "active_wars": [{"war_id": WAR_ID}],
    }


def planned() -> dict[str, object]:
    return {
        "snapshot_id": FRAME["snapshot_id"], "revision": FRAME["revision"],
        "plan": {
            "policy": "one-life-turn-v1", "selected_step": None,
            "construction_wartime_observation": {"source_frame": {
                "snapshot_id": FRAME["snapshot_id"],
                "revision": FRAME["revision"],
                "native_revision": FRAME["native_revision"],
                "date_raw": FRAME["date_raw"],
                "episode_run_id": FRAME["episode_run_id"],
                "actor_character_id": FRAME["played_character_id"],
            }},
        },
    }


class NoSelectedWarActionFeeTests(unittest.TestCase):
    def test_explicit_empty_step_proves_only_immediate_zero(self) -> None:
        seen = observe_no_selected_war_action_fee_v1(
            snapshot=snapshot(), planned=planned(), war_id=WAR_ID,
        )
        amount = seen["immediate_war_action_cost_raw"]
        self.assertEqual(amount["raw"], 0)
        self.assertEqual(amount["source_frame"], FRAME)
        self.assertEqual(amount["war_id"], WAR_ID)
        self.assertIsNone(seen["pending_war_cash_raw"])
        self.assertIsNone(seen["future_war_cost_upper_raw"])
        self.assertFalse(seen["formal_cash_receipt_eligible"])

    def test_missing_or_selected_step_cannot_be_priced_zero(self) -> None:
        for step in ("query-war-termination-options-16777231", "move-army-71-to-22"):
            candidate = planned()
            candidate["plan"]["selected_step"] = step
            with self.subTest(step=step), self.assertRaisesRegex(ValueError, "selected war step"):
                observe_no_selected_war_action_fee_v1(
                    snapshot=snapshot(), planned=candidate, war_id=WAR_ID,
                )
        candidate = planned()
        candidate["plan"].pop("selected_step")
        with self.assertRaisesRegex(ValueError, "selected war step"):
            observe_no_selected_war_action_fee_v1(
                snapshot=snapshot(), planned=candidate, war_id=WAR_ID,
            )

    def test_stale_or_foreign_frame_fails(self) -> None:
        for key, other in (("snapshot_id", "native:4"), ("revision", 5)):
            candidate = planned()
            candidate[key] = other
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "crossed"):
                observe_no_selected_war_action_fee_v1(
                    snapshot=snapshot(), planned=candidate, war_id=WAR_ID,
                )
        candidate = planned()
        candidate["plan"]["construction_wartime_observation"][
            "source_frame"]["native_revision"] += 1
        with self.assertRaisesRegex(ValueError, "full same-frame"):
            observe_no_selected_war_action_fee_v1(
                snapshot=snapshot(), planned=candidate, war_id=WAR_ID,
            )

    def test_unpaused_or_other_war_fails(self) -> None:
        candidate = snapshot()
        candidate["paused"] = False
        with self.assertRaisesRegex(ValueError, "paused"):
            observe_no_selected_war_action_fee_v1(
                snapshot=candidate, planned=planned(), war_id=WAR_ID,
            )
        candidate = snapshot()
        candidate["active_wars"].append({"war_id": 42})
        with self.assertRaisesRegex(ValueError, "one matching"):
            observe_no_selected_war_action_fee_v1(
                snapshot=candidate, planned=planned(), war_id=WAR_ID,
            )


if __name__ == "__main__":
    unittest.main()
