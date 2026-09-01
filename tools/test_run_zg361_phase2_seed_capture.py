#!/usr/bin/env python3
"""CK3-free contracts for the reusable phase-two seed capture runner."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil
from types import SimpleNamespace
import tempfile
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
    ) -> None:
        self.fixture_source = fixture_source
        self.calls = calls
        self.keyboard_green = keyboard_green
        self.isolated = FakeIsolated()
        self.EXPECTED_EXE_SHA256 = sha256(executable)

    def bootstrap_userdir(
        self, profile: Path, product_source: Path
    ) -> dict[str, object]:
        self.calls.append("bootstrap")
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
            "manifest": {"projection": "fake", "tree_sha256": hashes["product"]},
        }

    def make_spec(self, state_dir: Path, _game_dir: Path) -> SimpleNamespace:
        self.calls.append("make-spec")
        return SimpleNamespace(state_dir=state_dir, profile_dir=state_dir / "profile")

    def resolve_native_bridge_config(
        self, _dll: Path, _injector: Path, pipe: str
    ) -> SimpleNamespace:
        self.calls.append("resolve-bridge")
        return SimpleNamespace(pipe_name=pipe)

    def start_phase2_native_session_supervisor(
        self, _spec: object, _bridge: object
    ) -> dict[str, object]:
        self.calls.append("supervisor-start")
        return {"fake": True}

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
        return {"result": "GREEN", "ready": True}


class FakeBridgeUnavailableError(RuntimeError):
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
        )

    def runtime(
        self, calls: list[str], *, parser_red: bool = False
    ) -> capture.RuntimeBindings:
        acceptance = FakeAcceptance(self.game / "binaries" / "ck3.exe", calls)
        zgrun = FakeZhongguoRunner(
            self.clean / "tools" / "fixtures" / "zg361_phase2_seed_bootstrap",
            self.game / "binaries" / "ck3.exe",
            calls,
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


def test_green_capture() -> None:
    with tempfile.TemporaryDirectory() as raw:
        fixture = Fixture(Path(raw))
        calls: list[str] = []
        runtime = fixture.runtime(calls)
        report = capture.run_capture(fixture.config(), runtime=runtime)
        require(report["result"] == "GREEN", f"fake capture RED: {report}")
        require(report["mcp_only"] is True, "capture lost MCP-only boundary")
        require(report["ocr_used"] is False, "fake capture used OCR")
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
            == report["bootstrap"]["tree_sha256"]["fixture"],
            "candidate provenance did not use independently observed runtime hashes",
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
        "--pipe",
        "sys.dont_write_bytecode = True",
        "verify_runtime_load_order(",
        "native_loader_smoke_readiness(",
        "scan_loader_error_log(",
        "wait_for_bootstrap_event(",
        "stop_phase2_native_session_supervisor(",
        "driver.close()",
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
    test_green_capture()
    test_parser_red_cleanup()
    test_total_event_deadline()
    test_cli_validation_and_artifact_preservation()
    test_source_zip_mismatch_is_preserved()
    test_bootstrap_runtime_hash_drift_is_preserved()
    test_seed_source_path_must_be_absolute()
    test_static_contract()
    print("GREEN: reusable phase-two seed capture is MCP-only and bounded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
