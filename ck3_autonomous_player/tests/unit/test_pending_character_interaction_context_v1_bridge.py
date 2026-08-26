from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.driver import (
    BridgeUnavailableError,
    UnsupportedStepError,
)
from xar_autoplayer.bridge.mcp_server import (
    _ck3_query_pending_character_interaction_context_v1,
    create_server,
)
from xar_autoplayer.bridge.native_driver import (
    NativeHeadlessGameplayDriver,
    _action_steps,
)
from xar_autoplayer.bridge.pending_character_interaction_context_contract import (
    PENDING_CHARACTER_INTERACTION_CONTEXT_V1_BACKEND_ID,
    PENDING_CHARACTER_INTERACTION_CONTEXT_V1_EXECUTABLE_SHA256,
    PENDING_CHARACTER_INTERACTION_CONTEXT_V1_GAME_VERSION,
    QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_CAPABILITY,
    QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP,
    normalize_pending_character_interaction_context_v1,
)
from xar_autoplayer.bridge.service import GameplayBridgeService


PENDING_ID = 16_777_249
NATIVE_REVISION = 41
PUBLIC_REVISION = 7
DATE_RAW = 53_178_264
STEP = QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP


def _build() -> dict[str, str]:
    return {
        "version": PENDING_CHARACTER_INTERACTION_CONTEXT_V1_GAME_VERSION,
        "exe_sha256": (
            PENDING_CHARACTER_INTERACTION_CONTEXT_V1_EXECUTABLE_SHA256
        ),
    }


def _provenance() -> dict[str, str]:
    return {
        "backend_id": PENDING_CHARACTER_INTERACTION_CONTEXT_V1_BACKEND_ID,
        "pending_storage_slot_rva": "0x57BF1C8",
        "character_storage_slot_rva": "0x570C130",
        "expiration_days_rva": "0x570F528",
        "local_routing_predicate_rva": "0x1266BA0",
        "reply_validator_rva": "0x26B3540",
        "auto_accept_trigger_evaluator_rva": "0x334C510",
        "target_type_registry_getter_rva": "0x33C52B0",
        "target_type_registry_rva": "0x4FFE290",
        "script_identifier_name_rva": "0x3B58970",
        "reply_primary_vtable_rva": "0x4082930",
        "reply_secondary_vtable_rva": "0x4082900",
    }


def _legality(
    *,
    accept: bool = True,
    reject: bool = True,
    block: bool = True,
    acknowledge: bool = False,
) -> dict[str, dict[str, object]]:
    values = {
        "accept": accept,
        "reject": reject,
        "block": block,
        "acknowledge": acknowledge,
    }
    return {
        key: {
            "status": "available",
            "allowed": allowed,
            "reason": None if allowed else f"{key}_not_legal",
        }
        for key, allowed in values.items()
    }


def _readiness(*, target_present: bool = False) -> dict[str, object]:
    reasons = []
    if target_present:
        reasons.append("target_generic_scope_payload_identity_not_closed")
    reasons.extend(
        [
            "structured_costs_unavailable",
            "structured_exchanges_unavailable",
            "structured_effect_preview_unavailable",
        ]
    )
    return {
        "stable_definition_ready": True,
        "roles_ready": True,
        "target_type_key_ready": True,
        "target_typed_identity_ready": not target_present,
        "send_options_ready": True,
        "routing_ready": True,
        "deadline_ready": True,
        "auto_accept_ready": True,
        "reply_legality_ready": True,
        "structured_terms_ready": False,
        "same_frame_ready": True,
        "interaction_semantic_decision_ready": False,
        "not_ready_reasons": reasons,
    }


def _target(*, present: bool = False) -> dict[str, object]:
    if not present:
        return {
            "present": False,
            "raw_type_index": 0,
            "raw_16_bytes_hex": "0" * 32,
            "type_key_status": "absent",
            "type_key": None,
            "type_key_reason": None,
            "typed_identity_status": "absent",
            "typed_identity": None,
            "typed_identity_reason": None,
        }
    return {
        "present": True,
        "raw_type_index": 7,
        "raw_16_bytes_hex": "07000100785634120000000000000000",
        "type_key_status": "available",
        "type_key": "title",
        "type_key_reason": None,
        "typed_identity_status": "unavailable",
        "typed_identity": None,
        "typed_identity_reason": (
            "generic_scope_payload_identity_not_closed"
        ),
    }


def _frame(
    status: str = "available",
    *,
    reason: str | None = None,
    target_present: bool = False,
    notification: bool = False,
) -> dict[str, object]:
    if status != "available":
        selected_reason = reason or (
            "send_option_count_mismatch"
            if status == "invalid"
            else "pending_generation_mismatch"
        )
        unavailable_legality = {
            key: {
                "status": "unavailable",
                "allowed": False,
                "reason": selected_reason,
            }
            for key in ("accept", "reject", "block", "acknowledge")
        }
        return {
            "schema": "pending-character-interaction-context-v1",
            "schema_version": 1,
            "status": status,
            "snapshot_revision": NATIVE_REVISION,
            "date_raw": DATE_RAW,
            "pending_interaction_id": PENDING_ID,
            "reason": selected_reason,
            "build": _build(),
            "definition": None,
            "roles": None,
            "target": None,
            "send_options": None,
            "routing": None,
            "deadline": None,
            "auto_accept": None,
            "legality": unavailable_legality,
            "terms": None,
            "readiness": {
                key: (
                    [selected_reason]
                    if key == "not_ready_reasons"
                    else False
                )
                for key in _readiness()
            },
            "provenance": _provenance(),
        }
    legality = (
        _legality(
            accept=False,
            reject=False,
            block=False,
            acknowledge=True,
        )
        if notification
        else _legality()
    )
    return {
        "schema": "pending-character-interaction-context-v1",
        "schema_version": 1,
        "status": "available",
        "snapshot_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "pending_interaction_id": PENDING_ID,
        "reason": None,
        "build": _build(),
        "definition": {
            "canonical_key": "fixture_request_support_interaction",
            "deterministic_key_hash": 0x12345678,
            "runtime_ordinal": 42,
        },
        "roles": {
            "actor_character_id": 1001,
            "recipient_character_id": 2001,
            "secondary_actor_character_id": -1,
            "secondary_recipient_character_id": -1,
            "intermediary_character_id": -1,
        },
        "target": _target(present=target_present),
        "send_options": {
            "exclusive": False,
            "definition_count": 2,
            "context_count": 2,
            "rows": [
                {
                    "native_index": index,
                    "numeric_flag_identifier": 31_001 + index,
                    "selected": index == 0,
                    "is_shown": True,
                    "is_valid": True,
                    "canonical_flag_status": "unavailable",
                    "canonical_flag_key": None,
                    "canonical_flag_reason": (
                        "numeric_flag_identifier_string_mapping_not_closed"
                    ),
                }
                for index in range(2)
            ],
        },
        "routing": {
            "kind": 0,
            "played_character_id": 2001,
            "current_responder_role": "recipient",
            "reply_execution_channel": "recipient",
            "local_route": True,
            "auto_accept_notification": notification,
        },
        "deadline": {
            "age_days": 17,
            "expiration_days": 60,
            "remaining_days": 43,
            "expiry_boundary_status": "not_reached",
        },
        "auto_accept": {
            "status": "available",
            "value": notification,
            "reason": None,
        },
        "legality": legality,
        "terms": {
            "special_data_present": False,
            "structured_costs": {
                "status": "unavailable",
                "value": None,
                "reason": "structured_costs_unavailable",
            },
            "structured_exchanges": {
                "status": "unavailable",
                "value": None,
                "reason": "structured_exchanges_unavailable",
            },
            "structured_effect_preview": {
                "status": "unavailable",
                "value": None,
                "reason": "structured_effect_preview_unavailable",
            },
            "recipient_ai_acceptance_score": {
                "status": "unavailable",
                "value": None,
                "reason": "recipient_ai_acceptance_score_unavailable",
            },
            "recipient_ai_final_decision": {
                "status": "unavailable",
                "value": None,
                "reason": "recipient_ai_final_decision_unavailable",
            },
        },
        "readiness": _readiness(target_present=target_present),
        "provenance": _provenance(),
    }


def _native_result(status: str = "available") -> dict[str, object]:
    return {
        "step": STEP,
        "accepted": True,
        "status": status,
        "query_sequence": 12,
        "snapshot_revision": NATIVE_REVISION,
        "pending_character_interaction_context": _frame(status),
        "backend_id": "native-headless",
    }


_MIRROR_KEYS = (
    "schema",
    "schema_version",
    "date_raw",
    "pending_interaction_id",
    "reason",
    "build",
    "definition",
    "roles",
    "target",
    "send_options",
    "routing",
    "deadline",
    "auto_accept",
    "legality",
    "terms",
    "readiness",
    "provenance",
)


def _driver_result(status: str = "available") -> dict[str, object]:
    result = _native_result(status)
    frame = result["pending_character_interaction_context"]
    assert isinstance(frame, dict)
    for key in _MIRROR_KEYS:
        result[key] = copy.deepcopy(frame[key])
    result.update(
        {
            "pending_character_interaction_context_ready": False,
            "queried_snapshot_id": "pending-fixture:7",
            "queried_revision": PUBLIC_REVISION,
            "queried_native_revision": NATIVE_REVISION,
        }
    )
    return result


def _semantic_snapshot(
    revision: int = NATIVE_REVISION,
    *,
    paused: bool = True,
    pending_id: int = PENDING_ID,
) -> dict[str, object]:
    return {
        "type": "state_snapshot",
        "protocol_version": 1,
        "snapshot_id": f"native:{revision}",
        "revision": revision,
        "state": {
            "phase": "map_hud",
            "date": "1066.10.16",
            "date_raw": DATE_RAW,
            "speed": 1,
            "paused": paused,
            "map_ready": True,
            "history": [],
            "active_event": None,
            "pending_character_interaction": {
                "instance_id": pending_id,
                "sender_character_id": 1001,
                "auto_accept_notification": False,
            },
            "played_character": {"character_id": 2001, "alive": True},
            "one_life_settlement": None,
            "active_wars": [],
            "player_armies": [],
        },
    }


class PendingCharacterInteractionContextV1ContractTests(unittest.TestCase):
    def test_available_absent_target_preserves_semantic_red(self) -> None:
        frame = _frame()
        frame["target"]["raw_16_bytes_hex"] = (
            "0000deadbeef00000000000000000000"
        )
        normalized = normalize_pending_character_interaction_context_v1(
            frame,
            expected_pending_interaction_id=PENDING_ID,
            expected_date_raw=DATE_RAW,
            expected_snapshot_revision=NATIVE_REVISION,
        )

        self.assertEqual(normalized["status"], "available")
        self.assertEqual(
            normalized["definition"]["canonical_key"],
            "fixture_request_support_interaction",
        )
        self.assertEqual(normalized["target"]["type_key_status"], "absent")
        self.assertEqual(
            normalized["target"]["raw_16_bytes_hex"],
            "0000deadbeef00000000000000000000",
        )
        self.assertTrue(normalized["legality"]["accept"]["allowed"])
        self.assertFalse(
            normalized["readiness"][
                "interaction_semantic_decision_ready"
            ]
        )

    def test_absent_target_accepts_strings_from_a_real_json_wire(self) -> None:
        wire_frame = json.loads(json.dumps(_frame()))

        normalized = normalize_pending_character_interaction_context_v1(
            wire_frame,
            expected_pending_interaction_id=PENDING_ID,
            expected_date_raw=DATE_RAW,
            expected_snapshot_revision=NATIVE_REVISION,
        )

        self.assertEqual(normalized["target"]["type_key_status"], "absent")
        self.assertEqual(
            normalized["target"]["typed_identity_status"], "absent"
        )

    def test_present_target_requires_stable_type_key_but_stays_opaque(self) -> None:
        normalized = normalize_pending_character_interaction_context_v1(
            _frame(target_present=True),
            expected_pending_interaction_id=PENDING_ID,
            expected_date_raw=DATE_RAW,
            expected_snapshot_revision=NATIVE_REVISION,
        )

        self.assertEqual(normalized["target"]["type_key"], "title")
        self.assertEqual(
            normalized["target"]["typed_identity_status"], "unavailable"
        )
        self.assertFalse(
            normalized["readiness"]["target_typed_identity_ready"]
        )

    def test_intermediary_and_notification_channels_remain_distinct(self) -> None:
        intermediary = _frame()
        intermediary["roles"]["intermediary_character_id"] = 3001
        intermediary["routing"].update(
            {
                "kind": 1,
                "played_character_id": 3001,
                "current_responder_role": "intermediary",
                "reply_execution_channel": "intermediary",
            }
        )
        normalized = normalize_pending_character_interaction_context_v1(
            intermediary,
            expected_pending_interaction_id=PENDING_ID,
            expected_date_raw=DATE_RAW,
            expected_snapshot_revision=NATIVE_REVISION,
        )
        self.assertEqual(
            normalized["routing"]["current_responder_role"],
            "intermediary",
        )

        notification = normalize_pending_character_interaction_context_v1(
            _frame(notification=True),
            expected_pending_interaction_id=PENDING_ID,
            expected_date_raw=DATE_RAW,
            expected_snapshot_revision=NATIVE_REVISION,
        )
        self.assertTrue(
            notification["legality"]["acknowledge"]["allowed"]
        )
        self.assertFalse(notification["legality"]["accept"]["allowed"])

    def test_unavailable_and_invalid_frames_do_not_invent_state(self) -> None:
        for status in ("unavailable", "invalid"):
            with self.subTest(status=status):
                normalized = (
                    normalize_pending_character_interaction_context_v1(
                        _frame(status),
                        expected_pending_interaction_id=PENDING_ID,
                        expected_date_raw=DATE_RAW,
                        expected_snapshot_revision=NATIVE_REVISION,
                    )
                )
                self.assertIsNone(normalized["definition"])
                self.assertFalse(
                    normalized["legality"]["accept"]["allowed"]
                )
                self.assertFalse(
                    normalized["readiness"]["same_frame_ready"]
                )

    def test_full_generation_nested_counts_and_typed_boundaries_are_strict(self) -> None:
        mutations = {
            "generation": lambda row: row.__setitem__(
                "pending_interaction_id", PENDING_ID + 2**24
            ),
            "date": lambda row: row.__setitem__("date_raw", DATE_RAW + 1),
            "build": lambda row: row["build"].__setitem__(
                "version", "1.19.0.7"
            ),
            "target_type": lambda row: row["target"].__setitem__(
                "raw_type_index", 7
            ),
            "target_key": lambda row: row["target"].__setitem__(
                "type_key", "invented"
            ),
            "counts": lambda row: row["send_options"].__setitem__(
                "context_count", 1
            ),
            "row_identity": lambda row: row["send_options"]["rows"][0].__setitem__(
                "canonical_flag_key", "invented"
            ),
            "deadline": lambda row: row["deadline"].__setitem__(
                "remaining_days", 44
            ),
            "terms": lambda row: row["terms"]["structured_costs"].__setitem__(
                "value", 0
            ),
            "semantic_ready": lambda row: row["readiness"].__setitem__(
                "interaction_semantic_decision_ready", True
            ),
            "provenance": lambda row: row["provenance"].__setitem__(
                "reply_validator_rva", "0x0"
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                frame = _frame()
                mutate(frame)
                with self.assertRaises(ValueError):
                    normalize_pending_character_interaction_context_v1(
                        frame,
                        expected_pending_interaction_id=PENDING_ID,
                        expected_date_raw=DATE_RAW,
                        expected_snapshot_revision=NATIVE_REVISION,
                    )


class _FakeEndpoint:
    def __init__(self) -> None:
        self.pipe_name = r"\\.\pipe\xar_pending_context_v1_fixture"
        self.frames: list[dict[str, object]] = []
        self.on_frame = None
        self.on_disconnect = None
        self.send_hook = None

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame
        self.on_disconnect = on_disconnect

    def publish(self, frame: dict[str, object]) -> None:
        assert self.on_frame is not None
        self.on_frame(frame)

    def send(self, frame: dict[str, object]) -> None:
        self.frames.append(frame)
        if self.send_hook is not None:
            self.send_hook(frame)

    def close(self) -> None:
        return None

    def transport_error(self) -> str | None:
        return None


def _native_driver(
    *, paused: bool = True
) -> tuple[NativeHeadlessGameplayDriver, _FakeEndpoint]:
    endpoint = _FakeEndpoint()
    driver = NativeHeadlessGameplayDriver(
        endpoint.pipe_name,
        endpoint=endpoint,
        command_timeout_seconds=0.1,
    )
    endpoint.publish(
        {
            "type": "hello",
            "protocol_version": 1,
            "bridge_version": "0.1.0",
            "pid": 7878,
            "session_generation": 0,
            "game_version": PENDING_CHARACTER_INTERACTION_CONTEXT_V1_GAME_VERSION,
            "expected_ck3_version": (
                PENDING_CHARACTER_INTERACTION_CONTEXT_V1_GAME_VERSION
            ),
            "executable_sha256": (
                PENDING_CHARACTER_INTERACTION_CONTEXT_V1_EXECUTABLE_SHA256
            ),
            "capabilities": [
                "game.state.snapshot",
                QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_CAPABILITY,
            ],
        }
    )
    endpoint.publish(_semantic_snapshot(paused=paused))
    return driver, endpoint


def _answer_with(endpoint: _FakeEndpoint, result_factory) -> None:
    def answer(frame: dict[str, object]) -> None:
        if frame.get("type") != "execute_step":
            return
        endpoint.publish(
            {
                "type": "command_result",
                "protocol_version": 1,
                "request_id": frame["request_id"],
                "ok": True,
                "result": result_factory(),
            }
        )

    endpoint.send_hook = answer


class PendingCharacterInteractionContextV1NativeDriverTests(unittest.TestCase):
    def test_action_requires_paused_snapshot_and_current_pending_id(self) -> None:
        self.assertEqual(
            _action_steps(
                [QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_CAPABILITY],
                pending_character_interaction={
                    "instance_id": PENDING_ID,
                    "auto_accept_notification": False,
                },
                paused=True,
            ),
            [STEP],
        )
        self.assertEqual(
            _action_steps(
                [QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_CAPABILITY],
                pending_character_interaction={
                    "instance_id": PENDING_ID,
                    "auto_accept_notification": False,
                },
                paused=False,
            ),
            [],
        )

    def test_typed_driver_sends_complete_generation_and_normalizes_frame(self) -> None:
        driver, endpoint = _native_driver()
        _answer_with(endpoint, _native_result)

        capabilities = driver.capabilities()
        self.assertTrue(
            capabilities[
                "pending_character_interaction_context_v1_query_supported"
            ]
        )
        self.assertIn(STEP, capabilities["action_steps"])

        result = driver.query_pending_character_interaction_context_v1(
            PENDING_ID,
            expected_revision=int(driver.take_snapshot()["revision"]),
        )

        request = endpoint.frames[-1]
        self.assertEqual(request["step"], STEP)
        self.assertEqual(request["pending_interaction_id"], PENDING_ID)
        self.assertNotIn("played_character_id", request)
        self.assertEqual(result["status"], "available")
        self.assertFalse(result["pending_character_interaction_context_ready"])
        self.assertEqual(result["pending_interaction_id"], PENDING_ID)

    def test_driver_rejects_low_bits_alias_and_frame_drift(self) -> None:
        driver, _endpoint = _native_driver()
        with self.assertRaisesRegex(BridgeUnavailableError, "does not match"):
            driver.query_pending_character_interaction_context_v1(
                PENDING_ID + 2**24,
                expected_revision=int(driver.take_snapshot()["revision"]),
            )

        driver, endpoint = _native_driver()

        def drift() -> dict[str, object]:
            result = _native_result()
            endpoint.publish(_semantic_snapshot(NATIVE_REVISION + 1))
            return result

        _answer_with(endpoint, drift)
        with self.assertRaisesRegex(BridgeUnavailableError, "crossed"):
            driver.query_pending_character_interaction_context_v1(
                PENDING_ID,
                expected_revision=int(driver.take_snapshot()["revision"]),
            )


class _ServiceDriver:
    def __init__(
        self,
        status: str = "available",
        *,
        advertise: bool = True,
        drift: bool = False,
        mirror_drift: bool = False,
        paused: bool = True,
    ) -> None:
        self.status = status
        self.advertise = advertise
        self.drift = drift
        self.mirror_drift = mirror_drift
        self.paused = paused
        self.calls = 0

    def capabilities(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "backend_id": "native-headless",
            "source": "named-pipe",
            "snapshot": True,
            "wait_for_change": False,
            "action_steps": [STEP] if self.advertise else [],
            "bridge_capabilities": (
                [QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_CAPABILITY]
                if self.advertise
                else []
            ),
        }

    def take_snapshot(self) -> dict[str, object]:
        self.calls += 1
        revision = (
            PUBLIC_REVISION + 1
            if self.drift and self.calls > 1
            else PUBLIC_REVISION
        )
        return {
            "format_version": 1,
            "snapshot_id": f"pending-fixture:{revision}",
            "revision": revision,
            "native_revision": NATIVE_REVISION,
            "source": "named-pipe",
            "backend_id": "native-headless",
            "date_raw": DATE_RAW,
            "paused": self.paused,
            "episode_run_id": "native-2001-fixture",
            "pending_character_interaction": {
                "instance_id": PENDING_ID,
                "sender_character_id": 1001,
                "auto_accept_notification": False,
                "source": "native",
            },
            "diagnostics": {
                "hello": {
                    "game_version": (
                        PENDING_CHARACTER_INTERACTION_CONTEXT_V1_GAME_VERSION
                    ),
                    "expected_ck3_version": (
                        PENDING_CHARACTER_INTERACTION_CONTEXT_V1_GAME_VERSION
                    ),
                    "expected_ck3_sha256": (
                        PENDING_CHARACTER_INTERACTION_CONTEXT_V1_EXECUTABLE_SHA256
                    ),
                }
            },
        }

    def query_pending_character_interaction_context_v1(
        self,
        pending_interaction_id: int,
        *,
        expected_revision: int | None,
    ) -> dict[str, object]:
        if (
            pending_interaction_id != PENDING_ID
            or expected_revision != PUBLIC_REVISION
        ):
            raise AssertionError("service changed pending query binding")
        result = _driver_result(self.status)
        if self.mirror_drift:
            result["pending_interaction_id"] += 2**24
        return result

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        raise AssertionError("service must use the parameterized driver method")

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        raise AssertionError("pending observation must not advance")


class PendingCharacterInteractionContextV1ServiceTests(unittest.TestCase):
    def test_facade_returns_exact_binding_and_semantic_red(self) -> None:
        result = _ck3_query_pending_character_interaction_context_v1(
            GameplayBridgeService(_ServiceDriver()),
            PENDING_ID,
            PUBLIC_REVISION,
        )

        self.assertEqual(result["status"], "available")
        self.assertEqual(
            result["scope"], "exact-pending-character-interaction-context"
        )
        self.assertEqual(result["binding"]["pending_interaction_id"], PENDING_ID)
        self.assertEqual(result["binding"]["native_revision"], NATIVE_REVISION)
        self.assertFalse(result["pending_character_interaction_context_ready"])
        self.assertEqual(result["build"]["version"], "1.19.0.6")

    def test_service_returns_typed_unavailable_and_invalid(self) -> None:
        for status in ("unavailable", "invalid"):
            with self.subTest(status=status):
                result = GameplayBridgeService(
                    _ServiceDriver(status)
                ).query_pending_character_interaction_context_v1(
                    PENDING_ID,
                    expected_revision=PUBLIC_REVISION,
                )
                self.assertEqual(result["status"], status)
                self.assertEqual(
                    result["reason"],
                    (
                        "send_option_count_mismatch"
                        if status == "invalid"
                        else "pending_generation_mismatch"
                    ),
                )
                self.assertIsNone(result["terms"])
                self.assertFalse(result["legality"]["accept"]["allowed"])

    def test_service_rejects_alias_capability_revision_mirror_and_drift(self) -> None:
        with self.assertRaisesRegex(BridgeUnavailableError, "paused"):
            GameplayBridgeService(
                _ServiceDriver(paused=False)
            ).query_pending_character_interaction_context_v1(
                PENDING_ID,
                expected_revision=PUBLIC_REVISION,
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "does not match"):
            GameplayBridgeService(
                _ServiceDriver()
            ).query_pending_character_interaction_context_v1(
                PENDING_ID + 2**24,
                expected_revision=PUBLIC_REVISION,
            )
        with self.assertRaises(UnsupportedStepError):
            GameplayBridgeService(
                _ServiceDriver(advertise=False)
            ).query_pending_character_interaction_context_v1(
                PENDING_ID,
                expected_revision=PUBLIC_REVISION,
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "revision mismatch"):
            GameplayBridgeService(
                _ServiceDriver()
            ).query_pending_character_interaction_context_v1(
                PENDING_ID,
                expected_revision=PUBLIC_REVISION - 1,
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "mirrors disagree"):
            GameplayBridgeService(
                _ServiceDriver(mirror_drift=True)
            ).query_pending_character_interaction_context_v1(
                PENDING_ID,
                expected_revision=PUBLIC_REVISION,
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "crossed"):
            GameplayBridgeService(
                _ServiceDriver(drift=True)
            ).query_pending_character_interaction_context_v1(
                PENDING_ID,
                expected_revision=PUBLIC_REVISION,
            )


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class PendingCharacterInteractionContextV1McpTests(
    unittest.IsolatedAsyncioTestCase
):
    async def test_official_client_lists_and_calls_pending_context_tool(self) -> None:
        from mcp import Client

        server = create_server(_ServiceDriver())
        async with Client(server) as client:
            listed = await client.list_tools()
            names = {tool.name for tool in listed.tools}
            self.assertIn(
                "ck3_query_pending_character_interaction_context_v1", names
            )
            result = await client.call_tool(
                "ck3_query_pending_character_interaction_context_v1",
                {
                    "pending_interaction_id": PENDING_ID,
                    "expected_revision": PUBLIC_REVISION,
                },
            )

        self.assertFalse(result.is_error)
        payload = result.structured_content
        self.assertEqual(payload["status"], "available")
        self.assertEqual(payload["pending_interaction_id"], PENDING_ID)
        self.assertFalse(payload["pending_character_interaction_context_ready"])


if __name__ == "__main__":
    unittest.main()
