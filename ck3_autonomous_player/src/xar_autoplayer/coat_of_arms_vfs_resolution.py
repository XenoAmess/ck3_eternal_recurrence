"""Bounded direct-DDS winner projection over a live CK3 mount receipt.

This module deliberately does not claim to call CK3's internal resolver. It
combines the exact-build, private mounted-data observer with byte-level source
inspection and the separately proven later-mount precedence for direct DDS
assets. Unsupported or incomplete mounts fail closed.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
from typing import Final
import zipfile

from .coat_of_arms_resources import (
    CK3_COAT_OF_ARMS_RESOURCE_CATALOG_V1_BUILD,
    CK3_COAT_OF_ARMS_RESOURCE_CATALOG_V1_EXE_SHA256,
    _sha256,
)


_MAX_MOUNTS: Final = 128
_MAX_ARCHIVE_MEMBERS: Final = 50_000
_MAX_ASSET_BYTES: Final = 16 * 1024 * 1024
_ALLOWED_PREFIXES: Final = (
    "gfx/coat_of_arms/patterns/",
    "gfx/coat_of_arms/colored_emblems/",
    "gfx/coat_of_arms/textured_emblems/",
)


class CoatOfArmsVfsResolutionError(RuntimeError):
    """Raised when a live receipt cannot support a closed projection."""


def _normalized_logical_path(value: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 512:
        raise ValueError("logical_path must contain 1 to 512 characters")
    if "\\" in value or value.startswith("/") or value.endswith("/"):
        raise ValueError("logical_path must be a relative POSIX path")
    path = PurePosixPath(value)
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("logical_path contains an unsafe segment")
    normalized = path.as_posix()
    if normalized != value:
        raise ValueError("logical_path must already be normalized")
    if not normalized.casefold().startswith(
        tuple(prefix.casefold() for prefix in _ALLOWED_PREFIXES)
    ) or path.suffix.casefold() != ".dds":
        raise ValueError(
            "logical_path must be a direct CK3 coat-of-arms DDS asset"
        )
    return normalized


def _live_mount_rows(diagnostics: object) -> list[dict[str, object]]:
    if not isinstance(diagnostics, dict):
        raise CoatOfArmsVfsResolutionError("bridge diagnostics are unavailable")
    hello = diagnostics.get("hello")
    if not isinstance(hello, dict):
        raise CoatOfArmsVfsResolutionError("exact-build hello is unavailable")
    if (
        diagnostics.get("connected") is not True
        or hello.get("ck3_build_match") is not True
        or hello.get("expected_ck3_sha256")
        != CK3_COAT_OF_ARMS_RESOURCE_CATALOG_V1_EXE_SHA256
    ):
        raise CoatOfArmsVfsResolutionError(
            "bridge is not connected to the frozen exact CK3 build"
        )
    private = diagnostics.get("private_observers")
    observer = (
        private.get("physfs_mounted_data_observer_v1")
        if isinstance(private, dict)
        else None
    )
    if not isinstance(observer, dict):
        raise CoatOfArmsVfsResolutionError(
            "physfs mounted-data observer is unavailable"
        )
    rows = observer.get("rows")
    if not isinstance(rows, list) or not 0 < len(rows) <= _MAX_MOUNTS:
        raise CoatOfArmsVfsResolutionError(
            "mounted-data rows are empty or exceed the bounded contract"
        )
    count = observer.get("call_count")
    success = observer.get("success_count")
    failure = observer.get("failure_count")
    row_count = observer.get("row_count")
    if not (
        observer.get("installed") is True
        and observer.get("failure_flags") == 0
        and observer.get("slot_overwrite_count") == 0
        and count == success == row_count == len(rows)
        and failure == 0
    ):
        raise CoatOfArmsVfsResolutionError(
            "mounted-data observer receipt is incomplete or lossy"
        )
    result: list[dict[str, object]] = []
    for expected_ordinal, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise CoatOfArmsVfsResolutionError("mounted-data row is not an object")
        path = row.get("path")
        if not (
            row.get("ordinal") == expected_ordinal
            and row.get("success") is True
            and isinstance(row.get("raw_result"), int)
            and not isinstance(row.get("raw_result"), bool)
            and int(row["raw_result"]) != 0
            and row.get("terminated") is True
            and row.get("null_pointer") is False
            and row.get("read_fault") is False
            and isinstance(path, str)
            and path
        ):
            raise CoatOfArmsVfsResolutionError(
                "mounted-data row is incomplete, truncated, or out of order"
            )
        result.append(row)
    return result


def _read_bounded_asset(path: Path) -> bytes:
    size = path.stat().st_size
    if not 128 <= size <= _MAX_ASSET_BYTES:
        raise CoatOfArmsVfsResolutionError(
            "mounted DDS is outside the bounded asset-size contract"
        )
    data = path.read_bytes()
    if len(data) != size or data[:4] != b"DDS ":
        raise CoatOfArmsVfsResolutionError("mounted asset is not a stable DDS")
    return data


def _dds_summary(data: bytes) -> dict[str, object]:
    return {
        "width": int.from_bytes(data[16:20], "little"),
        "height": int.from_bytes(data[12:16], "little"),
        "mipmap_count": max(1, int.from_bytes(data[28:32], "little")),
        "four_cc_hex": data[84:88].hex().upper(),
    }


def _source_kind(source: Path, game_content_root: Path) -> str:
    normalized_source = Path(os.path.normcase(str(source.resolve())))
    normalized_game = Path(os.path.normcase(str(game_content_root.resolve())))
    normalized_dlc = Path(os.path.normcase(str((game_content_root / "dlc").resolve())))
    if normalized_source == normalized_game:
        return "base_game"
    if normalized_source.is_relative_to(normalized_dlc):
        return "dlc"
    return "external_mount"


def _directory_candidate(
    root: Path,
    logical_path: str,
    ordinal: int,
    game_content_root: Path,
) -> dict[str, object] | None:
    resolved_root = root.resolve()
    candidate = (resolved_root / Path(*PurePosixPath(logical_path).parts)).resolve()
    if not candidate.is_relative_to(resolved_root):
        raise CoatOfArmsVfsResolutionError(
            "mounted directory candidate escapes its source root"
        )
    if not candidate.exists():
        return None
    if not candidate.is_file():
        raise CoatOfArmsVfsResolutionError(
            "mounted direct-DDS candidate is not a regular file"
        )
    data = _read_bounded_asset(candidate)
    return {
        "mount_ordinal": ordinal,
        "source_kind": _source_kind(resolved_root, game_content_root),
        "source_path": str(resolved_root),
        "content_kind": "directory",
        "asset_relative_path": logical_path,
        "asset_bytes": len(data),
        "asset_sha256": hashlib.sha256(data).hexdigest().upper(),
        "dds": _dds_summary(data),
    }


def _archive_candidate(
    archive_path: Path,
    logical_path: str,
    ordinal: int,
) -> dict[str, object] | None:
    try:
        with zipfile.ZipFile(archive_path) as archive:
            members = [member for member in archive.infolist() if not member.is_dir()]
            if len(members) > _MAX_ARCHIVE_MEMBERS:
                raise CoatOfArmsVfsResolutionError(
                    "mounted archive exceeds the member-count contract"
                )
            by_folded_name: dict[str, list[zipfile.ZipInfo]] = {}
            for member in members:
                member_path = PurePosixPath(member.filename)
                if member_path.is_absolute() or ".." in member_path.parts:
                    raise CoatOfArmsVfsResolutionError(
                        "mounted archive contains an unsafe member path"
                    )
                by_folded_name.setdefault(
                    member_path.as_posix().casefold(), []
                ).append(member)
            matches = by_folded_name.get(logical_path.casefold(), [])
            if not matches:
                return None
            if len(matches) != 1:
                raise CoatOfArmsVfsResolutionError(
                    "mounted archive has ambiguous direct-DDS members"
                )
            member = matches[0]
            if not 128 <= member.file_size <= _MAX_ASSET_BYTES:
                raise CoatOfArmsVfsResolutionError(
                    "mounted archive DDS is outside the size contract"
                )
            data = archive.read(member)
    except zipfile.BadZipFile as error:
        raise CoatOfArmsVfsResolutionError(
            "mounted file is not a readable ZIP archive"
        ) from error
    if len(data) != member.file_size or data[:4] != b"DDS ":
        raise CoatOfArmsVfsResolutionError(
            "mounted archive member is not a stable DDS"
        )
    return {
        "mount_ordinal": ordinal,
        "source_kind": "external_archive_mount",
        "source_path": str(archive_path.resolve()),
        "content_kind": "archive",
        "asset_relative_path": member.filename,
        "asset_bytes": len(data),
        "asset_sha256": hashlib.sha256(data).hexdigest().upper(),
        "dds": _dds_summary(data),
    }


def project_coat_of_arms_vfs_asset_winner_v1(
    diagnostics: object,
    game_directory: str,
    logical_path: str,
) -> dict[str, object]:
    """Project one direct DDS winner from a complete live mount receipt."""

    if not isinstance(game_directory, str) or not game_directory.strip():
        raise ValueError("game_directory must be a non-empty string")
    logical = _normalized_logical_path(logical_path)
    game_root = Path(game_directory).expanduser().resolve()
    executable = game_root / "binaries" / "ck3.exe"
    if (
        not executable.is_file()
        or _sha256(executable)
        != CK3_COAT_OF_ARMS_RESOURCE_CATALOG_V1_EXE_SHA256
    ):
        raise CoatOfArmsVfsResolutionError(
            "game_directory is not the frozen exact CK3 build"
        )
    rows = _live_mount_rows(diagnostics)
    candidates: list[dict[str, object]] = []
    inspected_mounts: list[dict[str, object]] = []
    for row in rows:
        ordinal = int(row["ordinal"])
        source = Path(str(row["path"])).expanduser().resolve()
        if not source.exists():
            raise CoatOfArmsVfsResolutionError(
                "an observed mounted-data source no longer exists"
            )
        if source.is_dir():
            candidate = _directory_candidate(
                source, logical, ordinal, game_root / "game"
            )
            source_type = "directory"
        elif source.is_file():
            candidate = _archive_candidate(source, logical, ordinal)
            source_type = "archive"
        else:
            raise CoatOfArmsVfsResolutionError(
                "observed mounted-data source is not inspectable"
            )
        inspected_mounts.append(
            {
                "ordinal": ordinal,
                "path": str(source),
                "source_type": source_type,
                "candidate_present": candidate is not None,
            }
        )
        if candidate is not None:
            candidates.append(candidate)

    receipt_rows = [
        {
            "ordinal": int(row["ordinal"]),
            "path": str(row["path"]),
            "raw_result": int(row["raw_result"]),
        }
        for row in rows
    ]
    receipt_bytes = json.dumps(
        receipt_rows, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    winner = candidates[-1] if candidates else None
    return {
        "schema": "ck3-coat-of-arms-vfs-asset-winner-projection-v1",
        "schema_version": 1,
        "status": (
            "projected_direct_asset_winner"
            if winner is not None
            else "not_found_in_inspectable_mounts"
        ),
        "ck3_build": CK3_COAT_OF_ARMS_RESOURCE_CATALOG_V1_BUILD,
        "logical_path": logical,
        "mount_count": len(rows),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "winner": winner,
        "inspected_mounts": inspected_mounts,
        "provenance": {
            "mode": "live-mount-receipt-plus-static-byte-projection",
            "mount_observer": "physfs_mounted_data_observer_v1",
            "mount_receipt_sha256": hashlib.sha256(receipt_bytes)
            .hexdigest()
            .upper(),
            "executable_sha256": CK3_COAT_OF_ARMS_RESOURCE_CATALOG_V1_EXE_SHA256,
            "mount_order_observed": True,
            "source_bytes_observed": True,
            "later_mount_precedence_contract": (
                "exact_1.19.0.6_direct_dds_r22_r23"
            ),
            "engine_resolver_called": False,
            "resource_registration_observed": False,
            "replace_path_applied": False,
            "definition_merge_applied": False,
            "claim_scope": "direct_dds_path_winner_projection_only",
        },
    }
