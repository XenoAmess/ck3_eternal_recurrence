#!/usr/bin/env python3
"""Bind a real product-only subject checkpoint to the endgame formal cell.

This module does not switch characters, launch CK3, select an option, or
write product state.  A managed runner may call it only after CK3's ordinary
single-player Switch Character UI has moved the exact #361 subject into the
played slot without advancing the date, and after saving that paused state.
The function verifies the saved bytes and live played-subject snapshot, then
returns the narrow receipt consumed by the formal action cell.  The cell
still requires the existing Workforce and AI-owned B1 providers to observe
the business state and the now-AI owner independently.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import re
from typing import Final, Mapping, Protocol

from zg361_phase2_cross_cycle_endgame_action_cell import (
    EndgameResultBinding,
    EndgameSubjectService,
    EndgameSubjectProofSession,
    PRODUCTION_SUBJECT_TRANSITION_MODE,
    RESULT_EVENT,
)


PRODUCTION_SUBJECT_CHECKPOINT_KIND: Final = (
    "zg361_phase2_cross_cycle_endgame_product_subject_checkpoint_v1"
)
EXACT_GAME_VERSION: Final = "1.19.0.6"
EXACT_EXE_SHA256: Final = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
_SHA256_RE: Final = re.compile(r"[0-9A-F]{64}\Z")


class ProductionSubjectService(EndgameSubjectService, Protocol):
    """The existing subject-side service; no new bridge capability is added."""


class ProductionSubjectCheckpointError(RuntimeError):
    def __init__(self, reason_code: str, evidence: Mapping[str, object]) -> None:
        self.reason_code = reason_code
        self.evidence = {
            **dict(evidence),
            "result": "RED",
            "reason_code": reason_code,
        }
        super().__init__(f"production subject checkpoint RED [{reason_code}]")


def _fail(reason_code: str, **evidence: object) -> None:
    raise ProductionSubjectCheckpointError(reason_code, evidence)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def bind_product_subject_checkpoint_session(
    service: ProductionSubjectService,
    result: EndgameResultBinding,
    checkpoint_receipt: Mapping[str, object],
) -> EndgameSubjectProofSession:
    """Validate one materialized no-fixture subject checkpoint and bind it."""

    receipt = dict(checkpoint_receipt)
    raw_path = receipt.get("path")
    path = Path(raw_path).resolve() if isinstance(raw_path, str) else Path()
    expected_bytes = receipt.get("bytes")
    expected_sha = str(receipt.get("sha256", "")).upper()
    exact_file = (
        isinstance(raw_path, str)
        and path.is_absolute()
        and path.is_file()
        and isinstance(expected_bytes, int)
        and not isinstance(expected_bytes, bool)
        and expected_bytes > 0
        and path.stat().st_size == expected_bytes
        and _SHA256_RE.fullmatch(expected_sha) is not None
        and _sha256(path) == expected_sha
    )
    exact_contract = (
        receipt.get("schema_version") == 1
        and receipt.get("kind") == PRODUCTION_SUBJECT_CHECKPOINT_KIND
        and receipt.get("result") == "GREEN"
        and receipt.get("transition_mode") == PRODUCTION_SUBJECT_TRANSITION_MODE
        and receipt.get("game_version") == EXACT_GAME_VERSION
        and str(receipt.get("game_exe_sha256", "")).upper()
        == EXACT_EXE_SHA256
        and str(receipt.get("parent_result_checkpoint_sha256", "")).upper()
        == result.result_checkpoint_sha256
        and receipt.get("save_lineage_id") == result.save_lineage_id
        and receipt.get("source_event_definition_key") == RESULT_EVENT
        and receipt.get("owner_character_id") == result.owner_character_id
        and receipt.get("subject_character_id") == result.subject_character_id
        and receipt.get("player_character_id") == result.subject_character_id
        and receipt.get("date_raw") == result.result_date_raw
        and receipt.get("product_only") is True
        and receipt.get("official_ui_switch_observed") is True
        and receipt.get("fixture_used") is False
        and receipt.get("typed_event_fixture_used") is False
        and receipt.get("business_state_fixture_used") is False
        and receipt.get("console_used") is False
        and receipt.get("generic_character_rebind_used") is False
    )
    if not (exact_file and exact_contract):
        _fail(
            "subject_checkpoint_contract_invalid",
            checkpoint_receipt=receipt,
            file_materialized=exact_file,
            contract_valid=exact_contract,
        )

    snapshot = service.snapshot()
    played = snapshot.get("played_character") if isinstance(snapshot, Mapping) else None
    active = snapshot.get("active_event") if isinstance(snapshot, Mapping) else None
    live_binding = {
        "snapshot_id": snapshot.get("snapshot_id") if isinstance(snapshot, Mapping) else None,
        "revision": snapshot.get("revision") if isinstance(snapshot, Mapping) else None,
        "native_revision": snapshot.get("native_revision") if isinstance(snapshot, Mapping) else None,
        "date_raw": snapshot.get("date_raw") if isinstance(snapshot, Mapping) else None,
        "player_character_id": (
            played.get("character_id") if isinstance(played, Mapping) else None
        ),
        "paused": snapshot.get("paused") if isinstance(snapshot, Mapping) else None,
        "map_ready": snapshot.get("map_ready") if isinstance(snapshot, Mapping) else None,
        "active_event": active,
    }
    live_valid = (
        live_binding["paused"] is True
        and live_binding["map_ready"] is True
        and isinstance(live_binding["snapshot_id"], str)
        and bool(live_binding["snapshot_id"])
        and isinstance(live_binding["revision"], int)
        and not isinstance(live_binding["revision"], bool)
        and int(live_binding["revision"]) >= 0
        and isinstance(live_binding["native_revision"], int)
        and not isinstance(live_binding["native_revision"], bool)
        and int(live_binding["native_revision"]) > 0
        and live_binding["date_raw"] == result.result_date_raw
        and live_binding["player_character_id"] == result.subject_character_id
        and active is None
    )
    if not live_valid:
        _fail(
            "played_subject_checkpoint_not_observed",
            expected_subject_character_id=result.subject_character_id,
            expected_date_raw=result.result_date_raw,
            live_binding=live_binding,
        )

    return EndgameSubjectProofSession(
        service=service,
        transition_receipt={
            "result": "GREEN",
            "transition_mode": PRODUCTION_SUBJECT_TRANSITION_MODE,
            "checkpoint_restore_observed": True,
            "action_ack_only": False,
            "from_player_character_id": result.owner_character_id,
            "to_player_character_id": result.subject_character_id,
            "date_raw": result.result_date_raw,
            "restored_checkpoint_sha256": result.result_checkpoint_sha256,
            "subject_checkpoint_sha256": expected_sha,
            "save_lineage_id": result.save_lineage_id,
            "product_only": True,
            "official_ui_switch_observed": True,
            "fixture_used": False,
            "typed_event_fixture_used": False,
            "business_state_fixture_used": False,
            "console_used": False,
            "generic_character_rebind_used": False,
            "subject_checkpoint": {
                "path": str(path),
                "bytes": expected_bytes,
                "sha256": expected_sha,
            },
            "live_binding": live_binding,
        },
    )


__all__ = [
    "EXACT_EXE_SHA256",
    "EXACT_GAME_VERSION",
    "PRODUCTION_SUBJECT_CHECKPOINT_KIND",
    "ProductionSubjectCheckpointError",
    "ProductionSubjectService",
    "bind_product_subject_checkpoint_session",
]
