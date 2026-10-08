"""Strict contract for one paused Council candidate frame.

The native producer owns CK3 legality and skill enrichment. Python validates
the stable Council19 payload and keeps the planner bound to its exact paused
frame. Native 1.19.0.6 and 1.20.0.2 adapters publish this same DTO; the separate
Council22 action verifies appointment through a later incumbent receipt.
The private read path can explicitly opt in to Chancellor diplomacy or
Spymaster intrigue. Its composition step also reads Court Chaplain learning;
public requests and assignment consumers retain their existing coverage.
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
CHANCELLOR_POSITION_KEY: Final = "councillor_chancellor"
CHANCELLOR_MAIN_SKILL_KEY: Final = "diplomacy"
SPYMASTER_POSITION_KEY: Final = "councillor_spymaster"
SPYMASTER_MAIN_SKILL_KEY: Final = "intrigue"
COURT_CHAPLAIN_POSITION_KEY: Final = "councillor_court_chaplain"
COURT_CHAPLAIN_MAIN_SKILL_KEY: Final = "learning"
_PRIVATE_COMPOSITION_STEP: Final = "private-query-council-composition-candidates-v1"
_PRIVATE_FINAL_GATES_STEP: Final = "private-query-council-final-gates-v1"
_POSITION_MAIN_SKILL_KEYS: Final = {
    STEWARD_POSITION_KEY: STEWARD_MAIN_SKILL_KEY,
    CHANCELLOR_POSITION_KEY: CHANCELLOR_MAIN_SKILL_KEY,
    SPYMASTER_POSITION_KEY: SPYMASTER_MAIN_SKILL_KEY,
    COURT_CHAPLAIN_POSITION_KEY: COURT_CHAPLAIN_MAIN_SKILL_KEY,
}

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
    "incumbent_main_skill",
    "vacant",
    "action_route",
}
_POSITION_OPTIONAL_FIELDS: Final = {"current_task_owner_domain_tax_mult_v1"}
_CURRENT_TASK_TAX_FIELDS: Final = {
    "status", "unavailable_reason", "active_task_id", "owner_character_id",
    "incumbent_character_id", "task_key", "frozen", "modifier_id",
    "keyword_id", "observed_keyword_key", "value",
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
    "incumbent_main_skill_ready",
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


def _normalize_current_task_tax(
    value: object, *, owner_character_id: int, incumbent_character_id: int | None
) -> dict[str, object]:
    """Keep the current owner component distinct from assignment readiness."""
    if not isinstance(value, dict) or set(value) != _CURRENT_TASK_TAX_FIELDS:
        raise ValueError("current task owner tax must contain exactly the v1 fields")
    if value["owner_character_id"] != owner_character_id or (
        value["incumbent_character_id"] != incumbent_character_id
    ):
        raise ValueError("current task owner tax must match the selected seat")
    _integer(value["active_task_id"], "current task ID", minimum=-(2**31), maximum=2**31 - 1)
    modifier_id = _integer(value["modifier_id"], "current task modifier ID", minimum=0, maximum=65535)
    keyword_id = _integer(value["keyword_id"], "current task keyword ID", minimum=0, maximum=2**31 - 1)
    if modifier_id != 162 or keyword_id != 11976:
        raise ValueError("current task owner tax descriptor does not match actual4")
    for key in ("task_key", "observed_keyword_key"):
        if value[key] is not None and (
            not isinstance(value[key], str) or not value[key]
        ):
            raise ValueError(f"current task owner tax {key} must be a string or null")
    if value["frozen"] is not None and not isinstance(value["frozen"], bool):
        raise ValueError("current task owner tax frozen must be a boolean or null")
    result = dict(value)
    if value["status"] == "available":
        numeric = value["value"]
        if (
            value["unavailable_reason"] is not None
            or value["observed_keyword_key"] != "domain_tax_mult"
            or value["task_key"] is None
            or value["frozen"] is None
            or incumbent_character_id is None
            or not isinstance(numeric, dict)
            or set(numeric) != {"raw", "scale"}
            or numeric["scale"] != 100000
        ):
            raise ValueError("available current task owner tax needs its native component")
        result["value"] = {
            "raw": _integer(numeric["raw"], "current task owner tax raw",
                            minimum=-(2**63), maximum=2**63 - 1),
            "scale": 100000,
        }
    elif value["status"] == "unavailable":
        if value["value"] is not None or not isinstance(value["unavailable_reason"], str) or not value["unavailable_reason"]:
            raise ValueError("unavailable current task owner tax needs a reason and null value")
    else:
        raise ValueError("current task owner tax status must be available or unavailable")
    return result


def build_council_composition_candidates_request_v1(
    *,
    expected_snapshot_id: object,
    public_revision: object,
    native_revision: object,
    date_raw: object,
    owner_character_id: object,
    position_key: object = STEWARD_POSITION_KEY,
    allow_chancellor_read_only: bool = False,
    allow_spymaster_read_only: bool = False,
    query_step: object = None,
) -> dict[str, object]:
    """Build the exact request fields accepted by the Council19 producer."""

    if position_key != STEWARD_POSITION_KEY and not (
        (allow_chancellor_read_only is True and position_key == CHANCELLOR_POSITION_KEY)
        or (allow_spymaster_read_only is True and position_key == SPYMASTER_POSITION_KEY)
        or (query_step in {_PRIVATE_COMPOSITION_STEP, _PRIVATE_FINAL_GATES_STEP}
            and position_key == COURT_CHAPLAIN_POSITION_KEY)
    ):
        raise ValueError(
            "position_key must be councillor_steward or explicitly opted-in "
            "readonly councillor_chancellor or councillor_spymaster, or "
            "councillor_court_chaplain in the private composition or final-gates step"
        )
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
        "position_key": position_key,
    }


def normalize_council_composition_candidates_v1(
    value: object,
    *,
    expected_snapshot_id: object,
    expected_public_revision: object,
    expected_native_revision: object,
    expected_date_raw: object,
    expected_owner_character_id: object,
    expected_position_key: object = STEWARD_POSITION_KEY,
) -> dict[str, object]:
    """Validate one complete, available, same-frame Council19 payload."""

    request = build_council_composition_candidates_request_v1(
        expected_snapshot_id=expected_snapshot_id,
        public_revision=expected_public_revision,
        native_revision=expected_native_revision,
        date_raw=expected_date_raw,
        owner_character_id=expected_owner_character_id,
        position_key=expected_position_key,
        allow_chancellor_read_only=True,
        allow_spymaster_read_only=True,
        query_step=_PRIVATE_COMPOSITION_STEP,
    )
    main_skill_key = _POSITION_MAIN_SKILL_KEYS[request["position_key"]]
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
    if (
        not isinstance(position, dict)
        or not _POSITION_FIELDS <= set(position)
        or set(position) - _POSITION_FIELDS - _POSITION_OPTIONAL_FIELDS
    ):
        raise ValueError("position must contain the v1 fields and supported observations")
    if position.get("position_key") != request["position_key"]:
        raise ValueError("position_key does not match the requested position")
    incumbent_raw = position.get("incumbent_character_id")
    incumbent_character_id = (
        None
        if incumbent_raw is None
        else _full_character_id(
            incumbent_raw, "position.incumbent_character_id"
        )
    )
    incumbent_skill_raw = position.get("incumbent_main_skill")
    if incumbent_skill_raw is None:
        incumbent_main_skill = None
    elif (
        isinstance(incumbent_skill_raw, dict)
        and set(incumbent_skill_raw) == _MAIN_SKILL_FIELDS
        and incumbent_skill_raw.get("key") == main_skill_key
    ):
        incumbent_main_skill = {
            "key": main_skill_key,
            "value": _integer(
                incumbent_skill_raw.get("value"),
                "position.incumbent_main_skill.value",
                minimum=0,
                maximum=2**31 - 1,
            ),
        }
    else:
        raise ValueError("position.incumbent_main_skill is invalid")
    vacant = position.get("vacant")
    if not isinstance(vacant, bool) or vacant is not (
        incumbent_character_id is None
    ):
        raise ValueError("position.vacant disagrees with incumbent identity")
    if vacant is not (incumbent_main_skill is None):
        raise ValueError(
            "position incumbent identity and main skill must be ready together"
        )
    action_route = position.get("action_route")
    expected_route = "assign" if vacant else "replace"
    if action_route != expected_route:
        raise ValueError("position.action_route disagrees with vacancy state")
    current_task_tax = None
    if "current_task_owner_domain_tax_mult_v1" in position:
        current_task_tax = _normalize_current_task_tax(
            position["current_task_owner_domain_tax_mult_v1"],
            owner_character_id=owner_character_id,
            incumbent_character_id=incumbent_character_id,
        )

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
        if main_skill.get("key") != main_skill_key:
            raise ValueError(f"{name}.main_skill.key must be {main_skill_key}")
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
                    "key": main_skill_key,
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
            "incumbent_main_skill": incumbent_main_skill,
            **({"current_task_owner_domain_tax_mult_v1": current_task_tax}
               if "current_task_owner_domain_tax_mult_v1" in position else {}),
        },
        "candidate_collection_complete": True,
        "candidates": candidates,
        "readiness": dict(readiness),
    }
