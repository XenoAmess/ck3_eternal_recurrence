from __future__ import annotations

import copy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer.bridge.driver import BridgeUnavailableError, DevelopmentReportDriver
from xar_autoplayer.bridge.frontend_fixture_start_contract import (
    FAITH_E01_FRONTEND_TARGET, FAITH_E01_PROFILE_ID, EXE_SHA256_12004,
    fixture_business_context_binding, validate_fixture_start_policy,
)
from xar_autoplayer.bridge.frontend_fixture_scenario_start_v1 import (
    BOOKMARK, CHARACTER, PROBE, START, require_scenario_start_submission,
)
from test_frontend_fixture_start_policy import capabilities, current, fake_driver, policy


def scenario_policy():
    value = policy()
    value.update(schema="ck3-frontend-fixture-start-policy-v2", schema_version=2,
        profile_id=FAITH_E01_PROFILE_ID, frontend_target=dict(FAITH_E01_FRONTEND_TARGET),
        post_start={"government_key": "clan_government", "primary_title_tier_key": "empire", "independent": True})
    return value


def scenario_driver(directory, *, fail_step=None, wrong_model=None):
    driver, _ = fake_driver(directory)
    driver.frontend_fixture_start_policy_binding.update(profile_id=FAITH_E01_PROFILE_ID,
        frontend_target=dict(FAITH_E01_FRONTEND_TARGET))
    caps = capabilities()
    caps["diagnostics"]["hello"].update(expected_ck3_version="1.20.0.4",
        expected_ck3_sha256=EXE_SHA256_12004, game_adapter_id="ck3-1.20.0.4-msvc-x64")
    driver.capabilities = lambda: caps
    state = {"bookmark": False, "character": False}
    calls = []
    def execute(step, **kwargs):
        calls.append(step)
        if step == fail_step:
            raise BridgeUnavailableError("lost ACK after possible native execution")
        if step == PROBE:
            if not state["bookmark"]:
                return {"accepted": True, "status": "unavailable", "selected_bookmark_key": "bm_1066_rags_to_riches"}
            target = FAITH_E01_FRONTEND_TARGET
            result = {"accepted": True, "status": "identity_ready", "candidate_identity_ready": True,
                "selected_bookmark_key": target["bookmark_key"], "selected_bookmark_group_key": target["bookmark_group_key"],
                "selected_date_low_raw": target["start_date_raw"], "candidate_keys": [target["character_name_key"]],
                "supported_1066_candidate_index": 0, "selected_character_index": 0 if state["character"] else -1,
                "supported_1066_government_key": target["government_key"], "supported_1066_date_matches": True,
                "supported_1066_feudal": False}
            if wrong_model:
                result.update(wrong_model)
            return result
        rows = (directory / "frontend-fixture-start-requests.jsonl").read_text().splitlines()
        import json
        last = json.loads(rows[-1])
        if last["step"] != step or last["retry_allowed"] is not False:
            raise AssertionError("mutation lacks a prior durable exact-step intent")
        if step == BOOKMARK:
            state["bookmark"] = True
        elif step == CHARACTER:
            state["character"] = True
        elif step != START:
            raise AssertionError("unexpected step")
        return {"step": step, "accepted": True, "status": "acknowledged_verification_pending", "backend_id": "native-headless"}
    driver._execute_primitive_step = execute
    return driver, calls


class ScenarioPolicyTests(unittest.TestCase):
    def test_exact_episode_profile_is_closed_and_old_policy_does_not_admit_clan(self):
        self.assertEqual(validate_fixture_start_policy(scenario_policy()), scenario_policy())
        for field, bad in (("profile_id", "other"), ("frontend_target", {**FAITH_E01_FRONTEND_TARGET, "native_actor_id": 34014}),
                ("frontend_target", {**FAITH_E01_FRONTEND_TARGET, "start_date_raw": True})):
            value = scenario_policy()
            value[field] = bad
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_fixture_start_policy(value)
        old = policy()
        old["post_start"]["government_key"] = "clan_government"
        with self.assertRaises(ValueError):
            validate_fixture_start_policy(old)

    def test_same_revision_actual_actor_binds_without_guessing_history_fullref(self):
        with tempfile.TemporaryDirectory() as directory:
            driver, _ = scenario_driver(Path(directory))
            receipt = driver.submit_frontend_fixture_scenario_start_v1()
        snapshot, root = current(actor=87123)
        snapshot["date_raw"] = root["date_raw"] = FAITH_E01_FRONTEND_TARGET["start_date_raw"]
        root["provenance"].update(game_version="1.20.0.4", executable_sha256=EXE_SHA256_12004)
        root["government"]["key"] = "clan_government"
        root["primary_title"].update(tier_key="empire", tier_raw=5)
        bound = fixture_business_context_binding(snapshot, root, scenario_policy(), receipt)
        self.assertEqual(bound["actor_character_id"], 87123)
        self.assertFalse(bound["fixture_target_identity_proven"])


class ScenarioSubmissionTests(unittest.TestCase):
    def test_real_driver_crosses_bookmark_then_selects_once_and_keeps_postcondition_pending(self):
        with tempfile.TemporaryDirectory() as directory:
            driver, calls = scenario_driver(Path(directory))
            receipt = driver.submit_frontend_fixture_scenario_start_v1()
            self.assertEqual(calls, [PROBE, BOOKMARK, PROBE, CHARACTER, PROBE, START])
            self.assertFalse(receipt["postcondition_verified"])
            self.assertFalse(receipt["fixture_target_identity_proven"])
            with self.assertRaises(BridgeUnavailableError):
                driver.submit_frontend_fixture_scenario_start_v1()
            self.assertEqual(len(calls), 6)

    def test_lost_mutation_ack_is_not_replayed_by_same_or_new_driver(self):
        for step in (BOOKMARK, CHARACTER, START):
            with self.subTest(step=step), tempfile.TemporaryDirectory() as directory:
                driver, calls = scenario_driver(Path(directory), fail_step=step)
                with self.assertRaises(BridgeUnavailableError):
                    driver.submit_frontend_fixture_scenario_start_v1()
                before = list(calls)
                with self.assertRaises(BridgeUnavailableError):
                    driver.submit_frontend_fixture_scenario_start_v1()
                self.assertEqual(calls, before)
                replacement, replacement_calls = scenario_driver(Path(directory))
                with self.assertRaises(FileExistsError):
                    replacement.submit_frontend_fixture_scenario_start_v1()
                self.assertEqual(replacement_calls, [])

    def test_wrong_model_government_or_date_never_starts(self):
        for bad in ({"supported_1066_government_key": "feudal_government"}, {"selected_date_low_raw": 53144328}):
            with self.subTest(bad=bad), tempfile.TemporaryDirectory() as directory:
                driver, calls = scenario_driver(Path(directory), wrong_model=bad)
                driver.frontend_transition_timeout_seconds = 0.001
                with self.assertRaises(BridgeUnavailableError):
                    driver.submit_frontend_fixture_scenario_start_v1()
                self.assertNotIn(CHARACTER, calls)
                self.assertNotIn(START, calls)

    def test_wrong_profile_and_robert_method_reject_before_native_submission(self):
        with tempfile.TemporaryDirectory() as directory:
            driver, calls = scenario_driver(Path(directory))
            with self.assertRaises(BridgeUnavailableError):
                driver.submit_frontend_fixture_robert_start_v1()
            driver.frontend_fixture_start_policy_binding["profile_id"] = "arbitrary"
            with self.assertRaises(ValueError):
                driver.submit_frontend_fixture_scenario_start_v1()
            self.assertEqual(calls, [])


class ScenarioMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_registered_tool_has_no_actor_arguments_and_returns_pending(self):
        from mcp import Client
        from xar_autoplayer.bridge.mcp_server import create_server
        with tempfile.TemporaryDirectory() as directory:
            native, _ = scenario_driver(Path(directory))
            receipt = native.submit_frontend_fixture_scenario_start_v1()
            driver = DevelopmentReportDriver(Path(directory))
            driver.frontend_fixture_start_policy_binding = copy.deepcopy(native.frontend_fixture_start_policy_binding)
            calls = []
            driver.submit_frontend_fixture_scenario_start_v1 = lambda: (calls.append(1) or receipt)
            async with Client(create_server(driver)) as client:
                names = {tool.name: tool for tool in (await client.list_tools()).tools}
                name = "ck3_submit_frontend_fixture_scenario_start_v1"
                self.assertIn(name, names)
                self.assertNotIn("ck3_submit_frontend_fixture_robert_start_v1", names)
                self.assertEqual(names[name].input_schema["properties"], {})
                self.assertFalse(names[name].input_schema["additionalProperties"])
                self.assertTrue((await client.call_tool(name, {"native_actor_id": 34014})).is_error)
                self.assertEqual(calls, [])
                value = await client.call_tool(name, {})
                self.assertFalse(value.is_error)
                self.assertFalse(value.structured_content["postcondition_verified"])
                self.assertEqual(calls, [1])


if __name__ == "__main__":
    unittest.main()
