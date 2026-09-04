#!/usr/bin/env python3
"""CK3-free contracts for the reusable phase-two seed capture runner."""

from __future__ import annotations

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
    def __init__(self, calls: list[str]) -> None:
        self.calls = calls

    def snapshot(self) -> dict[str, object]:
        return {
            "snapshot_id": "fake-snapshot-7",
            "revision": 7,
            "date_raw": 777,
            "paused": True,
            "map_ready": True,
            "speed": 1,
            "played_character": {"character_id": 9001},
            "active_event": {"instance_id": 44},
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
        return {"accepted": True}

    def query_current_event_window_context_v1(
        self, _event_id: int, **_kwargs: object
    ) -> dict[str, object]:
        self.calls.append("event-context")
        return {
            "current_event_window_context": {
                "event_definition_key": capture.SEED_EVENT_DEFINITION_KEY
            }
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
    def __init__(self, calls: list[str]) -> None:
        self.calls = calls
        self.materialize_kwargs: dict[str, object] | None = None

    def capture_mcp_evidence(
        self, _service: object, output: Path
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
        return {
            **{name: str(path) for name, path in files.items()},
            "domain_query_matrix": {
                "schema_version": 1,
                "b2_pip_owner_character_id": 9200,
                "incident_owner_character_id": 9200,
                "workforce_owner_character_id": 9200,
                "ai_owned_case_owner_character_id": 9200,
                "ai_owned_case_subject_character_id": 9001,
            },
        }

    def materialize_candidate(self, **kwargs: object) -> dict[str, object]:
        self.calls.append("candidate-materialize")
        self.materialize_kwargs = dict(kwargs)
        output = Path(kwargs["output_dir"])
        output.mkdir(parents=True)
        capture.write_json(output / "seed-contract.json", {"ready": True})
        return {
            "result": "GREEN",
            "ready": True,
            "provider_baseline_ready": True,
        }


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
        (seed_fixture / "descriptor.mod").write_text(
            "name=fixture\n", encoding="utf-8"
        )
        self.old_save.write_bytes(b"frozen-real-save")
        contract = {
            "source": {
                "absolute_save": str(self.old_save),
                "sha256": sha256(self.old_save),
            }
        }
        contract_path = self.clean / "tools" / "zg361_phase2_seed_contract.json"
        contract_path.parent.mkdir(parents=True, exist_ok=True)
        contract_path.write_text(json.dumps(contract), encoding="utf-8")
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

    def rebuild_source_zip(self) -> None:
        with zipfile.ZipFile(self.source_zip, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(
                item for item in self.clean.rglob("*") if item.is_file()
            ):
                archive.write(path, path.relative_to(self.clean).as_posix())

    def config(self) -> capture.CaptureConfig:
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
    ) -> capture.RuntimeBindings:
        acceptance = FakeAcceptance(self.game / "binaries" / "ck3.exe", calls)
        zgrun = FakeZhongguoRunner(
            self.clean / "tools" / "fixtures" / "zg361_phase2_seed_bootstrap",
            self.game / "binaries" / "ck3.exe",
            calls,
            process_exit=process_exit,
        )
        service = FakeService(calls)

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
            seed=FakeSeed(calls),
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
        require(len(calls) == 10, "seed preflight command count drifted")
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
        < source.index("event_snapshot = wait_for_bootstrap_event("),
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
    test_parser_red_cleanup()
    test_native_session_process_exit_cleanup()
    test_exact_known_predecessor_is_drained_once()
    test_calculated_event_id_is_observed_but_not_an_identity_gate()
    test_pause_revision_race_reloads_snapshot_and_retries()
    test_known_predecessor_identity_drift_fails_closed()
    test_total_event_deadline()
    test_cli_validation_and_artifact_preservation()
    test_product_projection_options_reach_isolated_bootstrap()
    test_named_product_projection_requires_manifest_before_runtime()
    test_stale_bootstrap_cannot_silently_downgrade_named_projection()
    test_no_launch_preflight_green_does_not_cross_native_boundary()
    test_list_domain_observer_pending_is_typed_no_launch_red()
    test_list_domain_observer_manifest_binds_frozen_no_launch_inputs()
    test_no_launch_preflight_missing_static_gate_is_red_without_fixture_override()
    test_no_launch_preflight_running_ck3_is_persisted_red()
    test_source_zip_mismatch_is_preserved()
    test_bootstrap_runtime_hash_drift_is_preserved()
    test_seed_source_path_must_be_absolute()
    test_static_preflight_runs_optimized_seed_smokes()
    test_runner_import_guard_prevents_clean_source_bytecode()
    test_static_contract()
    print("GREEN: reusable phase-two seed capture is MCP-only and bounded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
