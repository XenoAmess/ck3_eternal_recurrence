"""True-shape H2743 attempt-12 read-only input binding and negative gates."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.h2743_surrender_preaction_inputs_v1 import (
    CHECKPOINT_SHA256,
    project_h2743_surrender_preaction_inputs,
)


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "h2743_surrender_preaction_attempt12.json"


def case() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def project(value: dict) -> dict:
    return project_h2743_surrender_preaction_inputs(
        value["before_snapshot"], value["baseline_first"],
        value["option_result"], value["baseline_second"],
        value["after_snapshot"], checkpoint_sha256=CHECKPOINT_SHA256,
    )


class H2743PreactionInputsTests(unittest.TestCase):
    def test_attempt12_true_shape_preserves_only_current_inputs(self) -> None:
        evidence = case()
        result = project(evidence)
        self.assertEqual(result["status"], "same_frame_preaction_inputs_only")
        self.assertFalse(result["source_bytes_authenticated_here"])
        self.assertEqual(result["target_title_ids"], [2128])
        self.assertEqual(result["target_title_holder_prestate"], [
            {"title_id": 2128, "holder_character_id": 33435,
             "holder_immediate_liege_character_id": 29829}])
        self.assertEqual(len(result["primary_resource_balances"]), 14)
        self.assertEqual(result["possible_fp2_payer_gold_prestate"], [
            {"character_id": 30097, "resource": "gold",
             "value": {"raw": 22861397, "scale": 100000}},
            {"character_id": 29829, "resource": "gold",
             "value": {"raw": 111861020, "scale": 100000}},
        ])
        self.assertIs(result["truce_predicates"]["nomad_both"]["value"], False)
        for key in ("fp2_payer_character_id", "script_candidate_days",
                    "post_surrender_actual_expiry_date_raw", "enabled_effect_selector",
                    "runtime_target_scope_title_id", "cb_prestige_factor_q100000",
                    "title_vassal_delta", "signed_resource_delta", "directed_truce",
                    "recommended_outcome", "action_literal"):
            self.assertIsNone(result[key], key)
        self.assertFalse(result["effect_projection_complete"])
        self.assertFalse(result["material_complete"])

    def test_wrong_frame_and_war_binding_rejected(self) -> None:
        mutations = (
            lambda x: x["after_snapshot"].update(date_raw=53217265),
            lambda x: x["before_snapshot"]["diagnostics"].update(connection_generation=2),
            lambda x: x["before_snapshot"]["active_wars"][0].update(war_id=16777232),
            lambda x: x["baseline_second"].update(queried_revision=5),
            lambda x: x["option_result"].update(queried_connection_generation=2),
            lambda x: x["option_result"]["termination_query_context"].update(
                queried_date_raw=53217265),
            lambda x: x["after_snapshot"]["active_wars"][0].update(
                player_relative_war_score=-11),
            lambda x: x["option_result"]["termination_query_context"][
                "active_war_signature"][0].update(player_relative_war_score=-11),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                value = case()
                mutate(value)
                with self.assertRaises(ValueError):
                    project(value)

    def test_fake_terms_or_partial_wire_values_rejected(self) -> None:
        mutations = (
            lambda x: x["baseline_first"]["defender_de_jure_exit_terms_v1"].update(
                signed_resource_delta=[]),
            lambda x: x["baseline_first"]["defender_de_jure_exit_terms_v1"].update(
                material_complete=True),
            lambda x: x["baseline_first"]["defender_de_jure_exit_terms_v1"][
                "truce_inputs_v1"].update(evaluated_days=1825),
            lambda x: x["baseline_first"]["defender_de_jure_exit_terms_v1"][
                "primary_resource_balances"].pop(),
            lambda x: x["option_result"]["war_termination_options"]["options"][
                "surrender"].update(terms_observable=True),
            lambda x: x["option_result"]["war_termination_options"][
                "active_casus_belli_identity"].update(canonical_key="other_cb"),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                value = case()
                mutate(value)
                with self.assertRaises(ValueError):
                    project(value)

    def test_double_read_drift_rejected(self) -> None:
        value = case()
        changed = deepcopy(value["baseline_second"])
        changed["defender_de_jure_exit_terms_v1"]["primary_resource_balances"][0][
            "value"]["raw"] += 1
        value["baseline_second"] = changed
        with self.assertRaisesRegex(ValueError, "double-read drift"):
            project(value)

    def test_wrong_checkpoint_claim_rejected(self) -> None:
        value = case()
        with self.assertRaisesRegex(ValueError, "checkpoint claim differs"):
            project_h2743_surrender_preaction_inputs(
                value["before_snapshot"], value["baseline_first"],
                value["option_result"], value["baseline_second"],
                value["after_snapshot"], checkpoint_sha256="0" * 64)


if __name__ == "__main__":
    unittest.main()
