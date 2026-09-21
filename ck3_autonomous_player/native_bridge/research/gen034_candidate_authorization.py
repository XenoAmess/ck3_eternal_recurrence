"""Canonical terminal authorization binding for the GEN-034-D handoff."""

from __future__ import annotations

import hashlib
import json
import re


SCHEMA = "xar.ck3.gen034_d_terminal_authorization.v1"


class CandidateAuthorizationError(ValueError):
    """A frozen terminal selection and its recomputation disagree."""


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise CandidateAuthorizationError(f"{name} must be a positive integer")
    return value


def _sha256(value: object, name: str) -> str:
    result = str(value).strip().upper()
    if re.fullmatch(r"[0-9A-F]{64}", result) is None:
        raise CandidateAuthorizationError(f"{name} must be an uppercase SHA-256")
    return result


def terminal_authorization_v1(
    *,
    selected_step: object,
    recommended_outcome: object,
    war_id: object,
    opponent_character_id: object,
    source_capture_sha256: object,
) -> dict[str, object]:
    bound_war_id = _positive_int(war_id, "WarID")
    opponent = _positive_int(opponent_character_id, "opponent CharacterID")
    outcome = str(recommended_outcome)
    if outcome not in {"white_peace", "surrender"}:
        raise CandidateAuthorizationError("terminal outcome must be white_peace or surrender")
    expected_step = (
        f"offer-white-peace-{bound_war_id}"
        if outcome == "white_peace"
        else f"surrender-war-{bound_war_id}"
    )
    if selected_step != expected_step:
        raise CandidateAuthorizationError(
            f"terminal step/outcome mismatch: {selected_step!r} != {expected_step!r}"
        )
    payload = {
        "schema": SCHEMA,
        "selected_step": expected_step,
        "recommended_outcome": outcome,
        "war_id": bound_war_id,
        "opponent_character_id": opponent,
        "source_capture_sha256": _sha256(
            source_capture_sha256, "source capture SHA-256"
        ),
    }
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return {
        "payload": payload,
        "sha256": hashlib.sha256(canonical).hexdigest().upper(),
    }


def require_matching_terminal_authorization_v1(
    actual: dict[str, object],
    *,
    expected_step: object,
    expected_outcome: object,
    expected_sha256: object,
) -> dict[str, object]:
    payload = actual.get("payload")
    digest = str(actual.get("sha256", "")).upper()
    if not isinstance(payload, dict):
        raise CandidateAuthorizationError("terminal authorization payload is missing")
    if (
        payload.get("selected_step") != expected_step
        or payload.get("recommended_outcome") != expected_outcome
        or digest != _sha256(expected_sha256, "expected terminal authorization SHA-256")
    ):
        raise CandidateAuthorizationError(
            "recomputed terminal authorization differs from the frozen selection"
        )
    return actual
