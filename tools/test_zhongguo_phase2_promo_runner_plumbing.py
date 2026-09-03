"""CK3-free regression tests for phase-two promo runner plumbing."""

from __future__ import annotations

import copy
from contextlib import ExitStack, nullcontext
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time
import types
from types import SimpleNamespace
import unittest
from unittest import mock


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))


def _install_optional_desktop_import_stubs() -> None:
    attributes = {
        "pyautogui": (
            "FAILSAFE",
            "press",
            "hotkey",
            "moveTo",
            "click",
            "mouseDown",
            "mouseUp",
            "size",
        ),
        "numpy": (),
        "cv2": (),
        "win32api": ("GetKeyboardLayoutList",),
        "win32con": (),
        "win32gui": ("GetForegroundWindow", "GetWindowText"),
        "win32process": ("GetWindowThreadProcessId",),
    }
    for name, names in attributes.items():
        if importlib.util.find_spec(name) is None:
            module = types.ModuleType(name)
            for attribute in names:
                setattr(module, attribute, None)
            sys.modules[name] = module


_install_optional_desktop_import_stubs()

import run_zhongguo_acceptance as capture  # noqa: E402
import zhongguo_phase2_footage_intake as footage_intake  # noqa: E402
from zhongguo_phase2_promo_producer import (  # noqa: E402
    Phase2PromoCaptureContext,
    Phase2PromoProducerUnavailable,
    canonical_phase2_capture_contract,
    make_managed_phase2_promo_capture_producer,
    make_phase2_promo_capture_scaffold,
)
from zhongguo_phase2_capture_choreography import (  # noqa: E402
    PHASE2_CAPTURE_SCENARIOS,
    phase2_choreography_readiness,
)


_REAL_PROMO_RECORDER = capture.PromoRecorder


class _FakeDriver:
    instances: list["_FakeDriver"] = []

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        self.closed = False
        self.instances.append(self)

    def close(self) -> None:
        self.closed = True


class _FakeService:
    def __init__(self, driver: _FakeDriver) -> None:
        self.driver = driver

    def capabilities(self) -> dict[str, object]:
        return {
            "diagnostics": {
                "connected": True,
                "bridge_pid": 4321,
                "connection_generation": 1,
            }
        }


class _FakeRecorder:
    instances: list["_FakeRecorder"] = []

    def __init__(self, artifact_dir: Path, *, contract: object) -> None:
        self.artifact_dir = artifact_dir
        self.contract = contract
        self.process: object | None = object()
        self.stop_calls = 0
        self.instances.append(self)

    def stop(self) -> dict[str, object]:
        self.stop_calls += 1
        self.process = None
        evidence: dict[str, object] = {
            "clean_capture_complete": True,
            "missing_clean_spans": [],
        }
        if self.contract == capture.PHASE2_PROMO_CAPTURE_CONTRACT:
            evidence.update(
                {
                    "capture_mode": capture.PHASE2_PROMO_CAPTURE_MODE,
                    "capture_contract_version": (
                        capture.PHASE2_PROMO_CAPTURE_CONTRACT_VERSION
                    ),
                    "capture_contract": self.contract.to_mapping(),
                }
            )
        return evidence


class _FakeProcess:
    def __init__(self, pid: int) -> None:
        self.pid = pid

    def poll(self) -> None:
        return None


def _enter_common_run_cell_patches(
    stack: ExitStack, temporary_root: Path
) -> dict[str, object]:
    runtime_targets: dict[str, Path] = {}

    def bootstrap_userdir(
        userdir: Path,
        _runtime_source: Path,
        *,
        workshop_manifest: Path | None = None,
        include_acceptance_fixture: bool = True,
    ) -> dict[str, object]:
        del workshop_manifest
        logs = userdir / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        (logs / "debug.log").write_text("", encoding="utf-8")
        product = userdir / "mod-content" / "product"
        fixture = userdir / "mod-content" / "fixture"
        product.mkdir(parents=True, exist_ok=True)
        if include_acceptance_fixture:
            fixture.mkdir(parents=True, exist_ok=True)
            runtime_targets.update(product=product, fixture=fixture)
        else:
            runtime_targets.update(product=product)
        enabled_mods = [f"mod/{capture.PRODUCT_OUTER}"]
        if include_acceptance_fixture:
            enabled_mods.append("mod/fixture.mod")
        return {
            "targets": dict(runtime_targets),
            "tree_snapshots": {
                key: {} for key in runtime_targets
            },
            "tree_sha256": {
                key: value
                for key, value in (
                    ("product", "A" * 64),
                    ("fixture", "B" * 64),
                )
                if key in runtime_targets
            },
            "enabled_mods": enabled_mods,
            "manifest": {"fixture": "unit"},
        }

    def make_spec(state_dir: Path, game_dir: Path) -> SimpleNamespace:
        resolved = Path(state_dir).resolve()
        return SimpleNamespace(
            state_dir=resolved,
            profile_dir=resolved / "profile",
            game_exe=Path(game_dir) / "binaries" / "ck3.exe",
        )

    stack.enter_context(
        mock.patch.object(capture.acceptance, "configure_runtime_userdir")
    )
    stack.enter_context(
        mock.patch.object(
            capture, "bootstrap_userdir", side_effect=bootstrap_userdir
        )
    )
    stack.enter_context(mock.patch.object(capture, "make_spec", side_effect=make_spec))
    stack.enter_context(
        mock.patch.object(capture.isolated, "tree_snapshot", return_value={})
    )
    stack.enter_context(
        mock.patch.object(
            capture.isolated,
            "installed_game_version",
            return_value=capture.EXPECTED_GAME_VERSION,
        )
    )
    stack.enter_context(
        mock.patch.object(
            capture.isolated,
            "sha256_file",
            return_value=capture.EXPECTED_EXE_SHA256,
        )
    )
    stack.enter_context(
        mock.patch.object(capture, "NativeHeadlessGameplayDriver", _FakeDriver)
    )
    stack.enter_context(
        mock.patch.object(capture, "GameplayBridgeService", _FakeService)
    )
    stack.enter_context(mock.patch.object(capture, "PromoRecorder", _FakeRecorder))
    stack.enter_context(
        mock.patch.object(
            capture,
            "handle_phase2_optional_legal_consent",
            return_value={
                "schema_version": 1,
                "result": "GREEN",
                "state": "no_modal",
                "authorized_click_count": 0,
                "real_profile_modified": False,
            },
        )
    )
    stack.enter_context(
        mock.patch.object(capture, "project_diagnostics", return_value=([], []))
    )
    stack.enter_context(mock.patch.object(capture, "copy_logs"))
    stack.enter_context(
        mock.patch.object(
            capture,
            "verify_runtime_load_order",
            return_value=["product", "fixture"],
        )
    )
    return {"runtime_targets": runtime_targets, "temporary_root": temporary_root}


class Phase2PromoRunnerPlumbingTests(unittest.TestCase):
    def test_inline_loaded_seed_handoff_binds_owner_session_before_capture(self) -> None:
        snapshot = {
            "snapshot_id": "phase2-seed:10",
            "revision": 10,
            "native_revision": 110,
            "date_raw": 777,
            "paused": True,
            "map_ready": True,
            "played_character": {"character_id": 9001, "alive": True},
            "diagnostics": {
                "bridge_pid": 4321,
                "connection_generation": 4,
            },
        }
        manifest = {
            "status": "available",
            "loaded_feature_manifest_ready": True,
            "binding": {
                key: snapshot[key]
                for key in (
                    "snapshot_id",
                    "revision",
                    "native_revision",
                    "date_raw",
                )
            },
            "effective_feature_flags": {
                "status": "available",
                "items": [
                    {"key": "all_under_heaven", "enabled": True},
                    {"key": "merit_admin", "enabled": True},
                ],
            },
            "script_dlc_keys": {
                "status": "available",
                "keys": ["All Under Heaven"],
            },
        }
        calls: list[tuple[str, int]] = []

        class Service:
            def query_loaded_feature_manifest_v1(
                self, *, expected_revision: int
            ) -> dict[str, object]:
                calls.append(("manifest", expected_revision))
                return copy.deepcopy(manifest)

            def snapshot(self) -> dict[str, object]:
                calls.append(("snapshot", 10))
                return copy.deepcopy(snapshot)

        contract = {
            "status": "ready",
            "ready": True,
            "saved_state": {
                "date_raw": 777,
                "played_character_id": 9001,
                "played_character_alive": True,
                "paused_on_load": True,
                "map_ready": True,
            },
        }
        with tempfile.TemporaryDirectory() as temporary:
            artifacts = Path(temporary)
            context = SimpleNamespace(
                title_navigation_service=Service(),
                seed_contract=contract,
                native_session_binding={
                    "bridge_pid": 4321,
                    "connection_generation": 4,
                },
                tracked_ck3_pid=4321,
                artifacts=artifacts,
            )
            proof = capture._phase2_promo_seed_proof_probe(context, snapshot)
            handoff = json.loads(
                (
                    artifacts
                    / capture.loaded_seed_live.REPORT_NAME
                ).read_text(encoding="utf-8")
            )
        self.assertEqual(calls, [("manifest", 10), ("snapshot", 10)])
        self.assertEqual(proof["schema_version"], 2)
        self.assertEqual(proof["result"], "GREEN")
        self.assertEqual(len(proof["span_requirements"]), 8)
        self.assertTrue(handoff["same_session_continuation_authorized"])
        self.assertEqual(handoff["expected_connection_generation"], 4)

    def test_inline_loaded_seed_missing_manifest_is_typed_before_capture(self) -> None:
        snapshot = {
            "snapshot_id": "phase2-seed:10",
            "revision": 10,
            "native_revision": 110,
            "date_raw": 777,
            "paused": True,
            "map_ready": True,
            "played_character": {"character_id": 9001, "alive": True},
            "diagnostics": {
                "bridge_pid": 4321,
                "connection_generation": 4,
            },
        }

        class MissingManifestService:
            def query_loaded_feature_manifest_v1(
                self, *, expected_revision: int
            ) -> dict[str, object]:
                del expected_revision
                return {"status": "unavailable"}

            def snapshot(self) -> dict[str, object]:
                raise AssertionError("manifest RED must precede second snapshot")

        with tempfile.TemporaryDirectory() as temporary:
            context = SimpleNamespace(
                title_navigation_service=MissingManifestService(),
                seed_contract={"status": "ready", "ready": True},
                native_session_binding={
                    "bridge_pid": 4321,
                    "connection_generation": 4,
                },
                tracked_ck3_pid=4321,
                artifacts=Path(temporary),
            )
            with self.assertRaises(Phase2PromoProducerUnavailable) as raised:
                capture._phase2_promo_seed_proof_probe(context, snapshot)
        self.assertEqual(
            raised.exception.reason_code,
            "loaded_feature_manifest_unavailable",
        )

    def setUp(self) -> None:
        self.prior_producer = capture._PHASE2_PROMO_CAPTURE_PRODUCER
        self.prior_visual_primitives = dict(
            capture._PHASE2_PROMO_VISUAL_PRIMITIVES
        )
        _FakeDriver.instances.clear()
        _FakeRecorder.instances.clear()

    def tearDown(self) -> None:
        capture._PHASE2_PROMO_CAPTURE_PRODUCER = self.prior_producer
        capture._PHASE2_PROMO_VISUAL_PRIMITIVES.clear()
        capture._PHASE2_PROMO_VISUAL_PRIMITIVES.update(
            self.prior_visual_primitives
        )

    def test_built_in_producer_registers_composite_all_eight_driver(self) -> None:
        capture._PHASE2_PROMO_CAPTURE_PRODUCER = None
        capture._PHASE2_PROMO_VISUAL_PRIMITIVES.clear()
        producer = capture._ensure_phase2_promo_capture_producer()
        context = SimpleNamespace(title_navigation_service=object())
        driver = capture._make_default_phase2_promo_span_driver(context)
        self.assertEqual(
            set(driver.available_handlers()),
            {
                "capture_fact_quota_calibration",
                "capture_receipt_appeal_pip",
                "capture_manager_governance",
                "capture_promotion_compensation",
                "capture_hc_workforce",
                "capture_projects_metrics",
                "capture_incidents_operations",
                "capture_cross_cycle_endgame",
            },
        )
        self.assertIs(producer, capture._PHASE2_PROMO_CAPTURE_PRODUCER)

    def test_visual_primitive_registry_accepts_only_canonical_unique_keys(self) -> None:
        capture._PHASE2_PROMO_VISUAL_PRIMITIVES.clear()
        primitive = lambda *_args, **_kwargs: {}  # noqa: E731
        capture.register_phase2_promo_visual_primitive(
            "facts-quota-calibration", primitive
        )
        self.assertIs(
            capture._PHASE2_PROMO_VISUAL_PRIMITIVES[
                "facts-quota-calibration"
            ],
            primitive,
        )
        with self.assertRaises(ValueError):
            capture.register_phase2_promo_visual_primitive(
                "facts-quota-calibration", primitive
            )
        with self.assertRaises(ValueError):
            capture.register_phase2_promo_visual_primitive(
                "legacy-phase1-span", primitive
            )

    def test_loaded_seed_proof_covers_all_eight_span_requirements(self) -> None:
        snapshot = {
            "snapshot_id": "phase2-seed:10",
            "revision": 10,
            "native_revision": 110,
            "date_raw": 777,
            "paused": True,
            "map_ready": True,
            "played_character": {"character_id": 9001, "alive": True},
            "diagnostics": {"bridge_pid": 4321, "connection_generation": 4},
        }
        contract = {
            "status": "ready",
            "ready": True,
            "saved_state": {
                "date_raw": 777,
                "played_character_id": 9001,
                "played_character_alive": True,
                "paused_on_load": True,
                "map_ready": True,
            },
        }
        manifest = {
            "status": "available",
            "loaded_feature_manifest_ready": True,
            "binding": {
                "snapshot_id": "phase2-seed:10",
                "revision": 10,
                "native_revision": 110,
                "date_raw": 777,
            },
            "effective_feature_flags": {
                "status": "available",
                "items": [
                    {"key": "all_under_heaven", "enabled": True},
                    {"key": "merit_admin", "enabled": True},
                ],
            },
            "script_dlc_keys": {
                "status": "available",
                "keys": ["All Under Heaven"],
            },
        }
        with tempfile.TemporaryDirectory() as temporary:
            evidence = capture.prove_phase2_loaded_seed(
                snapshot,
                contract,
                Path(temporary),
                loaded_feature_manifest=manifest,
            )
        self.assertEqual(evidence["result"], "GREEN")
        self.assertEqual(evidence["schema_version"], 2)
        self.assertEqual(len(evidence["span_requirements"]), 8)
        self.assertTrue(evidence["checks"]["all_span_loaded_features_ready"])
        for row in evidence["span_requirements"]:
            with self.subTest(span=row["span_id"]):
                self.assertTrue(row["loaded_feature_seed_ready"])
                self.assertFalse(row["provider_ready_claimed"])
                self.assertEqual(
                    row["event_gui_provider_live_proof"],
                    "required_at_span_execution",
                )
                requirements = row["requirements"]
                self.assertEqual(
                    requirements["loaded_feature_flags"],
                    ["all_under_heaven", "merit_admin"],
                )
                self.assertEqual(
                    requirements["script_dlc_keys"], ["All Under Heaven"]
                )
                self.assertTrue(requirements["event_definition_keys"])
                self.assertTrue(requirements["gui_surfaces"])
                self.assertTrue(requirements["mcp_queries"])
                self.assertTrue(requirements["mcp_actions"])

        context = Phase2PromoCaptureContext(
            stream="",
            artifacts=Path("unused-loaded-seed-integration"),
            recorder=object(),
            title_navigation_service=object(),
            tracked_ck3_pid=4321,
            native_bridge=object(),
            preflight_bridge_identity={"identity": "unit"},
            contract=canonical_phase2_capture_contract(),
            seed_contract=contract,
            seed_install={"result": "GREEN"},
            native_session_binding={
                "bridge_pid": 4321,
                "connection_generation": 4,
            },
            loader_gate={
                "result": "GREEN",
                "native_readiness": {"result": "GREEN"},
                "phase2_capability_preflight": {"result": "GREEN"},
            },
        )
        driver = capture._make_default_phase2_promo_span_driver(context)
        readiness = phase2_choreography_readiness(
            context,
            {
                "ready": True,
                "paused_snapshot": snapshot,
                "seed_load_proof": evidence,
            },
            driver,
        )
        self.assertEqual(readiness["result"], "RED")
        self.assertEqual(readiness["reason_code"], "span_driver_preflight_red")
        self.assertEqual(
            readiness["span_driver_preflight"]["reason_code"],
            "source_checkpoint_preflight_red",
        )
        self.assertEqual(readiness["missing_handlers"], [])
        self.assertTrue(readiness["checks"]["all_span_handlers_available"])
        self.assertTrue(
            all(row["handler_available"] for row in readiness["span_readiness"])
        )
        self.assertTrue(
            all(
                row["provider_ready_claimed"] is False
                for row in evidence["span_requirements"]
            )
        )

    def test_loaded_seed_proof_is_red_when_real_feature_provider_is_missing(self) -> None:
        snapshot = {
            "snapshot_id": "phase2-seed:10",
            "revision": 10,
            "native_revision": 110,
            "date_raw": 777,
            "paused": True,
            "map_ready": True,
            "played_character": {"character_id": 9001, "alive": True},
            "diagnostics": {"bridge_pid": 4321, "connection_generation": 4},
        }
        contract = {
            "status": "ready",
            "ready": True,
            "saved_state": {
                "date_raw": 777,
                "played_character_id": 9001,
                "played_character_alive": True,
                "paused_on_load": True,
                "map_ready": True,
            },
        }
        manifest = {
            "status": "available",
            "loaded_feature_manifest_ready": True,
            "binding": {
                "snapshot_id": "phase2-seed:10",
                "revision": 10,
                "native_revision": 110,
                "date_raw": 777,
            },
            "effective_feature_flags": {
                "status": "available",
                "items": [
                    {"key": "all_under_heaven", "enabled": True},
                    {"key": "merit_admin", "enabled": False},
                ],
            },
            "script_dlc_keys": {
                "status": "available",
                "keys": ["All Under Heaven"],
            },
        }
        with tempfile.TemporaryDirectory() as temporary:
            artifacts = Path(temporary)
            with self.assertRaises(capture.acceptance.RunnerError) as raised:
                capture.prove_phase2_loaded_seed(
                    snapshot,
                    contract,
                    artifacts,
                    loaded_feature_manifest=manifest,
                )
            persisted = json.loads(
                (artifacts / "04_phase2_seed_loaded.json").read_text(
                    encoding="utf-8"
                )
            )
        self.assertIn("all_span_loaded_features_ready", str(raised.exception))
        self.assertEqual(persisted["result"], "RED")
        self.assertTrue(
            all(
                row["observed_loaded_feature_flags"]["merit_admin"] is False
                for row in persisted["span_requirements"]
            )
        )

    def test_phase2_promo_preflight_keeps_missing_seed_typed_red(self) -> None:
        capture.register_phase2_promo_capture_producer(
            lambda *_args, **_kwargs: {}  # pragma: no cover - never invoked
        )
        bridge = SimpleNamespace(pipe_name=r"\\.\pipe\phase2-promo-unit")
        with (
            mock.patch.object(
                capture, "resolve_native_bridge_config", return_value=bridge
            ),
            mock.patch.object(
                capture,
                "preflight",
                return_value={"native_bridge_runtime": {"unit": True}},
            ) as preflight,
            mock.patch.object(
                capture,
                "load_phase2_seed_contract",
                return_value={
                    "ready": False,
                    "blocker": "no ready canonical paused seed",
                },
            ),
            mock.patch.object(capture, "run_cell") as forbidden_run_cell,
            mock.patch.object(capture, "install_phase2_seed") as forbidden_install,
            mock.patch.object(
                capture, "start_phase2_native_session_supervisor"
            ) as forbidden_supervisor,
        ):
            with self.assertRaises(capture.acceptance.RunnerError) as raised:
                capture.main(
                    preflight_only=True,
                    phase2_promo_capture=True,
                )
        self.assertIn("phase-two seed preflight RED", str(raised.exception))
        self.assertIn("no ready canonical paused seed", str(raised.exception))
        self.assertTrue(preflight.call_args.kwargs["require_visual_tools"])
        forbidden_run_cell.assert_not_called()
        forbidden_install.assert_not_called()
        forbidden_supervisor.assert_not_called()

    def test_phase2_promo_reuses_seed_supervisor_loader_and_context(self) -> None:
        seen: dict[str, object] = {}
        lifecycle: list[str] = []

        def runtime_probe(context: object) -> dict[str, object]:
            lifecycle.append("loaded-seed")
            seen["context"] = context
            return {"ready": True, "source": "managed-phase2-unit"}

        def choreography(
            context: object, runtime: dict[str, object]
        ) -> dict[str, object]:
            lifecycle.append("footage")
            self.assertIs(context, seen["context"])
            self.assertEqual(runtime["source"], "managed-phase2-unit")
            self.assertNotIn("cleanup", lifecycle)
            self.assertFalse(
                context.title_navigation_service.driver.closed  # type: ignore[union-attr]
            )
            return {
                "result": "GREEN",
                "capture_mode": capture.PHASE2_PROMO_CAPTURE_MODE,
                "capture_contract_version": (
                    capture.PHASE2_PROMO_CAPTURE_CONTRACT_VERSION
                ),
                "capture_contract": (
                    capture.PHASE2_PROMO_CAPTURE_CONTRACT.to_mapping()
                ),
            }

        capture.register_phase2_promo_capture_producer(
            make_phase2_promo_capture_scaffold(
                runtime_probe=runtime_probe,
                choreography=choreography,
            )
        )
        ready_contract = {
            "status": "ready",
            "ready": True,
            "seed_identity": "canonical-unit-seed",
        }
        seed_install = {
            "result": "GREEN",
            "contract": ready_contract,
            "targets": {"continue": "autosave.ck3"},
        }
        binding = {
            "bridge_pid": 4321,
            "connection_generation": 1,
        }
        loader_gate = {
            "result": "GREEN",
            "mode": "phase2_promo_capture",
            "native_readiness": {"result": "GREEN"},
            "phase2_capability_preflight": {"result": "GREEN"},
            "loader_error_log_scan": {"result": "GREEN"},
            "runtime_mount_inventory": ["product", "fixture"],
        }
        def install_seed(*_args: object, **_kwargs: object) -> dict[str, object]:
            lifecycle.append("seed")
            return copy.deepcopy(seed_install)

        def start_supervisor(*_args: object, **_kwargs: object) -> dict[str, object]:
            lifecycle.append("supervisor")
            return {"kind": "fake-supervisor"}

        def wait_binding(*_args: object, **_kwargs: object) -> dict[str, object]:
            lifecycle.append("binding")
            return copy.deepcopy(binding)

        def run_gate(*_args: object, **kwargs: object) -> dict[str, object]:
            lifecycle.append("loader")
            self.assertTrue(kwargs["phase2_live_batch"])
            self.assertTrue(kwargs["phase2_promo_capture"])
            self.assertTrue(kwargs["managed_restore_supervisor"])
            return copy.deepcopy(loader_gate)

        def stop_supervisor(
            *_args: object, **kwargs: object
        ) -> dict[str, object]:
            lifecycle.append("cleanup")
            self.assertEqual(kwargs["initial_pid"], 4321)
            self.assertEqual(kwargs["initial_generation"], 1)
            return {
                "pid_lineage": [4321],
                "connection_generation_lineage": [1],
                "session_report": {"restart_count": 0},
            }

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state_dir = root / "state"
            userdir = state_dir / "profile"
            bridge = SimpleNamespace(pipe_name=r"\\.\pipe\phase2-promo-unit")
            with ExitStack() as stack:
                _enter_common_run_cell_patches(stack, root)
                stack.enter_context(
                    mock.patch.object(
                        capture,
                        "handle_phase2_optional_legal_consent",
                        side_effect=lambda *_args, **_kwargs: (
                            lifecycle.append("legal-consent")
                            or {
                                "schema_version": 1,
                                "result": "GREEN",
                                "state": "no_modal",
                                "authorized_click_count": 0,
                                "real_profile_modified": False,
                            }
                        ),
                    )
                )
                install = stack.enter_context(
                    mock.patch.object(
                        capture, "install_phase2_seed", side_effect=install_seed
                    )
                )
                start = stack.enter_context(
                    mock.patch.object(
                        capture,
                        "start_phase2_native_session_supervisor",
                        side_effect=start_supervisor,
                    )
                )
                stack.enter_context(
                    mock.patch.object(
                        capture,
                        "wait_for_phase2_native_session_binding",
                        side_effect=wait_binding,
                    )
                )
                gate = stack.enter_context(
                    mock.patch.object(
                        capture, "run_loader_gate", side_effect=run_gate
                    )
                )
                stop = stack.enter_context(
                    mock.patch.object(
                        capture,
                        "stop_phase2_native_session_supervisor",
                        side_effect=stop_supervisor,
                    )
                )
                forbidden_launch = stack.enter_context(
                    mock.patch.object(capture, "launch_native_ck3")
                )
                forbidden_liveness = stack.enter_context(
                    mock.patch.object(
                        capture, "phase2_native_session_liveness_gate"
                    )
                )
                forbidden_legacy = stack.enter_context(
                    mock.patch.object(capture, "run_scenario")
                )
                report = capture.run_cell(
                    root / "artifacts",
                    userdir,
                    True,
                    state_dir=state_dir,
                    native_bridge=bridge,
                    phase2_promo_capture=True,
                    runtime_source=root / "runtime",
                    runtime_identity={
                        "native_bridge_runtime": {"identity": "preflight-unit"}
                    },
                    phase2_seed_contract_path=root / "generated-seed.json",
                )

        self.assertEqual(
            lifecycle,
            [
                "seed",
                "supervisor",
                "binding",
                "legal-consent",
                "loader",
                "loaded-seed",
                "footage",
                "cleanup",
            ],
        )
        install.assert_called_once()
        self.assertEqual(
            install.call_args.kwargs["contract_path"],
            (root / "generated-seed.json").resolve(),
        )
        start.assert_called_once()
        gate.assert_called_once()
        stop.assert_called_once()
        forbidden_launch.assert_not_called()
        forbidden_liveness.assert_not_called()
        forbidden_legacy.assert_not_called()
        context = seen["context"]
        self.assertEqual(context.seed_contract, ready_contract)  # type: ignore[union-attr]
        self.assertEqual(context.seed_install, seed_install)  # type: ignore[union-attr]
        self.assertEqual(context.native_session_binding, binding)  # type: ignore[union-attr]
        self.assertEqual(context.loader_gate, loader_gate)  # type: ignore[union-attr]
        self.assertEqual(context.tracked_ck3_pid, 4321)  # type: ignore[union-attr]
        self.assertTrue(context.title_navigation_service.driver.closed)  # type: ignore[union-attr]
        self.assertEqual(report["result"], "GREEN")
        self.assertTrue(report["loader_gate_executed"])
        self.assertTrue(report["gameplay_green_claimed"])
        self.assertEqual(report["phase2_seed_install"], seed_install)
        self.assertIsNone(report["native_session_liveness"])
        self.assertEqual(
            report["native_session_liveness_scope"],
            "not_applicable_phase2_promo_capture",
        )
        self.assertEqual(
            report["loader_gate_evidence"]["mode"], "phase2_promo_capture"
        )

    def test_phase2_promo_report_preserves_typed_producer_red(self) -> None:
        """A producer RED remains structured without opening a real runtime."""

        producer = make_phase2_promo_capture_scaffold(
            runtime_probe=lambda _context: {
                "ready": False,
                "blocker": "canonical_seed_not_ready",
            },
            error_factory=capture.acceptance.RunnerError,
        )
        capture.register_phase2_promo_capture_producer(producer)
        seed_contract = {
            "status": "ready",
            "ready": True,
            "seed_identity": "canonical-unit-seed",
        }
        seed_install = {
            "result": "GREEN",
            "contract": seed_contract,
            "targets": {"continue": "autosave.ck3"},
        }
        loader_gate = {
            "result": "GREEN",
            "mode": "phase2_promo_capture",
            "native_readiness": {"result": "GREEN"},
            "phase2_capability_preflight": {"result": "GREEN"},
            "loader_error_log_scan": {"result": "GREEN"},
            "runtime_mount_inventory": ["product", "fixture"],
        }

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state_dir = root / "state"
            userdir = state_dir / "profile"
            bridge = SimpleNamespace(pipe_name=r"\\.\pipe\phase2-promo-red")
            with ExitStack() as stack:
                _enter_common_run_cell_patches(stack, root)
                install = stack.enter_context(
                    mock.patch.object(
                        capture,
                        "install_phase2_seed",
                        return_value=copy.deepcopy(seed_install),
                    )
                )
                stack.enter_context(
                    mock.patch.object(
                        capture,
                        "start_phase2_native_session_supervisor",
                        return_value={"kind": "fake-supervisor"},
                    )
                )
                stack.enter_context(
                    mock.patch.object(
                        capture,
                        "wait_for_phase2_native_session_binding",
                        return_value={
                            "bridge_pid": 4321,
                            "connection_generation": 1,
                        },
                    )
                )
                stack.enter_context(
                    mock.patch.object(
                        capture,
                        "run_loader_gate",
                        return_value=copy.deepcopy(loader_gate),
                    )
                )
                stack.enter_context(
                    mock.patch.object(
                        capture,
                        "stop_phase2_native_session_supervisor",
                        return_value={
                            "pid_lineage": [4321],
                            "connection_generation_lineage": [1],
                            "session_report": {"restart_count": 0},
                        },
                    )
                )
                forbidden_launch = stack.enter_context(
                    mock.patch.object(capture, "launch_native_ck3")
                )
                forbidden_ffmpeg = stack.enter_context(
                    mock.patch.object(capture, "subprocess")
                )
                report = capture.run_cell(
                    root / "artifacts",
                    userdir,
                    True,
                    state_dir=state_dir,
                    native_bridge=bridge,
                    phase2_promo_capture=True,
                    runtime_source=root / "runtime",
                    runtime_identity={
                        "native_bridge_runtime": {"identity": "red-unit"}
                    },
                )
                persisted = json.loads(
                    (root / "artifacts" / "report.json").read_text(
                        encoding="utf-8"
                    )
                )

        install.assert_called_once()
        forbidden_launch.assert_not_called()
        forbidden_ffmpeg.Popen.assert_not_called()
        self.assertEqual(report["result"], "RED")
        typed_error = report["phase2_promo_producer_error"]
        self.assertEqual(
            typed_error,
            {
                "result": "RED",
                "reason_code": "runtime_unavailable",
                "evidence": {
                    "runtime": {
                        "ready": False,
                        "blocker": "canonical_seed_not_ready",
                    },
                    "result": "RED",
                    "reason_code": "runtime_unavailable",
                },
            },
        )
        self.assertIn("runtime_unavailable", report["error_reason"])
        self.assertFalse(report["gameplay_green_claimed"])
        self.assertEqual(
            persisted["phase2_promo_producer_error"], typed_error
        )

    def test_legacy_promo_keeps_suspended_launch_without_phase2_plumbing(self) -> None:
        process = _FakeProcess(2468)
        session = SimpleNamespace(process=process, watchdog_pid=2469)
        bridge = SimpleNamespace(pipe_name=r"\\.\pipe\legacy-promo-unit")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state_dir = root / "state"
            userdir = state_dir / "profile"
            with ExitStack() as stack:
                _enter_common_run_cell_patches(stack, root)
                stack.enter_context(
                    mock.patch.object(
                        capture,
                        "exclusive_launch_lock",
                        side_effect=lambda *_args, **_kwargs: nullcontext(),
                    )
                )
                stack.enter_context(
                    mock.patch.object(
                        capture,
                        "exclusive_state_lock",
                        side_effect=lambda *_args, **_kwargs: nullcontext(),
                    )
                )
                launch = stack.enter_context(
                    mock.patch.object(
                        capture, "launch_native_ck3", return_value=session
                    )
                )
                stop = stack.enter_context(
                    mock.patch.object(
                        capture,
                        "stop_tracked",
                        return_value={
                            "cleanup_proven": True,
                            "contract_errors": [],
                        },
                    )
                )
                stack.enter_context(
                    mock.patch.object(capture.acceptance, "wait_for_ocr_text")
                )
                stack.enter_context(
                    mock.patch.object(
                        capture.isolated, "dismiss_external_main_menu_popup"
                    )
                )
                stack.enter_context(
                    mock.patch.object(capture.acceptance, "navigate_lobby")
                )
                stack.enter_context(
                    mock.patch.object(capture.isolated, "wait_for_gameplay_hud")
                )
                stack.enter_context(
                    mock.patch.object(capture.acceptance, "ensure_game_paused")
                )
                stack.enter_context(
                    mock.patch.object(
                        capture,
                        "force_ck3_english_keyboard_layout",
                        return_value={"result": "GREEN"},
                    )
                )
                stack.enter_context(
                    mock.patch.object(capture.MarkerStream, "validate")
                )
                stack.enter_context(
                    mock.patch.object(
                        capture.acceptance.pyautogui,
                        "size",
                        return_value=SimpleNamespace(width=2560, height=1440),
                    )
                )
                legacy_scenario = stack.enter_context(
                    mock.patch.object(
                        capture,
                        "run_scenario",
                        return_value={"result": "GREEN", "legacy": True},
                    )
                )
                phase2_calls = [
                    stack.enter_context(mock.patch.object(capture, name))
                    for name in (
                        "install_phase2_seed",
                        "start_phase2_native_session_supervisor",
                        "wait_for_phase2_native_session_binding",
                        "run_loader_gate",
                        "run_phase2_promo_capture_scenario",
                        "phase2_native_session_liveness_gate",
                    )
                ]
                report = capture.run_cell(
                    root / "artifacts",
                    userdir,
                    True,
                    state_dir=state_dir,
                    native_bridge=bridge,
                    promo_capture=True,
                    runtime_source=root / "runtime",
                    runtime_identity={
                        "native_bridge_runtime": {"identity": "legacy-unit"}
                    },
                )

        launch.assert_called_once()
        stop.assert_called_once()
        legacy_scenario.assert_called_once()
        for phase2_call in phase2_calls:
            phase2_call.assert_not_called()
        self.assertEqual(report["result"], "GREEN")
        self.assertEqual(report["native_launch_sequence"], "suspended_inject_resume")
        self.assertFalse(report["loader_gate_executed"])
        self.assertIsNone(report["phase2_seed_install"])
        self.assertIsNone(report["native_session_liveness"])
        self.assertIsNone(report["native_session_liveness_scope"])

    def test_loader_gate_labels_promo_and_runs_managed_phase2_checks(self) -> None:
        calls: list[str] = []
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifacts = root / "artifacts"
            userdir = root / "profile"
            artifacts.mkdir()
            userdir.mkdir()

            def record(name: str, result: object):
                def invoke(*_args: object, **_kwargs: object) -> object:
                    calls.append(name)
                    return copy.deepcopy(result)

                return invoke

            with (
                mock.patch.object(
                    capture,
                    "wait_for_phase2_seed_loader_stage",
                    side_effect=record("loader", {"result": "GREEN"}),
                ),
                mock.patch.object(
                    capture,
                    "native_loader_smoke_readiness",
                    side_effect=record("readiness", {"result": "GREEN"}),
                ),
                mock.patch.object(
                    capture,
                    "phase2_runtime_capability_preflight",
                    side_effect=record("capabilities", {"result": "GREEN"}),
                ) as capability,
                mock.patch.object(
                    capture,
                    "scan_loader_error_log",
                    side_effect=record("errors", {"result": "GREEN"}),
                ),
                mock.patch.object(
                    capture,
                    "verify_runtime_load_order",
                    side_effect=record("mounts", ["product", "fixture"]),
                ),
            ):
                evidence = capture.run_loader_gate(
                    SimpleNamespace(),
                    artifacts,
                    userdir,
                    {},
                    tracked_ck3_pid=4321,
                    phase2_live_batch=False,
                    managed_restore_supervisor=True,
                    phase2_promo_capture=True,
                )
        self.assertEqual(
            calls,
            ["loader", "readiness", "capabilities", "errors", "mounts"],
        )
        self.assertEqual(evidence["mode"], "phase2_promo_capture")
        self.assertTrue(evidence["same_pid_gameplay_continuation_authorized"])
        self.assertTrue(
            capability.call_args.kwargs["managed_restore_supervisor"]
        )

    def test_phase2_legal_gate_no_modal_is_green_without_click(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            userdir = root / "native-state" / "profile"
            artifacts = root / "artifacts"
            userdir.mkdir(parents=True)
            artifacts.mkdir()
            with (
                mock.patch.object(capture.acceptance, "focus_ck3"),
                mock.patch.object(
                    capture.acceptance.ImageGrab,
                    "grab",
                    return_value=object(),
                ),
                mock.patch.object(
                    capture.acceptance,
                    "ocr_results",
                    return_value=[("Crusader Kings III", 1.0, (10, 10), None)],
                ),
                mock.patch.object(
                    capture.acceptance, "deliberate_click"
                ) as forbidden_click,
            ):
                evidence = capture.handle_phase2_optional_legal_consent(
                    userdir, artifacts
                )
            persisted = json.loads(
                (artifacts / "01_phase2_legal_consent.json").read_text(
                    encoding="utf-8"
                )
            )
        self.assertEqual(evidence["result"], "GREEN")
        self.assertEqual(evidence["state"], "no_modal")
        self.assertEqual(evidence["authorized_click_count"], 0)
        self.assertEqual(persisted, evidence)
        forbidden_click.assert_not_called()

    def test_phase2_legal_gate_denies_purchase_before_click(self) -> None:
        class FakeImage:
            def save(self, path: Path) -> None:
                Path(path).write_bytes(b"phase2-legal-preclassification")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            userdir = root / "native-state" / "profile"
            artifacts = root / "artifacts"
            userdir.mkdir(parents=True)
            artifacts.mkdir()
            with (
                mock.patch.object(capture.acceptance, "focus_ck3"),
                mock.patch.object(
                    capture.acceptance.ImageGrab,
                    "grab",
                    return_value=FakeImage(),
                ),
                mock.patch.object(
                    capture.acceptance,
                    "ocr_results",
                    return_value=[
                        ("Steam DLC", 1.0, (10, 10), None),
                        ("Buy Now", 1.0, (10, 30), None),
                    ],
                ),
                mock.patch.object(
                    capture.acceptance, "deliberate_click"
                ) as forbidden_click,
            ):
                with self.assertRaises(
                    capture.Phase2LegalConsentBlocked
                ) as raised:
                    capture.handle_phase2_optional_legal_consent(
                        userdir, artifacts
                    )
            persisted = json.loads(
                (artifacts / "01_phase2_legal_consent.json").read_text(
                    encoding="utf-8"
                )
            )
            attempt = persisted["classification_attempts"][0]
            screenshot = Path(attempt["preclassification_screenshot"])
            screenshot_exists = screenshot.is_file()
            screenshot_hash_matches = (
                attempt["preclassification_screenshot_sha256"]
                == capture.legal_consent.sha256(screenshot)
            )
        self.assertEqual(raised.exception.reason_code, "PurchaseActionNotAuthorized")
        self.assertEqual(persisted["result"], "RED")
        self.assertEqual(persisted["state"], "typed_stop")
        self.assertEqual(
            persisted["classification_diagnostics"]["classification_state"],
            "external_purchase_forbidden",
        )
        self.assertEqual(len(persisted["classification_attempts"]), 1)
        self.assertEqual(
            attempt["raw_ocr_rows"],
            ["Steam DLC", "Buy Now"],
        )
        self.assertEqual(
            attempt["normalized_rows"],
            ["Steam DLC", "Buy Now"],
        )
        self.assertEqual(
            attempt["classification_state"],
            "external_purchase_forbidden",
        )
        self.assertEqual(attempt["purchase_action_labels"], ["Buy Now"])
        self.assertIn("steam", attempt["external_commerce_terms"])
        self.assertEqual(
            attempt["authorization_version"],
            capture.legal_consent.LEGAL_AUTHORIZATION_VERSION,
        )
        self.assertTrue(screenshot_exists)
        self.assertTrue(screenshot_hash_matches)
        forbidden_click.assert_not_called()

    def test_phase2_legal_gate_authorizes_broad_protocol_before_control_lookup(self) -> None:
        class FakeImage:
            def save(self, path: Path) -> None:
                Path(path).write_bytes(b"phase2-ambiguous-legal-modal")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            userdir = root / "native-state" / "profile"
            artifacts = root / "artifacts"
            userdir.mkdir(parents=True)
            artifacts.mkdir()
            with (
                mock.patch.object(capture.acceptance, "focus_ck3"),
                mock.patch.object(
                    capture.acceptance.ImageGrab,
                    "grab",
                    return_value=FakeImage(),
                ),
                mock.patch.object(
                    capture.acceptance,
                    "ocr_results",
                    return_value=[
                        ("Paradox   Interactive", 1.0, (10, 10), None),
                        ("Telemetry", 1.0, (10, 30), None),
                    ],
                ),
                mock.patch.object(
                    capture.acceptance, "deliberate_click"
                ) as forbidden_click,
                mock.patch.object(
                    capture.acceptance,
                    "find_ocr_text",
                    return_value=None,
                ),
            ):
                with self.assertRaises(
                    capture.Phase2LegalConsentBlocked
                ) as raised:
                    capture.handle_phase2_optional_legal_consent(
                        userdir, artifacts
                    )
            persisted = json.loads(
                (artifacts / "01_phase2_legal_consent.json").read_text(
                    encoding="utf-8"
                )
            )
            attempt = persisted["classification_attempts"][0]
            screenshot = Path(attempt["preclassification_screenshot"])
            self.assertTrue(screenshot.is_file())
        self.assertEqual(
            raised.exception.reason_code,
            "LegalConsentControlNotFound",
        )
        self.assertEqual(attempt["classification_state"], "authorized_agreement")
        self.assertEqual(
            attempt["normalized_rows"],
            ["Paradox Interactive", "Telemetry"],
        )
        self.assertEqual(attempt["protocol_category_terms"], ["telemetry"])
        self.assertEqual(
            persisted["classification_diagnostics"],
            {
                key: attempt[key]
                for key in (
                    "normalized_rows",
                    "normalized_text",
                    "ck3_context_confirmed",
                    "origin_terms",
                    "game_context_recognized",
                    "allowed_terms",
                    "denied_terms",
                    "purchase_terms",
                    "action_labels",
                    "purchase_action_labels",
                    "commerce_confirm_labels",
                    "dismiss_only_labels",
                    "external_commerce_terms",
                    "real_currency_matches",
                    "internal_resource_terms",
                    "commerce_mention_terms",
                    "external_commerce_context",
                    "internal_resource_context",
                    "actionable_commerce",
                    "commerce_context_conflict",
                    "legal_document_hints",
                    "protocol_category_terms",
                    "notification_hints",
                    "safe_action_terms",
                    "classification_state",
                    "evidence_required",
                    "authorization_text",
                    "authorization_version",
                )
            },
        )
        forbidden_click.assert_not_called()

    def test_production_sidecars_feed_strict_footage_intake_unchanged(self) -> None:
        """Exercise the planned producer bundle through the real intake contract.

        The fixture replaces only live CK3, desktop sampling and FFmpeg.  The
        managed producer, eight-span choreography, PromoRecorder clean-hold /
        timeline implementation, run_cell report, main matrix and evidence
        index are the production implementations.
        """

        tracked_pid = 4321
        connection_generation = 1
        snapshot = {
            "snapshot_id": "phase2-cross-contract:100",
            "revision": 100,
            "native_revision": 200,
            "date_raw": 777,
            "paused": True,
            "map_ready": True,
            "played_character": {"character_id": 9001, "alive": True},
            "diagnostics": {
                "bridge_pid": tracked_pid,
                "connection_generation": connection_generation,
            },
        }
        seed_contract = {
            "status": "ready",
            "ready": True,
            "saved_state": {
                "date_raw": 777,
                "played_character_id": 9001,
                "played_character_alive": True,
                "paused_on_load": True,
                "map_ready": True,
            },
        }
        seed_install = {
            "result": "GREEN",
            "contract": copy.deepcopy(seed_contract),
            "targets": {"continue": "canonical-phase2.ck3"},
        }
        manifest = {
            "status": "available",
            "loaded_feature_manifest_ready": True,
            "binding": {
                "snapshot_id": snapshot["snapshot_id"],
                "revision": snapshot["revision"],
                "native_revision": snapshot["native_revision"],
                "date_raw": snapshot["date_raw"],
            },
            "effective_feature_flags": {
                "status": "available",
                "items": [
                    {"key": "all_under_heaven", "enabled": True},
                    {"key": "merit_admin", "enabled": True},
                ],
            },
            "script_dlc_keys": {
                "status": "available",
                "keys": ["All Under Heaven"],
            },
        }
        loader_gate = {
            "result": "GREEN",
            "mode": "phase2_promo_capture",
            "same_pid_gameplay_continuation_authorized": True,
            "native_readiness": {"result": "GREEN"},
            "phase2_capability_preflight": {"result": "GREEN"},
            "loader_error_log_scan": {"result": "GREEN"},
            "runtime_mount_inventory": ["product", "fixture"],
        }
        runtime_revision = {"revision": 100, "native_revision": 200}

        class ContractDriver:
            def __init__(self) -> None:
                self.calls = 0

            def available_handlers(self) -> tuple[str, ...]:
                return tuple(item.handler for item in PHASE2_CAPTURE_SCENARIOS)

            def run_span(self, scenario, _context, _runtime):
                self.calls += 1
                runtime_revision["revision"] += 1
                runtime_revision["native_revision"] += 1
                return {
                    "result": "GREEN",
                    "surface_visible": True,
                    "postcondition_green": True,
                    "provider_observed": True,
                    "handler": scenario.handler,
                    "binding": {
                        "snapshot_id": (
                            f"phase2-cross-contract:{runtime_revision['revision']}"
                        ),
                        "revision": runtime_revision["revision"],
                        "native_revision": runtime_revision["native_revision"],
                        "date_raw": 777 + self.calls,
                        "bridge_pid": tracked_pid,
                        "connection_generation": connection_generation,
                    },
                }

        class FixtureStdin:
            def write(self, _value: bytes) -> None:
                return None

            def flush(self) -> None:
                return None

        class FixtureProcess:
            stdin = FixtureStdin()

            def poll(self) -> None:
                return None

            def wait(self, *, timeout: int) -> int:
                del timeout
                return 0

            def terminate(self) -> None:  # pragma: no cover - success path
                raise AssertionError("fixture recorder must not require termination")

        class NoLaunchPromoRecorder(_REAL_PROMO_RECORDER):
            def start(self) -> None:
                self.raw_dir.mkdir(parents=True)
                self.raw_path.write_bytes(b"no-media-static-raw-capture-fixture")
                self.log_path.write_text(
                    "FFmpeg intentionally not invoked by static fixture\n",
                    encoding="utf-8",
                )
                self.process = FixtureProcess()  # type: ignore[assignment]
                self.started_monotonic = time.monotonic()
                self.started_at_utc = "2026-09-02T00:00:00+00:00"
                self.mark("recording_started_after_gameplay_hud")

            def hold(self, seconds: float = 2.5) -> None:
                # Preserve strictly increasing production marks without a
                # blocking sleep or creating any media.
                assert self.started_monotonic is not None
                self.started_monotonic -= seconds

        def file_record(path: Path) -> dict[str, object]:
            return {
                "path": str(path.resolve()),
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper(),
            }

        def clean_frame_fixture(
            artifacts: Path, stem: str, *, label: str, phase: str
        ) -> dict[str, object]:
            samples: list[dict[str, object]] = []
            for sample_index, suffix in enumerate(("", "_drawer_confirmation"), 1):
                image_path = artifacts / f"{stem}{suffix}.png"
                image_path.write_bytes(
                    f"static-clean-frame:{label}:{phase}:{sample_index}".encode()
                )
                ocr_path = artifacts / f"{stem}{suffix}_ocr.json"
                capture.write_json(
                    ocr_path,
                    {"schema_version": 1, "items": [], "static_fixture": True},
                )
                samples.append(
                    {
                        "sample_index": sample_index,
                        "normalized_decisions_header_ocr": "",
                        "image": file_record(image_path),
                        "ocr": file_record(ocr_path),
                    }
                )
            gate_path = artifacts / f"{stem}_gate.json"
            payload = {
                "schema_version": 1,
                "result": "GREEN",
                "span": label,
                "phase": phase,
                "full_screen": True,
                "fixture_test_ui_absent": True,
                "native_decisions_drawer_absent": True,
                "forbidden_hits": [],
                "drawer_absence_consecutive_samples": 2,
                "drawer_absence_samples": samples,
                "image": samples[0]["image"],
                "ocr": samples[0]["ocr"],
            }
            capture.write_json(gate_path, payload)
            payload["gate"] = file_record(gate_path)
            return payload

        def seed_proof(context, observed_snapshot):
            return capture.prove_phase2_loaded_seed(
                dict(observed_snapshot),
                dict(context.seed_contract),
                context.artifacts,
                loaded_feature_manifest=manifest,
            )

        producer = make_managed_phase2_promo_capture_producer(
            paused_snapshot_probe=lambda _context: copy.deepcopy(snapshot),
            seed_proof_probe=seed_proof,
            reviewed_history_id="han_6875",
            span_driver_factory=lambda _context: ContractDriver(),
        )
        capture.register_phase2_promo_capture_producer(producer)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact_root = (root / "capture").resolve()
            bridge = SimpleNamespace(pipe_name=r"\\.\pipe\phase2-contract-unit")
            seed_path = (root / "canonical-phase2.ck3").resolve()
            seed_path.write_bytes(b"canonical-phase2-seed")
            seed_sha = hashlib.sha256(seed_path.read_bytes()).hexdigest().upper()
            seed_contract.update(
                {
                    "provenance": {
                        "source_git_commit": "1" * 40,
                        "source_report_sha256": "2" * 64,
                        "source_evidence_index_sha256": "3" * 64,
                    },
                    "runtime": {
                        "source_product_tree_sha256": "A" * 64,
                        "game_version": capture.EXPECTED_GAME_VERSION,
                        "executable_sha256": capture.EXPECTED_EXE_SHA256,
                    },
                    "source": {
                        "bytes": seed_path.stat().st_size,
                        "sha256": seed_sha,
                    },
                }
            )
            seed_install.update(
                {
                    "contract": copy.deepcopy(seed_contract),
                    "source": {
                        "path": str(seed_path),
                        "bytes": seed_path.stat().st_size,
                        "sha256": seed_sha,
                    },
                }
            )

            class ReceiptService(_FakeService):
                def snapshot(self) -> dict[str, object]:
                    value = copy.deepcopy(snapshot)
                    value["revision"] = runtime_revision["revision"]
                    value["native_revision"] = runtime_revision["native_revision"]
                    value["snapshot_id"] = (
                        f"phase2-cross-contract:{runtime_revision['revision']}"
                    )
                    return value

                def save_checkpoint(
                    self, *, expected_revision: int
                ) -> dict[str, object]:
                    self.assert_revision(expected_revision)
                    checkpoint_path = (
                        root
                        / "native-checkpoints"
                        / f"checkpoint-{time.monotonic_ns()}.ck3"
                    ).resolve()
                    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
                    checkpoint_path.write_bytes(
                        f"native:{expected_revision}:{checkpoint_path.name}".encode()
                    )
                    payload = checkpoint_path.read_bytes()
                    return {
                        "accepted": True,
                        "checkpoint": {
                            "status": "saved",
                            "path": str(checkpoint_path),
                            "size": len(payload),
                            "sha256": hashlib.sha256(payload).hexdigest().upper(),
                        },
                    }

                @staticmethod
                def assert_revision(expected_revision: int) -> None:
                    if expected_revision != runtime_revision["revision"]:
                        raise AssertionError("receipt save revision drifted")

            def artifact_hash(path: Path) -> str:
                candidate = Path(path).resolve()
                if candidate == seed_path or root / "native-checkpoints" in candidate.parents:
                    return hashlib.sha256(candidate.read_bytes()).hexdigest().upper()
                try:
                    candidate.relative_to(artifact_root)
                except ValueError:
                    return capture.EXPECTED_EXE_SHA256
                return hashlib.sha256(candidate.read_bytes()).hexdigest().upper()

            with ExitStack() as stack:
                _enter_common_run_cell_patches(stack, root)
                stack.enter_context(
                    mock.patch.object(capture, "GameplayBridgeService", ReceiptService)
                )
                stack.enter_context(
                    mock.patch.object(capture, "PromoRecorder", NoLaunchPromoRecorder)
                )
                stack.enter_context(
                    mock.patch.object(
                        capture,
                        "assert_promo_frame_clean",
                        side_effect=clean_frame_fixture,
                    )
                )
                stack.enter_context(
                    mock.patch.object(
                        capture.isolated,
                        "sha256_file",
                        side_effect=artifact_hash,
                    )
                )
                stack.enter_context(
                    mock.patch.object(
                        capture,
                        "install_phase2_seed",
                        return_value=copy.deepcopy(seed_install),
                    )
                )
                stack.enter_context(
                    mock.patch.object(
                        capture,
                        "start_phase2_native_session_supervisor",
                        return_value={"kind": "static-no-launch-supervisor"},
                    )
                )
                stack.enter_context(
                    mock.patch.object(
                        capture,
                        "wait_for_phase2_native_session_binding",
                        return_value={
                            "bridge_pid": tracked_pid,
                            "connection_generation": connection_generation,
                        },
                    )
                )
                stack.enter_context(
                    mock.patch.object(
                        capture,
                        "run_loader_gate",
                        return_value=copy.deepcopy(loader_gate),
                    )
                )
                def stop_with_receipt(
                    _supervisor: object,
                    cleanup_artifacts: Path,
                    **_kwargs: object,
                ) -> dict[str, object]:
                    cleanup = {
                        "result": "GREEN",
                        "cleanup_proven": True,
                        "contract_errors": [],
                        "failed_checks": [],
                        "checks": {"tracked_process_tree_gone": True},
                        "pid_lineage": [tracked_pid],
                        "connection_generation_lineage": [
                            connection_generation
                        ],
                        "session_report": {"restart_count": 0},
                    }
                    capture.write_json(
                        cleanup_artifacts / "09_phase2_native_session_cleanup.json",
                        cleanup,
                    )
                    return cleanup

                stack.enter_context(
                    mock.patch.object(
                        capture,
                        "stop_phase2_native_session_supervisor",
                        side_effect=stop_with_receipt,
                    )
                )
                forbidden_launch = stack.enter_context(
                    mock.patch.object(capture, "launch_native_ck3")
                )
                forbidden_ffmpeg = stack.enter_context(
                    mock.patch.object(
                        capture.shutil,
                        "which",
                        side_effect=AssertionError(
                            "static cross-contract fixture must not resolve FFmpeg"
                        ),
                    )
                )
                stack.enter_context(
                    mock.patch.object(
                        capture,
                        "promo_real_character_provenance",
                        return_value={
                            "result": "GREEN",
                            "history_id": "han_6875",
                            "static_fixture": True,
                        },
                    )
                )
                stack.enter_context(
                    mock.patch.object(
                        capture,
                        "resolve_native_bridge_config",
                        return_value=bridge,
                    )
                )
                preflight = stack.enter_context(
                    mock.patch.object(
                        capture,
                        "preflight",
                        return_value={
                            "native_bridge_runtime": {"identity": "static-unit"}
                        },
                    )
                )
                steam_root = root / "steam"
                stack.enter_context(
                    mock.patch.object(
                        capture.terminal,
                        "steam_userdata_root",
                        return_value=steam_root,
                    )
                )
                stack.enter_context(
                    mock.patch.object(
                        capture.isolated,
                        "steam_workshop_app_roots",
                        return_value=[],
                    )
                )
                stack.enter_context(
                    mock.patch.object(capture.isolated, "registered_workshop_targets")
                )
                stack.enter_context(
                    mock.patch.object(capture.isolated, "ensure_test_paths_safe")
                )
                stack.enter_context(
                    mock.patch.object(
                        capture.isolated, "protected_snapshot", return_value={}
                    )
                )
                stack.enter_context(
                    mock.patch.object(capture.isolated, "verify_protected_storage")
                )
                exit_code = capture.main(
                    artifacts_dir=str(artifact_root),
                    keep_userdir=True,
                    phase2_promo_capture=True,
                    phase2_seed_contract=str(root / "canonical-seed.json"),
                )

            strict = footage_intake.validate_footage_intake(artifact_root)
            timeline = json.loads(
                (artifact_root / "cell" / "promo" / "capture-timeline.json").read_text(
                    encoding="utf-8"
                )
            )
            outer = json.loads(
                (artifact_root / "report.json").read_text(encoding="utf-8")
            )
            index = json.loads(
                (artifact_root / "evidence-index.json").read_text(encoding="utf-8")
            )

        self.assertEqual(exit_code, 0, outer)
        self.assertEqual(strict["result"], "GREEN", strict["errors"])
        self.assertTrue(all(strict["checks"].values()), strict["checks"])
        self.assertEqual(outer["cell"]["promo_capture"], timeline)
        self.assertEqual(len(timeline["clean_frame_gates"]), 8)
        self.assertEqual(
            sum(len(row["frames"]) for row in timeline["clean_frame_gates"]),
            16,
        )
        self.assertEqual(len(timeline["marks"]), 18)
        indexed_paths = {row["path"] for row in index["files"]}
        self.assertIn("report.json", indexed_paths)
        self.assertIn("cell/04_phase2_seed_loaded.json", indexed_paths)
        self.assertIn("cell/promo/capture-timeline.json", indexed_paths)
        self.assertIn("cell/promo/raw/zg361-promo-live-full-take-01.mkv", indexed_paths)
        forbidden_launch.assert_not_called()
        forbidden_ffmpeg.assert_not_called()
        self.assertTrue(preflight.call_args.kwargs["require_visual_tools"])


if __name__ == "__main__":
    unittest.main()
