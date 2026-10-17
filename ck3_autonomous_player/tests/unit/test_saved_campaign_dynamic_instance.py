"""Approved saved startup uses the current process's event instance, read-only."""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import test_saved_campaign_startup_admission as fixture

HOST = fixture.HOST
ACTOR = 123456789  # Full reference from this test's frozen save, not a history ID.
EXPECTED = {"actor_character_id": ACTOR, "date_raw": 51394920}
PROFILE = "faith-and-power-e01-abbasid-867"
EVENT = "xar_faith_h01_prepare.1"
INSTANCE = 612  # The previous process's instance is deliberately not used.


def current_snapshot(epoch=7, instance=INSTANCE):
    value = fixture.snapshot(epoch)
    value["date_raw"] = EXPECTED["date_raw"]
    value["played_character"]["character_id"] = ACTOR
    value["active_event"].update(instance_id=instance, options=[
        {"option_number": 1, "enabled": True}, {"option_number": 2, "enabled": True}])
    return value


def current_packet(instance=INSTANCE):
    value = fixture.packet()
    context = value["current_event_window_context"]
    context.update(current_event_instance_id=instance, event_definition_key=EVENT,
        date_raw=EXPECTED["date_raw"])
    context["root_scope"]["typed_identity"]["character_id"] = ACTOR
    context["options"] = [{"rendered_index": index, "native_option_index": index,
        "shown": True, "enabled": True, "fallback": False, "cancel": False} for index in (0, 1)]
    return value


class Client(fixture.Client):
    def __init__(self, state, *, context=None, instance=INSTANCE, after_change=None):
        root = fixture.root()
        root.update(player_character_id=ACTOR, date_raw=EXPECTED["date_raw"])
        super().__init__(state, context=context or current_packet(instance), root_value=root,
            after_change=after_change)
        self.instance = instance

    async def fresh(self):
        self.frames += 1
        value = current_snapshot(6 + self.frames, self.instance)
        if self.frames >= 4 and self.after_change:
            self.after_change(value)
        return value


class DynamicSavedInstanceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state = Path(self.temp.name)
        handler = self.state / "startup_handler.py"
        handler.write_bytes(fixture.HANDLER)
        self.contract = {"schema": "ck3-saved-campaign-startup-case-contract-v2",
            "profile_id": PROFILE, "state_dir": str(self.state), "dependencies": [],
            "handler": {"path": str(handler), "bytes": len(fixture.HANDLER),
                "sha256": hashlib.sha256(fixture.HANDLER).hexdigest(), "function": "admit_saved_startup_event"},
            "expected": {"event_definition_key": EVENT, "event_instance_id": None,
                "root_character_id": ACTOR, **EXPECTED, "native_option_indices": [0, 1]}}

    async def wait(self, client, contract=None):
        report = {"pipe": "fixture-pipe", "saved_campaign_launch": {
            "status": "ACTUAL_SINGLE_CLI_RESTORE_LAUNCHED", "argv_admitted": True, "ck3_pid": 71},
            "saved_campaign_startup_case_contract_input": {"contract": contract or self.contract}}
        result = await HOST.wait_for_saved_campaign(client, EXPECTED, report=report,
            write=lambda: None, timeout=1, managed_done=None, poll_interval=0)
        return result, report

    async def test_current_instance_is_bound_after_owner_frames_without_mutating_input(self):
        original = copy.deepcopy(self.contract)
        client = Client(self.state)
        result, report = await self.wait(client)
        admission = result["binding"]["startup_event_admission"]
        self.assertEqual(admission["event_instance_id"], INSTANCE)
        self.assertEqual(client.calls[-1], ("ck3_query_current_event_window_context_v1",
            {"event_instance_id": INSTANCE, "expected_revision": 3}))
        binding = admission["runtime_instance_binding"]
        self.assertIsNone(binding["input_event_instance_id"])
        self.assertEqual(binding["actual_event_instance_id"], INSTANCE)
        self.assertEqual(binding["actor_character_id"], ACTOR)
        self.assertEqual(binding["bridge_pid"], 71)
        self.assertFalse(binding["selection_attempted"])
        self.assertEqual(self.contract, original)
        record = report["saved_campaign_restore"]["startup_case"]
        self.assertEqual(record["contract"], original)
        self.assertEqual(record["runtime_contract"]["schema"], "ck3-saved-campaign-startup-case-contract-v1")
        self.assertEqual(record["runtime_contract"]["expected"]["event_instance_id"], INSTANCE)
        self.assertNotIn("profile_id", record["runtime_contract"])
        self.assertFalse(any("select" in name for name, _ in client.calls))

    def test_v2_is_restricted_to_exact_approved_definition_date_profile_and_options(self):
        changes = [lambda c: c.update(profile_id="another-profile"),
            lambda c: c["expected"].update(event_instance_id=1),
            lambda c: c["expected"].update(event_definition_key="fp3_struggle.0051"),
            lambda c: c["expected"].update(date_raw=51394921),
            lambda c: c["expected"].update(native_option_indices=[0, 2]),
            lambda c: c["expected"].update(root_character_id=ACTOR + 1),
            lambda c: c["expected"].update(root_character_id=0, actor_character_id=0)]
        for change in changes:
            value = copy.deepcopy(self.contract)
            change(value)
            with self.subTest(change=change), self.assertRaises(ValueError):
                HOST.verify_saved_campaign_startup_case_contract(value, self.state)

    async def test_binding_cannot_skip_two_actual_owner_frames(self):
        client = Client(self.state)
        with self.assertRaisesRegex(RuntimeError, "two stable owner frames"):
            await HOST.admit_saved_startup_event(client, current_snapshot(), EXPECTED, fixture.BINDING,
                self.contract, state={}, write=lambda: None, deadline=time.monotonic() + 1, managed_done=None)
        self.assertEqual(client.calls, [])

    async def test_runtime_window_definition_root_options_and_frame_remain_strict(self):
        changes = [lambda p: p["current_event_window_context"].update(current_event_instance_id=1),
            lambda p: p["current_event_window_context"].update(event_definition_key="fp3_struggle.0051"),
            lambda p: p["current_event_window_context"]["root_scope"]["typed_identity"].update(character_id=ACTOR + 1),
            lambda p: p["current_event_window_context"]["options"][1].update(enabled=False),
            lambda p: p.update(queried_native_revision=4)]
        for change in changes:
            packet = current_packet()
            change(packet)
            client = Client(self.state, context=packet)
            with self.subTest(change=change), self.assertRaises(RuntimeError):
                await self.wait(client)
            self.assertFalse(any("select" in name for name, _ in client.calls))

    async def test_new_fresh_frame_must_retain_the_same_bound_event_and_actual_actor(self):
        for change in [lambda s: s["active_event"].update(instance_id=INSTANCE + 1),
                lambda s: s["played_character"].update(character_id=ACTOR + 1),
                lambda s: s.update(date_raw=EXPECTED["date_raw"] + 1)]:
            with self.subTest(change=change), self.assertRaises((RuntimeError, ValueError)):
                await self.wait(Client(self.state, after_change=change))

    async def test_saved_input_actual_actor_cannot_be_replaced_by_contract_actor(self):
        self.contract["expected"].update(actor_character_id=ACTOR + 1, root_character_id=ACTOR + 1)
        client = Client(self.state)
        with self.assertRaisesRegex(RuntimeError, "saved actor/date/instance"):
            await self.wait(client)
        self.assertFalse(any(name == "ck3_query_current_event_window_context_v1" for name, _ in client.calls))

    def test_legacy_v1_still_requires_a_concrete_instance(self):
        self.contract.pop("profile_id")
        self.contract["schema"] = "ck3-saved-campaign-startup-case-contract-v1"
        with self.assertRaises(ValueError):
            HOST.verify_saved_campaign_startup_case_contract(self.contract, self.state)


if __name__ == "__main__":
    unittest.main()
