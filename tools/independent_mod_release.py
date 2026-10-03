#!/usr/bin/env python3
"""Deterministic runtime projection for independent original and maintained CK3 mods.

Product wrappers own feature validation, tag creation and publication. This
module only accepts an explicit runtime inventory and verifies its exact bytes.
Every build uses a new output directory and keeps any failed partial output.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tempfile
from typing import Iterable
import zipfile


ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
UTF8_BOM = b"\xef\xbb\xbf"
BOM_SUFFIXES = frozenset({".txt", ".gui", ".yml"})
TEXT_SUFFIXES = BOM_SUFFIXES | {".mod", ".json", ".csv", ".lua", ".asset", ".gfx", ".sfx"}
SOURCE_ONLY_DIRECTORIES = frozenset({"docs", "tools"})
SOURCE_ONLY_FILES = frozenset({"README.md"})
PRODUCT_ID = re.compile(r"[a-z][a-z0-9_]*", re.ASCII)
VERSION = re.compile(r"[0-9]+(?:\.[0-9]+){0,3}(?:[-+][A-Za-z0-9.-]+)?", re.ASCII)
REVISION = re.compile(r"[0-9a-f]{40}", re.ASCII)
DIGEST = re.compile(r"[0-9a-f]{64}", re.ASCII)
ITEM_ID = re.compile(r"[1-9][0-9]*", re.ASCII)


def _relative_path(raw: str) -> str:
    if not isinstance(raw, str) or not raw or "\\" in raw or ":" in raw:
        raise ValueError(f"runtime path must be a relative POSIX path: {raw!r}")
    path = PurePosixPath(raw)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in raw.split("/")):
        raise ValueError(f"runtime path is not canonical: {raw!r}")
    if path.as_posix() != raw:
        raise ValueError(f"runtime path is not canonical: {raw!r}")
    return raw


def _item_id(value: str | None, upstream_item_id: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or ITEM_ID.fullmatch(value) is None or int(value) > 2**64 - 1:
        raise ValueError("Workshop item ID must be a canonical positive uint64 decimal string")
    if value == upstream_item_id:
        raise ValueError("maintained edition must not reuse the upstream Workshop item ID")
    return value


@dataclass(frozen=True)
class ProductSpec:
    product_id: str
    source: Path
    runtime_files: frozenset[str] | Iterable[str]
    upstream_item_id: str | None
    tag_prefix: str

    def __post_init__(self) -> None:
        if not isinstance(self.product_id, str) or PRODUCT_ID.fullmatch(self.product_id) is None:
            raise ValueError("product_id must be a lowercase ASCII identifier")
        if self.upstream_item_id is not None:
            if not isinstance(self.upstream_item_id, str) or ITEM_ID.fullmatch(self.upstream_item_id) is None:
                raise ValueError("upstream_item_id must be None for originals or a canonical positive decimal string")
            if int(self.upstream_item_id) > 2**64 - 1:
                raise ValueError("upstream_item_id exceeds uint64")
        if not isinstance(self.tag_prefix, str) or not self.tag_prefix or any(c.isspace() for c in self.tag_prefix):
            raise ValueError("tag_prefix must be a nonempty string without whitespace")
        if isinstance(self.runtime_files, (str, bytes)):
            raise ValueError("runtime_files must be an explicit collection of relative paths")
        paths = tuple(_relative_path(path) for path in self.runtime_files)
        if not paths or "descriptor.mod" not in paths:
            raise ValueError("runtime_files must include descriptor.mod")
        if len({path.casefold() for path in paths}) != len(paths):
            raise ValueError("runtime_files contains duplicate or case-colliding paths")
        if any(PurePosixPath(path).parts[0] in SOURCE_ONLY_DIRECTORIES or path in SOURCE_ONLY_FILES for path in paths):
            raise ValueError("README.md, docs and tools are source-only")
        object.__setattr__(self, "source", Path(self.source))
        object.__setattr__(self, "runtime_files", frozenset(paths))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _link(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def _inventory(root: Path) -> tuple[dict[str, Path], set[str]]:
    if not root.is_dir() or _link(root):
        raise ValueError(f"tree root must be an existing ordinary directory: {root}")
    files: dict[str, Path] = {}
    directories: set[str] = set()
    for path in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        if _link(path):
            raise ValueError(f"links are forbidden: {relative}")
        if path.is_file():
            files[relative] = path
        elif path.is_dir():
            directories.add(relative)
        else:
            raise ValueError(f"unsupported filesystem entry: {relative}")
    return files, directories


def runtime_directories(spec: ProductSpec) -> set[str]:
    result: set[str] = set()
    for relative in spec.runtime_files:
        for parent in PurePosixPath(relative).parents:
            if parent != PurePosixPath("."):
                result.add(parent.as_posix())
    return result


def _source_only(relative: str) -> bool:
    return relative in SOURCE_ONLY_FILES or PurePosixPath(relative).parts[0] in SOURCE_ONLY_DIRECTORIES


def _runtime_text_errors(spec: ProductSpec, relative: str, data: bytes) -> list[str]:
    suffix = PurePosixPath(relative).suffix.lower()
    if relative != "descriptor.mod" and suffix not in TEXT_SUFFIXES:
        return []
    errors: list[str] = []
    if relative == "descriptor.mod" and data.startswith(UTF8_BOM):
        errors.append("descriptor.mod must not have a UTF-8 BOM")
    elif suffix in BOM_SUFFIXES and not data.startswith(UTF8_BOM):
        errors.append(f"runtime script/localization lacks UTF-8 BOM: {relative}")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return errors + [f"runtime text is not UTF-8: {relative}"]
    if "remote_file_id" in text:
        errors.append(f"canonical runtime contains remote_file_id: {relative}")
    if spec.upstream_item_id is not None and re.search(r"(?<![0-9])" + re.escape(spec.upstream_item_id) + r"(?![0-9])", text):
        errors.append(f"upstream Workshop identity leaked into runtime: {relative}")
    return errors


def source_errors(spec: ProductSpec) -> list[str]:
    try:
        files, directories = _inventory(spec.source)
    except (OSError, ValueError) as error:
        return [str(error)]
    errors = [f"missing runtime file: {path}" for path in sorted(spec.runtime_files - files.keys())]
    errors.extend(f"file outside allowlist: {path}" for path in files if path not in spec.runtime_files and not _source_only(path))
    allowed_directories = runtime_directories(spec)
    errors.extend(f"directory outside allowlist: {path}/" for path in sorted(directories) if path not in allowed_directories and not _source_only(path))
    for relative in sorted(spec.runtime_files & files.keys()):
        errors.extend(_runtime_text_errors(spec, relative, files[relative].read_bytes()))
    try:
        descriptor_version(spec.source)
    except (OSError, UnicodeError, ValueError) as error:
        errors.append(str(error))
    return errors


def descriptor_version(source: Path) -> str:
    value = (Path(source) / "descriptor.mod").read_text(encoding="utf-8-sig")
    matches = re.findall(r'(?m)^[ \t]*version[ \t]*=[ \t]*"([^"\r\n]+)"[ \t]*(?:#[^\r\n]*)?$', value)
    if len(matches) != 1 or VERSION.fullmatch(matches[0]) is None:
        raise ValueError("descriptor.mod requires exactly one numeric version")
    return matches[0]


def product_tag(spec: ProductSpec, version: str) -> str:
    if not isinstance(version, str) or VERSION.fullmatch(version) is None:
        raise ValueError("invalid mod version")
    return spec.tag_prefix + version


def build(
    spec: ProductSpec,
    output: Path,
    revision: str,
    workshop_item_id: str | None = None,
    *,
    git_tag: str | None = None,
) -> tuple[Path, Path, Path, dict[str, object]]:
    errors = source_errors(spec)
    if errors:
        raise ValueError("invalid product source:\n" + "\n".join(errors))
    if not isinstance(revision, str) or REVISION.fullmatch(revision) is None:
        raise ValueError("revision must be a full lowercase Git commit SHA")
    item = _item_id(workshop_item_id, spec.upstream_item_id)
    version = descriptor_version(spec.source)
    if git_tag not in {None, product_tag(spec, version)}:
        raise ValueError("git_tag does not match the product version")
    source = spec.source.resolve()
    if _link(Path(output)):
        raise ValueError("build output must not be a link")
    staging = Path(output).resolve()
    if source == staging or source in staging.parents or staging in source.parents:
        raise ValueError("source and staging must not contain one another")
    manifest_path = staging.with_name(staging.name + ".manifest.json")
    archive_path = staging.with_name(staging.name + ".zip")
    for path in (staging, manifest_path, archive_path):
        if path.exists() or _link(path):
            raise ValueError(f"build output already exists; use a new attempt: {path}")
    staging.mkdir(parents=True)
    entries: list[dict[str, object]] = []
    for relative in sorted(spec.runtime_files):
        data = (source / PurePosixPath(relative)).read_bytes()
        # Recheck the bytes actually copied, in case source changed after preflight.
        errors = _runtime_text_errors(spec, relative, data)
        if errors:
            raise ValueError("\n".join(errors))
        target = staging / PurePosixPath(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        entries.append({"path": relative, "size": len(data), "sha256": sha256_bytes(data)})
    if descriptor_version(staging) != version:
        raise ValueError("descriptor version changed during build")
    payload: dict[str, object] = {
        "format_version": 1,
        "product_id": spec.product_id,
        "mod_version": version,
        "git_tag": git_tag,
        "git_sha": revision,
        "workshop_item_id": item,
        "files": entries,
    }
    manifest_path.write_bytes((json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    with zipfile.ZipFile(archive_path, "w") as archive:
        for entry in entries:
            relative = str(entry["path"])
            info = zipfile.ZipInfo(f"{spec.product_id}/{relative}", ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (staging / PurePosixPath(relative)).read_bytes(), compresslevel=9)
    verify_manifest(spec, staging, manifest_path)
    return staging, manifest_path, archive_path, payload


def check_reproducible(
    spec: ProductSpec, revision: str, workshop_item_id: str | None = None
) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix=spec.product_id + "-release-check-") as temporary:
        root = Path(temporary)
        first = build(spec, root / "one" / spec.product_id, revision, workshop_item_id)
        second = build(spec, root / "two" / spec.product_id, revision, workshop_item_id)
        if first[1].read_bytes() != second[1].read_bytes():
            raise ValueError("manifest is not byte reproducible")
        if first[2].read_bytes() != second[2].read_bytes():
            raise ValueError("ZIP is not byte reproducible")
        return {
            "file_count": len(spec.runtime_files),
            "manifest_sha256": sha256_file(first[1]),
            "zip_sha256": sha256_file(first[2]),
        }


def load_manifest(spec: ProductSpec, manifest_path: Path) -> dict[str, object]:
    payload = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    fields = {"format_version", "product_id", "mod_version", "git_tag", "git_sha", "workshop_item_id", "files"}
    if not isinstance(payload, dict) or set(payload) != fields:
        raise ValueError("manifest fields mismatch")
    if type(payload["format_version"]) is not int or payload["format_version"] != 1 or payload["product_id"] != spec.product_id:
        raise ValueError("manifest product identity mismatch")
    version = payload["mod_version"]
    if not isinstance(version, str) or VERSION.fullmatch(version) is None:
        raise ValueError("manifest mod version is invalid")
    if payload["git_tag"] is not None and (
        not isinstance(payload["git_tag"], str) or payload["git_tag"] != product_tag(spec, version)
    ):
        raise ValueError("manifest Git tag is invalid")
    if not isinstance(payload["git_sha"], str) or REVISION.fullmatch(payload["git_sha"]) is None:
        raise ValueError("manifest Git revision is invalid")
    _item_id(payload["workshop_item_id"], spec.upstream_item_id)
    entries = payload["files"]
    if not isinstance(entries, list):
        raise ValueError("manifest files must be a list")
    paths = []
    for entry in entries:
        if (not isinstance(entry, dict) or set(entry) != {"path", "size", "sha256"}
                or not isinstance(entry["path"], str) or type(entry["size"]) is not int
                or entry["size"] < 0 or not isinstance(entry["sha256"], str)
                or DIGEST.fullmatch(entry["sha256"]) is None):
            raise ValueError("manifest file entry is invalid")
        paths.append(_relative_path(entry["path"]))
    if paths != sorted(spec.runtime_files):
        raise ValueError("manifest runtime inventory mismatch")
    return payload


def verify_manifest(spec: ProductSpec, target: Path, manifest_path: Path) -> int:
    payload = load_manifest(spec, manifest_path)
    files, directories = _inventory(Path(target))
    errors = [f"extra file: {relative}" for relative in files.keys() - spec.runtime_files]
    errors.extend(f"extra directory: {relative}/" for relative in sorted(directories - runtime_directories(spec)))
    for entry in payload["files"]:
        relative = entry["path"]
        path = files.get(relative)
        if path is None:
            errors.append(f"missing: {relative}")
            continue
        data = path.read_bytes()
        if len(data) != entry["size"] or sha256_bytes(data) != entry["sha256"]:
            errors.append(f"mismatch: {relative}")
        errors.extend(_runtime_text_errors(spec, relative, data))
    try:
        if descriptor_version(Path(target)) != payload["mod_version"]:
            errors.append("manifest and descriptor versions differ")
    except (OSError, UnicodeError, ValueError) as error:
        errors.append(str(error))
    if errors:
        raise ValueError("manifest verification failed:\n" + "\n".join(sorted(errors)))
    return len(spec.runtime_files)
