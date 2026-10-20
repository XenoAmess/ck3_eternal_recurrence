"""Frozen historical byte checks; no live policy, bus or volume probes."""
import hashlib
from pathlib import Path
import unittest
import zlib

import storage_policy_annotation_adapter_v1 as adapter


class PolicyAnnotationTests(unittest.TestCase):
    def setUp(self):
        self.path = Path(__file__).resolve().parents[2] / "docs/storage-retention-policy.md"
        # Exact policy blob at 6a56dd44ba966f641bd2e3662bd8dc059ea5cd44;
        # CI uses this fixture without a history checkout or a live policy read.
        fixture = Path(__file__).parent / "fixtures/storage_retention_policy_annotation_ec20e14f.md.zlib"
        self.raw = zlib.decompress(fixture.read_bytes())
        self.expected = {"path": str(self.path), "bytes": adapter.OLD_BYTES, "sha256": adapter.OLD_SHA}

    def test_exact_inverse(self):
        result = adapter.validate_bytes(self.raw, self.expected)
        self.assertTrue(result["accepted_annotation_only"])
        self.assertEqual(result["actual_current_policy_pin"]["sha256"], hashlib.sha256(self.raw).hexdigest())
        self.assertNotEqual(result["actual_current_policy_pin"], self.expected)

    def test_other_edit_rejected(self):
        with self.assertRaises(ValueError):
            adapter.validate_bytes(self.raw[:-1] + b"!", self.expected)

    def test_plan_drift_rejected(self):
        with self.assertRaises(ValueError):
            adapter.validate_bytes(self.raw, {**self.expected, "sha256": "0" * 64})


if __name__ == "__main__":
    unittest.main()
