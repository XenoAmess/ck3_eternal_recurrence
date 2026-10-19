"""Real registered App/SAVE/warm binder over small synthetic checkpoint files.

No Game, Native bridge, real process identity or live SAVE/Driver is accessed.
"""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from mcp import Client
from test_successor_ui_checkpoint_cold_app_v1 import NativeFixture, planned
from xar_autoplayer import successor_ui_pending_ledger_v1 as journal
from xar_autoplayer import successor_ui_checkpoint_lineage_v1 as lineage
from xar_autoplayer.bridge import mcp_server, successor_ui_app_owner_v1 as app_module
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService


class CompletedWarmAppTests(unittest.IsolatedAsyncioTestCase):
    async def test_resolved_same_Game_source_maintenance_allows_one_original_save(self):
        with tempfile.TemporaryDirectory(prefix="m7-warm-App-software-") as temp:
            root = Path(temp)
            epoch = ["e" * 64]
            executable = os.path.normcase(os.path.abspath("synthetic/ck3.exe"))
            def identity(pid):
                return {"pid": pid, "creation_date": "synthetic-original-birth", "executable": executable}
            with patch.object(app_module, "_machine_id", return_value="synthetic-App-machine"), \
                    patch.object(journal, "owner_source_epoch_v1", side_effect=lambda: epoch[0]), \
                    patch("xar_autoplayer.runtime._process_identity", side_effect=identity), \
                    patch.object(GameplayBridgeService, "plan_turn", planned):
                old = NativeFixture(root)
                async with Client(mcp_server.create_server(old)) as client:
                    for _ in range(3):
                        turn = await client.call_tool("ck3_auto_turn", {})
                        self.assertFalse(turn.is_error, str(turn))
                    save = await client.call_tool("ck3_save_checkpoint", {"expected_revision": old.frame["revision"]})
                    self.assertFalse(save.is_error, str(save))
                    self.assertEqual(save.structured_content["successor_ui_completed_checkpoint_v1"]["status"], "captured")
                original = (root / journal.FILE).read_bytes()
                completion = (root / lineage.COMPLETION_FILE).read_bytes()
                close_path = next(root.glob("successor-ui-close-*.json"))
                close_bytes = close_path.read_bytes()
                epoch[0] = "f" * 64
                warm = NativeFixture(root)
                warm.frame = deepcopy(old.frame)
                warm.frame["diagnostics"]["connection_generation"] += 1
                # Run the actual first-hello warm adoption; the cold candidate
                # binder intentionally represents a different process.
                warm._session_bridge_pid = None
                NativeHeadlessGameplayDriver._adopt_bridge_session(
                    warm, warm.frame["diagnostics"]["bridge_pid"])
                NativeHeadlessGameplayDriver._bind_episode_from_playable_snapshot(warm, warm.frame,
                    current_character_id=warm.frame["played_character"]["character_id"])
                self.assertEqual(warm._driver_state_restore_kind, "same_pid_hot")
                self.assertEqual(warm._episode_binding_state, "active_resumed")
                self.assertIsNone(getattr(warm, "_successor_ui_cold_checkpoint_projection_v1", None))
                # UNKNOWN cannot gain a SAVE or retirement through the new route.
                unknown = json.loads(close_bytes); unknown["status"] = "UNKNOWN"
                close_path.write_text(json.dumps(unknown), encoding="utf-8")
                async with Client(mcp_server.create_server(warm)) as client:
                    rejected = await client.call_tool("ck3_save_checkpoint", {"expected_revision": warm.frame["revision"]})
                    self.assertTrue(rejected.is_error, str(rejected))
                    self.assertEqual(warm.saves, 0)
                    self.assertEqual((root / journal.FILE).read_bytes(), original)
                    close_path.write_bytes(close_bytes)
                    with patch.object(lineage, "observe_native_cold_checkpoint_v1",
                                      side_effect=AssertionError("same Game must not request a cold token")):
                        saved = await client.call_tool("ck3_save_checkpoint", {"expected_revision": warm.frame["revision"]})
                    self.assertFalse(saved.is_error, str(saved))
                    self.assertEqual(saved.structured_content["original_extra"], {"preserved": True})
                    self.assertEqual((warm.continues, warm.closes, warm.saves), (0, 0, 1))
                archives = list((root / "successor-ui-resolved-history").glob("successor-ui-resolved-*.json"))
                self.assertEqual(len(archives), 1)
                self.assertEqual(archives[0].read_bytes(), original)
                self.assertEqual(close_path.read_bytes(), close_bytes)
                self.assertEqual((root / lineage.COMPLETION_FILE).read_bytes(), completion)
                self.assertFalse((root / journal.FILE).exists())
                self.assertIsNone(getattr(warm, "_successor_ui_cold_checkpoint_projection_v1", None))


if __name__ == "__main__":
    unittest.main()
