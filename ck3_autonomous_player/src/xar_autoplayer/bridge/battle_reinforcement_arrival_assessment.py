"""Immutable lifecycle and conditional arrival assessment from normalized v1.

This is a pure consumer of the existing native route/ETA and new present-time
admission. It does not issue actions or predict battle survival, AI redirection,
casualties, or a future CombatID binding.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ArrivalLifecycle = Literal[
    "already_participating", "assigned_en_route", "ordinary_en_route",
    "assigned_eta_unavailable", "arrived_not_yet_participating", "no_arrival_target",
]
ArrivalEligibility = Literal[
    "eligible", "ineligible", "already_in_active_combat", "unavailable", "not_applicable",
]
TargetProvenance = Literal[
    "native_help_override", "committed_route_final", "current_active_combat", "none",
]


@dataclass(frozen=True, slots=True)
class ConditionalReinforcementArrival:
    """One time-indexed scenario; all binding remains conditional."""

    selected_public_cunit_id: int
    target_province_id: int
    target_provenance: TargetProvenance
    native_eta_date_raw: int
    currently_selected_combat_id: int
    join_side_if_observed_state_persists: Literal["attacker", "defender"]
    condition: str = (
        "observed_route_target_current_admission_gates_combat_and_relations_"
        "persist_until_native_eta"
    )
    temporal_semantics: str = "present_time_only_not_future_binding"
    future_binding: bool = False


@dataclass(frozen=True, slots=True)
class BattleReinforcementArrivalAssessment:
    selected_public_cunit_id: int
    snapshot_revision: int
    observed_date_raw: int
    status: Literal["available", "unavailable"]
    unavailable_reason: str | None
    lifecycle: ArrivalLifecycle | None
    eligibility_now: ArrivalEligibility
    target_province_id: int | None
    target_provenance: TargetProvenance
    native_eta_date_raw: int | None
    actual_active_combat_id: int | None
    subject_current_participation_verified: bool
    currently_selected_combat_id: int | None
    join_side_now: Literal["none", "attacker", "defender"]
    current_attacker_public_cunit_ids_in_stored_order: tuple[int, ...]
    current_defender_public_cunit_ids_in_stored_order: tuple[int, ...]
    conditional_arrival: ConditionalReinforcementArrival | None
    temporal_semantics: str = "present_time_only_not_future_binding"
    future_binding: bool = False


def derive_battle_reinforcement_arrival_assessment(
    normalized_frame: dict[str, object],
) -> BattleReinforcementArrivalAssessment:
    """Consume a frame already validated by the production service contract.

    An older frame without the optional nested extension has no new admission
    observation. No first-edge duration or current compatible combat becomes a
    native final ETA or a future guaranteed participant.
    """
    subject_id = normalized_frame["selected_public_cunit_id"]
    revision = normalized_frame["snapshot_revision"]
    date_raw = normalized_frame["observed_date_raw"]
    contact = normalized_frame["contact_projection"]
    admission = contact.get("arrival_admission") if isinstance(contact, dict) else None
    if normalized_frame["status"] != "available" or not isinstance(admission, dict):
        return BattleReinforcementArrivalAssessment(
            selected_public_cunit_id=subject_id, snapshot_revision=revision,
            observed_date_raw=date_raw, status="unavailable",
            unavailable_reason=(normalized_frame["unavailable_reason"]
                                or "arrival_admission_not_published"),
            lifecycle=None, eligibility_now="unavailable", target_province_id=None,
            target_provenance="none", native_eta_date_raw=None,
            actual_active_combat_id=None, subject_current_participation_verified=False,
            currently_selected_combat_id=None, join_side_now="none",
            current_attacker_public_cunit_ids_in_stored_order=(),
            current_defender_public_cunit_ids_in_stored_order=(), conditional_arrival=None,
        )

    target = admission["target"]
    subject = admission["subject"]
    target_id = target["province_id"]
    provenance = target["provenance"]
    eligibility = admission["eligibility_now"]
    selected_combat = admission["contact_if_now_selected_combat_id"]
    join_side = admission["join_side"]
    admission_available = admission["status"] in {"available", "not_applicable"}
    verified = admission_available and admission["subject_current_participation_verified"]
    route = normalized_frame["route"]
    eta = None
    if provenance == "native_help_override":
        eta = route["assignment_eta_date_raw"]
    elif provenance == "committed_route_final":
        route_ids = route["route_province_ids"]
        arrivals = route["arrival_date_raws"]
        if route_ids and route_ids[-1] == target_id and arrivals is not None:
            eta = arrivals[-1]

    lifecycle = None
    if verified:
        lifecycle = "already_participating"
    elif normalized_frame["assignment"]["active_combat_id"] is not None:
        # An active backlink without the complete admission's actual roster
        # verification cannot establish the new participation observation.
        lifecycle = None
    elif target_id is None:
        lifecycle = "no_arrival_target"
    elif route["current_province_id"] == target_id:
        lifecycle = "arrived_not_yet_participating"
    elif provenance == "native_help_override":
        lifecycle = (
            "assigned_en_route" if route["route_alignment"] == "aligned_to_assignment" and eta is not None
            else "assigned_eta_unavailable"
        )
    elif provenance == "committed_route_final":
        lifecycle = "ordinary_en_route"

    conditional = None
    if (admission_available and lifecycle in {"assigned_en_route", "ordinary_en_route"}
            and eligibility == "eligible" and eta is not None
            and selected_combat is not None and join_side in {"attacker", "defender"}):
        conditional = ConditionalReinforcementArrival(
            selected_public_cunit_id=subject_id, target_province_id=target_id,
            target_provenance=provenance, native_eta_date_raw=eta,
            currently_selected_combat_id=selected_combat,
            join_side_if_observed_state_persists=join_side,
        )
    return BattleReinforcementArrivalAssessment(
        selected_public_cunit_id=subject_id, snapshot_revision=revision,
        observed_date_raw=date_raw, status="available" if admission_available else "unavailable",
        unavailable_reason=admission["unavailable_reason"], lifecycle=lifecycle,
        eligibility_now=eligibility, target_province_id=target_id,
        target_provenance=provenance, native_eta_date_raw=eta,
        actual_active_combat_id=subject["active_combat_id"],
        subject_current_participation_verified=verified,
        currently_selected_combat_id=selected_combat if admission_available else None,
        join_side_now=join_side if admission_available else "none",
        current_attacker_public_cunit_ids_in_stored_order=(tuple(admission["current_attacker_public_cunit_ids_in_stored_order"])
                                                        if admission_available else ()),
        current_defender_public_cunit_ids_in_stored_order=(tuple(admission["current_defender_public_cunit_ids_in_stored_order"])
                                                        if admission_available else ()),
        conditional_arrival=conditional,
    )
