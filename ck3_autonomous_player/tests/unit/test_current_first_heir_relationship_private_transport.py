"""Focused no-launch contract for the standalone first-heir relation read."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import asyncio
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.current_first_heir_relationship_private_transport import (
    SCHEMA, STEP, query_current_first_heir_relationship_private_v1,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError


def _frame() -> dict[str, object]:
    return {"native_revision": 3, "revision": 4, "date_raw": 53215920,
            "paused": True, "map_ready": True,
            "played_character": {"character_id": 29829, "alive": True}}


def _reply(status: str = "available", **fields: object) -> dict[str, object]:
    return {"ok": True, "result": {
        "step": STEP, "accepted": True, "private_build": True,
        "read_only": True, "advertised": False,
        "native_revision": 3,
        "subject_source": "public_campaign_root_primary_first_heir",
        "heir_character_id": 38822, "status": status,
        "unavailable_reason": None, "bilateral_verified": True,
        "betrothed_character_id": None,
        "primary_spouse_character_id": None,
        "spouse_character_ids": [], **fields,
    }}


def _pair_value(**fields: object) -> dict[str, object]:
    return {
        "status": "available", "unavailable_reason": None,
        "actor_character_id": 29829, "heir_character_id": 38822,
        "partner_character_id": 38718, "recipient_character_id": 32897,
        "intermediary_character_id": None,
        "adult_readback_available": True,
        "heir_is_adult": True, "partner_is_adult": True,
        "heir_adult_measure_raw": 19, "partner_adult_measure_raw": 23,
        "heir_adult_threshold_raw": 18, "partner_adult_threshold_raw": 21,
        "ready_to_marry_betrothed": True,
        "final_legality_sampled": True, "complete_can_send": True,
        "recipient_acceptance_ready": True, "recipient_ai_accept_raw": 1000000,
        "recipient_answer_status_raw": 0,
        "generic_costs": {
            "raw_scale": 100000, "payer_role": "actor", "application_timing": "on_send",
            **{key: 0 for key in ("gold_raw", "prestige_raw", "piety_raw", "renown_raw",
                "influence_raw", "herd_raw", "treasury_raw", "treasury_or_gold_raw",
                "merit_raw", "barter_goods_raw")},
        },
        "effective_matrilineal_if_accepted": False,
        "predicted_outcome_if_accepted": "marriage", **fields,
    }


class _Endpoint:
    request: dict[str, object] | None = None

    def send(self, request: dict[str, object]) -> None:
        self.request = request


class _State:
    def __init__(self, reply: dict[str, object] | None) -> None:
        self.reply = reply

    def wait_for_command_result(self, request_id: str,
                                timeout_seconds: float) -> dict[str, object] | None:
        return self.reply


class _Driver:
    allow_private_current_first_heir_relationship_query = True

    def __init__(self, reply: dict[str, object] | None,
                 frames: list[dict[str, object]], heir: int | None = 38822) -> None:
        self.endpoint = _Endpoint()
        self.state = _State(reply)
        self.frames = frames
        self.heir = heir

    def take_snapshot(self) -> dict[str, object]:
        return self.frames.pop(0)

    def _execute_campaign_root_context_v1_query(
        self, *, expected_revision: int,
    ) -> dict[str, object]:
        if expected_revision != 4:
            raise AssertionError("wrong public frame")
        return {"status": "available", "query_sequence": 11,
                "held_title_partition": [{"primary": True,
                                          "first_heir_character_id": self.heir}]}


class CurrentFirstHeirRelationshipPrivateTests(unittest.TestCase):
    def test_fixed_pair_value_preserves_runtime_thresholds_and_signed_costs(self) -> None:
        value = _pair_value()
        value["generic_costs"]["prestige_raw"] = 3000000
        driver = _Driver(_reply(betrothed_character_id=38718,
                               betrothal_actionability=value), [_frame()] * 3)
        result = query_current_first_heir_relationship_private_v1(
            driver, expected_native_revision=3)
        self.assertEqual(result["betrothal_actionability"], value)
        self.assertNotIn("candidate_id", driver.endpoint.request)
        self.assertNotIn("heir_character_id", driver.endpoint.request)
        self.assertEqual(result["betrothal_actionability"]["heir_adult_threshold_raw"], 18)

        from xar_autoplayer.first_heir_companion_paused_observer import (
            observe_first_heir_companion_after_child,
        )
        before = {**_frame(), "snapshot_id": "native:3",
                  "episode_run_id": "native-29829-test", "episode_character_id": 29829,
                  "played_character_id": 29829, "played_character_alive": True}
        requests: list[int] = []

        def parsed_read(*, expected_native_revision: int) -> dict[str, object]:
            requests.append(expected_native_revision)
            return result

        companion = observe_first_heir_companion_after_child(
            SimpleNamespace(query_current_first_heir_relationship_private_v1=parsed_read),
            SimpleNamespace(snapshot=lambda: dict(before)), before=before,
            child_observation={"same_frame": True}, first_heir_resolved=None, turn_index=2,
        )
        self.assertEqual(requests, [3])
        self.assertEqual(companion["existing_betrothal_value_status"],
                         "native_legal_marriage_value_observed")
        self.assertIs(companion["new_proposal_eligible"], False)
        self.assertIs(companion["read_only"], True)
        self.assertNotIn("selected_step", companion)

    def test_unavailable_pair_keeps_observed_adulthood_and_unknown_final_value(self) -> None:
        value = _pair_value(
            status="unavailable", unavailable_reason="final_context_unavailable",
            recipient_character_id=None, final_legality_sampled=False,
            complete_can_send=None, recipient_acceptance_ready=False,
            recipient_ai_accept_raw=None, recipient_answer_status_raw=None,
            generic_costs=None, effective_matrilineal_if_accepted=None,
            predicted_outcome_if_accepted=None,
        )
        result = query_current_first_heir_relationship_private_v1(
            _Driver(_reply(betrothed_character_id=38718,
                           betrothal_actionability=value), [_frame()] * 3),
            expected_native_revision=3)
        observed = result["betrothal_actionability"]
        self.assertIs(observed["ready_to_marry_betrothed"], True)
        self.assertIsNone(observed["complete_can_send"])
        self.assertIsNone(observed["generic_costs"])

    def test_legacy_pair_input_is_unknown_and_not_applicable_remains_distinct(self) -> None:
        result = query_current_first_heir_relationship_private_v1(
            _Driver(_reply(betrothed_character_id=38718), [_frame()] * 3),
            expected_native_revision=3)
        legacy = result["betrothal_actionability"]
        self.assertEqual(legacy["status"], "unavailable")
        self.assertEqual(legacy["unavailable_reason"], "native_readback_not_supplied")
        self.assertIsNone(legacy["ready_to_marry_betrothed"])
        self.assertIsNone(legacy["generic_costs"])
        absent = {**legacy, "status": "not_applicable",
                  "unavailable_reason": "no_current_betrothal", "partner_character_id": None}
        result = query_current_first_heir_relationship_private_v1(
            _Driver(_reply(betrothal_actionability=absent), [_frame()] * 3),
            expected_native_revision=3)
        self.assertEqual(result["betrothal_actionability"]["status"], "not_applicable")

    def test_sampled_native_rejection_is_observed_and_other_pair_is_rejected(self) -> None:
        rejected = _pair_value(complete_can_send=False, recipient_answer_status_raw=2)
        result = query_current_first_heir_relationship_private_v1(
            _Driver(_reply(betrothed_character_id=38718,
                           betrothal_actionability=rejected), [_frame()] * 3),
            expected_native_revision=3)
        self.assertEqual(result["betrothal_actionability"]["status"], "available")
        self.assertIs(result["betrothal_actionability"]["complete_can_send"], False)
        with self.assertRaisesRegex(BridgeUnavailableError, "identity changed"):
            query_current_first_heir_relationship_private_v1(
                _Driver(_reply(betrothed_character_id=38718,
                               betrothal_actionability=_pair_value(partner_character_id=38719)),
                        [_frame()] * 3), expected_native_revision=3)

    def test_opt_in_is_required_before_any_native_read(self) -> None:
        driver = _Driver(_reply(), [_frame()] * 3)
        driver.allow_private_current_first_heir_relationship_query = False
        with self.assertRaises(UnsupportedStepError):
            query_current_first_heir_relationship_private_v1(
                driver, expected_native_revision=3)
        self.assertIsNone(driver.endpoint.request)

    def test_empty_relation_is_an_available_bilateral_read_without_candidates(self) -> None:
        driver = _Driver(_reply(), [_frame()] * 3)
        result = query_current_first_heir_relationship_private_v1(
            driver, expected_native_revision=3)
        self.assertEqual(result["schema"], SCHEMA)
        self.assertEqual(result["status"], "available")
        self.assertEqual(result["heir_character_id"], 38822)
        self.assertEqual(result["spouse_character_ids"], [])
        self.assertIsNone(result["betrothed_character_id"])
        self.assertTrue(result["bilateral_verified"])
        self.assertEqual(driver.endpoint.request["step"], STEP)
        self.assertNotIn("candidate_id", driver.endpoint.request)
        self.assertNotIn("heir_character_id", driver.endpoint.request)

    def test_betrothal_and_spouse_relationships_stay_distinct(self) -> None:
        for fields, expected in (
            ({"betrothed_character_id": 38710}, "betrothed_character_id"),
            ({"primary_spouse_character_id": 38710,
              "spouse_character_ids": [38710]}, "primary_spouse_character_id"),
        ):
            with self.subTest(expected=expected):
                driver = _Driver(_reply(**fields), [_frame()] * 3)
                result = query_current_first_heir_relationship_private_v1(
                    driver, expected_native_revision=3)
                self.assertEqual(result[expected], 38710)

    def test_unavailable_is_not_an_empty_relation(self) -> None:
        reply = _reply(status="unavailable",
                       unavailable_reason="partner_unavailable",
                       bilateral_verified=False, spouse_character_ids=None)
        result = query_current_first_heir_relationship_private_v1(
            _Driver(reply, [_frame()] * 3), expected_native_revision=3)
        self.assertEqual(result["status"], "unavailable")
        self.assertNotIn("spouse_character_ids", result)
        malformed = _reply(status="unavailable",
                           unavailable_reason="partner_unavailable")
        with self.assertRaisesRegex(BridgeUnavailableError, "unavailable.*malformed"):
            query_current_first_heir_relationship_private_v1(
                _Driver(malformed, [_frame()] * 3), expected_native_revision=3)

    def test_frame_drift_or_identity_change_is_red(self) -> None:
        changed = deepcopy(_frame())
        changed["date_raw"] += 1
        with self.assertRaisesRegex(BridgeUnavailableError, "frame changed"):
            query_current_first_heir_relationship_private_v1(
                _Driver(_reply(), [_frame(), _frame(), changed]),
                expected_native_revision=3)
        wrong = _reply(heir_character_id=38823)
        with self.assertRaisesRegex(BridgeUnavailableError, "identity changed"):
            query_current_first_heir_relationship_private_v1(
                _Driver(wrong, [_frame()] * 3), expected_native_revision=3)

    def test_no_first_heir_cannot_be_reported_as_available(self) -> None:
        unavailable = _reply(status="unavailable", heir_character_id=-1,
                             unavailable_reason="public_campaign_root_primary_first_heir_absent",
                             bilateral_verified=False, spouse_character_ids=None)
        result = query_current_first_heir_relationship_private_v1(
            _Driver(unavailable, [_frame()] * 3, heir=None),
            expected_native_revision=3)
        self.assertEqual(result["status"], "unavailable")
        self.assertIsNone(result["heir_character_id"])

    def test_mcp_read_only_tool_is_local_opt_in_only(self) -> None:
        from mcp import Client
        from xar_autoplayer.bridge.mcp_server import create_server, main, parser

        class McpDriver:
            allow_private_current_first_heir_relationship_query = False

            def query_current_first_heir_relationship_private_v1(
                self, *, expected_native_revision: int,
            ) -> dict[str, object]:
                return {"native_revision": expected_native_revision,
                        "status": "unavailable"}

        self.assertFalse(parser().parse_args([]).private_current_first_heir_relationship_query)
        with self.assertRaisesRegex(ValueError, "native-headless stdio"):
            main(["--driver", "native-headless", "--transport", "streamable-http",
                  "--private-current-first-heir-relationship-query"])

        async def check() -> None:
            driver = McpDriver()
            name = "ck3_query_current_first_heir_relationship_private_v1"
            async with Client(create_server(driver)) as client:
                names = {tool.name for tool in (await client.list_tools()).tools}
                self.assertNotIn(name, names)
            driver.allow_private_current_first_heir_relationship_query = True
            async with Client(create_server(driver)) as client:
                tools = {tool.name: tool for tool in (await client.list_tools()).tools}
                self.assertTrue(tools[name].annotations.read_only_hint)
                result = await client.call_tool(name, {"expected_native_revision": 3})
                self.assertFalse(result.is_error)
                self.assertEqual(result.structured_content["native_revision"], 3)

        asyncio.run(check())


if __name__ == "__main__":
    unittest.main()
