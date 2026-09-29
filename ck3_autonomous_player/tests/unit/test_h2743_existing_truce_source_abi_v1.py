"""Static source/ABI admission gates for the default-off H2743 old slot."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest


NATIVE_ROOT = Path(__file__).resolve().parents[2] / "native_bridge"
sys.path.insert(0, str(NATIVE_ROOT / "research"))

from verify_h2743_existing_truce_source_abi_v1 import (
    SOURCE_FILES,
    admit_frozen,
    validate_source_contract,
)

FROZEN = (NATIVE_ROOT / "research" /
          "h2743_existing_truce_source_abi_v1.json")


def source_texts() -> dict[str, str]:
    return {
        name: (NATIVE_ROOT / name).read_text(encoding="utf-8")
        for name in SOURCE_FILES
    }


def frozen() -> dict:
    return json.loads(FROZEN.read_text(encoding="utf-8"))


class H2743ExistingTruceSourceAbiTests(unittest.TestCase):
    def test_actual_source_contract_is_default_off_and_read_only(self) -> None:
        validate_source_contract(source_texts())
        value = frozen()
        admit_frozen(value, value)
        self.assertEqual(value["status"],
                         "static_source_abi_verified_build_pending")
        self.assertFalse(value["default_enabled"])
        self.assertFalse(value["live_observed"])
        self.assertIsNone(value["loaded_dll_sha256"])
        self.assertIsNone(value["post_surrender_actual_expiry_date_raw"])
        self.assertIsNone(value["action_literal"])

    def test_compiled_candidate_enabled_by_default_is_rejected(self) -> None:
        value = source_texts()
        value["CMakeLists.txt"] = value["CMakeLists.txt"].replace(
            "read-only attacker-to-defender existing-slot query\"\n  OFF",
            "read-only attacker-to-defender existing-slot query\"\n  ON",
            1,
        )
        with self.assertRaisesRegex(ValueError, "source contract missing"):
            validate_source_contract(value)

    def test_missing_identity_or_frame_claim_is_rejected(self) -> None:
        mutations = (
            ("src/ck3_11906.cpp", "individual_county_de_jure_cb"),
            ("src/ck3_11906.cpp", "kWarTargetedTitleIdsOffset"),
            ("src/bridge.cpp", "expected_episode_id"),
            ("src/bridge.cpp", "expected_checkpoint_sha256"),
            ("src/h2743_preaction_existing_truce_v1.cpp",
             "war_after != war_before"),
        )
        for name, token in mutations:
            value = source_texts()
            value[name] = value[name].replace(token, "REMOVED")
            with self.subTest(name=name, token=token):
                with self.assertRaisesRegex(ValueError, "source contract missing"):
                    validate_source_contract(value)

    def test_effect_evaluation_or_fake_future_expiry_is_rejected(self) -> None:
        value = source_texts()
        value["src/h2743_preaction_existing_truce_v1.cpp"] += (
            "\nevaluate_truce_duration_days\n")
        with self.assertRaisesRegex(ValueError, "read-only core contains"):
            validate_source_contract(value)
        value = source_texts()
        value["src/h2743_preaction_existing_truce_v1.cpp"] = value[
            "src/h2743_preaction_existing_truce_v1.cpp"].replace(
                "post_surrender_actual_expiry_date_raw\\\":null",
                "post_surrender_actual_expiry_date_raw\\\":53219000", 1)
        with self.assertRaisesRegex(ValueError, "source contract missing"):
            validate_source_contract(value)

    def test_frozen_source_or_abi_drift_and_readiness_overclaim_rejected(self) -> None:
        actual = frozen()
        mutations = (
            lambda x: x["source_sha256"].update(
                {"src/h2743_preaction_existing_truce_v1.cpp": "0" * 64}),
            lambda x: x["native_ranges"]["get_truce_end_date"].update(
                sha256="0" * 64),
            lambda x: x["stock_script_sha256"].update(
                {"common/on_action/war_on_actions.txt": "0" * 64}),
            lambda x: x.update(default_enabled=True),
            lambda x: x.update(post_surrender_actual_expiry_date_raw=53219000),
            lambda x: x.update(action_literal="surrender-war-16777231"),
        )
        for mutate in mutations:
            candidate = deepcopy(actual)
            mutate(candidate)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                admit_frozen(actual, candidate)


if __name__ == "__main__":
    unittest.main()
