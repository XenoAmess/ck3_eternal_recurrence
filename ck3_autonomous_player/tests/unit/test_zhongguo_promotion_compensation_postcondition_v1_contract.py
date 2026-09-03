from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BRIDGE = ROOT / "ck3_autonomous_player" / "native_bridge"
HEADER = BRIDGE / "include" / "xar_bridge" / "zhongguo_promotion_compensation_postcondition_v1.hpp"
SOURCE = BRIDGE / "src" / "zhongguo_promotion_compensation_postcondition_v1.cpp"
CONTRACT = BRIDGE / "research" / "zhongguo_promotion_compensation_postcondition_v1_abi.json"
PP = ROOT / "mod_zhongguo_style" / "common" / "scripted_effects" / "zg361_feedback_promotion_pip_runtime_effects.txt"
COMP = ROOT / "mod_zhongguo_style" / "common" / "scripted_effects" / "zg361_generated_compensation_runtime_effects.txt"


class PromotionCompensationProviderContractTests(unittest.TestCase):
    def test_exact_build_and_public_surface_are_frozen(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        header = HEADER.read_text(encoding="utf-8")
        self.assertEqual(contract["game_version"], "1.19.0.6")
        self.assertEqual(
            contract["executable_sha256"],
            "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
        )
        self.assertIn(contract["capability"], header)
        self.assertEqual(
            contract["request"]["public_inputs"],
            ["request_nonce", "expected_revision"],
        )
        for forbidden in contract["request"]["forbidden_inputs"]:
            self.assertNotIn(forbidden, {"request_nonce", "expected_revision"})

    def test_choice_receipt_and_revision_are_real_product_fields(self) -> None:
        product = PP.read_text(encoding="utf-8-sig")
        for key in (
            "zg361_pp_m147_receipt_active",
            "zg361_pp_m147_consumed",
            "zg361_pp_m147_receipt_owner",
            "zg361_pp_m147_receipt_subject",
            "zg361_pp_m147_receipt_cycle",
            "zg361_pp_m147_receipt_case",
            "zg361_pp_m147_receipt_route",
            "zg361_pp_m147_consumer_revision",
            "zg361_pp_m147_receipt_serial",
            "zg361_pp_m147_receipt_revision",
        ):
            self.assertIn(key, product)
        self.assertIn(
            "name = zg361_pp_m147_consumer_revision value = var:zg361_case_t_revision",
            product,
        )
        self.assertIn(
            "name = zg361_pp_m147_receipt_serial value = var:zg361_pp_t_result_case",
            product,
        )

    def test_all_compensation_receipts_have_identity_and_visible_revision(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        product = COMP.read_text(encoding="utf-8-sig")
        for mechanism in contract["compensation_receipt_selector"]["mechanism_allowlist"]:
            prefix = f"zg361_comp_m{mechanism:03d}_"
            for suffix in contract["compensation_receipt_selector"]["fixed_suffixes"]:
                self.assertIn(prefix + suffix, product)
        assignments = re.findall(
            r"set_variable = \{ name = zg361_comp_m\d{3}_visible_revision "
            r"value = var:zg361_case_(?:l|ae|af)_revision \}",
            product,
        )
        self.assertEqual(len(assignments), 33)

        for key in (
            "zg361_comp_promotion_receipt_owner",
            "zg361_comp_promotion_receipt_subject",
            "zg361_comp_promotion_receipt_cycle",
            "zg361_comp_promotion_receipt_case",
            "zg361_comp_promotion_receipt_choice_serial",
            "zg361_comp_promotion_receipt_serial",
            "zg361_comp_promotion_receipt_choice_revision",
            "zg361_comp_promotion_receipt_revision",
            "zg361_comp_promotion_receipt_posted",
        ):
            self.assertIn(key, product)

    def test_provider_is_closed_and_requires_correlated_serials(self) -> None:
        header = HEADER.read_text(encoding="utf-8")
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("kZhongguoPromotionCompensationMechanismAllowlist", header)
        self.assertIn("IsMechanismAllowlisted", source)
        self.assertNotIn("product_receipt_serial_not_persisted", source)
        self.assertIn("ready.receipt_serials_ready =", source)
        self.assertIn("posted_choice_serial_value", source)
        self.assertNotRegex(
            header,
            r"ZhongguoPromotionCompensationRequestV1\s*\{[^}]*"
            r"(subject_character_id|owner_character_id|variable_name|mechanism_id)",
        )


if __name__ == "__main__":
    unittest.main()
