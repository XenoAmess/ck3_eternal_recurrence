"""Episode-bound proof for the stock combat phase-event source playset.

The immutable phase-event manifest intentionally does not claim that its
files are the ones loaded by a running game.  This module closes only that
one fidelity gate for a managed native session.  It binds the live bridge
PID and snapshot to the prepared environment, proves that ``dlc_load.json``
enables exactly the production autoplay mod, rejects a production overlay or
``replace_path`` covering any manifest source, and hashes every stock source
again.  AST execution and native-trace fidelity remain separate gates.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any

from ..environment import (
    OUTER_DESCRIPTOR_NAME,
    OUTER_DESCRIPTOR_REF,
    PROFILE_MANIFEST_NAME,
    _contract_digest,
    parse_descriptor_target,
    sha256_file,
    snapshot_digest,
    tree_snapshot,
)
from .phase_event_manifest import (
    STOCK_PHASE_EVENT_MANIFEST_SHA256,
    FrozenPhaseEventManifest,
    load_stock_phase_event_manifest,
)


LOADED_PLAYSET_PROOF_SCHEMA_VERSION = 1
LOADED_PLAYSET_PROOF_SCOPE = (
    "managed-session-single-mod-stock-phase-event-sources"
)
_ACTIVE_UNSAFE_MARKER_REASON = (
    "suspended launch active; removed only after authenticated tree shutdown"
)
_SHA256 = re.compile(r"[0-9A-Fa-f]{64}")
_NONCE = re.compile(r"[0-9a-f]{32}")


class LoadedPlaysetProofError(ValueError):
    """The current managed session cannot prove the stock source playset."""


def build_loaded_playset_proof(
    state_dir: str | Path,
    *,
    episode_run_id: object,
    snapshot_binding: object,
    native_hello: object,
    _manifest: FrozenPhaseEventManifest | None = None,
) -> dict[str, object]:
    """Build a canonical proof for one episode and one observed native frame.

    ``_manifest`` exists only to permit small deterministic unit fixtures.  A
    production caller omits it and therefore always loads the pinned package
    manifest, including its canonical hash and exact-build validation.
    """

    root = Path(state_dir).expanduser().resolve()
    episode = _nonempty_string(episode_run_id, "episode_run_id")
    binding = _snapshot_binding(snapshot_binding)
    hello = _native_hello(native_hello)
    manifest = _manifest or load_stock_phase_event_manifest()
    if len(manifest.files) != 11:
        raise LoadedPlaysetProofError(
            "phase-event manifest must contain exactly 11 source files"
        )
    if manifest.canonical_manifest_sha256 != STOCK_PHASE_EVENT_MANIFEST_SHA256:
        raise LoadedPlaysetProofError("phase-event manifest identity drifted")

    profile = (root / "profile").resolve()
    environment_path = profile / PROFILE_MANIFEST_NAME
    environment = _read_object(environment_path, "environment manifest")
    environment_sha256 = environment.get("environment_sha256")
    if (
        not isinstance(environment_sha256, str)
        or _SHA256.fullmatch(environment_sha256) is None
        or environment_sha256 != _contract_digest(environment)
    ):
        raise LoadedPlaysetProofError(
            "managed environment contract fingerprint differs"
        )
    if environment.get("state_dir") != str(root) or environment.get(
        "profile_dir"
    ) != str(profile):
        raise LoadedPlaysetProofError(
            "managed environment belongs to another state/profile directory"
        )

    game = _object(environment.get("game"), "environment.game")
    if game.get("raw_version") != manifest.game_version:
        raise LoadedPlaysetProofError(
            "managed environment game version differs from phase manifest"
        )
    executable = Path(
        _nonempty_string(game.get("executable"), "environment.game.executable")
    ).expanduser().resolve()
    if executable.name.casefold() != "ck3.exe" or executable.parent.name.casefold() != "binaries":
        raise LoadedPlaysetProofError("managed executable path is not CK3 binaries/ck3.exe")
    game_dir = executable.parent.parent.resolve()
    executable_sha256 = _sha256_upper(executable, "CK3 executable")
    if (
        str(game.get("executable_sha256", "")).upper()
        != manifest.executable_sha256
        or executable_sha256 != manifest.executable_sha256
        or hello["game_version"] != manifest.game_version
        or hello["executable_sha256"] != manifest.executable_sha256
    ):
        raise LoadedPlaysetProofError(
            "managed/native CK3 exact-build identity differs from phase manifest"
        )

    launch_record_path = root / "control" / "ck3.json"
    launch_record = _launch_record(
        _read_object(launch_record_path, "managed launch record"),
        expected_pid=hello["pid"],
        expected_executable=executable,
    )
    unsafe_marker_path = root / "control" / "unsafe-cleanup.json"
    unsafe_marker = _unsafe_marker(
        _read_object(unsafe_marker_path, "managed active-session marker"),
        launch_record=launch_record,
    )

    load_profile = _object(
        environment.get("load_profile"), "environment.load_profile"
    )
    dlc_load_path = profile / "dlc_load.json"
    dlc_load = _read_object(dlc_load_path, "managed dlc_load.json")
    expected_load = {
        "enabled_mods": [OUTER_DESCRIPTOR_REF],
        "disabled_dlcs": [],
    }
    if dlc_load != expected_load or load_profile.get("enabled_mods") != [
        OUTER_DESCRIPTOR_REF
    ] or load_profile.get("disabled_dlcs") != []:
        raise LoadedPlaysetProofError(
            "managed enabled_mods is not the exact xar_autoplayer singleton"
        )
    dlc_load_sha256 = _sha256_lower(dlc_load_path, "managed dlc_load.json")
    if load_profile.get("dlc_load_sha256") != dlc_load_sha256:
        raise LoadedPlaysetProofError(
            "managed dlc_load.json bytes differ from the environment binding"
        )

    outer_path = profile / "mod" / OUTER_DESCRIPTOR_NAME
    outer_sha256 = _sha256_lower(outer_path, "managed outer descriptor")
    if (
        load_profile.get("outer_descriptor") != str(outer_path.resolve())
        or load_profile.get("outer_descriptor_sha256") != outer_sha256
    ):
        raise LoadedPlaysetProofError(
            "managed outer descriptor differs from the environment binding"
        )
    try:
        production_root = parse_descriptor_target(outer_path)
    except (OSError, UnicodeError, ValueError) as error:
        raise LoadedPlaysetProofError(
            f"managed outer descriptor target is malformed: {error}"
        ) from error
    mod = _object(environment.get("mod"), "environment.mod")
    if mod.get("production_path") != str(production_root):
        raise LoadedPlaysetProofError(
            "managed production path differs from the environment binding"
        )
    try:
        production_root.relative_to(profile)
    except ValueError as error:
        raise LoadedPlaysetProofError(
            "managed production tree escapes the isolated profile"
        ) from error

    production_snapshot = tree_snapshot(production_root)
    production_tree_sha256 = snapshot_digest(production_snapshot)
    if (
        mod.get("production_tree_sha256") != production_tree_sha256
        or mod.get("production_file_count") != len(production_snapshot)
    ):
        raise LoadedPlaysetProofError(
            "managed production tree differs from the environment binding"
        )
    inner_descriptor = production_root / "descriptor.mod"
    inner_text = _read_text(inner_descriptor, "production descriptor")
    if "remote_file_id" in inner_text:
        raise LoadedPlaysetProofError(
            "production descriptor contains remote_file_id"
        )
    replace_paths = _descriptor_replace_paths(inner_text)
    production_paths = {
        _canonical_relative_path(relative, "production tree path").casefold()
        for relative in production_snapshot
    }

    stock_rows: list[dict[str, object]] = []
    overlay_paths: list[str] = []
    replace_conflicts: list[str] = []
    for source in manifest.files:
        relative = _canonical_relative_path(
            source.relative_path, "phase-event source path"
        )
        overlay_present = relative.casefold() in production_paths
        conflicts = [
            prefix
            for prefix in replace_paths
            if _replace_path_covers(prefix, relative)
        ]
        if overlay_present:
            overlay_paths.append(relative)
        replace_conflicts.extend(conflicts)
        stock_path = game_dir / "game" / PurePosixPath(relative)
        stock_sha256 = _sha256_upper(stock_path, f"stock source {relative}")
        if stock_sha256 != source.sha256:
            raise LoadedPlaysetProofError(
                f"stock phase-event source hash differs: {relative}"
            )
        stock_rows.append(
            {
                "load_order": source.load_order,
                "relative_path": relative,
                "manifest_sha256": source.sha256,
                "stock_sha256": stock_sha256,
                "production_overlay_present": overlay_present,
                "replace_path_conflicts": conflicts,
            }
        )
    if overlay_paths:
        raise LoadedPlaysetProofError(
            "production tree overlays phase-event manifest sources: "
            + ", ".join(overlay_paths)
        )
    if replace_conflicts:
        raise LoadedPlaysetProofError(
            "production descriptor replace_path covers phase-event sources: "
            + ", ".join(sorted(set(replace_conflicts)))
        )

    proof: dict[str, object] = {
        "schema_version": LOADED_PLAYSET_PROOF_SCHEMA_VERSION,
        "status": "verified",
        "proof_scope": LOADED_PLAYSET_PROOF_SCOPE,
        "episode_run_id": episode,
        "snapshot_binding": binding,
        "environment_sha256": environment_sha256,
        "environment_manifest_bytes_sha256": _sha256_upper(
            environment_path, "environment manifest"
        ),
        "phase_event_manifest_sha256": manifest.canonical_manifest_sha256,
        "managed_session": {
            "native_bridge_pid": hello["pid"],
            "native_session_generation": hello["session_generation"],
            "launch_nonce": launch_record["nonce"],
            "launch_creation_date": launch_record["creation_date"],
            "launch_record_sha256": _sha256_upper(
                launch_record_path, "managed launch record"
            ),
            "active_session_marker_sha256": _sha256_upper(
                unsafe_marker_path, "managed active-session marker"
            ),
            "state_dir": str(root),
            "profile_dir": str(profile),
            "executable": str(executable),
            "executable_sha256": executable_sha256,
            "active_marker_reason": unsafe_marker["reason"],
        },
        "dlc_load": {
            "relative_path": "dlc_load.json",
            "sha256": dlc_load_sha256.upper(),
            "enabled_mods": [OUTER_DESCRIPTOR_REF],
            "disabled_dlcs": [],
            "exact_singleton": True,
        },
        "production_mod": {
            "descriptor_ref": OUTER_DESCRIPTOR_REF,
            "outer_descriptor_sha256": outer_sha256.upper(),
            "production_root": str(production_root),
            "production_tree_sha256": production_tree_sha256.upper(),
            "production_file_count": len(production_snapshot),
            "inner_descriptor_sha256": _sha256_upper(
                inner_descriptor, "production descriptor"
            ),
            "replace_paths": replace_paths,
            "phase_source_overlay_count": 0,
            "phase_source_replace_path_conflict_count": 0,
        },
        "stock_sources": {
            "game_root": str(game_dir),
            "count": len(stock_rows),
            "files": stock_rows,
        },
        "claims": {
            "managed_session_pid_bound": True,
            "episode_environment_bound": True,
            "enabled_mods_exact_singleton": True,
            "production_phase_source_overlays_absent": True,
            "production_replace_path_conflicts_absent": True,
            "stock_source_sha256_exact": True,
            "loaded_playset_verified": True,
        },
        "unavailable_reason": None,
    }
    proof["proof_sha256"] = _proof_digest(proof)
    return copy.deepcopy(proof)


def validate_loaded_playset_proof(
    value: object,
    state_dir: str | Path,
    *,
    episode_run_id: object,
    snapshot_binding: object,
    native_hello: object,
    _manifest: FrozenPhaseEventManifest | None = None,
) -> dict[str, object]:
    """Rebuild and compare a proof, rejecting file, episode, or frame drift."""

    row = _object(value, "loaded playset proof")
    claimed = row.get("proof_sha256")
    if not isinstance(claimed, str) or _SHA256.fullmatch(claimed) is None:
        raise LoadedPlaysetProofError("loaded playset proof hash is malformed")
    if _proof_digest(row) != claimed:
        raise LoadedPlaysetProofError("loaded playset proof hash differs")
    expected = build_loaded_playset_proof(
        state_dir,
        episode_run_id=episode_run_id,
        snapshot_binding=snapshot_binding,
        native_hello=native_hello,
        _manifest=_manifest,
    )
    if row != expected:
        raise LoadedPlaysetProofError(
            "loaded playset proof differs from the current episode/environment"
        )
    return copy.deepcopy(expected)


def unavailable_loaded_playset_proof(
    *, episode_run_id: object, reason: str
) -> dict[str, object]:
    """Return a typed negative result without pretending the gate is closed."""

    episode = episode_run_id if isinstance(episode_run_id, str) and episode_run_id else None
    detail = reason if isinstance(reason, str) and reason else "proof_unavailable"
    row: dict[str, object] = {
        "schema_version": LOADED_PLAYSET_PROOF_SCHEMA_VERSION,
        "status": "unavailable",
        "proof_scope": LOADED_PLAYSET_PROOF_SCOPE,
        "episode_run_id": episode,
        "environment_sha256": None,
        "claims": {"loaded_playset_verified": False},
        "unavailable_reason": detail,
    }
    row["proof_sha256"] = _proof_digest(row)
    return row


def _proof_digest(value: dict[str, object]) -> str:
    stable = copy.deepcopy(value)
    stable.pop("proof_sha256", None)
    encoded = json.dumps(
        stable,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


def _snapshot_binding(value: object) -> dict[str, object]:
    row = _object(value, "snapshot_binding")
    if set(row) != {"snapshot_id", "revision", "native_revision"}:
        raise LoadedPlaysetProofError("snapshot_binding schema is malformed")
    snapshot_id = _nonempty_string(row.get("snapshot_id"), "snapshot_binding.snapshot_id")
    revision = _nonnegative_int(row.get("revision"), "snapshot_binding.revision")
    native_revision = _nonnegative_int(
        row.get("native_revision"), "snapshot_binding.native_revision"
    )
    return {
        "snapshot_id": snapshot_id,
        "revision": revision,
        "native_revision": native_revision,
    }


def _native_hello(value: object) -> dict[str, object]:
    row = _object(value, "native hello")
    pid = _positive_int(row.get("pid"), "native hello.pid")
    generation = _nonnegative_int(
        row.get("session_generation"), "native hello.session_generation"
    )
    version = _nonempty_string(row.get("game_version"), "native hello.game_version")
    executable_sha256 = _nonempty_string(
        row.get("executable_sha256"), "native hello.executable_sha256"
    ).upper()
    if _SHA256.fullmatch(executable_sha256) is None:
        raise LoadedPlaysetProofError("native hello executable SHA-256 is malformed")
    return {
        "pid": pid,
        "session_generation": generation,
        "game_version": version,
        "executable_sha256": executable_sha256,
    }


def _launch_record(
    value: dict[str, Any], *, expected_pid: int, expected_executable: Path
) -> dict[str, object]:
    if set(value) != {
        "format_version",
        "nonce",
        "ck3_pid",
        "parent_pid",
        "executable",
        "creation_date",
    }:
        raise LoadedPlaysetProofError("managed launch record schema is malformed")
    if value.get("format_version") != 1:
        raise LoadedPlaysetProofError("managed launch record version is malformed")
    nonce = _nonempty_string(value.get("nonce"), "managed launch nonce")
    if _NONCE.fullmatch(nonce) is None:
        raise LoadedPlaysetProofError("managed launch nonce is malformed")
    pid = _positive_int(value.get("ck3_pid"), "managed launch CK3 PID")
    if pid != expected_pid:
        raise LoadedPlaysetProofError(
            "native bridge PID differs from the managed launch record"
        )
    parent_pid = _positive_int(value.get("parent_pid"), "managed launch parent PID")
    executable = Path(
        _nonempty_string(value.get("executable"), "managed launch executable")
    ).expanduser().resolve()
    if executable != expected_executable:
        raise LoadedPlaysetProofError(
            "managed launch executable differs from the environment"
        )
    return {
        "format_version": 1,
        "nonce": nonce,
        "ck3_pid": pid,
        "parent_pid": parent_pid,
        "executable": str(executable),
        "creation_date": _nonempty_string(
            value.get("creation_date"), "managed launch creation_date"
        ),
    }


def _unsafe_marker(
    value: dict[str, Any], *, launch_record: dict[str, object]
) -> dict[str, object]:
    if set(value) != {"nonce", "ck3_pid", "reason"}:
        raise LoadedPlaysetProofError(
            "managed active-session marker schema is malformed"
        )
    if (
        value.get("nonce") != launch_record["nonce"]
        or value.get("ck3_pid") != launch_record["ck3_pid"]
        or value.get("reason") != _ACTIVE_UNSAFE_MARKER_REASON
    ):
        raise LoadedPlaysetProofError(
            "managed active-session marker differs from the launch record"
        )
    return {
        "nonce": value["nonce"],
        "ck3_pid": value["ck3_pid"],
        "reason": value["reason"],
    }


def _descriptor_replace_paths(text: str) -> list[str]:
    result: list[str] = []
    for raw in re.findall(r'(?im)^\s*replace_path\s*=\s*"([^"\r\n]+)"\s*$', text):
        relative = _canonical_relative_path(raw, "descriptor replace_path")
        if relative.casefold() in {item.casefold() for item in result}:
            raise LoadedPlaysetProofError(
                "production descriptor repeats replace_path"
            )
        result.append(relative)
    return result


def _replace_path_covers(prefix: str, relative: str) -> bool:
    folded_prefix = prefix.casefold().rstrip("/")
    folded_relative = relative.casefold()
    return folded_relative == folded_prefix or folded_relative.startswith(
        folded_prefix + "/"
    )


def _canonical_relative_path(value: object, name: str) -> str:
    raw = _nonempty_string(value, name).replace("\\", "/")
    path = PurePosixPath(raw)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise LoadedPlaysetProofError(f"{name} is not a canonical relative path")
    canonical = path.as_posix()
    if raw != canonical:
        raise LoadedPlaysetProofError(f"{name} is not canonical")
    return canonical


def _read_object(path: Path, name: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise LoadedPlaysetProofError(f"{name} is unavailable: {error}") from error
    return _object(value, name)


def _read_text(path: Path, name: str) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as error:
        raise LoadedPlaysetProofError(f"{name} is unavailable: {error}") from error


def _sha256_upper(path: Path, name: str) -> str:
    try:
        return sha256_file(path).upper()
    except OSError as error:
        raise LoadedPlaysetProofError(f"{name} is unavailable: {error}") from error


def _sha256_lower(path: Path, name: str) -> str:
    try:
        return sha256_file(path).lower()
    except OSError as error:
        raise LoadedPlaysetProofError(f"{name} is unavailable: {error}") from error


def _object(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise LoadedPlaysetProofError(f"{name} must be an object")
    return value


def _nonempty_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise LoadedPlaysetProofError(f"{name} must be a nonempty string")
    return value


def _nonnegative_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise LoadedPlaysetProofError(f"{name} must be a non-negative integer")
    return value


def _positive_int(value: object, name: str) -> int:
    result = _nonnegative_int(value, name)
    if result <= 0:
        raise LoadedPlaysetProofError(f"{name} must be positive")
    return result
