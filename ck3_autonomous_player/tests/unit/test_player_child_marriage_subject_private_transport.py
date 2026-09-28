"""Focused no-launch contract for one specified player-child marriage read."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import asyncio
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError
from xar_autoplayer.bridge.player_child_marriage_subject_private_transport import (
    SCHEMA, STEP, query_player_child_marriage_subject_private_v1,
)


def _frame() -> dict[str, object]:
    return {"native_revision": 3, "revision": 4, "date_raw": 53215920,
            "paused": True, "map_ready": True,
            "played_character": {"character_id": 29829, "alive": True}}


def _row(answer: int = 0) -> dict[str, object]:
    return {"played_character_id": 29829, "subject_character_id": 37265,
            "candidate_character_id": 40001,
            "recipient_matchmaker_character_id": 40000,
            "complete_can_send": True, "recipient_ai_accept_raw": 500,
            "recipient_answer_status_raw": answer,
            "recipient_answer_allows_send": answer != 2}


def _reply(**fields: object) -> dict[str, object]:
    return {"ok": True, "result": {
        "step": STEP, "accepted": True, "private_build": True,
        "read_only": True, "advertised": False,
        "native_revision": 3, "query_sequence": 5,
        "subject_source": "specified_player_child",
        "subject_character_id": 37265, "status": "available",
        "unavailable_reason": None, "player_child_verified": True,
        "adult_measure_raw": 18, "adult_threshold_raw": 16, "adult": True,
        "house_id": 174, "dynasty_id": 144,
        "employer_character_id": 29829,
        "bilateral_verified": True, "betrothed_character_id": None,
        "primary_spouse_character_id": None, "spouse_character_ids": [],
        "family_candidates": [_row()],
        "arrange_marriage_diagnostics": {"slots_scanned": 10,
                                         "storage_capacity": 10},
        "family_subject_role_mismatches": 0, **fields,
    }}


class _Endpoint:
    request: dict[str, object] | None = None

    def send(self, request: dict[str, object]) -> None:
        self.request = request


class _State:
    def __init__(self, reply: dict[str, object]) -> None:
        self.reply = reply

    def wait_for_command_result(self, request_id: str,
                                timeout_seconds: float) -> dict[str, object]:
        return self.reply


class _Driver:
    allow_private_player_child_marriage_subject_query = True

    def __init__(self, reply: dict[str, object],
                 frames: list[dict[str, object]]) -> None:
        self.endpoint = _Endpoint()
        self.state = _State(reply)
        self.frames = frames

    def take_snapshot(self) -> dict[str, object]:
        return self.frames.pop(0)


class PlayerChildMarriageSubjectPrivateTests(unittest.TestCase):
    def test_specified_child_must_be_native_verified(self) -> None:
        driver = _Driver(_reply(), [_frame(), _frame()])
        result = query_player_child_marriage_subject_private_v1(
            driver, expected_native_revision=3, subject_character_id=37265)
        self.assertEqual(result["schema"], SCHEMA)
        self.assertTrue(result["player_child_verified"])
        self.assertEqual(result["house_id"], 174)
        self.assertEqual(result["employer_character_id"], 29829)
        self.assertEqual(len(result["native_legal_candidates"]), 1)
        self.assertEqual(driver.endpoint.request["subject_character_id"], 37265)
        self.assertEqual(driver.endpoint.request["step"], STEP)

        unavailable = _reply(status="unavailable",
                             unavailable_reason="not_player_child",
                             player_child_verified=False,
                             family_candidates=[], adult_measure_raw=None,
                             adult=False, bilateral_verified=False,
                             spouse_character_ids=None)
        result = query_player_child_marriage_subject_private_v1(
            _Driver(unavailable, [_frame(), _frame()]),
            expected_native_revision=3, subject_character_id=37265)
        self.assertEqual(result["unavailable_reason"], "not_player_child")
        self.assertNotIn("candidates", result)

    def test_answer_and_frame_are_independent_gates(self) -> None:
        refused = _reply(family_candidates=[_row(2)])
        result = query_player_child_marriage_subject_private_v1(
            _Driver(refused, [_frame(), _frame()]),
            expected_native_revision=3, subject_character_id=37265)
        self.assertEqual(result["native_legal_candidates"], [])
        changed = deepcopy(_frame())
        changed["date_raw"] += 1
        with self.assertRaisesRegex(BridgeUnavailableError, "frame changed"):
            query_player_child_marriage_subject_private_v1(
                _Driver(_reply(), [_frame(), changed]),
                expected_native_revision=3, subject_character_id=37265)

    def test_opt_in_and_identity_are_required(self) -> None:
        driver = _Driver(_reply(), [_frame(), _frame()])
        driver.allow_private_player_child_marriage_subject_query = False
        with self.assertRaises(UnsupportedStepError):
            query_player_child_marriage_subject_private_v1(
                driver, expected_native_revision=3, subject_character_id=37265)
        self.assertIsNone(driver.endpoint.request)
        with self.assertRaisesRegex(BridgeUnavailableError, "identity changed"):
            query_player_child_marriage_subject_private_v1(
                _Driver(_reply(subject_character_id=38822), [_frame(), _frame()]),
                expected_native_revision=3, subject_character_id=37265)

    def test_mcp_registration_is_local_explicit_opt_in(self) -> None:
        from mcp import Client
        from xar_autoplayer.bridge.mcp_server import create_server, main, parser

        class McpDriver:
            allow_private_player_child_marriage_subject_query = False

            def query_player_child_marriage_subject_private_v1(
                self, *, expected_native_revision: int, subject_character_id: int,
            ) -> dict[str, object]:
                return {"native_revision": expected_native_revision,
                        "subject_character_id": subject_character_id}

        self.assertFalse(
            parser().parse_args([]).private_player_child_marriage_subject_query
        )
        with self.assertRaisesRegex(ValueError, "native-headless stdio"):
            main(["--driver", "native-headless", "--transport", "streamable-http",
                  "--private-player-child-marriage-subject-query"])

        async def check() -> None:
            driver = McpDriver()
            name = "ck3_query_player_child_marriage_subject_private_v1"
            async with Client(create_server(driver)) as client:
                names = {tool.name for tool in (await client.list_tools()).tools}
                self.assertNotIn(name, names)
            driver.allow_private_player_child_marriage_subject_query = True
            async with Client(create_server(driver)) as client:
                tools = {tool.name: tool for tool in (await client.list_tools()).tools}
                self.assertTrue(tools[name].annotations.read_only_hint)
                result = await client.call_tool(
                    name, {"expected_native_revision": 3,
                           "subject_character_id": 37265})
                self.assertFalse(result.is_error)
                self.assertEqual(result.structured_content["subject_character_id"],
                                 37265)

        asyncio.run(check())
