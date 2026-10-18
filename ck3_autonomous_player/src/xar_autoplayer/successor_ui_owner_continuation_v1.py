"""Continue an already fully verified natural handoff without replaying it.

The owner supplies its original timeline/Close validators. UI observation is
separate from title reconciliation, goal progression and checkpoint proof.
"""
from __future__ import annotations

from copy import deepcopy

from .errors import AgentError
from .bridge.driver import BridgeUnavailableError, UnsupportedStepError


def continue_verified_successor_ui_v1(service, *, transition, snapshot, attempt,
                                    classify_timeline, close_issue, capture_failure,
                                    previous_observation=None, durability=None, before_close=None, allow_close=True):
    """Return (current snapshot, player-decision pending, date advanced, UI pending)."""
    prior = transition.get("timeline_blocker_continuation")
    if isinstance(prior, dict) and prior.get("close_attempted") is True:
        raise AgentError("successor typed Close was already attempted; do not resend")
    if previous_observation is not None and not isinstance(prior, dict):
        raise AgentError("successor UI lost its original deferred query")
    revision, date = snapshot.get("revision"), snapshot.get("date_raw")
    successor = transition["successor_character_id"]
    episode = transition["episode_run_id"]
    attempt["stage"] = "ordinary_successor_timeline_query"
    try:
        query = service.query_current_timeline_blocker_context_v1(expected_revision=revision)
    except (BridgeUnavailableError, UnsupportedStepError, ValueError) as error:
        capture_failure(stage="ordinary_successor_timeline_query",
                        kind="natural_succession_timeline_query_failed", message=str(error), error=error)
        raise AgentError("ordinary natural successor timeline query failed: " + str(error)) from error
    state = classify_timeline(query)
    observation = None
    cold = transition.get("_successor_ui_cold_binding_v1")
    if isinstance(snapshot.get("active_event"), dict) or previous_observation is not None or cold is not None:
        # Only this new event shape needs the strict Service projection. The
        # original, already qualified modal and clear routes keep their guard.
        try:
            observation = service.observe_verified_successor_ui_v1(
                transition=transition, snapshot=snapshot, timeline_query=query,
                previous_observation=previous_observation, cold_resume_binding=cold)
        except (BridgeUnavailableError, UnsupportedStepError, ValueError) as error:
            capture_failure(stage="ordinary_successor_timeline_query",
                            kind="natural_succession_ui_projection_invalid", message=str(error), error=error)
            raise AgentError("ordinary successor UI observation failed: " + str(error)) from error
        transition["successor_ui_observation"] = deepcopy(observation)
        transition.pop("_successor_ui_cold_binding_v1", None)
        if observation["event_instance_id"] is not None:
            # This defers the checkpoint, not the event's original policy.
            # No semantic/effect claim or SAVE/Close permission follows.
            state = "deferred_player_decision"
        elif observation["ui_clearance"] == "clear":
            if state != "already_clear":
                state = None
        elif observation["ui_clearance"] != "modal_present" or state != "close_required":
            state = None
    if isinstance(snapshot.get("pending_character_interaction"), dict):
        state = "deferred_player_decision"
    if state is None:
        capture_failure(stage="ordinary_successor_timeline_query",
                        kind="natural_succession_timeline_state_ambiguous",
                        message="ordinary successor timeline state is neither a bound death modal nor independently clear")
        raise AgentError("ordinary successor timeline state is ambiguous")
    continuation = {"status": state, "initial_query": deepcopy(query), "close_result": None}
    if previous_observation is not None:
        continuation["deferred_event_observation"] = deepcopy(previous_observation)
        continuation["original_deferred_query"] = deepcopy(prior.get("initial_query"))
    transition["timeline_blocker_continuation"] = continuation
    if state == "deferred_player_decision":
        continuation["ui_clearance_verified"] = False
        if durability is not None:
            durability.update(transition, snapshot)
        return snapshot, True, False, True
    if state != "close_required":
        pending = isinstance(snapshot.get("active_event"), dict) or isinstance(snapshot.get("pending_character_interaction"), dict)
        if durability is not None:
            if pending:
                durability.update(transition, snapshot)
                return snapshot, True, False, True
            durability.resolve(transition, snapshot)
        return snapshot, pending, False, False
    attempt["stage"] = "ordinary_successor_timeline_close"
    if allow_close is not True:
        if durability is not None:
            durability.update(transition, snapshot)
        return snapshot, False, False, True
    if before_close is not None:
        intercepted = before_close({"plan": {"selected_step": "continue-death-succession-modal-v1",
            "phase": "ordinary_successor_timeline_close",
            "reason": "Verified natural successor; current native modal requires one typed Close."},
            "selected_step": "continue-death-succession-modal-v1",
            "snapshot_id": snapshot.get("snapshot_id"), "revision": revision})
        if intercepted is not None:
            if not isinstance(intercepted, dict):
                raise TypeError("successor Close before_submit must return a mapping or None")
            continuation.update(status="deferred_owner_interception", owner_interception=deepcopy(intercepted))
            if durability is not None:
                durability.update(transition, snapshot)
            return snapshot, False, False, True
    # Set before calling the original typed route. An exception, ACK-only or
    # failed independent postcondition must never arm another invocation.
    continuation["close_attempted"] = True
    arguments = dict(expected_revision=revision, expected_played_character_id=successor,
                     expected_episode_run_id=episode)
    if durability is not None:
        durability.begin_close(transition, snapshot, arguments)
    try:
        result = service.continue_death_succession_modal_private_v1(**arguments)
    except (BridgeUnavailableError, UnsupportedStepError, ValueError) as error:
        capture_failure(stage="ordinary_successor_timeline_close",
                        kind="natural_succession_timeline_close_failed", message=str(error), error=error)
        raise AgentError("ordinary natural successor typed Close failed: " + str(error)) from error
    continuation["close_result"] = deepcopy(result)
    if durability is not None:
        durability.retain_close_result(result)
    issue = close_issue(result, starting_date_raw=date, successor_character_id=successor)
    if issue is not None:
        capture_failure(stage="ordinary_successor_timeline_close",
                        kind="natural_succession_timeline_close_" + issue,
                        message="ordinary successor typed Close lacks its material postcondition: " + issue)
        raise AgentError("ordinary successor typed Close lacks its material postcondition: " + issue)
    current = service.snapshot()
    played = current.get("played_character")
    if not (isinstance(played, dict) and played.get("alive") is True
            and played.get("character_id") == successor
            and current.get("episode_character_id") == successor and current.get("episode_run_id") == episode
            and current.get("date_raw") == result.get("ending_date_raw")
            and current.get("revision") == result.get("ending_revision")
            and current.get("native_revision") == result.get("ending_native_revision")):
        continuation["status"] = "independent_identity_unverified"
        raise AgentError("ordinary successor changed identity after typed Close")
    continuation["status"] = "materially_cleared"
    if durability is not None:
        durability.resolve(transition, current)
    pending = isinstance(current.get("active_event"), dict) or isinstance(current.get("pending_character_interaction"), dict)
    return current, pending, True, False
