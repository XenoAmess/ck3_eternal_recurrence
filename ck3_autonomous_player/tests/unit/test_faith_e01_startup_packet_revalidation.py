from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from test_frontend_fixture_scenario_host import current_frame, event_packet, load_harness, policy, submission


def consumer():
    source = Path(__file__).resolve().parents[2] / "native_bridge/research/revalidate_faith_e01_startup_packets.py"
    spec = importlib.util.spec_from_file_location("startup_packet_revalidation_test", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def packet_report(host):
    before, _ = current_frame(8, startup=True)
    current, _ = current_frame(9, startup=True)
    after, root = current_frame(10, startup=True)
    rows = []
    for row_id, tool, result in (
            ("before1", "ck3_take_snapshot", before), ("before2", "ck3_take_snapshot", current),
            ("event", "ck3_query_current_event_window_context_v1", event_packet(current)),
            ("after", "ck3_take_snapshot", after), ("root", "ck3_query_campaign_root_context_v1", root)):
        rows.append({"id": row_id, "ok": True, "plan": {"tool": tool}, "result": result})
    return {"error": "RuntimeError: preserved original startup RED", "steps": rows,
        "frontend_fixture_start_submission": {"result": submission(host)},
        "frontend_fixture_start_policy_input": {"policy": policy()}}


async def check(module, host, report):
    return await module.revalidate(host, report, previous_row="before1", current_row="before2",
        event_row="event", after_row="after", root_row="root", expected_pid=71, expected_generation=2)


class StartupPacketRevalidationTests(unittest.IsolatedAsyncioTestCase):
    async def test_reuses_strict_observer_without_clearing_original_error_or_dispatching_game_calls(self):
        host, module = load_harness(), consumer()
        report = packet_report(host)
        before = copy.deepcopy(report)
        result = await check(module, host, report)
        self.assertEqual(report, before)
        self.assertEqual(result["native_option_indices"], [2, 5])
        self.assertFalse(result["original_host_run_green"])
        self.assertFalse(result["game_operations_performed_by_this_consumer"])
        self.assertFalse(result["fixture_target_identity_proven"])
        self.assertEqual(result["business_context_binding"]["actor_character_id"], 123456789)

    async def test_actual_r1_intro_shape_cannot_be_relabelled_as_the_preparation_event(self):
        host, module = load_harness(), consumer()
        report = packet_report(host)
        context = report["steps"][2]["result"]["current_event_window_context"]
        # The R1 live failure was fp3_struggle.0051 with one visible option.
        context["event_definition_key"] = "fp3_struggle.0051"
        context["options"] = context["options"][:1]
        with self.assertRaisesRegex(RuntimeError, "typed definition/root/player/frame"):
            await check(module, host, report)
        self.assertEqual(report["error"], "RuntimeError: preserved original startup RED")

    async def test_wrong_process_or_reordered_rows_reject_before_packet_readmission(self):
        host, module = load_harness(), consumer()
        for fault in ("process", "order", "duplicate"):
            report = packet_report(host)
            if fault == "process":
                report["frontend_fixture_start_submission"]["result"]["binding"]["bridge_pid"] = 99
            elif fault == "order":
                report["steps"][0], report["steps"][1] = report["steps"][1], report["steps"][0]
            else:
                report["steps"].append(copy.deepcopy(report["steps"][0]))
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                await check(module, host, report)


if __name__ == "__main__":
    unittest.main()
