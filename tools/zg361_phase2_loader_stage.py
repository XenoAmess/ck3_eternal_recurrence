#!/usr/bin/env python3
"""Typed, append-only CK3 loader-stage gate for the phase-two seed.

The gate reads only CK3's append-only ``debug.log`` and ``error.log``.  It
does not inspect screenshots, send input, or read a runner-owned atomic JSON
target.  A known ZhongGuo parser/compiler failure may end a stalled database
initialization early; theme warnings alone never do.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any


DATABASE_MARKERS = (
    "jomini_eventmanager.cpp",
    "jomini_script_system.cpp",
    "pdx_persistent_reader.cpp",
    "jomini_script_argument.cpp",
)
FRONTEND_MARKER = "Setting idler 'Frontend'"
LOAD_SAVE_MARKER = "Setting idler 'Load Save'"
IN_GAME_MARKER = "Setting idler 'In Game'"
PRODUCT_PATH_PATTERN = re.compile(
    r"(?:common/(?:script_values|scripted_effects)/|events/)"
    r"zg361_[^\s')\"]+\.txt",
    re.IGNORECASE,
)
LOG_PREFIX_PATTERN = re.compile(
    r"^\[[^\]]+\]\[[A-Z]\]\[[^\]]+\]:\s*"
)
THEME_WARNING_PATTERN = re.compile(
    r"Theme missing in event '(?:zg361|zga_phase2_seed)[^']*'",
    re.IGNORECASE,
)


class LoaderStageError(RuntimeError):
    """A typed loader-stage boundary rejected or timed out."""

    def __init__(self, message: str, evidence: dict[str, Any]) -> None:
        super().__init__(message)
        self.evidence = evidence


class LoaderParseRed(LoaderStageError):
    """Known ZhongGuo parser/compiler errors stalled database init."""


class LoaderResumeRed(LoaderStageError):
    """The frontend appeared but ``-continuelastsave`` did not advance."""


class LoaderStageTimeout(LoaderStageError):
    """No proven loader-stage terminal was observed within the bound."""


class LoaderNativeSessionExitRed(LoaderStageError):
    """The managed native session ended before a loader terminal was proven."""


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _decode(payload: bytes) -> str:
    return payload.decode("utf-8", errors="replace")


def _message(line: str) -> str:
    return " ".join(LOG_PREFIX_PATTERN.sub("", line).split())


def _source_path(context: str) -> str | None:
    match = PRODUCT_PATH_PATTERN.search(context.replace("\\", "/"))
    return match.group(0) if match is not None else None


def extract_fatal_errors(error_log: bytes) -> list[dict[str, Any]]:
    """Extract and deduplicate only attempt-07-proven fatal signatures."""

    lines = _decode(error_log).splitlines()
    findings: list[dict[str, Any]] = []
    fingerprints: set[str] = set()

    def add_finding(
        category: str, line_number: int, context_lines: list[str]
    ) -> None:
        context = "\n".join(context_lines)
        source_path = _source_path(context)
        if source_path is None:
            return
        message = " ".join(
            part for part in (_message(line) for line in context_lines) if part
        )
        fingerprint = hashlib.sha256(
            f"{category}\0{source_path}\0{message}".encode("utf-8")
        ).hexdigest()
        if fingerprint in fingerprints:
            return
        fingerprints.add(fingerprint)
        findings.append(
            {
                "category": category,
                "line_number": line_number,
                "message": message,
                "source_path": source_path,
                "fingerprint_sha256": fingerprint,
                "context": context_lines,
            }
        )

    for index, line in enumerate(lines):
        lowered = line.lower()
        normalized_path_line = lowered.replace("\\", "/")
        if (
            "duplicated event id 'zg361" in lowered
            and "events/zg361_" in normalized_path_line
        ):
            add_finding(
                "invalid_generated_event_registration", index + 1, [line]
            )
            continue
        if (
            "compiling source for zg361_" in lowered
            and "failed for unknown arguments: ticket_subject" in lowered
        ):
            add_finding("ticket_subject_unknown_argument", index + 1, [line])
            continue
        if "[pdx_persistent_reader.cpp" in lowered and any(
            f"unknown trigger: {operator}" in lowered
            for operator in ("value", "add", "multiply")
        ):
            context_lines = [line]
            following = index + 1
            while following < len(lines):
                candidate = lines[following]
                if not candidate or LOG_PREFIX_PATTERN.match(candidate):
                    break
                context_lines.append(candidate)
                following += 1
            joined = " ".join(context_lines).lower()
            if any(
                token in joined
                for token in (
                    "unknown trigger: value",
                    "unknown trigger: add",
                    "unknown trigger: multiply",
                )
            ):
                add_finding(
                    "arithmetic_value_unknown_trigger",
                    index + 1,
                    context_lines,
                )
            continue
        if "[jomini_script_system.cpp" in lowered:
            context_lines = [line]
            following = index + 1
            while following < len(lines):
                candidate = lines[following]
                if not candidate or LOG_PREFIX_PATTERN.match(candidate):
                    break
                context_lines.append(candidate)
                following += 1
            if (
                "revoke_court_position effect [ expected opening bracket ]"
                in " ".join(context_lines).lower()
            ):
                add_finding(
                    "revoke_court_position_expected_opening_bracket",
                    index + 1,
                    context_lines,
                )
    return findings


def inspect_loader_logs(
    debug_log: bytes,
    error_log: bytes,
    *,
    native_ready: bool = False,
) -> dict[str, Any]:
    """Classify one immutable image of CK3's two append-only logs."""

    debug_text = _decode(debug_log)
    error_text = _decode(error_log)
    if native_ready:
        stage = "native_ready"
    elif IN_GAME_MARKER in debug_text:
        stage = "in_game"
    elif LOAD_SAVE_MARKER in debug_text:
        stage = "load_save"
    elif FRONTEND_MARKER in debug_text:
        stage = "frontend"
    elif any(marker in debug_text for marker in DATABASE_MARKERS):
        stage = "database_init"
    elif debug_text:
        stage = "engine_start"
    else:
        stage = "awaiting_logs"
    fatal_errors = extract_fatal_errors(error_log)
    return {
        "stage": stage,
        "database_init_seen": any(
            marker in debug_text for marker in DATABASE_MARKERS
        ),
        "event_wait_authorized": stage
        in {"native_ready", "load_save", "in_game"},
        "fatal_error_count": len(fatal_errors),
        "fatal_errors": fatal_errors,
        "theme_warning_count": len(THEME_WARNING_PATTERN.findall(error_text)),
        "debug_log": {
            "bytes": len(debug_log),
            "sha256": _sha256(debug_log),
        },
        "error_log": {
            "bytes": len(error_log),
            "sha256": _sha256(error_log),
        },
    }


def append_jsonl(path: Path, value: object) -> None:
    """Durably append one compact record; never replace a live target."""

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(payload + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _read_append_only(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return b""


def wait_for_phase2_seed_loader_stage(
    log_dir: Path,
    progress_jsonl: Path,
    *,
    timeout_seconds: float = 300.0,
    fatal_stall_seconds: float = 45.0,
    poll_interval_seconds: float = 0.25,
    native_ready_probe: Callable[[], bool] | None = None,
    native_session_probe: Callable[[], dict[str, Any] | None] | None = None,
    clock: Callable[[], float] = time.monotonic,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Wait for save/native progress or fail on a typed early RED.

    ``native_session_probe`` is an optional supervisor-side health boundary.
    It must return ``None`` while the managed session is still running and a
    mapping with ``terminal=True`` once that session has finished.  The
    terminal mapping is copied into append-only evidence, so a non-zero CK3
    exit (or a supervisor error) cannot be misreported as a generic 300-second
    loader timeout.
    """

    if (
        timeout_seconds <= 0
        or fatal_stall_seconds <= 0
        or fatal_stall_seconds >= timeout_seconds
        or poll_interval_seconds < 0
    ):
        raise ValueError("loader-stage timing parameters are invalid")
    debug_path = log_dir / "debug.log"
    error_path = log_dir / "error.log"
    started = clock()
    deadline = started + timeout_seconds
    last_identity: tuple[str, str] | None = None
    last_progress_at = started
    last_emitted_state: tuple[object, ...] | None = None
    sequence = 0
    last_observation: dict[str, Any] | None = None

    while clock() < deadline:
        now = clock()
        debug_log = _read_append_only(debug_path)
        error_log = _read_append_only(error_path)
        native_ready = False
        native_probe_error: str | None = None
        if native_ready_probe is not None:
            try:
                native_ready = native_ready_probe() is True
            except Exception as error:  # a loading bridge is expected to reject
                native_probe_error = f"{type(error).__name__}: {error}"
        observation = inspect_loader_logs(
            debug_log, error_log, native_ready=native_ready
        )
        identity = (
            str(observation["debug_log"]["sha256"]),
            str(observation["error_log"]["sha256"]),
        )
        if identity != last_identity:
            last_identity = identity
            last_progress_at = now
        quiet_seconds = max(0.0, now - last_progress_at)
        observation.update(
            {
                "schema_version": 1,
                "elapsed_seconds": round(max(0.0, now - started), 3),
                "quiet_seconds": round(quiet_seconds, 3),
                "native_probe_error": native_probe_error,
            }
        )
        state_key = (
            identity,
            observation["stage"],
            observation["fatal_error_count"],
            native_probe_error,
        )
        if state_key != last_emitted_state:
            sequence += 1
            append_jsonl(
                progress_jsonl,
                {"sequence": sequence, "state": "loader_progress", **observation},
            )
            last_emitted_state = state_key
        last_observation = observation

        if native_session_probe is not None:
            try:
                native_session_terminal = native_session_probe()
            except Exception as error:
                native_session_terminal = {
                    "terminal": True,
                    "probe_error": f"{type(error).__name__}: {error}",
                }
            if native_session_terminal is not None:
                if not isinstance(native_session_terminal, dict):
                    native_session_terminal = {
                        "terminal": True,
                        "probe_error": (
                            "native session probe returned a non-object: "
                            f"{type(native_session_terminal).__name__}"
                        ),
                    }
                elif native_session_terminal.get("terminal") is not True:
                    native_session_terminal = {
                        "terminal": True,
                        "probe_error": (
                            "native session probe returned a non-terminal object"
                        ),
                        "probe_result": native_session_terminal,
                    }
                session_report = native_session_terminal.get("session_report")
                exit_reason = (
                    session_report.get("exit_reason")
                    if isinstance(session_report, dict)
                    else None
                )
                process_exit_code = (
                    session_report.get("process_exit_code")
                    if isinstance(session_report, dict)
                    else None
                )
                if exit_reason == "process_exit":
                    terminal_state = "native_session_process_exit"
                    terminal_message = (
                        "managed native_session exited before loader readiness"
                    )
                else:
                    terminal_state = "native_session_exit"
                    terminal_message = (
                        "managed native_session ended before loader readiness"
                    )
                if native_session_terminal.get("probe_error"):
                    terminal_state = "native_session_probe_red"
                    terminal_message = (
                        "managed native_session supervisor probe failed"
                    )
                result = {
                    "sequence": sequence + 1,
                    **observation,
                    "state": terminal_state,
                    "result": "RED",
                    "native_session": native_session_terminal,
                    "exit_reason": exit_reason,
                    "process_exit_code": process_exit_code,
                    "process_exit_nonzero": (
                        exit_reason == "process_exit"
                        and process_exit_code not in (None, 0)
                    ),
                }
                append_jsonl(progress_jsonl, result)
                raise LoaderNativeSessionExitRed(terminal_message, result)
        if observation["event_wait_authorized"] is True:
            result = {
                "sequence": sequence + 1,
                "state": "loader_stage_ready",
                "result": "GREEN",
                **observation,
            }
            append_jsonl(progress_jsonl, result)
            return result
        if (
            observation["stage"] == "database_init"
            and observation["fatal_error_count"] > 0
            and quiet_seconds >= fatal_stall_seconds
        ):
            result = {
                "sequence": sequence + 1,
                "state": "loader_parse_red",
                "result": "RED",
                **observation,
            }
            append_jsonl(progress_jsonl, result)
            raise LoaderParseRed(
                "ZhongGuo loader parser/compiler errors stalled database init",
                result,
            )
        if poll_interval_seconds:
            sleeper(poll_interval_seconds)

    observation = last_observation or inspect_loader_logs(b"", b"")
    if observation.get("stage") == "frontend":
        state = "save_resume_red"
        error_type: type[LoaderStageError] = LoaderResumeRed
        message = "CK3 reached frontend but did not enter Load Save/In Game"
    else:
        state = "loader_stage_timeout"
        error_type = LoaderStageTimeout
        message = "CK3 did not reach Load Save/In Game/native readiness"
    result = {
        "sequence": sequence + 1,
        "state": state,
        "result": "RED",
        **observation,
    }
    append_jsonl(progress_jsonl, result)
    raise error_type(message, result)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log-dir", type=Path, required=True)
    parser.add_argument("--progress-jsonl", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=float, default=300.0)
    parser.add_argument("--fatal-stall-seconds", type=float, default=45.0)
    parser.add_argument("--poll-interval-seconds", type=float, default=0.25)
    args = parser.parse_args()
    try:
        result = wait_for_phase2_seed_loader_stage(
            args.log_dir.resolve(),
            args.progress_jsonl.resolve(),
            timeout_seconds=args.timeout_seconds,
            fatal_stall_seconds=args.fatal_stall_seconds,
            poll_interval_seconds=args.poll_interval_seconds,
        )
    except LoaderStageError as error:
        print(json.dumps(error.evidence, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
