from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path, PureWindowsPath
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
    / "run_current_event_window_context_live_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_current_event_window_context_live_acceptance",
    HARNESS_PATH,
)
assert SPEC is not None and SPEC.loader is not None
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)


EVENT_ID = 0x2C00_0031
PUBLIC_REVISION = 17
NATIVE_REVISION = 91
DATE_RAW = 53_175_816
CALCULATED_EVENT_ID = -712_345
RUNTIME_STATS_ORDINAL = 37


def _no_effect_payload() -> dict[str, object]:
    return {
        "effect_indicators": {
            "status": "available",
            "coverage": HARNESS.EXPECTED_EFFECT_INDICATOR_COVERAGE,
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


def _snapshot() -> dict[str, object]:
    return {
        "snapshot_id": f"native:{NATIVE_REVISION}",
        "revision": PUBLIC_REVISION,
        "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "paused": True,
        "map_ready": True,
        "episode_run_id": "event-window-live-fixture",
        "backend_id": "native-headless",
        "played_character": {
            "character_id": HARNESS.PLAYER_CHARACTER_ID,
            "alive": True,
        },
        "active_event": {"instance_id": EVENT_ID, "option_count": 5},
    }


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
            **_no_effect_payload(),
        },
        {
            "rendered_index": 1,
            "native_option_index": 1,
            "shown": True,
            "enabled": False,
            "fallback": False,
            "cancel": False,
            "resolved_name": HARNESS.EXPECTED_OPTION_NAMES[1],
            "unavailable_reason": "Is controlled by the AI",
            **_no_effect_payload(),
        },
        {
            "rendered_index": 2,
            "native_option_index": 3,
            "shown": True,
            "enabled": True,
            "fallback": False,
            "cancel": True,
            "resolved_name": HARNESS.EXPECTED_OPTION_NAMES[2],
            "unavailable_reason": "",
            **_no_effect_payload(),
        },
    ]


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


def _query_result(sequence: int, frame: object | None = None) -> dict[str, object]:
    selected = copy.deepcopy(frame if frame is not None else _frame())
    selected_event_id = selected["current_event_instance_id"]
    result = {
        "step": HARNESS.QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
        "accepted": True,
        "status": "available",
        "query_sequence": sequence,
        "snapshot_revision": NATIVE_REVISION,
        "current_event_window_context": selected,
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
            "event_instance_id": selected_event_id,
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
        result[key] = copy.deepcopy(selected[key])
    return result


def _cross_stage_inputs() -> tuple[dict[str, object], dict[str, object]]:
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
    return seed, cold


class _FakeQueryService:
    def __init__(
        self, *, drift: bool = False, numeric_drift: bool = False
    ) -> None:
        self.calls: list[tuple[int, int]] = []
        self._queries = 0
        self._drift = drift
        self._numeric_drift = numeric_drift

    def snapshot(self) -> dict[str, object]:
        value = _snapshot()
        if self._drift and self._queries >= 1:
            value["native_revision"] = NATIVE_REVISION + 1
        return value

    def query_current_event_window_context_v1(
        self, event_id: int, *, expected_revision: int
    ) -> dict[str, object]:
        self.calls.append((event_id, expected_revision))
        self._queries += 1
        frame = _frame()
        if self._numeric_drift and self._queries >= 2:
            frame["calculated_event_id"] += 1
        return _query_result(9 + self._queries, frame)


def _make_projection_spec(root: Path, *, seed_stage: bool) -> SimpleNamespace:
    profile = root / "profile"
    production = profile / "mod-content" / "xar-production"
    production.mkdir(parents=True)
    (profile / "mod").mkdir()
    enabled = [HARNESS.OUTER_DESCRIPTOR_REF]
    if seed_stage:
        bridge = (
            profile
            / "mod-content"
            / HARNESS.owner_live.MOD_BRIDGE_TARGET_NAME
        )
        bridge.mkdir()
        outer = profile / "mod" / HARNESS.owner_live.MOD_BRIDGE_OUTER_NAME
        outer.write_text("fixture", encoding="utf-8")
        inbox = HARNESS.owner_live._seed_inbox_path(
            SimpleNamespace(profile_dir=profile)
        )
        inbox.parent.mkdir(parents=True)
        inbox.write_text("fixture", encoding="utf-8")
        enabled.append(f"mod/{HARNESS.owner_live.MOD_BRIDGE_OUTER_NAME}")
    (profile / "dlc_load.json").write_text(
        json.dumps({"enabled_mods": enabled, "disabled_dlcs": []}),
        encoding="utf-8",
    )
    return SimpleNamespace(profile_dir=profile, production_dir=production)


class CurrentEventWindowContextLiveAcceptanceTests(unittest.TestCase):
    def test_frozen_commit_binary_and_immutable_checkpoint(self) -> None:
        self.assertEqual(
            HARNESS.FROZEN_SOURCE_COMMIT,
            "cea30a067b1e112596d70532b98fa068b2102ebf",
        )
        self.assertEqual(
            HARNESS.FROZEN_BRIDGE_DLL_SHA256,
            "52398435F8AA5177D6D507BFAA38CD2578EB988F0629F1C5E13360CC91FB3BB0",
        )
        self.assertEqual(
            HARNESS.FROZEN_BRIDGE_INJECTOR_SHA256,
            "1618840EC108F688B3EBECC6D7F8963038BA64C8D4A3E10DDE2E29E3F443B4DF",
        )
        self.assertEqual(
            HARNESS.EXPECTED_SOURCE_SAVE_SHA256,
            "5BA2136911EAD0CAF1F7D2F3DE02EAFBD8039861C46F01F35F698B3B5CFFFC5F",
        )
        self.assertEqual(HARNESS.CONTINUE_SAVE_NAME, "autosave.ck3")

    def test_fixture_definition_is_exact_generic_and_nonreligious(self) -> None:
        proof = HARNESS._fixture_definition_contract()

        self.assertTrue(proof["ok"])
        self.assertEqual(proof["canonical_key"], HARNESS.EXPECTED_EVENT_KEY)
        self.assertEqual(
            proof["event_definition_sha256"], HARNESS.FIXTURE_EVENT_SHA256
        )
        self.assertEqual(
            proof["content_manifest"]["sha256"],
            HARNESS.FIXTURE_CONTENT_MANIFEST_SHA256,
        )
        self.assertEqual(len(proof["content_manifest"]["files"]), 10)
        for key in (
            "five_authored_options",
            "shown_disabled_option",
            "hidden_option",
            "one_cancel_option",
            "fallback_only_if_regular_empty",
            "no_event_gameplay_effects",
            "all_locales_have_exact_keys",
            "no_religion_semantics",
        ):
            self.assertTrue(proof["checks"][key], key)

    def test_default_root_reserves_longest_windows_fixture_path(self) -> None:
        root = Path(r"C:\Users\xenoa\AppData\Local\Temp") / (
            HARNESS._ROOT_PREFIX + "0" * 32
        )
        proof = HARNESS._generated_fixture_path_length_contract(root)

        self.assertEqual(HARNESS._ROOT_PREFIX, "xew-")
        self.assertEqual(HARNESS._CK3_PHYSFS_PATH_LIMIT, 250)
        self.assertTrue(proof["ok"])
        self.assertEqual(proof["maximum_generated_path_characters"], 243)
        self.assertEqual(len(proof["longest_paths"]), 1)
        self.assertEqual(
            proof["longest_paths"][0]["relative_path"],
            str(
                PureWindowsPath(HARNESS._COLD_STAGE_NAME)
                / "profile"
                / "mod-content"
                / HARNESS.FIXTURE_MOD_TARGET_NAME
                / "localization"
                / "simp_chinese"
                / "xar_event_window_context_live_fixture_l_simp_chinese.yml"
            ),
        )

        at_limit = root.with_name(root.name + "x" * 7)
        rejected = HARNESS._generated_fixture_path_length_contract(at_limit)
        self.assertFalse(rejected["ok"])
        self.assertEqual(
            rejected["maximum_generated_path_characters"],
            rejected["ck3_physfs_path_limit"],
        )

    def test_fixture_projection_keeps_identical_content_and_drops_mod_bridge(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            seed_spec = _make_projection_spec(root / "seed", seed_stage=True)
            HARNESS._install_fixture_definition(seed_spec)
            seed = HARNESS._fixture_projection_proof(
                seed_spec, seed_stage=True
            )

            cold_spec = _make_projection_spec(root / "cold", seed_stage=False)
            HARNESS._install_fixture_definition(cold_spec)
            cold = HARNESS._fixture_projection_proof(
                cold_spec, seed_stage=False
            )

        self.assertTrue(seed["ok"])
        self.assertTrue(cold["ok"])
        self.assertEqual(
            seed["content_manifest"]["sha256"],
            cold["content_manifest"]["sha256"],
        )
        self.assertIn(
            f"mod/{HARNESS.owner_live.MOD_BRIDGE_OUTER_NAME}",
            seed["dlc_load"]["enabled_mods"],
        )
        self.assertNotIn(
            f"mod/{HARNESS.owner_live.MOD_BRIDGE_OUTER_NAME}",
            cold["dlc_load"]["enabled_mods"],
        )

    def test_fixture_session_uses_existing_narrow_supervised_seam(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            spec = _make_projection_spec(Path(raw), seed_stage=False)
            HARNESS._install_fixture_definition(spec)
            config = SimpleNamespace(pipe_name=r"\\.\pipe\fixture")
            stop_event = threading.Event()
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
        self.assertEqual(report["fixture_stage"], "cold-double-query")
        self.assertTrue(report["exact_fixture_projection"]["ok"])

    def test_generation_effect_is_guarded_human_only_and_never_selects(self) -> None:
        effect = HARNESS._generate_effect()
        proof = HARNESS._effect_contract()

        self.assertTrue(proof["ok"])
        self.assertIn("is_ai = no", effect)
        self.assertIn(HARNESS.GENERATE_GUARD, effect)
        self.assertIn(
            f"trigger_event = {{ id = {HARNESS.EXPECTED_EVENT_KEY} }}",
            effect,
        )
        self.assertNotIn("select-event-option-", effect)
        self.assertTrue(proof["checks"]["no_religion_semantics"])

    def test_context_proof_covers_identity_presentation_and_unready_fields(self) -> None:
        proof = HARNESS._context_proof(
            _query_result(10),
            event_id=EVENT_ID,
            snapshot_id=f"native:{NATIVE_REVISION}",
            public_revision=PUBLIC_REVISION,
            native_revision=NATIVE_REVISION,
            date_raw=DATE_RAW,
        )

        self.assertTrue(proof["ok"])
        for key in (
            "full_instance_binding",
            "canonical_definition_key",
            "calculated_event_id_is_signed_int32",
            "runtime_stats_ordinal_is_signed_int32",
            "materialized_option_shape",
            "hidden_native_index_absent",
            "fallback_native_index_absent",
            "root_and_saved_scopes_unavailable",
            "readiness_truthful",
            "exact_provenance",
            "strict_mirrors",
        ):
            self.assertTrue(proof["checks"][key], key)

    def test_context_proof_rejects_each_actionability_drift(self) -> None:
        mutations = {
            "key": lambda frame: frame.__setitem__(
                "event_definition_key", "wrong.1"
            ),
            "calculated_bool": lambda frame: frame.__setitem__(
                "calculated_event_id", True
            ),
            "ordinal_overflow": lambda frame: frame.__setitem__(
                "runtime_stats_ordinal", 2**31
            ),
            "disabled_reason_missing": lambda frame: frame["options"][1].__setitem__(
                "unavailable_reason", ""
            ),
            "fallback_forged": lambda frame: frame["options"][0].__setitem__(
                "fallback", True
            ),
            "scope_forged": lambda frame: frame.__setitem__(
                "root_scope", {"character_id": 1}
            ),
            "semantic_ready_forged": lambda frame: frame["readiness"].__setitem__(
                "semantic_decision_ready", True
            ),
            "effect_preview_forged": lambda frame: frame["options"][0].__setitem__(
                "effect_preview", {"status": "available", "reason": None}
            ),
            "effect_indicator_row_forged": lambda frame: frame["options"][0][
                "effect_indicators"
            ].__setitem__("rows", [{"kind": "stress"}]),
            "effect_indicator_readiness_forged": lambda frame: frame[
                "readiness"
            ].__setitem__("effect_indicators_ready", False),
            "resource_delta_forged": lambda frame: frame["options"][0].__setitem__(
                "resource_deltas", {"status": "available"}
            ),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                frame = _frame()
                mutate(frame)
                proof = HARNESS._context_proof(
                    _query_result(10, frame),
                    event_id=EVENT_ID,
                    snapshot_id=f"native:{NATIVE_REVISION}",
                    public_revision=PUBLIC_REVISION,
                    native_revision=NATIVE_REVISION,
                    date_raw=DATE_RAW,
                )
                self.assertFalse(proof["ok"])

    def test_double_query_is_same_revision_full_id_and_read_only(self) -> None:
        service = _FakeQueryService()
        result = HARNESS._run_double_query_sequence(
            service,
            expected_event_id=EVENT_ID,
            expected_date_raw=DATE_RAW,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(
            service.calls,
            [(EVENT_ID, PUBLIC_REVISION), (EVENT_ID, PUBLIC_REVISION)],
        )
        self.assertEqual(
            result["commands"],
            [
                HARNESS.QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                HARNESS.QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
            ],
        )
        self.assertTrue(
            result["checks"]["adjacent_context_frames_strictly_equal"]
        )
        self.assertTrue(result["checks"]["only_query_sequence_changed"])

    def test_double_query_rejects_snapshot_drift(self) -> None:
        result = HARNESS._run_double_query_sequence(
            _FakeQueryService(drift=True),
            expected_event_id=EVENT_ID,
            expected_date_raw=DATE_RAW,
        )

        self.assertFalse(result["ok"])
        self.assertFalse(result["checks"]["between_same_paused_binding"])

    def test_double_query_rejects_process_local_numeric_drift(self) -> None:
        result = HARNESS._run_double_query_sequence(
            _FakeQueryService(numeric_drift=True),
            expected_event_id=EVENT_ID,
            expected_date_raw=DATE_RAW,
        )

        self.assertFalse(result["ok"])
        self.assertTrue(result["checks"]["first_context_valid"])
        self.assertTrue(result["checks"]["second_context_valid"])
        self.assertFalse(
            result["checks"]["adjacent_context_frames_strictly_equal"]
        )
        self.assertFalse(result["checks"]["only_query_sequence_changed"])

    def test_cross_stage_binds_full_identity_definition_and_fixture_bytes(self) -> None:
        seed, cold = _cross_stage_inputs()

        proof = HARNESS._cross_stage_proof(seed, cold, {"ok": True})
        self.assertTrue(proof["ok"])
        indicator_drift = copy.deepcopy(cold)
        indicator_drift["sequence"]["first_query"][
            "current_event_effect_indicators_ready"
        ] = False
        self.assertFalse(
            HARNESS._cross_stage_proof(
                seed, indicator_drift, {"ok": True}
            )["ok"]
        )

        cold["same_process_proof"]["bridge_pid"] = 101
        self.assertFalse(
            HARNESS._cross_stage_proof(seed, cold, {"ok": True})["ok"]
        )

    def test_cross_stage_accepts_process_local_numeric_changes(self) -> None:
        seed, cold = _cross_stage_inputs()
        process_local_frame = _frame()
        process_local_frame["calculated_event_id"] += 420_000
        process_local_frame["runtime_stats_ordinal"] += 892
        cold["sequence"]["first_query"] = _query_result(
            2, process_local_frame
        )
        process_local_proof = HARNESS._cross_stage_proof(
            seed, cold, {"ok": True}
        )

        self.assertTrue(process_local_proof["ok"])
        self.assertNotEqual(
            process_local_proof["seed_calculated_event_id"],
            process_local_proof["cold_calculated_event_id"],
        )
        self.assertNotEqual(
            process_local_proof["seed_runtime_stats_ordinal"],
            process_local_proof["cold_runtime_stats_ordinal"],
        )

    def test_cross_stage_rejects_invalid_process_local_numeric_metadata(self) -> None:
        for stage, field, value in (
            (stage, field, value)
            for stage in ("seed", "cold")
            for field in ("calculated_event_id", "runtime_stats_ordinal")
            for value in (True, None, 2**31)
        ):
            with self.subTest(stage=stage, field=field, value=value):
                seed, cold = _cross_stage_inputs()
                frame = _frame()
                frame[field] = value
                if stage == "seed":
                    seed["seed_query"] = _query_result(1, frame)
                else:
                    cold["sequence"]["first_query"] = _query_result(
                        2, frame
                    )
                self.assertFalse(
                    HARNESS._cross_stage_proof(
                        seed, cold, {"ok": True}
                    )["ok"]
                )

    def test_cross_stage_rejects_key_or_full_instance_drift(self) -> None:
        seed, cold = _cross_stage_inputs()
        key_frame = _frame()
        key_frame["event_definition_key"] = "wrong.1"
        cold["sequence"]["first_query"] = _query_result(2, key_frame)
        self.assertFalse(
            HARNESS._cross_stage_proof(seed, cold, {"ok": True})["ok"]
        )

        seed, cold = _cross_stage_inputs()
        instance_frame = _frame()
        instance_frame["current_event_instance_id"] = EVENT_ID + 1
        cold["sequence"]["current_event_instance_id"] = EVENT_ID + 1
        cold["sequence"]["first_query"] = _query_result(
            2, instance_frame
        )
        self.assertFalse(
            HARNESS._cross_stage_proof(seed, cold, {"ok": True})["ok"]
        )

    def test_preflight_failure_cannot_launch_or_prepare_a_stage(self) -> None:
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
                    HARNESS.FROZEN_BRIDGE_DLL_SHA256
                ),
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
            ), mock.patch.object(
                HARNESS.owner_live, "_prepare_stage"
            ) as prepare, mock.patch.object(
                HARNESS, "ck3_processes", return_value=[]
            ):
                payload, exit_code = HARNESS._run(args)

        self.assertEqual(exit_code, 1)
        self.assertFalse(payload["ok"])
        self.assertIn("isolated exact-commit", payload["error"])
        prepare.assert_not_called()
        self.assertIsNone(payload["seed_stage"])
        self.assertIsNone(payload["cold_stage"])

    def test_runner_source_never_selects_event_or_runs_auto_turn(self) -> None:
        source = HARNESS_PATH.read_text(encoding="utf-8")
        self.assertNotIn("service.resolve_active_event", source)
        self.assertNotIn("service.auto_turn(", source)
        self.assertNotIn("service.select_event", source)
        self.assertEqual(source.count("query_current_event_window_context_v1("), 3)


if __name__ == "__main__":
    unittest.main()
