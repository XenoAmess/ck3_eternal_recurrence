"""Bounded reuse of a *completed* negative educate-child pair observation.

This never claims that a later Native query was performed or that a family
opportunity is empty.  It only defers this one guardian/ward pair's expensive
ordinary interaction query; marriage, focus and other children still run.
The service owns the in-memory records, so cold restoration starts with a
fresh query.  No business action is inferred from a query ACK.
"""

from __future__ import annotations

PERIOD_RAW = 30 * 24


def source_scope(frame: object, needs: object, heir_id: object) -> tuple | None:
    if not isinstance(frame, dict) or frame.get("status") != "complete":
        return None
    actor, child = frame.get("actor_character_id"), None
    if (type(actor) is not int or actor <= 0 or type(heir_id) is not int
            or heir_id <= 0 or type(frame.get("bridge_pid")) is not int
            or frame["bridge_pid"] <= 0 or type(frame.get("connection_generation")) is not int
            or frame["connection_generation"] <= 0 or not isinstance(frame.get("episode_run_id"), str)
            or not frame["episode_run_id"] or type(frame.get("date_raw")) is not int
            or type(frame.get("native_revision")) is not int
            or not isinstance(needs, dict)):
        return None
    child = needs.get("raw_character_id")
    values = needs.get("values")
    focus = needs.get("focus_management")
    court = needs.get("current_court_owner")
    provider = needs.get("education_provider_inputs")
    relation = needs.get("relation_materials")
    if (type(child) is not int or child <= 0 or not isinstance(values, dict)
            or values.get("status") != "available"
            or type(values.get("age_measure_raw")) is not int
            or not isinstance(focus, dict) or focus.get("available") is not True
            or not isinstance(court, dict) or court.get("available") is not True
            or court.get("source_qualified") is not True
            or court.get("owner_character_id_raw") != actor
            or not isinstance(provider, dict) or provider.get("status") != "available"
            or provider.get("collection_available") is not True
            or not isinstance(relation, dict) or relation.get("observed") is not True
            or relation.get("collection_available") is not True
            or needs.get("missing_observations") != []):
        return None
    provider_obs = provider.get("observation")
    relation_obs = relation.get("observation")
    named = relation_obs.get("guardian_named_material") if isinstance(relation_obs, dict) else None
    if (not isinstance(provider_obs, dict) or not isinstance(named, dict)
            or named.get("available") is not True
            or named.get("identity_round_trip") is not True
            or named.get("sample_stable") is not True
            or type(named.get("matched_peer_full_id")) is not int
            or named["matched_peer_full_id"] != actor):
        return None
    # A changed court/guardian/focus/child age is a new source scope.  Never
    # include the daily revision in the persistent scope: it is checked only
    # for same-frame reuse below.
    return (frame["bridge_pid"], frame["connection_generation"],
            frame["episode_run_id"], actor, heir_id, child,
            values["age_measure_raw"], values.get("sex_selector_raw"),
            focus.get("state"), focus.get("current_key"),
            court["owner_character_id_raw"],
            named["matched_peer_full_id"],
            provider_obs.get("guardian_full_id"),
            provider_obs.get("role_source"))


def deferred(records: dict, scope: tuple | None, frame: dict) -> dict | None:
    if scope is None or not isinstance(records, dict):
        return None
    child = scope[5]
    record = records.get(child)
    if not isinstance(record, dict) or record.get("scope") != scope:
        return None
    date, native_revision = frame.get("date_raw"), frame.get("native_revision")
    if type(date) is not int or type(native_revision) is not int:
        return None
    last_date = record.get("last_date_raw")
    if type(last_date) is not int or date < last_date:
        return None
    same_frame = (date == last_date and native_revision == record.get("last_native_revision"))
    until = record.get("cooldown_until_date_raw")
    active = type(until) is int and date < until
    if not same_frame and not active:
        return None
    return {"schema": "xar.ck3.family-guardian-negative-cadence/v1",
            "status": "same_frame_negative_reuse" if same_frame else "policy_deferred",
            "child_full_id": child, "guardian_full_id": scope[3],
            "last_observed_date_raw": last_date,
            "last_observed_native_revision": record["last_native_revision"],
            "cooldown_until_date_raw": until,
            "current_native_legal_status": "unknown_without_fresh_query",
            "business_action_credit": False}


def _negative_query(query: object, frame: dict, child: int, actor: int) -> dict | None:
    if not isinstance(query, dict):
        return None
    context = query.get("character_interaction_ordinary_context")
    roles = context.get("effective_roles") if isinstance(context, dict) else None
    if not (query.get("step") == "query-character-interaction-ordinary-v1"
            and query.get("accepted") is True and query.get("status") == "available"
            and query.get("read_only") is True
            and query.get("game_pid") == frame.get("bridge_pid")
            and query.get("connection_generation") == frame.get("connection_generation")
            and query.get("date_raw") == frame.get("date_raw")
            and query.get("queried_native_revision") == frame.get("native_revision")
            and query.get("queried_revision") == frame.get("revision")
            and isinstance(context, dict)
            and context.get("schema") == "ck3-character-interaction-ordinary-context-v1"
            and context.get("status") == "available"
            and context.get("source") == "native_current_ordinary_interaction_context_1.20.0.4"
            and context.get("read_only") is True
            and context.get("game_pid") == frame.get("bridge_pid")
            and context.get("connection_generation") == frame.get("connection_generation")
            and context.get("date_raw") == frame.get("date_raw")
            and context.get("snapshot_revision") == frame.get("native_revision")
            and context.get("interaction_key") == "educate_child_interaction"
            and context.get("player_character_id") == actor
            and context.get("recipient_id") == child
            and context.get("actor_alive") is True
            and context.get("recipient_alive") is True
            and context.get("shown") is False
            and context.get("can_send") is False
            and context.get("ready_to_initiate") is False
            and context.get("native_context_available") is True
            and context.get("ordinary_context_supported") is True
            and context.get("source_code_pins_verified") is True
            and context.get("actor_binding_verified") is True
            and context.get("recipient_binding_verified") is True
            and context.get("owner_thread_verified") is True
            and context.get("tls_verified") is True
            and context.get("frame_verified") is True
            and context.get("active_event_present") is False
            and context.get("incoming_interaction_present") is False
            and context.get("unavailable_reason") is None
            and isinstance(context.get("executable_sha256"), str)
            and len(context["executable_sha256"]) == 64
            and type(context.get("definition_stable_hash")) is int
            and isinstance(roles, dict)
            and roles.get("actor_id") == actor
            and roles.get("recipient_id") == actor
            and roles.get("secondary_actor_id") == actor
            and roles.get("secondary_recipient_id") == child):
        return None
    return context


def observe(records: dict, scope: tuple | None, frame: dict,
            default_query: object, attempts: object, *, selected_step: str) -> dict | None:
    """Count one new date only after both exact Native reads reject this pair."""
    if (scope is None or selected_step != "life-advance"
            or not isinstance(attempts, list) or len(attempts) != 1):
        return None
    child, actor = scope[5], scope[3]
    first = _negative_query(default_query, frame, child, actor)
    attempt = attempts[0]
    if not isinstance(attempt, dict) or attempt.get("variant") != "observed_selected_options":
        return None
    second = _negative_query(attempt.get("query"), frame, child, actor)
    if not isinstance(first, dict) or not isinstance(second, dict):
        return None
    material = second.get("education_request_materialization")
    if not (first.get("selected_option_count") == 0
            and second.get("selected_option_count") == 0
            and type(default_query.get("query_sequence")) is int
            and type(attempt["query"].get("query_sequence")) is int
            and default_query["query_sequence"] != attempt["query"]["query_sequence"]
            and first.get("definition_stable_hash") == second.get("definition_stable_hash")
            and first.get("executable_sha256") == second.get("executable_sha256")
            and isinstance(material, dict)
            and material.get("status") == "available"
            and material.get("child_full_id") == child
            and material.get("guardian_full_id") == actor
            and material.get("requested_option_keys") == []
            and material.get("pair_matches") is True
            and material.get("option_keys_match") is True):
        return None
    date, native_revision = frame["date_raw"], frame["native_revision"]
    previous = records.get(child)
    same_scope = isinstance(previous, dict) and previous.get("scope") == scope
    if same_scope and previous.get("last_date_raw") == date:
        return None  # A second plan in the same AUTO is not a second date.
    if same_scope and type(previous.get("last_date_raw")) is int and date < previous["last_date_raw"]:
        return None
    until = previous.get("cooldown_until_date_raw") if same_scope else None
    # Initial activation needs two different dates. Once established, a
    # completed negative at expiry rolls the next review forward by 30 days.
    count = min(2, previous.get("count", 0) + 1) if same_scope else 1
    if count >= 2:
        until = date + PERIOD_RAW
    record = {"scope": scope, "count": count, "last_date_raw": date,
              "last_native_revision": native_revision,
              "cooldown_until_date_raw": until,
              "last_executable_sha256": first["executable_sha256"],
              "last_definition_stable_hash": first["definition_stable_hash"]}
    records[child] = record
    return {"schema": "xar.ck3.family-guardian-negative-cadence/v1",
            "status": "negative_observed", "child_full_id": child,
            "guardian_full_id": actor, "consecutive_observed_dates": count,
            "last_observed_date_raw": date,
            "cooldown_until_date_raw": until,
            "business_action_credit": False}
