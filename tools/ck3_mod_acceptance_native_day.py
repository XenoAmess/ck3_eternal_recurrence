"""Typed projection of one retained native exact-day tool receipt.

No transport or retry lives here. Raw public rows remain in actual-results;
the caller records this projection separately for existing day consumers.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal, Protocol, TypedDict

Object = dict[str, object]
STEP = "life-advance-one-day"
_CLOCK_CAPABILITIES = frozenset({
    "game.command.research-arm-tactical-daily-sentinel-v1-N",
    "game.command.research-query-tactical-daily-sentinel-v1",
    "game.command.research-cancel-tactical-daily-sentinel-v1-generation-N",
    # Without this existing typed observer the old composite can auto-select
    # ordinary events, instead of leaving the caller's event boundary intact.
    "game.command.query-current-event-window-context-v1",
})


PendingInteractionPolicy = Literal["stop_at_boundary", "observe_unanswered_inbox"]


class PendingInboxSummaryV1(TypedDict):
    instance_id: int
    sender_character_id: int
    auto_accept_notification: bool
    source: Literal["native"]


class PendingInboxChangeV1(TypedDict):
    snapshot_id: str
    revision: int
    native_revision: int
    date_raw: int
    change: Literal["appeared", "disappeared", "changed"]
    before: PendingInboxSummaryV1 | None
    after: PendingInboxSummaryV1 | None


class PendingInboxObservationV1(TypedDict):
    policy: Literal["observe_unanswered_inbox"]
    starting_snapshot_id: str
    ending_snapshot_id: str
    before: PendingInboxSummaryV1 | None
    after: PendingInboxSummaryV1 | None
    changes: list[PendingInboxChangeV1]
    resolved: Literal[False]
    reply_attempted: Literal[False]
    modal_status: Literal["not_observed"]


def pending_interaction_policy_v1(value: object) -> PendingInteractionPolicy:
    if type(value) is str and value == "stop_at_boundary":
        return "stop_at_boundary"
    if type(value) is str and value == "observe_unanswered_inbox":
        return "observe_unanswered_inbox"
    raise ValueError("Exact declared pending interaction policy required")


def admit_pending_interaction_policy_v1(value: object, *, product: object,
                                         case: object) -> PendingInteractionPolicy:
    policy = pending_interaction_policy_v1(value)
    need(policy == "stop_at_boundary" or (product == "financial-markets" and type(case) is str
         and case in {"market-evolution", "delisting-gui"}), "Inbox observation is limited to the two declared financial observation cases")
    return policy


def _pending_inbox_summary_v1(value: object) -> PendingInboxSummaryV1 | None:
    if value is None:
        return None
    row = obj(value, "original pending inbox summary")
    need(set(row) == {"instance_id", "sender_character_id", "auto_accept_notification", "source"}
         and row.get("source") == "native" and type(row.get("auto_accept_notification")) is bool,
         "Exact original native pending inbox fields required")
    instance = integer(row.get("instance_id"), "pending full instance ID")
    sender = integer(row.get("sender_character_id"), "pending full sender ID")
    need(all(-(2**31) <= identity < 2**31 and identity != -1 for identity in (instance, sender)),
         "Pending inbox full IDs must preserve exact signed32 values excluding -1")
    automatic = row["auto_accept_notification"]
    if not isinstance(automatic, bool):
        raise ValueError("Exact notification boolean required")
    return {"instance_id": instance, "sender_character_id": sender,
            "auto_accept_notification": automatic, "source": "native"}


def pending_inbox_observation_v1(value: object, before: Object,
                                  after: Object) -> PendingInboxObservationV1:
    """Consume actual Host observations, never infer a modal or a resolved reply."""
    row = obj(value, "actual pending inbox observation")
    need(set(row) == {"policy", "starting_snapshot_id", "ending_snapshot_id", "before", "after",
                      "changes", "resolved", "reply_attempted", "modal_status"}
         and row.get("policy") == "observe_unanswered_inbox" and row.get("resolved") is False
         and row.get("reply_attempted") is False and row.get("modal_status") == "not_observed",
         "Exact unanswered inbox observation, never resolution credit, required")
    start_id, end_id = before.get("snapshot_id"), after.get("snapshot_id")
    need(isinstance(start_id, str) and bool(start_id) and isinstance(end_id, str) and bool(end_id)
         and row.get("starting_snapshot_id") == start_id and row.get("ending_snapshot_id") == end_id,
         "Inbox observation must bind the actual before/after Full snapshots")
    initial = _pending_inbox_summary_v1(row["before"])
    final = _pending_inbox_summary_v1(row["after"])
    need(initial == _pending_inbox_summary_v1(before.get("pending_character_interaction"))
         and final == _pending_inbox_summary_v1(after.get("pending_character_interaction")),
         "Inbox observation differs from actual before/after pending fields")
    rows = row["changes"]
    need(isinstance(rows, list), "Actual inbox change list required")
    if not isinstance(rows, list):
        raise ValueError("Actual inbox change list required")
    changes: list[PendingInboxChangeV1] = []
    cursor = initial
    for raw in rows:
        change = obj(raw, "actual inbox change")
        need(set(change) == {"snapshot_id", "revision", "native_revision", "date_raw", "change", "before", "after"},
             "Exact original inbox change fields required")
        first = _pending_inbox_summary_v1(change["before"])
        second = _pending_inbox_summary_v1(change["after"])
        need(first == cursor and first != second, "Actual inbox change chain is incomplete or duplicated")
        kind: Literal["appeared", "disappeared", "changed"] = ("appeared" if first is None else "disappeared" if second is None else "changed")
        snap = change["snapshot_id"]
        revision = integer(change["revision"], "inbox change public revision")
        native = integer(change["native_revision"], "inbox change native revision")
        date = integer(change["date_raw"], "inbox change actual date")
        need(isinstance(snap, str) and bool(snap) and change["change"] == kind and revision > 0 and native > 0
             and integer(before.get("date_raw"), "before date") <= date <= integer(after.get("date_raw"), "after date"),
             "Inbox change must retain an actual in-interval Full identity/date")
        if not isinstance(snap, str):
            raise ValueError("Actual inbox change snapshot ID required")
        changes.append({"snapshot_id": snap, "revision": revision, "native_revision": native,
                        "date_raw": date, "change": kind, "before": first, "after": second})
        cursor = second
    need(cursor == final, "Actual inbox change list does not reach its final observed state")
    if not isinstance(start_id, str) or not isinstance(end_id, str):
        raise ValueError("Actual before/after snapshot IDs required")
    return {"policy": "observe_unanswered_inbox", "starting_snapshot_id": start_id,
            "ending_snapshot_id": end_id, "before": initial, "after": final, "changes": changes,
            "resolved": False, "reply_attempted": False, "modal_status": "not_observed"}


class DayClient(Protocol):
    _seq: int
    output: Path

    def guard(self, reserve: Literal[90] = 90) -> object: ...
    def snapshot(self, allow_actor_change: bool = False,
                 require_event_free: bool = True) -> object: ...
    def advance_day(self, days: int = 1, timeout: float = 300,
                    allow_event_boundary: bool = False,
                    allow_actor_change: bool = False,
                    pending_interaction_policy: PendingInteractionPolicy = "stop_at_boundary") -> Object: ...
    def execute_plan(self, steps: list[Object], name: str, timeout: float | None = None,
                     reserve: Literal[90] = 90) -> list[object]: ...
    def validate_frame(self, frame: object, allow_actor_change: bool = False,
                       require_event_free: bool = True, require_paused: bool = True) -> object: ...
    def checkpoint(self, name: str, value: object) -> Path: ...


class NaturalDayResult(TypedDict):
    before: Object
    running_successor: None
    event_boundary: Object | None
    after: Object
    requested_days: Literal[1]
    target_date_raw: int
    elapsed_hours: int
    progress_status: str
    requested_interval_complete: bool
    event_resolution: str
    preflight: Object
    selected_event_options: int
    actor_transition: Object


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def obj(value: object, label: str) -> Object:
    if not isinstance(value, dict) or any(not isinstance(k, str) for k in value):
        raise ValueError(label + " must be a JSON object")
    return {k: v for k, v in value.items() if isinstance(k, str)}


def integer(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(label + " must be an integer, not bool")
    return value


def pending_instance(value: object) -> int | None:
    # Preparation imports this pure public module before selecting an SDK.
    # Only actual native-frame consumption needs the selected SDK contract.
    from xar_autoplayer.bridge.campaign_interaction_boundary_v1 import pending_instance_v1
    return pending_instance_v1(value)


def strings(value: object, label: str) -> set[str]:
    if not isinstance(value, list) or any(not isinstance(v, str) for v in value):
        raise ValueError(label + " must be a string list")
    return {v for v in value if isinstance(v, str)}


def native_day_advertised(report: Object) -> bool:
    raw = report.get("capabilities")
    if raw is None:
        return False
    caps = obj(raw, "actual capabilities")
    actions = strings(caps.get("action_steps", []), "actual action steps")
    bridge = strings(caps.get("bridge_capabilities", []), "actual bridge capabilities")
    return STEP in actions and _CLOCK_CAPABILITIES <= bridge


def native_day_request_count(report: Object, *, allow_actor_change: bool) -> int:
    """Count the fresh readonly frame plus one dispatch only on the native route."""
    need(type(allow_actor_change) is bool, "Original actor policy must be bool")
    return 2 if not allow_actor_change and native_day_advertised(report) else 1


def latest_frame(report: Object) -> Object:
    rows = report.get("steps", [])
    if not isinstance(rows, list):
        raise ValueError("Actual report steps must be a list")
    for raw in reversed(rows):
        row = obj(raw, "actual completed step")
        if row.get("finished_at") and row.get("ok") is True and row.get("after_snapshot") is not None:
            return obj(row["after_snapshot"], "latest actual after snapshot")
    return obj(report.get("readiness"), "actual readiness snapshot")


def frame_owner(frame: Object) -> tuple[int, int, int]:
    need(frame.get("source") == "injected-dll-named-pipe" and
         frame.get("backend_id") == "native-headless" and
         frame.get("episode_projection") == "native_campaign" and
         frame.get("map_ready") is True and frame.get("paused") is True,
         "Native day requires an actual paused native campaign frame")
    actor = obj(frame.get("played_character"), "actual played character")
    diagnostics = obj(frame.get("diagnostics"), "actual diagnostics")
    hello = obj(diagnostics.get("hello"), "actual hello")
    owner = (integer(diagnostics.get("bridge_pid"), "actual PID"),
             integer(diagnostics.get("connection_generation"), "actual generation"),
             integer(actor.get("character_id"), "actual actor"))
    need(all(v > 0 for v in owner) and actor.get("alive") is True and actor.get("source") == "native",
         "Native day requires a complete living owner")
    need(integer(hello.get("pid"), "hello PID") == owner[0] and
         integer(hello.get("connection_generation"), "hello generation") == owner[1] and
         hello.get("ck3_build_match") is True, "Native day hello owner/build differs")
    integer(frame.get("date_raw"), "actual date")
    need(integer(frame.get("revision"), "actual public revision") > 0 and
         integer(frame.get("native_revision"), "actual native revision") > 0,
         "Native day requires actual revisions")
    return owner


def fresh_native_day_before(previous: Object, fresh: Object, *,
                            allow_event_boundary: bool = False) -> Object:
    """Keep the current intent's owner/date while admitting a newer paused revision."""
    need(frame_owner(previous) == frame_owner(fresh), "Fresh native day crossed its original owner")
    need(previous.get("episode_run_id") == fresh.get("episode_run_id"),
         "Fresh native day crossed its original episode")
    need(integer(previous.get("date_raw"), "previous date") ==
         integer(fresh.get("date_raw"), "fresh date"), "Fresh native day changed its original date")
    need(type(allow_event_boundary) is bool, "Original event policy must be bool")
    if fresh.get("active_event") is not None:
        need(allow_event_boundary, "Native day begins event-free; observe the new event first")
        obj(fresh.get("active_event"), "actual fresh event")
    if pending_instance(fresh.get("pending_character_interaction")) is not None:
        need(allow_event_boundary, "Native day begins notification-free; observe the new notification first")
    for key in ("revision", "native_revision"):
        need(integer(fresh.get(key), "fresh " + key) >= integer(previous.get(key), "previous " + key),
             "Fresh native day revisions regressed")
    return fresh


def project_pre_day_event_boundary(previous: Object, fresh: Object, *,
                                   snapshot_step_id: str) -> Object:
    """Expose a real readonly event boundary without claiming a native day call."""
    fresh_native_day_before(previous, fresh, allow_event_boundary=True)
    need(previous.get("active_event") is None and previous.get("pending_character_interaction") is None,
         "Original native day begins without an unresolved interruption")
    need(fresh.get("active_event") is not None or pending_instance(fresh.get("pending_character_interaction")) is not None,
         "Actual new native interruption required")
    need(isinstance(snapshot_step_id, str) and snapshot_step_id.startswith("case-snapshot-") and
         snapshot_step_id.removeprefix("case-snapshot-").isdigit(), "Actual snapshot step ID required")
    source = "actual-pre-day-snapshot-event-boundary"
    result: NaturalDayResult = {
        "before": previous, "running_successor": None, "event_boundary": fresh,
        "after": fresh, "requested_days": 1,
        "target_date_raw": integer(previous.get("date_raw"), "previous date") + 24,
        "elapsed_hours": 0, "progress_status": "event_boundary_before_dispatch",
        "requested_interval_complete": False, "event_resolution": "typed_query_required",
        "preflight": {"source": source, "world_dispatch_attempted": False},
        "selected_event_options": 0,
        "actor_transition": {"allowed": False, "observed": False,
            "before": frame_owner(previous)[2], "after": frame_owner(fresh)[2],
            "predecessor_death_proved": False},
    }
    return {"id": snapshot_step_id, "ok": True, "error": None,
            "after_snapshot": fresh, "source": source,
            "world_dispatch_attempted": False, "result": result}


def project_native_day(row: Object, before: Object, *, allow_event_boundary: bool) -> Object:
    """Validate actual producer fields before exposing the old day contract."""
    need(row.get("ok") is True and not row.get("error"),
         "Native exact-day result is unknown/rejected; never repeat or fallback")
    value = obj(row.get("result"), "actual native exact-day result")
    after = obj(row.get("after_snapshot"), "actual native after snapshot")
    need(frame_owner(before) == frame_owner(after), "Native exact day crossed its original owner")
    start = integer(value.get("starting_date_raw"), "native start date")
    end = integer(value.get("ending_date_raw"), "native ending date")
    need(start == integer(before.get("date_raw"), "before date") and
         end == integer(after.get("date_raw"), "after date"), "Native day date binding differs")
    need(integer(after.get("revision"), "after revision") >= integer(before.get("revision"), "before revision") and
         integer(after.get("native_revision"), "after native revision") >= integer(before.get("native_revision"), "before native revision"),
         "Native day revisions regressed")
    need(value.get("step") == STEP and value.get("source") == "native-composite" and
         value.get("backend_id") == "native-headless" and value.get("paused") is True and
         integer(value.get("requested_horizon_days"), "native horizon") == 1,
         "Actual native exact-day producer contract missing")
    need(before.get("active_event") is None and before.get("pending_character_interaction") is None,
         "Original native day begins without an unresolved interruption")
    hours = end - start
    need(0 <= hours <= 24, "Native exact-day interval is outside its single intent")
    boundary: Object | None = None
    event = after.get("active_event")
    pending = after.get("pending_character_interaction")
    notification_id = pending_instance(pending)
    if event is not None:
        need(allow_event_boundary, "Actual event requires the caller's original boundary branch")
        obj(event, "actual current event")
        boundary = after
    if notification_id is not None:
        need(allow_event_boundary, "Actual notification requires the caller's original boundary branch")
        boundary = after
    need(hours == 24 or boundary is not None,
         "Native day neither completed 24h nor observed an allowed event boundary")
    need(value.get("active_event") == event,
         "Native result and independent actual after event differ")
    need("pending_character_interaction" in value and "pending_character_interaction" in after
         and value["pending_character_interaction"] == pending,
         "Native result and independent actual notification differ or are missing")
    ordinary = value.get("ordinary_events")
    need(isinstance(ordinary, list) and not ordinary,
         "Public native day must preserve events for the existing typed caller")
    progress, resolution = value.get("progress_status"), value.get("event_resolution")
    need(isinstance(progress, str) and isinstance(resolution, str), "Native progress fields missing")
    if not isinstance(progress, str) or not isinstance(resolution, str):
        raise ValueError("Native progress strings missing")
    result: NaturalDayResult = {
        "before": before, "running_successor": None, "event_boundary": boundary,
        "after": after, "requested_days": 1, "target_date_raw": start + 24,
        "elapsed_hours": hours, "progress_status": progress,
        "requested_interval_complete": hours == 24, "event_resolution": resolution,
        "preflight": {"source": "actual-life-advance-one-day", "actions": value.get("actions")},
        "selected_event_options": 0,
        "actor_transition": {"allowed": False, "observed": False,
            "before": frame_owner(before)[2], "after": frame_owner(after)[2],
            "predecessor_death_proved": False},
    }
    return {**row, "result": result}
