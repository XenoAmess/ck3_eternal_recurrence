"""Official MCP v2 server facade for replaceable CK3 gameplay drivers."""

from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path
from typing import Annotated, Literal
from pydantic import Field

IngameUiHandleV1 = Annotated[int, Field(strict=True, gt=0, lt=2**32 - 1)]
PublicCUnitId = Annotated[int, Field(strict=True, ge=0, le=2**31 - 1)]
NormalExitRevisionV1 = Annotated[int, Field(strict=True, gt=0, lt=2**64)]
NormalExitSignatureV1 = Annotated[str, Field(strict=True, min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")]
StressBaseAmountV1 = Annotated[int, Field(strict=True, ge=-300, le=300)]
OrdinaryInteractionKeyV1 = Annotated[str, Field(strict=True, min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_]+$")]
OrdinaryRecipientIdV1 = Annotated[int, Field(strict=True, ge=1, le=2**32 - 2)]
IngameUiRevisionV1 = Annotated[int, Field(strict=True, ge=0, lt=2**64)]
ArmyTooltipReceiptV1 = Annotated[str, Field(strict=True, min_length=32, max_length=32, pattern=r"^[0-9a-f]{32}$")]

from xar_autoplayer.ck3_save_artifacts import Ck3ProfileArtifactInspector
from xar_autoplayer.ck3_runtime_diagnostics import Ck3RuntimeDiagnosticsInspector

from xar_autoplayer.coat_of_arms_configured_resources import (
    query_coat_of_arms_configured_resource_catalog_v1,
    read_coat_of_arms_configured_resource_asset_v1,
)
from xar_autoplayer.coat_of_arms_dlc_sources import (
    query_coat_of_arms_installed_dlc_sources_v1,
)
from xar_autoplayer.coat_of_arms_load_configuration import (
    query_coat_of_arms_load_configuration_v1,
)
from xar_autoplayer.coat_of_arms_vfs_resolution import (
    project_coat_of_arms_vfs_asset_winner_v1,
)
from xar_autoplayer.coat_of_arms_definitions import (
    query_coat_of_arms_definition_catalog_v1,
    read_coat_of_arms_definition_v1,
)
from xar_autoplayer.coat_of_arms_resources import (
    query_coat_of_arms_resource_catalog_v1,
    read_coat_of_arms_render_support_v1,
    read_coat_of_arms_resource_asset_v1,
)
from xar_autoplayer.vanilla_events import (
    CURRENT_CK3_BUILD,
    EXACT_CK3_BUILD,
    ck3_list_vanilla_event_knowledge_v1 as list_vanilla_event_knowledge_v1,
    list_vanilla_event_evidence_v1,
    portable_event_keys_v1,
    query_vanilla_event_knowledge_v1,
    query_vanilla_event_source_provenance_v1,
    read_vanilla_event_evidence_v1,
)
from xar_autoplayer.vanilla_events.portable_evidence import EvidenceBundleError

from .driver import (
    DevelopmentReportDriver,
    GameplayBridgeDriver,
    HybridGameplayDriver,
)
from .mod_driver import load_data_mod_driver
from .native_driver import (
    ConfiguredHybridFallbackDriver,
    MinimizedRejectingVisualDriver,
    NativeHeadlessGameplayDriver,
    selected_pipe_name,
)
from .war31_one_shot_surrender import War31OneShotSurrenderGate
from .succession_transition_contract import (
    ORDINARY_CAMPAIGN_SUCCESSION,
    ROGUE_ONE_LIFE,
    bind_succession_lifecycle_from_environment_v1,
)
from .session_driver import DevelopmentSessionDriver
from .service import GameplayBridgeService
from .army_strengths_mcp_result import build_army_strengths_mcp_result
from .activity_feast_guest_target_private_transport import (
    query_activity_feast_guest_target_private_v1,
)
from .activity_feast_guest_route_proof_private_transport import (
    query_activity_feast_guest_route_proof_private_v1,
)
from .activity_feast_guest_rule_provenance_private_transport import (
    query_activity_feast_guest_rule_provenance_private_v1,
)
from .activity_feast_guest_opinion_private_transport import (
    query_activity_feast_guest_opinion_private_v1,
)
from .war_entry_contract import normalize_war_entry_target_ids


def _default_state_dir() -> Path:
    configured = os.environ.get("XAR_AUTOPLAYER_STATE_DIR")
    if configured:
        return Path(configured)
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        raise RuntimeError("LOCALAPPDATA or XAR_AUTOPLAYER_STATE_DIR is required")
    return Path(local) / "XarAutoplayer"


def _ck3_query_vanilla_event_knowledge_v1(
    event_definition_key: str,
    ck3_build: str = CURRENT_CK3_BUILD,
) -> dict[str, object]:
    """Query frozen vanilla-event knowledge without a running CK3 process."""
    return query_vanilla_event_knowledge_v1(
        event_definition_key,
        ck3_build=ck3_build,
    )


def _ck3_list_vanilla_event_knowledge_v1(
    ck3_build: str = CURRENT_CK3_BUILD,
    query: str | None = None,
    namespace: str | None = None,
    evidence_class: str = "any",
    has_observations: bool | None = None,
    after_key: str | None = None,
    limit: int = 50,
) -> dict[str, object]:
    """Discover frozen event records with stable keyset pagination."""
    portable_keys = frozenset()
    if ck3_build == EXACT_CK3_BUILD:
        try:
            portable_keys = portable_event_keys_v1()
        except EvidenceBundleError:
            pass
    return list_vanilla_event_knowledge_v1(
        build=ck3_build,
        query=query,
        namespace=namespace,
        evidence_class=evidence_class,
        has_observations=has_observations,
        after_key=after_key,
        limit=limit,
        portable_event_keys=portable_keys,
    )


def _ck3_list_vanilla_event_evidence_v1(
    event_definition_key: str | None = None,
    kind: str | None = None,
    after_evidence_id: str | None = None,
    limit: int = 50,
    ck3_build: str = "1.19.0.6",
) -> dict[str, object]:
    """List content-addressed portable evidence without host paths."""
    return list_vanilla_event_evidence_v1(
        event_definition_key,
        kind=kind,
        after_evidence_id=after_evidence_id,
        limit=limit,
        ck3_build=ck3_build,
    )


def _ck3_read_vanilla_event_evidence_v1(
    evidence_id: str,
    offset: int = 0,
    max_bytes: int = 64 * 1024,
    ck3_build: str = "1.19.0.6",
) -> dict[str, object]:
    """Read one verified, bounded chunk by its uncompressed SHA-256."""
    return read_vanilla_event_evidence_v1(
        evidence_id,
        offset=offset,
        max_bytes=max_bytes,
        ck3_build=ck3_build,
    )


def _ck3_query_vanilla_event_source_provenance_v1(
    key: str,
    build: str = CURRENT_CK3_BUILD,
) -> dict[str, object]:
    """Read generated source provenance and unproven lexical caller hits."""
    return query_vanilla_event_source_provenance_v1(key, build)


def _ck3_query_coat_of_arms_resource_catalog_v1(
    game_directory: str,
    kind: str,
    query: str | None = None,
    visible_only: bool = True,
    offset: int = 0,
    limit: int = 50,
) -> dict[str, object]:
    """Index one page of exact-build base-game CoA designer resources."""
    return query_coat_of_arms_resource_catalog_v1(
        game_directory,
        kind,
        query=query,
        visible_only=visible_only,
        offset=offset,
        limit=limit,
    )


def _ck3_query_coat_of_arms_definition_catalog_v1(
    game_directory: str,
    query: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> dict[str, object]:
    """Page exact-build static CoA definitions without claiming VFS state."""
    return query_coat_of_arms_definition_catalog_v1(
        game_directory,
        query=query,
        offset=offset,
        limit=limit,
    )


def _ck3_read_coat_of_arms_definition_v1(
    game_directory: str,
    key: str,
) -> dict[str, object]:
    """Read source candidates and resolve only unambiguous static aliases."""
    return read_coat_of_arms_definition_v1(game_directory, key)


def _ck3_read_coat_of_arms_resource_asset_v1(
    game_directory: str,
    kind: str,
    name: str,
) -> dict[str, object]:
    """Read one exact-build manifest-owned CoA DDS asset."""
    return read_coat_of_arms_resource_asset_v1(
        game_directory,
        kind,
        name,
    )


def _ck3_read_coat_of_arms_render_support_v1(
    game_directory: str,
) -> dict[str, object]:
    """Read exact-build shader provenance, named colors, and surface mask."""
    return read_coat_of_arms_render_support_v1(game_directory)


def _ck3_query_coat_of_arms_load_configuration_v1(
    user_directory: str,
) -> dict[str, object]:
    """Project configured CoA mod candidates without claiming engine mount."""
    return query_coat_of_arms_load_configuration_v1(user_directory)


def _ck3_query_coat_of_arms_installed_dlc_sources_v1(
    game_directory: str,
) -> dict[str, object]:
    """Project installed DLC CoA files without claiming ownership or mount."""
    return query_coat_of_arms_installed_dlc_sources_v1(game_directory)


def _ck3_query_coat_of_arms_configured_resource_catalog_v1(
    user_directory: str,
    kind: str,
    query: str | None = None,
    visible_only: bool = True,
    offset: int = 0,
    limit: int = 50,
) -> dict[str, object]:
    """Page configured mod candidates without choosing an engine winner."""
    return query_coat_of_arms_configured_resource_catalog_v1(
        user_directory,
        kind,
        query=query,
        visible_only=visible_only,
        offset=offset,
        limit=limit,
    )


def _ck3_read_coat_of_arms_configured_resource_asset_v1(
    user_directory: str,
    kind: str,
    candidate_id: str,
) -> dict[str, object]:
    """Read one configured mod DDS by opaque manifest candidate identity."""
    return read_coat_of_arms_configured_resource_asset_v1(
        user_directory,
        kind,
        candidate_id,
    )


def _ck3_project_coat_of_arms_vfs_asset_winner_v1(
    service: GameplayBridgeService,
    game_directory: str,
    logical_path: str,
) -> dict[str, object]:
    """Project a direct-DDS winner from the current exact-build mount receipt."""
    return project_coat_of_arms_vfs_asset_winner_v1(
        service.bridge_diagnostics(),
        game_directory,
        logical_path,
    )


def load_driver(
    factory: str | None,
    *,
    userdir: str | os.PathLike[str] | None = None,
    state_dir: str | os.PathLike[str] | None = None,
    pipe_name: str | None = None,
    war31_one_shot_surrender_gate: War31OneShotSurrenderGate | None = None,
    succession_lifecycle_binding: dict[str, object] | None = None,
    allow_private_death_succession_modal_continue: bool = False,
) -> GameplayBridgeDriver:
    """Load a daemon driver without coupling MCP to a concrete game bridge."""
    def selected_state_dir() -> Path:
        return Path(state_dir) if state_dir else _default_state_dir()

    def selected_save_dir() -> Path:
        return selected_state_dir() / "profile" / "save games"

    if not factory or factory == "vision-report":
        return DevelopmentReportDriver(selected_state_dir())
    if factory == "vision-session":
        return DevelopmentSessionDriver(selected_state_dir())
    if factory == "mod":
        return load_data_mod_driver(userdir)
    if factory == "hybrid":
        return HybridGameplayDriver(
            load_data_mod_driver(userdir),
            DevelopmentSessionDriver(selected_state_dir()),
        )
    if factory == "native-headless":
        return NativeHeadlessGameplayDriver(
            selected_pipe_name(pipe_name),
            state_dir=selected_state_dir(),
            save_dir=selected_save_dir(),
            war31_one_shot_surrender_gate=war31_one_shot_surrender_gate,
            succession_lifecycle_binding=succession_lifecycle_binding,
            allow_private_current_timeline_blocker_query=(
                allow_private_death_succession_modal_continue
            ),
            allow_private_death_succession_modal_continue=(
                allow_private_death_succession_modal_continue
            ),
        )
    if succession_lifecycle_binding is not None:
        raise ValueError("explicit succession lifecycle requires native-headless driver")
    if war31_one_shot_surrender_gate is not None:
        raise ValueError("WAR31 one-shot gate requires native-headless driver")
    if factory == "hybrid-fallback":
        return ConfiguredHybridFallbackDriver(
            NativeHeadlessGameplayDriver(
                selected_pipe_name(pipe_name),
                state_dir=selected_state_dir(),
                save_dir=selected_save_dir(),
            ),
            load_data_mod_driver(userdir),
            MinimizedRejectingVisualDriver(
                DevelopmentSessionDriver(selected_state_dir())
            ),
        )
    module_name, separator, attribute = factory.partition(":")
    if not separator or not module_name or not attribute:
        raise ValueError(
            "driver factory must be vision-report, vision-session, mod, "
            "hybrid, native-headless, hybrid-fallback, or module:callable"
        )
    candidate = getattr(importlib.import_module(module_name), attribute)
    if not callable(candidate):
        raise TypeError("driver factory is not callable")
    driver = candidate()
    if not isinstance(driver, GameplayBridgeDriver):
        raise TypeError("driver factory did not return a GameplayBridgeDriver")
    return driver


def _ck3_query_combat_simulation_inputs_v3(
    service: GameplayBridgeService,
    target_province_id: int,
    attacker_entry_province_id: int | None,
    attacker_army_ids: list[PublicCUnitId],
    defender_army_ids: list[PublicCUnitId],
    expected_revision: int | None = None,
    constructor_adjacency_kind_raw: Annotated[int, Field(strict=True, ge=0, le=0)] | None = None,
) -> dict[str, object]:
    """Official production-v3 facade shared by MCP and contract tests."""
    return service.query_combat_simulation_inputs_v3(
        target_province_id,
        attacker_entry_province_id,
        attacker_army_ids,
        defender_army_ids,
        expected_revision=expected_revision,
        constructor_adjacency_kind_raw=constructor_adjacency_kind_raw,
    )


def _ck3_query_war_entry_assessments(
    service: GameplayBridgeService,
    target_character_ids: list[int],
    expected_revision: int | None = None,
) -> dict[str, object]:
    """Official one-target exact-build strategic-power facade."""
    targets = normalize_war_entry_target_ids(target_character_ids)
    return service.query_war_entry_assessments(
        targets,
        expected_revision=expected_revision,
    )


def _ck3_query_projected_contact_scope_v1(
    service: GameplayBridgeService, subject_army_id: PublicCUnitId,
    target_province_id: int, incoming_entry_province_id: int,
    expected_revision: IngameUiRevisionV1,
) -> dict[str, object]:
    """Read a hypothetical arrival against current target state."""
    return service.query_projected_contact_scope_v1(
        subject_army_id, target_province_id, incoming_entry_province_id,
        expected_revision=expected_revision,
    )


def _ck3_query_actual_contact_scope(
    service: GameplayBridgeService,
    subject_army_id: PublicCUnitId,
    target_province_id: int,
    expected_revision: int | None = None,
) -> dict[str, object]:
    """Official pre-contact prediction or post-contact observation facade."""
    return service.query_actual_contact_scope(
        subject_army_id,
        target_province_id,
        expected_revision=expected_revision,
    )


def _ck3_query_battle_control_snapshot_v1(
    service: GameplayBridgeService,
    subject_army_id: PublicCUnitId,
    expected_revision: int,
) -> dict[str, object]:
    """Observe retreat gates for one full public CUnitID without mutation."""
    return service.query_battle_control_snapshot_v1(
        subject_army_id,
        expected_revision=expected_revision,
    )


def _ck3_query_battle_transition_v1(
    service: GameplayBridgeService,
    combat_id: int,
    expected_revision: int,
) -> dict[str, object]:
    """Observe exact lifecycle and optional current attrition for a full CombatID."""
    return service.query_battle_transition_v1(
        combat_id,
        expected_revision=expected_revision,
    )


def _ck3_query_battle_terminal_transition_v1(
    service: GameplayBridgeService,
    prior_combat_id: int | None,
    subject_public_cunit_id: PublicCUnitId | None,
    expected_revision: int,
    after_terminal_sequence: int | None = None,
    character_ids: list[int] | None = None,
) -> dict[str, object]:
    """Observe a journal-backed terminal event and exact successor state."""
    return service.query_battle_terminal_transition_v1(
        prior_combat_id,
        subject_public_cunit_id,
        expected_revision=expected_revision,
        after_terminal_sequence=after_terminal_sequence,
        character_ids=character_ids,
    )


def _ck3_query_battle_reinforcement_assignment_v1(
    service: GameplayBridgeService,
    selected_public_cunit_id: PublicCUnitId,
    expected_revision: int,
) -> dict[str, object]:
    """Observe one CUnit's native AI help assignment without mutation."""
    return service.query_battle_reinforcement_assignment_v1(
        selected_public_cunit_id,
        expected_revision=expected_revision,
    )


def _ck3_query_campaign_root_context_v1(
    service: GameplayBridgeService,
    expected_revision: int,
) -> dict[str, object]:
    """Observe the exact local-player root and loaded rule selection."""
    return service.query_campaign_root_context_v1(
        expected_revision=expected_revision,
    )


def _ck3_query_steward_develop_county_candidates_v1(
    service: GameplayBridgeService,
    expected_revision: int,
) -> dict[str, object]:
    return service.query_steward_develop_county_candidates_v1(
        expected_revision=expected_revision,
    )


def _ck3_query_council_composition_candidates_v1(
    service: GameplayBridgeService,
    expected_snapshot_id: str,
    public_revision: int,
    native_revision: int,
    date_raw: int,
    owner_character_id: int,
    position_key: str = "councillor_steward",
) -> dict[str, object]:
    """Read one exact paused steward-candidate frame without mutation."""

    return service.query_council_composition_candidates_v1(
        expected_snapshot_id=expected_snapshot_id,
        public_revision=public_revision,
        native_revision=native_revision,
        date_raw=date_raw,
        owner_character_id=owner_character_id,
        position_key=position_key,
    )


def _ck3_change_steward_develop_county_task_v1(
    service: GameplayBridgeService,
    councillor_character_id: int,
    target_county_title_id: int,
    expected_revision: int,
    replace_existing_task: bool,
    task_key: str = "task_develop_county",
) -> dict[str, object]:
    """Submit the fixed native Develop County task; return an ACK only."""

    return service.change_steward_develop_county_task_v1(
        councillor_character_id,
        task_key,
        target_county_title_id,
        expected_revision=expected_revision,
        replace_existing_task=replace_existing_task,
    )


def _ck3_query_player_faction_alerts_v1(
    service: GameplayBridgeService,
    expected_revision: int,
) -> dict[str, object]:
    """Observe exact targeting-faction and county-exposure alert components."""
    return service.query_player_faction_alerts_v1(
        expected_revision=expected_revision,
    )


def _ck3_search_entities_v1(
    service: GameplayBridgeService,
    expected_revision: int,
    relation_filter: str = "any",
    after_character_id: int | None = None,
    limit: int = 50,
) -> dict[str, object]:
    """Search current-player relationship identities with keyset pagination."""
    return service.search_entities_v1(
        expected_revision=expected_revision,
        relation_filter=relation_filter,
        after_character_id=after_character_id,
        limit=limit,
    )


def _ck3_query_turn_bundle_v1(
    service: GameplayBridgeService,
    expected_revision: int,
) -> dict[str, object]:
    """Aggregate the current paused ruler, vitals, realm and succession."""
    return service.query_turn_bundle_v1(
        expected_revision=expected_revision,
    )


def _ck3_query_zhongguo_case_snapshot_v1(
    service: GameplayBridgeService,
    case_kind: str,
    request_nonce: str,
    expected_revision: int,
    subject_character_id: int | None = None,
    owner_character_id: int | None = None,
) -> dict[str, object]:
    """Observe one allowlisted ZhongGuo case without generic variable access."""
    return service.query_zhongguo_case_snapshot_v1(
        case_kind,
        request_nonce,
        expected_revision=expected_revision,
        subject_character_id=subject_character_id,
        owner_character_id=owner_character_id,
    )


def _ck3_query_zhongguo_b1_cycle_snapshot_v1(
    service: GameplayBridgeService,
    request_nonce: str,
    expected_revision: int,
) -> dict[str, object]:
    """Observe the played manager's closed B1 cycle projection."""
    return service.query_zhongguo_b1_cycle_snapshot_v1(
        request_nonce,
        expected_revision=expected_revision,
    )


def _ck3_query_zhongguo_ai_owned_case_snapshot_v1(
    service: GameplayBridgeService,
    owner_character_id: int,
    subject_character_id: int,
    request_nonce: str,
    expected_revision: int | None = None,
) -> dict[str, object]:
    """Observe one authorized AI manager's B1 case without mutation."""
    return service.query_zhongguo_ai_owned_case_snapshot_v1(
        owner_character_id,
        subject_character_id,
        request_nonce,
        expected_revision=expected_revision,
    )


def _ck3_query_zhongguo_result_case_snapshot_v1(
    service: GameplayBridgeService,
    request_nonce: str,
    expected_revision: int,
    owner_character_id: int,
) -> dict[str, object]:
    """Observe the paused player's received result from one expected owner."""
    return service.query_zhongguo_result_case_snapshot_v1(
        request_nonce,
        expected_revision=expected_revision,
        owner_character_id=owner_character_id,
    )


def _ck3_query_zhongguo_b2_pip_snapshot_v1(
    service: GameplayBridgeService,
    request_nonce: str,
    expected_revision: int,
    owner_character_id: int,
) -> dict[str, object]:
    """Observe the player's strict B2 PIP state without generic variables."""
    return service.query_zhongguo_b2_pip_snapshot_v1(
        request_nonce,
        expected_revision=expected_revision,
        owner_character_id=owner_character_id,
    )


def _ck3_query_zhongguo_promotion_compensation_postcondition_v1(
    service: GameplayBridgeService,
    request_nonce: str,
    expected_revision: int,
) -> dict[str, object]:
    """Observe correlated promotion and posted-compensation receipts."""
    return service.query_zhongguo_promotion_compensation_postcondition_v1(
        request_nonce,
        expected_revision=expected_revision,
    )


def _ck3_query_zhongguo_compensation_af5_snapshot_v1(
    service: GameplayBridgeService,
    request_nonce: str,
    expected_revision: int,
) -> dict[str, object]:
    """Observe standalone AF5 compensation state and terminal receipts."""
    return service.query_zhongguo_compensation_af5_snapshot_v1(
        request_nonce,
        expected_revision=expected_revision,
    )


def _ck3_query_zhongguo_workforce_owner_snapshot_v1(
    service: GameplayBridgeService,
    request_nonce: str,
    expected_revision: int,
) -> dict[str, object]:
    """Observe standalone owner-view Workforce state and terminal receipts."""
    return service.query_zhongguo_workforce_owner_snapshot_v1(
        request_nonce,
        expected_revision=expected_revision,
    )


def _ck3_query_zhongguo_projects_metrics_postcondition_v1(
    service: GameplayBridgeService,
    request_nonce: str,
    expected_revision: int,
    owner_character_id: int,
    subject_character_id: int | None = None,
) -> dict[str, object]:
    """Observe one project's contribution-to-metrics receipt lineage."""
    return service.query_zhongguo_projects_metrics_postcondition_v1(
        request_nonce,
        expected_revision=expected_revision,
        owner_character_id=owner_character_id,
        subject_character_id=subject_character_id,
    )


def _ck3_query_zhongguo_career_hc_workforce_postcondition_v1(
    service: GameplayBridgeService,
    request_nonce: str,
    expected_revision: int,
    owner_character_id: int,
) -> dict[str, object]:
    """Observe the exact M360 route-B receipt and career-HC ledger."""
    return service.query_zhongguo_career_hc_workforce_postcondition_v1(
        request_nonce,
        expected_revision=expected_revision,
        owner_character_id=owner_character_id,
    )


def _ck3_query_zhongguo_workforce_collective_snapshot_v1(
    service: GameplayBridgeService,
    request_nonce: str,
    expected_revision: int,
    owner_character_id: int,
) -> dict[str, object]:
    """Observe the player's Workforce collective and owner rolling ledger."""
    return service.query_zhongguo_workforce_collective_snapshot_v1(
        request_nonce,
        expected_revision=expected_revision,
        owner_character_id=owner_character_id,
    )


def _ck3_query_zhongguo_workforce_normal_exit_snapshot_v1(
    service: GameplayBridgeService,
    request_nonce: str,
    expected_revision: int,
    owner_character_id: int,
) -> dict[str, object]:
    """Observe the player's Workforce normal-exit and HC lifecycle."""
    return service.query_zhongguo_workforce_normal_exit_snapshot_v1(
        request_nonce,
        expected_revision=expected_revision,
        owner_character_id=owner_character_id,
    )


def _ck3_query_zhongguo_incident_snapshot_v1(
    service: GameplayBridgeService,
    request_nonce: str,
    expected_revision: int,
    owner_character_id: int,
    profile: str,
) -> dict[str, object]:
    """Observe one strict X/Y/Z incident projection for the player."""
    return service.query_zhongguo_incident_snapshot_v1(
        request_nonce,
        expected_revision=expected_revision,
        owner_character_id=owner_character_id,
        profile=profile,
    )


def _ck3_query_zhongguo_manager_governance_snapshot_v1(
    service: GameplayBridgeService,
    request_nonce: str,
    expected_revision: int,
    subject_character_id: int,
    owner_character_id: int,
) -> dict[str, object]:
    """Observe one manager's frozen team/distribution/score lifecycle."""
    return service.query_zhongguo_manager_governance_snapshot_v1(
        request_nonce,
        expected_revision=expected_revision,
        subject_character_id=subject_character_id,
        owner_character_id=owner_character_id,
    )


def _ck3_query_zhongguo_manager_subordinate_selector_v1(
    service: GameplayBridgeService,
    request_nonce: str,
    expected_revision: int,
) -> dict[str, object]:
    """Select one provider-observed bounded AI manager/subordinate pair."""
    return service.query_zhongguo_manager_subordinate_selector_v1(
        request_nonce,
        expected_revision=expected_revision,
    )


def _ck3_query_zhongguo_scoreboard_state_v1(
    service: GameplayBridgeService,
    request_nonce: str,
    expected_revision: int,
) -> dict[str, object]:
    """Observe fixed scoreboard instances and the current player's ACL."""
    return service.query_zhongguo_scoreboard_state_v1(
        request_nonce,
        expected_revision=expected_revision,
    )


def _ck3_activate_zhongguo_scoreboard_v1(
    service: GameplayBridgeService,
    request_nonce: str,
    action: str,
    expected_revision: int,
    expected_native_revision: int,
    expected_connection_generation: int,
    expected_player_character_id: int,
    expected_provider_session_id: str,
    expected_observation_sequence: int,
    expected_observed_state_revision: int,
    expected_tree_fingerprint_v1: str,
    expected_semantic_fingerprint_v1: str,
    expected_window_instance_pointer: str,
    expected_target_instance_pointer: str,
    expected_target_vtable_pointer: str,
) -> dict[str, object]:
    """Cross the named-widget transport; unavailable stays a typed RED."""
    return service.activate_zhongguo_scoreboard_v1(
        request_nonce,
        action,
        expected_revision=expected_revision,
        expected_native_revision=expected_native_revision,
        expected_connection_generation=expected_connection_generation,
        expected_player_character_id=expected_player_character_id,
        expected_provider_session_id=expected_provider_session_id,
        expected_observation_sequence=expected_observation_sequence,
        expected_observed_state_revision=expected_observed_state_revision,
        expected_tree_fingerprint_v1=expected_tree_fingerprint_v1,
        expected_semantic_fingerprint_v1=expected_semantic_fingerprint_v1,
        expected_window_instance_pointer=expected_window_instance_pointer,
        expected_target_instance_pointer=expected_target_instance_pointer,
        expected_target_vtable_pointer=expected_target_vtable_pointer,
    )


def _ck3_center_map_on_landed_title_v1(
    service: GameplayBridgeService,
    title_key: str,
    expected_revision: int,
) -> dict[str, object]:
    """Explicit presentation-only title navigation; never planner-selected."""
    return service.center_map_on_landed_title_v1(
        title_key,
        expected_revision=expected_revision,
    )


def _ck3_set_played_character_v1(
    service: GameplayBridgeService,
    character_id: int,
    expected_revision: int,
) -> dict[str, object]:
    """Explicit operator action for rebinding to any valid living character."""
    return service.set_player_character_v1(
        character_id,
        expected_revision=expected_revision,
    )


def _ck3_begin_coat_of_arms_source_upload_v2(
    service: GameplayBridgeService,
    total_bytes: int,
    source_sha256: str,
    chunk_count: int,
    chunk_encoding: str,
    expected_revision: int,
    apply: bool,
    expected_game_version: str,
    expected_executable_sha256: str,
) -> dict[str, object]:
    """Reserve one bounded exact-build source upload session."""
    return service.begin_coat_of_arms_source_upload_v2(
        total_bytes=total_bytes,
        source_sha256=source_sha256,
        chunk_count=chunk_count,
        chunk_encoding=chunk_encoding,
        expected_revision=expected_revision,
        apply=apply,
        expected_game_version=expected_game_version,
        expected_executable_sha256=expected_executable_sha256,
    )


def _ck3_append_coat_of_arms_source_chunk_v2(
    service: GameplayBridgeService,
    upload_id: str,
    generation: int,
    chunk_index: int,
    chunk_count: int,
    chunk_encoding: str,
    chunk_bytes: int,
    chunk_sha256: str,
    chunk_base64: str,
    source_sha256: str,
    expected_revision: int,
    apply: bool,
    expected_game_version: str,
    expected_executable_sha256: str,
) -> dict[str, object]:
    """Append one strict-order independently hashed upload chunk."""
    return service.append_coat_of_arms_source_chunk_v2(
        upload_id=upload_id,
        generation=generation,
        chunk_index=chunk_index,
        chunk_count=chunk_count,
        chunk_encoding=chunk_encoding,
        chunk_bytes=chunk_bytes,
        chunk_sha256=chunk_sha256,
        chunk_base64=chunk_base64,
        source_sha256=source_sha256,
        expected_revision=expected_revision,
        apply=apply,
        expected_game_version=expected_game_version,
        expected_executable_sha256=expected_executable_sha256,
    )


def _ck3_commit_coat_of_arms_source_upload_v2(
    service: GameplayBridgeService,
    upload_id: str,
    generation: int,
    chunk_count: int,
    source_sha256: str,
    expected_revision: int,
    apply: bool,
    expected_game_version: str,
    expected_executable_sha256: str,
) -> dict[str, object]:
    """Commit one complete upload through exactly one native apply call."""
    return service.commit_coat_of_arms_source_upload_v2(
        upload_id=upload_id,
        generation=generation,
        chunk_count=chunk_count,
        source_sha256=source_sha256,
        expected_revision=expected_revision,
        apply=apply,
        expected_game_version=expected_game_version,
        expected_executable_sha256=expected_executable_sha256,
    )


def _ck3_abort_coat_of_arms_source_upload_v2(
    service: GameplayBridgeService,
    upload_id: str,
    generation: int,
) -> dict[str, object]:
    """Discard one upload without invoking the native bridge."""
    return service.abort_coat_of_arms_source_upload_v2(
        upload_id=upload_id,
        generation=generation,
    )


def _ck3_probe_coat_of_arms_source_v1(
    service: GameplayBridgeService,
    source: str,
    expected_revision: int,
    apply: bool,
) -> dict[str, object]:
    """Probe one exact source through CK3 without planner or UI fallback."""
    return service.probe_coat_of_arms_source_v1(
        source,
        expected_revision=expected_revision,
        apply=apply,
    )


def _ck3_export_coat_of_arms_source_v1(
    service: GameplayBridgeService,
    expected_revision: int,
) -> dict[str, object]:
    """Export the current design through CK3's native Copy action."""
    return service.export_coat_of_arms_source_v1(
        expected_revision=expected_revision,
    )


def _ck3_query_loaded_feature_manifest_v1(
    service: GameplayBridgeService,
    expected_revision: int,
) -> dict[str, object]:
    """Observe effective feature flags and script DLC keys without ownership inference."""
    return service.query_loaded_feature_manifest_v1(
        expected_revision=expected_revision,
    )


def _ck3_query_frontend_gui_route_v1(
    service: GameplayBridgeService,
) -> dict[str, object]:
    """Read the current CK3 frontend page without screen interpretation."""
    return service.query_frontend_gui_route_v1()


def _ck3_inspect_frontend_gui_tree_v1(
    service: GameplayBridgeService,
) -> dict[str, object]:
    """Inspect bounded native GUI names without OCR or input."""
    return service.inspect_frontend_gui_tree_v1()


def _ck3_inspect_frontend_coat_of_arms_tree_v1(
    service: GameplayBridgeService,
) -> dict[str, object]:
    """Inspect the active native CoA page without OCR or input."""
    return service.inspect_frontend_coat_of_arms_tree_v1()


def _ck3_inspect_frontend_coat_of_arms_pattern_grid_v1(
    service: GameplayBridgeService,
) -> dict[str, object]:
    """Inspect every direct child of the fixed native CoA pattern grid."""
    return service.inspect_frontend_coat_of_arms_pattern_grid_v1()


def _ck3_compare_frontend_coat_of_arms_framebuffer_v1(
    service: GameplayBridgeService,
    reference_png_base64: str,
    reference_png_sha256: str,
) -> dict[str, object]:
    """Compare a hash-bound browser preview to the route-bound CK3 framebuffer."""
    return service.compare_frontend_coat_of_arms_framebuffer_v1(
        reference_png_base64,
        reference_png_sha256,
    )


def _ck3_calibrate_frontend_coat_of_arms_framebuffer_v2(
    service: GameplayBridgeService,
    calibration_id: str,
    phase: str,
) -> dict[str, object]:
    """Capture one hash-receipted solid-state calibration frame."""
    return service.calibrate_frontend_coat_of_arms_framebuffer_v2(
        calibration_id,
        phase,
    )


def _ck3_compare_frontend_coat_of_arms_framebuffer_v2(
    service: GameplayBridgeService,
    calibration_id: str,
    reference_png_base64: str,
    reference_png_sha256: str,
) -> dict[str, object]:
    """Compare a canonical PNG using a fixed reference-independent surface."""
    return service.compare_frontend_coat_of_arms_framebuffer_v2(
        calibration_id,
        reference_png_base64,
        reference_png_sha256,
    )


def _ck3_calibrate_frontend_coat_of_arms_framebuffer_v3(
    service: GameplayBridgeService,
    calibration_id: str,
    phase: str,
) -> dict[str, object]:
    """Capture a bounded native surface/anchor stage for UV registration."""
    return service.calibrate_frontend_coat_of_arms_framebuffer_v3(
        calibration_id,
        phase,
    )


def _ck3_compare_frontend_coat_of_arms_framebuffer_v3(
    service: GameplayBridgeService,
    calibration_id: str,
    reference_png_base64: str,
    reference_png_sha256: str,
) -> dict[str, object]:
    """Compare a canonical PNG through a reference-independent native UV map."""
    return service.compare_frontend_coat_of_arms_framebuffer_v3(
        calibration_id,
        reference_png_base64,
        reference_png_sha256,
    )


def _ck3_capture_frontend_coat_of_arms_framebuffer_v1(
    service: GameplayBridgeService,
    calibration_id: str,
    side: int = 230,
) -> dict[str, object]:
    """Capture the calibrated native CoA surface without a reference image."""
    return service.capture_frontend_coat_of_arms_framebuffer_v1(
        calibration_id, side
    )


def _ck3_prepare_frontend_coat_of_arms_framebuffer_v1(
    service: GameplayBridgeService,
) -> dict[str, object]:
    """Bring the exact route-bound CK3 window forward without input."""
    return service.prepare_frontend_coat_of_arms_framebuffer_v1()


def _ck3_activate_frontend_new_game_v1(
    service: GameplayBridgeService,
) -> dict[str, object]:
    """Activate CK3's named New Game widget and verify Bookmarks opened."""
    return service.activate_frontend_new_game_v1()


def _ck3_activate_frontend_pick_any_character_v1(
    service: GameplayBridgeService,
) -> dict[str, object]:
    """Activate Play Any Ruler and verify the native lobby opened."""
    return service.activate_frontend_pick_any_character_v1()


def _ck3_activate_frontend_start_1066_bookmark_character_v1(
    service: GameplayBridgeService,
    character_name_key: str,
) -> dict[str, object]:
    """Select an exact-build 1066 bookmark character and start its map."""
    return service.activate_frontend_start_1066_bookmark_character_v1(
        character_name_key
    )


def _ck3_activate_frontend_prepare_custom_ruler_v1(
    service: GameplayBridgeService,
) -> dict[str, object]:
    """Select a fixed featured ruler and verify designer access in the lobby."""
    return service.activate_frontend_prepare_custom_ruler_v1()


def _ck3_activate_frontend_ruler_designer_v1(
    service: GameplayBridgeService,
) -> dict[str, object]:
    """Activate the fixed default Ruler Designer button and verify its route."""
    return service.activate_frontend_ruler_designer_v1()


def _ck3_activate_frontend_coat_of_arms_designer_v1(
    service: GameplayBridgeService,
) -> dict[str, object]:
    """Activate the dynasty CoA edit button and verify the dedicated route."""
    return service.activate_frontend_coat_of_arms_designer_v1()


def _ck3_commit_frontend_dynasty_coat_of_arms_v1(
    service: GameplayBridgeService,
) -> dict[str, object]:
    """Commit the current dynasty CoA and verify the dedicated page closed."""
    return service.commit_frontend_dynasty_coat_of_arms_v1()


def _ck3_activate_frontend_coat_of_arms_custom_mode_v1(
    service: GameplayBridgeService,
) -> dict[str, object]:
    """Enter native custom mode and verify the background grid is ready."""
    return service.activate_frontend_coat_of_arms_custom_mode_v1()


def _ck3_query_pending_character_interaction_context_v1(
    service: GameplayBridgeService,
    pending_interaction_id: int,
    expected_revision: int,
) -> dict[str, object]:
    """Observe one pending request, including costs and typed war binding."""
    return service.query_pending_character_interaction_context_v1(
        pending_interaction_id,
        expected_revision=expected_revision,
    )


def _ck3_query_current_event_window_context_v1(
    service: GameplayBridgeService,
    event_instance_id: int,
    expected_revision: int,
) -> dict[str, object]:
    """Observe one active event's options and lossy typed effect indicators."""
    return service.query_current_event_window_context_v1(
        event_instance_id,
        expected_revision=expected_revision,
    )


def _ck3_query_current_timeline_blocker_context_v1(
    service: GameplayBridgeService,
    expected_revision: int,
) -> dict[str, object]:
    """Read the existing private timeline context through the opted-in MCP facade."""
    return service.query_current_timeline_blocker_context_v1(
        expected_revision=expected_revision,
    )


def _ck3_query_minor_religious_war_defenders_private_v1(
    service: GameplayBridgeService,
    target_character_id: int,
    expected_revision: int,
) -> dict[str, object]:
    """Private war readback seam; intentionally absent from the MCP tool list."""
    query = getattr(
        service.driver, "query_minor_religious_war_defenders_private_v1", None
    )
    if not callable(query):
        raise RuntimeError(
            "minor religious war defenders private query is unavailable"
        )
    return query(
        target_character_id=target_character_id,
        expected_revision=expected_revision,
    )


def _ck3_query_m5_war_primary_current_private_v1(
    service: GameplayBridgeService,
    target_character_id: int,
    expected_revision: int,
) -> dict[str, object]:
    """Private M5 war readback seam; intentionally absent from public tools."""
    query = getattr(
        service.driver, "query_m5_war_primary_current_private_v1", None
    )
    if not callable(query):
        raise RuntimeError("M5 war primary current private query is unavailable")
    return query(
        target_character_id=target_character_id,
        expected_revision=expected_revision,
    )


def _ck3_query_player_epidemic_recovery_private_v1(
    service: GameplayBridgeService,
    expected_revision: int,
    requested_title_id: int = 0,
    expected_event_instance_id: int | None = None,
) -> dict[str, object]:
    """Private M2 CE1 readback seam; intentionally absent from the MCP tool list."""
    return service.query_player_epidemic_recovery_private_v1(
        expected_revision=expected_revision,
        requested_title_id=requested_title_id,
        expected_event_instance_id=expected_event_instance_id,
    )


def _ck3_query_construction_province_income_private_v1(
    service: GameplayBridgeService,
    expected_revision: int,
    barony_title_id: int,
    province_id: int,
) -> dict[str, object]:
    """Private aggregate readback; intentionally absent from public MCP tools."""
    from .domain_construction_private_transport_v1 import (
        query_construction_province_income_private,
    )

    return query_construction_province_income_private(
        service.driver,
        expected_revision=expected_revision,
        barony_title_id=barony_title_id,
        province_id=province_id,
    )


def _ck3_continue_death_succession_modal_v1(
    service: GameplayBridgeService,
    expected_revision: int,
    expected_played_character_id: int,
    expected_episode_run_id: str,
) -> dict[str, object]:
    """Continue one exact successor modal through the existing typed private transport."""
    return service.continue_death_succession_modal_private_v1(
        expected_revision=expected_revision,
        expected_played_character_id=expected_played_character_id,
        expected_episode_run_id=expected_episode_run_id,
    )


def _ck3_preview_active_combat_retreat_v1(
    service: GameplayBridgeService,
    selected_public_cunit_id: PublicCUnitId,
    target_province_id: int,
    expected_revision: int,
) -> dict[str, object]:
    """Issue a token only for a legal same-frame exact native route."""
    return service.preview_active_combat_retreat_v1(
        selected_public_cunit_id,
        target_province_id,
        expected_revision=expected_revision,
    )


def _ck3_order_active_combat_retreat_v1(
    service: GameplayBridgeService,
    selected_public_cunit_id: PublicCUnitId,
    expected_revision: int,
    expected_combat_id: int,
    expected_side_index: int,
    expected_scope: str,
    target_province_id: int,
    candidate_token: str,
) -> dict[str, object]:
    """Re-prove and consume one active-retreat token before player movement."""
    return service.order_active_combat_retreat_v1(
        selected_public_cunit_id,
        expected_revision=expected_revision,
        expected_combat_id=expected_combat_id,
        expected_side_index=expected_side_index,
        expected_scope=expected_scope,
        target_province_id=target_province_id,
        candidate_token=candidate_token,
    )


def _forbid_unknown_tool_arguments_v1(server: object, tool_name: str) -> None:
    """Freeze one pinned MCP 2.0 tool to an exact top-level input object."""
    manager = getattr(server, "_tool_manager", None)
    tools = getattr(manager, "_tools", None)
    tool = tools.get(tool_name) if isinstance(tools, dict) else None
    metadata = getattr(tool, "fn_metadata", None)
    argument_model = getattr(metadata, "arg_model", None)
    model_config = getattr(argument_model, "model_config", None)
    model_rebuild = getattr(argument_model, "model_rebuild", None)
    model_json_schema = getattr(argument_model, "model_json_schema", None)
    if not (
        isinstance(model_config, dict)
        and callable(model_rebuild)
        and callable(model_json_schema)
    ):
        raise RuntimeError(
            "pinned MCP tool metadata cannot enforce exact v1 arguments"
        )
    model_config["extra"] = "forbid"
    model_rebuild(force=True)
    parameters = model_json_schema()
    if not (
        isinstance(parameters, dict)
        and parameters.get("additionalProperties") is False
    ):
        raise RuntimeError("MCP exact-argument schema did not become closed")
    tool.parameters = parameters


def _ck3_query_current_battle_knight_v1(
    service: GameplayBridgeService,
    subject_public_cunit_id: PublicCUnitId,
    character_id: int,
    regiment_id: int,
    expected_played_character_id: int,
    expected_war_id: int,
    expected_native_carmy_id: int,
    expected_combat_id: int,
    expected_province_id: int,
    expected_date_raw: int,
    expected_revision: int,
    expected_native_revision: int,
    expected_snapshot_id: str,
) -> dict[str, object]:
    """Private current read; every identity comes from this session's frame."""
    return service.query_current_battle_knight_v1(
        subject_public_cunit_id=subject_public_cunit_id,
        character_id=character_id,
        regiment_id=regiment_id,
        expected_played_character_id=expected_played_character_id,
        expected_war_id=expected_war_id,
        expected_native_carmy_id=expected_native_carmy_id,
        expected_combat_id=expected_combat_id,
        expected_province_id=expected_province_id,
        expected_date_raw=expected_date_raw,
        expected_revision=expected_revision,
        expected_native_revision=expected_native_revision,
        expected_snapshot_id=expected_snapshot_id,
    )

def create_server(
    driver: GameplayBridgeDriver,
    *,
    profile_dir: str | os.PathLike[str] | None = None,
):
    """Build the MCP server lazily so baseline vision installs need no SDK."""
    try:
        from mcp.server import MCPServer
        from mcp.types import CallToolResult, ToolAnnotations
    except ImportError as error:
        raise RuntimeError(
            "MCP mode requires the optional dependency: pip install 'mcp==2.0.0'"
        ) from error

    service = GameplayBridgeService(driver)
    artifact_inspector = (
        Ck3ProfileArtifactInspector(profile_dir)
        if profile_dir is not None
        else None
    )
    runtime_diagnostics = (
        Ck3RuntimeDiagnosticsInspector(profile_dir)
        if profile_dir is not None
        else None
    )
    read_only_tool = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )
    server = MCPServer(
        name="Xar CK3 Gameplay Bridge",
        version="0.1.0",
        instructions=(
            "Control the current one-life CK3 episode through semantic steps. "
            "Use ck3_plan_turn unless a specific gameplay step is requested."
        ),
    )

    @server.tool()
    def ck3_get_capabilities() -> dict[str, object]:
        """List the current bridge backend and gameplay steps it implements."""
        return service.capabilities()

    @server.tool(annotations=read_only_tool)
    def ck3_query_core_frame_v1() -> dict[str, object]:
        """Read the exact .4 app-main player/clock prefix; complete_snapshot stays false."""
        return service.query_core_frame_v1()

    _forbid_unknown_tool_arguments_v1(server, "ck3_query_core_frame_v1")

    if getattr(driver, "allow_private_prisoner_collection_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_player_prisoner_collection_private_v1(
            expected_revision: int, ransom_ordinal: int = 0,
            release_option_keys: list[str] | None = None,
            release_material_target_character_id: int | None = None,
        ) -> dict[str, object]:
            """Read custody, release terms and an optional retained target's current relation."""
            if release_material_target_character_id is not None:
                return driver.query_player_prisoner_collection_private_v1(
                    expected_revision=expected_revision, ransom_ordinal=ransom_ordinal,
                    release_option_keys=release_option_keys,
                    release_material_target_character_id=release_material_target_character_id,
                )
            if release_option_keys is not None:
                return driver.query_player_prisoner_collection_private_v1(
                    expected_revision=expected_revision,
                    ransom_ordinal=ransom_ordinal,
                    release_option_keys=release_option_keys,
                )
            if ransom_ordinal != 0:
                return driver.query_player_prisoner_collection_private_v1(
                    expected_revision=expected_revision,
                    ransom_ordinal=ransom_ordinal,
                )
            return driver.query_player_prisoner_collection_private_v1(
                expected_revision=expected_revision,
            )

    if getattr(driver, "allow_private_prisoner_ransom_action", False) is True:
        @server.tool()
        def ck3_ransom_player_prisoner_private_v1(
            collection: dict[str, object], prisoner_character_id: int,
        ) -> dict[str, object]:
            """Submit one current native ransom quote and return its pending ACK."""
            return driver.submit_player_prisoner_ransom_private_v1(
                collection=collection, prisoner_character_id=prisoner_character_id,
            )

        @server.tool()
        def ck3_release_player_prisoner_private_v1(
            collection: dict[str, object], prisoner_character_id: int,
        ) -> dict[str, object]:
            """Submit the queried native release terms and return a pending ACK."""
            return driver.submit_player_prisoner_release_private_v1(
                collection=collection, prisoner_character_id=prisoner_character_id,
            )

    if getattr(driver, "allow_private_current_first_heir_relationship_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_current_first_heir_relationship_private_v1(
            expected_native_revision: int,
        ) -> dict[str, object]:
            """Read the current first heir's bilateral marriage relation on a paused frame."""
            return driver.query_current_first_heir_relationship_private_v1(
                expected_native_revision=expected_native_revision,
            )

    if getattr(driver, "allow_private_player_child_marriage_subject_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_player_child_marriage_subject_private_v1(
            expected_native_revision: int, subject_character_id: int,
            diagnose_family_arrays: bool = False,
        ) -> dict[str, object]:
            """Read one player child and current native marriage proposal legality."""
            return driver.query_player_child_marriage_subject_private_v1(
                expected_native_revision=expected_native_revision,
                subject_character_id=subject_character_id,
                diagnose_family_arrays=diagnose_family_arrays,
            )

        @server.tool(annotations=read_only_tool)
        def ck3_query_player_child_marriage_value_private_v1(
            legality: dict[str, object], candidate_character_id: int,
            request_matrilineal_option: bool = False,
        ) -> dict[str, object]:
            """Read one player's child match, optionally selecting matrilineal."""
            return driver.query_player_child_marriage_value_private_v1(
                legality=legality, candidate_character_id=candidate_character_id,
                request_matrilineal_option=request_matrilineal_option,
            )

    if getattr(driver, "allow_private_activity_feast_guest_target_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_activity_feast_guest_target_private_v1(
            expected_revision: int, target_character_id: int,
        ) -> dict[str, object]:
            """Read one full feast guest ID on the current paused Stage-5 frame."""
            return query_activity_feast_guest_target_private_v1(
                driver, expected_revision=expected_revision,
                target_character_id=target_character_id,
            )

    if getattr(driver, "allow_private_active_scheme_sway_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_active_scheme_sway_target_private_v1(
            expected_revision: int, target_character_id: int,
        ) -> dict[str, object]:
            """Read the current Sway instance, opinion and native final legality."""
            return driver.query_active_scheme_sway_target_private_v1(
                expected_revision=expected_revision,
                target_character_id=target_character_id,
            )

    if getattr(driver, "allow_private_active_scheme_sway_action", False) is True:
        @server.tool()
        def ck3_start_active_scheme_sway_private_v1(
            readback: dict[str, object], action_id: str,
        ) -> dict[str, object]:
            """Submit one selected Sway target from its current native final quote."""
            return driver.submit_active_scheme_sway_private_v1(readback=readback, action_id=action_id)

        @server.tool(annotations=read_only_tool)
        def ck3_query_active_scheme_sway_receipt_private_v1(
            target_character_id: int, action_id: str, expected_revision: int,
            pre_capture_epoch: int,
        ) -> dict[str, object]:
            """Read the independent active-instance receipt for a submitted Sway."""
            return driver.query_active_scheme_sway_receipt_private_v1(
                target_character_id=target_character_id, action_id=action_id,
                expected_revision=expected_revision, pre_capture_epoch=pre_capture_epoch,
            )

    if getattr(driver, "allow_private_realm_law_paused_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_realm_law_final_terms_private_v1(
            expected_revision: int,
        ) -> dict[str, object]:
            """Read active realm laws, native final enactability and all cost slots."""
            return driver.query_realm_law_final_terms_private_v1(
                expected_revision=expected_revision,
            )

    if getattr(driver, "allow_private_realm_law_action", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_realm_law_crown_action_private_v1(expected_revision: int) -> dict[str, object]:
            """Read final crown-law candidates, balances and title successor state."""
            return driver.query_realm_law_crown_action_private_v1(expected_revision=expected_revision)

        @server.tool()
        def ck3_enact_realm_law_crown_private_v1(
            readback: dict[str, object], law_key: str, budgets: dict[str, int],
            action_id: str,
        ) -> dict[str, object]:
            """Enact one explicitly selected crown law within caller resource limits."""
            return driver.submit_realm_law_crown_private_v1(
                readback=readback, law_key=law_key, budgets=budgets, action_id=action_id,
            )

        @server.tool(annotations=read_only_tool)
        def ck3_query_realm_law_crown_receipt_private_v1(
            expected_revision: int, submitted_request_id: str,
        ) -> dict[str, object]:
            """Read independent effective-law, resource and successor postconditions."""
            return driver.query_realm_law_crown_receipt_private_v1(
                expected_revision=expected_revision, submitted_request_id=submitted_request_id,
            )

    if getattr(driver, "allow_private_council_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_council_composition_candidates_private_v1(
            expected_revision: int,
            position_key: str = "councillor_steward",
        ) -> dict[str, object]:
            """Read native Steward, Chancellor or Spymaster candidates through the private mailbox."""
            return driver.query_council_composition_candidates_private_v1(
                expected_revision=expected_revision, position_key=position_key,
            )

        @server.tool(annotations=read_only_tool)
        def ck3_query_council_final_gates_private_v1(
            expected_revision: int,
            position_key: str = "councillor_steward",
        ) -> dict[str, object]:
            """Read native candidate, pending interaction and incumbent final gates."""
            return driver.query_council_final_gates_private_v1(
                expected_revision=expected_revision, position_key=position_key,
            )

    if getattr(driver, "allow_private_council_action", False) is True:
        @server.tool()
        def ck3_assign_councillor_private_v1(
            query: dict[str, object], candidate_character_id: int,
            expected_revision: int, action_request_id: str | None = None,
        ) -> dict[str, object]:
            """Assign one selected native council candidate from its same-frame quote."""
            return driver.submit_council_assign_private_v1(
                query=query, candidate_character_id=candidate_character_id,
                expected_revision=expected_revision, action_request_id=action_request_id,
            )

        @server.tool(annotations=read_only_tool)
        def ck3_query_council_assign_receipt_private_v1(
            pending: dict[str, object], expected_revision: int,
        ) -> dict[str, object]:
            """Read the assignment's independent later-frame incumbent receipt."""
            return driver.query_council_assign_receipt_private_v1(pending=pending, expected_revision=expected_revision)

    if getattr(driver, "allow_private_government_runtime_adapter_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_government_runtime_adapter_private_v1(
            expected_revision: int,
        ) -> dict[str, object]:
            """Read the native government identity and same-frame adapter readiness."""
            return driver.query_government_runtime_adapter_private_v1(
                expected_revision=expected_revision,
            )

    if getattr(driver, "allow_private_active_scheme_sway_outcome_opinion_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_active_scheme_sway_outcome_opinion_private_v1(
            expected_revision: int, target_character_id: int,
        ) -> dict[str, object]:
            """Read current target opinion and native Sway modifiers without an event."""
            return driver.query_active_scheme_sway_outcome_opinion_private_v1(
                expected_revision=expected_revision,
                target_character_id=target_character_id,
            )

    if getattr(driver, "allow_private_family_obligations_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_family_obligations_private_v1(
            expected_revision: int, subject_character_id: int | None = None,
            candidate_character_id: int | None = None, request_matrilineal_option: bool = False,
            break_recipient_character_id: int | None = None, ally_character_id: int | None = None,
            enumerate_current_allies: bool = False,
        ) -> dict[str, object]:
            """Read requested native family terms or a current-player ally war-support pair."""
            return driver.query_family_obligations_private_v1(
                expected_revision=expected_revision, subject_character_id=subject_character_id,
                candidate_character_id=candidate_character_id,
                request_matrilineal_option=request_matrilineal_option,
                break_recipient_character_id=break_recipient_character_id, ally_character_id=ally_character_id,
                enumerate_current_allies=enumerate_current_allies,
            )

        @server.tool()
        def ck3_submit_call_ally_to_war_private_v1(
            expected_revision: int, war_id: int, recipient_character_id: int,
        ) -> dict[str, object]:
            """Quote and send one selected ally invitation; ACK does not prove a join."""
            return service.submit_call_ally_to_war_private_v1(
                expected_revision=expected_revision, war_id=war_id,
                recipient_character_id=recipient_character_id,
            )

    if getattr(driver, "allow_private_war_cash_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_war_cash_current_resources_private_v1(
            expected_revision: int,
        ) -> dict[str, object]:
            """Read treasury, monthly flow and native military expense vectors."""
            return driver.query_war_cash_current_resources_private_v1(expected_revision=expected_revision)

        @server.tool(annotations=read_only_tool)
        def ck3_query_construction_cash_outcome_private_v1(
            expected_revision: int, reserve_gold_raw: int,
            existing_commitment_gold_raw: int, horizon_months: int,
        ) -> dict[str, object]:
            """Read current cash scenarios with the real durable construction receipt."""
            return driver.query_construction_cash_outcome_private_v1(
                expected_revision=expected_revision, reserve_gold_raw=reserve_gold_raw,
                existing_commitment_gold_raw=existing_commitment_gold_raw,
                horizon_months=horizon_months,
            )

        @server.tool(annotations=read_only_tool)
        def ck3_query_war_cash_termination_send_costs_private_v1(
            expected_revision: int, war_id: int, outcome: str,
        ) -> dict[str, object]:
            """Read one war choice's on-send fees, keeping unpriced effects explicit."""
            return driver.query_war_cash_termination_send_costs_private_v1(
                expected_revision=expected_revision, war_id=war_id, outcome=outcome,
            )

    if getattr(driver, "allow_private_player_religion_context_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_player_religion_context_v1(
            expected_revision: int,
        ) -> dict[str, object]:
            """Read current native Rite/Faith/Religion IDs, keys and raw resources."""
            return driver.query_player_religion_context_private_v1(
                expected_revision=expected_revision,
            )

        @server.tool(annotations=read_only_tool)
        def ck3_query_player_holy_order_loan_context_v1(
            expected_revision: int,
        ) -> dict[str, object]:
            """Read native holy-order borrowing terms and current debt; no action."""
            return driver.query_player_holy_order_loan_context_private_v1(
                expected_revision=expected_revision,
            )

        @server.tool(annotations=read_only_tool)
        def ck3_query_player_holy_order_context_v1(
            expected_revision: int,
        ) -> dict[str, object]:
            """Read native holy-order patronage, leases and independent military hire terms."""
            return driver.query_player_holy_order_context_private_v1(
                expected_revision=expected_revision,
            )

        @server.tool(annotations=read_only_tool)
        def ck3_query_player_holy_order_selected_title_terms_v1(
            expected_revision: int,
        ) -> dict[str, object]:
            """Read native holy-order candidate estates and per-title final terms; no action."""
            return driver.query_player_holy_order_selected_title_terms_private_v1(
                expected_revision=expected_revision,
            )

        @server.tool(annotations=read_only_tool)
        def ck3_query_player_seek_indulgences_terms_v1(
            expected_revision: Annotated[int, Field(strict=True, gt=0)],
            recipient_character_id: Annotated[int, Field(strict=True, ge=0, le=2**32 - 2)],
        ) -> dict[str, object]:
            """Read ordinary indulgence visibility and native final eligibility; no action."""
            return service.query_player_seek_indulgences_terms_v1(
                expected_revision=expected_revision, recipient_character_id=recipient_character_id,
            )

        @server.tool(annotations=read_only_tool)
        def ck3_query_player_head_of_faith_gold_context_v1(
            expected_revision: int,
        ) -> dict[str, object]:
            """Read native ordinary clergy-gold terms, acceptance and separate effect fee."""
            return driver.query_player_head_of_faith_gold_context_private_v1(
                expected_revision=expected_revision,
            )

        @server.tool(annotations=read_only_tool)
        def ck3_query_player_repentance_context_v1(
            expected_revision: int,
        ) -> dict[str, object]:
            """Read native excommunication trait and current-head repentance final preview."""
            return driver.query_player_repentance_context_private_v1(
                expected_revision=expected_revision,
            )

    if getattr(driver, "allow_private_player_religion_doctrines_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_player_religion_doctrines_v1(expected_revision: int) -> dict[str, object]:
            """Read current and main Faith doctrines and native parameter rows."""
            return driver.query_player_religion_doctrines_private_v1(expected_revision=expected_revision)

    if getattr(driver, "allow_private_player_rite_governance_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_player_rite_governance_v1(expected_revision: int) -> dict[str, object]:
            """Read the state Rite, heads and organization with separate source status."""
            return driver.query_player_rite_governance_private_v1(expected_revision=expected_revision)

    if getattr(driver, "allow_private_player_religion_conversion_terms_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_player_religion_conversion_terms_v1(
            expected_revision: int, target_rite_id: int,
        ) -> dict[str, object]:
            """Read the native conversion gate and quoted costs for the selected Rite."""
            return driver.query_player_religion_conversion_terms_private_v1(
                expected_revision=expected_revision, target_rite_id=target_rite_id,
            )

        @server.tool()
        def ck3_convert_player_religion_private_v1(
            expected_revision: int, target_rite_id: int,
            max_piety_cost_raw: int, action_id: str,
        ) -> dict[str, object]:
            """Submit one explicit ordinary paid target and return its pending record."""
            return service.submit_player_religion_conversion_private_v1(
                expected_revision=expected_revision, target_rite_id=target_rite_id,
                max_piety_cost_raw=max_piety_cost_raw, action_id=action_id,
            )

        @server.tool(annotations=read_only_tool)
        def ck3_query_player_religion_conversion_result_private_v1(
            expected_revision: int, request_id: str, action_id: str,
        ) -> dict[str, object]:
            """Read actual later conversion material for the retained native request."""
            return service.query_player_religion_conversion_result_private_v1(
                expected_revision=expected_revision, request_id=request_id, action_id=action_id,
            )

    if getattr(driver, "allow_private_active_scheme_sway_completion_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_active_scheme_sway_completion_private_v1(
            expected_revision: int, target_character_id: int, scheme_instance_id: int,
        ) -> dict[str, object]:
            """Read exact Sway instance state without inferring its terminal cause."""
            return driver.query_active_scheme_sway_completion_private_v1(
                expected_revision=expected_revision, target_character_id=target_character_id,
                scheme_instance_id=scheme_instance_id,
            )

    if callable(getattr(driver, "submit_regular_maa_create_private_v1", None)):
        @server.tool()
        def ck3_submit_regular_maa_create(
            expected_revision: int, type_index: int, action_id: str,
        ) -> dict[str, object]:
            """Submit one regular MAA command; queued ACK does not verify creation/payment."""
            return service.submit_regular_maa_create_private_v1(
                expected_revision=expected_revision, type_index=type_index, action_id=action_id,
            )

    if getattr(driver, "allow_private_player_ordinary_holy_war_declaration_context_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_player_ordinary_holy_war_declaration_context_v1(
            expected_revision: int, declaration_id: str,
        ) -> dict[str, object]:
            """Read the selected ordinary holy-war context and independent CB resource quote."""
            return service.query_player_ordinary_holy_war_declaration_context_private_v1(
                expected_revision=expected_revision, declaration_id=declaration_id,
            )

    if getattr(driver, "allow_private_player_clergy_appointment_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_player_clergy_appointment_v1(
            expected_revision: int, candidate_character_id: int,
        ) -> dict[str, object]:
            """Read native candidate appointment and reassignment observations."""
            return driver.query_player_clergy_appointment_private_v1(expected_revision=expected_revision, candidate_character_id=candidate_character_id)

        @server.tool()
        def ck3_submit_county_conversion_task(
            expected_revision: int, expected_active_task_id: int,
            expected_incumbent_character_id: int, province_id: int,
            replace_existing_task: bool, action_id: str,
        ) -> dict[str, object]:
            """Queue one selected conversion task; verify its actual assignment separately."""
            return service.submit_county_conversion_task_private_v1(
                expected_revision=expected_revision,
                expected_active_task_id=expected_active_task_id,
                expected_incumbent_character_id=expected_incumbent_character_id,
                province_id=province_id, replace_existing_task=replace_existing_task,
                action_id=action_id,
            )

        @server.tool(annotations=read_only_tool)
        def ck3_query_county_conversion_task_result(
            expected_revision: int, submitted_request_id: str, action_id: str,
        ) -> dict[str, object]:
            """Read current native task assignment for the retained submitted request."""
            return service.query_county_conversion_task_result_private_v1(
                expected_revision=expected_revision,
                submitted_request_id=submitted_request_id, action_id=action_id,
            )

    if getattr(driver, "allow_private_player_rite_members_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_player_rite_members_v1(
            expected_revision: int,
        ) -> dict[str, object]:
            """Read the current Rite and Faith member lists in native order."""
            return driver.query_player_rite_members_private_v1(expected_revision=expected_revision)

    if getattr(driver, "allow_private_player_religion_hostility_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_player_religion_hostility_v1(
            expected_revision: int, target_rite_id: int,
        ) -> dict[str, object]:
            """Read native hostility values for an explicitly selected Rite."""
            return driver.query_player_religion_hostility_private_v1(expected_revision=expected_revision, target_rite_id=target_rite_id)

    if getattr(driver, "allow_private_player_religion_doctrine_knowledge_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_player_religion_doctrine_knowledge_v1(
            expected_revision: int, doctrine_key: str | None = None,
        ) -> dict[str, object]:
            """Read learned doctrines or the native lookup for one doctrine key."""
            return driver.query_player_religion_doctrine_knowledge_private_v1(expected_revision=expected_revision, doctrine_key=doctrine_key)

    if getattr(driver, "allow_private_player_religion_tenets_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_player_religion_tenets_v1(
            expected_revision: int,
            target_rite_id: int | None = None, tenet_key: str | None = None,
            include_knowledge_catalogue: Annotated[bool, Field(strict=True)] = False,
        ) -> dict[str, object]:
            """Read Tenets, optional paired .3 comparison and native knowledge inputs."""
            if target_rite_id is None and tenet_key is None and include_knowledge_catalogue is False:
                return driver.query_player_religion_tenets_private_v1(expected_revision=expected_revision)
            optional_fields: dict[str, object] = {}
            if include_knowledge_catalogue is True:
                optional_fields["include_knowledge_catalogue"] = True
            if target_rite_id is not None or tenet_key is not None:
                optional_fields.update(target_rite_id=target_rite_id, tenet_key=tenet_key)
            return driver.query_player_religion_tenets_private_v1(
                expected_revision=expected_revision,
                **optional_fields,
            )

    if getattr(driver, "allow_private_player_religion_conversion_choices_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_player_religion_conversion_choices_v1(
            expected_revision: int,
        ) -> dict[str, object]:
            """Read native conversion choices and current Faith Rite membership."""
            return driver.query_player_religion_conversion_choices_private_v1(expected_revision=expected_revision)

    if getattr(driver, "allow_private_player_religion_conversion_inputs_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_player_religion_conversion_inputs_v1(
            expected_revision: int, target_rite_id: int,
        ) -> dict[str, object]:
            """Read native conversion knowledge and predicted fulfillment inputs."""
            return driver.query_player_religion_conversion_inputs_private_v1(expected_revision=expected_revision, target_rite_id=target_rite_id)

    if getattr(driver, "allow_private_epidemic_treatment_presence_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_player_epidemic_treatment_presence_private_v1(
            expected_revision: int,
        ) -> dict[str, object]:
            """Read actual player treatment variables and modifier presence."""
            return driver.query_player_epidemic_treatment_presence_private_v1(
                expected_revision=expected_revision,
            )

    if getattr(driver, "allow_private_player_religion_conversion_reasons_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_player_religion_conversion_reasons_v1(
            expected_revision: int, target_rite_id: int,
        ) -> dict[str, object]:
            """Read native conversion reason inputs for the selected Rite."""
            return driver.query_player_religion_conversion_reasons_private_v1(
                expected_revision=expected_revision, target_rite_id=target_rite_id,
            )

    if getattr(driver, "allow_private_player_religion_reform_context_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_player_religion_reform_context_v1(
            expected_revision: int,
        ) -> dict[str, object]:
            """Read native reform components without opening the reform interface."""
            return driver.query_player_religion_reform_context_private_v1(
                expected_revision=expected_revision,
            )

    if getattr(driver, "allow_private_active_scheme_sway_completion_execution_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_active_scheme_sway_completion_execution_private_v1(
            expected_revision: int, target_character_id: int, scheme_instance_id: int,
            after_sequence: int = 0,
        ) -> dict[str, object]:
            """Read native hidden Sway branch execution records for the exact instance."""
            return driver.query_active_scheme_sway_completion_execution_private_v1(
                expected_revision=expected_revision, target_character_id=target_character_id,
                scheme_instance_id=scheme_instance_id, after_sequence=after_sequence,
            )

    if getattr(driver, "allow_private_epidemic_recovery_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_player_epidemic_recovery_private_v1(
            expected_revision: int, requested_title_id: int = 0,
            expected_event_instance_id: int | None = None,
        ) -> dict[str, object]:
            """Read the native CE1 county list or a specified county after recovery."""
            return _ck3_query_player_epidemic_recovery_private_v1(
                service, expected_revision=expected_revision, requested_title_id=requested_title_id,
                expected_event_instance_id=expected_event_instance_id,
            )

    if getattr(driver, "allow_private_player_religion_doctrine_catalogue_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_player_religion_doctrine_catalogue_v1(
            expected_revision: int,
        ) -> dict[str, object]:
            """Read all loaded native Doctrine definitions."""
            return driver.query_player_religion_doctrine_catalogue_private_v1(
                expected_revision=expected_revision,
            )

    if getattr(driver, "allow_private_player_religion_numeric_special_parameters_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_player_religion_numeric_special_parameters_v1(
            expected_revision: int,
        ) -> dict[str, object]:
            """Read Rite numeric caches and the separate native Faith final value."""
            return driver.query_player_religion_numeric_special_parameters_private_v1(
                expected_revision=expected_revision,
            )

    if getattr(driver, "allow_private_player_religion_conversion_outcome_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_player_religion_conversion_outcome_v1(
            expected_revision: int, target_rite_id: int,
        ) -> dict[str, object]:
            """Read current conversion outcome facts without attributing resource changes."""
            return driver.query_player_religion_conversion_outcome_private_v1(
                expected_revision=expected_revision, target_rite_id=target_rite_id,
            )

    if getattr(driver, "allow_private_active_scheme_sway_completion_termination_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_active_scheme_sway_completion_termination_private_v1(
            expected_revision: int, target_character_id: int, scheme_instance_id: int,
            after_sequence: int = 0,
        ) -> dict[str, object]:
            """Read native Sway termination records for the exact instance."""
            return driver.query_active_scheme_sway_completion_termination_private_v1(
                expected_revision=expected_revision, target_character_id=target_character_id,
                scheme_instance_id=scheme_instance_id, after_sequence=after_sequence,
            )

    if getattr(driver, "allow_private_player_religion_personal_parameters_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_player_religion_personal_parameters_v1(
            expected_revision: int,
        ) -> dict[str, object]:
            """Read the current player's native personal Tenet parameter observations."""
            return driver.query_player_religion_personal_parameters_private_v1(
                expected_revision=expected_revision,
            )

    if getattr(driver, "allow_private_active_scheme_sway_completion_invalidation_reason_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_active_scheme_sway_completion_invalidation_reason_private_v1(
            expected_revision: int, target_character_id: int, scheme_instance_id: int,
            after_sequence: int = 0,
        ) -> dict[str, object]:
            """Read native Sway invalidation notification inputs for the exact instance."""
            return driver.query_active_scheme_sway_completion_invalidation_reason_private_v1(
                expected_revision=expected_revision, target_character_id=target_character_id,
                scheme_instance_id=scheme_instance_id, after_sequence=after_sequence,
            )

    if getattr(driver, "allow_private_player_religion_draft_groups_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_player_religion_draft_groups_v1(
            expected_revision: int,
        ) -> dict[str, object]:
            """Read selected draft-group sources and current native Tenet gates."""
            return driver.query_player_religion_draft_groups_private_v1(
                expected_revision=expected_revision,
            )

    if getattr(driver, "allow_private_player_religion_draft_doctrine_choices_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_player_religion_draft_doctrine_choices_v1(
            expected_revision: int,
        ) -> dict[str, object]:
            """Read current draft Doctrine sources with their native final gates."""
            return driver.query_player_religion_draft_doctrine_choices_private_v1(
                expected_revision=expected_revision,
            )

    if getattr(driver, "allow_private_player_religion_draft_tenet_choices_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_player_religion_draft_tenet_choices_v1(
            expected_revision: int,
        ) -> dict[str, object]:
            """Read current draft Tenet sources with their native final gates."""
            return driver.query_player_religion_draft_tenet_choices_private_v1(
                expected_revision=expected_revision,
            )

    if getattr(driver, "allow_private_player_religion_draft_resource_costs_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_player_religion_draft_resource_costs_v1(
            expected_revision: int,
        ) -> dict[str, object]:
            """Read the native current draft base resource fee quote."""
            return driver.query_player_religion_draft_resource_costs_private_v1(
                expected_revision=expected_revision,
            )

    if getattr(driver, "allow_private_player_religion_ai_reform_inputs_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_player_religion_ai_reform_inputs_v1(
            expected_revision: int,
        ) -> dict[str, object]:
            """Read native reform AI inputs and retained controller schedules."""
            return driver.query_player_religion_ai_reform_inputs_private_v1(
                expected_revision=expected_revision,
            )

    if getattr(driver, "allow_private_faction_gift_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_faction_gift_candidate_private_v1(
            expected_revision: int,
            same_frame_root: dict[str, object],
            minimum_gold_reserve_raw: int = 10_000_000,
        ) -> dict[str, object]:
            """Read the native gift candidate against an observed same-frame root."""
            from .driver import PreSubmissionRevisionMismatchError

            snapshot = driver.take_internal_semantic_snapshot()
            if type(expected_revision) is not int or snapshot.get("revision") != expected_revision:
                raise PreSubmissionRevisionMismatchError(
                    "private faction gift query requires the current public revision"
                )
            return driver.query_faction_gift_private_candidate_v1(
                snapshot=snapshot,
                same_frame_root=same_frame_root,
                minimum_gold_reserve_raw=minimum_gold_reserve_raw,
            )

    if getattr(driver, "allow_private_faction_gift_action", False) is True:
        @server.tool()
        def ck3_send_faction_gift_private_v1(
            candidate: dict[str, object],
            checkpoint: dict[str, object],
            expected_revision: int,
        ) -> dict[str, object]:
            """Submit one observed native gift candidate through its existing ledger."""
            return driver.submit_faction_gift_private_v1(
                candidate=candidate, checkpoint=checkpoint,
                expected_revision=expected_revision,
            )

        @server.tool(annotations=read_only_tool)
        def ck3_query_faction_gift_receipt_private_v1(
            pending: dict[str, object], expected_revision: int,
        ) -> dict[str, object]:
            """Read the independent native result of the pending gift."""
            return driver.query_faction_gift_receipt_private_v1(
                pending=pending, expected_revision=expected_revision,
            )

        @server.tool(annotations=read_only_tool)
        def ck3_query_faction_gift_cold_recovery_private_v1(
            pending: dict[str, object], expected_revision: int,
        ) -> dict[str, object]:
            """Re-read the pending gift's material facts after an existing restore."""
            return driver.query_faction_gift_cold_recovery_private_v1(
                pending=pending, expected_revision=expected_revision,
            )

    if getattr(driver, "allow_private_activity_feast_stage5_start_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_activity_feast_stage5_start_inputs_private_v1(
            expected_revision: int,
        ) -> dict[str, object]:
            """Read Feast final Start legality, configured costs and guest inputs."""
            return driver.query_activity_feast_stage5_start_inputs_private_v1(
                expected_revision=expected_revision,
            )

        @server.tool(annotations=read_only_tool)
        def ck3_query_activity_feast_hosted_post_private_v1(
            expected_revision: int,
        ) -> dict[str, object]:
            """Read hosted Feast identity and native completed or invalidated flags."""
            return driver.query_activity_feast_hosted_post_private_v1(
                expected_revision=expected_revision,
            )

    if getattr(driver, "allow_private_activity_stage5_feast_full_cost_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_activity_stage5_feast_full_cost_private_v1(
            expected_revision: int,
        ) -> dict[str, object]:
            """Read every native Feast resource cost on the current paused frame."""
            return driver.query_activity_stage5_feast_full_cost_private_v1(
                expected_revision=expected_revision,
            )

    if getattr(driver, "allow_private_activity_feast_guest_candidate_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_activity_feast_guest_candidate_private_v1(
            expected_revision: int,
        ) -> dict[str, object]:
            """Read native guest candidate IDs and join or arrival observations."""
            return driver.query_activity_feast_guest_candidate_private_v1(
                expected_revision=expected_revision,
            )

    if getattr(driver, "allow_private_activity_feast_guest_opinion_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_activity_feast_guest_opinion_private_v1(
            expected_revision: int, guest_character_id: int,
            activity_id: int | None = None,
        ) -> dict[str, object]:
            """Read guest opinion and reward modifiers, optionally for a full activity ID."""
            return query_activity_feast_guest_opinion_private_v1(
                driver, expected_revision=expected_revision,
                guest_character_id=guest_character_id,
                activity_id=activity_id,
            )

    if getattr(driver, "allow_private_activity_feast_guest_route_proof_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_activity_feast_guest_route_proof_private_v1(
            expected_revision: int,
        ) -> dict[str, object]:
            """Read selected guests, a pre-invitation candidate and native Start legality."""
            return query_activity_feast_guest_route_proof_private_v1(
                driver, expected_revision=expected_revision,
            )

    if getattr(driver, "allow_private_activity_feast_guest_rule_provenance_query", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_activity_feast_guest_rule_provenance_private_v1(
            expected_revision: int, authored_rule_key: str,
            candidate_character_id: int,
        ) -> dict[str, object]:
            """Read one candidate's membership in a named active Feast invitation rule."""
            return query_activity_feast_guest_rule_provenance_private_v1(
                driver, expected_revision=expected_revision,
                authored_rule_key=authored_rule_key,
                candidate_character_id=candidate_character_id,
            )

    @server.tool(annotations=read_only_tool)
    def ck3_get_bridge_diagnostics() -> dict[str, object]:
        """Return live transport diagnostics without claiming CK3 game state."""
        return service.bridge_diagnostics()

    @server.tool(annotations=read_only_tool)
    def ck3_inspect_save_artifacts_v1() -> dict[str, object]:
        """Inspect saves below the server-bound isolated profile; no path input."""
        if artifact_inspector is None:
            raise RuntimeError(
                "save artifact inspection requires a server-configured profile"
            )
        return artifact_inspector.inspect_save_artifacts_v1()

    @server.tool(annotations=read_only_tool)
    def ck3_query_engine_diagnostics_v1(
        fingerprint_limit: int = 50,
        tail_limit: int = 25,
    ) -> dict[str, object]:
        """Read bounded fixed logs/crashes below the server-bound profile."""
        if runtime_diagnostics is None:
            raise RuntimeError(
                "engine diagnostics require a server-configured profile"
            )
        return runtime_diagnostics.query_engine_diagnostics_v1(
            fingerprint_limit=fingerprint_limit,
            tail_limit=tail_limit,
        )

    @server.tool(annotations=read_only_tool)
    def ck3_query_engine_log_literals_v1(
        log_name: str,
        literals: list[str],
        sample_limit: int = 3,
    ) -> dict[str, object]:
        """Count exact phrases in one fixed log below the server-bound profile."""
        if runtime_diagnostics is None:
            raise RuntimeError(
                "engine log inspection requires a server-configured profile"
            )
        return runtime_diagnostics.query_engine_log_literals_v1(
            log_name=log_name,
            literals=literals,
            sample_limit=sample_limit,
        )

    @server.tool(annotations=read_only_tool)
    def ck3_query_current_battle_knight_v1(
        subject_public_cunit_id: PublicCUnitId,
        character_id: int,
        regiment_id: int,
        expected_played_character_id: int,
        expected_war_id: int,
        expected_native_carmy_id: int,
        expected_combat_id: int,
        expected_province_id: int,
        expected_date_raw: int,
        expected_revision: int,
        expected_native_revision: int,
        expected_snapshot_id: str,
    ) -> dict[str, object]:
        """Read one paired knight/regiment's current battle stats while paused."""
        return _ck3_query_current_battle_knight_v1(
            service,
            subject_public_cunit_id,
            character_id,
            regiment_id,
            expected_played_character_id,
            expected_war_id,
            expected_native_carmy_id,
            expected_combat_id,
            expected_province_id,
            expected_date_raw,
            expected_revision,
            expected_native_revision,
            expected_snapshot_id,
        )

    @server.tool()
    def ck3_take_snapshot(
        include_native_command_history: bool = False,
    ) -> dict[str, object]:
        """Return the session snapshot; opt in to the full native transcript."""
        return service.snapshot(
            include_native_command_history=include_native_command_history,
        )

    semantic_snapshot = getattr(driver, "take_internal_semantic_snapshot", None)
    if (getattr(driver, "allow_private_semantic_snapshot_readonly", False) is True
            and callable(semantic_snapshot)):
        @server.tool(annotations=read_only_tool)
        def ck3_take_semantic_snapshot_private_v1() -> dict[str, object]:
            """Read one native semantic frame without the command transcript."""
            frame = semantic_snapshot()
            if (not isinstance(frame, dict)
                    or any(key in frame for key in (
                        "native_command_history", "native_rollback_war_failure",
                        "native_rollback_war_failures",
                    ))):
                raise RuntimeError(
                    "native semantic snapshot must exclude driver transcript fields"
                )
            # MCP emits both pretty text and structured content. Keep the one
            # line stdio response well below the full campaign transcript.
            if len(json.dumps(frame, ensure_ascii=False).encode("utf-8")) > 8 * 1024 * 1024:
                raise RuntimeError("native semantic snapshot exceeds the 8 MiB read bound")
            return frame

    if getattr(driver, "allow_private_death_succession_modal_continue", False) is True:
        @server.tool(annotations=read_only_tool)
        def ck3_query_current_timeline_blocker_context_v1(
            expected_revision: int,
        ) -> dict[str, object]:
            """Read the current native succession blocker on this paused frame."""
            return _ck3_query_current_timeline_blocker_context_v1(service, expected_revision)

        @server.tool()
        def ck3_continue_death_succession_modal_v1(
            expected_revision: int,
            expected_played_character_id: int,
            expected_episode_run_id: str,
        ) -> dict[str, object]:
            """Close once, observe material clearance, and prove successor time advance."""
            return _ck3_continue_death_succession_modal_v1(
                service, expected_revision, expected_played_character_id, expected_episode_run_id,
            )

    @server.tool()
    def ck3_get_one_life_settlement() -> dict[str, object]:
        """Inspect the current death settlement and its episode binding."""
        return service.one_life_settlement()

    @server.tool()
    def ck3_settle_one_life(
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Finish this life only after its score and new record are durable."""
        return service.settle_one_life(expected_revision=expected_revision)

    @server.tool()
    def ck3_plan_turn() -> dict[str, object]:
        """Choose the next one-life gameplay step from the shared planner."""
        return service.plan_nonwar_turn() if getattr(driver, "nonwar_only", False) is True else service.plan_turn()

    @server.tool()
    def ck3_auto_turn() -> dict[str, object]:
        """Plan and execute exactly one supported one-life gameplay turn."""
        return service.auto_nonwar_turn() if getattr(driver, "nonwar_only", False) is True else service.auto_turn()

    @server.tool()
    def ck3_execute_step(
        step: str, expected_revision: int | None = None,
        expected_h2743_frame: dict[str, object] | None = None,
    ) -> dict[str, object]:
        """Execute one semantic gameplay step through the selected backend."""
        payload = service.execute_step(
            step, expected_revision=expected_revision,
            expected_h2743_frame=expected_h2743_frame,
        )
        if step == "query-army-strengths-v1":
            return build_army_strengths_mcp_result(payload)
        return payload

    @server.tool()
    def ck3_save_checkpoint(
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Create and materialize the fixed isolated CK3 checkpoint save."""
        return service.save_checkpoint(expected_revision=expected_revision)

    @server.tool()
    def ck3_restore_checkpoint(
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Restart the pure-native CK3 session and continue its checkpoint."""
        return service.restore_checkpoint(expected_revision=expected_revision)

    @server.tool()
    def ck3_start_next_episode(
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Start a new one-life run from the immutable native seed save."""
        return service.start_next_episode(expected_revision=expected_revision)

    @server.tool()
    def ck3_reply_pending_character_interaction(
        accept: bool,
        interaction_instance_id: int | None = None,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Accept or reject the current native character interaction."""
        return service.reply_pending_character_interaction(
            accept=accept,
            interaction_instance_id=interaction_instance_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_acknowledge_pending_character_interaction(
        interaction_instance_id: int,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Acknowledge one exact native auto-accept interaction notification."""
        return service.acknowledge_pending_character_interaction(
            interaction_instance_id=interaction_instance_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_get_war_state() -> dict[str, object]:
        """Return active native wars and the player's currently raised armies."""
        return service.war_state()

    @server.tool()
    def ck3_query_arrange_marriage_choices(
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Enumerate native marriage choices for the current player character."""
        return service.query_arrange_marriage_choices(
            expected_revision=expected_revision
        )

    @server.tool()
    def ck3_arrange_marriage(
        choice_id: str,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Submit one exact choice from ck3_query_arrange_marriage_choices."""
        return service.arrange_marriage(
            choice_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_query_declarable_wars(
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Enumerate CK3's currently valid native war declarations."""
        return service.query_declarable_wars(
            expected_revision=expected_revision
        )

    @server.tool()
    def ck3_collect_declarable_wars_result_v1(
        request_id: str,
        expected_revision: int,
    ) -> dict[str, object]:
        """Collect one retained request without resubmitting native enumeration."""
        return service.collect_declarable_wars_result_v1(
            request_id, expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_declare_war(
        declaration_id: str,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Declare one exact choice returned by ck3_query_declarable_wars."""
        return service.declare_war(
            declaration_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_raise_troops_default(
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Raise troops at CK3's native default rally point."""
        return service.raise_troops_default(
            expected_revision=expected_revision
        )

    @server.tool()
    def ck3_move_army(
        army_id: PublicCUnitId,
        target_province_id: int,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Move one native player army to an exact CK3 province."""
        return service.move_army(
            army_id,
            target_province_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_start_assault(
        siege_id: int,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Start Assault for one exact full-generation native SiegeID."""
        return service.start_assault(
            siege_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_stop_assault(
        siege_id: int,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Stop Assault for one exact full-generation native SiegeID."""
        return service.stop_assault(
            siege_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_disband_army(
        army_id: PublicCUnitId,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Disband one exact native player army."""
        return service.disband_army(
            army_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_enforce_demands(
        war_id: int,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Enforce demands in an exact native war that reached 100%."""
        return service.enforce_demands(
            war_id,
            expected_revision=expected_revision,
        )

    @server.tool(annotations=read_only_tool)
    def ck3_query_player_default_raise_v1(
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Read the player's final native default raise legality, including during war."""
        return service.query_player_default_raise_v1(expected_revision=expected_revision)

    @server.tool()
    def ck3_hire_mercenary_v1(
        company_id: int, expected_revision: int,
    ) -> dict[str, object]:
        """Submit one normal mercenary hire; native ACK awaits independent after-state."""
        return service.hire_mercenary_v1(
            company_id=company_id, expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_hire_holy_order_v1(
        holy_order_id: int, expected_revision: int,
    ) -> dict[str, object]:
        """Submit one normal holy-order hire; native ACK awaits independent after-state."""
        return service.hire_holy_order_v1(
            holy_order_id=holy_order_id, expected_revision=expected_revision,
        )

    @server.tool(annotations=read_only_tool)
    def ck3_query_player_mercenary_context_v1(
        expected_revision: int,
    ) -> dict[str, object]:
        """Read the player's native mercenary candidates, hire terms, prices and arrival location."""
        return service.query_player_mercenary_context_v1(expected_revision=expected_revision)

    @server.tool(annotations=read_only_tool)
    def ck3_query_army_commander_candidates_v1(
        army_id: PublicCUnitId,
        expected_revision: int | None = None,
        target_province_id: Annotated[int, Field(strict=True, ge=1, le=2**31 - 1)] | None = None,
    ) -> dict[str, object]:
        """Read native manual candidates and optional current target dice endpoints."""
        return service.query_army_commander_candidates_v1(
            army_id,
            expected_revision=expected_revision,
            target_province_id=target_province_id,
        )

    @server.tool()
    def ck3_assign_army_commander_v1(
        army_id: PublicCUnitId,
        commander_character_id: Annotated[int, Field(strict=True, ge=0, le=2**31 - 1)],
        expected_revision: IngameUiRevisionV1,
    ) -> dict[str, object]:
        """Assign a native commander and independently read back the army context."""
        return service.assign_army_commander_v1(
            army_id,
            commander_character_id,
            expected_revision=expected_revision,
        )

    def ck3_query_army_strengths(
        army_ids: list[PublicCUnitId],
        expected_revision: int | None = None,
        ordered_refill_entry_mode: Literal["observed_prepared", "fixed_chunk0_prepare"] = "observed_prepared",
        ordered_besieging_entry_mode: Literal["observed_prepared", "fixed_chunk0_prepare"] = "observed_prepared",
    ) -> Annotated[CallToolResult, dict[str, object]]:
        """Read soldiers and AI base power; never interpret them as win odds.

        Choose the observed or conditional preparation entry for scoped refill.
        The separate B entry uses the actual refreshed target physical union.
        """
        payload = service.query_army_strengths(
            army_ids,
            expected_revision=expected_revision,
            ordered_refill_entry_mode=ordered_refill_entry_mode,
            ordered_besieging_entry_mode=ordered_besieging_entry_mode,
        )
        return build_army_strengths_mcp_result(payload)

    # SDK resolves future annotations against module globals; use the lazy SDK type.
    ck3_query_army_strengths.__annotations__["return"] = Annotated[
        CallToolResult, dict[str, object]
    ]
    server.tool()(ck3_query_army_strengths)

    @server.tool(annotations=read_only_tool)
    def ck3_query_projected_contact_scope_v1(
        subject_army_id: PublicCUnitId,
        target_province_id: Annotated[int, Field(strict=True, ge=1, le=2**31 - 1)],
        incoming_entry_province_id: Annotated[int, Field(strict=True, ge=1, le=2**31 - 1)],
        expected_revision: IngameUiRevisionV1,
    ) -> dict[str, object]:
        """Project arrival against current target state; no move or future battle claim."""
        return _ck3_query_projected_contact_scope_v1(
            service, subject_army_id, target_province_id, incoming_entry_province_id,
            expected_revision,
        )

    @server.tool()
    def ck3_query_actual_contact_scope(
        subject_army_id: PublicCUnitId,
        target_province_id: int,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Predict contact or read actual CombatID/sides; pass order to v3."""
        return _ck3_query_actual_contact_scope(
            service,
            subject_army_id,
            target_province_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_query_battle_control_snapshot_v1(
        subject_army_id: PublicCUnitId,
        expected_revision: int,
    ) -> dict[str, object]:
        """Read one full public CUnitID's battle and retreat gates while paused."""
        return _ck3_query_battle_control_snapshot_v1(
            service,
            subject_army_id,
            expected_revision,
        )

    @server.tool()
    def ck3_query_battle_transition_v1(
        combat_id: int,
        expected_revision: int,
    ) -> dict[str, object]:
        """Read lifecycle and optional actual strength, losses, width and advantage."""
        return _ck3_query_battle_transition_v1(
            service,
            combat_id,
            expected_revision,
        )

    @server.tool()
    def ck3_query_battle_terminal_transition_v1(
        prior_combat_id: int | None,
        subject_public_cunit_id: PublicCUnitId | None,
        expected_revision: int,
        after_terminal_sequence: int | None = None,
        character_ids: list[int] | None = None,
    ) -> dict[str, object]:
        """Read terminal history and requested current characters; null IDs omit battle context."""
        return _ck3_query_battle_terminal_transition_v1(
            service,
            prior_combat_id,
            subject_public_cunit_id,
            expected_revision,
            after_terminal_sequence,
            character_ids,
        )

    @server.tool()
    def ck3_query_battle_reinforcement_assignment_v1(
        selected_public_cunit_id: PublicCUnitId,
        expected_revision: int,
    ) -> dict[str, object]:
        """Read native help flags, target, exact route/ETA and contact candidates."""
        return _ck3_query_battle_reinforcement_assignment_v1(
            service,
            selected_public_cunit_id,
            expected_revision,
        )

    @server.tool()
    def ck3_query_campaign_root_context_v1(
        expected_revision: int,
    ) -> dict[str, object]:
        """Read player, title, capital, lieges, government and rule tokens."""
        return _ck3_query_campaign_root_context_v1(
            service,
            expected_revision,
        )

    @server.tool()
    def ck3_query_council_composition_candidates_v1(
        expected_snapshot_id: str,
        public_revision: int,
        native_revision: int,
        date_raw: int,
        owner_character_id: int,
        position_key: str = "councillor_steward",
    ) -> dict[str, object]:
        """Read native steward candidates bound to one exact paused frame."""

        return _ck3_query_council_composition_candidates_v1(
            service,
            expected_snapshot_id,
            public_revision,
            native_revision,
            date_raw,
            owner_character_id,
            position_key,
        )

    @server.tool()
    def ck3_query_steward_develop_county_candidates_v1(
        expected_revision: int,
    ) -> dict[str, object]:
        """Read native Develop County task/location legality and current growth."""
        return _ck3_query_steward_develop_county_candidates_v1(
            service,
            expected_revision,
        )

    @server.tool()
    def ck3_change_steward_develop_county_task_v1(
        councillor_character_id: int,
        target_county_title_id: int,
        expected_revision: int,
        replace_existing_task: bool,
        task_key: str = "task_develop_county",
    ) -> dict[str, object]:
        """Submit Develop County; verify the result in a later paused frame."""

        return _ck3_change_steward_develop_county_task_v1(
            service,
            councillor_character_id,
            target_county_title_id,
            expected_revision,
            replace_existing_task,
            task_key,
        )

    @server.tool(annotations=read_only_tool)
    def ck3_query_player_faction_alerts_v1(
        expected_revision: int,
    ) -> dict[str, object]:
        """Read native player-faction alert rows and planner projection."""
        return _ck3_query_player_faction_alerts_v1(
            service,
            expected_revision,
        )

    @server.tool()
    def ck3_search_entities_v1(
        expected_revision: int,
        relation_filter: str = "any",
        after_character_id: int | None = None,
        limit: int = 50,
    ) -> dict[str, object]:
        """Find self, direct vassal or adjacent-holder CharacterIDs."""
        return _ck3_search_entities_v1(
            service,
            expected_revision,
            relation_filter,
            after_character_id,
            limit,
        )

    @server.tool()
    def ck3_query_turn_bundle_v1(
        expected_revision: int,
    ) -> dict[str, object]:
        """Read one same-frame planner bundle with typed local readiness."""
        return _ck3_query_turn_bundle_v1(
            service,
            expected_revision,
        )

    @server.tool()
    def ck3_query_zhongguo_case_snapshot_v1(
        case_kind: str,
        request_nonce: str,
        expected_revision: int,
        subject_character_id: int | None = None,
        owner_character_id: int | None = None,
    ) -> dict[str, object]:
        """Read one allowlisted case, receipt, and persisted deadline frame."""
        return _ck3_query_zhongguo_case_snapshot_v1(
            service,
            case_kind,
            request_nonce,
            expected_revision,
            subject_character_id,
            owner_character_id,
        )

    @server.tool()
    def ck3_query_zhongguo_b1_cycle_snapshot_v1(
        request_nonce: str,
        expected_revision: int,
    ) -> dict[str, object]:
        """Read the played manager's B1 cycle, roster, quota and closure."""
        return _ck3_query_zhongguo_b1_cycle_snapshot_v1(
            service,
            request_nonce,
            expected_revision,
        )

    @server.tool()
    def ck3_query_zhongguo_ai_owned_case_snapshot_v1(
        owner_character_id: int,
        subject_character_id: int,
        request_nonce: str,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Read one AI manager's eligibility, case, stage, route and receipt."""
        return _ck3_query_zhongguo_ai_owned_case_snapshot_v1(
            service,
            owner_character_id,
            subject_character_id,
            request_nonce,
            expected_revision,
        )

    @server.tool()
    def ck3_query_zhongguo_result_case_snapshot_v1(
        request_nonce: str,
        expected_revision: int,
        owner_character_id: int,
    ) -> dict[str, object]:
        """Read the player's received result; owner is an equality filter."""
        return _ck3_query_zhongguo_result_case_snapshot_v1(
            service,
            request_nonce,
            expected_revision,
            owner_character_id,
        )

    @server.tool()
    def ck3_query_zhongguo_b2_pip_snapshot_v1(
        request_nonce: str,
        expected_revision: int,
        owner_character_id: int,
    ) -> dict[str, object]:
        """Read the player's fixed-allowlist B2 PIP projection."""
        return _ck3_query_zhongguo_b2_pip_snapshot_v1(
            service,
            request_nonce,
            expected_revision,
            owner_character_id,
        )

    @server.tool()
    def ck3_query_zhongguo_promotion_compensation_postcondition_v1(
        request_nonce: str,
        expected_revision: int,
    ) -> dict[str, object]:
        """Read one correlated promotion/compensation business receipt."""
        return _ck3_query_zhongguo_promotion_compensation_postcondition_v1(
            service,
            request_nonce,
            expected_revision,
        )

    @server.tool()
    def ck3_query_zhongguo_compensation_af5_snapshot_v1(
        request_nonce: str,
        expected_revision: int,
    ) -> dict[str, object]:
        """Read one correlated compensation AF5 business receipt."""
        return _ck3_query_zhongguo_compensation_af5_snapshot_v1(
            service,
            request_nonce,
            expected_revision,
        )

    @server.tool()
    def ck3_query_zhongguo_workforce_owner_snapshot_v1(
        request_nonce: str,
        expected_revision: int,
    ) -> dict[str, object]:
        """Read one correlated Workforce owner business receipt."""
        return _ck3_query_zhongguo_workforce_owner_snapshot_v1(
            service,
            request_nonce,
            expected_revision,
        )

    @server.tool()
    def ck3_query_zhongguo_projects_metrics_postcondition_v1(
        request_nonce: str,
        expected_revision: int,
        owner_character_id: int,
        subject_character_id: int | None = None,
    ) -> dict[str, object]:
        """Read one correlated contribution-to-metrics business receipt."""
        return _ck3_query_zhongguo_projects_metrics_postcondition_v1(
            service,
            request_nonce,
            expected_revision,
            owner_character_id,
            subject_character_id,
        )

    @server.tool()
    def ck3_query_zhongguo_career_hc_workforce_postcondition_v1(
        request_nonce: str,
        expected_revision: int,
        owner_character_id: int,
    ) -> dict[str, object]:
        """Read the route-B receipt and fixed six-bucket career-HC ledger."""
        return _ck3_query_zhongguo_career_hc_workforce_postcondition_v1(
            service,
            request_nonce,
            expected_revision,
            owner_character_id,
        )

    @server.tool()
    def ck3_query_zhongguo_workforce_collective_snapshot_v1(
        request_nonce: str,
        expected_revision: int,
        owner_character_id: int,
    ) -> dict[str, object]:
        """Read the player's Workforce collective and rolling-three ledger."""
        return _ck3_query_zhongguo_workforce_collective_snapshot_v1(
            service,
            request_nonce,
            expected_revision,
            owner_character_id,
        )

    @server.tool()
    def ck3_query_zhongguo_workforce_normal_exit_snapshot_v1(
        request_nonce: str,
        expected_revision: int,
        owner_character_id: int,
    ) -> dict[str, object]:
        """Read the player's fixed-allowlist normal-exit/HC lifecycle."""
        return _ck3_query_zhongguo_workforce_normal_exit_snapshot_v1(
            service,
            request_nonce,
            expected_revision,
            owner_character_id,
        )

    @server.tool()
    def ck3_query_zhongguo_incident_snapshot_v1(
        request_nonce: str,
        expected_revision: int,
        owner_character_id: int,
        profile: str,
    ) -> dict[str, object]:
        """Read the player's fixed-allowlist X/Y/Z incident projection."""
        return _ck3_query_zhongguo_incident_snapshot_v1(
            service,
            request_nonce,
            expected_revision,
            owner_character_id,
            profile,
        )

    @server.tool()
    def ck3_query_zhongguo_manager_governance_snapshot_v1(
        request_nonce: str,
        expected_revision: int,
        subject_character_id: int,
        owner_character_id: int,
    ) -> dict[str, object]:
        """Read the fixed-allowlist manager-governance lifecycle."""
        return _ck3_query_zhongguo_manager_governance_snapshot_v1(
            service,
            request_nonce,
            expected_revision,
            subject_character_id,
            owner_character_id,
        )

    @server.tool()
    def ck3_query_zhongguo_manager_subordinate_selector_v1(
        request_nonce: str,
        expected_revision: int,
    ) -> dict[str, object]:
        """Select an observed AI direct manager and direct subordinate."""
        return _ck3_query_zhongguo_manager_subordinate_selector_v1(
            service,
            request_nonce,
            expected_revision,
        )

    @server.tool()
    def ck3_query_zhongguo_scoreboard_state_v1(
        request_nonce: str,
        expected_revision: int,
    ) -> dict[str, object]:
        """Read fixed named scoreboard state and current-player frozen ACL."""
        return _ck3_query_zhongguo_scoreboard_state_v1(
            service,
            request_nonce,
            expected_revision,
        )

    @server.tool()
    def ck3_activate_zhongguo_scoreboard_v1(
        request_nonce: str,
        action: str,
        expected_revision: int,
        expected_native_revision: int,
        expected_connection_generation: int,
        expected_player_character_id: int,
        expected_provider_session_id: str,
        expected_observation_sequence: int,
        expected_observed_state_revision: int,
        expected_tree_fingerprint_v1: str,
        expected_semantic_fingerprint_v1: str,
        expected_window_instance_pointer: str,
        expected_target_instance_pointer: str,
        expected_target_vtable_pointer: str,
    ) -> dict[str, object]:
        """Use the fail-closed scoreboard transport; never imply GUI PASS."""
        return _ck3_activate_zhongguo_scoreboard_v1(
            service,
            request_nonce,
            action,
            expected_revision,
            expected_native_revision,
            expected_connection_generation,
            expected_player_character_id,
            expected_provider_session_id,
            expected_observation_sequence,
            expected_observed_state_revision,
            expected_tree_fingerprint_v1,
            expected_semantic_fingerprint_v1,
            expected_window_instance_pointer,
            expected_target_instance_pointer,
            expected_target_vtable_pointer,
        )

    @server.tool()
    def ck3_open_character_window_v1(character_id: IngameUiHandleV1, expected_revision: IngameUiRevisionV1) -> dict[str, object]:
        """Open an exact CharacterID; ACK requires independent window readback."""
        return service.open_character_window_v1(character_id, expected_revision=expected_revision)

    @server.tool()
    def ck3_select_army_ui_v1(subject_army_id: PublicCUnitId, expected_revision: IngameUiRevisionV1) -> dict[str, object]:
        """Select a played army's public CUnitID through vanilla presentation routing."""
        return service.select_army_ui_v1(subject_army_id, expected_revision=expected_revision)

    @server.tool()
    def ck3_hover_army_tooltip_v1(subject_army_id: PublicCUnitId, tooltip_kind: Literal["supply_state", "attrition"], expected_revision: IngameUiRevisionV1) -> dict[str, object]:
        """Native Army tooltip enter on exact 1.20.0.3; ACK remains pending GUI and rendered verification."""
        return service.hover_army_tooltip_v1(subject_army_id, tooltip_kind, expected_revision=expected_revision)

    @server.tool()
    def ck3_leave_army_tooltip_v1(subject_army_id: PublicCUnitId, tooltip_kind: Literal["supply_state", "attrition"], action_receipt: ArmyTooltipReceiptV1, expected_revision: IngameUiRevisionV1) -> dict[str, object]:
        """Native Army tooltip leave with a bound receipt; use its new receipt for later query."""
        return service.leave_army_tooltip_v1(subject_army_id, tooltip_kind, action_receipt, expected_revision=expected_revision)

    @server.tool()
    def ck3_query_army_tooltip_v1(subject_army_id: PublicCUnitId, tooltip_kind: Literal["supply_state", "attrition"], action_receipt: ArmyTooltipReceiptV1, expected_revision: IngameUiRevisionV1) -> dict[str, object]:
        """Read actual native cache bytes for a bound Army tooltip receipt; freshness and pixels remain unverified."""
        return service.query_army_tooltip_v1(subject_army_id, tooltip_kind, action_receipt, expected_revision=expected_revision)

    @server.tool()
    def ck3_open_combat_window_v1(combat_id: IngameUiHandleV1, expected_revision: IngameUiRevisionV1) -> dict[str, object]:
        """Open an exact CombatID scoped to the played army; verify separately."""
        return service.open_combat_window_v1(combat_id, expected_revision=expected_revision)

    @server.tool()
    def ck3_fit_combat_window_v1(combat_id: IngameUiHandleV1, expected_revision: IngameUiRevisionV1) -> dict[str, object]:
        """Fit the current original battle window using native viewport/layout bounds; verify pixels separately."""
        return service.fit_combat_window_v1(combat_id, expected_revision=expected_revision)

    @server.tool()
    def ck3_open_knights_window_v1(expected_revision: IngameUiRevisionV1) -> dict[str, object]:
        """Open played actor's military-eligible KnightsView, not active combat roster."""
        return service.open_knights_window_v1(expected_revision=expected_revision)

    @server.tool()
    def ck3_query_ingame_ui_window_v1(window_kind: Literal["character", "army", "combat", "knights"], expected_revision: IngameUiRevisionV1) -> dict[str, object]:
        """Fresh owner-thread full-ID window readback plus bounded target subtree."""
        return service.query_ingame_ui_window_v1(window_kind, expected_revision=expected_revision)

    @server.tool()
    def ck3_hover_combat_knights_v1(combat_id: IngameUiHandleV1, ui_side: Literal["left", "right"], expected_revision: IngameUiRevisionV1) -> dict[str, object]:
        """Native enter/leave of fixed knight-count text; verify hover and original pixels independently."""
        return service.hover_combat_knights_v1(combat_id, ui_side, expected_revision=expected_revision)

    @server.tool()
    def ck3_center_map_on_landed_title_v1(
        title_key: str,
        expected_revision: int,
    ) -> dict[str, object]:
        """Center the map on one canonical title key through native readback."""
        return _ck3_center_map_on_landed_title_v1(
            service,
            title_key,
            expected_revision,
        )

    @server.tool()
    def ck3_set_played_character_v1(
        character_id: int,
        expected_revision: int,
    ) -> dict[str, object]:
        """Switch the local player to any valid living CK3 character ID."""
        return _ck3_set_played_character_v1(
            service,
            character_id,
            expected_revision,
        )

    @server.tool()
    def ck3_begin_coat_of_arms_source_upload_v2(
        total_bytes: int,
        source_sha256: str,
        chunk_count: int,
        chunk_encoding: str,
        expected_revision: int,
        apply: bool,
        expected_game_version: str,
        expected_executable_sha256: str,
    ) -> dict[str, object]:
        """Begin bounded chunked transfer of a large CK3 coat-of-arms source."""
        return _ck3_begin_coat_of_arms_source_upload_v2(
            service,
            total_bytes,
            source_sha256,
            chunk_count,
            chunk_encoding,
            expected_revision,
            apply,
            expected_game_version,
            expected_executable_sha256,
        )

    @server.tool()
    def ck3_append_coat_of_arms_source_chunk_v2(
        upload_id: str,
        generation: int,
        chunk_index: int,
        chunk_count: int,
        chunk_encoding: str,
        chunk_bytes: int,
        chunk_sha256: str,
        chunk_base64: str,
        source_sha256: str,
        expected_revision: int,
        apply: bool,
        expected_game_version: str,
        expected_executable_sha256: str,
    ) -> dict[str, object]:
        """Append a strictly ordered and independently hashed source chunk."""
        return _ck3_append_coat_of_arms_source_chunk_v2(
            service,
            upload_id,
            generation,
            chunk_index,
            chunk_count,
            chunk_encoding,
            chunk_bytes,
            chunk_sha256,
            chunk_base64,
            source_sha256,
            expected_revision,
            apply,
            expected_game_version,
            expected_executable_sha256,
        )

    @server.tool()
    def ck3_commit_coat_of_arms_source_upload_v2(
        upload_id: str,
        generation: int,
        chunk_count: int,
        source_sha256: str,
        expected_revision: int,
        apply: bool,
        expected_game_version: str,
        expected_executable_sha256: str,
    ) -> dict[str, object]:
        """Verify a complete upload and apply it through one native call."""
        return _ck3_commit_coat_of_arms_source_upload_v2(
            service,
            upload_id,
            generation,
            chunk_count,
            source_sha256,
            expected_revision,
            apply,
            expected_game_version,
            expected_executable_sha256,
        )

    @server.tool()
    def ck3_abort_coat_of_arms_source_upload_v2(
        upload_id: str,
        generation: int,
    ) -> dict[str, object]:
        """Abort an upload without changing the CK3 designer."""
        return _ck3_abort_coat_of_arms_source_upload_v2(
            service,
            upload_id,
            generation,
        )

    @server.tool()
    def ck3_probe_coat_of_arms_source_v1(
        source: str,
        expected_revision: int,
        apply: bool,
    ) -> dict[str, object]:
        """Probe UTF-8 coat-of-arms source through CK3's native engine path."""
        return _ck3_probe_coat_of_arms_source_v1(
            service,
            source,
            expected_revision,
            apply,
        )

    @server.tool()
    def ck3_export_coat_of_arms_source_v1(
        expected_revision: int,
    ) -> dict[str, object]:
        """Return CK3's canonical source for the active designer coat of arms."""
        return _ck3_export_coat_of_arms_source_v1(
            service,
            expected_revision,
        )

    @server.tool()
    def ck3_query_frontend_applied_game_rules_v1() -> dict[str, object]:
        """Read actual CGameRuleInstance choices, independently of the GUI model."""
        return service.query_frontend_applied_game_rules_v1()

    @server.tool()
    def ck3_query_frontend_game_rules_window_v1() -> dict[str, object]:
        """Read actual rule window visibility and stock edit eligibility."""
        return service.query_frontend_game_rules_window_v1()

    @server.tool()
    def ck3_select_frontend_game_rule_v1(rule_key: str,
            expected_current_setting_key: str, desired_setting_key: str) -> dict[str, object]:
        """Select an actual rule option with bounded stock Next and native readback."""
        return service.select_frontend_game_rule_v1(
            rule_key, expected_current_setting_key, desired_setting_key)

    @server.tool()
    def ck3_apply_and_hide_frontend_game_rules_v1() -> dict[str, object]:
        """Invoke stock Apply then Hide and independently observe window closure."""
        return service.apply_and_hide_frontend_game_rules_v1()

    @server.tool()
    def ck3_hide_frontend_game_rules_v1() -> dict[str, object]:
        """Invoke stock Hide and independently observe window closure."""
        return service.hide_frontend_game_rules_v1()

    @server.tool()
    def ck3_query_frontend_game_rule_selections_v1() -> dict[str, object]:
        """Read actual native rules-window choices; excludes Apply verification."""
        return service.query_frontend_game_rule_selections_v1()

    @server.tool()
    def ck3_activate_frontend_game_rules_v1() -> dict[str, object]:
        """Open vanilla Bookmarks game rules and verify native selected objects."""
        return service.activate_frontend_game_rules_v1()

    @server.tool()
    def ck3_query_frontend_gui_route_v1() -> dict[str, object]:
        """Read CK3's current native frontend route; no OCR or input."""
        return _ck3_query_frontend_gui_route_v1(service)

    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False))
    def ck3_select_ingame_decision_item_v1(decision_key: str, expected_revision: int | None = None) -> dict[str, object]:
        """Invoke source OnSelect once on the unique actual .3 row, then read selected detail identity."""
        return service.select_ingame_decision_item_v1(decision_key, expected_revision=expected_revision)

    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False))
    def ck3_confirm_ingame_decision_item_v1(decision_key: str, expected_window_kind: Literal["vivhite_courtier"], expected_revision: int | None = None) -> dict[str, object]:
        """Invoke the selected detail's fixed Confirm once and independently read the actual inner modal."""
        return service.confirm_ingame_decision_item_v1(decision_key, expected_window_kind, expected_revision=expected_revision)

    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False))
    def ck3_confirm_ingame_decision_outcome_v1(
        decision_key: str, expected_outcome: Literal["event_window", "decision_closed"],
        expected_revision: int, expected_event_definition_key: str | None = None,
    ) -> dict[str, object]:
        """Confirm the actual selected player decision once and read its declared UI outcome; business acceptance remains separate."""
        return service.confirm_ingame_decision_outcome_v1(
            decision_key, expected_outcome, expected_revision=expected_revision,
            expected_event_definition_key=expected_event_definition_key)

    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False))
    def ck3_click_white_numeric_control_v1(control: Literal["diplomacy_plus_1", "martial_plus_1", "stewardship_plus_1", "intrigue_plus_1", "learning_plus_1", "prowess_plus_1"], expected_before_value: int, expected_before_price_text: str, intent_id: str, expected_revision: IngameUiRevisionV1 | None = None) -> dict[str, object]:
        """One fixed skill+1 callback, separate actual business/text after, actual price values only."""
        return service.click_white_numeric_control_v1(control, expected_before_value, expected_before_price_text, intent_id, expected_revision=expected_revision)

    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False))
    def ck3_click_white_control_v1(control: Literal["age_plus_1"], expected_before_age: int, intent_id: str, expected_revision: IngameUiRevisionV1 | None = None) -> dict[str, object]:
        """Invoke fixed age+1 once per durable intent, then separately read actual business/text after."""
        return service.click_white_control_v1(control, expected_before_age, intent_id, expected_revision=expected_revision)

    @server.tool(annotations=read_only_tool)
    def ck3_query_aub_business_state_v1(*, expected_revision: IngameUiRevisionV1 | None = None) -> dict[str, object]:
        """Read actual four fixed AUB character flags and complete detail census."""
        return service.query_aub_business_state_v1(expected_revision=expected_revision)

    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False))
    def ck3_confirm_aub_policy_v1(expected_selected_key: Literal[
        "aub_policy_treasury_only_pause_choice","aub_policy_treasury_only_continue_choice",
        "aub_policy_personal_only_pause_choice","aub_policy_personal_only_continue_choice",
        "aub_policy_treasury_first_pause_choice","aub_policy_treasury_first_continue_choice"],
        *, expected_revision: IngameUiRevisionV1 | None = None) -> dict[str, object]:
        """Confirm the actual selected AUB policy once; read independent native flags and closure."""
        return service.confirm_aub_policy_v1(expected_selected_key,expected_revision=expected_revision)

    @server.tool(annotations=read_only_tool)
    def ck3_query_aub_policy_options_v1(expected_revision: IngameUiRevisionV1 | None = None) -> dict[str, object]:
        """Read actual fixed six AUB keys/Entry.IsSelected; no enabled/tooltip/Confirm."""
        return service.query_aub_policy_options_v1(expected_revision=expected_revision)

    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False))
    def ck3_select_aub_policy_option_v1(
        expected_selected_key: Literal["aub_policy_treasury_only_pause_choice","aub_policy_treasury_only_continue_choice","aub_policy_personal_only_pause_choice","aub_policy_personal_only_continue_choice","aub_policy_treasury_first_pause_choice","aub_policy_treasury_first_continue_choice"],
        desired_key: Literal["aub_policy_treasury_only_pause_choice","aub_policy_treasury_only_continue_choice","aub_policy_personal_only_pause_choice","aub_policy_personal_only_continue_choice","aub_policy_treasury_first_pause_choice","aub_policy_treasury_first_continue_choice"],
        expected_revision: IngameUiRevisionV1 | None = None,
    ) -> dict[str, object]:
        """Invoke actual AUB Entry.Self source OnSelect once; require independent selected readback. Does not Confirm."""
        return service.select_aub_policy_option_v1(expected_selected_key,desired_key,expected_revision=expected_revision)

    @server.tool(annotations=read_only_tool)
    def ck3_query_white_rendered_text_v1(expected_revision: IngameUiRevisionV1 | None = None) -> dict[str, object]:
        """Read nine fixed actual visible White TextBox UTF-8 values; no down state."""
        return service.query_white_rendered_text_v1(expected_revision=expected_revision)

    @server.tool(annotations=read_only_tool)
    def ck3_query_white_player_business_variables_v1(expected_revision: IngameUiRevisionV1 | None = None) -> dict[str, object]:
        """Read eight fixed current-player White variables with actual absence/type/Q100000; no text/down/price or GUI credit."""
        return service.query_white_player_business_variables_v1(expected_revision=expected_revision)

    @server.tool(annotations=read_only_tool)
    def ck3_query_ingame_decision_item_v1(decision_key: str, expected_revision: int | None = None) -> dict[str, object]:
        """Read exact .3 native decision key/owner and actual detail definition; no widget action credit."""
        return service.query_ingame_decision_item_v1(decision_key, expected_revision=expected_revision)

    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False))
    def ck3_open_ingame_decisions_v1(expected_revision: int | None = None) -> dict[str, object]:
        """Open the fixed exact .3 Decisions HUD button once, with later native visibility proof."""
        return service.open_ingame_decisions_v1(expected_revision=expected_revision)

    @server.tool()
    def ck3_inspect_gui_window_tree_v1(
        window_kind: Literal["ingame_topbar", "decisions", "decision_detail", "courtier", "vivhite_courtier", "death_succession", "death_destiny"],
    ) -> dict[str, object]:
        """Read one bounded native window tree; no text, selection, hover or input."""
        return service.inspect_gui_window_tree_v1(window_kind)

    @server.tool()
    def ck3_inspect_frontend_gui_tree_v1() -> dict[str, object]:
        """Read a bounded native GUI-name census; no OCR or input."""
        return _ck3_inspect_frontend_gui_tree_v1(service)

    @server.tool()
    def ck3_inspect_frontend_coat_of_arms_tree_v1() -> dict[str, object]:
        """Inspect only the active native coat-of-arms page."""
        return _ck3_inspect_frontend_coat_of_arms_tree_v1(service)

    @server.tool()
    def ck3_inspect_frontend_coat_of_arms_pattern_grid_v1() -> dict[str, object]:
        """Inspect the fixed native pattern grid; no path, OCR, or input."""
        return _ck3_inspect_frontend_coat_of_arms_pattern_grid_v1(service)

    @server.tool()
    def ck3_compare_frontend_coat_of_arms_framebuffer_v1(
        reference_png_base64: str,
        reference_png_sha256: str,
    ) -> dict[str, object]:
        """Compare a canonical PNG to the native CoA framebuffer without input."""
        return _ck3_compare_frontend_coat_of_arms_framebuffer_v1(
            service,
            reference_png_base64,
            reference_png_sha256,
        )

    @server.tool()
    def ck3_calibrate_frontend_coat_of_arms_framebuffer_v2(
        calibration_id: str,
        phase: str,
    ) -> dict[str, object]:
        """Capture begin/complete states for a reference-independent CoA surface."""
        return _ck3_calibrate_frontend_coat_of_arms_framebuffer_v2(
            service,
            calibration_id,
            phase,
        )

    @server.tool()
    def ck3_compare_frontend_coat_of_arms_framebuffer_v2(
        calibration_id: str,
        reference_png_base64: str,
        reference_png_sha256: str,
    ) -> dict[str, object]:
        """Compare a canonical PNG against the fixed calibrated CoA surface."""
        return _ck3_compare_frontend_coat_of_arms_framebuffer_v2(
            service,
            calibration_id,
            reference_png_base64,
            reference_png_sha256,
        )

    @server.tool()
    def ck3_calibrate_frontend_coat_of_arms_framebuffer_v3(
        calibration_id: str,
        phase: str,
    ) -> dict[str, object]:
        """Capture surface/anchor states for reference-independent UV registration."""
        return _ck3_calibrate_frontend_coat_of_arms_framebuffer_v3(
            service,
            calibration_id,
            phase,
        )

    @server.tool()
    def ck3_compare_frontend_coat_of_arms_framebuffer_v3(
        calibration_id: str,
        reference_png_base64: str,
        reference_png_sha256: str,
    ) -> dict[str, object]:
        """Compare a canonical PNG against the native-UV-registered CoA surface."""
        return _ck3_compare_frontend_coat_of_arms_framebuffer_v3(
            service,
            calibration_id,
            reference_png_base64,
            reference_png_sha256,
        )

    @server.tool()
    def ck3_capture_frontend_coat_of_arms_framebuffer_v1(
        calibration_id: str,
        side: int = 230,
    ) -> dict[str, object]:
        """Capture the native-UV-registered CoA surface without a reference."""
        return _ck3_capture_frontend_coat_of_arms_framebuffer_v1(
            service, calibration_id, side
        )

    @server.tool()
    def ck3_prepare_frontend_coat_of_arms_framebuffer_v1() -> dict[str, object]:
        """Prepare the route-bound CK3 framebuffer without key or mouse input."""
        return _ck3_prepare_frontend_coat_of_arms_framebuffer_v1(service)

    @server.tool()
    def ck3_activate_frontend_new_game_v1() -> dict[str, object]:
        """Semantically open New Game and independently verify Bookmarks."""
        return _ck3_activate_frontend_new_game_v1(service)

    @server.tool()
    def ck3_activate_frontend_pick_any_character_v1() -> dict[str, object]:
        """Semantically open ruler selection and independently verify it."""
        return _ck3_activate_frontend_pick_any_character_v1(service)

    if getattr(driver, "frontend_fixture_start_policy_binding", None) is not None:
        @server.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False,
                                               idempotentHint=False, openWorldHint=False))
        def ck3_submit_frontend_fixture_robert_start_v1() -> dict[str, object]:
            """Explicit fixture Start once with actual Robert pre-proof; post-map proof is separate."""
            return service.submit_frontend_fixture_robert_start_v1()
        _forbid_unknown_tool_arguments_v1(server, "ck3_submit_frontend_fixture_robert_start_v1")

    @server.tool()
    def ck3_activate_frontend_start_1066_bookmark_character_v1(
        character_name_key: str,
    ) -> dict[str, object]:
        """Select a native 1066 bookmark character and verify its paused map."""
        return _ck3_activate_frontend_start_1066_bookmark_character_v1(
            service,
            character_name_key,
        )

    @server.tool()
    def ck3_activate_frontend_prepare_custom_ruler_v1() -> dict[str, object]:
        """Select one featured ruler and open a designer-ready lobby."""
        return _ck3_activate_frontend_prepare_custom_ruler_v1(service)

    @server.tool()
    def ck3_activate_frontend_ruler_designer_v1() -> dict[str, object]:
        """Open Ruler Designer through the fixed native GUI path."""
        return _ck3_activate_frontend_ruler_designer_v1(service)

    @server.tool()
    def ck3_activate_frontend_coat_of_arms_designer_v1() -> dict[str, object]:
        """Open the dynasty coat-of-arms page through its fixed native path."""
        return _ck3_activate_frontend_coat_of_arms_designer_v1(service)

    @server.tool()
    def ck3_commit_frontend_dynasty_coat_of_arms_v1() -> dict[str, object]:
        """Commit the dynasty coat of arms through the exact native Finish."""
        return _ck3_commit_frontend_dynasty_coat_of_arms_v1(service)

    @server.tool()
    def ck3_activate_frontend_coat_of_arms_custom_mode_v1() -> dict[str, object]:
        """Enter native custom mode and prove its background grid opened."""
        return _ck3_activate_frontend_coat_of_arms_custom_mode_v1(service)

    @server.tool()
    def ck3_query_coat_of_arms_resource_catalog_v1(
        game_directory: str,
        kind: str,
        query: str | None = None,
        visible_only: bool = True,
        offset: int = 0,
        limit: int = 50,
    ) -> dict[str, object]:
        """Index base-game designer manifests; does not claim engine registration."""
        return _ck3_query_coat_of_arms_resource_catalog_v1(
            game_directory,
            kind,
            query,
            visible_only,
            offset,
            limit,
        )

    @server.tool()
    def ck3_query_coat_of_arms_definition_catalog_v1(
        game_directory: str,
        query: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> dict[str, object]:
        """Page exact-build static CoA definitions; no VFS winner claim."""
        return _ck3_query_coat_of_arms_definition_catalog_v1(
            game_directory,
            query,
            offset,
            limit,
        )

    @server.tool()
    def ck3_read_coat_of_arms_definition_v1(
        game_directory: str,
        key: str,
    ) -> dict[str, object]:
        """Read exact source and an unambiguous static alias chain only."""
        return _ck3_read_coat_of_arms_definition_v1(game_directory, key)

    @server.tool()
    def ck3_read_coat_of_arms_resource_asset_v1(
        game_directory: str,
        kind: str,
        name: str,
    ) -> dict[str, object]:
        """Read one manifest-owned base-game CoA DDS; no runtime claim."""
        return _ck3_read_coat_of_arms_resource_asset_v1(
            game_directory,
            kind,
            name,
        )

    @server.tool()
    def ck3_read_coat_of_arms_render_support_v1(
        game_directory: str,
    ) -> dict[str, object]:
        """Read shader-grounded offline render inputs; no runtime claim."""
        return _ck3_read_coat_of_arms_render_support_v1(game_directory)

    @server.tool()
    def ck3_query_coat_of_arms_load_configuration_v1(
        user_directory: str,
    ) -> dict[str, object]:
        """Read dlc_load.json CoA candidates; does not claim engine VFS state."""
        return _ck3_query_coat_of_arms_load_configuration_v1(user_directory)

    @server.tool()
    def ck3_query_coat_of_arms_installed_dlc_sources_v1(
        game_directory: str,
    ) -> dict[str, object]:
        """List installed DLC CoA files; does not claim entitlement or mount."""
        return _ck3_query_coat_of_arms_installed_dlc_sources_v1(game_directory)

    @server.tool()
    def ck3_query_coat_of_arms_configured_resource_catalog_v1(
        user_directory: str,
        kind: str,
        query: str | None = None,
        visible_only: bool = True,
        offset: int = 0,
        limit: int = 50,
    ) -> dict[str, object]:
        """Page configured mod candidates; does not claim VFS precedence."""
        return _ck3_query_coat_of_arms_configured_resource_catalog_v1(
            user_directory,
            kind,
            query,
            visible_only,
            offset,
            limit,
        )

    @server.tool()
    def ck3_read_coat_of_arms_configured_resource_asset_v1(
        user_directory: str,
        kind: str,
        candidate_id: str,
    ) -> dict[str, object]:
        """Read one configured manifest-owned DDS; no VFS winner claim."""
        return _ck3_read_coat_of_arms_configured_resource_asset_v1(
            user_directory,
            kind,
            candidate_id,
        )

    @server.tool()
    def ck3_project_coat_of_arms_vfs_asset_winner_v1(
        game_directory: str,
        logical_path: str,
    ) -> dict[str, object]:
        """Project one direct DDS winner from complete live mount evidence."""
        return _ck3_project_coat_of_arms_vfs_asset_winner_v1(
            service,
            game_directory,
            logical_path,
        )

    @server.tool()
    def ck3_query_loaded_feature_manifest_v1(
        expected_revision: int,
    ) -> dict[str, object]:
        """Read effective build flags and script DLC keys; ownership stays unknown."""
        return _ck3_query_loaded_feature_manifest_v1(
            service,
            expected_revision,
        )

    @server.tool()
    def ck3_query_pending_character_interaction_context_v1(
        pending_interaction_id: int,
        expected_revision: int,
    ) -> dict[str, object]:
        """Read routing, paid costs, exact special-war binding, and legality."""
        return _ck3_query_pending_character_interaction_context_v1(
            service,
            pending_interaction_id,
            expected_revision,
        )

    @server.tool(annotations=read_only_tool)
    def ck3_query_character_interaction_ordinary_v1(
        interaction_key: OrdinaryInteractionKeyV1, recipient_id: OrdinaryRecipientIdV1,
        expected_revision: IngameUiRevisionV1,
    ) -> dict[str, object]:
        """Read actual ordinary interaction terms for the current actor and full recipient ID."""
        return service.query_character_interaction_ordinary_v1(interaction_key, recipient_id,
            expected_revision=expected_revision)

    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False, openWorldHint=False))
    def ck3_initiate_character_interaction_ordinary_v1(
        interaction_key: OrdinaryInteractionKeyV1, recipient_id: OrdinaryRecipientIdV1,
        expected_revision: IngameUiRevisionV1,
    ) -> dict[str, object]:
        """Submit one ordinary interaction; a pending receipt is not a business outcome."""
        return service.initiate_character_interaction_ordinary_v1(interaction_key, recipient_id,
            expected_revision=expected_revision)

    @server.tool(annotations=read_only_tool)
    def ck3_observe_normal_exit_v1() -> dict[str, object]:
        """Read the backend-owned pending original process handle; never redispatch."""
        return service.observe_normal_exit_v1()

    @server.tool(annotations=read_only_tool)
    def ck3_query_normal_exit_context_v1(expected_revision: NormalExitRevisionV1) -> dict[str, object]:
        """Observe the actual map exit context and backend signature; no dispatch."""
        return service.query_normal_exit_context_v1(expected_revision=expected_revision)

    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=False, openWorldHint=False))
    def ck3_request_normal_exit_v1(
        action: Literal["prepare_confirmation", "continue_preparation", "confirm_desktop"],
        expected_revision: NormalExitRevisionV1,
        expected_exit_context_signature: NormalExitSignatureV1,
    ) -> dict[str, object]:
        """Claim one stock map exit phase; confirmation preserves native save policy."""
        return service.request_normal_exit_v1(action, expected_revision=expected_revision,
            expected_exit_context_signature=expected_exit_context_signature)

    @server.tool(annotations=read_only_tool)
    def ck3_query_current_actor_stress_adjustment_v1(
        base_amount: StressBaseAmountV1, expected_revision: IngameUiRevisionV1,
    ) -> dict[str, object]:
        """Read current native stress adjustment; no option-cost or final-stress prediction."""
        return service.query_current_actor_stress_adjustment_v1(
            base_amount, expected_revision=expected_revision)

    @server.tool()
    def ck3_query_current_event_window_context_v1(
        event_instance_id: int,
        expected_revision: int,
    ) -> dict[str, object]:
        """Read shown options and typed indicators; full preview stays unavailable."""
        return _ck3_query_current_event_window_context_v1(
            service,
            event_instance_id,
            expected_revision,
        )

    @server.tool()
    def ck3_query_vanilla_event_knowledge_v1(
        event_definition_key: str,
        ck3_build: str = CURRENT_CK3_BUILD,
    ) -> dict[str, object]:
        """Read frozen source-reviewed event semantics without launching CK3."""
        return _ck3_query_vanilla_event_knowledge_v1(
            event_definition_key,
            ck3_build=ck3_build,
        )

    @server.tool()
    def ck3_list_vanilla_event_knowledge_v1(
        ck3_build: str = CURRENT_CK3_BUILD,
        query: str | None = None,
        namespace: str | None = None,
        evidence_class: str = "any",
        has_observations: bool | None = None,
        after_key: str | None = None,
        limit: int = 50,
    ) -> dict[str, object]:
        """Discover offline event knowledge with a stable dataset cursor."""
        return _ck3_list_vanilla_event_knowledge_v1(
            ck3_build=ck3_build,
            query=query,
            namespace=namespace,
            evidence_class=evidence_class,
            has_observations=has_observations,
            after_key=after_key,
            limit=limit,
        )

    @server.tool()
    def ck3_list_vanilla_event_evidence_v1(
        event_definition_key: str | None = None,
        kind: str | None = None,
        after_evidence_id: str | None = None,
        limit: int = 50,
        ck3_build: str = "1.19.0.6",
    ) -> dict[str, object]:
        """List portable evidence metadata; paths remain repository-relative."""
        return _ck3_list_vanilla_event_evidence_v1(
            event_definition_key,
            kind=kind,
            after_evidence_id=after_evidence_id,
            limit=limit,
            ck3_build=ck3_build,
        )

    @server.tool()
    def ck3_read_vanilla_event_evidence_v1(
        evidence_id: str,
        offset: int = 0,
        max_bytes: int = 64 * 1024,
        ck3_build: str = "1.19.0.6",
    ) -> dict[str, object]:
        """Read one verified evidence chunk by content SHA-256."""
        return _ck3_read_vanilla_event_evidence_v1(
            evidence_id,
            offset=offset,
            max_bytes=max_bytes,
            ck3_build=ck3_build,
        )

    @server.tool()
    def ck3_query_vanilla_event_source_provenance_v1(
        key: str,
        build: str = CURRENT_CK3_BUILD,
    ) -> dict[str, object]:
        """Read definition provenance and lexical, unproven caller candidates."""
        return _ck3_query_vanilla_event_source_provenance_v1(key, build)

    @server.tool()
    def ck3_preview_active_combat_retreat_v1(
        selected_public_cunit_id: PublicCUnitId,
        target_province_id: int,
        expected_revision: int,
    ) -> dict[str, object]:
        """Preview one legal active-combat withdrawal and return a short token."""
        return _ck3_preview_active_combat_retreat_v1(
            service,
            selected_public_cunit_id,
            target_province_id,
            expected_revision,
        )

    @server.tool()
    def ck3_order_active_combat_retreat_v1(
        selected_public_cunit_id: PublicCUnitId,
        expected_revision: int,
        expected_combat_id: int,
        expected_side_index: int,
        expected_scope: str,
        target_province_id: int,
        candidate_token: str,
    ) -> dict[str, object]:
        """Consume a fresh retreat token; ACK remains verification-pending."""
        return _ck3_order_active_combat_retreat_v1(
            service,
            selected_public_cunit_id,
            expected_revision,
            expected_combat_id,
            expected_side_index,
            expected_scope,
            target_province_id,
            candidate_token,
        )

    @server.tool()
    def ck3_query_combat_simulation_inputs(
        target_province_id: int,
        attacker_entry_province_id: int | None,
        attacker_army_ids: list[PublicCUnitId],
        defender_army_ids: list[PublicCUnitId],
        expected_revision: int | None = None,
        constructor_adjacency_kind_raw: Annotated[int, Field(strict=True, ge=0, le=0)] | None = None,
    ) -> dict[str, object]:
        """Read one explicit hypothetical contact; does not claim win odds."""
        return service.query_combat_simulation_inputs(
            target_province_id,
            attacker_entry_province_id,
            attacker_army_ids,
            defender_army_ids,
            expected_revision=expected_revision,
            constructor_adjacency_kind_raw=constructor_adjacency_kind_raw,
        )

    @server.tool()
    def ck3_query_combat_phase_event_trace_v1(
        combat_id: int,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Read one paused native CombatID evaluator; no battle odds or action."""
        return service.query_combat_phase_event_trace_v1(
            combat_id, expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_query_combat_simulation_inputs_v3(
        target_province_id: int,
        attacker_entry_province_id: int | None,
        attacker_army_ids: list[PublicCUnitId],
        defender_army_ids: list[PublicCUnitId],
        expected_revision: int | None = None,
        constructor_adjacency_kind_raw: Annotated[int, Field(strict=True, ge=0, le=0)] | None = None,
    ) -> dict[str, object]:
        """Read exact phase inputs; readiness does not imply simulated odds."""
        return _ck3_query_combat_simulation_inputs_v3(
            service,
            target_province_id,
            attacker_entry_province_id,
            attacker_army_ids,
            defender_army_ids,
            expected_revision=expected_revision,
            constructor_adjacency_kind_raw=constructor_adjacency_kind_raw,
        )

    @server.tool()
    def ck3_query_war_entry_assessments(
        target_character_ids: list[int],
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Read native power for one declarable or active-war target."""
        return _ck3_query_war_entry_assessments(
            service,
            target_character_ids,
            expected_revision=expected_revision,
        )

    @server.tool(annotations=read_only_tool)
    def ck3_query_player_claims_v1(
        title_ids: list[Annotated[int, Field(strict=True, ge=0, le=2**31 - 1)]],
        expected_revision: Annotated[int, Field(strict=True, ge=0)],
    ) -> dict[str, object]:
        """Read current-player claims for ordered full TitleIDs without requiring CWar."""
        return service.query_player_claims_v1(
            title_ids, expected_revision=expected_revision,
        )

    @server.tool(annotations=read_only_tool)
    def ck3_query_title_holder_v1(
        title_id: int,
        expected_revision: int,
    ) -> dict[str, object]:
        """Read the actual holder and realm relationships of one native TitleID."""
        return service.query_title_holder_v1(
            title_id, expected_revision=expected_revision,
        )

    @server.tool(annotations=read_only_tool)
    def ck3_query_war_occupation_targets_v1(
        war_id: Annotated[int, Field(strict=True, ge=0, le=2**31 - 1)],
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Read this war's native eligible holding and occupation collection."""
        return service.query_war_occupation_targets_v1(
            war_id, expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_query_war_termination_options(
        war_id: int,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Read native surrender/white-peace/victory legality for one WarID."""
        return service.query_war_termination_options(
            war_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_query_outbound_war_white_peace_status(
        war_id: int,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Read the exact sender-side pending receipt for white peace."""
        return service.query_outbound_war_white_peace_status(
            war_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_query_war_termination_terms(
        war_id: int,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Read exact claim-CB claimant, targets, claims and dispositions."""
        return service.query_war_termination_terms(
            war_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_surrender_war(
        war_id: int,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Submit surrender only from a same-revision native query result."""
        return service.surrender_war(
            war_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_offer_white_peace(
        war_id: int,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Offer white peace only when native support and query prove legality."""
        return service.offer_white_peace(
            war_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_select_event_option(
        option_number: int,
        event_instance_id: int | None = None,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Select a 1-based option on the current CK3 event."""
        return service.select_event_option(
            option_number,
            event_instance_id=event_instance_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_resolve_active_event(
        event_instance_id: int | None = None,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Choose and select the best enabled option on the current event."""
        return service.resolve_active_event(
            event_instance_id=event_instance_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_wait_for_change(
        after_revision: int, timeout_seconds: float = 10.0
    ) -> dict[str, object]:
        """Wait until CK3 publishes a newer semantic snapshot or timeout."""
        return service.wait_for_change(
            after_revision, timeout_seconds=timeout_seconds
        )

    @server.resource("ck3://capabilities")
    def ck3_capabilities_resource() -> dict[str, object]:
        return service.capabilities()

    @server.resource("ck3://state/current")
    def ck3_current_state_resource() -> dict[str, object]:
        return service.snapshot()

    _forbid_unknown_tool_arguments_v1(
        server, "ck3_query_zhongguo_ai_owned_case_snapshot_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_inspect_save_artifacts_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_query_engine_diagnostics_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_query_engine_log_literals_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_query_steward_develop_county_candidates_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_change_steward_develop_county_task_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_query_player_faction_alerts_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_query_zhongguo_b1_cycle_snapshot_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_query_zhongguo_result_case_snapshot_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_query_zhongguo_b2_pip_snapshot_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server,
        "ck3_query_zhongguo_promotion_compensation_postcondition_v1",
    )
    _forbid_unknown_tool_arguments_v1(
        server,
        "ck3_query_zhongguo_compensation_af5_snapshot_v1",
    )
    _forbid_unknown_tool_arguments_v1(
        server,
        "ck3_query_zhongguo_workforce_owner_snapshot_v1",
    )
    _forbid_unknown_tool_arguments_v1(
        server,
        "ck3_query_zhongguo_projects_metrics_postcondition_v1",
    )
    _forbid_unknown_tool_arguments_v1(
        server,
        "ck3_query_zhongguo_career_hc_workforce_postcondition_v1",
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_query_zhongguo_workforce_collective_snapshot_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_query_zhongguo_workforce_normal_exit_snapshot_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_query_zhongguo_incident_snapshot_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_query_zhongguo_manager_governance_snapshot_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_query_zhongguo_manager_subordinate_selector_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_query_zhongguo_scoreboard_state_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_activate_zhongguo_scoreboard_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_set_played_character_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_query_vanilla_event_knowledge_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_list_vanilla_event_knowledge_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_list_vanilla_event_evidence_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_read_vanilla_event_evidence_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_query_vanilla_event_source_provenance_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_begin_coat_of_arms_source_upload_v2"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_append_coat_of_arms_source_chunk_v2"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_commit_coat_of_arms_source_upload_v2"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_abort_coat_of_arms_source_upload_v2"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_probe_coat_of_arms_source_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_export_coat_of_arms_source_v1"
    )
    _forbid_unknown_tool_arguments_v1(server, "ck3_query_frontend_applied_game_rules_v1")
    _forbid_unknown_tool_arguments_v1(server, "ck3_query_frontend_game_rules_window_v1")
    _forbid_unknown_tool_arguments_v1(server, "ck3_select_frontend_game_rule_v1")
    _forbid_unknown_tool_arguments_v1(server, "ck3_apply_and_hide_frontend_game_rules_v1")
    _forbid_unknown_tool_arguments_v1(server, "ck3_hide_frontend_game_rules_v1")
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_query_frontend_game_rule_selections_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_activate_frontend_game_rules_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_query_frontend_gui_route_v1"
    )
    _forbid_unknown_tool_arguments_v1(server, "ck3_open_ingame_decisions_v1")
    _forbid_unknown_tool_arguments_v1(server, "ck3_query_white_player_business_variables_v1")
    _forbid_unknown_tool_arguments_v1(server, "ck3_query_aub_business_state_v1")
    _forbid_unknown_tool_arguments_v1(server, "ck3_confirm_aub_policy_v1")
    _forbid_unknown_tool_arguments_v1(server, "ck3_query_aub_policy_options_v1")
    _forbid_unknown_tool_arguments_v1(server, "ck3_select_aub_policy_option_v1")
    _forbid_unknown_tool_arguments_v1(server, "ck3_click_white_numeric_control_v1")
    _forbid_unknown_tool_arguments_v1(server, "ck3_click_white_control_v1")
    _forbid_unknown_tool_arguments_v1(server, "ck3_query_white_rendered_text_v1")
    _forbid_unknown_tool_arguments_v1(server, "ck3_query_ingame_decision_item_v1")
    _forbid_unknown_tool_arguments_v1(server, "ck3_select_ingame_decision_item_v1")
    _forbid_unknown_tool_arguments_v1(server, "ck3_confirm_ingame_decision_item_v1")
    _forbid_unknown_tool_arguments_v1(server, "ck3_confirm_ingame_decision_outcome_v1")
    _forbid_unknown_tool_arguments_v1(server, "ck3_observe_normal_exit_v1")
    _forbid_unknown_tool_arguments_v1(server, "ck3_query_normal_exit_context_v1")
    _forbid_unknown_tool_arguments_v1(server, "ck3_request_normal_exit_v1")
    _forbid_unknown_tool_arguments_v1(server, "ck3_query_current_actor_stress_adjustment_v1")
    _forbid_unknown_tool_arguments_v1(server, "ck3_query_character_interaction_ordinary_v1")
    _forbid_unknown_tool_arguments_v1(server, "ck3_initiate_character_interaction_ordinary_v1")
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_inspect_gui_window_tree_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_inspect_frontend_gui_tree_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_inspect_frontend_coat_of_arms_tree_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_inspect_frontend_coat_of_arms_pattern_grid_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_compare_frontend_coat_of_arms_framebuffer_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_calibrate_frontend_coat_of_arms_framebuffer_v2"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_compare_frontend_coat_of_arms_framebuffer_v2"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_calibrate_frontend_coat_of_arms_framebuffer_v3"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_compare_frontend_coat_of_arms_framebuffer_v3"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_capture_frontend_coat_of_arms_framebuffer_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_prepare_frontend_coat_of_arms_framebuffer_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_activate_frontend_new_game_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_activate_frontend_pick_any_character_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_activate_frontend_start_1066_bookmark_character_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_activate_frontend_prepare_custom_ruler_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_activate_frontend_ruler_designer_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_activate_frontend_coat_of_arms_designer_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_commit_frontend_dynasty_coat_of_arms_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_activate_frontend_coat_of_arms_custom_mode_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_query_coat_of_arms_resource_catalog_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_query_coat_of_arms_definition_catalog_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_read_coat_of_arms_definition_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_read_coat_of_arms_resource_asset_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_read_coat_of_arms_render_support_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_query_coat_of_arms_load_configuration_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_query_coat_of_arms_installed_dlc_sources_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_query_coat_of_arms_configured_resource_catalog_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_read_coat_of_arms_configured_resource_asset_v1"
    )
    _forbid_unknown_tool_arguments_v1(
        server, "ck3_project_coat_of_arms_vfs_asset_winner_v1"
    )
    return server


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="xar-ck3-mcp")
    result.add_argument(
        "--nonwar-only", action="store_true",
        help="plan nonwar opportunities, receipts and normal time advance through the public turn tools",
    )
    result.add_argument(
        "--driver",
        default=os.environ.get("XAR_CK3_BRIDGE_DRIVER", "vision-report"),
        help=(
            "vision-report, vision-session, mod, hybrid, native-headless, "
            "hybrid-fallback, or a module:factory returning GameplayBridgeDriver"
        ),
    )
    result.add_argument(
        "--state-dir",
        default=os.environ.get("XAR_AUTOPLAYER_STATE_DIR"),
        help=(
            "XarAutoplayer state root; native checkpoints materialize under "
            "<state-dir>/profile/save games"
        ),
    )
    result.add_argument(
        "--userdir",
        default=os.environ.get("XAR_CK3_USERDIR"),
        help="active CK3 user directory used by --driver mod",
    )
    result.add_argument(
        "--pipe-name",
        default=os.environ.get("XAR_CK3_BRIDGE_PIPE"),
        help=(
            r"native bridge pipe (default: \\.\pipe\xar_ck3_bridge_mcp); "
            "also accepted through XAR_CK3_BRIDGE_PIPE"
        ),
    )
    result.add_argument(
        "--transport", choices=("stdio", "streamable-http"), default="stdio"
    )
    result.add_argument("--host", default="127.0.0.1")
    result.add_argument("--port", type=int, default=8765)
    result.add_argument(
        "--environment-manifest",
        help="prepared environment manifest for an explicit native succession lifecycle",
    )
    result.add_argument(
        "--succession-lifecycle",
        choices=(ROGUE_ONE_LIFE, ORDINARY_CAMPAIGN_SUCCESSION),
    )
    result.add_argument("--ordinary-campaign-no-pact", action="store_true")
    result.add_argument(
        "--private-semantic-snapshot-readonly",
        action="store_true",
        help="enable the local stdio-only native frame read without command history",
    )
    result.add_argument(
        "--private-death-succession-modal-continue", action="store_true",
        help="enable the compiled native succession blocker read and typed modal Close",
    )
    result.add_argument(
        "--private-current-first-heir-relationship-query",
        action="store_true",
        help="enable the local stdio-only read of the current first-heir relation",
    )
    result.add_argument(
        "--private-player-child-marriage-subject-query",
        action="store_true",
        help="enable a local stdio-only read of one specified player child",
    )
    result.add_argument(
        "--private-active-scheme-sway-query", action="store_true",
        help="enable the private read of the current Sway instance and native terms",
    )
    result.add_argument(
        "--private-realm-law-paused-query", action="store_true",
        help="enable the private current-player realm-law final-terms read",
    )
    result.add_argument(
        "--private-government-runtime-adapter-query", action="store_true",
        help="enable the private same-frame government and effective-feature read",
    )
    result.add_argument(
        "--private-prisoner-collection-query", action="store_true",
        help="enable the private prisoner collection and native ransom quote read",
    )
    result.add_argument(
        "--private-activity-feast-queries", action="store_true",
        help="enable private Feast observation tools without enabling Start",
    )
    result.add_argument(
        "--private-war-cash-queries", action="store_true",
        help="enable actual current military expenses and termination send-fee reads",
    )
    result.add_argument(
        "--private-family-obligations-query", action="store_true",
        help="enable native child-house preview and betrothal-break terms reads",
    )
    result.add_argument(
        "--private-council-query", action="store_true",
        help="enable native Steward candidates and complete final-gate reads",
    )
    result.add_argument(
        "--private-realm-law-crown-action", action="store_true",
        help="enable the private explicit crown-law quote, typed enact and receipt",
    )
    result.add_argument(
        "--private-active-scheme-sway-action", action="store_true",
        help="enable explicit private Sway quote, typed start and independent receipt",
    )
    result.add_argument(
        "--private-council-action", action="store_true",
        help="enable the private explicit council candidate assignment and receipt",
    )
    result.add_argument(
        "--private-faction-gift-query", action="store_true",
        help="enable the private gift candidate read against an observed campaign root",
    )
    result.add_argument(
        "--private-faction-gift-action", action="store_true",
        help="enable explicit private gift submit, independent receipt and cold fact read",
    )
    result.add_argument(
        "--private-prisoner-ransom-action", action="store_true",
        help="enable an explicit private ransom using the current native collection quote",
    )
    result.add_argument(
        "--private-player-religion-context-query", action="store_true",
        help="enable the private current-player native Rite/Faith/Religion context read",
    )
    result.add_argument(
        "--private-player-religion-doctrines-query", action="store_true",
        help="enable the private current and main Faith doctrine read",
    )
    result.add_argument(
        "--private-player-rite-governance-query", action="store_true",
        help="enable private state Rite, heads and organization observations",
    )
    result.add_argument(
        "--private-player-religion-conversion-terms-query", action="store_true",
        help="enable private conversion terms and explicit paid target submission/results",
    )
    result.add_argument(
        "--private-active-scheme-sway-completion-query", action="store_true",
        help="enable the private exact Sway instance terminal-state observation",
    )
    result.add_argument(
        "--private-player-ordinary-holy-war-declaration-context-query", action="store_true",
        help="Read a selected ordinary holy-war context and its independent CB quote.",
    )
    result.add_argument(
        "--private-player-clergy-appointment-query", action="store_true",
        help="Read native candidate appointment and reassignment observations.",
    )
    result.add_argument(
        "--private-player-rite-members-query", action="store_true",
        help="Read the current Rite and Faith member lists in native order.",
    )
    result.add_argument(
        "--private-player-religion-hostility-query", action="store_true",
        help="Read native hostility values for an explicitly selected Rite.",
    )
    result.add_argument(
        "--private-player-religion-doctrine-knowledge-query", action="store_true",
        help="Read learned doctrines or the native lookup for one doctrine key.",
    )
    result.add_argument(
        "--private-player-religion-tenets-query", action="store_true",
        help="Read the current player's native tenet rows.",
    )
    result.add_argument(
        "--private-player-religion-conversion-choices-query", action="store_true",
        help="Read native conversion choices and current Faith Rite membership.",
    )
    result.add_argument(
        "--private-player-religion-conversion-inputs-query", action="store_true",
        help="Read native conversion knowledge and predicted fulfillment inputs.",
    )
    result.add_argument(
        "--private-player-epidemic-treatment-presence-query", action="store_true",
        help="enable the existing native player treatment presence observation",
    )
    result.add_argument(
        "--private-player-religion-conversion-reasons-query", action="store_true",
        help="enable the native conversion reason observation for a selected Rite",
    )
    result.add_argument(
        "--private-player-religion-reform-context-query", action="store_true",
        help="enable the native current-player reform context observation",
    )
    result.add_argument(
        "--private-active-scheme-sway-completion-execution-query", action="store_true",
        help="enable retained native hidden Sway execution observations",
    )
    result.add_argument(
        "--private-player-epidemic-recovery-query", action="store_true",
        help="enable the existing native CE1 recovery county observation",
    )
    result.add_argument(
        "--private-player-religion-doctrine-catalogue-query", action="store_true",
        help="enable the loaded native Doctrine definition catalogue observation",
    )
    result.add_argument(
        "--private-player-religion-numeric-special-parameters-query", action="store_true",
        help="enable Rite numeric cache and native Faith final value observations",
    )
    result.add_argument(
        "--private-player-religion-conversion-outcome-query", action="store_true",
        help="enable current conversion outcome observations for a selected Rite",
    )
    result.add_argument(
        "--private-active-scheme-sway-completion-termination-query", action="store_true",
        help="enable retained native Sway termination observations",
    )
    result.add_argument(
        "--private-player-religion-personal-parameters-query", action="store_true",
        help="enable the current player's native personal Tenet parameter observations",
    )
    result.add_argument(
        "--private-active-scheme-sway-completion-invalidation-reason-query", action="store_true",
        help="enable retained native Sway invalidation notification observations",
    )
    result.add_argument(
        "--private-player-religion-draft-groups-query", action="store_true",
        help="enable selected draft-group source and current native Tenet gate observations",
    )
    result.add_argument(
        "--private-player-religion-draft-doctrine-choices-query", action="store_true",
        help="enable current draft Doctrine source and native final gate observations",
    )
    result.add_argument(
        "--private-player-religion-draft-tenet-choices-query", action="store_true",
        help="enable current draft Tenet source and native final gate observations",
    )
    result.add_argument(
        "--private-player-religion-draft-resource-costs-query", action="store_true",
        help="enable the native current draft base resource fee quote",
    )
    result.add_argument(
        "--private-player-religion-ai-reform-inputs-query", action="store_true",
        help="enable native reform AI input and controller schedule observations",
    )
    result.add_argument(
        "--private-active-scheme-sway-outcome-opinion-query", action="store_true",
        help="enable independent native Sway modifier and current target opinion observations",
    )
    for name in (
        "authorization-receipt",
        "source-checkpoint",
        "source-driver",
        "submission-fence",
    ):
        result.add_argument("--war31-one-shot-" + name)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    explicit_lifecycle = (
        args.environment_manifest,
        args.succession_lifecycle,
        args.ordinary_campaign_no_pact,
    )
    if any(explicit_lifecycle) and (
        not args.environment_manifest or not args.succession_lifecycle
    ):
        raise ValueError(
            "explicit succession lifecycle requires an environment manifest and mode"
        )
    if any(explicit_lifecycle) and args.driver != "native-headless":
        raise ValueError("explicit succession lifecycle requires native-headless driver")
    succession_lifecycle_binding = (
        bind_succession_lifecycle_from_environment_v1(
            json.loads(Path(args.environment_manifest).read_text(encoding="utf-8-sig")),
            lifecycle=args.succession_lifecycle,
            ordinary_campaign_no_pact=args.ordinary_campaign_no_pact,
        )
        if args.environment_manifest else None
    )
    war31_paths = (
        args.war31_one_shot_authorization_receipt,
        args.war31_one_shot_source_checkpoint,
        args.war31_one_shot_source_driver,
        args.war31_one_shot_submission_fence,
    )
    if any(war31_paths) and not all(war31_paths):
        raise ValueError("WAR31 one-shot gate requires all four explicit paths")
    if all(war31_paths) and (
        args.driver != "native-headless" or args.transport != "stdio"
    ):
        raise ValueError("WAR31 one-shot gate requires native-headless stdio")
    war31_gate = (
        War31OneShotSurrenderGate(
            authorization_receipt=war31_paths[0],
            source_checkpoint=war31_paths[1],
            source_driver=war31_paths[2],
            submission_fence=war31_paths[3],
        )
        if all(war31_paths) else None
    )
    if args.private_current_first_heir_relationship_query and (
        args.driver != "native-headless" or args.transport != "stdio"
    ):
        raise ValueError(
            "private current first-heir relationship MCP query requires "
            "native-headless stdio"
        )
    if args.private_player_child_marriage_subject_query and (
        args.driver != "native-headless" or args.transport != "stdio"
    ):
        raise ValueError(
            "private player-child marriage MCP query requires native-headless stdio"
        )
    if (args.private_active_scheme_sway_query or args.private_realm_law_paused_query
            or args.private_government_runtime_adapter_query
            or args.private_prisoner_collection_query
            or args.private_activity_feast_queries or args.private_war_cash_queries
            or args.private_family_obligations_query or args.private_council_query
            or args.private_realm_law_crown_action
            or args.private_active_scheme_sway_action or args.private_council_action
            or args.private_faction_gift_query or args.private_faction_gift_action
            or args.private_prisoner_ransom_action
            or args.private_player_religion_context_query
            or args.private_player_religion_doctrines_query
            or args.private_player_rite_governance_query
            or args.private_player_religion_conversion_terms_query
            or args.private_active_scheme_sway_completion_query
            or args.private_player_ordinary_holy_war_declaration_context_query
            or args.private_player_clergy_appointment_query
            or args.private_player_rite_members_query
            or args.private_player_religion_hostility_query
            or args.private_player_religion_doctrine_knowledge_query
            or args.private_player_religion_tenets_query
            or args.private_player_religion_conversion_choices_query
            or args.private_player_religion_conversion_inputs_query
            or args.private_player_epidemic_treatment_presence_query
            or args.private_player_religion_conversion_reasons_query
            or args.private_player_religion_reform_context_query
            or args.private_active_scheme_sway_completion_execution_query
            or args.private_player_epidemic_recovery_query
            or args.private_player_religion_doctrine_catalogue_query
            or args.private_player_religion_numeric_special_parameters_query
            or args.private_player_religion_conversion_outcome_query
            or args.private_active_scheme_sway_completion_termination_query
            or args.private_player_religion_personal_parameters_query
            or args.private_active_scheme_sway_completion_invalidation_reason_query
            or args.private_player_religion_draft_groups_query
            or args.private_player_religion_draft_doctrine_choices_query
            or args.private_player_religion_draft_tenet_choices_query
            or args.private_player_religion_draft_resource_costs_query
            or args.private_player_religion_ai_reform_inputs_query
            or args.private_active_scheme_sway_outcome_opinion_query
            ) and (
        args.driver != "native-headless" or args.transport != "stdio"
    ):
        raise ValueError("private nonwar MCP queries require native-headless stdio")
    if args.private_semantic_snapshot_readonly and (
        args.driver != "native-headless" or args.transport != "stdio"
    ):
        raise ValueError(
            "private semantic snapshot MCP query requires native-headless stdio"
        )
    selected_state_dir = Path(args.state_dir) if args.state_dir else _default_state_dir()
    driver = load_driver(
        args.driver,
        userdir=args.userdir,
        state_dir=selected_state_dir,
        pipe_name=args.pipe_name,
        war31_one_shot_surrender_gate=war31_gate,
        succession_lifecycle_binding=succession_lifecycle_binding,
        allow_private_death_succession_modal_continue=(
            args.private_death_succession_modal_continue
        ),
    )
    driver.nonwar_only = args.nonwar_only
    if args.private_semantic_snapshot_readonly:
        driver.allow_private_semantic_snapshot_readonly = True
    if args.private_current_first_heir_relationship_query:
        driver.allow_private_current_first_heir_relationship_query = True
    if args.private_player_child_marriage_subject_query:
        driver.allow_private_player_child_marriage_subject_query = True
    if args.private_active_scheme_sway_query:
        driver.allow_private_active_scheme_sway_query = True
    if args.private_realm_law_paused_query:
        driver.allow_private_realm_law_paused_query = True
    if args.private_government_runtime_adapter_query:
        driver.allow_private_government_runtime_adapter_query = True
    if args.private_prisoner_collection_query:
        driver.allow_private_prisoner_collection_query = True
    if args.private_activity_feast_queries:
        driver.allow_private_activity_planner_diag_query = True
        driver.allow_private_activity_stage5_feast_full_cost_query = True
        driver.allow_private_activity_feast_stage5_start_query = True
        driver.allow_private_activity_feast_guest_candidate_query = True
        driver.allow_private_activity_feast_guest_opinion_query = True
        driver.allow_private_activity_feast_guest_target_query = True
        driver.allow_private_activity_feast_guest_route_proof_query = True
        driver.allow_private_activity_feast_guest_rule_provenance_query = True
        driver.allow_private_activity_feast_lifecycle_observation = True
    if args.private_war_cash_queries:
        driver.allow_private_war_cash_query = True
    if args.private_family_obligations_query:
        driver.allow_private_family_obligations_query = True
    if args.private_council_query:
        driver.allow_private_council_query = True
    if args.private_realm_law_crown_action:
        driver.allow_private_realm_law_action = True
    if args.private_active_scheme_sway_action:
        driver.allow_private_active_scheme_sway_query = True
        driver.allow_private_active_scheme_sway_action = True
    if args.private_council_action:
        driver.allow_private_council_query = True
        driver.allow_private_council_action = True
    if args.private_faction_gift_query:
        driver.allow_private_faction_gift_query = True
    if args.private_faction_gift_action:
        driver.allow_private_faction_gift_query = True
        driver.allow_private_faction_gift_action = True
    if args.private_prisoner_ransom_action:
        driver.allow_private_prisoner_collection_query = True
        driver.allow_private_prisoner_ransom_action = True
    if args.private_player_religion_context_query:
        driver.allow_private_player_religion_context_query = True
    if args.private_player_religion_doctrines_query:
        driver.allow_private_player_religion_doctrines_query = True
    if args.private_player_rite_governance_query:
        driver.allow_private_player_rite_governance_query = True
    if args.private_player_religion_conversion_terms_query:
        driver.allow_private_player_religion_conversion_terms_query = True
    if args.private_active_scheme_sway_completion_query:
        driver.allow_private_active_scheme_sway_completion_query = True
    if args.private_player_ordinary_holy_war_declaration_context_query:
        driver.allow_private_player_ordinary_holy_war_declaration_context_query = True
    if args.private_player_clergy_appointment_query:
        driver.allow_private_player_clergy_appointment_query = True
    if args.private_player_rite_members_query:
        driver.allow_private_player_rite_members_query = True
    if args.private_player_religion_hostility_query:
        driver.allow_private_player_religion_hostility_query = True
    if args.private_player_religion_doctrine_knowledge_query:
        driver.allow_private_player_religion_doctrine_knowledge_query = True
    if args.private_player_religion_tenets_query:
        driver.allow_private_player_religion_tenets_query = True
    if args.private_player_religion_conversion_choices_query:
        driver.allow_private_player_religion_conversion_choices_query = True
    if args.private_player_religion_conversion_inputs_query:
        driver.allow_private_player_religion_conversion_inputs_query = True
    if args.private_player_epidemic_treatment_presence_query:
        driver.allow_private_epidemic_treatment_presence_query = True
    if args.private_player_religion_conversion_reasons_query:
        driver.allow_private_player_religion_conversion_reasons_query = True
    if args.private_player_religion_reform_context_query:
        driver.allow_private_player_religion_reform_context_query = True
    if args.private_active_scheme_sway_completion_execution_query:
        driver.allow_private_active_scheme_sway_completion_execution_query = True
    if args.private_player_epidemic_recovery_query:
        driver.allow_private_epidemic_recovery_query = True
    if args.private_player_religion_doctrine_catalogue_query:
        driver.allow_private_player_religion_doctrine_catalogue_query = True
    if args.private_player_religion_numeric_special_parameters_query:
        driver.allow_private_player_religion_numeric_special_parameters_query = True
    if args.private_player_religion_conversion_outcome_query:
        driver.allow_private_player_religion_conversion_outcome_query = True
    if args.private_active_scheme_sway_completion_termination_query:
        driver.allow_private_active_scheme_sway_completion_termination_query = True
    if args.private_player_religion_personal_parameters_query:
        driver.allow_private_player_religion_personal_parameters_query = True
    if args.private_active_scheme_sway_completion_invalidation_reason_query:
        driver.allow_private_active_scheme_sway_completion_invalidation_reason_query = True
    if args.private_player_religion_draft_groups_query:
        driver.allow_private_player_religion_draft_groups_query = True
    if args.private_player_religion_draft_doctrine_choices_query:
        driver.allow_private_player_religion_draft_doctrine_choices_query = True
    if args.private_player_religion_draft_tenet_choices_query:
        driver.allow_private_player_religion_draft_tenet_choices_query = True
    if args.private_player_religion_draft_resource_costs_query:
        driver.allow_private_player_religion_draft_resource_costs_query = True
    if args.private_player_religion_ai_reform_inputs_query:
        driver.allow_private_player_religion_ai_reform_inputs_query = True
    if args.private_active_scheme_sway_outcome_opinion_query:
        driver.allow_private_active_scheme_sway_outcome_opinion_query = True
    server = create_server(
        driver,
        profile_dir=selected_state_dir / "profile",
    )
    try:
        if args.transport == "stdio":
            server.run(transport="stdio")
        else:
            server.run(
                transport="streamable-http",
                host=args.host,
                port=args.port,
                stateless_http=True,
                json_response=True,
            )
    finally:
        close = getattr(driver, "close", None)
        if callable(close):
            close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
