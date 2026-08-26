from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import threading
import unittest
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[2]
HARNESS_PATH = (
    PROJECT_ROOT
    / "native_bridge"
    / "research"
    / "run_pending_character_interaction_notification_ack_live_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_pending_character_interaction_notification_ack_live_acceptance",
    HARNESS_PATH,
)
assert SPEC is not None and SPEC.loader is not None
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)


PENDING_ID = 0x2C00_0021
PUBLIC_REVISION = 17
NATIVE_REVISION = 91
DATE_RAW = 53_175_816


def _snapshot(*, acknowledged: bool = False) -> dict[str, object]:
    native_revision = NATIVE_REVISION + int(acknowledged)
    return {
        "snapshot_id": f"native:{native_revision}",
        "revision": PUBLIC_REVISION + int(acknowledged),
        "native_revision": native_revision,
        "date_raw": DATE_RAW,
        "paused": True,
        "map_ready": True,
        "episode_run_id": "notification-ack-live-fixture",
        "backend_id": "native-headless",
        "played_character": {
            "character_id": HARNESS.RECIPIENT_CHARACTER_ID,
            "alive": True,
        },
        "pending_character_interaction": (
            None
            if acknowledged
            else {
                "instance_id": PENDING_ID,
                "sender_character_id": HARNESS.SOURCE_CHARACTER_ID,
                "auto_accept_notification": True,
            }
        ),
        "active_wars": [],
    }


def _unavailable(reason: str) -> dict[str, object]:
    return {"status": "unavailable", "value": None, "reason": reason}


def _frame(*, notification: bool = True) -> dict[str, object]:
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
            "deterministic_key_hash": 0x1234_5678,
            "runtime_ordinal": 55,
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
            "auto_accept_notification": notification,
        },
        "deadline": {
            "age_days": 0,
            "expiration_days": 60,
            "remaining_days": 60,
            "expiry_boundary_status": "not_reached",
        },
        "auto_accept": {
            "status": "available",
            "value": True,
            "reason": None,
        },
        "legality": {
            "accept": {
                "status": "available",
                "allowed": False,
                "reason": "auto_accept_notification_channel",
            },
            "reject": {
                "status": "available",
                "allowed": False,
                "reason": "auto_accept_notification_channel",
            },
            "block": {
                "status": "available",
                "allowed": False,
                "reason": "auto_accept_notification_channel",
            },
            "acknowledge": {
                "status": "available",
                "allowed": True,
                "reason": None,
            },
        },
        "terms": {
            "special_data_present": True,
            "structured_costs": _unavailable(
                "structured_costs_unavailable"
            ),
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


class _FakeQueryAckService:
    def __init__(self, *, keep_old_id: bool = False) -> None:
        self.keep_old_id = keep_old_id
        self.acknowledged = False
        self.query_count = 0
        self.calls: list[tuple[object, ...]] = []

    def snapshot(self) -> dict[str, object]:
        return _snapshot(
            acknowledged=self.acknowledged and not self.keep_old_id
        )

    def query_pending_character_interaction_context_v1(
        self,
        pending_interaction_id: int,
        *,
        expected_revision: int,
    ) -> dict[str, object]:
        self.calls.append(
            ("query", pending_interaction_id, expected_revision)
        )
        self.query_count += 1
        return _query_result(self.query_count)

    def acknowledge_pending_character_interaction(
        self,
        *,
        interaction_instance_id: int,
        expected_revision: int,
    ) -> dict[str, object]:
        self.calls.append(
            ("ack", interaction_instance_id, expected_revision)
        )
        self.acknowledged = True
        remaining = (
            {
                "instance_id": PENDING_ID,
                "sender_character_id": HARNESS.SOURCE_CHARACTER_ID,
                "auto_accept_notification": True,
            }
            if self.keep_old_id
            else None
        )
        return {
            "step": HARNESS.ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_STEP,
            "accepted": True,
            "status": "submitted",
            "acknowledged": True,
            "interaction_instance_id": interaction_instance_id,
            "interaction_result": {
                "status": "acknowledged",
                "instance_id": interaction_instance_id,
                "sender_character_id": HARNESS.SOURCE_CHARACTER_ID,
            },
            "remaining_pending_character_interaction": remaining,
        }


def _capabilities(*, notification: bool) -> dict[str, object]:
    required = [
        HARNESS.QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_CAPABILITY,
        HARNESS.ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_CAPABILITY,
    ]
    actions = []
    if notification:
        actions = [
            HARNESS.QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP,
            HARNESS.ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_STEP,
        ]
    return {
        "bridge_capabilities": required,
        "action_steps": actions,
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


class PendingNotificationAckLiveAcceptanceTests(unittest.TestCase):
    def test_frozen_source_commit_and_reviewed_binary_hashes(self) -> None:
        self.assertEqual(
            HARNESS.FROZEN_ACK_SOURCE_COMMIT,
            "70bf8e6b689780b459b361af5edf57c0f7521fca",
        )
        self.assertEqual(
            HARNESS.FROZEN_ACK_DLL_SHA256,
            "BFB1E38FCA879681074C4AB64C077F0111A7A828EA3E5284D21E0B362F40D9A9",
        )
        self.assertEqual(
            HARNESS.FROZEN_ACK_INJECTOR_SHA256,
            "1F418FFD2D765278C4EF749D3C389447FC0141FD52BDEBF79D536F1DEBAACD5C",
        )

    def test_immutable_source_identity_is_reused(self) -> None:
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

    def test_fixture_definition_contract_is_exact_and_nonreligious(self) -> None:
        proof = HARNESS._fixture_definition_contract()

        self.assertTrue(proof["ok"])
        self.assertEqual(proof["canonical_key"], HARNESS.EXPECTED_INTERACTION_KEY)
        self.assertEqual(
            proof["relative_path"],
            HARNESS.FIXTURE_DEFINITION_RELATIVE.as_posix(),
        )
        self.assertEqual(proof["sha256"], HARNESS.FIXTURE_DEFINITION_SHA256)
        self.assertTrue(HARNESS._fixture_definition_raw().startswith(b"\xef\xbb\xbf"))
        self.assertTrue(proof["checks"]["canonical_definition_only"])
        self.assertTrue(proof["checks"]["auto_accept"])
        self.assertTrue(proof["checks"]["force_notification"])
        self.assertTrue(proof["checks"]["hidden"])
        self.assertTrue(proof["checks"]["always_shown_and_valid"])
        self.assertTrue(proof["checks"]["diagnostic_handlers_only"])
        self.assertTrue(proof["checks"]["no_gameplay_mutator_tokens"])
        self.assertTrue(proof["checks"]["no_religion_semantics"])
        self.assertEqual(
            HARNESS.FIXTURE_DEFINITION_SHA256,
            "76AD6E5337366E86851F1A51B6EED2A910B85BD3181B492059DC37362B637501",
        )

    def test_fixture_projection_is_byte_identical_with_seed_bridge_only_in_seed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            seed_profile = root / "seed-profile"
            seed_production = seed_profile / "mod-content" / "xar-production"
            seed_bridge = (
                seed_profile
                / "mod-content"
                / HARNESS.owner_live.MOD_BRIDGE_TARGET_NAME
            )
            seed_production.mkdir(parents=True)
            seed_bridge.mkdir(parents=True)
            (seed_profile / "mod").mkdir()
            (seed_profile / "mod" / HARNESS.owner_live.MOD_BRIDGE_OUTER_NAME).write_text(
                "fixture", encoding="utf-8"
            )
            seed_inbox = HARNESS.owner_live._seed_inbox_path(
                SimpleNamespace(profile_dir=seed_profile)
            )
            seed_inbox.parent.mkdir(parents=True)
            seed_inbox.write_text("fixture", encoding="utf-8")
            (seed_profile / "dlc_load.json").write_text(
                json.dumps(
                    {
                        "enabled_mods": [
                            HARNESS.OUTER_DESCRIPTOR_REF,
                            f"mod/{HARNESS.owner_live.MOD_BRIDGE_OUTER_NAME}",
                        ],
                        "disabled_dlcs": [],
                    }
                ),
                encoding="utf-8",
            )
            seed_spec = SimpleNamespace(
                profile_dir=seed_profile,
                production_dir=seed_production,
            )
            HARNESS._install_fixture_definition(seed_spec)
            seed_proof = HARNESS._fixture_projection_proof(
                seed_spec, seed_stage=True
            )

            cold_profile = root / "cold-profile"
            cold_production = cold_profile / "mod-content" / "xar-production"
            cold_production.mkdir(parents=True)
            (cold_profile / "mod").mkdir()
            (cold_profile / "dlc_load.json").write_text(
                json.dumps(
                    {
                        "enabled_mods": [HARNESS.OUTER_DESCRIPTOR_REF],
                        "disabled_dlcs": [],
                    }
                ),
                encoding="utf-8",
            )
            cold_spec = SimpleNamespace(
                profile_dir=cold_profile,
                production_dir=cold_production,
            )
            HARNESS._install_fixture_definition(cold_spec)
            cold_proof = HARNESS._fixture_projection_proof(
                cold_spec, seed_stage=False
            )

        self.assertTrue(seed_proof["ok"])
        self.assertTrue(cold_proof["ok"])
        self.assertEqual(
            seed_proof["definition_sha256"],
            cold_proof["definition_sha256"],
        )
        self.assertEqual(
            seed_proof["definition_sha256"],
            HARNESS.FIXTURE_DEFINITION_SHA256,
        )
        self.assertIn(
            f"mod/{HARNESS.owner_live.MOD_BRIDGE_OUTER_NAME}",
            seed_proof["dlc_load"]["enabled_mods"],
        )
        self.assertNotIn(
            f"mod/{HARNESS.owner_live.MOD_BRIDGE_OUTER_NAME}",
            cold_proof["dlc_load"]["enabled_mods"],
        )

    def test_effect_order_requires_human_recipient_before_send(self) -> None:
        switch = HARNESS._switch_effect()
        generate = HARNESS._generate_effect()
        proof = HARNESS._effect_contract()

        self.assertTrue(proof["ok"])
        self.assertIn("set_player_character", switch)
        self.assertNotIn("run_interaction", switch)
        self.assertNotIn("set_player_character", generate)
        self.assertIn("scope:xar_fixture_notification_ack_recipient = { is_ai = no }", generate)
        self.assertIn("send_threshold = decline", generate)
        self.assertIn(
            "scope:xar_fixture_notification_ack_source = {\n"
            "\t\trun_interaction = {",
            generate,
        )
        self.assertNotIn("execute_threshold", generate)
        self.assertIn("province:2543", generate)
        self.assertIn("province:2619", generate)
        self.assertIn(
            "save_temporary_scope_as = xar_fixture_notification_ack_source",
            generate,
        )
        self.assertNotIn("liege = {", generate)
        self.assertNotIn("set_relation_guardian", generate)
        self.assertNotIn("set_employer", generate)
        self.assertNotIn("random_living_character", generate)
        self.assertNotIn("character:29829", generate)
        self.assertNotIn("character:37011", generate)
        self.assertNotIn("character:36108", generate)
        self.assertNotIn("on_accept", generate)
        self.assertNotIn("on_auto_accept", generate)

    def test_cold_session_uses_narrow_exact_fixture_launch_seam(self) -> None:
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
            HARNESS._install_fixture_definition(spec)
            stop_event = threading.Event()
            config = SimpleNamespace(pipe_name=r"\\.\pipe\fixture")

            with mock.patch.object(
                HARNESS.owner_live,
                "_fixture_native_session",
                return_value={"ok": True, "kind": "shared-fixture-seam"},
            ) as launch:
                report = HARNESS._fixture_definition_native_session(
                    spec=spec,
                    config=config,
                    timeout=123.0,
                    stop_event=stop_event,
                    seed_stage=False,
                )

                launch.assert_called_once_with(
                    spec=spec,
                    config=config,
                    timeout=123.0,
                    stop_event=stop_event,
                )
                self.assertTrue(report["ok"])
                self.assertEqual(report["fixture_stage"], "cold-query-ack")
                self.assertTrue(report["exact_fixture_projection"]["ok"])

                (
                    profile
                    / "mod-content"
                    / HARNESS.owner_live.MOD_BRIDGE_TARGET_NAME
                ).mkdir()
                with self.assertRaisesRegex(
                    HARNESS.AgentError,
                    "cold-query-ack exact fixture projection differs",
                ):
                    HARNESS._fixture_definition_native_session(
                        spec=spec,
                        config=config,
                        timeout=123.0,
                        stop_event=stop_event,
                        seed_stage=False,
                    )
                self.assertEqual(launch.call_count, 1)

    def test_wait_for_notification_rejects_ordinary_pending(self) -> None:
        snapshot = _snapshot()
        snapshot["pending_character_interaction"][
            "auto_accept_notification"
        ] = False

        class Service:
            def snapshot(self) -> dict[str, object]:
                return snapshot

        with tempfile.TemporaryDirectory() as raw:
            with self.assertRaisesRegex(HARNESS.AgentError, "ordinary pending"):
                HARNESS._wait_for_notification(
                    Service(),
                    debug_log=Path(raw) / "missing.log",
                    log_offset=0,
                    expected_date_raw=DATE_RAW,
                    deadline=10**20,
                    session_done=threading.Event(),
                    session_state={},
                )

    def test_capability_projection_is_ack_only_for_notification(self) -> None:
        before = HARNESS._capability_proof(
            _capabilities(notification=False), notification_present=False
        )
        notification = HARNESS._capability_proof(
            _capabilities(notification=True), notification_present=True
        )

        self.assertTrue(before["ok"])
        self.assertTrue(notification["ok"])
        bad = _capabilities(notification=True)
        bad["action_steps"].append("accept-pending-character-interaction")
        self.assertFalse(
            HARNESS._capability_proof(
                bad, notification_present=True
            )["ok"]
        )

    def test_notification_context_proves_key_roles_route_options_deadline_legality(self) -> None:
        proof = HARNESS._notification_context_proof(
            _query_result(1),
            pending_id=PENDING_ID,
            native_revision=NATIVE_REVISION,
            date_raw=DATE_RAW,
        )

        self.assertTrue(proof["ok"])
        for key in (
            "canonical_nonreligious_definition",
            "exact_roles",
            "no_target",
            "zero_send_options",
            "recipient_notification_route",
            "fresh_deadline",
            "auto_accept_true",
            "acknowledge_only_legality",
        ):
            self.assertTrue(proof["checks"][key], key)

    def test_notification_context_rejects_ordinary_flag_or_normal_reply(self) -> None:
        frame = _frame(notification=False)
        frame["legality"]["accept"] = {
            "status": "available",
            "allowed": True,
            "reason": None,
        }
        proof = HARNESS._notification_context_proof(
            _query_result(1, frame),
            pending_id=PENDING_ID,
            native_revision=NATIVE_REVISION,
            date_raw=DATE_RAW,
        )

        self.assertFalse(proof["ok"])
        self.assertFalse(proof["checks"]["recipient_notification_route"])
        self.assertFalse(proof["checks"]["acknowledge_only_legality"])

    def test_query_query_ack_uses_same_revision_full_id_and_proves_disappearance(self) -> None:
        service = _FakeQueryAckService()
        result = HARNESS._run_query_ack_sequence(
            service,
            expected_pending_id=PENDING_ID,
            expected_date_raw=DATE_RAW,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(
            service.calls,
            [
                ("query", PENDING_ID, PUBLIC_REVISION),
                ("query", PENDING_ID, PUBLIC_REVISION),
                ("ack", PENDING_ID, PUBLIC_REVISION),
            ],
        )
        self.assertTrue(result["checks"]["old_full_id_gone_from_fresh_snapshot"])
        self.assertEqual(result["pending_slot"], PENDING_ID & 0x00FF_FFFF)
        self.assertEqual(result["pending_generation"], PENDING_ID >> 24)

    def test_query_query_ack_rejects_unchanged_old_full_id(self) -> None:
        result = HARNESS._run_query_ack_sequence(
            _FakeQueryAckService(keep_old_id=True),
            expected_pending_id=PENDING_ID,
            expected_date_raw=DATE_RAW,
        )

        self.assertFalse(result["ok"])
        self.assertFalse(
            result["checks"]["old_full_id_gone_from_driver_result"]
        )
        self.assertFalse(
            result["checks"]["old_full_id_gone_from_fresh_snapshot"]
        )

    def test_mutation_boundary_forbids_accept_reject_and_block(self) -> None:
        good = HARNESS._mutation_boundary_proof(
            [
                HARNESS.QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP,
                HARNESS.QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP,
                HARNESS.ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_STEP,
            ]
        )
        bad = HARNESS._mutation_boundary_proof(
            [
                HARNESS.QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP,
                "accept-pending-character-interaction",
                HARNESS.ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_STEP,
            ]
        )

        self.assertTrue(good["ok"])
        self.assertFalse(bad["ok"])
        self.assertEqual(
            bad["forbidden_normal_reply_steps_observed"],
            ["accept-pending-character-interaction"],
        )

    def test_cross_stage_requires_distinct_process_and_old_id_gone(self) -> None:
        seed = {
            "ok": True,
            "pending_identity": {
                "instance_id": PENDING_ID,
                "sender_character_id": HARNESS.SOURCE_CHARACTER_ID,
                "auto_accept_notification": True,
            },
            "stable_pre_save_snapshot": {"date_raw": DATE_RAW},
            "same_process_proof": {"bridge_pid": 101},
            "fixture_projection_proof": {
                "ok": True,
                "definition_sha256": HARNESS.FIXTURE_DEFINITION_SHA256,
            },
        }
        production = {
            "ok": True,
            "same_process_proof": {"bridge_pid": 202},
            "fixture_projection_proof": {
                "ok": True,
                "definition_sha256": HARNESS.FIXTURE_DEFINITION_SHA256,
            },
            "sequence": {
                "pending_interaction_id": PENDING_ID,
                "date_raw": DATE_RAW,
                "first_query": _query_result(1),
                "checks": {
                    "old_full_id_gone_from_driver_result": True,
                    "old_full_id_gone_from_fresh_snapshot": True,
                },
            },
        }

        proof = HARNESS._cross_stage_proof(
            seed, production, {"ok": True}
        )
        self.assertTrue(proof["ok"])
        production["same_process_proof"]["bridge_pid"] = 101
        self.assertFalse(
            HARNESS._cross_stage_proof(seed, production, {"ok": True})[
                "ok"
            ]
        )

    def test_prior_red_attempt_hashes_include_actor_scope_and_remove_guardian(self) -> None:
        self.assertEqual(
            HARNESS.PRIOR_STOCK_ACTOR_SCOPE_RED_ARTIFACT_SHA256,
            "C8EE5E2C1F354DA38D137260FB28DF2C895D3A872E0F8ADDDF3EEBA46FA39E74",
        )
        self.assertEqual(
            HARNESS.PRIOR_STOCK_REMOVE_GUARDIAN_RED_ARTIFACT_SHA256,
            "726F468A46C39462370A8422B7CBC15093310A7F34E769AE7D78C01E1E9DC607",
        )

    def test_preflight_failure_still_reports_stage_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            args = SimpleNamespace(
                timeout=1.0,
                readiness_timeout=1.0,
                seed_timeout=1.0,
                postcondition_timeout=1.0,
                expected_source_save_sha256=(
                    HARNESS.EXPECTED_SOURCE_SAVE_SHA256
                ),
                expected_bridge_dll_sha256=HARNESS.FROZEN_ACK_DLL_SHA256,
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

            with mock.patch.object(
                HARNESS,
                "_dependency_source_contract",
                return_value={"ok": False},
            ):
                payload, exit_code = HARNESS._run(args)

        self.assertEqual(exit_code, 1)
        self.assertFalse(payload["ok"])
        self.assertIn("isolated exact-commit dependency tree", payload["error"])
        self.assertIsNone(payload["seed_stage"])
        self.assertIsNone(payload["production_stage"])

    def test_runner_never_calls_generic_reply_or_auto_turn(self) -> None:
        source = HARNESS_PATH.read_text(encoding="utf-8")
        self.assertNotIn("service.reply_pending_character_interaction", source)
        self.assertNotIn("service.auto_turn(", source)
        self.assertIn(
            "service.acknowledge_pending_character_interaction", source
        )


if __name__ == "__main__":
    unittest.main()
