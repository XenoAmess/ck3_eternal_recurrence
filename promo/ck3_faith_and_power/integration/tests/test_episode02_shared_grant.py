import sys
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(HERE.parent / 'src'))
from faith_power_promo import storage_shared_grant as helper


class SharedGrantTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=HERE, prefix="test-only-")
        self.addCleanup(self.temp.cleanup)
        self.grant_root = Path(self.temp.name)
        self.root = self.grant_root / "sample"
        self.root.mkdir()
        self.now = datetime.now(timezone.utc)
        self.ledger = {
            "schema": "faith-e02-combined-production-admission-v1", "machine_id": "fixture-machine",
            "active": True, "expires_at_utc": (self.now + timedelta(hours=1)).isoformat(),
            "approved_root": str(self.grant_root), "policy_version": "1.0.0",
            "suballocations_bytes": {"native": 768 * 1024**2, "sample": 640 * 1024**2},
            "this_write_peak_bytes": 1408 * 1024**2,
            "volume_total_bytes": 511776722944, "other_unspent_reservations_upper_bytes": 51177672294,
            "system_growth_reserve_bytes": 17179869184, "project_usage_upper_bytes": 49656983472,
            "effective_project_quota_bytes": 51177672294,
        }
        self.path = self.grant_root / "ADMISSION.json"
        self.free = 112630538240

    def admit(self, peak=1024):
        self.path.write_text(json.dumps(self.ledger), encoding="utf-8")
        return helper._admit(REPO, self.path, self.root, self.root / "render", "fixture-machine", peak,
            lambda path: ({"allocated": max(4096, path.stat().st_size)}, None), {"scope": "fixture"},
            now=self.now, disk_usage=lambda p: shutil._ntuple_diskusage(self.ledger["volume_total_bytes"], 1, self.free))

    def test_current_usage_is_subtracted_without_refilling_tts(self):
        (self.root / "voice.mp3").write_bytes(b"voice")
        result = self.admit()
        self.assertEqual(result["sample_usage"]["allocated_bytes"], 4096)
        self.assertEqual(result["sample_remaining_after_render_peak_bytes"], 640 * 1024**2 - 4096 - 1024)
        self.assertFalse(result["spent_refilled"])

    def test_native_lane_stays_reserved_in_fresh_capacity(self):
        result = self.admit()
        required = 1408 * 1024**2 + self.ledger["other_unspent_reservations_upper_bytes"] + 17179869184 + 21474836480
        self.assertEqual(result["required_free_bytes"], required)
        self.free = required - 1
        with self.assertRaisesRegex(ValueError, "shared free space"):
            self.admit()

    def test_sample_usage_and_future_render_cannot_borrow_native_lane(self):
        (self.root / "voice.mp3").write_bytes(b"voice")
        with self.assertRaisesRegex(ValueError, "suballocation"):
            self.admit(640 * 1024**2)

    def test_machine_and_expiry_are_current(self):
        self.ledger["machine_id"] = "other-fixture"
        with self.assertRaisesRegex(ValueError, "same-machine"):
            self.admit()
        self.ledger["machine_id"] = "fixture-machine"
        self.ledger["expires_at_utc"] = self.now.isoformat()
        with self.assertRaisesRegex(ValueError, "same-machine"):
            self.admit()

    def test_combined_quota_and_named_envelopes_are_preserved(self):
        self.ledger["effective_project_quota_bytes"] = self.ledger["project_usage_upper_bytes"]
        with self.assertRaisesRegex(ValueError, "quota"):
            self.admit()
        self.ledger["effective_project_quota_bytes"] = 51177672294
        self.ledger["suballocations_bytes"]["native"] -= 1
        with self.assertRaisesRegex(ValueError, "both named"):
            self.admit()

    def test_output_stays_in_the_allocated_sample_root(self):
        self.path.write_text(json.dumps(self.ledger), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "root and output"):
            helper._admit(REPO, self.path, self.root, self.grant_root / "native", "fixture-machine", 1024,
                lambda p: ({"allocated": 0}, None), {}, now=self.now)


if __name__ == "__main__":
    unittest.main()
