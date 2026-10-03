"""Actor-only ordinary default raise legality, using the final native validator."""
from __future__ import annotations
from collections.abc import Mapping
from .timeline_blocker_private_transport import _binding
from .version_identity import CK3_12003, require_exact_native_build

STEP = "query-player-default-raise-v1"
CAPABILITY = "game.command.query-player-default-raise-v1"

def player_default_raise_frame_binding(snapshot: Mapping[str, object]) -> tuple[object, ...]:
    # Retain the established instance, connection, episode and paused-frame
    # contract. The query does not require absence of an existing army.
    return _binding(snapshot)

def normalize_player_default_raise_v1(value: object, *, snapshot: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(value, dict) or value.get("schema") != "ck3_12003_player_default_raise_v1":
        raise ValueError("native default raise schema is malformed")
    build = require_exact_native_build(value.get("game_version"), value.get("executable_sha256"))
    player = snapshot.get("played_character")
    if (build != CK3_12003 or not isinstance(player, Mapping)
            or type(value.get("actor_character_id")) is not int
            or value["actor_character_id"] != player.get("character_id")
            or type(value.get("snapshot_revision")) is not int
            or value["snapshot_revision"] != snapshot.get("native_revision")
            or type(value.get("date_raw")) is not int
            or value["date_raw"] != snapshot.get("date_raw")):
        raise ValueError("native default raise identity differs from current player frame")
    status = value.get("status")
    ready = value.get("default_raise_legality_ready")
    legal = value.get("native_default_raise_legal")
    province = value.get("default_raise_province_id")
    if (status not in {"available", "partial", "unavailable", "requires_paused", "invalid_request"}
            or type(ready) is not bool or legal is not None and type(legal) is not bool
            or province is not None and (type(province) is not int or not 0 < province <= 2**31-1)
            or not isinstance(value.get("failure"), str) or not value["failure"]
            or ready != (legal is not None) or (status == "available") != ready
            or ready and (province is None or value["failure"] != "none")):
        raise ValueError("native default raise final legality/readiness is malformed")
    return dict(value)
