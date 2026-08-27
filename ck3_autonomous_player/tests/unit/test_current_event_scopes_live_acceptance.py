from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import re
from types import SimpleNamespace
import tempfile
import unittest
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[2]
HARNESS_PATH = (
    PROJECT_ROOT
    / "native_bridge"
    / "research"
    / "run_current_event_scopes_live_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_current_event_scopes_live_acceptance",
    HARNESS_PATH,
)
assert SPEC is not None and SPEC.loader is not None
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)
BASE = HARNESS.BASE


EVENT_ID = 0x2C00_0042
PUBLIC_REVISION = 29
NATIVE_REVISION = 131
DATE_RAW = 53_175_816
CALCULATED_EVENT_ID = -712_345
RUNTIME_STATS_ORDINAL = 47
NAME_IDENTIFIER = 12_345


def _character_scope(character_id: int = BASE.PLAYER_CHARACTER_ID) -> dict[str, object]:
    return {
        "status": "available",
        "raw_type_index": 4,
        "type_key": "character",
        "subtype": 0,
        "typed_identity": {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        },
    }


def _saved_scopes(
    *,
    character_id: int = BASE.PLAYER_CHARACTER_ID,
    name_identifier: int = NAME_IDENTIFIER,
) -> list[dict[str, object]]:
    return [
        {
            "name": HARNESS.EXPECTED_SAVED_SCOPE_NAME,
            "name_identifier": name_identifier,
            "scope": _character_scope(character_id),
        }
    ]


def _options() -> list[dict[str, object]]:
    return [
        {
            "rendered_index": 0,
            "native_option_index": 0,
            "shown": True,
            "enabled": True,
            "fallback": False,
            "cancel": False,
            "resolved_name": HARNESS.EXPECTED_OPTION_NAMES[0],
            "unavailable_reason": "",
            "effect_indicators": {
                "status": "available",
                "coverage": BASE.EXPECTED_EFFECT_INDICATOR_COVERAGE,
                "complete_effect_set": False,
                "rows": [],
            },
            "effect_preview": {
                "status": "unavailable",
                "reason": "indicator_subset_has_no_completeness_signal",
            },
            "resource_deltas": {"status": "unavailable"},
            "relationship_deltas": {"status": "unavailable"},
        }
    ]


def _readiness() -> dict[str, bool]:
    return {
        "event_definition_identity_ready": True,
        "root_scope_ready": True,
        "saved_scopes_ready": True,
        "option_presentation_ready": True,
        "effect_indicators_ready": True,
        "effect_preview_ready": False,
        "semantic_decision_ready": False,
    }


def _snapshot() -> dict[str, object]:
    return {
        "snapshot_id": f"native:{NATIVE_REVISION}",
        "revision": PUBLIC_REVISION,
        "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "paused": True,
        "map_ready": True,
        "episode_run_id": "event-scopes-live-fixture",
        "backend_id": "native-headless",
        "played_character": {
            "character_id": BASE.PLAYER_CHARACTER_ID,
            "alive": True,
        },
        "active_event": {"instance_id": EVENT_ID, "option_count": 1},
    }


def _frame(
    *,
    character_id: int = BASE.PLAYER_CHARACTER_ID,
    name_identifier: int = NAME_IDENTIFIER,
) -> dict[str, object]:
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "snapshot_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "current_event_instance_id": EVENT_ID,
        "window_match_count": 1,
        "unavailable_reason": None,
        "event_definition_key": HARNESS.EXPECTED_EVENT_KEY,
        "calculated_event_id": CALCULATED_EVENT_ID,
        "runtime_stats_ordinal": RUNTIME_STATS_ORDINAL,
        "root_scope": _character_scope(character_id),
        "saved_scopes": _saved_scopes(
            character_id=character_id,
            name_identifier=name_identifier,
        ),
        "options": _options(),
        "readiness": _readiness(),
        "provenance": {
            "root": "module+0x570F7B8->+0x10",
            "idler_vtable_rva": "0x40B1D30",
            "manager_offset": "+0x28",
            "backend_id": "ck3-1.19.0.6-native-event-window-v1",
        },
    }


_MIRROR_KEYS = (
    "schema",
    "schema_version",
    "date_raw",
    "current_event_instance_id",
    "window_match_count",
    "unavailable_reason",
    "event_definition_key",
    "calculated_event_id",
    "runtime_stats_ordinal",
    "root_scope",
    "saved_scopes",
    "options",
    "readiness",
    "provenance",
)


def _query_result(
    sequence: int,
    *,
    character_id: int = BASE.PLAYER_CHARACTER_ID,
    name_identifier: int = NAME_IDENTIFIER,
) -> dict[str, object]:
    frame = _frame(
        character_id=character_id,
        name_identifier=name_identifier,
    )
    result = {
        "step": BASE.QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
        "accepted": True,
        "status": "available",
        "query_sequence": sequence,
        "snapshot_revision": NATIVE_REVISION,
        "current_event_window_context": copy.deepcopy(frame),
        "backend_id": "native-headless",
        "current_event_window_context_ready": True,
        "current_event_effect_indicators_ready": True,
        "queried_snapshot_id": f"native:{NATIVE_REVISION}",
        "queried_revision": PUBLIC_REVISION,
        "queried_native_revision": NATIVE_REVISION,
        "scope": "exact-current-event-window",
        "source": {
            "snapshot_id": f"native:{NATIVE_REVISION}",
            "revision": PUBLIC_REVISION,
            "native_revision": NATIVE_REVISION,
            "date_raw": DATE_RAW,
            "paused": True,
            "backend_id": "native-headless",
        },
        "binding": {
            "snapshot_id": f"native:{NATIVE_REVISION}",
            "revision": PUBLIC_REVISION,
            "native_revision": NATIVE_REVISION,
            "date_raw": DATE_RAW,
            "expected_revision": PUBLIC_REVISION,
            "event_instance_id": EVENT_ID,
        },
    }
    for key in _MIRROR_KEYS:
        result[key] = copy.deepcopy(frame[key])
    return result


def _context_proof(result: object) -> dict[str, object]:
    with HARNESS._installed_fixture_profile():
        return BASE._context_proof(
            result,
            event_id=EVENT_ID,
            snapshot_id=f"native:{NATIVE_REVISION}",
            public_revision=PUBLIC_REVISION,
            native_revision=NATIVE_REVISION,
            date_raw=DATE_RAW,
        )


def _cross_stage(
    *,
    seed_name_identifier: int = NAME_IDENTIFIER,
    cold_name_identifier: int = NAME_IDENTIFIER + 100,
    cold_character_id: int = BASE.PLAYER_CHARACTER_ID,
) -> dict[str, object]:
    seed = {
        "ok": True,
        "event_instance_id": EVENT_ID,
        "seed_query": _query_result(
            1, name_identifier=seed_name_identifier
        ),
        "stable_pre_save_snapshot": _snapshot(),
        "same_process_proof": {"bridge_pid": 101},
        "fixture_projection_proof": {
            "content_manifest": {
                "sha256": HARNESS.FIXTURE_CONTENT_MANIFEST_SHA256
            }
        },
        "mutation_boundary": {"ok": True},
    }
    cold = {
        "ok": True,
        "mod_bridge_loaded": False,
        "same_process_proof": {"bridge_pid": 202},
        "fixture_projection_proof": {
            "content_manifest": {
                "sha256": HARNESS.FIXTURE_CONTENT_MANIFEST_SHA256
            },
            "checks": {"mod_bridge_presence_matches_stage": True},
        },
        "sequence": {
            "current_event_instance_id": EVENT_ID,
            "date_raw": DATE_RAW,
            "first_query": _query_result(
                2,
                character_id=cold_character_id,
                name_identifier=cold_name_identifier,
            ),
            "mutation_boundary": {"ok": True},
        },
    }
    with HARNESS._installed_fixture_profile():
        return BASE._cross_stage_proof(seed, cold, {"ok": True})


class _FakeAdjacentService:
    def __init__(self, *, second_name_identifier: int = NAME_IDENTIFIER) -> None:
        self._snapshots = iter((_snapshot(), _snapshot(), _snapshot()))
        self._queries = iter(
            (
                _query_result(41, name_identifier=NAME_IDENTIFIER),
                _query_result(
                    42, name_identifier=second_name_identifier
                ),
            )
        )

    def snapshot(self) -> dict[str, object]:
        return copy.deepcopy(next(self._snapshots))

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]:
        if event_instance_id != EVENT_ID or expected_revision != PUBLIC_REVISION:
            raise AssertionError("fixture query binding changed")
        return copy.deepcopy(next(self._queries))


class CurrentEventScopesFixtureTests(unittest.TestCase):
    def test_definition_is_exact_nonreligious_character_scope_fixture(self) -> None:
        proof = HARNESS._fixture_definition_contract()
        self.assertTrue(proof["ok"], proof)
        self.assertTrue(proof["checks"]["single_exact_root_save"])
        self.assertTrue(proof["checks"]["single_effectless_option"])
        self.assertEqual(
            proof["event_definition_sha256"], HARNESS.FIXTURE_EVENT_SHA256
        )
        self.assertEqual(
            proof["content_manifest"]["sha256"],
            HARNESS.FIXTURE_CONTENT_MANIFEST_SHA256,
        )

    def test_implementation_freeze_placeholders_are_explicit_and_centralized(
        self,
    ) -> None:
        commit = HARNESS.FROZEN_SCOPE_SOURCE_COMMIT
        dll = HARNESS.FROZEN_SCOPE_BRIDGE_DLL_SHA256
        self.assertTrue(
            commit == "__IMPLEMENTATION_COMMIT__"
            or re.fullmatch(r"[0-9a-f]{40}", commit) is not None
        )
        self.assertTrue(
            dll == "__IMPLEMENTATION_DLL_SHA256__"
            or re.fullmatch(r"[0-9A-F]{64}", dll) is not None
        )
        source = HARNESS_PATH.read_text(encoding="utf-8")
        if commit == "__IMPLEMENTATION_COMMIT__":
            self.assertEqual(source.count('"__IMPLEMENTATION_COMMIT__"'), 1)
        if dll == "__IMPLEMENTATION_DLL_SHA256__":
            self.assertEqual(
                source.count('"__IMPLEMENTATION_DLL_SHA256__"'), 1
            )

    def test_profile_is_scoped_and_restores_every_base_hook(self) -> None:
        originals = {
            "key": BASE.EXPECTED_EVENT_KEY,
            "commit": BASE.FROZEN_SOURCE_COMMIT,
            "dll": BASE.FROZEN_BRIDGE_DLL_SHA256,
            "seed_stage_name": BASE._SEED_STAGE_NAME,
            "cold_stage_name": BASE._COLD_STAGE_NAME,
            "shape": BASE._expected_option_shape,
            "context": BASE._context_proof,
            "cross": BASE._cross_stage_proof,
            "seed_stage": BASE._run_seed_stage,
            "cold_stage": BASE._run_cold_query_stage,
            "checkpoint_transfer": BASE._checkpoint_transfer_proof,
            "cleanup_root": BASE._cleanup_root,
            "mutation_boundary": BASE._mutation_boundary_proof,
        }
        with HARNESS._installed_fixture_profile():
            self.assertEqual(BASE.EXPECTED_EVENT_KEY, HARNESS.EXPECTED_EVENT_KEY)
            self.assertEqual(
                BASE.FROZEN_SOURCE_COMMIT,
                HARNESS.FROZEN_SCOPE_SOURCE_COMMIT,
            )
            self.assertEqual(
                BASE.FROZEN_BRIDGE_DLL_SHA256,
                HARNESS.FROZEN_SCOPE_BRIDGE_DLL_SHA256,
            )
            self.assertEqual(BASE._SEED_STAGE_NAME, HARNESS._SEED_STAGE_NAME)
            self.assertEqual(BASE._COLD_STAGE_NAME, HARNESS._COLD_STAGE_NAME)
            self.assertIs(BASE._context_proof, HARNESS._context_proof)
            self.assertIs(BASE._cross_stage_proof, HARNESS._cross_stage_proof)
            self.assertIs(BASE._run_seed_stage, originals["seed_stage"])
            self.assertIs(BASE._run_cold_query_stage, originals["cold_stage"])
            self.assertIs(
                BASE._checkpoint_transfer_proof,
                originals["checkpoint_transfer"],
            )
            self.assertIs(BASE._cleanup_root, originals["cleanup_root"])
            self.assertIs(
                BASE._mutation_boundary_proof,
                originals["mutation_boundary"],
            )
        self.assertEqual(BASE.EXPECTED_EVENT_KEY, originals["key"])
        self.assertEqual(BASE.FROZEN_SOURCE_COMMIT, originals["commit"])
        self.assertEqual(BASE.FROZEN_BRIDGE_DLL_SHA256, originals["dll"])
        self.assertEqual(BASE._SEED_STAGE_NAME, originals["seed_stage_name"])
        self.assertEqual(BASE._COLD_STAGE_NAME, originals["cold_stage_name"])
        self.assertIs(BASE._expected_option_shape, originals["shape"])
        self.assertIs(BASE._context_proof, originals["context"])
        self.assertIs(BASE._cross_stage_proof, originals["cross"])

    def test_generate_effect_is_guarded_and_never_selects_option(self) -> None:
        with HARNESS._installed_fixture_profile():
            proof = BASE._effect_contract()
        self.assertTrue(proof["ok"], proof)
        self.assertIn(
            f"trigger_event = {{ id = {HARNESS.EXPECTED_EVENT_KEY} }}",
            proof["source"],
        )
        self.assertNotIn("select-event-option", proof["source"])

    def test_generated_paths_remain_below_physfs_limit(self) -> None:
        root = Path(tempfile.gettempdir()) / (HARNESS._ROOT_PREFIX + "a" * 32)
        with HARNESS._installed_fixture_profile():
            proof = BASE._generated_fixture_path_length_contract(root)
        self.assertTrue(proof["ok"], proof)
        self.assertLess(
            proof["maximum_generated_path_characters"],
            proof["ck3_physfs_path_limit"],
        )

    def test_cold_projection_has_fixture_and_no_mod_bridge(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            profile = Path(raw) / "profile"
            (profile / "mod").mkdir(parents=True)
            production = profile / "mod-content" / "production"
            production.mkdir(parents=True)
            (profile / "dlc_load.json").write_text(
                json.dumps(
                    {
                        "enabled_mods": [BASE.OUTER_DESCRIPTOR_REF],
                        "disabled_dlcs": [],
                    }
                ),
                encoding="utf-8",
            )
            spec = SimpleNamespace(
                profile_dir=profile,
                production_dir=production,
            )
            with HARNESS._installed_fixture_profile():
                BASE._install_fixture_definition(spec)
                proof = BASE._fixture_projection_proof(
                    spec, seed_stage=False
                )
            self.assertTrue(proof["ok"], proof)
            self.assertTrue(
                proof["checks"]["mod_bridge_presence_matches_stage"]
            )

    def test_option_shape_is_single_enabled_effectless_row(self) -> None:
        self.assertTrue(HARNESS._expected_option_shape(_options()))
        malformed = _options()
        malformed[0]["effect_indicators"]["rows"] = [
            {
                "kind": "death",
                "subject": "played_character",
                "direction": "not_applicable",
            }
        ]
        self.assertFalse(HARNESS._expected_option_shape(malformed))
        malformed = _options()
        malformed[0]["unexpected"] = True
        self.assertFalse(HARNESS._expected_option_shape(malformed))

    def test_context_proof_accepts_exact_root_named_scope_and_readiness(self) -> None:
        proof = _context_proof(_query_result(1))
        self.assertTrue(proof["ok"], proof)
        for key in (
            "root_scope_exact_played_character",
            "single_named_scope_exact_played_character",
            "readiness_truthful",
            "effect_and_semantic_readiness_false",
            "strict_mirrors",
        ):
            self.assertTrue(proof["checks"][key], key)
        self.assertNotIn(
            "root_and_saved_scopes_unavailable", proof["checks"]
        )

    def test_name_identifier_contract_is_full_signed_int32(self) -> None:
        for name_identifier in (-(2**31), -1, 0, 2**31 - 1):
            with self.subTest(valid=name_identifier):
                proof = _context_proof(
                    _query_result(1, name_identifier=name_identifier)
                )
                self.assertTrue(proof["ok"], proof)
                self.assertTrue(
                    proof["checks"][
                        "single_named_scope_exact_played_character"
                    ]
                )

        for name_identifier in (-(2**31) - 1, 2**31, True, 1.0, "1"):
            with self.subTest(invalid=name_identifier):
                result = _query_result(1)
                result["saved_scopes"][0]["name_identifier"] = name_identifier
                result["current_event_window_context"]["saved_scopes"][0][
                    "name_identifier"
                ] = name_identifier
                proof = _context_proof(result)
                self.assertFalse(proof["ok"])
                self.assertFalse(
                    proof["checks"][
                        "single_named_scope_exact_played_character"
                    ]
                )

    def test_context_proof_rejects_root_character_or_type_drift(self) -> None:
        for name, mutate in (
            (
                "character_id",
                lambda scope: scope["typed_identity"].__setitem__(
                    "character_id", BASE.PLAYER_CHARACTER_ID + 1
                ),
            ),
            (
                "type_key",
                lambda scope: scope.__setitem__("type_key", "title"),
            ),
            (
                "raw_type",
                lambda scope: scope.__setitem__("raw_type_index", 7),
            ),
        ):
            with self.subTest(name=name):
                result = _query_result(1)
                mutate(result["root_scope"])
                mutate(
                    result["current_event_window_context"]["root_scope"]
                )
                proof = _context_proof(result)
                self.assertFalse(proof["ok"])
                self.assertFalse(
                    proof["checks"]["root_scope_exact_played_character"]
                )

    def test_context_proof_rejects_named_scope_drift_and_raw_payload(self) -> None:
        mutations = (
            lambda row: row.__setitem__("name", "wrong_scope"),
            lambda row: row.__setitem__("name_identifier", True),
            lambda row: row["scope"]["typed_identity"].__setitem__(
                "character_id", BASE.PLAYER_CHARACTER_ID + 1
            ),
            lambda row: row["scope"].__setitem__(
                "raw_16_bytes_hex", "00" * 16
            ),
        )
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                result = _query_result(1)
                mutate(result["saved_scopes"][0])
                mutate(
                    result["current_event_window_context"]["saved_scopes"][0]
                )
                proof = _context_proof(result)
                self.assertFalse(proof["ok"])
                self.assertFalse(
                    proof["checks"][
                        "single_named_scope_exact_played_character"
                    ]
                )

    def test_context_proof_rejects_scope_or_semantic_readiness_drift(self) -> None:
        for key, value in (
            ("root_scope_ready", False),
            ("saved_scopes_ready", False),
            ("effect_preview_ready", True),
            ("semantic_decision_ready", True),
        ):
            with self.subTest(key=key):
                result = _query_result(1)
                result["readiness"][key] = value
                result["current_event_window_context"]["readiness"][key] = value
                proof = _context_proof(result)
                self.assertFalse(proof["ok"])
                self.assertFalse(proof["checks"]["readiness_truthful"])

    def test_cross_stage_uses_stable_scope_identity_not_numeric_name_id(self) -> None:
        proof = _cross_stage(
            seed_name_identifier=17,
            cold_name_identifier=29,
        )
        self.assertTrue(proof["ok"], proof)
        self.assertTrue(proof["checks"]["same_stable_scope_identities"])
        self.assertTrue(proof["checks"]["scope_readiness_stays_true"])
        self.assertNotIn("unclosed_semantics_stay_false", proof["checks"])

    def test_cross_stage_rejects_character_identity_drift(self) -> None:
        proof = _cross_stage(
            cold_character_id=BASE.PLAYER_CHARACTER_ID + 1
        )
        self.assertFalse(proof["ok"])
        self.assertFalse(proof["checks"]["same_stable_scope_identities"])

    def test_adjacent_cold_queries_are_exact_except_sequence(self) -> None:
        with HARNESS._installed_fixture_profile():
            proof = BASE._run_double_query_sequence(
                _FakeAdjacentService(),
                expected_event_id=EVENT_ID,
                expected_date_raw=DATE_RAW,
            )
        self.assertTrue(proof["ok"], proof)
        self.assertTrue(
            proof["checks"]["adjacent_context_frames_strictly_equal"]
        )
        self.assertTrue(proof["checks"]["only_query_sequence_changed"])

    def test_adjacent_cold_queries_reject_same_process_name_id_drift(self) -> None:
        with HARNESS._installed_fixture_profile():
            proof = BASE._run_double_query_sequence(
                _FakeAdjacentService(
                    second_name_identifier=NAME_IDENTIFIER + 1
                ),
                expected_event_id=EVENT_ID,
                expected_date_raw=DATE_RAW,
            )
        self.assertFalse(proof["ok"])
        self.assertFalse(
            proof["checks"]["adjacent_context_frames_strictly_equal"]
        )
        self.assertFalse(proof["checks"]["only_query_sequence_changed"])

    def test_command_boundary_never_allows_event_selection(self) -> None:
        seed = BASE._mutation_boundary_proof(
            [BASE.QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP, "save-checkpoint"],
            seed_stage=True,
        )
        cold = BASE._mutation_boundary_proof(
            [
                BASE.QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                BASE.QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
            ],
            seed_stage=False,
        )
        selected = BASE._mutation_boundary_proof(
            ["select-event-option-1"], seed_stage=False
        )
        self.assertTrue(seed["ok"], seed)
        self.assertTrue(cold["ok"], cold)
        self.assertFalse(selected["ok"])

    def test_wrapper_replaces_old_null_scope_gate_and_preserves_base_gates(
        self,
    ) -> None:
        context_checks = {
            "root_scope_exact_played_character": True,
            "single_named_scope_exact_played_character": True,
            "readiness_truthful": True,
            "effect_and_semantic_readiness_false": True,
        }
        cross_checks = {
            "root_scope_exact_in_both_stages": True,
            "saved_scope_exact_in_both_stages": True,
            "same_stable_scope_identities": True,
            "scope_readiness_stays_true": True,
            "effect_and_semantic_readiness_stay_false": True,
        }
        base_payload = {
            "ok": False,
            "error": None,
            "evidence_classification": "not-qualified",
            "fixed_scenario": {
                "authored_option_count": 5,
                "expected_rendered_native_indices": [0, 1, 3],
                "expected_hidden_native_index": 2,
                "expected_unmaterialized_fallback_native_index": 4,
            },
            "policy": {},
            "readiness_gates": {
                "effect_scopes_and_semantic_readiness_remain_unclosed": False,
                "immutable_source_bytes_and_metadata": True,
                "managed_process_cleanup": True,
                "nonce_disposable_cleanup": True,
                "adjacent_same_revision_double_query": True,
                "no_event_option_selected": True,
            },
            "cold_stage": {
                "sequence": {
                    "first_context_proof": {"checks": context_checks}
                }
            },
            "cross_stage_proof": {"checks": cross_checks},
            "frozen_source_contract": {},
        }
        args = SimpleNamespace()
        with mock.patch.object(
            BASE, "_run", return_value=(base_payload, 1)
        ) as delegated:
            payload, exit_code = HARNESS._run(args)
        delegated.assert_called_once_with(args)
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(
            payload["kind"], "ck3_current_event_scopes_live_acceptance"
        )
        self.assertNotIn(
            "effect_scopes_and_semantic_readiness_remain_unclosed",
            payload["readiness_gates"],
        )
        self.assertTrue(
            payload["readiness_gates"][
                "root_and_named_character_scopes_exact"
            ]
        )
        self.assertTrue(
            payload["readiness_gates"][
                "immutable_source_bytes_and_metadata"
            ]
        )
        self.assertTrue(payload["readiness_gates"]["managed_process_cleanup"])
        self.assertTrue(payload["readiness_gates"]["nonce_disposable_cleanup"])
        self.assertTrue(payload["readiness_gates"]["no_event_option_selected"])
        self.assertTrue(payload["policy"]["root_scope_ready_expected"])
        self.assertFalse(
            payload["policy"][
                "named_scope_identifier_is_cross_process_identity"
            ]
        )

        for blocking_gate in (
            "managed_process_cleanup",
            "nonce_disposable_cleanup",
            "no_event_option_selected",
        ):
            with self.subTest(blocking_gate=blocking_gate):
                red_payload = copy.deepcopy(base_payload)
                red_payload["readiness_gates"][blocking_gate] = False
                with mock.patch.object(
                    BASE, "_run", return_value=(red_payload, 1)
                ):
                    wrapped, wrapped_exit = HARNESS._run(args)
                self.assertFalse(wrapped["ok"])
                self.assertEqual(wrapped_exit, 1)
                self.assertFalse(
                    wrapped["readiness_gates"][blocking_gate]
                )


if __name__ == "__main__":
    unittest.main()
