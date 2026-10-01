from __future__ import annotations

import asyncio
from collections import Counter
import copy
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from native_campaign_autoplay import (
    CampaignConfig, INSPECT, PAUSE, QUERY_EVENT, SAVE, SELECT_EVENT, SIMULATION,
    SNAPSHOT, TOOLS, choose_option, read_plaintext_save, run,
)


class FakeClient:
    """Real async transport surface with delayed native state and temp saves."""
    def __init__(self, directory: Path):
        self.directory = directory
        self.calls = []
        self.raw = 1000
        self.revision = 1
        self.paused = True
        self.speed = 5
        self.event = None
        self.context_options = []
        self.progress = True
        self.pending = None
        self.late_action = None
        self.red_reason = None
        self.guard_error = False
        self.bad_save_body = False
        self.unknown_pause = False
        self.dead_player = False
        self.identity_change = False
        self.running_reads = 0
        self.save_count = 0

    def envelope(self, value):
        return {"is_error": False, "structured_content": {"session_id": "owned-client-session", "profile_sha256": "a"*64, **value}, "content": []}

    def frame(self):
        if self.pending is not None:
            left, paused = self.pending
            if left:
                self.pending = (left-1, paused)
            else:
                self.paused = paused
                self.pending = None
                self.revision += 1
        if not self.paused:
            self.running_reads += 1
            if self.progress:
                self.raw += 24
                self.revision += 1
            if self.unknown_pause and self.running_reads > 1:
                self.paused = True
        return {"revision": self.revision, "native_revision": self.revision, "date_raw": self.raw,
                "paused": self.paused, "speed": self.speed, "map_ready": True,
                "episode_projection": "native_campaign", "active_event": copy.deepcopy(self.event),
                "pending_character_interaction": None,
                "played_character": {"character_id": 12, "alive": not (self.dead_player and self.running_reads > 1)},
                "diagnostics": {"bridge_pid": 51 if self.identity_change and self.save_count else 50,
                    "connection_generation": 1, "hello": {"expected_ck3_version": "1.20.0.2", "expected_ck3_sha256": "b"*64}}}

    async def call_tool(self, name, arguments):
        await asyncio.sleep(0)  # Exercise asynchronous sequencing, not a sync stub.
        self.calls.append((name, copy.deepcopy(arguments)))
        if self.guard_error and name == SNAPSHOT:
            return {"is_error": True, "structured_content": None, "content": [{"type": "text", "text": "offline/lease/crash guard rejected"}]}
        if name == INSPECT:
            return self.envelope({"status": "profile_bound", "attached": True})
        if name == SNAPSHOT:
            return self.envelope({"status": "native_snapshot_verified", "snapshot": self.frame()})
        if name == QUERY_EVENT:
            return self.envelope({"status": "native_event_query_verified", "result": {
                "current_event_window_context": {"status": "available", "current_event_instance_id": self.event["instance_id"],
                    "event_definition_key": "native.example", "readiness": {"option_presentation_ready": True},
                    "options": copy.deepcopy(self.context_options)}}})
        action = "pause" if name == PAUSE else arguments.get("action")
        if self.red_reason is not None:
            return self.envelope({"status": "RED", "reason": self.red_reason})
        if name == PAUSE or name == SIMULATION:
            if action in {"pause", "resume"}:
                desired = action == "pause"
                if self.late_action == action:
                    self.pending = (2, desired)
                    self.late_action = None
                    message = "current native pause" if name == PAUSE else "native pause/resume"
                    return self.envelope({"status": "RED", "reason": f"RuntimeError: {message} postcondition did not materialize"})
                self.paused = desired
            else:
                self.speed = int(action[-1])
            self.revision += 1
            return self.envelope({"status": "native_gameplay_postcondition_verified"})
        if name == SELECT_EVENT:
            self.event = None
            self.revision += 1
            return self.envelope({"status": "native_gameplay_postcondition_verified"})
        if name == SAVE:
            self.save_count += 1
            actual = date(1900, 1, 1) + timedelta(days=(self.raw-1000)//24)
            value = f"{actual.year}.{actual.month}.{actual.day}"
            body = "2100.1.1" if self.bad_save_body else value
            raw = f'SAV0100fixture\nmeta_data={{\n\tmeta_date={value}\n}}\ndate={body}\nversion="1.20.0.2"\nsave_marker={self.save_count}\n'.encode()
            path = self.directory / "xar_checkpoint.ck3"
            path.write_bytes(raw)
            self.revision += 1
            return self.envelope({"status": "native_gameplay_postcondition_verified", "result": {"checkpoint": {
                "status": "saved", "path": str(path.resolve()), "size": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(), "date_raw": self.raw,
                "succession_lifecycle": {"legacy_only": True}}}})
        raise AssertionError(f"unexpected capability: {name}")


def option(index, *, shown=True, enabled=True, rows=()):
    return {"native_option_index": index, "rendered_index": 0, "shown": shown, "enabled": enabled,
            "resolved_name": "ignored_localization", "effect_indicators": {"rows": list(rows), "complete_effect_set": False}}


class CampaignTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.saves = self.root / "save games"
        self.saves.mkdir()
        self.client = FakeClient(self.saves)

    def config(self, **overrides):
        values = dict(start_date="1900.1.1", target_date="1900.1.3", baseline_date_raw=1000,
                      save_directory=self.saves, evidence_directory=self.root/"evidence", checkpoint_days=1,
                      poll_seconds=0.002, postcondition_timeout_seconds=0.03,
                      no_progress_timeout_seconds=0.015, tool_timeout_seconds=1)
        values.update(overrides)
        return CampaignConfig(**values)

    def receipts(self, kind):
        return [json.loads(path.read_text(encoding="utf-8")) for path in sorted((self.root/"evidence").glob(f"*-{kind}.json"))]

    async def test_normal_time_target_and_immutable_full_byte_archives(self):
        result = await run(self.client, self.config())
        self.assertEqual(result["status"], "completed")
        proof = result["final_checkpoint"]
        self.assertEqual(proof["body_date"], "1900.1.3")
        archives = sorted((self.root/"evidence/checkpoints").glob("*.ck3"))
        self.assertEqual(len(archives), 2)
        for path in archives:
            raw, actual = read_plaintext_save(path)
            self.assertEqual(len(raw), actual["bytes"])
            self.assertTrue(path.name.endswith(actual["sha256"]+".ck3"))
        initial = archives[0].read_bytes()
        self.client.directory.joinpath("xar_checkpoint.ck3").write_bytes(b"later source overwrite")
        self.assertEqual(archives[0].read_bytes(), initial)
        self.assertTrue(all(name in TOOLS for name, _ in self.client.calls))

    async def test_late_resume_red_is_preserved_and_never_replayed(self):
        self.client.late_action = "resume"
        result = await run(self.client, self.config())
        self.assertEqual(result["status"], "completed")
        self.assertEqual(sum(name == SIMULATION and args.get("action") == "resume" for name,args in self.client.calls), 1)
        self.assertTrue(any(row["response"]["structured_content"].get("status") == "RED" for row in self.receipts("mcp-receipt")))
        self.assertTrue(any(row.get("recovered_late_postcondition") for row in self.receipts("action-confirmed")))

    async def test_native_option_index_not_rendered_order(self):
        self.client.event = {"instance_id": 7, "option_count": 4}
        self.client.context_options = [
            option(0, shown=False), option(1, rows=[{"kind":"stress", "direction":"increase", "critical":False}]),
            option(2), option(3, enabled=False),
        ]
        result = await run(self.client, self.config())
        self.assertEqual(result["status"], "completed")
        selected = [args for name,args in self.client.calls if name == SELECT_EVENT]
        self.assertEqual(selected[0]["option_number"], 3)
        self.assertEqual(selected[0]["event_instance_id"], 7)
        choice = self.receipts("event-choice")[0]
        self.assertFalse(choice["complete_effect_preview"])
        self.assertFalse(choice["localization_used_for_choice"])

    async def test_arbitrary_red_strongly_rejects_without_retry(self):
        self.client.paused = False
        self.client.red_reason = "RuntimeError: native pause/resume postcondition did not materialize; offline guard failed"
        result = await run(self.client, self.config())
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(Counter(name for name,_ in self.client.calls)[PAUSE], 1)
        self.assertEqual(Counter(name for name,_ in self.client.calls)[SAVE], 0)

    async def test_guard_error_prevents_all_actions(self):
        self.client.guard_error = True
        result = await run(self.client, self.config())
        self.assertEqual(result["status"], "rejected")
        self.assertTrue(all(name in {INSPECT,SNAPSHOT} for name,_ in self.client.calls))

    async def test_no_progress_stops_instead_of_repeated_resume(self):
        self.client.progress = False
        result = await run(self.client, self.config())
        self.assertEqual(result["status"], "await_root")
        self.assertEqual(result["reason"], "native_clock_no_progress")
        self.assertEqual(sum(name == SIMULATION and args.get("action") == "resume" for name,args in self.client.calls), 1)

    async def test_unknown_pause_and_player_terminal_require_root(self):
        self.client.unknown_pause = True
        result = await run(self.client, self.config())
        self.assertEqual(result["status"], "await_root")
        self.assertEqual(result["reason"], "unexpected_pause_or_unknown_modal")
        self.client = FakeClient(self.saves)
        self.client.dead_player = True
        result = await run(self.client, self.config(evidence_directory=self.root/"terminal-evidence"))
        self.assertEqual(result["status"], "await_root")
        self.assertEqual(result["reason"], "player_terminal_or_unavailable")

    async def test_body_date_mismatch_cannot_complete_target(self):
        self.client.bad_save_body = True
        result = await run(self.client, self.config())
        self.assertEqual(result["status"], "rejected")
        self.assertIn("checkpoint_body_or_format_invalid", result["reason"])
        self.assertEqual(self.client.save_count, 1)
        self.assertFalse((self.root/"evidence/checkpoints").exists())

    async def test_process_identity_change_rejects_after_single_save(self):
        self.client.identity_change = True
        result = await run(self.client, self.config())
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["reason"], "native_process_build_identity_changed")
        self.assertEqual(self.client.save_count, 1)

    async def test_later_entry_preserves_frozen_baseline(self):
        self.client.raw = 1048
        result = await run(self.client, self.config())
        self.assertEqual(result["status"], "completed")
        self.assertFalse(any(name == SIMULATION for name,_ in self.client.calls))
        self.assertEqual(self.receipts("config")[0]["baseline_date_raw"], 1000)

    async def test_unresolved_dispatch_times_out_without_replay(self):
        original = self.client.call_tool
        async def delayed(name, arguments):
            if name == SIMULATION:
                self.client.calls.append((name, copy.deepcopy(arguments)))
                await asyncio.sleep(0.1)
            return await original(name, arguments)
        self.client.call_tool = delayed
        result = await run(self.client, self.config(tool_timeout_seconds=0.01))
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["reason"], "mcp_request_failed_or_unresolved")
        self.assertEqual(sum(name == SIMULATION for name,_ in self.client.calls), 1)
        self.assertTrue(self.receipts("request-error"))

    async def test_public_model_dump_queue_transport_is_supported(self):
        class SerializedResult:
            def __init__(self, raw):
                self.raw = raw
            def model_dump(self):
                return self.raw
        original = self.client.call_tool
        async def wrapped(name, arguments):
            return SerializedResult(await original(name, arguments))
        self.client.call_tool = wrapped
        result = await run(self.client, self.config())
        self.assertEqual(result["status"], "completed")

    async def test_checkpoint_receipt_sha_must_match_full_file(self):
        original = self.client.call_tool
        async def mismatch(name, arguments):
            result = await original(name, arguments)
            if name == SAVE:
                result["structured_content"]["result"]["checkpoint"]["sha256"] = "0"*64
            return result
        self.client.call_tool = mismatch
        result = await run(self.client, self.config())
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["reason"], "checkpoint_declared_bytes_or_native_date_disagree")
        self.assertEqual(self.client.save_count, 1)


class SaveAndOptionTests(unittest.TestCase):
    def test_date_inside_nested_or_quoted_fields_is_not_body_date(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"save.ck3"
            path.write_bytes(b'SAV0100header\nmeta_data={\nmeta_date=1900.1.1\n}\nfoo={\ndate=2000.1.1\n}\nlabel="quoted\ndate=2001.1.1\n"\ndate=1900.1.1\n')
            _, proof = read_plaintext_save(path)
            self.assertEqual(proof["body_date"], "1900.1.1")

    def test_critical_indicator_is_ranked_before_stress(self):
        chosen = choose_option({"options": [option(0, rows=[{"critical":True}]), option(4, rows=[{"kind":"stress","direction":"increase"}]), option(5)]})
        self.assertEqual(chosen["native_option_index"], 5)


if __name__ == "__main__":
    unittest.main()
