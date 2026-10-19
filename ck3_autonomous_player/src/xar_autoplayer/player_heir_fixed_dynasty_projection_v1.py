"""Pure fixed-T0 dynasty projection for one native player-heir observation.

The future query owner must construct these internal DTOs from its validated
native response and retained campaign baseline. This module neither reads the
game nor authenticates client JSON. It has no MCP route, migration token or
runtime registration. A projection cannot qualify its provider or an actual H
measurement by itself. No complete eligible backup domain is inferred here.
"""
from __future__ import annotations

from dataclasses import dataclass


EXACT_EXE_SHA256 = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"
GETTER_SOURCE_CLOSURE_SHA256 = "632f01555310ab57b65743a686d5653b87a08ada14ebcb7d849371027ae27660"
SOURCE_KIND = "native_get_player_heir_12004_v1"


@dataclass(frozen=True, slots=True)
class FixedDynastyAnchorV1:
    """Existing immutable T0 anchor; current actor/episode must not replace it."""
    goal_campaign_id: str
    origin_character_id: int
    baseline_episode_run_id: str
    t0_date_raw: int
    founding_dynasty_id_raw: int
    baseline_save_sha256: str
    baseline_summary_sha256: str


# Source-pinned initial campaign mapping, distinct from the scoring/video label.
# A caller cannot reuse this exact summary hash while replacing its original D0.
ROBERT_V20261019_T0_ANCHOR = FixedDynastyAnchorV1(
    "native-31254-6271ac8cd441", 31254, "native-31254-6271ac8cd441", 53144328, 174,
    "381e832bb3122b1c544d5bcd505eb86b4d40456a4d37969bcf208714d0aa88f4",
    "bb5cb5593e6a4e1156dfbacf2d94aa13f10eb41735a5f215dbaad2eb2d89ada8")


@dataclass(frozen=True, slots=True)
class CandidateQueryBindingV1:
    """Outer query owner's exact tuple, absent from the native core prefix.

    Hashes are normalized lowercase by the existing owner. Game birth is an
    opaque exact string, never a float. Goal campaign identity is distinct from
    a video's scoring label and from the current successor episode.
    """
    machine_id: str
    game_birth: str
    bridge_pid: int
    connection_generation: int
    executable_sha256: str
    native_provider_sha256: str
    owner_source_epoch: str
    query_id: str
    snapshot_id: str
    revision: int
    native_revision: int
    capture_epoch: int
    date_raw: int
    actor_character_id: int
    episode_run_id: str
    goal_campaign_id: str
    origin_character_id: int
    baseline_save_sha256: str
    baseline_summary_sha256: str


@dataclass(frozen=True, slots=True)
class CandidateCoreFrameV1:
    """Copied CoreSnapshotPrefix values; contains no engine pointer."""
    date_raw: int
    paused: bool
    speed: int
    local_player_id: int
    map_ready: bool
    has_played_character: bool
    played_character_id: int
    played_character_alive: bool


@dataclass(frozen=True, slots=True)
class CandidateLineageV1:
    # Existing family_value::Lineage semantics. -1 is known none ONLY when
    # NativePlayerHeirCandidateV1.lineage_available is true.
    house_id: int
    dynasty_id: int


@dataclass(frozen=True, slots=True)
class NativePlayerHeirCandidateV1:
    """Field-for-field projection of the independent native Observation.

    available means coherent observation, including an actual null or dead
    result. identity_and_frame_stable includes native full-ID/pointer round
    trips and liveness/lineage bookends; it is never a caller permission flag.
    """
    available: bool
    unavailable_reason: str | None
    source_fixture: bool
    original_getter_source_bound: bool
    before: CandidateCoreFrameV1
    after: CandidateCoreFrameV1
    getter_observed: bool
    candidate_present: bool
    actor_character_id: int
    candidate_character_id: int
    candidate_alive: bool
    identity_and_frame_stable: bool
    lineage_available: bool
    candidate_lineage: CandidateLineageV1
    lineage_unavailable_reason: str | None


@dataclass(frozen=True, slots=True)
class BoundPlayerHeirCandidateV1:
    binding: CandidateQueryBindingV1
    observation: NativePlayerHeirCandidateV1
    source_kind: str
    getter_source_closure_sha256: str


@dataclass(frozen=True, slots=True)
class FixedDynastyCandidateProjectionV1:
    status: str
    reason: str
    fixed_dynasty_id_raw: int | None
    candidate_character_id: int | None
    candidate_same_fixed_dynasty: bool | None
    positive_same_dynasty_legal_witness: bool
    k: int | None
    b: None
    H_interval: tuple[int, int]
    complete_backup_domain: bool = False
    scope: str = "pure_current_candidate_projection"


def _full_id(value: object, *, none_allowed: bool = False) -> bool:
    # Preserve every generation bit. Negative signed IDs except -1 are valid.
    return (type(value) is int and -2**31 <= value < 2**31
            and (none_allowed or value != -1))


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value.lower() not in {"unknown", "null", "none"}


def _sha(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _natural(value: object, *, positive: bool = False) -> bool:
    return type(value) is int and value >= (1 if positive else 0)


def _valid_anchor(value: object) -> bool:
    return (isinstance(value, FixedDynastyAnchorV1)
        and _text(value.goal_campaign_id) and _text(value.baseline_episode_run_id)
        and _full_id(value.origin_character_id) and _full_id(value.founding_dynasty_id_raw)
        and _natural(value.t0_date_raw) and _sha(value.baseline_save_sha256)
        and _sha(value.baseline_summary_sha256)
        and (value.baseline_summary_sha256 != ROBERT_V20261019_T0_ANCHOR.baseline_summary_sha256
             or value == ROBERT_V20261019_T0_ANCHOR))


def _valid_binding(value: object) -> bool:
    return (isinstance(value, CandidateQueryBindingV1)
        and all(_text(getattr(value, key)) for key in (
            "machine_id", "game_birth", "query_id", "snapshot_id", "episode_run_id", "goal_campaign_id"))
        and all(_sha(getattr(value, key)) for key in (
            "executable_sha256", "native_provider_sha256", "owner_source_epoch",
            "baseline_save_sha256", "baseline_summary_sha256"))
        and value.executable_sha256 == EXACT_EXE_SHA256
        and _natural(value.bridge_pid, positive=True) and _natural(value.connection_generation, positive=True)
        and _natural(value.revision) and _natural(value.native_revision, positive=True)
        and _natural(value.capture_epoch, positive=True) and _natural(value.date_raw)
        and _full_id(value.actor_character_id) and _full_id(value.origin_character_id))


def _valid_core(value: object) -> bool:
    return (isinstance(value, CandidateCoreFrameV1)
        and _natural(value.date_raw) and _natural(value.speed)
        and _natural(value.local_player_id)
        and all(type(getattr(value, key)) is bool for key in (
            "paused", "map_ready", "has_played_character", "played_character_alive"))
        and value.paused and value.map_ready and value.has_played_character
        and value.played_character_alive and _full_id(value.played_character_id))


def project_fixed_dynasty_candidate_v1(*, anchor: FixedDynastyAnchorV1,
        captured: BoundPlayerHeirCandidateV1, current: CandidateQueryBindingV1,
        current_core: CandidateCoreFrameV1) -> FixedDynastyCandidateProjectionV1:
    """Return k=1 only for a fresh positive witness; all absence stays unknown.

    The native selector is called once by its provider. A different dynasty,
    null, dead candidate, incomplete lineage or failed bookend cannot prove
    that no other legal D0 candidate exists. Therefore this leaf never emits
    k=0, b=0 or a point H score. A valid single witness yields [70,100].
    """
    fixed = anchor.founding_dynasty_id_raw if _valid_anchor(anchor) else None

    def unknown(reason: str, candidate: int | None = None,
                same: bool | None = None) -> FixedDynastyCandidateProjectionV1:
        return FixedDynastyCandidateProjectionV1("unknown", reason, fixed, candidate,
            same, False, None, None, (0, 100))

    if fixed is None:
        return unknown("invalid_fixed_T0_anchor")
    if (not isinstance(captured, BoundPlayerHeirCandidateV1)
            or not _valid_binding(captured.binding) or not _valid_binding(current)):
        return unknown("query_binding_unavailable")
    if captured.binding != current:
        return unknown("stale_or_cross_query_binding")
    if (current.goal_campaign_id != anchor.goal_campaign_id
            or current.origin_character_id != anchor.origin_character_id
            or current.baseline_save_sha256 != anchor.baseline_save_sha256
            or current.baseline_summary_sha256 != anchor.baseline_summary_sha256
            or current.date_raw < anchor.t0_date_raw):
        return unknown("different_original_campaign_baseline")
    if (captured.source_kind != SOURCE_KIND
            or captured.getter_source_closure_sha256 != GETTER_SOURCE_CLOSURE_SHA256):
        return unknown("original_player_heir_source_unavailable")
    observation = captured.observation
    if (not isinstance(observation, NativePlayerHeirCandidateV1)
            or any(type(getattr(observation, key)) is not bool for key in (
                "available", "source_fixture", "original_getter_source_bound", "getter_observed",
                "candidate_present", "candidate_alive", "identity_and_frame_stable", "lineage_available"))):
        return unknown("malformed_native_observation")
    if observation.source_fixture:
        return unknown("synthetic_provider_has_no_scoring_credit")
    if (not observation.available or not observation.original_getter_source_bound
            or not observation.getter_observed or not observation.identity_and_frame_stable
            or observation.unavailable_reason not in (None, "")):
        return unknown("native_candidate_observation_unavailable")
    if (not _valid_core(current_core) or not _valid_core(observation.before)
            or not _valid_core(observation.after)
            or observation.before != observation.after or observation.after != current_core
            or current_core.date_raw != current.date_raw
            or current_core.played_character_id != current.actor_character_id
            or not _full_id(observation.actor_character_id)
            or observation.actor_character_id != current.actor_character_id):
        return unknown("native_actor_or_frame_changed")
    if not observation.candidate_present:
        return unknown("observed_null_is_not_complete_eligible_absence")
    candidate = observation.candidate_character_id
    if not _full_id(candidate) or candidate == current.actor_character_id or not observation.candidate_alive:
        return unknown("candidate_identity_or_liveness_unavailable")
    if not observation.lineage_available:
        return unknown("candidate_lineage_unavailable", candidate)
    if observation.lineage_unavailable_reason not in (None, ""):
        return unknown("candidate_lineage_malformed", candidate)
    lineage = observation.candidate_lineage
    if (not isinstance(lineage, CandidateLineageV1)
            or not _full_id(lineage.house_id, none_allowed=True)
            or not _full_id(lineage.dynasty_id, none_allowed=True)
            or (lineage.house_id == -1 and lineage.dynasty_id != -1)):
        return unknown("candidate_lineage_malformed", candidate)
    same = lineage.dynasty_id == fixed
    if not same:
        return unknown("selected_candidate_outside_fixed_D0_incomplete_domain", candidate, False)
    # Cadet house, current owner's dynasty and age are deliberately not proxies
    # for native eligibility or fixed-D0 membership. Backups remain unobserved.
    return FixedDynastyCandidateProjectionV1("positive_witness", "one_living_native_player_heir_in_fixed_D0",
        fixed, candidate, True, True, 1, None, (70, 100))
