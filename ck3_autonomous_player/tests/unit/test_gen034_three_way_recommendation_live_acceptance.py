"""Focused checks for the bounded GEN-034-D recommendation runner."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
TEST_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TEST_ROOT))
SCRIPT = (
    ROOT
    / "native_bridge"
    / "research"
    / "run_gen034_three_way_recommendation_live_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_gen034_three_way_recommendation_live_acceptance", SCRIPT
)
if SPEC is None or SPEC.loader is None:  # pragma: no cover
    raise RuntimeError(f"cannot load harness: {SCRIPT}")
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)

from test_raiktor_three_way_exit_recommendation import _dominance  # noqa: E402
from test_raiktor_white_peace_narrow_projection_provider import (  # noqa: E402
    DEFENDER_ID,
    WAR_ID,
    _options_query,
    _snapshot,
    _terms_query,
)
from xar_autoplayer.simulation.raiktor_white_peace_narrow_projection_provider import (  # noqa: E402
    provide_raiktor_white_peace_narrow_projection,
)


class Gen034ThreeWayRecommendationLiveAcceptanceTests(unittest.TestCase):
    def test_composition_produces_one_live_bound_recommendation(self) -> None:
        snapshot = _snapshot()
        options = _options_query()
        terms = _terms_query()
        projection = provide_raiktor_white_peace_narrow_projection(
            snapshot, options, terms, production_live=True
        )
        dominance = _dominance(projection)

        result = HARNESS._compose_recommendation(
            snapshot, options, terms, dominance
        )

        self.assertTrue(result["production_recommendation_ready"])
        self.assertTrue(result["action_ready"])
        self.assertEqual(result["recommended_outcome"], "continue")
        self.assertEqual(result["action_literal"], "resume-map")
        self.assertFalse(result["postcondition_verified"])

    def test_history_accepts_only_four_declared_reads(self) -> None:
        prefix = [{"command": "restore-checkpoint", "ok": True}]
        commands = [
            HARNESS.query_war_termination_options_step(WAR_ID),
            HARNESS.query_war_termination_terms_step(WAR_ID),
            HARNESS.query_war_entry_assessments_step([DEFENDER_ID]),
            HARNESS.query_war_entry_assessments_step([DEFENDER_ID]),
        ]
        after = [
            *prefix,
            *({"command": command, "ok": True} for command in commands),
        ]
        self.assertTrue(
            HARNESS._history_checks(
                {"native_command_history": prefix},
                {"native_command_history": after},
                expected_commands=commands,
            )["exact_read_only_command_delta"]
        )
        after.append({"command": "resume-map", "ok": True})
        self.assertFalse(
            HARNESS._history_checks(
                {"native_command_history": prefix},
                {"native_command_history": after},
                expected_commands=commands,
            )["exact_read_only_command_delta"]
        )

    def test_exact_build_requires_exit_and_power_capabilities(self) -> None:
        terms_capability = HARNESS.base.QUERY_WAR_TERMINATION_TERMS_CAPABILITY
        options_capability = (
            HARNESS.exit_read.QUERY_WAR_TERMINATION_OPTIONS_CAPABILITY
        )
        power_capability = HARNESS.power.QUERY_WAR_ENTRY_ASSESSMENTS_CAPABILITY
        capabilities = {
            "bridge_capabilities": [
                terms_capability,
                options_capability,
                power_capability,
            ],
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
                        power_capability,
                    ],
                }
            },
            "action_steps": [
                HARNESS.query_war_termination_terms_step(WAR_ID),
                HARNESS.query_war_termination_options_step(WAR_ID),
                HARNESS.query_war_entry_assessments_step([DEFENDER_ID]),
            ],
        }

        proof = HARNESS._exact_build_proof(
            capabilities,
            managed_executable_sha256=(
                HARNESS.base.EXPECTED_EXECUTABLE_SHA256
            ),
            war_id=WAR_ID,
            opponent_character_id=DEFENDER_ID,
        )
        self.assertTrue(proof["ok"])

        capabilities["bridge_capabilities"].remove(power_capability)
        rejected = HARNESS._exact_build_proof(
            capabilities,
            managed_executable_sha256=(
                HARNESS.base.EXPECTED_EXECUTABLE_SHA256
            ),
            war_id=WAR_ID,
            opponent_character_id=DEFENDER_ID,
        )
        self.assertFalse(rejected["ok"])
        self.assertFalse(rejected["checks"]["power_bridge_capability"])

    def test_runner_source_contains_no_mutating_call(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn('"step": "resume-map"', source)
        self.assertNotIn('"step": f"offer-white-peace-', source)
        self.assertNotIn('"step": f"surrender-war-', source)
        self.assertIn('"mutation_commands": []', source)


if __name__ == "__main__":
    unittest.main()
