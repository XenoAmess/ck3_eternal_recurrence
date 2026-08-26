from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
HARNESS_PATH = (
    PROJECT_ROOT
    / "native_bridge"
    / "research"
    / "run_pending_character_interaction_context_live_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_pending_character_interaction_context_live_acceptance",
    HARNESS_PATH,
)
assert SPEC is not None and SPEC.loader is not None
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)


PENDING_ID = 16_777_249
PUBLIC_REVISION = 7
NATIVE_REVISION = 41
DATE_RAW = 53_175_816


def _snapshot(
    *,
    pending_id: int = PENDING_ID,
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
        "episode_run_id": "pending-context-live-fixture",
        "backend_id": "native-headless",
        "played_character": {
            "character_id": HARNESS.RECIPIENT_CHARACTER_ID,
            "alive": True,
        },
        "pending_character_interaction": {
            "instance_id": pending_id,
            "sender_character_id": HARNESS.SOURCE_CHARACTER_ID,
            "auto_accept_notification": False,
        },
        "active_wars": [],
    }


def _legality() -> dict[str, dict[str, object]]:
    return {
        "accept": {"status": "available", "allowed": True, "reason": None},
        "reject": {"status": "available", "allowed": True, "reason": None},
        "block": {
            "status": "available",
            "allowed": True,
            "reason": None,
        },
        "acknowledge": {
            "status": "available",
            "allowed": False,
            "reason": "normal_reply_channel",
        },
    }


def _unavailable_term(reason: str) -> dict[str, object]:
    return {"status": "unavailable", "value": None, "reason": reason}


def _frame() -> dict[str, object]:
    return {
        "schema": "pending-character-interaction-context-v1",
        "schema_version": 1,
        "status": "available",
        "snapshot_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "pending_interaction_id": PENDING_ID,
        "reason": None,
        "build": {
            "version": HARNESS.PENDING_CHARACTER_INTERACTION_CONTEXT_V1_GAME_VERSION,
            "exe_sha256": (
                HARNESS.PENDING_CHARACTER_INTERACTION_CONTEXT_V1_EXECUTABLE_SHA256
            ),
        },
        "definition": {
            "canonical_key": HARNESS.EXPECTED_INTERACTION_KEY,
            "deterministic_key_hash": 0x12345678,
            "runtime_ordinal": 42,
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
        "auto_accept": {
            "status": "available",
            "value": False,
            "reason": None,
        },
        "legality": _legality(),
        "terms": {
            "special_data_present": True,
            "structured_costs": _unavailable_term(
                "structured_costs_unavailable"
            ),
            "structured_exchanges": _unavailable_term(
                "structured_exchanges_unavailable"
            ),
            "structured_effect_preview": _unavailable_term(
                "structured_effect_preview_unavailable"
            ),
            "recipient_ai_acceptance_score": _unavailable_term(
                "recipient_ai_acceptance_score_unavailable"
            ),
            "recipient_ai_final_decision": _unavailable_term(
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
            "structured_terms_ready": False,
            "same_frame_ready": True,
            "interaction_semantic_decision_ready": False,
            "not_ready_reasons": [
                "structured_costs_unavailable",
                "structured_exchanges_unavailable",
                "structured_effect_preview_unavailable",
            ],
        },
        "provenance": {},
    }


def _query_result(sequence: int, frame: object | None = None) -> dict[str, object]:
    selected = copy.deepcopy(frame if frame is not None else _frame())
    assert isinstance(selected, dict)
    return {
        "step": HARNESS.QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP,
        "accepted": True,
        "status": "available",
        "query_sequence": sequence,
        "snapshot_revision": NATIVE_REVISION,
        "pending_character_interaction_context": selected,
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


class _FakeQueryService:
    def __init__(
        self,
        *,
        frame_drift: bool = False,
        snapshot_drift: bool = False,
    ) -> None:
        self.frame_drift = frame_drift
        self.snapshot_drift = snapshot_drift
        self.query_count = 0
        self.calls: list[tuple[int, int]] = []

    def snapshot(self) -> dict[str, object]:
        drift = int(self.snapshot_drift and self.query_count > 0)
        return _snapshot(
            public_revision=PUBLIC_REVISION + drift,
            native_revision=NATIVE_REVISION + drift,
        )

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
            frame["deadline"]["remaining_days"] = 59
        return _query_result(self.query_count, frame)


class _FakeRawDriver:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []

    def _execute_primitive_step(
        self, step: str, **kwargs: object
    ) -> dict[str, object]:
        self.calls.append((step, dict(kwargs)))
        return {
            "step": step,
            "accepted": True,
            "status": "submitted",
            "backend_id": "native-headless",
        }


def _capabilities(*, pending: bool = True) -> dict[str, object]:
    required = [
        HARNESS.OFFER_WHITE_PEACE_CAPABILITY,
        HARNESS.QUERY_WAR_TERMINATION_OPTIONS_CAPABILITY,
        HARNESS.QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_CAPABILITY,
    ]
    return {
        "bridge_capabilities": required,
        "action_steps": [
            HARNESS.WAR_OPTIONS_STEP,
            HARNESS.SAVE_CHECKPOINT_STEP,
        ]
        + (
            [HARNESS.QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP]
            if pending
            else []
        ),
        "pending_character_interaction_context_v1_query_supported": True,
        "diagnostics": {
            "connected": True,
            "bridge_pid": 1234,
            "connection_generation": 5,
            "hello": {
                "capabilities": required,
                "expected_ck3_version": (
                    HARNESS.PENDING_CHARACTER_INTERACTION_CONTEXT_V1_GAME_VERSION
                ),
                "expected_ck3_sha256": (
                    HARNESS.PENDING_CHARACTER_INTERACTION_CONTEXT_V1_EXECUTABLE_SHA256
                ),
                "game_adapter_id": HARNESS.EXPECTED_ADAPTER_ID,
                "game_adapter_status": "ready",
                "ck3_build_match": True,
            },
        },
    }


class PendingInteractionContextLiveAcceptanceTests(unittest.TestCase):
    def test_fixed_source_identity_and_hash_are_the_immutable_fixture(self) -> None:
        self.assertEqual(
            HARNESS.DEFAULT_SOURCE_PROFILE,
            Path(
                r"C:\Users\xenoa\AppData\Local\Temp"
                r"\xar-war-entry-known-good-profile-control\profile"
            ),
        )
        self.assertEqual(
            HARNESS.DEFAULT_SOURCE_SAVE,
            Path(r"save games\xar_checkpoint_pre_white_peace_53175816.ck3"),
        )
        self.assertEqual(
            HARNESS.EXPECTED_SOURCE_SAVE_SHA256,
            "5BA2136911EAD0CAF1F7D2F3DE02EAFBD8039861C46F01F35F698B3B5CFFFC5F",
        )

    def test_switch_effect_uses_live_province_owner_and_no_religion(self) -> None:
        effect = HARNESS._switch_effect()
        self.assertIn("province:2543", effect)
        self.assertIn("province_owner", effect)
        self.assertIn("set_player_character = scope:", effect)
        self.assertIn(HARNESS.SWITCH_MARKER, effect)
        self.assertNotIn("character:36108", effect)
        for forbidden in (
            "faith",
            "doctrine",
            "tenet",
            "fervor",
            "convert",
            "reformation",
            "holy_war",
        ):
            self.assertNotIn(forbidden, effect.casefold())

    def test_raw_offer_is_capability_gated_and_revision_bound(self) -> None:
        driver = _FakeRawDriver()
        result = HARNESS._raw_offer_white_peace(
            driver, expected_revision=PUBLIC_REVISION
        )

        self.assertTrue(result["ok"])
        self.assertTrue(result["seed_only_raw_call"])
        self.assertEqual(
            driver.calls,
            [
                (
                    HARNESS.OFFER_WHITE_PEACE_STEP,
                    {
                        "expected_revision": PUBLIC_REVISION,
                        "required_capability": (
                            HARNESS.OFFER_WHITE_PEACE_CAPABILITY
                        ),
                    },
                )
            ],
        )

    def test_source_war_and_options_prove_plain_claim_cb(self) -> None:
        snapshot = _snapshot()
        snapshot["played_character"] = {
            "character_id": HARNESS.SOURCE_CHARACTER_ID,
            "alive": True,
        }
        snapshot["pending_character_interaction"] = None
        snapshot["active_wars"] = [
            {
                "war_id": HARNESS.WAR_ID,
                "player_side": "attacker",
                "primary_opponent_character_id": (
                    HARNESS.RECIPIENT_CHARACTER_ID
                ),
                "player_is_primary_war_leader": True,
                "targeted_title_ids": [HARNESS.EXPECTED_TARGET_TITLE_ID],
            }
        ]
        source = HARNESS._source_war_proof(snapshot)
        options = HARNESS._war_options_proof(
            {
                "step": HARNESS.WAR_OPTIONS_STEP,
                "accepted": True,
                "status": "available",
                "war_termination_options": {
                    "war_id": HARNESS.WAR_ID,
                    "player_side": "attacker",
                    "player_is_primary_war_leader": True,
                    "active_casus_belli_identity": {
                        "database_index": 7,
                        "canonical_key": HARNESS.EXPECTED_CASUS_BELLI_KEY,
                    },
                    "cb_allows_white_peace": True,
                    "options": {
                        "white_peace": {
                            "context_constructed": True,
                            "native_validator_passed": True,
                            "available": True,
                        }
                    },
                },
            }
        )

        self.assertTrue(source["ok"])
        self.assertTrue(options["ok"])
        self.assertTrue(options["checks"]["ordinary_claim_cb"])

    def test_context_proof_covers_identity_options_deadline_and_legality(
        self,
    ) -> None:
        proof = HARNESS._context_proof(
            _query_result(1),
            pending_id=PENDING_ID,
            native_revision=NATIVE_REVISION,
            date_raw=DATE_RAW,
        )

        self.assertTrue(proof["ok"])
        self.assertTrue(proof["checks"]["exact_roles"])
        self.assertTrue(proof["checks"]["zero_send_options_exact"])
        self.assertTrue(proof["checks"]["recipient_local_route"])
        self.assertTrue(proof["checks"]["fresh_deadline"])
        self.assertTrue(proof["checks"]["reply_legalities_available"])
        self.assertTrue(proof["checks"]["block_legal"])
        self.assertTrue(proof["checks"]["acknowledge_not_normal_reply"])
        self.assertFalse(proof["readiness"]["structured_terms_ready"])

    def test_context_proof_rejects_definition_and_reply_drift(self) -> None:
        frame = _frame()
        frame["definition"]["canonical_key"] = "religious_drift"
        frame["legality"]["accept"]["allowed"] = False
        proof = HARNESS._context_proof(
            _query_result(1, frame),
            pending_id=PENDING_ID,
            native_revision=NATIVE_REVISION,
            date_raw=DATE_RAW,
        )

        self.assertFalse(proof["ok"])
        self.assertFalse(
            proof["checks"]["canonical_white_peace_definition"]
        )
        self.assertFalse(proof["checks"]["accept_and_reject_legal"])

    def test_double_query_is_adjacent_same_revision_and_read_only(self) -> None:
        service = _FakeQueryService()
        result = HARNESS._run_double_query_sequence(
            service,
            expected_pending_id=PENDING_ID,
            expected_date_raw=DATE_RAW,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(
            service.calls,
            [
                (PENDING_ID, PUBLIC_REVISION),
                (PENDING_ID, PUBLIC_REVISION),
            ],
        )
        self.assertEqual(
            result["commands"],
            [
                HARNESS.QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP,
                HARNESS.QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP,
            ],
        )
        self.assertTrue(result["mutation_boundary"]["ok"])
        self.assertEqual(
            result["mutation_boundary"]["forbidden_reply_steps_observed"],
            [],
        )

    def test_double_query_rejects_frame_and_snapshot_drift(self) -> None:
        frame_drift = HARNESS._run_double_query_sequence(
            _FakeQueryService(frame_drift=True),
            expected_pending_id=PENDING_ID,
            expected_date_raw=DATE_RAW,
        )
        snapshot_drift = HARNESS._run_double_query_sequence(
            _FakeQueryService(snapshot_drift=True),
            expected_pending_id=PENDING_ID,
            expected_date_raw=DATE_RAW,
        )

        self.assertFalse(frame_drift["ok"])
        self.assertFalse(
            frame_drift["checks"]["adjacent_context_frames_strictly_equal"]
        )
        self.assertFalse(snapshot_drift["ok"])
        self.assertFalse(
            snapshot_drift["checks"]["between_same_paused_binding"]
        )

    def test_mutation_boundaries_reject_any_default_reply(self) -> None:
        seed = HARNESS._mutation_boundary_proof(
            [
                HARNESS.WAR_OPTIONS_STEP,
                HARNESS.OFFER_WHITE_PEACE_STEP,
                HARNESS.SAVE_CHECKPOINT_STEP,
            ],
            seed_stage=True,
        )
        bad = HARNESS._mutation_boundary_proof(
            [
                HARNESS.QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP,
                "accept-pending-character-interaction",
            ],
            seed_stage=False,
        )

        self.assertTrue(seed["ok"])
        self.assertFalse(bad["ok"])
        self.assertEqual(
            bad["forbidden_reply_steps_observed"],
            ["accept-pending-character-interaction"],
        )

    def test_capabilities_keep_offer_raw_and_publish_typed_query(self) -> None:
        seed = HARNESS._capability_proof(
            _capabilities(pending=False), seed_stage=True
        )
        production = HARNESS._capability_proof(
            _capabilities(), seed_stage=False
        )

        self.assertTrue(seed["ok"])
        self.assertTrue(seed["checks"]["white_peace_not_public_action"])
        self.assertTrue(production["ok"])

    def test_exact_binary_proof_binds_pending_contract(self) -> None:
        expected_dll = "A" * 64
        proof = HARNESS._exact_binary_proof(
            _capabilities(),
            executable_sha256=(
                HARNESS.PENDING_CHARACTER_INTERACTION_CONTEXT_V1_EXECUTABLE_SHA256
            ),
            dll_sha256=expected_dll,
            expected_dll_sha256=expected_dll,
        )

        self.assertTrue(proof["ok"])
        self.assertTrue(
            proof["checks"]["pending_contract_executable_sha256"]
        )

    def test_production_projection_excludes_seed_bridge(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            profile = root / "profile"
            production = profile / "mod-content" / "xar-production"
            production.mkdir(parents=True)
            (profile / "mod").mkdir()
            (profile / "dlc_load.json").write_text(
                json.dumps(
                    {
                        "enabled_mods": [HARNESS.OUTER_DESCRIPTOR_REF],
                        "disabled_dlcs": [],
                    }
                ),
                encoding="utf-8",
            )
            spec = SimpleNamespace(
                profile_dir=profile,
                production_dir=production,
            )

            proof = HARNESS._production_projection_proof(spec)

        self.assertTrue(proof["ok"])
        self.assertTrue(proof["checks"]["seed_mod_tree_absent"])

    def test_source_save_resolution_is_contained_and_hash_bound(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            profile = Path(raw) / "profile"
            save = profile / "save games" / "source.ck3"
            save.parent.mkdir(parents=True)
            save.write_bytes(b"immutable-source")
            digest = hashlib.sha256(save.read_bytes()).hexdigest().upper()

            resolved, identity = HARNESS._resolve_source_save(
                profile, Path("save games/source.ck3"), digest
            )

            self.assertEqual(resolved, save.resolve())
            self.assertEqual(identity["sha256"], digest)
            with self.assertRaisesRegex(HARNESS.AgentError, "escapes"):
                HARNESS._resolve_source_save(
                    profile, Path("../outside.ck3"), digest
                )
            with self.assertRaisesRegex(HARNESS.AgentError, "differs"):
                HARNESS._resolve_source_save(
                    profile, Path("save games/source.ck3"), "A" * 64
                )

    def test_cleanup_requires_nonce_and_clean_started_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            target = parent / "clone"
            target.mkdir()
            marker = target / HARNESS._ROOT_MARKER_NAME
            marker.write_text(
                json.dumps(
                    {"kind": HARNESS._ROOT_KIND, "nonce": "right"}
                ),
                encoding="utf-8",
            )
            blocked = HARNESS._cleanup_root(
                target,
                nonce="right",
                retain=False,
                stages=[
                    {
                        "stage": "seed",
                        "session_started": True,
                        "cleanup": {"ok": False},
                    }
                ],
            )
            self.assertFalse(blocked["ok"])
            self.assertTrue(target.exists())

            removed = HARNESS._cleanup_root(
                target,
                nonce="right",
                retain=False,
                stages=[
                    {
                        "stage": "seed",
                        "session_started": True,
                        "cleanup": {"ok": True},
                    },
                    {
                        "stage": "production",
                        "session_started": True,
                        "cleanup": {"ok": True},
                    },
                ],
            )
            self.assertTrue(removed["ok"])
            self.assertFalse(target.exists())

    def test_cross_stage_requires_same_pending_id_and_distinct_pids(self) -> None:
        seed = {
            "ok": True,
            "pending_identity": {
                "instance_id": PENDING_ID,
                "sender_character_id": HARNESS.SOURCE_CHARACTER_ID,
            },
            "stable_pre_save_snapshot": {"date_raw": DATE_RAW},
            "same_process_proof": {"bridge_pid": 101},
            "mutation_boundary": {"checks": {"no_reply_action": True}},
        }
        production = {
            "ok": True,
            "same_process_proof": {"bridge_pid": 202},
            "production_projection_proof": {"ok": True},
            "sequence": {
                "pending_interaction_id": PENDING_ID,
                "date_raw": DATE_RAW,
                "mutation_boundary": {
                    "checks": {"no_reply_action": True}
                },
                "first_query": _query_result(1),
            },
        }

        proof = HARNESS._cross_stage_proof(
            seed, production, {"ok": True}
        )

        self.assertTrue(proof["ok"])
        production["same_process_proof"]["bridge_pid"] = 101
        self.assertFalse(
            HARNESS._cross_stage_proof(
                seed, production, {"ok": True}
            )["ok"]
        )

    def test_preflight_failure_returns_a_diagnostic_payload(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            args = SimpleNamespace(
                timeout=1.0,
                readiness_timeout=1.0,
                seed_timeout=1.0,
                expected_source_save_sha256=(
                    HARNESS.EXPECTED_SOURCE_SAVE_SHA256
                ),
                expected_bridge_dll_sha256="A" * 64,
                source_profile=root / "missing-source-profile",
                source_save=Path("save games/missing.ck3"),
                state_dir=root / "disposable-state",
                output=root / "outside" / "artifact.json",
                game_dir=root / "game",
                bridge_pipe=r"\\.\pipe\fixture",
                bridge_dll=root / "bridge.dll",
                bridge_injector=root / "injector.exe",
                retain_state=False,
            )

            payload, exit_code = HARNESS._run(args)

        self.assertEqual(exit_code, 1)
        self.assertFalse(payload["ok"])
        self.assertIn("immutable source profile is missing", payload["error"])
        self.assertIsNone(payload["seed_stage"])
        self.assertIsNone(payload["production_stage"])
        self.assertFalse(any(payload["readiness_gates"].values()))

    def test_runner_source_names_ack_as_unclosed_without_calling_it(self) -> None:
        source = HARNESS_PATH.read_text(encoding="utf-8")
        self.assertIn("acknowledge", source)
        self.assertNotIn("service.reply_pending_character_interaction", source)
        self.assertNotIn("service.auto_turn(", source)


if __name__ == "__main__":
    unittest.main()
