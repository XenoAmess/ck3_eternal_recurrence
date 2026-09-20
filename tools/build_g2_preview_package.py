#!/usr/bin/env python3
"""Build a parameterized, deterministic ordinary-campaign preview package.

The builder deliberately separates immutable input staging from the existing
``g2_preview_operator.py prepare-state`` no-launch check.  A candidate ZIP is
only assembled after the rebound receipt and preflight have both proved that
no CK3 process was launched.  Live qualification and GO promotion remain
external to the immutable candidate ZIP.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
from typing import Any
import zipfile


SPEC_SCHEMA = "xar.ck3.preview-package-build/v1"
INVENTORY_SCHEMA = "xar.ck3.preview-bundle-stage-sources/v2"
ASSEMBLY_SCHEMA = "xar.ck3.preview-bundle-assembly/v3"
NO_LAUNCH_SCHEMA = "xar.ck3.preview-package-no-launch-validation/v1"
REBIND_SCHEMA = "xar.ck3.ordinary-seed-rebind/v1"
QUALIFICATION_SCHEMA = "xar.ck3.preview-package-qualification-input/v1"
GO_SCHEMA = "xar.ck3.preview-live-qualification/v2"
CANDIDATE_KIND = "g2_standard_feudal_ordinary_preview_candidate"
PENDING_STATUS = "NO_GO_PENDING_EXTRACTED_BUNDLE_LIVE_SMOKE"
EXCLUSIONS = [
    "CK3 executable/body",
    "personal credentials",
    "Steam Workshop cache",
    ".venv",
    "runtime caches",
    "runtime logs/dumps",
    "mutable qualification state",
]
PROMOTION_GATES = {
    "fresh_extraction",
    "eligibility_green",
    "formal_production_entry",
    "nonempty_strategy_action",
    "independent_postcondition",
    "next_turn_consumed",
    "controlled_stop_checkpointed",
    "cold_restore_new_process",
    "same_high_level_goal",
    "no_repeat_consumed_action",
    "single_instance_cleanup",
}
REQUIRED_REPO_FILES = (
    ".gitignore",
    "ck3_autonomous_player/agent.py",
    "ck3_autonomous_player/pyproject.toml",
    "ck3_autonomous_player/src/xar_autoplayer/cli.py",
    "ck3_autonomous_player/native_bridge/research/"
    "run_campaign_root_context_live_acceptance.py",
    "tools/build_release.py",
    "tools/requirements-static.txt",
    "tools/g2_preview_operator.py",
    "tools/g2_preview_eligibility.py",
    "tools/build_g2_preview_package.py",
    "XenoAmess_s_Eternal_Recurrence/descriptor.mod",
)
PACKAGE_REPO_PATHS = (
    ".gitignore",
    "ck3_autonomous_player/agent.py",
    "ck3_autonomous_player/pyproject.toml",
    "ck3_autonomous_player/src",
    "ck3_autonomous_player/configs",
    "ck3_autonomous_player/schemas",
    "ck3_autonomous_player/strategies",
    "ck3_autonomous_player/knowledge",
    "ck3_autonomous_player/native_bridge/research/"
    "run_campaign_root_context_live_acceptance.py",
    "tools/build_release.py",
    "tools/requirements-static.txt",
    "tools/g2_preview_operator.py",
    "tools/g2_preview_eligibility.py",
    "tools/build_g2_preview_package.py",
    "XenoAmess_s_Eternal_Recurrence",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json_bytes(value))


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def input_path(base: Path, value: object, field: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a nonempty path")
    path = Path(value)
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def require_sha(value: object, field: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-fA-F]{64}", value) is None:
        raise ValueError(f"{field} must be a 64-character SHA-256")
    return value.casefold()


def require_commit(value: object, field: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-fA-F]{40}", value) is None:
        raise ValueError(f"{field} must be a 40-character Git commit")
    return value.casefold()


def require_object(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def require_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a nonempty string")
    return value


def relative_destination(value: object, field: str) -> str:
    text = require_string(value, field).replace("\\", "/")
    path = PurePosixPath(text)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ValueError(f"{field} must be a safe relative path")
    return path.as_posix()


def file_row(path: Path) -> dict[str, object]:
    return {"size": path.stat().st_size, "sha256": sha256(path)}


def snapshot(root: Path) -> dict[str, dict[str, object]]:
    if not root.is_dir():
        raise FileNotFoundError(root)
    return {
        path.relative_to(root).as_posix(): file_row(path)
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix())
        if path.is_file()
    }


def snapshot_digest(value: dict[str, dict[str, object]]) -> str:
    wire = json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("ascii")
    return hashlib.sha256(wire).hexdigest()


def verify_artifact(base: Path, value: object, field: str) -> tuple[Path, str]:
    item = require_object(value, field)
    path = input_path(base, item.get("path"), f"{field}.path")
    expected = require_sha(item.get("sha256"), f"{field}.sha256")
    if not path.is_file():
        raise FileNotFoundError(path)
    actual = sha256(path)
    if actual != expected:
        raise ValueError(f"{field} hash differs: {actual} != {expected}")
    return path, actual


def expected_context(value: object) -> dict[str, Any]:
    context = require_object(value, "sample_resume.expected_active_context")
    if set(context) != {
        "war_ids",
        "army_ids",
        "active_event",
        "pending_character_interaction",
    }:
        raise ValueError("expected_active_context must contain exactly four fields")
    for field in ("war_ids", "army_ids"):
        rows = context[field]
        if (
            not isinstance(rows, list)
            or any(not isinstance(row, int) or isinstance(row, bool) or row <= 0 for row in rows)
            or len(rows) != len(set(rows))
        ):
            raise ValueError(f"expected_active_context.{field} must be unique positive integers")
    if context["active_event"] is not None or context["pending_character_interaction"] is not None:
        raise ValueError("ordinary preview builder currently requires null event/interaction")
    return json.loads(json.dumps(context))


def validate_spec(spec: dict[str, Any]) -> dict[str, Any]:
    if spec.get("schema") != SPEC_SCHEMA:
        raise ValueError(f"build spec schema must be {SPEC_SCHEMA!r}")
    output = require_object(spec.get("output"), "output")
    zip_name = require_string(output.get("zip_name"), "output.zip_name")
    if Path(zip_name).name != zip_name or not zip_name.casefold().endswith(".zip"):
        raise ValueError("output.zip_name must be a plain .zip filename")
    source = require_object(spec.get("source"), "source")
    require_commit(source.get("commit"), "source.commit")
    require_string(source.get("repo"), "source.repo")
    require_string(source.get("canonical_remote_url"), "source.canonical_remote_url")
    ck3 = require_object(spec.get("ck3"), "ck3")
    require_string(ck3.get("exact_build"), "ck3.exact_build")
    require_sha(ck3.get("exe_sha256"), "ck3.exe_sha256")
    if ck3.get("exe_included") is not False:
        raise ValueError("ck3.exe_included must be false")
    native = require_object(spec.get("native"), "native")
    require_commit(native.get("source_commit"), "native.source_commit")
    require_string(native.get("relation"), "native.relation")
    for field in ("dll", "injector"):
        require_object(native.get(field), f"native.{field}")
        require_sha(native[field].get("sha256"), f"native.{field}.sha256")
    sample = require_object(spec.get("sample_resume"), "sample_resume")
    for field in ("checkpoint", "driver_state"):
        require_object(sample.get(field), f"sample_resume.{field}")
        require_sha(sample[field].get("sha256"), f"sample_resume.{field}.sha256")
    for field in ("date_raw", "history_index", "episode_character_id"):
        if not isinstance(sample.get(field), int) or isinstance(sample[field], bool) or sample[field] < 0:
            raise ValueError(f"sample_resume.{field} must be a nonnegative integer")
    for field in ("episode_run_id", "pipe"):
        require_string(sample.get(field), f"sample_resume.{field}")
    expected_context(sample.get("expected_active_context"))
    require_object(sample.get("goal"), "sample_resume.goal")
    lifecycle = require_object(spec.get("lifecycle"), "lifecycle")
    expected_lifecycle = {
        "xar_enabled": "xar_off",
        "succession_lifecycle": "ordinary_campaign_succession",
        "ordinary_campaign_no_pact": True,
        "government": "feudal_government",
    }
    if lifecycle != expected_lifecycle:
        raise ValueError(f"lifecycle must equal {expected_lifecycle!r}")
    content = require_object(spec.get("content"), "content")
    for field in ("dlc_load", "production_manifest"):
        require_object(content.get(field), f"content.{field}")
        require_sha(content[field].get("sha256"), f"content.{field}.sha256")
    production = require_object(content.get("production_tree"), "content.production_tree")
    require_string(production.get("path"), "content.production_tree.path")
    if not isinstance(production.get("file_count"), int) or production["file_count"] <= 0:
        raise ValueError("content.production_tree.file_count must be positive")
    require_sha(production.get("tree_sha256"), "content.production_tree.tree_sha256")
    enabled_mods = content.get("enabled_mods_in_order")
    disabled_dlcs = content.get("disabled_dlcs")
    if (
        not isinstance(enabled_mods, list)
        or not enabled_mods
        or any(not isinstance(row, str) or not row for row in enabled_mods)
    ):
        raise ValueError("content.enabled_mods_in_order must be a nonempty string list")
    if not isinstance(disabled_dlcs, list) or any(
        not isinstance(row, str) or not row for row in disabled_dlcs
    ):
        raise ValueError("content.disabled_dlcs must be a string list")
    if (
        not isinstance(content.get("installed_dlc_descriptors"), int)
        or isinstance(content["installed_dlc_descriptors"], bool)
        or content["installed_dlc_descriptors"] < 0
    ):
        raise ValueError("content.installed_dlc_descriptors must be nonnegative")
    if not isinstance(content.get("dlc_entitlement_verified"), bool):
        raise ValueError("content.dlc_entitlement_verified must be boolean")
    bounds = require_object(spec.get("bounds"), "bounds")
    for field in (
        "formal_turns",
        "timeout_seconds",
        "session_ceiling_seconds",
        "readiness_timeout_seconds",
    ):
        if not isinstance(bounds.get(field), int) or bounds[field] <= 0:
            raise ValueError(f"bounds.{field} must be a positive integer")
    if bounds["timeout_seconds"] <= bounds["readiness_timeout_seconds"]:
        raise ValueError("bounds.timeout_seconds must exceed readiness_timeout_seconds")
    if bounds["session_ceiling_seconds"] < bounds["timeout_seconds"]:
        raise ValueError("bounds.session_ceiling_seconds must cover timeout_seconds")
    release = require_object(spec.get("release"), "release")
    if release.get("candidate_status") != PENDING_STATUS:
        raise ValueError(f"release.candidate_status must be {PENDING_STATUS!r}")
    require_string(release.get("g2_authoritative"), "release.g2_authoritative")
    for field in ("supported_boundary", "unsupported_boundary"):
        rows = release.get(field)
        if not isinstance(rows, list) or not rows or any(not isinstance(row, str) or not row for row in rows):
            raise ValueError(f"release.{field} must be a nonempty string list")
    evidence = spec.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        raise ValueError("evidence must be a nonempty list")
    seen: set[str] = set()
    for index, row in enumerate(evidence):
        item = require_object(row, f"evidence[{index}]")
        destination = relative_destination(item.get("dest"), f"evidence[{index}].dest")
        if not destination.startswith("evidence/"):
            raise ValueError("evidence destinations must be below evidence/")
        folded = destination.casefold()
        if folded in seen:
            raise ValueError(f"duplicate evidence destination: {destination}")
        seen.add(folded)
        require_string(item.get("source"), f"evidence[{index}].source")
        require_sha(item.get("sha256"), f"evidence[{index}].sha256")
        require_string(item.get("role"), f"evidence[{index}].role")
    host = require_object(spec.get("build_host"), "build_host")
    for field in ("python", "game_dir", "no_launch_state_dir"):
        require_string(host.get(field), f"build_host.{field}")
    return spec


def load_spec(path: Path) -> tuple[dict[str, Any], Path]:
    path = path.resolve()
    return validate_spec(read_json(path)), path.parent


def run_git(repo: Path, *arguments: str) -> str:
    environment = os.environ.copy()
    if arguments and arguments[0] == "status":
        environment["GIT_OPTIONAL_LOCKS"] = "0"
    return subprocess.check_output(
        ["git", "-C", str(repo), *arguments],
        text=True,
        stderr=subprocess.STDOUT,
        env=environment,
    ).strip()


def verify_source_repo(spec: dict[str, Any], base: Path) -> tuple[Path, str]:
    source = spec["source"]
    repo = input_path(base, source["repo"], "source.repo")
    if not (repo / ".git").exists():
        raise ValueError(f"source repo lacks usable .git metadata: {repo}")
    expected = require_commit(source["commit"], "source.commit")
    actual = run_git(repo, "rev-parse", "HEAD").casefold()
    if actual != expected:
        raise ValueError(f"source commit differs: {actual} != {expected}")
    dirty = run_git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    if dirty:
        raise ValueError(f"source repository is dirty: {dirty[:500]}")
    missing = [relative for relative in REQUIRED_REPO_FILES if not (repo / relative).is_file()]
    if missing:
        raise ValueError(f"source checkout lacks required package files: {missing}")
    return repo, actual


def git_bytes(repo: Path, *arguments: str, stdin: bytes | None = None) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(repo), *arguments],
        input=stdin,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode(errors="replace").strip()
        raise ValueError(f"git {' '.join(arguments)} failed: {detail}")
    return completed.stdout


def ls_tree_rows(repo: Path, commit: str, *paths: str) -> list[tuple[str, str, str, str]]:
    command = ["ls-tree", "-r", "-z", "--full-tree", commit]
    if paths:
        command.extend(["--", *paths])
    rows: list[tuple[str, str, str, str]] = []
    for raw in git_bytes(repo, *command).split(b"\0"):
        if not raw:
            continue
        metadata, separator, name = raw.partition(b"\t")
        if not separator:
            raise ValueError("git ls-tree emitted a malformed row")
        mode, kind, object_id = metadata.decode("ascii").split()
        rows.append((mode, kind, object_id, name.decode("utf-8")))
    return rows


def write_git_object(target: Path, kind: str, object_id: str, data: bytes) -> None:
    actual = git_bytes(target, "hash-object", "-t", kind, "-w", "--stdin", stdin=data)
    if actual.decode("ascii").strip() != object_id:
        raise ValueError(f"Git object identity differs for {kind} {object_id}")


def build_frozen_repo(
    source: Path,
    target: Path,
    commit: str,
    canonical_remote: str,
) -> None:
    """Create a path-independent sparse checkout with deterministic Git metadata."""

    target.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(target)], check=True)
    git_dir = target / ".git"
    for relative in ("hooks", "logs", "branches"):
        path = git_dir / relative
        if path.is_dir():
            shutil.rmtree(path)
    for relative in ("description", "FETCH_HEAD", "ORIG_HEAD", "index.lock"):
        path = git_dir / relative
        if path.exists():
            path.unlink()
    (git_dir / "info").mkdir(parents=True, exist_ok=True)
    # ZIP only preserves file entries.  Keep the otherwise-empty directories
    # that Git requires when recognizing a non-bare repository after a fresh
    # extraction.
    for relative in (
        "refs/.keep",
        "objects/info/.keep",
        "objects/pack/.keep",
    ):
        marker = git_dir / relative
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_bytes(b"")
    config = (
        "[core]\n"
        "\trepositoryformatversion = 0\n"
        "\tfilemode = false\n"
        "\tbare = false\n"
        "\tlogallrefupdates = false\n"
        "\tsymlinks = false\n"
        "\tignorecase = true\n"
        "\tsparseCheckout = true\n"
        "[remote \"origin\"]\n"
        f"\turl = {canonical_remote}\n"
        "\tfetch = +refs/heads/master:refs/remotes/origin/master\n"
    )
    lowered = config.casefold()
    if any(token in lowered for token in ("extraheader", "authorization:", "password=", "token=")):
        raise ValueError("canonical Git config contains credential-bearing settings")
    (git_dir / "config").write_text(config, encoding="utf-8", newline="\n")
    patterns = "".join(f"/{path}/\n" if "." not in PurePosixPath(path).name else f"/{path}\n" for path in PACKAGE_REPO_PATHS)
    (git_dir / "info" / "sparse-checkout").write_text(
        patterns, encoding="utf-8", newline="\n"
    )

    commit_bytes = git_bytes(source, "cat-file", "commit", commit)
    write_git_object(target, "commit", commit, commit_bytes)
    root_tree = run_git(source, "show", "-s", "--format=%T", commit)
    tree_ids = {root_tree}
    tree_output = git_bytes(
        source, "ls-tree", "-r", "-t", "-z", "--full-tree", commit
    )
    for raw in tree_output.split(b"\0"):
        if not raw:
            continue
        metadata = raw.partition(b"\t")[0].decode("ascii").split()
        if len(metadata) == 3 and metadata[1] == "tree":
            tree_ids.add(metadata[2])
    for object_id in sorted(tree_ids):
        write_git_object(
            target,
            "tree",
            object_id,
            git_bytes(source, "cat-file", "tree", object_id),
        )
    (git_dir / "HEAD").write_text(f"{commit}\n", encoding="ascii", newline="\n")
    (git_dir / "shallow").write_text(f"{commit}\n", encoding="ascii", newline="\n")

    all_rows = ls_tree_rows(source, commit)
    selected_rows = ls_tree_rows(source, commit, *PACKAGE_REPO_PATHS)
    selected_names = {row[3] for row in selected_rows}
    for mode, kind, object_id, name in selected_rows:
        if kind != "blob" or mode == "120000":
            raise ValueError(f"package source path is not a regular blob: {name}")
        data = git_bytes(source, "cat-file", "blob", object_id)
        write_git_object(target, "blob", object_id, data)
        destination = target / PurePosixPath(name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)

    index_rows = "".join(
        f"{mode} {object_id}\t{name}\n" for mode, _kind, object_id, name in all_rows
    ).encode("utf-8")
    index_path = git_dir / "index"
    if index_path.exists():
        index_path.unlink()
    git_bytes(target, "update-index", "--add", "--index-info", stdin=index_rows)
    skipped = "".join(
        f"{name}\n" for _mode, _kind, _object_id, name in all_rows if name not in selected_names
    ).encode("utf-8")
    if skipped:
        git_bytes(target, "update-index", "--skip-worktree", "--stdin", stdin=skipped)
    if run_git(target, "rev-parse", "HEAD").casefold() != commit:
        raise ValueError("normalized source repository commit differs")
    if run_git(target, "status", "--porcelain=v1", "--untracked-files=all"):
        raise ValueError("normalized frozen source repository is dirty")


def copy_verified(source: Path, target: Path, expected_sha: str) -> None:
    if sha256(source) != expected_sha:
        raise ValueError(f"source changed before copy: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    if sha256(target) != expected_sha:
        raise ValueError(f"copied bytes differ: {target}")


def operator_manifest(
    spec: dict[str, Any],
    *,
    package_root: str,
    python: str,
    game_dir: str,
    state_dir: str,
) -> dict[str, Any]:
    sample = spec["sample_resume"]
    native = spec["native"]
    content = spec["content"]
    bounds = spec["bounds"]
    lifecycle = spec["lifecycle"]
    separator = "\\"
    root = package_root.rstrip("\\/")
    return {
        "source_commit": spec["source"]["commit"].casefold(),
        "source_repo": f"{root}{separator}repo",
        "python": python,
        "game_dir": game_dir,
        "game_exe_sha256": spec["ck3"]["exe_sha256"].casefold(),
        "state_dir": state_dir,
        "source_save": f"{root}{separator}sample-resume{separator}xar_checkpoint.ck3",
        "checkpoint_sha256": sample["checkpoint"]["sha256"].casefold(),
        "driver_state_sha256": sample["driver_state"]["sha256"].casefold(),
        "episode_character_id": sample["episode_character_id"],
        "episode_run_id": sample["episode_run_id"],
        "date_raw": sample["date_raw"],
        "pipe": sample["pipe"],
        "dll": f"{root}{separator}native{separator}xar_ck3_bridge.dll",
        "dll_sha256": native["dll"]["sha256"].casefold(),
        "injector": f"{root}{separator}native{separator}xar_ck3_bridge_injector.exe",
        "injector_sha256": native["injector"]["sha256"].casefold(),
        "environment_sha256": None,
        "production_tree_sha256": content["production_tree"]["tree_sha256"].casefold(),
        "xar_enabled": lifecycle["xar_enabled"],
        "succession_lifecycle": lifecycle["succession_lifecycle"],
        "ordinary_campaign_no_pact": lifecycle["ordinary_campaign_no_pact"],
        "formal_report": "written-under-command-output/formal-report.txt",
        "supported_government": lifecycle["government"],
        "timeout_seconds": bounds["timeout_seconds"],
        "session_ceiling_seconds": bounds["session_ceiling_seconds"],
        "readiness_timeout_seconds": bounds["readiness_timeout_seconds"],
        "formal_turns": bounds["formal_turns"],
        "preview_action": spec.get("preview_action"),
        "expected_active_context": expected_context(sample["expected_active_context"]),
    }


def quickstart(spec: dict[str, Any]) -> str:
    source_commit = spec["source"]["commit"].casefold()
    ck3 = spec["ck3"]
    sample = spec["sample_resume"]
    bounds = spec["bounds"]
    supported = "\n".join(f"- {row}" for row in spec["release"]["supported_boundary"])
    unsupported = "\n".join(f"- {row}" for row in spec["release"]["unsupported_boundary"])
    return rf"""# Ordinary standard-feudal CK3 auto-player preview

This immutable candidate is frozen at agent commit `{source_commit}` for CK3
`{ck3['exact_build']}` / `ck3.exe` SHA-256 `{ck3['exe_sha256'].casefold()}`. It
does not contain CK3, credentials, a Python virtual environment, Workshop
cache, mutable runtime state, or prior runtime logs.

## Qualified candidate boundary

Supported after the external GO receipt for this exact ZIP says GREEN:

{supported}

Not supported or advertised by this preview:

{unsupported}

The bundled source pair is history `{sample['history_index']}`, date
`{sample['date_raw']}`, actor `{sample['episode_character_id']}`. Its expected
initial active context is recorded exactly in `candidate-manifest.json`.

## One-time setup

The qualified Windows runtime uses CPython 3.13 (the qualification host uses
3.13.2). Extract the ZIP into a new directory, open a command prompt in that
root, and install the package's exact pinned dependencies from its
`pyproject.toml`:

```text
py -3.13 -m venv .xar-preview-venv
.xar-preview-venv\Scripts\python.exe -m pip install --disable-pip-version-check .\repo\ck3_autonomous_player
```

Copy `operator-manifest.template.json` to `operator-manifest.json`. Replace the
four `<ABSOLUTE_...>` tokens with the virtual-environment Python executable,
this extracted package root, the
CK3 install root containing `binaries\ck3.exe`, and a new empty writable state
directory. The manifest pins and verifies the CK3 executable hash before any
launch; paths for source, DLL, injector and save derive from the package root.

Confirm all managed hosts have zero CK3 processes and allocate the next
monotonic single-instance round. Then run:

```text
.xar-preview-venv\Scripts\python.exe .\repo\tools\g2_preview_operator.py prepare-state --manifest .\operator-manifest.json --sample-dir .\sample-resume
```

Do not type or guess the rebound hashes. `prepare-state` refuses to overwrite
an existing pair, performs the production-only no-launch preflight, verifies
the rebound driver bytes, and atomically records both rebound hashes in the
operator manifest.

## Read-only eligibility and bounded production play

Choose fresh monotonic output IDs for every attempt; the examples below use
`R1001` and `R1002` only as placeholders.

```text
.xar-preview-venv\Scripts\python.exe .\repo\tools\g2_preview_eligibility.py --manifest .\operator-manifest.json --output .\runs\eligibility-R1001
.xar-preview-venv\Scripts\python.exe .\repo\tools\g2_preview_operator.py run --manifest .\operator-manifest.json --output .\runs\formal-R1002 --turns {bounds['formal_turns']} --timeout {bounds['timeout_seconds']} --readiness-timeout {bounds['readiness_timeout_seconds']}
```

For a controlled checkpointed stop, from another terminal run:

```text
.xar-preview-venv\Scripts\python.exe .\repo\tools\g2_preview_operator.py request-stop --manifest .\operator-manifest.json
```

After complete process reclamation, allocate a new round and invoke the same
`run` entry with a new output directory for a real cold restore. Checkpoint:
`<state_dir>\profile\save games\xar_checkpoint.ck3`; agent state:
`<state_dir>\native-session\driver-state.json`; logs:
`<state_dir>\profile\logs`. Unknown forced states and RED remain failures. Do
not retry an action whose material result is unconfirmed.
"""


def safety_errors(bundle: Path) -> list[str]:
    errors: list[str] = []
    forbidden_parts = {
        ".venv",
        "__pycache__",
        ".pytest_cache",
        "workshop",
        "cache",
        "caches",
        "dumps",
    }
    forbidden_names = {".env", "credentials.json", "id_rsa", "id_ed25519", "ck3.exe"}
    forbidden_suffixes = {".pyc", ".pyo", ".log", ".dmp", ".mdmp"}
    folded: dict[str, str] = {}
    for path in sorted(bundle.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file():
            continue
        relative = path.relative_to(bundle).as_posix()
        collision = folded.setdefault(relative.casefold(), relative)
        if collision != relative:
            errors.append(f"case-fold collision: {collision} / {relative}")
        parts = [part.casefold() for part in path.relative_to(bundle).parts]
        if "crusader kings iii" in parts:
            errors.append(f"CK3 body path: {relative}")
        if any(part in forbidden_parts for part in parts):
            errors.append(f"forbidden cache/workshop path: {relative}")
        if path.name.casefold() in forbidden_names:
            errors.append(f"forbidden executable/credential path: {relative}")
        if path.suffix.casefold() in forbidden_suffixes:
            errors.append(f"forbidden runtime/cache suffix: {relative}")
        if "logs" in parts and ".git" not in parts:
            errors.append(f"runtime logs path: {relative}")
    return errors


def stage(spec_path: Path) -> dict[str, Any]:
    spec, base = load_spec(spec_path)
    stage_root = input_path(base, spec["output"]["stage_dir"], "output.stage_dir")
    if stage_root.exists():
        raise FileExistsError(f"stage already exists: {stage_root}")
    bundle = stage_root / "bundle"
    for relative in ("config", "evidence", "native", "sample-resume", "reference-production-mod"):
        (bundle / relative).mkdir(parents=True, exist_ok=True)
    source_repo, source_commit = verify_source_repo(spec, base)
    host = spec["build_host"]
    host_python = input_path(base, host["python"], "build_host.python")
    host_game = input_path(base, host["game_dir"], "build_host.game_dir")
    if not host_python.is_file():
        raise FileNotFoundError(host_python)
    game_executable = host_game / "binaries" / "ck3.exe"
    if not game_executable.is_file():
        raise FileNotFoundError(game_executable)
    if sha256(game_executable) != spec["ck3"]["exe_sha256"].casefold():
        raise ValueError("build host CK3 executable hash differs")
    build_frozen_repo(
        source_repo,
        bundle / "repo",
        source_commit,
        require_string(spec["source"]["canonical_remote_url"], "source.canonical_remote_url"),
    )
    if run_git(bundle / "repo", "rev-parse", "HEAD").casefold() != source_commit:
        raise ValueError("copied source commit differs")

    copy_plan: list[tuple[Path, Path, str, str]] = []
    for field, destination in (
        ("dll", "native/xar_ck3_bridge.dll"),
        ("injector", "native/xar_ck3_bridge_injector.exe"),
    ):
        path, digest = verify_artifact(base, spec["native"][field], f"native.{field}")
        copy_plan.append((path, bundle / destination, digest, f"native.{field}"))
    for field, destination in (
        ("checkpoint", "sample-resume/xar_checkpoint.ck3"),
        ("driver_state", "sample-resume/driver-state.json"),
    ):
        path, digest = verify_artifact(base, spec["sample_resume"][field], f"sample_resume.{field}")
        copy_plan.append((path, bundle / destination, digest, f"sample_resume.{field}"))
    for field, destination in (
        ("dlc_load", "config/dlc_load.json"),
        ("production_manifest", "config/xar-production.manifest.json"),
    ):
        path, digest = verify_artifact(base, spec["content"][field], f"content.{field}")
        copy_plan.append((path, bundle / destination, digest, f"content.{field}"))
    evidence_rows: list[dict[str, Any]] = []
    for index, item in enumerate(spec["evidence"]):
        source = input_path(base, item["source"], f"evidence[{index}].source")
        expected = require_sha(item["sha256"], f"evidence[{index}].sha256")
        if not source.is_file() or sha256(source) != expected:
            raise ValueError(f"evidence[{index}] source/hash differs: {source}")
        destination = relative_destination(item["dest"], f"evidence[{index}].dest")
        if destination.casefold().endswith(".json"):
            read_json(source)
        copy_plan.append((source, bundle / destination, expected, f"evidence[{index}]"))
        evidence_rows.append({"path": destination, "sha256": expected, "role": item["role"]})
    for source, target, digest, _field in copy_plan:
        copy_verified(source, target, digest)

    production_cfg = spec["content"]["production_tree"]
    production_source = input_path(base, production_cfg["path"], "content.production_tree.path")
    production_snapshot = snapshot(production_source)
    production_digest = snapshot_digest(production_snapshot)
    if (
        len(production_snapshot) != production_cfg["file_count"]
        or production_digest != production_cfg["tree_sha256"].casefold()
    ):
        raise ValueError(
            "production projection differs: "
            f"{len(production_snapshot)}/{production_digest}"
        )
    shutil.copytree(production_source, bundle / "reference-production-mod" / "xar-production")
    if snapshot(bundle / "reference-production-mod" / "xar-production") != production_snapshot:
        raise ValueError("copied production tree differs")

    sample = spec["sample_resume"]
    seed_pair = {
        "schema": "xar.ck3.preview-seed-pair/v2",
        "source_commit": source_commit,
        "checkpoint": {
            "path": "xar_checkpoint.ck3",
            "sha256": sample["checkpoint"]["sha256"].casefold(),
            "date_raw": sample["date_raw"],
            "history_index": sample["history_index"],
        },
        "driver_state": {
            "path": "driver-state.json",
            "sha256": sample["driver_state"]["sha256"].casefold(),
        },
        "episode_character_id": sample["episode_character_id"],
        "episode_run_id": sample["episode_run_id"],
        "pipe": sample["pipe"],
        "expected_active_context": expected_context(sample["expected_active_context"]),
        "goal": sample["goal"],
    }
    write_json(bundle / "sample-resume" / "seed-pair-manifest.json", seed_pair)
    template = operator_manifest(
        spec,
        package_root="<ABSOLUTE_EXTRACTED_PACKAGE_ROOT>",
        python="<ABSOLUTE_PYTHON_EXE>",
        game_dir="<ABSOLUTE_CK3_INSTALL_ROOT>",
        state_dir="<ABSOLUTE_NEW_EMPTY_STATE_DIRECTORY>",
    )
    write_json(bundle / "operator-manifest.template.json", template)
    (bundle / "QUICKSTART.md").write_text(quickstart(spec), encoding="utf-8", newline="\n")
    local = operator_manifest(
        spec,
        package_root=str(bundle),
        python=str(host_python),
        game_dir=str(host_game),
        state_dir=str(input_path(base, host["no_launch_state_dir"], "build_host.no_launch_state_dir")),
    )
    write_json(stage_root / "operator-manifest.no-launch.json", local)

    errors = safety_errors(bundle)
    if errors:
        raise ValueError("unsafe staged paths:\n" + "\n".join(errors[:30]))
    rows = [
        {"path": path.relative_to(bundle).as_posix(), **file_row(path)}
        for path in sorted(bundle.rglob("*"), key=lambda item: item.as_posix())
        if path.is_file()
    ]
    inventory = {
        "schema": INVENTORY_SCHEMA,
        "status": "SEALED_INPUTS_WAITING_NO_LAUNCH_FINALIZATION",
        "source_commit": source_commit,
        "native_source_commit": spec["native"]["source_commit"].casefold(),
        "ck3_exact_build": spec["ck3"]["exact_build"],
        "ck3_exe_sha256": spec["ck3"]["exe_sha256"].casefold(),
        "production_projection": {
            "file_count": len(production_snapshot),
            "tree_sha256": production_digest,
        },
        "evidence": evidence_rows,
        "bundle_files_before_no_launch": rows,
        "explicit_exclusions": EXCLUSIONS,
    }
    write_json(stage_root / "source-inventory.json", inventory)
    config = {
        "schema": ASSEMBLY_SCHEMA,
        "status": "WAITING_NO_LAUNCH_FINALIZATION",
        "spec_sha256": sha256(spec_path.resolve()),
        "source_commit": source_commit,
        "production_file_count": len(production_snapshot),
        "production_tree_sha256": production_digest,
        "zip_name": spec["output"]["zip_name"],
    }
    write_json(stage_root / "staging-config.json", config)
    return {
        "status": inventory["status"],
        "stage_root": str(stage_root),
        "bundle_files": len(rows),
        "production_file_count": len(production_snapshot),
        "production_tree_sha256": production_digest,
        "no_launch_manifest": str(stage_root / "operator-manifest.no-launch.json"),
        "no_launch_state_dir": local["state_dir"],
    }


def no_launch_report(state: Path) -> Path:
    reports = sorted((state / "preflights").glob("*/report.json"))
    if len(reports) != 1:
        raise ValueError(f"expected exactly one no-launch preflight report, found {len(reports)}")
    return reports[0]


def finalize_no_launch(spec_path: Path) -> dict[str, Any]:
    spec, base = load_spec(spec_path)
    stage_root = input_path(base, spec["output"]["stage_dir"], "output.stage_dir")
    bundle = stage_root / "bundle"
    config_path = stage_root / "staging-config.json"
    if not bundle.is_dir() or not config_path.is_file():
        raise FileNotFoundError("staged bundle/config is missing")
    config = read_json(config_path)
    if config.get("status") != "WAITING_NO_LAUNCH_FINALIZATION":
        raise ValueError(f"stage status does not permit finalization: {config.get('status')!r}")
    if config.get("spec_sha256") != sha256(spec_path.resolve()):
        raise ValueError("build spec changed after staging")
    state = input_path(
        base,
        spec["build_host"]["no_launch_state_dir"],
        "build_host.no_launch_state_dir",
    )
    receipt_path = state / "ordinary-seed-rebind-v1.json"
    report_path = no_launch_report(state)
    receipt = read_json(receipt_path)
    report = read_json(report_path)
    sample = spec["sample_resume"]
    lifecycle = spec["lifecycle"]
    state_save = state / "profile" / "save games" / "xar_checkpoint.ck3"
    state_driver = state / "native-session" / "driver-state.json"
    state_environment = state / "profile" / "xar-autoplayer-environment.json"
    for path in (state_save, state_driver, state_environment):
        if not path.is_file():
            raise FileNotFoundError(path)
    state_environment_payload = read_json(state_environment)
    receipt_driver_target = receipt.get("driver_state", {}).get("target_sha256")
    receipt_environment_target = receipt.get("environment", {}).get("target_sha256")
    checks = {
        "receipt_schema": receipt.get("schema") == REBIND_SCHEMA,
        "receipt_green": receipt.get("ok") is True and receipt.get("status") == "rebound",
        "receipt_no_launch": receipt.get("ck3_launch_attempted") is False,
        "preflight_green": report.get("ok") is True and report.get("status") == "ready",
        "preflight_no_launch": report.get("ck3_launch_attempted") is False,
        "pipe_exact": receipt.get("pipe_name") == sample["pipe"] and report.get("pipe") == sample["pipe"],
        "save_bytes_unchanged": receipt.get("save", {}).get("bytes_unchanged") is True
        and receipt.get("save", {}).get("target", {}).get("sha256")
        == sample["checkpoint"]["sha256"].casefold(),
        "source_driver_exact": receipt.get("driver_state", {}).get("source_sha256")
        == sample["driver_state"]["sha256"].casefold(),
        "target_pair_exact": sha256(state_save)
        == sample["checkpoint"]["sha256"].casefold()
        and sha256(state_driver) == receipt_driver_target,
        "target_environment_exact": state_environment_payload.get(
            "environment_sha256"
        )
        == receipt_environment_target
        and report.get("profile", {}).get("environment_sha256")
        == receipt_environment_target,
        "episode_exact": receipt.get("no_launch_preflight_expectations", {}).get("expected_character_id")
        == sample["episode_character_id"]
        and receipt.get("no_launch_preflight_expectations", {}).get("expected_episode_run_id")
        == sample["episode_run_id"],
        "lifecycle_exact": receipt.get("no_launch_preflight_expectations", {}).get("xar_enabled")
        == lifecycle["xar_enabled"]
        and receipt.get("no_launch_preflight_expectations", {}).get("succession_lifecycle")
        == lifecycle["succession_lifecycle"]
        and receipt.get("no_launch_preflight_expectations", {}).get("ordinary_campaign_no_pact")
        is lifecycle["ordinary_campaign_no_pact"],
        "production_exact": report.get("profile", {}).get("production_tree_sha256")
        == spec["content"]["production_tree"]["tree_sha256"].casefold(),
    }
    if not all(checks.values()):
        failed = sorted(key for key, value in checks.items() if not value)
        raise ValueError(f"no-launch finalization checks failed: {failed}")
    target_driver = require_sha(
        receipt_driver_target,
        "receipt.driver_state.target_sha256",
    )
    environment = require_sha(
        receipt_environment_target,
        "receipt.environment.target_sha256",
    )
    destinations = (
        (receipt_path, bundle / "evidence" / "package-no-launch-rebind-receipt.json"),
        (report_path, bundle / "evidence" / "package-no-launch-preflight-report.json"),
    )
    for source, target in destinations:
        shutil.copy2(source, target)
    validation = {
        "schema": NO_LAUNCH_SCHEMA,
        "status": "GREEN_NO_LAUNCH_ONLY",
        "qualifies_as_live_evidence": False,
        "source_commit": spec["source"]["commit"].casefold(),
        "runtime_projection_revision": report.get("profile", {}).get("agent_runtime_revision"),
        "repo_clean": run_git(bundle / "repo", "status", "--porcelain").strip() == "",
        "ck3_launch_attempted": False,
        "desktop_interaction": False,
        "process_inventory": report.get("process_inventory"),
        "environment_sha256": environment,
        "source_checkpoint_sha256": sha256(bundle / "sample-resume" / "xar_checkpoint.ck3"),
        "source_driver_sha256": sha256(bundle / "sample-resume" / "driver-state.json"),
        "rebound_driver_sha256": target_driver,
        "rebind_receipt_sha256": sha256(destinations[0][1]),
        "preflight_report_sha256": sha256(destinations[1][1]),
        "production_tree_sha256": report["profile"]["production_tree_sha256"],
        "checks": checks,
        "limits": [
            "No CK3 process was launched.",
            "This does not replace fresh-extraction live eligibility, material action, next-turn consumption, controlled stop, or new-process cold restore evidence.",
        ],
    }
    write_json(bundle / "evidence" / "package-no-launch-validation.json", validation)
    local_manifest_path = stage_root / "operator-manifest.no-launch.json"
    local_manifest = read_json(local_manifest_path)
    local_manifest["environment_sha256"] = environment
    local_manifest["driver_state_sha256"] = target_driver
    write_json(local_manifest_path, local_manifest)
    config.update(
        {
            "status": "NO_LAUNCH_GREEN_READY_TO_ASSEMBLE",
            "environment_sha256": environment,
            "rebound_driver_state_sha256": target_driver,
            "no_launch_validation_sha256": sha256(
                bundle / "evidence" / "package-no-launch-validation.json"
            ),
        }
    )
    write_json(config_path, config)
    return validation


def bundle_files(bundle: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in bundle.rglob("*")
            if path.is_file() and path.name != "candidate-manifest.json"
        ),
        key=lambda item: item.relative_to(bundle).as_posix(),
    )


def candidate_manifest(
    spec: dict[str, Any],
    config: dict[str, Any],
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    sample = spec["sample_resume"]
    lifecycle = spec["lifecycle"]
    content = spec["content"]
    bounds = spec["bounds"]
    release = spec["release"]
    validation_path = Path("evidence/package-no-launch-validation.json")
    return {
        "format_version": 3,
        "kind": CANDIDATE_KIND,
        "status": release["candidate_status"],
        "g2_authoritative": release["g2_authoritative"],
        "support_scope": {
            "government": lifecycle["government"],
            "ck3_exact_build": spec["ck3"]["exact_build"],
            "ck3_exe_sha256": spec["ck3"]["exe_sha256"].casefold(),
            "ck3_exe_included": False,
            "xar_enabled": lifecycle["xar_enabled"],
            "succession_lifecycle": lifecycle["succession_lifecycle"],
            "ordinary_campaign_no_pact": lifecycle["ordinary_campaign_no_pact"],
            "enabled_mods_in_order": content.get("enabled_mods_in_order", []),
            "disabled_dlcs": content.get("disabled_dlcs", []),
            "installed_dlc_descriptors": content.get("installed_dlc_descriptors"),
            "dlc_entitlement_verified": content.get("dlc_entitlement_verified", False),
        },
        "source": {
            "agent_commit": spec["source"]["commit"].casefold(),
            "native_source_commit": spec["native"]["source_commit"].casefold(),
            "native_relation": spec["native"]["relation"],
            "python_entry": "repo/ck3_autonomous_player/agent.py",
            "operator_entry": "repo/tools/g2_preview_operator.py",
            "eligibility_entry": "repo/tools/g2_preview_eligibility.py",
            "package_builder": "repo/tools/build_g2_preview_package.py",
            "native_dll": "native/xar_ck3_bridge.dll",
            "native_injector": "native/xar_ck3_bridge_injector.exe",
            "production_reference": "reference-production-mod/xar-production",
            "production_tree_sha256": config["production_tree_sha256"],
            "production_file_count": config["production_file_count"],
            "dlc_config": "config/dlc_load.json",
        },
        "sample_resume": {
            "status": "RAW_PAIR_REQUIRES_AUTOMATIC_PREPARE_STATE_REBIND",
            "checkpoint": "sample-resume/xar_checkpoint.ck3",
            "checkpoint_sha256": sample["checkpoint"]["sha256"].casefold(),
            "driver_state": "sample-resume/driver-state.json",
            "driver_state_sha256": sample["driver_state"]["sha256"].casefold(),
            "rebound_hash_source": "prepare-state receipt",
            "pipe": sample["pipe"],
            "episode_character_id": sample["episode_character_id"],
            "episode_run_id": sample["episode_run_id"],
            "saved_date_raw": sample["date_raw"],
            "history_index": sample["history_index"],
            "active_goal": sample["goal"],
        },
        "expected_active_context": expected_context(sample["expected_active_context"]),
        "formal_entry": {
            "prepare": "repo/tools/g2_preview_operator.py prepare-state",
            "eligibility": "repo/tools/g2_preview_eligibility.py",
            "run": "repo/tools/g2_preview_operator.py run",
            "stop": "repo/tools/g2_preview_operator.py request-stop",
            "status": "repo/tools/g2_preview_operator.py status",
            "verify_zip": "repo/tools/g2_preview_operator.py verify-zip",
            "bridge_mode": "native-headless",
            "cold_start_checkpoint": True,
            "bounded_turns": bounds["formal_turns"],
            "timeout_seconds": bounds["timeout_seconds"],
            "session_ceiling_seconds": bounds["session_ceiling_seconds"],
            "readiness_timeout_seconds": bounds["readiness_timeout_seconds"],
            "checkpoint_in_state": "profile/save games/xar_checkpoint.ck3",
            "driver_state_in_state": "native-session/driver-state.json",
            "game_logs_in_state": "profile/logs",
        },
        "preview_action": spec.get("preview_action"),
        "no_launch_validation": {
            **read_json(Path(config["stage_root"]) / "bundle" / validation_path),
            "receipt": "evidence/package-no-launch-rebind-receipt.json",
            "preflight": "evidence/package-no-launch-preflight-report.json",
            "summary": validation_path.as_posix(),
        },
        "historical_evidence": [
            {
                "path": relative_destination(row["dest"], "evidence.dest"),
                "sha256": row["sha256"].casefold(),
                "role": row["role"],
            }
            for row in spec["evidence"]
        ],
        "supported_boundary": release["supported_boundary"],
        "known_limits": release["unsupported_boundary"],
        "explicit_exclusions": EXCLUSIONS,
        "assembly": {
            "schema": ASSEMBLY_SCHEMA,
            "source_commit": config["source_commit"],
            "production_file_count": config["production_file_count"],
            "production_tree_sha256": config["production_tree_sha256"],
            "deterministic_zip": {
                "timestamp": "1980-01-01T00:00:00",
                "compression": "deflate-6",
                "mode": "100644",
            },
        },
        "bundle_files_excluding_this_manifest": rows,
    }


def verify_zip(archive_path: Path, bundle: Path) -> dict[str, Any]:
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or len(names) != len({name.casefold() for name in names}):
            raise ValueError("ZIP contains duplicate or case-fold-colliding names")
        bad = archive.testzip()
        if bad is not None:
            raise ValueError(f"ZIP CRC failure: {bad}")
        expected = {
            path.relative_to(bundle).as_posix(): path
            for path in bundle.rglob("*")
            if path.is_file()
        }
        if set(names) != set(expected):
            raise ValueError("ZIP member set differs from assembled bundle")
        for name, path in expected.items():
            data = archive.read(name)
            if len(data) != path.stat().st_size or hashlib.sha256(data).hexdigest() != sha256(path):
                raise ValueError(f"ZIP member bytes differ: {name}")
    return {
        "zip_size": archive_path.stat().st_size,
        "zip_sha256": sha256(archive_path),
        "zip_entry_count": len(names),
        "zip_crc_test": "GREEN",
    }


def assemble(spec_path: Path) -> dict[str, Any]:
    spec, base = load_spec(spec_path)
    stage_root = input_path(base, spec["output"]["stage_dir"], "output.stage_dir")
    bundle = stage_root / "bundle"
    config = read_json(stage_root / "staging-config.json")
    if config.get("status") not in {
        "NO_LAUNCH_GREEN_READY_TO_ASSEMBLE",
        "ASSEMBLED_PENDING_EXTRACTED_BUNDLE_LIVE_SMOKE",
    }:
        raise ValueError(f"stage status does not permit assembly: {config.get('status')!r}")
    if config.get("spec_sha256") != sha256(spec_path.resolve()):
        raise ValueError("build spec changed after staging")
    if run_git(bundle / "repo", "rev-parse", "HEAD").casefold() != config["source_commit"]:
        raise ValueError("bundled repository commit differs")
    if run_git(bundle / "repo", "status", "--porcelain=v1", "--untracked-files=all"):
        raise ValueError("bundled repository is dirty")
    production = snapshot(bundle / "reference-production-mod" / "xar-production")
    if (
        len(production) != config["production_file_count"]
        or snapshot_digest(production) != config["production_tree_sha256"]
    ):
        raise ValueError("bundled production tree differs")
    errors = safety_errors(bundle)
    if errors:
        raise ValueError("unsafe bundle paths:\n" + "\n".join(errors[:30]))
    files = bundle_files(bundle)
    rows = [
        {"path": path.relative_to(bundle).as_posix(), **file_row(path)}
        for path in files
    ]
    config_with_root = {**config, "stage_root": str(stage_root)}
    manifest = candidate_manifest(spec, config_with_root, rows)
    internal = bundle / "candidate-manifest.json"
    internal.write_bytes(json_bytes(manifest))
    archive_path = stage_root / config["zip_name"]
    if archive_path.exists():
        archive_path.unlink()
    paths = sorted(
        [*files, internal], key=lambda item: item.relative_to(bundle).as_posix()
    )
    with zipfile.ZipFile(
        archive_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6,
    ) as archive:
        for path in paths:
            relative = path.relative_to(bundle).as_posix()
            info = zipfile.ZipInfo(relative, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.extra = b""
            info.comment = b""
            with path.open("rb") as source, archive.open(info, "w") as target:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    target.write(block)
    verified = verify_zip(archive_path, bundle)
    download = {
        "format_version": 3,
        "kind": "g2_preview_candidate_download",
        "status": manifest["status"],
        "zip_path": str(archive_path),
        **verified,
        "manifest_inside_zip": "candidate-manifest.json",
        "manifest_sha256": sha256(internal),
        "source_commit": config["source_commit"],
        "native_source_commit": spec["native"]["source_commit"].casefold(),
        "no_ck3_body": True,
        "extracted_bundle_live_smoke": "PENDING",
        "promotion_model": "External live qualification binds GO to this exact immutable ZIP SHA-256; the ZIP is never rewritten after qualification.",
    }
    write_json(stage_root / "download-manifest.json", download)
    config["status"] = "ASSEMBLED_PENDING_EXTRACTED_BUNDLE_LIVE_SMOKE"
    config["zip_sha256"] = verified["zip_sha256"]
    config["candidate_manifest_sha256"] = download["manifest_sha256"]
    write_json(stage_root / "staging-config.json", config)
    return download


def qualification_artifact(
    base: Path, value: object, field: str
) -> tuple[dict[str, object], dict[str, Any]]:
    path, digest = verify_artifact(base, value, field)
    return (
        {"path": str(path), "size": path.stat().st_size, "sha256": digest},
        read_json(path),
    )


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        temporary.unlink()
    temporary.write_bytes(json_bytes(value))
    temporary.replace(path)


def promote(spec_path: Path, qualification_path: Path) -> dict[str, Any]:
    spec, spec_base = load_spec(spec_path)
    qualification_path = qualification_path.resolve()
    qualification = read_json(qualification_path)
    qualification_base = qualification_path.parent
    if qualification.get("schema") != QUALIFICATION_SCHEMA:
        raise ValueError(f"qualification schema must be {QUALIFICATION_SCHEMA!r}")
    gates = qualification.get("gates")
    if not isinstance(gates, dict) or set(gates) != PROMOTION_GATES or not all(
        value is True for value in gates.values()
    ):
        raise ValueError("qualification gates must be the exact all-GREEN promotion set")
    stage_root = input_path(
        spec_base, spec["output"]["stage_dir"], "output.stage_dir"
    )
    bundle = stage_root / "bundle"
    config = read_json(stage_root / "staging-config.json")
    if config.get("status") != "ASSEMBLED_PENDING_EXTRACTED_BUNDLE_LIVE_SMOKE":
        raise ValueError("candidate is not assembled and pending live smoke")
    archive = stage_root / config["zip_name"]
    actual_zip = sha256(archive)
    expected_zip = require_sha(
        qualification.get("package_zip_sha256"),
        "qualification.package_zip_sha256",
    )
    if actual_zip != expected_zip or config.get("zip_sha256") != expected_zip:
        raise ValueError("qualification ZIP identity differs from assembled candidate")
    before_bytes = archive.read_bytes()
    verified_zip = verify_zip(archive, bundle)
    with zipfile.ZipFile(archive) as zipped:
        internal_bytes = zipped.read("candidate-manifest.json")
    internal = json.loads(internal_bytes.decode("utf-8-sig"))
    if not isinstance(internal, dict):
        raise ValueError("candidate manifest inside ZIP is not an object")
    source_commit = require_commit(
        qualification.get("source_commit"), "qualification.source_commit"
    )
    native_commit = require_commit(
        qualification.get("native_source_commit"),
        "qualification.native_source_commit",
    )
    if (
        source_commit != spec["source"]["commit"].casefold()
        or source_commit != internal.get("source", {}).get("agent_commit")
        or native_commit != spec["native"]["source_commit"].casefold()
        or native_commit != internal.get("source", {}).get("native_source_commit")
    ):
        raise ValueError("qualification source/native pins differ")

    rounds = require_object(qualification.get("rounds"), "qualification.rounds")
    if set(rounds) != {"eligibility", "formal_stop", "cold_restore"}:
        raise ValueError("qualification rounds must be eligibility/formal_stop/cold_restore")
    round_numbers: list[int] = []
    evidence: dict[str, Any] = {}
    parsed: dict[str, dict[str, Any]] = {}
    for role in ("eligibility", "formal_stop", "cold_restore"):
        row = require_object(rounds[role], f"qualification.rounds.{role}")
        round_id = require_string(row.get("round_id"), f"qualification.rounds.{role}.round_id")
        if re.fullmatch(r"R[1-9][0-9]*", round_id) is None:
            raise ValueError(f"invalid qualification round ID: {round_id}")
        round_numbers.append(int(round_id[1:]))
        required_artifacts = ["report", "closed_ledger"]
        if role != "eligibility":
            required_artifacts.append("operator_receipt")
        evidence[role] = {"round_id": round_id}
        parsed[role] = {}
        for artifact_name in required_artifacts:
            artifact, payload = qualification_artifact(
                qualification_base,
                row.get(artifact_name),
                f"qualification.rounds.{role}.{artifact_name}",
            )
            evidence[role][artifact_name] = artifact
            parsed[role][artifact_name] = payload
        ledger = parsed[role]["closed_ledger"]
        cleanup = ledger.get("cleanup")
        if (
            ledger.get("round_id") != round_id
            or str(ledger.get("package_zip_sha256", "")).casefold() != expected_zip
            or ledger.get("source_commit") != source_commit
            or not isinstance(cleanup, dict)
            or cleanup.get("ok") is not True
            or cleanup.get("tree_gone") is not True
        ):
            raise ValueError(f"{role} closed ledger is not exact/clean")
    if round_numbers != sorted(set(round_numbers)):
        raise ValueError("qualification round IDs must be distinct and increasing")

    eligibility = parsed["eligibility"]["report"]
    eligibility_checks = eligibility.get("checks")
    if (
        eligibility.get("ok") is not True
        or eligibility.get("status") != "GREEN_READ_ONLY"
        or not isinstance(eligibility_checks, dict)
        or not eligibility_checks
        or not all(value is True for value in eligibility_checks.values())
    ):
        raise ValueError("fresh-extraction eligibility report is not fully GREEN")
    formal = parsed["formal_stop"]["report"]
    formal_receipt = parsed["formal_stop"]["operator_receipt"]
    if not (
        formal.get("ok") is False
        and formal.get("status") == "operator_stop_checkpointed"
        and formal.get("outcome") == "operator_stopped"
        and formal_receipt.get("ok") is True
        and formal_receipt.get("status") == "completed"
        and formal_receipt.get("formal_exit_code") == 0
    ):
        raise ValueError("formal report/receipt is not a controlled checkpointed stop")
    cold = parsed["cold_restore"]["report"]
    cold_receipt = parsed["cold_restore"]["operator_receipt"]
    if not (
        cold.get("ok") is True
        and cold.get("status") == "turn_limit"
        and cold_receipt.get("ok") is True
        and cold_receipt.get("status") == "completed"
        and cold_receipt.get("formal_exit_code") == 0
    ):
        raise ValueError("cold-restore report/receipt is not GREEN")

    chain = require_object(qualification.get("chain"), "qualification.chain")
    for field in (
        "formal_checkpoint_after_sha256",
        "formal_driver_after_sha256",
        "cold_checkpoint_before_sha256",
        "cold_driver_before_sha256",
        "cold_checkpoint_after_sha256",
        "cold_driver_after_sha256",
    ):
        chain[field] = require_sha(chain.get(field), f"qualification.chain.{field}")
    if (
        chain["formal_checkpoint_after_sha256"]
        != chain["cold_checkpoint_before_sha256"]
        or chain["formal_driver_after_sha256"]
        != chain["cold_driver_before_sha256"]
    ):
        raise ValueError("formal-stop and cold-restore paired state does not chain")
    if (
        formal_receipt.get("checkpoint_sha256_after")
        != chain["formal_checkpoint_after_sha256"]
        or formal_receipt.get("driver_state_sha256_after")
        != chain["formal_driver_after_sha256"]
        or cold_receipt.get("checkpoint_sha256_before")
        != chain["cold_checkpoint_before_sha256"]
        or cold_receipt.get("driver_state_sha256_before")
        != chain["cold_driver_before_sha256"]
        or cold_receipt.get("checkpoint_sha256_after")
        != chain["cold_checkpoint_after_sha256"]
        or cold_receipt.get("driver_state_sha256_after")
        != chain["cold_driver_after_sha256"]
    ):
        raise ValueError("operator receipts do not match the declared pair chain")
    previous_pid = chain.get("formal_process_id")
    current_pid = chain.get("cold_process_id")
    if (
        not isinstance(previous_pid, int)
        or isinstance(previous_pid, bool)
        or not isinstance(current_pid, int)
        or isinstance(current_pid, bool)
        or previous_pid <= 0
        or current_pid <= 0
        or previous_pid == current_pid
    ):
        raise ValueError("cold restore must bind two distinct positive process IDs")
    final_checkpoint, _ = verify_artifact(
        qualification_base,
        chain.get("final_checkpoint"),
        "qualification.chain.final_checkpoint",
    )
    final_driver, _ = verify_artifact(
        qualification_base,
        chain.get("final_driver_state"),
        "qualification.chain.final_driver_state",
    )
    if (
        sha256(final_checkpoint) != chain["cold_checkpoint_after_sha256"]
        or sha256(final_driver) != chain["cold_driver_after_sha256"]
    ):
        raise ValueError("frozen final pair differs from cold-restore receipt")

    output_cfg = require_object(qualification.get("output"), "qualification.output")
    receipt_path = input_path(
        qualification_base,
        output_cfg.get("qualification_receipt"),
        "qualification.output.qualification_receipt",
    )
    if receipt_path.exists():
        raise FileExistsError(receipt_path)
    package_sha_before_promotion = sha256(archive)
    receipt = {
        "schema": GO_SCHEMA,
        "status": "GO_RUNNABLE_PREVIEW",
        "qualification_scope": "exact immutable ZIP only",
        "g2_authoritative": {
            "status": spec["release"]["g2_authoritative"],
            "preview_does_not_complete_new_g2_milestone": True,
        },
        "immutable_package": {
            "zip": {
                "path": str(archive),
                **verified_zip,
                "modified_by_live_qualification": False,
            },
            "internal_candidate_manifest": {
                "path": "candidate-manifest.json",
                "sha256": hashlib.sha256(internal_bytes).hexdigest(),
                "frozen_status": internal.get("status"),
            },
        },
        "version_pins": {
            "agent_commit": source_commit,
            "native_source_commit": native_commit,
            "ck3_exact_build": spec["ck3"]["exact_build"],
            "ck3_exe_sha256": spec["ck3"]["exe_sha256"].casefold(),
            "production_tree_sha256": config["production_tree_sha256"],
        },
        "gates": gates,
        "live_evidence": evidence,
        "paired_cold_restore": {
            **chain,
            "final_checkpoint": {
                "path": str(final_checkpoint),
                **file_row(final_checkpoint),
            },
            "final_driver_state": {
                "path": str(final_driver),
                **file_row(final_driver),
            },
        },
        "supported_boundary": spec["release"]["supported_boundary"],
        "known_limits": spec["release"]["unsupported_boundary"],
        "qualification_input": {
            "path": str(qualification_path),
            "sha256": sha256(qualification_path),
        },
    }
    atomic_json(receipt_path, receipt)
    receipt_sha = sha256(receipt_path)
    download_path = stage_root / "download-manifest.json"
    download = read_json(download_path)
    if download.get("zip_sha256") != expected_zip:
        raise ValueError("download manifest ZIP identity differs before promotion")
    download.update(
        {
            "status": "GO_RUNNABLE_PREVIEW",
            "extracted_bundle_live_smoke": "GREEN",
            "live_qualification_manifest": str(receipt_path),
            "live_qualification_sha256": receipt_sha,
            "qualification_scope": "exact immutable ZIP only",
            "g2_authoritative": spec["release"]["g2_authoritative"],
        }
    )
    atomic_json(download_path, download)
    if archive.read_bytes() != before_bytes or sha256(archive) != package_sha_before_promotion:
        raise ValueError("immutable ZIP changed during promotion")
    config["status"] = "GO_RUNNABLE_PREVIEW"
    config["live_qualification_sha256"] = receipt_sha
    write_json(stage_root / "staging-config.json", config)
    return {
        "status": "GO_RUNNABLE_PREVIEW",
        "zip_path": str(archive),
        "zip_sha256": expected_zip,
        "qualification_receipt": str(receipt_path),
        "qualification_receipt_sha256": receipt_sha,
        "download_manifest": str(download_path),
        "download_manifest_sha256": sha256(download_path),
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    for name in ("stage", "finalize-no-launch", "assemble"):
        command = commands.add_parser(name)
        command.add_argument("--config", type=Path, required=True)
    promote_parser = commands.add_parser("promote")
    promote_parser.add_argument("--config", type=Path, required=True)
    promote_parser.add_argument("--qualification", type=Path, required=True)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "stage":
            result = stage(args.config)
        elif args.command == "finalize-no-launch":
            result = finalize_no_launch(args.config)
        elif args.command == "assemble":
            result = assemble(args.config)
        else:
            result = promote(args.config, args.qualification)
    except (OSError, ValueError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps({"ok": True, **result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
