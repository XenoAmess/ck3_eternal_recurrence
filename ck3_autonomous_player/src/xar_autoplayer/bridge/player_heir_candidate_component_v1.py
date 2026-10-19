"""Optional player-heir parsing on the existing campaign-root query only.

No query, public token constructor, Native custody issuer or disk writer lives
here. Missing components do no additional work. The future canonical launch
owner must establish loaded DLL custody independently before H can qualify.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import asdict, dataclass

from ..player_heir_fixed_dynasty_projection_v1 import (
    BoundPlayerHeirCandidateV1, CandidateCoreFrameV1, CandidateLineageV1,
    CandidateQueryBindingV1, EXACT_EXE_SHA256, GETTER_SOURCE_CLOSURE_SHA256,
    NativePlayerHeirCandidateV1, ROBERT_V20261019_T0_ANCHOR, SOURCE_KIND,
    project_fixed_dynasty_candidate_v1,
)

COMPONENT = "player_heir_candidate_v1"
PROJECTION = "player_heir_fixed_dynasty_projection_v1"
_COMPONENT_KEYS = {"schema_version", "snapshot_revision", "query_kind", "executable_sha256",
                   "getter_rva", "parent_frame_bound", "observation"}
_OBSERVATION_KEYS = set(NativePlayerHeirCandidateV1.__dataclass_fields__)
_CORE_KEYS = set(CandidateCoreFrameV1.__dataclass_fields__)
_BOOL_KEYS = {"available", "source_fixture", "original_getter_source_bound", "getter_observed",
              "candidate_present", "candidate_alive", "identity_and_frame_stable", "lineage_available"}
_LOADED_NATIVE_SEAL = object()


@dataclass(frozen=True, slots=True)
class ParsedPlayerHeirComponentV1:
    status: str
    reason: str | None
    observation: NativePlayerHeirCandidateV1 | None


@dataclass(frozen=True, slots=True)
class _LoadedNativeProviderV1:
    """Reserved internal custody interface; deliberately has no producer yet.

    A future canonical Native30 launch/adoption producer must validate actual
    loaded-module evidence before issuing this owner/driver-bound value. A
    client mapping or a source-contract SHA cannot supply that qualification.
    """
    owner: object
    driver: object
    machine_id: str
    game_pid: int
    game_birth: str
    game_executable: str
    connection_generation: int
    pipe_name: str
    native_dll_sha256: str
    seal: object
    game_creation_filetime: int | None = None


def _integer(value, low, high):
    return type(value) is int and low <= value <= high


def _reason(value):
    return value is None or (isinstance(value, str) and 0 < len(value) <= 1024)


def _core(value):
    if (not isinstance(value, dict) or set(value) != _CORE_KEYS
            or not _integer(value["date_raw"], -(2**31), 2**31 - 1)
            or not _integer(value["speed"], 0, 2**31 - 1)
            or not _integer(value["local_player_id"], -(2**31), 2**31 - 1)
            or not _integer(value["played_character_id"], -(2**31), 2**31 - 1)
            or any(type(value[key]) is not bool for key in (
                "paused", "map_ready", "has_played_character", "played_character_alive"))):
        raise ValueError("malformed_native_core_frame")
    return CandidateCoreFrameV1(**value)


def parse_optional_player_heir_component_v1(value, *, root):
    """Parse compact native values; unavailable H never invalidates the root."""
    if value is None:
        return ParsedPlayerHeirComponentV1("missing", "optional_component_not_produced", None)
    try:
        if (not isinstance(value, dict) or set(value) != _COMPONENT_KEYS
                or type(value["schema_version"]) is not int or value["schema_version"] != 1
                or value["query_kind"] != "campaign_root_context_v1"
                or value["getter_rva"] != "0x289DCC0"
                or type(value["parent_frame_bound"]) is not bool
                or not _integer(value["snapshot_revision"], 1, 2**64 - 1)
                or value["snapshot_revision"] != root.get("snapshot_revision")
                or not isinstance(value["executable_sha256"], str)
                or value["executable_sha256"].lower() != EXACT_EXE_SHA256
                or str(root.get("provenance", {}).get("executable_sha256", "")).lower() != EXACT_EXE_SHA256):
            raise ValueError("component_source_or_parent_revision_mismatch")
        raw = value["observation"]
        if (not isinstance(raw, dict) or set(raw) != _OBSERVATION_KEYS
                or any(type(raw[key]) is not bool for key in _BOOL_KEYS)
                or not _integer(raw["actor_character_id"], -(2**31), 2**31 - 1)
                or not _integer(raw["candidate_character_id"], -(2**31), 2**31 - 1)
                or not _reason(raw["unavailable_reason"])
                or not _reason(raw["lineage_unavailable_reason"])):
            raise ValueError("malformed_native_candidate_observation")
        lineage = raw["candidate_lineage"]
        if (not isinstance(lineage, dict) or set(lineage) != {"house_id", "dynasty_id"}
                or any(not _integer(lineage[k], -(2**31), 2**31 - 1) for k in lineage)):
            raise ValueError("malformed_native_candidate_lineage")
        before, after = _core(raw["before"]), _core(raw["after"])
        observation = NativePlayerHeirCandidateV1(**{
            **raw, "before": before, "after": after, "candidate_lineage": CandidateLineageV1(**lineage)})
        if (value["parent_frame_bound"] is not True or root.get("status") != "available"
                or any(core.date_raw != root.get("date_raw")
                    or core.local_player_id != root.get("local_player_id")
                    or core.played_character_id != root.get("player_character_id")
                    for core in (before, after))
                or observation.actor_character_id != root.get("player_character_id")):
            return ParsedPlayerHeirComponentV1("unknown", "native_parent_frame_not_bound", observation)
        return ParsedPlayerHeirComponentV1("parsed", None, observation)
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        return ParsedPlayerHeirComponentV1("unknown", str(error)[:1024], None)


def _unknown(reason):
    # Reuse the existing pure score mapper's unknown semantics.
    result = asdict(project_fixed_dynasty_candidate_v1(anchor=ROBERT_V20261019_T0_ANCHOR,
        captured=None, current=None, current_core=None))
    result["reason"] = reason
    return result


def _snapshot_binding(snapshot):
    actor, diag = snapshot.get("played_character", {}), snapshot.get("diagnostics", {})
    if (not isinstance(actor, Mapping) or not isinstance(diag, Mapping)
            or snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or actor.get("alive") is not True):
        raise ValueError("SDK_stable_living_frame_unavailable")
    return (snapshot.get("snapshot_id"), snapshot.get("revision"), snapshot.get("native_revision"),
        snapshot.get("date_raw"), snapshot.get("episode_run_id"), actor.get("character_id"),
        diag.get("bridge_pid"), diag.get("connection_generation"))


def project_existing_root_player_heir_v1(driver, *, starting, current, root, request_id, query_sequence):
    """Called once by the original successful root query; never sends a command.

    Only this registered App's future typed loaded-provider custody permits a
    full query binding. Until that producer exists, valid parsed observations
    are cached as unknown. Missing/old producers cause no OS read or mutation.
    """
    if COMPONENT not in root:
        return None
    parsed = parse_optional_player_heir_component_v1(root[COMPONENT], root=root)
    if parsed.status != "parsed":
        return _unknown(parsed.reason or "optional_candidate_unavailable")
    try:
        from .native_driver import NativeHeadlessGameplayDriver
        from .successor_ui_app_owner_v1 import SuccessorUIAppOwner, _game_identity
        from ..successor_ui_checkpoint_lineage_v1 import same_game_identity_v1
        from .nonwar_private_build import private_native_build_identity
        from .version_identity import CK3_12004
        from ..strategy import normalize_ordinary_campaign_goal_v1
        owner = getattr(driver, "_player_heir_candidate_owner_v1", None)
        if (not isinstance(driver, NativeHeadlessGameplayDriver) or not isinstance(owner, SuccessorUIAppOwner)
                or owner.driver is not driver or owner.service.driver is not driver
                or getattr(owner.service, "_successor_ui_app_owner_v1", None) is not owner):
            return _unknown("canonical_SDK_owner_unavailable")
        first, last = _snapshot_binding(starting), _snapshot_binding(current)
        if (first != last or private_native_build_identity(starting) != CK3_12004
                or private_native_build_identity(current) != CK3_12004
                or root.get("snapshot_revision") != first[2] or root.get("date_raw") != first[3]
                or root.get("player_character_id") != first[5]
                or not _integer(first[6], 1, 2**31 - 1) or not _integer(first[7], 1, 2**63 - 1)
                or not isinstance(request_id, str) or not request_id
                or not _integer(query_sequence, 1, 2**64 - 1)):
            return _unknown("SDK_query_or_actor_frame_changed")
        provider = getattr(owner, "_player_heir_loaded_provider_v1", None)
        if provider is None and getattr(owner, "_player_heir_loaded_custody_v1", None) is not None:
            from .native_loaded_provider_origin_v1 import ensure_received_provider_v1
            ensure_received_provider_v1(owner)
            provider = getattr(owner, "_player_heir_loaded_provider_v1", None)
        if (not isinstance(provider, _LoadedNativeProviderV1) or provider.seal is not _LOADED_NATIVE_SEAL
                or provider.owner is not owner or provider.driver is not driver
                or provider.machine_id != owner.machine or provider.game_pid != first[6]
                or provider.connection_generation != first[7] or provider.pipe_name != driver.pipe_name
                or not isinstance(provider.native_dll_sha256, str) or len(provider.native_dll_sha256) != 64
                or any(c not in "0123456789abcdef" for c in provider.native_dll_sha256)
                or provider.native_dll_sha256 == GETTER_SOURCE_CLOSURE_SHA256):
            return _unknown("trusted_loaded_Native_DLL_custody_unavailable")
        if provider.game_creation_filetime is not None:
            from .native_loaded_provider_origin_v1 import exact_live_provider_game_v1
            game = exact_live_provider_game_v1(owner, provider)
        else:
            key = (first[6], first[7], driver.pipe_name)
            cached = getattr(owner, "_player_heir_game_identity_cache_v1", None)
            if not isinstance(cached, tuple) or len(cached) != 2 or cached[0] != key:
                game = _game_identity(current)
                owner._player_heir_game_identity_cache_v1 = (key, deepcopy(game))
            else:
                game = deepcopy(cached[1])
            if not same_game_identity_v1(game, {"pid": provider.game_pid, "creation_date": provider.game_birth,
                                             "executable": provider.game_executable}):
                return _unknown("loaded_provider_actual_Game_birth_mismatch")
        goal = normalize_ordinary_campaign_goal_v1(current.get("campaign_goal"))
        if (goal != normalize_ordinary_campaign_goal_v1(driver._campaign_goal)
                or goal != normalize_ordinary_campaign_goal_v1(starting.get("campaign_goal"))
                or goal["current_character_id"] != first[5]):
            return _unknown("original_goal_or_current_actor_mismatch")
        anchor = ROBERT_V20261019_T0_ANCHOR
        binding = CandidateQueryBindingV1(owner.machine, game["creation_date"], first[6], first[7],
            EXACT_EXE_SHA256, provider.native_dll_sha256, owner.epoch, request_id, first[0], first[1], first[2],
            query_sequence, first[3], first[5], first[4], goal["campaign_id"], goal["origin_character_id"],
            anchor.baseline_save_sha256, anchor.baseline_summary_sha256)
        captured = BoundPlayerHeirCandidateV1(binding, parsed.observation, SOURCE_KIND, GETTER_SOURCE_CLOSURE_SHA256)
        result = asdict(project_fixed_dynasty_candidate_v1(anchor=anchor, captured=captured,
            current=binding, current_core=parsed.observation.after))
        result.update(machine_id=owner.machine, game_identity=game,
            native_provider_sha256=provider.native_dll_sha256, owner_source_epoch=owner.epoch,
            query_id=request_id, native_query_sequence=query_sequence,
            capture_epoch_basis="original_root_query_sequence", queried_snapshot_id=first[0],
            queried_revision=first[1], queried_native_revision=first[2])
        return result
    except Exception as error:
        # Optional H never replaces the original root result or permits retry.
        return _unknown("optional_candidate_source_unavailable:" + type(error).__name__)
