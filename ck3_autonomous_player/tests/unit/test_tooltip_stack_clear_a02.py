"""Global tooltip clear: actual contracts/Driver/Service/MCP, synthetic native I/O."""
import copy
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from test_faith_power_presentation_ui_v6 import Driver, raw, normalize, RECEIPT
from xar_autoplayer.bridge.religion_presentation_ui_contract import request_fields
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver


class WireDriver(Driver):
    # Exercise the original revision translator and original parsed-return writer.
    # Only the native send/result boundary and current snapshot are synthetic.
    _execute_primitive_step = NativeHeadlessGameplayDriver._execute_primitive_step

    def __init__(self, response, storage):
        super().__init__(response)
        self.storage = Path(storage)
        self._request_sequence = 0
        self.command_timeout_seconds = 1
        self.endpoint = SimpleNamespace(send=lambda request: self.calls.append(copy.deepcopy(request)))
        self.state = SimpleNamespace(wait_for_command_result=lambda request_id, timeout:
            {"ok": True, "result": self.response(self.calls[-1])})

    def _native_driver_state_path(self):
        return self.storage / "driver.json"


def packet(phase="observed"):
    operation = "close_tooltips" if phase == "pending" else "query"
    value = raw("tooltips", operation, 0, receipt=RECEIPT)
    value.update(subject_id_available=False, current_subject_id=None,
                 effective_visible=phase != "cleared", verification_pending=phase == "pending")
    value["tree"].update(root_available=False, widget_count=0, widgets=[])
    leaf = value["presentation_ui"]
    leaf.update(subject_id=None, target_kind=None, target_index=None, source_bound=False,
                post_window_visible=None, action_owner_epoch=None if phase == "observed" else 12,
                observation_owner_epoch=None if phase == "pending" else 14)
    leaf["tooltip_clear"] = {"available": True, "cleared": phase == "cleared", "phase": phase,
        "active_count": None if phase == "pending" else 0 if phase == "cleared" else 1,
        "deferred": None if phase == "pending" else False,
        "locked": [True] if phase == "observed" else [],
        "source_null": [False] if phase == "observed" else []}
    return value


class TooltipStackClearContracts(unittest.TestCase):
    def test_finite_manager_request_and_locked_source_observation(self):
        self.assertEqual(request_fields("query", "tooltips", 0), {})
        self.assertEqual(request_fields("close_tooltips", "tooltips", 0, presentation_receipt=RECEIPT),
                         {"presentation_receipt": RECEIPT})
        for operation, subject, fields in [("close_tooltips", 0, {}), ("query", 1, {}),
                ("query", 0, {"presentation_tab": ""}), ("query", 0, {"presentation_index": 0}),
                ("query", 0, {"presentation_target": "faith_core_tenet"})]:
            with self.subTest(operation=operation, fields=fields), self.assertRaises(ValueError):
                request_fields(operation, "tooltips", subject, **fields)
        result = normalize(packet(), kind="tooltips", subject=0)
        self.assertEqual(result["presentation_ui"]["tooltip_clear"]["locked"], [True])
        self.assertFalse(result["presentation_ui"]["source_bound"])

    def test_ack_is_not_clear_and_postquery_is_independent(self):
        normalize(packet("pending"), operation="close_tooltips", kind="tooltips", subject=0,
                  presentation_receipt=RECEIPT)
        normalize(packet("cleared"), kind="tooltips", subject=0, presentation_receipt=RECEIPT)
        for phase, key, bad in [("pending", "cleared", True), ("cleared", "active_count", 1),
                                ("cleared", "deferred", True)]:
            value = packet(phase); value["presentation_ui"]["tooltip_clear"][key] = bad
            with self.subTest(phase=phase, key=key), self.assertRaises(ValueError):
                normalize(value, operation="close_tooltips" if phase == "pending" else "query",
                          kind="tooltips", subject=0, presentation_receipt=RECEIPT)
        value = packet("cleared"); value["presentation_ui"]["observation_owner_epoch"] = 12
        with self.assertRaises(ValueError):
            normalize(value, kind="tooltips", subject=0, presentation_receipt=RECEIPT)
        value = packet(); value["presentation_ui"]["source_bound"] = True
        with self.assertRaises(ValueError): normalize(value, kind="tooltips", subject=0)


class TooltipStackClearMcp(unittest.IsolatedAsyncioTestCase):
    async def test_existing_registered_umbrella_query_action_later_query_wire(self):
        from mcp import Client
        from xar_autoplayer.bridge.mcp_server import create_server
        sequence = ["observed", "pending", "cleared"]
        temporary = tempfile.TemporaryDirectory(prefix="tooltip-clear-wire-")
        self.addCleanup(temporary.cleanup)
        driver = WireDriver(lambda fields: packet(sequence.pop(0)), temporary.name)
        common = {"window_kind": "tooltips", "subject_id": 0, "expected_revision": 4}
        steps = [("ck3_query_faith_power_ui_v1", common),
                 ("ck3_present_faith_power_ui_v1", {**common, "operation": "close_tooltips", "presentation_receipt": RECEIPT}),
                 ("ck3_query_faith_power_ui_v1", {**common, "presentation_receipt": RECEIPT})]
        async with Client(create_server(driver)) as client:
            for tool, args in steps:
                result = await client.call_tool(tool, args)
                self.assertFalse(result.is_error, result)
        self.assertEqual([row["expected_revision"] for row in driver.calls], [3,3,3])
        self.assertEqual([row["window_kind"] for row in driver.calls], ["tooltips"]*3)
        self.assertEqual([row.get("operation") for row in driver.calls], [None,"close_tooltips",None])
        self.assertEqual(len(list((Path(temporary.name)/"ingame-ui-native-results").glob("*.json"))), 3)


if __name__ == "__main__": unittest.main()
