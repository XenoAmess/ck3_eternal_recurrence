"""Root-only FIRST compound for the existing family policy's MCP CLI opt-in.

All native responses are new source-shaped fixture inputs. No prior native
wire, game action, birth or natural-succession outcome is qualified here.
"""

from __future__ import annotations

import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge import mcp_server
from xar_autoplayer.bridge.domain_construction_private_transport_v1 import QUERY_NATIVE
from xar_autoplayer.bridge.driver import CallbackGameplayDriver
from xar_autoplayer.bridge.marriage_candidate_alliance_private_transport import (
    STEP as RICH_STEP, query_first_heir_candidate_alliance_projection_private_v1,
)
from xar_autoplayer.bridge.observed_heir_marriage_private_action_v1 import SUBMIT_STEP
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.family_marriage_formal_consumer import read_family_marriage_ledger
from xar_autoplayer.first_heir_native_reproductive_preference import BASIS
from xar_autoplayer.m5_formal_proposal_collector import collect_m5_formal_proposals
from xar_autoplayer.m5_peacetime_proposal_sources_v1 import (
    query_m5_peacetime_proposal_sources_v1,
)


class McpFamilyFormalCliServiceTests(unittest.TestCase):
    def test_explicit_family_cli_opt_in_reaches_registered_service_and_m5(self) -> None:
        """Real main/parser/config/create_server reach the real family Service.

        Only load_driver's game I/O factory and server.run's stdio lifetime
        are replaced. Fixture endpoint replies feed the unchanged strict
        rich transport, registered planner, native preview loop and M5 source
        and selector. No planner, arithmetic or process identity is patched.
        """
        from mcp import Client
        from mcp.server import MCPServer

        actor, heir = 29829, 0x03000002
        candidates = [0x03000003, 0x03000005, 0x03000006, 0x03000007, 0x03000008]
        recipients = [0x03000020 + index for index in range(5)]
        acceptance = [500000, 400000, 300000, 200000, 100000]
        flags = (
            "allow_private_family_marriage_formal_trial",
            "allow_private_current_first_heir_betrothal_fulfillment",
            "allow_private_current_first_heir_relationship_query",
            "allow_private_family_obligations_query",
        )
        costs = {**dict.fromkeys(("gold_raw", "prestige_raw", "piety_raw", "renown_raw",
            "influence_raw", "herd_raw", "treasury_raw", "treasury_or_gold_raw",
            "merit_raw", "barter_goods_raw"), 0), "raw_scale": 100000,
            "payer_role": "actor", "application_timing": "on_send"}
        frame = {
            "snapshot_id": "native:7", "revision": 7, "native_revision": 7,
            "date_raw": 53220000, "paused": True, "map_ready": True,
            "active_event": None, "pending_character_interaction": None,
            "active_wars": [], "player_armies": [], "history": [],
            "episode_run_id": "source-fixture-mcp-family-cli30",
            "episode_character_id": actor,
            "played_character": {"character_id": actor, "alive": True},
            "played_character_gold": {"raw": 100000000, "scale": 100000},
            "campaign_goal": {
                "format_version": 1, "goal_key": "dynasty_continuity",
                "campaign_id": "source30-original-robert-cli",
                "origin_character_id": actor, "current_character_id": actor,
                "progress": {"reconciled_successions": 0, "last_succession": None},
            },
            "diagnostics": {"hello": {
                "expected_ck3_version": CK3_12004.game_version,
                "expected_ck3_sha256": CK3_12004.executable_sha256,
            }},
        }

        def fertility(raw):
            return {"source": "native_marriage_fertility_input", "extension_present": True,
                    "native_gate_evaluated": True, "native_gate_allows": True,
                    "effective_raw": raw}

        source_rows = [{
            "actor_character_id": actor, "heir_character_id": heir,
            "candidate_character_id": candidate, "recipient_character_id": recipients[index],
            "status": "available", "failure": "none", "projection_failure": "none",
            "outcome_failure": "none", "predicted_outcome_if_accepted": "marriage",
            "matrilineal_option_selected": False, "effective_matrilineal_if_accepted": False,
            "heir_is_adult": True, "candidate_is_adult": True,
            "grand_wedding_option_selected": False,
            "heir_adult_measure_raw": 20, "candidate_adult_measure_raw": 20,
            "heir_adult_threshold_raw": 16, "candidate_adult_threshold_raw": 16,
            "played_house_id": 100, "played_dynasty_id": 200,
            "heir_house_id": 100, "heir_dynasty_id": 200,
            "candidate_house_id": 300 + index, "candidate_dynasty_id": 400 + index,
            "heir_sex_selector_raw": 0, "candidate_sex_selector_raw": 1,
            "heir_betrothed_character_id": None, "heir_primary_spouse_character_id": None,
            "heir_spouse_character_ids": [], "heir_native_fertility": fertility(15000),
            "candidate_native_fertility": fertility(10000 if index == 0 else 15000),
            "native_candidate_fertility_floor_raw": 10000,
            "heir_native_scorer_age_override_raw": -1,
            "candidate_native_scorer_age_override_raw": [None, 46, -1, -1, None][index],
            "native_candidate_scorer_age_upper_raw": 45,
            "recipient_ai_accept_raw": acceptance[index], "recipient_answer_status_raw": 0,
            "complete_can_send": True, "generic_costs": deepcopy(costs),
            "possible_alliance_pairs": [],
        } for index, candidate in enumerate(candidates)]

        class FixtureDriver(CallbackGameplayDriver):
            require_initial_lifestyle_focus_before_date_advance = False

            def __init__(self, state_dir):
                super().__init__(backend_id="native-headless", snapshot=lambda: deepcopy(frame),
                    execute=self.unexpected_action, action_steps=("life-advance",))
                for flag in flags:
                    setattr(self, flag, False)
                self.state_dir = state_dir
                # The original fixed-pair dispatch reads its owning process
                # identity even for an unpartnered heir. Use the Root harness's
                # actual identity; no process is launched or lookup replaced.
                self._session_bridge_pid = os.getpid()
                self.command_timeout_seconds = 1.0
                self.endpoint, self.state = self, self
                self.requests, self.projections, self.relationships, self.preview_queries = [], [], [], []
                self.legality_reads = 0

            def unexpected_action(self, step, revision):
                raise AssertionError(f"read-only CLI qualification cannot execute {step}")

            def take_internal_semantic_snapshot(self):
                return self.take_snapshot()

            def query_current_first_heir_relationship_private_v1(self, *, expected_native_revision,
                    campaign_root_result=None):
                if not self.allow_private_current_first_heir_relationship_query or expected_native_revision != 7:
                    raise AssertionError("current-heir query lost its CLI opt-in/frame")
                relation = {
                    "schema": "xar.ck3.current-first-heir-relationship.v1", "schema_version": 1,
                    "status": "available", "unavailable_reason": None,
                    "exact_ck3_build": CK3_12004.game_version,
                    "exe_sha256": CK3_12004.executable_sha256,
                    "native_revision": 7, "read_only": True, "advertised": False,
                    "bilateral_verified": True, "heir_character_id": heir,
                    "betrothed_character_id": None, "primary_spouse_character_id": None,
                    "spouse_character_ids": [],
                }
                self.relationships.append(deepcopy(relation))
                return relation

            def query_observed_first_heir_marriage_legality_v1(self, *, expected_native_revision):
                if expected_native_revision != 7:
                    raise AssertionError("final legality crossed the source frame")
                self.legality_reads += 1
                return {"schema": "xar.ck3.observed-first-heir-marriage-legality.v1",
                    "schema_version": 1, "status": "available", "read_only": True,
                    "advertised": False, "exact_ck3_build": CK3_12004.game_version,
                    "exe_sha256": CK3_12004.executable_sha256, "native_revision": 7,
                    "query_sequence": 12, "root_query_sequence": 11,
                    "observed_first_heir_character_id": heir,
                    "native_legal_candidates": [{
                        "played_character_id": actor, "subject_character_id": heir,
                        "candidate_character_id": candidate,
                        "recipient_matchmaker_character_id": recipients[index],
                        "intermediary_character_id": -1, "native_rank": None,
                        "complete_can_send": True, "recipient_answer_allows_send": True,
                        "recipient_answer_status_raw": 0, "recipient_ai_accept_raw": acceptance[index],
                        "played_dynasty_id": 200, "heir_dynasty_id": 200,
                        "candidate_dynasty_id": 400 + index,
                        "heir_adult_measure_raw": 20, "candidate_adult_measure_raw": 20,
                        "realm_backed_actor_recipient": True,
                    } for index, candidate in enumerate(candidates)],
                }

            def query_first_heir_candidate_alliance_projection_private_v1(self, **kwargs):
                projection = query_first_heir_candidate_alliance_projection_private_v1(self, **kwargs)
                self.projections.append(deepcopy(projection))
                return projection

            def query_family_obligations_private_v1(self, *, expected_revision,
                    subject_character_id, candidate_character_id, request_matrilineal_option):
                if (not self.allow_private_family_obligations_query
                        or expected_revision != 7 or subject_character_id != heir
                        or candidate_character_id not in candidates
                        or request_matrilineal_option is not False):
                    raise AssertionError("native pair preview lost its CLI opt-in/frame/option")
                self.preview_queries.append(candidate_character_id)
                # All five are sendable played-Dynasty previews. The later
                # selected candidate changes solely because of preference.
                return {"queried_native_revision": 7, "frame": {"date_raw": 53220000},
                    "native_child_house_preview": {
                        "status": "available", "reason": "",
                        "subject_character_id": heir, "candidate_character_id": candidate_character_id,
                        "requested_matrilineal_option": False, "selected_matrilineal_option": False,
                        "effective_matrilineal_if_accepted": False, "complete_can_send": True,
                        "native_selected_parent_character_id": heir, "house_id": 100, "dynasty_id": 200,
                    }}

            def send(self, request):
                if request.get("expected_revision") != 7 or request.get("step") not in {RICH_STEP, QUERY_NATIVE}:
                    raise AssertionError("CLI read fixture received an action/unplanned query")
                self.requests.append(deepcopy(request))

            def wait_for_command_result(self, request_id, timeout_seconds):
                request = self.requests[-1]
                if request["request_id"] != request_id:
                    raise AssertionError("query correlation changed")
                step = request["step"]
                if step == RICH_STEP:
                    if (request["legality_query_sequence"] != 12
                            or [request[f"candidate_id_{index}"] for index in range(5)] != candidates):
                        raise AssertionError("source fixed-five query order changed")
                    result = {"step": step, "accepted": True, "private_build": True,
                        "read_only": True, "advertised": False, "native_revision": 7,
                        "legality_query_sequence": 12, "status": "available", "rows": deepcopy(source_rows)}
                else:
                    world = {"status": "source_available", "snapshot_revision": 7,
                        "date_raw": 53220000, "player_character_id": actor,
                        "native_final_legality_evaluated": True, "native_cost_evaluated": True,
                        "player_gold_raw": 100000000, "active_constructions": [],
                        "completed_buildings_observed": True, "completed_buildings": [],
                        "legal_samples": [], "positive_income_coverage_complete": True}
                    result = {"step": step, "accepted": True, "private_probe": {
                        "advertised": False, "snapshot_revision": 7, "date_raw": 53220000,
                        "proof_epoch": 1, "player_world_building_sources": world}}
                return {"type": "command_result", "protocol_version": 1,
                        "request_id": request_id, "ok": True, "result": result}

        scenes = (
            ("configdefault", [], (False, False, False, False)),
            ("queryonly", ["--private-current-first-heir-relationship-query",
                                  "--private-family-obligations-query"], (False, False, True, True)),
            ("explicit", ["--allow-private-family-marriage-formal-trial"],
             (True, True, True, True)),
        )

        async def consume(server, driver, name, configured, argv):
            async with Client(server) as client:
                tools = {tool.name for tool in (await client.list_tools()).tools}
                self.assertIn("ck3_plan_turn", tools)
                self.assertEqual("ck3_query_current_first_heir_relationship_private_v1" in tools,
                                 configured[2])
                self.assertEqual("ck3_query_family_obligations_private_v1" in tools, configured[3])
                planned = await client.call_tool("ck3_plan_turn", {})
                self.assertFalse(planned.is_error)
                plan = planned.structured_content["plan"]
            record = {"scene": name, "argv": argv, "configured_flags": dict(zip(flags, configured)),
                      "service_plan": deepcopy(plan), "selected_candidate_character_id": None,
                      "preview_query_order": deepcopy(driver.preview_queries)}
            if not configured[0]:
                self.assertEqual(plan["selected_step"], "life-advance")
                self.assertNotIn("family_marriage_choice", plan)
                self.assertEqual(driver.legality_reads, 0)
                self.assertEqual(driver.projections, [])
                self.assertEqual(driver.relationships, [])
                self.assertEqual(driver.preview_queries, [])
                self.assertEqual(driver.requests, [])
            else:
                self.assertEqual(plan["selected_step"], SUBMIT_STEP)
                choice = plan["family_marriage_choice"]
                selected = candidates[2]
                self.assertEqual(choice["candidate_character_id"], selected)
                self.assertEqual(driver.preview_queries, [selected])
                self.assertEqual(len(driver.projections), 1)
                self.assertGreaterEqual(len(driver.relationships), 2)
                self.assertEqual(plan["family_marriage_current_relationship"], driver.relationships[-1])
                self.assertEqual(choice["recipient_ai_accept_raw"], acceptance[2])
                self.assertGreater(acceptance[0], acceptance[2])
                self.assertGreater(acceptance[1], acceptance[2])
                rows = driver.projections[0]["rows"]
                self.assertEqual([row["candidate_character_id"] for row in rows], candidates)
                self.assertEqual([row["rejection_reasons"] for row in
                                  plan["family_marriage_private_diagnostic"]["rows"]], [[]] * 5)
                self.assertFalse(rows[0]["candidate_native_fertility_floor_comparison_v1"]["passes"])
                self.assertFalse(rows[1]["candidate_native_scorer_age_branch_v1"]["passes"])
                basis = choice[BASIS]
                self.assertEqual(basis["preference_class"], 0)
                self.assertEqual(basis["comparison_status"], "observed_pass")
                self.assertEqual(basis["floor_comparison"], rows[2]["candidate_native_fertility_floor_comparison_v1"])
                self.assertEqual(basis["age_comparison"], rows[2]["candidate_native_scorer_age_branch_v1"])
                self.assertTrue(basis["age_considered"])
                self.assertEqual(choice["immediate_generic_costs"], costs)
                self.assertIn("child_dynasty_result", choice["unpriced"])
                preview = choice["native_child_house_preview"]["native_child_house_preview"]
                self.assertTrue(preview["complete_can_send"])
                self.assertEqual((preview["native_selected_parent_character_id"], preview["dynasty_id"]),
                                 (heir, 200))
                snapshot = driver.take_snapshot()
                source = query_m5_peacetime_proposal_sources_v1(driver, snapshot=snapshot, history=[],
                    baseline_plan={"policy": "one-life-turn-v1", "selected_step": "life-advance"},
                    expected_revision=7)
                m5_plan = source["domains"]["marriage"]["plan"]
                self.assertEqual(m5_plan["family_marriage_choice"], choice)
                self.assertEqual(source["domains"]["marriage"]["plans"][0]["family_marriage_choice"][BASIS], basis)
                collection = collect_m5_formal_proposals(snapshot=snapshot, sources=source)
                self.assertEqual(collection["status"], "reserved_analytic")
                self.assertEqual(collection["collected_domains"], ["marriage"])
                self.assertEqual(collection["dispatch"]["selected_candidate_id"],
                                 f"marriage:first-heir:{heir}:{selected}:{recipients[2]}")
                record.update({"selected_candidate_character_id": selected, "preference_basis": deepcopy(basis),
                               "m5_source_choice": deepcopy(m5_plan["family_marriage_choice"]),
                               "m5_collection": deepcopy(collection)})
            self.assertIsNone(read_family_marriage_ledger(driver.state_dir)["pending"])
            self.assertTrue(all(request["step"] in {RICH_STEP, QUERY_NATIVE} for request in driver.requests))
            return record

        records = []
        with tempfile.TemporaryDirectory(prefix="xar-mcp-family-cli30-") as directory:
            for name, options, configured in scenes:
                with self.subTest(scene=name):
                    state_dir = Path(directory) / name
                    captured, loaded = [], []

                    def load_fixture(driver_name, **kwargs):
                        self.assertEqual(driver_name, "native-headless")
                        self.assertEqual(kwargs["state_dir"], state_dir)
                        driver = FixtureDriver(kwargs["state_dir"])
                        self.assertEqual(tuple(getattr(driver, flag) for flag in flags), (False,) * 4)
                        loaded.append(driver)
                        return driver

                    def capture_run(server, **kwargs):
                        self.assertEqual(kwargs, {"transport": "stdio"})
                        self.assertEqual(len(loaded), 1)
                        driver = loaded[0]
                        self.assertEqual(tuple(getattr(driver, flag) for flag in flags), configured)
                        captured.append(server)

                    argv = ["--driver", "native-headless", "--transport", "stdio",
                            "--state-dir", str(state_dir), *options]
                    with patch.object(mcp_server, "load_driver", side_effect=load_fixture) as factory, \
                            patch.object(MCPServer, "run", new=capture_run):
                        self.assertEqual(mcp_server.main(argv), 0)
                    self.assertEqual(factory.call_count, 1)
                    self.assertEqual(len(captured), 1)
                    records.append(asyncio.run(consume(captured[0], loaded[0], name, configured, argv)))
        self.assertEqual(len(records), 3)
        output_path = os.environ.get("XAR_MCP_FAMILY_FORMAL_CLI_SERVICE_OUTPUT")
        if output_path:
            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps({
                "schema": "xar.source30-mcp-family-formal-cli-service-evidence.v1",
                "input_boundary": "new_source_shaped_io_factory_and_stdio_capture_only",
                "actor_character_id": actor, "scene_count": 3, "unique_rich_source_row_count": 5,
                "native_observer_requalification": False, "game_action": False,
                "birth": False, "natural_succession": False, "live": False,
                "scenes": records,
            }, indent=2) + "\n", encoding="utf-8")
