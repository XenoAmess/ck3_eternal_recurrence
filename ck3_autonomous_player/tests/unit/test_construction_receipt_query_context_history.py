"""One Root-only compound for the observed construction receipt query context.

Saved small world/ledger inputs are reused unchanged. Only the selected plan,
semantic frame, endpoint and process identity are synthetic fixture seams.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
from unittest.mock import patch

from test_construction_formal_private_consumer import frame
from xar_autoplayer.bridge import domain_construction_private_transport_v1 as transport
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.construction_formal_consumer import (
    RECEIPT_STEP, ROOT_QUERY_STEP, read_construction_ledger, write_construction_ledger,
)


class _SavedWorldEndpoint:
    pipe_name = r"\\.\pipe\xar-construction-receipt-context-history-fixture"

    def __init__(self, source, world, epoch):
        self.source = source
        self.world = world
        self.epoch = epoch
        self.requests = []
        self.on_frame = None

    def start(self, on_frame, on_disconnect):
        self.on_frame = on_frame

    def send(self, request):
        assert request["type"] == "execute_step"
        assert request["step"] == transport.QUERY_NATIVE
        assert request["expected_revision"] == self.source["native_revision"]
        self.requests.append(deepcopy(request))
        self.on_frame({
            "type": "command_result", "protocol_version": 1,
            "request_id": request["request_id"], "ok": True,
            "result": {
                "step": transport.QUERY_NATIVE, "accepted": True,
                "private_probe": {
                    "advertised": False,
                    "snapshot_revision": self.source["native_revision"],
                    "date_raw": self.source["date_raw"], "proof_epoch": self.epoch,
                    "player_world_building_sources": deepcopy(self.world),
                },
            },
        })

    def close(self):
        pass


def test_registered_receipts_omit_only_query_context_history_and_keep_durable_income(tmp_path):
    capture_path = Path(os.environ["XAR_R82_CONSTRUCTION_WORLD_CAPTURE"])
    ledger_path = Path(os.environ["XAR_R82_CONSTRUCTION_LEDGER_CAPTURE"])
    capture = json.loads(capture_path.read_text(encoding="utf-8-sig"))["result"]
    body = capture.get("structured_content") or capture.get("structuredContent")
    if body is None:
        body = json.loads(next(row["text"] for row in capture["content"]
                               if row.get("type") == "text"))
    ledger = json.loads(ledger_path.read_text(encoding="utf-8-sig"))
    pending = deepcopy(ledger["pending"])
    applied = deepcopy(ledger["applied"])
    prior = deepcopy(ledger.get("applied_prior", []))
    assert pending["action_request_id"] == "construction-submit-f085547b9f4e4817a6ee5b01a98629b5"
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
    identity = (143468, "20261009101637.326052+000")
    income_raw = 1_234_567
    old_history = [{
        "index": index, "command": "query-synthetic-ordered-history", "ok": True,
        "result": {"ordered_rows": [{"z": index, "a": None}],
                   "pending": {"status": "action_state_unknown", "ack": None}},
    } for index in range(1, 8)]
    old_history.append({
        "index": 8, "command": ROOT_QUERY_STEP, "ok": True,
        "result": {"campaign_root_context": {
            "status": "available", "snapshot_revision": source["native_revision"],
            "date_raw": source["date_raw"], "player_character_id": 29829,
            "player_monthly_gold_income": {"raw": income_raw, "scale": 100_000},
        }},
    })
    endpoint = _SavedWorldEndpoint(source, actual_world, body["proof_epoch"])
    state_dir = tmp_path / "synthetic-driver-state"
    driver = NativeHeadlessGameplayDriver(
        endpoint.pipe_name, endpoint=endpoint, state_dir=state_dir,
        command_timeout_seconds=1.0, episode_projection="native_campaign")
    driver.allow_private_construction_formal_trial = True
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
            patch.object(driver, "_persist_driver_state", wraps=driver._persist_driver_state) as writes,
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
                # The outer receipt retains the one history export needed by
                # applied income; the two world-query context reads omit it.
                assert copies.call_count == index
                assert writes.call_count == index
                assert len(endpoint.requests) == index
                assert driver._command_history[:8] == old_history
                durable = json.loads((state_dir / "native-session/driver-state.json")
                                     .read_text(encoding="utf-8"))
                assert durable["command_history"][:8] == old_history
                assert len(durable["command_history"]) == 8 + index
            public = driver.take_snapshot()
            assert copies.call_count == 3
            assert len(public["native_command_history"]) == 10
            public["native_command_history"][0]["result"]["ordered_rows"][0]["z"] = -1
            assert driver._command_history[0] == old_history[0]

    try:
        asyncio.run(run())
        resolution, old_receipt = outputs
        assert resolution["status"] == "not_applied_after_restore"
        assert resolution["original_pending"] == pending
        assert resolution["postcondition_verified"] is False
        assert resolution["material_postcondition_verified"] is False
        assert resolution["new_native_submit_calls"] == 0
        assert resolution["m4_credit"] == 0
        assert old_receipt["status"] == "applied"
        assert old_receipt["completion_status"] == "in_progress"
        assert old_receipt["observed_player_monthly_gold_income_raw"] == income_raw
        current = read_construction_ledger(state_dir)
        assert current["pending"] is None
        assert current["last_not_applied_resolution"] == resolution
        assert current["applied"]["action_request_id"] == applied["action_request_id"]
        assert current.get("applied_prior", []) == prior
        assert all(row["step"] == transport.QUERY_NATIVE for row in endpoint.requests)
        assert snapshot["date_raw"] == source["date_raw"]
        output_path = os.environ.get("XAR_CONSTRUCTION_QUERY_CONTEXT_FIRST_OUTPUT")
        if output_path:
            Path(output_path).write_text(json.dumps({
                "schema": "xar.construction-receipt-query-context-history-first.v1",
                "status": "GREEN", "world_capture": str(capture_path),
                "ledger_capture": str(ledger_path), "registered_auto_turn_calls": 2,
                "native_readonly_queries": 2, "native_submits": 0,
                "outer_history_exports": 2, "inner_query_history_exports": 0,
                "durable_full_history_writes": 2, "durable_history_entries": 10,
                "same_frame_applied_income_preserved_raw": income_raw,
                "resolution": resolution, "old_applied_receipt": old_receipt,
                "fixture_boundary": "saved small world/ledger, synthetic plan/frame/endpoint/process",
                "live_speedup_measured": False, "game_calls": 0,
            }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    finally:
        driver.close()
