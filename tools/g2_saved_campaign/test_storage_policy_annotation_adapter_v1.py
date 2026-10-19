"""Pure byte/AST checks; no production bus, assets or volume probes."""
import hashlib
from pathlib import Path
import unittest

import storage_policy_annotation_adapter_v1 as adapter


class PolicyAnnotationTests(unittest.TestCase):
    def setUp(self):
        self.path = Path(__file__).resolve().parents[2] / "docs/storage-retention-policy.md"
        self.raw = self.path.read_bytes()
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
