#!/usr/bin/env python3
"""Focused tests for the final cleanup-dispatch-aware B7 freeze."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from verify_zg361_promotion_source_capture_no_launch_candidate_final import (
    SUPERSEDED_DRIFTED_FILES,
    verify_final_promotion_source_capture_no_launch_candidate,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / (
    "ck3_autonomous_player/native_bridge/research/fixtures/"
    "zhongguo_promotion_source_capture_no_launch_candidate_7d50c2d_20260904.json"
)


class FinalPromotionSourceNoLaunchCandidateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def verify(self, manifest: dict[str, object]) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "candidate.json"
            path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return verify_final_promotion_source_capture_no_launch_candidate(
                path, source_root=ROOT, running_process_names=[]
            )

    def test_final_candidate_is_superseded_fail_closed(self) -> None:
        report = self.verify(self.manifest)
        self.assertEqual(report["result"], "RED")
        self.assertEqual(
            report["failed_checks"],
            [
                "frozen_source_files_match",
                "native_source_fingerprint_matches",
                "supersession_is_explicit_and_fail_closed",
                "a01_candidate_superseded_fail_closed",
            ],
        )
        self.assertFalse(report["ck3_started"])
        self.assertFalse(report["live_proof_claimed"])
        self.assertFalse(report["production_advertisement_ready"])

    def test_later_runner_drift_invalidates_historical_exact_list(self) -> None:
        report = self.verify(self.manifest)
        self.assertEqual(
            report["superseded_drifted_files"],
            sorted((*SUPERSEDED_DRIFTED_FILES, "tools/run_zhongguo_acceptance.py")),
        )
        self.assertFalse(report["checks"]["a01_candidate_superseded_fail_closed"])

    def test_rejects_extends_or_supersession_tampering(self) -> None:
        changed = copy.deepcopy(self.manifest)
        changed["extends"]["sha256"] = "0" * 64
        changed["supersession"]["manifest_sha256"] = "0" * 64
        report = self.verify(changed)
        self.assertEqual(report["result"], "RED")
        self.assertFalse(report["checks"]["final_manifest_identity"])
        self.assertFalse(report["checks"]["a01_candidate_superseded_fail_closed"])

    def test_rejects_enabled_action_or_ack_as_result(self) -> None:
        changed = copy.deepcopy(self.manifest)
        changed["query_action_boundary"]["action_production_advertised"] = True
        changed["query_action_boundary"]["ack_is_business_result"] = True
        report = self.verify(changed)
        self.assertEqual(report["result"], "RED")
        self.assertFalse(report["checks"]["review_query_action_default_off"])

    def test_rejects_command_effect_or_ctest_drift(self) -> None:
        changed = copy.deepcopy(self.manifest)
        changed["live_command"]["argv"].append("--unexpected")
        changed["effect_boundary"]["compensation"][
            "fingerprint_sha256"
        ] = "0" * 64
        changed["build"]["ctest_log"]["sha256"] = "0" * 64
        report = self.verify(changed)
        self.assertEqual(report["result"], "RED")
        self.assertFalse(report["checks"]["single_authorized_runner_command"])
        self.assertFalse(report["checks"]["effect_shards_match_manifest"])
        self.assertFalse(report["checks"]["frozen_ctest_log_is_94_of_94_green"])

    def test_rejects_false_live_claim(self) -> None:
        changed = copy.deepcopy(self.manifest)
        changed["live_proof_claimed"] = True
        report = self.verify(changed)
        self.assertEqual(report["result"], "RED")
        self.assertFalse(report["checks"]["no_launch_or_ack_result_claim"])


if __name__ == "__main__":
    unittest.main()
