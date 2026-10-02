"""Offline checks of the same-owner service; these never launch CK3."""
import asyncio
import json
from pathlib import Path
import tempfile
import threading
import unittest

from capture_session import private_phase_trace_call, service_requests


class PrivatePhaseTraceContractTests(unittest.TestCase):
    def setUp(self):
        self.calls = []

        class Driver:
            def __init__(inner, calls):
                inner.calls = calls

            def _execute_primitive_step(inner, step, **kwargs):
                inner.calls.append((step, kwargs))
                return {"status": "forwarded"}

        self.driver = Driver(self.calls)
        self.begin = {
            "action": "private_phase_trace",
            "step": "experimental-combat-phase-event-trace-begin-v1",
            "expected_revision": 7,
            "combat_id": 16777218,
            "managed_daily_sequence_token": 66005,
            "checkpoint_sequence": 9,
        }

    def test_optional_weight_capture_bool_is_forwarded_only_on_begin(self):
        for value in (True, False):
            with self.subTest(value=value):
                request = {**self.begin,
                           "capture_runtime_random_list_weights": value}
                self.assertEqual(private_phase_trace_call(
                    request, enabled=True, driver=self.driver),
                    {"status": "forwarded"})
                self.assertIs(self.calls[-1][1]["request_fields"]["capture_runtime_random_list_weights"], value)
        self.assertEqual(self.calls[-1][1]["required_capability"],
                          "game.command.experimental-combat-phase-event-trace-managed-v1")

    def test_passive_monitor_closed_fields_independent_token_and_same_budget(self):
        begin = {"action": "private_phase_trace",
                 "step": "experimental-scoped-character-variable-monitor-begin-v1",
                 "expected_revision": 7, "monitor_sequence_token": 8866007,
                 "scoped_character_id": 33437, "scoped_related_character_id": 34120}
        finish = {k: v for k, v in begin.items() if not k.startswith("scoped_")}
        finish["step"] = "experimental-scoped-character-variable-monitor-finish-v1"
        for request in (begin, finish):
            private_phase_trace_call(request, enabled=True, driver=self.driver)
            self.assertEqual(self.calls[-1][1]["timeout_seconds"], 90)
            self.assertEqual(self.calls[-1][1]["request_fields"],
                             {k: v for k, v in request.items()
                              if k not in {"action", "step", "expected_revision"}})
        prior = len(self.calls)
        invalid = [{**begin, key: value} for key in ("expected_revision", "monitor_sequence_token")
                   for value in (True, 0, -1, 2**64, "7", None)]
        invalid += [{**begin, key: value} for key in ("scoped_character_id", "scoped_related_character_id")
                    for value in (True, 0, -1, 2**31, "33437", None)]
        invalid += [{**begin, "scoped_related_character_id": 33437},
                    {k:v for k,v in begin.items() if k != "scoped_related_character_id"},
                    {**finish, "scoped_character_id": 33437}]
        invalid += [{**begin, name: 1} for name in
                    ("combat_id", "checkpoint_sequence", "managed_daily_sequence_token",
                     "capture_runtime_scoped_chain", "day_count", "retry")]
        for request in invalid:
            with self.subTest(request=request), self.assertRaises(RuntimeError):
                private_phase_trace_call(request, enabled=True, driver=self.driver)
        with self.assertRaises(RuntimeError):
            private_phase_trace_call(begin, enabled=False, driver=self.driver)
        self.assertEqual(len(self.calls), prior)

    def test_scoped_chain_closed_fields_and_native_budget(self):
        scoped = {**self.begin, "capture_runtime_scoped_chain": True,
                  "scoped_character_id": 33437, "scoped_related_character_id": 34120,
                  "scoped_event_load_index": 11}
        private_phase_trace_call(scoped, enabled=True, driver=self.driver)
        fields = self.calls[-1][1]["request_fields"]
        self.assertEqual({key: fields[key] for key in scoped if key.startswith("scoped_")},
                         {key: scoped[key] for key in scoped if key.startswith("scoped_")})
        self.assertIs(fields["capture_runtime_scoped_chain"], True)
        self.assertEqual(self.calls[-1][1]["timeout_seconds"], 90)
        private_phase_trace_call({**self.begin, "capture_runtime_scoped_chain": False},
                                 enabled=True, driver=self.driver)
        prior = len(self.calls)
        bad = [dict(scoped, scoped_character_id=value) for value in (True, 0, -1, 2**31, "33437", None)]
        bad += [dict(scoped, scoped_related_character_id=33437),
                dict(scoped, scoped_event_load_index=True),
                dict(scoped, scoped_event_load_index=13),
                dict(scoped, capture_runtime_scoped_chain=1),
                dict(scoped, capture_runtime_scoped_chain=False),
                {key: value for key, value in scoped.items() if key != "scoped_related_character_id"},
                {**self.begin, "scoped_character_id": 33437}]
        finish = {key: value for key, value in scoped.items() if key != "checkpoint_sequence"}
        finish["step"] = "experimental-combat-phase-event-trace-finish-v1"
        bad.append(finish)
        for request in bad:
            with self.subTest(request=request), self.assertRaises(RuntimeError):
                private_phase_trace_call(request, enabled=True, driver=self.driver)
        with self.assertRaises(RuntimeError):
            private_phase_trace_call(scoped, enabled=False, driver=self.driver)
        self.assertEqual(len(self.calls), prior)

    def test_absent_flag_preserves_previous_wire_shape(self):
        private_phase_trace_call(self.begin, enabled=True, driver=self.driver)
        self.assertNotIn("capture_runtime_random_list_weights",
                          self.calls[-1][1]["request_fields"])
        self.assertNotIn("capture_runtime_join_width",
                         self.calls[-1][1]["request_fields"])
        self.assertNotIn("capture_runtime_join_full_entries",
                         self.calls[-1][1]["request_fields"])
        self.assertNotIn("capture_runtime_counter_output",
                         self.calls[-1][1]["request_fields"])
        self.assertNotIn("capture_runtime_advantage_components",
                         self.calls[-1][1]["request_fields"])

    def test_advantage_component_opt_in_is_begin_only_bool_and_composes_with_counter(self):
        for value in (True, False):
            with self.subTest(value=value):
                request = {**self.begin,
                           "capture_runtime_counter_output": True,
                           "capture_runtime_advantage_components": value}
                private_phase_trace_call(request, enabled=True, driver=self.driver)
                fields = self.calls[-1][1]["request_fields"]
                self.assertIs(fields["capture_runtime_counter_output"], True)
                self.assertIs(fields["capture_runtime_advantage_components"], value)
        prior = len(self.calls)
        for value in (0, 1, "true", None, [], {}):
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                private_phase_trace_call(
                    {**self.begin, "capture_runtime_advantage_components": value},
                    enabled=True, driver=self.driver)
        finish = {key: value for key, value in self.begin.items()
                  if key != "checkpoint_sequence"}
        finish["step"] = "experimental-combat-phase-event-trace-finish-v1"
        finish["capture_runtime_advantage_components"] = True
        with self.assertRaises(RuntimeError):
            private_phase_trace_call(finish, enabled=True, driver=self.driver)
        self.assertEqual(len(self.calls), prior)

    def test_optional_counter_output_capture_is_bounded_to_begin(self):
        for value in (True, False):
            with self.subTest(value=value):
                request = {**self.begin, "capture_runtime_counter_output": value}
                private_phase_trace_call(request, enabled=True, driver=self.driver)
                self.assertIs(self.calls[-1][1]["request_fields"]
                              ["capture_runtime_counter_output"], value)
        prior = len(self.calls)
        for value in (0, 1, "true", None):
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                private_phase_trace_call(
                    {**self.begin, "capture_runtime_counter_output": value},
                    enabled=True, driver=self.driver)
        finish = {key: value for key, value in self.begin.items()
                  if key != "checkpoint_sequence"}
        finish["step"] = "experimental-combat-phase-event-trace-finish-v1"
        finish["capture_runtime_counter_output"] = True
        with self.assertRaises(RuntimeError):
            private_phase_trace_call(finish, enabled=True, driver=self.driver)
        self.assertEqual(len(self.calls), prior)

    def test_join_width_requires_bool_and_frozen_candidate(self):
        for value in (True, False):
            request = {**self.begin, "candidate_joining_army_id": 22,
                       "capture_runtime_join_width": value}
            private_phase_trace_call(request, enabled=True, driver=self.driver)
            self.assertIs(self.calls[-1][1]["request_fields"]
                          ["capture_runtime_join_width"], value)
        prior = len(self.calls)
        for request in ({**self.begin, "capture_runtime_join_width": True},
                        {**self.begin, "candidate_joining_army_id": 22,
                         "capture_runtime_join_width": 1}):
            with self.assertRaises(RuntimeError):
                private_phase_trace_call(request, enabled=True,
                                         driver=self.driver)
        self.assertEqual(len(self.calls), prior)

    def test_join_full_entries_requires_both_explicit_opt_ins(self):
        valid = {**self.begin, "candidate_joining_army_id": 22,
                 "capture_runtime_join_width": True,
                 "capture_runtime_join_full_entries": True}
        private_phase_trace_call(valid, enabled=True, driver=self.driver)
        self.assertIs(self.calls[-1][1]["request_fields"]
                      ["capture_runtime_join_full_entries"], True)
        prior = len(self.calls)
        invalid = (
            {**self.begin, "candidate_joining_army_id": 22,
             "capture_runtime_join_full_entries": True},
            {**valid, "capture_runtime_join_width": False},
            {**valid, "capture_runtime_join_full_entries": 1},
            {**valid, "candidate_joining_army_id": 0},
        )
        for request in invalid:
            with self.subTest(request=request), self.assertRaises(RuntimeError):
                private_phase_trace_call(request, enabled=True,
                                         driver=self.driver)
        self.assertEqual(len(self.calls), prior)

    def test_non_bool_and_finish_flag_are_rejected_before_driver_call(self):
        for value in (0, 1, "true", None):
            with self.subTest(value=value):
                with self.assertRaises(RuntimeError):
                    private_phase_trace_call(
                        {**self.begin, "capture_runtime_random_list_weights": value},
                        enabled=True, driver=self.driver)
        finish = {key: value for key, value in self.begin.items()
                  if key != "checkpoint_sequence"}
        finish["step"] = "experimental-combat-phase-event-trace-finish-v1"
        finish["capture_runtime_random_list_weights"] = True
        with self.assertRaises(RuntimeError):
            private_phase_trace_call(finish, enabled=True, driver=self.driver)
        self.assertEqual(self.calls, [])

    def test_opt_in_is_required(self):
        with self.assertRaises(RuntimeError):
            private_phase_trace_call(self.begin, enabled=False, driver=self.driver)
        self.assertEqual(self.calls, [])


class HotServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_failed_call_keeps_owner_available_and_never_retries_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            requests = Path(temp) / "requests"
            calls = []
            owner = object()
            owners = []

            async def call(name, arguments):
                calls.append((name, arguments))
                owners.append(owner)
                if name == "ck3_activate_frontend_start_1066_bookmark_character_v1":
                    raise RuntimeError("postcondition unavailable")
                return {"map_ready": True, "paused": True}

            async def producer():
                while not requests.exists():
                    await asyncio.sleep(0.01)
                rows = [
                    {"action": "mcp", "tool": "ck3_activate_frontend_start_1066_bookmark_character_v1"},
                    {"action": "mcp", "tool": "ck3_take_snapshot"},
                    {"action": "finish"},
                ]
                for i, row in enumerate(rows):
                    path = requests / f"{i:03}.pending"
                    path.write_text(json.dumps(row), encoding="utf-8")
                    path.rename(path.with_suffix(".json"))

            await asyncio.gather(
                service_requests(requests, call=call, stopped=threading.Event(), seconds=3,
                                 state_reader=lambda: {"bridge_pid": 123}), producer())
            self.assertEqual(len(calls), 2)
            self.assertTrue(all(item is owner for item in owners))
            responses = Path(temp) / "requests-responses"
            self.assertEqual(json.loads((responses / "000.json").read_text())["result"], "RED")
            self.assertEqual(json.loads((responses / "001.json").read_text())["body"]["map_ready"], True)
            self.assertEqual(json.loads((responses / "002.json").read_text())["result"], "SERVICE_FINISHED")
            self.assertEqual(len(list(requests.glob("*.json"))), 3)

    async def test_stopped_owner_does_not_execute_requests(self):
        with tempfile.TemporaryDirectory() as temp:
            stopped = threading.Event()
            stopped.set()

            async def call(*args):
                self.fail("Stopped service must not call MCP")

            await service_requests(Path(temp) / "requests", call=call, stopped=stopped,
                                   seconds=1, state_reader=lambda: {})
            ended = json.loads((Path(temp) / "requests-responses/service-ended.json").read_text())
            self.assertEqual(ended["reason"], "owner_stopped")

    async def test_gui_scale_recheck_after_native_ui_save_is_disk_only(self):
        with tempfile.TemporaryDirectory() as temp:
            requests = Path(temp) / "requests"
            values = iter(({"disk_gate_passed": False, "observed_scale": "1.3",
                            "recording_authorized_by_this_gate": False},
                           {"disk_gate_passed": True, "observed_scale": "1.0",
                            "recording_authorized_by_this_gate": False}))

            async def no_mcp(*args):
                self.fail("GUI disk readback must not call MCP")

            async def producer():
                while not requests.exists():
                    await asyncio.sleep(0.01)
                for index, row in enumerate(({"action": "gui_scale_disk_readback"},
                                             {"action": "gui_scale_disk_readback"},
                                             {"action": "finish"})):
                    pending = requests / f"{index:03}.pending"
                    pending.write_text(json.dumps(row), encoding="utf-8")
                    pending.rename(pending.with_suffix(".json"))

            await asyncio.gather(
                service_requests(requests, call=no_mcp, stopped=threading.Event(),
                                 seconds=3, state_reader=lambda: {},
                                 gui_scale_readback=lambda: next(values)), producer())
            responses = Path(temp) / "requests-responses"
            self.assertEqual(json.loads((responses / "000.json").read_text())["result"], "RED")
            second = json.loads((responses / "001.json").read_text())
            self.assertEqual(second["result"], "DISK_MATCH_REQUIRES_VISUAL_REVIEW")
            self.assertFalse(second["body"]["recording_authorized_by_this_gate"])



if __name__ == "__main__":
    unittest.main()
