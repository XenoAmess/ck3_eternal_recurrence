"""The bounded MCP sequence observes opportunity without submitting a war."""

from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path
import stat
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


SCRIPT = (Path(__file__).resolve().parents[2] / "native_bridge" / "research"
          / "run_war_opportunity_readback.py")
spec = importlib.util.spec_from_file_location("war_opportunity_readback", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def snapshot(history: list[dict[str, object]]) -> dict[str, object]:
    return {
        "paused": True, "map_ready": True, "snapshot_id": "native:4",
        "revision": 5, "native_revision": 4, "date_raw": 53144328,
        "episode_run_id": "native-test", "episode_character_id": 29829,
        "played_character": {"character_id": 29829, "alive": True},
        "native_command_history": history,
    }


class Client:
    def __init__(self, server: object, targets: list[int],
                 unsafe: bool = False) -> None:
        del server
        self.targets = targets
        self.unsafe = unsafe
        self.history: list[dict[str, object]] = []
        self.calls: list[str] = []

    async def __aenter__(self) -> "Client":
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def list_tools(self) -> SimpleNamespace:
        return SimpleNamespace(tools=[SimpleNamespace(name=n) for n in (
            "ck3_take_snapshot", "ck3_get_capabilities",
            "ck3_query_campaign_root_context_v1", "ck3_query_declarable_wars",
            "ck3_query_war_entry_assessments")])

    async def call_tool(self, name: str, args: dict[str, object]) -> SimpleNamespace:
        self.calls.append(name)
        if name == "ck3_get_capabilities":
            value = {"diagnostics": {"hello": {
                "game_adapter_id": "ck3-1.19.0.6-msvc-x64",
                "game_adapter_status": "ready", "ck3_build_match": True,
                "expected_ck3_sha256": module.EXE_SHA256}}}
        elif name == "ck3_take_snapshot":
            value = snapshot(list(self.history))
        elif name == "ck3_query_campaign_root_context_v1":
            self.history.append({"command": "query-campaign-root-context-v1", "ok": True})
            value = {"status": "available", "player_character_id": 29829,
                     "queried_snapshot_id": "native:4",
                     "queried_revision": args["expected_revision"]}
        elif name == "ck3_query_declarable_wars":
            self.history.append({"command": "query-declarable-wars", "ok": True})
            value = {"query_sequence": 2, "declarable_wars": [
                {"target_character_id": target, "declaration_id": str(target)}
                for target in self.targets]}
        else:
            target = args["target_character_ids"][0]
            command = ("declare-war-unsafe" if self.unsafe else
                       f"query-war-entry-assessments-v1-1-{target}")
            self.history.append({"command": command, "ok": True})
            value = {"status": "available", "target_character_ids": [target],
                     "queried_snapshot_id": "native:4", "queried_revision": 5}
        return SimpleNamespace(is_error=False, structured_content=value, content=[])


class WarOpportunityReadbackTests(unittest.TestCase):
    def run_frame(self, targets: list[int], *, limit: int = 8,
                  unsafe: bool = False) -> dict[str, object]:
        client = Client(None, targets, unsafe)
        with patch.dict(sys.modules, {"mcp": SimpleNamespace(Client=lambda server: client)}), \
             patch.object(module, "create_server", return_value=object()):
            return asyncio.run(module.query_frame(object(), 29829, 53144328, limit))

    def test_empty_query_proves_observed_no_legal_target(self) -> None:
        result = self.run_frame([])
        self.assertEqual(result["status"], "green")
        self.assertEqual(result["war_entry_assessments"], [])
        self.assertIn("ck3_query_declarable_wars", result["mcp_calls"])
        self.assertEqual(result["gameplay_actions"], 0)

    def test_legal_targets_are_assessed_without_declaration(self) -> None:
        result = self.run_frame([31050, 30097])
        self.assertEqual(result["status"], "green")
        self.assertEqual([r["target_character_ids"] for r in
                          result["war_entry_assessments"]], [[31050], [30097]])
        self.assertTrue(all("declare-war" not in command for command in
                            result["native_commands"]))

    def test_bound_and_unexpected_mutation_are_visible(self) -> None:
        result = self.run_frame([31050, 30097], limit=1)
        self.assertEqual(result["status"], "green_partial")
        self.assertFalse(result["scope_complete"])
        with self.assertRaisesRegex(RuntimeError, "unexpected native command"):
            self.run_frame([31050], unsafe=True)

    def test_frozen_source_copy_is_writable_without_changing_source(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / "frozen.json"
            target = Path(root) / "candidate.json"
            source.write_bytes(b'{"format_version": 2}\n')
            source.chmod(stat.S_IREAD)
            try:
                module.copy_frozen_bytes_to_candidate(source, target)
                self.assertEqual(target.read_bytes(), source.read_bytes())
                self.assertFalse(source.stat().st_mode & stat.S_IWRITE)
                self.assertTrue(target.stat().st_mode & stat.S_IWRITE)
            finally:
                source.chmod(source.stat().st_mode | stat.S_IWRITE)


if __name__ == "__main__":
    unittest.main()
