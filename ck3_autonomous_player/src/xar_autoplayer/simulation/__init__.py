"""Pure, side-effect-free simulation helpers."""

from .combat_core import (
    CURRENT_BOUNDED_CORE_MANIFEST,
    BattleTransitionKernel,
    CombatExperiment,
    CombatMonteCarloSummary,
    TransitionFidelityManifest,
    run_combat_experiment,
)
from .combat_input import (
    EngagementReadiness,
    FrozenCombatSimulationInput,
    engagement_readiness,
    freeze_combat_simulation_input,
    load_live_combat_fixture,
)
from .phase_event_manifest import (
    STOCK_PHASE_EVENT_MANIFEST_SHA256,
    FrozenPhaseEventManifest,
    load_stock_phase_event_manifest,
)
from .phase_event_evaluator import (
    PHASE_EVENT_AST_EVALUATOR_SCHEMA_VERSION,
    PHASE_EVENT_AST_EVALUATOR_SHA256,
    PHASE_EVENT_AST_EVALUATOR_VERSION,
    PhaseEventEvaluationError,
    PhaseEventTrialState,
    audit_stock_phase_event_evaluator,
    evaluate_phase_event_contexts,
    execute_phase_event_effect,
)
from .candidate_source_proof import (
    CANDIDATE_SOURCE_PROOF_POLICY,
    CandidateSourceProofError,
    candidate_source_sequence_preimage,
    candidate_source_sequence_sha256,
    normalize_candidate_source_proof,
)
from .loaded_playset_proof import (
    LOADED_PLAYSET_PROOF_SCHEMA_VERSION,
    LOADED_PLAYSET_PROOF_SCOPE,
    LoadedPlaysetProofError,
    build_loaded_playset_proof,
    unavailable_loaded_playset_proof,
    validate_loaded_playset_proof,
)
from .combat_decision_contract import (
    COMBAT_ENTRY_EU_ACTIVATION_ENABLED,
    COMBAT_ENTRY_EU_CONTRACT_SHA256,
    COMBAT_ENTRY_EU_CONTRACT_VERSION,
    COMBAT_ENTRY_EU_SCHEMA_VERSION,
    CombatEntryEuContractError,
    assess_combat_entry_eu_contract,
    combat_entry_eu_contract,
)

__all__ = [
    "CURRENT_BOUNDED_CORE_MANIFEST",
    "BattleTransitionKernel",
    "CombatExperiment",
    "CombatMonteCarloSummary",
    "TransitionFidelityManifest",
    "run_combat_experiment",
    "EngagementReadiness",
    "FrozenCombatSimulationInput",
    "engagement_readiness",
    "freeze_combat_simulation_input",
    "load_live_combat_fixture",
    "STOCK_PHASE_EVENT_MANIFEST_SHA256",
    "FrozenPhaseEventManifest",
    "load_stock_phase_event_manifest",
    "PHASE_EVENT_AST_EVALUATOR_SCHEMA_VERSION",
    "PHASE_EVENT_AST_EVALUATOR_SHA256",
    "PHASE_EVENT_AST_EVALUATOR_VERSION",
    "PhaseEventEvaluationError",
    "PhaseEventTrialState",
    "audit_stock_phase_event_evaluator",
    "evaluate_phase_event_contexts",
    "execute_phase_event_effect",
    "CANDIDATE_SOURCE_PROOF_POLICY",
    "CandidateSourceProofError",
    "candidate_source_sequence_preimage",
    "candidate_source_sequence_sha256",
    "normalize_candidate_source_proof",
    "LOADED_PLAYSET_PROOF_SCHEMA_VERSION",
    "LOADED_PLAYSET_PROOF_SCOPE",
    "LoadedPlaysetProofError",
    "build_loaded_playset_proof",
    "unavailable_loaded_playset_proof",
    "validate_loaded_playset_proof",
    "COMBAT_ENTRY_EU_ACTIVATION_ENABLED",
    "COMBAT_ENTRY_EU_CONTRACT_SHA256",
    "COMBAT_ENTRY_EU_CONTRACT_VERSION",
    "COMBAT_ENTRY_EU_SCHEMA_VERSION",
    "CombatEntryEuContractError",
    "assess_combat_entry_eu_contract",
    "combat_entry_eu_contract",
]
