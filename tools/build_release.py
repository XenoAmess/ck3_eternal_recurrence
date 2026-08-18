#!/usr/bin/env python3
"""Build a byte-preserving, reproducible CK3 release staging directory."""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = ROOT / "XenoAmess_s_Eternal_Recurrence"
DEFAULT_OUTPUT = ROOT / "dist" / "XenoAmess_s_Eternal_Recurrence"

RELEASE_ROOT_FILES = {"descriptor.mod", "thumbnail.png"}
RELEASE_DIRECTORY_SUFFIXES = {
    "common": {".txt"},
    "events": {".txt"},
    "gfx": {".dds"},
    "gui": {".gui", ".txt"},
    "localization": {".yml"},
}
EXCLUDED_DEVELOPMENT_DIRECTORIES = {"tools"}
FORBIDDEN_CACHE_SUFFIXES = {".pyc", ".pyo"}
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
WORKSHOP_ITEM_ID = "3784706360"


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def release_source_errors(source):
    """Return allowlist violations without changing the source tree."""
    source = Path(source)
    if not source.is_dir():
        return [f"mod source directory missing: {source}"]

    errors = []
    for name in sorted(RELEASE_ROOT_FILES):
        if not (source / name).is_file():
            errors.append(f"required release file missing: {name}")
    for name in sorted(RELEASE_DIRECTORY_SUFFIXES):
        if not (source / name).is_dir():
            errors.append(f"required release directory missing: {name}/")

    known_roots = (
        RELEASE_ROOT_FILES
        | set(RELEASE_DIRECTORY_SUFFIXES)
        | EXCLUDED_DEVELOPMENT_DIRECTORIES
    )
    for path in sorted(source.iterdir(), key=lambda item: item.name):
        if path.name not in known_roots:
            errors.append(f"path outside release allowlist: {path.name}")

    for path in sorted(source.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(source)
        if path.is_symlink():
            errors.append(f"symlink is not allowed in release source: {relative.as_posix()}")
            continue
        if path.is_file() and (
            "__pycache__" in relative.parts
            or path.suffix.lower() in FORBIDDEN_CACHE_SUFFIXES
        ):
            errors.append(f"Python cache is forbidden in mod source: {relative.as_posix()}")
            continue
        if path.is_dir() or relative.parts[0] in EXCLUDED_DEVELOPMENT_DIRECTORIES:
            continue
        if len(relative.parts) == 1:
            if relative.name not in RELEASE_ROOT_FILES:
                errors.append(f"root file outside release allowlist: {relative.as_posix()}")
            continue
        allowed_suffixes = RELEASE_DIRECTORY_SUFFIXES.get(relative.parts[0])
        if allowed_suffixes is None or path.suffix.lower() not in allowed_suffixes:
            errors.append(f"file outside release allowlist: {relative.as_posix()}")
    return errors


def release_files(source):
    """Return the explicitly allowlisted release files in stable path order."""
    source = Path(source)
    files = [source / name for name in RELEASE_ROOT_FILES if (source / name).is_file()]
    for directory, suffixes in RELEASE_DIRECTORY_SUFFIXES.items():
        base = source / directory
        if base.is_dir():
            files.extend(
                path for path in base.rglob("*")
                if path.is_file() and path.suffix.lower() in suffixes
            )
    return sorted(files, key=lambda path: path.relative_to(source).as_posix())


def git_sha(repository=ROOT):
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


def git_output(*args, repository=ROOT):
    try:
        result = subprocess.run(
            ["git", "-C", str(repository), *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as error:
        raise ValueError(f"git {' '.join(args)} failed") from error
    return result.stdout.strip()


def descriptor_version(source):
    descriptor = (Path(source) / "descriptor.mod").read_text(encoding="utf-8-sig")
    matches = re.findall(r'(?m)^version="(\d+\.\d+\.\d+)"$', descriptor)
    if len(matches) != 1:
        raise ValueError("descriptor.mod must contain exactly one semantic version")
    return matches[0]


def release_identity(source):
    version = descriptor_version(source)
    revision = git_sha()
    if not revision:
        raise ValueError("release build requires a Git revision")
    if git_output("status", "--porcelain"):
        raise ValueError("release build requires a clean worktree")
    tag = f"v{version}"
    tags = git_output("tag", "--points-at", "HEAD").splitlines()
    if tag not in tags:
        raise ValueError(f"release build requires tag {tag} on HEAD")
    return {"mod_version": version, "git_tag": tag, "git_sha": revision}


def create_manifest(staging, revision, version, tag=None):
    files = []
    for path in sorted(staging.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file():
            continue
        data = path.read_bytes()
        files.append({
            "path": path.relative_to(staging).as_posix(),
            "size": len(data),
            "sha256": sha256_bytes(data),
        })
    return {
        "format_version": 2,
        "mod_version": version,
        "git_tag": tag,
        "git_sha": revision,
        "workshop_item_id": WORKSHOP_ITEM_ID,
        "files": files,
    }


def manifest_bytes(manifest):
    return (json.dumps(
        manifest,
        ensure_ascii=True,
        indent=2,
        sort_keys=True,
    ) + "\n").encode("utf-8")


def write_deterministic_zip(staging, archive, manifest):
    with zipfile.ZipFile(archive, "w") as output:
        for entry in manifest["files"]:
            path = staging / entry["path"]
            archive_name = f"{staging.name}/{entry['path']}"
            info = zipfile.ZipInfo(archive_name, ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            output.writestr(info, path.read_bytes(), compresslevel=9)


def build_release(source, staging, revision=None, tag=None, version=None,
                  versioned_sidecars=False):
    """Build staging plus sibling manifest/ZIP and return their paths and manifest."""
    source = Path(source).resolve()
    staging = Path(staging).resolve()
    errors = release_source_errors(source)
    if errors:
        raise ValueError("\n".join(errors))
    if staging == source or source in staging.parents or staging in source.parents:
        raise ValueError("release staging and mod source must not contain one another")

    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    for directory in RELEASE_DIRECTORY_SUFFIXES:
        (staging / directory).mkdir()
    for path in release_files(source):
        target = staging / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)

    staging_errors = release_source_errors(staging)
    if staging_errors:
        raise ValueError("invalid release staging:\n" + "\n".join(staging_errors))

    version = version or descriptor_version(source)
    manifest = create_manifest(staging, revision, version, tag)
    sidecar_name = f"{staging.name}-v{version}" if versioned_sidecars else staging.name
    manifest_path = staging.parent / f"{sidecar_name}.manifest.json"
    archive_path = staging.parent / f"{sidecar_name}.zip"
    manifest_path.write_bytes(manifest_bytes(manifest))
    write_deterministic_zip(staging, archive_path, manifest)
    return staging, manifest_path, archive_path, manifest


def zip_contents(archive):
    with zipfile.ZipFile(archive) as source:
        return {
            info.filename: source.read(info.filename)
            for info in source.infolist()
        }


def check_reproducible(source=DEFAULT_SOURCE):
    """Build twice in temporary directories and verify byte-for-byte reproducibility."""
    source = Path(source).resolve()
    errors = release_source_errors(source)
    if errors:
        raise ValueError("\n".join(errors))
    revision = git_sha()
    with tempfile.TemporaryDirectory(prefix="xar-release-check-") as temporary:
        temporary = Path(temporary)
        builds = []
        for parent in (temporary / "first", temporary / "second"):
            staging = parent / DEFAULT_OUTPUT.name
            builds.append(build_release(source, staging, revision))

        first = builds[0]
        second = builds[1]
        if first[3] != second[3]:
            raise ValueError("release manifests differ between identical builds")
        if first[1].read_bytes() != second[1].read_bytes():
            raise ValueError("serialized release manifests are not deterministic")
        if first[2].read_bytes() != second[2].read_bytes():
            raise ValueError("release ZIP bytes are not deterministic")
        if zip_contents(first[2]) != zip_contents(second[2]):
            raise ValueError("release ZIP contents differ between identical builds")
    return len(first[3]["files"])


def verify_manifest(target, manifest_path):
    target = Path(target).resolve()
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    version = descriptor_version(target)
    required_identity = {
        "format_version": 2,
        "mod_version": version,
        "git_tag": f"v{version}",
        "workshop_item_id": WORKSHOP_ITEM_ID,
    }
    for key, value in required_identity.items():
        if manifest.get(key) != value:
            raise ValueError(f"manifest identity mismatch for {key}: {manifest.get(key)!r} != {value!r}")
    if not re.fullmatch(r"[0-9a-f]{40}", manifest.get("git_sha") or ""):
        raise ValueError("manifest git_sha is not a full Git revision")
    entries = manifest.get("files", [])
    paths = [entry.get("path") for entry in entries]
    if len(paths) != len(set(paths)):
        raise ValueError("manifest contains duplicate file paths")
    expected = {entry["path"]: entry for entry in entries}
    actual_paths = {
        path.relative_to(target).as_posix(): path
        for path in target.rglob("*") if path.is_file()
    }
    errors = []
    for relative, entry in expected.items():
        path = actual_paths.pop(relative, None)
        if path is None:
            errors.append(f"missing: {relative}")
        elif path.stat().st_size != entry["size"] or sha256_file(path) != entry["sha256"]:
            errors.append(f"mismatch: {relative}")
    errors.extend(f"extra: {relative}" for relative in sorted(actual_paths))
    if errors:
        raise ValueError("manifest verification failed:\n" + "\n".join(errors))
    return len(expected)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="build twice in temporary directories and verify reproducibility",
    )
    parser.add_argument(
        "--release", action="store_true",
        help="require a clean tagged worktree and emit versioned release sidecars",
    )
    parser.add_argument("--verify", type=Path, help="verify a directory against --manifest")
    parser.add_argument("--manifest", type=Path, help="manifest used by --verify")
    args = parser.parse_args()
    try:
        if args.verify:
            if not args.manifest:
                raise ValueError("--verify requires --manifest")
            count = verify_manifest(args.verify, args.manifest)
            print(f"MANIFEST VERIFY OK: {count} files")
            return 0
        if args.check:
            count = check_reproducible(args.source)
            print(f"RELEASE CHECK OK: {count} files, deterministic manifest and ZIP")
            return 0
        identity = release_identity(args.source) if args.release else {
            "mod_version": descriptor_version(args.source),
            "git_tag": None,
            "git_sha": git_sha(),
        }
        staging, manifest, archive, details = build_release(
            args.source, args.output, identity["git_sha"], identity["git_tag"],
            identity["mod_version"], args.release)
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print(f"RELEASE BUILD FAILED: {error}", file=sys.stderr)
        return 1
    print(f"Release staging: {staging}")
    print(f"Manifest: {manifest}")
    print(f"Archive: {archive}")
    print(f"Files: {len(details['files'])}")
    print(f"Manifest SHA-256: {sha256_file(manifest)}")
    print(f"ZIP SHA-256: {sha256_file(archive)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
