"""Actual V2 required-step regression through production plan_turn."""

import copy
import json
from pathlib import Path
from unittest import TestCase, mock

from xar_autoplayer.bridge.combat_contract import QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY
from xar_autoplayer.bridge.combat_phase_contract import QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY
from xar_autoplayer.bridge.driver import CallbackGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService


FIXTURE = Path(__file__).parents[1] / "fixtures/combat/live_840_12003_v2_required_step.json"


class GeneralBattleV2OuterActual840Test(TestCase):
    def test_actual_required_step_routes_with_existing_parser_and_capability(self):
        saved = json.loads(FIXTURE.read_text(encoding="utf-8"))
        step = saved["actual_plan"]["required_step"]
        self.assertIsNone(saved["actual_plan"]["selected_step"])
        execute = mock.Mock(side_effect=AssertionError("planning must not execute"))
        driver = CallbackGameplayDriver(
            backend_id="native-headless", snapshot=lambda: {},
            execute=execute, action_steps=("life-advance",),
        )
        service = GameplayBridgeService(driver)
        snapshot = {
            "snapshot_id": saved["snapshot_id"], "revision": saved["revision"],
            "date_raw": saved["date_raw"], "paused": True, "history": [],
        }
        # Recreate the inner chosen literal preserved by the actual outer RED.
        inner = copy.deepcopy(saved["actual_plan"])
        inner.pop("required_step")
        inner["selected_step"] = step
        inner["reason"] = "obtain same-frame per-regiment inputs for this encounter"

        def call(selected, capabilities):
            candidate = {**inner, "selected_step": selected}
            advertised = {
                "format_version": 1, "backend_id": "native-headless",
                "action_steps": ["life-advance"], "bridge_capabilities": capabilities,
            }
            with (
                mock.patch.object(service, "snapshot", return_value=snapshot),
                mock.patch.object(service, "capabilities", return_value=advertised),
                mock.patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=candidate),
            ):
                return service.plan_turn()

        routed = call(step, [QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY])
        self.assertEqual(routed["snapshot_id"], "native:33")
        self.assertEqual(routed["revision"], 2)
        self.assertEqual(routed["plan"]["selected_step"], step)
        self.assertNotIn("required_step", routed["plan"])
        self.assertEqual(routed["plan"]["encounter"], saved["actual_plan"]["encounter"])

        absent = call(step, [])
        self.assertIsNone(absent["plan"]["selected_step"])
        self.assertEqual(absent["plan"]["required_step"], step)
        self.assertEqual(absent["plan"]["reason"], saved["actual_plan"]["reason"])
        malformed = step.replace("-a-1-", "-a-2-")
        invalid = call(malformed, [QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY])
        self.assertIsNone(invalid["plan"]["selected_step"])
        self.assertEqual(invalid["plan"]["required_step"], malformed)

        v3 = step.replace("-v2-", "-v3-")
        self.assertEqual(call(v3, [QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY])["plan"]["selected_step"], v3)
        self.assertIsNone(call(v3, [QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY])["plan"]["selected_step"])
        execute.assert_not_called()
        self.actual_routed_plan = routed
