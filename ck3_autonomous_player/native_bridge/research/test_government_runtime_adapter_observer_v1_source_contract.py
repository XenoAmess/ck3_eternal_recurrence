#!/usr/bin/env python3
"""Bind the private semantic core tables to the GOV1 exact-build freeze."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[3]
NATIVE = ROOT / "ck3_autonomous_player/native_bridge"
RESEARCH = NATIVE / "research/government_runtime_adapter_1_19_0_6.json"
LOADED_FEATURE_SOURCE = NATIVE / "src/loaded_feature_manifest_v1.cpp"
OBSERVER_SOURCE = NATIVE / "src/government_runtime_adapter_observer_v1.cpp"
ABI = NATIVE / "research/government_runtime_adapter_observer_v1_abi.json"
PROSPECTIVE_CONTRACT = (
    NATIVE / "research/fixtures/government_runtime_adapter_observer_v1_contract.json"
)

ARRAY_BY_GOVERNMENT = {
    "feudal_government": "kFeudalFlags",
    "republic_government": "kRepublicFlags",
    "theocracy_government": "kTheocracyFlags",
    "clan_government": "kClanFlags",
    "tribal_government": "kTribalFlags",
    "wanua_government": "kWanuaFlags",
    "mercenary_government": "kMercenaryFlags",
    "holy_order_government": "kHolyOrderFlags",
    "administrative_government": "kAdministrativeFlags",
    "landless_adventurer_government": "kLandlessAdventurerFlags",
    "nomad_government": "kNomadFlags",
    "herder_government": "kHerderFlags",
    "celestial_government": "kCelestialFlags",
    "mandala_government": "kMandalaFlags",
    "steppe_admin_government": "kSteppeAdministrativeFlags",
    "meritocratic_government": "kMeritocraticFlags",
    "japan_administrative_government": "kJapanAdministrativeFlags",
    "japan_feudal_government": "kJapanFeudalFlags",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def observer_flag_array(source: str, name: str) -> list[str]:
    match = re.search(
        rf"constexpr std::array {name}\{{(?P<body>.*?)\n\}};",
        source,
        flags=re.DOTALL,
    )
    if match is None:
        raise AssertionError(f"observer flag array is absent: {name}")
    return re.findall(r'std::string_view\{"([^"]+)"\}', match.group("body"))


def observer_feature_keys(source: str) -> list[str]:
    match = re.search(
        r"kFeatureKeys\{\{(?P<body>.*?)\n    \}\};", source, flags=re.DOTALL
    )
    if match is None:
        raise AssertionError("observer feature-key table is absent")
    return re.findall(r'"([^"]+)"', match.group("body"))


def loaded_feature_keys(source: str) -> list[str]:
    match = re.search(
        r"kFeatureDefinitions\{\{(?P<body>.*?)\n    \}\};",
        source,
        flags=re.DOTALL,
    )
    if match is None:
        raise AssertionError("loaded-feature definition table is absent")
    return re.findall(r'\{0x[0-9A-F]+, "([^"]+)"\}', match.group("body"))


class GovernmentRuntimeAdapterObserverSourceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.research = json.loads(RESEARCH.read_text(encoding="utf-8"))
        cls.abi = json.loads(ABI.read_text(encoding="utf-8"))
        cls.observer_source = OBSERVER_SOURCE.read_text(encoding="utf-8")
        cls.loaded_feature_source = LOADED_FEATURE_SOURCE.read_text(encoding="utf-8")

    def test_frozen_input_hashes(self) -> None:
        contract = self.abi["input_contract"]
        self.assertEqual(
            sha256(RESEARCH), contract["government_runtime_adapter_research_sha256"]
        )
        self.assertEqual(
            sha256(LOADED_FEATURE_SOURCE),
            contract["loaded_feature_manifest_source_sha256"],
        )
        self.assertEqual(
            sha256(PROSPECTIVE_CONTRACT),
            contract["prospective_observer_contract_sha256"],
        )

    def test_all_stock_government_flags_match_gov1(self) -> None:
        registry = self.research["government_registry"]
        self.assertEqual(len(registry), 18)
        self.assertEqual(set(ARRAY_BY_GOVERNMENT), {row["key"] for row in registry})
        declaration_count = 0
        for row in registry:
            observed = observer_flag_array(
                self.observer_source, ARRAY_BY_GOVERNMENT[row["key"]]
            )
            self.assertEqual(observed, row["flags"], row["key"])
            declaration_count += len(observed)
        self.assertEqual(declaration_count, 136)

    def test_all_44_runtime_feature_identities_match_existing_reader(self) -> None:
        observer = observer_feature_keys(self.observer_source)
        existing = loaded_feature_keys(self.loaded_feature_source)
        self.assertEqual(len(observer), 44)
        self.assertEqual(observer, existing)

    def test_religion_and_private_integration_boundaries(self) -> None:
        self.assertIn(
            "result.government.religious_identity_opaque", self.observer_source
        )
        self.assertIn(
            "SelectionStatus::owner_deferred_religious", self.observer_source
        )
        implementation = self.abi["implementation"]
        self.assertTrue(implementation["cmake_target_added"])
        self.assertTrue(implementation["private_bridge_binder_compiled"])
        for key in (
            "bridge_wired",
            "public_capability_added",
            "public_schema_changed",
            "mcp_changed",
            "planner_changed",
        ):
            self.assertFalse(implementation[key], key)
        self.assertFalse(self.abi["acceptance"]["ck3_launched"])


if __name__ == "__main__":
    unittest.main()
