#!/usr/bin/env python3
"""Build, verify, and reproduce the standalone Ox Here! Workshop release."""

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


ROOT = Path(__file__).resolve().parent.parent
PRODUCT_ID = "ox_here"
PRODUCT_TAG_PREFIX = "ox-here-v"
DEFAULT_SOURCE = ROOT / PRODUCT_ID
DEFAULT_OUTPUT = ROOT / "dist" / PRODUCT_ID
MANIFEST_FORMAT_VERSION = 1
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)

# Deliberately exact: sources, acceptance fixtures, and workshop prose never ship.
RUNTIME_FILES = frozenset(
    {
        "common/decision_group_types/ox_here_decision_group_types.txt",
        "common/decisions/ox_here_decisions.txt",
        "common/culture/cultures/ox_here_cultures.txt",
        "common/ethnicities/ox_here_ethnicities.txt",
        "common/scripted_character_templates/ox_here_character_templates.txt",
        "common/scripted_effects/ox_here_effects.txt",
        "common/scripted_guis/ox_here_guis.txt",
        "common/script_values/ox_here_values.txt",
        "descriptor.mod",
        "events/ox_here_events.txt",
        "gui/ox_here_bridge.gui",
        "gui/scripted_widgets/ox_here_scripted_widgets.txt",
        "thumbnail.png",
        "localization/english/ox_here_l_english.yml",
        "localization/french/ox_here_l_french.yml",
        "localization/german/ox_here_l_german.yml",
        "localization/japanese/ox_here_l_japanese.yml",
        "localization/korean/ox_here_l_korean.yml",
        "localization/polish/ox_here_l_polish.yml",
        "localization/russian/ox_here_l_russian.yml",
        "localization/simp_chinese/ox_here_l_simp_chinese.yml",
        "localization/spanish/ox_here_l_spanish.yml",
    }
)
# Kept in the development tree but intentionally absent from formal staging.
SOURCE_ONLY_FILES = frozenset({"README.md"})
TEXT_SUFFIXES = {".mod", ".txt", ".yml"}
FORBIDDEN_CACHE_SUFFIXES = {".pyc", ".pyo"}
FORBIDDEN_WORKSHOP_ITEM_IDS = frozenset({"3784706360", "3787304042"})
FULL_GIT_SHA = re.compile(r"[0-9a-f]{40}")
SEMANTIC_VERSION = re.compile(r"\d+\.\d+\.\d+")
WORKSHOP_ITEM_ID = re.compile(r"[1-9][0-9]*", re.ASCII)


def _allowed_directories() -> frozenset[str]:
    result: set[str] = set()
    for relative in RUNTIME_FILES:
        parent = PurePosixPath(relative).parent
        while parent != PurePosixPath("."):
            result.add(parent.as_posix())
            parent = parent.parent
    return frozenset(result)


RUNTIME_DIRECTORIES = _allowed_directories()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def product_tag(version: str) -> str:
    if SEMANTIC_VERSION.fullmatch(version) is None:
        raise ValueError(f"invalid semantic version: {version!r}")
    return f"{PRODUCT_TAG_PREFIX}{version}"


def normalize_workshop_item_id(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or WORKSHOP_ITEM_ID.fullmatch(value) is None:
        raise ValueError("Workshop item ID must be canonical positive ASCII digits without leading zeros")
    if int(value) > 2**64 - 1:
        raise ValueError("Workshop item ID exceeds the Steam unsigned 64-bit range")
    if value in FORBIDDEN_WORKSHOP_ITEM_IDS:
        raise ValueError("Ox Here! must not reuse an existing Workshop item ID")
    return value


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def release_source_errors(source: Path, *, allow_source_only_files: bool = True) -> list[str]:
    """Return all release-tree exact-allowlist violations."""
    source = Path(source)
    if not source.is_dir():
        return [f"mod source directory missing: {source}"]
    errors: list[str] = []
    actual_files: set[str] = set()
    actual_directories: set[str] = set()
    for path in sorted(source.rglob("*"), key=lambda item: item.as_posix()):
        relative = _relative(path, source)
        if path.is_symlink():
            errors.append(f"symlink is not allowed in release source: {relative}")
        elif path.is_dir():
            actual_directories.add(relative)
        elif path.is_file():
            actual_files.add(relative)
            if "__pycache__" in path.parts or path.suffix.lower() in FORBIDDEN_CACHE_SUFFIXES:
                errors.append(f"Python cache is forbidden in mod source: {relative}")
            if any(part.lower() in {"tools", "images", "source", "sources", "source_materials", "workshop", "artifacts"} for part in PurePosixPath(relative).parts):
                errors.append(f"tooling or source material is forbidden in runtime: {relative}")
        else:
            errors.append(f"unsupported filesystem entry in release source: {relative}")
    expected_files = RUNTIME_FILES | (SOURCE_ONLY_FILES if allow_source_only_files else frozenset())
    for relative in sorted(RUNTIME_FILES - actual_files):
        errors.append(f"required runtime file missing: {relative}")
    for relative in sorted(actual_files - expected_files):
        errors.append(f"file outside exact runtime allowlist: {relative}")
    for relative in sorted(actual_directories - RUNTIME_DIRECTORIES):
        errors.append(f"directory outside exact runtime allowlist: {relative}/")
    for relative in sorted(actual_files & RUNTIME_FILES):
        path = source / PurePosixPath(relative)
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_bytes().decode("utf-8-sig")
        except UnicodeDecodeError as error:
            errors.append(f"runtime text is not UTF-8: {relative}: {error}")
            continue
        if "remote_file_id" in text:
            errors.append(f"canonical runtime contains remote_file_id: {relative}")
        for old_id in FORBIDDEN_WORKSHOP_ITEM_IDS:
            if old_id in text:
                errors.append(f"existing Workshop item ID {old_id} is forbidden: {relative}")
    return errors


def descriptor_version(source: Path) -> str:
    try:
        text = (Path(source) / "descriptor.mod").read_bytes().decode("utf-8-sig")
    except FileNotFoundError as error:
        raise ValueError(f"descriptor.mod missing under {source}") from error
    except UnicodeDecodeError as error:
        raise ValueError("descriptor.mod is not UTF-8") from error
    matches = re.findall(r'(?m)^version="([^"\n]+)"$', text.replace("\r\n", "\n").replace("\r", "\n"))
    if len(matches) != 1 or SEMANTIC_VERSION.fullmatch(matches[0]) is None:
        raise ValueError("descriptor.mod must contain exactly one semantic version")
    return matches[0]


def git_sha(repository: Path = ROOT) -> str | None:
    try:
        result = subprocess.run(["git", "-C", str(repository), "rev-parse", "HEAD"], check=True, capture_output=True, text=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def git_output(*args: str, repository: Path = ROOT) -> str:
    try:
        result = subprocess.run(["git", "-C", str(repository), *args], check=True, capture_output=True, text=True)
    except FileNotFoundError as error:
        raise ValueError("git executable is unavailable") from error
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or error.stdout or "").strip()
        raise ValueError(f"git {' '.join(args)} failed{': ' + detail if detail else ''}") from error
    return result.stdout.strip()


def _require_full_revision(revision: str | None) -> str:
    if not isinstance(revision, str) or FULL_GIT_SHA.fullmatch(revision) is None:
        raise ValueError("manifest requires a full 40-character lowercase Git SHA")
    return revision


def release_identity(source: Path) -> dict[str, str]:
    source = Path(source).resolve()
    if source != DEFAULT_SOURCE.resolve():
        raise ValueError("formal release requires the canonical Ox Here! source")
    version = descriptor_version(source)
    revision = _require_full_revision(git_sha())
    if git_output("status", "--porcelain", "--untracked-files=all"):
        raise ValueError("release build requires a clean worktree")
    tag = product_tag(version)
    if tag not in set(git_output("tag", "--points-at", "HEAD").splitlines()):
        raise ValueError(f"release build requires tag {tag} on HEAD")
    return {"mod_version": version, "git_tag": tag, "git_sha": revision}


def create_manifest(staging: Path, revision: str, version: str, workshop_item_id: str | None = None, git_tag: str | None = None) -> dict[str, object]:
    revision = _require_full_revision(revision)
    if git_tag not in {None, product_tag(version)}:
        raise ValueError(f"manifest Git tag must be {product_tag(version)!r} or null")
    workshop_item_id = normalize_workshop_item_id(workshop_item_id)
    files = [{"path": relative, "size": len((Path(staging) / PurePosixPath(relative)).read_bytes()), "sha256": sha256_file(Path(staging) / PurePosixPath(relative))} for relative in sorted(RUNTIME_FILES)]
    return {"format_version": MANIFEST_FORMAT_VERSION, "product_id": PRODUCT_ID, "mod_version": version, "git_tag": git_tag, "git_sha": revision, "workshop_item_id": workshop_item_id, "files": files}


def manifest_bytes(manifest: dict[str, object]) -> bytes:
    return (json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_deterministic_zip(staging: Path, archive: Path, manifest: dict[str, object]) -> None:
    with zipfile.ZipFile(archive, "w") as output:
        for entry in manifest["files"]:
            relative = entry["path"]
            info = zipfile.ZipInfo(f"{PRODUCT_ID}/{relative}", ZIP_TIMESTAMP)
            info.compress_type, info.create_system, info.external_attr = zipfile.ZIP_DEFLATED, 3, 0o100644 << 16
            output.writestr(info, (Path(staging) / PurePosixPath(relative)).read_bytes(), compresslevel=9)


def build_release(source: Path, staging: Path, revision: str | None = None, version: str | None = None, workshop_item_id: str | None = None, versioned_sidecars: bool = False, git_tag: str | None = None) -> tuple[Path, Path, Path, dict[str, object]]:
    source, staging = Path(source).resolve(), Path(staging).resolve()
    errors = release_source_errors(source)
    if errors:
        raise ValueError("invalid Ox Here! source:\n" + "\n".join(errors))
    if staging == source or source in staging.parents or staging in source.parents:
        raise ValueError("release staging and mod source must not contain one another")
    source_version = descriptor_version(source)
    version = version or source_version
    if version != source_version:
        raise ValueError(f"requested version {version!r} does not match descriptor {source_version!r}")
    revision, workshop_item_id = _require_full_revision(revision or git_sha()), normalize_workshop_item_id(workshop_item_id)
    if staging.exists():
        shutil.rmtree(staging)
    for relative in sorted(RUNTIME_FILES):
        target = staging / PurePosixPath(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((source / PurePosixPath(relative)).read_bytes())
    errors = release_source_errors(staging, allow_source_only_files=False)
    if errors:
        raise ValueError("invalid Ox Here! staging:\n" + "\n".join(errors))
    manifest = create_manifest(staging, revision, version, workshop_item_id, git_tag)
    stem = f"{staging.name}-v{version}" if versioned_sidecars else staging.name
    manifest_path, archive_path = staging.parent / f"{stem}.manifest.json", staging.parent / f"{stem}.zip"
    manifest_path.write_bytes(manifest_bytes(manifest))
    write_deterministic_zip(staging, archive_path, manifest)
    return staging, manifest_path, archive_path, manifest


def zip_contents(archive: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(archive) as source:
        return {entry.filename: source.read(entry.filename) for entry in source.infolist()}


def check_reproducible(source: Path = DEFAULT_SOURCE, workshop_item_id: str | None = None, revision: str | None = None) -> dict[str, object]:
    source = Path(source).resolve()
    errors = release_source_errors(source)
    if errors:
        raise ValueError("invalid Ox Here! source:\n" + "\n".join(errors))
    revision, workshop_item_id = _require_full_revision(revision or git_sha()), normalize_workshop_item_id(workshop_item_id)
    with tempfile.TemporaryDirectory(prefix="ox-here-release-check-") as name:
        root = Path(name)
        first = build_release(source, root / "one" / PRODUCT_ID, revision, workshop_item_id=workshop_item_id)
        second = build_release(source, root / "two" / PRODUCT_ID, revision, workshop_item_id=workshop_item_id)
        if first[3] != second[3] or first[1].read_bytes() != second[1].read_bytes() or first[2].read_bytes() != second[2].read_bytes() or zip_contents(first[2]) != zip_contents(second[2]):
            raise ValueError("identical release builds are not byte reproducible")
        return {"file_count": len(first[3]["files"]), "manifest_sha256": sha256_file(first[1]), "zip_sha256": sha256_file(first[2])}


def workshop_descriptor_matches(path: Path, entry: dict[str, object], workshop_item_id: str) -> bool:
    try:
        workshop_item_id = normalize_workshop_item_id(workshop_item_id)
    except ValueError:
        return False
    if workshop_item_id is None:
        return False
    data = Path(path).read_bytes()
    if re.search(rb"\r(?!\n)", data):
        return False
    separators = re.findall(rb"\r\n|\n", data)
    if not separators or len(set(separators)) != 1:
        return False
    lines, marker = data.splitlines(), f'remote_file_id="{workshop_item_id}"'.encode("ascii")
    remote_lines = [index for index, line in enumerate(lines) if b"remote_file_id" in line]
    if remote_lines != [len(lines) - 1] or lines[-1] != marker:
        return False
    for separator in (b"\n", b"\r\n"):
        body = separator.join(lines[:-1])
        for candidate in (body, body + separator):
            if len(candidate) == entry.get("size") and sha256_bytes(candidate) == entry.get("sha256"):
                return True
    return False


def _load_manifest(manifest_path: Path, target: Path) -> dict[str, object]:
    try:
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"manifest is not valid JSON: {error}") from error
    required = {"format_version", "product_id", "mod_version", "git_tag", "git_sha", "workshop_item_id", "files"}
    if not isinstance(manifest, dict) or set(manifest) != required:
        raise ValueError("manifest fields mismatch")
    version = descriptor_version(target)
    if manifest["format_version"] != MANIFEST_FORMAT_VERSION or manifest["product_id"] != PRODUCT_ID or manifest["mod_version"] != version:
        raise ValueError("manifest identity mismatch")
    if manifest["git_tag"] not in {None, product_tag(version)}:
        raise ValueError("manifest identity mismatch for git_tag")
    _require_full_revision(manifest["git_sha"])
    normalize_workshop_item_id(manifest["workshop_item_id"])
    entries = manifest["files"]
    if not isinstance(entries, list):
        raise ValueError("manifest files must be a list")
    paths: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"path", "size", "sha256"} or not isinstance(entry["path"], str) or not isinstance(entry["size"], int) or isinstance(entry["size"], bool) or entry["size"] < 0 or not isinstance(entry["sha256"], str) or re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]) is None:
            raise ValueError("manifest file entry is invalid")
        paths.append(entry["path"])
    if paths != sorted(RUNTIME_FILES):
        raise ValueError("manifest file inventory mismatch")
    return manifest


def verify_manifest(target: Path, manifest_path: Path, workshop_cache: bool = False) -> int:
    target = Path(target).resolve()
    if not target.is_dir():
        raise ValueError(f"verification target directory missing: {target}")
    manifest = _load_manifest(manifest_path, target)
    item_id = manifest["workshop_item_id"]
    if workshop_cache and item_id is None:
        raise ValueError("--workshop-cache requires a non-null numeric manifest workshop_item_id")
    actual: dict[str, Path] = {}
    errors: list[str] = []
    for path in sorted(target.rglob("*"), key=lambda item: item.as_posix()):
        relative = _relative(path, target)
        if path.is_symlink():
            errors.append(f"symlink: {relative}")
        elif path.is_file():
            actual[relative] = path
    for entry in manifest["files"]:
        relative, path = entry["path"], actual.pop(entry["path"], None)
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
    return len(manifest["files"])


def _workshop_id_argument(value: str) -> str:
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
    modes.add_argument("--check", action="store_true", help="prove two isolated builds byte reproducible")
    modes.add_argument("--release", action="store_true", help="require clean ox-here-v<version> tag")
    modes.add_argument("--verify", type=Path, help="directory to verify")
    parser.add_argument("--manifest", type=Path, help="manifest used by --verify")
    parser.add_argument("--workshop-cache", action="store_true", help="permit only Launcher descriptor ID injection")
    parser.add_argument("--workshop-item-id", type=_workshop_id_argument, help="new item ID; never inferred")
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
            print(f"Verified directory: {args.verify.resolve()}\nFiles: {verify_manifest(args.verify, args.manifest, args.workshop_cache)}")
            return 0
        if args.check:
            result = check_reproducible(args.source, args.workshop_item_id)
            print(f"Reproducibility source: {args.source.resolve()}\nFiles: {result['file_count']}\nManifest SHA-256: {result['manifest_sha256']}\nZIP SHA-256: {result['zip_sha256']}")
            return 0
        identity = release_identity(args.source) if args.release else {"git_sha": _require_full_revision(git_sha()), "mod_version": descriptor_version(args.source), "git_tag": None}
        staging, manifest, archive, details = build_release(args.source, args.output, revision=identity["git_sha"], version=identity["mod_version"], workshop_item_id=args.workshop_item_id, versioned_sidecars=args.release, git_tag=identity["git_tag"])
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print(f"OX HERE RELEASE FAILED: {error}", file=sys.stderr)
        return 1
    print(f"Release staging: {staging}\nManifest: {manifest}\nArchive: {archive}\nFiles: {len(details['files'])}\nManifest SHA-256: {sha256_file(manifest)}\nZIP SHA-256: {sha256_file(archive)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
