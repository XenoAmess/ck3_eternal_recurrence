"""Focused checks for the bounded GEN-034-D recommendation runner."""

from __future__ import annotations

import asyncio
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest import mock


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
            HARNESS.query_war_entry_assessments_step([DEFENDER_ID]),
            HARNESS.query_war_entry_assessments_step([DEFENDER_ID]),
            HARNESS.query_war_termination_options_step(WAR_ID),
            HARNESS.query_war_termination_terms_step(WAR_ID),
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
        self.assertLess(
            source.index('"ck3_query_war_entry_assessments", power_arguments'),
            source.index('"ck3_query_war_termination_options", arguments'),
        )

    def test_capabilities_refresh_after_terminal_evidence_queries(self) -> None:
        expected_action = f"surrender-war-{WAR_ID}"
        tool_names = [
            "ck3_get_capabilities",
            "ck3_take_snapshot",
            "ck3_query_war_termination_options",
            "ck3_query_war_termination_terms",
            "ck3_query_war_entry_assessments",
        ]

        class FakeClient:
            calls: list[str] = []

            def __init__(self, _server: object) -> None:
                pass

            async def __aenter__(self) -> "FakeClient":
                return self

            async def __aexit__(self, *_args: object) -> None:
                return None

            async def list_tools(self) -> SimpleNamespace:
                return SimpleNamespace(
                    tools=[SimpleNamespace(name=name) for name in tool_names]
                )

            async def call_tool(
                self, name: str, _arguments: dict[str, object]
            ) -> SimpleNamespace:
                self.calls.append(name)
                if name == "ck3_get_capabilities":
                    action_steps = (
                        [expected_action]
                        if "ck3_query_war_termination_terms" in self.calls
                        else []
                    )
                    value = {
                        "bridge_capabilities": [
                            HARNESS.base.QUERY_WAR_TERMINATION_TERMS_CAPABILITY,
                        ],
                        "action_steps": action_steps,
                    }
                else:
                    value = {
                        "revision": 11,
                        "date_raw": 22,
                        "paused": True,
                        "played_character": {"character_id": 33},
                        "active_wars": [
                            {
                                "war_id": WAR_ID,
                                "primary_opponent_character_id": DEFENDER_ID,
                            }
                        ],
                    }
                return SimpleNamespace(
                    structured_content=deepcopy(value),
                    is_error=False,
                    content=[],
                )

        def action_gate(
            recommendation: dict[str, object],
            _snapshot: dict[str, object],
            capabilities: dict[str, object],
        ) -> dict[str, object]:
            ready = expected_action in capabilities["action_steps"]
            return {
                "action_ready": ready,
                "action_literal": expected_action if ready else None,
            }

        recommendation = {
            "production_recommendation_ready": True,
            "action_literal": expected_action,
        }
        patches = (
            mock.patch.dict(
                sys.modules, {"mcp": SimpleNamespace(Client=FakeClient)}
            ),
            mock.patch.object(
                HARNESS.base, "create_server", return_value=object()
            ),
            mock.patch.object(
                HARNESS.base, "_same_paused_binding", return_value=True
            ),
            mock.patch.object(
                HARNESS.power, "_active_war", return_value={"war_id": WAR_ID}
            ),
            mock.patch.object(
                HARNESS,
                "provide_raiktor_campaign_dominance",
                return_value={
                    "certificate_available": True,
                    "campaign_dominance_certificate": {},
                },
            ),
            mock.patch.object(
                HARNESS, "_compose_recommendation", return_value=recommendation
            ),
            mock.patch.object(
                HARNESS,
                "provide_raiktor_three_way_exit_action_gate",
                side_effect=action_gate,
            ),
            mock.patch.object(
                HARNESS,
                "_history_checks",
                return_value={"exact_read_only_command_delta": True},
            ),
        )
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[
            5
        ], patches[6], patches[7]:
            result = asyncio.run(
                HARNESS._run_mcp_sequence(
                    object(),
                    war_id=WAR_ID,
                    expected_character_id=33,
                    expected_date_raw=22,
                    opponent_character_id=DEFENDER_ID,
                )
            )

        self.assertTrue(result["ok"])
        self.assertTrue(result["checks"]["exactly_one_action_planned"])
        self.assertGreater(
            FakeClient.calls.index("ck3_get_capabilities"),
            FakeClient.calls.index("ck3_query_war_termination_terms"),
        )


if __name__ == "__main__":
    unittest.main()
