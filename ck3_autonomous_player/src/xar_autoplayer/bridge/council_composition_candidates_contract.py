"""Strict public contract for one paused steward-candidate frame.

The native producer owns CK3 legality and skill enrichment.  Python only
validates the frozen Council19 payload and keeps the formal planner bound to
that exact paused frame.  Appointment remains fail-closed until a separate
semantic action is implemented.
"""

from __future__ import annotations

from typing import Final


QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_CAPABILITY: Final = (
    "game.query.council-composition-candidates-v1"
)
QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP: Final = (
    "query-council-composition-candidates-v1"
)
COUNCIL_COMPOSITION_CANDIDATES_V1_SCHEMA: Final = (
    "xar.ck3.council-composition-candidates/v1"
)
ASSIGN_COUNCILLOR_V1_CAPABILITY: Final = "game.action.assign-councillor-v1"
STEWARD_POSITION_KEY: Final = "councillor_steward"
STEWARD_MAIN_SKILL_KEY: Final = "stewardship"

_ROOT_FIELDS: Final = {
    "snapshot",
    "owner_character_id",
    "position",
    "candidate_collection_complete",
    "candidates",
    "readiness",
}
_SNAPSHOT_FIELDS: Final = {
    "snapshot_id",
    "public_revision",
    "native_revision",
    "date_raw",
    "paused",
}
_POSITION_FIELDS: Final = {
    "position_key",
    "incumbent_character_id",
    "vacant",
    "action_route",
}
_CANDIDATE_FIELDS: Final = {
    "character_id",
    "native_collection_ordinal",
    "eligible",
    "eligibility_reason",
    "main_skill",
    "action_route",
}
_MAIN_SKILL_FIELDS: Final = {"key", "value"}
_READINESS_FIELDS: Final = {
    "identity_ready",
    "candidate_collection_ready",
    "incumbent_ready",
    "candidate_legality_ready",
    "main_skill_ready",
    "action_route_ready",
    "same_frame_ready",
    "ready",
}


def _integer(
    value: object, name: str, *, minimum: int, maximum: int
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value <= maximum
    ):
        raise ValueError(
            f"{name} must be an integer in [{minimum}, {maximum}]"
        )
    return value


def _full_character_id(value: object, name: str) -> int:
    result = _integer(
        value, name, minimum=-(2**31), maximum=2**31 - 1
    )
    if result == -1:
        raise ValueError(f"{name} must be a valid full CharacterID")
    return result


def _expected_snapshot_id(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("expected_snapshot_id must be a non-empty string")
    return value


def build_council_composition_candidates_request_v1(
    *,
    expected_snapshot_id: object,
    public_revision: object,
    native_revision: object,
    date_raw: object,
    owner_character_id: object,
    position_key: object = STEWARD_POSITION_KEY,
) -> dict[str, object]:
    """Build the exact request fields accepted by the Council19 producer."""

    if position_key != STEWARD_POSITION_KEY:
        raise ValueError("position_key must be councillor_steward")
    return {
        "expected_snapshot_id": _expected_snapshot_id(expected_snapshot_id),
        "public_revision": _integer(
            public_revision,
            "public_revision",
            minimum=1,
            maximum=2**64 - 1,
        ),
        "native_revision": _integer(
            native_revision,
            "native_revision",
            minimum=1,
            maximum=2**64 - 1,
        ),
        "date_raw": _integer(
            date_raw,
            "date_raw",
            minimum=-(2**31),
            maximum=2**31 - 1,
        ),
        "owner_character_id": _full_character_id(
            owner_character_id, "owner_character_id"
        ),
        "position_key": STEWARD_POSITION_KEY,
    }


def normalize_council_composition_candidates_v1(
    value: object,
    *,
    expected_snapshot_id: object,
    expected_public_revision: object,
    expected_native_revision: object,
    expected_date_raw: object,
    expected_owner_character_id: object,
) -> dict[str, object]:
    """Validate one complete, available, same-frame Council19 payload."""

    request = build_council_composition_candidates_request_v1(
        expected_snapshot_id=expected_snapshot_id,
        public_revision=expected_public_revision,
        native_revision=expected_native_revision,
        date_raw=expected_date_raw,
        owner_character_id=expected_owner_character_id,
    )
    if not isinstance(value, dict) or set(value) != _ROOT_FIELDS:
        raise ValueError(
            "council composition candidates must contain exactly the v1 fields"
        )

    snapshot = value.get("snapshot")
    if not isinstance(snapshot, dict) or set(snapshot) != _SNAPSHOT_FIELDS:
        raise ValueError("snapshot must contain exactly the v1 fields")
    expected_snapshot = {
        "snapshot_id": request["expected_snapshot_id"],
        "public_revision": request["public_revision"],
        "native_revision": request["native_revision"],
        "date_raw": request["date_raw"],
        "paused": True,
    }
    if snapshot != expected_snapshot:
        raise ValueError("snapshot does not match the requested paused frame")

    owner_character_id = _full_character_id(
        value.get("owner_character_id"), "owner_character_id"
    )
    if owner_character_id != request["owner_character_id"]:
        raise ValueError("owner_character_id does not match the request")

    position = value.get("position")
    if not isinstance(position, dict) or set(position) != _POSITION_FIELDS:
        raise ValueError("position must contain exactly the v1 fields")
    if position.get("position_key") != STEWARD_POSITION_KEY:
        raise ValueError("position_key must be councillor_steward")
    incumbent_raw = position.get("incumbent_character_id")
    incumbent_character_id = (
        None
        if incumbent_raw is None
        else _full_character_id(
            incumbent_raw, "position.incumbent_character_id"
        )
    )
    vacant = position.get("vacant")
    if not isinstance(vacant, bool) or vacant is not (
        incumbent_character_id is None
    ):
        raise ValueError("position.vacant disagrees with incumbent identity")
    action_route = position.get("action_route")
    expected_route = "assign" if vacant else "replace"
    if action_route != expected_route:
        raise ValueError("position.action_route disagrees with vacancy state")

    if value.get("candidate_collection_complete") is not True:
        raise ValueError("candidate_collection_complete must be true")
    candidates_raw = value.get("candidates")
    if not isinstance(candidates_raw, list):
        raise ValueError("candidates must be a list")
    candidates: list[dict[str, object]] = []
    character_ids: set[int] = set()
    for index, candidate_raw in enumerate(candidates_raw):
        name = f"candidates[{index}]"
        if (
            not isinstance(candidate_raw, dict)
            or set(candidate_raw) != _CANDIDATE_FIELDS
        ):
            raise ValueError(f"{name} must contain exactly the v1 fields")
        character_id = _full_character_id(
            candidate_raw.get("character_id"), f"{name}.character_id"
        )
        ordinal = _integer(
            candidate_raw.get("native_collection_ordinal"),
            f"{name}.native_collection_ordinal",
            minimum=0,
            maximum=2**32 - 1,
        )
        if character_id in character_ids:
            raise ValueError("candidate identities must be unique")
        character_ids.add(character_id)
        if candidate_raw.get("eligible") is not True:
            raise ValueError(f"{name}.eligible must be true")
        if (
            candidate_raw.get("eligibility_reason")
            != "native_candidate_provider_accepted"
        ):
            raise ValueError(f"{name}.eligibility_reason is invalid")
        main_skill = candidate_raw.get("main_skill")
        if not isinstance(main_skill, dict) or set(main_skill) != _MAIN_SKILL_FIELDS:
            raise ValueError(f"{name}.main_skill must contain exactly the v1 fields")
        if main_skill.get("key") != STEWARD_MAIN_SKILL_KEY:
            raise ValueError(f"{name}.main_skill.key must be stewardship")
        skill_value = _integer(
            main_skill.get("value"),
            f"{name}.main_skill.value",
            minimum=0,
            maximum=2**31 - 1,
        )
        if candidate_raw.get("action_route") != expected_route:
            raise ValueError(f"{name}.action_route disagrees with position")
        candidates.append(
            {
                **candidate_raw,
                "character_id": character_id,
                "native_collection_ordinal": ordinal,
                "main_skill": {
                    "key": STEWARD_MAIN_SKILL_KEY,
                    "value": skill_value,
                },
            }
        )

    readiness = value.get("readiness")
    if not isinstance(readiness, dict) or set(readiness) != _READINESS_FIELDS:
        raise ValueError("readiness must contain exactly the v1 fields")
    if any(readiness.get(field) is not True for field in _READINESS_FIELDS):
        raise ValueError("available Council19 payload requires complete readiness")
    return {
        "snapshot": dict(snapshot),
        "owner_character_id": owner_character_id,
        "position": {
            **position,
            "incumbent_character_id": incumbent_character_id,
        },
        "candidate_collection_complete": True,
        "candidates": candidates,
        "readiness": dict(readiness),
    }
