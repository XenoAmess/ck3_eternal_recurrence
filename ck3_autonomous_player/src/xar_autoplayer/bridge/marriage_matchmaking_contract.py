"""Typed consumer for the exact-build, private ranked marriage observation.

This is a read-only intake contract. The native route remains unregistered until
its paused production query and bilateral result gates have passed.
"""

from __future__ import annotations


_BUILD = "1.19.0.6"
_READY_KEYS = {
    "ranked_candidates_ready",
    "pair_character_ids_ready",
    "native_score_ready",
    "complete_can_send_ready",
    "recipient_ai_accept_ready",
    "recipient_answer_ready",
    "predicted_outcome_ready",
    "same_frame_ready",
}
_CANDIDATE_KEYS = {
    "rank",
    "subject_character_id",
    "matchmaker_character_id",
    "candidate_character_id",
    "native_candidate_score",
    "pair_roles",
    "complete_can_send",
    "complete_can_send_status_raw",
    "recipient_ai_accept_raw",
    "recipient_ai_accept_scale",
    "recipient_answer_status_raw",
    "recipient_answer_allows_send",
    "predicted_outcome",
}
_ROLE_KEYS = {
    "actor_character_id",
    "recipient_character_id",
    "secondary_actor_character_id",
    "secondary_recipient_character_id",
    "intermediary_character_id",
}


def normalize_ranked_marriage_observation(
    value: object,
    *,
    snapshot_id: str,
    public_revision: int,
    native_revision: int,
    date_raw: int,
    played_character_id: int,
) -> dict[str, object]:
    """Accept only the private observer's same-frame direct-player payload."""
    if not isinstance(value, dict) or value.get("status") != "available":
        raise ValueError("ranked marriage observation is unavailable")
    expected = {
        "private_build", "advertised", "status", "exact_build", "snapshot_id",
        "public_revision", "native_revision", "proof_epoch", "date_raw",
        "subject_character_id", "matchmaker_character_id",
        "religion_projection", "candidates", "readiness",
    }
    if set(value) != expected or value["private_build"] is not True or value["advertised"] is not False:
        raise ValueError("ranked marriage observation schema is malformed")
    if value["exact_build"] != _BUILD or value["religion_projection"] != "native_final_results_only":
        raise ValueError("ranked marriage exact-build or result provenance changed")
    if (
        value["snapshot_id"] != snapshot_id
        or value["public_revision"] != public_revision
        or value["native_revision"] != native_revision
        or value["date_raw"] != date_raw
        or value["subject_character_id"] != played_character_id
        or value["matchmaker_character_id"] != played_character_id
    ):
        raise ValueError("ranked marriage observation is not the current played-character frame")
    if not isinstance(snapshot_id, str) or snapshot_id != f"native:{native_revision}":
        raise ValueError("ranked marriage snapshot identity is malformed")
    for name in ("public_revision", "native_revision", "proof_epoch"):
        _integer(value[name], name, minimum=1, maximum=2**64 - 1)
    for name in ("subject_character_id", "matchmaker_character_id"):
        _integer(value[name], name, minimum=1, maximum=2**32 - 1)
    _integer(value["date_raw"], "date_raw", minimum=-(2**31), maximum=2**31 - 1)
    readiness = value["readiness"]
    if not isinstance(readiness, dict) or set(readiness) != _READY_KEYS or any(item is not True for item in readiness.values()):
        raise ValueError("ranked marriage observation is not decision-ready")
    rows = value["candidates"]
    if not isinstance(rows, list) or len(rows) > 8:
        raise ValueError("ranked marriage candidates exceed the native bound")
    seen: set[int] = set()
    previous_rank = 0
    normalized: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != _CANDIDATE_KEYS:
            raise ValueError("ranked marriage candidate schema is malformed")
        candidate = _integer(row["candidate_character_id"], "candidate_character_id", minimum=1, maximum=2**32 - 1)
        if candidate in seen or candidate == played_character_id:
            raise ValueError("ranked marriage contains a duplicate or self candidate")
        seen.add(candidate)
        rank = _integer(row["rank"], "rank", minimum=1, maximum=8)
        if rank <= previous_rank or row["subject_character_id"] != played_character_id or row["matchmaker_character_id"] != played_character_id:
            raise ValueError("ranked marriage candidate order or subject drifted")
        previous_rank = rank
        _integer(row["native_candidate_score"], "native_candidate_score", minimum=-(2**31), maximum=2**31 - 1)
        for name in ("complete_can_send_status_raw", "recipient_ai_accept_raw", "recipient_answer_status_raw"):
            _integer(row[name], name, minimum=-(2**31), maximum=2**31 - 1)
        if row["recipient_ai_accept_scale"] != 100000:
            raise ValueError("ranked marriage acceptance scale changed")
        if type(row["complete_can_send"]) is not bool or type(row["recipient_answer_allows_send"]) is not bool:
            raise ValueError("ranked marriage legality is not boolean")
        if row["predicted_outcome"] not in {"marriage", "betrothal"}:
            raise ValueError("ranked marriage outcome is unknown")
        roles = row["pair_roles"]
        if not isinstance(roles, dict) or set(roles) != _ROLE_KEYS:
            raise ValueError("ranked marriage pair roles are malformed")
        for name, role in roles.items():
            _integer(role, name, minimum=0, maximum=2**32 - 1)
        if roles["secondary_actor_character_id"] != played_character_id or roles["secondary_recipient_character_id"] != candidate:
            raise ValueError("ranked marriage actual pair differs from the direct-player choice")
        normalized.append(dict(row))
    return {"snapshot_id": snapshot_id, "public_revision": public_revision, "native_revision": native_revision,
            "date_raw": date_raw, "played_character_id": played_character_id, "candidates": normalized}


def _integer(value: object, name: str, *, minimum: int, maximum: int = 2**31 - 1) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} is not an integer in its native range")
    return value
