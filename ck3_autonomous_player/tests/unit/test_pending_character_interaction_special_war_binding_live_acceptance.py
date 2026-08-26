from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[2]
HARNESS_PATH = (
    PROJECT_ROOT
    / "native_bridge"
    / "research"
    / "run_pending_character_interaction_special_war_binding_live_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_pending_character_interaction_special_war_binding_live_acceptance",
    HARNESS_PATH,
)
assert SPEC is not None and SPEC.loader is not None
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)


PENDING_ID = 738_197_506
PUBLIC_REVISION = 7
NATIVE_REVISION = 41
DATE_RAW = 53_175_816


def _snapshot(
    *,
    public_revision: int = PUBLIC_REVISION,
    native_revision: int = NATIVE_REVISION,
) -> dict[str, object]:
    return {
        "snapshot_id": f"native:{native_revision}",
        "revision": public_revision,
        "native_revision": native_revision,
        "date_raw": DATE_RAW,
        "paused": True,
        "map_ready": True,
        "episode_run_id": "special-war-binding-live-fixture",
        "backend_id": "native-headless",
        "played_character": {
            "character_id": HARNESS.RECIPIENT_CHARACTER_ID,
            "alive": True,
        },
        "pending_character_interaction": {
            "instance_id": PENDING_ID,
            "sender_character_id": HARNESS.SOURCE_CHARACTER_ID,
            "auto_accept_notification": False,
        },
        "active_wars": [_war_row()],
    }


def _war_row() -> dict[str, object]:
    return {
        "war_id": HARNESS.WAR_ID,
        "player_side": "defender",
        "primary_opponent_character_id": HARNESS.SOURCE_CHARACTER_ID,
        "player_is_primary_war_leader": True,
        "enemy_primary_default_raise_province_id": 2619,
        "targeted_title_ids": [HARNESS.EXPECTED_TARGET_TITLE_ID],
        "war_objective_province_ids": [2543],
        "objective_province_states": [],
        "player_relative_war_score": -12_345,
        "allied_armies": [],
        "enemy_armies": [],
        "source": "native",
    }


def _provenance() -> dict[str, str]:
    return {
        "backend_id": (
            "ck3-1.19.0.6-native-pending-character-interaction-context-v1"
        ),
        "pending_storage_slot_rva": "0x57BF1C8",
        "character_storage_slot_rva": "0x570C130",
        "expiration_days_rva": "0x570F528",
        "local_routing_predicate_rva": "0x1266BA0",
        "reply_validator_rva": "0x26B3540",
        "auto_accept_trigger_evaluator_rva": "0x334C510",
        "cost_evaluator_rva": "0x2CDB7B0",
        "common_war_relation_rva": "0x2610840",
        "target_type_registry_getter_rva": "0x33C52B0",
        "target_type_registry_rva": "0x4FFE290",
        "script_identifier_name_rva": "0x3B58970",
        "reply_primary_vtable_rva": "0x4082930",
        "reply_secondary_vtable_rva": "0x4082900",
        "war_victory_special_vtable_rva": "0x428EEA8",
        "war_white_peace_special_vtable_rva": "0x428EF88",
        "war_defeat_special_vtable_rva": "0x428EF18",
    }


def _available_legality() -> dict[str, dict[str, object]]:
    return {
        "accept": {"status": "available", "allowed": True, "reason": None},
        "reject": {"status": "available", "allowed": True, "reason": None},
        "block": {"status": "available", "allowed": True, "reason": None},
        "acknowledge": {
            "status": "available",
            "allowed": False,
            "reason": "normal_reply_channel",
        },
    }


def _unavailable(reason: str) -> dict[str, object]:
    return {"status": "unavailable", "value": None, "reason": reason}


def _frame() -> dict[str, object]:
    costs = [
        {"resource_key": key, "raw": 0}
        for key in HARNESS._COST_RESOURCE_KEYS
    ]
    return {
        "schema": "pending-character-interaction-context-v1",
        "schema_version": 1,
        "status": "available",
        "snapshot_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "pending_interaction_id": PENDING_ID,
        "reason": None,
        "build": {
            "version": (
                HARNESS.PENDING_CHARACTER_INTERACTION_CONTEXT_V1_GAME_VERSION
            ),
            "exe_sha256": (
                HARNESS.PENDING_CHARACTER_INTERACTION_CONTEXT_V1_EXECUTABLE_SHA256
            ),
        },
        "definition": {
            "canonical_key": HARNESS.EXPECTED_INTERACTION_KEY,
            "deterministic_key_hash": 3_450_334_569,
            "runtime_ordinal": 294,
        },
        "roles": {
            "actor_character_id": HARNESS.SOURCE_CHARACTER_ID,
            "recipient_character_id": HARNESS.RECIPIENT_CHARACTER_ID,
            "secondary_actor_character_id": -1,
            "secondary_recipient_character_id": -1,
            "intermediary_character_id": -1,
        },
        "target": {
            "present": False,
            "raw_type_index": 0,
            "raw_16_bytes_hex": "0" * 32,
            "type_key_status": "absent",
            "type_key": None,
            "type_key_reason": None,
            "typed_identity_status": "absent",
            "typed_identity": None,
            "typed_identity_reason": None,
        },
        "send_options": {
            "exclusive": True,
            "definition_count": 0,
            "context_count": 0,
            "rows": [],
        },
        "routing": {
            "kind": 0,
            "played_character_id": HARNESS.RECIPIENT_CHARACTER_ID,
            "current_responder_role": "recipient",
            "reply_execution_channel": "recipient",
            "local_route": True,
            "auto_accept_notification": False,
        },
        "deadline": {
            "age_days": 0,
            "expiration_days": 60,
            "remaining_days": 60,
            "expiry_boundary_status": "not_reached",
        },
        "auto_accept": {"status": "available", "value": False, "reason": None},
        "legality": _available_legality(),
        "terms": {
            "special_data_present": True,
            "special_war_binding": {
                "status": "available",
                "value": {
                    "special_interaction_kind": (
                        HARNESS.EXPECTED_SPECIAL_INTERACTION_KIND
                    ),
                    "absolute_outcome": HARNESS.EXPECTED_ABSOLUTE_OUTCOME,
                    "war_id": HARNESS.WAR_ID,
                    "actor_war_role": HARNESS.EXPECTED_ACTOR_WAR_ROLE,
                    "recipient_war_role": (
                        HARNESS.EXPECTED_RECIPIENT_WAR_ROLE
                    ),
                    "binding_source": HARNESS.EXPECTED_BINDING_SOURCE,
                },
                "reason": None,
            },
            "structured_costs": {
                "status": "available",
                "value": {
                    "raw_scale": 100_000,
                    "payer_role": "actor",
                    "application_timing": "on_send",
                    "pending_payment_state": "already_applied",
                    "entries": costs,
                },
                "reason": None,
            },
            "structured_exchanges": _unavailable(
                "structured_exchanges_unavailable"
            ),
            "structured_effect_preview": _unavailable(
                "structured_effect_preview_unavailable"
            ),
            "recipient_ai_acceptance_score": _unavailable(
                "recipient_ai_acceptance_score_unavailable"
            ),
            "recipient_ai_final_decision": _unavailable(
                "recipient_ai_final_decision_unavailable"
            ),
        },
        "readiness": {
            "stable_definition_ready": True,
            "roles_ready": True,
            "target_type_key_ready": True,
            "target_typed_identity_ready": True,
            "send_options_ready": True,
            "routing_ready": True,
            "deadline_ready": True,
            "auto_accept_ready": True,
            "reply_legality_ready": True,
            "generic_costs_ready": True,
            "special_war_binding_ready": True,
            "special_outcome_terms_ready": False,
            "structured_terms_ready": False,
            "same_frame_ready": True,
            "interaction_semantic_decision_ready": False,
            "not_ready_reasons": list(HARNESS._NOT_READY_REASONS),
        },
        "provenance": _provenance(),
    }


def _query_result(
    sequence: int, frame: dict[str, object] | None = None
) -> dict[str, object]:
    return {
        "step": HARNESS.QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP,
        "accepted": True,
        "status": "available",
        "query_sequence": sequence,
        "snapshot_revision": NATIVE_REVISION,
        "pending_character_interaction_context": copy.deepcopy(
            frame if frame is not None else _frame()
        ),
        "backend_id": "native-headless",
        "pending_character_interaction_context_ready": False,
        "scope": "exact-pending-character-interaction-context",
        "binding": {
            "snapshot_id": f"native:{NATIVE_REVISION}",
            "revision": PUBLIC_REVISION,
            "native_revision": NATIVE_REVISION,
            "date_raw": DATE_RAW,
            "pending_interaction_id": PENDING_ID,
            "expected_revision": PUBLIC_REVISION,
        },
    }


def _war_state() -> dict[str, object]:
    return {
        "status": "active",
        "active_wars": [_war_row()],
        "player_armies": [],
        "war_termination_options": [],
        "war_termination_terms": [],
        "war_termination_exit_terms": [],
        "army_strengths": [],
        "army_strengths_status": None,
        "army_strengths_query_sequence": None,
        "snapshot_id": f"native:{NATIVE_REVISION}",
        "revision": PUBLIC_REVISION,
    }


class _FakeService:
    def __init__(
        self,
        *,
        frame_drift: bool = False,
        snapshot_drift: bool = False,
        war_drift: bool = False,
    ) -> None:
        self.frame_drift = frame_drift
        self.snapshot_drift = snapshot_drift
        self.war_drift = war_drift
        self.query_count = 0
        self.calls: list[tuple[int, int]] = []
        self.war_state_calls = 0

    def snapshot(self) -> dict[str, object]:
        drift = int(self.snapshot_drift and self.query_count >= 2)
        return _snapshot(
            public_revision=PUBLIC_REVISION + drift,
            native_revision=NATIVE_REVISION + drift,
        )

    def war_state(self) -> dict[str, object]:
        self.war_state_calls += 1
        result = _war_state()
        if self.war_drift:
            result["active_wars"][0]["primary_opponent_character_id"] = 999
        return result

    def query_pending_character_interaction_context_v1(
        self,
        pending_interaction_id: int,
        *,
        expected_revision: int,
    ) -> dict[str, object]:
        self.calls.append((pending_interaction_id, expected_revision))
        if pending_interaction_id != PENDING_ID:
            raise AssertionError("query used another pending ID")
        if expected_revision != PUBLIC_REVISION:
            raise AssertionError("query used another public revision")
        self.query_count += 1
        frame = _frame()
        if self.frame_drift and self.query_count == 2:
            frame["terms"]["special_war_binding"]["value"]["war_id"] += 1
        return _query_result(self.query_count, frame)


class PendingSpecialWarBindingLiveAcceptanceTests(unittest.TestCase):
    def test_frozen_source_binary_and_nonreligious_fixture_identity(self) -> None:
        self.assertEqual(
            HARNESS.FROZEN_SPECIAL_WAR_SOURCE_COMMIT,
            "542228a3c1221c189e4c9e84c35d8728aad4d1a1",
        )
        self.assertEqual(
            HARNESS.FROZEN_SPECIAL_WAR_DLL_SHA256,
            "2E60BC15320AA5C82E6C78AC236BC986601AFACB3C579A2F10881F43FD8B6C9F",
        )
        self.assertEqual(
            HARNESS.EXPECTED_SOURCE_SAVE_SHA256,
            "5BA2136911EAD0CAF1F7D2F3DE02EAFBD8039861C46F01F35F698B3B5CFFFC5F",
        )
        self.assertEqual(
            HARNESS.EXPECTED_CASUS_BELLI_KEY,
            "claim_cb",
        )

    def test_context_proof_accepts_exact_binding_and_keeps_semantics_open(
        self,
    ) -> None:
        proof = HARNESS._context_proof(
            _query_result(1),
            pending_id=PENDING_ID,
            native_revision=NATIVE_REVISION,
            date_raw=DATE_RAW,
        )

        self.assertTrue(proof["ok"])
        self.assertTrue(proof["checks"]["strict_contract_normalized"])
        self.assertTrue(proof["checks"]["special_war_binding_exact"])
        self.assertTrue(proof["checks"]["generic_zero_cost_exact"])
        self.assertTrue(proof["checks"]["remaining_terms_incomplete"])
        self.assertFalse(proof["readiness"]["special_outcome_terms_ready"])
        self.assertFalse(proof["readiness"]["structured_terms_ready"])
        self.assertFalse(
            proof["readiness"]["interaction_semantic_decision_ready"]
        )

    def test_context_proof_rejects_outcome_role_cost_and_readiness_drift(
        self,
    ) -> None:
        mutations = []

        outcome = _frame()
        outcome["terms"]["special_war_binding"]["value"][
            "absolute_outcome"
        ] = "attacker_victory"
        mutations.append(outcome)

        role = _frame()
        role["terms"]["special_war_binding"]["value"][
            "actor_war_role"
        ] = "primary_defender"
        mutations.append(role)

        cost = _frame()
        cost["terms"]["structured_costs"]["value"]["entries"][0][
            "raw"
        ] = 100_000
        mutations.append(cost)

        readiness = _frame()
        readiness["readiness"]["structured_terms_ready"] = True
        mutations.append(readiness)

        for frame in mutations:
            with self.subTest(frame=frame):
                proof = HARNESS._context_proof(
                    _query_result(1, frame),
                    pending_id=PENDING_ID,
                    native_revision=NATIVE_REVISION,
                    date_raw=DATE_RAW,
                )
                self.assertFalse(proof["ok"])

    def test_war_state_proves_same_war_and_primary_leaders(self) -> None:
        proof = HARNESS._war_state_proof(
            _war_state(), paused_snapshot=_snapshot()
        )

        self.assertTrue(proof["ok"])
        self.assertTrue(proof["checks"]["same_public_revision"])
        self.assertTrue(proof["checks"]["recipient_is_primary_defender"])
        self.assertTrue(proof["checks"]["actor_is_primary_attacker"])

    def test_double_query_is_same_revision_adjacent_and_read_only(self) -> None:
        service = _FakeService()
        result = HARNESS._run_double_query_sequence(
            service,
            expected_pending_id=PENDING_ID,
            expected_date_raw=DATE_RAW,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(
            service.calls,
            [(PENDING_ID, PUBLIC_REVISION), (PENDING_ID, PUBLIC_REVISION)],
        )
        self.assertEqual(service.war_state_calls, 1)
        self.assertEqual(
            result["commands"],
            [
                HARNESS.QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP,
                HARNESS.QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP,
            ],
        )
        self.assertTrue(result["checks"]["war_id_cross_corroborated"])
        self.assertTrue(result["checks"]["primary_roles_cross_corroborated"])
        self.assertEqual(
            result["mutation_boundary"]["forbidden_reply_steps_observed"],
            [],
        )

    def test_double_query_rejects_frame_snapshot_and_war_drift(self) -> None:
        frame = HARNESS._run_double_query_sequence(
            _FakeService(frame_drift=True),
            expected_pending_id=PENDING_ID,
            expected_date_raw=DATE_RAW,
        )
        snapshot = HARNESS._run_double_query_sequence(
            _FakeService(snapshot_drift=True),
            expected_pending_id=PENDING_ID,
            expected_date_raw=DATE_RAW,
        )
        war = HARNESS._run_double_query_sequence(
            _FakeService(war_drift=True),
            expected_pending_id=PENDING_ID,
            expected_date_raw=DATE_RAW,
        )

        self.assertFalse(frame["ok"])
        self.assertFalse(
            frame["checks"]["adjacent_context_frames_strictly_equal"]
        )
        self.assertFalse(snapshot["ok"])
        self.assertFalse(snapshot["checks"]["after_same_paused_binding"])
        self.assertFalse(war["ok"])
        self.assertFalse(war["checks"]["war_state_same_revision_valid"])

    def test_mutation_boundary_rejects_every_reply_channel(self) -> None:
        good = HARNESS._mutation_boundary_proof(
            [
                HARNESS.QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP,
                HARNESS.QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP,
            ]
        )
        self.assertTrue(good["ok"])

        for forbidden in HARNESS._FORBIDDEN_REPLY_STEPS:
            with self.subTest(forbidden=forbidden):
                bad = HARNESS._mutation_boundary_proof(
                    [
                        HARNESS.QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP,
                        forbidden,
                    ]
                )
                self.assertFalse(bad["ok"])
                self.assertEqual(
                    bad["forbidden_reply_steps_observed"], [forbidden]
                )

    def test_cross_stage_adapts_stricter_no_reply_or_ack_key(self) -> None:
        seed = {
            "ok": True,
            "pending_identity": {
                "instance_id": PENDING_ID,
                "sender_character_id": HARNESS.SOURCE_CHARACTER_ID,
            },
            "stable_pre_save_snapshot": {"date_raw": DATE_RAW},
            "same_process_proof": {"bridge_pid": 101},
            "mutation_boundary": {
                "checks": {"no_reply_action": True}
            },
        }
        production = {
            "ok": True,
            "same_process_proof": {"bridge_pid": 202},
            "production_projection_proof": {"ok": True},
            "sequence": {
                "pending_interaction_id": PENDING_ID,
                "date_raw": DATE_RAW,
                "mutation_boundary": {
                    "checks": {"no_reply_or_ack": True}
                },
                "first_query": _query_result(1),
            },
        }

        proof = HARNESS._cross_stage_proof(
            seed, production, {"ok": True}
        )

        self.assertTrue(proof["ok"])
        self.assertTrue(proof["checks"]["no_default_reply"])
        self.assertEqual(
            proof["reply_boundary_adapter"],
            {
                "seed_check_key": "no_reply_action",
                "seed_check_value": True,
                "production_check_key": "no_reply_or_ack",
                "production_check_value": True,
                "production_is_stricter": True,
            },
        )
        seed["mutation_boundary"]["checks"]["no_reply_action"] = False
        self.assertFalse(
            HARNESS._cross_stage_proof(
                seed, production, {"ok": True}
            )["ok"]
        )
        seed["mutation_boundary"]["checks"]["no_reply_action"] = True
        production["sequence"]["mutation_boundary"]["checks"][
            "no_reply_or_ack"
        ] = False
        self.assertFalse(
            HARNESS._cross_stage_proof(
                seed, production, {"ok": True}
            )["ok"]
        )

    def test_preflight_failure_cannot_enter_a_live_stage(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            args = SimpleNamespace(
                timeout=1.0,
                readiness_timeout=1.0,
                seed_timeout=1.0,
                expected_source_save_sha256=(
                    HARNESS.EXPECTED_SOURCE_SAVE_SHA256
                ),
                expected_bridge_dll_sha256=(
                    HARNESS.FROZEN_SPECIAL_WAR_DLL_SHA256
                ),
                source_profile=root / "missing-source-profile",
                source_save=Path("save games/missing.ck3"),
                state_dir=root / "disposable-state",
                output=root / "outside" / "artifact.json",
                game_dir=root / "game",
                bridge_pipe=r"\\.\pipe\fixture",
                bridge_dll=root / "missing-bridge.dll",
                bridge_injector=root / "missing-injector.exe",
                retain_state=False,
            )
            with mock.patch.object(HARNESS, "ck3_processes", return_value=[]):
                payload, exit_code = HARNESS._run(args)

        self.assertEqual(exit_code, 1)
        self.assertFalse(payload["ok"])
        self.assertIn("FileNotFoundError", payload["error"])
        self.assertIsNone(payload["seed_stage"])
        self.assertIsNone(payload["production_stage"])

    def test_runner_has_no_reply_or_turn_call_surface(self) -> None:
        source = HARNESS_PATH.read_text(encoding="utf-8")
        self.assertNotIn("service.reply_pending_character_interaction", source)
        self.assertNotIn("service.acknowledge_pending", source)
        self.assertNotIn("service.auto_turn(", source)
        self.assertNotIn("service.offer_white_peace", source)


if __name__ == "__main__":
    unittest.main()
