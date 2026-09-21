#!/usr/bin/env python3
"""Build or verify the hash-bound GEN-034-D candidate runner bundle."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import sys


RESEARCH_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = RESEARCH_ROOT.parents[2]
FIXTURE_ROOT = RESEARCH_ROOT / "fixtures"
OUTER_NAME = "g2_source_specific_war_loss_outer_owner_v1_manifest.json"
LIFECYCLE_NAME = "g2_source_specific_war_loss_lifecycle_v1_manifest.json"
LIVE_NAME = "g2_source_specific_war_loss_live_adapter_v1_manifest.json"
BUNDLE_NAME = "gen034-d-candidate-bundle.json"


class CandidateBundleError(ValueError):
    """A bundle input or frozen dependency drifted."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _load(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CandidateBundleError(f"JSON input is unavailable: {path}: {error}") from error
    if not isinstance(value, dict):
        raise CandidateBundleError(f"JSON root must be an object: {path}")
    return value


def _write(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _resolve_template_path(value: object, *, repository_root: Path) -> Path:
    path = Path(str(value)).expanduser()
    return path.resolve() if path.is_absolute() else (repository_root / path).resolve()


def _materialize_manifest(
    template_name: str,
    *,
    runtime_paths: dict[str, Path],
    repository_root: Path,
    output_paths: dict[str, Path] | None = None,
) -> dict[str, object]:
    result = copy.deepcopy(_load(FIXTURE_ROOT / template_name))
    paths = result.get("paths")
    hashes = result.get("sha256")
    if not isinstance(paths, dict) or not isinstance(hashes, dict):
        raise CandidateBundleError(f"manifest dependency table is invalid: {template_name}")
    for name, raw_path in list(paths.items()):
        if output_paths is not None and name in output_paths:
            path = output_paths[name]
        else:
            path = runtime_paths.get(
                name,
                _resolve_template_path(raw_path, repository_root=repository_root),
            )
        path = path.expanduser().resolve()
        if not path.is_file():
            raise CandidateBundleError(f"manifest dependency is missing: {name}: {path}")
        paths[name] = str(path)
        hashes[name] = _sha256(path)
    return result


def _verify_manifest(path: Path) -> dict[str, object]:
    value = _load(path)
    paths = value.get("paths")
    hashes = value.get("sha256")
    if not isinstance(paths, dict) or not isinstance(hashes, dict):
        raise CandidateBundleError(f"manifest dependency table is invalid: {path}")
    checked: dict[str, object] = {}
    for name, raw_path in paths.items():
        dependency = Path(str(raw_path)).expanduser().resolve()
        expected = str(hashes.get(name, "")).upper()
        if not dependency.is_file() or _sha256(dependency) != expected:
            raise CandidateBundleError(f"manifest dependency drifted: {name}: {dependency}")
        checked[name] = {
            "path": str(dependency),
            "size": dependency.stat().st_size,
            "sha256": expected,
        }
    return {
        "path": str(path.resolve()),
        "sha256": _sha256(path),
        "dependencies": checked,
    }


def build_bundle(args: argparse.Namespace) -> dict[str, object]:
    output_dir = args.output_dir.expanduser().resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise CandidateBundleError(f"output directory is not fresh: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    repository_root = args.repository_root.expanduser().resolve()
    profile_dir = output_dir / "candidate-state" / "profile"
    profile_dir.mkdir(parents=True, exist_ok=True)
    runtime_paths = {
        "capture_executable": args.capture_executable,
        "bridge_dll": args.bridge_dll,
        "bridge_injector": args.bridge_injector,
        "game_executable": args.game_root / "binaries" / "ck3.exe",
        "bookmark_events": args.game_root / "game" / "events" / "bookmark_events.txt",
    }
    outer_path = output_dir / OUTER_NAME
    lifecycle_path = output_dir / LIFECYCLE_NAME
    live_path = output_dir / LIVE_NAME
    _write(
        outer_path,
        _materialize_manifest(
            OUTER_NAME,
            runtime_paths=runtime_paths,
            repository_root=repository_root,
        ),
    )
    _write(
        lifecycle_path,
        _materialize_manifest(
            LIFECYCLE_NAME,
            runtime_paths=runtime_paths,
            repository_root=repository_root,
        ),
    )
    live = _materialize_manifest(
        LIVE_NAME,
        runtime_paths=runtime_paths,
        repository_root=repository_root,
        output_paths={"outer_owner_manifest": outer_path},
    )
    _write(live_path, live)
    command = [
        str(args.python_executable.expanduser().resolve()),
        "-B",
        str(
            (
                repository_root
                / "ck3_autonomous_player"
                / "native_bridge"
                / "research"
                / "run_g2_source_specific_war_loss_live_adapter.py"
            ).resolve()
        ),
        "--manifest",
        str(live_path),
        "--preflight-output",
        str(output_dir / "candidate-live-run-preflight.json"),
        "--artifact-dir",
        str(output_dir / "candidate-live-attempt-01"),
        "--userdir",
        str(profile_dir),
        "--profile-settings-template",
        str(args.profile_settings_template.expanduser().resolve()),
        "--game-root",
        str(args.game_root.expanduser().resolve()),
        "--capture-executable",
        str(args.capture_executable.expanduser().resolve()),
        "--bridge-dll",
        str(args.bridge_dll.expanduser().resolve()),
        "--bridge-injector",
        str(args.bridge_injector.expanduser().resolve()),
        "--expected-character-id",
        str(args.expected_character_id),
        "--candidate-terminal-intercept",
        "--candidate-turn-limit",
        str(args.candidate_turn_limit),
        "--candidate-timeout",
        str(args.candidate_timeout),
        "--authorize-private-live",
    ]
    bundle = {
        "schema": "xar.ck3.gen034_d_candidate_bundle.v1",
        "status": "static-ready-live-not-executed",
        "source_commit": args.source_commit,
        "manifests": {
            "outer_owner": _verify_manifest(outer_path),
            "lifecycle": _verify_manifest(lifecycle_path),
            "live_adapter": _verify_manifest(live_path),
        },
        "release_binaries": {
            name: {
                "path": str(path.expanduser().resolve()),
                "size": path.expanduser().resolve().stat().st_size,
                "sha256": _sha256(path.expanduser().resolve()),
            }
            for name, path in runtime_paths.items()
        },
        "profile_settings_template": str(
            args.profile_settings_template.expanduser().resolve()
        ),
        "candidate_command": command,
        "boundaries": {
            "ck3_started": False,
            "generic_exit_terms_reader_enabled": False,
            "private_terminal_action_submission": False,
            "formal_native_auto_run_required": True,
            "stop_before_first_matching_terminal_submit": True,
            "action_runner_required_after_candidate": True,
        },
    }
    _write(output_dir / BUNDLE_NAME, bundle)
    return bundle


def verify_bundle(output_dir: Path) -> dict[str, object]:
    root = output_dir.expanduser().resolve()
    bundle_path = root / BUNDLE_NAME
    bundle = _load(bundle_path)
    manifests = bundle.get("manifests")
    if not isinstance(manifests, dict):
        raise CandidateBundleError("candidate bundle lacks manifests")
    verified = {
        "outer_owner": _verify_manifest(root / OUTER_NAME),
        "lifecycle": _verify_manifest(root / LIFECYCLE_NAME),
        "live_adapter": _verify_manifest(root / LIVE_NAME),
    }
    for name, receipt in verified.items():
        frozen = manifests.get(name)
        if not isinstance(frozen, dict) or frozen.get("sha256") != receipt["sha256"]:
            raise CandidateBundleError(f"candidate manifest receipt drifted: {name}")
    return {
        "schema": "xar.ck3.gen034_d_candidate_bundle_verify.v1",
        "status": "verified-no-launch",
        "bundle": str(bundle_path),
        "bundle_sha256": _sha256(bundle_path),
        "manifests": verified,
        "ck3_started": False,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--game-root", type=Path)
    parser.add_argument("--capture-executable", type=Path)
    parser.add_argument("--bridge-dll", type=Path)
    parser.add_argument("--bridge-injector", type=Path)
    parser.add_argument("--profile-settings-template", type=Path)
    parser.add_argument("--python-executable", type=Path, default=Path(sys.executable))
    parser.add_argument("--source-commit", default="fc8d18e49ba483ba2009724ea32bac4b5a0f7062")
    parser.add_argument("--expected-character-id", type=int, default=29_829)
    parser.add_argument("--candidate-turn-limit", type=int, default=256)
    parser.add_argument("--candidate-timeout", type=float, default=1800.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.verify_only:
            result = verify_bundle(args.output_dir)
        else:
            required = {
                "game-root": args.game_root,
                "capture-executable": args.capture_executable,
                "bridge-dll": args.bridge_dll,
                "bridge-injector": args.bridge_injector,
                "profile-settings-template": args.profile_settings_template,
            }
            missing = [name for name, value in required.items() if value is None]
            if missing:
                raise CandidateBundleError(
                    "build inputs are missing: " + ", ".join(missing)
                )
            result = build_bundle(args)
    except (OSError, UnicodeError, json.JSONDecodeError, CandidateBundleError) as error:
        print(f"ERROR: {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
