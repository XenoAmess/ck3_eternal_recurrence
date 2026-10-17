"""Production primitive projection must remain consumable and preserve its origin."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from xar_autoplayer.bridge import military_reinforcement_12004 as action
from xar_autoplayer.bridge import military_reinforcement_12004_contract as contract
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.frontend_gui_route_contract import QUERY_FRONTEND_GUI_ROUTE_V1_CAPABILITY
from test_military_reinforcement_12004 import ack, census, snapshot


class Endpoint:
    def __init__(self):
        self.sent = []

    def start(self, on_frame, on_disconnect):
        self.on_frame, self.on_disconnect = on_frame, on_disconnect

    def send(self, request):
        self.sent.append(copy.deepcopy(request))


class State:
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.census_count = 0

    def capabilities(self):
        capabilities = ["game.command." + s for s in contract.STEPS]
        capabilities += ["game.command.inspect-gui-window-tree-v1", QUERY_FRONTEND_GUI_ROUTE_V1_CAPABILITY]
        hello = copy.deepcopy(snapshot()["diagnostics"]["hello"])
        hello.update(connection_generation=1, game_adapter_status="ready", capabilities=capabilities)
        hello["expected_ck3_sha256"] = hello["expected_ck3_sha256"].upper()
        return dict(backend_id="native-headless", mode="native-headless", source="injected-dll-named-pipe",
            visual_fallback=False, snapshot=False, wait_for_change=False, action_steps=list(contract.STEPS),
            bridge_capabilities=capabilities, diagnostics=dict(hello=hello, bridge_pid=29000,
                connection_generation=1, connected=True))

    def wait_for_command_result(self, request_id, timeout):
        request = self.endpoint.sent[-1]
        if request["step"] == "inspect-gui-window-tree-v1":
            self.census_count += 1
            result = census(1 if self.census_count == 1 else 0)
            result["refill_receiver_frame_12004"]["ticket_sequence"] += self.census_count
        else:
            result = ack(1, False)
        return dict(type="command_result", request_id=request_id, ok=True, result=result)


class MilitaryReinforcementTransportTests(unittest.TestCase):
    def test_real_primitive_projects_backend_and_native_revision_before_independent_verification(self):
        with tempfile.TemporaryDirectory() as temporary:
            endpoint = Endpoint()
            driver = NativeHeadlessGameplayDriver(endpoint=endpoint, state_dir=temporary)
            driver.state = State(endpoint)
            # Only native I/O and its semantic snapshot are substituted. The
            # action, actual primitive, GUI census consumer, and normalizer run.
            with patch.object(driver, "take_snapshot", side_effect=snapshot):
                result = action.set_fixed_military_reinforcement_12004(
                    driver, desired_enabled=False, expected_revision=110)
            self.assertEqual(len(endpoint.sent), 3)
            request = endpoint.sent[1]
            self.assertEqual(request["step"], contract.DISABLE_STEP)
            self.assertEqual(request["expected_revision"], 109)
            self.assertEqual(result["queried_revision"], 110)
            self.assertEqual(driver.state.census_count, 2)
            self.assertTrue(result["postcondition_verified"])
            self.assertFalse(result["verification_pending"])
            native_ack = result["native_ack"]
            self.assertEqual(native_ack["backend_id"], "native-headless")
            self.assertFalse(native_ack["postcondition_verified"])
            self.assertTrue(native_ack["verification_pending"])
            self.assertEqual(native_ack["status"], "acknowledged_verification_pending")
            self.assertEqual(result["later_observation"]["switch"]["raw_byte_4a9"], 0)
            raw_path = Path(result["action_claim_path"]).with_suffix(".result.json")
            self.assertEqual(json.loads(raw_path.read_text(encoding="utf-8"))["raw"], native_ack)
            binding = contract.reinforcement_binding(snapshot())
            before = result["before_observation"]
            self.assertFalse(contract.normalize_reinforcement_ack(native_ack, binding, False, before)["postcondition_verified"])
            wire = {key: value for key, value in native_ack.items() if key != "backend_id"}
            self.assertEqual(contract.normalize_reinforcement_ack(wire, binding, False, before), wire)
            for bad in ("other-backend", None, True):
                with self.subTest(backend_id=bad), self.assertRaises(ValueError):
                    contract.normalize_reinforcement_ack({**native_ack, "backend_id": bad}, binding, False, before)
            self.actual_evidence = {"sent_step": request["step"], "sent_expected_revision": request["expected_revision"],
                "public_revision": result["queried_revision"], "native_ack_backend_id": native_ack["backend_id"],
                "native_ack_postcondition_verified": native_ack["postcondition_verified"],
                "native_ack_verification_pending": native_ack["verification_pending"],
                "final_postcondition_verified": result["postcondition_verified"],
                "before_raw_byte_4a9": before["switch"]["raw_byte_4a9"],
                "later_raw_byte_4a9": result["later_observation"]["switch"]["raw_byte_4a9"],
                "raw_receipt_preserves_actual_transport_projection": True, "requests": endpoint.sent}


if __name__ == "__main__":
    unittest.main()
