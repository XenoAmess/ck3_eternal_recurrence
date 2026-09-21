from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "audit_coa_runtime_registry_boundary.py"
SPEC = importlib.util.spec_from_file_location("audit_coa_runtime_registry_boundary", MODULE_PATH)
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class CoatOfArmsRuntimeRegistryBoundaryTest(unittest.TestCase):
    def test_marker_scan_is_exact_and_reports_all_occurrences(self) -> None:
        data = b"\0".join(AUDIT.REGISTRY_MARKERS) + b"\0" + AUDIT.REGISTRY_MARKERS[0]
        rows = AUDIT.find_ascii_markers(data)
        self.assertEqual(len(rows), len(AUDIT.REGISTRY_MARKERS))
        self.assertEqual(len(rows[0]["offsets"]), 2)
        self.assertTrue(all(row["offsets"] for row in rows))

    def test_checked_in_tools_keep_engine_and_projection_claims_separate(self) -> None:
        receipt = AUDIT.audit_repository_contract(ROOT)
        self.assertTrue(receipt["required_negative_provenance_present"])
        self.assertFalse(receipt["unverified_runtime_registry_tools_public"])
        self.assertEqual(len(receipt["source_receipts"]), 3)


if __name__ == "__main__":
    unittest.main()
