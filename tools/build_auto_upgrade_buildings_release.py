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
from typing import TypedDict

from workshop_compatibility_tags import render_release_file_bytes

import gen_auto_upgrade_buildings as generator
from auto_upgrade_buildings_data import EXPECTED_GAME_VERSION


ROOT = Path(__file__).resolve().parents[1]
PRODUCT_ID = "mod_auto_upgrade_buildings"
PRODUCT_TAG_PREFIX = "auto-upgrade-buildings-v"
DEFAULT_SOURCE = ROOT / PRODUCT_ID
DEFAULT_OUTPUT = ROOT / "dist" / PRODUCT_ID
UPSTREAM_WORKSHOP_ITEM_ID = "3596580780"
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
HOUSE_RELATION_FIX_FILE = "localization/replace/aub_florin_house_relation_l_simp_chinese.yml"
HOUSE_RELATION_FIX_TEXT = (
    'l_simp_chinese:\n'
    ' house_relation_latest_change_amount:0 "#weak （[HOUSE_RELATION.GetLatestChangeAmount|=+%^]）#!"\n'
)
RUNTIME_FILES = frozenset(
    {
        "common/decisions/build_decision.txt",
        "common/on_action/aub_on_actions.txt",
        "descriptor.mod",
        "events/auto_build.txt",
        "gfx/interface/illustrations/decisions/decision_auto_upgrade_buildings.dds",
        "localization/english/auto_build_l_english.yml",
        "localization/french/auto_build_l_french.yml",
        "localization/german/auto_build_l_german.yml",
        "localization/japanese/auto_build_l_japanese.yml",
        "localization/korean/auto_build_l_korean.yml",
        "localization/polish/auto_build_l_polish.yml",
        "localization/russian/auto_build_l_russian.yml",
        "localization/simp_chinese/auto_build_l_simp_chinese.yml",
        HOUSE_RELATION_FIX_FILE,
        "localization/spanish/auto_build_l_spanish.yml",
        "thumbnail.png",
    }
) | frozenset(path.relative_to(generator.MOD).as_posix() for path in generator.generated_outputs())
SOURCE_ONLY_FILES = frozenset({"README.md"})
SEMVER = re.compile(r"\d+\.\d+\.\d+")
FULL_SHA = re.compile(r"[0-9a-f]{40}")
WORKSHOP_ITEM_ID = re.compile(r"[1-9][0-9]*", re.ASCII)


class ManifestFile(TypedDict):
    path: str
    size: int
    sha256: str


class ReleaseManifest(TypedDict):
    format_version: int
    product_id: str
    mod_version: str
    git_tag: str | None
    git_sha: str
    workshop_item_id: str | None
    files: list[ManifestFile]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def product_tag(version: str) -> str:
    if SEMVER.fullmatch(version) is None:
        raise ValueError(f"invalid semantic version: {version!r}")
    return f"{PRODUCT_TAG_PREFIX}{version}"


def normalize_workshop_item_id(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or WORKSHOP_ITEM_ID.fullmatch(value) is None:
        raise ValueError(
            "Workshop item ID must be canonical positive ASCII digits without leading zeros"
        )
    if int(value) > 2**64 - 1:
        raise ValueError("Workshop item ID exceeds the Steam unsigned 64-bit range")
    if value == UPSTREAM_WORKSHOP_ITEM_ID:
        raise ValueError("the maintained edition must not reuse the upstream Workshop item ID")
    return value


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
            if path.name.startswith("auto_build_l_"):
                price_lines = [line for line in value.splitlines()
                               if line.lstrip().startswith("enable_auto_build_text:")]
                if len(price_lines) != 1 or EXPECTED_GAME_VERSION not in price_lines[0]:
                    errors.append(f"localization differs from reviewed building contract: {relative}: price version")
            if relative == HOUSE_RELATION_FIX_FILE and value.replace("\r\n", "\n") != HOUSE_RELATION_FIX_TEXT:
                errors.append(f"localization differs from reviewed building contract: {relative}: one-space correction")
    for path, expected in generator.generated_outputs().items():
        relative = path.relative_to(DEFAULT_SOURCE)
        actual = source / relative
        if actual.is_file() and actual.read_bytes() != expected:
            errors.append(f"generated runtime differs from reviewed building contract: {relative.as_posix()}")
    return errors


def descriptor_version(source: Path) -> str:
    value = (source / "descriptor.mod").read_text(encoding="utf-8")
    matches = list(re.finditer(r'(?m)^version="([^"\n]+)"$', value.replace("\r\n", "\n")))
    if len(matches) != 1 or SEMVER.fullmatch(matches[0].group(1)) is None:
        raise ValueError("descriptor.mod requires exactly one semantic version")
    return matches[0].group(1)


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


def git_output(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(ROOT), *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        raise ValueError("git executable is unavailable") from error
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or error.stdout or "").strip()
        raise ValueError(
            f"git {' '.join(args)} failed{': ' + detail if detail else ''}"
        ) from error
    return result.stdout.strip()


def release_identity(source: Path) -> dict[str, str]:
    source = Path(source).resolve()
    if source != DEFAULT_SOURCE.resolve():
        raise ValueError("formal release requires the canonical Auto Upgrade Buildings source")
    version = descriptor_version(source)
    revision = git_sha()
    if git_output("status", "--porcelain", "--untracked-files=all", "--", PRODUCT_ID):
        raise ValueError("release build requires the product source to be committed and clean")
    tag = product_tag(version)
    if tag not in set(git_output("tag", "--points-at", "HEAD").splitlines()):
        raise ValueError(f"release build requires tag {tag} on HEAD")
    return {"mod_version": version, "git_tag": tag, "git_sha": revision}


def manifest(
    staging: Path,
    revision: str,
    version: str,
    workshop_item_id: str | None = None,
    git_tag: str | None = None,
) -> ReleaseManifest:
    workshop_item_id = normalize_workshop_item_id(workshop_item_id)
    if git_tag not in {None, product_tag(version)}:
        raise ValueError(f"manifest Git tag must be {product_tag(version)!r} or null")
    return {
        "format_version": 1,
        "product_id": PRODUCT_ID,
        "mod_version": version,
        "git_tag": git_tag,
        "git_sha": revision,
        "workshop_item_id": workshop_item_id,
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
    source: Path,
    staging: Path,
    revision: str | None = None,
    workshop_item_id: str | None = None,
    versioned_sidecars: bool = False,
    git_tag: str | None = None,
) -> tuple[Path, Path, Path, ReleaseManifest]:
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
        target.write_bytes(render_release_file_bytes(relative, (source / PurePosixPath(relative)).read_bytes()))
    version = descriptor_version(source)
    payload = manifest(staging, revision, version, workshop_item_id, git_tag)
    stem = f"{staging.name}-v{version}" if versioned_sidecars else staging.name
    manifest_path = staging.parent / f"{stem}.manifest.json"
    archive_path = staging.parent / f"{stem}.zip"
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


def check_reproducible(
    source: Path = DEFAULT_SOURCE, workshop_item_id: str | None = None
) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="auto-upgrade-release-check-") as name:
        root = Path(name)
        revision = git_sha()
        first = build_release(
            source, root / "one" / PRODUCT_ID, revision, workshop_item_id
        )
        second = build_release(
            source, root / "two" / PRODUCT_ID, revision, workshop_item_id
        )
        if first[1].read_bytes() != second[1].read_bytes():
            raise ValueError("manifest is not byte reproducible")
        if first[2].read_bytes() != second[2].read_bytes():
            raise ValueError("ZIP is not byte reproducible")
        return {
            "file_count": len(first[3]["files"]),
            "manifest_sha256": sha256_file(first[1]),
            "zip_sha256": sha256_file(first[2]),
        }


def workshop_descriptor_matches(
    path: Path, entry: ManifestFile, workshop_item_id: str | None
) -> bool:
    try:
        workshop_item_id = normalize_workshop_item_id(workshop_item_id)
    except ValueError:
        return False
    if workshop_item_id is None:
        return False
    data = Path(path).read_bytes()
    if len(data) == entry.get("size") and sha256_bytes(data) == entry.get("sha256"):
        return True
    if re.search(rb"\r(?!\n)", data):
        return False
    separators = re.findall(rb"\r\n|\n", data)
    if not separators or len(set(separators)) != 1:
        return False
    lines = data.splitlines()
    marker = f'remote_file_id="{workshop_item_id}"'.encode("ascii")
    remote_lines = [index for index, line in enumerate(lines) if b"remote_file_id" in line]
    if remote_lines != [len(lines) - 1] or lines[-1] != marker:
        return False
    for separator in (b"\n", b"\r\n"):
        body = separator.join(lines[:-1])
        for candidate in (body, body + separator):
            if len(candidate) == entry.get("size") and sha256_bytes(candidate) == entry.get(
                "sha256"
            ):
                return True
    return False


def load_manifest(path: Path) -> ReleaseManifest:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"manifest is not valid JSON: {error}") from error
    required = {
        "format_version",
        "product_id",
        "mod_version",
        "git_tag",
        "git_sha",
        "workshop_item_id",
        "files",
    }
    if not isinstance(payload, dict) or set(payload) != required:
        raise ValueError("manifest fields mismatch")
    if type(payload["format_version"]) is not int or payload["format_version"] != 1 or payload["product_id"] != PRODUCT_ID:
        raise ValueError("manifest identity mismatch")
    version = payload["mod_version"]
    if not isinstance(version, str) or SEMVER.fullmatch(version) is None:
        raise ValueError("manifest version is invalid")
    tag = payload["git_tag"]
    if tag is not None and (not isinstance(tag, str) or tag != product_tag(version)):
        raise ValueError("manifest Git tag is invalid")
    if not isinstance(payload["git_sha"], str) or FULL_SHA.fullmatch(payload["git_sha"]) is None:
        raise ValueError("manifest Git revision is invalid")
    item_id = normalize_workshop_item_id(payload["workshop_item_id"])
    entries = payload["files"]
    if not isinstance(entries, list):
        raise ValueError("manifest files must be a list")
    paths: list[str] = []
    files: list[ManifestFile] = []
    for entry in entries:
        if (
            not isinstance(entry, dict)
            or set(entry) != {"path", "size", "sha256"}
            or not isinstance(entry["path"], str)
            or not isinstance(entry["size"], int)
            or isinstance(entry["size"], bool)
            or entry["size"] < 0
            or not isinstance(entry["sha256"], str)
            or re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]) is None
        ):
            raise ValueError("manifest file entry is invalid")
        paths.append(entry["path"])
        files.append({"path": entry["path"], "size": entry["size"], "sha256": entry["sha256"]})
    if paths != sorted(RUNTIME_FILES):
        raise ValueError("manifest file inventory mismatch")
    return {"format_version": 1, "product_id": PRODUCT_ID, "mod_version": version,
            "git_tag": tag, "git_sha": payload["git_sha"], "workshop_item_id": item_id,
            "files": files}


def verify_manifest(target: Path, manifest_path: Path, workshop_cache: bool = False) -> int:
    target = Path(target).resolve()
    if not target.is_dir():
        raise ValueError(f"verification target directory missing: {target}")
    payload = load_manifest(manifest_path)
    item_id = payload["workshop_item_id"]
    if workshop_cache and item_id is None:
        raise ValueError("--workshop-cache requires a non-null manifest Workshop item ID")
    actual = {
        path.relative_to(target).as_posix(): path
        for path in target.rglob("*")
        if path.is_file()
    }
    errors: list[str] = []
    for entry in payload["files"]:
        relative = entry["path"]
        path = actual.pop(relative, None)
        if path is None:
            errors.append(f"missing: {relative}")
        elif workshop_cache and relative == "descriptor.mod":
            if not workshop_descriptor_matches(path, entry, item_id):
                errors.append("mismatch: descriptor.mod")
        elif path.stat().st_size != entry["size"] or sha256_file(path) != entry["sha256"]:
            errors.append(f"mismatch: {relative}")
    errors.extend(f"extra: {relative}" for relative in sorted(actual))
    if errors:
        raise ValueError("manifest verification failed:\n" + "\n".join(errors))
    return len(payload["files"])


def workshop_id_argument(value: str) -> str:
    try:
        result = normalize_workshop_item_id(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from error
    assert result is not None
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--release", action="store_true")
    modes.add_argument("--verify", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--workshop-cache", action="store_true")
    parser.add_argument("--workshop-item-id", type=workshop_id_argument)
    args = parser.parse_args(argv)
    try:
        if args.manifest and not args.verify:
            raise ValueError("--manifest requires --verify")
        if args.workshop_cache and not args.verify:
            raise ValueError("--workshop-cache requires --verify")
        if args.verify and not args.manifest:
            raise ValueError("--verify requires --manifest")
        if args.verify and args.workshop_item_id is not None:
            raise ValueError("--workshop-item-id is recorded while building, not verifying")
        if args.verify:
            count = verify_manifest(args.verify, args.manifest, args.workshop_cache)
            print(f"Verified directory: {args.verify.resolve()}\nFiles: {count}")
            return 0
        if args.check:
            result = check_reproducible(args.source, args.workshop_item_id)
            print(
                f"AUTO UPGRADE BUILDINGS RELEASE CHECK OK\nFiles: {result['file_count']}\n"
                f"Manifest SHA-256: {result['manifest_sha256']}\n"
                f"ZIP SHA-256: {result['zip_sha256']}"
            )
        else:
            identity = (
                release_identity(args.source)
                if args.release
                else {
                    "git_sha": git_sha(),
                    "git_tag": None,
                }
            )
            _, manifest_path, archive_path, payload = build_release(
                args.source,
                args.output,
                revision=identity["git_sha"],
                workshop_item_id=args.workshop_item_id,
                versioned_sidecars=args.release,
                git_tag=identity["git_tag"],
            )
            print(
                f"Built: {args.output.resolve()}\nFiles: {len(payload['files'])}\n"
                f"Manifest: {manifest_path}\nZIP: {archive_path}\n"
                f"Manifest SHA-256: {sha256_file(manifest_path)}\n"
                f"ZIP SHA-256: {sha256_file(archive_path)}"
            )
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"AUTO UPGRADE BUILDINGS RELEASE FAILED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
