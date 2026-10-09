"""Root-only registered FIRST for the two real R81 cold-query receipts.

Receipt material, revisions, dates and raw creation strings are actual saved
inputs. Endpoint/process lookup and the baseline LIFE chooser are fixture
seams. No command is sent and no snapshot revision is invented or advanced.
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
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.construction_formal_consumer import (
    RECEIPT_STEP, plan_construction_private, priority_construction_receipt,
    read_construction_ledger, same_construction_process_identity,
    write_construction_ledger,
)


def test_registered_r81_actual_creation_encodings_stop_repeated_cold_query(tmp_path):
    from mcp import Client

    capture_dir = Path(os.environ["XAR_R81_CONSTRUCTION_COLD_CAPTURE_DIR"])
    utc = "20261009043752.997404+000"
    local = "20261009123752.997404+480"
    scenarios = [("002-r81-bomfixed-normal-turn01.json", local, utc),
                 ("003-r81-bomfixed-normal-turn02.json", utc, local)]
    records = []
    baseline = {"policy": "fixture-normal-life", "phase": "life_advance",
                "selected_step": "life-advance"}

    async def run():
        for index, (name, saved_creation, current_creation) in enumerate(scenarios):
            saved = json.loads((capture_dir / name).read_text(encoding="utf-8-sig"))["result"]
            body = saved.get("structured_content") or saved.get("structuredContent")
            if body is None:
                body = json.loads(next(row["text"] for row in saved["content"]
                                       if row.get("type") == "text"))
            receipt = deepcopy(body["result"])
            assert body["plan"]["phase"] == "construction_cold_applied_requery"
            assert receipt["status"] == "applied" and receipt["postcondition_verified"] is True
            assert receipt["post_bridge_pid"] == 175696
            assert receipt["post_bridge_creation_date"] == saved_creation
            assert receipt["post_native_revision"] == 5 and receipt["post_date_raw"] == 53288568
            raw_start = deepcopy(receipt["start_receipt"])
            assert (175696, saved_creation) != (175696, current_creation)
            assert same_construction_process_identity(
                (175696, saved_creation), (175696, current_creation))
            driver = Driver(tmp_path / str(index))
            driver.allow_private_construction_formal_trial = True
            driver.nonwar_only = False
            driver.snapshot = frame(receipt["post_native_revision"],
                episode=receipt["episode_run_id"],
                public_revision=receipt["post_public_revision"])
            driver.snapshot["date_raw"] = receipt["post_date_raw"]
            driver.snapshot["played_character_gold"]["raw"] = receipt["post_player_gold_raw"]
            driver.snapshot["diagnostics"] = {"hello": {
                "expected_ck3_version": CK3_12004.game_version,
                "expected_ck3_sha256": CK3_12004.executable_sha256}}
            ledger = {"schema": "xar.ck3.construction_formal_pending_v1",
                      "pending": None, "applied": deepcopy(receipt), "applied_prior": []}
            write_construction_ledger(driver.state_dir, ledger)
            identity = (175696, current_creation)
            with patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=baseline), \
                    patch.object(transport, "_identity", return_value=identity), \
                    patch("xar_autoplayer.bridge.service.construction_process_identity", return_value=identity), \
                    patch("xar_autoplayer.m5_peacetime_proposal_sources_v1.construction_process_identity", return_value=identity):
                snapshot = driver.take_snapshot()
                assert priority_construction_receipt(driver, ledger, snapshot) is None
                async with Client(mcp_server.create_server(driver)) as client:
                    for _ in range(2):
                        observed = await client.call_tool("ck3_plan_turn", {})
                        assert not observed.is_error, observed.content
                        plan = observed.structured_content["plan"]
                        assert plan["selected_step"] == "life-advance"
                        assert plan.get("phase") != "construction_cold_applied_requery"
                        assert plan["construction_receipt_consumed"] == receipt
                assert not driver.requests
                assert read_construction_ledger(driver.state_dir)["applied"] == receipt
                assert receipt["start_receipt"] == raw_start
                # Preserve the original cold/checkpoint behavior for a truly
                # different creation instant, PID, or actual older frame.
                different = (175696, "20261009043753.997404+000")
                assert priority_construction_receipt(
                    driver, ledger, snapshot, process_identity=different) == receipt
                assert priority_construction_receipt(
                    driver, ledger, snapshot, process_identity=(175697, current_creation)) == receipt
                older = {**snapshot, "native_revision": receipt["post_native_revision"] - 1}
                assert priority_construction_receipt(
                    driver, ledger, older, process_identity=identity) == receipt
            records.append({"capture": name, "saved_creation": saved_creation,
                            "compared_creation": current_creation,
                            "material_receipt_and_start_unchanged": True,
                            "following_selected_step": "life-advance"})

    asyncio.run(run())
    output = os.environ.get("XAR_R81_CONSTRUCTION_CREATION_FIRST_OUTPUT")
    if output:
        Path(output).write_text(json.dumps({
            "schema": "xar.r81-construction-creation-time-registered.v1",
            "capture_dir": str(capture_dir), "scenarios": records,
            "registered_plan_calls": 4, "native_requests": 0,
            "revisions_changed": False, "date_advanced": False,
            "Game_calls": 0, "capability_credit": 0,
            "fixture_seams": ["outer process lookup", "baseline chooser", "outer snapshot carrier"],
        }, indent=2) + "\n", encoding="utf-8")
