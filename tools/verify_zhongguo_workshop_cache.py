#!/usr/bin/env python3
"""Verify a fresh ZhongGuo 361 Workshop cache against a formal release.

The formal manifest and ZIP always describe the canonical, ID-free release.
For a first Workshop upload the launcher may publish one final
``remote_file_id`` line in the cached inner descriptor.  That exception is
available only through the explicit ``launcher-injected`` descriptor policy;
all other bytes and every other file must remain canonical.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath


sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_mod_zhongguo_style_release as release  # noqa: E402


REPORT_FORMAT_VERSION = 1
REPORT_KIND = "zhongguo_workshop_cache_verification"
DESCRIPTOR_POLICIES = ("canonical", "launcher-injected")
EXIT_GREEN = 0
EXIT_RED = 1
EXPECTED_ZIP_EXTERNAL_ATTR = 0o100644 << 16


class VerificationError(ValueError):
    """A deterministic release/cache contract was not satisfied."""


def _resolved(path: Path) -> Path:
    return Path(path).expanduser().resolve()


def _input_record(path: Path) -> dict[str, object]:
    path = _resolved(path)
    result: dict[str, object] = {"path": str(path), "exists": path.is_file()}
    if path.is_file():
        result.update({"size": path.stat().st_size, "sha256": release.sha256_file(path)})
    return result


def _formal_manifest(cache_leaf: Path, manifest_path: Path) -> dict[str, object]:
    manifest = release._load_manifest(manifest_path, cache_leaf)
    expected_tag = release.product_tag(str(manifest["mod_version"]))
    if manifest["git_tag"] != expected_tag:
        raise VerificationError(
            f"formal manifest requires git_tag {expected_tag!r}, got {manifest['git_tag']!r}"
        )
    item_id = release.normalize_workshop_item_id(manifest["workshop_item_id"])
    if item_id is None:
        raise VerificationError("post-upload manifest requires a non-null Workshop item ID")
    if cache_leaf.name != item_id:
        raise VerificationError(
            f"cache leaf name must equal Workshop item ID {item_id}, got {cache_leaf.name!r}"
        )

    paths = [str(entry["path"]) for entry in manifest["files"]]
    missing_roots = sorted(release.RELEASE_ROOT_FILES - set(paths))
    present_directories = {PurePosixPath(path).parts[0] for path in paths}
    missing_directories = sorted(
        set(release.RELEASE_DIRECTORY_SUFFIXES) - present_directories
    )
    expected_localization = {
        f"localization/{language}/{family}_l_{language}.yml"
        for language in release.REQUIRED_LOCALIZATION_LANGUAGES
        for family in release.LOCALIZATION_FAMILIES
    }
    missing_localization = sorted(expected_localization - set(paths))
    if missing_roots or missing_directories or missing_localization:
        details: list[str] = []
        if missing_roots:
            details.append("root files=" + ", ".join(missing_roots))
        if missing_directories:
            details.append("runtime directories=" + ", ".join(missing_directories))
        if missing_localization:
            details.append("localization files=" + ", ".join(missing_localization))
        raise VerificationError("formal manifest inventory is incomplete: " + "; ".join(details))
    return manifest


def _verify_archive(
    archive_path: Path, manifest: dict[str, object]
) -> dict[str, dict[str, object]]:
    archive_path = _resolved(archive_path)
    if not archive_path.is_file():
        raise VerificationError(f"release ZIP missing: {archive_path}")

    entries = manifest["files"]
    expected_names = [
        f"{release.PRODUCT_ID}/{entry['path']}" for entry in entries
    ]
    errors: list[str] = []
    records: dict[str, dict[str, object]] = {}
    with zipfile.ZipFile(archive_path) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if names != expected_names:
            missing = sorted(set(expected_names) - set(names))
            extra = sorted(set(names) - set(expected_names))
            duplicates = sorted({name for name in names if names.count(name) > 1})
            if missing:
                errors.append("ZIP missing: " + ", ".join(missing))
            if extra:
                errors.append("ZIP extra: " + ", ".join(extra))
            if duplicates:
                errors.append("ZIP duplicate: " + ", ".join(duplicates))
            if not (missing or extra or duplicates):
                errors.append("ZIP member order differs from the formal manifest")
        if archive.comment:
            errors.append("ZIP archive comment is not canonical")

        if not errors:
            for info, entry in zip(infos, entries, strict=True):
                relative = str(entry["path"])
                if info.is_dir():
                    errors.append(f"ZIP contains directory member: {info.filename}")
                    continue
                if info.date_time != release.ZIP_TIMESTAMP:
                    errors.append(f"ZIP timestamp mismatch: {relative}")
                if info.compress_type != zipfile.ZIP_DEFLATED:
                    errors.append(f"ZIP compression mismatch: {relative}")
                if info.create_system != 3 or info.external_attr != EXPECTED_ZIP_EXTERNAL_ATTR:
                    errors.append(f"ZIP file-mode metadata mismatch: {relative}")
                if info.extra or info.comment:
                    errors.append(f"ZIP member metadata is not canonical: {relative}")
                if info.flag_bits & 1:
                    errors.append(f"ZIP member must not be encrypted: {relative}")
                try:
                    data = archive.read(info)
                except (OSError, RuntimeError, zipfile.BadZipFile) as error:
                    errors.append(f"ZIP member cannot be read: {relative}: {error}")
                    continue
                digest = release.sha256_bytes(data)
                records[relative] = {"size": len(data), "sha256": digest}
                if len(data) != entry["size"] or digest != entry["sha256"]:
                    errors.append(f"ZIP content mismatch: {relative}")
                if relative == "descriptor.mod" and b"remote_file_id" in data:
                    errors.append("canonical ZIP descriptor.mod contains remote_file_id")

    if errors:
        raise VerificationError("release ZIP verification failed:\n" + "\n".join(errors))
    return records


def _remote_file_id(data: bytes) -> str | None:
    matches = re.findall(rb'(?m)^remote_file_id="([1-9][0-9]*)"\r?$', data)
    if len(matches) != 1:
        return None
    return matches[0].decode("ascii")


def _verify_cache(
    cache_leaf: Path,
    manifest: dict[str, object],
    descriptor_policy: str,
) -> tuple[dict[str, dict[str, object]], dict[str, object]]:
    if descriptor_policy not in DESCRIPTOR_POLICIES:
        raise VerificationError(f"unknown descriptor policy: {descriptor_policy!r}")
    cache_leaf = _resolved(cache_leaf)
    if not cache_leaf.is_dir():
        raise VerificationError(f"Workshop cache leaf missing: {cache_leaf}")

    actual: dict[str, Path] = {}
    errors: list[str] = []
    for path in sorted(cache_leaf.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(cache_leaf).as_posix()
        if path.is_symlink():
            errors.append(f"cache symlink: {relative}")
        elif path.is_file():
            actual[relative] = path
        elif not path.is_dir():
            errors.append(f"unsupported cache entry: {relative}")

    item_id = str(manifest["workshop_item_id"])
    records: dict[str, dict[str, object]] = {}
    descriptor_state: dict[str, object] = {
        "policy": descriptor_policy,
        "remote_file_id": None,
        "canonical_rebuild_required": descriptor_policy == "launcher-injected",
    }
    for entry in manifest["files"]:
        relative = str(entry["path"])
        path = actual.pop(relative, None)
        if path is None:
            errors.append(f"cache missing: {relative}")
            continue
        data = path.read_bytes()
        digest = release.sha256_bytes(data)
        mode = "canonical"
        if relative == "descriptor.mod" and descriptor_policy == "launcher-injected":
            mode = "launcher-injected"
            if not release.workshop_descriptor_matches(path, entry, item_id):
                errors.append("cache descriptor.mod is not the exact permitted launcher injection")
            else:
                descriptor_state["remote_file_id"] = _remote_file_id(data)
        else:
            if len(data) != entry["size"] or digest != entry["sha256"]:
                errors.append(f"cache content mismatch: {relative}")
            if relative == "descriptor.mod" and b"remote_file_id" in data:
                errors.append("canonical cache descriptor.mod contains remote_file_id")
        records[relative] = {"size": len(data), "sha256": digest, "mode": mode}

    errors.extend(f"cache extra: {relative}" for relative in sorted(actual))
    if errors:
        raise VerificationError("Workshop cache verification failed:\n" + "\n".join(errors))
    return records, descriptor_state


def verify_workshop_cache(
    *,
    cache_leaf: Path,
    manifest_path: Path,
    archive_path: Path,
    descriptor_policy: str,
) -> dict[str, object]:
    """Return a machine-readable GREEN report or raise ``VerificationError``."""
    cache_leaf = _resolved(cache_leaf)
    manifest_path = _resolved(manifest_path)
    archive_path = _resolved(archive_path)
    if not manifest_path.is_file():
        raise VerificationError(f"formal manifest missing: {manifest_path}")

    try:
        manifest = _formal_manifest(cache_leaf, manifest_path)
        archive_records = _verify_archive(archive_path, manifest)
        cache_records, descriptor = _verify_cache(
            cache_leaf, manifest, descriptor_policy
        )
    except VerificationError:
        raise
    except (OSError, RuntimeError, UnicodeError, ValueError, zipfile.BadZipFile) as error:
        raise VerificationError(str(error)) from error
    files: list[dict[str, object]] = []
    for entry in manifest["files"]:
        relative = str(entry["path"])
        files.append(
            {
                "path": relative,
                "expected_size": entry["size"],
                "expected_sha256": entry["sha256"],
                "archive_size": archive_records[relative]["size"],
                "archive_sha256": archive_records[relative]["sha256"],
                "cache_size": cache_records[relative]["size"],
                "cache_sha256": cache_records[relative]["sha256"],
                "cache_match_mode": cache_records[relative]["mode"],
            }
        )

    return {
        "format_version": REPORT_FORMAT_VERSION,
        "kind": REPORT_KIND,
        "result": "GREEN",
        "errors": [],
        "cache_leaf": str(cache_leaf),
        "descriptor": descriptor,
        "manifest": {
            **_input_record(manifest_path),
            "product_id": manifest["product_id"],
            "mod_version": manifest["mod_version"],
            "git_sha": manifest["git_sha"],
            "git_tag": manifest["git_tag"],
            "workshop_item_id": manifest["workshop_item_id"],
        },
        "archive": {
            **_input_record(archive_path),
            "file_count": len(archive_records),
            "canonical_descriptor_has_remote_file_id": False,
        },
        "cache": {"file_count": len(cache_records)},
        "files": files,
    }


def _red_report(
    *,
    cache_leaf: Path,
    manifest_path: Path,
    archive_path: Path,
    descriptor_policy: str,
    error: BaseException,
) -> dict[str, object]:
    return {
        "format_version": REPORT_FORMAT_VERSION,
        "kind": REPORT_KIND,
        "result": "RED",
        "errors": [str(error)],
        "cache_leaf": str(_resolved(cache_leaf)),
        "descriptor": {
            "policy": descriptor_policy,
            "canonical_rebuild_required": descriptor_policy == "launcher-injected",
        },
        "manifest": _input_record(manifest_path),
        "archive": _input_record(archive_path),
        "cache": {},
        "files": [],
    }


def _json_bytes(payload: dict[str, object]) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _write_report(path: Path, payload: dict[str, object], cache_leaf: Path) -> None:
    path = _resolved(path)
    cache_leaf = _resolved(cache_leaf)
    if path == cache_leaf or cache_leaf in path.parents:
        raise VerificationError("report path must remain outside the verified cache leaf")
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _json_bytes(payload)
    if path.exists():
        if path.is_file() and path.read_bytes() == data:
            return
        raise VerificationError(f"refusing to overwrite existing report: {path}")
    path.write_bytes(data)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--cache-leaf", type=Path, required=True)
    result.add_argument("--manifest", type=Path, required=True)
    result.add_argument("--zip", dest="archive", type=Path, required=True)
    result.add_argument(
        "--descriptor-policy", choices=DESCRIPTOR_POLICIES, required=True
    )
    result.add_argument("--report", type=Path)
    return result


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    try:
        payload = verify_workshop_cache(
            cache_leaf=arguments.cache_leaf,
            manifest_path=arguments.manifest,
            archive_path=arguments.archive,
            descriptor_policy=arguments.descriptor_policy,
        )
        if arguments.report is not None:
            _write_report(arguments.report, payload, arguments.cache_leaf)
    except (
        OSError,
        RuntimeError,
        UnicodeError,
        ValueError,
        zipfile.BadZipFile,
    ) as error:
        payload = _red_report(
            cache_leaf=arguments.cache_leaf,
            manifest_path=arguments.manifest,
            archive_path=arguments.archive,
            descriptor_policy=arguments.descriptor_policy,
            error=error,
        )
        if arguments.report is not None:
            try:
                _write_report(arguments.report, payload, arguments.cache_leaf)
            except (OSError, ValueError) as report_error:
                payload["errors"].append(f"report write failed: {report_error}")
        sys.stdout.write(_json_bytes(payload).decode("ascii"))
        return EXIT_RED
    sys.stdout.write(_json_bytes(payload).decode("ascii"))
    return EXIT_GREEN


if __name__ == "__main__":
    raise SystemExit(main())
