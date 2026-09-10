#!/usr/bin/env python3
"""CK3-free contracts for the reusable phase-two seed capture runner."""

from __future__ import annotations

import copy
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace
import tempfile
import threading
import zipfile

import run_zg361_phase2_seed_capture as capture
sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "ck3_autonomous_player" / "src"),
)
import zg361_phase2_promotion_source_production_entry as production


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


class FakeIsolated:
    @staticmethod
    def installed_game_version() -> str:
        return "1.19.0.6"

    @staticmethod
    def tree_snapshot(root: Path) -> tuple[tuple[str, str], ...]:
        return tuple(
            (path.relative_to(root).as_posix(), sha256(path))
            for path in sorted(item for item in root.rglob("*") if item.is_file())
        )

    @staticmethod
    def snapshot_digest(snapshot: object) -> str:
        payload = json.dumps(snapshot, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


class FakeAcceptance:
    def __init__(self, executable: Path, calls: list[str]) -> None:
        self.CK3_EXE = executable
        self.ACTIVE_CK3_PID: int | None = None
        self.calls = calls

    def configure_runtime_userdir(self, profile: Path) -> None:
        self.calls.append("configure-userdir")
        require(profile.name == "profile", "runtime profile path drifted")

    def ck3_is_running(self) -> bool:
        return False


class FakeDriver:
    def __init__(self, calls: list[str]) -> None:
        self.calls = calls
        self.closed = False

    def close(self) -> None:
        self.calls.append("driver-close")
        self.closed = True


class FakeService:
    def __init__(
        self,
        calls: list[str],
        event_definition_key: str = capture.SEED_EVENT_DEFINITION_KEY,
        manager_pip_route: bool = False,
        checkpoint_path: Path | None = None,
    ) -> None:
        self.calls = calls
        self.event_definition_key = event_definition_key
        self.manager_pip_route = manager_pip_route
        self.event_state = "pip" if manager_pip_route else "final"
        self.played_character_id = 9001
        self.revision = 7
        self.paused = True
        self.speed = 1
        self.checkpoint_path = checkpoint_path
        self.checkpoint_episode_character_id: int | None = None
        self.date_raw = (
            capture.KNOWN_PRE_BOOTSTRAP_B2_PIP_EVENT["date_raw"]
            if manager_pip_route
            else 777
        )

    def snapshot(self) -> dict[str, object]:
        return {
            "snapshot_id": "fake-snapshot-7",
            "revision": self.revision,
            "date_raw": self.date_raw,
            "paused": self.paused,
            "map_ready": True,
            "speed": self.speed,
            "played_character": {"character_id": self.played_character_id},
            "active_event": (
                {"source": "native", "instance_id": 30, "option_count": 3}
                if self.event_state == "pip"
                else None
                if self.event_state == "continuation_pending"
                else {"instance_id": 44, "option_count": 1}
            ),
            "diagnostics": {
                "bridge_pid": 4321,
                "connection_generation": 1,
            },
        }

    def capabilities(self) -> dict[str, object]:
        return {
            "mode": "native-headless",
            "backend_id": "native-headless",
            "visual_fallback": False,
            "diagnostics": {
                "connected": True,
                "bridge_pid": 4321,
                "connection_generation": 1,
            },
        }

    def execute_step(self, step: str, **_kwargs: object) -> dict[str, object]:
        self.calls.append(f"execute:{step}")
        if step == "pause-map":
            self.paused = True
        elif step.startswith("set-speed-"):
            self.speed = int(step.rsplit("-", 1)[1])
        elif step == "resume-map":
            if self.event_state == "continuation_pending":
                self.event_state = "final"
                self.date_raw += 24
                self.revision += 1
                self.paused = True
            else:
                self.paused = False
        return {"accepted": True}

    def save_checkpoint(self, *, expected_revision: int) -> dict[str, object]:
        self.calls.append("save-checkpoint")
        require(expected_revision == self.revision, "save used stale revision")
        require(self.checkpoint_path is not None, "fake checkpoint path is absent")
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        self.checkpoint_path.write_bytes(b"SAV0101" + b"r129-transition")
        digest = sha256(self.checkpoint_path)
        return {
            "accepted": True,
            "checkpoint": {
                "status": "saved",
                "path": str(self.checkpoint_path.resolve()),
                "size": self.checkpoint_path.stat().st_size,
                "sha256": digest,
                "date_raw": self.date_raw,
                "episode_character_id": (
                    self.played_character_id
                    if self.checkpoint_episode_character_id is None
                    else self.checkpoint_episode_character_id
                ),
                "strategy": "fake-unit",
            },
        }

    def query_current_event_window_context_v1(
        self, event_id: int, **_kwargs: object
    ) -> dict[str, object]:
        self.calls.append("event-context")
        if self.event_state == "pip":
            require(event_id == 30, "manager fake queried wrong PIP instance")
            return {"current_event_window_context": _known_b2_pip_context()}
        return {
            "current_event_window_context": {
                "event_definition_key": self.event_definition_key
            }
        }

    def select_event_option(
        self,
        option_number: int,
        *,
        event_instance_id: int,
        expected_revision: int,
    ) -> dict[str, object]:
        self.calls.append(f"select-event-option:{option_number}")
        require(self.event_state == "pip", "manager fake selected final event")
        require(event_instance_id == 30, "manager fake selected wrong PIP instance")
        require(expected_revision == self.revision, "manager fake used stale revision")
        require(option_number == 3, "manager route did not refuse the PIP")
        self.event_state = "final"
        self.revision += 1
        if self.played_character_id == 9001:
            self.played_character_id = 9002
        return {
            "step": "select-event-option-3",
            "accepted": True,
            "status": "submitted",
            "option_number": 3,
            "option_index": 2,
            "event_selection": {
                "postcondition_verified": True,
                "old_event_instance_id": 30,
                "new_event_instance_id": 44,
                "selected_option_number": 3,
                "selected_native_option_index": 2,
            },
        }

    def query_loaded_feature_manifest_v1(
        self, **_kwargs: object
    ) -> dict[str, object]:
        self.calls.append("provider:manifest")
        return {"loaded_feature_manifest_ready": True}

    def query_zhongguo_b2_pip_snapshot_v1(
        self, *_args: object, **_kwargs: object
    ) -> dict[str, object]:
        self.calls.append("provider:b2")
        return {"status": "available", "readiness": {"ready": True}}

    def query_zhongguo_incident_snapshot_v1(
        self, *_args: object, **kwargs: object
    ) -> dict[str, object]:
        profile = str(kwargs["profile"])
        self.calls.append(f"provider:incident:{profile}")
        return {
            "status": "available",
            "readiness": {"ready": True},
            "terminal": {"kind": "na" if profile == "x" else "incident"},
        }

    def query_zhongguo_workforce_collective_snapshot_v1(
        self, *_args: object, **_kwargs: object
    ) -> dict[str, object]:
        self.calls.append("provider:workforce")
        return {"status": "available", "readiness": {"ready": True}}

    def query_zhongguo_ai_owned_case_snapshot_v1(
        self, *_args: object, **_kwargs: object
    ) -> dict[str, object]:
        self.calls.append("provider:ai-owned")
        return {"status": "available", "readiness": {"ready": True}}


class FakeZhongguoRunner:
    NATIVE_TITLE_COMMAND_TIMEOUT_S = 30.0
    EXPECTED_GAME_VERSION = "1.19.0.6"

    def __init__(
        self,
        fixture_source: Path,
        executable: Path,
        calls: list[str],
        keyboard_green: bool = True,
        process_exit: bool = False,
    ) -> None:
        self.fixture_source = fixture_source
        self.calls = calls
        self.keyboard_green = keyboard_green
        self.process_exit = process_exit
        self.supervisor: dict[str, object] | None = None
        self.supervisor_options: dict[str, object] = {}
        self.bootstrap_projection_kwargs: dict[str, object] = {}
        self.isolated = FakeIsolated()
        self.EXPECTED_EXE_SHA256 = sha256(executable)

    def bootstrap_userdir(
        self, profile: Path, product_source: Path, **kwargs: object
    ) -> dict[str, object]:
        self.calls.append("bootstrap")
        self.bootstrap_projection_kwargs = dict(kwargs)
        product = profile / "mod-content" / "zhongguo_361"
        fixture = profile / "mod-content" / "fixture"
        shutil.copytree(product_source, product)
        shutil.copytree(self.fixture_source, fixture)
        for path in (
            profile / "mod",
            profile / "logs",
            profile / "save games",
        ):
            path.mkdir(parents=True, exist_ok=True)
        (profile / "logs" / "debug.log").write_text(
            "product and fixture mounted once\n", encoding="utf-8"
        )
        snapshots = {
            "product": self.isolated.tree_snapshot(product),
            "fixture": self.isolated.tree_snapshot(fixture),
        }
        hashes = {
            name: self.isolated.snapshot_digest(snapshot)
            for name, snapshot in snapshots.items()
        }
        return {
            "targets": {"product": product, "fixture": fixture},
            "tree_snapshots": snapshots,
            "tree_sha256": hashes,
            "enabled_mods": list(capture.EXPECTED_ENABLED_MODS),
            "manifest": {
                "projection": kwargs.get("product_projection", "broad"),
                "tree_sha256": hashes["product"],
            },
        }

    def make_spec(self, state_dir: Path, _game_dir: Path) -> SimpleNamespace:
        self.calls.append("make-spec")
        return SimpleNamespace(state_dir=state_dir, profile_dir=state_dir / "profile")

    def resolve_native_bridge_config(
        self, _dll: Path, _injector: Path, pipe: str
    ) -> SimpleNamespace:
        self.calls.append("resolve-bridge")
        return SimpleNamespace(pipe_name=pipe)

    def preflight(self, **_kwargs: object) -> dict[str, object]:
        """Fail loudly if the seed gate regresses to the generic acceptance gate."""

        self.calls.append("generic-preflight")
        raise AssertionError(
            "phase-two seed preflight must not invoke generic acceptance preflight"
        )

    def start_phase2_native_session_supervisor(
        self, _spec: object, _bridge: object, **kwargs: object
    ) -> dict[str, object]:
        self.calls.append("supervisor-start")
        self.supervisor_options = dict(kwargs)
        self.supervisor = {
            "stop_event": threading.Event(),
            "session_done": threading.Event(),
            "session_state": {"report": None, "error": None},
            "session_thread": threading.Thread(
                target=lambda: None,
                name="fake-phase2-native-session",
            ),
        }
        return self.supervisor

    def wait_for_phase2_native_session_binding(
        self,
        _service: object,
        _supervisor: object,
        _artifacts: Path,
        **kwargs: object,
    ) -> dict[str, object]:
        self.calls.append("transport-binding")
        require(kwargs["timeout_s"] == 12.0, "binding timeout drifted")
        return {"bridge_pid": 4321, "connection_generation": 1}

    def handle_phase2_optional_legal_consent(
        self, profile: Path, artifacts: Path
    ) -> dict[str, object]:
        self.calls.append("legal-consent")
        require(profile.name == "profile", "legal gate escaped isolated profile")
        require(artifacts.name == "artifacts", "legal evidence root drifted")
        return {
            "schema_version": 1,
            "result": "GREEN",
            "state": "no_modal",
            "authorized_click_count": 0,
            "real_profile_modified": False,
            "ocr_used": True,
            "image_used": True,
        }

    def verify_runtime_load_order(
        self, profile: Path, bootstrap: dict[str, object]
    ) -> list[str]:
        self.calls.append("single-mount-gate")
        targets = bootstrap["targets"]
        require(isinstance(targets, dict), "fake bootstrap targets malformed")
        return [str(Path(targets[name]).resolve()) for name in ("product", "fixture")]

    def native_loader_smoke_readiness(
        self, _service: object, _artifacts: Path, **kwargs: object
    ) -> dict[str, object]:
        self.calls.append("native-readiness")
        require(kwargs["tracked_ck3_pid"] == 4321, "native PID drifted")
        require(kwargs["timeout_s"] == 13.0, "native timeout drifted")
        return {"result": "GREEN"}

    def scan_loader_error_log(
        self, _profile: Path, _artifacts: Path
    ) -> dict[str, object]:
        self.calls.append("loader-error-scan")
        return {"result": "GREEN", "matches": []}

    def stop_phase2_native_session_supervisor(
        self, _supervisor: object, _artifacts: Path, **kwargs: object
    ) -> dict[str, object]:
        self.calls.append("supervisor-cleanup")
        require(kwargs["initial_pid"] == 4321, "cleanup PID drifted")
        require(
            kwargs["expected_pipe"].startswith(capture.PIPE_PREFIX),
            "cleanup pipe drifted",
        )
        return {
            "schema_version": 1,
            "result": "GREEN",
            "checks": {"supervisor_stopped": True},
            "failed_checks": [],
        }


class FakeSeed:
    def __init__(
        self,
        calls: list[str],
        seed_purpose: str = capture.DEFAULT_SEED_PURPOSE,
    ) -> None:
        self.calls = calls
        self.seed_purpose = seed_purpose
        self.materialize_kwargs: dict[str, object] | None = None
        self.manager_entry_override: dict[str, object] | None = None
        self.candidate_entry_override: dict[str, object] | None = None
        self.last_capture_result: dict[str, object] | None = None

    def capture_mcp_evidence(
        self, service: object, output: Path
    ) -> dict[str, object]:
        self.calls.append("seed-capture-mcp")
        output.mkdir(parents=True)
        files = {
            "event_context_path": output / "event-context.json",
            "paused_snapshot_path": output / "paused-snapshot.json",
            "event_close_path": output / "event-close.json",
            "checkpoint_response_path": output / "checkpoint-response.json",
        }
        for path in files.values():
            capture.write_json(path, {"result": "GREEN"})
        result: dict[str, object] = {
            **{name: str(path) for name, path in files.items()},
        }
        if self.seed_purpose == capture.DEFAULT_SEED_PURPOSE:
            result["domain_query_matrix"] = {
                "schema_version": 1,
                "b2_pip_owner_character_id": 9200,
                "incident_owner_character_id": 9200,
                "workforce_owner_character_id": 9200,
                "ai_owned_case_owner_character_id": 9200,
                "ai_owned_case_subject_character_id": 9001,
            }
        else:
            manager_id = getattr(service, "played_character_id", 9001)
            result["played_character_id"] = manager_id
            result["manager_entry"] = (
                dict(self.manager_entry_override)
                if self.manager_entry_override is not None
                else {
                    "manager_character_id": manager_id,
                    "reviewable_subject_character_id": (
                        9001 if manager_id == 9002 else 9002
                    ),
                }
            )
        self.last_capture_result = result
        return result

    def materialize_candidate(self, **kwargs: object) -> dict[str, object]:
        self.calls.append("candidate-materialize")
        self.materialize_kwargs = dict(kwargs)
        output = Path(kwargs["output_dir"])
        output.mkdir(parents=True)
        contract_path = output / "seed-contract.json"
        result: dict[str, object] = {
            "result": "GREEN",
            "ready": True,
            "contract_path": str(contract_path),
        }
        if self.seed_purpose == capture.DEFAULT_SEED_PURPOSE:
            capture.write_json(contract_path, {"ready": True})
            result["provider_baseline_ready"] = True
        else:
            require(
                isinstance(self.last_capture_result, dict),
                "manager candidate lacks typed capture input",
            )
            typed_entry = self.last_capture_result.get("manager_entry")
            require(isinstance(typed_entry, dict), "manager typed entry is absent")
            candidate_entry = (
                dict(self.candidate_entry_override)
                if self.candidate_entry_override is not None
                else dict(typed_entry)
            )
            played_id = self.last_capture_result.get("played_character_id")
            capture.write_json(
                contract_path,
                {
                    "kind": "zg361_phase2_player_manager_paused_seed",
                    "ready": True,
                    "saved_state": {"played_character_id": played_id},
                    "manager_entry": candidate_entry,
                },
            )
            result["played_character_id"] = played_id
            result["manager_entry"] = candidate_entry
        return result


class FakeBridgeUnavailableError(RuntimeError):
    pass


class FakePreSubmissionRevisionMismatchError(FakeBridgeUnavailableError):
    pass


class FakeLoaderStageError(RuntimeError):
    def __init__(self, message: str, evidence: dict[str, object]) -> None:
        super().__init__(message)
        self.evidence = evidence


class Fixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.clean = root / "clean-source"
        self.attempt = root / "attempt"
        self.artifacts = self.attempt / "artifacts"
        self.game = root / "game"
        self.old_save = root / "old-save.ck3"
        self.settings_template = root / "known-good" / "pdx_settings.txt"
        self.dll = root / "bridge.dll"
        self.injector = root / "injector.exe"
        self.source_zip = self.attempt / "head-source.zip"
        self.git_sha = "a" * 40
        self.pipe = capture.PIPE_PREFIX + "zg361_phase2_seed_fake"
        product = self.clean / "mod_zhongguo_style"
        seed_fixture = (
            self.clean
            / "tools"
            / "fixtures"
            / "zg361_phase2_seed_bootstrap"
        )
        product.mkdir(parents=True)
        seed_fixture.mkdir(parents=True)
        (product / "descriptor.mod").write_text("name=product\n", encoding="utf-8")
        for relative in capture.CRITICAL_B2_PRODUCT_PATHS:
            provider = product / relative
            provider.parent.mkdir(parents=True, exist_ok=True)
            provider.write_bytes(f"fixture:{relative}\n".encode("utf-8"))
        (seed_fixture / "descriptor.mod").write_text(
            "name=fixture\n", encoding="utf-8"
        )
        manager_fixture = (
            self.clean
            / "tools"
            / "fixtures"
            / "zg361_phase2_manager_seed_bootstrap"
        )
        manager_fixture.mkdir(parents=True)
        (manager_fixture / "descriptor.mod").write_text(
            "name=manager-fixture\n", encoding="utf-8"
        )
        self.old_save.write_bytes(b"frozen-real-save")
        contract = {
            "kind": "zg361_phase2_paused_seed",
            "status": "ready",
            "source": {
                "absolute_save": str(self.old_save),
                "sha256": sha256(self.old_save),
            }
        }
        contract_path = self.clean / "tools" / "zg361_phase2_seed_contract.json"
        contract_path.parent.mkdir(parents=True, exist_ok=True)
        contract_path.write_text(json.dumps(contract), encoding="utf-8")
        manager_contract = {
            "kind": "zg361_phase2_player_manager_seed_request",
            "seed_purpose": "player-manager",
            "status": "blocked_live_capture_required",
            "source": dict(contract["source"]),
            "saved_state": {
                "date_raw": 53147016,
                "played_character_id": 9001,
            },
            "player_transition_contract": {
                "handoff_mode": "post_exact_pip_load_gui",
                "trigger_effect_key": capture.MANAGER_SEED_PREEMPTIVE_EFFECT,
                "activation_surface": (
                    "load_safe_scripted_gui_terminal_pip_retry"
                ),
                "hidden_carrier_event_definition_key": (
                    capture.MANAGER_SEED_HANDOFF_CARRIER_EVENT_DEFINITION_KEY
                ),
                "post_switch_event_definition_key": (
                    capture.MANAGER_SEED_EVENT_DEFINITION_KEY
                ),
                "source_character_id": 9001,
                "target_character_id": 9002,
                "completion_date_raw": 53147040,
                "allowed_prebootstrap_event_definition_keys": ["zg361b2.40"],
                "activation_event_definition_key": "zg361b2.40",
                "activation_event_date_raw": 53147040,
                "activation_event_selected_option_number": 3,
                "activation_event_selected_native_option_index": 2,
                "activation_event_outcome": "refuse",
                "activation_signal_variable": "zg361_b2_m015_state",
                "activation_signal_preselection_value": 1,
                "activation_signal_value": 5,
                "fixture_gui_retry_duration_seconds": 0.5,
                "post_activation_paused_settle_seconds": 5.0,
                "forbids_timeline_resume_after_activation_event_drain": True,
                "requires_exact_activation_event_drain": True,
                "requires_completion_at_exact_date": True,
                "forbids_other_prebootstrap_event_drains": True,
                "preempts_destructive_later_event": True,
                "timeline_speed": 5,
                "destructive_later_event_definition_key": (
                    "ep3_interactions_events.0630"
                ),
                "destructive_later_event_date_raw": 53147256,
                "requires_source_save_hash_match": True,
                "requires_source_saved_player_identity": True,
                "requires_typed_post_switch_player": True,
                "requires_post_switch_manager_revalidation": True,
                "requires_final_manager_entry_identity_match": True,
                "fixture_set_player_character_count": 1,
                "fixture_creates_character": False,
                "fixture_creates_title": False,
                "fixture_creates_relationship": False,
                "fixture_calls_product_b1": False,
                "fixture_writes_product_receipts": False,
            },
            "transition_checkpoint_contract": {
                "kind": capture.MANAGER_TRANSITION_CHECKPOINT_KIND,
                "final_seed_ready": False,
                "clears_product_state": False,
                "writes_product_receipt": False,
                "continuation_maximum_date_raw": 53147064,
                "continuation_timeline_speed": 5,
                "continuation_forbids_unregistered_event_drains": True,
            },
        }
        manager_contract_path = (
            self.clean / "tools" / "zg361_phase2_manager_seed_contract.json"
        )
        manager_contract_path.write_text(
            json.dumps(manager_contract), encoding="utf-8"
        )
        executable = self.game / "binaries" / "ck3.exe"
        rules = self.game / "game" / "common" / "game_rules" / "00_game_rules.txt"
        executable.parent.mkdir(parents=True)
        rules.parent.mkdir(parents=True)
        executable.write_bytes(b"fake-ck3-executable")
        rules.write_text("game_rules = {}\n", encoding="utf-8")
        self.dll.write_bytes(b"fake-bridge-dll")
        self.injector.write_bytes(b"fake-injector")
        _write_full_settings(self.settings_template)
        _write_warm_shadercache(self.settings_template.parent)
        self.attempt.mkdir(parents=True)
        self.rebuild_source_zip()

    def use_direct_manager_contract(self) -> None:
        path = self.clean / "tools" / "zg361_phase2_manager_seed_contract.json"
        contract = json.loads(path.read_text(encoding="utf-8"))
        contract["saved_state"] = {
            "date_raw": None,
            "played_character_id": 9001,
        }
        contract["player_transition_contract"] = {
            "handoff_mode": capture.MANAGER_DIRECT_ENTRY_MODE,
            "trigger_effect_key": capture.MANAGER_SEED_PREEMPTIVE_EFFECT,
            "activation_surface": "load_safe_gui_direct_manager",
            "entry_event_definition_key": (
                capture.MANAGER_SEED_EVENT_DEFINITION_KEY
            ),
            "source_character_id": 9001,
            "target_character_id": 9001,
            "target_source": "already_played_character",
            "owner_scope": capture.MANAGER_SEED_OWNER_SCOPE,
            "subject_scope": capture.MANAGER_SEED_SUBJECT_SCOPE,
            "source_date_binding": "first_paused_typed_snapshot",
            "allowed_prebootstrap_event_definition_keys": [],
            "requires_exact_activation_event_drain": False,
            "requires_final_event_at_bound_source_date": True,
            "forbids_other_prebootstrap_event_drains": True,
            "forbids_any_prebootstrap_event_input": True,
            "timeline_speed": 5,
            "timeline_speed_only_if_advancement_required": True,
            "destructive_later_event_definition_key": (
                "ep3_interactions_events.0630"
            ),
            "requires_destructive_event_zero_input_red": True,
            "requires_source_save_hash_match": True,
            "requires_source_saved_player_identity": True,
            "requires_typed_final_player": True,
            "requires_manager_entry_revalidation": True,
            "requires_final_manager_entry_identity_match": True,
            "fixture_set_player_character_count": 0,
            "fixture_creates_character": False,
            "fixture_creates_title": False,
            "fixture_creates_relationship": False,
            "fixture_calls_product_b1": False,
            "fixture_writes_product_receipts": False,
        }
        path.write_text(json.dumps(contract), encoding="utf-8")
        self.rebuild_source_zip()

    def rebuild_source_zip(self) -> None:
        with zipfile.ZipFile(self.source_zip, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(
                item for item in self.clean.rglob("*") if item.is_file()
            ):
                archive.write(path, path.relative_to(self.clean).as_posix())

    def config(
        self, seed_purpose: str = capture.DEFAULT_SEED_PURPOSE
    ) -> capture.CaptureConfig:
        return capture.CaptureConfig(
            clean_source=self.clean,
            attempt_dir=self.attempt,
            artifacts_dir=self.artifacts,
            source_zip=self.source_zip,
            frozen_git_sha=self.git_sha,
            game_dir=self.game,
            bridge_dll=self.dll,
            bridge_injector=self.injector,
            pipe_name=self.pipe,
            seed_purpose=seed_purpose,
            loader_timeout_seconds=60.0,
            native_readiness_timeout_seconds=13.0,
            event_timeout_seconds=14.0,
            binding_timeout_seconds=12.0,
            keyboard_watchdog_interval_seconds=0.01,
            profile_settings_template=self.settings_template,
        )

    def runtime(
        self,
        calls: list[str],
        *,
        parser_red: bool = False,
        process_exit: bool = False,
        seed_purpose: str = capture.DEFAULT_SEED_PURPOSE,
        event_definition_key: str | None = None,
        manager_pip_route: bool | None = None,
    ) -> capture.RuntimeBindings:
        acceptance = FakeAcceptance(self.game / "binaries" / "ck3.exe", calls)
        zgrun = FakeZhongguoRunner(
            self.clean
            / "tools"
            / "fixtures"
            / str(
                capture.SEED_PURPOSE_SPECS[seed_purpose]["fixture_directory"]
            ),
            self.game / "binaries" / "ck3.exe",
            calls,
            process_exit=process_exit,
        )
        service = FakeService(
            calls,
            event_definition_key=(
                event_definition_key
                if event_definition_key is not None
                else str(
                    capture.SEED_PURPOSE_SPECS[seed_purpose][
                        "event_definition_key"
                    ]
                )
            ),
            manager_pip_route=(
                manager_pip_route
                if manager_pip_route is not None
                else (
                    seed_purpose == capture.MANAGER_SEED_PURPOSE
                    and event_definition_key is None
                )
            ),
            checkpoint_path=self.root / "fake-native-checkpoint.ck3",
        )

        def driver_factory(*_args: object, **_kwargs: object) -> FakeDriver:
            calls.append("driver-open")
            return FakeDriver(calls)

        def loader_stage(
            _logs: Path, progress: Path, **kwargs: object
        ) -> dict[str, object]:
            calls.append("loader-stage")
            require(kwargs["timeout_seconds"] == 60.0, "loader timeout drifted")
            require(
                kwargs["fatal_stall_seconds"] == 45.0,
                "loader parser fail-fast drifted",
            )
            probe = kwargs.get("native_session_probe")
            require(callable(probe), "native session early-exit probe missing")
            if process_exit:
                require(
                    zgrun.supervisor is not None,
                    "fake native supervisor was not retained",
                )
                state = zgrun.supervisor["session_state"]
                require(isinstance(state, dict), "fake session state malformed")
                state["report"] = {
                    "kind": "ck3_native_headless_session",
                    "exit_reason": "process_exit",
                    "process_exit_code": 1,
                    "pid": 4321,
                    "ok": False,
                }
                zgrun.supervisor["session_done"].set()
                terminal = probe()
                require(
                    isinstance(terminal, dict)
                    and terminal.get("terminal") is True,
                    "native process-exit probe did not publish a terminal",
                )
                evidence = {
                    "result": "RED",
                    "state": "native_session_process_exit",
                    "stage": "awaiting_logs",
                    "database_init_seen": False,
                    "event_wait_authorized": False,
                    "native_session": terminal,
                    "exit_reason": "process_exit",
                    "process_exit_code": 1,
                    "process_exit_nonzero": True,
                }
                capture.append_jsonl(progress, evidence)
                raise FakeLoaderStageError(
                    "managed native_session exited before loader readiness",
                    evidence,
                )
            if parser_red:
                evidence = {
                    "result": "RED",
                    "state": "loader_parse_red",
                    "stage": "database_init",
                    "fatal_error_count": 4,
                    "fatal_errors": [{"fingerprint_sha256": "f" * 64}],
                }
                capture.append_jsonl(progress, evidence)
                raise FakeLoaderStageError("parser RED", evidence)
            evidence = {
                "result": "GREEN",
                "state": "loader_stage_ready",
                "stage": "load_save",
            }
            capture.append_jsonl(progress, evidence)
            return evidence

        def keyboard_layout_attestor(
            tracked_pid: int, artifacts: Path, stem: str
        ) -> dict[str, object]:
            calls.append("hkl-us-english")
            require(tracked_pid == 4321, "HKL watchdog PID drifted")
            evidence = {
                "result": "GREEN",
                "observed_hkl": "0x04090409",
                "restore_requested": False,
                "desktop_input_sent": False,
                "window_focus_changed": False,
            }
            capture.write_json(artifacts / f"{stem}.json", evidence)
            return evidence

        return capture.RuntimeBindings(
            acceptance=acceptance,
            zgrun=zgrun,
            seed=FakeSeed(calls, seed_purpose),
            driver_factory=driver_factory,
            service_factory=lambda _driver: service,
            bridge_unavailable_error=FakeBridgeUnavailableError,
            pre_submission_revision_mismatch_error=(
                FakePreSubmissionRevisionMismatchError
            ),
            loader_stage_error=FakeLoaderStageError,
            wait_for_loader_stage=loader_stage,
            keyboard_layout_attestor=keyboard_layout_attestor,
            sleep=lambda _seconds: None,
        )


class FakeTime:
    def __init__(self) -> None:
        self.value = 0.0

    def clock(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.value += seconds


def _write_full_settings(path: Path, *, lines: int = 24) -> None:
    body = [
        '"game"={',
        '\t"cloud_save"={ version=0 enabled=no }',
        '}',
        '"Graphics"={',
        '\t"display_mode"={ version=0 value="fullscreen" }',
        '}',
        '"System"={',
        '\t"language"={ version=0 value="l_simp_chinese" }',
        '}',
    ]
    body.extend(f'"padding_{index}"={{ version=0 value={index} }}' for index in range(lines))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(body) + "\n", encoding="utf-8")


def _write_warm_shadercache(root: Path) -> Path:
    """Create the smallest valid DX11 cache pair for profile-gate tests."""

    cache = root / "shadercache"
    for lane, stem in (("ps_5_0", "0000000000000001"), ("vs_5_0", "0000000000000002")):
        lane_dir = cache / "dx11" / lane
        lane_dir.mkdir(parents=True, exist_ok=True)
        (lane_dir / f"{stem}.bin").write_bytes(b"compiled-shader")
        (lane_dir / f"{stem}.scache").write_bytes(b"shader-cache-record")
    return cache


def test_game_dir_resolution_prefers_steam_and_preserves_explicit() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        steam = root / "SteamLibrary"
        install = steam / "steamapps" / "common" / "CK3-Actual"
        (install / "binaries").mkdir(parents=True)
        (install / "game" / "common" / "game_rules").mkdir(parents=True)
        (install / "binaries" / "ck3.exe").write_bytes(b"exe")
        (install / "game" / "common" / "game_rules" / "00_game_rules.txt").write_text(
            "rules = {}\n", encoding="utf-8"
        )
        apps = steam / "steamapps"
        (apps / "appmanifest_1158310.acf").write_text(
            '"AppState" {\n\t"installdir" "CK3-Actual"\n}\n',
            encoding="utf-8",
        )
        previous_game = os.environ.pop("XAR_CK3_GAME_DIR", None)
        previous_steam = os.environ.get("XAR_STEAM_DIR")
        os.environ["XAR_STEAM_DIR"] = str(steam)
        try:
            selected, source, candidates = capture.resolve_ck3_game_dir()
            require(selected == install.resolve(), "Steam install was not selected")
            require(source == "steam-library", "Steam provenance was not recorded")
            require(
                any(row["path"] == str(install.resolve()) and row["valid"] is True for row in candidates),
                "valid Steam candidate was not retained",
            )
            explicit = root / "operator-custom"
            selected_explicit, source_explicit, rows_explicit = capture.resolve_ck3_game_dir(explicit)
            require(selected_explicit == explicit.resolve(), "explicit game path was replaced")
            require(source_explicit == "explicit-cli", "explicit path provenance drifted")
            require(rows_explicit[0]["valid"] is False, "invalid explicit path was silently substituted")
        finally:
            if previous_game is not None:
                os.environ["XAR_CK3_GAME_DIR"] = previous_game
            if previous_steam is None:
                os.environ.pop("XAR_STEAM_DIR", None)
            else:
                os.environ["XAR_STEAM_DIR"] = previous_steam


def test_game_dir_resolution_never_falls_back_to_repository() -> None:
    """A missing Steam install must be a typed RED, not a repo-path launch."""

    previous_game = os.environ.pop("XAR_CK3_GAME_DIR", None)
    original_roots = capture._steam_library_roots
    capture._steam_library_roots = lambda: []
    try:
        try:
            capture.resolve_ck3_game_dir()
        except capture.SeedCaptureError as error:
            require(
                "no valid SteamLibrary install" in str(error),
                "automatic game-dir failure was not typed",
            )
            require(
                error.evidence.get("automatic_requires_steam") is True,
                "repository fallback evidence was not recorded",
            )
        else:
            raise AssertionError("automatic resolver silently selected repository copy")
    finally:
        capture._steam_library_roots = original_roots
        if previous_game is not None:
            os.environ["XAR_CK3_GAME_DIR"] = previous_game


def test_profile_settings_requires_explicit_template_and_records_auto_candidate() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        fixture = Fixture(root)
        template = root / "known-good" / "pdx_settings.txt"
        _write_full_settings(template)
        _write_warm_shadercache(template.parent)
        config = replace(fixture.config(), profile_settings_template=template)
        evidence = capture.prepare_profile_settings(config)
        require(evidence["result"] == "GREEN", "explicit settings template was not copied")
        destination = config.profile_dir / "pdx_settings.txt"
        require(destination.is_file(), "settings destination was not created")
        require(evidence["destination_sha256"] == sha256(destination), "settings hash evidence drifted")

        auto_root = root / "operator-profile"
        auto_settings = auto_root / "pdx_settings.txt"
        _write_full_settings(auto_settings)
        previous_auto = os.environ.get("XAR_REAL_CK3_PROFILE")
        os.environ["XAR_REAL_CK3_PROFILE"] = str(auto_root)
        try:
            fresh = replace(fixture.config(), attempt_dir=root / "attempt-auto")
            fresh = replace(fresh, artifacts_dir=fresh.attempt_dir / "artifacts")
            fresh = replace(fresh, profile_settings_template=None)
            auto_evidence = capture.prepare_profile_settings(fresh)
        finally:
            if previous_auto is None:
                os.environ.pop("XAR_REAL_CK3_PROFILE", None)
            else:
                os.environ["XAR_REAL_CK3_PROFILE"] = previous_auto
        require(
            auto_evidence["result"] == "AVAILABLE_NOT_SELECTED",
            "operator settings were copied without an explicit pin",
        )
        require(
            auto_evidence["auto_candidate"]["selected"] is False,
            "auto settings candidate was not marked unselected",
        )
        require(
            not (fresh.profile_dir / "pdx_settings.txt").exists(),
            "implicit profile settings copy changed isolated state",
        )


def test_formal_profile_assets_fail_typed_for_missing_template_or_cache() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        fixture = Fixture(root)
        missing = root / "missing" / "pdx_settings.txt"
        try:
            capture.prepare_profile_settings(
                replace(fixture.config(), profile_settings_template=missing)
            )
        except capture.SeedCaptureError as error:
            require(
                error.evidence.get("result") == "BLOCKED",
                "missing settings did not return typed BLOCKED evidence",
            )
            require(error.evidence.get("profile_ready") is False,
                    "missing settings was marked ready")
        else:
            raise AssertionError("missing settings template was accepted")

        no_cache = root / "no-cache" / "pdx_settings.txt"
        _write_full_settings(no_cache)
        try:
            capture.prepare_profile_settings(
                replace(fixture.config(), profile_settings_template=no_cache)
            )
        except capture.SeedCaptureError as error:
            require(
                "shadercache" in str(error).lower(),
                "missing cache failure omitted cache reason",
            )
            require(error.evidence.get("result") == "BLOCKED",
                    "missing cache did not return typed BLOCKED evidence")
        else:
            raise AssertionError("settings without a warm cache was accepted")


def test_formal_profile_assets_reject_preexisting_unpinned_cache() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        fixture = Fixture(root)
        config = fixture.config()
        destination_cache = config.profile_dir / "shadercache" / "dx11" / "ps_5_0"
        destination_cache.mkdir(parents=True)
        (destination_cache / "stale.bin").write_bytes(b"stale")
        try:
            capture.prepare_profile_settings(config)
        except capture.SeedCaptureError as error:
            require(error.evidence.get("result") == "BLOCKED",
                    "preexisting cache mismatch was not typed BLOCKED")
            require("refusing to merge" in str(error).lower(),
                    "preexisting cache refusal was not recorded")
        else:
            raise AssertionError("preexisting unpinned cache was merged")


def test_formal_profile_assets_reject_copy_manifest_drift() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        fixture = Fixture(root)
        original_copytree = capture.shutil.copytree

        def corrupt_copytree(*args: object, **kwargs: object) -> str:
            result = original_copytree(*args, **kwargs)
            destination = Path(str(args[1])) if len(args) > 1 else Path()
            if destination.name == "shadercache":
                target = destination / "dx11" / "ps_5_0" / "0000000000000001.bin"
                target.write_bytes(b"tampered-after-copy")
            return result

        capture.shutil.copytree = corrupt_copytree  # type: ignore[assignment]
        try:
            try:
                capture.prepare_profile_settings(fixture.config())
            except capture.SeedCaptureError as error:
                require(error.evidence.get("result") == "BLOCKED",
                        "copy drift did not return typed BLOCKED evidence")
                require("manifest equality" in str(error).lower(),
                        "copy drift reason was not persisted")
            else:
                raise AssertionError("tampered shadercache copy was accepted")
        finally:
            capture.shutil.copytree = original_copytree  # type: ignore[assignment]


def test_tree_manifest_records_byte_sizes_under_bytes_key() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        item = root / "nested" / "shader.bin"
        item.parent.mkdir(parents=True)
        item.write_bytes(b"12345")
        manifest = capture.tree_manifest(root)
        require(manifest["files"] == [{
            "path": "nested/shader.bin",
            "bytes": 5,
            "sha256": sha256(item),
        }], "tree manifest did not preserve bytes field")
        require("size" not in manifest["files"][0],
                "tree manifest retained the stale size field")


def test_release_bridge_bundle_provenance_binds_pair_and_rejects_debug() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        fixture = Fixture(root)
        manifest = root / "bridge-bundle.json"
        payload = {
            "schema_version": 1,
            "kind": "offline_native_bridge_fresh_bundle_audit",
            "status": "built_skip_tests",
            "built_at_local": "2026-09-03T10:52:00+08:00",
            "source": {
                "git_head": "b" * 40,
                "fingerprint_sha256": "c" * 64,
            },
            "build": {
                "build_dir": str(root / "release-build"),
                "generator": "Ninja",
                "configuration": "Release",
                "compiler": "MSVC",
                "compile_link": "success",
                "tests_ran": False,
            },
            "cmake_flags": {"XAR_CK3_ENABLE_PHASE2": False},
            "artifacts": {
                "dll": {
                    "path": str(fixture.dll),
                    "bytes": fixture.dll.stat().st_size,
                    "sha256": sha256(fixture.dll).upper(),
                },
                "injector": {
                    "path": str(fixture.injector),
                    "bytes": fixture.injector.stat().st_size,
                    "sha256": sha256(fixture.injector).upper(),
                },
                "pe_imports": {"debug_crt_present": False},
            },
        }
        manifest.write_text(json.dumps(payload), encoding="utf-8")
        config = replace(fixture.config(), bridge_bundle_manifest=manifest)
        provenance = capture.bridge_bundle_provenance(config)
        require(isinstance(provenance, dict), "Release provenance was not returned")
        require(provenance["build_type"] == "Release", "build type was not bound")
        require(provenance["matches"] == {
            "dll_sha256": True,
            "dll_bytes": True,
            "injector_sha256": True,
            "injector_bytes": True,
        }, "bridge pair hash/size match was not recorded")
        payload["build"]["configuration"] = "Debug"
        manifest.write_text(json.dumps(payload), encoding="utf-8")
        try:
            capture.bridge_bundle_provenance(config)
        except capture.SeedCaptureError as error:
            require("requires a Release bridge bundle" in str(error), "Debug bundle rejection was mistyped")
        else:
            raise AssertionError("Debug bridge bundle was accepted")


def test_phase2_frontend_first_options_reach_seed_supervisor() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        fixture = Fixture(root)
        calls: list[str] = []
        previous_auto = os.environ.get("XAR_REAL_CK3_PROFILE")
        os.environ["XAR_REAL_CK3_PROFILE"] = str(root / "no-auto-profile")
        try:
            config = replace(
                fixture.config(),
                frontend_first_load_save_name="phase2_seed",
                frontend_first_timeout_seconds=12.5,
            )
            runtime = fixture.runtime(calls)
            report = capture.run_capture(config, runtime=runtime)
        finally:
            if previous_auto is None:
                os.environ.pop("XAR_REAL_CK3_PROFILE", None)
            else:
                os.environ["XAR_REAL_CK3_PROFILE"] = previous_auto
        require(report["result"] == "GREEN", "frontend-first fake capture was RED")
        zgrun = runtime.zgrun
        require(
            zgrun.supervisor_options
            == {
                "frontend_first_load_save_name": "phase2_seed",
                "frontend_first_timeout_seconds": 12.5,
            },
            "frontend-first options did not reach the phase2 supervisor",
        )
        require(
            report["frontend_first_warmup"]["save_materialization"]["load_save_name"]
            == "phase2_seed",
            "frontend-first save was not materialized under the requested basename",
        )
        require("supervisor-start" in calls, "phase2 supervisor was not started")


def test_real_phase2_frontend_first_option_validation() -> None:
    import run_zhongguo_acceptance as zgrun

    zgrun._validate_phase2_frontend_first_options(
        "phase2_seed",
        12.5,
        phase2_runtime_mode=True,
    )
    for invalid_timeout in (float("nan"), float("inf"), float("-inf")):
        try:
            zgrun._validate_phase2_frontend_first_options(
                "phase2_seed",
                invalid_timeout,
                phase2_runtime_mode=True,
            )
        except zgrun.acceptance.RunnerError as error:
            require(
                "finite and positive" in str(error),
                "frontend-first timeout rejection was mistyped",
            )
        else:
            raise AssertionError(
                "non-finite frontend-first timeout passed real runner validation"
            )


def test_real_phase2_frontend_first_binding_uses_first_mcp_generation() -> None:
    import run_zhongguo_acceptance as zgrun

    class BindingService:
        def __init__(self, *, bridge_pid: int, generation: object) -> None:
            self.bridge_pid = bridge_pid
            self.generation = generation

        def capabilities(self) -> dict[str, object]:
            return {
                "mode": zgrun.NATIVE_BRIDGE_MODE,
                "backend_id": zgrun.NATIVE_BRIDGE_MODE,
                "visual_fallback": False,
                "diagnostics": {
                    "connected": True,
                    "bridge_pid": self.bridge_pid,
                    "connection_generation": self.generation,
                },
            }

    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        warmup_path = root / "frontend-first-warmup.json"
        warmup_path.write_text(
            json.dumps(
                {
                    "status": "ready",
                    "warmup_bridge": {
                        "mode": "disabled",
                        "dll_injection": False,
                        "mcp": False,
                    },
                    "warmup_pid": 1111,
                    "final_pid": 4321,
                }
            ),
            encoding="utf-8",
        )
        session_done = threading.Event()
        stop_thread = threading.Event()
        session_thread = threading.Thread(target=stop_thread.wait)
        session_thread.start()
        supervisor = {
            "session_done": session_done,
            "session_state": {},
            "session_thread": session_thread,
            "frontend_first_enabled": True,
            "frontend_first_load_save_name": "phase2_seed",
            "frontend_first_evidence_path": str(warmup_path),
        }
        try:
            green_artifacts = root / "green"
            green_artifacts.mkdir()
            binding = zgrun.wait_for_phase2_native_session_binding(
                BindingService(bridge_pid=4321, generation=1),
                supervisor,
                green_artifacts,
                timeout_s=0.1,
                poll_interval_s=0.0,
            )
            require(binding["bridge_pid"] == 4321, "final PID binding drifted")
            require(
                binding["connection_generation"] == 1,
                "first MCP connection was not accepted as generation one",
            )
            require(
                binding["checks"]["frontend_first_warmup_ready"] is True,
                "ready frontend warm-up was not proven",
            )
            require(
                binding["checks"]["frontend_first_final_pid_matches"] is True,
                "final injected PID was not matched",
            )
            require(
                binding["checks"]["initial_connection_generation_one"] is True,
                "frontend-first binding lost the initial generation invariant",
            )

            red_cases = (
                ("wrong-final-pid", 9999, 1, "frontend_first_final_pid_matches"),
                ("invalid-generation", 4321, 0, "initial_connection_generation_one"),
            )
            for label, bridge_pid, generation, failed_check in red_cases:
                red_artifacts = root / label
                red_artifacts.mkdir()
                try:
                    zgrun.wait_for_phase2_native_session_binding(
                        BindingService(
                            bridge_pid=bridge_pid,
                            generation=generation,
                        ),
                        supervisor,
                        red_artifacts,
                        timeout_s=0.02,
                        poll_interval_s=0.0,
                    )
                except zgrun.acceptance.RunnerError as error:
                    require(
                        failed_check in str(error),
                        f"{label} RED did not identify {failed_check}",
                    )
                else:
                    raise AssertionError(f"frontend-first binding accepted {label}")
        finally:
            stop_thread.set()
            session_thread.join(timeout=1.0)
        require(
            session_thread.is_alive() is False,
            "frontend-first binding test thread did not stop",
        )


def test_green_capture() -> None:
    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        calls: list[str] = []
        runtime = fixture.runtime(calls)
        report = capture.run_capture(fixture.config(), runtime=runtime)
        require(report["result"] == "GREEN", f"fake capture RED: {report}")
        require(
            report["seed_purpose"] == "player-subject"
            and report["seed_contract_kind"] == "zg361_phase2_paused_seed",
            "historical default seed purpose/contract kind drifted",
        )
        require(report["mcp_only"] is True, "capture lost MCP-only boundary")
        require(
            report["ocr_used"] is True and report["image_used"] is True,
            "legal-consent-only visual boundary was not recorded",
        )
        require(
            report["legal_consent"]["state"] == "no_modal",
            "default no-modal legal gate did not preserve the capture flow",
        )
        require(report["coordinates_used"] is False, "fake capture used coordinates")
        require(report["test_decision_used"] is False, "fake capture used a test decision")
        source_identity = report["source_identity"]
        require(isinstance(source_identity, dict), "source identity missing")
        require(
            source_identity["git"]["declared_sha"] == fixture.git_sha,
            "declared frozen Git SHA drifted",
        )
        require(
            source_identity["archive_source_equivalence"]["equivalent"] is True,
            "source ZIP was not bound to the clean tree",
        )
        require(
            source_identity["source_zip"]["sha256"]
            == sha256(fixture.source_zip),
            "source ZIP blob hash drifted",
        )
        expected_zip_manifest = capture.zip_manifest(fixture.source_zip)
        require(
            source_identity["source_zip"]["logical_tree_sha256"]
            == expected_zip_manifest["logical_tree_sha256"],
            "source ZIP logical tree hash drifted",
        )
        expected_source_manifest = capture.tree_manifest(fixture.clean)
        require(
            source_identity["clean_source_tree"]["tree_sha256"]
            == expected_source_manifest["tree_sha256"],
            "clean source tree hash drifted",
        )
        require(
            report["bootstrap"]["enabled_mods"]
            == list(capture.EXPECTED_ENABLED_MODS),
            "profile did not enable exactly product+fixture",
        )
        require(
            report["runtime_mount_inventory"]
            == [
                str(
                    (
                        fixture.attempt
                        / "native-state"
                        / "profile"
                        / "mod-content"
                        / name
                    ).resolve()
                )
                for name in ("zhongguo_361", "fixture")
            ],
            "runtime did not prove the exact product/fixture mount pair",
        )
        require(
            report["cleanup"]["result"] == "GREEN"
            and report["cleanup"]["failed_checks"] == [],
            "canonical cleanup proof is not GREEN",
        )
        require(report["driver_closed"] is True, "driver close missing")
        require(report["runtime_unchanged"] is True, "runtime tree changed")
        require(report["clean_source_unchanged"] is True, "clean source changed")
        require(
            report["external_dependencies"]["unchanged"] is True,
            "external dependency drifted",
        )
        expected_dependency_hashes = {
            "source_zip": sha256(fixture.source_zip),
            "old_save": sha256(fixture.old_save),
            "game_executable": sha256(fixture.game / "binaries" / "ck3.exe"),
            "vanilla_game_rules": sha256(
                fixture.game
                / "game"
                / "common"
                / "game_rules"
                / "00_game_rules.txt"
            ),
            "bridge_dll": sha256(fixture.dll),
            "bridge_injector": sha256(fixture.injector),
        }
        require(
            report["external_dependencies"]["sha256_before"]
            == expected_dependency_hashes,
            "external dependency before hashes drifted",
        )
        require(
            report["external_dependencies"]["sha256_after"]
            == expected_dependency_hashes,
            "external dependency after hashes drifted",
        )
        seed = runtime.seed
        require(isinstance(seed, FakeSeed), "fake seed binding drifted")
        require(
            seed.materialize_kwargs is not None
            and seed.materialize_kwargs["product_tree_sha256"]
            == report["bootstrap"]["tree_sha256"]["product"]
            and seed.materialize_kwargs["fixture_tree_sha256"]
            == report["bootstrap"]["tree_sha256"]["fixture"]
            and seed.materialize_kwargs["provider_probes_path"]
            == fixture.artifacts / "provider-probes.json",
            "candidate provenance did not use independently observed runtime hashes",
        )
        require(
            report["live_verdict"] == "paused_seed_ready"
            and report["provider_baseline_verdict"]
            == "ready_provider_matrix_captured"
            and report["candidate"]["ready"] is True,
            "provider-GREEN capture did not produce a ready candidate",
        )
        require(
            report["keyboard_watchdog"]["green_attestation_count"] >= 1,
            "US English HKL watchdog never went GREEN",
        )
        require(
            any(row["name"] == "debug.log" for row in report["logs_copy"]["files"]),
            "CK3 log copy/index is missing debug.log",
        )
        order = {
            name: calls.index(name)
            for name in (
                "transport-binding",
                "legal-consent",
                "loader-stage",
                "single-mount-gate",
                "native-readiness",
                "loader-error-scan",
                "event-context",
                "seed-capture-mcp",
                "candidate-materialize",
                "supervisor-cleanup",
                "driver-close",
            )
        }
        require(
            order["transport-binding"]
            < order["legal-consent"]
            < order["loader-stage"]
            < order["single-mount-gate"]
            < order["native-readiness"]
            < order["loader-error-scan"]
            < order["event-context"]
            < order["seed-capture-mcp"]
            < order["candidate-materialize"]
            < order["supervisor-cleanup"]
            < order["driver-close"],
            f"capture order drifted: {calls}",
        )
        persisted = json.loads(
            (fixture.artifacts / "runner-report.json").read_text(encoding="utf-8")
        )
        require(persisted == report, "persisted report differs from return value")
        require(
            rows(fixture.artifacts / "bootstrap-event-wait.jsonl")[-1]["state"]
            == "bootstrap_event_ready",
            "event waiter lacks a GREEN append-only terminal",
        )


def test_player_manager_capture_routes_fixture_event_and_materializer() -> None:
    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        calls: list[str] = []
        purpose = capture.MANAGER_SEED_PURPOSE
        runtime = fixture.runtime(calls, seed_purpose=purpose)
        report = capture.run_capture(
            fixture.config(seed_purpose=purpose), runtime=runtime
        )
        require(report["result"] == "GREEN", f"manager fake capture RED: {report}")
        require(
            report["seed_purpose"] == purpose
            and report["seed_contract_kind"]
            == "zg361_phase2_player_manager_seed_request",
            "manager report did not bind purpose and request contract kind",
        )
        require(
            report["expected_event_definition_key"]
            == capture.MANAGER_SEED_EVENT_DEFINITION_KEY
            and report["bootstrap_event"]["event_definition_key"]
            == capture.MANAGER_SEED_EVENT_DEFINITION_KEY,
            "manager runner did not wait for the exact manager fixture event",
        )
        require(
            report["fixture_kind"]
            == "acceptance-only phase2 player-manager seed bootstrap",
            "manager fixture kind was not reported",
        )
        require(
            report["scenario_verdict"] == "GREEN"
            and report["seed_verdict"] == "GREEN"
            and report["provider_probes"]["result"] == "NOT_APPLICABLE"
            and report["provider_baseline_verdict"]
            == "not_applicable_player_manager_seed",
            "manager seed result was confused with the player-subject provider matrix",
        )
        require(
            not any(call.startswith("provider:") for call in calls),
            "manager seed capture queried player-subject product providers",
        )
        seed = runtime.seed
        require(isinstance(seed, FakeSeed), "manager fake seed binding drifted")
        require(
            seed.materialize_kwargs is not None
            and "provider_probes_path" not in seed.materialize_kwargs,
            "manager materializer received a forged player-subject provider receipt",
        )
        mounted_fixture = Path(report["bootstrap"]["targets"]["fixture"])
        require(
            (mounted_fixture / "descriptor.mod").read_text(encoding="utf-8")
            == "name=manager-fixture\n",
            "manager capture mounted the historical player-subject fixture",
        )


def test_direct_player_manager_first_frame_capture_is_zero_input() -> None:
    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        fixture.use_direct_manager_contract()
        calls: list[str] = []
        purpose = capture.MANAGER_SEED_PURPOSE
        runtime = fixture.runtime(
            calls,
            seed_purpose=purpose,
            manager_pip_route=False,
        )
        report = capture.run_capture(
            fixture.config(seed_purpose=purpose), runtime=runtime
        )
        require(report["result"] == "GREEN", f"direct manager RED: {report}")
        require(
            report["manager_entry_mode"] == "direct-already-player-manager",
            "direct source was reported as a player handoff",
        )
        source = report["manager_direct_source_snapshot"]
        require(
            source["result"] == "GREEN"
            and source["date_raw"] == 777
            and source["observed_played_character_id"] == 9001
            and source["gameplay_input_sent"] is False,
            f"first paused typed source was not bound exactly: {source}",
        )
        binding = report["manager_direct_final_binding"]
        require(
            binding["result"] == "GREEN"
            and binding["observed_manager_character_id"] == 9001
            and binding["observed_played_character_id"] == 9001
            and binding["observed_reviewable_subject_character_id"] == 9002
            and binding["observed_date_raw"] == 777
            and binding["failed_checks"] == [],
            f"direct final typed pair drifted: {binding}",
        )
        candidate = report["manager_direct_candidate_identity"]
        require(
            candidate["result"] == "GREEN"
            and candidate["typed_manager_character_id"] == 9001
            and candidate["typed_subject_character_id"] == 9002
            and candidate["failed_checks"] == [],
            f"direct candidate identity drifted: {candidate}",
        )
        require(
            not any(call.startswith("execute:") for call in calls)
            and not any(call.startswith("select-event-option:") for call in calls),
            f"first-frame direct event sent unnecessary input: {calls}",
        )
        require(
            not (fixture.artifacts / "known-pre-bootstrap-b2-pip-event-drain.json").exists()
            and "manager_activation_event_drain" not in report
            and "manager_player_transition" not in report,
            "direct manager capture emitted legacy PIP evidence",
        )


def test_direct_player_manager_destructive_first_frame_is_zero_input_red() -> None:
    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        fixture.use_direct_manager_contract()
        calls: list[str] = []
        purpose = capture.MANAGER_SEED_PURPOSE
        runtime = fixture.runtime(
            calls,
            seed_purpose=purpose,
            event_definition_key="ep3_interactions_events.0630",
            manager_pip_route=False,
        )
        report = capture.run_capture(
            fixture.config(seed_purpose=purpose), runtime=runtime
        )
        evidence = report.get("failure_evidence")
        require(
            report["result"] == "RED"
            and isinstance(evidence, dict)
            and evidence.get("state") == "unexpected_visible_event"
            and evidence.get("observed_event_definition_key")
            == "ep3_interactions_events.0630"
            and evidence.get("drained_pre_bootstrap_events") == [],
            f"direct destructive first frame was not exact RED: {evidence}",
        )
        require(
            not any(call.startswith("execute:") for call in calls)
            and not any(call.startswith("select-event-option:") for call in calls)
            and "seed-capture-mcp" not in calls
            and "candidate-materialize" not in calls,
            f"destructive first frame crossed the zero-input boundary: {calls}",
        )


def test_direct_player_manager_wrong_played_id_is_zero_input_red() -> None:
    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        fixture.use_direct_manager_contract()
        calls: list[str] = []
        purpose = capture.MANAGER_SEED_PURPOSE
        runtime = fixture.runtime(
            calls,
            seed_purpose=purpose,
            manager_pip_route=False,
        )
        service = runtime.service_factory(None)
        require(isinstance(service, FakeService), "direct player fake drifted")
        service.played_character_id = 9003
        report = capture.run_capture(
            fixture.config(seed_purpose=purpose), runtime=runtime
        )
        evidence = report.get("failure_evidence")
        require(
            report["result"] == "RED"
            and isinstance(evidence, dict)
            and evidence.get("stage")
            == "direct_manager_first_paused_typed_snapshot"
            and evidence.get("failed_checks")
            == ["played_character_matches_frozen_manager"],
            f"wrong direct player did not fail at the first frame: {evidence}",
        )
        require(
            not any(call.startswith("execute:") for call in calls)
            and not any(call.startswith("select-event-option:") for call in calls)
            and "seed-capture-mcp" not in calls,
            f"wrong direct player crossed the zero-input boundary: {calls}",
        )


def test_direct_player_manager_missing_typed_player_is_zero_input_red() -> None:
    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        fixture.use_direct_manager_contract()
        calls: list[str] = []
        purpose = capture.MANAGER_SEED_PURPOSE
        runtime = fixture.runtime(
            calls,
            seed_purpose=purpose,
            manager_pip_route=False,
        )
        service = runtime.service_factory(None)
        require(isinstance(service, FakeService), "direct player fake drifted")
        service.played_character_id = None
        report = capture.run_capture(
            fixture.config(seed_purpose=purpose), runtime=runtime
        )
        evidence = report.get("failure_evidence")
        require(
            report["result"] == "RED"
            and isinstance(evidence, dict)
            and evidence.get("stage")
            == "direct_manager_first_paused_typed_snapshot"
            and evidence.get("observed_played_character_id") is None
            and evidence.get("failed_checks")
            == ["played_character_matches_frozen_manager"],
            f"missing typed direct player did not fail at first frame: {evidence}",
        )
        require(
            not any(call.startswith("execute:") for call in calls)
            and not any(call.startswith("select-event-option:") for call in calls)
            and "seed-capture-mcp" not in calls,
            f"missing typed direct player crossed the zero-input boundary: {calls}",
        )


def test_direct_player_manager_self_subject_is_red_before_materialize() -> None:
    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        fixture.use_direct_manager_contract()
        calls: list[str] = []
        purpose = capture.MANAGER_SEED_PURPOSE
        runtime = fixture.runtime(
            calls,
            seed_purpose=purpose,
            manager_pip_route=False,
        )
        seed = runtime.seed
        require(isinstance(seed, FakeSeed), "direct subject fake drifted")
        seed.manager_entry_override = {
            "manager_character_id": 9001,
            "reviewable_subject_character_id": 9001,
        }
        report = capture.run_capture(
            fixture.config(seed_purpose=purpose), runtime=runtime
        )
        evidence = report.get("failure_evidence")
        require(
            report["result"] == "RED"
            and isinstance(evidence, dict)
            and evidence.get("stage")
            == "direct_already_player_manager_final_binding"
            and evidence.get("failed_checks")
            == ["subject_matches_typed_handoff_subject"],
            f"self-subject direct capture false-GREENed: {evidence}",
        )
        require(
            "seed-capture-mcp" in calls and "candidate-materialize" not in calls,
            "self-subject direct capture crossed materialization",
        )


def test_direct_player_manager_candidate_identity_drift_is_red() -> None:
    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        fixture.use_direct_manager_contract()
        calls: list[str] = []
        purpose = capture.MANAGER_SEED_PURPOSE
        runtime = fixture.runtime(
            calls,
            seed_purpose=purpose,
            manager_pip_route=False,
        )
        seed = runtime.seed
        require(isinstance(seed, FakeSeed), "direct candidate fake drifted")
        seed.candidate_entry_override = {
            "manager_character_id": 9001,
            "reviewable_subject_character_id": 9003,
        }
        report = capture.run_capture(
            fixture.config(seed_purpose=purpose), runtime=runtime
        )
        evidence = report.get("failure_evidence")
        require(
            report["result"] == "RED"
            and isinstance(evidence, dict)
            and evidence.get("stage") == "direct_manager_candidate_identity"
            and "candidate_subject_matches_typed_event"
            in evidence.get("failed_checks", []),
            f"direct candidate drift false-GREENed: {evidence}",
        )
        require(
            "candidate-materialize" in calls,
            "candidate drift test did not cross the intended materializer boundary",
        )


def test_player_manager_post_exact_pip_handoff_proves_final_event() -> None:
    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        calls: list[str] = []
        purpose = capture.MANAGER_SEED_PURPOSE
        runtime = fixture.runtime(calls, seed_purpose=purpose)
        report = capture.run_capture(
            fixture.config(seed_purpose=purpose), runtime=runtime
        )
        require(report["result"] == "GREEN", f"manager handoff RED: {report}")
        require(
            report["manager_entry_mode"] == "post-exact-pip-load-gui-handoff",
            "manager handoff was not reported as the post-PIP GUI route",
        )
        require(
            report["manager_entry_event"] == {
                "event_definition_key": capture.MANAGER_SEED_EVENT_DEFINITION_KEY,
                "date_raw": 53147040,
                "revision": 8,
            },
            "manager entry did not preserve the exact post-PIP .1 checkpoint",
        )
        transition = report["manager_player_transition"]
        transition_contract = report["manager_transition_contract"]
        require(
            transition_contract["checks"]["terminal_pip_activation_signal"]
            is True
            and transition_contract["checks"][
                "gui_retry_duration_is_bounded"
            ]
            is True
            and transition_contract["checks"][
                "post_activation_pause_is_bounded"
            ]
            is True,
            "manager transition contract lost the R124 GUI settle gates",
        )
        require(
            transition["result"] == "GREEN"
            and transition["source_character_id"] == 9001
            and transition["target_character_id"] == 9002
            and transition["observed_played_character_id"] == 9002
            and transition["observed_manager_character_id"] == 9002
            and transition["observed_reviewable_subject_character_id"] == 9001
            and transition["source_date_raw"] == 53147016
            and transition["completion_date_raw"] == 53147040
            and transition["observed_date_raw"] == 53147040
            and transition["failed_checks"] == [],
            "source hash + final typed event did not prove the post-PIP rebind",
        )
        require(
            report["manager_handoff_final_binding"]["result"] == "GREEN"
            and report["manager_handoff_final_binding"]["failed_checks"] == []
            and report["manager_handoff_final_binding"]
            ["observed_manager_character_id"]
            == 9002
            and report["manager_handoff_final_binding"]
            ["observed_reviewable_subject_character_id"]
            == 9001,
            "final .1 identities did not close against the source player pair",
        )
        require(
            report["bootstrap_event"]["event_definition_key"]
            == capture.MANAGER_SEED_EVENT_DEFINITION_KEY
            and report["bootstrap_event"]["revision"] == 8
            and report["bootstrap_event"]["date_raw"] == 53147040,
            "capture did not stop on the exact post-PIP .1 manager event",
        )
        require(
            "typed-player-transition" not in calls
            and calls.index("seed-capture-mcp")
            < calls.index("candidate-materialize"),
            f"runner crossed an unauthorized player-transition boundary: {calls}",
        )
        require(
            not any(call.startswith("provider:") for call in calls),
            "manager handoff queried player-subject product providers",
        )
        transition_artifact = fixture.artifacts / "manager-preemptive-player-transition.json"
        require(
            transition_artifact.is_file()
            and json.loads(transition_artifact.read_text(encoding="utf-8"))
            == transition,
            "preemptive transition artifact is absent or differs from the report",
        )
        wait_rows = rows(fixture.artifacts / "bootstrap-event-wait.jsonl")
        ready_keys = [
            row.get("event_definition_key")
            for row in wait_rows
            if row.get("state") == "bootstrap_event_ready"
        ]
        require(
            ready_keys == [capture.MANAGER_SEED_EVENT_DEFINITION_KEY],
            f"manager waiter did not accept only the final fixture event: {ready_keys}",
        )
        require(
            any(
                row.get("state") == "post_activation_gui_settle_started"
                and row.get("settle_seconds") == 5.0
                and row.get("timeline_resume_forbidden") is True
                for row in wait_rows
            ),
            "manager run did not bind the exact PIP drain to paused GUI settle",
        )
        require(
            report["manager_activation_event_drain"]["selection"]["option_number"]
            == 3
            and report["manager_activation_event_drain"]["selection"][
                "option_index"
            ]
            == 2,
            "manager route did not refuse the exact PIP with option three",
        )


def test_player_manager_handoff_rejects_final_subject_identity_drift() -> None:
    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        calls: list[str] = []
        purpose = capture.MANAGER_SEED_PURPOSE
        runtime = fixture.runtime(
            calls,
            seed_purpose=purpose,
        )
        seed = runtime.seed
        require(isinstance(seed, FakeSeed), "manager mismatch seed fake drifted")
        seed.manager_entry_override = {
            "manager_character_id": 9002,
            "reviewable_subject_character_id": 9003,
        }
        report = capture.run_capture(
            fixture.config(seed_purpose=purpose), runtime=runtime
        )
        require(report["result"] == "RED", "manager identity drift false-GREENed")
        require(
            report["scenario_verdict"] == "RED"
            and report["seed_verdict"] == "RED",
            "manager identity drift did not remain scenario/seed RED",
        )
        evidence = report.get("failure_evidence")
        require(
            isinstance(evidence, dict)
            and evidence.get("stage") == "post_exact_pip_player_transition"
            and evidence.get("result") == "RED"
            and evidence.get("expected_manager_character_id") == 9002
            and evidence.get("observed_manager_character_id") == 9002
            and evidence.get("expected_reviewable_subject_character_id") == 9001
            and evidence.get("observed_reviewable_subject_character_id") == 9003
            and evidence.get("failed_checks")
            == ["subject_matches_typed_handoff_subject"],
            f"manager identity drift evidence is not exact: {evidence}",
        )
        require(
            "typed-player-transition" not in calls
            and "seed-capture-mcp" in calls
            and "candidate-materialize" not in calls,
            "manager identity drift was not stopped before materialization",
        )


def test_player_manager_preemptive_handoff_rejects_later_date() -> None:
    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        calls: list[str] = []
        purpose = capture.MANAGER_SEED_PURPOSE
        runtime = fixture.runtime(calls, seed_purpose=purpose)
        service = runtime.service_factory(None)
        require(isinstance(service, FakeService), "manager date fake drifted")
        service.date_raw = 53147064
        service.paused = False
        report = capture.run_capture(
            fixture.config(seed_purpose=purpose), runtime=runtime
        )
        require(report["result"] == "RED", "later-date manager event false-GREENed")
        evidence = report.get("failure_evidence")
        require(
            isinstance(evidence, dict)
            and evidence.get("state") == "maximum_bootstrap_date_exceeded"
            and evidence.get("maximum_date_raw") == 53147040
            and evidence.get("observed_date_raw") == 53147064
            and evidence.get("protective_pause", {}).get("attempted") is True,
            f"later-date rejection evidence is not exact: {evidence}",
        )
        require(
            "execute:pause-map" in calls,
            "later-date RED did not attempt a protective MCP pause",
        )
        require(
            "seed-capture-mcp" not in calls
            and "candidate-materialize" not in calls,
            "later-date RED reached capture/materialization",
        )


def test_player_manager_preemptive_handoff_rejects_wrong_played_manager() -> None:
    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        calls: list[str] = []
        purpose = capture.MANAGER_SEED_PURPOSE
        runtime = fixture.runtime(calls, seed_purpose=purpose)
        service = runtime.service_factory(None)
        seed = runtime.seed
        require(isinstance(service, FakeService), "manager player fake drifted")
        require(isinstance(seed, FakeSeed), "manager seed fake drifted")
        service.played_character_id = 9003
        seed.manager_entry_override = {
            "manager_character_id": 9002,
            "reviewable_subject_character_id": 9001,
        }
        report = capture.run_capture(
            fixture.config(seed_purpose=purpose), runtime=runtime
        )
        evidence = report.get("failure_evidence")
        require(
            report["result"] == "RED"
            and isinstance(evidence, dict)
            and evidence.get("observed_played_character_id") == 9003
            and evidence.get("failed_checks")
            == ["played_character_matches_target_manager"],
            f"wrong played manager was not isolated as RED: {evidence}",
        )
        require("candidate-materialize" not in calls, "wrong player materialized")


def test_player_manager_handoff_never_drains_destructive_later_event() -> None:
    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        calls: list[str] = []
        purpose = capture.MANAGER_SEED_PURPOSE
        runtime = fixture.runtime(
            calls,
            seed_purpose=purpose,
            event_definition_key="ep3_interactions_events.0630",
        )
        report = capture.run_capture(
            fixture.config(seed_purpose=purpose), runtime=runtime
        )
        require(report["result"] == "RED", "destructive event false-GREENed")
        evidence = report.get("failure_evidence")
        require(
            isinstance(evidence, dict)
            and evidence.get("state") == "unexpected_visible_event"
            and evidence.get("observed_event_definition_key")
            == "ep3_interactions_events.0630"
            and evidence.get("drained_pre_bootstrap_events") == [],
            f"destructive event was not rejected before input: {evidence}",
        )
        require(
            not any(call.startswith("execute:") for call in calls)
            and "seed-capture-mcp" not in calls,
            f"destructive event received gameplay input: {calls}",
        )


def test_player_manager_same_date_grace_uses_speed_five() -> None:
    class SourceDateCarrierService:
        def __init__(self) -> None:
            self.revision = 1
            self.speed = 1
            self.paused = True
            self.active = False
            self.steps: list[str] = []

        def snapshot(self) -> dict[str, object]:
            return {
                "revision": self.revision,
                "date_raw": 777,
                "paused": self.paused,
                "map_ready": True,
                "speed": self.speed,
                "active_event": (
                    {"instance_id": 44, "option_count": 1}
                    if self.active
                    else None
                ),
            }

        def execute_step(self, step: str, *, expected_revision: int) -> None:
            require(expected_revision == self.revision, "speed-5 test used stale revision")
            self.steps.append(step)
            self.revision += 1
            if step == "set-speed-5":
                self.speed = 5
            elif step == "resume-map":
                self.paused = False
                self.active = True
            elif step == "pause-map":
                self.paused = True
            else:
                raise AssertionError(f"unexpected same-date grace step: {step}")

        def query_current_event_window_context_v1(
            self, _event_id: int, **_kwargs: object
        ) -> dict[str, object]:
            return {
                "current_event_window_context": {
                    "event_definition_key": capture.MANAGER_SEED_EVENT_DEFINITION_KEY
                }
            }

    with tempfile.TemporaryDirectory() as raw:
        service = SourceDateCarrierService()
        snapshot = capture.wait_for_bootstrap_event(
            service,
            Path(raw),
            bridge_unavailable_error=FakeBridgeUnavailableError,
            timeout_seconds=2.0,
            expected_event_definition_key=capture.MANAGER_SEED_EVENT_DEFINITION_KEY,
            maximum_date_raw=777,
            expected_event_date_raw=777,
            allow_known_prebootstrap_drains=False,
            known_prebootstrap_drain_allowlist=(),
            timeline_speed=5,
            clock=FakeTime().clock,
            sleeper=lambda _seconds: None,
        )
        require(snapshot["date_raw"] == 777, "speed-5 grace advanced past its date")
        require(
            service.steps == ["set-speed-5", "resume-map", "pause-map"],
            f"manager same-date grace did not use speed 5: {service.steps}",
        )


def test_player_manager_wrong_event_is_scenario_and_seed_red() -> None:
    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        calls: list[str] = []
        purpose = capture.MANAGER_SEED_PURPOSE
        runtime = fixture.runtime(
            calls,
            seed_purpose=purpose,
            event_definition_key=capture.SEED_EVENT_DEFINITION_KEY,
        )
        report = capture.run_capture(
            fixture.config(seed_purpose=purpose), runtime=runtime
        )
        require(report["result"] == "RED", "wrong manager event false-GREENed")
        require(
            report["scenario_verdict"] == "RED"
            and report["seed_verdict"] == "RED",
            "missing manager event did not remain scenario/seed RED",
        )
        evidence = report.get("failure_evidence")
        require(
            isinstance(evidence, dict)
            and evidence.get("state") == "unexpected_visible_event"
            and evidence.get("expected_event_definition_key")
            == capture.MANAGER_SEED_EVENT_DEFINITION_KEY
            and evidence.get("observed_event_definition_key")
            == capture.SEED_EVENT_DEFINITION_KEY,
            "manager wrong-event evidence was not exact",
        )
        require(
            "seed-capture-mcp" not in calls and "candidate-materialize" not in calls,
            "manager RED reached evidence capture/materialization",
        )


def test_player_manager_preflight_reports_purpose_and_contract_kind() -> None:
    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        calls: list[str] = []
        purpose = capture.MANAGER_SEED_PURPOSE
        report = capture.run_preflight(
            fixture.config(seed_purpose=purpose),
            runtime=fixture.runtime(calls, seed_purpose=purpose),
            _allow_fixture_static_skip=True,
        )
        require(report["result"] == "GREEN", f"manager preflight RED: {report}")
        require(
            report["seed_purpose"] == purpose
            and report["seed_contract_kind"]
            == "zg361_phase2_player_manager_seed_request"
            and report["expected_seed_contract_kind"]
            == "zg361_phase2_player_manager_seed_request"
            and report["seed_contract_status"]
            == "blocked_live_capture_required",
            "manager preflight did not distinguish purpose/request contract",
        )
        require(
            report["seed_ready"] is False
            and report["readiness_scope"]
            == "frozen_inputs_and_projection_only",
            "manager preflight falsely claimed a captured seed",
        )
        static_row = report["static_preflight"]
        require(
            static_row["result"] == "SKIPPED"
            and "seed_bootstrap_test" in static_row["missing_scripts"]
            and any(
                str(path).endswith(
                    "test_zg361_phase2_manager_seed_bootstrap.py"
                )
                for path in static_row["missing_paths"]
            )
            and any(
                str(path).endswith(
                    "test_zg361_phase2_manager_seed_fixture.py"
                )
                for path in static_row["missing_paths"]
            ),
            "manager preflight did not select the manager-specific static gates",
        )


def test_parser_red_cleanup() -> None:
    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        calls: list[str] = []
        report = capture.run_capture(
            fixture.config(), runtime=fixture.runtime(calls, parser_red=True)
        )
        require(report["result"] == "RED", "parser failure false-GREENed")
        expected = {
            "result": "RED",
            "state": "loader_parse_red",
            "stage": "database_init",
            "fatal_error_count": 4,
            "fatal_errors": [{"fingerprint_sha256": "f" * 64}],
        }
        require(report["loader_stage"] == expected, "parser evidence was rewritten")
        require("single-mount-gate" not in calls, "parser RED reached mount gate")
        require("native-readiness" not in calls, "parser RED reached native readiness")
        require("loader-error-scan" not in calls, "parser RED reached error scan")
        require("event-context" not in calls, "parser RED reached event waiter")
        require("seed-capture-mcp" not in calls, "parser RED reached capture")
        require("supervisor-cleanup" in calls, "parser RED skipped cleanup")
        require("driver-close" in calls, "parser RED skipped driver close")
        require(report["runtime_unchanged"] is True, "RED runtime tree changed")
        require(report["clean_source_unchanged"] is True, "RED source tree changed")
        require(
            rows(
                fixture.artifacts / "01_phase2_loader_stage_progress.jsonl"
            )[-1]
            == expected,
            "append-only loader terminal was not preserved",
        )
        require(
            rows(fixture.artifacts / "runner-failures.jsonl")[-1]["loader_stage"]
            == expected,
            "failure stream did not preserve typed parser evidence",
        )
        require(
            (fixture.artifacts / "ck3-logs" / "debug.log").is_file(),
            "parser RED did not preserve CK3 logs",
        )


def test_native_session_process_exit_cleanup() -> None:
    """A supervisor process-exit RED is retained while cleanup still runs."""

    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        calls: list[str] = []
        report = capture.run_capture(
            fixture.config(),
            runtime=fixture.runtime(calls, process_exit=True),
        )
        require(report["result"] == "RED", "native process exit false-GREENed")
        loader_evidence = report["loader_stage"]
        require(
            isinstance(loader_evidence, dict)
            and loader_evidence.get("state") == "native_session_process_exit",
            "native process exit terminal was not retained by runner",
        )
        require(
            loader_evidence.get("process_exit_code") == 1
            and loader_evidence.get("process_exit_nonzero") is True,
            "runner lost the non-zero native exit code",
        )
        require(
            "supervisor-cleanup" in calls,
            "native process exit skipped managed cleanup",
        )
        require(
            "single-mount-gate" not in calls
            and "native-readiness" not in calls
            and "event-context" not in calls
            and "seed-capture-mcp" not in calls,
            "native process exit crossed the loader failure boundary",
        )
        require(
            report["cleanup"]["result"] == "GREEN",
            "native process exit did not retain cleanup proof",
        )
        require(
            rows(fixture.artifacts / "01_phase2_loader_stage_progress.jsonl")[-1][
                "state"
            ]
            == "native_session_process_exit",
            "append-only loader stream lacks process-exit terminal",
        )
        require(
            rows(fixture.artifacts / "runner-failures.jsonl")[-1]["loader_stage"][
                "state"
            ]
            == "native_session_process_exit",
            "failure stream lost process-exit evidence",
        )


def _known_predecessor_context(
    root_character_id: int = 29037, calculated_event_id: int = 3030004
) -> dict[str, object]:
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "snapshot_revision": 5,
        "date_raw": capture.KNOWN_PRE_BOOTSTRAP_EVENT["date_raw"],
        "current_event_instance_id": 10,
        "window_match_count": 1,
        "event_definition_key": capture.KNOWN_PRE_BOOTSTRAP_EVENT[
            "event_definition_key"
        ],
        "calculated_event_id": calculated_event_id,
        "root_scope": {
            "typed_identity": {
                "status": "available",
                "kind": "character",
                "character_id": root_character_id,
            }
        },
        "saved_scopes": [
            {
                "name": "zg361_reviewing_superior",
                "scope": {
                    "typed_identity": {
                        "status": "available",
                        "kind": "character",
                        "character_id": 32904,
                    }
                },
            }
        ],
        "options": [
            {
                "rendered_index": index,
                "native_option_index": index,
                "shown": True,
                "enabled": True,
                "fallback": False,
                "cancel": False,
            }
            for index in range(4)
        ],
    }


class KnownPredecessorService:
    def __init__(
        self, *, root_character_id: int = 29037, calculated_event_id: int = 3030004
    ) -> None:
        self.state = "predecessor"
        self.revision = 5
        self.root_character_id = root_character_id
        self.calculated_event_id = calculated_event_id
        self.selections: list[tuple[int, int, int]] = []

    def snapshot(self) -> dict[str, object]:
        active_event = (
            {"instance_id": 10, "option_count": 4}
            if self.state == "predecessor"
            else {"instance_id": 11, "option_count": 1}
        )
        return {
            "revision": self.revision,
            "date_raw": capture.KNOWN_PRE_BOOTSTRAP_EVENT["date_raw"],
            "paused": True,
            "map_ready": True,
            "speed": 1,
            "active_event": active_event,
        }

    def query_current_event_window_context_v1(
        self, event_instance_id: int, **_kwargs: object
    ) -> dict[str, object]:
        if self.state == "predecessor":
            require(event_instance_id == 10, "wrong predecessor instance queried")
            return {
                "current_event_window_context": _known_predecessor_context(
                    self.root_character_id, self.calculated_event_id
                )
            }
        require(event_instance_id == 11, "wrong seed instance queried")
        return {
            "current_event_window_context": {
                "event_definition_key": capture.SEED_EVENT_DEFINITION_KEY
            }
        }

    def select_event_option(
        self,
        option_number: int,
        *,
        event_instance_id: int,
        expected_revision: int,
    ) -> dict[str, object]:
        self.selections.append(
            (option_number, event_instance_id, expected_revision)
        )
        require(self.state == "predecessor", "predecessor selected twice")
        self.state = "seed"
        self.revision += 1
        return {
            "step": "select-event-option-1",
            "accepted": True,
            "status": "submitted",
            "option_number": 1,
            "option_index": 0,
            "event_selection": {
                "postcondition_verified": True,
                "old_event_instance_id": 10,
                "new_event_instance_id": 11,
                "selected_option_number": 1,
                "selected_native_option_index": 0,
            },
        }


def _known_vanilla_context(
    *,
    event_key: str = "spymaster_task.0381",
    root_character_id: int = 29037,
    character_to_hook_id: int = 44001,
    second_option_fallback: bool = False,
) -> dict[str, object]:
    expected = capture.KNOWN_PRE_BOOTSTRAP_VANILLA_EVENT
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "snapshot_revision": 8,
        "date_raw": expected["date_raw"],
        "current_event_instance_id": 20,
        "window_match_count": 1,
        "event_definition_key": event_key,
        "calculated_event_id": 880381,
        "root_scope": {
            "typed_identity": {
                "status": "available",
                "kind": "character",
                "character_id": root_character_id,
            }
        },
        "saved_scopes": [
            {
                "name": "character_to_hook",
                "scope": {
                    "typed_identity": {
                        "status": "available",
                        "kind": "character",
                        "character_id": character_to_hook_id,
                    }
                },
            }
        ],
        "options": [
            {
                "rendered_index": index,
                "native_option_index": index,
                "shown": True,
                "enabled": True,
                "fallback": second_option_fallback and index == 1,
                "cancel": False,
            }
            for index in range(2)
        ],
    }


class KnownVanillaPrebootstrapService:
    def __init__(
        self,
        *,
        event_key: str = "spymaster_task.0381",
        root_character_id: int = 29037,
        character_to_hook_id: int = 44001,
        second_option_fallback: bool = False,
        reaches_seed: bool = True,
        wrong_selection_ack: bool = False,
    ) -> None:
        self.state = "vanilla"
        self.revision = 8
        self.paused = True
        self.event_key = event_key
        self.root_character_id = root_character_id
        self.character_to_hook_id = character_to_hook_id
        self.second_option_fallback = second_option_fallback
        self.reaches_seed = reaches_seed
        self.wrong_selection_ack = wrong_selection_ack
        self.selections: list[tuple[int, int, int]] = []
        self.steps: list[str] = []

    def snapshot(self) -> dict[str, object]:
        expected = capture.KNOWN_PRE_BOOTSTRAP_VANILLA_EVENT
        if self.state == "vanilla":
            active_event: dict[str, object] | None = {
                "source": "native",
                "instance_id": 20,
                "option_count": 2,
            }
        elif self.state == "seed":
            active_event = {
                "source": "native",
                "instance_id": 21,
                "option_count": 1,
            }
        else:
            active_event = None
        return {
            "revision": self.revision,
            "date_raw": expected["date_raw"],
            "paused": self.paused,
            "map_ready": True,
            "speed": 1,
            "active_event": active_event,
        }

    def query_current_event_window_context_v1(
        self, event_instance_id: int, **_kwargs: object
    ) -> dict[str, object]:
        if self.state == "vanilla":
            require(event_instance_id == 20, "wrong vanilla instance queried")
            return {
                "current_event_window_context": _known_vanilla_context(
                    event_key=self.event_key,
                    root_character_id=self.root_character_id,
                    character_to_hook_id=self.character_to_hook_id,
                    second_option_fallback=self.second_option_fallback,
                )
            }
        require(event_instance_id == 21, "wrong seed instance queried")
        return {
            "current_event_window_context": {
                "event_definition_key": capture.SEED_EVENT_DEFINITION_KEY
            }
        }

    def select_event_option(
        self,
        option_number: int,
        *,
        event_instance_id: int,
        expected_revision: int,
    ) -> dict[str, object]:
        self.selections.append(
            (option_number, event_instance_id, expected_revision)
        )
        require(self.state == "vanilla", "vanilla event selected twice")
        self.state = "seed" if self.reaches_seed else "empty"
        self.revision += 1
        selected_index = 0 if self.wrong_selection_ack else 1
        return {
            "step": "select-event-option-2",
            "accepted": True,
            "status": "submitted",
            "option_number": 2,
            "option_index": selected_index,
            "event_selection": {
                "postcondition_verified": True,
                "old_event_instance_id": 20,
                "new_event_instance_id": 21 if self.reaches_seed else None,
                "selected_option_number": 2,
                "selected_native_option_index": selected_index,
            },
        }

    def execute_step(
        self, step: str, *, expected_revision: int
    ) -> dict[str, object]:
        require(expected_revision == self.revision, "stale timeline revision")
        self.steps.append(step)
        if step == "resume-map":
            self.paused = False
        return {"accepted": True}


def _known_b2_pip_context(
    *, prompt_owner_character_id: int = 32904
) -> dict[str, object]:
    expected = capture.KNOWN_PRE_BOOTSTRAP_B2_PIP_EVENT

    def character_scope(name: str, character_id: int) -> dict[str, object]:
        return {
            "name": name,
            "scope": {
                "typed_identity": {
                    "status": "available",
                    "kind": "character",
                    "character_id": character_id,
                }
            },
        }

    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "snapshot_revision": 7,
        "date_raw": expected["date_raw"],
        "current_event_instance_id": 30,
        "window_match_count": 1,
        "event_definition_key": expected["event_definition_key"],
        "calculated_event_id": 4430040,
        "root_scope": {
            "typed_identity": {
                "status": "available",
                "kind": "character",
                "character_id": expected["root_character_id"],
            }
        },
        "saved_scopes": [
            character_scope(
                "zg361_reviewing_superior",
                expected["reviewing_superior_character_id"],
            ),
            character_scope(
                "zg361_b2_pip_prompt_owner", prompt_owner_character_id
            ),
            character_scope(
                "zg361_b2_pip_prompt_subject",
                expected["prompt_subject_character_id"],
            ),
            character_scope(
                "zga_personal_result_target",
                expected["personal_result_target_character_id"],
            ),
        ],
        "options": [
            {
                "rendered_index": index,
                "native_option_index": index,
                "shown": True,
                "enabled": True,
                "fallback": False,
                "cancel": False,
            }
            for index in range(expected["option_count"])
        ],
    }


class KnownB2PipPrebootstrapService:
    def __init__(
        self,
        *,
        prompt_owner_character_id: int = 32904,
        selected_option_number: int = 1,
        final_event_definition_key: str = capture.SEED_EVENT_DEFINITION_KEY,
        post_drain_empty_snapshots: int = 0,
    ) -> None:
        self.state = "pip"
        self.revision = 7
        self.prompt_owner_character_id = prompt_owner_character_id
        self.selected_option_number = selected_option_number
        self.final_event_definition_key = final_event_definition_key
        self.post_drain_empty_snapshots = post_drain_empty_snapshots
        self.post_drain_snapshot_count = 0
        self.selections: list[tuple[int, int, int]] = []
        self.steps: list[str] = []

    def snapshot(self) -> dict[str, object]:
        expected = capture.KNOWN_PRE_BOOTSTRAP_B2_PIP_EVENT
        if self.state == "pip":
            active_event: dict[str, object] | None = {
                "source": "native",
                "instance_id": 30,
                "option_count": 3,
            }
        elif self.state == "settling":
            self.post_drain_snapshot_count += 1
            if self.post_drain_snapshot_count > self.post_drain_empty_snapshots:
                self.state = "seed"
                active_event = {
                    "source": "native",
                    "instance_id": 31,
                    "option_count": 1,
                }
            else:
                active_event = None
        else:
            active_event = {
                "source": "native",
                "instance_id": 31,
                "option_count": 1,
            }
        return {
            "revision": self.revision,
            "date_raw": expected["date_raw"],
            "paused": True,
            "map_ready": True,
            "speed": 1,
            "active_event": active_event,
        }

    def query_current_event_window_context_v1(
        self, event_instance_id: int, **_kwargs: object
    ) -> dict[str, object]:
        if self.state == "pip":
            require(event_instance_id == 30, "wrong PIP instance queried")
            return {
                "current_event_window_context": _known_b2_pip_context(
                    prompt_owner_character_id=self.prompt_owner_character_id
                )
            }
        require(event_instance_id == 31, "wrong seed instance queried")
        return {
            "current_event_window_context": {
                "event_definition_key": self.final_event_definition_key
            }
        }

    def select_event_option(
        self,
        option_number: int,
        *,
        event_instance_id: int,
        expected_revision: int,
    ) -> dict[str, object]:
        self.selections.append(
            (option_number, event_instance_id, expected_revision)
        )
        require(self.state == "pip", "PIP event selected twice")
        require(
            option_number == self.selected_option_number,
            "PIP selected option drifted",
        )
        self.state = (
            "settling" if self.post_drain_empty_snapshots > 0 else "seed"
        )
        self.revision += 1
        return {
            "step": f"select-event-option-{option_number}",
            "accepted": True,
            "status": "submitted",
            "option_number": option_number,
            "option_index": option_number - 1,
            "event_selection": {
                "postcondition_verified": True,
                "old_event_instance_id": 30,
                "new_event_instance_id": 31,
                "selected_option_number": option_number,
                "selected_native_option_index": option_number - 1,
            },
        }

    def execute_step(
        self, step: str, *, expected_revision: int
    ) -> dict[str, object]:
        require(expected_revision == self.revision, "PIP settle used stale revision")
        self.steps.append(step)
        return {"accepted": True}


def _known_vanilla_no_secrets_context(
    *, councillor_character_id: int = 27963
) -> dict[str, object]:
    expected = capture.KNOWN_PRE_BOOTSTRAP_VANILLA_NO_SECRETS_EVENT

    def character_scope(name: str, character_id: int) -> dict[str, object]:
        return {
            "name": name,
            "scope": {
                "status": "available",
                "type_key": "character",
                "typed_identity": {
                    "status": "available",
                    "kind": "character",
                    "character_id": character_id,
                },
            },
        }

    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "snapshot_revision": 82,
        "date_raw": expected["date_raw"],
        "current_event_instance_id": 40,
        "window_match_count": 1,
        "event_definition_key": expected["event_definition_key"],
        "calculated_event_id": 5080399,
        "root_scope": {
            "typed_identity": {
                "status": "available",
                "kind": "character",
                "character_id": expected["root_character_id"],
            }
        },
        "saved_scopes": [
            character_scope("councillor", councillor_character_id),
            character_scope(
                "councillor_liege",
                expected["councillor_liege_character_id"],
            ),
            character_scope(
                "target_character", expected["target_character_id"]
            ),
            {
                "name": expected["required_boolean_scope"],
                "scope": {
                    "status": "available",
                    "type_key": "boolean",
                    "typed_identity": {
                        "status": "unavailable",
                        "reason": "generic_scope_payload_identity_not_closed",
                    },
                },
            },
        ],
        "options": [
            {
                "rendered_index": index,
                "native_option_index": index,
                "shown": True,
                "enabled": True,
                "fallback": False,
                "cancel": False,
            }
            for index in range(expected["option_count"])
        ],
    }


class KnownVanillaNoSecretsPrebootstrapService:
    def __init__(self, *, councillor_character_id: int = 27963) -> None:
        self.state = "no_secrets"
        self.revision = 82
        self.councillor_character_id = councillor_character_id
        self.selections: list[tuple[int, int, int]] = []

    def snapshot(self) -> dict[str, object]:
        expected = capture.KNOWN_PRE_BOOTSTRAP_VANILLA_NO_SECRETS_EVENT
        active_event = (
            {"source": "native", "instance_id": 40, "option_count": 2}
            if self.state == "no_secrets"
            else {"source": "native", "instance_id": 41, "option_count": 1}
        )
        return {
            "revision": self.revision,
            "date_raw": expected["date_raw"],
            "paused": True,
            "map_ready": True,
            "speed": 1,
            "active_event": active_event,
        }

    def query_current_event_window_context_v1(
        self, event_instance_id: int, **_kwargs: object
    ) -> dict[str, object]:
        if self.state == "no_secrets":
            require(event_instance_id == 40, "wrong no-secrets instance queried")
            return {
                "current_event_window_context": (
                    _known_vanilla_no_secrets_context(
                        councillor_character_id=self.councillor_character_id
                    )
                )
            }
        require(event_instance_id == 41, "wrong seed instance queried")
        return {
            "current_event_window_context": {
                "event_definition_key": capture.SEED_EVENT_DEFINITION_KEY
            }
        }

    def select_event_option(
        self,
        option_number: int,
        *,
        event_instance_id: int,
        expected_revision: int,
    ) -> dict[str, object]:
        self.selections.append(
            (option_number, event_instance_id, expected_revision)
        )
        require(self.state == "no_secrets", "no-secrets event selected twice")
        require(option_number == 2, "no-secrets keep-task option drifted")
        self.state = "seed"
        self.revision += 1
        return {
            "step": "select-event-option-2",
            "accepted": True,
            "status": "submitted",
            "option_number": 2,
            "option_index": 1,
            "event_selection": {
                "postcondition_verified": True,
                "old_event_instance_id": 40,
                "new_event_instance_id": 41,
                "selected_option_number": 2,
                "selected_native_option_index": 1,
            },
        }


class RegisteredPrebootstrapSequenceService:
    """Expose the product card, exact vanilla interruption, then the seed."""

    def __init__(self) -> None:
        self.state = "product"
        self.revision = 5
        self.selections: list[tuple[int, int, int]] = []

    def snapshot(self) -> dict[str, object]:
        if self.state == "product":
            date_raw = capture.KNOWN_PRE_BOOTSTRAP_EVENT["date_raw"]
            active_event = {
                "source": "native",
                "instance_id": 10,
                "option_count": 4,
            }
        elif self.state == "vanilla":
            date_raw = capture.KNOWN_PRE_BOOTSTRAP_VANILLA_EVENT["date_raw"]
            active_event = {
                "source": "native",
                "instance_id": 20,
                "option_count": 2,
            }
        else:
            date_raw = capture.KNOWN_PRE_BOOTSTRAP_VANILLA_EVENT["date_raw"]
            active_event = {
                "source": "native",
                "instance_id": 21,
                "option_count": 1,
            }
        return {
            "revision": self.revision,
            "date_raw": date_raw,
            "paused": True,
            "map_ready": True,
            "speed": 1,
            "active_event": active_event,
        }

    def query_current_event_window_context_v1(
        self, event_instance_id: int, **_kwargs: object
    ) -> dict[str, object]:
        if self.state == "product":
            require(event_instance_id == 10, "wrong product event queried")
            return {"current_event_window_context": _known_predecessor_context()}
        if self.state == "vanilla":
            require(event_instance_id == 20, "wrong vanilla event queried")
            return {"current_event_window_context": _known_vanilla_context()}
        require(event_instance_id == 21, "wrong seed event queried")
        return {
            "current_event_window_context": {
                "event_definition_key": capture.SEED_EVENT_DEFINITION_KEY
            }
        }

    def select_event_option(
        self,
        option_number: int,
        *,
        event_instance_id: int,
        expected_revision: int,
    ) -> dict[str, object]:
        self.selections.append(
            (option_number, event_instance_id, expected_revision)
        )
        if self.state == "product":
            require(option_number == 1, "product option drifted")
            old_id, new_id, selected_index = 10, 20, 0
            self.state = "vanilla"
        else:
            require(self.state == "vanilla", "unexpected sequence selection")
            require(option_number == 2, "vanilla option drifted")
            old_id, new_id, selected_index = 20, 21, 1
            self.state = "seed"
        self.revision += 1
        return {
            "step": f"select-event-option-{option_number}",
            "accepted": True,
            "status": "submitted",
            "option_number": option_number,
            "option_index": selected_index,
            "event_selection": {
                "postcondition_verified": True,
                "old_event_instance_id": old_id,
                "new_event_instance_id": new_id,
                "selected_option_number": option_number,
                "selected_native_option_index": selected_index,
            },
        }


def test_exact_known_predecessor_is_drained_once() -> None:
    with tempfile.TemporaryDirectory() as raw:
        artifacts = Path(raw)
        service = KnownPredecessorService()
        snapshot = capture.wait_for_bootstrap_event(
            service,
            artifacts,
            bridge_unavailable_error=FakeBridgeUnavailableError,
            timeout_seconds=10.0,
            source_save_sha256=capture.KNOWN_PRE_BOOTSTRAP_EVENT[
                "source_save_sha256"
            ],
            clock=FakeTime().clock,
            sleeper=lambda _seconds: None,
        )
        require(
            snapshot["active_event"] == {"instance_id": 11, "option_count": 1},
            "waiter did not reach the exact seed event after predecessor drain",
        )
        require(
            service.selections == [(1, 10, 5)],
            "known predecessor was not closed exactly once with option 1",
        )
        drain = json.loads(
            (artifacts / "known-pre-bootstrap-event-drain.json").read_text(
                encoding="utf-8"
            )
        )
        require(drain["result"] == "GREEN", "predecessor drain lacks GREEN proof")
        require(
            all(drain["identity_checks"].values())
            and all(drain["selection_checks"].values()),
            "predecessor drain did not preserve its exact identity/ACK gates",
        )
        require(
            drain["observed_calculated_event_id"] == 3030004,
            "process-local calculated event ID was not retained as evidence",
        )


def test_calculated_event_id_is_observed_but_not_an_identity_gate() -> None:
    with tempfile.TemporaryDirectory() as raw:
        artifacts = Path(raw)
        service = KnownPredecessorService(calculated_event_id=2990004)
        capture.wait_for_bootstrap_event(
            service,
            artifacts,
            bridge_unavailable_error=FakeBridgeUnavailableError,
            timeout_seconds=10.0,
            source_save_sha256=capture.KNOWN_PRE_BOOTSTRAP_EVENT[
                "source_save_sha256"
            ],
            clock=FakeTime().clock,
            sleeper=lambda _seconds: None,
        )
        drain = json.loads(
            (artifacts / "known-pre-bootstrap-event-drain.json").read_text(
                encoding="utf-8"
            )
        )
        require(drain["result"] == "GREEN", "unstable engine ID blocked drain")
        require(
            drain["observed_calculated_event_id"] == 2990004,
            "drifted engine ID was not retained as a non-gating observation",
        )
        require(
            "calculated_event_id" not in drain["identity_checks"],
            "unstable engine ID remained an identity check",
        )


def test_exact_vanilla_prebootstrap_event_uses_option_two() -> None:
    with tempfile.TemporaryDirectory() as raw:
        artifacts = Path(raw)
        service = KnownVanillaPrebootstrapService()
        snapshot = capture.wait_for_bootstrap_event(
            service,
            artifacts,
            bridge_unavailable_error=FakeBridgeUnavailableError,
            timeout_seconds=10.0,
            source_save_sha256=capture.KNOWN_PRE_BOOTSTRAP_VANILLA_EVENT[
                "source_save_sha256"
            ],
            clock=FakeTime().clock,
            sleeper=lambda _seconds: None,
        )
        require(
            snapshot["active_event"]
            == {"source": "native", "instance_id": 21, "option_count": 1},
            "waiter did not reach the seed after the vanilla interruption",
        )
        require(
            service.selections == [(2, 20, 8)],
            "spymaster_task.0381 was not closed exactly once with option 2",
        )
        drain = json.loads(
            (
                artifacts / "known-pre-bootstrap-vanilla-event-drain.json"
            ).read_text(encoding="utf-8")
        )
        require(
            drain["state"] == "known_pre_bootstrap_vanilla_event_drained"
            and drain["result"] == "GREEN",
            "exact vanilla drain lacks typed GREEN evidence",
        )
        require(
            all(drain["identity_checks"].values())
            and all(drain["selection_checks"].values()),
            "vanilla drain did not retain all identity and ACK gates",
        )
        require(
            drain["wait_policy"] == "continue_under_original_total_deadline",
            "vanilla drain silently introduced a short secondary deadline",
        )


def test_exact_b2_pip_prebootstrap_event_uses_accept_option() -> None:
    with tempfile.TemporaryDirectory() as raw:
        artifacts = Path(raw)
        service = KnownB2PipPrebootstrapService()
        snapshot = capture.wait_for_bootstrap_event(
            service,
            artifacts,
            bridge_unavailable_error=FakeBridgeUnavailableError,
            timeout_seconds=10.0,
            source_save_sha256=capture.KNOWN_PRE_BOOTSTRAP_B2_PIP_EVENT[
                "source_save_sha256"
            ],
            clock=FakeTime().clock,
            sleeper=lambda _seconds: None,
        )
        require(
            snapshot["active_event"]
            == {"source": "native", "instance_id": 31, "option_count": 1},
            "waiter did not reach the seed after the exact B2 PIP drain",
        )
        require(
            service.selections == [(1, 30, 7)],
            "exact B2 PIP was not accepted once with native option zero",
        )
        drain = json.loads(
            (
                artifacts / "known-pre-bootstrap-b2-pip-event-drain.json"
            ).read_text(encoding="utf-8")
        )
        require(
            drain["state"] == "known_pre_bootstrap_b2_pip_event_drained"
            and drain["result"] == "GREEN",
            "exact B2 PIP drain lacks typed GREEN evidence",
        )
        require(
            all(drain["identity_checks"].values())
            and all(drain["selection_checks"].values()),
            "B2 PIP drain did not retain every identity and ACK gate",
        )


def test_manager_b2_pip_route_uses_refuse_option_only() -> None:
    with tempfile.TemporaryDirectory() as raw:
        artifacts = Path(raw)
        service = KnownB2PipPrebootstrapService(
            selected_option_number=3,
            final_event_definition_key=capture.MANAGER_SEED_EVENT_DEFINITION_KEY,
        )
        snapshot = capture.wait_for_bootstrap_event(
            service,
            artifacts,
            bridge_unavailable_error=FakeBridgeUnavailableError,
            timeout_seconds=10.0,
            expected_event_definition_key=capture.MANAGER_SEED_EVENT_DEFINITION_KEY,
            source_save_sha256=capture.KNOWN_PRE_BOOTSTRAP_B2_PIP_EVENT[
                "source_save_sha256"
            ],
            maximum_date_raw=capture.KNOWN_PRE_BOOTSTRAP_B2_PIP_EVENT["date_raw"],
            expected_event_date_raw=capture.KNOWN_PRE_BOOTSTRAP_B2_PIP_EVENT[
                "date_raw"
            ],
            known_prebootstrap_drain_allowlist=("zg361b2.40",),
            known_b2_pip_option_number=3,
            timeline_speed=5,
            clock=FakeTime().clock,
            sleeper=lambda _seconds: None,
        )
        require(
            snapshot["date_raw"]
            == capture.KNOWN_PRE_BOOTSTRAP_B2_PIP_EVENT["date_raw"],
            "manager event did not remain on the exact PIP date",
        )
        require(
            service.selections == [(3, 30, 7)],
            "manager route did not use refusal option three exactly once",
        )
        drain = json.loads(
            (
                artifacts / "known-pre-bootstrap-b2-pip-event-drain.json"
            ).read_text(encoding="utf-8")
        )
        require(
            drain["selection"]["option_number"] == 3
            and drain["selection"]["option_index"] == 2
            and all(drain["selection_checks"].values()),
            "manager PIP refusal lost its exact native option proof",
        )


def test_manager_post_activation_gui_settles_while_paused() -> None:
    with tempfile.TemporaryDirectory() as raw:
        artifacts = Path(raw)
        service = KnownB2PipPrebootstrapService(
            selected_option_number=3,
            final_event_definition_key=capture.MANAGER_SEED_EVENT_DEFINITION_KEY,
            post_drain_empty_snapshots=3,
        )
        fake_time = FakeTime()
        snapshot = capture.wait_for_bootstrap_event(
            service,
            artifacts,
            bridge_unavailable_error=FakeBridgeUnavailableError,
            timeout_seconds=10.0,
            expected_event_definition_key=capture.MANAGER_SEED_EVENT_DEFINITION_KEY,
            source_save_sha256=capture.KNOWN_PRE_BOOTSTRAP_B2_PIP_EVENT[
                "source_save_sha256"
            ],
            maximum_date_raw=capture.KNOWN_PRE_BOOTSTRAP_B2_PIP_EVENT["date_raw"],
            expected_event_date_raw=capture.KNOWN_PRE_BOOTSTRAP_B2_PIP_EVENT[
                "date_raw"
            ],
            known_prebootstrap_drain_allowlist=("zg361b2.40",),
            known_b2_pip_option_number=3,
            post_activation_event_definition_key="zg361b2.40",
            post_activation_paused_settle_seconds=1.0,
            timeline_speed=5,
            clock=fake_time.clock,
            sleeper=fake_time.sleep,
        )
        require(
            snapshot["active_event"]
            == {"source": "native", "instance_id": 31, "option_count": 1},
            "paused GUI settle did not reach the manager event",
        )
        require(
            service.steps == [],
            f"paused GUI settle advanced the game timeline: {service.steps}",
        )
        wait_rows = rows(artifacts / "bootstrap-event-wait.jsonl")
        require(
            any(
                row.get("state") == "post_activation_gui_settle_started"
                and row.get("timeline_resume_forbidden") is True
                for row in wait_rows
            ),
            "paused GUI settle lacks its typed start evidence",
        )


def test_manager_post_activation_gui_timeout_never_resumes_map() -> None:
    with tempfile.TemporaryDirectory() as raw:
        artifacts = Path(raw)
        service = KnownB2PipPrebootstrapService(
            selected_option_number=3,
            final_event_definition_key=capture.MANAGER_SEED_EVENT_DEFINITION_KEY,
            post_drain_empty_snapshots=100,
        )
        fake_time = FakeTime()
        try:
            capture.wait_for_bootstrap_event(
                service,
                artifacts,
                bridge_unavailable_error=FakeBridgeUnavailableError,
                timeout_seconds=10.0,
                expected_event_definition_key=(
                    capture.MANAGER_SEED_EVENT_DEFINITION_KEY
                ),
                source_save_sha256=(
                    capture.KNOWN_PRE_BOOTSTRAP_B2_PIP_EVENT[
                        "source_save_sha256"
                    ]
                ),
                maximum_date_raw=(
                    capture.KNOWN_PRE_BOOTSTRAP_B2_PIP_EVENT["date_raw"]
                ),
                expected_event_date_raw=(
                    capture.KNOWN_PRE_BOOTSTRAP_B2_PIP_EVENT["date_raw"]
                ),
                known_prebootstrap_drain_allowlist=("zg361b2.40",),
                known_b2_pip_option_number=3,
                post_activation_event_definition_key="zg361b2.40",
                post_activation_paused_settle_seconds=0.25,
                timeline_speed=5,
                clock=fake_time.clock,
                sleeper=fake_time.sleep,
            )
        except capture.SeedCaptureError as error:
            evidence = error.evidence
        else:
            raise AssertionError("post-activation GUI timeout false-GREENed")
        require(
            evidence.get("state") == "post_activation_gui_settle_timeout"
            and evidence.get("timeline_resumed_after_activation") is False
            and evidence.get("date_raw")
            == capture.KNOWN_PRE_BOOTSTRAP_B2_PIP_EVENT["date_raw"],
            f"post-activation timeout evidence drifted: {evidence}",
        )
        require(
            service.steps == [],
            f"post-activation timeout resumed the map: {service.steps}",
        )


def test_clean_manager_continuation_uses_one_date_only_sentinel() -> None:
    class CleanBoundarySentinelService:
        def __init__(self) -> None:
            self.revision = 90
            self.event_ready = False
            self.steps: list[str] = []
            self.date_raw = 53154144
            self.driver = self

        def snapshot(self) -> dict[str, object]:
            return {
                "snapshot_id": f"native:{self.revision}",
                "revision": self.revision,
                "native_revision": self.revision,
                "date_raw": self.date_raw,
                "paused": True,
                "speed": 5,
                "map_ready": True,
                "player_armies": [],
                "played_character": {"character_id": 32904},
                "active_event": (
                    {"source": "native", "instance_id": 91, "option_count": 1}
                    if self.event_ready
                    else None
                ),
            }

        def _execute_primitive_step(
            self,
            step: str,
            *,
            expected_revision: int | None,
            required_capability: str | None = None,
            timeout_seconds: float,
            internal_semantic_snapshot: bool,
        ) -> dict[str, object]:
            require(expected_revision is None, "sentinel used a stale public revision")
            require(timeout_seconds > 0, "sentinel timeout was not positive")
            require(internal_semantic_snapshot, "sentinel used the public view")
            self.steps.append(step)
            status = {
                "state": "armed",
                "generation": 4,
                "starting_date_raw": 53154144,
                "target_date_raw": 53154168,
                "last_observed_date_raw": 53154144,
                "trigger_date_raw": 0,
                "speed": 5,
                "mode": "terminal_or_sentinel",
                "army_count": 0,
                "combat_count": 0,
                "completed_daily_ticks": 0,
                "intermediate_pause_count": 0,
                "trigger_flags": 0,
                "trigger_reasons": [],
                "signed_date_delta_from_target_raw": 0,
                "overshoot_days": -1,
                "pause_wrapper_called": False,
                "pause_observed": False,
                "terminal_observed": False,
                "abnormal": False,
            }
            if step.startswith("research-arm-tactical-daily-sentinel-v1-"):
                require(
                    required_capability
                    == "game.command.research-arm-tactical-daily-sentinel-v1-N",
                    "sentinel arm capability drifted",
                )
                return {
                    "step": step,
                    "accepted": True,
                    "status": "available",
                    "tactical_daily_sentinel": status,
                }
            if step == "resume-map":
                require(required_capability is None, "resume gained a research cap")
                self.date_raw += 24
                self.revision += 1
                self.event_ready = True
                return {"step": step, "accepted": True, "status": "submitted"}
            require(
                step == "research-query-tactical-daily-sentinel-v1",
                f"unexpected sentinel step: {step}",
            )
            require(
                required_capability
                == "game.command.research-query-tactical-daily-sentinel-v1",
                "sentinel status capability drifted",
            )
            return {
                "step": step,
                "accepted": True,
                "status": "available",
                "tactical_daily_sentinel": {
                    **status,
                    "state": "triggered",
                    "last_observed_date_raw": 53154168,
                    "trigger_date_raw": 53154168,
                    "completed_daily_ticks": 1,
                    "trigger_flags": 1,
                    "trigger_reasons": ["date_deadline"],
                    "overshoot_days": 0,
                    "pause_wrapper_called": True,
                    "pause_observed": True,
                },
            }

        def query_current_event_window_context_v1(
            self, event_instance_id: int, *, expected_revision: int
        ) -> dict[str, object]:
            require(event_instance_id == 91, "pulse event instance drifted")
            require(expected_revision == self.revision, "pulse query revision drifted")
            return {
                "current_event_window_context": {
                    "event_definition_key": capture.MANAGER_SEED_EVENT_DEFINITION_KEY,
                }
            }

    with tempfile.TemporaryDirectory() as raw:
        artifacts = Path(raw)
        service = CleanBoundarySentinelService()
        fake_time = FakeTime()
        snapshot = capture.wait_for_bootstrap_event(
            service,
            artifacts,
            bridge_unavailable_error=FakeBridgeUnavailableError,
            timeout_seconds=10.0,
            expected_event_definition_key=capture.MANAGER_SEED_EVENT_DEFINITION_KEY,
            maximum_date_raw=53154168,
            expected_event_date_raw=53154168,
            allow_known_prebootstrap_drains=False,
            initial_paused_event_settle_seconds=0.2,
            initial_paused_date_sentinel=True,
            timeline_speed=5,
            clock=fake_time.clock,
            sleeper=fake_time.sleep,
        )
        require(
            snapshot["date_raw"] == 53154168
            and snapshot["active_event"]["instance_id"] == 91,
            f"date-only activation sentinel lost its event: {snapshot}",
        )
        require(
            service.steps
            == [
                "research-arm-tactical-daily-sentinel-v1-53154144-to-53154168-speed-5-mode-terminal-a-0",
                "resume-map",
                "research-query-tactical-daily-sentinel-v1",
            ],
            f"date sentinel transport drifted: {service.steps}",
        )
        wait_rows = rows(artifacts / "bootstrap-event-wait.jsonl")
        require(
            any(
                row.get("state")
                == "manager_continuation_date_sentinel_stopped"
                and row.get("resume_submission_count") == 1
                and row.get("external_pause_used") is False
                and row.get("timeline_speed") == 5
                for row in wait_rows
            ),
            "date-only activation sentinel lacks typed evidence",
        )


def test_b2_pip_prebootstrap_identity_drift_fails_closed() -> None:
    with tempfile.TemporaryDirectory() as raw:
        service = KnownB2PipPrebootstrapService(
            prompt_owner_character_id=99999
        )
        try:
            capture.wait_for_bootstrap_event(
                service,
                Path(raw),
                bridge_unavailable_error=FakeBridgeUnavailableError,
                timeout_seconds=10.0,
                source_save_sha256=capture.KNOWN_PRE_BOOTSTRAP_B2_PIP_EVENT[
                    "source_save_sha256"
                ],
                clock=FakeTime().clock,
                sleeper=lambda _seconds: None,
            )
            raise AssertionError("identity-drifted B2 PIP was selected")
        except capture.SeedCaptureError as error:
            require(
                error.evidence["state"]
                == "known_pre_bootstrap_b2_pip_event_identity_mismatch",
                "B2 PIP identity mismatch lacks its typed RED state",
            )
            require(
                error.evidence["identity_checks"][
                    "prompt_owner_character_id"
                ]
                is False,
                "B2 PIP owner drift was not exposed",
            )
        require(
            not service.selections,
            "identity-drifted B2 PIP crossed the action boundary",
        )


def test_exact_vanilla_no_secrets_event_keeps_current_task() -> None:
    with tempfile.TemporaryDirectory() as raw:
        artifacts = Path(raw)
        service = KnownVanillaNoSecretsPrebootstrapService()
        snapshot = capture.wait_for_bootstrap_event(
            service,
            artifacts,
            bridge_unavailable_error=FakeBridgeUnavailableError,
            timeout_seconds=10.0,
            source_save_sha256=(
                capture.KNOWN_PRE_BOOTSTRAP_VANILLA_NO_SECRETS_EVENT[
                    "source_save_sha256"
                ]
            ),
            clock=FakeTime().clock,
            sleeper=lambda _seconds: None,
        )
        require(
            snapshot["active_event"]
            == {"source": "native", "instance_id": 41, "option_count": 1},
            "waiter did not reach seed after the no-secrets event drain",
        )
        require(
            service.selections == [(2, 40, 82)],
            "no-secrets event did not keep the current task with option two",
        )
        drain = json.loads(
            (
                artifacts
                / "known-pre-bootstrap-vanilla-no-secrets-event-drain.json"
            ).read_text(encoding="utf-8")
        )
        require(
            drain["state"]
            == "known_pre_bootstrap_vanilla_no_secrets_event_drained"
            and drain["result"] == "GREEN",
            "no-secrets event drain lacks typed GREEN evidence",
        )
        require(
            all(drain["identity_checks"].values())
            and all(drain["selection_checks"].values()),
            "no-secrets drain lost an identity or ACK gate",
        )


def test_r120_source_hash_is_exactly_authorized_for_b2_sequence() -> None:
    r120_hash = (
        "8e6ceb97e97cd6b9185ebbcce38b42fc087e0b800cd5e321037c9f29a79e45b9"
    )
    unexpected_hash = "0" * 64
    service_rows = (
        (
            KnownB2PipPrebootstrapService(),
            _known_b2_pip_context(),
            capture.KNOWN_PRE_BOOTSTRAP_B2_PIP_EVENT,
            capture._known_pre_bootstrap_b2_pip_event_checks,
            30,
        ),
        (
            KnownVanillaNoSecretsPrebootstrapService(),
            _known_vanilla_no_secrets_context(),
            capture.KNOWN_PRE_BOOTSTRAP_VANILLA_NO_SECRETS_EVENT,
            capture._known_pre_bootstrap_vanilla_no_secrets_event_checks,
            40,
        ),
    )
    for service, context, expected, checker, event_instance_id in service_rows:
        require(
            expected["source_save_sha256"] in expected["source_save_sha256s"]
            and r120_hash in expected["source_save_sha256s"]
            and len(expected["source_save_sha256s"]) == 2,
            "exact old/R120 source hash allowlist drifted",
        )
        accepted = checker(
            source_save_sha256=r120_hash,
            snapshot=service.snapshot(),
            context=context,
            event_instance_id=event_instance_id,
        )
        rejected = checker(
            source_save_sha256=unexpected_hash,
            snapshot=service.snapshot(),
            context=context,
            event_instance_id=event_instance_id,
        )
        require(all(accepted.values()), "R120 exact source hash was not accepted")
        require(
            rejected["source_save_sha256"] is False
            and all(
                value
                for key, value in rejected.items()
                if key != "source_save_sha256"
            ),
            "unregistered source hash did not fail only the exact hash gate",
        )


def test_vanilla_no_secrets_identity_drift_fails_closed() -> None:
    with tempfile.TemporaryDirectory() as raw:
        service = KnownVanillaNoSecretsPrebootstrapService(
            councillor_character_id=99999
        )
        try:
            capture.wait_for_bootstrap_event(
                service,
                Path(raw),
                bridge_unavailable_error=FakeBridgeUnavailableError,
                timeout_seconds=10.0,
                source_save_sha256=(
                    capture.KNOWN_PRE_BOOTSTRAP_VANILLA_NO_SECRETS_EVENT[
                        "source_save_sha256"
                    ]
                ),
                clock=FakeTime().clock,
                sleeper=lambda _seconds: None,
            )
            raise AssertionError("identity-drifted no-secrets event was selected")
        except capture.SeedCaptureError as error:
            require(
                error.evidence["state"]
                == (
                    "known_pre_bootstrap_vanilla_no_secrets_event_"
                    "identity_mismatch"
                ),
                "no-secrets identity mismatch lacks its typed RED state",
            )
            require(
                error.evidence["identity_checks"]["councillor_character_id"]
                is False,
                "no-secrets councillor drift was not exposed",
            )
        require(
            not service.selections,
            "identity-drifted no-secrets event crossed the action boundary",
        )


def test_multiple_registered_prebootstrap_events_are_supported() -> None:
    with tempfile.TemporaryDirectory() as raw:
        artifacts = Path(raw)
        service = RegisteredPrebootstrapSequenceService()
        snapshot = capture.wait_for_bootstrap_event(
            service,
            artifacts,
            bridge_unavailable_error=FakeBridgeUnavailableError,
            timeout_seconds=10.0,
            source_save_sha256=capture.KNOWN_PRE_BOOTSTRAP_EVENT[
                "source_save_sha256"
            ],
            clock=FakeTime().clock,
            sleeper=lambda _seconds: None,
        )
        require(
            snapshot["active_event"]["instance_id"] == 21,
            "registered event sequence did not reach the seed",
        )
        require(
            service.selections == [(1, 10, 5), (2, 20, 6)],
            "registered events were not drained in their explicit option order",
        )
        require(
            (artifacts / "known-pre-bootstrap-event-drain.json").is_file()
            and (
                artifacts / "known-pre-bootstrap-vanilla-event-drain.json"
            ).is_file(),
            "one registered event drain overwrote or omitted the other",
        )


def test_vanilla_prebootstrap_identity_and_option_shape_fail_closed() -> None:
    expected_save = capture.KNOWN_PRE_BOOTSTRAP_VANILLA_EVENT[
        "source_save_sha256"
    ]
    for root_id, character_to_hook_id, option_fallback, source_save, failed_check in (
        (99999, 44001, False, expected_save, "root_character_id"),
        (
            29037,
            29037,
            False,
            expected_save,
            "character_to_hook_excludes_known_principals",
        ),
        (
            29037,
            32904,
            False,
            expected_save,
            "character_to_hook_excludes_known_principals",
        ),
        (29037, 44001, True, expected_save, "authored_options_exact"),
        (29037, 44001, False, "0" * 64, "source_save_sha256"),
    ):
        with tempfile.TemporaryDirectory() as raw:
            artifacts = Path(raw)
            service = KnownVanillaPrebootstrapService(
                root_character_id=root_id,
                character_to_hook_id=character_to_hook_id,
                second_option_fallback=option_fallback,
            )
            try:
                capture.wait_for_bootstrap_event(
                    service,
                    artifacts,
                    bridge_unavailable_error=FakeBridgeUnavailableError,
                    timeout_seconds=10.0,
                    source_save_sha256=source_save,
                    clock=FakeTime().clock,
                    sleeper=lambda _seconds: None,
                )
                raise AssertionError("drifted vanilla interruption was selected")
            except capture.SeedCaptureError as error:
                require(
                    error.evidence["state"]
                    == "known_pre_bootstrap_vanilla_event_identity_mismatch",
                    "vanilla identity mismatch lacks its typed RED state",
                )
                require(
                    error.evidence["identity_checks"][failed_check] is False,
                    f"expected failed identity check was not preserved: {failed_check}",
                )
            require(
                not service.selections,
                "identity-drifted vanilla event crossed the action boundary",
            )


def test_unregistered_vanilla_event_remains_unexpected_red() -> None:
    with tempfile.TemporaryDirectory() as raw:
        service = KnownVanillaPrebootstrapService(event_key="spymaster_task.0398")
        try:
            capture.wait_for_bootstrap_event(
                service,
                Path(raw),
                bridge_unavailable_error=FakeBridgeUnavailableError,
                timeout_seconds=10.0,
                source_save_sha256=capture.KNOWN_PRE_BOOTSTRAP_VANILLA_EVENT[
                    "source_save_sha256"
                ],
                clock=FakeTime().clock,
                sleeper=lambda _seconds: None,
            )
            raise AssertionError("unregistered vanilla event was ignored")
        except capture.SeedCaptureError as error:
            require(
                error.evidence["state"] == "unexpected_visible_event"
                and error.evidence["observed_event_definition_key"]
                == "spymaster_task.0398",
                "unregistered vanilla event did not retain explicit RED evidence",
            )
        require(not service.selections, "unregistered vanilla event was selected")


def test_vanilla_drain_keeps_original_deadline_and_resumes_timeline() -> None:
    with tempfile.TemporaryDirectory() as raw:
        service = KnownVanillaPrebootstrapService(reaches_seed=False)
        fake_time = FakeTime()
        try:
            capture.wait_for_bootstrap_event(
                service,
                Path(raw),
                bridge_unavailable_error=FakeBridgeUnavailableError,
                timeout_seconds=0.35,
                source_save_sha256=capture.KNOWN_PRE_BOOTSTRAP_VANILLA_EVENT[
                    "source_save_sha256"
                ],
                clock=fake_time.clock,
                sleeper=fake_time.sleep,
            )
            raise AssertionError("missing seed escaped the original total deadline")
        except capture.SeedCaptureError as error:
            require(
                error.evidence["state"]
                == "bootstrap_event_timeout_after_known_prebootstrap_events",
                "post-drain timeout lacks its typed terminal",
            )
            require(
                error.evidence["known_pre_bootstrap_vanilla_event_drained"] is True
                and error.evidence["drained_pre_bootstrap_events"]
                == ["spymaster_task.0381"],
                "post-drain timeout lost the exact event history",
            )
            require(
                error.evidence["wait_policy"]
                == "original_total_deadline_not_reset_by_drains",
                "post-drain timeout used an undeclared secondary deadline",
            )
        require(
            fake_time.value >= 0.35,
            "event drain truncated the configured total wait",
        )
        require(
            "resume-map" in service.steps,
            "timeline remained paused after the incidental event closed",
        )


def test_vanilla_selection_ack_must_confirm_native_option_two() -> None:
    with tempfile.TemporaryDirectory() as raw:
        artifacts = Path(raw)
        service = KnownVanillaPrebootstrapService(wrong_selection_ack=True)
        try:
            capture.wait_for_bootstrap_event(
                service,
                artifacts,
                bridge_unavailable_error=FakeBridgeUnavailableError,
                timeout_seconds=10.0,
                source_save_sha256=capture.KNOWN_PRE_BOOTSTRAP_VANILLA_EVENT[
                    "source_save_sha256"
                ],
                clock=FakeTime().clock,
                sleeper=lambda _seconds: None,
            )
            raise AssertionError("wrong native option index false-GREENed")
        except capture.SeedCaptureError as error:
            require(
                error.evidence["state"]
                == "known_pre_bootstrap_vanilla_event_selection_red",
                "wrong option ACK lacks its typed RED state",
            )
            require(
                error.evidence["selection_checks"]["option_index"] is False
                and error.evidence["selection_checks"][
                    "selected_native_option_index"
                ]
                is False,
                "wrong native option index was not exposed",
            )


def test_pause_revision_race_reloads_snapshot_and_retries() -> None:
    class RacingPauseService:
        def __init__(self) -> None:
            self.revision = 5
            self.paused = False
            self.pause_attempts: list[int] = []

        def snapshot(self) -> dict[str, object]:
            return {
                "revision": self.revision,
                "date_raw": 777,
                "paused": self.paused,
                "map_ready": True,
                "speed": 1,
                "active_event": {"instance_id": 11, "option_count": 1},
            }

        def execute_step(
            self, step: str, *, expected_revision: int
        ) -> dict[str, object]:
            require(step == "pause-map", "race exercised an unexpected step")
            self.pause_attempts.append(expected_revision)
            if len(self.pause_attempts) == 1:
                self.revision += 1
                raise FakePreSubmissionRevisionMismatchError(
                    "native gameplay revision mismatch: expected 5, current 6"
                )
            require(
                expected_revision == self.revision,
                "pause retry did not use a fresh revision",
            )
            self.paused = True
            self.revision += 1
            return {"accepted": True}

        def query_current_event_window_context_v1(
            self, event_instance_id: int, **_kwargs: object
        ) -> dict[str, object]:
            require(event_instance_id == 11, "wrong seed instance queried")
            return {
                "current_event_window_context": {
                    "event_definition_key": capture.SEED_EVENT_DEFINITION_KEY
                }
            }

    with tempfile.TemporaryDirectory() as raw:
        artifacts = Path(raw)
        service = RacingPauseService()
        fake_time = FakeTime()
        snapshot = capture.wait_for_bootstrap_event(
            service,
            artifacts,
            bridge_unavailable_error=FakeBridgeUnavailableError,
            pre_submission_revision_mismatch_error=(
                FakePreSubmissionRevisionMismatchError
            ),
            timeout_seconds=10.0,
            clock=fake_time.clock,
            sleeper=fake_time.sleep,
        )
        require(snapshot["paused"] is True, "pause race did not converge")
        require(
            service.pause_attempts == [5, 6],
            "pause retry did not bind to the refreshed revision exactly once",
        )
        require(
            any(
                row["state"] == "pause_revision_changed_before_submission"
                for row in rows(artifacts / "bootstrap-event-wait.jsonl")
            ),
            "pause race retry lacks typed evidence",
        )


def test_resume_revision_race_reloads_snapshot_and_retries() -> None:
    class RacingResumeService:
        def __init__(self) -> None:
            self.revision = 4
            self.seed_ready = False
            self.resume_attempts: list[int] = []

        def snapshot(self) -> dict[str, object]:
            return {
                "revision": self.revision,
                "date_raw": 777,
                "paused": True,
                "map_ready": True,
                "speed": 1,
                "active_event": (
                    {"source": "native", "instance_id": 51, "option_count": 1}
                    if self.seed_ready
                    else None
                ),
            }

        def execute_step(
            self, step: str, *, expected_revision: int
        ) -> dict[str, object]:
            require(step == "resume-map", "race exercised an unexpected step")
            self.resume_attempts.append(expected_revision)
            if len(self.resume_attempts) == 1:
                self.revision += 1
                raise FakePreSubmissionRevisionMismatchError(
                    "native gameplay revision mismatch: expected 4, current 5"
                )
            require(
                expected_revision == self.revision,
                "resume retry did not use the refreshed revision",
            )
            self.seed_ready = True
            self.revision += 1
            return {"accepted": True}

        def query_current_event_window_context_v1(
            self, event_instance_id: int, **_kwargs: object
        ) -> dict[str, object]:
            require(event_instance_id == 51, "wrong seed instance queried")
            return {
                "current_event_window_context": {
                    "event_definition_key": capture.SEED_EVENT_DEFINITION_KEY
                }
            }

    with tempfile.TemporaryDirectory() as raw:
        artifacts = Path(raw)
        service = RacingResumeService()
        fake_time = FakeTime()
        snapshot = capture.wait_for_bootstrap_event(
            service,
            artifacts,
            bridge_unavailable_error=FakeBridgeUnavailableError,
            pre_submission_revision_mismatch_error=(
                FakePreSubmissionRevisionMismatchError
            ),
            timeout_seconds=10.0,
            clock=fake_time.clock,
            sleeper=fake_time.sleep,
        )
        require(
            snapshot["active_event"]["instance_id"] == 51,
            "resume race did not converge on the seed event",
        )
        require(
            service.resume_attempts == [4, 5],
            "resume race did not retry with a fresh revision",
        )
        require(
            any(
                row["state"]
                == "timeline_revision_changed_before_submission"
                and row["step"] == "resume-map"
                for row in rows(artifacts / "bootstrap-event-wait.jsonl")
            ),
            "resume race retry lacks typed evidence",
        )


def test_known_predecessor_identity_drift_fails_closed() -> None:
    with tempfile.TemporaryDirectory() as raw:
        artifacts = Path(raw)
        service = KnownPredecessorService(root_character_id=99999)
        try:
            capture.wait_for_bootstrap_event(
                service,
                artifacts,
                bridge_unavailable_error=FakeBridgeUnavailableError,
                timeout_seconds=10.0,
                source_save_sha256=capture.KNOWN_PRE_BOOTSTRAP_EVENT[
                    "source_save_sha256"
                ],
                clock=FakeTime().clock,
                sleeper=lambda _seconds: None,
            )
            raise AssertionError("drifted known predecessor escaped its identity gate")
        except capture.SeedCaptureError as error:
            require(
                error.evidence["state"]
                == "known_pre_bootstrap_event_identity_mismatch",
                "known predecessor identity RED was not typed",
            )
        require(not service.selections, "identity-drifted event was selected")


def test_total_event_deadline() -> None:
    class EventFreeService:
        def __init__(self) -> None:
            self.paused = True
            self.speed = 2

        def snapshot(self) -> dict[str, object]:
            return {
                "revision": 1,
                "date_raw": 777,
                "paused": self.paused,
                "map_ready": True,
                "speed": self.speed,
                "active_event": None,
            }

        def execute_step(self, step: str, **_kwargs: object) -> None:
            if step == "set-speed-1":
                self.speed = 1
            elif step == "resume-map":
                self.paused = False

    with tempfile.TemporaryDirectory() as raw:
        artifacts = Path(raw)
        fake_time = FakeTime()
        try:
            capture.wait_for_bootstrap_event(
                EventFreeService(),
                artifacts,
                bridge_unavailable_error=FakeBridgeUnavailableError,
                timeout_seconds=0.35,
                clock=fake_time.clock,
                sleeper=fake_time.sleep,
            )
            raise AssertionError("event-free timeline escaped its total deadline")
        except capture.SeedCaptureError as error:
            require(
                error.evidence["state"] == "bootstrap_event_timeout",
                "event timeout terminal was not typed",
            )
        require(fake_time.value < 0.6, "event waiter reset or exceeded its deadline")
        require(
            rows(artifacts / "bootstrap-event-wait.jsonl")[-1]["state"]
            == "bootstrap_event_timeout",
            "bounded event wait lacks append-only RED terminal",
        )


def test_cli_validation_and_artifact_preservation() -> None:
    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        parsed = capture.parse_args(
            [
                "--clean-source",
                str(fixture.clean),
                "--attempt-dir",
                str(fixture.attempt),
                "--artifacts-dir",
                str(fixture.artifacts),
                "--source-zip",
                str(fixture.source_zip),
                "--git-sha",
                fixture.git_sha,
                "--game-dir",
                str(fixture.game),
                "--bridge-dll",
                str(fixture.dll),
                "--injector",
                str(fixture.injector),
                "--pipe",
                fixture.pipe,
                "--loader-timeout-seconds",
                "60",
                "--native-readiness-timeout-seconds",
                "13",
                "--event-timeout-seconds",
                "14",
                "--binding-timeout-seconds",
                "12",
            ]
        ).resolved()
        require(parsed.clean_source == fixture.clean.resolve(), "CLI source drifted")
        require(parsed.pipe_name == fixture.pipe, "CLI explicit pipe drifted")
        require(
            parsed.seed_purpose == capture.DEFAULT_SEED_PURPOSE
            and parsed.seed_contract
            == (fixture.clean / "tools" / "zg361_phase2_seed_contract.json").resolve(),
            "CLI default no longer preserves player-subject behavior",
        )
        require(parsed.loader_timeout_seconds == 60.0, "CLI timeout drifted")
        require(parsed.product_projection == "broad", "default product projection drifted")
        projection_manifest = fixture.root / "cli-projection.json"
        projection_manifest.write_text("{}", encoding="utf-8")
        parsed_projection = capture.parse_args(
            [
                "--clean-source", str(fixture.clean),
                "--attempt-dir", str(fixture.attempt / "projection-attempt"),
                "--artifacts-dir", str(fixture.attempt / "projection-attempt" / "artifacts"),
                "--source-zip", str(fixture.source_zip),
                "--git-sha", fixture.git_sha,
                "--game-dir", str(fixture.game),
                "--bridge-dll", str(fixture.dll),
                "--injector", str(fixture.injector),
                "--pipe", fixture.pipe,
                "--product-projection", "workforce",
                "--product-projection-manifest", str(projection_manifest),
                "--product-source", str(fixture.clean / "mod_zhongguo_style"),
            ]
        ).resolved()
        require(parsed_projection.product_projection == "workforce",
                "named product projection CLI option drifted")
        require(parsed_projection.product_projection_manifest == projection_manifest.resolve(),
                "product projection manifest CLI option drifted")
        require(parsed_projection.product_source == (fixture.clean / "mod_zhongguo_style").resolve(),
                "external product source CLI option drifted")
        parsed_preflight = capture.parse_args(
            [
                "--clean-source",
                str(fixture.clean),
                "--attempt-dir",
                str(fixture.attempt),
                "--artifacts-dir",
                str(fixture.artifacts),
                "--source-zip",
                str(fixture.source_zip),
                "--git-sha",
                fixture.git_sha,
                "--game-dir",
                str(fixture.game),
                "--bridge-dll",
                str(fixture.dll),
                "--injector",
                str(fixture.injector),
                "--pipe",
                fixture.pipe,
                "--preflight-only",
            ]
        )
        require(parsed_preflight.preflight_only is True,
                "--preflight-only CLI flag was not preserved")
        parsed_manager = capture.parse_args(
            [
                "--clean-source", str(fixture.clean),
                "--attempt-dir", str(fixture.attempt / "manager-attempt"),
                "--artifacts-dir", str(fixture.attempt / "manager-attempt" / "artifacts"),
                "--source-zip", str(fixture.source_zip),
                "--git-sha", fixture.git_sha,
                "--game-dir", str(fixture.game),
                "--bridge-dll", str(fixture.dll),
                "--injector", str(fixture.injector),
                "--pipe", fixture.pipe,
                "--seed-purpose", "player-manager",
            ]
        ).resolved()
        require(
            parsed_manager.seed_purpose == capture.MANAGER_SEED_PURPOSE
            and parsed_manager.fixture_source.name
            == "zg361_phase2_manager_seed_bootstrap"
            and parsed_manager.seed_contract
            == (
                fixture.clean
                / "tools"
                / "zg361_phase2_manager_seed_contract.json"
            ).resolve()
            and parsed_manager.materializer_module
            == "zg361_phase2_manager_seed_bootstrap",
            "--seed-purpose player-manager did not select the dedicated inputs",
        )
        transition_receipt = fixture.root / "transition-receipt.json"
        transition_receipt.write_text("{}", encoding="utf-8")
        parsed_transition = capture.parse_args(
            [
                "--clean-source", str(fixture.clean),
                "--attempt-dir", str(fixture.attempt / "transition-attempt"),
                "--artifacts-dir", str(fixture.attempt / "transition-artifacts"),
                "--source-zip", str(fixture.source_zip),
                "--git-sha", fixture.git_sha,
                "--game-dir", str(fixture.game),
                "--bridge-dll", str(fixture.dll),
                "--injector", str(fixture.injector),
                "--pipe", fixture.pipe,
                "--seed-purpose", "player-manager",
                "--manager-transition-checkpoint-receipt", str(transition_receipt),
            ]
        ).resolved()
        require(
            parsed_transition.manager_transition_checkpoint_receipt
            == transition_receipt.resolve(),
            "manager transition receipt CLI path drifted",
        )
        capture.validate_config(parsed)
        for label, invalid_timing in (
            ("NaN", float("nan")),
            ("positive infinity", float("inf")),
            ("negative infinity", float("-inf")),
        ):
            try:
                capture.validate_config(
                    replace(parsed, event_timeout_seconds=invalid_timing)
                )
                raise AssertionError(f"{label} timeout passed validation")
            except capture.SeedCaptureError as error:
                require(
                    "timing values must be positive" in str(error),
                    f"{label} timeout rejection was mistyped",
                )

        calls: list[str] = []
        invalid = replace(parsed, pipe_name="not-a-windows-pipe")
        report = capture.run_capture(invalid, runtime=fixture.runtime(calls))
        require(report["result"] == "RED", "invalid CLI contract false-GREENed")
        require(not calls, "invalid CLI contract reached a runtime dependency")
        report_path = fixture.artifacts / "runner-report.json"
        failure_path = fixture.artifacts / "runner-failures.jsonl"
        require(report_path.is_file(), "invalid preflight did not preserve a report")
        require(failure_path.is_file(), "invalid preflight did not preserve failure JSONL")
        report_hash = sha256(report_path)
        try:
            capture.run_capture(invalid, runtime=fixture.runtime([]))
            raise AssertionError("runner reused a nonempty frozen artifact directory")
        except capture.SeedCaptureError as error:
            require("not empty" in str(error), "repeat-run rejection was mistyped")
        require(
            sha256(report_path) == report_hash,
            "repeat-run rejection overwrote the preserved failure report",
        )


def test_product_projection_options_reach_isolated_bootstrap() -> None:
    """Projection selection survives CLI/config plumbing without launching CK3."""

    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        manifest = fixture.root / "workforce-projection.json"
        manifest.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "kind": "zg361_phase2_product_projection",
                    "projection": "workforce",
                    "files": ["descriptor.mod", "thumbnail.png"],
                }
            ),
            encoding="utf-8",
        )
        config = replace(
            fixture.config().resolved(),
            product_projection="workforce",
            product_projection_manifest=manifest.resolve(),
            product_source_override=(fixture.clean / "mod_zhongguo_style").resolve(),
        )
        capture.validate_config(config)
        calls: list[str] = []
        runtime = fixture.runtime(calls)
        config.profile_dir.mkdir(parents=True)
        bootstrap = capture._bootstrap_product_projection(runtime.zgrun, config)
        require(bootstrap["enabled_mods"] == list(capture.EXPECTED_ENABLED_MODS),
                "projection bootstrap changed enabled mods")
        require(
            runtime.zgrun.bootstrap_projection_kwargs
            == {
                "product_projection": "workforce",
                "product_projection_manifest": manifest.resolve(),
            },
            "named projection options did not reach isolated bootstrap",
        )
        require(calls == ["bootstrap"], "projection smoke crossed an unexpected runtime boundary")


def test_named_product_projection_requires_manifest_before_runtime() -> None:
    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        config = replace(
            fixture.config(),
            product_projection="workforce",
            seed_contract=(fixture.clean / "tools" / "zg361_phase2_seed_contract.json"),
        )
        try:
            capture.validate_config(config)
        except capture.SeedCaptureError as error:
            require(
                "requires an explicit manifest" in str(error),
                "named projection manifest requirement was mistyped",
            )
        else:
            raise AssertionError("named projection without manifest passed validation")


def test_stale_bootstrap_cannot_silently_downgrade_named_projection() -> None:
    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        manifest = fixture.root / "projection.json"
        manifest.write_text("{}", encoding="utf-8")
        config = replace(
            fixture.config().resolved(),
            product_projection="core",
            product_projection_manifest=manifest.resolve(),
        )

        class StaleBootstrap:
            def bootstrap_userdir(self, _profile: Path, _source: Path, **_kwargs: object):
                return {"manifest": {"projection": "broad"}}

        try:
            capture._bootstrap_product_projection(StaleBootstrap(), config)
        except capture.SeedCaptureError as error:
            require(
                "did not honor" in str(error),
                "stale bootstrap downgrade was not typed",
            )
            require(
                error.evidence.get("observed_projection") == "broad",
                "stale bootstrap evidence omitted observed projection",
            )
        else:
            raise AssertionError("stale bootstrap silently accepted named projection")


def test_no_launch_preflight_green_does_not_cross_native_boundary() -> None:
    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        calls: list[str] = []
        report = capture.run_preflight(
            fixture.config(),
            runtime=fixture.runtime(calls),
            _allow_fixture_static_skip=True,
        )
        require(report["result"] == "GREEN", "no-launch preflight unexpectedly RED")
        require(report["status"] == "preflight-ready" and report["ok"] is True,
                "GREEN preflight status contract drifted")
        require(report["seed_ready"] is False,
                "preflight falsely advertised a live seed")
        require(report["readiness_scope"] == "frozen_inputs_and_projection_only",
                "preflight readiness scope drifted")
        require(report["ck3_launch_attempted"] is False,
                "preflight claimed a CK3 launch")
        require(report["launch_boundary"] == "not-crossed",
                "preflight crossed the native launch boundary")
        require(report["native_session_started"] is False,
                "preflight started a native session")
        require(report["driver_opened"] is False,
                "preflight opened a bridge driver")
        require("supervisor-start" not in calls,
                "preflight reached the supervisor start")
        require("driver-open" not in calls,
                "preflight reached the bridge driver")
        require("transport-binding" not in calls,
                "preflight reached MCP transport binding")
        require(
            "generic-preflight" not in calls,
            "seed preflight regressed to the generic acceptance preflight",
        )
        static_preflight = report["static_preflight"]
        require(
            isinstance(static_preflight, dict)
            and static_preflight.get("result") == "SKIPPED"
            and "seed-specific" in str(static_preflight.get("reason")),
            "seed-specific static preflight was not selected for the injected fixture",
        )
        require(report["bootstrap"]["projection_only"] is True,
                "preflight projection was not labelled projection-only")
        report_path = fixture.artifacts / "preflight.json"
        require(report_path.is_file(), "GREEN preflight artifact is missing")
        persisted = json.loads(report_path.read_text(encoding="utf-8"))
        require(persisted == report, "preflight artifact differs from return value")


def test_no_launch_preflight_rejects_stale_critical_b2_product_source() -> None:
    """A stale staged product must fail before isolated materialization."""

    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        staged_product = fixture.root / "stale-product"
        shutil.copytree(fixture.clean / "mod_zhongguo_style", staged_product)
        stale_relative = capture.CRITICAL_B2_PRODUCT_PATHS[0]
        (staged_product / stale_relative).write_bytes(b"stale-generated-provider\n")
        calls: list[str] = []
        report = capture.run_preflight(
            replace(
                fixture.config(),
                product_source_override=staged_product,
            ),
            runtime=fixture.runtime(calls),
            _allow_fixture_static_skip=True,
        )
        require(report["result"] == "RED", "stale B2 product false-GREENed")
        require("bootstrap" not in calls, "stale B2 product reached bootstrap")
        require(
            report["checks"]["critical_b2_product_byte_equivalence"] == "RED",
            "stale B2 source did not type the failed check",
        )
        evidence = report["critical_b2_product_byte_equivalence"]
        require(isinstance(evidence, dict), "stale B2 evidence is missing")
        require(
            evidence.get("mismatches")
            == [
                {
                    "path": stale_relative,
                    "target": "product_source",
                    "reason": "bytes-differ",
                }
            ],
            "stale B2 source mismatch was not exact",
        )
        artifact = json.loads(
            (fixture.artifacts / "critical-b2-product-byte-equivalence.json")
            .read_text(encoding="utf-8")
        )
        require(artifact == evidence, "stale B2 artifact differs from report")
        require("supervisor-start" not in calls, "stale B2 source started CK3")


def test_no_launch_preflight_rejects_stale_mounted_critical_b2_product() -> None:
    """A bootstrap copy drift must fail before runtime tree acceptance/launch."""

    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        calls: list[str] = []
        runtime = fixture.runtime(calls)
        original_bootstrap = runtime.zgrun.bootstrap_userdir
        stale_relative = capture.CRITICAL_B2_PRODUCT_PATHS[1]

        def stale_bootstrap(
            profile: Path, product_source: Path, **kwargs: object
        ) -> dict[str, object]:
            result = original_bootstrap(profile, product_source, **kwargs)
            targets = result["targets"]
            require(isinstance(targets, dict), "fake bootstrap targets malformed")
            mounted = Path(targets["product"])
            (mounted / stale_relative).write_bytes(b"stale-mounted-provider\n")
            return result

        runtime.zgrun.bootstrap_userdir = stale_bootstrap
        report = capture.run_preflight(
            fixture.config(),
            runtime=runtime,
            _allow_fixture_static_skip=True,
        )
        require(report["result"] == "RED", "stale mounted B2 file false-GREENed")
        require("bootstrap" in calls, "mounted-byte test did not reach bootstrap")
        require(
            report["checks"]["critical_b2_product_byte_equivalence"] == "RED",
            "stale mounted B2 file did not type the failed check",
        )
        evidence = report["critical_b2_product_byte_equivalence"]
        require(isinstance(evidence, dict), "mounted B2 evidence is missing")
        require(
            evidence.get("mismatches")
            == [
                {
                    "path": stale_relative,
                    "target": "mounted_product",
                    "reason": "bytes-differ",
                }
            ],
            "stale mounted B2 mismatch was not exact",
        )
        require("supervisor-start" not in calls, "stale mounted B2 file started CK3")


def _install_list_domain_contract(fixture: Fixture) -> Path:
    source = Path(capture.__file__).with_name(
        "zg361_phase2_list_domain_acceptance_contract.json"
    )
    target = fixture.clean / "tools" / source.name
    shutil.copy2(source, target)
    fixture.rebuild_source_zip()
    return target


def test_list_domain_observer_pending_is_typed_no_launch_red() -> None:
    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        _install_list_domain_contract(fixture)
        calls: list[str] = []
        config = replace(fixture.config(), list_domain_observer_gate=True)
        report = capture.run_preflight(
            config,
            runtime=fixture.runtime(calls),
            _allow_fixture_static_skip=True,
        )
        gate = report["list_domain_observer_gate"]
        require(report["result"] == "RED", "missing native seam false-GREENed")
        require(isinstance(gate, dict), "typed observer gate was not embedded")
        require(
            gate.get("status") == "waiting-producer-histogram-v2"
            and gate.get("failure_reason") == "native_observer_manifest_pending",
            "missing native seam was not classified as waiting",
        )
        require(
            gate.get("known_live_input", {}).get("callback_slot2_rva")
            == "0x817C20",
            "known list-domain input drifted",
        )
        require("supervisor-start" not in calls, "pending seam crossed launch boundary")
        require("driver-open" not in calls, "pending seam opened a bridge driver")
        require(report["ck3_launch_attempted"] is False, "pending seam claimed launch")
        require(
            (fixture.artifacts / "list-domain-observer-gate.json").is_file(),
            "pending seam gate artifact is missing",
        )
        require(
            (fixture.artifacts / "source-tree-manifest.before.json").is_file(),
            "pending seam did not preserve the frozen source manifest",
        )


def test_list_domain_observer_manifest_binds_frozen_no_launch_inputs() -> None:
    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        _install_list_domain_contract(fixture)
        abi = fixture.clean / "ck3_autonomous_player" / "native_bridge" / "research" / "next_observer_abi.json"
        source_contract = fixture.clean / "ck3_autonomous_player" / "native_bridge" / "research" / "next_observer_contract.json"
        abi.parent.mkdir(parents=True, exist_ok=True)
        abi.write_text('{"schema_version":1}\n', encoding="utf-8")
        source_contract.write_text('{"schema_version":1}\n', encoding="utf-8")
        fixture.rebuild_source_zip()
        canonical = json.loads(
            (fixture.clean / "tools" / "zg361_phase2_list_domain_acceptance_contract.json").read_text(encoding="utf-8")
        )
        manifest = fixture.root / "native-observer-seam.json"
        manifest.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "kind": "zg361_phase2_native_observer_seam",
                    "result": "GREEN",
                    "source_git_commit": fixture.git_sha,
                    "exact_build": {
                        "game_version": "1.19.0.6",
                        "game_executable_sha256": sha256(fixture.game / "binaries" / "ck3.exe"),
                    },
                    "build": {
                        "private_option": "XAR_CK3_ENABLE_PHASE2_NEXT_OBSERVER_V1",
                        "private_option_enabled": True,
                        "bridge_dll_sha256": sha256(fixture.dll),
                        "bridge_injector_sha256": sha256(fixture.injector),
                    },
                    "session_binding": {
                        "source_zip_sha256": sha256(fixture.source_zip),
                        "clean_source_tree_sha256": capture.tree_manifest(
                            fixture.clean
                        )["tree_sha256"],
                        "pipe_name": fixture.pipe,
                    },
                    "seam": {
                        "hooks": [
                            {"rva": "0x3B9CFD2", "anchor_sha256": "b" * 64},
                            {"rva": "0x3B9CFD7", "anchor_sha256": "c" * 64},
                        ],
                        "task_register": "RBX",
                        "callback_field_offset": "0x38",
                        "heartbeat_object": "phase2_producer_slot2_histogram_observer_v2",
                        "prior_list_domain_callback_slot2_rva": "0x817C20",
                        "histogram": canonical["native_seam"]["histogram"],
                        "abi": {
                            "path": abi.relative_to(fixture.clean).as_posix(),
                            "sha256": sha256(abi),
                        },
                        "source_contract": {
                            "path": source_contract.relative_to(fixture.clean).as_posix(),
                            "sha256": sha256(source_contract),
                        },
                    },
                    "report_contract": {
                        "schema": "phase2-producer-slot2-histogram-v2",
                        "artifact_name": "phase2-producer-slot2-histogram-v2.json",
                        "required_fields": canonical["native_seam"]["required_report_fields"],
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        calls: list[str] = []
        config = replace(
            fixture.config(),
            list_domain_observer_gate=True,
            acceptance_observer_manifest=manifest,
        )
        report = capture.run_preflight(
            config,
            runtime=fixture.runtime(calls),
            _allow_fixture_static_skip=True,
        )
        gate = report["list_domain_observer_gate"]
        require(report["result"] == "GREEN", "valid frozen seam did not preflight")
        require(
            isinstance(gate, dict)
            and gate.get("status") == "static-wiring-ready"
            and gate.get("runner_observer_gate_ready") is True,
            "valid native seam did not satisfy the static wiring gate",
        )
        require(
            report["external_dependencies"]["sha256_before"]["acceptance_observer_manifest"]
            == sha256(manifest),
            "native seam manifest was not frozen as an external dependency",
        )
        require("supervisor-start" not in calls, "no-launch seam test started CK3")

        sixteen_bin_manifest = json.loads(manifest.read_text(encoding="utf-8"))
        sixteen_bin_manifest["seam"]["histogram"]["capacity"] = 16
        manifest.write_text(json.dumps(sixteen_bin_manifest), encoding="utf-8")
        rejected = capture.evaluate_observer_gate(
            contract_path=fixture.clean
            / "tools"
            / "zg361_phase2_list_domain_acceptance_contract.json",
            observer_manifest_path=manifest,
            clean_source=fixture.clean,
            frozen_git_commit=fixture.git_sha,
            game_version="1.19.0.6",
            game_executable_sha256=sha256(
                fixture.game / "binaries" / "ck3.exe"
            ),
            bridge_dll_sha256=sha256(fixture.dll),
            bridge_injector_sha256=sha256(fixture.injector),
            source_zip_sha256=sha256(fixture.source_zip),
            clean_source_tree_sha256=capture.tree_manifest(fixture.clean)[
                "tree_sha256"
            ],
            pipe_name=fixture.pipe,
        )
        require(
            rejected["result"] == "RED"
            and rejected["failure_reason"]
            == "native seam bounded histogram contract drifted",
            "16-bin native candidate bypassed the canonical 64-bin gate",
        )


def test_no_launch_preflight_missing_static_gate_is_red_without_fixture_override() -> None:
    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        calls: list[str] = []
        report = capture.run_preflight(
            fixture.config(), runtime=fixture.runtime(calls)
        )
        require(
            report["result"] == "RED",
            "real no-launch preflight skipped missing seed gate scripts",
        )
        require(
            report["status"] == "preflight-blocked" and report["ok"] is False,
            "missing seed gate scripts did not produce a blocked report",
        )
        require(
            "cannot be skipped" in str(report["failure_reason"]),
            "missing seed gate blocker was not typed",
        )
        evidence = report["failure_evidence"]
        require(
            isinstance(evidence, dict)
            and evidence.get("result") == "RED"
            and evidence.get("missing_scripts"),
            "missing seed gate evidence was not preserved",
        )
        require(
            (fixture.artifacts / "static-preflight.json").is_file(),
            "missing seed gate did not persist static evidence",
        )
        require(
            "bootstrap" not in calls
            and "supervisor-start" not in calls
            and "driver-open" not in calls,
            "missing seed gate crossed the launch/projection boundary",
        )


def test_no_launch_preflight_running_ck3_is_persisted_red() -> None:
    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        calls: list[str] = []
        runtime = fixture.runtime(calls)
        runtime.acceptance.ck3_is_running = lambda: True
        report = capture.run_preflight(fixture.config(), runtime=runtime)
        require(report["result"] == "RED", "running CK3 false-GREENed preflight")
        require(report["status"] == "preflight-blocked" and report["ok"] is False,
                "running CK3 RED status contract drifted")
        require("zero running ck3.exe" in report["failure_reason"],
                "running CK3 blocker was not typed")
        require(report["ck3_launch_attempted"] is False,
                "RED preflight claimed a CK3 launch")
        require(report["launch_boundary"] == "not-crossed",
                "RED preflight crossed the launch boundary")
        require("bootstrap" not in calls,
                "running CK3 check did not precede profile projection")
        report_path = fixture.artifacts / "preflight.json"
        require(report_path.is_file(), "RED preflight artifact is missing")
        require(
            (fixture.artifacts / "preflight-failures.jsonl").is_file(),
            "RED preflight failure stream is missing",
        )


def test_source_zip_mismatch_is_preserved() -> None:
    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        changed = fixture.clean / "mod_zhongguo_style" / "descriptor.mod"
        changed.write_text("name=drifted-product\n", encoding="utf-8")
        calls: list[str] = []
        report = capture.run_capture(
            fixture.config(), runtime=fixture.runtime(calls)
        )
        require(report["result"] == "RED", "source drift false-GREENed")
        require(not calls, "source drift reached a runtime dependency")
        evidence = report["failure_evidence"]
        require(
            isinstance(evidence, dict) and evidence.get("equivalent") is False,
            "source drift lacks exact archive/tree equivalence evidence",
        )
        require(
            evidence.get("content_mismatches")
            == ["mod_zhongguo_style/descriptor.mod"],
            "source drift mismatch path was not preserved exactly",
        )
        require(
            (fixture.artifacts / "source-zip-manifest.json").is_file()
            and (fixture.artifacts / "source-tree-manifest.before.json").is_file(),
            "source drift did not preserve both frozen manifests",
        )
        require(
            rows(fixture.artifacts / "runner-failures.jsonl")[-1][
                "failure_evidence"
            ]
            == evidence,
            "source drift evidence changed in the append-only failure stream",
        )


def test_bootstrap_runtime_hash_drift_is_preserved() -> None:
    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        calls: list[str] = []
        runtime = fixture.runtime(calls)
        original_bootstrap = runtime.zgrun.bootstrap_userdir

        def drifted_bootstrap(
            profile: Path, product_source: Path
        ) -> dict[str, object]:
            value = original_bootstrap(profile, product_source)
            hashes = value["tree_sha256"]
            require(isinstance(hashes, dict), "fake bootstrap hashes malformed")
            hashes["product"] = "0" * 64
            return value

        runtime.zgrun.bootstrap_userdir = drifted_bootstrap
        report = capture.run_capture(fixture.config(), runtime=runtime)
        require(report["result"] == "RED", "bootstrap hash drift false-GREENed")
        require(
            "supervisor-start" not in calls,
            "bootstrap hash drift started CK3",
        )
        evidence = report["failure_evidence"]
        require(
            isinstance(evidence, dict)
            and evidence["declared_tree_sha256"]["product"] == "0" * 64
            and evidence["observed_tree_sha256"]["product"] != "0" * 64,
            "bootstrap hash drift lacks declared/observed evidence",
        )
        require(
            report["runtime_unchanged"] is True,
            "bootstrap hash RED changed the projected runtime",
        )


def test_seed_source_path_must_be_absolute() -> None:
    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        contract = fixture.clean / "tools" / "zg361_phase2_seed_contract.json"
        value = json.loads(contract.read_text(encoding="utf-8"))
        value["source"]["absolute_save"] = "old-save.ck3"
        contract.write_text(json.dumps(value), encoding="utf-8")
        fixture.rebuild_source_zip()
        calls: list[str] = []
        report = capture.run_capture(
            fixture.config(), runtime=fixture.runtime(calls)
        )
        require(report["result"] == "RED", "relative seed path false-GREENed")
        require(not calls, "relative seed path reached a runtime dependency")
        require(
            "absolute_save must be absolute" in str(report["failure_reason"]),
            "relative seed path rejection was mistyped",
        )


def test_static_preflight_runs_optimized_seed_smokes() -> None:
    """Keep the seed preflight matrix aligned with the official CI smoke."""

    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        scripts = (
            "validate_static.py",
            "validate_local.py",
            "test_zg361_phase2_loader_stage.py",
            "test_zg361_phase2_seed_bootstrap.py",
            "test_zg361_phase2_seed_fixture.py",
            "test_zg361_phase2_manager_recovery_interrupts.py",
            "test_zg361_phase2_manager_recovery_tgp_interrupts.py",
            "test_zg361_phase2_manager_recovery_tribute_interrupts.py",
            "test_run_zg361_phase2_seed_capture.py",
        )
        tools_dir = fixture.clean / "tools"
        tools_dir.mkdir(parents=True, exist_ok=True)
        for name in scripts:
            if name == "validate_local.py":
                continue
            (tools_dir / name).write_text("# preflight smoke\n", encoding="utf-8")
        mod_tools_dir = fixture.clean / "mod_zhongguo_style" / "tools"
        mod_tools_dir.mkdir(parents=True, exist_ok=True)
        (mod_tools_dir / "validate_local.py").write_text(
            "# preflight smoke\n", encoding="utf-8"
        )
        fixture.artifacts.mkdir(parents=True, exist_ok=True)

        calls: list[tuple[list[str], dict[str, object]]] = []
        original_run = capture.subprocess.run

        def fake_run(command: list[str], **kwargs: object) -> SimpleNamespace:
            calls.append((list(command), dict(kwargs)))
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        capture.subprocess.run = fake_run
        try:
            evidence = capture._run_seed_static_preflight(
                fixture.config(), fixture.artifacts
            )
        finally:
            capture.subprocess.run = original_run

        require(
            evidence["result"] == "GREEN",
            "seed preflight smoke matrix unexpectedly failed",
        )
        require(len(calls) == 16, "seed preflight command count drifted")
        optimized = {
            Path(command[-1]).name
            for command, _kwargs in calls
            if "-O" in command
        }
        require(
            optimized == set(scripts[2:]),
            "optimized seed smoke coverage is incomplete",
        )
        require(
            all(kwargs.get("cwd") == fixture.clean for _command, kwargs in calls),
            "seed preflight smoke did not use the frozen clean source cwd",
        )
        require(
            all("-B" in command for command, _kwargs in calls),
            "seed preflight child omitted the no-bytecode switch",
        )
        require(
            all(
                kwargs.get("env", {}).get("PYTHONDONTWRITEBYTECODE") == "1"
                for _command, kwargs in calls
            ),
            "seed preflight child omitted the no-bytecode environment guard",
        )


def test_runner_import_guard_prevents_clean_source_bytecode() -> None:
    """The first adapter import must not create a cache in a clean export."""

    with tempfile.TemporaryDirectory(prefix="xar-phase2-bytecode-") as raw:
        root = Path(raw)
        tools_dir = root / "tools"
        tools_dir.mkdir()
        shutil.copy2(capture.__file__, tools_dir / "run_zg361_phase2_seed_capture.py")
        shutil.copy2(
            Path(capture.__file__).with_name("kaishek_preflight.py"),
            tools_dir / "kaishek_preflight.py",
        )
        shutil.copy2(
            Path(capture.__file__).with_name(
                "zg361_phase2_acceptance_observer_gate.py"
            ),
            tools_dir / "zg361_phase2_acceptance_observer_gate.py",
        )
        shutil.copy2(
            Path(capture.__file__).with_name(
                "zg361_phase2_date_sentinel_activation.py"
            ),
            tools_dir / "zg361_phase2_date_sentinel_activation.py",
        )
        script = tools_dir / "run_zg361_phase2_seed_capture.py"
        environment = {
            key: value
            for key, value in os.environ.items()
            if key not in {"PYTHONDONTWRITEBYTECODE", "PYTHONPYCACHEPREFIX"}
        }
        environment["PYTHONPATH"] = str(tools_dir)
        completed = subprocess.run(
            [
                sys.executable,
                "-S",
                "-c",
                f"import runpy; runpy.run_path({str(script)!r})",
            ],
            cwd=root,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        require(
            completed.returncode == 0,
            f"runner import guard smoke failed: {completed.stderr}",
        )
        bytecode = [
            path
            for path in root.rglob("*")
            if path.is_file()
            and ("__pycache__" in path.parts or path.suffix.lower() in {".pyc", ".pyo"})
        ]
        require(not bytecode, f"runner import wrote bytecode: {bytecode}")


def test_static_contract() -> None:
    source = Path(capture.__file__).read_text(encoding="utf-8")
    for token in (
        "--clean-source",
        "--attempt-dir",
        "--artifacts-dir",
        "--source-zip",
        "--git-sha",
        "--bridge-dll",
        "--injector",
        "--bridge-bundle-manifest",
        "--product-projection",
        "--product-projection-manifest",
        "--product-source",
        "--pipe",
        "--seed-purpose",
        "--manager-transition-checkpoint-capture",
        "--manager-transition-checkpoint-receipt",
        "--preflight-only",
        "--list-domain-observer-gate",
        "--acceptance-observer-manifest",
        "list-domain-observer-gate.json",
        "def run_preflight(",
        '"launch_boundary": "not-crossed"',
        '"ck3_launch_attempted": False',
        "sys.dont_write_bytecode = True",
        "verify_runtime_load_order(",
        "native_loader_smoke_readiness(",
        "scan_loader_error_log(",
        "wait_for_bootstrap_event(",
        "stop_phase2_native_session_supervisor(",
        "native_session_probe",
        "_phase2_native_session_probe(",
        "driver.close()",
        "AUTOMATIC_GAME_DIR_REQUIRES_STEAM",
        "CACHE_PROVENANCE_SCAN_LIMIT",
        "_bootstrap_product_projection(",
    ):
        require(token in source, f"runner contract token missing: {token}")
    require(
        source.index("active_runtime.wait_for_loader_stage(")
        < source.index("zgrun.native_loader_smoke_readiness(")
        < source.index("zgrun.scan_loader_error_log(")
        < source.index("entry_snapshot = wait_for_bootstrap_event("),
        "loader/native/event order drifted",
    )
    require(capture.LOADER_FATAL_STALL_SECONDS == 45.0, "45s fail-fast drifted")
    require("wait_for_ocr_text(" not in source, "runner contains OCR fallback")
    require("pyautogui" not in source, "runner contains desktop input fallback")
    require("focus_ck3(" not in source, "runner changes foreground focus")
    require(
        "force_ck3_english_keyboard_layout(" not in source,
        "runner inherited a transitive desktop-input HKL helper",
    )
    require("keyDown(" not in source, "runner injects a desktop key")
    require("keyUp(" not in source, "runner injects a desktop key")
    require("Z:\\" not in source, "runner retained a machine-specific hardcoded path")


def test_r129_transition_checkpoint_then_clean_manager_continuation() -> None:
    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        purpose = capture.MANAGER_SEED_PURPOSE
        capture_calls: list[str] = []
        capture_runtime = fixture.runtime(capture_calls, seed_purpose=purpose)
        transition_service = capture_runtime.service_factory(None)
        require(isinstance(transition_service, FakeService), "transition fake drifted")
        transition_service.speed = 5
        # The live native driver freezes this as the session-origin player even
        # after the fixture changes the current typed player to 9002.
        transition_service.checkpoint_episode_character_id = 9001
        first = capture.run_capture(
            replace(
                fixture.config(seed_purpose=purpose),
                manager_transition_checkpoint_capture=True,
            ),
            runtime=capture_runtime,
        )
        require(
            first["result"] == "TRANSITION_CHECKPOINT_READY"
            and first["scenario_verdict"] == "INTERMEDIATE_GREEN"
            and first["seed_verdict"] == "RED"
            and first["final_seed_ready"] is False,
            f"transition checkpoint forged a final result: {first}",
        )
        receipt = first["manager_transition_checkpoint"]
        require(
            receipt["kind"] == capture.MANAGER_TRANSITION_CHECKPOINT_KIND
            and receipt["played_character_id"] == 9002
            and receipt["date_raw"] == 53147040
            and receipt["paused"] is True
            and receipt["timeline_speed"] == 5
            and receipt["product_state_cleared"] is False
            and receipt["product_receipt_written"] is False,
            f"transition receipt drifted: {receipt}",
        )
        require(
            receipt["checkpoint"]["episode_character_id"] == 9001
            and receipt["checkpoint"]["typed_played_character_id"] == 9002
            and receipt["checkpoint"]["episode_character_id_semantics"]
            == "native_session_origin",
            f"transition receipt confused session and live identities: {receipt}",
        )
        require(
            "save-checkpoint" in capture_calls
            and "seed-capture-mcp" not in capture_calls
            and "candidate-materialize" not in capture_calls,
            f"transition phase crossed the final seed gate: {capture_calls}",
        )
        receipt_path = fixture.artifacts / "manager-transition-checkpoint-receipt.json"
        require(receipt_path.is_file(), "transition receipt was not persisted")

        continuation_calls: list[str] = []
        continuation_runtime = fixture.runtime(
            continuation_calls,
            seed_purpose=purpose,
            manager_pip_route=False,
        )
        continuation_service = continuation_runtime.service_factory(None)
        require(isinstance(continuation_service, FakeService), "continuation fake drifted")
        continuation_service.played_character_id = 9002
        continuation_service.date_raw = 53147040
        continuation_service.speed = 5
        continuation_service.event_state = "continuation_pending"
        original_recovery = capture.recover_active_manager_cycle

        def fake_recovery(
            service: FakeService, **_kwargs: object
        ) -> dict[str, object]:
            continuation_calls.append("manager-cycle-recovery")
            service.date_raw += 240
            service.paused = True
            return {
                "schema_version": 1,
                "kind": "zg361_phase2_promotion_source_production_entry",
                "result": "GREEN",
                "readiness": "paused-clean-review-boundary",
                "clean_review_boundary": {
                    "date_raw": service.date_raw,
                    "review_now_eligible": True,
                    "b1_active": False,
                    "central_active": False,
                    "pp_active": False,
                },
            }

        capture.recover_active_manager_cycle = fake_recovery
        original_date_sentinel = capture.run_date_only_daily_activation

        def fake_date_sentinel(
            service: FakeService,
            starting_snapshot: dict[str, object],
            **kwargs: object,
        ) -> dict[str, object]:
            continuation_calls.append("date-only-sentinel")
            require(
                starting_snapshot["date_raw"] == 53147280
                and service.event_state == "continuation_pending",
                "continuation sentinel did not start at the clean boundary",
            )
            require(kwargs["speed"] == 5, "continuation sentinel lost speed five")
            service.date_raw += 24
            service.revision += 1
            service.event_state = "final"
            return {
                "schema_version": 1,
                "kind": "zg361_phase2_date_only_activation_sentinel",
                "result": "GREEN",
                "starting_date_raw": 53147280,
                "target_date_raw": 53147304,
                "speed": 5,
                "resume_submission_count": 1,
                "external_pause_used": False,
            }

        capture.run_date_only_daily_activation = fake_date_sentinel
        continuation_attempt = fixture.root / "continuation" / "attempt"
        continuation_artifacts = fixture.root / "continuation" / "artifacts"
        try:
            final = capture.run_capture(
                replace(
                    fixture.config(seed_purpose=purpose),
                    attempt_dir=continuation_attempt,
                    artifacts_dir=continuation_artifacts,
                    manager_transition_checkpoint_receipt=receipt_path,
                ),
                runtime=continuation_runtime,
            )
        finally:
            capture.recover_active_manager_cycle = original_recovery
            capture.run_date_only_daily_activation = original_date_sentinel
        require(final["result"] == "GREEN", f"clean continuation RED: {final}")
        require(
            final["manager_entry_mode"]
            == "active-manager-transition-checkpoint-continuation"
            and final["manager_transition_contract"]["handoff_mode"]
            == capture.MANAGER_TRANSITION_CONTINUATION_MODE
            and final["manager_direct_final_binding"]["result"] == "GREEN"
            and final["manager_direct_candidate_identity"]["result"] == "GREEN",
            "clean continuation bypassed a final manager gate",
        )
        require(
            final["manager_entry_event"]["date_raw"] == 53147304
            and final["manager_cycle_recovery"]["readiness"]
            == "paused-clean-review-boundary"
            and final["manager_transition_contract"]["maximum_date_raw"]
            == 53147304
            and final["manager_transition_contract"][
                "recovered_boundary_date_raw"
            ]
            == 53147280
            and final["manager_transition_contract"]["activation_carrier"]
            == "acceptance-hidden-daily-retry-under-native-date-only-sentinel",
            "clean continuation did not bind the exact next-day activation",
        )
        require(
            not any(call.startswith("select-event-option:3") for call in continuation_calls)
            and "manager-cycle-recovery" in continuation_calls
            and "date-only-sentinel" in continuation_calls
            and "seed-capture-mcp" in continuation_calls
            and "candidate-materialize" in continuation_calls,
            f"continuation replayed PIP or skipped final capture: {continuation_calls}",
        )


def test_r156_materialized_manager_carrier_binds_clean_boundary_date() -> None:
    recovery = {
        "target_binding": {
            "snapshot_id": "native:295",
            "revision": 296,
            "native_revision": 295,
            "date_raw": 53154120,
            "paused": True,
            "map_ready": True,
            "player_character_id": 32904,
            "connection_generation": 1,
            "event_instance_id": 17,
            "event_option_count": 1,
        }
    }
    contract = capture._manager_recovery_activation_contract(
        recovery,
        clean_boundary_date_raw=53154120,
        expected_manager_character_id=32904,
        expected_connection_generation=1,
    )
    require(
        contract
        == {
            "activation_target_date_raw": 53154120,
            "activation_carrier": (
                "acceptance-hidden-daily-retry-materialized-at-clean-boundary"
            ),
            "activation_date_sentinel_required": False,
            "activation_event_instance_id": 17,
        },
        f"materialized manager carrier date drifted: {contract}",
    )

    delayed = capture._manager_recovery_activation_contract(
        {"target_binding": None},
        clean_boundary_date_raw=53154120,
        expected_manager_character_id=32904,
        expected_connection_generation=1,
    )
    require(
        delayed["activation_target_date_raw"] == 53154144
        and delayed["activation_date_sentinel_required"] is True,
        f"empty clean boundary lost its one-day sentinel: {delayed}",
    )

    drifted = copy.deepcopy(recovery)
    drifted["target_binding"]["date_raw"] = 53154144
    try:
        capture._manager_recovery_activation_contract(
            drifted,
            clean_boundary_date_raw=53154120,
            expected_manager_character_id=32904,
            expected_connection_generation=1,
        )
    except capture.SeedCaptureError as error:
        require(
            error.evidence["checks"]["date_raw"] is False,
            f"drifted carrier date lacked exact evidence: {error.evidence}",
        )
    else:
        raise AssertionError("drifted manager carrier target false-GREENed")


def test_rejects_known_manager_sources_before_launch() -> None:
    rejected = {
        "bf5960b7194e1222029add884743c688fee0d86f95559670c587317461519e74": [
            "R119",
            "R128",
        ],
        "2c9278d4f5a2707ad23e577d6677ee69673e77876e2f6232349972657cc02261": [
            "R410",
        ],
    }
    for digest, attempts in rejected.items():
        try:
            capture._enforce_allowed_manager_source_save(digest.upper())
        except capture.SeedCaptureError as error:
            require(
                error.evidence == {
                    "stage": "manager_source_save_prelaunch",
                    "result": "RED",
                    "source_save_sha256": digest,
                    "rejected_attempts": attempts,
                },
                f"rejected source evidence drifted: {error.evidence}",
            )
        else:
            raise AssertionError(
                f"known manager source passed the prelaunch gate: {digest}"
            )

    digest = next(
        value
        for value, attempts in rejected.items()
        if attempts == ["R410"]
    )

    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        calls: list[str] = []
        runtime = fixture.runtime(
            calls, seed_purpose=capture.MANAGER_SEED_PURPOSE
        )
        original = capture._enforce_allowed_manager_source_save
        capture._enforce_allowed_manager_source_save = lambda _observed: original(
            digest
        )
        try:
            report = capture.run_capture(
                fixture.config(seed_purpose=capture.MANAGER_SEED_PURPOSE),
                runtime=runtime,
            )
        finally:
            capture._enforce_allowed_manager_source_save = original
        require(
            report["result"] == "RED"
            and report["failure_evidence"]["stage"]
            == "manager_source_save_prelaunch",
            "known source rejection was not persisted as typed RED",
        )
        require(
            "bootstrap" not in calls
            and "supervisor-start" not in calls
            and "driver-open" not in calls,
            f"known source rejection crossed the native launch boundary: {calls}",
        )


def test_manager_recovery_classifies_terminal_owner_without_rebinding() -> None:
    terminal = {
        "snapshot_id": "native:104",
        "revision": 104,
        "native_revision": 103,
        "date_raw": 53149440,
        "paused": False,
        "speed": 5,
        "map_ready": True,
        "actual_player_character_id": 33001,
        "expected_player_character_id": 32904,
        "actual_connection_generation": 1,
        "expected_connection_generation": 1,
        "bridge_pid": 200604,
        "one_life_terminal": True,
        "one_life_terminal_reason": "played_character_changed",
        "active_event": None,
    }
    original = production.enter_promotion_source_checkpoint_v1

    def fail_terminal(*_args, **kwargs):
        kwargs["evidence_out"]["observations"] = [
            {"revision": 103, "date_raw": 53149368}
        ]
        raise production.PromotionBindingError(terminal)

    production.enter_promotion_source_checkpoint_v1 = fail_terminal
    try:
        with tempfile.TemporaryDirectory() as raw:
            artifacts = Path(raw)
            try:
                capture.recover_active_manager_cycle(
                    object(),
                    clean_source=Path(__file__).resolve().parents[1],
                    artifacts=artifacts,
                    timeout_seconds=1.0,
                    clock=lambda: 0.0,
                    sleeper=lambda _seconds: None,
                )
            except capture.SeedCaptureError as error:
                require(
                    error.evidence["result"] == "SCENARIO_INVALID"
                    and error.evidence["reason_code"]
                    == "manager-owner-terminal",
                    f"terminal owner classification drifted: {error.evidence}",
                )
                require(
                    error.evidence["evidence"]["binding_failure"] == terminal,
                    "terminal binding frame was not retained",
                )
            else:
                raise AssertionError("terminal owner crossing did not fail closed")
            artifact = json.loads(
                (artifacts / "manager-cycle-recovery.json").read_text(
                    encoding="utf-8"
                )
            )
            require(
                artifact["binding_failure"] == terminal,
                "terminal binding frame was not persisted",
            )
    finally:
        production.enter_promotion_source_checkpoint_v1 = original


def main() -> int:
    test_game_dir_resolution_prefers_steam_and_preserves_explicit()
    test_game_dir_resolution_never_falls_back_to_repository()
    test_profile_settings_requires_explicit_template_and_records_auto_candidate()
    test_formal_profile_assets_fail_typed_for_missing_template_or_cache()
    test_formal_profile_assets_reject_preexisting_unpinned_cache()
    test_formal_profile_assets_reject_copy_manifest_drift()
    test_tree_manifest_records_byte_sizes_under_bytes_key()
    test_release_bridge_bundle_provenance_binds_pair_and_rejects_debug()
    test_phase2_frontend_first_options_reach_seed_supervisor()
    test_real_phase2_frontend_first_option_validation()
    test_real_phase2_frontend_first_binding_uses_first_mcp_generation()
    test_green_capture()
    test_player_manager_capture_routes_fixture_event_and_materializer()
    test_direct_player_manager_first_frame_capture_is_zero_input()
    test_direct_player_manager_destructive_first_frame_is_zero_input_red()
    test_direct_player_manager_wrong_played_id_is_zero_input_red()
    test_direct_player_manager_self_subject_is_red_before_materialize()
    test_direct_player_manager_candidate_identity_drift_is_red()
    test_player_manager_post_exact_pip_handoff_proves_final_event()
    test_player_manager_handoff_rejects_final_subject_identity_drift()
    test_player_manager_preemptive_handoff_rejects_later_date()
    test_player_manager_preemptive_handoff_rejects_wrong_played_manager()
    test_player_manager_handoff_never_drains_destructive_later_event()
    test_player_manager_same_date_grace_uses_speed_five()
    test_player_manager_wrong_event_is_scenario_and_seed_red()
    test_player_manager_preflight_reports_purpose_and_contract_kind()
    test_parser_red_cleanup()
    test_native_session_process_exit_cleanup()
    test_exact_known_predecessor_is_drained_once()
    test_calculated_event_id_is_observed_but_not_an_identity_gate()
    test_exact_vanilla_prebootstrap_event_uses_option_two()
    test_exact_b2_pip_prebootstrap_event_uses_accept_option()
    test_manager_b2_pip_route_uses_refuse_option_only()
    test_manager_post_activation_gui_settles_while_paused()
    test_manager_post_activation_gui_timeout_never_resumes_map()
    test_clean_manager_continuation_uses_one_date_only_sentinel()
    test_b2_pip_prebootstrap_identity_drift_fails_closed()
    test_exact_vanilla_no_secrets_event_keeps_current_task()
    test_r120_source_hash_is_exactly_authorized_for_b2_sequence()
    test_vanilla_no_secrets_identity_drift_fails_closed()
    test_multiple_registered_prebootstrap_events_are_supported()
    test_vanilla_prebootstrap_identity_and_option_shape_fail_closed()
    test_unregistered_vanilla_event_remains_unexpected_red()
    test_vanilla_drain_keeps_original_deadline_and_resumes_timeline()
    test_vanilla_selection_ack_must_confirm_native_option_two()
    test_pause_revision_race_reloads_snapshot_and_retries()
    test_resume_revision_race_reloads_snapshot_and_retries()
    test_known_predecessor_identity_drift_fails_closed()
    test_total_event_deadline()
    test_cli_validation_and_artifact_preservation()
    test_product_projection_options_reach_isolated_bootstrap()
    test_named_product_projection_requires_manifest_before_runtime()
    test_stale_bootstrap_cannot_silently_downgrade_named_projection()
    test_no_launch_preflight_green_does_not_cross_native_boundary()
    test_no_launch_preflight_rejects_stale_critical_b2_product_source()
    test_no_launch_preflight_rejects_stale_mounted_critical_b2_product()
    test_list_domain_observer_pending_is_typed_no_launch_red()
    test_list_domain_observer_manifest_binds_frozen_no_launch_inputs()
    test_no_launch_preflight_missing_static_gate_is_red_without_fixture_override()
    test_no_launch_preflight_running_ck3_is_persisted_red()
    test_source_zip_mismatch_is_preserved()
    test_bootstrap_runtime_hash_drift_is_preserved()
    test_seed_source_path_must_be_absolute()
    test_static_preflight_runs_optimized_seed_smokes()
    test_runner_import_guard_prevents_clean_source_bytecode()
    test_manager_recovery_classifies_terminal_owner_without_rebinding()
    test_r129_transition_checkpoint_then_clean_manager_continuation()
    test_r156_materialized_manager_carrier_binds_clean_boundary_date()
    test_rejects_known_manager_sources_before_launch()
    test_static_contract()
    print("GREEN: reusable phase-two seed capture is MCP-only and bounded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
