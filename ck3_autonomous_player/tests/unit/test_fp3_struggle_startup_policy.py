from __future__ import annotations

import copy
from pathlib import Path
import sys
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from test_frontend_fixture_scenario_host import current_frame, event_packet, load_harness, policy, submission
from xar_autoplayer.vanilla_events.registry import query_vanilla_event_knowledge_v1
from xar_autoplayer.vanilla_events.policy import recommend_registered_vanilla_event_option_v1
from xar_autoplayer.vanilla_events.records_fp3_struggle_intro_12004 import EVENT_KEY, SOURCE_PATH, SOURCE_SHA256


def predecessor_packet(snapshot, unknown=False):
    packet = event_packet(snapshot)
    context = packet["current_event_window_context"]
    context["event_definition_key"] = "unknown_predecessor.1" if unknown else EVENT_KEY
    context["saved_scopes"] = [{"name":name, "scope":{"status":"available", "type_key":kind}}
        for name,kind in (("start","boolean"), ("Mutawakkil","character"), ("Muntasir","character"),
            ("Mustain","character"), ("Mostaza","character"))]
    context["options"] = [{"rendered_index":0, "native_option_index":0, "shown":True,
        "enabled":True, "fallback":False, "cancel":False, "resolved_name":"Acknowledge"}]
    if unknown:
        context["options"] = [{**context["options"][0], "native_option_index":1},
            {**context["options"][0], "rendered_index":1}]
    return packet


def predecessor_snapshot(unknown=False):
    value = current_frame(2, startup=True)[0]
    value["active_event"]["option_count"] = 2 if unknown else 1
    value["active_event"]["options"] = value["active_event"]["options"][:2 if unknown else 1]
    return value


class StruggleKnowledgeTests(unittest.TestCase):
    def test_current_source_record_is_reviewed_effectless_and_build_specific(self):
        row = query_vanilla_event_knowledge_v1(EVENT_KEY, "1.20.0.4")
        self.assertEqual(row["status"], "available")
        self.assertEqual(row["analysis"]["source_sha256"][SOURCE_PATH], SOURCE_SHA256)
        effect = row["analysis"]["selected_choice_effect_profile"]
        self.assertEqual(effect["selected_option_effects"], [])
        self.assertEqual(effect["common_after_effects"], [])
        self.assertIsNone(effect["observable_postcondition"])
        self.assertNotEqual(query_vanilla_event_knowledge_v1(EVENT_KEY, "1.20.0.3")["status"], "available")

    def test_real_scope_shape_recommends_sole_option_and_rejects_wrong_player(self):
        snapshot = predecessor_snapshot()
        context = predecessor_packet(snapshot)["current_event_window_context"]
        result = recommend_registered_vanilla_event_option_v1(context,
            played_character_id=123456789, snapshot_option_count=1)
        self.assertEqual(result["status"], "recommended", result)
        self.assertEqual(result["selected_option_number"], 1)
        self.assertEqual(result["selected_native_option_index"], 0)
        wrong = recommend_registered_vanilla_event_option_v1(context,
            played_character_id=34014, snapshot_option_count=1)
        self.assertEqual(wrong["status"], "blocked")


class PredecessorSequenceTests(unittest.IsolatedAsyncioTestCase):
    async def consume(self, *, unknown=False, lost_ack=False, unchanged=False):
        harness, state, before = load_harness(), {}, predecessor_snapshot(unknown)
        calls = []
        class Client:
            async def call(self, tool, args=None):
                calls.append((tool,args))
                if tool == "ck3_query_current_event_window_context_v1": return predecessor_packet(before, unknown)
                if tool == "ck3_select_event_option":
                    record = state["startup_predecessor_events"][-1]
                    if record["status"] != "OPTION_REQUEST_WRITTEN_NO_RETRY" or not record["selection_attempted"]:
                        raise AssertionError("Decision was not recorded first")
                    if lost_ack: raise RuntimeError("lost native ACK")
                    return {"accepted":True}
                raise AssertionError("Unexpected mutation")
            async def fresh(self):
                if unchanged: return copy.deepcopy(before)
                after = current_frame(3, startup=True)[0]
                after.update(snapshot_id="native:4", native_revision=5, revision=6)
                after["active_event"]["instance_id"] = 918
                return after
        client = Client()
        async def run():
            return await harness.dispatch_fixture_scenario_startup_event(client, before, submission(harness), policy(),
                state=state, write=lambda:None, deadline=time.monotonic()+2)
        if lost_ack or unchanged:
            with self.assertRaises(RuntimeError): await run()
            with self.assertRaisesRegex(RuntimeError, "already attempted"): await run()
            result = None
        else:
            result = await run()
        return result,state,calls

    async def test_known_intro_is_confirmed_once_and_queued_prepare_remains_unselected(self):
        after,state,calls = await self.consume()
        self.assertEqual(after["active_event"]["instance_id"], 918)
        selects = [args for tool,args in calls if tool == "ck3_select_event_option"]
        self.assertEqual(selects, [{"option_number":1, "event_instance_id":917, "expected_revision":10}])
        record = state["startup_predecessor_events"][0]
        self.assertTrue(record["old_event_gone_observed"])
        self.assertIsNone(record["fallback_plan"])
        self.assertNotIn("startup_case", state)

    async def test_unknown_predecessor_captures_then_uses_first_displayed_native_mapping(self):
        after,state,calls = await self.consume(unknown=True)
        record = state["startup_predecessor_events"][0]
        self.assertTrue(record["offline_followup_required"])
        self.assertEqual(record["fallback_plan"]["unhandled_event_fallback"]["event_definition_key"], "unknown_predecessor.1")
        self.assertEqual(record["selected_option_number"], 2)
        self.assertEqual([args["option_number"] for tool,args in calls if tool == "ck3_select_event_option"], [2])
        self.assertEqual(after["active_event"]["instance_id"], 918)

    async def test_lost_ack_never_replays_or_claims_postcondition(self):
        _,state,calls = await self.consume(lost_ack=True)
        self.assertFalse(state["startup_predecessor_events"][0]["old_event_gone_observed"])
        self.assertEqual(sum(tool == "ck3_select_event_option" for tool,_ in calls), 1)

    async def test_ack_with_same_old_instance_remains_red_without_replay(self):
        _,state,calls = await self.consume(unchanged=True)
        record = state["startup_predecessor_events"][0]
        self.assertTrue(record["selection_result"]["accepted"])
        self.assertFalse(record["old_event_gone_observed"])
        self.assertEqual(sum(tool == "ck3_select_event_option" for tool,_ in calls), 1)


if __name__ == "__main__":
    unittest.main()
