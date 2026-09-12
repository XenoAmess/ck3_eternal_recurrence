#!/usr/bin/env python3
"""Build and verify the standalone Reclaim the Motherland mod."""

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
PRODUCT_ID = "mod_reclaim_the_motherland"
PRODUCT_TAG_PREFIX = "reclaim-motherland-v"
DEFAULT_SOURCE = ROOT / PRODUCT_ID
DEFAULT_OUTPUT = ROOT / "dist" / PRODUCT_ID
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
MANIFEST_FORMAT_VERSION = 1

# This is deliberately the exact current runtime inventory; README.md never ships.
RUNTIME_FILES = frozenset(
    {
        "common/decisions/rmtm_restoration_decisions.txt",
        "common/decisions/dlc_decisions/tgp/zz_rmtm_mandate_override.txt",
        "common/game_rules/rmtm_game_rules.txt",
        "common/script_values/rmtm_loyalty_values.txt",
        "common/scripted_effects/rmtm_dynastic_cycle_effects.txt",
        "common/scripted_effects/rmtm_generated_title_name_effects.txt",
        "common/scripted_effects/rmtm_loyalty_resolution_effects.txt",
        "common/scripted_effects/rmtm_vanilla_compat_effects.txt",
        "common/scripted_effects/zz_rmtm_vanilla_overrides.txt",
        "common/scripted_triggers/rmtm_loyalty_triggers.txt",
        "common/scripted_triggers/rmtm_restoration_triggers.txt",
        "descriptor.mod",
        "events/rmtm_loyalty_events.txt",
        "localization/english/rmtm_l_english.yml",
        "localization/english/rmtm_generated_title_names_l_english.yml",
        "localization/french/rmtm_l_french.yml",
        "localization/french/rmtm_generated_title_names_l_french.yml",
        "localization/german/rmtm_l_german.yml",
        "localization/german/rmtm_generated_title_names_l_german.yml",
        "localization/japanese/rmtm_l_japanese.yml",
        "localization/japanese/rmtm_generated_title_names_l_japanese.yml",
        "localization/korean/rmtm_l_korean.yml",
        "localization/korean/rmtm_generated_title_names_l_korean.yml",
        "localization/polish/rmtm_l_polish.yml",
        "localization/polish/rmtm_generated_title_names_l_polish.yml",
        "localization/russian/rmtm_l_russian.yml",
        "localization/russian/rmtm_generated_title_names_l_russian.yml",
        "localization/simp_chinese/rmtm_l_simp_chinese.yml",
        "localization/simp_chinese/rmtm_generated_title_names_l_simp_chinese.yml",
        "localization/spanish/rmtm_l_spanish.yml",
        "localization/spanish/rmtm_generated_title_names_l_spanish.yml",
        "thumbnail.png",
    }
)
SOURCE_ONLY_FILES = frozenset(
    {"README.md", "docs/acceptance-plan.md", "docs/acceptance-report.md"}
)
FORBIDDEN_WORKSHOP_ITEM_IDS = frozenset(
    {
        "3784706360",
        "3787304042",
        "3790635143",
        "3792585972",
        "3797711947",
        "3798133925",
    }
)
FULL_GIT_SHA = re.compile(r"[0-9a-f]{40}")
SEMANTIC_VERSION = re.compile(r"\d+\.\d+\.\d+")
WORKSHOP_ITEM_ID = re.compile(r"[1-9][0-9]*", re.ASCII)
LOCALIZATION_ENTRY = re.compile(r'^ ([^:\s]+):\d+ "((?:[^"\\]|\\.)*)"$')
LOCALIZATION_LANGUAGES = (
    "english",
    "french",
    "german",
    "japanese",
    "korean",
    "polish",
    "russian",
    "simp_chinese",
    "spanish",
)
LOCALIZATION_SOURCE_LANGUAGES = frozenset({"english", "simp_chinese"})
LOCALIZATION_PROTECTED_TOKEN = re.compile(r"#[A-Za-z0-9_]+|#!")


def _allowed_directories(files: frozenset[str]) -> frozenset[str]:
    result: set[str] = set()
    for relative in files:
        parent = PurePosixPath(relative).parent
        while parent != PurePosixPath("."):
            result.add(parent.as_posix())
            parent = parent.parent
    return frozenset(result)


RUNTIME_DIRECTORIES = _allowed_directories(RUNTIME_FILES)
SOURCE_DIRECTORIES = _allowed_directories(RUNTIME_FILES | SOURCE_ONLY_FILES)


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
        raise ValueError(
            "Workshop item ID must be positive ASCII digits without leading zeros"
        )
    if int(value) > 2**64 - 1:
        raise ValueError("Workshop item ID exceeds the Steam unsigned 64-bit range")
    if value in FORBIDDEN_WORKSHOP_ITEM_IDS:
        raise ValueError("Reclaim the Motherland must use a new Workshop item ID")
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

    expected_files = RUNTIME_FILES | (
        SOURCE_ONLY_FILES if allow_source_only_files else frozenset()
    )
    errors.extend(
        f"required runtime file missing: {relative}"
        for relative in sorted(RUNTIME_FILES - actual_files)
    )
    errors.extend(
        f"file outside exact runtime allowlist: {relative}"
        for relative in sorted(actual_files - expected_files)
    )
    errors.extend(
        f"directory outside exact runtime allowlist: {relative}/"
        for relative in sorted(
            actual_directories
            - (SOURCE_DIRECTORIES if allow_source_only_files else RUNTIME_DIRECTORIES)
        )
    )

    for relative in sorted(actual_files & RUNTIME_FILES):
        path = source / PurePosixPath(relative)
        data = path.read_bytes()
        if relative == "descriptor.mod":
            if data.startswith(b"\xef\xbb\xbf"):
                errors.append("descriptor.mod must not contain a UTF-8 BOM")
        elif path.suffix.lower() in {".txt", ".gui", ".yml"}:
            if not data.startswith(b"\xef\xbb\xbf"):
                errors.append(f"script/localization lacks UTF-8 BOM: {relative}")

        if path.suffix.lower() in {".mod", ".txt", ".gui", ".yml"}:
            try:
                value = data.decode("utf-8-sig")
            except UnicodeDecodeError as error:
                errors.append(f"runtime text is not UTF-8: {relative}: {error}")
                continue
            if "remote_file_id" in value:
                errors.append(f"canonical runtime contains remote_file_id: {relative}")
            for item_id in FORBIDDEN_WORKSHOP_ITEM_IDS:
                if item_id in value:
                    errors.append(
                        f"existing Workshop item ID {item_id} is forbidden: {relative}"
                    )
    return errors


def _localization_entries(path: Path, language: str) -> dict[str, str]:
    data = Path(path).read_bytes()
    if not data.startswith(b"\xef\xbb\xbf"):
        raise ValueError(f"localization lacks UTF-8 BOM: {path}")
    lines = data.decode("utf-8-sig").splitlines()
    if not lines or lines[0] != f"l_{language}:":
        raise ValueError(f"localization header mismatch: {path}")
    result: dict[str, str] = {}
    for line_number, line in enumerate(lines[1:], 2):
        if not line or line.lstrip().startswith("#"):
            continue
        match = LOCALIZATION_ENTRY.fullmatch(line)
        if match is None:
            raise ValueError(f"malformed localization line: {path}:{line_number}")
        key, value = match.groups()
        if key in result:
            raise ValueError(f"duplicate localization key: {path}:{line_number}: {key}")
        result[key] = value
    if not result:
        raise ValueError(f"localization has no entries: {path}")
    return result


def release_localization_errors(source: Path) -> list[str]:
    """Require complete, translated localization for a formal release."""

    matrix: dict[str, dict[str, str]] = {}
    errors: list[str] = []
    for language in LOCALIZATION_LANGUAGES:
        directory = Path(source) / "localization" / language
        values: dict[str, str] = {}
        for path in sorted(directory.glob("rmtm_*.yml")):
            try:
                entries = _localization_entries(path, language)
            except (OSError, UnicodeError, ValueError) as error:
                errors.append(str(error))
                continue
            duplicates = sorted(set(values) & set(entries))
            if duplicates:
                errors.append(f"duplicate localization keys across files: {duplicates}")
            values.update(entries)
        if not values:
            errors.append(f"{language} localization has no RMTM entries")
        else:
            matrix[language] = values
    english = matrix.get("english")
    if english is None:
        return errors
    for language, values in matrix.items():
        if set(values) != set(english):
            errors.append(
                f"{language} localization key mismatch: "
                f"missing={sorted(set(english) - set(values))}, "
                f"extra={sorted(set(values) - set(english))}"
            )
            continue
        for key, value in values.items():
            if not value.strip():
                errors.append(f"{language} localization is empty: {key}")
            if sorted(LOCALIZATION_PROTECTED_TOKEN.findall(value)) != sorted(
                LOCALIZATION_PROTECTED_TOKEN.findall(english[key])
            ):
                errors.append(
                    f"{language} localization changes CK3 formatting tokens: {key}"
                )
        if language not in LOCALIZATION_SOURCE_LANGUAGES:
            placeholders = sorted(
                key
                for key, value in values.items()
                if value == english[key] and not key.startswith("rmtm_later_dynn_title_")
            )
            if placeholders:
                errors.append(
                    f"{language} still contains English placeholder values: {placeholders}"
                )
    return errors


def descriptor_version(source: Path) -> str:
    path = Path(source) / "descriptor.mod"
    try:
        value = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ValueError(f"cannot read descriptor.mod: {error}") from error
    matches = re.findall(
        r'(?m)^version="([^"\n]+)"$', value.replace("\r\n", "\n")
    )
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
        raise ValueError("formal release requires the canonical Reclaim source")
    if git_output("status", "--porcelain", "--untracked-files=all"):
        raise ValueError("formal release requires a clean worktree")
    version = descriptor_version(source)
    tag = product_tag(version)
    if tag not in git_output("tag", "--points-at", "HEAD").splitlines():
        raise ValueError(f"formal release requires tag {tag} on HEAD")
    localization_errors = release_localization_errors(source)
    if localization_errors:
        raise ValueError(
            "formal release localization is incomplete:\n"
            + "\n".join(localization_errors)
        )
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
    if SEMANTIC_VERSION.fullmatch(version) is None:
        raise ValueError("manifest requires a semantic mod version")
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
    *,
    workshop_item_id: str | None = None,
    versioned_sidecars: bool = False,
    git_tag: str | None = None,
) -> tuple[Path, Path, Path, dict[str, object]]:
    source = Path(source).resolve()
    staging = Path(staging).resolve()
    errors = release_source_errors(source)
    if errors:
        raise ValueError(
            "invalid Reclaim the Motherland source:\n" + "\n".join(errors)
        )
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
    with tempfile.TemporaryDirectory(prefix="reclaim-release-check-") as name:
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
        "format_version",
        "product_id",
        "mod_version",
        "git_tag",
        "git_sha",
        "workshop_item_id",
        "files",
    }
    if not isinstance(manifest, dict) or set(manifest) != required:
        raise ValueError("manifest fields mismatch")
    if manifest["format_version"] != MANIFEST_FORMAT_VERSION:
        raise ValueError("manifest format mismatch")
    if manifest["product_id"] != PRODUCT_ID:
        raise ValueError("manifest product mismatch")
    version = manifest["mod_version"]
    if not isinstance(version, str) or SEMANTIC_VERSION.fullmatch(version) is None:
        raise ValueError("manifest mod version is invalid")
    revision = manifest["git_sha"]
    if not isinstance(revision, str) or FULL_GIT_SHA.fullmatch(revision) is None:
        raise ValueError("manifest Git SHA is invalid")
    git_tag = manifest["git_tag"]
    if git_tag not in {None, product_tag(version)}:
        raise ValueError("manifest Git tag does not match the mod version")
    normalize_workshop_item_id(manifest["workshop_item_id"])
    files = manifest["files"]
    if not isinstance(files, list):
        raise ValueError("manifest files must be a list")
    paths: list[str] = []
    for entry in files:
        if not isinstance(entry, dict) or set(entry) != {"path", "size", "sha256"}:
            raise ValueError("manifest file entry fields mismatch")
        relative = entry["path"]
        if not isinstance(relative, str):
            raise ValueError("manifest file path is invalid")
        if not isinstance(entry["size"], int) or entry["size"] < 0:
            raise ValueError(f"manifest file size is invalid: {relative}")
        if (
            not isinstance(entry["sha256"], str)
            or re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]) is None
        ):
            raise ValueError(f"manifest file SHA-256 is invalid: {relative}")
        paths.append(relative)
    if paths != sorted(RUNTIME_FILES):
        raise ValueError("manifest file inventory mismatch")
    return manifest


def workshop_descriptor_matches(
    path: Path, entry: dict[str, object], workshop_item_id: str
) -> bool:
    data = Path(path).read_bytes()
    # Direct Steamworks uploads preserve the canonical inner descriptor, while
    # Paradox Launcher uploads append one remote_file_id line.  A fresh cache
    # may therefore contain either exact representation of the same release.
    if len(data) == entry["size"] and sha256_bytes(data) == entry["sha256"]:
        return True
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


def verify_manifest(
    target: Path, manifest_path: Path, *, workshop_cache: bool = False
) -> int:
    target = Path(target).resolve()
    manifest = _load_manifest(manifest_path)
    item_id = manifest["workshop_item_id"]
    if workshop_cache and item_id is None:
        raise ValueError("Workshop-cache verification requires a manifest item ID")
    actual = {
        _relative(path, target): path for path in target.rglob("*") if path.is_file()
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
            count = verify_manifest(
                args.verify, args.manifest, workshop_cache=args.workshop_cache
            )
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
        print(f"RECLAIM RELEASE FAILED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
