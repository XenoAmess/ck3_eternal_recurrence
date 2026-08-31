from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.zhongguo_ai_owned_case_snapshot_contract import (
    ZHONGGUO_AI_OWNED_CASE_BACKGROUND_ROUTE_V1,
    ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_ALLOWLIST_ID,
    ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_BACKEND_ID,
    ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_BRIDGE_VERSION,
    ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CASE_KIND,
    ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CONSUMER_ID,
    ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256,
    ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_GAME_ADAPTER_ID,
    ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_GAME_VERSION,
    ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_SOURCE_BACKEND_ID,
    ZhongguoAiOwnedCaseQueryV1,
    normalize_native_zhongguo_ai_owned_case_snapshot_v1,
    normalize_zhongguo_ai_owned_case_snapshot_v1_response,
    parse_query_zhongguo_ai_owned_case_snapshot_v1_step,
    query_zhongguo_ai_owned_case_snapshot_v1_step,
)


NATIVE_REVISION = 91
PUBLIC_REVISION = 12
CONNECTION_GENERATION = 5
DATE_RAW = 730_211
PLAYER = 100
OWNER = 200
SUBJECT = 300
NONCE = "zg361.ai-case:91"
SNAPSHOT_ID = "native-headless:zg361-ai-case:91"


def _available(value: object) -> dict[str, object]:
    return {"status": "available", "value": value, "unavailable_reason": None}


def _unavailable(reason: str) -> dict[str, object]:
    return {"status": "unavailable", "value": None, "unavailable_reason": reason}


def _query(
    *, owner: int = OWNER, subject: int = SUBJECT
) -> ZhongguoAiOwnedCaseQueryV1:
    return ZhongguoAiOwnedCaseQueryV1(owner, subject, NONCE)


def _provenance() -> dict[str, str]:
    return {
        "game_version": ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_GAME_VERSION,
        "executable_sha256": (
            ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256
        ),
        "backend_id": ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_BACKEND_ID,
        "consumer_id": ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CONSUMER_ID,
        "allowlist_id": ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_ALLOWLIST_ID,
        "variable_context_for_scope_rva": "0x3329A40",
        "character_storage_slot_rva": "0x570C130",
        "primary_title_rva": "0x25F3350",
        "immediate_liege_rva": "0x2613480",
        "government_rva": "0x26165B0",
        "is_human_player_rva": "0x28BCEB0",
    }


def _readiness(**overrides: bool) -> dict[str, bool]:
    result = {
        "owner_eligibility_ready": True,
        "case_identity_ready": True,
        "stage_ready": True,
        "route_ready": True,
        "receipt_ready": True,
        "same_frame_ready": True,
        "ready": True,
    }
    result.update(overrides)
    return result


def _frame(
    *,
    title_tier: int = 3,
    title_tier_key: str = "duchy",
    state: int = 7,
    active: bool = True,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "available",
        "case_kind": ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CASE_KIND,
        "request_nonce": NONCE,
        "snapshot_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "paused": True,
        "player_character_id": PLAYER,
        "requested_owner_character_id": OWNER,
        "subject_character_id": SUBJECT,
        "owner_eligibility": {
            "owner_character_id": _available(OWNER),
            "owner_alive": _available(True),
            "owner_is_ai": _available(True),
            "primary_title_id": _available(8_001),
            "primary_title_tier_raw": _available(title_tier),
            "primary_title_tier_key": _available(title_tier_key),
            "government_key": _available("celestial_government"),
            "subject_immediate_liege_character_id": _available(OWNER),
            "subject_is_direct_subject": _available(True),
            "authorized": _available(True),
        },
        "case": {
            "owner_character_id": _available(OWNER),
            "subject_character_id": _available(SUBJECT),
            "cycle_serial": _available(7),
            "case_serial": _available(903),
            "state": _available(state),
            "active": _available(active),
            "revision": _available(5),
            "timeline_serial": _available(6),
            "feedback_revision": _available(4),
        },
        "stage": {
            "state": _available(state),
            "key": _available(
                "calibration_open" if state == 7 else "published"
            ),
            "active": _available(active),
        },
        "route": {
            "kind": _available(ZHONGGUO_AI_OWNED_CASE_BACKGROUND_ROUTE_V1),
            "visible_event_allowed": _available(False),
            "owner_is_ai": _available(True),
            "manager_eligible": _available(True),
            "direct_subject_eligible": _available(True),
        },
        "policy": {
            "policy_id": _available("mechanism_039"),
            "choice": _available(1),
        },
        "operation": {
            "operation_id": _available(39),
            "operation_key": _available("roster_lock"),
            "hook": _available("roster_lock"),
            "pre_state": _available(1),
            "post_state": _available(1),
        },
        "receipt": {
            "status": "recorded",
            "key": _available("roster_lock"),
            "owner_character_id": _available(OWNER),
            "subject_character_id": _available(SUBJECT),
            "cycle_serial": _available(7),
            "case_serial": _available(903),
            "state": _available(1),
            "choice": _available(1),
        },
        "readiness": _readiness(),
        "unavailable_reason": None,
        "provenance": _provenance(),
    }


def _not_recorded_hegemony_frame() -> dict[str, object]:
    frame = _frame(
        title_tier=6, title_tier_key="hegemony", state=8, active=False
    )
    frame["policy"] = {
        "policy_id": _unavailable("no_operation_recorded"),
        "choice": _available(0),
    }
    frame["operation"] = {
        "operation_id": _available(0),
        "operation_key": _unavailable("no_operation_recorded"),
        "hook": _unavailable("no_operation_recorded"),
        "pre_state": _unavailable("receipt_not_recorded"),
        "post_state": _unavailable("receipt_not_recorded"),
    }
    frame["receipt"] = {
        "status": "not_recorded",
        **{
            key: _unavailable("receipt_not_recorded")
            for key in (
                "key",
                "owner_character_id",
                "subject_character_id",
                "cycle_serial",
                "case_serial",
                "state",
                "choice",
            )
        },
    }
    return frame


def _unavailable_frame(
    reason: str = "case_not_found",
    *,
    owner: int = OWNER,
) -> dict[str, object]:
    frame = _frame()
    frame["status"] = "unavailable"
    frame["requested_owner_character_id"] = owner
    frame["unavailable_reason"] = reason
    for group_name in (
        "owner_eligibility",
        "case",
        "stage",
        "route",
        "policy",
        "operation",
    ):
        group = frame[group_name]
        if not isinstance(group, dict):
            raise AssertionError(group_name)
        for key in group:
            group[key] = _unavailable("case_unavailable")
    receipt = frame["receipt"]
    if not isinstance(receipt, dict):
        raise AssertionError("receipt")
    receipt["status"] = "unavailable"
    for key in set(receipt) - {"status"}:
        receipt[key] = _unavailable("case_unavailable")
    frame["readiness"] = {
        key: False
        for key in (
            "owner_eligibility_ready",
            "case_identity_ready",
            "stage_ready",
            "route_ready",
            "receipt_ready",
            "same_frame_ready",
            "ready",
        )
    }
    if reason in {"case_not_found", "owner_filter_mismatch"}:
        frame["readiness"]["same_frame_ready"] = True
    return frame


def _response(frame: dict[str, object] | None = None) -> dict[str, object]:
    result = copy.deepcopy(frame if frame is not None else _frame())
    result.update(
        {
            "build": {
                "version": ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_GAME_VERSION,
                "exe_sha256": (
                    ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256
                ),
            },
            "source": {
                "bridge_version": (
                    ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_BRIDGE_VERSION
                ),
                "game_adapter_id": (
                    ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_GAME_ADAPTER_ID
                ),
                "backend_id": (
                    ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_SOURCE_BACKEND_ID
                ),
                "consumer_id": (
                    ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CONSUMER_ID
                ),
                "connection_generation": CONNECTION_GENERATION,
                "snapshot_id": SNAPSHOT_ID,
                "revision": PUBLIC_REVISION,
                "native_revision": NATIVE_REVISION,
                "date_raw": DATE_RAW,
                "paused": True,
                "player_character_id": PLAYER,
            },
            "binding": {
                "request_nonce": NONCE,
                "snapshot_id": SNAPSHOT_ID,
                "revision": PUBLIC_REVISION,
                "native_revision": NATIVE_REVISION,
                "connection_generation": CONNECTION_GENERATION,
                "date_raw": DATE_RAW,
                "paused": True,
                "player_character_id": PLAYER,
                "owner_character_id": OWNER,
                "subject_character_id": SUBJECT,
                "expected_revision": PUBLIC_REVISION,
            },
        }
    )
    return result


def _normalize(frame: dict[str, object]) -> dict[str, object]:
    return normalize_native_zhongguo_ai_owned_case_snapshot_v1(
        frame,
        expected_query=_query(),
        expected_snapshot_revision=NATIVE_REVISION,
        expected_date_raw=DATE_RAW,
        expected_player_character_id=PLAYER,
    )


class ZhongguoAiOwnedCaseSnapshotContractTests(unittest.TestCase):
    def test_step_round_trip_is_canonical_and_has_no_variable_name(self) -> None:
        step = query_zhongguo_ai_owned_case_snapshot_v1_step(
            OWNER, SUBJECT, NONCE
        )
        self.assertEqual(
            parse_query_zhongguo_ai_owned_case_snapshot_v1_step(step),
            _query(),
        )
        self.assertNotIn("zg361_", step)
        prefix, nonce_hex = step.rsplit("-", 1)
        for malformed in (
            step.replace(f"-{OWNER}-", f"-0{OWNER}-"),
            step.replace(f"-{SUBJECT}-", f"-0{SUBJECT}-"),
            f"{prefix}-{nonce_hex.upper()}",
            query_zhongguo_ai_owned_case_snapshot_v1_step(
                OWNER, SUBJECT, NONCE
            ).replace(f"-{SUBJECT}-", f"-{OWNER}-"),
            step + "00",
        ):
            with self.subTest(malformed=malformed):
                self.assertIsNone(
                    parse_query_zhongguo_ai_owned_case_snapshot_v1_step(
                        malformed
                    )
                )

    def test_authorized_ai_duke_recorded_receipt_is_ready(self) -> None:
        normalized = _normalize(_frame())
        self.assertTrue(normalized["readiness"]["ready"])
        self.assertEqual(
            normalized["owner_eligibility"]["primary_title_tier_key"][
                "value"
            ],
            "duchy",
        )
        self.assertEqual(normalized["route"]["kind"]["value"],
                         ZHONGGUO_AI_OWNED_CASE_BACKGROUND_ROUTE_V1)
        self.assertFalse(
            normalized["route"]["visible_event_allowed"]["value"]
        )

    def test_authorized_ai_hegemony_not_recorded_is_typed_ready(self) -> None:
        normalized = _normalize(_not_recorded_hegemony_frame())
        self.assertTrue(normalized["readiness"]["ready"])
        self.assertEqual(normalized["stage"]["key"]["value"], "published")
        self.assertEqual(normalized["receipt"]["status"], "not_recorded")
        self.assertEqual(
            normalized["receipt"]["key"]["unavailable_reason"],
            "receipt_not_recorded",
        )

    def test_eligibility_case_and_route_cross_bindings_are_strict(self) -> None:
        mutations = {
            "human_owner": lambda row: row["owner_eligibility"][
                "owner_is_ai"
            ].__setitem__("value", False),
            "wrong_government": lambda row: row["owner_eligibility"][
                "government_key"
            ].__setitem__("value", "feudal_government"),
            "county_owner": lambda row: row["owner_eligibility"][
                "primary_title_tier_raw"
            ].__setitem__("value", 2),
            "wrong_liege": lambda row: row["owner_eligibility"][
                "subject_immediate_liege_character_id"
            ].__setitem__("value", OWNER + 1),
            "wrong_case_owner": lambda row: row["case"][
                "owner_character_id"
            ].__setitem__("value", OWNER + 1),
            "visible_event": lambda row: row["route"][
                "visible_event_allowed"
            ].__setitem__("value", True),
            "wrong_route": lambda row: row["route"]["kind"].__setitem__(
                "value", "player_visible_event"
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                frame = _frame()
                mutate(frame)
                with self.assertRaises(ValueError):
                    _normalize(frame)

    def test_stage_and_receipt_typed_negatives_remain_available_not_ready(self) -> None:
        stage_frame = _frame(state=8, active=True)
        stage_frame["stage"]["key"] = _unavailable("stage_inconsistent")
        stage_frame["readiness"] = _readiness(
            stage_ready=False, ready=False
        )
        normalized_stage = _normalize(stage_frame)
        self.assertEqual(normalized_stage["status"], "available")
        self.assertFalse(normalized_stage["readiness"]["ready"])

        receipt_frame = _frame()
        receipt_frame["receipt"]["status"] = "unavailable"
        for key in set(receipt_frame["receipt"]) - {"status"}:
            receipt_frame["receipt"][key] = _unavailable(
                "receipt_inconsistent"
            )
        receipt_frame["operation"]["pre_state"] = _unavailable(
            "receipt_inconsistent"
        )
        receipt_frame["operation"]["post_state"] = _unavailable(
            "receipt_inconsistent"
        )
        receipt_frame["readiness"] = _readiness(
            receipt_ready=False, ready=False
        )
        normalized_receipt = _normalize(receipt_frame)
        self.assertFalse(normalized_receipt["readiness"]["receipt_ready"])

        leaked = copy.deepcopy(receipt_frame)
        leaked["receipt"]["owner_character_id"] = _available(OWNER)
        with self.assertRaises(ValueError):
            _normalize(leaked)

    def test_unknown_operation_is_typed_but_cannot_claim_readiness(self) -> None:
        frame = _frame()
        frame["policy"] = {
            "policy_id": _unavailable("unknown_allowlisted_operation"),
            "choice": _available(2),
        }
        frame["operation"] = {
            "operation_id": _available(41),
            "operation_key": _unavailable("unknown_allowlisted_operation"),
            "hook": _unavailable("unknown_allowlisted_operation"),
            "pre_state": _unavailable("receipt_inconsistent"),
            "post_state": _unavailable("receipt_inconsistent"),
        }
        frame["receipt"] = {
            "status": "unavailable",
            **{
                key: _unavailable("receipt_inconsistent")
                for key in (
                    "key",
                    "owner_character_id",
                    "subject_character_id",
                    "cycle_serial",
                    "case_serial",
                    "state",
                    "choice",
                )
            },
        }
        frame["readiness"] = _readiness(
            receipt_ready=False, ready=False
        )
        normalized = _normalize(frame)
        self.assertFalse(normalized["readiness"]["ready"])

        impossible = copy.deepcopy(frame)
        impossible["operation"]["operation_id"] = _available(0)
        impossible["policy"]["policy_id"] = _unavailable(
            "no_operation_recorded"
        )
        impossible["operation"]["operation_key"] = _unavailable(
            "no_operation_recorded"
        )
        impossible["operation"]["hook"] = _unavailable(
            "no_operation_recorded"
        )
        with self.assertRaises(ValueError):
            _normalize(impossible)

    def test_player_owner_and_case_absence_are_typed_unavailable(self) -> None:
        player_owner = _unavailable_frame(
            "owner_is_played_character", owner=PLAYER
        )
        normalized_player = normalize_native_zhongguo_ai_owned_case_snapshot_v1(
            player_owner,
            expected_query=_query(owner=PLAYER),
            expected_snapshot_revision=NATIVE_REVISION,
            expected_date_raw=DATE_RAW,
            expected_player_character_id=PLAYER,
        )
        self.assertEqual(
            normalized_player["unavailable_reason"],
            "owner_is_played_character",
        )
        self.assertFalse(normalized_player["readiness"]["same_frame_ready"])

        absent = _normalize(_unavailable_frame())
        self.assertEqual(absent["unavailable_reason"], "case_not_found")
        self.assertTrue(absent["readiness"]["same_frame_ready"])

    def test_public_response_binds_owner_subject_source_and_revision(self) -> None:
        response = _response()
        normalized = normalize_zhongguo_ai_owned_case_snapshot_v1_response(
            response,
            expected_query=_query(),
            expected_snapshot_id=SNAPSHOT_ID,
            expected_revision=PUBLIC_REVISION,
            expected_native_revision=NATIVE_REVISION,
            expected_connection_generation=CONNECTION_GENERATION,
            expected_date_raw=DATE_RAW,
            expected_player_character_id=PLAYER,
        )
        self.assertEqual(normalized["binding"]["owner_character_id"], OWNER)
        self.assertEqual(
            normalized["binding"]["subject_character_id"], SUBJECT
        )

        for path, value in (
            (("binding", "owner_character_id"), OWNER + 1),
            (("binding", "expected_revision"), PUBLIC_REVISION + 1),
            (("source", "consumer_id"), "generic-variable-reader"),
            (("source", "connection_generation"), CONNECTION_GENERATION + 1),
            (("build", "version"), "1.19.0.5"),
        ):
            with self.subTest(path=path):
                mutated = copy.deepcopy(response)
                mutated[path[0]][path[1]] = value
                with self.assertRaises(ValueError):
                    normalize_zhongguo_ai_owned_case_snapshot_v1_response(
                        mutated,
                        expected_query=_query(),
                        expected_snapshot_id=SNAPSHOT_ID,
                        expected_revision=PUBLIC_REVISION,
                        expected_native_revision=NATIVE_REVISION,
                        expected_connection_generation=CONNECTION_GENERATION,
                        expected_date_raw=DATE_RAW,
                        expected_player_character_id=PLAYER,
                    )


if __name__ == "__main__":
    unittest.main()
