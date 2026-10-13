"""One focused construction diagnostic consumer; all endpoint frames are synthetic."""
from __future__ import annotations

import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_construction_formal_private_consumer import Driver, frame
from xar_autoplayer.bridge import domain_construction_private_transport_v1 as transport
from xar_autoplayer.bridge import mcp_server
from xar_autoplayer.construction_formal_consumer import (
    read_construction_ledger,
    write_construction_ledger,
)


class ConstructionFailureDiagnosticRegisteredConsumerTest(unittest.TestCase):
    def test_registered_receipt_failure_retains_bounded_diagnostic_without_resubmit(self):
        from mcp import Client

        owner = self
        identity = (73001, "20261013020000.000000+000")
        pending = {
            "status": "submitted_verification_pending",
            "action_request_id": "construction-original-diagnostic-only",
            "episode_run_id": "native-29829-diagnostic-only",
            "actor_character_id": 29829,
            "pre_native_revision": 2,
            "pre_date_raw": 53290296,
            "pre_proof_epoch": 20,
            "source_bridge_pid": identity[0],
            "source_bridge_creation_date": identity[1],
            "candidate": {"barony_title_id": 2103, "province_id": 2635,
                          "building_type_id": 604, "slot_index": 3,
                          "gold_before_raw": 83667022,
                          "stock_gold_cost_raw": 14250000},
        }
        original = deepcopy(pending)

        class DiagnosticDriver(Driver):
            response_kind = "rejected"
            waits = 0

            def wait_for_command_result(self, request_id, timeout):
                self.waits += 1
                owner.assertEqual(self.requests[-1]["step"], transport.QUERY_NATIVE)
                owner.assertEqual(self.requests[-1]["expected_revision"], 3)
                if self.response_kind == "absent":
                    return None
                return {
                    "type": "command_result", "protocol_version": 1,
                    "request_id": ("foreign-query" if self.response_kind == "foreign"
                                   else request_id),
                    "ok": False, "error": "synthetic native rejection " + "界" * 3000,
                    "private_probe": {
                        "status": "unavailable", "failure": "synthetic_source_read_failed",
                        "schema_version": 1, "advertised": False,
                        "snapshot_revision": 3, "date_raw": 53290296, "proof_epoch": 30,
                        "player_world_building_sources": {
                            "status": "unavailable", "failure": "definition_identity",
                            "definition_identity_diagnostic": {
                                "stage": "selected_definition_identity", "failed_index": 7},
                            "forbidden_full_rows": [{"payload": "not diagnostic truth"}],
                        },
                    },
                }

        async def run(directory):
            driver = DiagnosticDriver(Path(directory) / "state")
            driver.allow_private_construction_formal_trial = True
            driver.snapshot = frame(3, episode=pending["episode_run_id"])
            driver.snapshot["date_raw"] = pending["pre_date_raw"]
            driver.snapshot["diagnostics"] = {"hello": {
                "expected_ck3_version": "1.20.0.4",
                "expected_ck3_sha256":
                    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518",
            }}
            write_construction_ledger(driver.state_dir, {
                "schema": "xar.ck3.construction_formal_pending_v1",
                "pending": deepcopy(pending), "applied": None, "applied_prior": [],
            })
            baseline = {"policy": "fixture-life", "phase": "life_advance",
                        "selected_step": "life-advance"}
            with patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=baseline), \
                    patch.object(transport, "_identity", return_value=identity), \
                    patch("xar_autoplayer.bridge.service.construction_process_identity", return_value=identity):
                async with Client(mcp_server.create_server(driver)) as client:
                    for kind, classification in (
                        ("rejected", "matched_native_rejected"),
                        ("absent", "result_absent_cause_unknown"),
                        ("foreign", "invalid_envelope"),
                    ):
                        driver.response_kind = kind
                        result = await client.call_tool("ck3_auto_turn", {})
                        owner.assertTrue(result.is_error, result.content)
                        structured = result.structured_content
                        owner.assertEqual(structured["error_type"], "BridgeUnavailableError")
                        diagnostic = structured["diagnostics"]["construction_transport_v1"]
                        owner.assertEqual(diagnostic["classification"], classification)
                        owner.assertEqual(diagnostic["source"], "construction_transport_v1")
                        owner.assertTrue(diagnostic["diagnostic_only"])
                        owner.assertEqual(diagnostic["step"], transport.QUERY_NATIVE)
                        owner.assertEqual(diagnostic["expected_native_revision"], 3)
                        owner.assertLessEqual(len(json.dumps(
                            diagnostic, ensure_ascii=False, separators=(",", ":"),
                            allow_nan=False).encode("utf-8")), 4096)
                        owner.assertTrue(all(value is None or type(value) in (str, bool, int, float)
                                             for value in diagnostic.values()))
                        if kind == "rejected":
                            owner.assertEqual(diagnostic["definition_identity_stage"],
                                              "selected_definition_identity")
                            owner.assertEqual(diagnostic["definition_identity_failed_index"], 7)
                            owner.assertEqual(diagnostic["probe_proof_epoch"], 30)
                            owner.assertTrue(diagnostic["gate_request_id"])
                            owner.assertFalse(diagnostic["gate_ok"])
                            owner.assertNotIn("forbidden_full_rows", diagnostic)
                        else:
                            owner.assertNotIn("native_error", diagnostic)
                            owner.assertNotIn("definition_identity_stage", diagnostic)
                        owner.assertEqual(read_construction_ledger(driver.state_dir)["pending"], original)
            owner.assertEqual(driver.waits, 3)
            owner.assertEqual(len(driver.requests), 3)
            owner.assertTrue(all(row["step"] == transport.QUERY_NATIVE for row in driver.requests))
            owner.assertEqual(len({row["request_id"] for row in driver.requests}), 3)
            owner.assertEqual(pending, original)

        with tempfile.TemporaryDirectory(
            dir=os.environ.get("XAR_CONSTRUCTION_DIAGNOSTIC_ARTIFACT_ROOT"),
        ) as directory:
            asyncio.run(run(directory))


if __name__ == "__main__":
    unittest.main()
