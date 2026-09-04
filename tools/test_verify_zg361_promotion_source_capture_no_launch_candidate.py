#!/usr/bin/env python3
"""Focused tests for the promotion-source no-launch freeze verifier."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from verify_zg361_promotion_source_capture_no_launch_candidate import (
    verify_promotion_source_capture_no_launch_candidate,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / (
    "ck3_autonomous_player/native_bridge/research/fixtures/"
    "zhongguo_promotion_source_capture_no_launch_candidate_366f30f_20260904.json"
)


class PromotionSourceNoLaunchCandidateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def verify(self, manifest: dict[str, object]) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "candidate.json"
            path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return verify_promotion_source_capture_no_launch_candidate(
                path,
                source_root=ROOT,
                running_process_names=[],
            )

    def test_frozen_candidate_is_ready_for_one_serial_live_attempt(self) -> None:
        report = self.verify(self.manifest)
        self.assertEqual(report["result"], "READY_TO_SERIAL_LIVE")
        self.assertEqual(report["failed_checks"], [])
        self.assertEqual(len(report["authorized_live_argv"]), 15)
        self.assertFalse(report["ck3_started"])
        self.assertFalse(report["live_proof_claimed"])
        self.assertFalse(report["production_advertisement_ready"])

    def test_rejects_enabled_action_or_ack_as_result(self) -> None:
        changed = copy.deepcopy(self.manifest)
        changed["query_action_boundary"]["action_production_advertised"] = True
        changed["query_action_boundary"]["ack_is_business_result"] = True
        report = self.verify(changed)
        self.assertEqual(report["result"], "RED")
        self.assertFalse(report["checks"]["review_query_action_default_off"])

    def test_rejects_command_drift(self) -> None:
        changed = copy.deepcopy(self.manifest)
        changed["live_command"]["argv"].append("--unexpected")
        report = self.verify(changed)
        self.assertEqual(report["result"], "RED")
        self.assertFalse(report["checks"]["single_authorized_runner_command"])

    def test_rejects_effect_inventory_drift(self) -> None:
        changed = copy.deepcopy(self.manifest)
        changed["effect_boundary"]["feedback_promotion_pip"][
            "fingerprint_sha256"
        ] = "0" * 64
        report = self.verify(changed)
        self.assertEqual(report["result"], "RED")
        self.assertFalse(report["checks"]["effect_shards_match_manifest"])

    def test_rejects_false_live_claim(self) -> None:
        changed = copy.deepcopy(self.manifest)
        changed["live_proof_claimed"] = True
        report = self.verify(changed)
        self.assertEqual(report["result"], "RED")
        self.assertFalse(report["checks"]["no_launch_or_ack_result_claim"])


if __name__ == "__main__":
    unittest.main()
