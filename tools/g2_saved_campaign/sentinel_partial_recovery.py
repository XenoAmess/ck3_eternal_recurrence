"""Exact post-submit partial sentinel observation; no replay and no failed credit."""
import copy
from datetime import datetime
import re

MODE = "sentinel_player_decision_boundary_partial"

SCHEMA = "g2.queue.sentinel-player-decision-partial-recovery/v1"

ERROR = re.compile(r"Error executing tool ck3_auto_turn: native (?P<step>war-objective-hold-sentinel-advance-war-(?P<war>[1-9][0-9]{0,9})-army-(?P<army>0|[1-9][0-9]{0,9})-at-(?P<province>[1-9][0-9]{0,9})-until-(?P<until>[1-9][0-9]{0,18})-speed-(?P<speed>[45])) postcondition failed: native tactical sentinel player-decision boundary did not stabilize on one fresh paused frame")

def require(value, message):
    if not value:
        raise ValueError("sentinel partial recovery denied: " + message)

def qualify(row, plan_row, state, launch):
    """Pure exact-error, real before-submit plan and unsettled-cycle binding."""
    request = row.get("request") if isinstance(row, dict) else None
    result = row.get("result") if isinstance(row, dict) else None
    require(isinstance(request, dict) and request.get("tool") == "ck3_auto_turn"
        and request.get("arguments") == {} and type(request.get("sequence")) is int
        and request["sequence"] > 0 and row.get("client_error") is None,
        "original completed AUTO identity differs")
    require(isinstance(result, dict) and result.get("is_error") is True
        and result.get("result_type") == "complete" and result.get("structured_content") is None,
        "original must remain a completed error, never success")
    content = result.get("content")
    require(isinstance(content, list) and len(content) == 1 and content[0].get("type") == "text"
        and isinstance(content[0].get("text"), str), "one exact native error required")
    match = ERROR.fullmatch(content[0]["text"])
    require(match is not None, "error is outside the reviewed sentinel interruption")
    values = {key: int(match[key]) for key in ("war", "army", "province", "until", "speed")}
    require(values["war"] < 2**32 and values["army"] < 2**31 and values["province"] < 2**32,
            "canonical IDs out of range")
    before = state.get("before") or {}
    pending = state.get("pending_cycle") or {}
    require(type(state.get("completed_cycles")) is int
        and pending.get("global_turn") == state["completed_cycles"] + 1
        and pending.get("auto_sequence") == request["sequence"] and pending.get("stage") == "auto_unsettled"
        and pending.get("before") == before and state.get("pending_checkpoint") is None
        and state.get("terminal") is None, "exact unsettled original cycle required")
    delta = values["until"] - before.get("date_raw", values["until"])
    require(24 <= delta <= 7 * 24 and delta % 24 == 0, "original bounded hold deadline differs")
    body = (plan_row.get("result") or {}).get("structured_content") or {}
    plan = body.get("plan") or {}
    require(plan_row.get("source") == "actual GameplayBridgeService.before_submit callback"
        and plan_row.get("game_pid") == launch["pid"]
        and plan_row.get("game_creation_date") == launch["creation_date"]
        and plan_row.get("request") == {"tool": "root_before_auto_turn_submit", "parent_sequence": request["sequence"]}
        and (plan_row.get("result") or {}).get("is_error") is False
        and body.get("status") == "planned" and plan.get("policy") == "one-life-turn-v1"
        and plan.get("phase") == "native_war_stationary_objective_hold_sentinel"
        and plan.get("selected_step") == body.get("selected_step") == match["step"]
        and body.get("snapshot_id") == before.get("snapshot_id")
        and body.get("revision") == before.get("revision"), "original before-submit source/plan differs")
    try:
        started = datetime.fromisoformat(row["started_at_utc"])
        planned = datetime.fromisoformat(plan_row["ended_at_utc"])
        ended = datetime.fromisoformat(row["ended_at_utc"])
        require(all(value.tzinfo is not None for value in (started, planned, ended))
                and started <= planned <= ended, "before-submit timing differs")
    except (KeyError, TypeError):
        raise ValueError("sentinel partial recovery denied: completed request timing missing")
    return {"actual_recovery_kind": MODE, "selected_step": match["step"], **values,
        "original_submission_may_have_applied": True, "read_only_precondition": False,
        "original_action_replayed": False, "failed_pending_cycle_credit": 0,
        "failed_pending_date_credit": 0, "failed_pending_business_credit": 0}

def decision_identity(body):
    event, interaction = body.get("active_event"), body.get("pending_character_interaction")
    if isinstance(event, dict):
        require(interaction is None and type(event.get("instance_id")) is int
                and event["instance_id"] > 0 and type(event.get("option_count")) is int
                and event["option_count"] > 0,
                "one complete event identity required")
        return ("event", event["instance_id"])
    if isinstance(interaction, dict):
        require(event is None and bool(interaction),
                "one complete interaction identity required")
        # No ordinary interaction selector is run by this recovery. Strict
        # equality at the second read prevents silently consuming a new one.
        return ("interaction", copy.deepcopy(interaction))
    raise ValueError("known pause recovery denied: no current event or interaction")

def checked_semantic(body, *, before, launch, lifecycle, normalize_lifecycle,
                     expected_paused, previous=None):
    require(isinstance(body, dict) and body.get("map_ready") is True
            and body.get("paused") is expected_paused
            and body.get("one_life_terminal") is False,
            "actual map/pause/one-life state differs")
    played, diagnostics = body.get("played_character"), body.get("diagnostics")
    require(isinstance(played, dict) and played.get("alive") is True
            and type(played.get("character_id")) is int
            and isinstance(diagnostics, dict), "living actor or Native diagnostics absent")
    hello = diagnostics.get("hello")
    require(isinstance(hello, dict) and type(launch.get("pid")) is int
            and diagnostics.get("bridge_pid") == hello.get("pid") == launch["pid"]
            and type(diagnostics.get("connection_generation")) is int
            and diagnostics["connection_generation"] == hello.get("connection_generation"),
            "same Game PID and Native connection are unproven")
    require(type(body.get("revision")) is int and body["revision"] >= 0
            and type(body.get("native_revision")) is int and body["native_revision"] > 0
            and isinstance(body.get("snapshot_id"), str) and body["snapshot_id"]
            and type(body.get("date_raw")) is int
            and body["date_raw"] >= before["date_raw"]
            and played["character_id"] == before["actor_character_id"]
            and body.get("episode_run_id") == before["episode_run_id"]
            and normalize_lifecycle(body.get("succession_lifecycle")) == lifecycle,
            "actor/episode/date/revision/lifecycle binding differs")
    identity = decision_identity(body)
    if previous is not None:
        require(identity == previous["decision_identity"]
                and body["date_raw"] >= previous["date_raw"]
                and body["revision"] >= previous["revision"]
                and body["native_revision"] >= previous["native_revision"]
                and diagnostics["connection_generation"] == previous["connection_generation"],
                "decision/connection/revision changed during pause")
    return {
        "snapshot_id": body["snapshot_id"], "revision": body["revision"],
        "native_revision": body["native_revision"], "date_raw": body["date_raw"],
        "actor_character_id": played["character_id"],
        "episode_run_id": body["episode_run_id"],
        "decision_identity": identity,
        "connection_generation": diagnostics["connection_generation"],
    }

def projected_state(state, final_frame, receipt_path):
    """Retain all settled credit; only abandon the failed pending branch."""
    projected = copy.deepcopy(state)
    prior = state["before"]
    require(final_frame["date_raw"] >= prior["date_raw"], "date regressed")
    compact = {key: final_frame[key] for key in (
        "snapshot_id", "revision", "native_revision", "date_raw",
        "actor_character_id", "episode_run_id",
    )}
    projected["before"] = compact
    projected["before_metrics_response"] = str(receipt_path)
    projected["pending_cycle"] = None
    projected["checkpoint_dirty_since_save"] = bool(
        state.get("checkpoint_dirty_since_save") or compact["date_raw"] > prior["date_raw"]
    )
    projected["known_pause_recovery_last"] = {
        "schema": SCHEMA, "receipt": str(receipt_path),
        "failed_pending_credit": 0, "original_auto_replayed": False,
    }
    return projected

def qualify_stable_observations(first_body, second_body, *, before, launch,
        lifecycle, normalize_lifecycle, normalize_pending_interaction_id,
        until, expected_birth, observed_births):
    """Caller supplies two actual fresh reads and their same kernel generation."""
    require(type(expected_birth) is int and expected_birth > 0
        and observed_births == (expected_birth, expected_birth), "full Game birth changed")
    first = checked_semantic(first_body, before=before, launch=launch,
        lifecycle=lifecycle, normalize_lifecycle=normalize_lifecycle, expected_paused=True)
    second = checked_semantic(second_body, before=before, launch=launch,
        lifecycle=lifecycle, normalize_lifecycle=normalize_lifecycle, expected_paused=True, previous=first)
    for body, frame in ((first_body, first), (second_body, second)):
        require(frame["date_raw"] <= until and frame["revision"] >= before["revision"]
            and frame["native_revision"] >= before["native_revision"], "clock bound/revision changed")
        interaction = body.get("pending_character_interaction")
        if isinstance(interaction, dict):
            require(normalize_pending_interaction_id(interaction.get("instance_id"))
                    == interaction["instance_id"]
                and type(interaction.get("sender_character_id")) is int and interaction["sender_character_id"] > 0
                and interaction.get("source") == "native" and type(interaction.get("auto_accept_notification")) is bool,
                "complete native interaction identity required")
    require(first == second, "fresh paused observation changed")
    return second
