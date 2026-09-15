"""Verify and bind a sealed R693 candidate-local autoplayer source repository."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import ModuleType
from typing import Any


IDENTITY_SCHEMA = "xar.ck3.g2_m4_council18_r693_runtime_source_identity_v1"
SOURCE_COMMIT = "41bd2d5d0c159676876f21adc3845cf0afeeaf97"
SOURCE_TREE_GIT_OID = "bcff5fae3647f57554a0456b236f0f791e1c3d27"
BUILD_RELEASE_GIT_BLOB_OID = "d7f050fc668e5cc16445b6db4efe9f5493a61ee6"
SOURCE_REPOSITORY_RELATIVE = Path("source-repo")
SOURCE_ROOT_RELATIVE = SOURCE_REPOSITORY_RELATIVE / "ck3_autonomous_player" / "src"
TOOLS_ROOT_RELATIVE = SOURCE_REPOSITORY_RELATIVE / "tools"
MODULE_PATHS = {
    "xar_autoplayer.bridge.native_driver": Path(
        "xar_autoplayer/bridge/native_driver.py"
    ),
    "xar_autoplayer.native_auto_run": Path("xar_autoplayer/native_auto_run.py"),
    "xar_autoplayer.environment": Path("xar_autoplayer/environment.py"),
    "xar_autoplayer.runtime": Path("xar_autoplayer/runtime.py"),
}
TOOL_MODULE_PATHS = {"build_release": Path("build_release.py")}
ISOLATED_PROBE_BOOTSTRAP = (
    "import runpy,sys;"
    "root=sys.argv[1];"
    "sys.path.insert(0,root);"
    "sys.argv=['candidate_runtime_import_probe.py','--candidate-root',root];"
    "runpy.run_path(root+'/candidate_runtime_import_probe.py',run_name='__main__')"
)


def isolated_import_probe_command(
    python: Path, candidate_root: Path, *, optimized: bool
) -> list[str]:
    optimization = ["-O"] if optimized else []
    return [
        str(python),
        "-I",
        *optimization,
        "-B",
        "-c",
        ISOLATED_PROBE_BOOTSTRAP,
        str(candidate_root.resolve()),
    ]


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


def build_source_identity(repository_root: Path) -> dict[str, Any]:
    source_root = repository_root / "ck3_autonomous_player" / "src"
    tools_root = repository_root / "tools"
    rows, tree_sha = source_inventory(source_root)
    module_sha = {
        name: sha256(source_root / relative)
        for name, relative in MODULE_PATHS.items()
    }
    module_sha.update(
        {
            name: sha256(tools_root / relative)
            for name, relative in TOOL_MODULE_PATHS.items()
        }
    )
    tool_rows, tools_sha = source_inventory(tools_root)
    return {
        "schema": IDENTITY_SCHEMA,
        "status": "sealed-candidate-local",
        "source_commit": SOURCE_COMMIT,
        "source_tree_git_oid": SOURCE_TREE_GIT_OID,
        "build_release_git_blob_oid": BUILD_RELEASE_GIT_BLOB_OID,
        "source_root_relative": SOURCE_ROOT_RELATIVE.as_posix(),
        "tools_root_relative": TOOLS_ROOT_RELATIVE.as_posix(),
        "source_tree_sha256": tree_sha,
        "file_count": len(rows),
        "total_size_bytes": sum(int(row["size_bytes"]) for row in rows),
        "tools_tree_sha256": tools_sha,
        "tools_file_count": len(tool_rows),
        "tools_total_size_bytes": sum(
            int(row["size_bytes"]) for row in tool_rows
        ),
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
        "build_release_git_blob_oid": BUILD_RELEASE_GIT_BLOB_OID,
        "source_root_relative": SOURCE_ROOT_RELATIVE.as_posix(),
        "tools_root_relative": TOOLS_ROOT_RELATIVE.as_posix(),
        "external_workspace_root_allowed": False,
    }
    for key, expected in expected_scalars.items():
        if identity.get(key) != expected:
            raise RuntimeError(f"candidate source identity {key} differs")
    rows, actual_tree_sha = source_inventory(source_root)
    tools_root = (candidate_root / TOOLS_ROOT_RELATIVE).resolve()
    tools_root.relative_to(candidate_root)
    if not tools_root.is_dir():
        raise RuntimeError("candidate-local tools root is missing")
    tool_rows, actual_tools_sha = source_inventory(tools_root)
    if (
        identity.get("source_tree_sha256") != actual_tree_sha
        or identity.get("file_count") != len(rows)
        or identity.get("total_size_bytes")
        != sum(int(row["size_bytes"]) for row in rows)
        or identity.get("tools_tree_sha256") != actual_tools_sha
        or identity.get("tools_file_count") != len(tool_rows)
        or identity.get("tools_total_size_bytes")
        != sum(int(row["size_bytes"]) for row in tool_rows)
    ):
        raise RuntimeError("candidate-local source inventory differs")
    module_sha = identity.get("module_sha256")
    if not isinstance(module_sha, dict) or set(module_sha) != (
        set(MODULE_PATHS) | set(TOOL_MODULE_PATHS)
    ):
        raise RuntimeError("candidate source module inventory differs")
    for name, relative in MODULE_PATHS.items():
        path = source_root / relative
        if not path.is_file() or sha256(path) != module_sha.get(name):
            raise RuntimeError(f"candidate source module SHA-256 differs: {name}")
    for name, relative in TOOL_MODULE_PATHS.items():
        path = tools_root / relative
        if not path.is_file() or sha256(path) != module_sha.get(name):
            raise RuntimeError(f"candidate tools module SHA-256 differs: {name}")
    return source_root, identity


def assert_imported_module(
    module: ModuleType,
    *,
    expected_name: str,
    source_root: Path,
    identity: dict[str, Any],
) -> None:
    """Reject an import resolved from site-packages or an operator checkout."""

    if module.__name__ != expected_name or expected_name not in (
        set(MODULE_PATHS) | set(TOOL_MODULE_PATHS)
    ):
        raise RuntimeError(f"unexpected runtime module: {module.__name__!r}")
    raw_file = getattr(module, "__file__", None)
    if not isinstance(raw_file, str):
        raise RuntimeError(f"runtime module has no file: {expected_name}")
    actual = Path(raw_file).resolve()
    if expected_name in MODULE_PATHS:
        expected = (source_root / MODULE_PATHS[expected_name]).resolve()
    else:
        expected = (
            source_root.parents[1] / "tools" / TOOL_MODULE_PATHS[expected_name]
        ).resolve()
    if actual != expected:
        raise RuntimeError(
            f"runtime module escaped candidate source: {expected_name}: {actual}"
        )
    module_sha = identity.get("module_sha256")
    if not isinstance(module_sha, dict) or sha256(actual) != module_sha.get(
        expected_name
    ):
        raise RuntimeError(f"imported runtime module SHA-256 differs: {expected_name}")

