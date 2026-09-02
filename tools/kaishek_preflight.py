#!/usr/bin/env python3
"""Optional bridge from the CK3 runners to ``open_kaishek preflight``.

The CK3 repository deliberately does not vendor the JVM runtime.  This module
therefore treats the Kaishek check as an optional, *offline* accelerator: it
invokes a locally built CLI when one is available, preserves the CLI JSON and
its provenance, and returns an explicit outcome when the accelerator cannot be
used.  It never installs dependencies, starts CK3, opens MCP, or mutates a
save.

The command contract starts at the stable ``open_kaishek`` preflight contract
introduced by commit ``b306a95`` (or a compatible descendant).  The checkout
and JAR are resolved at invocation time, so a locally advanced ``main`` is
used without a network fetch; explicit checkout, JAR, and provenance
environment overrides remain supported.  The command shape is ``preflight
--root PATH --profile ID --fixture ID``.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any, Mapping


ADAPTER_SCHEMA = "xar.ck3.open_kaishek_preflight.v1"
CLI_SCHEMA = "open_kaishek.preflight.v1"
# This is the stable minimum contract used for provenance.  The actual
# checkout HEAD is resolved and archived separately on every invocation, so
# newer mainline slices are adopted without changing this adapter.  A runner
# may intentionally bind another checkout through XAR_OPEN_KAISHEK_COMMIT
# (and the corresponding root/JAR overrides); that explicit value is retained
# as the provenance override.
CLI_CONTRACT_COMMIT = "b306a95"
DEFAULT_OPEN_KAISHEK_ROOT = Path(r"Z:\workspace\open_kaishek")
DEFAULT_CLI_RELATIVE_JAR = Path(
    "kaishek-cli/target/kaishek-cli-0.1.0-SNAPSHOT.jar"
)
DEFAULT_PROFILE = "ck3-1.19.0.6-zg361"
DEFAULT_FIXTURE = "synthetic-361-014"
# A full 76-file corpus exceeded the former 120 s bound in a real offline
# preflight.  Keep the timeout finite but leave enough margin for the current
# parser/validator pass; callers can override it with
# XAR_KAISHEK_PREFLIGHT_TIMEOUT_SECONDS.
DEFAULT_TIMEOUT_SECONDS = 180.0

_UNAVAILABLE = "not-applicable"
_UNSUPPORTED = "unsupported"
_FAILED = "failed"
_GREEN = "green"


def _first_env(environ: Mapping[str, str], *names: str) -> str | None:
    for name in names:
        value = environ.get(name)
        if value is not None and value.strip():
            return value.strip()
    return None


def _as_path(value: str | os.PathLike[str] | None) -> Path | None:
    if value is None:
        return None
    return Path(value).expanduser().resolve()


def _env_bool(environ: Mapping[str, str], name: str, default: bool = False) -> bool:
    value = environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "y"}


def _env_float(environ: Mapping[str, str], *names: str, default: float) -> float:
    value = _first_env(environ, *names)
    if value is None:
        return default
    try:
        parsed = float(value)
    except ValueError:
        return default
    return parsed if parsed > 0 else default


def _git_dir(checkout: Path) -> Path | None:
    """Resolve a normal or worktree ``.git`` location without spawning git."""

    marker = checkout / ".git"
    if marker.is_dir():
        return marker
    if not marker.is_file():
        return None
    try:
        line = marker.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not line.lower().startswith("gitdir:"):
        return None
    raw = line.split(":", 1)[1].strip()
    path = Path(raw)
    return (checkout / path).resolve() if not path.is_absolute() else path.resolve()


def _git_commit(checkout: Path | None) -> str | None:
    """Read the checked-out commit for provenance, best effort only."""

    if checkout is None:
        return None
    git_dir = _git_dir(checkout)
    if git_dir is None:
        return None
    try:
        head = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if head.startswith("ref: "):
        ref = head[5:].strip()
        try:
            value = (git_dir / ref).read_text(encoding="utf-8").strip()
        except OSError:
            value = None
        if not value:
            packed = git_dir / "packed-refs"
            try:
                for line in packed.read_text(encoding="utf-8").splitlines():
                    if line and not line.startswith("#") and not line.startswith("^"):
                        sha, _, name = line.split(" ", 1)
                        if name == ref:
                            value = sha
                            break
            except (OSError, ValueError):
                value = None
        head = value or ""
    head = head.strip().lower()
    return head if len(head) == 40 and all(c in "0123456789abcdef" for c in head) else None


def _sha256_file(path: Path | None) -> str | None:
    if path is None or not path.is_file():
        return None
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
    except OSError:
        return None
    return digest.hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _base_result(
    *,
    outcome: str,
    reason: str,
    profile: str,
    fixture: str,
    corpus_root: Path | None,
    checkout: Path | None,
    jar: Path | None,
    command: list[str],
    timeout_seconds: float,
    required: bool,
    release: str,
    commit: str | None,
    ck3_build: str | None,
    ck3_exe_sha256: str | None,
) -> dict[str, Any]:
    result_name = {
        _GREEN: "GREEN",
        _UNAVAILABLE: "NOT_APPLICABLE",
        _UNSUPPORTED: "UNSUPPORTED",
        _FAILED: "FAILED",
    }.get(outcome, "FAILED")
    provenance: dict[str, Any] = {
        "adapter_schema": ADAPTER_SCHEMA,
        "cli_contract_commit": CLI_CONTRACT_COMMIT,
        "open_kaishek_release": release,
        "open_kaishek_commit": commit,
        "open_kaishek_root": str(checkout) if checkout is not None else None,
        "cli_jar": str(jar) if jar is not None else None,
        "cli_jar_sha256": _sha256_file(jar),
        "profile_id": profile,
        "fixture_id": fixture,
        "corpus_root": str(corpus_root) if corpus_root is not None else None,
        "ck3_exact_build": ck3_build,
        "ck3_exe_sha256": ck3_exe_sha256,
        "command": list(command),
        "preflight_timeout_seconds": timeout_seconds,
        "python": sys.executable,
    }
    return {
        "schema": ADAPTER_SCHEMA,
        "status": outcome,
        "outcome": outcome,
        "result": result_name,
        "ok": outcome == _GREEN,
        "reason": reason,
        "required": required,
        "profile": profile,
        "profile_id": profile,
        "fixture": fixture,
        "fixture_id": fixture,
        "root": str(corpus_root) if corpus_root is not None else None,
        "corpus_root": str(corpus_root) if corpus_root is not None else None,
        "open_kaishek_release": release,
        "open_kaishek_commit": commit,
        "cli_contract_commit": CLI_CONTRACT_COMMIT,
        "cli_status": None,
        "exit_code": None,
        "elapsed_seconds": 0.0,
        "report": None,
        "stdout": "",
        "stderr": "",
        "unsupported_items": [],
        "provenance": provenance,
        "started_at_utc": _now(),
        "finished_at_utc": None,
    }


def _write_artifact(path: Path | None, payload: dict[str, Any]) -> str | None:
    if path is None:
        return None
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temporary, path)
    return str(path)


def _unsupported_items(value: object, path: str = "report") -> list[str]:
    """Find explicit unsupported/schema-only markers in a CLI report."""

    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in {"status", "semantic", "runtime"} and isinstance(child, str):
                normalized = child.strip().upper()
                if normalized == "UNSUPPORTED" or normalized == "SCHEMA-ONLY":
                    found.append(child_path)
            found.extend(_unsupported_items(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_unsupported_items(child, f"{path}[{index}]"))
    return found


def _extract_json(stdout: str) -> dict[str, Any] | None:
    # The CLI promises one object.  Choosing the last object tolerates a JVM
    # launcher warning while retaining the raw stdout in the artifact.
    for line in reversed(stdout.splitlines()):
        candidate = line.strip()
        if not candidate:
            continue
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        return value if isinstance(value, dict) else None
    return None


def _finish(
    payload: dict[str, Any],
    *,
    artifact_path: Path | None,
    artifact_error: str | None = None,
) -> dict[str, Any]:
    payload["finished_at_utc"] = _now()
    if artifact_error:
        payload["artifact_error"] = artifact_error
        # A requested evidence path that cannot be written is a real adapter
        # failure; never let a successful CLI invocation lose its evidence.
        payload["status"] = _FAILED
        payload["result"] = "FAILED"
        payload["ok"] = False
        payload["reason"] = "artifact-write-failed"
    if artifact_path is not None:
        payload["artifact_path"] = str(artifact_path.expanduser().resolve())
    try:
        _write_artifact(artifact_path, payload)
    except OSError as error:
        # The caller still receives the complete in-memory result.  Avoid a
        # second write attempt, and make the evidence loss explicit.
        payload["artifact_error"] = f"{type(error).__name__}: {error}"
        payload["status"] = _FAILED
        payload["result"] = "FAILED"
        payload["ok"] = False
        payload["reason"] = "artifact-write-failed"
    return payload


def run_preflight(
    *,
    root: str | os.PathLike[str] | None = None,
    profile: str | None = None,
    fixture: str | None = None,
    artifact_path: str | os.PathLike[str] | None = None,
    open_kaishek_root: str | os.PathLike[str] | None = None,
    jar_path: str | os.PathLike[str] | None = None,
    java: str | None = None,
    timeout_seconds: float | None = None,
    required: bool | None = None,
    ck3_build: str | None = None,
    ck3_exe_sha256: str | None = None,
    open_kaishek_release: str | None = None,
    open_kaishek_commit: str | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Run the optional ``open_kaishek preflight`` command.

    ``root`` is the CK3 source/corpus passed to the CLI's ``--root`` option;
    ``open_kaishek_root`` is the checkout containing the built CLI jar.  All
    values have environment overrides so a CI job can point at a different
    checkout without editing the runner.  Missing optional dependencies return
    ``status == "not-applicable"`` (or ``failed`` when ``required=True``).
    """

    environ = dict(os.environ)
    if env:
        environ.update({str(key): str(value) for key, value in env.items()})

    profile = profile or _first_env(
        environ, "XAR_KAISHEK_PREFLIGHT_PROFILE", "OPEN_KAISHEK_PROFILE"
    ) or DEFAULT_PROFILE
    fixture = fixture or _first_env(
        environ, "XAR_KAISHEK_PREFLIGHT_FIXTURE", "OPEN_KAISHEK_FIXTURE"
    ) or DEFAULT_FIXTURE
    corpus_root = _as_path(root) if root is not None else _as_path(
        _first_env(
            environ,
            "XAR_KAISHEK_PREFLIGHT_ROOT",
            "OPEN_KAISHEK_PREFLIGHT_ROOT",
            "KAISHEK_PREFLIGHT_ROOT",
        )
    )
    checkout = _as_path(open_kaishek_root) if open_kaishek_root is not None else _as_path(
        _first_env(
            environ,
            "XAR_OPEN_KAISHEK_ROOT",
            "OPEN_KAISHEK_ROOT",
            "KAISHEK_ROOT",
            "XAR_KAISHEK_ROOT",
        )
        or str(DEFAULT_OPEN_KAISHEK_ROOT)
    )
    explicit_jar = jar_path is not None or bool(
        _first_env(
            environ,
            "XAR_OPEN_KAISHEK_JAR",
            "OPEN_KAISHEK_JAR",
            "KAISHEK_JAR",
        )
    )
    jar = _as_path(jar_path) if jar_path is not None else _as_path(
        _first_env(
            environ,
            "XAR_OPEN_KAISHEK_JAR",
            "OPEN_KAISHEK_JAR",
            "KAISHEK_JAR",
        )
    )
    if jar is None and checkout is not None:
        jar = checkout / DEFAULT_CLI_RELATIVE_JAR
    artifact = _as_path(artifact_path) if artifact_path is not None else _as_path(
        _first_env(
            environ,
            "XAR_KAISHEK_PREFLIGHT_ARTIFACT",
            "OPEN_KAISHEK_PREFLIGHT_ARTIFACT",
        )
    )
    java_executable = java or _first_env(
        environ, "XAR_KAISHEK_JAVA", "OPEN_KAISHEK_JAVA"
    ) or "java"
    timeout = (
        timeout_seconds
        if timeout_seconds is not None
        else _env_float(
            environ,
            "XAR_KAISHEK_PREFLIGHT_TIMEOUT_SECONDS",
            "OPEN_KAISHEK_PREFLIGHT_TIMEOUT_SECONDS",
            default=DEFAULT_TIMEOUT_SECONDS,
        )
    )
    if timeout <= 0:
        timeout = DEFAULT_TIMEOUT_SECONDS
    required_value = (
        required
        if required is not None
        else _env_bool(environ, "XAR_KAISHEK_PREFLIGHT_REQUIRED", False)
    )
    release = open_kaishek_release or _first_env(
        environ,
        "XAR_OPEN_KAISHEK_RELEASE",
        "OPEN_KAISHEK_RELEASE",
        "KAISHEK_RELEASE",
    ) or "unreleased"
    commit_override = open_kaishek_commit or _first_env(
        environ,
        "XAR_OPEN_KAISHEK_COMMIT",
        "OPEN_KAISHEK_COMMIT",
        "KAISHEK_COMMIT",
    )
    commit = commit_override or _git_commit(checkout)

    command = [java_executable, "-jar", str(jar) if jar is not None else "", "preflight"]
    if corpus_root is not None:
        command.extend(["--root", str(corpus_root)])
    command.extend(["--profile", profile, "--fixture", fixture])

    payload = _base_result(
        outcome=_UNAVAILABLE,
        reason="open_kaishek-not-available",
        profile=profile,
        fixture=fixture,
        corpus_root=corpus_root,
        checkout=checkout,
        jar=jar,
        command=command,
        timeout_seconds=timeout,
        required=bool(required_value),
        release=release,
        commit=commit,
        ck3_build=ck3_build,
        ck3_exe_sha256=ck3_exe_sha256,
    )

    if _env_bool(environ, "XAR_KAISHEK_PREFLIGHT_DISABLED", False):
        payload["reason"] = "disabled-by-environment"
        if required_value:
            payload["status"] = _FAILED
            payload["result"] = "FAILED"
            payload["ok"] = False
            payload["reason"] = "required-but-disabled"
        return _finish(payload, artifact_path=artifact)

    if checkout is not None and not checkout.is_dir() and not explicit_jar:
        payload["reason"] = "open_kaishek-root-missing"
        if required_value:
            payload["status"] = _FAILED
            payload["result"] = "FAILED"
            payload["ok"] = False
            payload["reason"] = "required-open_kaishek-root-missing"
        return _finish(payload, artifact_path=artifact)
    if jar is None or not jar.is_file():
        payload["reason"] = "cli-jar-missing" if checkout.is_dir() else "open_kaishek-root-missing"
        if required_value:
            payload["status"] = _FAILED
            payload["result"] = "FAILED"
            payload["ok"] = False
            payload["reason"] = "required-cli-jar-missing"
        return _finish(payload, artifact_path=artifact)
    if shutil.which(java_executable) is None and not Path(java_executable).is_file():
        payload["reason"] = "java-not-found"
        if required_value:
            payload["status"] = _FAILED
            payload["result"] = "FAILED"
            payload["ok"] = False
            payload["reason"] = "required-java-not-found"
        return _finish(payload, artifact_path=artifact)

    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=str(checkout) if checkout is not None and checkout.is_dir() else None,
            env=environ,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        payload["status"] = _FAILED
        payload["result"] = "FAILED"
        payload["ok"] = False
        payload["reason"] = "cli-timeout"
        payload["stdout"] = str(error.stdout or "")
        payload["stderr"] = str(error.stderr or "")
        payload["elapsed_seconds"] = round(time.monotonic() - started, 3)
        return _finish(payload, artifact_path=artifact)
    except OSError as error:
        payload["status"] = _FAILED
        payload["result"] = "FAILED"
        payload["ok"] = False
        payload["reason"] = "cli-exec-failed"
        payload["stderr"] = f"{type(error).__name__}: {error}"
        payload["elapsed_seconds"] = round(time.monotonic() - started, 3)
        return _finish(payload, artifact_path=artifact)

    stdout = completed.stdout if isinstance(completed.stdout, str) else str(completed.stdout or "")
    stderr = completed.stderr if isinstance(completed.stderr, str) else str(completed.stderr or "")
    report = _extract_json(stdout)
    payload["exit_code"] = completed.returncode
    payload["elapsed_seconds"] = round(time.monotonic() - started, 3)
    payload["stdout"] = stdout
    payload["stderr"] = stderr
    payload["report"] = report

    if report is None:
        payload["status"] = _FAILED
        payload["result"] = "FAILED"
        payload["ok"] = False
        payload["reason"] = "invalid-cli-json"
        return _finish(payload, artifact_path=artifact)
    # Older/partial CLIs may emit the generic ``{"status":"UNSUPPORTED"}``
    # envelope without the v1 schema.  Preserve that distinction rather than
    # misreporting an explicitly unsupported semantic as a transport failure.
    if report.get("status") == "UNSUPPORTED" or completed.returncode == 4:
        payload["cli_status"] = report.get("status")
        payload["report"] = report
        payload["status"] = _UNSUPPORTED
        payload["result"] = "UNSUPPORTED"
        payload["ok"] = False
        payload["reason"] = "cli-unsupported-schema"
        return _finish(payload, artifact_path=artifact)
    if report.get("schema") != CLI_SCHEMA:
        payload["status"] = _FAILED
        payload["result"] = "FAILED"
        payload["ok"] = False
        payload["reason"] = "unexpected-cli-schema"
        return _finish(payload, artifact_path=artifact)

    cli_status = report.get("status")
    payload["cli_status"] = cli_status
    unsupported = _unsupported_items(report)
    payload["unsupported_items"] = unsupported
    report_provenance = report.get("provenance")
    if isinstance(report_provenance, dict):
        payload["provenance"]["cli_provenance"] = report_provenance
        # These hashes are useful to bind a later CK3 artifact without making
        # the adapter guess at a source tree that the CLI did not scan.
        payload["provenance"]["corpus_sha256"] = report_provenance.get("root_sha256")
    payload["provenance"]["cli_tool_version"] = report.get("tool_version")
    payload["provenance"]["cli_build_fingerprint"] = report.get("build_fingerprint")

    if cli_status == "UNSUPPORTED" or completed.returncode == 4:
        payload["status"] = _UNSUPPORTED
        payload["result"] = "UNSUPPORTED"
        payload["ok"] = False
        payload["reason"] = "cli-unsupported"
    elif cli_status != "GREEN" or completed.returncode != 0:
        payload["status"] = _FAILED
        payload["result"] = "FAILED"
        payload["ok"] = False
        payload["reason"] = "cli-red" if cli_status == "RED" else "cli-nonzero"
    elif unsupported:
        # A generic/schema-only UNSUPPORTED nested in an otherwise successful
        # envelope is not a green preflight.  Keep this explicit so callers
        # cannot accidentally gate CK3 on an unsupported semantic alias.
        payload["status"] = _UNSUPPORTED
        payload["result"] = "UNSUPPORTED"
        payload["ok"] = False
        payload["reason"] = "unsupported-semantic"
    else:
        boundary_errors = []
        for key in ("ck3_started", "save_mutated", "network_used"):
            value = report_provenance.get(key) if isinstance(report_provenance, dict) else None
            if value not in ("false", False):
                boundary_errors.append(key)
        if boundary_errors:
            payload["status"] = _FAILED
            payload["result"] = "FAILED"
            payload["ok"] = False
            payload["reason"] = "offline-boundary-violation"
            payload["boundary_errors"] = boundary_errors
        else:
            payload["status"] = _GREEN
            payload["result"] = "GREEN"
            payload["ok"] = True
            payload["reason"] = "preflight-green"

    return _finish(payload, artifact_path=artifact)


# Short aliases keep the adapter convenient for runners and tests while the
# descriptive name remains the public contract used in documentation.
run = run_preflight
preflight = run_preflight


__all__ = [
    "ADAPTER_SCHEMA",
    "CLI_CONTRACT_COMMIT",
    "CLI_SCHEMA",
    "DEFAULT_FIXTURE",
    "DEFAULT_PROFILE",
    "DEFAULT_TIMEOUT_SECONDS",
    "run",
    "run_preflight",
    "preflight",
]
