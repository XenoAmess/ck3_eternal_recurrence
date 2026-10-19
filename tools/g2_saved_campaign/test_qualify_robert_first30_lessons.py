"""Deployment regressions: reject stale/missing repair source without game calls."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("robert_lessons_audit", HERE / "qualify_robert_first30_lessons.py")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class AdoptionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.reviewed, self.frozen = self.root / "reviewed", self.root / "frozen"
        for base in (self.reviewed, self.frozen):
            (base / "xar_autoplayer").mkdir(parents=True)
            (base / "xar_autoplayer/policy.py").write_bytes(b"POLICY = 'reviewed'\n")
        self.catalogue = {"source_comparison": "utf8-lf", "lessons": [{"sources": ["policy.py"]}]}

    def audit(self):
        return AUDIT.audit_sources(self.frozen, self.reviewed, self.catalogue)

    def test_stale_frozen_policy_is_rejected(self):
        (self.frozen / "xar_autoplayer/policy.py").write_bytes(b"POLICY = 'old'\n")
        result = self.audit()
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["sources"][0]["reason"], "frozen_source_differs_from_reviewed_repair")

    def test_missing_repair_leaf_is_rejected(self):
        (self.frozen / "xar_autoplayer/policy.py").unlink()
        self.assertEqual(self.audit()["status"], "FAIL")

    def test_newline_only_change_retains_actual_byte_identity(self):
        (self.frozen / "xar_autoplayer/policy.py").write_bytes(b"POLICY = 'reviewed'\r\n")
        result = self.audit()
        self.assertEqual(result["status"], "PASS")
        row = result["sources"][0]
        self.assertNotEqual(row["adopted"]["sha256"], row["reviewed"]["sha256"])
        self.assertEqual(row["adopted"]["utf8_lf_sha256"], row["reviewed"]["utf8_lf_sha256"])

    def test_catalogue_cannot_audit_parent_file(self):
        self.catalogue["lessons"][0]["sources"] = ["../outside.py"]
        with self.assertRaises(ValueError):
            self.audit()

    def test_oversized_source_is_not_read_as_a_repair(self):
        original = AUDIT.MAX_SOURCE_BYTES
        self.addCleanup(setattr, AUDIT, "MAX_SOURCE_BYTES", original)
        AUDIT.MAX_SOURCE_BYTES = 16
        result = self.audit()
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("16 MiB", result["sources"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
