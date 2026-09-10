#!/usr/bin/env python3
"""MCP-owned exact-build migration of a real legacy seed, without custom mods.

The plan and preflight commands never launch CK3. The serve command remains
inert until the operator sends run-migration, then loads, saves, archives and
cleans up one isolated migration session. The result is not a product seed.
"""

from __future__ import annotations

import argparse
import copy
import importlib
import shutil
import sys
import threading
import time
import hashlib
import json
import re
from pathlib import Path
from typing import Mapping, Protocol, Sequence

import zg361_phase2_af5_operator_job as operator


class MigrationError(RuntimeError):
    def __init__(self, message: str, evidence: Mapping[str, object] | None = None) -> None:
        super().__init__(message)
        self.evidence = copy.deepcopy(dict(evidence)) if evidence is not None else None


class BoundService(Protocol):
    def snapshot(self) -> dict[str, object]: ...
    def capabilities(self) -> dict[str, object]: ...
    def save_checkpoint(self, *, expected_revision: int) -> dict[str, object]: ...


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _legacy_metadata(path: Path) -> dict[str, object]:
    with path.open("rb") as stream:
        prefix = stream.read(2 * 1024 * 1024)
    if not prefix.startswith(b"SAV0102"):
        raise MigrationError("legacy source lacks the expected SAV0102 header")
    boundary = prefix.find(b"PK\x03\x04")
    if boundary < 0:
        raise MigrationError("legacy source metadata boundary was not found")
    text = prefix[:boundary].decode("utf-8")

    def scalar(pattern: str, label: str) -> str:
        match = re.search(pattern, text, re.MULTILINE)
        if match is None:
            raise MigrationError(f"legacy source metadata lacks {label}")
        return match.group(1)

    portrait = re.search(r"\bmeta_main_portrait=\{(?P<body>.*?)\n\s*\}\n\s*meta_heir_portrait=", text, re.DOTALL)
    if portrait is None:
        raise MigrationError("legacy source metadata lacks a bounded main portrait")
    identity = re.search(r"^\s*id=(\d+)\s*$", portrait.group("body"), re.MULTILINE)
    if identity is None:
        raise MigrationError("legacy source metadata lacks the player CharacterID")
    return {
        "container_header": "SAV0102",
        "save_game_version": int(scalar(r"^\s*save_game_version=(\d+)\s*$", "save_game_version")),
        "game_version": scalar(r'^\s*version="([^"]+)"\s*$', "version"),
        "date": scalar(r"^\s*meta_date=([0-9.]+)\s*$", "meta_date"),
        "player_name": scalar(r'^\s*meta_player_name="([^"]+)"\s*$', "meta_player_name"),
        "title_name": scalar(r'^\s*meta_title_name="([^"]+)"\s*$', "meta_title_name"),
        "player_tier": int(scalar(r"^\s*meta_player_tier=(\d+)\s*$", "meta_player_tier")),
        "player_character_id": int(identity.group(1)),
        "government": scalar(r"^\s*meta_government=([^\s]+)\s*$", "meta_government"),
        "ironman": scalar(r"^\s*ironman=(yes|no)\s*$", "ironman"),
    }


def build_no_launch_plan(
    *,
    source_save: Path,
    expected_source_sha256: str,
    target_executable: Path,
    expected_target_executable_sha256: str,
    bridge_dll: Path,
    bridge_injector: Path,
    product_projection: Path,
    product_manifest: Path,
) -> dict[str, object]:
    paths = {
        "source_save": source_save.resolve(),
        "target_executable": target_executable.resolve(),
        "bridge_dll": bridge_dll.resolve(),
        "bridge_injector": bridge_injector.resolve(),
        "product_projection": product_projection.resolve(),
        "product_manifest": product_manifest.resolve(),
    }
    for name, path in paths.items():
        expected_kind = "directory" if name == "product_projection" else "file"
        if (expected_kind == "file" and not path.is_file()) or (
            expected_kind == "directory" and not path.is_dir()
        ):
            raise MigrationError(f"{name} is not an existing {expected_kind}: {path}")
    source_sha = sha256_file(paths["source_save"])
    exe_sha = sha256_file(paths["target_executable"])
    if source_sha != expected_source_sha256.upper():
        raise MigrationError("legacy source SHA-256 drifted")
    if exe_sha != expected_target_executable_sha256.upper():
        raise MigrationError("target CK3 executable is not the pinned exact build")
    metadata = _legacy_metadata(paths["source_save"])
    return {
        "schema_version": 1,
        "kind": "ck3_legacy_seed_exact_build_migration_activation_v1",
        "result": "GREEN",
        "mode": "no-launch-preflight",
        "launch_attempted": False,
        "ck3_control_attempted": False,
        "source": {
            "path": str(paths["source_save"]),
            "bytes": paths["source_save"].stat().st_size,
            "sha256": source_sha,
            "metadata": metadata,
        },
        "target": {
            "game_version": "1.19.0.6",
            "executable": str(paths["target_executable"]),
            "executable_sha256": exe_sha,
            "required_adapter_id": "ck3-1.19.0.6-msvc-x64",
            "required_output_header": "SAV0101",
            "required_player_character_id": metadata["player_character_id"],
        },
        "frozen_inputs": {
            "bridge_dll": {"path": str(paths["bridge_dll"]), "sha256": sha256_file(paths["bridge_dll"])},
            "bridge_injector": {"path": str(paths["bridge_injector"]), "sha256": sha256_file(paths["bridge_injector"])},
            "product_projection": str(paths["product_projection"]),
            "product_manifest": {"path": str(paths["product_manifest"]), "sha256": sha256_file(paths["product_manifest"])},
        },
        "migration_round": {
            "playset": "no-custom-mods",
            "load_argument": "-loadsave=legacy_migration_source",
            "source_materialization": "<isolated-profile>/save games/legacy_migration_source.ck3",
            "reason": "avoid product initialization before the exact-build seed is frozen",
        },
        "operator_mcp_contract": {
            "transport": "streamable-http",
            "exclusive_process_names": ["ck3.exe"],
            "required_order": [
                "prove CK3 process inventory is empty",
                "copy and re-hash the source into a fresh isolated profile",
                "launch exact CK3 with no custom mods and the explicit -loadsave basename",
                "bind the exact bridge and require a paused map-ready snapshot",
                "call migrate_already_bound on that service without advancing time or selecting an event",
                "managed cleanup; a later fresh round may load the migrated seed with the product projection",
            ],
        },
        "reuse_assessment": {
            "generic_native_supervisor_and_typed_service": "REUSABLE",
            "manager_seed_bootstrap": "NOT_DIRECTLY_REUSABLE_REQUIRES_FIXTURE_EVENT_AND_CURRENT_LINEAGE",
            "phase2_source_checkpoint_provider": "NOT_APPLICABLE_UNTIL_STAGE_SPECIFIC_RECEIPTS_EXIST",
            "seed_capture_runner": "LOWER_LEVEL_LAUNCH_COMPONENTS_REUSABLE_BUT_NO_MIGRATION_MODE",
        },
        "fail_closed": [
            "another CK3 PID exists at launch admission",
            "source copy hash differs from this plan",
            "loader does not reach one paused map-ready player snapshot",
            "exact-build hello, adapter id, PID, or save-checkpoint capability is absent",
            "played CharacterID differs from the selected source or an active event blocks a clean freeze",
            "error.log reports a loader/project RED",
            "MCP save result lacks an existing byte/hash/date-bound SAV0101 checkpoint",
        ],
        "scope_boundary": "migration only; not a ready product seed and not P1 acceptance",
    }


def migrate_already_bound(service: BoundService, plan: Mapping[str, object], output: Path) -> dict[str, object]:
    """Immediately freeze a successfully loaded legacy save through typed MCP."""
    if plan.get("kind") != "ck3_legacy_seed_exact_build_migration_activation_v1" or plan.get("result") != "GREEN":
        raise MigrationError("activation plan is not GREEN")
    source = plan.get("source")
    target = plan.get("target")
    if not isinstance(source, Mapping) or not isinstance(target, Mapping):
        raise MigrationError("activation plan is malformed")
    source_path = Path(str(source.get("path"))).resolve()
    if not source_path.is_file() or sha256_file(source_path) != source.get("sha256"):
        raise MigrationError("source save changed after no-launch admission")
    snap = service.snapshot()
    diagnostics = snap.get("diagnostics")
    hello = diagnostics.get("hello") if isinstance(diagnostics, Mapping) else None
    played = snap.get("played_character")
    caps = hello.get("capabilities") if isinstance(hello, Mapping) else None
    checks = {
        "paused": snap.get("paused") is True,
        "map_ready": snap.get("map_ready") is True,
        "player": isinstance(played, Mapping) and played.get("character_id") == target.get("required_player_character_id") and played.get("alive") is True,
        "no_active_event": snap.get("active_event") is None,
        "exact_build": isinstance(hello, Mapping) and hello.get("ck3_build_match") is True and hello.get("expected_ck3_version") == target.get("game_version") and hello.get("expected_ck3_sha256") == target.get("executable_sha256") and hello.get("game_adapter_id") == target.get("required_adapter_id") and hello.get("game_adapter_status") == "ready",
        "save_capability": isinstance(caps, list) and "game.command.save-checkpoint" in caps,
    }
    revision = snap.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
        checks["revision"] = False
    else:
        checks["revision"] = True
    if not all(checks.values()):
        raise MigrationError(f"live migration admission failed closed: {checks}", {"checks": checks, "snapshot": snap})
    response = service.save_checkpoint(expected_revision=revision)
    checkpoint = response.get("checkpoint", response)
    if not isinstance(checkpoint, Mapping):
        raise MigrationError("MCP save-checkpoint response is malformed")
    path = Path(str(checkpoint.get("path"))).resolve()
    expected_date = snap.get("date_raw")
    valid = (
        response.get("accepted", True) is True
        and checkpoint.get("status") == "saved"
        and path.is_file()
        and checkpoint.get("size") == path.stat().st_size
        and str(checkpoint.get("sha256", "")).upper() == sha256_file(path)
        and checkpoint.get("date_raw") == expected_date
        and checkpoint.get("episode_character_id") in (None, target.get("required_player_character_id"))
        and _read_header(path) == b"SAV0101"
    )
    if not valid:
        raise MigrationError("MCP checkpoint did not satisfy exact-build byte/date/player gates", {"snapshot": snap, "save_result": response})
    after = service.snapshot()
    if after.get("date_raw") != expected_date or after.get("played_character") != played or after.get("paused") is not True:
        raise MigrationError("live state changed while freezing the migrated seed")
    report = {
        "schema_version": 1,
        "kind": "ck3_legacy_seed_exact_build_migration_receipt_v1",
        "result": "GREEN",
        "mcp_only": True,
        "source_sha256": source.get("sha256"),
        "target_build": {"game_version": target.get("game_version"), "executable_sha256": target.get("executable_sha256")},
        "binding": {"pid": diagnostics.get("bridge_pid", hello.get("pid")), "connection_generation": diagnostics.get("connection_generation", hello.get("connection_generation")), "date_raw": expected_date, "player_character_id": target.get("required_player_character_id")},
        "checkpoint": {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path), "header": "SAV0101"},
        "before_snapshot": snap,
        "after_snapshot": after,
        "save_result": response,
        "product_seed_ready": False,
        "next_required_action": "cold-load this checkpoint in a fresh exclusive CK3 round with the current product projection, then run manager/provider admission",
    }
    write_json(output, report)
    return report


def _read_header(path: Path) -> bytes:
    with path.open("rb") as stream:
        return stream.read(7)


ACTIVATION_KIND = "zg361_phase2_legacy_seed_operator_activation_v1"
CONTROLS = ["status", "run-migration", "cleanup"]


def validate_operator_activation(activation_path: Path, *, require_empty_slot: bool) -> dict[str, object]:
    value = operator.read_object(activation_path)
    if value.get("schema_version") != 1 or value.get("kind") != ACTIVATION_KIND:
        raise MigrationError("migration operator activation kind differs")
    root = operator.checked_directory(value.get("repository_root"), "repository_root")
    code_commit = value.get("code_commit")
    if not isinstance(code_commit, str) or re.fullmatch(r"[0-9a-f]{40}", code_commit) is None:
        raise MigrationError("code_commit must be a full frozen Git commit")
    if operator.git_identity(root) != {"head": code_commit, "tracked_dirty": False}:
        raise MigrationError("migration execution checkout differs from its freeze")
    plan_path = operator.checked_file(value.get("migration_plan"), "migration_plan")
    plan = operator.read_object(plan_path)
    if plan.get("kind") != "ck3_legacy_seed_exact_build_migration_activation_v1" or plan.get("result") != "GREEN":
        raise MigrationError("migration plan is not GREEN")
    source = operator.mapping(plan.get("source"), "migration source")
    operator.checked_file(source, "migration source")
    target = operator.mapping(plan.get("target"), "migration target")
    game_dir = operator.checked_directory(value.get("game_directory"), "game_directory")
    game_exe = game_dir / "binaries/ck3.exe"
    if game_exe != Path(str(target.get("executable"))).resolve() or sha256_file(game_exe) != target.get("executable_sha256"):
        raise MigrationError("migration target does not match the explicit CK3 installation")
    frozen = operator.mapping(plan.get("frozen_inputs"), "frozen inputs")
    paths = {}
    for key in ("bridge_dll", "bridge_injector"):
        row = operator.mapping(frozen.get(key), key)
        path = Path(str(row.get("path"))).resolve()
        if not path.is_file() or sha256_file(path) != row.get("sha256"):
            raise MigrationError(f"migration {key} hash differs")
        paths[key] = path
    prior_cleanup = operator.checked_file(value.get("prior_cleanup"), "prior_cleanup")
    cleanup = operator.read_object(prior_cleanup)
    if cleanup.get("result") != "GREEN" or cleanup.get("scope") != "phase2_managed_native_session_cleanup":
        raise MigrationError("prior canonical cleanup is not GREEN")
    startup = operator.checked_directory(value.get("startup_template_profile"), "startup_template_profile")
    if not (startup / "shadercache").is_dir():
        raise MigrationError("startup template has no shadercache")
    outputs = {}
    for key in ("state_directory", "artifact_directory"):
        path = Path(str(value.get(key, ""))).expanduser()
        if not path.is_absolute() or (require_empty_slot and path.exists()):
            raise MigrationError(f"{key} must be a fresh absolute output")
        outputs[key] = path.resolve()
    if outputs["state_directory"] == outputs["artifact_directory"]:
        raise MigrationError("state and artifact directories must differ")
    for key in ("bridge_pipe", "warmup_bridge_pipe"):
        if not isinstance(value.get(key), str) or operator.PIPE_RE.fullmatch(value[key]) is None:
            raise MigrationError(f"{key} is not a run-unique bridge pipe")
    if value["bridge_pipe"] == value["warmup_bridge_pipe"]:
        raise MigrationError("warmup and migration bridge pipes must differ")
    rounds = operator.mapping(value.get("rounds"), "rounds")
    warmup = operator.ROUND_RE.fullmatch(str(rounds.get("frontend_warmup", "")))
    gameplay = operator.ROUND_RE.fullmatch(str(rounds.get("migration", "")))
    if warmup is None or gameplay is None or int(gameplay.group(1)) != int(warmup.group(1)) + 1:
        raise MigrationError("migration launch must immediately follow its warmup round")
    if require_empty_slot and operator.ck3_pids():
        raise MigrationError("exclusive CK3 slot is occupied")
    return {"activation": value, "activation_record": operator.file_record(activation_path),
            "repository_root": root, "code_commit": code_commit, "plan": plan,
            "game_directory": game_dir, "startup_template_profile": startup,
            "rounds": dict(rounds), "bridge_pipe": value["bridge_pipe"],
            "warmup_bridge_pipe": value["warmup_bridge_pipe"], **paths, **outputs}


def materialize_migration_profile(bound: Mapping[str, object], runner: object) -> dict[str, object]:
    """Create only settings, caches and the source save; mount no custom mod."""
    profile = Path(str(bound["state_directory"])) / "profile"
    for relative in ("logs", "save games", "player/game_rules"):
        (profile / relative).mkdir(parents=True, exist_ok=True)
    shader = runner.project_particle2_startup_shader_bundle(profile, game_dir=bound["game_directory"])
    (profile / "pdx_settings.txt").write_text(runner.terminal.render_settings(), encoding="utf-8")
    operator.write_object(profile / "dlc_load.json", {"enabled_mods": [], "disabled_dlcs": []})
    startup = operator._copy_startup_assets(Path(str(bound["startup_template_profile"])), profile)
    source = operator.mapping(bound["plan"]["source"], "migration source")
    materialized = []
    for target in (profile / "save games/legacy_migration_source.ck3", profile / "last_save.ck3"):
        shutil.copy2(Path(str(source["path"])), target)
        record = operator.file_record(target)
        if record["sha256"] != source["sha256"]:
            raise MigrationError("materialized legacy source hash differs")
        materialized.append(record)
    return {"schema_version": 1, "result": "GREEN", "profile": str(profile),
            "enabled_mods": [], "custom_mods_loaded": False,
            "source_materialization": materialized, "startup_assets": startup,
            "particle2_startup_shader_projection": operator.bootstrap_evidence_json_value(shader)}


class LegacySeedMigrationJob:
    def __init__(self, activation_path: Path) -> None:
        self.activation_path = activation_path.expanduser().resolve()
        self.lock = threading.RLock()
        self.stop_requested = threading.Event()
        self.worker: threading.Thread | None = None
        self.state = "READY_NO_LAUNCH"
        self.stage = "ready"
        self.migration_result = "PENDING"
        self.failure_reason: str | None = None
        self.bound = None
        self.runner = None
        self.supervisor = None
        self.driver = None
        self.service = None
        self.binding = None
        self.receipt = None
        self.cleanup_receipt = None

    def status(self) -> dict[str, object]:
        with self.lock:
            cleanup_result = self.cleanup_receipt.get("result") if self.cleanup_receipt else "PENDING"
            return {"schema_version": 1, "kind": "zg361_legacy_seed_migration_operator_status_v1",
                    "state": self.state, "stage": self.stage,
                    "result": "RED" if self.failure_reason or cleanup_result == "RED" else self.migration_result,
                    "migration_result": self.migration_result, "cleanup_result": cleanup_result,
                    "failure_reason": self.failure_reason, "binding": self.binding,
                    "rounds": self.bound.get("rounds") if self.bound else None,
                    "ck3_pids": operator.ck3_pids(), "controls": CONTROLS,
                    "product_seed_ready": False, "video_lock_touched": False}

    def start(self) -> dict[str, object]:
        with self.lock:
            if self.worker is not None or self.state != "READY_NO_LAUNCH":
                return {**self.status(), "control": "run-migration", "idempotent": True}
            self.state = "RUNNING_MIGRATION"
            self.worker = threading.Thread(target=self._run, name="legacy-migration", daemon=False)
            self.worker.start()
            return {**self.status(), "control": "run-migration", "accepted": True}

    def _run(self) -> None:
        try:
            self.bound = validate_operator_activation(self.activation_path, require_empty_slot=True)
            self._execute(self.bound)
            self.state = "MIGRATION_GREEN_PARKED"
            self.perform_cleanup()
        except BaseException as error:
            self.failure_reason = f"{type(error).__name__}: {error}"
            self.migration_result = "GREEN" if self.receipt else "RED"
            snapshot = None
            if self.service is not None:
                try:
                    snapshot = self.service.snapshot()
                    if snapshot.get("paused") is not True:
                        self.service.execute_step("pause-map", expected_revision=int(snapshot["revision"]))
                        snapshot = self.service.snapshot()
                except BaseException:
                    snapshot = None
            self.state = "MIGRATION_RED_PARKED" if operator.ck3_pids() else "MIGRATION_RED_NO_LIVE_PROCESS"
            if self.bound is not None:
                operator.write_object(Path(str(self.bound["artifact_directory"])) / "migration-red.json", {
                    "schema_version": 1, "result": "RED", "migration_result": self.migration_result,
                    "failure_stage": self.stage, "failure_reason": self.failure_reason,
                    "evidence": operator.bootstrap_evidence_json_value(getattr(error, "evidence", None)),
                    "snapshot": operator.bootstrap_evidence_json_value(snapshot), "red_preserved": True,
                    "product_seed_ready": False,
                })
        finally:
            print(json.dumps({**self.status(), "notification": "run-migration-finished"}), flush=True)

    def _execute(self, bound: Mapping[str, object]) -> None:
        root = Path(str(bound["repository_root"]))
        sys.path.insert(0, str(root / "tools"))
        sys.path.insert(0, str(root / "ck3_autonomous_player/src"))
        runner = importlib.import_module("run_zhongguo_acceptance")
        acceptance = importlib.import_module("run_acceptance")
        environment = importlib.import_module("xar_autoplayer.environment")
        native_driver = importlib.import_module("xar_autoplayer.bridge.native_driver")
        service_module = importlib.import_module("xar_autoplayer.bridge.service")
        for module in (runner, acceptance, environment, native_driver, service_module):
            if not Path(str(module.__file__)).resolve().is_relative_to(root):
                raise MigrationError("migration execution module is outside the frozen checkout")
        self.runner = runner
        artifacts = Path(str(bound["artifact_directory"]))
        state_dir = Path(str(bound["state_directory"]))
        artifacts.mkdir(parents=True, exist_ok=False)
        state_dir.mkdir(parents=True, exist_ok=False)
        self.stage = "materialization"
        materialization = materialize_migration_profile(bound, runner)
        operator.write_object(artifacts / "01-materialization.json", materialization)
        profile = state_dir / "profile"
        acceptance.configure_runtime_userdir(profile)
        spec = environment.make_spec(state_dir=state_dir, game_dir=bound["game_directory"])
        bridge = runner.resolve_native_bridge_config(str(bound["bridge_dll"]), str(bound["bridge_injector"]), bound["bridge_pipe"])
        warmup_bridge = runner.resolve_native_bridge_config(str(bound["bridge_dll"]), str(bound["bridge_injector"]), bound["warmup_bridge_pipe"])
        self.stage = "native_startup"
        activation = bound["activation"]
        self.supervisor = runner.start_phase2_native_session_supervisor(
            spec, bridge, runtime_timeout_seconds=float(activation.get("runtime_timeout_seconds", 1800.0)),
            frontend_first_load_save_name="legacy_migration_source",
            frontend_first_timeout_seconds=float(activation.get("frontend_timeout_seconds", 300.0)),
            frontend_first_warmup_bridge=warmup_bridge,
        )
        self.driver = native_driver.NativeHeadlessGameplayDriver(
            bound["bridge_pipe"], state_dir=state_dir, save_dir=profile / "save games",
            command_timeout_seconds=runner.NATIVE_TITLE_COMMAND_TIMEOUT_S,
        )
        self.service = service_module.GameplayBridgeService(self.driver)
        self.binding = runner.wait_for_phase2_native_session_binding(self.service, self.supervisor, artifacts)
        pid = operator.positive_int(self.binding.get("bridge_pid"), "migration PID")
        if operator.ck3_pids() != [pid]:
            raise MigrationError("migration CK3 process is not the sole live process")
        self.stage = "loader"
        runner.native_loader_smoke_readiness(self.service, artifacts, tracked_ck3_pid=pid)
        loader = runner.scan_loader_error_log(profile, artifacts)
        if loader.get("result") != "GREEN":
            raise MigrationError("legacy loader scan returned RED", loader)
        self.stage = "paused_legacy_map"
        deadline = time.monotonic() + float(activation.get("map_timeout_seconds", 300.0))
        snapshot = None
        while time.monotonic() < deadline:
            snapshot = self.service.snapshot()
            if snapshot.get("map_ready") is True and snapshot.get("played_character"):
                if snapshot.get("paused") is not True:
                    self.service.execute_step("pause-map", expected_revision=int(snapshot["revision"]))
                break
            time.sleep(0.25)
        else:
            raise MigrationError("legacy map did not become ready", {"last_snapshot": snapshot})
        self.stage = "native_migration_save"
        self.receipt = migrate_already_bound(self.service, bound["plan"], artifacts / "migration-receipt.json")
        self.migration_result = "GREEN"
        checkpoint = self.receipt["checkpoint"]
        archived = runner._phase2_archive_checkpoint(
            {"path": checkpoint["path"], "size": checkpoint["bytes"], "sha256": checkpoint["sha256"]},
            artifacts / "migrated-exact-build-seed.ck3",
            save_lineage_id=f"{bound['rounds']['migration']}.legacy-migration",
        )
        self.receipt.update(
            archived_checkpoint=archived, source=bound["plan"]["source"],
            execution_identity={"repository_root": str(root), "code_commit": bound["code_commit"]},
            rounds=bound["rounds"], custom_mods_loaded=False,
            loader_scan=operator.file_record(artifacts / "02_loader_error_scan.json"),
        )
        operator.write_object(artifacts / "migration-receipt.json", self.receipt)
        self.stage = "migration_saved"

    def perform_cleanup(self) -> dict[str, object]:
        with self.lock:
            if self.state == "RUNNING_MIGRATION":
                return {**self.status(), "control": "cleanup", "accepted": False, "reason": "migration active"}
            if self.cleanup_receipt is not None:
                return {**self.status(), "control": "cleanup", "idempotent": True}
        self.stage = "cleanup"
        if self.supervisor is None:
            if operator.ck3_pids():
                return {**self.status(), "control": "cleanup", "accepted": False, "reason": "no owned supervisor"}
            cleanup = {"result": "GREEN", "no_launch": True}
        else:
            capabilities = None
            try:
                capabilities = self.service.capabilities()
            except BaseException:
                pass
            binding = self.binding or {}
            cleanup = self.runner.stop_phase2_native_session_supervisor(
                self.supervisor, self.bound["artifact_directory"], initial_pid=binding.get("bridge_pid"),
                initial_generation=binding.get("connection_generation"), expected_pipe=self.bound["bridge_pipe"],
                scenario_evidence=self.receipt or {"result": "RED", "restore_expected": False},
                final_capabilities=capabilities,
            )
            if self.driver is not None:
                self.driver.close()
        self.cleanup_receipt = {"schema_version": 1,
            "result": "GREEN" if cleanup.get("result") == "GREEN" and operator.ck3_pids() == [] else "RED",
            "canonical_cleanup": cleanup, "ck3_pids_after": operator.ck3_pids(), "product_seed_ready": False}
        if self.bound is not None:
            operator.write_object(self.bound["artifact_directory"] / "migration-managed-cleanup.json", self.cleanup_receipt)
        self.state = "CLEANED" if self.cleanup_receipt["result"] == "GREEN" else "CLEANUP_RED"
        self.stop_requested.set()
        return {**self.status(), "control": "cleanup", "accepted": True}

    def serve(self) -> int:
        self.bound = validate_operator_activation(self.activation_path, require_empty_slot=False)
        print(json.dumps(self.status()), flush=True)
        while not self.stop_requested.is_set():
            line = sys.stdin.readline()
            if line == "":
                self.stop_requested.wait(5.0)
                continue
            control = line.strip().casefold()
            if control == "status":
                response = self.status()
            elif control == "run-migration":
                response = self.start()
            elif control == "cleanup":
                response = self.perform_cleanup()
            else:
                response = {"result": "RED", "error": "unknown control", "controls": CONTROLS}
            print(json.dumps(response), flush=True)
        if self.worker is not None:
            self.worker.join()
        return 0 if not self.failure_reason and self.cleanup_receipt and self.cleanup_receipt["result"] == "GREEN" else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    plan_parser = commands.add_parser("plan")
    for name in ("source-save", "target-executable", "bridge-dll", "bridge-injector", "product-projection", "product-manifest", "output"):
        plan_parser.add_argument("--" + name, type=Path, required=True)
    plan_parser.add_argument("--expected-source-sha256", required=True)
    plan_parser.add_argument("--expected-target-executable-sha256", required=True)
    preflight = commands.add_parser("preflight")
    preflight.add_argument("--activation", type=Path, required=True)
    preflight.add_argument("--output", type=Path)
    serve = commands.add_parser("serve")
    serve.add_argument("--activation", type=Path, required=True)
    args = vars(parser.parse_args(argv))
    command = args.pop("command")
    if command == "serve":
        return LegacySeedMigrationJob(args["activation"]).serve()
    output = args.pop("output", None)
    if command == "plan":
        report = build_no_launch_plan(**args)
    else:
        bound = validate_operator_activation(args["activation"], require_empty_slot=False)
        report = {"result": "GREEN", "mode": "no-launch-preflight", "launch_attempted": False,
                  "activation": bound["activation_record"], "product_seed_ready": False}
    if output is not None:
        operator.write_object(output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
