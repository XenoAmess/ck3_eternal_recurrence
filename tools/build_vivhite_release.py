#!/usr/bin/env python3
"""Build and verify reproducible releases of the standalone Vivhite mod."""

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
PRODUCT_ID = "Eternal_Recurrence_Vivhite_Courtier"
PRODUCT_TAG_PREFIX = "vivhite-v"
DEFAULT_SOURCE = ROOT / PRODUCT_ID
DEFAULT_OUTPUT = ROOT / "dist" / PRODUCT_ID
MANIFEST_FORMAT_VERSION = 3
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)

# This is intentionally an exact file allowlist rather than a suffix allowlist.
# The standalone product has no development projection and no events directory.
RUNTIME_FILES = frozenset(
    {
        "common/decision_group_types/ervc_decision_group_types.txt",
        "common/decisions/ervc_courtier_creator_decisions.txt",
        "common/script_values/ervc_courtier_creator_values.txt",
        "common/script_values/ervc_generated_courtier_catalog_values.txt",
        "common/scripted_effects/ervc_courtier_creator_effects.txt",
        "common/scripted_effects/ervc_generated_courtier_catalog_effects.txt",
        "common/scripted_guis/ervc_courtier_creator_guis.txt",
        "common/scripted_guis/ervc_decision_bridge_guis.txt",
        "common/scripted_triggers/ervc_courtier_creator_triggers.txt",
        "common/scripted_triggers/ervc_generated_courtier_catalog_triggers.txt",
        "descriptor.mod",
        "gfx/interface/icons/traits/ervc_glassfire_icon.dds",
        "gfx/interface/illustrations/decisions/decision_ervc_courtier.dds",
        "gui/ervc_courtier_creator.gui",
        "gui/ervc_decision_bridge.gui",
        "gui/ervc_texticons.gui",
        "gui/scripted_widgets/ervc_scripted_widgets.txt",
        "localization/english/ervc_l_english.yml",
        "localization/french/ervc_l_french.yml",
        "localization/german/ervc_l_german.yml",
        "localization/japanese/ervc_l_japanese.yml",
        "localization/korean/ervc_l_korean.yml",
        "localization/polish/ervc_l_polish.yml",
        "localization/russian/ervc_l_russian.yml",
        "localization/simp_chinese/ervc_l_simp_chinese.yml",
        "localization/spanish/ervc_l_spanish.yml",
        "thumbnail.png",
    }
)
TEXT_SUFFIXES = {".mod", ".txt", ".gui", ".yml"}
FORBIDDEN_CACHE_SUFFIXES = {".pyc", ".pyo"}
ORIGINAL_WORKSHOP_ITEM_ID = "3784706360"
FULL_GIT_SHA = re.compile(r"[0-9a-f]{40}")
SEMANTIC_VERSION = re.compile(r"\d+\.\d+\.\d+")
WORKSHOP_ITEM_ID = re.compile(r"[1-9][0-9]*", re.ASCII)
FORBIDDEN_RUNTIME_PATTERNS = (
    (
        "original custom identifier 'xar'",
        re.compile(r"(?<![A-Za-z0-9_])xar(?=[_.:]|[^A-Za-z0-9_]|$)"),
    ),
    (
        "original custom identifier prefix 'xa_'",
        re.compile(r"(?<![A-Za-z0-9_])xa_[A-Za-z0-9_]*"),
    ),
    ("original log prefix 'XAR:'", re.compile(r"XAR:")),
    (
        "original Workshop item ID",
        re.compile(re.escape(ORIGINAL_WORKSHOP_ITEM_ID)),
    ),
    (
        "acceptance fixture identifier 'erva'",
        re.compile(r"(?<![A-Za-z0-9_])erva(?=[_.:]|[^A-Za-z0-9_]|$)"),
    ),
    ("acceptance fixture log prefix 'ERVA:'", re.compile(r"ERVA:")),
    (
        "acceptance fixture marker prefix 'ERVA_'",
        re.compile(r"(?<![A-Za-z0-9_])ERVA_[A-Za-z0-9_]*"),
    ),
)


def _allowed_directories() -> frozenset[str]:
    directories: set[str] = set()
    for relative in RUNTIME_FILES:
        parent = PurePosixPath(relative).parent
        while parent != PurePosixPath("."):
            directories.add(parent.as_posix())
            parent = parent.parent
    return frozenset(directories)


RUNTIME_DIRECTORIES = _allowed_directories()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
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
        raise ValueError(
            "Workshop item ID must be canonical positive ASCII digits without leading zeros"
        )
    if int(value) > 2**64 - 1:
        raise ValueError("Workshop item ID exceeds the Steam unsigned 64-bit range")
    if value == ORIGINAL_WORKSHOP_ITEM_ID:
        raise ValueError("standalone Workshop item ID must not reuse the original item")
    return value


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def release_source_errors(source: Path) -> list[str]:
    """Return exact-allowlist and product-isolation violations."""
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
            continue
        if path.is_dir():
            actual_directories.add(relative)
            continue
        if not path.is_file():
            errors.append(f"unsupported filesystem entry in release source: {relative}")
            continue
        actual_files.add(relative)
        if "__pycache__" in path.parts or path.suffix.lower() in FORBIDDEN_CACHE_SUFFIXES:
            errors.append(f"Python cache is forbidden in mod source: {relative}")
        if any(
            part.lower() in {"tools", "images", "source", "sources", "source_materials"}
            for part in PurePosixPath(relative).parts
        ):
            errors.append(f"tooling or source material is forbidden in runtime: {relative}")

    for relative in sorted(RUNTIME_FILES - actual_files):
        errors.append(f"required runtime file missing: {relative}")
    for relative in sorted(actual_files - RUNTIME_FILES):
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
        for label, pattern in FORBIDDEN_RUNTIME_PATTERNS:
            if pattern.search(text):
                errors.append(f"{label} is forbidden in standalone runtime: {relative}")
    return errors


def release_files(source: Path) -> list[Path]:
    """Return all exact allowlist files in deterministic path order."""
    source = Path(source)
    return [source / PurePosixPath(relative) for relative in sorted(RUNTIME_FILES)]


def descriptor_version(source: Path) -> str:
    path = Path(source) / "descriptor.mod"
    try:
        text = path.read_bytes().decode("utf-8-sig")
    except FileNotFoundError as error:
        raise ValueError(f"descriptor.mod missing under {source}") from error
    except UnicodeDecodeError as error:
        raise ValueError("descriptor.mod is not UTF-8") from error
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    matches = re.findall(r'(?m)^version="([^"\n]+)"$', text)
    if len(matches) != 1 or SEMANTIC_VERSION.fullmatch(matches[0]) is None:
        raise ValueError("descriptor.mod must contain exactly one semantic version")
    return matches[0]


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
    revision = result.stdout.strip()
    return revision or None


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
        suffix = f": {detail}" if detail else ""
        raise ValueError(f"git {' '.join(args)} failed{suffix}") from error
    return result.stdout.strip()


def _require_full_revision(revision: str | None) -> str:
    if not isinstance(revision, str) or FULL_GIT_SHA.fullmatch(revision) is None:
        raise ValueError("manifest requires a full 40-character lowercase Git SHA")
    return revision


def release_identity(source: Path) -> dict[str, str]:
    """Require the standalone release tag and a completely clean repository."""
    source = Path(source).resolve()
    if source != DEFAULT_SOURCE.resolve():
        raise ValueError("formal release requires the canonical standalone source")
    version = descriptor_version(source)
    revision = _require_full_revision(git_sha())
    if git_output("status", "--porcelain", "--untracked-files=all"):
        raise ValueError("release build requires a clean worktree")
    tag = product_tag(version)
    tags = set(git_output("tag", "--points-at", "HEAD").splitlines())
    if tag not in tags:
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
    if git_tag is not None and git_tag != expected_tag:
        raise ValueError(f"manifest Git tag must be {expected_tag!r} or null")
    workshop_item_id = normalize_workshop_item_id(workshop_item_id)
    files: list[dict[str, object]] = []
    for relative in sorted(RUNTIME_FILES):
        data = (Path(staging) / PurePosixPath(relative)).read_bytes()
        files.append(
            {"path": relative, "size": len(data), "sha256": sha256_bytes(data)}
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
            path = Path(staging) / PurePosixPath(relative)
            info = zipfile.ZipInfo(f"{PRODUCT_ID}/{relative}", ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            output.writestr(info, path.read_bytes(), compresslevel=9)


def build_release(
    source: Path,
    staging: Path,
    revision: str | None = None,
    version: str | None = None,
    workshop_item_id: str | None = None,
    versioned_sidecars: bool = False,
    git_tag: str | None = None,
) -> tuple[Path, Path, Path, dict[str, object]]:
    """Copy the exact runtime and emit its deterministic manifest and ZIP."""
    source = Path(source).resolve()
    staging = Path(staging).resolve()
    errors = release_source_errors(source)
    if errors:
        raise ValueError("invalid standalone source:\n" + "\n".join(errors))
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
    for relative in sorted(RUNTIME_FILES):
        source_path = source / PurePosixPath(relative)
        target_path = staging / PurePosixPath(relative)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(source_path.read_bytes())

    staging_errors = release_source_errors(staging)
    if staging_errors:
        raise ValueError("invalid standalone staging:\n" + "\n".join(staging_errors))

    manifest = create_manifest(
        staging, revision, version, workshop_item_id, git_tag=git_tag
    )
    sidecar_stem = (
        f"{staging.name}-v{version}" if versioned_sidecars else staging.name
    )
    manifest_path = staging.parent / f"{sidecar_stem}.manifest.json"
    archive_path = staging.parent / f"{sidecar_stem}.zip"
    manifest_path.write_bytes(manifest_bytes(manifest))
    write_deterministic_zip(staging, archive_path, manifest)
    return staging, manifest_path, archive_path, manifest


def zip_contents(archive: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(archive) as source:
        return {
            info.filename: source.read(info.filename) for info in source.infolist()
        }


def check_reproducible(
    source: Path = DEFAULT_SOURCE,
    workshop_item_id: str | None = None,
    revision: str | None = None,
) -> dict[str, object]:
    """Build twice in isolation and prove manifest and ZIP byte reproducibility."""
    source = Path(source).resolve()
    errors = release_source_errors(source)
    if errors:
        raise ValueError("invalid standalone source:\n" + "\n".join(errors))
    revision = _require_full_revision(revision or git_sha())
    workshop_item_id = normalize_workshop_item_id(workshop_item_id)
    with tempfile.TemporaryDirectory(prefix="vivhite-release-check-") as temporary:
        temporary_root = Path(temporary)
        builds = []
        for parent_name in ("first", "second"):
            staging = temporary_root / parent_name / PRODUCT_ID
            builds.append(
                build_release(
                    source,
                    staging,
                    revision=revision,
                    workshop_item_id=workshop_item_id,
                )
            )
        first, second = builds
        if first[3] != second[3]:
            raise ValueError("release manifests differ between identical builds")
        first_manifest_bytes = first[1].read_bytes()
        first_zip_bytes = first[2].read_bytes()
        if first_manifest_bytes != second[1].read_bytes():
            raise ValueError("serialized release manifests are not deterministic")
        if first_zip_bytes != second[2].read_bytes():
            raise ValueError("release ZIP bytes are not deterministic")
        if zip_contents(first[2]) != zip_contents(second[2]):
            raise ValueError("release ZIP contents differ between identical builds")
        return {
            "file_count": len(first[3]["files"]),
            "manifest_sha256": sha256_bytes(first_manifest_bytes),
            "zip_sha256": sha256_bytes(first_zip_bytes),
        }


def workshop_descriptor_matches(
    path: Path, entry: dict[str, object], workshop_item_id: str
) -> bool:
    """Accept only the observed launcher newline rewrite plus one final ID line."""
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

    marker = f'remote_file_id="{workshop_item_id}"'.encode("ascii")
    lines = data.splitlines()
    remote_lines = [
        index for index, line in enumerate(lines) if b"remote_file_id" in line
    ]
    if remote_lines != [len(lines) - 1] or lines[-1] != marker:
        return False
    canonical_lines = lines[:-1]
    for separator in (b"\n", b"\r\n"):
        body = separator.join(canonical_lines)
        for candidate in (body, body + separator):
            if (
                len(candidate) == entry.get("size")
                and sha256_bytes(candidate) == entry.get("sha256")
            ):
                return True
    return False


def _load_and_validate_manifest(
    manifest_path: Path, target: Path
) -> dict[str, object]:
    try:
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"manifest is not valid JSON: {error}") from error
    if not isinstance(manifest, dict):
        raise ValueError("manifest root must be an object")

    required_keys = {
        "format_version",
        "product_id",
        "mod_version",
        "git_tag",
        "git_sha",
        "workshop_item_id",
        "files",
    }
    if set(manifest) != required_keys:
        missing = sorted(required_keys - set(manifest))
        extra = sorted(set(manifest) - required_keys)
        raise ValueError(f"manifest fields mismatch; missing={missing}, extra={extra}")

    version = descriptor_version(target)
    identity = {
        "format_version": MANIFEST_FORMAT_VERSION,
        "product_id": PRODUCT_ID,
        "mod_version": version,
    }
    for key, expected in identity.items():
        if manifest.get(key) != expected:
            raise ValueError(
                f"manifest identity mismatch for {key}: "
                f"{manifest.get(key)!r} != {expected!r}"
            )
    expected_tag = product_tag(version)
    manifest_tag = manifest.get("git_tag")
    if manifest_tag is not None and not isinstance(manifest_tag, str):
        raise ValueError("manifest git_tag must be a string or null")
    if manifest_tag not in {None, expected_tag}:
        raise ValueError(
            "manifest identity mismatch for git_tag: "
            f"{manifest_tag!r} is neither null nor {expected_tag!r}"
        )
    _require_full_revision(manifest.get("git_sha"))
    normalize_workshop_item_id(manifest.get("workshop_item_id"))

    entries = manifest.get("files")
    if not isinstance(entries, list):
        raise ValueError("manifest files must be a list")
    paths: list[str] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or set(entry) != {"path", "size", "sha256"}:
            raise ValueError(f"manifest file entry {index} has invalid fields")
        relative = entry.get("path")
        size = entry.get("size")
        digest = entry.get("sha256")
        if not isinstance(relative, str):
            raise ValueError(f"manifest file entry {index} has a non-string path")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            raise ValueError(f"manifest file entry {relative!r} has an invalid size")
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise ValueError(f"manifest file entry {relative!r} has an invalid SHA-256")
        paths.append(relative)
    expected_paths = sorted(RUNTIME_FILES)
    if paths != expected_paths:
        missing = sorted(RUNTIME_FILES - set(paths))
        extra = sorted(set(paths) - RUNTIME_FILES)
        duplicates = sorted({path for path in paths if paths.count(path) > 1})
        raise ValueError(
            "manifest file inventory mismatch; "
            f"missing={missing}, extra={extra}, duplicates={duplicates}, "
            f"sorted={paths == sorted(paths)}"
        )
    return manifest


def verify_manifest(
    target: Path, manifest_path: Path, workshop_cache: bool = False
) -> int:
    """Verify product identity, exact inventory, and every recorded file byte."""
    target = Path(target).resolve()
    if not target.is_dir():
        raise ValueError(f"verification target directory missing: {target}")
    manifest = _load_and_validate_manifest(manifest_path, target)
    workshop_item_id = manifest["workshop_item_id"]
    if workshop_cache and workshop_item_id is None:
        raise ValueError(
            "--workshop-cache requires a non-null numeric manifest workshop_item_id"
        )

    actual_paths: dict[str, Path] = {}
    symlinks: list[str] = []
    for path in sorted(target.rglob("*"), key=lambda item: item.as_posix()):
        relative = _relative(path, target)
        if path.is_symlink():
            symlinks.append(relative)
        elif path.is_file():
            actual_paths[relative] = path

    errors = [f"symlink: {relative}" for relative in symlinks]
    expected = {entry["path"]: entry for entry in manifest["files"]}
    for relative, entry in expected.items():
        path = actual_paths.pop(relative, None)
        if path is None:
            errors.append(f"missing: {relative}")
            continue
        if workshop_cache and relative == "descriptor.mod":
            if not workshop_descriptor_matches(path, entry, workshop_item_id):
                errors.append("mismatch: descriptor.mod")
            continue
        if path.stat().st_size != entry["size"] or sha256_file(path) != entry["sha256"]:
            errors.append(f"mismatch: {relative}")
    errors.extend(f"extra: {relative}" for relative in sorted(actual_paths))
    if errors:
        raise ValueError("manifest verification failed:\n" + "\n".join(errors))
    return len(expected)


def _workshop_id_argument(value: str) -> str:
    try:
        normalized = normalize_workshop_item_id(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from error
    assert normalized is not None
    return normalized


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--check",
        action="store_true",
        help="build twice in temporary directories and prove reproducibility",
    )
    modes.add_argument(
        "--release",
        action="store_true",
        help="require a clean vivhite-v<version> tag and version sidecars",
    )
    modes.add_argument("--verify", type=Path, help="directory to verify")
    parser.add_argument("--manifest", type=Path, help="manifest used by --verify")
    parser.add_argument(
        "--workshop-cache",
        action="store_true",
        help="require and normalize only the launcher's final remote_file_id line",
    )
    parser.add_argument(
        "--workshop-item-id",
        type=_workshop_id_argument,
        help="new standalone Workshop item ID to record; no default is assumed",
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
            count = verify_manifest(
                args.verify, args.manifest, workshop_cache=args.workshop_cache
            )
            print(f"Verified directory: {args.verify.resolve()}")
            print(f"Manifest: {args.manifest.resolve()}")
            print(f"Files: {count}")
            return 0

        if args.check:
            result = check_reproducible(args.source, args.workshop_item_id)
            print(f"Reproducibility source: {args.source.resolve()}")
            print(f"Files: {result['file_count']}")
            print(f"Manifest SHA-256: {result['manifest_sha256']}")
            print(f"ZIP SHA-256: {result['zip_sha256']}")
            return 0

        if args.release:
            identity = release_identity(args.source)
            revision = identity["git_sha"]
            version = identity["mod_version"]
            git_tag = identity["git_tag"]
        else:
            revision = _require_full_revision(git_sha())
            version = descriptor_version(args.source)
            git_tag = None
        staging, manifest_path, archive_path, details = build_release(
            args.source,
            args.output,
            revision=revision,
            version=version,
            workshop_item_id=args.workshop_item_id,
            versioned_sidecars=args.release,
            git_tag=git_tag,
        )
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print(f"VIVHITE RELEASE FAILED: {error}", file=sys.stderr)
        return 1

    print(f"Release staging: {staging}")
    print(f"Manifest: {manifest_path}")
    print(f"Archive: {archive_path}")
    print(f"Files: {len(details['files'])}")
    print(f"Manifest SHA-256: {sha256_file(manifest_path)}")
    print(f"ZIP SHA-256: {sha256_file(archive_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
