"""Root-only FIRST: consume saved R80 material through the registered MCP.

The captured world and original pending are real saved inputs. The endpoint,
process identity and baseline chooser are fixture seams; no game is called.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
from unittest.mock import patch

from test_construction_formal_private_consumer import Driver, frame
from xar_autoplayer.bridge import domain_construction_private_transport_v1 as transport
from xar_autoplayer.bridge import mcp_server
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.construction_formal_consumer import (
    RECEIPT_STEP, read_construction_ledger, write_construction_ledger,
)


def test_registered_r80_saved_material_mismatch_recovers_without_resubmit(tmp_path):
    from mcp import Client

    capture_path = Path(os.environ["XAR_R80_CONSTRUCTION_WORLD_CAPTURE"])
    pending_path = Path(os.environ["XAR_R80_CONSTRUCTION_PENDING_CAPTURE"])
    capture = json.loads(capture_path.read_text(encoding="utf-8-sig"))["result"]
    body = capture.get("structured_content") or capture.get("structuredContent")
    if body is None:
        body = json.loads(next(row["text"] for row in capture["content"]
                               if row.get("type") == "text"))
    original = json.loads(pending_path.read_text(encoding="utf-8-sig"))["pending"]
    assert original["candidate"]["building_type_id"] == 604
    assert original["candidate"]["slot_index"] == 3
    saved_original = deepcopy(original)
    source = body["source_frame"]
    actual_world = body["world"]
    snapshot = frame(source["native_revision"], episode=source["episode_run_id"],
                     public_revision=source["revision"])
    snapshot["date_raw"] = source["date_raw"]
    snapshot["played_character_gold"]["raw"] = actual_world["player_gold_raw"]
    snapshot["diagnostics"] = {"hello": {
        "expected_ck3_version": body["exact_ck3_build"],
        "expected_ck3_sha256": body["exe_sha256"],
    }}

    class SavedMaterialDriver(Driver):
        def wait_for_command_result(self, request_id, timeout):
            request = self.requests[-1]
            assert request["step"] == transport.QUERY_NATIVE
            assert request["expected_revision"] == source["native_revision"]
            return {"type": "command_result", "protocol_version": 1,
                    "request_id": request_id, "ok": True, "result": {
                        "step": transport.QUERY_NATIVE, "accepted": True,
                        "private_probe": {"advertised": False,
                            "snapshot_revision": source["native_revision"],
                            "date_raw": source["date_raw"],
                            "proof_epoch": body["proof_epoch"],
                            "player_world_building_sources": deepcopy(actual_world)}}}

    driver = SavedMaterialDriver(tmp_path / "private-fixture-state")
    driver.allow_private_construction_formal_trial = True
    driver.nonwar_only = False
    driver.snapshot = snapshot
    write_construction_ledger(driver.state_dir, {
        "schema": "xar.ck3.construction_formal_pending_v1",
        "pending": deepcopy(original), "applied": None, "applied_prior": [],
    })
    identity = (original["source_bridge_pid"], original["source_bridge_creation_date"])
    baseline = {"policy": "fixture-life", "phase": "life_advance",
                "selected_step": "life-advance"}

    async def run():
        with patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=baseline), \
                patch.object(transport, "_identity", return_value=identity), \
                patch("xar_autoplayer.bridge.service.construction_process_identity", return_value=identity), \
                patch.object(GameplayBridgeService, "auto_nonwar_turn", side_effect=AssertionError("normal path required")):
            async with Client(mcp_server.create_server(driver)) as client:
                result = await client.call_tool("ck3_auto_turn", {})
                assert not result.is_error, result.content
                output = result.structured_content
                assert output["selected_step"] == RECEIPT_STEP
                receipt = output["result"]
                assert receipt["status"] == "observed_mismatched_construction"
                assert receipt["postcondition_verified"] is False
                assert receipt["requested_postcondition_verified"] is False
                assert receipt["material_postcondition_verified"] is True
                assert receipt["candidate"] == original["candidate"]
                assert receipt["original_pending"] == saved_original
                assert receipt["observed_material_tuple"] == {
                    "barony_title_id": 2103, "province_id": 2635,
                    "building_type_id": 596, "slot_index": 1}
                assert receipt["original_quote_gold_debit_observed_raw"] == 14250000
                assert receipt["observed_slot_occupants"][0]["building_key"] == "farm_estates_02"
                assert receipt["actual_authored_monthly_income_delta_hundredths"] is None
                assert read_construction_ledger(driver.state_dir)["pending"] is None
                following = await client.call_tool("ck3_plan_turn", {})
                assert not following.is_error, following.content
                plan = following.structured_content["plan"]
                assert plan["selected_step"] == "life-advance"
                assert plan["construction_receipt_consumed"] == receipt
                economy = plan["construction_economic_outcome"]
                assert economy["phase"] == "observed_mismatched_construction"
                assert economy["authored_direct_monthly_income_delta_hundredths"] is None
                assert economy["material_completed"] is False
                assert economy["requested_construction_verified"] is False
                assert all(row["step"] == transport.QUERY_NATIVE for row in driver.requests)
                assert original == saved_original
                return receipt

    receipt = asyncio.run(run())
    output = os.environ.get("XAR_R80_CONSTRUCTION_RECOVERY_FIRST_OUTPUT")
    if output:
        Path(output).write_text(json.dumps({
            "schema": "xar.r80-construction-mismatch-registered-consumer.v1",
            "saved_world_capture": str(capture_path), "saved_pending_capture": str(pending_path),
            "receipt": receipt, "registered_mcp_calls": 2,
            "native_submits": 0, "game_calls": 0, "m4_credit": 0,
            "fixture_boundary": "actual saved material; synthetic outer endpoint/process/baseline",
        }, indent=2) + "\n", encoding="utf-8")
