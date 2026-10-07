"""Independent current prisoner-to-player named relation material."""

from __future__ import annotations

import copy
from collections.abc import Mapping

from .version_identity import CK3_12004, require_exact_native_build

_SCHEMA = "xar.ck3.prisoner-release-material-opinion-12004-v1"
_FIELDS = {
    "schema", "build_version", "executable_sha256", "available",
    "unavailable_reason", "snapshot_revision", "date_raw",
    "actor_character_id", "target_character_id", "target_opinion_of_actor",
    "released_from_prison", "release_causation_observed", "custody_change_observed",
}


def normalize_prisoner_release_material_opinion_12004(
    value: object, *, native_revision: int, date_raw: int,
    player_character_id: int, target_character_id: int,
) -> dict[str, object]:
    """Consume the optional value under the existing owning collection query."""
    if not isinstance(value, Mapping) or set(value) != _FIELDS:
        raise ValueError("prisoner release material fields are malformed")
    if (
        value.get("schema") != _SCHEMA
        or require_exact_native_build(
            value.get("build_version"), value.get("executable_sha256")) != CK3_12004
        or type(value.get("available")) is not bool
        or not isinstance(value.get("unavailable_reason"), str)
        or value.get("release_causation_observed") is not False
        or value.get("custody_change_observed") is not False
    ):
        raise ValueError("prisoner release material source identity is malformed")
    expected = {
        "snapshot_revision": native_revision,
        "date_raw": date_raw, "actor_character_id": player_character_id,
        "target_character_id": target_character_id,
    }
    if any(type(value.get(key)) is not int or value[key] != raw or raw <= 0
           for key, raw in expected.items()):
        raise ValueError("prisoner release material differs from the current pair/frame")
    modifier = value.get("released_from_prison")
    if (
        not isinstance(modifier, Mapping)
        or set(modifier) != {"observed", "present", "value"}
        or type(modifier.get("observed")) is not bool
        or type(modifier.get("present")) is not bool
    ):
        raise ValueError("released_from_prison observation is malformed")
    opinion = value["target_opinion_of_actor"]
    if value["available"]:
        if (
            value["unavailable_reason"] != ""
            or type(opinion) is not int
            or modifier["observed"] is not True
            or (modifier["present"] and type(modifier["value"]) is not int)
            or (not modifier["present"] and modifier["value"] is not None)
        ):
            raise ValueError("prisoner release material available value is malformed")
    elif (
        not value["unavailable_reason"] or opinion is not None
        or modifier["observed"] or modifier["present"] or modifier["value"] is not None
    ):
        raise ValueError("prisoner release material failure is malformed")
    return copy.deepcopy(dict(value))


def compare_prisoner_release_material_opinion_12004(
    before: Mapping[str, object], after: Mapping[str, object],
) -> dict[str, object]:
    """Keep independently observed total and named changes separate.

    Inputs may come from separate process generations. Native revisions are
    query-local; pair/build/date identity is taken from each normalized value.
    A named change is a measured relation input, not an action attribution.
    """
    samples = []
    for value in (before, after):
        normalized = normalize_prisoner_release_material_opinion_12004(
            value, native_revision=value.get("snapshot_revision"), date_raw=value.get("date_raw"),
            player_character_id=value.get("actor_character_id"),
            target_character_id=value.get("target_character_id"),
        )
        if not normalized["available"]:
            raise ValueError("release material comparison requires two observed values")
        samples.append(normalized)
    first, second = samples
    if (
        first["actor_character_id"] != second["actor_character_id"]
        or first["target_character_id"] != second["target_character_id"]
        or second["date_raw"] < first["date_raw"]
    ):
        raise ValueError("release material comparison changed the pair or reversed time")
    pre_modifier = first["released_from_prison"]
    post_modifier = second["released_from_prison"]
    # Observed absence contributes zero to this one named sum. This says
    # nothing about other modifiers, dread, stress or total action utility.
    named_delta = (
        (post_modifier["value"] if post_modifier["present"] else 0)
        - (pre_modifier["value"] if pre_modifier["present"] else 0)
    )
    return {
        "schema": "xar.ck3.prisoner-release-material-opinion-comparison-12004-v1",
        "actor_character_id": first["actor_character_id"],
        "target_character_id": first["target_character_id"],
        "pre_date_raw": first["date_raw"], "post_date_raw": second["date_raw"],
        "observed_total_opinion_delta": (
            second["target_opinion_of_actor"] - first["target_opinion_of_actor"]),
        "observed_released_from_prison_delta": named_delta,
        "named_relation_improved": named_delta > 0,
        "release_causation_observed": False,
        "custody_change_observed": False,
    }
