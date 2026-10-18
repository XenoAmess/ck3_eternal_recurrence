# GENERATED FILE: tools/gen_ck3_live_run_identity_package.py
# Canonical: tools/ck3_live_run_id.py; selected-source SHA256: 9cc471cad707b12f7057b60908ee1528d23b418264fbfdae71e23097944b674a
"""Exact packaged canonical machine identity; no independent algorithm."""
from __future__ import annotations

import hashlib
import os
import platform
import re
from pathlib import Path


MACHINE_ENV = "XAR_CK3_MACHINE_ID"


SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


class LiveRunIdError(RuntimeError):
    """The live-run identifier could not be allocated or persisted."""


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
