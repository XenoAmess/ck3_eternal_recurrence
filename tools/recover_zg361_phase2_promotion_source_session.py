#!/usr/bin/env python3
"""Recover one late ZhongGuo promotion-source session into a fresh owner.

This is a deliberately thin recovery wrapper.  It never mutates the source
profile/save, never uses desktop input, and delegates the actual CK3 lifecycle,
loader gate, and production route to the existing Phase-2 implementation.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, replace
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import traceback
from collections.abc import Callable, Mapping
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUTOPLAYER_SOURCE = ROOT / "ck3_autonomous_player" / "src"
for import_root in (ROOT / "tools", AUTOPLAYER_SOURCE):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

import run_acceptance as acceptance  # noqa: E402
import run_zhongguo_acceptance as runner  # noqa: E402
from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
)
from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402
from xar_autoplayer.environment import make_spec, write_json_atomic  # noqa: E402
from zg361_phase2_promotion_source_production_entry import (  # noqa: E402
    PRODUCT_TIMELINE_ORIGIN_DATE_RAW,
    PromotionProductionEntryError,
    enter_promotion_source_checkpoint_v1,
)


SHA256_RE = re.compile(r"[0-9a-f]{64}")
PRESERVED_PROFILE_ENTRIES = (
    "pdx_settings.txt",
    "shadercache",
    "account",
    "dlc_signature",
)


class RecoveryError(RuntimeError):
    pass


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_object(path: Path, label: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RecoveryError(f"{label} is unreadable: {path}: {error}") from error
    if not isinstance(value, dict):
        raise RecoveryError(f"{label} must be a JSON object: {path}")
    return value


def _write(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json_atomic(path, dict(value))


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def process_image_is_running(image_name: str) -> bool:
    """Query one exact Windows image name without touching its process."""

    result = subprocess.run(
        ["tasklist", "/FI", f"IMAGENAME eq {image_name}", "/FO", "CSV", "/NH"],
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise RecoveryError(
            f"could not prove empty process slot for {image_name!r}: "
            f"tasklist exit {result.returncode}: {result.stderr.strip()}"
        )
    for row in csv.reader(io.StringIO(result.stdout)):
        if row and row[0].casefold() == image_name.casefold():
            return True
    return False


def verify_exact_game(game_dir: Path) -> dict[str, object]:
    executable = game_dir / "binaries" / "ck3.exe"
    settings = game_dir / "launcher" / "launcher-settings.json"
    if not executable.is_file():
        raise RecoveryError(f"CK3 executable is missing: {executable}")
    digest = _sha256_file(executable)
    if digest != runner.EXPECTED_EXE_SHA256:
        raise RecoveryError(
            "CK3 executable SHA-256 drifted: "
            f"{digest}, expected {runner.EXPECTED_EXE_SHA256}"
        )
    settings_value = _read_object(settings, "CK3 launcher settings")
    version = settings_value.get("rawVersion")
    if version != runner.EXPECTED_GAME_VERSION:
        raise RecoveryError(
            f"CK3 version is {version!r}, expected {runner.EXPECTED_GAME_VERSION!r}"
        )
    raw_executable = settings_value.get("exePath")
    if not isinstance(raw_executable, str) or not raw_executable:
        raise RecoveryError("CK3 launcher settings contain no exePath")
    declared = (settings.parent / raw_executable).resolve()
    if declared != executable.resolve():
        raise RecoveryError(
            f"CK3 launcher exePath differs from the selected executable: {declared}"
        )
    return {
        "game_dir": str(game_dir),
        "version": version,
        "executable": str(executable.resolve()),
        "executable_sha256": digest,
    }


@dataclass(frozen=True)
class RecoveryConfig:
    source_profile: Path
    source_save: Path
    expected_source_save_sha256: str
    source_run_cell: Path
    state_dir: Path
    artifacts_dir: Path
    product_source: Path
    product_projection: str
    product_projection_manifest: Path
    game_dir: Path
    bridge_dll: Path
    bridge_injector: Path
    bridge_pipe: str
    timeout_seconds: float = 1800.0
    frontend_timeout_seconds: float = 180.0

    def resolved(self) -> "RecoveryConfig":
        return replace(
            self,
            source_profile=self.source_profile.resolve(),
            source_save=self.source_save.resolve(),
            source_run_cell=self.source_run_cell.resolve(),
            state_dir=self.state_dir.resolve(),
            artifacts_dir=self.artifacts_dir.resolve(),
            product_source=self.product_source.resolve(),
            product_projection_manifest=self.product_projection_manifest.resolve(),
            game_dir=self.game_dir.resolve(),
            bridge_dll=self.bridge_dll.resolve(),
            bridge_injector=self.bridge_injector.resolve(),
            expected_source_save_sha256=(
                self.expected_source_save_sha256.strip().lower()
            ),
        )


@dataclass(frozen=True)
class RuntimeBindings:
    process_running: Callable[[str], bool]
    verify_game: Callable[[Path], dict[str, object]]
    validate_seed_contract: Callable[[Mapping[str, object]], None]
    bootstrap_userdir: Callable[..., dict[str, object]]
    configure_runtime_userdir: Callable[[Path], None]
    make_spec: Callable[[Path, Path], object]
    resolve_bridge: Callable[[Path, Path, str], object]
    bridge_identity: Callable[[object], dict[str, object]]
    driver_factory: Callable[..., object]
    service_factory: Callable[[object], object]
    start_supervisor: Callable[..., dict[str, object]]
    wait_binding: Callable[..., dict[str, object]]
    loader_gate: Callable[..., dict[str, object]]
    production_entry: Callable[..., dict[str, object]]
    stop_supervisor: Callable[..., dict[str, object]]


def default_runtime() -> RuntimeBindings:
    return RuntimeBindings(
        process_running=process_image_is_running,
        verify_game=verify_exact_game,
        validate_seed_contract=runner.validate_phase2_promotion_source_seed_contract,
        bootstrap_userdir=runner.bootstrap_userdir,
        configure_runtime_userdir=acceptance.configure_runtime_userdir,
        make_spec=make_spec,
        resolve_bridge=runner.resolve_native_bridge_config,
        bridge_identity=runner.native_bridge_preflight_identity,
        driver_factory=NativeHeadlessGameplayDriver,
        service_factory=GameplayBridgeService,
        start_supervisor=runner.start_phase2_native_session_supervisor,
        wait_binding=runner.wait_for_phase2_native_session_binding,
        loader_gate=runner.run_loader_gate,
        production_entry=enter_promotion_source_checkpoint_v1,
        stop_supervisor=runner.stop_phase2_native_session_supervisor,
    )


def _validate_inputs(
    config: RecoveryConfig, runtime: RuntimeBindings
) -> tuple[dict[str, object], object, dict[str, object], dict[str, object]]:
    if config.state_dir.exists():
        raise RecoveryError(f"target state directory already exists: {config.state_dir}")
    if config.artifacts_dir.exists():
        raise RecoveryError(
            f"target artifact/source-run-cell already exists: {config.artifacts_dir}"
        )
    if (
        config.state_dir == config.artifacts_dir
        or _is_relative_to(config.state_dir, config.artifacts_dir)
        or _is_relative_to(config.artifacts_dir, config.state_dir)
    ):
        raise RecoveryError("target state and artifact directories must not overlap")
    if not config.state_dir.parent.is_dir():
        raise RecoveryError(f"target state parent is missing: {config.state_dir.parent}")
    if not config.artifacts_dir.parent.is_dir():
        raise RecoveryError(
            f"target artifact parent is missing: {config.artifacts_dir.parent}"
        )
    if not config.source_profile.is_dir():
        raise RecoveryError(f"source profile is missing: {config.source_profile}")
    if not (config.source_profile / "pdx_settings.txt").is_file():
        raise RecoveryError("source profile lacks pdx_settings.txt")
    if not (config.source_profile / "shadercache").is_dir():
        raise RecoveryError("source profile lacks its warm shadercache")
    if not config.source_save.is_file():
        raise RecoveryError(f"source save is missing: {config.source_save}")
    if not _is_relative_to(config.source_save, config.source_profile):
        raise RecoveryError("source save must be inside the explicit source profile")
    if SHA256_RE.fullmatch(config.expected_source_save_sha256) is None:
        raise RecoveryError("expected source-save SHA-256 must be 64 lowercase hex")
    actual_save_sha256 = _sha256_file(config.source_save)
    if actual_save_sha256 != config.expected_source_save_sha256:
        raise RecoveryError(
            "source save SHA-256 mismatch: "
            f"{actual_save_sha256}, expected {config.expected_source_save_sha256}"
        )
    if not config.source_run_cell.is_dir():
        raise RecoveryError(f"source run cell is missing: {config.source_run_cell}")
    seed_install_path = config.source_run_cell / "00_phase2_seed_install.json"
    seed_install = _read_object(seed_install_path, "source seed-install evidence")
    seed_contract = seed_install.get("contract")
    if not (
        seed_install.get("result") == "GREEN"
        and isinstance(seed_contract, Mapping)
        and seed_contract.get("ready") is True
        and seed_contract.get("status") == "ready"
    ):
        raise RecoveryError("source seed-install evidence is not GREEN/ready")
    try:
        runtime.validate_seed_contract(seed_contract)
    except Exception as error:
        raise RecoveryError(f"source promotion seed contract is invalid: {error}") from error
    if not config.product_source.is_dir():
        raise RecoveryError(f"current product source is missing: {config.product_source}")
    if not config.product_projection.strip():
        raise RecoveryError("current product projection name is empty")
    if not config.product_projection_manifest.is_file():
        raise RecoveryError(
            "current product projection manifest is missing: "
            f"{config.product_projection_manifest}"
        )
    output_paths = (config.state_dir, config.artifacts_dir)
    input_roots = (
        config.source_profile,
        config.source_run_cell,
        config.product_source,
    )
    for output in output_paths:
        for source_root in input_roots:
            if (
                output == source_root
                or _is_relative_to(output, source_root)
                or _is_relative_to(source_root, output)
            ):
                raise RecoveryError(
                    "recovery output overlaps an immutable input root: "
                    f"{output} <-> {source_root}"
                )
    for path, label in (
        (config.bridge_dll, "bridge DLL"),
        (config.bridge_injector, "bridge injector"),
    ):
        if not path.is_file():
            raise RecoveryError(f"{label} is missing: {path}")
    if config.timeout_seconds <= 0 or config.frontend_timeout_seconds <= 0:
        raise RecoveryError("recovery timeouts must be positive")
    bridge = runtime.resolve_bridge(
        config.bridge_dll, config.bridge_injector, config.bridge_pipe
    )
    bridge_identity = runtime.bridge_identity(bridge)
    game_identity = runtime.verify_game(config.game_dir)
    return seed_install, bridge, bridge_identity, {
        "path": str(config.source_save),
        "profile": str(config.source_profile),
        "bytes": config.source_save.stat().st_size,
        "sha256": actual_save_sha256,
        "last_write_time_ns": config.source_save.stat().st_mtime_ns,
        "game": game_identity,
    }


def _require_empty_process_slots(
    config: RecoveryConfig, runtime: RuntimeBindings
) -> dict[str, object]:
    images = tuple(dict.fromkeys(("ck3.exe", config.bridge_injector.name)))
    occupied = [image for image in images if runtime.process_running(image)]
    if occupied:
        raise RecoveryError(
            "managed recovery requires empty CK3/injector process slots: "
            + ", ".join(occupied)
        )
    return {"checked_images": list(images), "occupied_images": [], "result": "GREEN"}


def _copy_profile_startup_assets(
    source_profile: Path, target_profile: Path
) -> list[dict[str, object]]:
    copied: list[dict[str, object]] = []
    for name in PRESERVED_PROFILE_ENTRIES:
        source = source_profile / name
        if not source.exists():
            continue
        target = target_profile / name
        if source.is_dir():
            if target.exists():
                raise RecoveryError(f"profile startup target already exists: {target}")
            shutil.copytree(source, target)
            copied.append({"name": name, "kind": "directory"})
        elif source.is_file():
            shutil.copy2(source, target)
            copied.append(
                {
                    "name": name,
                    "kind": "file",
                    "bytes": target.stat().st_size,
                    "sha256": _sha256_file(target),
                }
            )
    copied_names = {str(row["name"]) for row in copied}
    if "pdx_settings.txt" not in copied_names or "shadercache" not in copied_names:
        raise RecoveryError("source profile startup settings/cache were not copied")
    return copied


def _compact_bootstrap(value: Mapping[str, object]) -> dict[str, object]:
    targets_value = value.get("targets")
    targets = targets_value if isinstance(targets_value, Mapping) else {}
    return {
        "enabled_mods": list(value.get("enabled_mods", [])),
        "targets": {str(key): str(path) for key, path in targets.items()},
        "tree_sha256": value.get("tree_sha256"),
        "manifest": value.get("manifest"),
    }


def _retention_evidence(
    *,
    config: RecoveryConfig,
    supervisor: Mapping[str, object],
    service: object,
    tracked_pid: int,
    reason: str,
) -> dict[str, object]:
    capabilities = service.capabilities()
    snapshot = service.snapshot()
    diagnostics_value = capabilities.get("diagnostics")
    diagnostics = (
        diagnostics_value if isinstance(diagnostics_value, Mapping) else {}
    )
    played_value = snapshot.get("played_character")
    played = played_value if isinstance(played_value, Mapping) else {}
    session_done = supervisor.get("session_done")
    checks = {
        "supervisor_still_running": (
            hasattr(session_done, "is_set") and not session_done.is_set()
        ),
        "bridge_connected": (
            capabilities.get("mode") == runner.NATIVE_BRIDGE_MODE
            and diagnostics.get("connected") is True
        ),
        "tracked_pid_unchanged": diagnostics.get("bridge_pid") == tracked_pid,
        "map_ready": snapshot.get("map_ready") is True,
        "played_character_bound": (
            isinstance(played.get("character_id"), int)
            and not isinstance(played.get("character_id"), bool)
            and int(played["character_id"]) > 0
        ),
    }
    healthy = all(checks.values())
    return {
        "schema_version": 1,
        "kind": "zg361_phase2_healthy_session_retention",
        "result": "RETAINED" if healthy else "RED",
        "reason": reason,
        "state_dir": str(config.state_dir),
        "profile_dir": str(config.state_dir / "profile"),
        "pipe": config.bridge_pipe,
        "bridge_pid": diagnostics.get("bridge_pid"),
        "connection_generation": diagnostics.get("connection_generation"),
        "snapshot_id": snapshot.get("snapshot_id"),
        "revision": snapshot.get("revision"),
        "date_raw": snapshot.get("date_raw"),
        "paused": snapshot.get("paused"),
        "played_character_id": played.get("character_id"),
        "checks": checks,
        "failed_checks": [name for name, passed in checks.items() if not passed],
        "process_restart_required": False,
        "reconnect_authorized": healthy,
    }


def _freeze_retention_logs(profile: Path, artifacts: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for name in ("error.log", "debug.log"):
        source = profile / "logs" / name
        target = artifacts / f"final_{name}"
        if not source.is_file():
            raise RecoveryError(f"retention log is missing: {source}")
        shutil.copy2(source, target)
        rows.append(
            {
                "name": name,
                "bytes": target.stat().st_size,
                "sha256": _sha256_file(target),
            }
        )
    return rows


def _supervisor_state(supervisor: Mapping[str, object]) -> dict[str, object]:
    done_value = supervisor.get("session_done")
    done = bool(hasattr(done_value, "is_set") and done_value.is_set())
    state_value = supervisor.get("session_state")
    state = state_value if isinstance(state_value, Mapping) else {}
    return {
        "schema_version": 1,
        "session_done": done,
        "error": state.get("error"),
        "report": state.get("report"),
    }


def _revoke_ended_retention(
    retention: Mapping[str, object], session_state: Mapping[str, object]
) -> dict[str, object]:
    value = dict(retention)
    checks_value = value.get("checks")
    checks = dict(checks_value) if isinstance(checks_value, Mapping) else {}
    checks["supervisor_still_running"] = False
    checks["supervisor_still_running_at_final_handoff"] = False
    value.update(
        result="RED",
        reason="supervisor_ended_before_recovery_handoff",
        reconnect_authorized=False,
        process_restart_required=True,
        checks=checks,
        failed_checks=[name for name, passed in checks.items() if passed is not True],
        session_state=dict(session_state),
    )
    return value


def run(
    raw_config: RecoveryConfig,
    *,
    runtime: RuntimeBindings | None = None,
) -> dict[str, object]:
    config = raw_config.resolved()
    active = runtime or default_runtime()
    seed_install, bridge, bridge_identity, source_identity = _validate_inputs(
        config, active
    )
    # The first check guarantees that validation itself is no-launch.  The
    # second check, immediately before supervisor creation, closes the long
    # product materialization window without pretending to replace the native
    # cross-process launch mutex owned by native_session.
    initial_process_inventory = _require_empty_process_slots(config, active)

    config.state_dir.mkdir()
    config.artifacts_dir.mkdir()
    profile = config.state_dir / "profile"
    report: dict[str, object] = {
        "schema_version": 1,
        "kind": "zg361_phase2_promotion_source_late_save_recovery",
        "result": "RED",
        "source_identity": source_identity,
        "source_run_cell": str(config.source_run_cell),
        "state_dir": str(config.state_dir),
        "profile_dir": str(profile),
        "artifacts_dir": str(config.artifacts_dir),
        "product_source": str(config.product_source),
        "product_projection": config.product_projection,
        "product_projection_manifest": str(config.product_projection_manifest),
        "bridge": bridge_identity,
        "initial_process_inventory": initial_process_inventory,
        "prelaunch_process_inventory": None,
        "profile_materialization": None,
        "binding": None,
        "loader_gate": None,
        "entry": None,
        "entry_error": None,
        "unknown_interrupt_retention": False,
        "session_retention": None,
        "session_state": None,
        "cleanup": None,
        "driver_closed": None,
        "launch_performed": False,
        "mcp_only": True,
        "ocr_used": False,
        "coordinates_used": False,
        "console_used": False,
        "timeline_origin_date_raw": PRODUCT_TIMELINE_ORIGIN_DATE_RAW,
        "failure_reason": None,
    }
    _write(config.artifacts_dir / "report.json", report)

    supervisor: dict[str, object] | None = None
    driver: object | None = None
    service: object | None = None
    binding: dict[str, object] | None = None
    entry_evidence: dict[str, object] = {}
    retain_eligible = False
    retained = False
    stopped = False
    try:
        bootstrap = active.bootstrap_userdir(
            profile,
            config.product_source,
            None,
            include_acceptance_fixture=False,
            product_projection=config.product_projection,
            product_projection_manifest=config.product_projection_manifest,
        )
        enabled_mods = bootstrap.get("enabled_mods")
        expected_mods = [f"mod/{runner.PRODUCT_OUTER}"]
        if enabled_mods != expected_mods:
            raise RecoveryError(
                f"recovery profile is not product-only: {enabled_mods!r}"
            )
        startup_assets = _copy_profile_startup_assets(config.source_profile, profile)
        autosave = profile / "save games" / "autosave.ck3"
        last_save = profile / "last_save.ck3"
        shutil.copy2(config.source_save, autosave)
        shutil.copy2(config.source_save, last_save)
        if (
            _sha256_file(autosave) != config.expected_source_save_sha256
            or _sha256_file(last_save) != config.expected_source_save_sha256
        ):
            raise RecoveryError("late-save copies failed byte verification")
        profile_evidence = {
            "schema_version": 1,
            "result": "GREEN",
            "source_profile": str(config.source_profile),
            "startup_assets": startup_assets,
            "autosave": str(autosave),
            "last_save": str(last_save),
            "save_sha256": config.expected_source_save_sha256,
            "bootstrap": _compact_bootstrap(bootstrap),
            "product_only_runtime": True,
            "acceptance_fixture_loaded": False,
        }
        report["profile_materialization"] = profile_evidence
        _write(config.artifacts_dir / "01_profile_materialization.json", profile_evidence)
        # Preserve the established manager-seed lineage schema for the existing
        # resume client.  The late save is a descendant, recorded independently
        # above; rewriting the seed contract would invent a second protocol.
        _write(config.artifacts_dir / "00_phase2_seed_install.json", seed_install)

        active.configure_runtime_userdir(profile)
        spec = active.make_spec(config.state_dir, config.game_dir)
        report["prelaunch_process_inventory"] = _require_empty_process_slots(
            config, active
        )
        supervisor = active.start_supervisor(
            spec,
            bridge,
            frontend_first_load_save_name="autosave",
            frontend_first_timeout_seconds=config.frontend_timeout_seconds,
        )
        report["launch_performed"] = True
        driver = active.driver_factory(
            config.bridge_pipe,
            state_dir=config.state_dir,
            save_dir=profile / "save games",
            command_timeout_seconds=runner.NATIVE_TITLE_COMMAND_TIMEOUT_S,
        )
        service = active.service_factory(driver)
        binding = active.wait_binding(
            service, supervisor, config.artifacts_dir
        )
        report["binding"] = binding
        tracked_pid_value = binding.get("bridge_pid")
        if (
            isinstance(tracked_pid_value, bool)
            or not isinstance(tracked_pid_value, int)
            or tracked_pid_value <= 0
        ):
            raise RecoveryError("managed binding returned no positive CK3 PID")
        tracked_pid = tracked_pid_value
        loader = active.loader_gate(
            service,
            config.artifacts_dir,
            profile,
            bootstrap,
            tracked_ck3_pid=tracked_pid,
            phase2_live_batch=False,
            managed_restore_supervisor=True,
            phase2_promotion_source_capture_live=True,
        )
        report["loader_gate"] = loader
        _write(config.artifacts_dir / "03_loader_gate.json", loader)
        if loader.get("result") != "GREEN":
            raise RecoveryError("exact-build loader gate returned non-GREEN")

        try:
            entry_result = active.production_entry(
                service,
                timeout_seconds=config.timeout_seconds,
                poll_interval_seconds=0.05,
                prefer_natural_cycle=False,
                evidence_out=entry_evidence,
            )
            if not isinstance(entry_result, dict) or entry_result.get("result") != "GREEN":
                raise RecoveryError("promotion production entry returned non-GREEN")
            entry_evidence = entry_result
            retain_eligible = True
            report["result"] = "GREEN"
        except PromotionProductionEntryError as error:
            report["entry_error"] = f"{type(error).__name__}: {error}"
            unknown = entry_evidence.get("unexpected_event")
            retain_eligible = isinstance(unknown, Mapping)
            report["unknown_interrupt_retention"] = retain_eligible
            if not retain_eligible:
                raise
        finally:
            report["entry"] = entry_evidence
            _write(
                config.artifacts_dir
                / "04_promotion_source_production_entry.json",
                entry_evidence,
            )

        if not retain_eligible:
            raise RecoveryError("promotion entry did not reach a retainable boundary")
        retention = _retention_evidence(
            config=config,
            supervisor=supervisor,
            service=service,
            tracked_pid=tracked_pid,
            reason=(
                "entry_green_recovery_boundary"
                if report["result"] == "GREEN"
                else "fail_closed_unknown_interrupt_recovery_boundary"
            ),
        )
        report["session_retention"] = retention
        if retention.get("result") != "RETAINED":
            raise RecoveryError(
                "managed CK3 was not healthy at the requested retention boundary: "
                + ", ".join(str(item) for item in retention["failed_checks"])
            )
        report["retention_logs"] = _freeze_retention_logs(
            profile, config.artifacts_dir
        )
        _write(
            config.artifacts_dir / "09_phase2_native_session_retained.json",
            retention,
        )
        retained = True
    except BaseException as error:
        report["failure_reason"] = f"{type(error).__name__}: {error}"
        if not isinstance(error, (RecoveryError, PromotionProductionEntryError)):
            report["traceback"] = traceback.format_exc()
    finally:
        if supervisor is not None and not retained:
            observed_session_state = _supervisor_state(supervisor)
            report["session_state"] = observed_session_state
            _write(
                config.artifacts_dir / "10_phase2_native_session_state.json",
                observed_session_state,
            )
            if observed_session_state["session_done"] is True:
                report["cleanup"] = {
                    "schema_version": 1,
                    "result": "ALREADY_ENDED",
                    "stop_requested": False,
                    "session_state": observed_session_state,
                }
                stopped = True
            else:
                final_capabilities: object = None
                if service is not None:
                    try:
                        final_capabilities = service.capabilities()
                    except BaseException:
                        final_capabilities = None
                try:
                    initial_pid = (
                        binding.get("bridge_pid")
                        if isinstance(binding, Mapping)
                        else None
                    )
                    initial_generation = (
                        binding.get("connection_generation")
                        if isinstance(binding, Mapping)
                        else None
                    )
                    report["cleanup"] = active.stop_supervisor(
                        supervisor,
                        config.artifacts_dir,
                        initial_pid=initial_pid,
                        initial_generation=initial_generation,
                        expected_pipe=config.bridge_pipe,
                        scenario_evidence=entry_evidence,
                        final_capabilities=final_capabilities,
                    )
                    stopped = True
                except BaseException as stop_error:
                    report["cleanup_error"] = (
                        f"{type(stop_error).__name__}: {stop_error}"
                    )
        if driver is not None:
            try:
                driver.close()
                report["driver_closed"] = True
            except BaseException as close_error:
                report["driver_closed"] = False
                report["driver_close_error"] = (
                    f"{type(close_error).__name__}: {close_error}"
                )
        if supervisor is not None:
            final_session_state = _supervisor_state(supervisor)
            report["session_state"] = final_session_state
            _write(
                config.artifacts_dir / "10_phase2_native_session_state.json",
                final_session_state,
            )
            if retained and final_session_state["session_done"] is True:
                retained = False
                retention_value = report.get("session_retention")
                retention = (
                    retention_value
                    if isinstance(retention_value, Mapping)
                    else {}
                )
                revoked = _revoke_ended_retention(
                    retention, final_session_state
                )
                report["session_retention"] = revoked
                report["result"] = "RED"
                report["failure_reason"] = (
                    "RecoveryError: managed supervisor ended before final "
                    "resume-client handoff"
                )
                _write(
                    config.artifacts_dir
                    / "09_phase2_native_session_retained.json",
                    revoked,
                )
        report["session_retained_for_resume_client"] = retained
        report["supervisor_stopped"] = stopped
        _write(config.artifacts_dir / "report.json", report)
    return report


def parse_args(argv: list[str] | None = None) -> RecoveryConfig:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-profile", type=Path, required=True)
    parser.add_argument("--source-save", type=Path, required=True)
    parser.add_argument("--expected-source-save-sha256", required=True)
    parser.add_argument("--source-run-cell", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--artifacts-dir", type=Path, required=True)
    parser.add_argument("--product-source", type=Path, required=True)
    parser.add_argument("--product-projection", required=True)
    parser.add_argument("--product-projection-manifest", type=Path, required=True)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--bridge-injector", type=Path, required=True)
    parser.add_argument("--bridge-pipe", required=True)
    parser.add_argument("--timeout-seconds", type=float, default=1800.0)
    parser.add_argument("--frontend-timeout-seconds", type=float, default=180.0)
    args = parser.parse_args(argv)
    return RecoveryConfig(
        source_profile=args.source_profile,
        source_save=args.source_save,
        expected_source_save_sha256=args.expected_source_save_sha256,
        source_run_cell=args.source_run_cell,
        state_dir=args.state_dir,
        artifacts_dir=args.artifacts_dir,
        product_source=args.product_source,
        product_projection=args.product_projection,
        product_projection_manifest=args.product_projection_manifest,
        game_dir=args.game_dir,
        bridge_dll=args.bridge_dll,
        bridge_injector=args.bridge_injector,
        bridge_pipe=args.bridge_pipe,
        timeout_seconds=args.timeout_seconds,
        frontend_timeout_seconds=args.frontend_timeout_seconds,
    )


def main(argv: list[str] | None = None) -> int:
    try:
        report = run(parse_args(argv))
    except (RecoveryError, OSError, ValueError) as error:
        print(f"recovery preflight failed: {type(error).__name__}: {error}")
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    return 0 if report.get("result") == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
