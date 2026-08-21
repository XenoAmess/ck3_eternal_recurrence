"""Read-only snapshots for storage the autonomous player must never mutate."""

from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path
import hashlib

from .environment import (
    STEAM_APP_ID,
    _steam_path,
    is_relative_to,
    real_ck3_profile,
    sha256_file,
    snapshot_digest,
    steam_protected_roots,
)
from .errors import AgentError


def file_record(path: Path) -> dict[str, object]:
    stat = path.stat()
    return {
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": sha256_file(path),
    }


def metadata_record(path: Path) -> dict[str, int]:
    """Cheap mutation evidence for large, protected Workshop trees."""
    stat = path.stat()
    return {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns}


def real_profile_snapshot() -> dict[str, object]:
    root = real_ck3_profile()
    paths = list(path for path in root.iterdir() if path.is_file()) if root.is_dir() else []
    for relative in ("player", "save games", "rulers"):
        directory = root / relative
        if directory.is_dir():
            paths.extend(sorted(path for path in directory.rglob("*") if path.is_file()))
    mod_dir = root / "mod"
    if mod_dir.is_dir():
        paths.extend(sorted(path for path in mod_dir.glob("*.mod") if path.is_file()))
    return {
        path.relative_to(root).as_posix(): file_record(path)
        for path in paths
        if path.is_file()
    }


def steam_userdata_snapshot() -> dict[str, object]:
    steam = _steam_path()
    if steam is None:
        raise AgentError("Steam installation is unavailable for storage attestation")
    root = steam / "userdata"
    app_dirs = sorted(path for path in root.glob(f"*/{STEAM_APP_ID}") if path.is_dir())
    if not app_dirs:
        raise AgentError(
            f"no local Steam userdata found for CK3 app {STEAM_APP_ID}: {root}"
        )
    result: dict[str, object] = {}
    for app_dir in app_dirs:
        for path in sorted(item for item in app_dir.rglob("*") if item.is_file()):
            relative = path.relative_to(root).as_posix()
            if path.name.casefold() == "remotecache.vdf":
                raw = path.read_bytes()
                normalized, count = re.subn(
                    rb'("ChangeNumber"\s+")[0-9]+(")',
                    rb'\1<volatile>\2',
                    raw,
                    count=1,
                )
                if count != 1:
                    raise AgentError(
                        f"Steam remotecache lacks one ChangeNumber field: {path}"
                    )
                result[relative] = {
                    "semantic_sha256": hashlib.sha256(normalized).hexdigest(),
                    "policy": "ChangeNumber and file mtime are volatile; all other bytes exact",
                }
            else:
                result[relative] = file_record(path)
    return result


def steam_userdata_volatile_snapshot() -> dict[str, object]:
    steam = _steam_path()
    if steam is None:
        raise AgentError("Steam installation is unavailable for storage attestation")
    root = steam / "userdata"
    app_dirs = sorted(path for path in root.glob(f"*/{STEAM_APP_ID}") if path.is_dir())
    result: dict[str, object] = {}
    for app_dir in app_dirs:
        for path in sorted(app_dir.rglob("remotecache.vdf")):
            raw = path.read_bytes()
            match = re.search(rb'"ChangeNumber"\s+"([0-9]+)"', raw)
            if not match:
                raise AgentError(f"Steam remotecache ChangeNumber is missing: {path}")
            stat = path.stat()
            result[path.relative_to(root).as_posix()] = {
                "change_number": int(match.group(1)),
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
    return result


def _descriptor_target(path: Path) -> Path:
    text = path.read_text(encoding="utf-8-sig")
    matches = re.findall(r'(?m)^\s*path\s*=\s*"([^"\r\n]+)"\s*$', text)
    if len(matches) != 1:
        raise AgentError(f"registered Workshop descriptor has invalid path=: {path}")
    target = Path(os.path.expandvars(matches[0])).expanduser()
    if not target.is_absolute():
        raise AgentError(f"registered Workshop target is not absolute: {path}")
    return target.resolve()


def workshop_snapshot() -> dict[str, object]:
    mod_dir = real_ck3_profile() / "mod"
    descriptors = sorted(mod_dir.glob("ugc_*.mod")) if mod_dir.is_dir() else []
    roots = [path.resolve() for label, path in steam_protected_roots() if "Workshop" in label]
    result: dict[str, object] = {}
    for descriptor in descriptors:
        result[f"descriptor:{descriptor.name}"] = file_record(descriptor)
        target = _descriptor_target(descriptor)
        if not any(is_relative_to(target, root) for root in roots):
            raise AgentError(f"registered Workshop target is outside Steam roots: {target}")
        if not target.is_dir():
            continue
        for item in sorted(path for path in target.rglob("*") if path.is_file()):
            relative = item.relative_to(target).as_posix()
            # Registered Workshop trees can total tens of gigabytes. Full content
            # hashing would reread every unrelated mod before each launch. The
            # descriptors remain content-hashed; target trees use the same
            # size/mtime inventory proven by the Vivhite isolation runner.
            result[f"target:{descriptor.name}/{relative}"] = metadata_record(item)
    return result


def protected_snapshot() -> dict[str, object]:
    snapshot = {
        "real_profile": real_profile_snapshot(),
        "steam_userdata": steam_userdata_snapshot(),
        "workshop": workshop_snapshot(),
    }
    return {
        "digest": snapshot_digest(snapshot),
        "stores": snapshot,
        "allowed_volatile": {
            "steam_remotecache": steam_userdata_volatile_snapshot(),
            "policy": "Only top-level ChangeNumber/mtime may change; semantic bytes remain protected.",
        },
    }


def _difference_summary(expected: dict[str, object], actual: dict[str, object]) -> str:
    added = sorted(set(actual) - set(expected))
    removed = sorted(set(expected) - set(actual))
    changed = sorted(
        key for key in set(expected) & set(actual) if expected[key] != actual[key]
    )
    parts = []
    for label, values in (("added", added), ("removed", removed), ("changed", changed)):
        if values:
            suffix = ",..." if len(values) > 5 else ""
            parts.append(f"{label}={values[:5]!r}{suffix}")
    return "; ".join(parts) or "no key-level difference"


def verify_protected_unchanged(
    baseline: dict[str, object], quiet_seconds: float = 5.0
) -> dict[str, object]:
    current = protected_snapshot()
    changed = [
        key
        for key in baseline["stores"]
        if baseline["stores"][key] != current["stores"].get(key)
    ]
    if "workshop" in changed or (changed and quiet_seconds <= 0):
        raise AgentError(
            "protected storage changed during isolated smoke: " + ", ".join(changed)
        )
    if quiet_seconds > 0:
        # Steam can briefly create and remove a local-cloud bookkeeping file
        # after the game exits. Accept only once the protected profile and Steam
        # app directory have returned to the exact baseline and then remained
        # there continuously. Workshop trees were already checked above; no
        # process remains that could mutate them during this short interval.
        deadline = time.monotonic() + max(120.0, quiet_seconds)
        stable_since: float | None = None
        expected_profile = baseline["stores"]["real_profile"]
        expected_steam = baseline["stores"]["steam_userdata"]
        last_signature: tuple[str, str] | None = None
        while time.monotonic() < deadline:
            actual_profile = real_profile_snapshot()
            actual_steam = steam_userdata_snapshot()
            if actual_profile == expected_profile and actual_steam == expected_steam:
                if stable_since is None:
                    stable_since = time.monotonic()
                if time.monotonic() - stable_since >= quiet_seconds:
                    result = dict(baseline)
                    result["allowed_volatile"] = {
                        "steam_remotecache": steam_userdata_volatile_snapshot(),
                        "policy": (
                            "Only top-level ChangeNumber/mtime may change; "
                            "semantic bytes remain protected."
                        ),
                    }
                    return result
            else:
                stable_since = None
                signature = (
                    _difference_summary(expected_profile, actual_profile),
                    _difference_summary(expected_steam, actual_steam),
                )
                if signature != last_signature:
                    print(
                        "[xar-autoplayer integrity] waiting for baseline: "
                        f"real_profile({signature[0]}); steam_userdata({signature[1]})",
                        file=sys.stderr,
                        flush=True,
                    )
                    last_signature = signature
            time.sleep(1.0)
        final_profile = real_profile_snapshot()
        final_steam = steam_userdata_snapshot()
        raise AgentError(
            "real profile or Steam userdata did not return to baseline for a "
            f"continuous {quiet_seconds:g}-second quiet interval; "
            f"real_profile({_difference_summary(expected_profile, final_profile)}); "
            f"steam_userdata({_difference_summary(expected_steam, final_steam)})"
        )
    return current
