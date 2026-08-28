#!/usr/bin/env python3
"""Build, verify, and reproduce the ZhongGuo 361 Style Workshop release."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parent.parent
PRODUCT_ID = "mod_zhongguo_style"
PRODUCT_TAG_PREFIX = "zhongguo-361-v"
DEFAULT_SOURCE = ROOT / PRODUCT_ID
DEFAULT_OUTPUT = ROOT / "dist" / PRODUCT_ID
MANIFEST_FORMAT_VERSION = 1
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)

# This is a projection allowlist, not a copy-all build. Everything else stays in
# the development tree and can never be uploaded by this builder.
RELEASE_ROOT_FILES = frozenset({"descriptor.mod", "thumbnail.png"})
RELEASE_DIRECTORY_SUFFIXES = {
    "common": frozenset({".txt"}),
    "events": frozenset({".txt"}),
    "gfx": frozenset({".dds"}),
    "gui": frozenset({".gui", ".txt"}),
    "localization": frozenset({".yml"}),
}
SOURCE_ONLY_ROOT_FILES = frozenset({"README.md"})
SOURCE_ONLY_DIRECTORIES = frozenset(
    {"artifacts", "docs", "fixtures", "images", "promo", "tools", "workshop"}
)
FORBIDDEN_RUNTIME_PARTS = frozenset({"acceptance", "fixture", "fixtures", "test", "tests"})
REQUIRED_LOCALIZATION_LANGUAGES = frozenset(
    {
        "english",
        "french",
        "german",
        "japanese",
        "korean",
        "polish",
        "russian",
        "simp_chinese",
        "spanish",
    }
)
TEXT_SUFFIXES = frozenset({".gui", ".mod", ".txt", ".yml"})
BOM_SUFFIXES = frozenset({".gui", ".txt", ".yml"})
FORBIDDEN_WORKSHOP_ITEM_IDS = frozenset({"3784706360", "3787304042", "3790635143"})
FULL_GIT_SHA = re.compile(r"[0-9a-f]{40}")
SEMANTIC_VERSION = re.compile(r"\d+\.\d+\.\d+")
WORKSHOP_ITEM_ID = re.compile(r"[1-9][0-9]*", re.ASCII)
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
THUMBNAIL_DIMENSIONS = (640, 640)
THUMBNAIL_SIZE_LIMIT = 1_000_000


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def product_tag(version: str) -> str:
    if SEMANTIC_VERSION.fullmatch(version) is None:
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
    if value in FORBIDDEN_WORKSHOP_ITEM_IDS:
        raise ValueError("ZhongGuo 361 Style must not reuse an existing Workshop item ID")
    return value


def _runtime_path_allowed(relative: str) -> bool:
    path = PurePosixPath(relative)
    if len(path.parts) == 1:
        return relative in RELEASE_ROOT_FILES
    suffixes = RELEASE_DIRECTORY_SUFFIXES.get(path.parts[0])
    return suffixes is not None and path.suffix.lower() in suffixes


def _is_forbidden_runtime_path(relative: str) -> bool:
    for part in PurePosixPath(relative).parts:
        lowered = part.lower()
        stem = PurePosixPath(lowered).stem
        if lowered in FORBIDDEN_RUNTIME_PARTS:
            return True
        if "acceptance" in lowered or "fixture" in lowered:
            return True
        if stem.startswith("test_") or stem.endswith("_test") or "_test_" in stem:
            return True
    return False


def descriptor_text(source: Path) -> str:
    path = Path(source) / "descriptor.mod"
    try:
        data = path.read_bytes()
    except FileNotFoundError as error:
        raise ValueError(f"descriptor.mod missing under {source}") from error
    if data.startswith(b"\xef\xbb\xbf"):
        raise ValueError("descriptor.mod must not carry a UTF-8 BOM")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("descriptor.mod is not UTF-8") from error


def descriptor_version(source: Path) -> str:
    text = descriptor_text(source).replace("\r\n", "\n").replace("\r", "\n")
    matches = re.findall(r'(?m)^version="([^"\n]+)"$', text)
    if len(matches) != 1 or SEMANTIC_VERSION.fullmatch(matches[0]) is None:
        raise ValueError("descriptor.mod must contain exactly one semantic version")
    return matches[0]


def _descriptor_errors(source: Path) -> list[str]:
    try:
        text = descriptor_text(source).replace("\r\n", "\n").replace("\r", "\n")
    except ValueError as error:
        return [str(error)]
    errors: list[str] = []
    required_patterns = {
        "version": r'(?m)^version="[^"\n]+"$',
        "name": r'(?m)^name="[^"\n]+"$',
        "supported_version": r'(?m)^supported_version="[^"\n]+"$',
        "picture": r'(?m)^picture="thumbnail\.png"$',
    }
    for field, pattern in required_patterns.items():
        if len(re.findall(pattern, text)) != 1:
            errors.append(f"descriptor.mod must contain exactly one valid {field} field")
    try:
        descriptor_version(source)
    except ValueError as error:
        errors.append(str(error))
    if "remote_file_id" in text:
        errors.append("canonical descriptor.mod contains remote_file_id")
    return errors


def _thumbnail_errors(source: Path) -> list[str]:
    path = Path(source) / "thumbnail.png"
    if not path.is_file():
        return ["required release file missing: thumbnail.png"]
    data = path.read_bytes()
    errors: list[str] = []
    if len(data) >= THUMBNAIL_SIZE_LIMIT:
        errors.append("thumbnail.png must remain below 1,000,000 bytes")
    if len(data) < 24 or not data.startswith(PNG_SIGNATURE) or data[12:16] != b"IHDR":
        errors.append("thumbnail.png is not a recognizable PNG with an IHDR header")
    else:
        dimensions = struct.unpack(">II", data[16:24])
        if dimensions != THUMBNAIL_DIMENSIONS:
            errors.append(
                f"thumbnail.png must be 640x640, got {dimensions[0]}x{dimensions[1]}"
            )
    return errors


def release_source_errors(
    source: Path, *, allow_source_only_files: bool = True
) -> list[str]:
    """Return projection violations without modifying the source tree."""
    source = Path(source)
    if not source.is_dir():
        return [f"mod source directory missing: {source}"]

    errors: list[str] = []
    for name in sorted(RELEASE_ROOT_FILES - {"thumbnail.png"}):
        if not (source / name).is_file():
            errors.append(f"required release file missing: {name}")
    for name in sorted(RELEASE_DIRECTORY_SUFFIXES):
        if not (source / name).is_dir():
            errors.append(f"required release directory missing: {name}/")

    allowed_top_level = set(RELEASE_ROOT_FILES) | set(RELEASE_DIRECTORY_SUFFIXES)
    if allow_source_only_files:
        allowed_top_level |= set(SOURCE_ONLY_ROOT_FILES) | set(SOURCE_ONLY_DIRECTORIES)
    for path in sorted(source.iterdir(), key=lambda item: item.name):
        if path.name not in allowed_top_level:
            errors.append(f"path outside release/source allowlist: {path.name}")
        elif not allow_source_only_files and (
            path.name in SOURCE_ONLY_ROOT_FILES or path.name in SOURCE_ONLY_DIRECTORIES
        ):
            errors.append(f"source-only path leaked into staging: {path.name}")

    localization_root = source / "localization"
    if localization_root.is_dir():
        actual_languages = {path.name for path in localization_root.iterdir() if path.is_dir()}
        for language in sorted(REQUIRED_LOCALIZATION_LANGUAGES - actual_languages):
            errors.append(f"required localization directory missing: localization/{language}/")

    for path in sorted(source.rglob("*"), key=lambda item: item.as_posix()):
        relative = _relative(path, source)
        top = PurePosixPath(relative).parts[0]
        if allow_source_only_files and (
            top in SOURCE_ONLY_DIRECTORIES or relative in SOURCE_ONLY_ROOT_FILES
        ):
            continue
        if path.is_symlink():
            errors.append(f"symlink is not allowed in release runtime: {relative}")
            continue
        if path.is_dir():
            continue
        if not path.is_file():
            errors.append(f"unsupported filesystem entry in release runtime: {relative}")
            continue
        if not _runtime_path_allowed(relative):
            errors.append(f"file outside release allowlist: {relative}")
            continue
        if _is_forbidden_runtime_path(relative):
            errors.append(f"fixture/test path is forbidden in release runtime: {relative}")
            continue
        data = path.read_bytes()
        if b"remote_file_id" in data:
            errors.append(f"canonical runtime contains remote_file_id: {relative}")
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            errors.append(f"runtime text is not UTF-8: {relative}: {error}")
            continue
        if path.suffix.lower() in BOM_SUFFIXES and not data.startswith(b"\xef\xbb\xbf"):
            errors.append(f"runtime script/localization is missing UTF-8 BOM: {relative}")
        for old_id in FORBIDDEN_WORKSHOP_ITEM_IDS:
            if old_id in text:
                errors.append(f"existing Workshop item ID {old_id} is forbidden: {relative}")

    errors.extend(_descriptor_errors(source))
    errors.extend(_thumbnail_errors(source))
    return errors


def release_files(source: Path) -> list[Path]:
    """Return only runtime files, in stable POSIX-relative order."""
    source = Path(source)
    files: list[Path] = []
    for name in RELEASE_ROOT_FILES:
        path = source / name
        if path.is_file():
            files.append(path)
    for directory, suffixes in RELEASE_DIRECTORY_SUFFIXES.items():
        base = source / directory
        if base.is_dir():
            files.extend(
                path
                for path in base.rglob("*")
                if path.is_file() and path.suffix.lower() in suffixes
            )
    return sorted(files, key=lambda path: _relative(path, source))


def git_sha(repository: Path = ROOT) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repository), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def git_output(*args: str, repository: Path = ROOT) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repository), *args],
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


def _require_full_revision(revision: str | None) -> str:
    if not isinstance(revision, str) or FULL_GIT_SHA.fullmatch(revision) is None:
        raise ValueError("manifest requires a full 40-character lowercase Git SHA")
    return revision


def release_identity(source: Path) -> dict[str, str]:
    source = Path(source).resolve()
    if source != DEFAULT_SOURCE.resolve():
        raise ValueError("formal release requires the canonical ZhongGuo 361 Style source")
    version = descriptor_version(source)
    revision = _require_full_revision(git_sha())
    if git_output("status", "--porcelain", "--untracked-files=all"):
        raise ValueError("release build requires a clean worktree")
    tag = product_tag(version)
    if tag not in set(git_output("tag", "--points-at", "HEAD").splitlines()):
        raise ValueError(f"release build requires tag {tag} on HEAD")
    return {"mod_version": version, "git_tag": tag, "git_sha": revision}


def create_manifest(
    staging: Path,
    revision: str,
    version: str,
    workshop_item_id: str | None = None,
    git_tag: str | None = None,
) -> dict[str, object]:
    revision = _require_full_revision(revision)
    expected_tag = product_tag(version)
    if git_tag not in {None, expected_tag}:
        raise ValueError(f"manifest Git tag must be {expected_tag!r} or null")
    workshop_item_id = normalize_workshop_item_id(workshop_item_id)
    files = []
    for path in release_files(staging):
        relative = _relative(path, staging)
        files.append(
            {
                "path": relative,
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
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
    return (
        json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


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
    version: str | None = None,
    workshop_item_id: str | None = None,
    versioned_sidecars: bool = False,
    git_tag: str | None = None,
) -> tuple[Path, Path, Path, dict[str, object]]:
    """Copy the production projection and emit its manifest and deterministic ZIP."""
    source, staging = Path(source).resolve(), Path(staging).resolve()
    errors = release_source_errors(source)
    if errors:
        raise ValueError("invalid ZhongGuo 361 Style source:\n" + "\n".join(errors))
    if staging == source or source in staging.parents or staging in source.parents:
        raise ValueError("release staging and mod source must not contain one another")

    source_version = descriptor_version(source)
    version = version or source_version
    if version != source_version:
        raise ValueError(
            f"requested version {version!r} does not match descriptor {source_version!r}"
        )
    revision = _require_full_revision(revision or git_sha())
    workshop_item_id = normalize_workshop_item_id(workshop_item_id)

    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    for source_path in release_files(source):
        relative = _relative(source_path, source)
        target = staging / PurePosixPath(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source_path.read_bytes())

    errors = release_source_errors(staging, allow_source_only_files=False)
    if errors:
        raise ValueError("invalid ZhongGuo 361 Style staging:\n" + "\n".join(errors))
    manifest = create_manifest(staging, revision, version, workshop_item_id, git_tag)
    stem = f"{staging.name}-v{version}" if versioned_sidecars else staging.name
    manifest_path = staging.parent / f"{stem}.manifest.json"
    archive_path = staging.parent / f"{stem}.zip"
    manifest_path.write_bytes(manifest_bytes(manifest))
    write_deterministic_zip(staging, archive_path, manifest)
    return staging, manifest_path, archive_path, manifest


def zip_contents(archive: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(archive) as source:
        return {entry.filename: source.read(entry.filename) for entry in source.infolist()}


def check_reproducible(
    source: Path = DEFAULT_SOURCE,
    workshop_item_id: str | None = None,
    revision: str | None = None,
) -> dict[str, object]:
    source = Path(source).resolve()
    errors = release_source_errors(source)
    if errors:
        raise ValueError("invalid ZhongGuo 361 Style source:\n" + "\n".join(errors))
    revision = _require_full_revision(revision or git_sha())
    workshop_item_id = normalize_workshop_item_id(workshop_item_id)
    with tempfile.TemporaryDirectory(prefix="zhongguo-361-release-check-") as name:
        root = Path(name)
        first = build_release(
            source,
            root / "one" / PRODUCT_ID,
            revision,
            workshop_item_id=workshop_item_id,
        )
        second = build_release(
            source,
            root / "two" / PRODUCT_ID,
            revision,
            workshop_item_id=workshop_item_id,
        )
        if (
            first[3] != second[3]
            or first[1].read_bytes() != second[1].read_bytes()
            or first[2].read_bytes() != second[2].read_bytes()
            or zip_contents(first[2]) != zip_contents(second[2])
        ):
            raise ValueError("identical release builds are not byte reproducible")
        return {
            "file_count": len(first[3]["files"]),
            "manifest_sha256": sha256_file(first[1]),
            "zip_sha256": sha256_file(first[2]),
        }


def workshop_descriptor_matches(
    path: Path, entry: dict[str, object], workshop_item_id: str
) -> bool:
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
    lines = data.splitlines()
    marker = f'remote_file_id="{workshop_item_id}"'.encode("ascii")
    remote_lines = [index for index, line in enumerate(lines) if b"remote_file_id" in line]
    if remote_lines != [len(lines) - 1] or lines[-1] != marker:
        return False
    # The launcher may normalize the canonical descriptor's newline style before
    # appending the ID. Reconstruct both canonical styles, with and without the
    # original terminal newline, but permit no other content change.
    for separator in (b"\n", b"\r\n"):
        body = separator.join(lines[:-1])
        for candidate in (body, body + separator):
            if len(candidate) == entry.get("size") and sha256_bytes(candidate) == entry.get(
                "sha256"
            ):
                return True
    return False


def _load_manifest(manifest_path: Path, target: Path) -> dict[str, object]:
    try:
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"manifest is not valid JSON: {error}") from error
    required = {
        "files",
        "format_version",
        "git_sha",
        "git_tag",
        "mod_version",
        "product_id",
        "workshop_item_id",
    }
    if not isinstance(manifest, dict) or set(manifest) != required:
        raise ValueError("manifest fields mismatch")
    version = descriptor_version(target)
    if (
        manifest["format_version"] != MANIFEST_FORMAT_VERSION
        or manifest["product_id"] != PRODUCT_ID
        or manifest["mod_version"] != version
    ):
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
        if (
            not isinstance(entry, dict)
            or set(entry) != {"path", "sha256", "size"}
            or not isinstance(entry["path"], str)
            or not isinstance(entry["size"], int)
            or isinstance(entry["size"], bool)
            or entry["size"] < 0
            or not isinstance(entry["sha256"], str)
            or re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]) is None
        ):
            raise ValueError("manifest file entry is invalid")
        relative = entry["path"]
        posix = PurePosixPath(relative)
        if (
            relative != posix.as_posix()
            or posix.is_absolute()
            or ".." in posix.parts
            or not _runtime_path_allowed(relative)
            or _is_forbidden_runtime_path(relative)
        ):
            raise ValueError(f"manifest contains forbidden runtime path: {relative!r}")
        paths.append(relative)
    if paths != sorted(set(paths)):
        raise ValueError("manifest file inventory must be unique and sorted")
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
    modes.add_argument("--check", action="store_true", help="prove two builds byte reproducible")
    modes.add_argument("--release", action="store_true", help="require a clean matching release tag")
    modes.add_argument("--verify", type=Path, help="directory to verify")
    parser.add_argument("--manifest", type=Path, help="manifest used by --verify")
    parser.add_argument(
        "--workshop-cache",
        action="store_true",
        help="permit only the launcher's final descriptor ID injection",
    )
    parser.add_argument(
        "--workshop-item-id",
        type=_workshop_id_argument,
        help="new item ID to record in a sidecar; never inferred",
    )
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
                f"Reproducibility source: {args.source.resolve()}\n"
                f"Files: {result['file_count']}\n"
                f"Manifest SHA-256: {result['manifest_sha256']}\n"
                f"ZIP SHA-256: {result['zip_sha256']}"
            )
            return 0
        identity = (
            release_identity(args.source)
            if args.release
            else {
                "git_sha": _require_full_revision(git_sha()),
                "mod_version": descriptor_version(args.source),
                "git_tag": None,
            }
        )
        staging, manifest, archive, details = build_release(
            args.source,
            args.output,
            revision=identity["git_sha"],
            version=identity["mod_version"],
            workshop_item_id=args.workshop_item_id,
            versioned_sidecars=args.release,
            git_tag=identity["git_tag"],
        )
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print(f"ZHONGGUO 361 RELEASE FAILED: {error}", file=sys.stderr)
        return 1
    print(
        f"Release staging: {staging}\n"
        f"Manifest: {manifest}\n"
        f"Archive: {archive}\n"
        f"Files: {len(details['files'])}\n"
        f"Manifest SHA-256: {sha256_file(manifest)}\n"
        f"ZIP SHA-256: {sha256_file(archive)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
