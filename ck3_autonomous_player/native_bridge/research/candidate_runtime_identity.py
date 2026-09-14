"""Verify and bind a sealed candidate-local autoplayer source repository."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import ModuleType
from typing import Any


IDENTITY_SCHEMA = "xar.ck3.g2_m4_council14_runtime_source_identity_v1"
SOURCE_COMMIT = "dd36d1b7e8e3a79260a888efaeadd4b922df5f7f"
SOURCE_TREE_GIT_OID = "e73e30b1d73b29f1ae4a6e4c469358f9f927942c"
SOURCE_REPOSITORY_RELATIVE = Path("source-repo")
SOURCE_ROOT_RELATIVE = SOURCE_REPOSITORY_RELATIVE / "ck3_autonomous_player" / "src"
MODULE_PATHS = {
    "xar_autoplayer.bridge.native_driver": Path(
        "xar_autoplayer/bridge/native_driver.py"
    ),
    "xar_autoplayer.native_auto_run": Path("xar_autoplayer/native_auto_run.py"),
    "xar_autoplayer.environment": Path("xar_autoplayer/environment.py"),
    "xar_autoplayer.runtime": Path("xar_autoplayer/runtime.py"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def source_inventory(source_root: Path) -> tuple[list[dict[str, Any]], str]:
    """Return the stable file inventory and its path/size/content digest."""

    rows: list[dict[str, Any]] = []
    tree_digest = hashlib.sha256()
    for path in sorted(item for item in source_root.rglob("*") if item.is_file()):
        relative = path.relative_to(source_root).as_posix()
        file_sha = sha256(path)
        size = path.stat().st_size
        rows.append({"path": relative, "size_bytes": size, "sha256": file_sha})
        tree_digest.update(relative.encode("utf-8"))
        tree_digest.update(b"\0")
        tree_digest.update(str(size).encode("ascii"))
        tree_digest.update(b"\0")
        tree_digest.update(file_sha.encode("ascii"))
        tree_digest.update(b"\n")
    return rows, tree_digest.hexdigest().upper()


def build_source_identity(source_root: Path) -> dict[str, Any]:
    rows, tree_sha = source_inventory(source_root)
    module_sha = {
        name: sha256(source_root / relative)
        for name, relative in MODULE_PATHS.items()
    }
    return {
        "schema": IDENTITY_SCHEMA,
        "status": "sealed-candidate-local",
        "source_commit": SOURCE_COMMIT,
        "source_tree_git_oid": SOURCE_TREE_GIT_OID,
        "source_root_relative": SOURCE_ROOT_RELATIVE.as_posix(),
        "source_tree_sha256": tree_sha,
        "file_count": len(rows),
        "total_size_bytes": sum(int(row["size_bytes"]) for row in rows),
        "module_sha256": module_sha,
        "external_workspace_root_allowed": False,
    }


def load_identity(candidate_root: Path) -> dict[str, Any]:
    path = candidate_root / SOURCE_REPOSITORY_RELATIVE / "source-identity.json"
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise RuntimeError("candidate source identity is not an object")
    return payload


def verify_candidate_source(candidate_root: Path) -> tuple[Path, dict[str, Any]]:
    """Verify source commit, Git tree identity, and every candidate-local byte."""

    candidate_root = candidate_root.resolve()
    source_root = (candidate_root / SOURCE_ROOT_RELATIVE).resolve()
    source_root.relative_to(candidate_root)
    if not source_root.is_dir():
        raise RuntimeError("candidate-local source root is missing")
    identity = load_identity(candidate_root)
    expected_scalars = {
        "schema": IDENTITY_SCHEMA,
        "status": "sealed-candidate-local",
        "source_commit": SOURCE_COMMIT,
        "source_tree_git_oid": SOURCE_TREE_GIT_OID,
        "source_root_relative": SOURCE_ROOT_RELATIVE.as_posix(),
        "external_workspace_root_allowed": False,
    }
    for key, expected in expected_scalars.items():
        if identity.get(key) != expected:
            raise RuntimeError(f"candidate source identity {key} differs")
    rows, actual_tree_sha = source_inventory(source_root)
    if (
        identity.get("source_tree_sha256") != actual_tree_sha
        or identity.get("file_count") != len(rows)
        or identity.get("total_size_bytes")
        != sum(int(row["size_bytes"]) for row in rows)
    ):
        raise RuntimeError("candidate-local source inventory differs")
    module_sha = identity.get("module_sha256")
    if not isinstance(module_sha, dict) or set(module_sha) != set(MODULE_PATHS):
        raise RuntimeError("candidate source module inventory differs")
    for name, relative in MODULE_PATHS.items():
        path = source_root / relative
        if not path.is_file() or sha256(path) != module_sha.get(name):
            raise RuntimeError(f"candidate source module SHA-256 differs: {name}")
    return source_root, identity


def assert_imported_module(
    module: ModuleType,
    *,
    expected_name: str,
    source_root: Path,
    identity: dict[str, Any],
) -> None:
    """Reject an import resolved from site-packages or an operator checkout."""

    if module.__name__ != expected_name or expected_name not in MODULE_PATHS:
        raise RuntimeError(f"unexpected runtime module: {module.__name__!r}")
    raw_file = getattr(module, "__file__", None)
    if not isinstance(raw_file, str):
        raise RuntimeError(f"runtime module has no file: {expected_name}")
    actual = Path(raw_file).resolve()
    expected = (source_root / MODULE_PATHS[expected_name]).resolve()
    if actual != expected:
        raise RuntimeError(
            f"runtime module escaped candidate source: {expected_name}: {actual}"
        )
    module_sha = identity.get("module_sha256")
    if not isinstance(module_sha, dict) or sha256(actual) != module_sha.get(
        expected_name
    ):
        raise RuntimeError(f"imported runtime module SHA-256 differs: {expected_name}")

