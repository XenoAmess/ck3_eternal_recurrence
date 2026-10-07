"""Actual current played jailer opinion toward a retained target.

The reverse target opinion and named release modifier keep their existing
material contract. This observer publishes an integer input, not a policy.
"""
from __future__ import annotations

import copy
from collections.abc import Mapping

from .version_identity import CK3_12004, require_exact_native_build

_SCHEMA = "xar.ck3.prisoner-keeper-opinion-12004-v1"
_FIELDS = {
    "schema", "build_version", "executable_sha256", "available",
    "unavailable_reason", "snapshot_revision", "date_raw",
    "actor_character_id", "target_character_id", "actor_opinion_of_target",
}


def normalize_prisoner_keeper_opinion_12004(
    value: object, *, native_revision: int, date_raw: int,
    player_character_id: int, target_character_id: int,
) -> dict[str, object]:
    """Strictly join the existing collection query's actual pair and frame."""
    if (
        type(native_revision) is not int or not 1 <= native_revision <= 2**64 - 1
        or type(date_raw) is not int or not -(2**31) <= date_raw <= 2**31 - 1
        or type(player_character_id) is not int
        or not 1 <= player_character_id <= 2**32 - 2
        or type(target_character_id) is not int
        or not 1 <= target_character_id <= 2**32 - 2
    ):
        raise ValueError("prisoner keeper opinion expected pair/frame is malformed")
    if not isinstance(value, Mapping) or set(value) != _FIELDS:
        raise ValueError("prisoner keeper opinion fields are malformed")
    if (
        value.get("schema") != _SCHEMA
        or require_exact_native_build(
            value.get("build_version"), value.get("executable_sha256")) != CK3_12004
        or type(value.get("available")) is not bool
        or type(value.get("unavailable_reason")) is not str
    ):
        raise ValueError("prisoner keeper opinion source identity is malformed")
    expected = {
        "snapshot_revision": native_revision, "date_raw": date_raw,
        "actor_character_id": player_character_id,
        "target_character_id": target_character_id,
    }
    if any(type(value.get(key)) is not int or value[key] != raw
           for key, raw in expected.items()):
        raise ValueError("prisoner keeper opinion differs from the current actor-to-target pair/frame")
    opinion = value["actor_opinion_of_target"]
    if value["available"]:
        if (
            value["unavailable_reason"] != ""
            or type(opinion) is not int or not -(2**31) <= opinion <= 2**31 - 1
        ):
            raise ValueError("prisoner keeper opinion available integer is malformed")
    elif not value["unavailable_reason"] or opinion is not None:
        raise ValueError("prisoner keeper opinion unavailable result is malformed")
    return copy.deepcopy(dict(value))
