#!/usr/bin/env python3
"""Create a portable, hash-bound operator profile for the G2 no-launch gate.

The generated profile exposes one command only: the source-specific live
adapter's ``--verify-only`` path.  It cannot authorize, launch, attach to, or
control CK3.  Host identity, endpoint and every absolute deployment path are
provided by the target operator when this generator is invoked.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Mapping


REPOSITORY_ROOT = Path(__file__).resolve().parent.parents[2]
DEFAULT_MANIFEST = (
    REPOSITORY_ROOT
    / "ck3_autonomous_player"
    / "native_bridge"
    / "research"
    / "fixtures"
    / "g2_source_specific_war_loss_live_adapter_v1_manifest.json"
)
MANIFEST_SCHEMA = "xar.ck3.g2_source_specific_war_loss_live_adapter_manifest.v1"
JOB_NAME = "g2-source-specific-no-launch-preflight"
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_REQUIRED_DEPENDENCIES = frozenset(
    {
        "adapter",
        "outer_owner_runner",
        "outer_owner_manifest",
        "lifecycle_runner",
        "source_ui_runner",
        "source_provider",
        "source_contract",
        "capture_executable",
        "bridge_dll",
        "bridge_injector",
        "game_executable",
        "bookmark_events",
        "run_acceptance",
        "profile_settings_guard",
    }
)
_RUNTIME_DEPENDENCIES = frozenset(
    {
        "capture_executable",
        "bridge_dll",
        "bridge_injector",
        "game_executable",
        "bookmark_events",
    }
)


class ProfilePreparationError(ValueError):
    """The portable G2 profile inputs do not satisfy the frozen contract."""


def _object(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ProfilePreparationError(f"{label} must be an object")
    return value


def _absolute(path: Path, label: str) -> Path:
    result = path.expanduser().resolve()
    if not result.is_absolute():
        raise ProfilePreparationError(f"{label} must resolve to an absolute path")
    return result


def _file(path: Path, label: str) -> Path:
    result = _absolute(path, label)
    if not result.is_file():
        raise ProfilePreparationError(f"{label} is not a file: {result}")
    return result


def _directory(path: Path, label: str) -> Path:
    result = _absolute(path, label)
    if not result.is_dir():
        raise ProfilePreparationError(f"{label} is not a directory: {result}")
    return result


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _expected_sha(value: object, label: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9A-Fa-f]{64}", value) is None:
        raise ProfilePreparationError(f"{label} must be 64 hex characters")
    return value.upper()


def _required_file(path: Path) -> dict[str, object]:
    return {
        "path": str(path),
        "kind": "file",
        "size": path.stat().st_size,
        "sha256": _sha256(path),
    }


def _deduplicated_required_paths(
    files: list[Path], directories: list[Path]
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for path in files:
        key = os.path.normcase(str(path))
        if key in seen:
            continue
        seen.add(key)
        rows.append(_required_file(path))
    for path in directories:
        key = os.path.normcase(str(path))
        if key in seen:
            continue
        seen.add(key)
        rows.append({"path": str(path), "kind": "directory"})
    return rows


def build_profile(
    *,
    target_id: str,
    display_name: str,
    token_user: str,
    desktop: str,
    machine: str,
    endpoint_host: str,
    endpoint_port: int,
    advertised_url: str | None,
    state_directory: Path,
    repository_root: Path,
    python_executable: Path,
    manifest_path: Path,
    preflight_output: Path,
    profile_settings_template: Path,
    game_executable: Path,
    bookmark_events: Path,
    capture_executable: Path,
    bridge_dll: Path,
    bridge_injector: Path,
) -> dict[str, object]:
    """Return one operator profile whose only job is G2 verify-only."""
    if _IDENTIFIER.fullmatch(target_id) is None:
        raise ProfilePreparationError("target-id is not a portable identifier")
    for value, label in (
        (display_name, "display-name"),
        (token_user, "token-user"),
        (desktop, "desktop"),
        (machine, "machine"),
        (endpoint_host, "endpoint-host"),
    ):
        if not value.strip():
            raise ProfilePreparationError(f"{label} cannot be empty")
    if not 1 <= endpoint_port <= 65535:
        raise ProfilePreparationError("endpoint-port must be in 1..65535")

    repo = _directory(repository_root, "repository-root")
    python = _file(python_executable, "python-executable")
    manifest_file = _file(manifest_path, "manifest")
    settings = _file(profile_settings_template, "profile-settings-template")
    shadercache = _directory(settings.parent / "shadercache", "warm shadercache")
    output = _absolute(preflight_output, "preflight-output")
    if output.exists():
        raise ProfilePreparationError(f"preflight-output already exists: {output}")

    try:
        manifest = _object(
            json.loads(manifest_file.read_text(encoding="utf-8-sig")), "manifest"
        )
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ProfilePreparationError(f"manifest is not UTF-8 JSON: {error}") from error
    if (
        manifest.get("schema") != MANIFEST_SCHEMA
        or manifest.get("status") != "static-ready-live-command-default-off"
        or manifest.get("default_off") is not True
        or manifest.get("live_executed") is not False
    ):
        raise ProfilePreparationError("manifest no-launch boundary drifted")
    live_admission = _object(manifest.get("live_admission"), "manifest live_admission")
    expected_war_id = live_admission.get("expected_war_id")
    if isinstance(expected_war_id, bool) or not isinstance(expected_war_id, int):
        raise ProfilePreparationError("manifest expected_war_id must be an integer")
    paths = _object(manifest.get("paths"), "manifest paths")
    hashes = _object(manifest.get("sha256"), "manifest sha256")
    missing = sorted(
        (_REQUIRED_DEPENDENCIES - paths.keys())
        | (_REQUIRED_DEPENDENCIES - hashes.keys())
    )
    if missing:
        raise ProfilePreparationError(
            "manifest dependencies are missing: " + ", ".join(missing)
        )

    runtime = {
        "game_executable": _file(game_executable, "game-executable"),
        "bookmark_events": _file(bookmark_events, "bookmark-events"),
        "capture_executable": _file(capture_executable, "capture-executable"),
        "bridge_dll": _file(bridge_dll, "bridge-dll"),
        "bridge_injector": _file(bridge_injector, "bridge-injector"),
    }
    dependencies: dict[str, Path] = {}
    for name in sorted(_REQUIRED_DEPENDENCIES):
        if name in _RUNTIME_DEPENDENCIES:
            selected = runtime[name]
        else:
            raw_path = paths[name]
            if not isinstance(raw_path, str) or not raw_path:
                raise ProfilePreparationError(f"manifest paths.{name} is invalid")
            candidate = Path(raw_path)
            selected = _file(
                candidate if candidate.is_absolute() else repo / candidate,
                f"manifest dependency {name}",
            )
        expected = _expected_sha(hashes[name], f"manifest sha256.{name}")
        actual = _sha256(selected)
        if actual != expected:
            raise ProfilePreparationError(
                f"manifest dependency drifted: {name} {actual} != {expected}"
            )
        dependencies[name] = selected

    adapter = dependencies["adapter"]
    command = [
        str(python),
        "-B",
        str(adapter),
        "--manifest",
        str(manifest_file),
        "--preflight-output",
        str(output),
        "--profile-settings-template",
        str(settings),
        "--game-executable",
        str(runtime["game_executable"]),
        "--bookmark-events",
        str(runtime["bookmark_events"]),
        "--capture-executable",
        str(runtime["capture_executable"]),
        "--bridge-dll",
        str(runtime["bridge_dll"]),
        "--bridge-injector",
        str(runtime["bridge_injector"]),
        "--expected-war-id",
        str(expected_war_id),
        "--verify-only",
    ]
    endpoint: dict[str, object] = {
        "transport": "streamable-http",
        "host": endpoint_host,
        "port": endpoint_port,
    }
    if advertised_url is not None:
        if not advertised_url.strip():
            raise ProfilePreparationError("advertised-url cannot be empty")
        endpoint["advertised_url"] = advertised_url

    required_files = [python, manifest_file, settings, *dependencies.values()]
    return {
        "schema_version": 1,
        "target": {
            "id": target_id,
            "display_name": display_name,
            "expected": {
                "token_user": token_user,
                "desktop": desktop,
                "machine": machine,
            },
        },
        "endpoint": endpoint,
        "state_directory": str(_absolute(state_directory, "state-directory")),
        "jobs": {
            JOB_NAME: {
                "command": command,
                "working_directory": str(repo),
                "exclusive_process_names": [],
                "required_paths": _deduplicated_required_paths(
                    required_files, [shadercache]
                ),
                "absent_paths": [str(output)],
            }
        },
    }


def write_profile(output_path: Path, profile: dict[str, object]) -> dict[str, object]:
    output = _absolute(output_path, "profile-output")
    if output.exists():
        raise ProfilePreparationError(f"profile-output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(profile, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, output)
    return {
        "status": "READY_TO_DEPLOY_G2_NO_LAUNCH_OPERATOR_PROFILE",
        "profile": str(output),
        "profile_sha256": hashlib.sha256(payload).hexdigest().upper(),
        "job_name": JOB_NAME,
        "ck3_launch_or_control_available": False,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-id", required=True)
    parser.add_argument("--display-name", required=True)
    parser.add_argument("--token-user", required=True)
    parser.add_argument("--desktop", required=True)
    parser.add_argument("--machine", required=True)
    parser.add_argument("--endpoint-host", default="127.0.0.1")
    parser.add_argument("--endpoint-port", type=int, required=True)
    parser.add_argument("--advertised-url")
    parser.add_argument("--state-directory", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--python-executable", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--preflight-output", type=Path, required=True)
    parser.add_argument("--profile-settings-template", type=Path, required=True)
    parser.add_argument("--game-executable", type=Path, required=True)
    parser.add_argument("--bookmark-events", type=Path, required=True)
    parser.add_argument("--capture-executable", type=Path, required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--bridge-injector", type=Path, required=True)
    parser.add_argument("--profile-output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        profile = build_profile(
            target_id=args.target_id,
            display_name=args.display_name,
            token_user=args.token_user,
            desktop=args.desktop,
            machine=args.machine,
            endpoint_host=args.endpoint_host,
            endpoint_port=args.endpoint_port,
            advertised_url=args.advertised_url,
            state_directory=args.state_directory,
            repository_root=args.repository_root,
            python_executable=args.python_executable,
            manifest_path=args.manifest,
            preflight_output=args.preflight_output,
            profile_settings_template=args.profile_settings_template,
            game_executable=args.game_executable,
            bookmark_events=args.bookmark_events,
            capture_executable=args.capture_executable,
            bridge_dll=args.bridge_dll,
            bridge_injector=args.bridge_injector,
        )
        result = write_profile(args.profile_output, profile)
    except (OSError, UnicodeError, ProfilePreparationError) as error:
        print(f"ERROR: {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
