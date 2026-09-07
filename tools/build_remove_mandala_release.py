#!/usr/bin/env python3
"""Build and verify the standalone Mandala Purge Workshop release."""

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
PRODUCT_ID = "mod_remove_mandala"
PRODUCT_TAG_PREFIX = "remove-mandala-v"
DEFAULT_SOURCE = ROOT / PRODUCT_ID
DEFAULT_OUTPUT = ROOT / "dist" / PRODUCT_ID
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
MANIFEST_FORMAT_VERSION = 1
RUNTIME_FILES = frozenset(
    {
        "common/game_rules/mrm_game_rules.txt",
        "common/on_action/mrm_on_actions.txt",
        "common/scripted_effects/mrm_effects.txt",
        "descriptor.mod",
        "events/mrm_events.txt",
        "localization/english/mrm_l_english.yml",
        "localization/french/mrm_l_french.yml",
        "localization/german/mrm_l_german.yml",
        "localization/japanese/mrm_l_japanese.yml",
        "localization/korean/mrm_l_korean.yml",
        "localization/polish/mrm_l_polish.yml",
        "localization/russian/mrm_l_russian.yml",
        "localization/simp_chinese/mrm_l_simp_chinese.yml",
        "localization/spanish/mrm_l_spanish.yml",
        "thumbnail.png",
    }
)
SOURCE_ONLY_FILES = frozenset({"README.md"})
FORBIDDEN_WORKSHOP_ITEM_IDS = frozenset(
    {"3784706360", "3787304042", "3790635143", "3792585972"}
)
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
        raise ValueError("Workshop item ID must be positive ASCII digits without leading zeros")
    if int(value) > 2**64 - 1:
        raise ValueError("Workshop item ID exceeds the Steam unsigned 64-bit range")
    if value in FORBIDDEN_WORKSHOP_ITEM_IDS:
        raise ValueError("Mandala Purge must not reuse an existing Workshop item ID")
    return value


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def release_source_errors(
    source: Path, *, allow_source_only_files: bool = True
) -> list[str]:
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
        else:
            errors.append(f"unsupported filesystem entry: {relative}")
    expected = RUNTIME_FILES | (
        SOURCE_ONLY_FILES if allow_source_only_files else frozenset()
    )
    errors.extend(
        f"required runtime file missing: {relative}"
        for relative in sorted(RUNTIME_FILES - actual_files)
    )
    errors.extend(
        f"file outside exact runtime allowlist: {relative}"
        for relative in sorted(actual_files - expected)
    )
    errors.extend(
        f"directory outside exact runtime allowlist: {relative}/"
        for relative in sorted(actual_directories - RUNTIME_DIRECTORIES)
    )
    for relative in sorted(actual_files & RUNTIME_FILES):
        path = source / PurePosixPath(relative)
        data = path.read_bytes()
        if relative == "descriptor.mod":
            if data.startswith(b"\xef\xbb\xbf"):
                errors.append("descriptor.mod must not contain a UTF-8 BOM")
        elif path.suffix.lower() in {".txt", ".yml"}:
            if not data.startswith(b"\xef\xbb\xbf"):
                errors.append(f"script/localization lacks UTF-8 BOM: {relative}")
        if path.suffix.lower() in {".mod", ".txt", ".yml"}:
            try:
                text = data.decode("utf-8-sig")
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
    path = Path(source) / "descriptor.mod"
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ValueError(f"cannot read descriptor.mod: {error}") from error
    matches = re.findall(r'(?m)^version="([^"\n]+)"$', text.replace("\r\n", "\n"))
    if len(matches) != 1 or SEMANTIC_VERSION.fullmatch(matches[0]) is None:
        raise ValueError("descriptor.mod must contain exactly one semantic version")
    return matches[0]


def git_output(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(ROOT), *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as error:
        detail = getattr(error, "stderr", "") or getattr(error, "stdout", "")
        raise ValueError(f"git {' '.join(args)} failed: {str(detail).strip()}") from error
    return result.stdout.strip()


def git_sha() -> str:
    revision = git_output("rev-parse", "HEAD")
    if FULL_GIT_SHA.fullmatch(revision) is None:
        raise ValueError("release manifest requires a full lowercase Git SHA")
    return revision


def release_identity(source: Path) -> dict[str, str]:
    if Path(source).resolve() != DEFAULT_SOURCE.resolve():
        raise ValueError("formal release requires the canonical Mandala Purge source")
    if git_output("status", "--porcelain", "--untracked-files=all"):
        raise ValueError("formal release requires a clean worktree")
    version = descriptor_version(source)
    tag = product_tag(version)
    if tag not in git_output("tag", "--points-at", "HEAD").splitlines():
        raise ValueError(f"formal release requires tag {tag} on HEAD")
    return {"mod_version": version, "git_tag": tag, "git_sha": git_sha()}


def create_manifest(
    staging: Path,
    revision: str,
    version: str,
    workshop_item_id: str | None = None,
    git_tag: str | None = None,
) -> dict[str, object]:
    if FULL_GIT_SHA.fullmatch(revision) is None:
        raise ValueError("manifest requires a full lowercase Git SHA")
    if git_tag not in {None, product_tag(version)}:
        raise ValueError("manifest Git tag does not match the mod version")
    workshop_item_id = normalize_workshop_item_id(workshop_item_id)
    files = []
    for relative in sorted(RUNTIME_FILES):
        path = Path(staging) / PurePosixPath(relative)
        files.append(
            {"path": relative, "size": path.stat().st_size, "sha256": sha256_file(path)}
        )
    return {
        "format_version": MANIFEST_FORMAT_VERSION,
        "product_id": PRODUCT_ID,
        "mod_version": version,
        "git_tag": git_tag,
        "git_sha": revision,
        "workshop_item_id": workshop_item_id,
        "files": files,
    }


def manifest_bytes(manifest: dict[str, object]) -> bytes:
    return (json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_deterministic_zip(
    staging: Path, archive: Path, manifest: dict[str, object]
) -> None:
    with zipfile.ZipFile(archive, "w") as output:
        for entry in manifest["files"]:
            relative = entry["path"]
            info = zipfile.ZipInfo(f"{PRODUCT_ID}/{relative}", ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            output.writestr(
                info,
                (Path(staging) / PurePosixPath(relative)).read_bytes(),
                compresslevel=9,
            )


def build_release(
    source: Path,
    staging: Path,
    revision: str | None = None,
    *,
    workshop_item_id: str | None = None,
    versioned_sidecars: bool = False,
    git_tag: str | None = None,
) -> tuple[Path, Path, Path, dict[str, object]]:
    source = Path(source).resolve()
    staging = Path(staging).resolve()
    errors = release_source_errors(source)
    if errors:
        raise ValueError("invalid Mandala Purge source:\n" + "\n".join(errors))
    if staging == source or source in staging.parents or staging in source.parents:
        raise ValueError("release staging and source must not contain one another")
    version = descriptor_version(source)
    revision = revision or git_sha()
    workshop_item_id = normalize_workshop_item_id(workshop_item_id)
    if staging.exists():
        shutil.rmtree(staging)
    for relative in sorted(RUNTIME_FILES):
        target = staging / PurePosixPath(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / PurePosixPath(relative), target)
    manifest = create_manifest(staging, revision, version, workshop_item_id, git_tag)
    stem = f"{staging.name}-v{version}" if versioned_sidecars else staging.name
    manifest_path = staging.parent / f"{stem}.manifest.json"
    archive_path = staging.parent / f"{stem}.zip"
    manifest_path.write_bytes(manifest_bytes(manifest))
    write_deterministic_zip(staging, archive_path, manifest)
    return staging, manifest_path, archive_path, manifest


def check_reproducible(source: Path = DEFAULT_SOURCE) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="remove-mandala-release-check-") as name:
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


def _load_manifest(path: Path) -> dict[str, object]:
    try:
        manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read manifest: {error}") from error
    required = {
        "format_version", "product_id", "mod_version", "git_tag", "git_sha",
        "workshop_item_id", "files",
    }
    if not isinstance(manifest, dict) or set(manifest) != required:
        raise ValueError("manifest fields mismatch")
    if manifest["format_version"] != MANIFEST_FORMAT_VERSION:
        raise ValueError("manifest format mismatch")
    if manifest["product_id"] != PRODUCT_ID:
        raise ValueError("manifest product mismatch")
    if [entry.get("path") for entry in manifest["files"]] != sorted(RUNTIME_FILES):
        raise ValueError("manifest file inventory mismatch")
    normalize_workshop_item_id(manifest["workshop_item_id"])
    return manifest


def workshop_descriptor_matches(
    path: Path, entry: dict[str, object], workshop_item_id: str
) -> bool:
    data = Path(path).read_bytes()
    if re.search(rb"\r(?!\n)", data):
        return False
    separators = re.findall(rb"\r\n|\n", data)
    if not separators or len(set(separators)) != 1:
        return False
    lines = data.splitlines()
    marker = f'remote_file_id="{workshop_item_id}"'.encode("ascii")
    remote_lines = [i for i, line in enumerate(lines) if b"remote_file_id" in line]
    if remote_lines != [len(lines) - 1] or lines[-1] != marker:
        return False
    for separator in (b"\n", b"\r\n"):
        body = separator.join(lines[:-1])
        for candidate in (body, body + separator):
            if len(candidate) == entry["size"] and sha256_bytes(candidate) == entry["sha256"]:
                return True
    return False


def verify_manifest(target: Path, manifest_path: Path, *, workshop_cache: bool = False) -> int:
    target = Path(target).resolve()
    manifest = _load_manifest(manifest_path)
    item_id = manifest["workshop_item_id"]
    if workshop_cache and item_id is None:
        raise ValueError("Workshop-cache verification requires a manifest item ID")
    actual = {
        _relative(path, target): path
        for path in target.rglob("*")
        if path.is_file()
    }
    errors: list[str] = []
    for entry in manifest["files"]:
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
    return len(manifest["files"])


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
    parser.add_argument("--workshop-item-id")
    args = parser.parse_args(argv)
    try:
        if args.verify:
            if not args.manifest:
                raise ValueError("--verify requires --manifest")
            count = verify_manifest(args.verify, args.manifest, workshop_cache=args.workshop_cache)
            print(f"Verified directory: {args.verify.resolve()}\nFiles: {count}")
            return 0
        if args.manifest or args.workshop_cache:
            raise ValueError("--manifest/--workshop-cache require --verify")
        item_id = normalize_workshop_item_id(args.workshop_item_id)
        if args.check:
            result = check_reproducible(args.source)
            print(
                f"Reproducibility source: {args.source.resolve()}\n"
                f"Files: {result['file_count']}\n"
                f"Manifest SHA-256: {result['manifest_sha256']}\n"
                f"ZIP SHA-256: {result['zip_sha256']}"
            )
            return 0
        if args.release:
            identity = release_identity(args.source)
            revision, git_tag = identity["git_sha"], identity["git_tag"]
        else:
            revision, git_tag = git_sha(), None
        _, manifest_path, archive_path, manifest = build_release(
            args.source,
            args.output,
            revision,
            workshop_item_id=item_id,
            versioned_sidecars=args.release,
            git_tag=git_tag,
        )
        print(
            f"Built: {args.output.resolve()}\nFiles: {len(manifest['files'])}\n"
            f"Manifest: {manifest_path}\nZIP: {archive_path}"
        )
        return 0
    except (OSError, ValueError) as error:
        print(f"MANDALA PURGE RELEASE FAILED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
