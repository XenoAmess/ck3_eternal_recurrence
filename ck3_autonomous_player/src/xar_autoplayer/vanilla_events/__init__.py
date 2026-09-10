"""Exact-build, read-only knowledge for CK3 vanilla events."""

from typing import Final

from .registry import (
    EXACT_CK3_BUILD,
    EXACT_CK3_EXE_SHA256,
    build_vanilla_event_registry,
    materialize_vanilla_timeline_contract,
    query_vanilla_event_knowledge_v1,
)
from .discovery import ck3_list_vanilla_event_knowledge_v1
from .portable_evidence import (
    list_vanilla_event_evidence_v1,
    portable_event_keys_v1,
    read_vanilla_event_evidence_v1,
)
from .source_index import query_vanilla_event_source_provenance_v1
from .records_analysis_embedded_a import (
    VANILLA_EMBEDDED_A_ANALYSIS,
    VANILLA_EMBEDDED_A_OBSERVATIONS,
)
from .records_analysis_embedded_b import (
    VANILLA_EMBEDDED_B_ANALYSIS,
    VANILLA_EMBEDDED_B_OBSERVATIONS,
)
from .records_analysis_embedded_c import VANILLA_EMBEDDED_C_ANALYSIS
from .records_analysis_manager_a import MANAGER_A_VANILLA_EVENT_ANALYSIS
from .records_analysis_manager_b import (
    MANAGER_VANILLA_ANALYSIS_B,
    MANAGER_VANILLA_OBSERVATIONS_B,
)
from .records_analysis_vanilla_shards import (
    VANILLA_SHARD_ANALYSIS,
    VANILLA_SHARD_OBSERVATIONS,
)
from .records_artifact import (
    VANILLA_ARTIFACT_ANALYSIS,
    VANILLA_ARTIFACT_OBSERVATIONS,
    VANILLA_ARTIFACT_TIMELINE_CONTRACTS,
)
from .records_bp1_house_feud import (
    VANILLA_BP1_HOUSE_FEUD_ANALYSIS,
    VANILLA_BP1_HOUSE_FEUD_OBSERVATIONS,
    VANILLA_BP1_HOUSE_FEUD_TIMELINE_CONTRACTS,
)
from .records_bp1_yearly import (
    VANILLA_BP1_YEARLY_ANALYSIS,
    VANILLA_BP1_YEARLY_OBSERVATIONS,
    VANILLA_BP1_YEARLY_TIMELINE_CONTRACTS,
)
from .records_embedded import EMBEDDED_VANILLA_TIMELINE_CONTRACTS
from .records_embedded_c import EMBEDDED_C_VANILLA_OBSERVATIONS
from .records_death_management import (
    VANILLA_DEATH_MANAGEMENT_ANALYSIS,
    VANILLA_DEATH_MANAGEMENT_OBSERVATIONS,
    VANILLA_DEATH_MANAGEMENT_TIMELINE_CONTRACTS,
)
from .records_diplomacy_majesty import (
    VANILLA_DIPLOMACY_MAJESTY_ANALYSIS,
    VANILLA_DIPLOMACY_MAJESTY_OBSERVATIONS,
    VANILLA_DIPLOMACY_MAJESTY_TIMELINE_CONTRACTS,
)
from .records_faction_demand import (
    VANILLA_FACTION_DEMAND_ANALYSIS,
    VANILLA_FACTION_DEMAND_OBSERVATIONS,
    VANILLA_FACTION_DEMAND_TIMELINE_CONTRACTS,
)
from .records_health import (
    VANILLA_HEALTH_ANALYSIS,
    VANILLA_HEALTH_OBSERVATIONS,
    VANILLA_HEALTH_TIMELINE_CONTRACTS,
)
from .records_epidemic import (
    VANILLA_EPIDEMIC_ANALYSIS,
    VANILLA_EPIDEMIC_OBSERVATIONS,
    VANILLA_EPIDEMIC_TIMELINE_CONTRACTS,
)
from .records_ep3_landless_admin import (
    VANILLA_EP3_LANDLESS_ADMIN_ANALYSIS,
    VANILLA_EP3_LANDLESS_ADMIN_OBSERVATIONS,
    VANILLA_EP3_LANDLESS_ADMIN_TIMELINE_CONTRACTS,
)
from .records_manager_a import (
    MANAGER_HOLY_WAR_ANALYSIS,
    MANAGER_HOLY_WAR_OBSERVATIONS,
    MANAGER_VANILLA_OBSERVATIONS_A,
    MANAGER_VANILLA_TIMELINE_CONTRACTS_A,
)
from .records_manager_b import (
    MANAGER_VANILLA_LEGACY_OBSERVATIONS_B,
    MANAGER_VANILLA_TIMELINE_CONTRACTS_B,
)
from .records_pay_homage import (
    VANILLA_PAY_HOMAGE_ANALYSIS,
    VANILLA_PAY_HOMAGE_OBSERVATIONS,
    VANILLA_PAY_HOMAGE_TIMELINE_CONTRACTS,
)
from .records_tgp_dynastic_cycle import (
    VANILLA_TGP_DYNASTIC_CYCLE_ANALYSIS,
    VANILLA_TGP_DYNASTIC_CYCLE_OBSERVATIONS,
    VANILLA_TGP_DYNASTIC_CYCLE_TIMELINE_CONTRACTS,
)
from .records_tgp_movement import (
    VANILLA_TGP_MOVEMENT_ANALYSIS,
    VANILLA_TGP_MOVEMENT_OBSERVATIONS,
    VANILLA_TGP_MOVEMENT_TIMELINE_CONTRACTS,
)
from .records_tgp_treasury import (
    VANILLA_TGP_TREASURY_ANALYSIS,
    VANILLA_TGP_TREASURY_OBSERVATIONS,
    VANILLA_TGP_TREASURY_TIMELINE_CONTRACTS,
)
from .records_trait_specific import (
    VANILLA_TRAIT_SPECIFIC_ANALYSIS,
    VANILLA_TRAIT_SPECIFIC_OBSERVATIONS,
    VANILLA_TRAIT_SPECIFIC_TIMELINE_CONTRACTS,
)
from .records_vassal_interaction import (
    VANILLA_VASSAL_INTERACTION_ANALYSIS,
    VANILLA_VASSAL_INTERACTION_OBSERVATIONS,
    VANILLA_VASSAL_INTERACTION_TIMELINE_CONTRACTS,
)
from .records_yearly import (
    VANILLA_YEARLY_ANALYSIS,
    VANILLA_YEARLY_OBSERVATIONS,
    VANILLA_YEARLY_TIMELINE_CONTRACTS,
)
from .records_vanilla_shards import (
    VANILLA_SHARD_LEGACY_LIVE_OBSERVATIONS_A,
    VANILLA_SHARD_LEGACY_LIVE_OBSERVATIONS_B,
    VANILLA_SHARD_TIMELINE_CONTRACTS,
)


DEFAULT_VANILLA_EVENT_CONTRACT_GROUPS: Final = (
    VANILLA_SHARD_TIMELINE_CONTRACTS,
    MANAGER_VANILLA_TIMELINE_CONTRACTS_A,
    MANAGER_VANILLA_TIMELINE_CONTRACTS_B,
    EMBEDDED_VANILLA_TIMELINE_CONTRACTS,
    VANILLA_EPIDEMIC_TIMELINE_CONTRACTS,
    VANILLA_EP3_LANDLESS_ADMIN_TIMELINE_CONTRACTS,
    VANILLA_TGP_MOVEMENT_TIMELINE_CONTRACTS,
    VANILLA_TGP_DYNASTIC_CYCLE_TIMELINE_CONTRACTS,
    VANILLA_PAY_HOMAGE_TIMELINE_CONTRACTS,
    VANILLA_VASSAL_INTERACTION_TIMELINE_CONTRACTS,
    VANILLA_TRAIT_SPECIFIC_TIMELINE_CONTRACTS,
    VANILLA_DEATH_MANAGEMENT_TIMELINE_CONTRACTS,
    VANILLA_DIPLOMACY_MAJESTY_TIMELINE_CONTRACTS,
    VANILLA_FACTION_DEMAND_TIMELINE_CONTRACTS,
    VANILLA_TGP_TREASURY_TIMELINE_CONTRACTS,
    VANILLA_YEARLY_TIMELINE_CONTRACTS,
    VANILLA_BP1_HOUSE_FEUD_TIMELINE_CONTRACTS,
    VANILLA_BP1_YEARLY_TIMELINE_CONTRACTS,
    VANILLA_ARTIFACT_TIMELINE_CONTRACTS,
    VANILLA_HEALTH_TIMELINE_CONTRACTS,
)


def _merge_metadata_tables(
    *tables: tuple[str, dict[str, dict[str, object]]],
) -> dict[str, dict[str, object]]:
    """Combine disjoint metadata sources without silent event-key replacement."""
    aggregate: dict[str, dict[str, object]] = {}
    for source_name, table in tables:
        duplicates = set(aggregate).intersection(table)
        if duplicates:
            raise ValueError(
                f"duplicate vanilla event metadata from {source_name}: "
                f"{sorted(duplicates)}"
            )
        aggregate.update(table)
    return aggregate


DEFAULT_VANILLA_EVENT_ANALYSIS: Final = _merge_metadata_tables(
    ("vanilla_shards", VANILLA_SHARD_ANALYSIS),
    ("manager_a", MANAGER_A_VANILLA_EVENT_ANALYSIS),
    ("manager_holy_war", MANAGER_HOLY_WAR_ANALYSIS),
    ("manager_b", MANAGER_VANILLA_ANALYSIS_B),
    ("embedded_a", VANILLA_EMBEDDED_A_ANALYSIS),
    ("embedded_b", VANILLA_EMBEDDED_B_ANALYSIS),
    ("embedded_c", VANILLA_EMBEDDED_C_ANALYSIS),
    ("epidemic", VANILLA_EPIDEMIC_ANALYSIS),
    ("ep3_landless_admin", VANILLA_EP3_LANDLESS_ADMIN_ANALYSIS),
    ("tgp_dynastic_cycle", VANILLA_TGP_DYNASTIC_CYCLE_ANALYSIS),
    ("pay_homage", VANILLA_PAY_HOMAGE_ANALYSIS),
    ("tgp_movement", VANILLA_TGP_MOVEMENT_ANALYSIS),
    ("vassal_interaction", VANILLA_VASSAL_INTERACTION_ANALYSIS),
    ("trait_specific", VANILLA_TRAIT_SPECIFIC_ANALYSIS),
    ("death_management", VANILLA_DEATH_MANAGEMENT_ANALYSIS),
    ("diplomacy_majesty", VANILLA_DIPLOMACY_MAJESTY_ANALYSIS),
    ("faction_demand", VANILLA_FACTION_DEMAND_ANALYSIS),
    ("tgp_treasury", VANILLA_TGP_TREASURY_ANALYSIS),
    ("yearly", VANILLA_YEARLY_ANALYSIS),
    ("bp1_house_feud", VANILLA_BP1_HOUSE_FEUD_ANALYSIS),
    ("bp1_yearly", VANILLA_BP1_YEARLY_ANALYSIS),
    ("artifact", VANILLA_ARTIFACT_ANALYSIS),
    ("health", VANILLA_HEALTH_ANALYSIS),
)
DEFAULT_VANILLA_EVENT_OBSERVATIONS: Final = _merge_metadata_tables(
    ("vanilla_shards", VANILLA_SHARD_OBSERVATIONS),
    (
        "vanilla_shards_legacy_live_a",
        VANILLA_SHARD_LEGACY_LIVE_OBSERVATIONS_A,
    ),
    (
        "vanilla_shards_legacy_live_b",
        VANILLA_SHARD_LEGACY_LIVE_OBSERVATIONS_B,
    ),
    ("manager_holy_war", MANAGER_HOLY_WAR_OBSERVATIONS),
    ("manager_a_legacy_live", MANAGER_VANILLA_OBSERVATIONS_A),
    ("manager_b", MANAGER_VANILLA_OBSERVATIONS_B),
    ("manager_b_legacy_live", MANAGER_VANILLA_LEGACY_OBSERVATIONS_B),
    ("embedded_a", VANILLA_EMBEDDED_A_OBSERVATIONS),
    ("embedded_b", VANILLA_EMBEDDED_B_OBSERVATIONS),
    ("embedded_c", EMBEDDED_C_VANILLA_OBSERVATIONS),
    ("epidemic", VANILLA_EPIDEMIC_OBSERVATIONS),
    ("ep3_landless_admin", VANILLA_EP3_LANDLESS_ADMIN_OBSERVATIONS),
    ("tgp_dynastic_cycle", VANILLA_TGP_DYNASTIC_CYCLE_OBSERVATIONS),
    ("pay_homage", VANILLA_PAY_HOMAGE_OBSERVATIONS),
    ("tgp_movement", VANILLA_TGP_MOVEMENT_OBSERVATIONS),
    ("vassal_interaction", VANILLA_VASSAL_INTERACTION_OBSERVATIONS),
    ("trait_specific", VANILLA_TRAIT_SPECIFIC_OBSERVATIONS),
    ("death_management", VANILLA_DEATH_MANAGEMENT_OBSERVATIONS),
    ("diplomacy_majesty", VANILLA_DIPLOMACY_MAJESTY_OBSERVATIONS),
    ("faction_demand", VANILLA_FACTION_DEMAND_OBSERVATIONS),
    ("tgp_treasury", VANILLA_TGP_TREASURY_OBSERVATIONS),
    ("yearly", VANILLA_YEARLY_OBSERVATIONS),
    ("bp1_house_feud", VANILLA_BP1_HOUSE_FEUD_OBSERVATIONS),
    ("bp1_yearly", VANILLA_BP1_YEARLY_OBSERVATIONS),
    ("artifact", VANILLA_ARTIFACT_OBSERVATIONS),
    ("health", VANILLA_HEALTH_OBSERVATIONS),
)


def _merge_default_contract_groups() -> dict[str, dict[str, object]]:
    """Build the legacy-compatible view without copying canonical values."""
    aggregate: dict[str, dict[str, object]] = {}
    for group in DEFAULT_VANILLA_EVENT_CONTRACT_GROUPS:
        duplicates = set(aggregate).intersection(group)
        if duplicates:
            raise ValueError(
                "duplicate default vanilla event contract key(s): "
                f"{sorted(duplicates)}"
            )
        aggregate.update(group)
    return aggregate


DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS: Final = (
    _merge_default_contract_groups()
)
VANILLA_EVENT_TIMELINE_CONTRACTS: Final = (
    DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS
)

# The public aggregate above intentionally preserves the canonical child
# objects for legacy production wrappers.  Query consumers use this separate
# defensive snapshot and therefore cannot mutate those source records.
build_vanilla_event_registry(
    DEFAULT_VANILLA_EVENT_CONTRACT_GROUPS,
    analysis=DEFAULT_VANILLA_EVENT_ANALYSIS,
    observations=DEFAULT_VANILLA_EVENT_OBSERVATIONS,
)

__all__ = [
    "DEFAULT_VANILLA_EVENT_ANALYSIS",
    "DEFAULT_VANILLA_EVENT_CONTRACT_GROUPS",
    "DEFAULT_VANILLA_EVENT_OBSERVATIONS",
    "DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS",
    "EXACT_CK3_BUILD",
    "EXACT_CK3_EXE_SHA256",
    "VANILLA_EVENT_TIMELINE_CONTRACTS",
    "build_vanilla_event_registry",
    "ck3_list_vanilla_event_knowledge_v1",
    "list_vanilla_event_evidence_v1",
    "materialize_vanilla_timeline_contract",
    "portable_event_keys_v1",
    "query_vanilla_event_knowledge_v1",
    "query_vanilla_event_source_provenance_v1",
    "read_vanilla_event_evidence_v1",
]
