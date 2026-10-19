"""Synthetic native SAVE bytes/cold driver, real App and registered MCP.

No process, Native bridge, game or real CK3 save is opened. The actual native
cold binder, SAVE driver persistence, full transition/Close validators and
App retirement consumer execute against small synthetic files and frames.
"""
from copy import deepcopy
from contextlib import nullcontext
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from mcp import Client
from test_successor_ui_app_owner_v1 import Driver, planned
from xar_autoplayer import successor_ui_pending_ledger_v1 as journal
from xar_autoplayer import successor_ui_checkpoint_lineage_v1 as lineage
from xar_autoplayer.bridge import mcp_server, successor_ui_app_owner_v1 as app_module
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.strategy import continue_ordinary_campaign_goal_v1


class Endpoint:
    def start(self, *args): pass
    def close(self): pass
    def stop(self): pass


class NativeFixture(Driver, NativeHeadlessGameplayDriver):
    def __init__(self, root):
        NativeHeadlessGameplayDriver.__init__(self, endpoint=Endpoint(), state_dir=root, save_dir=root)
        Driver.__init__(self, root)
        self._succession_lifecycle["pact_contract"] = "absent_by_fresh_campaign_xar_off_contract"
        for value in (self.frame, self.post, self.result, self.proof):
            value["succession_lifecycle"] = deepcopy(self._succession_lifecycle)
        self._session_bridge_pid = self.frame["diagnostics"]["bridge_pid"]

    def execute_step(self, step, *, expected_revision):
        if step == "save-checkpoint":
            if expected_revision != self.frame["revision"]:
                raise ValueError("synthetic stale SAVE")
            self.saves += 1
            data = b"synthetic CK3 checkpoint only"
            save = self.save_dir / "xar_checkpoint.ck3"
            save.write_bytes(data)
            checkpoint = dict(status="saved", path=str(save), name=save.name,
                size=len(data), sha256=hashlib.sha256(data).hexdigest(),
                date_raw=self.frame["date_raw"], strategy="native-autosave-command-v1",
                history_index=len(self._command_history) + 1,
                episode_character_id=self.frame["episode_character_id"], episode_run_id=self.frame["episode_run_id"],
                succession_lifecycle=deepcopy(self._succession_lifecycle))
            self._last_checkpoint = deepcopy(checkpoint)
            result = dict(step=step, accepted=True, checkpoint=checkpoint,
                materialization={"available": True}, original_extra={"preserved": True})
            receipt = NativeHeadlessGameplayDriver._record_command(self, step, ok=True, result=result)
            return {**result, "driver_state_replace_receipt": receipt}
        result = Driver.execute_step(self, step, expected_revision=expected_revision)
        if step == app_module.STEP:
            self._episode_character_id = self.frame["episode_character_id"]
            self._episode_run_id = self.frame["episode_run_id"]
            self._campaign_goal = deepcopy(self.frame["campaign_goal"])
        return result


class CompletedColdAppTests(unittest.IsolatedAsyncioTestCase):
    async def test_registered_save_real_cold_binder_archive_and_next_natural_continue(self):
        with tempfile.TemporaryDirectory(prefix="m7-cold-App-") as temp:
            root = Path(temp)
            executable = os.path.normcase(os.path.abspath("synthetic/ck3.exe"))
            state = {"epoch": "e" * 64, "old_alive": True}
            def process(pid):
                if pid == 123 and state["old_alive"]:
                    return {"pid": 123, "creation_date": "synthetic-original-birth", "executable": executable}
                if pid == 456:
                    return {"pid": 456, "creation_date": "synthetic-new-birth", "executable": executable}
                return {"pid": pid, "creation_date": "synthetic-reused-old-pid-birth", "executable": executable}
            with patch.object(app_module, "_machine_id", return_value="synthetic-App-machine"), \
                    patch.object(journal, "owner_source_epoch_v1", side_effect=lambda: state["epoch"]), \
                    patch("xar_autoplayer.runtime._process_identity", side_effect=process), \
                    patch.object(GameplayBridgeService, "plan_turn", planned):
                old = NativeFixture(root)
                # Existing fixtures use PID123. Keep that original frame/source.
                self.assertEqual(old.frame["diagnostics"]["bridge_pid"], 123)
                server = mcp_server.create_server(old)
                async with Client(server) as client:
                    continued = await client.call_tool("ck3_auto_turn", {})
                    self.assertFalse(continued.is_error, str(continued))
                    counts = old.snapshot_reads, old.saves
                    denied = await client.call_tool("ck3_save_checkpoint", {"expected_revision": old.frame["revision"]})
                    self.assertTrue(denied.is_error)
                    self.assertEqual((old.snapshot_reads, old.saves), counts)
                    self.assertFalse((root / lineage.COMPLETION_FILE).exists())
                    event = await client.call_tool("ck3_auto_turn", {})
                    self.assertFalse(event.is_error, str(event))
                    clear = await client.call_tool("ck3_auto_turn", {})
                    self.assertFalse(clear.is_error, str(clear))
                    self.assertFalse(clear.structured_content["successor_ui_obligation_v1"]["pending"])
                    close_file = next(root.glob("successor-ui-close-*.json"))
                    verified_close = close_file.read_bytes()
                    unknown = json.loads(verified_close); unknown["status"] = "UNKNOWN"
                    close_file.write_text(json.dumps(unknown), encoding="utf-8")
                    counts = old.snapshot_reads, old.saves
                    unknown_save = await client.call_tool("ck3_save_checkpoint", {"expected_revision": old.frame["revision"]})
                    self.assertTrue(unknown_save.is_error)
                    self.assertEqual((old.snapshot_reads, old.saves), counts)
                    close_file.write_bytes(verified_close)
                    counts = old.snapshot_reads
                    saved = await client.call_tool("ck3_save_checkpoint", {"expected_revision": old.frame["revision"]})
                    self.assertFalse(saved.is_error, str(saved))
                    result = saved.structured_content
                    self.assertEqual(result["successor_ui_completed_checkpoint_v1"]["status"], "captured")
                    self.assertEqual(old.snapshot_reads - counts, 1)
                    self.assertEqual(result["original_extra"], {"preserved": True})
                    paired_driver_path = old._native_driver_state_path()
                    paired_driver_raw = paired_driver_path.read_bytes()
                    counts = old.snapshot_reads, old.cap_reads
                    normal = await client.call_tool("ck3_auto_turn", {})
                    self.assertFalse(normal.is_error, str(normal))
                    self.assertEqual((old.snapshot_reads, old.cap_reads), counts)
                    # A later original SAVE still returns if evidence capture fails.
                    with patch.object(lineage, "write_completed_checkpoint_v1", side_effect=OSError("synthetic sidecar failure")):
                        saved_count = old.saves
                        failed_capture = await client.call_tool("ck3_save_checkpoint", {"expected_revision": old.frame["revision"]})
                        self.assertFalse(failed_capture.is_error, str(failed_capture))
                        self.assertEqual(old.saves, saved_count + 1)
                        self.assertEqual(failed_capture.structured_content["successor_ui_completed_checkpoint_v1"]["status"], "capture_failed")
                    # Restore the exact earlier retained small synthetic pair;
                    # do not hand-rewrite its history or lifecycle/goal fields.
                    anchor = json.loads((root / lineage.COMPLETION_FILE).read_text(encoding="utf-8"))
                    paired_driver_path.write_bytes(paired_driver_raw)
                original = (root / journal.FILE).read_bytes()
                close_path = next(root.glob("successor-ui-close-*.json"))
                original_close = close_path.read_bytes()
                anchor_raw = (root / lineage.COMPLETION_FILE).read_bytes()
                state.update(epoch="f" * 64, old_alive=False)
                cold = NativeFixture(root)
                cold.frame = deepcopy(old.frame)
                cold.frame["diagnostics"].update(bridge_pid=456, connection_generation=1)
                cold.frame.update(snapshot_id="synthetic-cold:first-paused", revision=1, native_revision=2)
                cold._session_bridge_pid = 456
                cold._pending_cold_candidate = cold._read_driver_state()
                self.assertIsNotNone(cold._pending_cold_candidate, cold._driver_state_error)
                NativeHeadlessGameplayDriver._bind_episode_from_playable_snapshot(cold, cold.frame,
                    current_character_id=cold.frame["played_character"]["character_id"])
                self.assertEqual(cold._driver_state_restore_kind, "cold_checkpoint")
                projection = cold._successor_ui_cold_checkpoint_projection_v1
                self.assertIsInstance(projection, lineage.NativeColdCheckpointProjectionV1)
                # Simulate later normal source queries; the trusted cold capsule
                # survives without scanning their history or rereading a SAVE.
                cold._command_history.append({"index": len(cold._command_history)+1, "command": "synthetic-readonly", "ok": True})
                previous, old_episode = cold.frame["episode_character_id"], cold.frame["episode_run_id"]
                cold.frame["played_character"]["character_id"] = 29
                cold.frame.update(one_life_terminal=True, one_life_terminal_reason="played_character_changed")
                cold.post = deepcopy(cold.frame)
                cold.post["played_character"]["character_id"] = 29
                cold.post.update(episode_character_id=29, episode_run_id="synthetic-next-successor",
                                 one_life_terminal=False, one_life_terminal_reason=None)
                reconciliation = deepcopy(cold.result["reconciliation"])
                reconciliation.update(predecessor_character_id=previous, actual_successor_character_id=29,
                    successor_binding={key: cold.frame[key] for key in ("snapshot_id", "revision", "native_revision", "date_raw")},
                    predecessor_binding={"episode_character_id": previous, "episode_run_id": old_episode})
                cold.result.update(predecessor_character_id=previous, successor_character_id=29,
                    source_episode_run_id=old_episode, episode_run_id="synthetic-next-successor", reconciliation=reconciliation)
                cold.result.update({key: cold.frame[key] for key in ("snapshot_id", "revision", "date_raw")})
                cold.post["campaign_goal"] = continue_ordinary_campaign_goal_v1(cold.frame["campaign_goal"], reconciliation)
                replace_original = os.replace
                def fail_only_retirement(source, destination):
                    if Path(source) == root / journal.FILE:
                        raise OSError("synthetic exact retirement move failure")
                    return replace_original(source, destination)
                for mode in ("client capsule", "UNKNOWN Close", "wrong checkpoint", "archive move failure"):
                    if mode == "client capsule":
                        cold._successor_ui_cold_checkpoint_projection_v1 = json.loads(projection.body)
                    elif mode == "UNKNOWN Close":
                        bad = json.loads(original_close); bad["status"] = "UNKNOWN"
                        close_path.write_text(json.dumps(bad), encoding="utf-8")
                    elif mode == "wrong checkpoint":
                        bad = json.loads(anchor_raw); bad["checkpoint"]["sha256"] = "b" * 64
                        (root / lineage.COMPLETION_FILE).write_text(json.dumps(bad), encoding="utf-8")
                    failure = patch.object(lineage.os, "replace", side_effect=fail_only_retirement) if mode == "archive move failure" else nullcontext()
                    with failure:
                        async with Client(mcp_server.create_server(cold)) as client:
                            rejected = await client.call_tool("ck3_auto_turn", {})
                    with self.subTest(mode):
                        self.assertTrue(rejected.is_error, str(rejected))
                        self.assertEqual(cold.continues, 0)
                        self.assertEqual((root / journal.FILE).read_bytes(), original)
                    cold._successor_ui_cold_checkpoint_projection_v1 = projection
                    close_path.write_bytes(original_close)
                    (root / lineage.COMPLETION_FILE).write_bytes(anchor_raw)
                async with Client(mcp_server.create_server(cold)) as client:
                    accepted = await client.call_tool("ck3_auto_turn", {})
                    self.assertFalse(accepted.is_error, str(accepted))
                    self.assertEqual(cold.continues, 1)
                    self.assertEqual(accepted.structured_content["successor_ui_obligation_v1"]["status"], "pending")
                    self.assertEqual(cold.frame["campaign_goal"]["progress"]["reconciled_successions"], 2)
                archives = list((root / "successor-ui-resolved-history").glob("successor-ui-resolved-*.json"))
                self.assertEqual(len(archives), 1)
                self.assertEqual(archives[0].read_bytes(), original)
                self.assertEqual(close_path.read_bytes(), original_close)
                self.assertNotEqual((root / journal.FILE).read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
