"""Bounded, read-only inspection of CK3 saves in one configured profile.

The public MCP surface never accepts a filesystem path.  Its caller receives
only artifacts discovered below the profile bound when the server starts.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import re
import zipfile


SAVE_ARTIFACTS_SCHEMA_V1 = "xar.ck3.save-artifacts/v1"
MAX_SAVE_ARTIFACTS = 512
MAX_REPORTED_ZIP_MEMBERS = 128
_RAW_TEXT_SAVE_HEADER = re.compile(rb"^SAV[0-9A-Fa-f]+\r?\nmeta_data=\{")
_RAW_BINARY_SAVE_HEADER = re.compile(
    rb"^SAV[0-9A-Fa-f]+\r?\nU1\x01\x00\x03\x00"
)


class SaveArtifactError(RuntimeError):
    """A configured CK3 save root or artifact cannot be inspected safely."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect_ck3_save_artifact_v1(path: Path, *, profile_dir: Path) -> dict[str, object]:
    """Inspect one already-selected save without accepting an external root."""

    root = profile_dir.resolve()
    resolved = path.resolve()
    if not resolved.is_relative_to(root):
        raise SaveArtifactError("CK3 save artifact escapes the configured profile")
    if path.is_symlink():
        raise SaveArtifactError("CK3 save artifact cannot be a symbolic link")
    size = path.stat().st_size
    row: dict[str, object] = {
        "name": path.name,
        "relative_path": path.relative_to(profile_dir).as_posix(),
        "bytes": size,
        "sha256": _sha256(path),
    }
    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            bad_member = archive.testzip()
            has_gamestate = any(member.filename == "gamestate" for member in members)
            reported = members[:MAX_REPORTED_ZIP_MEMBERS]
            row.update(
                {
                    "format": "zip-ck3",
                    "integrity_scope": "zip-crc",
                    "integrity_ok": bad_member is None and has_gamestate,
                    "zip_valid": bad_member is None,
                    "bad_member": bad_member,
                    "has_gamestate": has_gamestate,
                    "member_count": len(members),
                    "members_truncated": len(members) > len(reported),
                    "members": [
                        {
                            "name": member.filename,
                            "bytes": member.file_size,
                            "compressed_bytes": member.compress_size,
                            "crc32": f"{member.CRC:08x}",
                            "compression": member.compress_type,
                            "flags": member.flag_bits,
                        }
                        for member in reported
                    ],
                }
            )
            return row
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile) as error:
        with path.open("rb") as source:
            header = source.read(96)
        raw_header_kind: str | None = None
        if _RAW_TEXT_SAVE_HEADER.match(header) is not None:
            raw_header_kind = "text"
        elif _RAW_BINARY_SAVE_HEADER.match(header) is not None:
            raw_header_kind = "binary"
        raw_header_valid = raw_header_kind is not None
        row.update(
            {
                "format": "raw-ck3" if raw_header_valid else "unknown",
                "integrity_scope": "header-only" if raw_header_valid else "none",
                "integrity_ok": None,
                "raw_header_valid": raw_header_valid,
                "raw_header_kind": raw_header_kind,
                "zip_valid": False,
                "bad_member": None,
                "has_gamestate": None,
                "format_probe_error": type(error).__name__,
            }
        )
        return row


def require_seedable_ck3_save_v1(artifact: dict[str, object]) -> None:
    """Require a recognized save while preserving CK3's legal raw format.

    ZIP saves have an internal integrity mechanism and must contain the
    canonical ``gamestate`` member.  Raw saves expose no equivalent checksum;
    callers must pair their header-only format recognition with the full-file
    byte count and SHA-256 already returned by this module.
    """

    format_name = artifact.get("format")
    if format_name == "zip-ck3":
        if artifact.get("zip_valid") is not True or artifact.get("has_gamestate") is not True:
            raise SaveArtifactError(
                "ZIP CK3 seed must pass CRC validation and contain gamestate"
            )
        return
    if format_name == "raw-ck3" and artifact.get("raw_header_valid") is True:
        return
    raise SaveArtifactError("CK3 seed format is neither CRC-valid ZIP nor native SAV")


class Ck3ProfileArtifactInspector:
    """Read one profile selected by server bootstrap, never by an MCP call."""

    def __init__(self, profile_dir: str | Path) -> None:
        self.profile_dir = Path(profile_dir).resolve()

    def inspect_save_artifacts_v1(self) -> dict[str, object]:
        candidates: list[Path] = []
        last_save = self.profile_dir / "last_save.ck3"
        if last_save.is_file() or last_save.is_symlink():
            candidates.append(last_save)
        save_dir = self.profile_dir / "save games"
        if save_dir.is_dir():
            candidates.extend(
                sorted(save_dir.glob("*.ck3"), key=lambda item: item.name.casefold())
            )
        if len(candidates) > MAX_SAVE_ARTIFACTS:
            raise SaveArtifactError(
                f"configured profile contains more than {MAX_SAVE_ARTIFACTS} CK3 saves"
            )
        artifacts = [
            inspect_ck3_save_artifact_v1(path, profile_dir=self.profile_dir)
            for path in candidates
        ]
        return {
            "schema": SAVE_ARTIFACTS_SCHEMA_V1,
            "profile_dir": str(self.profile_dir),
            "save_root": str(save_dir),
            "artifact_count": len(artifacts),
            "artifacts": artifacts,
            "path_argument_accepted": False,
            "read_only": True,
        }
