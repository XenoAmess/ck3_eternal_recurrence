#!/usr/bin/env python3
"""Allocate machine- and mod-scoped identifiers for CK3 live runs."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
import platform
import re
import tempfile
import time
import uuid
from pathlib import Path
from typing import Iterator, Sequence


SCHEMA_VERSION = 1
IDENTITY_SCHEMA = "xar.ck3-live-run-identity.v1"
COUNTER_SCHEMA = "xar.ck3-live-run-counter.v1"
MACHINE_ENV = "XAR_CK3_MACHINE_ID"
STATE_ROOT_ENV = "XAR_CK3_LIVE_RUN_STATE_ROOT"
LOCK_TIMEOUT_SECONDS = 10.0

CANONICAL_MOD_KEYS = frozenset(
    {
        "auto-upgrade-buildings",
        "eternal-recurrence",
        "ox-here",
        "reclaim-the-motherland",
        "remove-mandala",
        "vivhite-courtier",
        "xenoamess-quality-of-life",
        "zhongguo-style",
    }
)

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
LEGACY_ALIAS_RE = re.compile(r"^R[0-9]+[a-z]?$", re.IGNORECASE)
RUN_STATUSES = frozenset(
    {"launch-started", "completed-green", "completed-red", "superseded", "voided"}
)


class LiveRunIdError(RuntimeError):
    """The live-run identifier could not be allocated or persisted."""


@dataclass(frozen=True)
class LiveRunIdentity:
    schema: str
    run_id: str
    execution_id: str
    machine_id: str
    mod_key: str
    sequence: int
    allocated_at_utc: str
    allocator_pid: int
    legacy_alias: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _slug(value: str, *, label: str) -> str:
    candidate = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    candidate = candidate[:64].rstrip("-")
    if not candidate or not SLUG_RE.fullmatch(candidate):
        raise LiveRunIdError(f"invalid {label}: {value!r}")
    return candidate


def _automatic_machine_token() -> str:
    if os.name == "nt":
        try:
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Cryptography",
            ) as key:
                value, _ = winreg.QueryValueEx(key, "MachineGuid")
            if value:
                return f"windows-machine-guid:{value}"
        except OSError:
            pass
    for candidate in (Path("/etc/machine-id"), Path("/var/lib/dbus/machine-id")):
        try:
            value = candidate.read_text(encoding="ascii").strip()
        except OSError:
            continue
        if value:
            return f"machine-id:{value}"
    return f"node:{platform.node()}"


def derive_machine_id(hostname: str, opaque_machine_token: str) -> str:
    """Derive a readable ID without exposing the underlying machine token."""
    host = _slug(hostname or "machine", label="hostname")[:32].rstrip("-")
    digest = hashlib.sha256(opaque_machine_token.encode("utf-8")).hexdigest()[:10]
    return f"{host}-{digest}"


def current_machine_id(override: str | None = None) -> str:
    explicit = override if override is not None else os.environ.get(MACHINE_ENV)
    if explicit:
        return _slug(explicit, label="machine id")
    return derive_machine_id(platform.node(), _automatic_machine_token())


def default_state_root() -> Path:
    configured = os.environ.get(STATE_ROOT_ENV)
    if configured:
        return Path(configured).expanduser().resolve()
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        base = Path(os.environ["LOCALAPPDATA"])
    elif os.environ.get("XDG_STATE_HOME"):
        base = Path(os.environ["XDG_STATE_HOME"])
    else:
        base = Path.home() / ".local" / "state"
    return (base / "XarCk3Acceptance" / "live-run-ids-v1").resolve()


def validate_mod_key(mod_key: str) -> str:
    value = _slug(mod_key, label="mod key")
    if value not in CANONICAL_MOD_KEYS:
        known = ", ".join(sorted(CANONICAL_MOD_KEYS))
        raise LiveRunIdError(f"unknown mod key {value!r}; expected one of: {known}")
    return value


def format_run_id(machine_id: str, mod_key: str, sequence: int) -> str:
    machine = _slug(machine_id, label="machine id")
    product = validate_mod_key(mod_key)
    if sequence < 1:
        raise LiveRunIdError("sequence must be positive")
    return f"{machine}--{product}--R{sequence:04d}"


@contextmanager
def _exclusive_file_lock(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+b")
    if path.stat().st_size == 0:
        handle.write(b"\0")
        handle.flush()
    started = time.monotonic()
    locked = False
    try:
        while not locked:
            handle.seek(0)
            try:
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
            except (BlockingIOError, OSError):
                if time.monotonic() - started >= LOCK_TIMEOUT_SECONDS:
                    raise LiveRunIdError(f"timed out locking live-run counter: {path}")
                time.sleep(0.05)
        yield
    finally:
        if locked:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def _write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        prefix=path.name + ".",
        suffix=".tmp",
        dir=path.parent,
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _read_last_sequence(path: Path, machine_id: str, mod_key: str) -> int:
    if not path.is_file():
        return 0
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise LiveRunIdError(f"invalid live-run counter {path}: {error}") from error
    expected = {
        "schema": COUNTER_SCHEMA,
        "machine_id": machine_id,
        "mod_key": mod_key,
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            raise LiveRunIdError(
                f"live-run counter identity mismatch for {key}: "
                f"{payload.get(key)!r} != {value!r}"
            )
    sequence = payload.get("last_sequence")
    if not isinstance(sequence, int) or sequence < 0:
        raise LiveRunIdError(f"invalid last_sequence in {path}")
    return sequence


def allocate_live_run_id(
    mod_key: str,
    *,
    state_root: Path | None = None,
    machine_id: str | None = None,
    execution_id: str | None = None,
    legacy_alias: str | None = None,
    allocated_at_utc: str | None = None,
    allocator_pid: int | None = None,
) -> LiveRunIdentity:
    product = validate_mod_key(mod_key)
    machine = current_machine_id(machine_id)
    if legacy_alias is not None and not LEGACY_ALIAS_RE.fullmatch(legacy_alias):
        raise LiveRunIdError(f"invalid legacy alias: {legacy_alias!r}")
    execution = execution_id or str(uuid.uuid4())
    try:
        uuid.UUID(execution)
    except ValueError as error:
        raise LiveRunIdError(f"invalid execution id: {execution!r}") from error
    timestamp = allocated_at_utc or datetime.now(timezone.utc).isoformat()
    base = (state_root or default_state_root()).expanduser().resolve()
    namespace = base / machine / product
    namespace.mkdir(parents=True, exist_ok=True)
    counter_path = namespace / "counter.json"
    history_path = namespace / "allocations.jsonl"
    with _exclusive_file_lock(namespace / "counter.lock"):
        sequence = _read_last_sequence(counter_path, machine, product) + 1
        identity = LiveRunIdentity(
            schema=IDENTITY_SCHEMA,
            run_id=format_run_id(machine, product, sequence),
            execution_id=execution,
            machine_id=machine,
            mod_key=product,
            sequence=sequence,
            allocated_at_utc=timestamp,
            allocator_pid=allocator_pid if allocator_pid is not None else os.getpid(),
            legacy_alias=legacy_alias.upper() if legacy_alias else None,
        )
        _write_json_atomic(
            counter_path,
            {
                "schema": COUNTER_SCHEMA,
                "schema_version": SCHEMA_VERSION,
                "machine_id": machine,
                "mod_key": product,
                "last_sequence": sequence,
                "last_run_id": identity.run_id,
                "updated_at_utc": timestamp,
            },
        )
        with history_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(identity.to_dict(), ensure_ascii=False, sort_keys=True))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    return identity


def allocate_live_run_ids(
    mod_keys: Sequence[str],
    *,
    state_root: Path | None = None,
    machine_id: str | None = None,
) -> tuple[LiveRunIdentity, ...]:
    products = tuple(dict.fromkeys(validate_mod_key(item) for item in mod_keys))
    if not products:
        raise LiveRunIdError("at least one mod key is required")
    execution_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    return tuple(
        allocate_live_run_id(
            product,
            state_root=state_root,
            machine_id=machine_id,
            execution_id=execution_id,
            allocated_at_utc=timestamp,
        )
        for product in products
    )


def record_live_run_status(
    identity: LiveRunIdentity,
    status: str,
    *,
    reason: str,
    state_root: Path | None = None,
    recorded_at_utc: str | None = None,
) -> dict[str, object]:
    if status not in RUN_STATUSES:
        raise LiveRunIdError(f"unknown live-run status: {status!r}")
    if not reason.strip():
        raise LiveRunIdError("live-run status reason must not be empty")
    base = (state_root or default_state_root()).expanduser().resolve()
    namespace = base / identity.machine_id / identity.mod_key
    history_path = namespace / "allocations.jsonl"
    if not history_path.is_file():
        raise LiveRunIdError(f"allocation history missing for {identity.run_id}")
    row = {
        "schema": "xar.ck3-live-run-status.v1",
        "run_id": identity.run_id,
        "execution_id": identity.execution_id,
        "machine_id": identity.machine_id,
        "mod_key": identity.mod_key,
        "sequence": identity.sequence,
        "status": status,
        "reason": reason.strip(),
        "recorded_at_utc": recorded_at_utc or datetime.now(timezone.utc).isoformat(),
        "recorder_pid": os.getpid(),
    }
    with _exclusive_file_lock(namespace / "counter.lock"):
        allocated = False
        for line in history_path.read_text(encoding="utf-8").splitlines():
            try:
                candidate = json.loads(line)
            except json.JSONDecodeError as error:
                raise LiveRunIdError(
                    f"invalid allocation history for {identity.run_id}: {error}"
                ) from error
            if candidate.get("run_id") == identity.run_id:
                allocated = candidate.get("execution_id") == identity.execution_id
                break
        if not allocated:
            raise LiveRunIdError(f"run identity is not present in its allocation history")
        status_path = namespace / "statuses.jsonl"
        with status_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    return row


def load_live_run_identity(
    run_id: str,
    mod_key: str,
    *,
    state_root: Path | None = None,
    machine_id: str | None = None,
) -> LiveRunIdentity:
    product = validate_mod_key(mod_key)
    machine = current_machine_id(machine_id)
    history_path = (
        (state_root or default_state_root()).expanduser().resolve()
        / machine
        / product
        / "allocations.jsonl"
    )
    if not history_path.is_file():
        raise LiveRunIdError(f"allocation history missing for {run_id}")
    for line in history_path.read_text(encoding="utf-8").splitlines():
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as error:
            raise LiveRunIdError(f"invalid allocation history: {error}") from error
        if payload.get("run_id") == run_id:
            return LiveRunIdentity(**payload)
    raise LiveRunIdError(f"unknown live-run ID: {run_id}")


def write_identity_receipt(artifacts: Path, identities: Sequence[LiveRunIdentity]) -> Path:
    target = artifacts / "live-run-identity.json"
    if target.exists():
        raise LiveRunIdError(f"live-run identity receipt already exists: {target}")
    rows = tuple(identities)
    if not rows:
        raise LiveRunIdError("cannot write an empty live-run identity receipt")
    execution_ids = {row.execution_id for row in rows}
    if len(execution_ids) != 1:
        raise LiveRunIdError("all identities in one receipt must share an execution id")
    _write_json_atomic(
        target,
        {
            "schema": "xar.ck3-live-run-receipt.v1",
            "schema_version": SCHEMA_VERSION,
            "execution_id": rows[0].execution_id,
            "identities": [row.to_dict() for row in rows],
        },
    )
    return target


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("machine", help="print this machine's stable ID")
    subparsers.add_parser("list-mods", help="print canonical mod keys")
    allocate = subparsers.add_parser("allocate", help="consume the next per-mod number")
    allocate.add_argument("--mod", required=True, choices=sorted(CANONICAL_MOD_KEYS))
    allocate.add_argument("--legacy-alias")
    allocate.add_argument("--state-root")
    allocate.add_argument("--machine-id")
    status = subparsers.add_parser("status", help="append lifecycle state for a run")
    status.add_argument("--run-id", required=True)
    status.add_argument("--mod", required=True, choices=sorted(CANONICAL_MOD_KEYS))
    status.add_argument("--machine-id")
    status.add_argument("--status", required=True, choices=sorted(RUN_STATUSES))
    status.add_argument("--reason", required=True)
    status.add_argument("--state-root")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.command == "machine":
        print(current_machine_id())
        return 0
    if args.command == "list-mods":
        print("\n".join(sorted(CANONICAL_MOD_KEYS)))
        return 0
    if args.command == "status":
        identity = load_live_run_identity(
            args.run_id,
            args.mod,
            state_root=Path(args.state_root) if args.state_root else None,
            machine_id=args.machine_id,
        )
        row = record_live_run_status(
            identity,
            args.status,
            reason=args.reason,
            state_root=Path(args.state_root) if args.state_root else None,
        )
        print(json.dumps(row, ensure_ascii=False, indent=2))
        return 0
    identity = allocate_live_run_id(
        args.mod,
        state_root=Path(args.state_root) if args.state_root else None,
        machine_id=args.machine_id,
        legacy_alias=args.legacy_alias,
    )
    print(json.dumps(identity.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except LiveRunIdError as error:
        print(f"CK3 LIVE RUN ID FAILED: {error}", file=os.sys.stderr)
        raise SystemExit(1)
