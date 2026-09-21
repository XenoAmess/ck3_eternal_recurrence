#!/usr/bin/env python3
"""Build and verify the source closure executed by the GEN-034-D candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re


SCHEMA = "xar.ck3.gen034_d_runtime_files.v1"
ALGORITHM = "sha256(canonical-json[path,bytes,sha256])"
SOURCE_ROOTS = (
    "ck3_autonomous_player/src/xar_autoplayer",
    "ck3_autonomous_player/native_bridge/research",
)
EXACT_FILES = (
    "tools/run_acceptance.py",
    "tools/run_zg361_phase2_seed_capture.py",
)
REQUIRED_PATHS = {
    "ck3_autonomous_player/src/xar_autoplayer/native_auto_run.py",
    "ck3_autonomous_player/src/xar_autoplayer/bridge/service.py",
    "ck3_autonomous_player/native_bridge/research/gen034_candidate_authorization.py",
    "ck3_autonomous_player/native_bridge/research/gen034_runtime_manifest.py",
    "ck3_autonomous_player/native_bridge/research/run_g2_source_specific_war_loss_live_adapter.py",
    "ck3_autonomous_player/native_bridge/research/run_g2_source_specific_war_loss_outer_owner.py",
    "ck3_autonomous_player/native_bridge/research/run_g2_source_specific_war_loss_lifecycle.py",
    "ck3_autonomous_player/native_bridge/research/run_raiktor_war_bound_private_capture_v1.py",
    "ck3_autonomous_player/native_bridge/research/run_gen034_three_way_exit_action_live_acceptance.py",
    "ck3_autonomous_player/native_bridge/research/run_gen034_three_way_recommendation_live_acceptance.py",
    "ck3_autonomous_player/native_bridge/research/run_raiktor_surrender_session_binding_live_acceptance.py",
    "ck3_autonomous_player/native_bridge/research/run_war_termination_terms_live_acceptance.py",
    "tools/run_acceptance.py",
    "tools/run_zg361_phase2_seed_capture.py",
}


class RuntimeManifestError(ValueError):
    """The frozen Python source closure is incomplete or has drifted."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _expected_sha256(value: object, name: str) -> str:
    result = str(value).strip().upper()
    if re.fullmatch(r"[0-9A-F]{64}", result) is None:
        raise RuntimeManifestError(f"{name} must be 64 hexadecimal digits")
    return result


def _selected_paths(runtime_root: Path) -> list[Path]:
    root = runtime_root.expanduser().resolve()
    selected: set[Path] = set()
    for relative_root in SOURCE_ROOTS:
        source_root = root / relative_root
        if not source_root.is_dir():
            raise RuntimeManifestError(f"runtime source root is missing: {source_root}")
        selected.update(path for path in source_root.rglob("*.py") if path.is_file())
    for relative in EXACT_FILES:
        path = root / relative
        if not path.is_file():
            raise RuntimeManifestError(f"runtime source file is missing: {path}")
        selected.add(path)
    return sorted(selected, key=lambda path: path.relative_to(root).as_posix())


def _entries(runtime_root: Path) -> list[dict[str, object]]:
    root = runtime_root.expanduser().resolve()
    result = [
        {
            "path": path.relative_to(root).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in _selected_paths(root)
    ]
    present = {str(row["path"]) for row in result}
    missing = sorted(REQUIRED_PATHS - present)
    if missing:
        raise RuntimeManifestError(
            "runtime source closure lacks required files: " + ", ".join(missing)
        )
    return result


def _tree_sha256(entries: list[dict[str, object]]) -> str:
    canonical = json.dumps(
        entries,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest().upper()


def build_runtime_file_manifest(
    runtime_root: Path, *, source_commit: str
) -> dict[str, object]:
    entries = _entries(runtime_root)
    return {
        "schema": SCHEMA,
        "source_commit": source_commit,
        "algorithm": ALGORITHM,
        "selection": {
            "recursive_python_roots": list(SOURCE_ROOTS),
            "exact_files": list(EXACT_FILES),
        },
        "required_paths": sorted(REQUIRED_PATHS),
        "file_count": len(entries),
        "tree_sha256": _tree_sha256(entries),
        "files": entries,
    }


def verify_runtime_file_manifest(
    manifest_path: Path,
    *,
    runtime_root: Path,
    expected_manifest_sha256: str | None = None,
) -> dict[str, object]:
    path = manifest_path.expanduser().resolve()
    if not path.is_file():
        raise RuntimeManifestError(f"runtime manifest is missing: {path}")
    manifest_sha256 = sha256_file(path)
    if expected_manifest_sha256 is not None and manifest_sha256 != _expected_sha256(
        expected_manifest_sha256, "expected runtime manifest SHA-256"
    ):
        raise RuntimeManifestError("runtime manifest file SHA-256 drifted")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeManifestError(f"runtime manifest is unavailable: {error}") from error
    if not isinstance(manifest, dict):
        raise RuntimeManifestError("runtime manifest root must be an object")
    if manifest.get("schema") != SCHEMA or manifest.get("algorithm") != ALGORITHM:
        raise RuntimeManifestError("runtime manifest schema/algorithm drifted")
    frozen = manifest.get("files")
    if not isinstance(frozen, list) or any(not isinstance(row, dict) for row in frozen):
        raise RuntimeManifestError("runtime manifest file table is invalid")
    actual = _entries(runtime_root)
    if frozen != actual:
        frozen_by_path = {
            str(row.get("path")): row for row in frozen if isinstance(row, dict)
        }
        actual_by_path = {str(row["path"]): row for row in actual}
        changed = sorted(
            path_value
            for path_value in set(frozen_by_path) | set(actual_by_path)
            if frozen_by_path.get(path_value) != actual_by_path.get(path_value)
        )
        raise RuntimeManifestError(
            "runtime source closure drifted: " + ", ".join(changed[:16])
        )
    tree_sha256 = _tree_sha256(actual)
    if (
        manifest.get("file_count") != len(actual)
        or str(manifest.get("tree_sha256", "")).upper() != tree_sha256
        or manifest.get("required_paths") != sorted(REQUIRED_PATHS)
    ):
        raise RuntimeManifestError("runtime manifest aggregate receipt drifted")
    return {
        "status": "verified",
        "path": str(path),
        "manifest_sha256": manifest_sha256,
        "runtime_root": str(runtime_root.expanduser().resolve()),
        "source_commit": manifest.get("source_commit"),
        "file_count": len(actual),
        "tree_sha256": tree_sha256,
    }


def _write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-commit", default="unknown")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--expected-manifest-sha256")
    args = parser.parse_args(argv)
    try:
        if args.verify_only:
            result = verify_runtime_file_manifest(
                args.output,
                runtime_root=args.runtime_root,
                expected_manifest_sha256=args.expected_manifest_sha256,
            )
        else:
            _write_json_atomic(
                args.output,
                build_runtime_file_manifest(
                    args.runtime_root, source_commit=args.source_commit
                ),
            )
            result = verify_runtime_file_manifest(
                args.output, runtime_root=args.runtime_root
            )
    except (OSError, UnicodeError, json.JSONDecodeError, RuntimeManifestError) as error:
        print(f"ERROR: {type(error).__name__}: {error}")
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
