"""Ordinary-plan inputs from an already normalized current native options row."""

from __future__ import annotations


def _integer(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _boolean(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def assess_current_native_war_end_conditions_v1(
    war: dict[str, object],
    same_frame_options: dict[str, object] | None,
) -> dict[str, object]:
    """Project facts without selecting an exit or changing existing rules.

    The ordinary chooser supplies only a row accepted by its established
    same-frame check. A negative-query lease is not a current options row.
    """
    score = _integer(war.get("player_relative_war_score"))
    primary = war.get("player_is_primary_war_leader") is True
    result: dict[str, object] = {
        "schema_version": 1,
        "war_id": war.get("war_id"),
        "player_side": war.get("player_side"),
        "player_relative_war_score": score,
        "status": "current_options_not_published",
        "native_options": None,
        "native_nonloss_exit_available": None,
        "ordinary_war_input": None,
        "existing_score_victory_candidate": primary and score is not None and score >= 100,
        "required_native_input": None,
    }
    if same_frame_options is None:
        return result
    raw_options = same_frame_options.get("options")
    if not isinstance(raw_options, dict):
        return result
    options: dict[str, dict[str, object]] = {}
    for name in ("surrender", "white_peace", "victory"):
        row = raw_options.get(name)
        if not isinstance(row, dict):
            return result
        response = row.get("recipient_response")
        options[name] = {
            "outcome": row.get("outcome"),
            "context_constructed": _boolean(row.get("context_constructed")),
            "native_validator_passed": _boolean(row.get("native_validator_passed")),
            "available": _boolean(row.get("available")),
            "ai_acceptance": row.get("ai_acceptance"),
            "auto_accept": _boolean(row.get("auto_accept")),
            "recipient_response_status": (
                response.get("status") if isinstance(response, dict) else None
            ),
            "recipient_would_accept_now": (
                _boolean(response.get("would_accept_now"))
                if isinstance(response, dict) and response.get("status") == "available"
                else None
            ),
        }
    victory = options["victory"]["available"]
    white_peace = options["white_peace"]["available"]
    nonloss = (
        victory or white_peace
        if isinstance(victory, bool) and isinstance(white_peace, bool)
        else None
    )
    result.update({
        "status": "current_native_conditions_observed",
        "war_duration_days": same_frame_options.get("war_duration_days"),
        "active_casus_belli_identity": same_frame_options.get("active_casus_belli_identity"),
        "cb_allows_white_peace": same_frame_options.get("cb_allows_white_peace"),
        "native_options": options,
        "native_nonloss_exit_available": nonloss,
        "ordinary_war_input": (
            "existing_score_victory_policy"
            if result["existing_score_victory_candidate"]
            else "existing_terminal_defeat_policy"
            if primary and score is not None and score <= -100
            else "review_existing_exit_policy"
            if nonloss is True
            else "continue_war"
            if nonloss is False
            else "native_option_legality_unavailable"
        ),
        "required_native_input": (
            "current_white_peace_recipient_response"
            if white_peace is True
            and options["white_peace"]["recipient_would_accept_now"] is None
            else None
        ),
    })
    return result
