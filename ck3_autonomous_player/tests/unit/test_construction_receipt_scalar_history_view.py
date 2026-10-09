"""One Root FIRST for receipt income sampled without full history export.

Reuse only helpers and saved small inputs; no old test or producer executes.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
from unittest.mock import patch

from test_construction_receipt_query_context_history import _SavedWorldEndpoint, frame
from xar_autoplayer.bridge import domain_construction_private_transport_v1 as transport
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.construction_formal_consumer import (
    RECEIPT_STEP, ROOT_QUERY_STEP, read_construction_ledger, write_construction_ledger,
)


def test_registered_receipts_sample_starting_income_without_full_history_export(tmp_path):
    world_path = Path(os.environ["XAR_R82_CONSTRUCTION_WORLD_CAPTURE"])
    ledger_path = Path(os.environ["XAR_R82_CONSTRUCTION_LEDGER_CAPTURE"])
    capture = json.loads(world_path.read_text(encoding="utf-8-sig"))["result"]
    body = capture.get("structured_content") or capture.get("structuredContent")
    if body is None:
        body = json.loads(next(row["text"] for row in capture["content"]
                               if row.get("type") == "text"))
    ledger = json.loads(ledger_path.read_text(encoding="utf-8-sig"))
    pending, applied = deepcopy(ledger["pending"]), deepcopy(ledger["applied"])
    source = body["source_frame"]
    world = body["world"]
    snapshot = frame(source["native_revision"], episode=source["episode_run_id"],
                     public_revision=source["revision"])
    snapshot["date_raw"] = source["date_raw"]
    snapshot["played_character_gold"]["raw"] = world["player_gold_raw"]
    snapshot["diagnostics"] = {"hello": {
        "expected_ck3_version": body["exact_ck3_build"],
        "expected_ck3_sha256": body["exe_sha256"],
    }}
    initial_income, later_income = 1_234_567, 2_345_678

    def root_result(income):
        return {"campaign_root_context": {
            "status": "available", "snapshot_revision": source["native_revision"],
            "date_raw": source["date_raw"], "player_character_id": 29829,
            "player_monthly_gold_income": {"raw": income, "scale": 100_000},
        }}

    old_history = [{
        "index": index, "command": "query-synthetic-observation", "ok": True,
        "result": {"ordered_rows": [{"z": index, "a": None}],
                   "pending": {"status": "action_state_unknown", "ack": None}},
    } for index in range(1, 8)]
    old_history.append({"index": 8, "command": ROOT_QUERY_STEP, "ok": True,
                        "result": root_result(initial_income)})

    class LaterSameFrameRootEndpoint(_SavedWorldEndpoint):
        def send(self, request):
            if len(self.requests) == 1:
                # A new same-frame root arrives during the applied material
                # query. The receipt must retain its earlier sampled value.
                driver._record_command(ROOT_QUERY_STEP, ok=True,
                                       result=root_result(later_income))
            super().send(request)

    endpoint = LaterSameFrameRootEndpoint(source, world, body["proof_epoch"])
    state_dir = tmp_path / "synthetic-driver-state"
    driver = NativeHeadlessGameplayDriver(
        endpoint.pipe_name, endpoint=endpoint, state_dir=state_dir,
        command_timeout_seconds=1.0, episode_projection="native_campaign")
    driver.allow_private_construction_formal_trial = True
    identity = (143468, "20261009101637.326052+000")
    with driver._driver_state_lock:
        driver._session_bridge_pid = identity[0]
        driver._episode_character_id = 29829
        driver._episode_run_id = source["episode_run_id"]
        driver._command_history = deepcopy(old_history)
    write_construction_ledger(state_dir, deepcopy(ledger))
    outputs = []

    async def run():
        server = create_server(driver)
        with (
            patch.object(driver, "take_internal_semantic_snapshot", side_effect=lambda: deepcopy(snapshot)),
            patch.object(transport, "_identity", return_value=identity),
            patch.object(driver, "_history_snapshot", wraps=driver._history_snapshot) as copies,
            patch.object(driver, "_with_internal_planning_view", wraps=driver._with_internal_planning_view) as views,
            patch.object(driver, "_persist_driver_state", wraps=driver._persist_driver_state) as writes,
            patch.object(transport, "same_frame_construction_income", wraps=transport.same_frame_construction_income) as incomes,
        ):
            for index, retained in enumerate((pending, applied), 1):
                planned = {
                    "snapshot_id": snapshot["snapshot_id"], "revision": source["revision"],
                    "plan": {"phase": "synthetic-selected-construction-receipt",
                             "selected_step": RECEIPT_STEP,
                             "construction_pending_action": deepcopy(retained)},
                }
                with patch.object(GameplayBridgeService, "plan_turn", return_value=planned):
                    registered = await server.call_tool("ck3_auto_turn", {})
                assert not registered.is_error, registered.content
                result = registered.structured_content
                assert result["selected_step"] == RECEIPT_STEP
                outputs.append(result["result"])
                assert copies.call_count == 0
                assert views.call_count == index
                assert incomes.call_count == index
                assert incomes.call_args.args[1] is driver._command_history
                assert writes.call_count == index
                assert len(endpoint.requests) == index
                assert driver._command_history[:8] == old_history
                durable = json.loads((state_dir / "native-session/driver-state.json")
                                     .read_text(encoding="utf-8"))
                assert durable["command_history"] == driver._command_history
                assert durable["command_history"][:8] == old_history
                assert len(durable["command_history"]) == (9 if index == 1 else 11)
            public = driver.take_snapshot()
            assert copies.call_count == 1
            assert len(public["native_command_history"]) == 11
            public["native_command_history"][0]["result"]["ordered_rows"][0]["z"] = -1
            assert driver._command_history[0] == old_history[0]

    try:
        asyncio.run(run())
        resolution, old_receipt = outputs
        assert resolution["status"] == "not_applied_after_restore"
        assert resolution["original_pending"] == pending
        assert resolution["postcondition_verified"] is False
        assert resolution["new_native_submit_calls"] == 0 and resolution["m4_credit"] == 0
        assert old_receipt["status"] == "applied" and old_receipt["completion_status"] == "in_progress"
        assert old_receipt["observed_player_monthly_gold_income_raw"] == initial_income
        assert transport.same_frame_construction_income(snapshot, driver._command_history) == (True, later_income)
        assert driver._command_history[-2]["command"] == ROOT_QUERY_STEP
        assert driver._command_history[-2]["result"] == root_result(later_income)
        assert driver._command_history[-1]["command"] == RECEIPT_STEP
        current = read_construction_ledger(state_dir)
        assert current["pending"] is None and current["last_not_applied_resolution"] == resolution
        assert current["applied"]["action_request_id"] == applied["action_request_id"]
        assert current.get("applied_prior", []) == ledger.get("applied_prior", [])
        assert all(row["step"] == transport.QUERY_NATIVE for row in endpoint.requests)
        output_path = os.environ.get("XAR_CONSTRUCTION_RECEIPT_SCALAR_FIRST_OUTPUT")
        if output_path:
            Path(output_path).write_text(json.dumps({
                "schema": "xar.construction-receipt-scalar-history-first.v1", "status": "GREEN",
                "world_capture": str(world_path), "ledger_capture": str(ledger_path),
                "registered_auto_turn_calls": 2, "native_readonly_queries": 2,
                "full_history_exports_during_receipts": 0, "locked_scalar_history_reads": 2,
                "durable_full_history_writes": 2, "durable_history_entries": 11,
                "initial_income_preserved_raw": initial_income, "later_same_frame_income_raw": later_income,
                "public_default_complete_detached_history": True,
                "native_submits": 0, "game_calls": 0, "live_speedup_measured": False,
                "resolution": resolution, "old_applied_receipt": old_receipt,
                "fixture_boundary": "saved small world/ledger; synthetic selected plan/frame/endpoint/process and later root query",
            }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    finally:
        driver.close()
