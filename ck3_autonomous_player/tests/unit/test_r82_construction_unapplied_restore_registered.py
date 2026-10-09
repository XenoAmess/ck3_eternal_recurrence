"""Root-only FIRST of the actual R82 restored intent and material query.

Only outer endpoint/process lookup and the baseline chooser are fixture seams.
No original state is written, no game is called, and no native action is sent.
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


def test_registered_r82_saved_unapplied_intent_resolves_without_resubmit(tmp_path):
    from mcp import Client

    capture_path = Path(os.environ["XAR_R82_CONSTRUCTION_WORLD_CAPTURE"])
    ledger_path = Path(os.environ["XAR_R82_CONSTRUCTION_LEDGER_CAPTURE"])
    capture = json.loads(capture_path.read_text(encoding="utf-8-sig"))["result"]
    body = capture.get("structured_content") or capture.get("structuredContent")
    if body is None:
        body = json.loads(next(row["text"] for row in capture["content"]
                               if row.get("type") == "text"))
    ledger = json.loads(ledger_path.read_text(encoding="utf-8-sig"))
    original = deepcopy(ledger["pending"])
    first_applied = deepcopy(ledger["applied"])
    original_prior = deepcopy(ledger.get("applied_prior", []))
    assert original["action_request_id"] == "construction-submit-f085547b9f4e4817a6ee5b01a98629b5"
    assert original["pre_native_revision"] == 9 and original["pre_proof_epoch"] == 581228
    assert original["candidate"]["barony_title_id"] == 2106
    assert original["candidate"]["building_type_id"] == 604
    assert original["candidate"]["slot_index"] == 2
    assert first_applied["candidate"]["barony_title_id"] == 2103
    assert first_applied["post_bridge_pid"] == 175696
    source = body["source_frame"]
    actual_world = body["world"]
    assert source["native_revision"] == 2 and source["revision"] == 3
    assert source["date_raw"] == 53288592 and body["proof_epoch"] == 47307
    assert actual_world["player_gold_raw"] == 69417022
    assert actual_world["completed_buildings_observed"] is True
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

    driver = SavedMaterialDriver(tmp_path / "isolated-construction-state")
    driver.allow_private_construction_formal_trial = True
    driver.nonwar_only = False
    driver.snapshot = snapshot
    write_construction_ledger(driver.state_dir, deepcopy(ledger))
    identity = (143468, "20261009101637.326052+000")
    baseline = {"policy": "fixture-life", "phase": "life_advance",
                "selected_step": "life-advance"}

    async def run():
        with patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=baseline), \
                patch.object(transport, "_identity", return_value=identity), \
                patch("xar_autoplayer.bridge.service.construction_process_identity", return_value=identity), \
                patch("xar_autoplayer.m5_peacetime_proposal_sources_v1.construction_process_identity", return_value=identity), \
                patch.object(GameplayBridgeService, "auto_nonwar_turn", side_effect=AssertionError("normal path required")):
            async with Client(mcp_server.create_server(driver)) as client:
                result = await client.call_tool("ck3_auto_turn", {})
                assert not result.is_error, result.content
                output = result.structured_content
                assert output["selected_step"] == RECEIPT_STEP
                resolution = output["result"]
                assert resolution["status"] == "not_applied_after_restore"
                assert resolution["postcondition_verified"] is False
                assert resolution["requested_postcondition_verified"] is False
                assert resolution["material_postcondition_verified"] is False
                assert resolution["original_pending"] == original
                assert resolution["candidate"] == original["candidate"]
                assert resolution["post_native_revision"] == 2
                assert resolution["post_proof_epoch"] == 47307
                assert resolution["post_player_gold_raw"] == 69417022
                assert resolution["observed_target_holding"]["active"] is False
                assert resolution["m4_credit"] == 0
                resolved = read_construction_ledger(driver.state_dir)
                assert resolved["pending"] is None
                assert resolved["last_not_applied_resolution"] == resolution
                assert resolved["applied"] == first_applied
                assert resolved["applied_prior"] == original_prior
                # The old first construction still takes its own ordinary
                # cold material recheck before a normal progression plan.
                old_result = await client.call_tool("ck3_auto_turn", {})
                assert not old_result.is_error, old_result.content
                old_receipt = old_result.structured_content["result"]
                assert old_result.structured_content["selected_step"] == RECEIPT_STEP
                assert old_receipt["action_request_id"] == first_applied["action_request_id"]
                assert old_receipt["status"] == "applied"
                assert old_receipt["completion_status"] == "in_progress"
                assert old_receipt["construction_progress_observation"]["native_progress_divisor_raw"] == 0
                following = await client.call_tool("ck3_plan_turn", {})
                assert not following.is_error, following.content
                plan = following.structured_content["plan"]
                assert plan["selected_step"] == "life-advance"
                assert plan.get("phase") not in (
                    "construction_pending_receipt", "construction_cold_applied_requery")
                assert read_construction_ledger(driver.state_dir)["last_not_applied_resolution"] == resolution
                assert len(driver.requests) == 2
                assert all(row["step"] == transport.QUERY_NATIVE for row in driver.requests)
                assert driver.snapshot == snapshot
                return resolution, old_receipt, plan["selected_step"]

    resolution, old_receipt, next_step = asyncio.run(run())
    output_path = os.environ.get("XAR_R82_CONSTRUCTION_RECOVERY_FIRST_OUTPUT")
    if output_path:
        Path(output_path).write_text(json.dumps({
            "schema": "xar.r82-construction-unapplied-restore-registered.v1",
            "saved_world_capture": str(capture_path), "saved_ledger_capture": str(ledger_path),
            "resolution": resolution, "old_applied_recheck": old_receipt,
            "next_selected_step": next_step, "registered_mcp_calls": 3,
            "native_readonly_queries": 2, "native_submits": 0,
            "game_calls": 0, "m4_credit": 0,
            "fixture_boundary": "actual saved world and ledger; outer endpoint/process/baseline seams",
        }, indent=2) + "\n", encoding="utf-8")
