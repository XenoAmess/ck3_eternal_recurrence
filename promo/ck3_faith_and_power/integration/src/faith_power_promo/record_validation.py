"""Exact installed RECORD validation with caller-declared pip target scripts.

Candidate for faith_power_promo.record_validation. No process, network, or
environment mutation. A target-scheme script mapping never skips a digest.
"""
from __future__ import annotations

import base64
import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


@dataclass(frozen=True)
class ScriptMapping:
    record_path: str
    relative_actual_path: str


@dataclass(frozen=True)
class InstalledRecordSpec:
    installation_root: Path
    record_file: Path
    script_mappings: tuple[ScriptMapping, ...] = ()


@dataclass(frozen=True)
class VerifiedScript:
    record_path: str
    actual_path: str
    bytes: int
    sha256: str


@dataclass(frozen=True)
class InstalledRecordResult:
    checked_payloads: int
    mapped_scripts: tuple[VerifiedScript, ...]


def validate_installed_record(spec: InstalledRecordSpec) -> InstalledRecordResult:
    """Verify every hashed payload, including explicitly relocated scripts.

    Normal entries must stay inside the exact installation root. Only the
    caller's finite exact RECORD keys may map to another path inside that root.
    Unknown traversal, missing payloads, unexpected rows, or mismatches reject.
    """
    root = spec.installation_root.resolve(strict=True)
    record = spec.record_file.resolve(strict=True)
    record.relative_to(root)
    mappings: dict[str, Path] = {}
    for item in spec.script_mappings:
        if not item.record_path or item.record_path in mappings:
            raise ValueError('Empty or duplicate script mapping')
        relative = PurePosixPath(item.relative_actual_path)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Mapped script must remain within installation root')
        actual = (root / relative).resolve(strict=True)
        actual.relative_to(root)
        mappings[item.record_path] = actual
    seen: set[str] = set()
    mapped: list[VerifiedScript] = []
    checked = 0
    rows = list(csv.reader(record.read_text(encoding='utf-8').splitlines()))
    if not 1 <= len(rows) <= 10000:
        raise ValueError('Installed RECORD row limit exceeded')
    for row in rows:
        if len(row) != 3:
            raise ValueError('Invalid installed RECORD row')
        relative_text, digest, length = row
        if not relative_text or relative_text in seen:
            raise ValueError('Empty or duplicate installed RECORD path')
        seen.add(relative_text)
        if not digest:
            if length:
                raise ValueError('Unhashed RECORD row unexpectedly declares length')
            continue
        if not length.isascii() or not length.isdecimal():
            raise ValueError('RECORD payload size must be an unsigned decimal integer')
        if relative_text in mappings:
            path = mappings[relative_text]
        else:
            relative = PurePosixPath(relative_text)
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError('Unmapped installed RECORD escape refused: ' + relative_text)
            path = (root / relative).resolve(strict=True)
            path.relative_to(root)
        algorithm, separator, encoded = digest.partition('=')
        data = path.read_bytes()
        sha256 = hashlib.sha256(data).hexdigest()
        if (algorithm != 'sha256' or separator != '=' or
                base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode('ascii').rstrip('=') != encoded or
                len(data) != int(length)):
            raise ValueError('Installed RECORD digest or size mismatch: ' + relative_text)
        checked += 1
        if relative_text in mappings:
            mapped.append(VerifiedScript(relative_text, str(path), len(data), sha256))
    if set(mappings) - seen:
        raise ValueError('Caller declared a script absent from actual RECORD')
    if checked == 0:
        raise ValueError('Installed RECORD did not verify any payload')
    return InstalledRecordResult(checked, tuple(mapped))
