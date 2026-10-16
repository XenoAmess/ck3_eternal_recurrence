from datetime import datetime, timezone
import json
from pathlib import Path
import unittest

import storage_retention_inspect as inspect


class RetentionInspectionTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads((Path(__file__).resolve().parents[1] / "docs/storage-retention-policy.json").read_text(encoding="utf-8"))
        self.now = datetime(2026, 10, 16, 10, tzinfo=timezone.utc)
        self.asset = {"asset_id": "export-a", "replica_id": "machine:export-a", "category": "derived", "state": "closed",
                      "active_references": [], "closed_at_utc_or_null": "2026-10-10T00:00:00Z",
                      "last_used_at_utc": "2026-10-15T12:00:00Z", "protected_until_utc_or_null": None}

    def test_last_actual_use_controls_default_deadline(self):
        self.assertEqual(inspect.evaluate_asset(self.asset, self.policy, self.now)["state"], "within_retention")
        self.asset["last_used_at_utc"] = "2026-10-10T00:00:00Z"
        result = inspect.evaluate_asset(self.asset, self.policy, self.now)
        self.assertEqual(result["state"], "review_due")
        self.assertFalse(result["deletion_authorized"])

    def test_current_use_unknown_closure_and_invalid_protection_block_review_candidate(self):
        self.asset["active_references"] = ["current-seed"]
        self.assertEqual(inspect.evaluate_asset(self.asset, self.policy, self.now)["state"], "current_use")
        self.asset["active_references"] = []
        self.asset["closed_at_utc_or_null"] = None
        self.assertEqual(inspect.evaluate_asset(self.asset, self.policy, self.now)["state"], "unknown")
        self.asset["protected_until_utc_or_null"] = "2026-10-30T00:00:00Z"
        self.asset["protection_approved_at_utc"] = "2026-10-16T00:00:00Z"
        self.assertEqual(inspect.evaluate_asset(self.asset, self.policy, self.now)["state"], "unknown")

    def test_different_machine_and_path_escape_rejected(self):
        profile = {"machine_id": "a", "policy_version": "1.0.0", "project_root_map": {"root": str(Path(__file__).parent)}, "volume_map": {}}
        asset = {**self.asset, "machine_id": "a", "root_id": "root", "relative_path": "../outside"}
        ledger = {"machine_id": "a", "policy_version": "1.0.0", "asset_groups": [asset]}
        with self.assertRaisesRegex(ValueError, "Machine ID"):
            inspect.inspect(profile, ledger, self.policy, "b", self.now)
        with self.assertRaisesRegex(ValueError, "outside"):
            inspect.inspect(profile, ledger, self.policy, "a", self.now)


if __name__ == "__main__":
    unittest.main()
