"""File and fake-MCP tests; never launch a server or contact a CK3 process."""

from __future__ import annotations

from contextlib import asynccontextmanager
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import sample_g2_12002_paused_readonly_sdk as sampler


ROOT = Path(__file__).resolve().parents[1]
TEMP_ROOT = ROOT / ".task-tmp" / "paused-readonly-sampler-tests"
TEMP_ROOT.mkdir(parents=True, exist_ok=True)


def plan() -> dict[str, object]:
    return {
        "schema": "xar.ck3.mcp-readonly-next-plan/v1",
        "executed": False, "formal_action_permits_enabled": False,
        "requires_real_restored_candidate_and_paused_frame": True,
        "argv": ["python", "-B", str(ROOT / "ck3_autonomous_player" / "mcp_server.py"),
                 "--driver", "native-headless", "--transport", "stdio",
                 *sorted(sampler.READ_FLAGS)],
    }


def options(*extra: str):
    return sampler.parser().parse_args(["--plan", "fixture-plan.json",
                                       "--artifacts", "fixture-artifacts", *extra])


class FakeMcpClient:
    def __init__(self, *, count=1, frame_change=None, error_tool=None):
        self.snapshot = {
            "snapshot_id": "fake-paused-101", "revision": 101,
            "native_revision": 41, "date_raw": 53220000,
            "played_character": {"character_id": 29829, "alive": True},
            "paused": True, "map_ready": True,
        }
        self.calls = []
        self.count = count
        self.frame_change = frame_change
        self.error_tool = error_tool
        self.initialized = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    async def initialize(self):
        self.initialized = True
        return {"protocolVersion": "fixture", "serverInfo": {"name": "fake"}}

    async def list_tools(self):
        return {"tools": [{"name": name} for name in (
            sampler.OBSERVATION_TOOL, sampler.ROOT_TOOL,
            *(tool for _, tool in sampler.DOMAIN_TOOLS),
        )]}

    async def call_tool(self, name, arguments):
        self.calls.append((name, deepcopy(arguments)))
        if name == sampler.OBSERVATION_TOOL:
            value = deepcopy(self.snapshot)
        elif name == sampler.ROOT_TOOL:
            value = {"status": "available", "campaign_root_context": {
                "snapshot_revision": self.snapshot["native_revision"],
                "date_raw": self.snapshot["date_raw"], "player_character_id": 29829,
                "government": {"key": "feudal_government"},
                "player_targeting_faction_count": self.count,
            }}
        else:
            value = {"schema": "fake-domain-read", "status": "available", "tool": name}
        if name == sampler.DOMAIN_TOOLS[0][1] and self.frame_change is not None:
            self.snapshot.update(self.frame_change)
        if name == self.error_tool:
            return {"isError": True, "content": [{"type": "text", "text": "native source unavailable"}]}
        return {"isError": False, "structuredContent": value, "content": []}


class SamplerFileTests(unittest.TestCase):
    def test_default_cli_consumes_plan_and_writes_files_without_starting_sdk(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temporary:
            directory = Path(temporary)
            input_plan = directory / "MCP-READONLY-NEXT-PLAN.json"
            input_plan.write_text(json.dumps(plan()), encoding="utf-8")
            with patch.object(sampler, "execute_stdio_plan", side_effect=AssertionError("server started")):
                code = sampler.main(["--plan", str(input_plan), "--artifacts", str(directory / "output")])
            self.assertEqual(code, 0)
            manifest = next((directory / "output").glob("sample-*/sampling-plan.json"))
            saved = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertIs(saved["executed"], False)
            self.assertEqual(len(saved["queries"]), 8)
            self.assertEqual(saved["formal_action_calls"], 0)

    def test_action_flag_plan_is_not_a_readonly_sampler_input(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temporary:
            path = Path(temporary) / "plan.json"
            value = plan()
            value["argv"].append("--private-faction-gift-action")
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "eight nonwar private read flags"):
                sampler.load_readonly_plan(path)


class SamplerFakeMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_all_eight_fixed_domains_use_real_observed_revision_and_root(self):
        client = FakeMcpClient()
        configured = options("--family-subject-character-id", "38822",
                             "--family-candidate-character-id", "38718",
                             "--sway-target-character-id", "37909")
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temporary:
            result = await sampler.sample_paused_readonly(
                client, artifacts=Path(temporary), options=configured, transport="fake-mcp",
            )
            self.assertEqual(result["status"], "sampled")
            self.assertEqual([row["status"] for row in result["domains"]], ["captured"] * 8)
            queries = [(name, arguments) for name, arguments in client.calls if name in dict(sampler.DOMAIN_TOOLS).values()]
            self.assertEqual([name for name, _ in queries], [name for _, name in sampler.DOMAIN_TOOLS])
            self.assertTrue(all(arguments["expected_revision"] == 101 for _, arguments in queries))
            gift = queries[-1][1]
            self.assertEqual(gift["same_frame_root"]["snapshot_revision"], 41)
            self.assertEqual(gift["same_frame_root"]["player_targeting_faction_count"], 1)
            self.assertEqual(gift["minimum_gold_reserve_raw"], 10_000_000)
            self.assertEqual(result["formal_action_calls"], 0)
            self.assertEqual(len(list(Path(temporary).glob("*.json"))), len(result["calls"]) + 2)

    async def test_unknown_ids_and_native_known_empty_factions_are_explicitly_skipped(self):
        client = FakeMcpClient(count=0)
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temporary:
            result = await sampler.sample_paused_readonly(
                client, artifacts=Path(temporary), options=options(), transport="fake-mcp",
            )
        records = {row["domain"]: row for row in result["domains"]}
        self.assertEqual(records["family"]["reason"], "explicit_family_subject_and_candidate_ids_required")
        self.assertEqual(records["sway"]["reason"], "explicit_sway_target_id_required")
        self.assertEqual(records["gift"]["reason"], "native_targeting_factions_known_empty")
        names = {name for name, _ in client.calls}
        for domain in ("family", "sway", "gift"):
            self.assertNotIn(dict(sampler.DOMAIN_TOOLS)[domain], names)

    async def test_paused_actor_or_date_change_stops_before_any_next_domain(self):
        for change in (
            {"paused": False}, {"date_raw": 53220001},
            {"played_character": {"character_id": 38822, "alive": True}},
        ):
            with self.subTest(change=change), tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temporary:
                client = FakeMcpClient(frame_change=change)
                result = await sampler.sample_paused_readonly(
                    client, artifacts=Path(temporary), options=options(), transport="fake-mcp",
                )
                self.assertEqual(result["status"], "stopped")
                self.assertEqual([row["domain"] for row in result["domains"]], ["government"])
                self.assertTrue(result["stop_reason"])
                self.assertEqual([name for name, _ in client.calls if name != sampler.OBSERVATION_TOOL],
                                 [sampler.DOMAIN_TOOLS[0][1]])

    async def test_native_query_error_packet_is_retained_and_other_same_frame_reads_continue(self):
        failed_tool = dict(sampler.DOMAIN_TOOLS)["prisoner"]
        client = FakeMcpClient(error_tool=failed_tool)
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temporary:
            directory = Path(temporary)
            result = await sampler.sample_paused_readonly(
                client, artifacts=directory, options=options(), transport="fake-mcp",
            )
            self.assertEqual(result["status"], "sampled_with_query_errors")
            record = next(row for row in result["calls"] if row["tool"] == failed_tool)
            packet = json.loads((directory / record["packet_file"]).read_text(encoding="utf-8"))
            self.assertIs(packet["packet"]["isError"], True)
            self.assertEqual(packet["packet"]["content"][0]["text"], "native source unavailable")
            self.assertIn(dict(sampler.DOMAIN_TOOLS)["feast"], {name for name, _ in client.calls})

    @unittest.skipIf(importlib.util.find_spec("mcp") is None, "optional MCP SDK not installed")
    async def test_actual_sdk_stdio_parameters_and_session_entry_are_mocked_without_server(self):
        client = FakeMcpClient(count=0)
        captured = []

        @asynccontextmanager
        async def fake_stdio(parameters, *, errlog):
            captured.append(parameters)
            self.assertIsNotNone(errlog)
            yield object(), object()

        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temporary:
            with patch("mcp.stdio_client", fake_stdio), patch("mcp.ClientSession", return_value=client):
                result = await sampler.execute_stdio_plan(
                    plan(), artifacts=Path(temporary), options=options(),
                )
        self.assertTrue(client.initialized)
        self.assertEqual(result["status"], "sampled")
        self.assertEqual(captured[0].command, "python")
        self.assertEqual(captured[0].args, plan()["argv"][1:])
        self.assertEqual(Path(captured[0].cwd), ROOT / "ck3_autonomous_player")


if __name__ == "__main__":
    unittest.main()
