"""Bind unchanged private nonwar DTOs to the selected native adapter build.

Legacy 1.19 DTOs have no SHA field. New 1.20 DTOs derive their version and SHA
from the exact hello already attached to the driver's semantic snapshot.
Namespace names of reused native value types are not build identities.
"""

from __future__ import annotations

from collections.abc import Mapping

from .driver import BridgeUnavailableError
from .version_identity import CK3_11906, CK3_12003, NativeBuildIdentity, require_exact_native_build


def private_native_schema(schema: str, snapshot: Mapping[str, object]) -> str:
    """Select the adapter's schema label while retaining its reviewed DTO layout."""
    if private_native_build_identity(snapshot) == CK3_12003 and schema.startswith("ck3_12002_"):
        return "ck3_12003_" + schema[len("ck3_12002_"):]
    return schema


def private_native_build_identity(snapshot: Mapping[str, object]) -> NativeBuildIdentity:
    diagnostics = snapshot.get("diagnostics")
    hello = diagnostics.get("hello") if isinstance(diagnostics, Mapping) else None
    if not isinstance(hello, Mapping):
        # Preserve the existing legacy private contract for archived 1.19
        # consumer inputs, which predate the hello projection. This branch
        # cannot label a result 1.20 or admit a 1.20 input.
        return CK3_11906
    version = hello.get("expected_ck3_version", hello.get("game_version"))
    sha256 = hello.get("expected_ck3_sha256", hello.get("executable_sha256"))
    try:
        return require_exact_native_build(version, sha256)
    except ValueError as error:
        raise BridgeUnavailableError("private nonwar source lacks a frozen exact native build") from error


def private_native_provenance(snapshot: Mapping[str, object]) -> dict[str, str]:
    build = private_native_build_identity(snapshot)
    result = {"exact_ck3_build": build.game_version}
    if build != CK3_11906:
        result["exe_sha256"] = build.executable_sha256
    return result


def private_native_readback_matches(
    snapshot: Mapping[str, object], readback: Mapping[str, object],
) -> bool:
    build = private_native_build_identity(snapshot)
    if readback.get("exact_ck3_build") != build.game_version:
        return False
    sha256 = readback.get("exe_sha256")
    if build == CK3_11906 and sha256 is None:
        return True
    return isinstance(sha256, str) and sha256.upper() == build.executable_sha256
