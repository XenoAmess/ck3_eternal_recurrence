#!/usr/bin/env python3
"""Continue one frozen GEN-034-D capture/checkpoint/driver bundle.

This runner never repeats the natural-event source capture.  It admits three
immutable source files, prepares a fresh formal production state, rebinds the
copied rogue checkpoint to that prepared environment, and cold-starts
``native_auto_run``.  The production loop is stopped at its first matching
terminal submit seam; only that successful interception may freeze an input
for the existing one-action live runner.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import sys


RESEARCH_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = RESEARCH_ROOT.parents[2]
PACKAGE_ROOT = REPOSITORY_ROOT / "ck3_autonomous_player" / "src"
for candidate in (RESEARCH_ROOT, PACKAGE_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import run_g2_source_specific_war_loss_live_adapter as adapter  # noqa: E402
from xar_autoplayer.bridge.raiktor_source_specific_war_loss_contract import (  # noqa: E402
    normalize_raiktor_source_specific_capture,
)
from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.native_session import (  # noqa: E402
    NATIVE_DRIVER_STATE_FILENAME,
    NATIVE_SESSION_CHECKPOINT_FILENAME,
    validate_cold_start_checkpoint_for_pipe,
)
from xar_autoplayer.runtime import NativeBridgeLaunchConfig  # noqa: E402


REPORT_SCHEMA = "xar.ck3.gen034_d_candidate_continuation.v1"
MODE = "frozen-source-continuation-to-terminal-intercept"


class ContinuationError(ValueError):
    """The frozen continuation could not safely reach its terminal seam."""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--source-capture", type=Path, required=True)
    parser.add_argument("--expected-source-capture-sha256", required=True)
    parser.add_argument("--source-checkpoint", type=Path, required=True)
    parser.add_argument("--expected-checkpoint-sha256", required=True)
    parser.add_argument("--source-driver-state", type=Path, required=True)
    parser.add_argument("--expected-driver-state-sha256", required=True)
    parser.add_argument("--expected-war-id", type=int, required=True)
    parser.add_argument("--profile-settings-template", type=Path, required=True)
    parser.add_argument("--expected-profile-settings-sha256", required=True)
    parser.add_argument("--expected-shadercache-tree-sha256", required=True)
    parser.add_argument("--game-root", type=Path)
    parser.add_argument("--game-executable", type=Path)
    parser.add_argument("--bookmark-events", type=Path)
    parser.add_argument("--capture-executable", type=Path)
    parser.add_argument("--bridge-dll", type=Path)
    parser.add_argument("--bridge-injector", type=Path)
    parser.add_argument("--candidate-turn-limit", type=int, default=256)
    parser.add_argument("--candidate-timeout", type=float, default=1800.0)
    parser.add_argument("--readiness-timeout", type=float, default=720.0)
    parser.add_argument("--authorize-private-live", action="store_true")
    return parser


def _write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _positive_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ContinuationError(f"{label} must be a positive integer")
    return value


def _positive_seconds(value: object, label: str, *, maximum: float) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or float(value) <= 0
        or float(value) > maximum
    ):
        raise ContinuationError(f"{label} must be in (0, {maximum:g}]")
    return float(value)


def _clean_runtime_root(runtime_root: Path) -> dict[str, object]:
    root = runtime_root.expanduser().resolve()
    if root != REPOSITORY_ROOT.resolve():
        raise ContinuationError(
            "runtime-root must be the clean checkout executing this runner"
        )
    try:
        top = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        ).stdout.strip()
        revision = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        ).stdout.strip()
        status = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "--no-optional-locks",
                "status",
                "--porcelain",
                "--untracked-files=all",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        ).stdout.splitlines()
    except (FileNotFoundError, subprocess.SubprocessError) as error:
        raise ContinuationError(f"runtime-root Git identity is unavailable: {error}") from error
    if Path(top).resolve() != root:
        raise ContinuationError("runtime-root is not its Git toplevel")
    if len(revision) != 40 or any(
        character not in "0123456789abcdef" for character in revision
    ):
        raise ContinuationError("runtime-root does not have a full Git revision")
    if status:
        raise ContinuationError(
            "runtime-root must be clean before formal preparation: "
            + ", ".join(status[:8])
        )
    return {
        "status": "clean",
        "path": str(root),
        "git_revision": revision,
        "repo_root_equals_runtime_root": True,
    }


def _source_receipt(
    path: Path, expected_sha256: object, label: str
) -> dict[str, object]:
    source = path.expanduser().resolve()
    expected = adapter._sha256_text(expected_sha256, f"{label} SHA-256")
    if not source.is_file():
        raise ContinuationError(f"{label} is unavailable: {source}")
    size = source.stat().st_size
    actual = adapter._sha256_file(source)
    if size <= 0 or actual != expected:
        raise ContinuationError(f"{label} differs from its frozen SHA-256")
    return {
        "path": str(source),
        "size": size,
        "sha256": actual,
    }


def _source_set(args: argparse.Namespace) -> dict[str, dict[str, object]]:
    return {
        "capture": _source_receipt(
            args.source_capture,
            args.expected_source_capture_sha256,
            "source capture",
        ),
        "checkpoint": _source_receipt(
            args.source_checkpoint,
            args.expected_checkpoint_sha256,
            "source checkpoint",
        ),
        "driver_state": _source_receipt(
            args.source_driver_state,
            args.expected_driver_state_sha256,
            "source driver state",
        ),
    }


def _source_immutability(
    admitted: dict[str, dict[str, object]],
) -> dict[str, object]:
    rows: dict[str, object] = {}
    unchanged = True
    for name, before in admitted.items():
        path = Path(str(before["path"]))
        exists = path.is_file()
        try:
            after_sha256 = adapter._sha256_file(path) if exists else None
            after_size = path.stat().st_size if exists else None
        except OSError:
            after_sha256 = None
            after_size = None
            exists = False
        row_unchanged = (
            exists
            and after_sha256 == before.get("sha256")
            and after_size == before.get("size")
        )
        unchanged = unchanged and row_unchanged
        rows[name] = {
            "path": str(path),
            "before_sha256": before.get("sha256"),
            "after_sha256": after_sha256,
            "before_size": before.get("size"),
            "after_size": after_size,
            "unchanged": row_unchanged,
        }
    return {"all_unchanged": unchanged, "files": rows}


def _require_sources_unchanged(
    admitted: dict[str, dict[str, object]], *, stage: str
) -> dict[str, object]:
    receipt = _source_immutability(admitted)
    if receipt.get("all_unchanged") is not True:
        raise ContinuationError(f"frozen source files changed during {stage}")
    return receipt


def _load_capture(path: Path, capture_sha256: str) -> dict[str, object]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
        normalized = normalize_raiktor_source_specific_capture(
            raw,
            capture_sha256=capture_sha256,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise ContinuationError(f"source capture is not admissible: {error}") from error
    if not isinstance(normalized, dict):
        raise ContinuationError("source capture normalization returned no object")
    return normalized


def _driver_pipe(path: Path) -> str:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ContinuationError(
            f"source driver state is unreadable: {error}"
        ) from error
    pipe_name = payload.get("pipe_name") if isinstance(payload, dict) else None
    if not isinstance(pipe_name, str) or not pipe_name:
        raise ContinuationError("source driver state lacks its native pipe")
    return pipe_name


def _runtime_manifest_binding(
    checked: dict[str, dict[str, object]],
) -> tuple[Path, str]:
    dependency = checked.get("runtime_manifest")
    if not isinstance(dependency, dict):
        raise ContinuationError("live manifest lacks its runtime source closure")
    path = Path(str(dependency.get("path"))).resolve()
    digest = adapter._sha256_text(
        dependency.get("sha256"), "runtime manifest SHA-256"
    )
    return path, digest


def _copy_inputs(
    attempt: Path,
    admitted: dict[str, dict[str, object]],
) -> dict[str, dict[str, object]]:
    destination = attempt / "inputs"
    names = {
        "capture": "capture.json",
        "checkpoint": NATIVE_SESSION_CHECKPOINT_FILENAME,
        "driver_state": NATIVE_DRIVER_STATE_FILENAME,
    }
    return {
        name: adapter._copy_formal_candidate_artifact(
            Path(str(receipt["path"])),
            destination / names[name],
            receipt["sha256"],
            label=f"frozen {name.replace('_', ' ')}",
        )
        for name, receipt in admitted.items()
    }


def _copied_path(copies: dict[str, dict[str, object]], name: str) -> Path:
    return Path(str(copies[name]["destination"])).resolve()


def _persist(report_path: Path, report: dict[str, object]) -> None:
    _write_json_atomic(report_path, report)


def run_continuation(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    attempt = args.attempt_dir.expanduser().resolve()
    formal_state = attempt.with_name(f"{attempt.name}-formal-state")
    if attempt.exists():
        raise ContinuationError(f"attempt directory already exists: {attempt}")
    if formal_state.exists():
        raise ContinuationError(f"formal state already exists: {formal_state}")
    if args.authorize_private_live is not True:
        raise ContinuationError("continuation live command remains default-OFF")
    expected_war_id = _positive_integer(args.expected_war_id, "expected WarID")
    turn_limit = _positive_integer(args.candidate_turn_limit, "candidate turn limit")
    if turn_limit > 4096:
        raise ContinuationError("candidate turn limit must not exceed 4096")
    timeout = _positive_seconds(
        args.candidate_timeout,
        "candidate timeout",
        maximum=7200.0,
    )
    readiness_timeout = _positive_seconds(
        args.readiness_timeout,
        "readiness timeout",
        maximum=3600.0,
    )
    if timeout <= readiness_timeout:
        raise ContinuationError(
            "candidate timeout must be greater than readiness timeout"
        )

    runtime_root = args.runtime_root.expanduser().resolve()
    runtime_identity = _clean_runtime_root(runtime_root)
    if attempt == runtime_root or attempt.is_relative_to(runtime_root):
        raise ContinuationError("attempt directory must be outside runtime-root")
    if formal_state == runtime_root or formal_state.is_relative_to(runtime_root):
        raise ContinuationError("formal state must be outside runtime-root")

    attempt.mkdir(parents=True, exist_ok=False)
    report_path = attempt / "report.json"
    report: dict[str, object] = {
        "schema": REPORT_SCHEMA,
        "status": "RUNNING",
        "mode": MODE,
        "stage": "source-admission",
        "stage_order": [],
        "runtime_identity": runtime_identity,
        "attempt_dir": str(attempt),
        "formal_state_dir": str(formal_state),
        "source_immutability": None,
        "candidate_native_auto_run": None,
        "action_runner_input": None,
        "boundaries": {
            "natural_event_repeated": False,
            "terminal_action_submitted": False,
            "action_runner_input_ready": False,
            "gen034_closed": False,
        },
    }
    stage_order = report["stage_order"]
    assert isinstance(stage_order, list)
    _persist(report_path, report)

    admitted: dict[str, dict[str, object]] | None = None
    candidate_report: dict[str, object] | None = None
    try:
        admitted = _source_set(args)
        report["sources"] = copy.deepcopy(admitted)
        stage_order.append("source-admission")

        report["stage"] = "runtime-admission"
        manifest, paths, timeouts, checked = adapter._load_manifest(
            args.manifest.expanduser().resolve(),
            repo_root=runtime_root,
            game_root=(
                args.game_root.expanduser().resolve()
                if args.game_root is not None
                else None
            ),
            game_executable=(
                args.game_executable.expanduser().resolve()
                if args.game_executable is not None
                else None
            ),
            bookmark_events=(
                args.bookmark_events.expanduser().resolve()
                if args.bookmark_events is not None
                else None
            ),
            capture_executable=(
                args.capture_executable.expanduser().resolve()
                if args.capture_executable is not None
                else None
            ),
            bridge_dll=(
                args.bridge_dll.expanduser().resolve()
                if args.bridge_dll is not None
                else None
            ),
            bridge_injector=(
                args.bridge_injector.expanduser().resolve()
                if args.bridge_injector is not None
                else None
            ),
            runtime_root=runtime_root,
        )
        report["live_manifest"] = {
            "path": str(args.manifest.expanduser().resolve()),
            "schema": manifest.get("schema"),
        }
        runtime_manifest_path, runtime_manifest_sha256 = _runtime_manifest_binding(
            checked
        )
        stage_order.append("runtime-admission")

        report["stage"] = "freeze-input-copies"
        copies = _copy_inputs(attempt, admitted)
        report["input_copies"] = copy.deepcopy(copies)
        copied_capture = _copied_path(copies, "capture")
        copied_checkpoint = _copied_path(copies, "checkpoint")
        copied_driver = _copied_path(copies, "driver_state")
        capture_sha256 = str(admitted["capture"]["sha256"])
        normalized = _load_capture(copied_capture, capture_sha256)
        source_set = normalized.get("source_set")
        captured_war_id = (
            source_set.get("war_id") if isinstance(source_set, dict) else None
        )
        if captured_war_id != expected_war_id:
            raise ContinuationError(
                "source capture WarID differs from the requested continuation"
            )
        pipe_name = _driver_pipe(copied_driver)
        report["source_normalization"] = normalized
        report["identity"] = {
            "war_id": captured_war_id,
            "pipe_name": pipe_name,
            "capture_sha256": capture_sha256,
        }
        stage_order.append("freeze-input-copies")

        report["stage"] = "formal-state-preparation"
        spec, formal_receipt = adapter.prepare_formal_candidate_state(
            artifact_dir=attempt,
            game_dir=paths.game_executable.parent.parent,
            profile_settings_template=args.profile_settings_template,
            expected_profile_settings_sha256=args.expected_profile_settings_sha256,
            expected_shadercache_tree_sha256=(
                args.expected_shadercache_tree_sha256
            ),
            source_checkpoint=copied_checkpoint,
            expected_checkpoint_sha256=admitted["checkpoint"]["sha256"],
            source_driver_state=copied_driver,
            expected_driver_state_sha256=admitted["driver_state"]["sha256"],
            expected_pipe_name=pipe_name,
            process_inventory=adapter._process_inventory,
            lifecycle_rebinder=adapter.ROGUE_LIFECYCLE_REBINDER,
        )
        report["formal_candidate_state"] = formal_receipt
        stage_order.append("formal-state-preparation")

        report["stage"] = "cold-checkpoint-validation"
        cold_validation = validate_cold_start_checkpoint_for_pipe(spec, pipe_name)
        report["cold_checkpoint_validation"] = cold_validation
        stage_order.append("cold-checkpoint-validation")

        report["stage"] = "runtime-closure-recheck"
        runtime_recheck = adapter.verify_runtime_file_manifest(
            runtime_manifest_path,
            runtime_root=runtime_root,
            expected_manifest_sha256=runtime_manifest_sha256,
        )
        report["runtime_before_native_auto_run"] = runtime_recheck
        report["source_immutability"] = _require_sources_unchanged(
            admitted,
            stage="formal preparation",
        )
        stage_order.append("runtime-closure-recheck")
        _persist(report_path, report)

        report["stage"] = "native-auto-run"
        candidate_report = adapter.native_auto_run(
            spec,
            turn_count=turn_limit,
            timeout_seconds=timeout,
            readiness_timeout_seconds=readiness_timeout,
            cold_start_checkpoint=True,
            native_bridge=NativeBridgeLaunchConfig(
                mode="native-headless",
                pipe_name=pipe_name,
                dll_path=paths.bridge_dll,
                injector_path=paths.bridge_injector,
            ),
            completion_contract="bounded",
            before_submit=adapter._candidate_terminal_interceptor(
                expected_war_id,
                capture_sha256,
            ),
        )
        report["candidate_native_auto_run"] = candidate_report
        adapter._record_and_validate_candidate_auto_run_report(
            attempt,
            candidate_report,
        )
        stage_order.append("native-auto-run")

        report["stage"] = "pre-freeze-source-recheck"
        report["source_immutability"] = _require_sources_unchanged(
            admitted,
            stage="native_auto_run",
        )
        stage_order.append("pre-freeze-source-recheck")

        report["stage"] = "freeze-action-runner-input"
        action_input = adapter._freeze_action_runner_input(
            artifact_dir=attempt,
            state_dir=spec.state_dir,
            paths=paths,
            source_capture_path=copied_capture,
            source_capture_sha256=capture_sha256,
            candidate_report=candidate_report,
            runtime_manifest_path=runtime_manifest_path,
            runtime_manifest_sha256=runtime_manifest_sha256,
            runtime_root=runtime_root,
            profile_settings_template=args.profile_settings_template,
            expected_profile_settings_sha256=(
                args.expected_profile_settings_sha256
            ),
            expected_shadercache_tree_sha256=(
                args.expected_shadercache_tree_sha256
            ),
        )
        report["action_runner_input"] = action_input
        stage_order.append("freeze-action-runner-input")

        report["stage"] = "final-source-recheck"
        report["source_immutability"] = _require_sources_unchanged(
            admitted,
            stage="action input freeze",
        )
        stage_order.append("final-source-recheck")
        report.update(
            {
                "status": "CANDIDATE_FROZEN",
                "stage": "complete",
                "boundaries": {
                    "natural_event_repeated": False,
                    "terminal_action_submitted": False,
                    "action_runner_input_ready": True,
                    "gen034_closed": False,
                },
            }
        )
        _persist(report_path, report)
        return report, 0
    except BaseException as error:
        if admitted is not None:
            report["source_immutability"] = _source_immutability(admitted)
        report.update(
            {
                "status": "RED",
                "error": f"{type(error).__name__}: {error}",
                "candidate_native_auto_run": candidate_report,
                "boundaries": {
                    "natural_event_repeated": False,
                    "terminal_action_submitted": False,
                    "action_runner_input_ready": False,
                    "gen034_closed": False,
                },
            }
        )
        _persist(report_path, report)
        return report, 2


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report, exit_code = run_continuation(args)
    except (ContinuationError, AgentError, OSError, ValueError) as error:
        print(f"ERROR: {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    stream = sys.stdout if exit_code == 0 else sys.stderr
    print(json.dumps(report, ensure_ascii=False, indent=2), file=stream)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
