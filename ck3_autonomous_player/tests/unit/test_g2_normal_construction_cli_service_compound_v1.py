"""One Root-only registered compound for existing construction CLI wiring.

Construction policy/transport/ledger are real. The outer game I/O fixture,
stdio lifetime, process identity and baseline chooser are explicit seams;
hello/current-date edits are synthetic and do not qualify native or live data.
"""
import asyncio
import copy
import json
import os
from pathlib import Path
from unittest.mock import patch

from test_construction_formal_private_consumer import Driver, frame, root
from xar_autoplayer.bridge import mcp_server
from xar_autoplayer.bridge import domain_construction_private_transport_v1 as transport
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.construction_formal_consumer import (
    RECEIPT_STEP, SUBMIT_STEP, read_construction_ledger,
)


class NormalConstructionFixtureDriver(Driver):
    def __init__(self, state_dir):
        super().__init__(state_dir)
        self.allow_private_construction_formal_trial = False
        self.nonwar_only = False
        self.snapshot = self.current_frame(3)
        current_root = root(3)[0]["result"]
        current_root["campaign_root_context"]["date_raw"] = self.snapshot["date_raw"]
        self.recorded = [("query-campaign-root-context-v1", current_root)]

    @staticmethod
    def current_frame(revision):
        value = frame(revision, episode="source-fixture-normal-construction-cli12004")
        value["date_raw"] = 53288472
        value["diagnostics"] = {"hello": {
            "expected_ck3_version": CK3_12004.game_version,
            "expected_ck3_sha256": CK3_12004.executable_sha256,
        }}
        if revision >= 4:
            value["played_character_gold"]["raw"] = 35000000
        return value


def test_registered_normal_construction_cli_submit_material_following_empty_and_war(tmp_path):
    from mcp import Client
    from mcp.server import MCPServer

    baseline = {"policy": "normal-baseline-fixture", "phase": "life_advance", "selected_step": "life-advance"}
    records = []

    def create_configured(scene, *, enabled, empty=False, war=False):
        directory = tmp_path / scene
        captured, loaded = [], []

        def load_fixture(driver_name, **kwargs):
            assert driver_name == "native-headless"
            assert kwargs["state_dir"] == directory
            driver = NormalConstructionFixtureDriver(directory)
            driver.no_positive_building = empty
            if war:
                driver.snapshot["active_wars"] = [{"war_id": 16777231}]
                driver.capabilities = lambda: {"action_steps": ["query-army-strengths-v1"], "bridge_capabilities": []}
            loaded.append(driver)
            return driver

        def capture_run(server, **kwargs):
            assert kwargs == {"transport": "stdio"}
            assert loaded[0].allow_private_construction_formal_trial is enabled
            assert loaded[0].nonwar_only is False
            captured.append(server)

        argv = ["--driver", "native-headless", "--transport", "stdio", "--state-dir", str(directory)]
        if enabled:
            argv.append("--allow-private-construction-formal-trial")
        with patch.object(mcp_server, "load_driver", side_effect=load_fixture) as factory, \
                patch.object(MCPServer, "run", new=capture_run):
            assert mcp_server.main(argv) == 0
        assert factory.call_count == 1 and len(captured) == 1
        return captured[0], loaded[0], argv

    async def run():
        with patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=baseline), \
                patch.object(GameplayBridgeService, "plan_nonwar_turn", side_effect=AssertionError("normal MCP must not use nonwar planner")), \
                patch.object(GameplayBridgeService, "auto_nonwar_turn", side_effect=AssertionError("normal MCP must not use nonwar executor")), \
                patch.object(transport, "_identity", return_value=(881, "fixture-construction12004")), \
                patch("xar_autoplayer.bridge.service.construction_process_identity", return_value=(881, "fixture-construction12004")):
            server, disabled, argv = create_configured("default-off", enabled=False)
            async with Client(server) as client:
                observed = await client.call_tool("ck3_plan_turn", {})
                assert not observed.is_error, observed.content
                assert observed.structured_content["plan"]["selected_step"] == "life-advance"
            assert not disabled.requests
            records.append({"scene": "default-off", "argv": argv, "configured": False, "native_requests": 0})

            server, driver, argv = create_configured("explicit-on", enabled=True)
            async with Client(server) as client:
                observed = await client.call_tool("ck3_plan_turn", {})
                assert not observed.is_error, observed.content
                selected = observed.structured_content["plan"]
                assert selected["selected_step"] == SUBMIT_STEP
                query = selected["construction_private_query"]
                assert query["exact_ck3_build"] == CK3_12004.game_version
                assert query["exe_sha256"] == CK3_12004.executable_sha256
                assert query["candidate"]["stock_gold_cost_raw"] == 15000000
                assert query["candidate"]["province_id"] == 2635
                assert not any(row["step"] == transport.ACTION_NATIVE for row in driver.requests)
                submitted = await client.call_tool("ck3_auto_turn", {})
                assert not submitted.is_error, submitted.content
                assert submitted.structured_content["selected_step"] == SUBMIT_STEP
                assert submitted.structured_content["result"]["status"] == "submitted_verification_pending"
                pending = read_construction_ledger(driver.state_dir)["pending"]
                assert pending["pre_native_revision"] == 3
                assert sum(row["step"] == transport.ACTION_NATIVE for row in driver.requests) == 1

                # The reply fixture's independent active tuple and reduced
                # native gold are only supplied at a separate later frame.
                driver.snapshot = driver.current_frame(4)
                applied = await client.call_tool("ck3_auto_turn", {})
                assert not applied.is_error, applied.content
                assert applied.structured_content["selected_step"] == RECEIPT_STEP
                material = applied.structured_content["result"]
                assert material["postcondition_verified"] is True
                assert material["post_player_gold_raw"] == 35000000
                assert material["candidate"]["province_id"] == 2635
                assert read_construction_ledger(driver.state_dir)["pending"] is None
                following = await client.call_tool("ck3_plan_turn", {})
                assert not following.is_error, following.content
                following_plan = following.structured_content["plan"]
                assert following_plan["selected_step"] == "life-advance"
                assert following_plan["construction_receipt_consumed"]["action_request_id"] == material["action_request_id"]
                assert sum(row["step"] == transport.ACTION_NATIVE for row in driver.requests) == 1
            records.append({"scene": "explicit-on", "argv": argv, "configured": True,
                "candidate": copy.deepcopy(query["candidate"]), "submit_count": 1,
                "material_postcondition_verified": True, "following_consumed": True})

            server, empty, argv = create_configured("no-positive-target", enabled=True, empty=True)
            async with Client(server) as client:
                observed = await client.call_tool("ck3_plan_turn", {})
                assert not observed.is_error, observed.content
                plan = observed.structured_content["plan"]
                assert plan["selected_step"] == "life-advance"
                assert plan["construction_private_query"]["status"] == "no_legal_budgeted_building"
                assert "candidate" not in plan["construction_private_query"]
            assert not any(row["step"] == transport.ACTION_NATIVE for row in empty.requests)
            records.append({"scene": "no-positive-target", "argv": argv, "configured": True,
                "status": "no_legal_budgeted_building", "submit_count": 0})

            server, war, argv = create_configured("selected-war-step", enabled=True, war=True)
            war_baseline = {"policy": "normal-war-fixture", "phase": "native_war_army_query", "selected_step": "query-army-strengths-v1"}
            with patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=war_baseline):
                async with Client(server) as client:
                    observed = await client.call_tool("ck3_plan_turn", {})
                    assert not observed.is_error, observed.content
                    assert observed.structured_content["plan"]["selected_step"] == "query-army-strengths-v1"
            assert not any(row["step"] == transport.ACTION_NATIVE for row in war.requests)
            assert war.snapshot["active_wars"] == [{"war_id": 16777231}]
            records.append({"scene": "selected-war-step", "argv": argv, "configured": True,
                "selected_step": "query-army-strengths-v1", "submit_count": 0})

    asyncio.run(run())
    output_path = os.environ.get("XAR_MCP_CONSTRUCTION_FORMAL_CLI_SERVICE_OUTPUT")
    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({
            "schema": "xar.normal-construction-cli-service-evidence12004.v1",
            "input_boundary": "source-shaped outer reply fixture and baseline chooser; real CLI and registered Service",
            "scene_count": len(records), "scenes": records,
            "native_observer_requalification": False, "game_action": False,
            "live": False, "m4_complete": False,
        }, indent=2) + "\n", encoding="utf-8")
