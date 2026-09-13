"""Focused checks for the bounded GEN-034-C live runner."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "native_bridge"
    / "research"
    / "run_gen034_white_peace_evaluation_live_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_gen034_white_peace_evaluation_live_acceptance", SCRIPT
)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - import guard
    raise RuntimeError(f"cannot load harness: {SCRIPT}")
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)

from test_raiktor_white_peace_narrow_projection_provider import (  # noqa: E402
    WAR_ID,
    _options_query,
    _snapshot,
    _terms_query,
)


class Gen034WhitePeaceEvaluationLiveAcceptanceTests(unittest.TestCase):
    def test_live_input_composition_marks_only_observation_inputs_live(
        self,
    ) -> None:
        terms = _terms_query()
        projection, evaluation = HARNESS._evaluate_live_inputs(
            _snapshot(), _options_query(), terms
        )

        self.assertTrue(projection["production_live"])
        self.assertTrue(evaluation["production_live_inputs"])
        self.assertTrue(evaluation["utility_evaluation_ready"])
        self.assertFalse(evaluation["full_three_way_recommendation_ready"])
        self.assertFalse(evaluation["action_ready"])
        self.assertIsNone(evaluation["action_literal"])

    def test_history_allows_exactly_the_two_read_only_queries(self) -> None:
        options_step = f"query-war-termination-options-v1-{WAR_ID}"
        terms_step = f"query-war-termination-terms-v1-{WAR_ID}"
        prefix = [{"command": "restore-checkpoint", "ok": True}]
        after = [
            *prefix,
            {"command": options_step, "ok": True},
            {"command": terms_step, "ok": True},
        ]
        self.assertTrue(
            HARNESS._history_checks(
                {"native_command_history": prefix},
                {"native_command_history": after},
                options_step=options_step,
                terms_step=terms_step,
            )["exact_read_only_command_delta"]
        )

        after.append(
            {
                "command": "query-war-termination-exit-terms-v2",
                "ok": True,
            }
        )
        self.assertFalse(
            HARNESS._history_checks(
                {"native_command_history": prefix},
                {"native_command_history": after},
                options_step=options_step,
                terms_step=terms_step,
            )["exact_read_only_command_delta"]
        )

    def test_exact_build_requires_both_narrow_query_capabilities(self) -> None:
        terms_capability = HARNESS.base.QUERY_WAR_TERMINATION_TERMS_CAPABILITY
        options_capability = HARNESS.QUERY_WAR_TERMINATION_OPTIONS_CAPABILITY
        terms_step = HARNESS.query_war_termination_terms_step(WAR_ID)
        options_step = HARNESS.query_war_termination_options_step(WAR_ID)
        capabilities = {
            "bridge_capabilities": [terms_capability, options_capability],
            "diagnostics": {
                "hello": {
                    "expected_ck3_version": HARNESS.base.EXPECTED_GAME_VERSION,
                    "game_adapter_id": HARNESS.base.EXPECTED_ADAPTER_ID,
                    "game_adapter_status": "ready",
                    "ck3_build_match": True,
                    "expected_ck3_sha256": (
                        HARNESS.base.EXPECTED_EXECUTABLE_SHA256
                    ),
                    "capabilities": [
                        terms_capability,
                        options_capability,
                    ],
                }
            },
            "action_steps": [terms_step, options_step],
        }

        proof = HARNESS._exact_build_proof(
            capabilities,
            managed_executable_sha256=(
                HARNESS.base.EXPECTED_EXECUTABLE_SHA256
            ),
            war_id=WAR_ID,
        )
        self.assertTrue(proof["ok"])

        capabilities["bridge_capabilities"].remove(options_capability)
        rejected = HARNESS._exact_build_proof(
            capabilities,
            managed_executable_sha256=(
                HARNESS.base.EXPECTED_EXECUTABLE_SHA256
            ),
            war_id=WAR_ID,
        )
        self.assertFalse(rejected["ok"])
        self.assertFalse(
            rejected["checks"]["options_bridge_capability"]
        )

    def test_runner_source_has_no_termination_or_preview_call(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn('call_tool("ck3_surrender_war"', source)
        self.assertNotIn('call_tool("ck3_offer_white_peace"', source)
        self.assertNotIn(
            'call_tool("ck3_query_war_termination_exit_terms_v2"', source
        )


if __name__ == "__main__":
    unittest.main()
