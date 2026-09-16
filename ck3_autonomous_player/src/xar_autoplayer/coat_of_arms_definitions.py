"""Bounded exact-build source catalog for CK3 coat-of-arms definitions.

This module deliberately reports static source candidates rather than claiming
the engine's mounted VFS winner or materialized parent-inheritance semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
from typing import Final


CK3_COAT_OF_ARMS_DEFINITION_V1_BUILD: Final = "1.19.0.6"
CK3_COAT_OF_ARMS_DEFINITION_V1_EXE_SHA256: Final = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
_DEFINITION_DIRECTORY: Final = Path("game/common/coat_of_arms/coat_of_arms")
_MAX_FILE_BYTES: Final = 8 * 1024 * 1024
_MAX_TOTAL_BYTES: Final = 64 * 1024 * 1024
_MAX_SOURCE_BYTES: Final = 256 * 1024
_MAX_PAGE_SIZE: Final = 200
_MAX_ALIAS_DEPTH: Final = 32
_KEY = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")


class CoatOfArmsDefinitionCatalogError(RuntimeError):
    """Raised when exact-build source cannot satisfy the bounded contract."""


@dataclass(frozen=True, slots=True)
class _Token:
    value: str
    start: int
    end: int
    line: int


@dataclass(frozen=True, slots=True)
class _Occurrence:
    key: str
    kind: str
    alias_target: str | None
    relative_path: str
    source: str
    source_line_start: int
    source_line_end: int
    source_ordinal: int
    file_bytes: int
    file_sha256: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _game_root(game_directory: str) -> tuple[Path, str]:
    if not isinstance(game_directory, str) or not game_directory.strip():
        raise ValueError("game_directory must be a non-empty string")
    root = Path(game_directory).expanduser().resolve()
    executable = root / "binaries" / "ck3.exe"
    directory = root / _DEFINITION_DIRECTORY
    if not executable.is_file() or not directory.is_dir():
        raise CoatOfArmsDefinitionCatalogError(
            "game_directory lacks the CK3 executable or CoA definition directory"
        )
    executable_sha256 = _sha256(executable)
    if executable_sha256 != CK3_COAT_OF_ARMS_DEFINITION_V1_EXE_SHA256:
        raise CoatOfArmsDefinitionCatalogError(
            "CK3 executable does not match the frozen 1.19.0.6 definition build"
        )
    return root, executable_sha256


def _tokens(text: str, label: str) -> tuple[_Token, ...]:
    result: list[_Token] = []
    index = 0
    line = 1
    while index < len(text):
        character = text[index]
        if character in " \t\r":
            index += 1
            continue
        if character == "\n":
            line += 1
            index += 1
            continue
        if character == "#":
            while index < len(text) and text[index] != "\n":
                index += 1
            continue
        if character in "{}=":
            result.append(_Token(character, index, index + 1, line))
            index += 1
            continue
        start = index
        start_line = line
        if character == '"':
            index += 1
            value: list[str] = []
            while index < len(text) and text[index] != '"':
                if text[index] in "\r\n":
                    raise CoatOfArmsDefinitionCatalogError(
                        f"{label}:{start_line}: unterminated string"
                    )
                if text[index] == "\\" and index + 1 < len(text):
                    index += 1
                value.append(text[index])
                index += 1
            if index >= len(text):
                raise CoatOfArmsDefinitionCatalogError(
                    f"{label}:{start_line}: unterminated string"
                )
            index += 1
            result.append(_Token("".join(value), start, index, start_line))
            continue
        while index < len(text) and text[index] not in " \t\r\n#{}=\"":
            index += 1
        if start == index:
            raise CoatOfArmsDefinitionCatalogError(
                f"{label}:{line}: unsupported source character"
            )
        result.append(_Token(text[start:index], start, index, start_line))
    return tuple(result)


def _scan_file(path: Path, relative_path: str) -> list[_Occurrence]:
    size = path.stat().st_size
    if size <= 0 or size > _MAX_FILE_BYTES:
        raise CoatOfArmsDefinitionCatalogError(
            f"definition source {relative_path} is outside the file-size contract"
        )
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeError as error:
        raise CoatOfArmsDefinitionCatalogError(
            f"definition source {relative_path} is not UTF-8"
        ) from error
    tokens = _tokens(text, relative_path)
    file_sha256 = _sha256(path)
    result: list[_Occurrence] = []
    index = 0
    ordinal = 0
    while index < len(tokens):
        key = tokens[index]
        if index + 2 >= len(tokens) or tokens[index + 1].value != "=":
            raise CoatOfArmsDefinitionCatalogError(
                f"{relative_path}:{key.line}: expected top-level key = value"
            )
        value = tokens[index + 2]
        if value.value == "{":
            depth = 1
            cursor = index + 3
            while cursor < len(tokens) and depth:
                if tokens[cursor].value == "{":
                    depth += 1
                elif tokens[cursor].value == "}":
                    depth -= 1
                cursor += 1
            if depth:
                raise CoatOfArmsDefinitionCatalogError(
                    f"{relative_path}:{value.line}: unterminated top-level block"
                )
            last = tokens[cursor - 1]
            end = last.end
            end_line = last.line
            kind = "block"
            alias_target = None
            index = cursor
        elif value.value in "}=":
            raise CoatOfArmsDefinitionCatalogError(
                f"{relative_path}:{value.line}: invalid top-level scalar"
            )
        else:
            end = value.end
            end_line = value.line
            kind = "alias" if _KEY.fullmatch(value.value) else "scalar"
            alias_target = value.value if kind == "alias" else None
            index += 3
        if not key.value.startswith("@"):
            source = text[key.start:end]
            source_bytes = len(source.encode("utf-8"))
            if source_bytes > _MAX_SOURCE_BYTES:
                raise CoatOfArmsDefinitionCatalogError(
                    f"definition {key.value} exceeds the source-size contract"
                )
            result.append(
                _Occurrence(
                    key=key.value,
                    kind=kind,
                    alias_target=alias_target,
                    relative_path=relative_path,
                    source=source,
                    source_line_start=key.line,
                    source_line_end=end_line,
                    source_ordinal=ordinal,
                    file_bytes=size,
                    file_sha256=file_sha256,
                )
            )
            ordinal += 1
    return result


def _catalog(game_directory: str) -> tuple[list[_Occurrence], dict[str, object]]:
    root, executable_sha256 = _game_root(game_directory)
    source_root = root / _DEFINITION_DIRECTORY
    files = sorted(
        (path for path in source_root.rglob("*.txt") if path.is_file()),
        key=lambda path: path.relative_to(root).as_posix().casefold(),
    )
    total_bytes = sum(path.stat().st_size for path in files)
    if not files or total_bytes > _MAX_TOTAL_BYTES:
        raise CoatOfArmsDefinitionCatalogError(
            "CoA definition source set is empty or outside the total-size contract"
        )
    occurrences: list[_Occurrence] = []
    file_receipts: list[dict[str, object]] = []
    manifest_digest = hashlib.sha256()
    for path in files:
        relative_path = path.relative_to(root).as_posix()
        file_sha256 = _sha256(path)
        manifest_digest.update(relative_path.encode("utf-8"))
        manifest_digest.update(b"\0")
        manifest_digest.update(file_sha256.encode("ascii"))
        manifest_digest.update(b"\n")
        file_receipts.append(
            {
                "relative_path": relative_path,
                "bytes": path.stat().st_size,
                "sha256": file_sha256,
            }
        )
        occurrences.extend(_scan_file(path, relative_path))
    return occurrences, {
        "mode": "base-game-coat-of-arms-definition-source-static",
        "executable_sha256": executable_sha256,
        "definition_directory": _DEFINITION_DIRECTORY.as_posix(),
        "source_files": len(files),
        "source_bytes": total_bytes,
        "source_manifest_sha256": manifest_digest.hexdigest().upper(),
        "file_receipts": file_receipts,
        "engine_mount_observed": False,
        "engine_parent_composition_observed": False,
        "dlc_and_mod_overrides_included": False,
    }


def _occurrence_receipt(value: _Occurrence, *, include_source: bool) -> dict[str, object]:
    source_bytes = value.source.encode("utf-8")
    result: dict[str, object] = {
        "key": value.key,
        "kind": value.kind,
        "alias_target": value.alias_target,
        "relative_path": value.relative_path,
        "source_line_start": value.source_line_start,
        "source_line_end": value.source_line_end,
        "source_ordinal": value.source_ordinal,
        "source_bytes": len(source_bytes),
        "source_sha256": hashlib.sha256(source_bytes).hexdigest().upper(),
        "file_bytes": value.file_bytes,
        "file_sha256": value.file_sha256,
    }
    if include_source:
        result["source_utf8"] = value.source
    return result


def query_coat_of_arms_definition_catalog_v1(
    game_directory: str,
    *,
    query: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> dict[str, object]:
    """Return one bounded page of unique base-game CoA definition keys."""

    if query is not None and (not isinstance(query, str) or len(query) > 128):
        raise ValueError("query must be null or a string of at most 128 characters")
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise ValueError("offset must be a non-negative integer")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= _MAX_PAGE_SIZE:
        raise ValueError(f"limit must be between 1 and {_MAX_PAGE_SIZE}")
    occurrences, provenance = _catalog(game_directory)
    by_key: dict[str, list[_Occurrence]] = {}
    for occurrence in occurrences:
        by_key.setdefault(occurrence.key, []).append(occurrence)
    needle = (query or "").strip().casefold()
    keys = sorted(
        (key for key in by_key if not needle or needle in key.casefold()),
        key=str.casefold,
    )
    selected = keys[offset : offset + limit]
    items = []
    for key in selected:
        candidates = by_key[key]
        items.append(
            {
                "key": key,
                "candidate_count": len(candidates),
                "kinds": sorted({candidate.kind for candidate in candidates}),
                "alias_targets": sorted({
                    candidate.alias_target
                    for candidate in candidates
                    if candidate.alias_target is not None
                }),
                "candidates": [
                    _occurrence_receipt(candidate, include_source=False)
                    for candidate in candidates
                ],
            }
        )
    next_offset = offset + len(selected)
    return {
        "schema": "ck3-coat-of-arms-definition-catalog-v1",
        "schema_version": 1,
        "status": "indexed",
        "ck3_build": CK3_COAT_OF_ARMS_DEFINITION_V1_BUILD,
        "query": query,
        "offset": offset,
        "limit": limit,
        "total": len(keys),
        "returned": len(items),
        "has_more": next_offset < len(keys),
        "next_offset": next_offset if next_offset < len(keys) else None,
        "items": items,
        "provenance": provenance,
    }


def read_coat_of_arms_definition_v1(
    game_directory: str,
    key: str,
) -> dict[str, object]:
    """Read exact source candidates and resolve only unambiguous alias chains."""

    if not isinstance(key, str) or not _KEY.fullmatch(key):
        raise ValueError("key must be a supported identifier of at most 128 characters")
    occurrences, provenance = _catalog(game_directory)
    by_key: dict[str, list[_Occurrence]] = {}
    for occurrence in occurrences:
        by_key.setdefault(occurrence.key, []).append(occurrence)
    direct = by_key.get(key, [])
    chain: list[dict[str, object]] = []
    seen: set[str] = set()
    current = key
    status = "missing"
    resolved: _Occurrence | None = None
    for _ in range(_MAX_ALIAS_DEPTH):
        if current in seen:
            status = "alias_cycle"
            break
        seen.add(current)
        candidates = by_key.get(current, [])
        if not candidates:
            status = "missing" if current == key else "alias_target_missing"
            break
        if len(candidates) != 1:
            status = "ambiguous_source_candidates"
            chain.append({"key": current, "candidate_count": len(candidates)})
            break
        candidate = candidates[0]
        chain.append(_occurrence_receipt(candidate, include_source=True))
        if candidate.kind == "block":
            status = "resolved_block"
            resolved = candidate
            break
        if candidate.kind != "alias" or candidate.alias_target is None:
            status = "unsupported_scalar"
            break
        current = candidate.alias_target
    else:
        status = "alias_depth_exceeded"
    return {
        "schema": "ck3-coat-of-arms-definition-v1",
        "schema_version": 1,
        "status": status,
        "ck3_build": CK3_COAT_OF_ARMS_DEFINITION_V1_BUILD,
        "requested_key": key,
        "direct_candidate_count": len(direct),
        "direct_candidates": [
            _occurrence_receipt(candidate, include_source=True)
            for candidate in direct
        ],
        "alias_chain": chain,
        "resolved_key": resolved.key if resolved else None,
        "resolved_definition": (
            _occurrence_receipt(resolved, include_source=True) if resolved else None
        ),
        "provenance": {
            **provenance,
            "resolution_scope": "static base-game source and unambiguous aliases only",
            "variables_expanded": False,
            "parent_inheritance_materialized": False,
            "vfs_winner_claimed": False,
        },
    }
