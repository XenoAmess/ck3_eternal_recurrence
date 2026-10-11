"""Connect a qualified current-child native court-owner field to the composer.

The input is the existing descendant row's copied source field, validated by
its owning transport. This function acquires no packet and runs no query.
"""

from collections.abc import Mapping

from dataclasses import dataclass


@dataclass(frozen=True)
class ChildCourtOwnerObservation12004:
    child_id: int
    available: bool = False
    source_qualified: bool = False
    owner_id: int | None = None


def child_court_owner_from_current_child_source_12004(
    child_id: int,
    source: Mapping[str, object] | None,
    *,
    native_revision: int,
) -> ChildCourtOwnerObservation12004:
    unavailable = ChildCourtOwnerObservation12004(child_id=child_id)
    if (
        type(child_id) is not int
        or not 0 <= child_id < 0xFFFFFFFF
        or type(native_revision) is not int
        or not 0 < native_revision < (1 << 64)
        or not isinstance(source, Mapping)
        or source.get("schema")
        != "xar.ck3.current-child-court-owner-readonly/1.20.0.4/v1"
        or type(source.get("child_character_id")) is not int
        or source.get("child_character_id") != child_id
        or type(source.get("native_revision")) is not int
        or source.get("native_revision") != native_revision
        or source.get("source_qualified") is not True
        or source.get("getter_projection_complete") is not True
        or source.get("identity_round_trip") is not True
        or source.get("sample_stable") is not True
    ):
        return unavailable

    status = source.get("status")
    owner = source.get("court_owner_id")
    if status == "known_null":
        if source.get("court_owner_present") is not False or owner is not None:
            return unavailable
        return ChildCourtOwnerObservation12004(
            child_id=child_id, available=True, source_qualified=True, owner_id=None
        )
    if (
        status != "resolved"
        or source.get("court_owner_present") is not True
        or type(owner) is not int
        or not 0 <= owner < 0xFFFFFFFF
    ):
        return unavailable
    return ChildCourtOwnerObservation12004(
        child_id=child_id, available=True, source_qualified=True, owner_id=owner
    )
