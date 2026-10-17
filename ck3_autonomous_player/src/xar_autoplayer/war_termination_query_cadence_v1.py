"""Per-war query scheduling after two observed no-action termination checks.

This is only a policy defer.  It never turns historical options into native
legality, a negative assessment, or business-action credit.
"""

from __future__ import annotations

from collections.abc import Iterable

from .bridge.war_contract import (
    parse_query_war_termination_options_step,
    war_termination_active_war_signature,
    war_termination_negative_query_signature,
)


_LEASE_RAW = 30 * 24


def _positive_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else None


def _stable_wars(value: object) -> list[dict[str, object]] | None:
    signature = war_termination_active_war_signature(value)
    if signature is None or not signature:
        return None
    return [
        {key: item for key, item in row.items() if key != "player_relative_war_score"}
        for row in signature
    ]


def _terminal_action(step: object) -> bool:
    return isinstance(step, str) and (
        step == "war-enforce-demands"
        or step.startswith(("enforce-demands-", "offer-white-peace-", "surrender-war-"))
        or step.startswith(("query-war-termination-terms-", "query-war-termination-exit-terms-"))
    )


def _priority_barrier(step: object) -> bool:
    return isinstance(step, str) and (
        step in {
            "resolve-current-event", "query-current-event-window-context-v1",
            "query-pending-character-interaction-context-v1",
            "acknowledge-pending-character-interaction",
            "death-terminal", "start-next-episode",
        }
        or step.startswith(("select-event-option-", "accept-pending-character-interaction", "reject-pending-character-interaction"))
    )


def _positive_exit(options: dict[str, object]) -> bool:
    rows = options.get("options")
    if not isinstance(rows, dict):
        return True
    victory = rows.get("victory")
    white_peace = rows.get("white_peace")
    if not isinstance(victory, dict) or not isinstance(white_peace, dict):
        return True
    response = white_peace.get("recipient_response")
    return bool(
        victory.get("available") is True
        or (
            white_peace.get("available") is True
            and (
                (white_peace.get("auto_accept_observable") is True and white_peace.get("auto_accept") is True)
                or (
                    isinstance(response, dict)
                    and response.get("status") == "available"
                    and response.get("would_accept_now") is True
                )
            )
        )
    )


def _known_duration_boundary_raw(options: dict[str, object], queried_raw: int) -> int | None:
    """Do not skip known 365-day claim or 180-day de-jure legality edges."""
    cb = options.get("active_casus_belli_identity")
    duration = options.get("war_duration_days")
    if not isinstance(cb, dict) or not isinstance(duration, int) or isinstance(duration, bool):
        return None
    if options.get("player_side") != "attacker" or options.get("player_is_primary_war_leader") is not True:
        return None
    key = cb.get("canonical_key")
    if key == "claim_cb" and options.get("cb_allows_white_peace") is True and 0 <= duration < 365:
        return queried_raw + (365 - duration) * 24
    if key == "individual_county_de_jure_cb" and 0 <= duration < 180:
        return queried_raw + (180 - duration) * 24
    return None


def war_termination_query_policy_defer_v1(
    snapshot: dict[str, object],
    active_wars: list[dict[str, object]],
    war: dict[str, object],
    recent_records: Iterable[dict[str, object]],
) -> dict[str, object] | None:
    """Return a scheduling defer, never native options or a business result.

    ``recent_records`` is newest-first and may stop once two valid, distinct-
    date checks are found.  Any unknown/terminal write breaks the streak.
    """
    if (
        snapshot.get("paused") is not True
        or snapshot.get("map_ready") is not True
        or snapshot.get("one_life_terminal_reason") is not None
        or isinstance(snapshot.get("active_event"), dict)
        or isinstance(snapshot.get("pending_character_interaction"), dict)
    ):
        return None
    modal = snapshot.get("top_exclusive_modal_choice_hint")
    if isinstance(modal, dict) and modal.get("status") == "present":
        return None
    played = snapshot.get("played_character")
    actor = _positive_int(played.get("character_id")) if isinstance(played, dict) and played.get("alive") is True else None
    date_raw = _positive_int(snapshot.get("date_raw"))
    war_id = _positive_int(war.get("war_id"))
    score = war.get("player_relative_war_score")
    episode = snapshot.get("episode_run_id")
    diagnostics = snapshot.get("diagnostics")
    connection = _positive_int(diagnostics.get("connection_generation")) if isinstance(diagnostics, dict) else None
    stable_wars = _stable_wars(active_wars)
    if (
        actor is None or date_raw is None or war_id is None or connection is None
        or not isinstance(episode, str) or not episode or stable_wars is None
        or not isinstance(score, int) or isinstance(score, bool)
        or not -100 < score < 100
    ):
        return None
    matches = [row for row in stable_wars if row.get("war_id") == war_id]
    if len(matches) != 1:
        return None
    current_cb = war.get("active_casus_belli_identity")
    dates: list[int] = []
    queries: list[int] = []
    cb_identity: dict[str, object] | None = None
    expiry = 0
    for record in recent_records:
        if not isinstance(record, dict):
            return None
        step = record.get("step")
        result = record.get("result")
        if (
            step == "restore-checkpoint" or _terminal_action(step)
            or _priority_barrier(step)
            or (isinstance(result, dict) and isinstance(result.get("war_action"), dict))
        ):
            return None
        if not isinstance(step, str):
            continue
        queried_war_id = parse_query_war_termination_options_step(step)
        if queried_war_id != war_id:
            if step.startswith("query-war-termination-options-") and queried_war_id is None:
                return None
            continue
        context = result.get("termination_query_context") if isinstance(result, dict) else None
        options = result.get("war_termination_options") if isinstance(result, dict) else None
        signature = war_termination_negative_query_signature(options)
        if not (
            record.get("ok") is True
            and isinstance(result, dict)
            and result.get("step") == step
            and result.get("accepted") is True
            and result.get("status") == "available"
            and isinstance(context, dict)
            and context.get("schema_version") == 1
            and _stable_wars(context.get("active_war_signature")) == stable_wars
            and context.get("queried_episode_run_id") == episode
            and context.get("queried_connection_generation") == connection
            and context.get("queried_character_id") == actor
            and isinstance(options, dict)
            and signature is not None
            and context.get("negative_decision_signature") == signature
            and signature.get("war_id") == war_id
            and context.get("queried_war_duration_days") == options.get("war_duration_days")
            and options.get("active_casus_belli_present") is True
            and isinstance(options.get("active_casus_belli_identity"), dict)
            and _positive_int(options["active_casus_belli_identity"].get("database_index")) is not None
            and isinstance(options["active_casus_belli_identity"].get("canonical_key"), str)
            and not _positive_exit(options)
        ):
            return None
        queried_date = _positive_int(context.get("queried_date_raw"))
        query_sequence = _positive_int(result.get("query_sequence"))
        if queried_date is None or query_sequence is None or queried_date > date_raw:
            return None
        observed_cb = options["active_casus_belli_identity"]
        if cb_identity is None:
            cb_identity = observed_cb
        if observed_cb != cb_identity or (isinstance(current_cb, dict) and current_cb != cb_identity):
            return None
        if dates and queried_date == dates[-1]:
            continue
        if dates and (queried_date > dates[-1] or query_sequence >= queries[-1]):
            return None
        dates.append(queried_date)
        queries.append(query_sequence)
        if len(dates) == 1:
            expiry = min(
                queried_date + _LEASE_RAW,
                _known_duration_boundary_raw(options, queried_date) or queried_date + _LEASE_RAW,
            )
        if len(dates) == 2:
            break
    if len(dates) != 2 or not (dates[1] < dates[0] < date_raw < expiry):
        return None
    return {
        "status": "policy_deferred_after_two_no_action_queries",
        "war_id": war_id,
        "latest_queried_date_raw": dates[0],
        "previous_queried_date_raw": dates[1],
        "latest_query_sequence": queries[0],
        "expires_date_raw": expiry,
        "fresh_native_result": False,
        "native_legality": None,
        "business_action_credit": 0,
        "last_observed_cb_identity": dict(cb_identity),
        "current_cb_identity_status": "unknown_without_fresh_native_query",
        "source": "history_policy_only",
    }
