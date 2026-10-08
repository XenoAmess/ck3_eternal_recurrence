"""Preserve predecessor family records at an admitted ordinary succession."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from .family_marriage_formal_consumer import _write, read_family_marriage_ledger


def archive_predecessor_family_marriage_v1(
    state_dir: Path | None, *, source_episode_run_id: str,
    successor_episode_run_id: str, predecessor_character_id: int,
    successor_character_id: int,
) -> dict[str, object] | None:
    """Called only after the driver's existing matched ordinary M3 admission.

    This is local episode bookkeeping. An unresolved proposal remains unresolved
    history; it is neither queried nor resent under the successor's identity.
    """
    if state_dir is None:
        return None
    ledger = read_family_marriage_ledger(state_dir)
    pending = ledger["pending"]
    resolved = ledger["resolved"]
    archive_pending = (
        isinstance(pending, dict)
        and pending.get("episode_run_id") == source_episode_run_id
    )
    archive_resolved = (
        isinstance(resolved, dict)
        and resolved.get("episode_run_id") == source_episode_run_id
    )
    if not archive_pending and not archive_resolved:
        return None
    entry = {
        "source": "matched_ordinary_successor_episode",
        "source_episode_run_id": source_episode_run_id,
        "successor_episode_run_id": successor_episode_run_id,
        "predecessor_character_id": predecessor_character_id,
        "successor_character_id": successor_character_id,
        "pending": deepcopy(pending) if archive_pending else None,
        "resolved": deepcopy(resolved) if archive_resolved else None,
    }
    _write(state_dir, {
        **ledger,
        "pending": None if archive_pending else pending,
        "resolved": None if archive_resolved else resolved,
        "episode_history": [*ledger.get("episode_history", []), entry],
    })
    return {
        "status": "predecessor_records_archived",
        "source_episode_run_id": source_episode_run_id,
        "successor_episode_run_id": successor_episode_run_id,
        "predecessor_character_id": predecessor_character_id,
        "successor_character_id": successor_character_id,
        "pending_archived": archive_pending,
        "resolved_archived": archive_resolved,
        "ck3_command_submitted": False,
    }
