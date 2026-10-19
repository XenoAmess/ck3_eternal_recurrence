"""Synthetic wire/pipe and future custody model; no live H or Native qualified.

The reserved sealed custody DTO is constructed only inside these tests to
exercise the future consumer. Production has no custody issuer yet.
"""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import test_campaign_root_context_v1_bridge as fixture
from xar_autoplayer.bridge import player_heir_candidate_component_v1 as leaf
from xar_autoplayer.bridge.campaign_root_context_contract import _PROVENANCE_BY_BUILD, normalize_campaign_root_context_v1
from xar_autoplayer.bridge.successor_ui_app_owner_v1 import install_successor_ui_app_owner_v1
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.player_heir_fixed_dynasty_projection_v1 import GETTER_SOURCE_CLOSURE_SHA256

_TEMPS = []


def native_result(component=True):
    result = fixture._native_result()
    result["backend_id"] = CK3_12004.backend_id("campaign-root-context-v1")
    root = result["campaign_root_context"]
    root["provenance"] = deepcopy(_PROVENANCE_BY_BUILD[CK3_12004.game_version])
    if component:
        core = dict(date_raw=root["date_raw"], paused=True, speed=1,
            local_player_id=root["local_player_id"], map_ready=True, has_played_character=True,
            played_character_id=root["player_character_id"], played_character_alive=True)
        root[leaf.COMPONENT] = dict(schema_version=1, snapshot_revision=root["snapshot_revision"],
            query_kind="campaign_root_context_v1", executable_sha256=CK3_12004.executable_sha256,
            getter_rva="0x289DCC0", parent_frame_bound=True, observation=dict(
                available=True, unavailable_reason=None, source_fixture=False,
                original_getter_source_bound=True, before=deepcopy(core), after=deepcopy(core),
                getter_observed=True, candidate_present=True, actor_character_id=root["player_character_id"],
                candidate_character_id=0x92000002 - 2**32, candidate_alive=True,
                identity_and_frame_stable=True, lineage_available=True,
                candidate_lineage={"house_id": 900, "dynasty_id": 174}, lineage_unavailable_reason=None))
    return result


def driver_with_owner():
    driver, endpoint = fixture._native_driver()
    endpoint.publish(dict(type="hello", protocol_version=1, bridge_version="0.1.0", pid=6767,
        session_generation=0, game_version=CK3_12004.game_version,
        expected_ck3_version=CK3_12004.game_version, executable_sha256=CK3_12004.executable_sha256,
        capabilities=["game.state.snapshot", fixture.QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY]))
    endpoint.publish(fixture._semantic_snapshot())
    # Let the original driver establish its episode before the test measures
    # optional-query work. Existing episode initialization is not this hook.
    driver.take_snapshot_without_native_command_history()
    driver._campaign_goal = dict(format_version=1, goal_key="dynasty_continuity",
        campaign_id="native-31254-6271ac8cd441", origin_character_id=31254,
        current_character_id=fixture.PLAYER_CHARACTER_ID,
        progress={"reconciled_successions": 1, "last_succession": None})
    driver._succession_lifecycle = {"lifecycle": "ordinary_campaign_succession"}
    driver.allow_private_death_succession_modal_continue = True
    temp = tempfile.TemporaryDirectory(prefix="m7-sdk-root-")
    _TEMPS.append(temp)
    driver.state_dir = Path(temp.name)
    service = SimpleNamespace(driver=driver)
    with patch("xar_autoplayer.bridge.successor_ui_app_owner_v1._machine_id", return_value="synthetic-M7-machine"):
        owner = install_successor_ui_app_owner_v1(service)
    return driver, endpoint, owner


def game(driver):
    snapshot = driver.take_snapshot_without_native_command_history()
    return dict(pid=snapshot["diagnostics"]["bridge_pid"], creation_date="20261019131054.525692+480",
        executable=os.path.abspath("synthetic/ck3.exe"))


def synthetic_future_custody(driver, owner):
    snapshot = driver.take_snapshot_without_native_command_history()
    identity = game(driver)
    return leaf._LoadedNativeProviderV1(owner, driver, owner.machine, identity["pid"],
        "20261019051054.525692+000", identity["executable"],
        snapshot["diagnostics"]["connection_generation"], driver.pipe_name, "a" * 64, leaf._LOADED_NATIVE_SEAL)


def run_query(driver, endpoint, response):
    fixture._answer_with(endpoint, lambda: deepcopy(response))
    before = driver.take_snapshot_without_native_command_history()
    return driver.execute_step(fixture.STEP, expected_revision=before["revision"])


class OptionalPlayerHeirComponentTests(unittest.TestCase):
    def tearDown(self):
        while _TEMPS:
            _TEMPS.pop().cleanup()

    def test_actual_cpp_serializer_wire_preserves_full_ids_and_fixture_boundary(self):
        path = Path(__file__).resolve().parents[3] / "docs/ck3-native-ai/evidence/player-heir-campaign-attachment-wire-fixture-2026-10-19.json"
        wire = path.read_bytes()
        self.assertEqual(hashlib.sha256(wire).hexdigest(),
            "f7feb5c3e6c527237f7cd0064e9540ee89dcf55fe8c48644cd5e54464dfdcdfa")
        component = json.loads(wire)["result"]["campaign_root_context"][leaf.COMPONENT]
        # The C++ qualification deliberately stubs the base root serializer.
        # Supply only that fixture's known parent frame, not a real root claim.
        root = dict(status="available", snapshot_revision=77, date_raw=53186880,
            local_player_id=7, player_character_id=1,
            provenance={"executable_sha256": CK3_12004.executable_sha256})
        parsed = leaf.parse_optional_player_heir_component_v1(component, root=root)
        self.assertEqual(parsed.status, "parsed")
        self.assertEqual(parsed.observation.candidate_character_id, -1845493758)
        self.assertEqual(parsed.observation.candidate_lineage.house_id, -520093695)
        self.assertEqual(parsed.observation.candidate_lineage.dynasty_id, -251658239)
        self.assertTrue(parsed.observation.source_fixture)
        self.assertFalse(parsed.observation.original_getter_source_bound)
        import test_player_heir_fixed_dynasty_projection_v1 as model
        case = model.fixture()
        binding = replace(case["current"], actor_character_id=1)
        case.update(current=binding, current_core=parsed.observation.after,
            captured=replace(case["captured"], binding=binding, observation=parsed.observation))
        result = model.project_fixed_dynasty_candidate_v1(**case)
        self.assertIsNone(result.k)
        self.assertEqual(result.reason, "synthetic_provider_has_no_scoring_credit")

    def test_old_producer_has_same_root_and_zero_new_source_work(self):
        driver, endpoint, owner = driver_with_owner()
        response = native_result(False)
        with patch("xar_autoplayer.runtime._process_identity", side_effect=AssertionError("extra OS")), \
                patch.object(leaf, "project_existing_root_player_heir_v1", side_effect=AssertionError("missing hook")):
            result = run_query(driver, endpoint, response)
        self.assertNotIn(leaf.PROJECTION, result)
        self.assertEqual(result["campaign_root_context"], response["campaign_root_context"])
        self.assertEqual(len([x for x in endpoint.frames if x.get("type") == "execute_step"]), 1)
        self.assertFalse(hasattr(owner, "_player_heir_game_identity_cache_v1"))

    def test_component_without_loaded_custody_caches_unknown_on_single_original_query(self):
        driver, endpoint, owner = driver_with_owner()
        owner._player_heir_loaded_provider_v1 = {"native_dll_sha256": "a" * 64, "source_bound": True}
        with patch("xar_autoplayer.runtime._process_identity", side_effect=AssertionError("not qualified")), \
                patch.object(driver, "_history_snapshot", side_effect=AssertionError("history export")):
            result = run_query(driver, endpoint, native_result())
        self.assertTrue(result["campaign_root_context_ready"])
        projection = result[leaf.PROJECTION]
        self.assertIsNone(projection["k"])
        self.assertIn("trusted_loaded_Native_DLL", projection["reason"])
        self.assertEqual(driver._campaign_root_context_query[leaf.PROJECTION], projection)
        self.assertEqual(len([x for x in endpoint.frames if x.get("type") == "execute_step"]), 1)

    def test_future_typed_custody_binds_real_query_id_and_caches_one_birth_read(self):
        driver, endpoint, owner = driver_with_owner()
        owner._player_heir_loaded_provider_v1 = synthetic_future_custody(driver, owner)
        with patch("xar_autoplayer.runtime._process_identity", return_value=game(driver)) as os_read:
            first = run_query(driver, endpoint, native_result())
            second = run_query(driver, endpoint, native_result())
        self.assertEqual(os_read.call_count, 1)
        for result in (first, second):
            value = result[leaf.PROJECTION]
            self.assertEqual(value["k"], 1)
            self.assertIsNone(value["b"])
            self.assertEqual(value["H_interval"], (70, 100))
            self.assertEqual(value["native_provider_sha256"], "a" * 64)
            self.assertEqual(value["machine_id"], owner.machine)
        requests = [x for x in endpoint.frames if x.get("type") == "execute_step"]
        self.assertEqual(len(requests), 2)
        self.assertEqual(first[leaf.PROJECTION]["query_id"], requests[0]["request_id"])
        self.assertEqual(second[leaf.PROJECTION]["query_id"], requests[1]["request_id"])
        self.assertNotEqual(requests[0]["request_id"], requests[1]["request_id"])
        first[leaf.PROJECTION]["k"] = 100
        self.assertEqual(driver._campaign_root_context_query[leaf.PROJECTION]["k"], 1)
        # Model a later original query's new connection tuple, without sending
        # a new command here. A new connection must refresh the OS birth once.
        snapshot = driver.take_snapshot_without_native_command_history()
        snapshot["diagnostics"]["connection_generation"] += 1
        owner._player_heir_loaded_provider_v1 = replace(owner._player_heir_loaded_provider_v1,
            connection_generation=snapshot["diagnostics"]["connection_generation"])
        with patch("xar_autoplayer.runtime._process_identity", return_value=game(driver)) as reconnected_read:
            rebound = leaf.project_existing_root_player_heir_v1(driver, starting=snapshot,
                current=deepcopy(snapshot), root=native_result()["campaign_root_context"],
                request_id="synthetic-reconnected-root", query_sequence=3)
        self.assertEqual(reconnected_read.call_count, 1)
        self.assertEqual(rebound["k"], 1)
        self.assertEqual(len([x for x in endpoint.frames if x.get("type") == "execute_step"]), 2)

    def test_source_hash_cannot_replace_loaded_DLL_and_other_owner_is_rejected(self):
        driver, endpoint, owner = driver_with_owner()
        custody = synthetic_future_custody(driver, owner)
        for bad in (replace(custody, native_dll_sha256=GETTER_SOURCE_CLOSURE_SHA256),
                    replace(custody, owner=object()), replace(custody, seal=object()),
                    replace(custody, game_birth="20261019051054.525693+000"),
                    replace(custody, connection_generation=custody.connection_generation + 1)):
            owner._player_heir_loaded_provider_v1 = bad
            with self.subTest(bad=bad), patch("xar_autoplayer.runtime._process_identity", return_value=game(driver)):
                result = run_query(driver, endpoint, native_result())
                self.assertIsNone(result[leaf.PROJECTION]["k"])

    def test_optional_bad_wire_does_not_lower_original_root_readiness(self):
        mutations = [lambda x: x.update(snapshot_revision=True),
            lambda x: x.update(executable_sha256="f" * 64), lambda x: x.update(getter_rva="0x0"),
            lambda x: x.update(parent_frame_bound=False),
            lambda x: x["observation"]["after"].update(played_character_id=22222),
            lambda x: x["observation"].update(candidate_character_id=2**31),
            lambda x: x["observation"].update(candidate_alive=1),
            lambda x: x.update(machine_id="self-signed"),
            lambda x: x["observation"].update(candidate_lineage={"house_id": 1, "dynasty_id": True})]
        for mutate in mutations:
            driver, endpoint, _ = driver_with_owner()
            response = native_result(); mutate(response["campaign_root_context"][leaf.COMPONENT])
            with self.subTest(mutation=mutate), patch("xar_autoplayer.runtime._process_identity", side_effect=AssertionError("unqualified OS")):
                result = run_query(driver, endpoint, response)
                self.assertTrue(result["campaign_root_context_ready"])
                self.assertIsNone(result[leaf.PROJECTION]["k"])

    def test_fixture_null_dead_lineage_and_generation_keep_mapper_limits(self):
        for changes in ({"source_fixture": True}, {"candidate_present": False, "candidate_character_id": -1},
                        {"candidate_alive": False}, {"lineage_available": False},
                        {"candidate_lineage": {"house_id": 900, "dynasty_id": 0x010000AE}}):
            driver, endpoint, owner = driver_with_owner()
            owner._player_heir_loaded_provider_v1 = synthetic_future_custody(driver, owner)
            response = native_result(); response["campaign_root_context"][leaf.COMPONENT]["observation"].update(changes)
            with self.subTest(changes=changes), patch("xar_autoplayer.runtime._process_identity", return_value=game(driver)):
                result = run_query(driver, endpoint, response)
            self.assertIsNone(result[leaf.PROJECTION]["k"])
            self.assertIsNone(result[leaf.PROJECTION]["b"])


if __name__ == "__main__":
    unittest.main()
