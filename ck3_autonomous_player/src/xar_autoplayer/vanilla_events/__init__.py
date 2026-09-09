"""Exact-build, read-only knowledge for CK3 vanilla events."""

from typing import Final

from .registry import (
    EXACT_CK3_BUILD,
    EXACT_CK3_EXE_SHA256,
    build_vanilla_event_registry,
    materialize_vanilla_timeline_contract,
    query_vanilla_event_knowledge_v1,
)
from .records_analysis_embedded_a import (
    VANILLA_EMBEDDED_A_ANALYSIS,
    VANILLA_EMBEDDED_A_OBSERVATIONS,
)
from .records_analysis_embedded_b import VANILLA_EMBEDDED_B_ANALYSIS
from .records_analysis_embedded_c import VANILLA_EMBEDDED_C_ANALYSIS
from .records_analysis_manager_a import MANAGER_A_VANILLA_EVENT_ANALYSIS
from .records_analysis_manager_b import MANAGER_VANILLA_ANALYSIS_B
from .records_analysis_vanilla_shards import (
    VANILLA_SHARD_ANALYSIS,
    VANILLA_SHARD_OBSERVATIONS,
)
from .records_embedded import EMBEDDED_VANILLA_TIMELINE_CONTRACTS
from .records_epidemic import (
    VANILLA_EPIDEMIC_ANALYSIS,
    VANILLA_EPIDEMIC_OBSERVATIONS,
    VANILLA_EPIDEMIC_TIMELINE_CONTRACTS,
)
from .records_manager_a import (
    MANAGER_HOLY_WAR_ANALYSIS,
    MANAGER_HOLY_WAR_OBSERVATIONS,
    MANAGER_VANILLA_TIMELINE_CONTRACTS_A,
)
from .records_manager_b import MANAGER_VANILLA_TIMELINE_CONTRACTS_B
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
from .records_vanilla_shards import VANILLA_SHARD_TIMELINE_CONTRACTS


DEFAULT_VANILLA_EVENT_CONTRACT_GROUPS: Final = (
    VANILLA_SHARD_TIMELINE_CONTRACTS,
    MANAGER_VANILLA_TIMELINE_CONTRACTS_A,
    MANAGER_VANILLA_TIMELINE_CONTRACTS_B,
    EMBEDDED_VANILLA_TIMELINE_CONTRACTS,
    VANILLA_EPIDEMIC_TIMELINE_CONTRACTS,
    VANILLA_TGP_MOVEMENT_TIMELINE_CONTRACTS,
    VANILLA_TGP_DYNASTIC_CYCLE_TIMELINE_CONTRACTS,
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
    ("tgp_dynastic_cycle", VANILLA_TGP_DYNASTIC_CYCLE_ANALYSIS),
    ("tgp_movement", VANILLA_TGP_MOVEMENT_ANALYSIS),
)
DEFAULT_VANILLA_EVENT_OBSERVATIONS: Final = _merge_metadata_tables(
    ("vanilla_shards", VANILLA_SHARD_OBSERVATIONS),
    ("manager_holy_war", MANAGER_HOLY_WAR_OBSERVATIONS),
    ("embedded_a", VANILLA_EMBEDDED_A_OBSERVATIONS),
    ("epidemic", VANILLA_EPIDEMIC_OBSERVATIONS),
    ("tgp_dynastic_cycle", VANILLA_TGP_DYNASTIC_CYCLE_OBSERVATIONS),
    ("tgp_movement", VANILLA_TGP_MOVEMENT_OBSERVATIONS),
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
    "materialize_vanilla_timeline_contract",
    "query_vanilla_event_knowledge_v1",
]
