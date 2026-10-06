"""Read one selected native context through the existing paused query transport."""

from __future__ import annotations

from .driver import BridgeUnavailableError
from .g2_private_query_transport import (
    private_g2_query_metadata_v1, read_private_g2_native_query_v1,
)
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .player_ordinary_holy_war_declaration_context_private_observation import (
    normalize_player_ordinary_holy_war_declaration_context_v1,
    selected_ordinary_holy_war_declaration,
)
from .version_identity import CK3_12003, CK3_12004, require_exact_native_backend


STEP = "query-player-ordinary-holy-war-declaration-context-v1"
DOMAIN_KEY = "player_ordinary_holy_war_declaration_context_v1"
PERMISSION = "allow_private_player_ordinary_holy_war_declaration_context_query"


def query_player_ordinary_holy_war_declaration_context_private_v1(
    driver: object, *, expected_revision: int, declaration_id: str,
    timeout_seconds: float = 30.0,
) -> dict[str, object]:
    if not isinstance(declaration_id, str) or not declaration_id:
        raise ValueError("declaration_id must identify an existing native declaration")
    selected = selected_ordinary_holy_war_declaration(driver.take_snapshot(), declaration_id)
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP, expected_revision=expected_revision,
        request_fields={**selected, "declaration_id": declaration_id,
                        "expected_public_revision": expected_revision},
        timeout_seconds=timeout_seconds,
    )
    try:
        if selected_ordinary_holy_war_declaration(before, declaration_id) != selected:
            raise ValueError("selected ordinary holy-war declaration crossed its current frame")
        build = require_exact_native_backend(
            result.get("game_version"), result.get("executable_sha256"),
            result.get("backend_id"), suffix="player-ordinary-holy-war-declaration-context-v1",
        )
        if (build not in (CK3_12003, CK3_12004) or build != private_native_build_identity(before)
                or result.get("domain_key") != DOMAIN_KEY
                or type(result.get("snapshot_revision")) is not int
                or result["snapshot_revision"] != before["native_revision"]
                or type(result.get("public_revision")) is not int
                or result["public_revision"] != before["revision"]
                or type(result.get("date_raw")) is not int
                or result["date_raw"] != before.get("date_raw")):
            raise ValueError("native ordinary holy-war envelope differs from the queried build/frame")
        value = normalize_player_ordinary_holy_war_declaration_context_v1(
            result.get("player_ordinary_holy_war_declaration_context"), snapshot=before,
            declaration_id=declaration_id, selected_declaration=selected,
        )
        if result.get("status") != ("observed" if value["available"] else "unavailable"):
            raise ValueError("native ordinary holy-war envelope lost its context availability")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {
        **value, **private_native_provenance(before), **private_g2_query_metadata_v1(before),
        "snapshot_revision": result["snapshot_revision"], "query_date_raw": result["date_raw"],
        "backend_id": result["backend_id"], "domain_key": DOMAIN_KEY,
        "query_status": result["status"], "advertised": False,
    }
