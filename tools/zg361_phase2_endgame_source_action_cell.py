#!/usr/bin/env python3
"""Bounded live capture of the owner-facing ``zg361we.356`` source.

The caller owns CK3 startup and cleanup.  This action only advances an already
loaded product session from a near-boundary checkpoint, stops on the first real
``zg361we.356`` frame, and delegates the same-frame save and registry assembly
to the canonical source-capture primitive.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Callable, Mapping

from zg361_phase2_cross_cycle_endgame_source_capture import (
    capture_cross_cycle_endgame_source_checkpoint_v1,
)
from zg361_phase2_promotion_source_production_entry import (
    enter_promotion_source_checkpoint_v1,
)


SOURCE_EVENT = "zg361we.356"
MAX_SOURCE_ADVANCE_DAYS = 30
HOURS_PER_DAY = 24
PROGRESS_SAMPLE_INTERVAL_DAYS = 30


class EndgameSourceActionError(RuntimeError):
    """Preserve a typed action RED for the managed operator."""

    def __init__(self, message: str, evidence: Mapping[str, object]) -> None:
        self.evidence = deepcopy(dict(evidence))
        super().__init__(message)


def _write(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def _positive_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return value


def _typed_available(group: object, key: str) -> object | None:
    field = group.get(key) if isinstance(group, Mapping) else None
    if not (
        isinstance(field, Mapping)
        and field.get("status") == "available"
        and field.get("unavailable_reason") is None
    ):
        return None
    return field.get("value")


def _restore_owner_after_post_save_retry(
    service: object,
    initial: Mapping[str, object],
    *,
    expected_owner_character_id: int,
    expected_date_raw: int,
    request_nonce: str,
) -> tuple[Mapping[str, object], dict[str, object] | None]:
    played = initial.get("played_character")
    current_player = (
        played.get("character_id") if isinstance(played, Mapping) else None
    )
    if current_player == expected_owner_character_id:
        return initial, None
    revision = initial.get("revision")
    if not (
        initial.get("paused") is True
        and initial.get("map_ready") is True
        and initial.get("date_raw") == expected_date_raw
        and initial.get("active_event") is None
        and isinstance(current_player, int)
        and not isinstance(current_player, bool)
        and current_player > 0
        and isinstance(revision, int)
        and not isinstance(revision, bool)
        and revision >= 0
    ):
        raise EndgameSourceActionError(
            "source retry is not on the paused post-save subject frame",
            {"result": "RED", "initial_snapshot": initial},
        )
    provider = service.query_zhongguo_workforce_collective_snapshot_v1(
        request_nonce + ".owner-restore",
        expected_revision=revision,
        owner_character_id=expected_owner_character_id,
    )
    al_case = provider.get("al_case") if isinstance(provider, Mapping) else None
    cycle_serial = _typed_available(al_case, "cycle_serial")
    case_serial = _typed_available(al_case, "case_serial")
    if not (
        isinstance(provider, Mapping)
        and provider.get("status") == "available"
        and provider.get("player_character_id") == current_player
        and provider.get("subject_character_id") == current_player
        and provider.get("requested_owner_character_id")
        == expected_owner_character_id
        and _typed_available(al_case, "owner_character_id")
        == expected_owner_character_id
        and _typed_available(al_case, "subject_character_id") == current_player
        and isinstance(cycle_serial, int)
        and not isinstance(cycle_serial, bool)
        and cycle_serial >= 3
        and isinstance(case_serial, int)
        and not isinstance(case_serial, bool)
        and case_serial > 0
        and _typed_available(al_case, "state") == 1
        and _typed_available(al_case, "active") is True
    ):
        raise EndgameSourceActionError(
            "source retry subject is not the expected active Workforce case",
            {"result": "RED", "provider": provider},
        )
    switch = service.set_player_character_v1(
        expected_owner_character_id,
        expected_revision=revision,
    )
    restored = service.snapshot()
    restored_played = (
        restored.get("played_character")
        if isinstance(restored, Mapping)
        else None
    )
    restored_event = (
        restored.get("active_event") if isinstance(restored, Mapping) else None
    )
    if not (
        isinstance(switch, Mapping)
        and switch.get("accepted") is True
        and switch.get("status") == "switched"
        and switch.get("from_character_id") == current_player
        and switch.get("to_character_id") == expected_owner_character_id
        and isinstance(restored, Mapping)
        and restored.get("paused") is True
        and restored.get("map_ready") is True
        and restored.get("date_raw") == expected_date_raw
        and isinstance(restored_played, Mapping)
        and restored_played.get("character_id")
        == expected_owner_character_id
        and isinstance(restored_event, Mapping)
        and isinstance(restored_event.get("instance_id"), int)
    ):
        raise EndgameSourceActionError(
            "source retry could not restore the owner-facing event frame",
            {"result": "RED", "switch": switch, "snapshot": restored},
        )
    return restored, {
        "result": "GREEN",
        "kind": "zg361_phase2_endgame_source_owner_restore_v1",
        "from_character_id": current_player,
        "to_character_id": expected_owner_character_id,
        "date_raw": expected_date_raw,
        "cycle_serial": cycle_serial,
        "case_serial": case_serial,
        "switch": dict(switch),
    }


def run_endgame_source_capture(
    service: object,
    *,
    evidence_directory: Path,
    prefix_manifest: Path,
    expected_owner_character_id: int,
    expected_date_raw: int,
    runtime_capture_lineage: Mapping[str, object],
    request_nonce: str,
    max_advance_days: int = MAX_SOURCE_ADVANCE_DAYS,
    timeout_seconds: float = 1800.0,
    entry_runner: Callable[..., Mapping[str, object]] = (
        enter_promotion_source_checkpoint_v1
    ),
    capture_runner: Callable[..., Mapping[str, object]] = (
        capture_cross_cycle_endgame_source_checkpoint_v1
    ),
) -> dict[str, object]:
    """Advance at most thirty product days and assemble the fourth source row."""

    days = _positive_int(max_advance_days, "max_advance_days")
    if days > MAX_SOURCE_ADVANCE_DAYS:
        raise ValueError(
            f"max_advance_days exceeds focused source bound {MAX_SOURCE_ADVANCE_DAYS}"
        )
    _positive_int(expected_owner_character_id, "expected_owner_character_id")
    target_date = _positive_int(expected_date_raw, "expected_date_raw")
    if not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    if not isinstance(request_nonce, str) or not request_nonce:
        raise ValueError("request_nonce must be nonempty")

    directory = Path(evidence_directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    action_path = directory / "endgame-source-action.json"
    entry_path = directory / "endgame-source-production-entry.json"
    initial = service.snapshot()
    initial, owner_restore = _restore_owner_after_post_save_retry(
        service,
        initial,
        expected_owner_character_id=expected_owner_character_id,
        expected_date_raw=target_date,
        request_nonce=request_nonce,
    )
    played = initial.get("played_character") if isinstance(initial, Mapping) else None
    initial_player = (
        played.get("character_id") if isinstance(played, Mapping) else None
    )
    starting_date = initial.get("date_raw") if isinstance(initial, Mapping) else None
    if not (
        isinstance(initial, Mapping)
        and initial.get("paused") is True
        and initial.get("map_ready") is True
        and initial_player == expected_owner_character_id
        and isinstance(starting_date, int)
        and not isinstance(starting_date, bool)
    ):
        raise EndgameSourceActionError(
            "endgame source action requires the paused owner-bound map",
            {"result": "RED", "initial_snapshot": initial},
        )
    absolute_end = starting_date + days * HOURS_PER_DAY
    if target_date < starting_date or target_date > absolute_end:
        raise EndgameSourceActionError(
            "expected endgame source date is outside the focused game-day bound",
            {
                "result": "RED",
                "starting_date_raw": starting_date,
                "expected_date_raw": target_date,
                "absolute_end_date_raw": absolute_end,
            },
        )

    evidence: dict[str, object] = {
        "schema_version": 1,
        "kind": "zg361_phase2_endgame_source_action_cell_v1",
        "result": "RED",
        "readiness": "bounded-live-pending",
        "request_nonce": request_nonce,
        "source_event_definition_key": SOURCE_EVENT,
        "expected_owner_character_id": expected_owner_character_id,
        "expected_date_raw": target_date,
        "starting_date_raw": starting_date,
        "max_advance_days": days,
        "absolute_end_date_raw": absolute_end,
        "source_checkpoint_captured": False,
        "fixture_used": False,
        "console_used": False,
        "video_lock_touched": False,
        "owner_restore": owner_restore,
        "failure_reason": None,
    }
    _write(action_path, evidence)
    progress: dict[str, object] = {
        "timeline_origin_date_raw": starting_date,
        "absolute_end_date_raw": absolute_end,
        "timeline_interrupt_drains": [],
    }
    try:
        production_entry = dict(
            entry_runner(
                service,
                timeout_seconds=float(timeout_seconds),
                progress_sample_interval_days=PROGRESS_SAMPLE_INTERVAL_DAYS,
                prefer_natural_cycle=True,
                pause_on_event_definition_key=SOURCE_EVENT,
                pause_on_event_occurrence=1,
                evidence_out=progress,
            )
        )
        _write(entry_path, production_entry)
        if not (
            production_entry.get("result") == "GREEN"
            and production_entry.get("readiness") == f"paused-real-{SOURCE_EVENT}"
            and production_entry.get("pause_on_event_definition_key") == SOURCE_EVENT
            and production_entry.get("pause_on_event_occurrence") == 1
            and production_entry.get("fixture_used") is False
            and production_entry.get("console_used") is False
        ):
            raise EndgameSourceActionError(
                "bounded production entry did not stop on the first real zg361we.356",
                {"result": "RED", "production_entry": production_entry},
            )
        capture = dict(
            capture_runner(
                service,
                prefix_manifest=Path(prefix_manifest).resolve(),
                capture_input_root=directory / "source-capture-input",
                receipt_path=directory / "endgame-source-receipt.json",
                completed_manifest_path=(
                    directory / "phase2-source-checkpoint-capture-manifest.json"
                ),
                registry_checkpoint_root=directory / "phase2-source-checkpoints",
                registry_path=directory / "phase2-source-checkpoint-registry.json",
                expected_owner_character_id=expected_owner_character_id,
                expected_date_raw=target_date,
                runtime_capture_lineage=deepcopy(dict(runtime_capture_lineage)),
                timeout_seconds=5.0,
            )
        )
        if not (
            capture.get("result") == "GREEN"
            and capture.get("source_checkpoint_captured") is True
            and isinstance(capture.get("registry"), Mapping)
        ):
            raise EndgameSourceActionError(
                "canonical endgame source capture did not assemble a registry",
                {"result": "RED", "capture": capture},
            )
        evidence.update(
            result="GREEN",
            readiness="captured-and-registered",
            source_checkpoint_captured=True,
            production_entry=production_entry,
            capture=capture,
            failure_reason=None,
        )
        _write(action_path, evidence)
        return evidence
    except BaseException as error:
        evidence["failure_reason"] = f"{type(error).__name__}: {error}"
        evidence["upstream_evidence"] = deepcopy(
            getattr(error, "evidence", None)
        )
        _write(action_path, evidence)
        if isinstance(error, EndgameSourceActionError):
            raise
        raise EndgameSourceActionError(str(error), evidence) from error


__all__ = [
    "EndgameSourceActionError",
    "MAX_SOURCE_ADVANCE_DAYS",
    "SOURCE_EVENT",
    "run_endgame_source_capture",
]
