#!/usr/bin/env python3
"""Drive the exact product path to paused ``zg361pp.147`` without CK3 launch."""

from __future__ import annotations

import copy
import time
from collections.abc import Callable, Mapping
from typing import Protocol

from xar_autoplayer.bridge.zhongguo_promotion_source_progress_contract import (
    verify_review_now_independent_postcondition_v1,
    widget_visible,
)
from zg361_phase2_promotion_compensation_action_cell import _snapshot_binding


M146 = "zg361pp.146"
M147 = "zg361pp.147"
MAX_ADVANCE_DAYS = 400
HOURS_PER_DAY = 24


class PromotionProductionEntryService(Protocol):
    def snapshot(self) -> dict[str, object]: ...
    def execute_step(
        self, step: str, *, expected_revision: int
    ) -> dict[str, object]: ...
    def query_zhongguo_promotion_source_progress_v1(
        self, request_nonce: str, *, expected_revision: int
    ) -> dict[str, object]: ...
    def activate_zhongguo_review_now_v1(
        self, request_nonce: str, source_progress: dict[str, object], *,
        expected_revision: int,
    ) -> dict[str, object]: ...
    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]: ...
    def select_event_option(
        self, option_number: int, *, event_instance_id: int,
        expected_revision: int,
    ) -> dict[str, object]: ...


class PromotionProductionEntryError(RuntimeError):
    pass


def _accepted(value: object, step: str) -> dict[str, object]:
    result = copy.deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    status = result.get("status")
    if not (
        result.get("accepted") is True
        and (status == "submitted" or (step == "pause-map" and status == "already_paused"))
    ):
        raise PromotionProductionEntryError(f"{step} did not return an accepted ACK")
    return result


def _binding(
    snapshot: object, *, player: int | None = None,
    connection_generation: int | None = None,
) -> tuple[dict[str, object], dict[str, object] | None]:
    value = copy.deepcopy(dict(snapshot)) if isinstance(snapshot, Mapping) else {}
    played = value.get("played_character")
    actual_player = played.get("character_id") if isinstance(played, Mapping) else None
    diagnostics = value.get("diagnostics")
    generation = (
        diagnostics.get("connection_generation")
        if isinstance(diagnostics, Mapping)
        else None
    )
    revision = value.get("revision")
    date_raw = value.get("date_raw")
    if (
        value.get("map_ready") is not True
        or isinstance(revision, bool)
        or not isinstance(revision, int)
        or revision < 0
        or isinstance(date_raw, bool)
        or not isinstance(date_raw, int)
        or not isinstance(actual_player, int)
        or actual_player <= 0
        or not isinstance(generation, int)
        or generation <= 0
        or (player is not None and actual_player != player)
        or (
            connection_generation is not None
            and generation != connection_generation
        )
    ):
        raise PromotionProductionEntryError(
            "promotion path crossed its played-owner/connection binding"
        )
    event_binding = None
    if isinstance(value.get("active_event"), Mapping):
        if value.get("paused") is not True:
            return value, None
        event_binding = _snapshot_binding(value, expected_event=True)
    return value, event_binding


def _event_definition(
    service: PromotionProductionEntryService,
    binding: Mapping[str, object],
) -> tuple[str, dict[str, object]]:
    result = service.query_current_event_window_context_v1(
        int(binding["event_instance_id"]),
        expected_revision=int(binding["revision"]),
    )
    context = result.get("current_event_window_context")
    response_binding = result.get("binding")
    key = context.get("event_definition_key") if isinstance(context, Mapping) else None
    if (
        result.get("status") != "available"
        or not isinstance(context, Mapping)
        or not isinstance(response_binding, Mapping)
        or not isinstance(key, str)
        or response_binding.get("snapshot_id") != binding.get("snapshot_id")
        or response_binding.get("revision") != binding.get("revision")
        or response_binding.get("native_revision") != binding.get("native_revision")
        or response_binding.get("event_instance_id")
        != binding.get("event_instance_id")
    ):
        raise PromotionProductionEntryError(
            "current-event query crossed the paused promotion frame"
        )
    return key, copy.deepcopy(result)


def enter_promotion_source_checkpoint_v1(
    service: PromotionProductionEntryService,
    *,
    timeout_seconds: float = 300.0,
    poll_interval_seconds: float = 0.05,
    clock: Callable[[], float] = time.monotonic,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, object]:
    """Open player B1, advance to .146, choose option 1, stop on D+1 .147."""
    if timeout_seconds <= 0 or poll_interval_seconds < 0:
        raise ValueError("promotion entry timing is invalid")
    initial, initial_event = _binding(service.snapshot())
    player = int(initial["played_character"]["character_id"])
    generation = int(initial["diagnostics"]["connection_generation"])
    starting_date = int(initial["date_raw"])
    evidence: dict[str, object] = {
        "schema_version": 1,
        "kind": "zg361_phase2_promotion_source_production_entry",
        "result": "RED",
        "readiness": "static-ready-live-pending",
        "player_character_id": player,
        "connection_generation": generation,
        "starting_date_raw": starting_date,
        "review_action": None,
        "review_action_postcondition": None,
        "m146_option1_submission": None,
        "m146_date_raw": None,
        "target_binding": None,
        "action_ack_used_as_state_evidence": False,
        "fixture_used": False,
        "console_used": False,
        "generic_character_rebind_used": False,
        "observations": [],
    }
    if initial_event is not None:
        key, _ = _event_definition(service, initial_event)
        if key == M147:
            evidence["result"] = "GREEN"
            evidence["readiness"] = "paused-real-zg361pp.147"
            evidence["target_binding"] = initial_event
            return evidence
        raise PromotionProductionEntryError(
            f"promotion entry started on unexpected event {key!r}"
        )
    if initial.get("paused") is not True:
        pause = service.execute_step(
            "pause-map", expected_revision=int(initial["revision"])
        )
        _accepted(pause, "pause-map")
        initial, _ = _binding(
            service.snapshot(), player=player,
            connection_generation=generation,
        )
    before = service.query_zhongguo_promotion_source_progress_v1(
        "promo.entry.before", expected_revision=int(initial["revision"])
    )
    progress = before.get("zhongguo_promotion_source_progress")
    if before.get("status") != "available" or not isinstance(progress, dict):
        unavailable_reason = (
            progress.get("unavailable_reason")
            if isinstance(progress, Mapping)
            else "payload_missing"
        )
        widgets = progress.get("widgets") if isinstance(progress, Mapping) else None
        unavailable_widgets = []
        if isinstance(widgets, list):
            for widget in widgets:
                if not isinstance(widget, Mapping):
                    continue
                exists = widget.get("exists")
                if not (
                    isinstance(exists, Mapping)
                    and exists.get("status") == "available"
                    and exists.get("value") is True
                ):
                    runtime_name = widget.get("runtime_name")
                    unavailable_widgets.append(
                        runtime_name if isinstance(runtime_name, str) else "<unnamed>"
                    )
        raise PromotionProductionEntryError(
            "fixed promotion progress observer is unavailable: "
            f"reason={unavailable_reason!r}; "
            f"unavailable_widgets={unavailable_widgets!r}"
        )
    if not any(widget_visible(progress, index) for index in (2, 3, 4)):
        if not widget_visible(progress, 1):
            raise PromotionProductionEntryError(
                "real review-now product action is not eligible on this seed"
            )
        action = service.activate_zhongguo_review_now_v1(
            "promo.entry.review", before,
            expected_revision=int(initial["revision"]),
        )
        evidence["review_action"] = action
        after_snapshot, _ = _binding(
            service.snapshot(), player=player,
            connection_generation=generation,
        )
        after = service.query_zhongguo_promotion_source_progress_v1(
            "promo.entry.after",
            expected_revision=int(after_snapshot["revision"]),
        )
        try:
            evidence["review_action_postcondition"] = (
                verify_review_now_independent_postcondition_v1(
                    action_result=action,
                    before_query_sequence=int(before["query_sequence"]),
                    after_result=after,
                    expected_connection_generation=generation,
                    expected_player_character_id=player,
                )
            )
        except ValueError as error:
            raise PromotionProductionEntryError(str(error)) from error

    deadline = clock() + timeout_seconds
    while clock() < deadline:
        snapshot, event = _binding(
            service.snapshot(), player=player,
            connection_generation=generation,
        )
        date_raw = int(snapshot["date_raw"])
        if date_raw > starting_date + MAX_ADVANCE_DAYS * HOURS_PER_DAY:
            raise PromotionProductionEntryError(
                "promotion path exceeded its 400-day product bound"
            )
        observations = evidence["observations"]
        assert isinstance(observations, list)
        observations.append({
            "revision": snapshot["revision"],
            "date_raw": date_raw,
            "paused": snapshot.get("paused"),
            "active_event": event is not None,
        })
        if isinstance(snapshot.get("active_event"), Mapping) and event is None:
            _accepted(
                service.execute_step(
                    "pause-map", expected_revision=int(snapshot["revision"])
                ),
                "pause-map",
            )
            if poll_interval_seconds:
                sleeper(poll_interval_seconds)
            continue
        if event is not None:
            key, _ = _event_definition(service, event)
            if key == M147:
                m146_date = evidence.get("m146_date_raw")
                if not isinstance(m146_date, int) or date_raw < m146_date + HOURS_PER_DAY:
                    raise PromotionProductionEntryError(
                        "zg361pp.147 was not independently observed at D+1"
                    )
                evidence["result"] = "GREEN"
                evidence["readiness"] = "paused-real-zg361pp.147"
                evidence["target_binding"] = event
                return evidence
            if key != M146 or evidence.get("m146_option1_submission") is not None:
                raise PromotionProductionEntryError(
                    f"promotion path encountered unexpected event {key!r}"
                )
            submission = service.select_event_option(
                1,
                event_instance_id=int(event["event_instance_id"]),
                expected_revision=int(event["revision"]),
            )
            evidence["m146_option1_submission"] = _accepted(
                submission, "select-event-option-1"
            )
            evidence["m146_date_raw"] = date_raw
            # The option ACK proves dispatch only; the D+1 .147 event query
            # below is the result evidence.
            if poll_interval_seconds:
                sleeper(poll_interval_seconds)
            continue
        if snapshot.get("speed") != 1:
            _accepted(
                service.execute_step(
                    "set-speed-1", expected_revision=int(snapshot["revision"])
                ),
                "set-speed-1",
            )
        elif snapshot.get("paused") is True:
            _accepted(
                service.execute_step(
                    "resume-map", expected_revision=int(snapshot["revision"])
                ),
                "resume-map",
            )
        if poll_interval_seconds:
            sleeper(poll_interval_seconds)
    raise PromotionProductionEntryError(
        "timed out before paused real zg361pp.147"
    )


__all__ = [
    "MAX_ADVANCE_DAYS",
    "M146",
    "M147",
    "PromotionProductionEntryError",
    "PromotionProductionEntryService",
    "enter_promotion_source_checkpoint_v1",
]
