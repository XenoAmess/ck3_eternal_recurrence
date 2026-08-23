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

    def test_snapshot_effect_projects_committed_one_life_settlement(self) -> None:
        effects = (ROOT / "common" / "scripted_effects" / "xar_mcp_bridge_effects.txt").read_text(
            encoding="utf-8-sig"
        )
        self.assertIn("xar_mcp_take_snapshot = {", effects)
        self.assertIn("value = flag:$REQUEST_ID$", effects)
        self.assertIn("[GetPlayer.GetID]", effects)
        self.assertIn("[GetCurrentDate.GetStringShort]", effects)
        self.assertIn("[GetCurrentDate.GetDateAsTotalDays]", effects)
        self.assertIn("global_var:xa_settlement_ready = 1", effects)
        self.assertIn("XAR_MCP:SETTLEMENT|ready=1", effects)
        self.assertIn(
            "source_character_id=[GetGlobalVariable("
            "'xa_settlement_source_character').Char.GetID]",
            effects,
        )
        for field in (
            "commit_serial",
            "final_score",
            "score_before_reject",
            "record_candidate",
            "old_record",
            "record_delta",
            "blessing_count",
            "refusal_count",
            "contract_progress",
            "record_written",
        ):
            with self.subTest(field=field):
                self.assertIn(f"|{field}=", effects)
        self.assertIn("XAR_MCP:SETTLEMENT|ready=0|commit_serial=0", effects)
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
        self.assertIsNone(frames[0].one_life_settlement)

    def test_fixture_parser_returns_complete_settlement_payload(self) -> None:
        fixture = (
            ROOT / "tests" / "fixtures" / "debug_snapshot_settlement.log"
        ).read_text(encoding="utf-8")
        frames = parse_complete_snapshots(fixture)
        self.assertEqual(1, len(frames))
        settlement = frames[0].one_life_settlement
        self.assertIsNotNone(settlement)
        assert settlement is not None
        self.assertTrue(settlement.ready)
        self.assertEqual(1, settlement.commit_serial)
        self.assertEqual(4_294_967_297, settlement.source_character_id)
        self.assertEqual(284.625, settlement.final_score)
        self.assertEqual(287.5, settlement.score_before_reject)
        self.assertEqual(284, settlement.record_candidate)
        self.assertEqual(250, settlement.old_record)
        self.assertEqual(34, settlement.record_delta)
        self.assertEqual(7, settlement.blessing_count)
        self.assertEqual(1, settlement.refusal_count)
        self.assertEqual(9, settlement.contract_progress)
        self.assertTrue(settlement.record_written)

    def test_unpublished_settlement_and_malformed_extension_keep_base_frame(self) -> None:
        prefix = (
            "XAR_MCP:BEGIN|schema=1|kind=snapshot|request_id={request_id}\n"
            "XAR_MCP:STATE|player_id=17|date=1 January, 1067|total_days=389485\n"
        )
        suffix = (
            "XAR_MCP:ACK|schema=1|request_id={request_id}|"
            "command=take_snapshot|status=ok\n"
            "XAR_MCP:END|schema=1|request_id={request_id}\n"
        )
        unpublished_id = "xar_req_unpublished"
        malformed_id = "xar_req_malformed"
        text = (
            prefix.format(request_id=unpublished_id)
            + "XAR_MCP:SETTLEMENT|ready=0|commit_serial=0\n"
            + suffix.format(request_id=unpublished_id)
            + prefix.format(request_id=malformed_id)
            + "XAR_MCP:SETTLEMENT|ready=1|commit_serial=1|final_score=bad\n"
            + suffix.format(request_id=malformed_id)
        )

        frames = parse_complete_snapshots(text)

        self.assertEqual(2, len(frames))
        unpublished = frames[0].one_life_settlement
        self.assertIsNotNone(unpublished)
        assert unpublished is not None
        self.assertFalse(unpublished.ready)
        self.assertEqual(0, unpublished.commit_serial)
        self.assertIsNone(unpublished.final_score)
        self.assertIsNone(frames[1].one_life_settlement)


if __name__ == "__main__":
    unittest.main()
