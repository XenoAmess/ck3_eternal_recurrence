from __future__ import annotations

import copy
import importlib.util
import json
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
    / "run_current_event_nonempty_effect_indicators_live_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_current_event_nonempty_effect_indicators_live_acceptance",
    HARNESS_PATH,
)
assert SPEC is not None and SPEC.loader is not None
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)
BASE = HARNESS.BASE


EVENT_ID = 0x2C00_0042
PUBLIC_REVISION = 23
NATIVE_REVISION = 101
DATE_RAW = 53_175_816
CALCULATED_EVENT_ID = -612_345
RUNTIME_STATS_ORDINAL = 43


def _effect_surface(rows: list[dict[str, object]]) -> dict[str, object]:
    return {
        "effect_indicators": {
            "status": "available",
            "coverage": BASE.EXPECTED_EFFECT_INDICATOR_COVERAGE,
            "complete_effect_set": False,
            "rows": copy.deepcopy(rows),
        },
        "effect_preview": {
            "status": "unavailable",
            "reason": "indicator_subset_has_no_completeness_signal",
        },
        "resource_deltas": {"status": "unavailable"},
        "relationship_deltas": {"status": "unavailable"},
    }


def _trait_row() -> dict[str, object]:
    return {
        "kind": "trait",
        "operation": "add",
        "trait": {"status": "available", "native_id": 123, "key": "brave"},
    }


def _stress_row() -> dict[str, object]:
    return {
        "kind": "stress",
        "direction": "increase",
        "magnitude": {"status": "unavailable"},
        "affected_by_trait": False,
        "critical": False,
    }


def _death_row() -> dict[str, object]:
    return {
        "kind": "death",
        "subject": "played_character",
        "direction": "not_applicable",
    }


def _options() -> list[dict[str, object]]:
    rows = ([], [_trait_row()], [_stress_row(), _death_row()])
    presentation = (
        (0, 0, False, HARNESS.EXPECTED_OPTION_NAMES[0]),
        (1, 1, False, HARNESS.EXPECTED_OPTION_NAMES[1]),
        (2, 3, True, HARNESS.EXPECTED_OPTION_NAMES[2]),
    )
    result: list[dict[str, object]] = []
    for indicators, expected in zip(rows, presentation, strict=True):
        rendered, native, cancel, name = expected
        result.append(
            {
                "rendered_index": rendered,
                "native_option_index": native,
                "shown": True,
                "enabled": True,
                "fallback": False,
                "cancel": cancel,
                "resolved_name": name,
                "unavailable_reason": "",
                **_effect_surface(indicators),
            }
        )
    return result


def _snapshot() -> dict[str, object]:
    return {
        "snapshot_id": f"native:{NATIVE_REVISION}",
        "revision": PUBLIC_REVISION,
        "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "paused": True,
        "map_ready": True,
        "episode_run_id": "event-nonempty-indicator-live-fixture",
        "backend_id": "native-headless",
        "played_character": {
            "character_id": BASE.PLAYER_CHARACTER_ID,
            "alive": True,
        },
        "active_event": {"instance_id": EVENT_ID, "option_count": 5},
    }


def _frame() -> dict[str, object]:
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
        "root_scope": None,
        "saved_scopes": None,
        "options": _options(),
        "readiness": {
            "event_definition_identity_ready": True,
            "option_presentation_ready": True,
            "effect_indicators_ready": True,
            "effect_preview_ready": False,
            "semantic_decision_ready": False,
        },
        "provenance": {
            "root": "module+0x570F7B8->+0x10",
            "idler_vtable_rva": "0x40B1D30",
            "manager_offset": "+0x28",
            "backend_id": "ck3-1.19.0.6-native-event-window-v1",
        },
    }


def _query_result(sequence: int) -> dict[str, object]:
    frame = _frame()
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
    for key in (
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
    ):
        result[key] = copy.deepcopy(frame[key])
    return result


class CurrentEventNonemptyIndicatorFixtureTests(unittest.TestCase):
    def test_definition_is_exact_nonreligious_and_nonempty(self) -> None:
        proof = HARNESS._fixture_definition_contract()
        self.assertTrue(proof["ok"], proof)
        self.assertEqual(
            proof["expected_indicator_kinds"], ["trait", "stress", "death"]
        )
        self.assertEqual(proof["empty_row_control_native_index"], 0)
        self.assertEqual(
            proof["event_definition_sha256"], HARNESS.FIXTURE_EVENT_SHA256
        )
        self.assertEqual(
            proof["content_manifest"]["sha256"],
            HARNESS.FIXTURE_CONTENT_MANIFEST_SHA256,
        )

    def test_profile_is_scoped_and_restores_base_runner(self) -> None:
        original_key = BASE.EXPECTED_EVENT_KEY
        original_shape = BASE._expected_option_shape
        with HARNESS._installed_fixture_profile():
            self.assertEqual(BASE.EXPECTED_EVENT_KEY, HARNESS.EXPECTED_EVENT_KEY)
            self.assertIs(BASE._expected_option_shape, HARNESS._expected_option_shape)
        self.assertEqual(BASE.EXPECTED_EVENT_KEY, original_key)
        self.assertIs(BASE._expected_option_shape, original_shape)

    def test_generate_effect_is_guarded_and_never_selects_an_option(self) -> None:
        with HARNESS._installed_fixture_profile():
            proof = BASE._effect_contract()
        self.assertTrue(proof["ok"], proof)
        self.assertIn(
            f"trigger_event = {{ id = {HARNESS.EXPECTED_EVENT_KEY} }}",
            proof["source"],
        )
        self.assertNotIn("select-event-option", proof["source"])

    def test_generated_paths_stay_below_physfs_limit(self) -> None:
        root = Path(tempfile.gettempdir()) / (HARNESS._ROOT_PREFIX + "a" * 32)
        with HARNESS._installed_fixture_profile():
            proof = BASE._generated_fixture_path_length_contract(root)
        self.assertTrue(proof["ok"], proof)
        self.assertLess(
            proof["maximum_generated_path_characters"],
            proof["ck3_physfs_path_limit"],
        )

    def test_cold_projection_has_exact_fixture_and_no_mod_bridge(self) -> None:
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
            spec = SimpleNamespace(profile_dir=profile, production_dir=production)
            with HARNESS._installed_fixture_profile():
                BASE._install_fixture_definition(spec)
                proof = BASE._fixture_projection_proof(spec, seed_stage=False)
            self.assertTrue(proof["ok"], proof)
            self.assertTrue(
                proof["checks"]["mod_bridge_presence_matches_stage"]
            )

    def test_expected_shape_accepts_empty_trait_stress_death_matrix(self) -> None:
        self.assertTrue(HARNESS._expected_option_shape(_options()))

    def test_empty_control_must_remain_empty(self) -> None:
        malformed = _options()
        malformed[0]["effect_indicators"]["rows"] = [_death_row()]
        self.assertFalse(HARNESS._expected_option_shape(malformed))

    def test_trait_identity_must_be_available_brave(self) -> None:
        for field, value in (("status", "unavailable"), ("key", "calm")):
            malformed = _options()
            malformed[1]["effect_indicators"]["rows"][0]["trait"][field] = value
            self.assertFalse(HARNESS._expected_option_shape(malformed))
        malformed = _options()
        malformed[1]["effect_indicators"]["rows"][0]["trait"]["native_id"] = True
        self.assertFalse(HARNESS._expected_option_shape(malformed))
        malformed = _options()
        malformed[1]["effect_indicators"]["rows"][0]["trait"]["native_id"] = -1
        self.assertFalse(HARNESS._expected_option_shape(malformed))

    def test_stress_row_keeps_lossy_magnitude_and_typed_flags(self) -> None:
        malformed = _options()
        malformed[2]["effect_indicators"]["rows"][0]["magnitude"] = 10
        self.assertFalse(HARNESS._expected_option_shape(malformed))
        malformed = _options()
        malformed[2]["effect_indicators"]["rows"][0]["critical"] = 0
        self.assertFalse(HARNESS._expected_option_shape(malformed))

    def test_death_row_is_exact_and_cannot_inherit_raw_gain(self) -> None:
        malformed = _options()
        malformed[2]["effect_indicators"]["rows"][1]["gain"] = True
        self.assertFalse(HARNESS._expected_option_shape(malformed))
        malformed = _options()
        malformed[2]["effect_indicators"]["rows"].reverse()
        self.assertFalse(HARNESS._expected_option_shape(malformed))

    def test_context_proof_keeps_semantic_readiness_false(self) -> None:
        with HARNESS._installed_fixture_profile():
            proof = BASE._context_proof(
                _query_result(1),
                event_id=EVENT_ID,
                snapshot_id=f"native:{NATIVE_REVISION}",
                public_revision=PUBLIC_REVISION,
                native_revision=NATIVE_REVISION,
                date_raw=DATE_RAW,
            )
        self.assertTrue(proof["ok"], proof)
        self.assertTrue(proof["checks"]["materialized_option_shape"])
        readiness = _frame()["readiness"]
        self.assertFalse(readiness["effect_preview_ready"])
        self.assertFalse(readiness["semantic_decision_ready"])

    def test_context_proof_rejects_false_completeness_claim(self) -> None:
        result = _query_result(1)
        result["options"][1]["effect_indicators"][
            "complete_effect_set"
        ] = True
        result["current_event_window_context"]["options"][1][
            "effect_indicators"
        ]["complete_effect_set"] = True
        with HARNESS._installed_fixture_profile():
            proof = BASE._context_proof(
                result,
                event_id=EVENT_ID,
                snapshot_id=f"native:{NATIVE_REVISION}",
                public_revision=PUBLIC_REVISION,
                native_revision=NATIVE_REVISION,
                date_raw=DATE_RAW,
            )
        self.assertFalse(proof["ok"])
        self.assertFalse(proof["checks"]["materialized_option_shape"])

    def test_cross_stage_binds_same_nonempty_rows_and_distinct_pids(self) -> None:
        seed = {
            "ok": True,
            "event_instance_id": EVENT_ID,
            "seed_query": _query_result(1),
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
                "first_query": _query_result(2),
                "mutation_boundary": {"ok": True},
            },
        }
        transfer = {"ok": True}
        with HARNESS._installed_fixture_profile():
            proof = BASE._cross_stage_proof(seed, cold, transfer)
        self.assertTrue(proof["ok"], proof)
        self.assertTrue(proof["checks"]["same_materialized_options"])
        self.assertTrue(proof["checks"]["unclosed_semantics_stay_false"])

    def test_command_boundary_allows_only_query_save_and_query_query(self) -> None:
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
            ["select-event-option-3"], seed_stage=False
        )
        self.assertTrue(seed["ok"], seed)
        self.assertTrue(cold["ok"], cold)
        self.assertFalse(selected["ok"])
        self.assertEqual(
            selected["forbidden_event_actions_observed"],
            ["select-event-option-3"],
        )

    def test_wrapper_marks_only_the_exact_nonempty_matrix_green(self) -> None:
        base_payload = {
            "ok": True,
            "evidence_classification": "fixture-scoped-live-confirmed",
            "fixed_scenario": {},
            "policy": {},
            "readiness_gates": {"rendered_native_presentation_exact": True},
            "cross_stage_proof": {
                "checks": {"same_materialized_options": True}
            },
        }
        with mock.patch.object(BASE, "_run", return_value=(base_payload, 0)):
            payload, exit_code = HARNESS._run(SimpleNamespace())
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(
            payload["kind"],
            "ck3_current_event_nonempty_effect_indicators_live_acceptance",
        )
        self.assertTrue(
            payload["readiness_gates"][
                "empty_control_trait_stress_death_rows_exact"
            ]
        )
        self.assertFalse(payload["policy"]["visual_gui_icon_render_verified"])

if __name__ == "__main__":
    unittest.main()
