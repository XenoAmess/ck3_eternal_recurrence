#!/usr/bin/env python3
"""Build the maintained Auto Upgrade Buildings release deterministically."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
PRODUCT_ID = "mod_auto_upgrade_buildings"
DEFAULT_SOURCE = ROOT / PRODUCT_ID
DEFAULT_OUTPUT = ROOT / "dist" / PRODUCT_ID
UPSTREAM_WORKSHOP_ITEM_ID = "3596580780"
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
RUNTIME_FILES = frozenset(
    {
        "common/decisions/build_decision.txt",
        "common/scripted_effects/build_scripted_effect.txt",
        "descriptor.mod",
        "events/auto_build.txt",
        "localization/english/auto_build_l_english.yml",
        "localization/simp_chinese/auto_build_l_simp_chinese.yml",
        "thumbnail.png",
    }
)
SOURCE_ONLY_FILES = frozenset({"README.md"})
SEMVER = re.compile(r"\d+\.\d+\.\d+")
FULL_SHA = re.compile(r"[0-9a-f]{40}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def runtime_directories() -> set[str]:
    result: set[str] = set()
    for relative in RUNTIME_FILES:
        parent = PurePosixPath(relative).parent
        while parent != PurePosixPath("."):
            result.add(parent.as_posix())
            parent = parent.parent
    return result


def source_errors(source: Path) -> list[str]:
    if not source.is_dir():
        return [f"source directory missing: {source}"]
    errors: list[str] = []
    files: set[str] = set()
    directories: set[str] = set()
    for path in sorted(source.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(source).as_posix()
        if path.is_symlink():
            errors.append(f"symlink is forbidden: {relative}")
        elif path.is_dir():
            directories.add(relative)
        elif path.is_file():
            files.add(relative)
        else:
            errors.append(f"unsupported filesystem entry: {relative}")
    allowed = RUNTIME_FILES | SOURCE_ONLY_FILES
    errors.extend(f"missing runtime file: {item}" for item in sorted(RUNTIME_FILES - files))
    errors.extend(f"file outside allowlist: {item}" for item in sorted(files - allowed))
    errors.extend(
        f"directory outside allowlist: {item}/"
        for item in sorted(directories - runtime_directories())
    )
    for relative in sorted(files & RUNTIME_FILES):
        path = source / PurePosixPath(relative)
        data = path.read_bytes()
        if relative == "descriptor.mod" and data.startswith(b"\xef\xbb\xbf"):
            errors.append("descriptor.mod must not have a UTF-8 BOM")
        if relative != "descriptor.mod" and path.suffix.lower() in {".txt", ".yml"}:
            if not data.startswith(b"\xef\xbb\xbf"):
                errors.append(f"script/localization lacks UTF-8 BOM: {relative}")
        if path.suffix.lower() in {".mod", ".txt", ".yml"}:
            try:
                value = data.decode("utf-8-sig")
            except UnicodeDecodeError as error:
                errors.append(f"runtime text is not UTF-8: {relative}: {error}")
                continue
            if "remote_file_id" in value:
                errors.append(f"canonical runtime contains remote_file_id: {relative}")
            if UPSTREAM_WORKSHOP_ITEM_ID in value:
                errors.append(f"upstream Workshop identity leaked into runtime: {relative}")
    return errors


def descriptor_version(source: Path) -> str:
    value = (source / "descriptor.mod").read_text(encoding="utf-8")
    matches = re.findall(r'(?m)^version="([^"\n]+)"$', value.replace("\r\n", "\n"))
    if len(matches) != 1 or SEMVER.fullmatch(matches[0]) is None:
        raise ValueError("descriptor.mod requires exactly one semantic version")
    return matches[0]


def git_sha() -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if FULL_SHA.fullmatch(result) is None:
        raise ValueError("Git did not return a full lowercase SHA")
    return result


def manifest(staging: Path, revision: str, version: str) -> dict[str, object]:
    return {
        "format_version": 1,
        "product_id": PRODUCT_ID,
        "mod_version": version,
        "git_sha": revision,
        "workshop_item_id": None,
        "files": [
            {
                "path": relative,
                "size": (staging / PurePosixPath(relative)).stat().st_size,
                "sha256": sha256_file(staging / PurePosixPath(relative)),
            }
            for relative in sorted(RUNTIME_FILES)
        ],
    }


def build_release(
    source: Path, staging: Path, revision: str | None = None
) -> tuple[Path, Path, Path, dict[str, object]]:
    source = source.resolve()
    staging = staging.resolve()
    errors = source_errors(source)
    if errors:
        raise ValueError("invalid Auto Upgrade Buildings source:\n" + "\n".join(errors))
    if source == staging or source in staging.parents or staging in source.parents:
        raise ValueError("source and staging must not contain one another")
    revision = revision or git_sha()
    if FULL_SHA.fullmatch(revision) is None:
        raise ValueError("manifest revision must be a full lowercase SHA")
    if staging.exists():
        shutil.rmtree(staging)
    for relative in sorted(RUNTIME_FILES):
        target = staging / PurePosixPath(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / PurePosixPath(relative), target)
    payload = manifest(staging, revision, descriptor_version(source))
    manifest_path = staging.parent / f"{staging.name}.manifest.json"
    archive_path = staging.parent / f"{staging.name}.zip"
    manifest_path.write_bytes(
        (json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode()
    )
    with zipfile.ZipFile(archive_path, "w") as archive:
        for entry in payload["files"]:
            relative = entry["path"]
            info = zipfile.ZipInfo(f"{PRODUCT_ID}/{relative}", ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(
                info,
                (staging / PurePosixPath(relative)).read_bytes(),
                compresslevel=9,
            )
    return staging, manifest_path, archive_path, payload


def check_reproducible(source: Path = DEFAULT_SOURCE) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="auto-upgrade-release-check-") as name:
        root = Path(name)
        revision = git_sha()
        first = build_release(source, root / "one" / PRODUCT_ID, revision)
        second = build_release(source, root / "two" / PRODUCT_ID, revision)
        if first[1].read_bytes() != second[1].read_bytes():
            raise ValueError("manifest is not byte reproducible")
        if first[2].read_bytes() != second[2].read_bytes():
            raise ValueError("ZIP is not byte reproducible")
        return {
            "file_count": len(first[3]["files"]),
            "manifest_sha256": sha256_file(first[1]),
            "zip_sha256": sha256_file(first[2]),
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.check:
            result = check_reproducible(args.source)
            print(
                f"AUTO UPGRADE BUILDINGS RELEASE CHECK OK\nFiles: {result['file_count']}\n"
                f"Manifest SHA-256: {result['manifest_sha256']}\n"
                f"ZIP SHA-256: {result['zip_sha256']}"
            )
        else:
            _, manifest_path, archive_path, payload = build_release(args.source, args.output)
            print(
                f"Built: {args.output.resolve()}\nFiles: {len(payload['files'])}\n"
                f"Manifest: {manifest_path}\nZIP: {archive_path}"
            )
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"AUTO UPGRADE BUILDINGS RELEASE FAILED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
