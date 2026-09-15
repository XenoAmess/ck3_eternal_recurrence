"""Exact-build protocol fixture for the unadvertised paused marriage query."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.marriage_matchmaking_private_transport import (
    PRIVATE_RANKED_MARRIAGE_STEP_V1,
    query_ranked_marriage_private_v1,
)


def _paused_frame() -> dict[str, object]:
    return {
        "native_revision": 693,
        "date_raw": 53178264,
        "paused": True,
        "map_ready": True,
        "played_character": {"character_id": 29829, "alive": True},
    }


def _native_observation() -> dict[str, object]:
    # Field names and bounds come from SerializeMarriageMatchmakingObservationV1
    # for CK3 1.19.0.6, not from an application-level marriage choice.
    return {
        "private_build": True,
        "advertised": False,
        "status": "available",
        "exact_build": "1.19.0.6",
        "snapshot_id": "native:693",
        "public_revision": 693,
        "native_revision": 693,
        "proof_epoch": 4,
        "date_raw": 53178264,
        "subject_character_id": 29829,
        "matchmaker_character_id": 29829,
        "religion_projection": "native_final_results_only",
        "candidates": [{
            "rank": 1,
            "subject_character_id": 29829,
            "matchmaker_character_id": 29829,
            "candidate_character_id": 30001,
            "native_candidate_score": 99,
            "pair_roles": {
                "actor_character_id": 29829,
                "recipient_character_id": 30001,
                "secondary_actor_character_id": 29829,
                "secondary_recipient_character_id": 30001,
                "intermediary_character_id": 0,
            },
            "complete_can_send": True,
            "complete_can_send_status_raw": 0,
            "recipient_ai_accept_raw": 250000,
            "recipient_ai_accept_scale": 100000,
            "recipient_answer_status_raw": 0,
            "recipient_answer_allows_send": True,
            "predicted_outcome": "marriage",
        }],
        "readiness": {
            key: True for key in (
                "ranked_candidates_ready", "pair_character_ids_ready",
                "native_score_ready", "complete_can_send_ready",
                "recipient_ai_accept_ready", "recipient_answer_ready",
                "predicted_outcome_ready", "same_frame_ready",
            )
        },
    }


class _Endpoint:
    def __init__(self) -> None:
        self.request: dict[str, object] | None = None

    def send(self, request: dict[str, object]) -> None:
        self.request = request


class _State:
    def __init__(self, result: dict[str, object] | None) -> None:
        self.result = result
        self.received_id: str | None = None

    def wait_for_command_result(self, request_id: str, timeout_seconds: float) -> dict[str, object] | None:
        self.received_id = request_id
        return self.result


class _Driver:
    def __init__(self, result: dict[str, object] | None, frames: list[dict[str, object]]) -> None:
        self.endpoint = _Endpoint()
        self.state = _State(result)
        self.frames = frames

    def take_snapshot(self) -> dict[str, object]:
        return self.frames.pop(0)


def _reply(status: str, **fields: object) -> dict[str, object]:
    return {"ok": True, "result": {
        "step": PRIVATE_RANKED_MARRIAGE_STEP_V1,
        "accepted": True,
        "status": status,
        **fields,
    }}


class PrivateRankedMarriageTransportTests(unittest.TestCase):
    def test_exact_build_ranked_row_arrives_from_one_paused_native_frame(self) -> None:
        driver = _Driver(
            _reply("available", query_sequence=1,
                   ranked_marriage_observation=_native_observation()),
            [_paused_frame(), _paused_frame()],
        )
        result = query_ranked_marriage_private_v1(driver, expected_native_revision=693)
        self.assertEqual(result["status"], "available")
        self.assertEqual(result["observation"]["candidates"][0]["candidate_character_id"], 30001)
        self.assertEqual(driver.endpoint.request["step"], PRIVATE_RANKED_MARRIAGE_STEP_V1)
        self.assertEqual(driver.endpoint.request["expected_revision"], 693)
        self.assertEqual(driver.state.received_id, driver.endpoint.request["request_id"])

    def test_unavailable_remains_typed_and_requires_same_frame(self) -> None:
        driver = _Driver(
            _reply("unavailable", unavailable_reason="paused_main_thread_not_observed"),
            [_paused_frame(), _paused_frame()],
        )
        result = query_ranked_marriage_private_v1(driver, expected_native_revision=693)
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["unavailable_reason"], "paused_main_thread_not_observed")

    def test_red_and_missing_result_are_not_reported_as_available(self) -> None:
        driver = _Driver({"ok": False, "error": "mailbox submit=busy"}, [_paused_frame()])
        with self.assertRaisesRegex(BridgeUnavailableError, "RED: mailbox submit=busy"):
            query_ranked_marriage_private_v1(driver, expected_native_revision=693)
        driver = _Driver(None, [_paused_frame()])
        with self.assertRaisesRegex(BridgeUnavailableError, "timed out"):
            query_ranked_marriage_private_v1(driver, expected_native_revision=693)

    def test_frame_drift_does_not_consume_a_ranked_result(self) -> None:
        changed = deepcopy(_paused_frame())
        changed["date_raw"] += 1
        driver = _Driver(
            _reply("available", query_sequence=1,
                   ranked_marriage_observation=_native_observation()),
            [_paused_frame(), changed],
        )
        with self.assertRaisesRegex(BridgeUnavailableError, "frame changed"):
            query_ranked_marriage_private_v1(driver, expected_native_revision=693)


if __name__ == "__main__":
    unittest.main()
