from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / "native_bridge"
FIXTURE = (
    NATIVE
    / "research"
    / "fixtures"
    / "g2_actual_truce_expiry_v1_source_contract.json"
)
ABI = NATIVE / "research" / "g2_actual_truce_expiry_v1_abi.json"


class G2ActualTruceExpirySourceContractTests(unittest.TestCase):
    def test_counts_default_off_and_green_boundary(self) -> None:
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(fixture["schema_version"], 1)
        self.assertFalse(fixture["default_enabled"])
        self.assertFalse(fixture["green_contract"]["ack_sufficient"])
        for row in fixture["required_counts"]:
            text = (NATIVE / row["path"]).read_text(encoding="utf-8")
            self.assertEqual(text.count(row["token"]), row["count"], row)
        for row in fixture["forbidden_tokens"]:
            text = (NATIVE / row["path"]).read_text(encoding="utf-8")
            self.assertNotIn(row["token"], text, row)

    def test_abi_binds_every_production_source_hash(self) -> None:
        abi = json.loads(ABI.read_text(encoding="utf-8"))
        self.assertEqual(abi["status"], "static-ready_live-pending")
        self.assertFalse(abi["default_enabled"])
        self.assertFalse(abi["candidate"]["ack_can_make_ready"])
        for relative, expected in abi["source_sha256"].items():
            observed = hashlib.sha256((NATIVE / relative).read_bytes()).hexdigest().upper()
            self.assertEqual(observed, expected, relative)


if __name__ == "__main__":
    unittest.main()
