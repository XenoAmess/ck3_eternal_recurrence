"""Match reused addon DTO labels to an already normalized religion Context."""

from __future__ import annotations

from collections.abc import Mapping

from .version_identity import CK3_12004, require_exact_native_build


def religion_context_addon_schema(
    schema: str, current_context: Mapping[str, object],
) -> str:
    if current_context.get("game_version") != CK3_12004.game_version:
        return schema
    build = require_exact_native_build(
        current_context.get("game_version"), current_context.get("executable_sha256"),
    )
    if build == CK3_12004:
        for prefix in ("ck3_12002_", "ck3_12003_"):
            if schema.startswith(prefix):
                return "ck3_12004_" + schema[len(prefix):]
    return schema
