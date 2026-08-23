from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.frame_parser import parse_complete_snapshots  # noqa: E402


class ModBridgeStaticTests(unittest.TestCase):
    def test_ck3_scripts_are_utf8_bom(self) -> None:
        paths = [
            ROOT / "descriptor.mod",
            ROOT / "gui" / "xar_mcp_bridge.gui",
            ROOT / "gui" / "scripted_widgets" / "xar_mcp_bridge_widgets.txt",
            ROOT / "common" / "scripted_effects" / "xar_mcp_bridge_effects.txt",
            ROOT / "templates" / "xar_mcp_inbox.txt",
            ROOT / "templates" / "xar_mcp_snapshot.example.txt",
        ]
        for path in paths:
            with self.subTest(path=path):
                self.assertTrue(path.read_bytes().startswith(b"\xef\xbb\xbf"))

    def test_poll_widget_uses_registered_point_four_second_run_loop(self) -> None:
        registration = (ROOT / "gui" / "scripted_widgets" / "xar_mcp_bridge_widgets.txt").read_text(
            encoding="utf-8-sig"
        )
        gui = (ROOT / "gui" / "xar_mcp_bridge.gui").read_text(encoding="utf-8-sig")
        self.assertIn("gui/xar_mcp_bridge.gui = xar_mcp_bridge_window", registration)
        self.assertIn("duration = 0.4", gui)
        self.assertIn("ExecuteConsoleCommand('run xar_mcp_inbox.txt')", gui)
        self.assertIn("gui.createwidget gui/xar_mcp_bridge.gui xar_mcp_poll_counter", gui)
        self.assertEqual(gui.count("{"), gui.count("}"))

    def test_snapshot_effect_uses_typed_request_and_minimal_state(self) -> None:
        effects = (ROOT / "common" / "scripted_effects" / "xar_mcp_bridge_effects.txt").read_text(
            encoding="utf-8-sig"
        )
        self.assertIn("xar_mcp_take_snapshot = {", effects)
        self.assertIn("value = flag:$REQUEST_ID$", effects)
        self.assertIn("[GetPlayer.GetID]", effects)
        self.assertIn("[GetCurrentDate.GetStringShort]", effects)
        self.assertIn("[GetCurrentDate.GetDateAsTotalDays]", effects)
        self.assertIn("XAR_MCP:ACK|schema=1", effects)
        executable = "\n".join(
            line for line in effects.splitlines() if not line.lstrip().startswith("#")
        )
        self.assertNotIn("every_character", executable)
        self.assertEqual(effects.count("{"), effects.count("}"))

    def test_default_inbox_is_noop(self) -> None:
        inbox = (ROOT / "templates" / "xar_mcp_inbox.txt").read_text(encoding="utf-8-sig")
        executable_lines = [
            line for line in inbox.splitlines() if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertEqual([], executable_lines)

    def test_fixture_parser_returns_only_complete_acknowledged_frame(self) -> None:
        fixture = (ROOT / "tests" / "fixtures" / "debug_snapshot.log").read_text(encoding="utf-8")
        frames = parse_complete_snapshots(fixture)
        self.assertEqual(1, len(frames))
        self.assertEqual("xar_req_000001", frames[0].request_id)
        self.assertEqual(4_294_967_297, frames[0].player_id)
        self.assertEqual("15 September, 1067", frames[0].date)
        self.assertEqual(389_742, frames[0].total_days)
        self.assertEqual("ok", frames[0].status)


if __name__ == "__main__":
    unittest.main()
