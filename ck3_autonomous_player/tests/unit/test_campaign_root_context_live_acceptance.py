from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "native_bridge"
    / "research"
    / "run_campaign_root_context_live_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_campaign_root_context_live_acceptance", SCRIPT
)
assert SPEC is not None and SPEC.loader is not None
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)


PUBLIC_REVISION = 7
NATIVE_REVISION = 19
DATE_RAW = 53_182_008
PLAYER_CHARACTER_ID = 29_829
PIPE_NAME = r"\\.\pipe\xar_campaign_root_context_live_fixture"


def _context(
    *,
    snapshot_revision: int = NATIVE_REVISION,
    date_raw: int = DATE_RAW,
    player_character_id: int = PLAYER_CHARACTER_ID,
    available: bool = True,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "available" if available else "unavailable",
        "snapshot_revision": snapshot_revision,
        "date_raw": date_raw,
        "local_player_id": 0 if available else None,
        "player_character_id": player_character_id if available else None,
        "player_character_alive": True if available else None,
        "primary_title": (
            {"title_id": 67_890, "tier_raw": 3, "tier_key": "duchy"}
            if available
            else None
        ),
        "capital_province_id": 42 if available else None,
        "immediate_liege_character_id": None,
        "top_liege_character_id": (
            player_character_id if available else None
        ),
        "independent": True if available else None,
        "government": (
            {
                "key": "feudal_government",
                "flags": ["government_is_feudal"],
                "native_flag_count": 1,
            }
            if available
            else None
        ),
        "selected_game_rule_tokens": (
            ["1453_end_date", "normal_difficulty"] if available else []
        ),
        "native_selected_game_rule_token_count": 2 if available else 0,
        "readiness": {
            "player_identity_ready": available,
            "primary_title_ready": available,
            "capital_ready": available,
            "lieges_ready": available,
            "government_ready": available,
            "selected_game_rule_tokens_ready": available,
            "same_frame_ready": available,
            "ready": available,
        },
        "unavailable_reason": None if available else "state_changed",
        "provenance": {
            "game_version": HARNESS.CAMPAIGN_ROOT_CONTEXT_V1_GAME_VERSION,
            "executable_sha256": (
                HARNESS.CAMPAIGN_ROOT_CONTEXT_V1_EXECUTABLE_SHA256
            ),
            "backend_id": (
                "ck3-1.19.0.6-native-campaign-root-context-v1"
            ),
            "primary_title_rva": "0x25F3350",
            "capital_province_rva": "0x2606760",
            "immediate_liege_rva": "0x2613480",
            "top_liege_rva": "0x2613600",
            "government_rva": "0x26165B0",
            "selected_game_rule_service_slot_rva": "0x5754B48",
        },
    }


def _query_result(
    query_sequence: int,
    *,
    context: dict[str, object] | None = None,
    public_revision: int = PUBLIC_REVISION,
    native_revision: int = NATIVE_REVISION,
    snapshot_id: str | None = None,
) -> dict[str, object]:
    frame = copy.deepcopy(context if context is not None else _context())
    available = frame["status"] == "available"
    selected_snapshot_id = snapshot_id or f"native:{native_revision}"
    return {
        "step": HARNESS.QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
        "accepted": True,
        "status": frame["status"],
        "query_sequence": query_sequence,
        "snapshot_revision": frame["snapshot_revision"],
        "campaign_root_context": frame,
        "backend_id": "native-headless",
        "campaign_root_context_ready": available,
        "scope": "exact-campaign-root-context",
        "build": {
            "version": HARNESS.CAMPAIGN_ROOT_CONTEXT_V1_GAME_VERSION,
            "exe_sha256": (
                HARNESS.CAMPAIGN_ROOT_CONTEXT_V1_EXECUTABLE_SHA256
            ),
        },
        "source": {
            "game_version": HARNESS.CAMPAIGN_ROOT_CONTEXT_V1_GAME_VERSION,
            "executable_sha256": (
                HARNESS.CAMPAIGN_ROOT_CONTEXT_V1_EXECUTABLE_SHA256
            ),
            "snapshot_id": selected_snapshot_id,
            "revision": public_revision,
            "native_revision": native_revision,
            "date_raw": DATE_RAW,
            "paused": True,
            "backend_id": "native-headless",
        },
        "binding": {
            "snapshot_id": selected_snapshot_id,
            "revision": public_revision,
            "native_revision": native_revision,
            "date_raw": DATE_RAW,
            "expected_revision": public_revision,
        },
    }


class _FakeService:
    def __init__(
        self,
        directory: Path,
        *,
        available: bool = True,
        result_drift: bool = False,
        business_drift: bool = False,
        snapshot_drift: bool = False,
        public_revision: int = PUBLIC_REVISION,
        native_revision: int = NATIVE_REVISION,
    ) -> None:
        self.directory = directory
        self.available = available
        self.result_drift = result_drift
        self.business_drift = business_drift
        self.snapshot_drift = snapshot_drift
        self.public_revision = public_revision
        self.native_revision = native_revision
        self.query_count = 0
        self.saved = False
        self.calls: list[tuple[str, int]] = []

    def snapshot(self) -> dict[str, object]:
        drift = int(self.snapshot_drift and self.query_count >= 1)
        save_advance = int(self.saved)
        revision = self.public_revision + drift + save_advance
        native_revision = self.native_revision + drift + save_advance
        return {
            "snapshot_id": f"native:{native_revision}",
            "revision": revision,
            "native_revision": native_revision,
            "date_raw": DATE_RAW,
            "paused": True,
            "episode_run_id": "campaign-root-live-fixture",
        }

    def query_campaign_root_context_v1(
        self, *, expected_revision: int
    ) -> dict[str, object]:
        self.calls.append((HARNESS.QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
                           expected_revision))
        if expected_revision != self.public_revision:
            raise AssertionError("query did not use the frozen public revision")
        self.query_count += 1
        context = _context(
            snapshot_revision=self.native_revision,
            available=self.available,
        )
        if self.business_drift and self.query_count == 2:
            context["capital_province_id"] = 99
        result = _query_result(
            self.query_count,
            context=context,
            public_revision=self.public_revision,
            native_revision=self.native_revision,
        )
        if self.result_drift and self.query_count == 2:
            result["scope"] = "drifted"
        return result

    def save_checkpoint(
        self, *, expected_revision: int
    ) -> dict[str, object]:
        self.calls.append((HARNESS.SAVE_CHECKPOINT_STEP, expected_revision))
        if expected_revision != self.public_revision:
            raise AssertionError("save did not use the frozen public revision")
        path = self.directory / HARNESS.NATIVE_SESSION_CHECKPOINT_FILENAME
        path.write_bytes(b"campaign-root-checkpoint")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        self.saved = True
        return {
            "step": HARNESS.SAVE_CHECKPOINT_STEP,
            "accepted": True,
            "checkpoint": {
                "status": "saved",
                "path": str(path),
                "name": HARNESS.NATIVE_SESSION_CHECKPOINT_FILENAME,
                "size": path.stat().st_size,
                "sha256": digest,
                "date_raw": DATE_RAW,
                "history_index": 3,
                "episode_character_id": PLAYER_CHARACTER_ID,
                "episode_run_id": "campaign-root-live-fixture",
            },
        }


def _capabilities(*, include_query: bool = True) -> dict[str, object]:
    bridge_capabilities = (
        [HARNESS.QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY]
        if include_query
        else []
    )
    return {
        "bridge_capabilities": bridge_capabilities,
        "action_steps": [
            HARNESS.QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
            HARNESS.SAVE_CHECKPOINT_STEP,
        ],
        "campaign_root_context_v1_query_supported": include_query,
        "diagnostics": {
            "connected": True,
            "bridge_pid": 1234,
            "connection_generation": 5,
            "hello": {
                "capabilities": bridge_capabilities,
                "expected_ck3_version": (
                    HARNESS.CAMPAIGN_ROOT_CONTEXT_V1_GAME_VERSION
                ),
                "expected_ck3_sha256": (
                    HARNESS.CAMPAIGN_ROOT_CONTEXT_V1_EXECUTABLE_SHA256
                ),
                "game_adapter_id": HARNESS.EXPECTED_ADAPTER_ID,
                "game_adapter_status": "ready",
                "ck3_build_match": True,
            },
        },
    }


def _stage(
    *,
    pid: int,
    context: dict[str, object],
    date_raw: int,
    cold: bool,
) -> dict[str, object]:
    query = _query_result(1, context=context)
    return {
        "ok": True,
        "cold_start_checkpoint": cold,
        "same_process_proof": {"bridge_pid": pid, "ok": True},
        "sequence": {
            "date_raw": date_raw,
            "first_query": query,
            "business_value": HARNESS._campaign_business_value(query),
            "ok": True,
        },
    }


class CampaignRootContextLiveAcceptanceTests(unittest.TestCase):
    def test_stage_a_double_query_and_save_are_exactly_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            service = _FakeService(Path(raw))
            result = HARNESS._run_double_query_sequence(
                service, save_checkpoint=True
            )

        self.assertTrue(result["ok"])
        self.assertTrue(result["query_checks"]["only_query_sequence_changed"])
        self.assertTrue(result["checkpoint"]["ok"])
        self.assertTrue(result["checkpoint_transition_proof"]["ok"])
        self.assertEqual(
            [call[0] for call in service.calls],
            [
                HARNESS.QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
                HARNESS.QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
                HARNESS.SAVE_CHECKPOINT_STEP,
            ],
        )

    def test_checkpoint_save_accepts_exact_forward_snapshot_transition(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as raw:
            service = _FakeService(
                Path(raw), public_revision=4, native_revision=3
            )
            result = HARNESS._run_double_query_sequence(
                service, save_checkpoint=True
            )

        self.assertTrue(result["ok"])
        transition = result["checkpoint_transition_proof"]
        self.assertEqual(
            transition["before"],
            {
                "snapshot_id": "native:3",
                "revision": 4,
                "native_revision": 3,
                "date_raw": DATE_RAW,
                "episode_run_id": "campaign-root-live-fixture",
                "paused": True,
            },
        )
        self.assertEqual(
            transition["after"],
            {
                "snapshot_id": "native:4",
                "revision": 5,
                "native_revision": 4,
                "date_raw": DATE_RAW,
                "episode_run_id": "campaign-root-live-fixture",
                "paused": True,
            },
        )

    def test_stage_b_double_query_never_saves(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            service = _FakeService(Path(raw))
            result = HARNESS._run_double_query_sequence(
                service, save_checkpoint=False
            )

        self.assertTrue(result["ok"])
        self.assertIsNone(result["checkpoint"])
        self.assertEqual(
            [call[0] for call in service.calls],
            [
                HARNESS.QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
                HARNESS.QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
            ],
        )

    def test_only_query_sequence_may_change(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            result = HARNESS._run_double_query_sequence(
                _FakeService(Path(raw), result_drift=True),
                save_checkpoint=False,
            )

        self.assertFalse(result["ok"])
        self.assertFalse(
            result["query_checks"]["only_query_sequence_changed"]
        )

    def test_context_business_drift_is_rejected_within_stage(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            result = HARNESS._run_double_query_sequence(
                _FakeService(Path(raw), business_drift=True),
                save_checkpoint=False,
            )

        self.assertFalse(result["ok"])
        self.assertFalse(result["query_checks"]["normalized_contexts_equal"])

    def test_typed_unavailable_is_retained_but_not_green(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            result = HARNESS._run_double_query_sequence(
                _FakeService(Path(raw), available=False),
                save_checkpoint=False,
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["first_query"]["status"], "unavailable")
        self.assertEqual(
            result["first_query"]["campaign_root_context"][
                "unavailable_reason"
            ],
            "state_changed",
        )

    def test_snapshot_revision_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            result = HARNESS._run_double_query_sequence(
                _FakeService(Path(raw), snapshot_drift=True),
                save_checkpoint=False,
            )

        self.assertFalse(result["ok"])
        self.assertFalse(
            result["query_checks"]["between_same_paused_binding"]
        )

    def test_capability_proof_classifies_save_as_action_only(self) -> None:
        result = HARNESS._capability_proof(
            _capabilities(), require_save_checkpoint=True
        )

        self.assertTrue(result["ok"])
        self.assertEqual(
            result["required_bridge_capabilities"],
            [HARNESS.QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY],
        )
        self.assertIn(
            HARNESS.SAVE_CHECKPOINT_STEP, result["required_action_steps"]
        )

    def test_capability_proof_requires_query_in_hello_and_bridge(self) -> None:
        result = HARNESS._capability_proof(
            _capabilities(include_query=False), require_save_checkpoint=False
        )
        self.assertFalse(result["ok"])

    def test_production_shaped_hello_qualifies_exact_build(self) -> None:
        result = HARNESS._exact_build_proof(
            _capabilities(),
            HARNESS.CAMPAIGN_ROOT_CONTEXT_V1_EXECUTABLE_SHA256,
        )
        self.assertTrue(result["ok"])

    def test_cross_stage_ignores_only_context_binding_fields(self) -> None:
        stage_a = _stage(
            pid=101,
            context=_context(snapshot_revision=19, date_raw=DATE_RAW),
            date_raw=DATE_RAW,
            cold=False,
        )
        stage_b = _stage(
            pid=202,
            context=_context(snapshot_revision=44, date_raw=DATE_RAW),
            date_raw=DATE_RAW,
            cold=True,
        )
        transfer = {
            "ok": True,
            "target_validation": {"saved_date_raw": DATE_RAW},
        }

        result = HARNESS._cross_stage_proof(stage_a, stage_b, transfer)

        self.assertTrue(result["ok"])
        self.assertNotEqual(
            result["stage_a_snapshot_revision"],
            result["stage_b_snapshot_revision"],
        )

    def test_cross_stage_rejects_business_change_and_pid_reuse(self) -> None:
        stage_a = _stage(
            pid=101,
            context=_context(),
            date_raw=DATE_RAW,
            cold=False,
        )
        changed = _context(snapshot_revision=44)
        changed["capital_province_id"] = 99
        stage_b = _stage(
            pid=101,
            context=changed,
            date_raw=DATE_RAW,
            cold=True,
        )
        transfer = {
            "ok": True,
            "target_validation": {"saved_date_raw": DATE_RAW},
        }

        result = HARNESS._cross_stage_proof(stage_a, stage_b, transfer)

        self.assertFalse(result["ok"])
        self.assertFalse(
            result["checks"]["campaign_business_values_equal"]
        )
        self.assertFalse(
            result["checks"]["distinct_positive_managed_pids"]
        )

    def test_source_save_resolution_is_hash_bound_and_contained(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            profile = root / "profile"
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

    def test_checkpoint_bundle_is_minimal_and_cold_validated(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source_spec = HARNESS.make_spec(root / "a", root / "game")
            target_spec = HARNESS.make_spec(root / "b", root / "game")
            checkpoint = (
                source_spec.profile_dir
                / "save games"
                / HARNESS.NATIVE_SESSION_CHECKPOINT_FILENAME
            )
            checkpoint.parent.mkdir(parents=True)
            checkpoint.write_bytes(b"cold-checkpoint")
            digest = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
            size = checkpoint.stat().st_size
            driver_state = (
                source_spec.state_dir
                / HARNESS.NATIVE_SESSION_QUEUE_DIRNAME
                / HARNESS.NATIVE_DRIVER_STATE_FILENAME
            )
            driver_state.parent.mkdir(parents=True)
            saved = {"size": size, "sha256": digest, "date_raw": DATE_RAW}
            driver_state.write_text(
                json.dumps(
                    {
                        "format_version": 2,
                        "pipe_name": PIPE_NAME,
                        "bridge_pid": 111,
                        "episode_character_id": PLAYER_CHARACTER_ID,
                        "episode_run_id": "campaign-root-cold-fixture",
                        "last_checkpoint": {
                            "name": HARNESS.NATIVE_SESSION_CHECKPOINT_FILENAME,
                            "size": size,
                            "sha256": digest,
                            "date_raw": DATE_RAW,
                            "history_index": 1,
                            "episode_character_id": PLAYER_CHARACTER_ID,
                            "episode_run_id": "campaign-root-cold-fixture",
                        },
                        "command_history": [
                            {
                                "index": 1,
                                "command": HARNESS.SAVE_CHECKPOINT_STEP,
                                "ok": True,
                                "result": {"checkpoint": saved},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (target_spec.profile_dir / "save games").mkdir(parents=True)

            result = HARNESS._transfer_checkpoint_bundle(
                source_spec, target_spec, pipe_name=PIPE_NAME
            )

            self.assertTrue(result["ok"])
            self.assertEqual(
                result["transferred_files"],
                [
                    HARNESS.NATIVE_SESSION_CHECKPOINT_FILENAME,
                    "native-session/driver-state.json",
                ],
            )
            self.assertEqual(
                HARNESS._sha256_file(
                    target_spec.profile_dir
                    / "save games"
                    / HARNESS.NATIVE_SESSION_CHECKPOINT_FILENAME
                ),
                HARNESS._sha256_file(checkpoint),
            )

    def test_mutation_boundary_rejects_any_extra_command(self) -> None:
        result = HARNESS._mutation_boundary_proof(
            [
                HARNESS.QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
                "life-advance",
                HARNESS.QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
            ],
            save_checkpoint=False,
        )
        self.assertFalse(result["ok"])

    def test_cleanup_requires_matching_nonce_and_all_started_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            target = parent / "clone"
            target.mkdir()
            marker = target / HARNESS._DISPOSABLE_MARKER_NAME
            marker.write_text(
                json.dumps(
                    {"kind": HARNESS._DISPOSABLE_KIND, "nonce": "right"}
                ),
                encoding="utf-8",
            )
            blocked = HARNESS._cleanup_disposable_root(
                target,
                clone_nonce="right",
                retain_state=False,
                stages=[
                    {
                        "stage": "stage-a",
                        "session_started": True,
                        "cleanup": {"ok": False},
                    }
                ],
            )
            self.assertFalse(blocked["ok"])
            self.assertTrue(target.exists())

            removed = HARNESS._cleanup_disposable_root(
                target,
                clone_nonce="right",
                retain_state=False,
                stages=[
                    {
                        "stage": "stage-a",
                        "session_started": True,
                        "cleanup": {"ok": True},
                    },
                    {
                        "stage": "stage-b",
                        "session_started": True,
                        "cleanup": {"ok": True},
                    },
                ],
            )
            self.assertTrue(removed["ok"])
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
