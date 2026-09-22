"""Focused static contract for the default-OFF M5 current-war private wire."""

from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"


class M5WarPrimaryPrivateWireContractTest(unittest.TestCase):
    def test_exact_build_and_private_status(self) -> None:
        supply = json.loads(
            (RESEARCH / "m5_primary_army_supply_1_19_0_6_abi.json").read_text(
                encoding="utf-8"
            )
        )
        join = json.loads(
            (RESEARCH / "m5_war_primary_readback_v1_contract.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(supply["game_version"], "1.19.0.6")
        self.assertEqual(supply["ck3_exe_sha256"], join["ck3_exe_sha256"])
        self.assertTrue(supply["private_candidate_wired"])
        self.assertTrue(join["private_candidate_wired"])
        self.assertFalse(supply["production_wired"])
        self.assertFalse(supply["advertised"])
        self.assertFalse(join["advertised"])
        self.assertFalse(join["live_verified"])

    def test_build_option_stays_default_off(self) -> None:
        cmake = (ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
        option = "XAR_CK3_ENABLE_G2_M5_WAR_PRIMARY_CURRENT_PRIVATE_V1"
        self.assertIn(f"  {option}\n", cmake)
        self.assertIn(
            '  "Admit one unadvertised same-paused-revision current primary war/supply readback"\n  OFF',
            cmake,
        )
        self.assertIn("src/m5_war_primary_private_wire_v1.cpp", cmake)

    def test_same_application_main_frame_and_no_public_ad(self) -> None:
        source = (
            ROOT / "src" / "m5_war_primary_private_wire_v1.cpp"
        ).read_text(encoding="utf-8")
        adapter = (ROOT / "src" / "ck3_11906_adapter.cpp").read_text(
            encoding="utf-8"
        )
        self.assertIn("OwnsPausedSlot(access)", source)
        self.assertGreaterEqual(source.count("SameFrame(access)"), 2)
        self.assertIn("ReadWarEntryAssessmentsV1(", source)
        self.assertIn("ReadDeclarationBoundPrewarScopeV1(", source)
        self.assertIn("ReadM5PrimaryArmySupplyV1(", source)
        self.assertIn("ReadM5WarPrimaryReadbackV1(", source)
        self.assertNotIn("query-m5-war-primary-current-v1-", adapter)
        self.assertNotIn("SubmitDeclareWar", source)


if __name__ == "__main__":
    unittest.main()
