"""Marriage action changes must not inherit another action's war display."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
sys.path.insert(0, str(ROOT / "tools" / "g2_saved_campaign"))

from xar_autoplayer import family_marriage_formal_consumer as consumer
from xar_autoplayer.bridge.observed_heir_marriage_private_action_v1 import RESULT_STEP
import decision_display_contract_v1 as display
from decision_text_view import AudienceState

OLD_STEP = "query-war-termination-options-134217814"
OLD_PHASE = "native_war_termination_query"
STALE: dict[str, object] = {
    "phase": OLD_PHASE, "selected_step": OLD_STEP,
    "reason": "Old war-only presentation must stay with its own action.",
}


def war_plan(presentation: object) -> dict[str, object]:
    return {
        "policy": "one-life-turn-v1", "phase": OLD_PHASE,
        "selected_step": OLD_STEP, "reason": "Read current native war terms.",
        "war_decision_presentation_v1": presentation,
        "war_id": 134217814, "active_wars": [{"war_id": 134217814}],
        "war_spending_priority_v1": {"read_only": True},
    }


def recheck(presentation: object) -> tuple[dict[str, object], dict[str, object]]:
    original = war_plan(presentation)
    planned: dict[str, object] = {"plan": original, "snapshot_id": "native:1"}
    resolved: dict[str, object] = {
        "post_bridge_pid": 11, "post_bridge_creation_date": "old-birth",
        "status": "marriage", "source_pending": {
            "heir_character_id": 202, "candidate_character_id": 303,
            "recipient_character_id": 404,
        },
    }
    with patch.object(consumer, "bridge_process_identity", return_value=(22, "new-birth")):
        actual: dict[str, object] = consumer._plan_existing_resolution(
            object(), planned, original, resolved, {})
    result: dict[str, object] = display.record(actual["plan"])
    return result, original


class MarriageDisplayBindingTests(unittest.TestCase):
    def test_cold_recheck_roundtrips_actual_producer_to_formatter_and_view(self) -> None:
        for previous_detail in (STALE, None, "malformed optional detail"):
            with self.subTest(previous_detail=previous_detail):
                before = copy.deepcopy(war_plan(previous_detail))
                plan, original = recheck(previous_detail)
                self.assertEqual(original, before)
                self.assertNotIn("war_decision_presentation_v1", plan)
                self.assertEqual(plan["selected_step"], RESULT_STEP)
                self.assertEqual(plan["phase"], "first_heir_marriage_cold_material_recheck")
                for name in ("war_id", "active_wars", "war_spending_priority_v1"):
                    self.assertEqual(plan[name], before[name])
                self.assertEqual(plan["family_marriage_cold_recovery"], True)
                self.assertEqual(display.record(plan["family_marriage_pending"])["candidate_character_id"], 303)

                compact: dict[str, object] = display.project_plan(plan)
                self.assertNotIn("decision_display_unavailable_v1", compact)
                wire: dict[str, object] = display.record(json.loads(json.dumps(compact)))
                card = display.parse_card(wire[display.DETAIL], step=RESULT_STEP, phase=plan["phase"])
                self.assertEqual(card.selected_step, RESULT_STEP)
                self.assertEqual(card.domain, "observation")
                view = AudienceState()
                view.consume({
                    "source_namespace": "p37-responses",
                    "request": {"tool": "root_before_auto_turn_submit", "parent_sequence": 10559},
                    "result": {"is_error": False, "structured_content": {
                        "status": "planned", "selected_step": RESULT_STEP, "plan": wire}},
                })
                self.assertIsNotNone(view.card)
                self.assertNotIn("Old war-only", view.render())
                projected: dict[str, object] = display.project_result({
                    "request": {"sequence": 10559, "tool": "ck3_auto_turn"}},
                    {"status": "executed", "selected_step": RESULT_STEP, "plan": wire,
                     "result": {"status": "available", "step": RESULT_STEP, "accepted": True}})
                view.consume(display.record(json.loads(json.dumps(projected))))
                self.assertIsNotNone(view.card)
                self.assertEqual(view.card.selected_step if view.card else None, RESULT_STEP)
                self.assertNotIn("Old war-only", view.render())

    def test_same_bridge_resolution_preserves_current_war_action_binding(self) -> None:
        plan = war_plan(copy.deepcopy(STALE))
        original = copy.deepcopy(plan)
        resolved: dict[str, object] = {
            "post_bridge_pid": 22, "post_bridge_creation_date": "same-birth",
            "status": "marriage", "source_pending": {},
        }
        with patch.object(consumer, "bridge_process_identity", return_value=(22, "same-birth")):
            result: dict[str, object] = consumer._plan_existing_resolution(
                object(), {"plan": plan}, plan, resolved, {})
        selected: dict[str, object] = display.record(result["plan"])
        self.assertEqual(plan, original)
        self.assertEqual(selected["selected_step"], OLD_STEP)
        self.assertEqual(selected["phase"], OLD_PHASE)
        self.assertEqual(selected["war_decision_presentation_v1"], STALE)
        self.assertNotIn("decision_display_unavailable_v1", display.project_plan(selected))

    def test_formatter_still_rejects_stale_or_mismatched_identity(self) -> None:
        unmigrated = war_plan(copy.deepcopy(STALE))
        unmigrated.update(selected_step=RESULT_STEP, phase="first_heir_marriage_cold_material_recheck")
        invalid: dict[str, object] = display.project_plan(unmigrated)
        self.assertIsNone(invalid[display.DETAIL])
        unavailable: dict[str, object] = display.record(invalid["decision_display_unavailable_v1"])
        self.assertEqual(unavailable["status"], "detail_unavailable")

        fixed, _ = recheck(copy.deepcopy(STALE))
        card = display.project_card(fixed).wire()
        with self.assertRaises(ValueError):
            display.parse_card(json.loads(json.dumps(card)), step=OLD_STEP, phase=OLD_PHASE)


if __name__ == "__main__":
    unittest.main()
