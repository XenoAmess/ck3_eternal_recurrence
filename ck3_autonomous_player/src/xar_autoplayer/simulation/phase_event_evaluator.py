"""Strict stock phase-event AST evaluator and offline transition kernel.

This module executes only the normalized AST frozen for CK3 1.19.0.6.  It
does not execute Paradox script text, accept caller-defined opcodes, or claim
that its draw stream reproduces an already-running CK3 timeline.  Every AST
node and transition call is checked against an explicit schema before any
payload can advertise evaluator readiness.

The kernel is useful in two deliberately separate ways:

* payload admission evaluates trigger/chance expressions for every one of
  the 13 stock rows and preflights their effect trees against the observed
  root/``combat_side`` context;
* trial execution consumes an explicit sequence of 31-bit draws and writes
  character, wound, maim, death, participant, commander, variable, and
  recomputation state back into an isolated trial snapshot.

Event rows and random-list branches are source ordered.  ``random_side_knight``
replays the exact-build source-vector, shared-then-source predicate,
tail-swap-remove, signed-int32-weight, and one-draw selector algorithm.  A
production context is admitted only when its native candidate-source proof is
schema exact, digest bound to the side index, and its knight subsequence equals
the candidate rows.  Arithmetic is signed Q100000 with truncation toward zero
after each multiply/divide.  Same-day native refresh timing, battle-horizon
feedback from recorded side effects, and the original effect draw trace remain
independent fidelity gates and are never inferred here.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Callable, Mapping, Sequence

from .candidate_source_proof import (
    CANDIDATE_SOURCE_PROOF_POLICY,
    CandidateSourceProofError,
    normalize_candidate_source_proof,
)
from .combat_core import FIXED_SCALE, fixed_div, fixed_mul, trunc_div_toward_zero
from .combat_core import weighted_choice_index
from .phase_event_manifest import (
    STOCK_PHASE_EVENT_MANIFEST_SHA256,
    FrozenPhaseEventManifest,
    FrozenPhaseEventRow,
    load_stock_phase_event_manifest,
)


PHASE_EVENT_AST_EVALUATOR_SCHEMA_VERSION = 1
PHASE_EVENT_AST_EVALUATOR_VERSION = "ck3-1.19.0.6-stock-phase-event-ast-v3"

_MANIFEST_CANDIDATE_ORDER_POLICY = (
    "native_random_side_knight_candidate_order_unresolved"
)
_NATIVE_CANDIDATE_ORDER_POLICY = (
    "ccombat_side_knight_source_then_tail_swap_remove_v1"
)
_NATIVE_CANDIDATE_SOURCE_CONTRACT = {
    "class_vtable_rva": "0x41DE5C0",
    "materializer_rva": "0x19DD670",
    "source_vector": (
        "CCombatSide+0x40/+0x4C stride0x60; row+0x08 RegimentID; "
        "CRegiment+0x148 CharacterID; skip only -1"
    ),
    "materialize_call_schedule": (
        "source predicate effect+0x60, then effect+0x220 entries, each paired "
        "with shared predicate effect+0x140"
    ),
    "predicate_receiver_order": "shared_then_source_empty_is_true",
    "limit_compaction": "tail_swap_remove_recheck_same_index",
    "weight_helper_rva": "0x337B310",
    "selector_rva": "0x33E8D40",
    "weight_conversion": (
        "signed_q100000_truncate_toward_zero_then_increment_positive_remainder;"
        " store_int32_low_bits"
    ),
    "total_accumulator": "signed_int32_twos_complement_wrap",
    "positive_total_selection": (
        "draw31_mod_total_then_signed_int32_subtract_in_compacted_order;"
        " first_negative_else_index_0"
    ),
    "nonpositive_total_selection": "draw31_mod_candidate_count",
    "draw_count_with_candidates": 1,
}

_VALUE_OPS = (
    "all",
    "any",
    "ceiling",
    "compare",
    "const_bool",
    "const_fixed",
    "divide",
    "floor",
    "modifier",
    "modifier_sequence",
    "multiply",
    "not",
    "state_ref",
    "subtract",
)
_EFFECT_OPS = (
    "call_transition",
    "if",
    "random_branch",
    "random_list",
    "select_side_knight",
    "sequence",
)
_DIRECT_TRANSITIONS = (
    "add_trait",
    "berserker_kill_random_reason",
    "increase_wound_or_die",
    "kill_character",
    "knight_increase_prowess_chance",
    "maim_random",
    "no_op",
    "observational_only",
    "require_character_stat_recompute",
    "require_participant_detach_recompute",
    "set_variable",
    "shieldmaiden_kill_random_reason",
)
_INTERNAL_TRANSITIONS = (
    "add_prowess",
    "rank_blademaster",
    "schedule_delayed_event",
)
_SUPPORTED_TRANSITIONS_SOURCE_ORDER = (
    "no_op",
    "increase_wound_or_die",
    "maim_random",
    "kill_character",
    "knight_increase_prowess_chance",
    "berserker_kill_random_reason",
    "shieldmaiden_kill_random_reason",
    "add_trait",
    "add_prowess",
    "rank_blademaster",
    "set_variable",
    "schedule_delayed_event",
    "observational_only",
    "require_character_stat_recompute",
    "require_participant_detach_recompute",
)
_UNMODELED_BATTLE_HORIZON_EFFECTS = (
    "accolade_eligibility_interface_message",
    "battle_death_variables",
    "battle_event",
    "battle_location_variable",
    "cranial_trophy",
    "delayed_epilepsy_risk",
    "delayed_infection_or_treatment",
    "glory",
    "hold_court_delayed_event",
    "house_relation",
    "memory",
    "mongol_beheaded_variables",
    "prestige",
    "slain_list",
    "toast",
)
_OBSERVATIONAL_EFFECTS = frozenset(_UNMODELED_BATTLE_HORIZON_EFFECTS)
_DELAYED_OBSERVATIONAL_EFFECTS = frozenset(
    {
        "delayed_epilepsy_risk",
        "delayed_infection_or_treatment",
        "hold_court_delayed_event",
    }
)
_BATTLE_HORIZON_FEEDBACK_EVIDENCE = {
    "accolade_eligibility_interface_message": {
        "source_anchor": "00_knight_phase_events.txt:knight_qualify_for_accolade",
        "known_behavior": "interface effect is emitted after unlock-variable writes",
        "direct_132_ref_intersection": [],
        "unclosed_feedback": "engine effect callbacks and state writes are not traced",
        "required_closure_evidence": "native before/after callback write-set trace",
    },
    "battle_death_variables": {
        "source_anchor": "00_knight_phase_events.txt:knight_killed",
        "known_behavior": "death metadata variables are written immediately",
        "direct_132_ref_intersection": [],
        "unclosed_feedback": "variable consumers inside the remaining battle are not closed",
        "required_closure_evidence": "loaded variable-consumer graph plus same-battle trace",
    },
    "battle_event": {
        "source_anchor": "00_commander_phase_events.txt/00_knight_phase_events.txt:battle_event",
        "known_behavior": "native battle-event effect is invoked immediately",
        "direct_132_ref_intersection": [],
        "unclosed_feedback": "native before/after state and callback behavior are not traced",
        "required_closure_evidence": "native BattleEvent append and callback state delta",
    },
    "battle_location_variable": {
        "source_anchor": "00_knight_phase_events.txt:knight_becomes_incapable",
        "known_behavior": "new battle memory receives a location variable",
        "direct_132_ref_intersection": [],
        "unclosed_feedback": "memory-variable consumers inside the battle are not closed",
        "required_closure_evidence": "loaded memory callback and consumer trace",
    },
    "cranial_trophy": {
        "source_anchor": "00_knight_phase_events.txt:knight_killed",
        "known_behavior": "conditional cranial-trophy branch runs synchronously",
        "direct_132_ref_intersection": [
            "character trait/modifier state",
            "effective combat stats",
        ],
        "unclosed_feedback": "resulting character state and stat modifiers are not modeled",
        "required_closure_evidence": "exact effect AST plus character/combat-stat writeback",
    },
    "delayed_epilepsy_risk": {
        "source_anchor": "20_health_effects.txt:1055-1063",
        "known_behavior": "5-percent branch schedules trait_specific.2001 in 30-300 days",
        "direct_132_ref_intersection": ["future character trait/effective stats"],
        "minimum_delay_days": 30,
        "unclosed_feedback": "battle duration is not bounded below 30 days",
        "required_closure_evidence": "battle horizon bound or delayed-event transition model",
    },
    "delayed_infection_or_treatment": {
        "source_anchor": "20_health_effects.txt:1159-1167",
        "known_behavior": "wound treatment/infection event is scheduled in 2-3 days",
        "direct_132_ref_intersection": [
            "root.traits.wounded.rank_raw",
            "root.alive",
            "effective combat stats",
        ],
        "minimum_delay_days": 2,
        "unclosed_feedback": "battle duration is not bounded below 2 days",
        "required_closure_evidence": "delayed health-event AST and battle-day scheduler",
    },
    "glory": {
        "source_anchor": "00_knight_phase_events.txt:add_glory",
        "known_behavior": "accolade glory is mutated synchronously",
        "direct_132_ref_intersection": [
            "combat_side.ordered_commanders_and_knights_with_accolade_parameters",
            "selected_enemy_knight accolade parameter tiers",
            "effective knight contribution/advantage",
        ],
        "unclosed_feedback": "rank, accolade parameters, knight effectiveness, and advantage feedback are not recomputed",
        "required_closure_evidence": "glory rank-up AST plus same-day accolade/combat recompute trace",
    },
    "hold_court_delayed_event": {
        "source_anchor": "00_knight_phase_events.txt:1220-1235",
        "known_behavior": "variables are removed and hold_court.8053 is scheduled in 1 day",
        "direct_132_ref_intersection": ["root/employer hold-court variables"],
        "minimum_delay_days": 1,
        "unclosed_feedback": "one day is inside a possible battle horizon",
        "required_closure_evidence": "hold_court.8053 transition AST and day scheduler",
    },
    "house_relation": {
        "source_anchor": "00_commander_phase_events.txt:374-382",
        "known_behavior": "house relation is mutated synchronously",
        "direct_132_ref_intersection": [],
        "unclosed_feedback": "remaining effect predicates and stat feedback are not recomputed",
        "required_closure_evidence": "loaded house-relation callback/consumer graph and trace",
    },
    "memory": {
        "source_anchor": "00_knight_phase_events.txt:533-539",
        "known_behavior": "character memory is created synchronously",
        "direct_132_ref_intersection": [],
        "unclosed_feedback": "memory callbacks and battle-horizon consumers are not traced",
        "required_closure_evidence": "loaded memory callback/consumer graph and trace",
    },
    "mongol_beheaded_variables": {
        "source_anchor": "00_knight_phase_events.txt:knight_killed",
        "known_behavior": "conditional beheading metadata variables are written",
        "direct_132_ref_intersection": [],
        "unclosed_feedback": "variable consumers inside the remaining battle are not closed",
        "required_closure_evidence": "loaded variable-consumer graph plus same-battle trace",
    },
    "prestige": {
        "source_anchor": "00_commander_phase_events.txt/00_knight_phase_events.txt:add_prestige",
        "known_behavior": "character prestige is mutated synchronously",
        "direct_132_ref_intersection": [],
        "unclosed_feedback": "scripted callbacks and derived combat-state feedback are not traced",
        "required_closure_evidence": "native resource-effect callback and combat-state delta trace",
    },
    "slain_list": {
        "source_anchor": "00_knight_phase_events.txt:knight_killed",
        "known_behavior": "slain-character list is mutated synchronously",
        "direct_132_ref_intersection": [],
        "unclosed_feedback": "list consumers at later battle stages are not closed",
        "required_closure_evidence": "loaded list-consumer graph through battle teardown",
    },
    "toast": {
        "source_anchor": "00_commander_phase_events.txt/00_knight_phase_events.txt:send_interface_toast",
        "known_behavior": "native toast block is invoked around immediate gameplay effects",
        "direct_132_ref_intersection": [
            "nested modeled death/wound/trait transition",
        ],
        "unclosed_feedback": "engine callback behavior is not traced independently from modeled inner effects",
        "required_closure_evidence": "native wrapper-vs-inner before/after differential",
    },
}
_ACCOLADE_BRANCHES = (
    "skirmisher",
    "archer",
    "crossbowmen",
    "pike",
    "vanguard",
    "outrider",
    "lancer",
    "camelry",
    "elephantry",
    "horse_archer",
    "gunpowder",
    "fanatic",
    "valiant",
)
_MAIM_BRANCHES = (
    "one_legged_then_wound",
    "disfigured_then_wound",
    "one_eyed_then_wound",
    "maimed_plus_recently_maimed",
)

_EVALUATOR_CONTRACT = {
    "schema_version": PHASE_EVENT_AST_EVALUATOR_SCHEMA_VERSION,
    "version": PHASE_EVENT_AST_EVALUATOR_VERSION,
    "manifest_sha256": STOCK_PHASE_EVENT_MANIFEST_SHA256,
    "event_rows": {"total": 13, "commander": 4, "knight": 9},
    "scope": {
        "root": "observed_character",
        "combat_side": "observed_side_index",
        "owner": "absent",
    },
    "arithmetic": {
        "scale": FIXED_SCALE,
        "signed": True,
        "multiply_divide_rounding": "truncate_toward_zero_each_operation",
    },
    "selection": {
        "row_order": "manifest_source_order",
        "manifest_candidate_order_tag": _MANIFEST_CANDIDATE_ORDER_POLICY,
        "candidate_order": _NATIVE_CANDIDATE_ORDER_POLICY,
        "candidate_algorithm": _NATIVE_CANDIDATE_SOURCE_CONTRACT,
        "candidate_materialization_input": (
            "production_candidate_source_proof_schema_digest_roster_bound"
        ),
        "candidate_source_proof_policy": CANDIDATE_SOURCE_PROOF_POLICY,
        "random_list_order": "source_order",
        "candidate_weights": "signed_int32_no_clamp_or_skip",
        "draw_domain": "signed_nonnegative_31_bit",
    },
    "value_ops": list(_VALUE_OPS),
    "effect_ops": list(_EFFECT_OPS),
    "supported_transitions_source_order": list(
        _SUPPORTED_TRANSITIONS_SOURCE_ORDER
    ),
    "direct_transitions": list(_DIRECT_TRANSITIONS),
    "internal_transitions": list(_INTERNAL_TRANSITIONS),
    "unmodeled_battle_horizon_effects": list(
        _UNMODELED_BATTLE_HORIZON_EFFECTS
    ),
    "production_readiness_blockers": [
        "battle_horizon_effect_feedback_closure",
        "original_same_day_effect_trace",
    ],
    "payload_admission_requirements": [
        "production_candidate_source_proof_validation",
    ],
    "same_day_native_trace": "independent_gate_not_claimed",
}


def _canonical_digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest().upper()


PHASE_EVENT_AST_EVALUATOR_SHA256 = _canonical_digest(_EVALUATOR_CONTRACT)


class PhaseEventEvaluationError(ValueError):
    """The AST, context, draw tape, or transition is outside the contract."""


@dataclass(slots=True)
class _DrawTape:
    draws: tuple[int, ...]
    position: int = 0
    records: list[dict[str, object]] = field(default_factory=list)

    @classmethod
    def from_value(cls, value: Sequence[int]) -> "_DrawTape":
        if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
            raise PhaseEventEvaluationError("draw tape must be an integer sequence")
        draws: list[int] = []
        for index, item in enumerate(value):
            if isinstance(item, bool) or not isinstance(item, int) or not 0 <= item <= 0x7FFFFFFF:
                raise PhaseEventEvaluationError(
                    f"draw tape[{index}] must be a non-negative 31-bit integer"
                )
            draws.append(item)
        return cls(tuple(draws))

    def take(self, purpose: str, weights: Sequence[int]) -> int:
        normalized = tuple(_signed_int64(item, f"{purpose}.weights") for item in weights)
        if not any(item > 0 for item in normalized):
            return -1
        if self.position >= len(self.draws):
            raise PhaseEventEvaluationError(
                f"draw tape exhausted while selecting {purpose}"
            )
        draw = self.draws[self.position]
        self.position += 1
        selected = weighted_choice_index(normalized, draw, fallback=-1)
        if selected < 0:
            raise PhaseEventEvaluationError(
                f"positive weighted selection failed for {purpose}"
            )
        self.records.append(
            {
                "ordinal": self.position - 1,
                "purpose": purpose,
                "random31": draw,
                "weights_source_order": list(normalized),
                "selected_index": selected,
            }
        )
        return selected

    def take_native_side_knight(
        self,
        purpose: str,
        weights_raw: Sequence[int],
    ) -> int:
        """Replay 0x33E8D40's signed-int32 selector for a nonempty vector."""

        normalized_raw = tuple(
            _signed_int64(item, f"{purpose}.weights_raw") for item in weights_raw
        )
        if not normalized_raw:
            return -1
        if self.position >= len(self.draws):
            raise PhaseEventEvaluationError(
                f"draw tape exhausted while selecting {purpose}"
            )
        int_weights = tuple(
            _native_candidate_int_weight(item) for item in normalized_raw
        )
        total = 0
        for weight in int_weights:
            total = _wrap_signed_int32(total + weight)
        draw = self.draws[self.position]
        self.position += 1
        if total > 0:
            remainder = draw % total
            selected = 0
            for index, weight in enumerate(int_weights):
                remainder = _wrap_signed_int32(remainder - weight)
                if remainder < 0:
                    selected = index
                    break
            mode = "positive_total_weighted"
        else:
            selected = draw % len(int_weights)
            remainder = None
            mode = "nonpositive_total_uniform"
        self.records.append(
            {
                "ordinal": self.position - 1,
                "purpose": purpose,
                "random31": draw,
                "weights_raw_compacted_order": list(normalized_raw),
                "weights_int32_compacted_order": list(int_weights),
                "total_int32": total,
                "selection_mode": mode,
                "terminal_remainder_int32": remainder,
                "selected_index": selected,
            }
        )
        return selected


@dataclass(slots=True)
class PhaseEventTrialState:
    """Mutable isolated state used by one deterministic effect execution."""

    root_character_id: int
    root_source_army_id: int
    root_source_regiment_id: int | None
    phase_roles: tuple[str, ...]
    combat_side_index: int
    enemy_side_index: int
    refs: dict[str, object]
    candidates: list[dict[str, object]]
    combat_membership: list[int]
    enemy_membership: list[int]
    ordered_enemy_knights: list[int]
    candidate_source_proof: dict[str, object]
    candidate_materialization_input_ready: bool
    combat_commander_character_id: int | None
    selected_enemy_character_id: int | None
    root_variable_updates: dict[str, object]
    liege_variable_updates: dict[str, object]
    observational_effects: list[str]
    delayed_effects: list[str]
    transition_log: list[dict[str, object]]
    character_stat_recompute_ids: list[int]
    participant_detach_recompute_ids: list[int]
    side_strength_recompute_indices: list[int]
    advantage_state: dict[str, object]

    @classmethod
    def from_context(
        cls,
        context_value: object,
        *,
        advantage_model: object | None = None,
    ) -> "PhaseEventTrialState":
        context = _object(context_value, "phase event evaluation context")
        _require_keys(
            context,
            {
                "root_character_id",
                "root_source_army_id",
                "root_source_regiment_id",
                "phase_roles",
                "combat_side_index",
                "enemy_side_index",
                "native_state_refs",
                "offline_state_refs",
                "candidate_source_proof",
                "candidate_rows",
            },
            "phase event evaluation context",
        )
        root_id = _positive_int(context["root_character_id"], "root_character_id")
        source_army = _positive_int(
            context["root_source_army_id"], "root_source_army_id"
        )
        source_regiment_value = context["root_source_regiment_id"]
        source_regiment = (
            None
            if source_regiment_value is None
            else _positive_int(source_regiment_value, "root_source_regiment_id")
        )
        roles_value = _array(context["phase_roles"], "phase_roles")
        roles = tuple(_string(item, "phase_roles item") for item in roles_value)
        if not roles or len(roles) != len(set(roles)) or not set(roles) <= {
            "commander",
            "knight",
        }:
            raise PhaseEventEvaluationError("phase_roles is malformed")
        combat_index = _side_index(context["combat_side_index"], "combat_side_index")
        enemy_index = _side_index(context["enemy_side_index"], "enemy_side_index")
        if enemy_index != 1 - combat_index:
            raise PhaseEventEvaluationError("enemy side is not opposite combat_side")

        native_refs = copy.deepcopy(_object(context["native_state_refs"], "native refs"))
        offline_refs = copy.deepcopy(_object(context["offline_state_refs"], "offline refs"))
        overlap = set(native_refs) & set(offline_refs)
        if overlap:
            raise PhaseEventEvaluationError(
                f"native/offline state refs overlap: {sorted(overlap)!r}"
            )
        refs = {**native_refs, **offline_refs}
        if refs.get("root.exists") is not True:
            raise PhaseEventEvaluationError("phase-event root does not exist")
        if refs.get("combat_side.character_membership") is None or refs.get(
            "enemy_side.character_membership"
        ) is None:
            raise PhaseEventEvaluationError("phase-event side membership is missing")
        combat_membership = _id_list(
            refs["combat_side.character_membership"],
            "combat_side.character_membership",
        )
        enemy_membership = _id_list(
            refs["enemy_side.character_membership"],
            "enemy_side.character_membership",
        )
        if root_id not in combat_membership:
            raise PhaseEventEvaluationError("root is absent from combat_side membership")
        ordered_enemy = _id_list(
            refs.get("combat_side.ordered_enemy_knights"),
            "combat_side.ordered_enemy_knights",
        )
        try:
            candidate_source_proof = normalize_candidate_source_proof(
                context["candidate_source_proof"], side_index=enemy_index
            )
        except CandidateSourceProofError as error:
            raise PhaseEventEvaluationError(
                f"candidate-source proof rejected: {error}"
            ) from error
        proof_sources = _array(
            candidate_source_proof["ordered_sources"],
            "candidate_source_proof.ordered_sources",
        )
        proof_knights = [
            int(source["character_id"])
            for source in proof_sources
            if isinstance(source, dict) and source.get("role") == "knight"
        ]
        if proof_knights != ordered_enemy:
            raise PhaseEventEvaluationError(
                "candidate-source proof knight subsequence differs from "
                "combat_side enemy-knight order"
            )
        commander_value = refs.get("combat_side.commander")
        commander = (
            None
            if commander_value is None
            else _positive_int(commander_value, "combat_side.commander")
        )
        if commander is not None and commander not in combat_membership:
            raise PhaseEventEvaluationError(
                "combat_side commander is absent from side membership"
            )

        candidate_values = _array(context["candidate_rows"], "candidate_rows")
        candidates: list[dict[str, object]] = []
        seen: set[int] = set()
        for index, candidate_value in enumerate(candidate_values):
            name = f"candidate_rows[{index}]"
            candidate = _object(candidate_value, name)
            _require_keys(
                candidate,
                {"character_id", "candidate_refs", "selected_enemy_knight_refs"},
                name,
            )
            character_id = _positive_int(candidate["character_id"], f"{name}.character_id")
            if character_id in seen:
                raise PhaseEventEvaluationError("candidate_rows repeats a character")
            seen.add(character_id)
            candidate_refs = copy.deepcopy(
                _object(candidate["candidate_refs"], f"{name}.candidate_refs")
            )
            selected_refs = copy.deepcopy(
                _object(
                    candidate["selected_enemy_knight_refs"],
                    f"{name}.selected_enemy_knight_refs",
                )
            )
            candidates.append(
                {
                    "character_id": character_id,
                    "candidate_refs": candidate_refs,
                    "selected_enemy_knight_refs": selected_refs,
                }
            )
        if [row["character_id"] for row in candidates] != ordered_enemy:
            raise PhaseEventEvaluationError(
                "candidate_rows does not preserve combat_side enemy-knight order"
            )
        if any(character_id not in enemy_membership for character_id in ordered_enemy):
            raise PhaseEventEvaluationError(
                "enemy knight is absent from enemy-side membership"
            )

        return cls(
            root_character_id=root_id,
            root_source_army_id=source_army,
            root_source_regiment_id=source_regiment,
            phase_roles=roles,
            combat_side_index=combat_index,
            enemy_side_index=enemy_index,
            refs=refs,
            candidates=candidates,
            combat_membership=combat_membership,
            enemy_membership=enemy_membership,
            ordered_enemy_knights=ordered_enemy,
            candidate_source_proof=candidate_source_proof,
            candidate_materialization_input_ready=True,
            combat_commander_character_id=commander,
            selected_enemy_character_id=None,
            root_variable_updates={},
            liege_variable_updates={},
            observational_effects=[],
            delayed_effects=[],
            transition_log=[],
            character_stat_recompute_ids=[],
            participant_detach_recompute_ids=[],
            side_strength_recompute_indices=[],
            advantage_state=_initial_advantage_state(advantage_model),
        )

    def candidate(self, character_id: int) -> dict[str, object]:
        for row in self.candidates:
            if row["character_id"] == character_id:
                return row
        raise PhaseEventEvaluationError(
            f"selected enemy CharacterID {character_id} is not a candidate"
        )

    def resolve_ref(
        self,
        path: str,
        *,
        candidate: dict[str, object] | None = None,
    ) -> object:
        if candidate is not None:
            refs = _object(candidate["candidate_refs"], "candidate refs")
            if path in refs:
                return refs[path]
        if path.startswith("candidate.") or path.startswith("derived.candidate_"):
            raise PhaseEventEvaluationError(
                f"candidate state ref {path!r} has no candidate scope"
            )
        if path.startswith("selected_enemy_knight."):
            if self.selected_enemy_character_id is None:
                raise PhaseEventEvaluationError(
                    f"selected-enemy state ref {path!r} has no selected scope"
                )
            selected = self.candidate(self.selected_enemy_character_id)
            refs = _object(
                selected["selected_enemy_knight_refs"], "selected enemy refs"
            )
            if path not in refs:
                raise PhaseEventEvaluationError(
                    f"selected-enemy state ref {path!r} is missing"
                )
            return refs[path]
        if path not in self.refs:
            raise PhaseEventEvaluationError(f"state ref {path!r} is missing")
        return self.refs[path]

    def snapshot(self) -> dict[str, object]:
        selected = self.selected_enemy_character_id
        root_traits = {
            key.removeprefix("root.traits."): value
            for key, value in self.refs.items()
            if key.startswith("root.traits.")
            and isinstance(value, bool)
            and key != "root.traits.maim_injuries"
        }
        candidate_states = []
        for candidate in self.candidates:
            candidate_refs = _object(candidate["candidate_refs"], "candidate refs")
            selected_refs = _object(
                candidate["selected_enemy_knight_refs"], "selected enemy refs"
            )
            candidate_states.append(
                {
                    "character_id": candidate["character_id"],
                    "alive": candidate_refs.get("candidate.alive"),
                    "prowess_raw": selected_refs.get(
                        "selected_enemy_knight.skills.prowess_raw"
                    ),
                    "lifestyle_blademaster": _object(
                        selected_refs.get(
                            "selected_enemy_knight.traits_and_culture_for_blademaster"
                        ),
                        "selected blademaster container",
                    ).get("lifestyle_blademaster"),
                    "lifestyle_blademaster_xp_raw": _object(
                        selected_refs.get(
                            "selected_enemy_knight.traits_and_culture_for_blademaster"
                        ),
                        "selected blademaster container",
                    ).get("lifestyle_blademaster_xp_raw"),
                    "in_enemy_membership": candidate["character_id"]
                    in self.enemy_membership,
                }
            )
        result: dict[str, object] = {
            "scope": {
                "root_character_id": self.root_character_id,
                "combat_side_index": self.combat_side_index,
                "enemy_side_index": self.enemy_side_index,
                "owner": {"status": "absent", "value": None},
            },
            "root": {
                "alive": self.refs["root.alive"],
                "prowess_raw": self.refs["root.skills.prowess_raw"],
                "wounded_rank_raw": self.refs["root.traits.wounded.rank_raw"],
                "traits": root_traits,
                "lifestyle_blademaster": _object(
                    self.refs["root.traits_and_culture_for_blademaster"],
                    "root blademaster container",
                )["lifestyle_blademaster"],
                "lifestyle_blademaster_xp_raw": _object(
                    self.refs["root.traits_and_culture_for_blademaster"],
                    "root blademaster container",
                )["lifestyle_blademaster_xp_raw"],
                "variable_updates": copy.deepcopy(self.root_variable_updates),
                "liege_variable_updates": copy.deepcopy(
                    self.liege_variable_updates
                ),
            },
            "sides": {
                "combat_membership": list(self.combat_membership),
                "enemy_membership": list(self.enemy_membership),
                "ordered_enemy_knights": list(self.ordered_enemy_knights),
                "combat_commander_character_id": self.combat_commander_character_id,
            },
            "candidate_source_proof": {
                "policy": self.candidate_source_proof["policy"],
                "source_vector_equivalence": self.candidate_source_proof[
                    "source_vector_equivalence"
                ],
                "sequence_sha256": self.candidate_source_proof[
                    "sequence_sha256"
                ],
                "materialization_input_ready": (
                    self.candidate_materialization_input_ready
                ),
            },
            "selected_enemy_character_id": selected,
            "enemy_candidates": candidate_states,
            "recompute": {
                "character_stat_ids": list(self.character_stat_recompute_ids),
                "participant_detach_ids": list(
                    self.participant_detach_recompute_ids
                ),
                "side_strength_indices": list(
                    self.side_strength_recompute_indices
                ),
                "advantage": copy.deepcopy(self.advantage_state),
            },
            "observational_effects": list(self.observational_effects),
            "delayed_effects": list(self.delayed_effects),
        }
        result["state_sha256"] = _canonical_digest(result)
        return result


def audit_stock_phase_event_evaluator(
    manifest: FrozenPhaseEventManifest | None = None,
) -> dict[str, object]:
    """Prove that all trigger/chance/effect nodes have strict handlers."""

    selected = manifest or load_stock_phase_event_manifest()
    if selected.canonical_manifest_sha256 != STOCK_PHASE_EVENT_MANIFEST_SHA256:
        raise PhaseEventEvaluationError("phase-event evaluator manifest drifted")
    if len(selected.event_rows) != 13:
        raise PhaseEventEvaluationError("phase-event evaluator requires 13 rows")
    if tuple(selected.supported_transition_opcodes) != (
        _SUPPORTED_TRANSITIONS_SOURCE_ORDER
    ):
        raise PhaseEventEvaluationError("transition opcode source order drifted")
    supported = set(selected.supported_transition_opcodes)
    expected_supported = set(_DIRECT_TRANSITIONS) | set(_INTERNAL_TRANSITIONS)
    if supported != expected_supported:
        raise PhaseEventEvaluationError(
            "manifest transition opcodes differ from evaluator handlers"
        )

    direct_calls: set[str] = set()
    candidate_order_occurrences: list[dict[str, object]] = []
    feedback_effect_events: dict[str, list[str]] = {
        key: [] for key in _UNMODELED_BATTLE_HORIZON_EFFECTS
    }
    rows: list[dict[str, object]] = []
    total_nodes = 0
    type_counts = {"commander": 0, "knight": 0}
    for row in selected.event_rows:
        type_counts[row.event_type] += 1
        dependencies = frozenset(row.state_dependencies)
        validity_count = _audit_value_node(
            row.validity_ast,
            name=f"{row.key}.validity_ast",
            dependencies=dependencies,
        )
        chance_count = _audit_value_node(
            row.chance_ast,
            name=f"{row.key}.chance_ast",
            dependencies=dependencies,
        )
        effect_count = _audit_effect_node(
            row.effect_ast,
            name=f"{row.key}.effect_ast",
            dependencies=dependencies,
            direct_calls=direct_calls,
        )
        _collect_effect_fidelity_dependencies(
            row.effect_ast,
            event_key=row.key,
            name=f"{row.key}.effect_ast",
            candidate_order_occurrences=candidate_order_occurrences,
            feedback_effect_events=feedback_effect_events,
        )
        total_nodes += validity_count + chance_count + effect_count
        rows.append(
            {
                "global_load_index": row.global_load_index,
                "type_load_index": row.type_load_index,
                "key": row.key,
                "type": row.event_type,
                "validity_ast_sha256": _canonical_digest(
                    _thaw(row.validity_ast)
                ),
                "chance_ast_sha256": _canonical_digest(_thaw(row.chance_ast)),
                "effect_ast_sha256": _canonical_digest(_thaw(row.effect_ast)),
                "validity_node_count": validity_count,
                "chance_node_count": chance_count,
                "effect_node_count": effect_count,
                "validity_covered": True,
                "chance_covered": True,
                "effect_covered": True,
            }
        )
    if type_counts != {"commander": 4, "knight": 9}:
        raise PhaseEventEvaluationError("phase-event evaluator family count drifted")
    if direct_calls != set(_DIRECT_TRANSITIONS):
        raise PhaseEventEvaluationError(
            "direct transition call coverage differs from the strict handlers"
        )
    observed_feedback_effects = {
        key for key, event_keys in feedback_effect_events.items() if event_keys
    }
    if observed_feedback_effects != _OBSERVATIONAL_EFFECTS:
        raise PhaseEventEvaluationError(
            "battle-horizon feedback effect inventory drifted"
        )
    if not candidate_order_occurrences or any(
        row["manifest_order_policy"] != _MANIFEST_CANDIDATE_ORDER_POLICY
        or row["evaluator_order_policy"] != _NATIVE_CANDIDATE_ORDER_POLICY
        for row in candidate_order_occurrences
    ):
        raise PhaseEventEvaluationError(
            "native side-knight candidate algorithm contract drifted"
        )
    feedback_ledger: list[dict[str, object]] = []
    for effect in _UNMODELED_BATTLE_HORIZON_EFFECTS:
        evidence = copy.deepcopy(_BATTLE_HORIZON_FEEDBACK_EVIDENCE[effect])
        evidence.update(
            {
                "effect": effect,
                "event_keys_source_order": list(feedback_effect_events[effect]),
                "model_status": "record_only_not_state_complete",
                "battle_horizon_exclusion_proved": False,
                "feedback_ready": False,
            }
        )
        feedback_ledger.append(evidence)
    proof: dict[str, object] = {
        "schema_version": PHASE_EVENT_AST_EVALUATOR_SCHEMA_VERSION,
        "status": "structurally_covered_fidelity_blocked",
        "evaluator_version": PHASE_EVENT_AST_EVALUATOR_VERSION,
        "evaluator_sha256": PHASE_EVENT_AST_EVALUATOR_SHA256,
        "manifest_sha256": selected.canonical_manifest_sha256,
        "scope_semantics": {
            "root": "observed_character",
            "combat_side": "observed_side_index",
            "owner": {"status": "absent", "value": None},
        },
        "arithmetic": {
            "scale": FIXED_SCALE,
            "signed": True,
            "rounding": "truncate_toward_zero_after_each_operation",
        },
        "source_order": {
            "event_rows": True,
            "candidate_rows": False,
            "candidate_algorithm": True,
            "random_list_branches": True,
        },
        "candidate_materialization_and_order": {
            "policy": _NATIVE_CANDIDATE_ORDER_POLICY,
            "candidate_source_proof_policy": CANDIDATE_SOURCE_PROOF_POLICY,
            "manifest_order_policy": _MANIFEST_CANDIDATE_ORDER_POLICY,
            "native_source_contract": copy.deepcopy(
                _NATIVE_CANDIDATE_SOURCE_CONTRACT
            ),
            "occurrence_count": len(candidate_order_occurrences),
            "occurrences": candidate_order_occurrences,
            "algorithm_ready": True,
            "materialization_input_ready": False,
            "materialization_input_blocker": (
                "production_candidate_source_proof_payload_required"
            ),
            "ready": False,
        },
        "battle_horizon_feedback": {
            "effect_count": len(feedback_ledger),
            "effects": feedback_ledger,
            "ready": False,
        },
        "coverage": {
            "event_row_count": len(rows),
            "commander_row_count": type_counts["commander"],
            "knight_row_count": type_counts["knight"],
            "ast_node_count": total_nodes,
            "trigger_ast_rows_covered": len(rows),
            "chance_ast_rows_covered": len(rows),
            "effect_ast_rows_covered": len(rows),
            "direct_transition_count": len(direct_calls),
            "internal_transition_count": len(_INTERNAL_TRANSITIONS),
            "unsupported_nodes": [],
            "unsupported_effects": [],
            "structural_ready": True,
            "ready": False,
        },
        "rows": rows,
        "ast_evaluator_ready": False,
        "original_trace_ready": False,
    }
    proof["proof_sha256"] = _canonical_digest(proof)
    return proof


def _collect_effect_fidelity_dependencies(
    node_value: object,
    *,
    event_key: str,
    name: str,
    candidate_order_occurrences: list[dict[str, object]],
    feedback_effect_events: dict[str, list[str]],
) -> None:
    if isinstance(node_value, Mapping):
        op = node_value.get("op")
        if op == "select_side_knight":
            candidate_order_occurrences.append(
                {
                    "event_key": event_key,
                    "node_path": name,
                    "manifest_order_policy": node_value.get("order_policy"),
                    "evaluator_order_policy": _NATIVE_CANDIDATE_ORDER_POLICY,
                }
            )
        elif op == "call_transition" and node_value.get("key") == (
            "observational_only"
        ):
            args = _mapping(node_value.get("args"), f"{name}.args")
            effects = _sequence(args.get("effects"), f"{name}.args.effects")
            for effect_value in effects:
                effect = _string(effect_value, f"{name}.args.effects item")
                if effect not in feedback_effect_events:
                    raise PhaseEventEvaluationError(
                        f"{name} has no battle-horizon feedback ledger for {effect!r}"
                    )
                if event_key not in feedback_effect_events[effect]:
                    feedback_effect_events[effect].append(event_key)
        for key, child in node_value.items():
            if key == "op":
                continue
            _collect_effect_fidelity_dependencies(
                child,
                event_key=event_key,
                name=f"{name}.{key}",
                candidate_order_occurrences=candidate_order_occurrences,
                feedback_effect_events=feedback_effect_events,
            )
        return
    if isinstance(node_value, (tuple, list)):
        for index, child in enumerate(node_value):
            _collect_effect_fidelity_dependencies(
                child,
                event_key=event_key,
                name=f"{name}[{index}]",
                candidate_order_occurrences=candidate_order_occurrences,
                feedback_effect_events=feedback_effect_events,
            )


def evaluate_phase_event_contexts(
    contexts_value: object,
    *,
    manifest: FrozenPhaseEventManifest | None = None,
) -> dict[str, object]:
    """Evaluate all 13 rows for every observed root context."""

    selected = manifest or load_stock_phase_event_manifest()
    audit = audit_stock_phase_event_evaluator(selected)
    contexts = _array(contexts_value, "phase-event evaluation contexts")
    results: list[dict[str, object]] = []
    for index, context in enumerate(contexts):
        state = PhaseEventTrialState.from_context(context)
        row_results = [
            _evaluate_row(row, state, include_effect_preflight=True)
            for row in selected.event_rows
        ]
        if len(row_results) != 13:
            raise PhaseEventEvaluationError(
                f"evaluation context {index} did not evaluate all 13 rows"
            )
        results.append(
            {
                "root_character_id": state.root_character_id,
                "phase_roles": list(state.phase_roles),
                "combat_side_index": state.combat_side_index,
                "enemy_side_index": state.enemy_side_index,
                "owner_scope": {"status": "absent", "value": None},
                "candidate_source_proof": {
                    "policy": state.candidate_source_proof["policy"],
                    "source_vector_equivalence": state.candidate_source_proof[
                        "source_vector_equivalence"
                    ],
                    "sequence_sha256": state.candidate_source_proof[
                        "sequence_sha256"
                    ],
                },
                "candidate_materialization_input_ready": (
                    state.candidate_materialization_input_ready
                ),
                "rows": row_results,
            }
        )
    materialization_input_ready = bool(results) and all(
        result["candidate_materialization_input_ready"] is True
        for result in results
    )
    candidate_projection = copy.deepcopy(
        audit["candidate_materialization_and_order"]
    )
    candidate_projection.update(
        {
            "materialization_input_ready": materialization_input_ready,
            "materialization_input_blocker": (
                None
                if materialization_input_ready
                else "production_candidate_source_proof_payload_required"
            ),
            "production_proofs": [
                {
                    "enemy_side_index": result["enemy_side_index"],
                    **copy.deepcopy(result["candidate_source_proof"]),
                }
                for result in results
            ],
            "ready": bool(
                audit["candidate_materialization_and_order"]["algorithm_ready"]
                and materialization_input_ready
            ),
        }
    )
    projection: dict[str, object] = {
        "schema_version": PHASE_EVENT_AST_EVALUATOR_SCHEMA_VERSION,
        "status": "structurally_covered_fidelity_blocked",
        "scope": "hypothetical_precontact_root_plus_combat_side_owner_absent",
        "evaluator_version": PHASE_EVENT_AST_EVALUATOR_VERSION,
        "evaluator_sha256": PHASE_EVENT_AST_EVALUATOR_SHA256,
        "evaluator_proof_sha256": audit["proof_sha256"],
        "manifest_sha256": selected.canonical_manifest_sha256,
        "event_row_coverage": copy.deepcopy(audit["coverage"]),
        "candidate_materialization_and_order": candidate_projection,
        "battle_horizon_feedback": copy.deepcopy(
            audit["battle_horizon_feedback"]
        ),
        "context_count": len(results),
        "contexts": results,
        "ast_evaluator_ready": False,
        "original_trace_ready": False,
    }
    projection["projection_sha256"] = _canonical_digest(projection)
    return projection


def execute_phase_event_effect(
    context_value: object,
    *,
    event_key: str,
    draws: Sequence[int],
    advantage_model: object | None = None,
    manifest: FrozenPhaseEventManifest | None = None,
    require_valid: bool = True,
) -> dict[str, object]:
    """Execute one frozen row effect against an isolated trial snapshot."""

    selected = manifest or load_stock_phase_event_manifest()
    audit = audit_stock_phase_event_evaluator(selected)
    key = _string(event_key, "event_key")
    matches = [row for row in selected.event_rows if row.key == key]
    if len(matches) != 1:
        raise PhaseEventEvaluationError(f"unknown phase-event row {key!r}")
    row = matches[0]
    state = PhaseEventTrialState.from_context(
        context_value, advantage_model=advantage_model
    )
    evaluation = _evaluate_row(row, state, include_effect_preflight=True)
    if row.event_type not in state.phase_roles:
        raise PhaseEventEvaluationError(
            f"root CharacterID {state.root_character_id} has no {row.event_type} role"
        )
    if require_valid and evaluation["trigger_valid"] is not True:
        raise PhaseEventEvaluationError(f"phase-event row {key!r} is not valid")
    before = state.snapshot()
    tape = _DrawTape.from_value(draws)
    _execute_effect_node(
        row.effect_ast,
        state=state,
        tape=tape,
        name=f"{row.key}.effect_ast",
    )
    after = state.snapshot()
    result: dict[str, object] = {
        "schema_version": PHASE_EVENT_AST_EVALUATOR_SCHEMA_VERSION,
        "status": "offline_projection_applied_fidelity_blocked",
        "evaluator_version": PHASE_EVENT_AST_EVALUATOR_VERSION,
        "evaluator_sha256": PHASE_EVENT_AST_EVALUATOR_SHA256,
        "evaluator_proof_sha256": audit["proof_sha256"],
        "manifest_sha256": selected.canonical_manifest_sha256,
        "event": {
            "global_load_index": row.global_load_index,
            "type_load_index": row.type_load_index,
            "key": row.key,
            "type": row.event_type,
            "trigger_valid": evaluation["trigger_valid"],
            "chance_raw": evaluation["chance_raw"],
            "int_weight": evaluation["int_weight"],
        },
        "draw_tape": {
            "provided": list(tape.draws),
            "consumed_count": tape.position,
            "remaining_count": len(tape.draws) - tape.position,
            "records": copy.deepcopy(tape.records),
        },
        "before_state_sha256": before["state_sha256"],
        "after_state": after,
        "transition_log": copy.deepcopy(state.transition_log),
        "candidate_selection_algorithm_ready": True,
        "candidate_materialization_input_ready": (
            state.candidate_materialization_input_ready
        ),
        "candidate_materialization_and_order_ready": (
            state.candidate_materialization_input_ready
        ),
        "battle_horizon_feedback_ready": False,
        "ast_evaluator_ready": False,
        "original_trace_ready": False,
        "planner_usable": False,
        "active_attack_allowed": False,
    }
    result["result_sha256"] = _canonical_digest(result)
    return result


def _evaluate_row(
    row: FrozenPhaseEventRow,
    state: PhaseEventTrialState,
    *,
    include_effect_preflight: bool,
) -> dict[str, object]:
    trigger = _eval_bool(row.validity_ast, state=state, name=f"{row.key}.validity")
    chance = _eval_fixed(row.chance_ast, state=state, name=f"{row.key}.chance")
    int_weight = trunc_div_toward_zero(chance, FIXED_SCALE)
    role_applicable = row.event_type in state.phase_roles
    result: dict[str, object] = {
        "global_load_index": row.global_load_index,
        "type_load_index": row.type_load_index,
        "key": row.key,
        "type": row.event_type,
        "role_applicable": role_applicable,
        "trigger_expression_value": trigger,
        "trigger_valid": bool(role_applicable and trigger),
        "chance_raw": chance,
        "scale": FIXED_SCALE,
        "int_weight": int_weight,
        "selectable_int_weight": int_weight if role_applicable and trigger else 0,
    }
    if include_effect_preflight:
        result["effect_preflight"] = _preflight_effect_node(
            row.effect_ast,
            state=state,
            name=f"{row.key}.effect_ast",
        )
    return result


def _audit_value_node(
    node_value: object,
    *,
    name: str,
    dependencies: frozenset[str],
) -> int:
    node = _mapping(node_value, name)
    op = _string(node.get("op"), f"{name}.op")
    if op not in _VALUE_OPS:
        raise PhaseEventEvaluationError(f"{name} uses unsupported value op {op!r}")
    count = 1
    if op == "const_bool":
        _require_keys(node, {"op", "value"}, name)
        _bool(node["value"], f"{name}.value")
    elif op == "const_fixed":
        _require_keys(node, {"op", "raw", "scale"}, name)
        _signed_int64(node["raw"], f"{name}.raw")
        if node["scale"] != FIXED_SCALE:
            raise PhaseEventEvaluationError(f"{name}.scale is not Q100000")
    elif op == "state_ref":
        _require_keys(node, {"op", "path", "value_type"}, name)
        path = _string(node["path"], f"{name}.path")
        if path not in dependencies:
            raise PhaseEventEvaluationError(
                f"{name} state ref {path!r} is not a row dependency"
            )
        if node["value_type"] not in {"bool", "fixed_q100000"}:
            raise PhaseEventEvaluationError(f"{name}.value_type is unsupported")
    elif op in {"all", "any"}:
        _require_keys(node, {"op", "args"}, name)
        args = _sequence(node["args"], f"{name}.args")
        if not args:
            raise PhaseEventEvaluationError(f"{name}.args must not be empty")
        count += sum(
            _audit_value_node(
                child,
                name=f"{name}.args[{index}]",
                dependencies=dependencies,
            )
            for index, child in enumerate(args)
        )
    elif op == "not":
        _require_keys(node, {"op", "arg"}, name)
        count += _audit_value_node(
            node["arg"], name=f"{name}.arg", dependencies=dependencies
        )
    elif op == "compare":
        _require_keys(node, {"op", "operator", "left", "right"}, name)
        if node["operator"] not in {"==", "<", "<=", ">", ">="}:
            raise PhaseEventEvaluationError(f"{name}.operator is unsupported")
        count += _audit_value_node(
            node["left"], name=f"{name}.left", dependencies=dependencies
        )
        count += _audit_value_node(
            node["right"], name=f"{name}.right", dependencies=dependencies
        )
    elif op == "subtract":
        _require_keys(node, {"op", "left", "right"}, name)
        count += _audit_value_node(
            node["left"], name=f"{name}.left", dependencies=dependencies
        )
        count += _audit_value_node(
            node["right"], name=f"{name}.right", dependencies=dependencies
        )
    elif op in {"multiply", "divide"}:
        _require_keys(node, {"op", "left", "right", "rounding"}, name)
        if node["rounding"] != "truncate_toward_zero":
            raise PhaseEventEvaluationError(f"{name}.rounding is unsupported")
        count += _audit_value_node(
            node["left"], name=f"{name}.left", dependencies=dependencies
        )
        count += _audit_value_node(
            node["right"], name=f"{name}.right", dependencies=dependencies
        )
    elif op in {"floor", "ceiling"}:
        _require_keys(node, {"op", "value", "limit"}, name)
        count += _audit_value_node(
            node["value"], name=f"{name}.value", dependencies=dependencies
        )
        count += _audit_value_node(
            node["limit"], name=f"{name}.limit", dependencies=dependencies
        )
    elif op == "modifier_sequence":
        _require_keys(
            node,
            {
                "op",
                "initial",
                "rounding",
                "modifiers",
                "final_weight_conversion",
            },
            name,
        )
        if node["rounding"] != "q100000_truncate_toward_zero_after_each_operation":
            raise PhaseEventEvaluationError(f"{name}.rounding is unsupported")
        if node["final_weight_conversion"] != (
            "signed_q100000_divide_100000_truncate_toward_zero"
        ):
            raise PhaseEventEvaluationError(
                f"{name}.final_weight_conversion is unsupported"
            )
        count += _audit_value_node(
            node["initial"], name=f"{name}.initial", dependencies=dependencies
        )
        modifiers = _sequence(node["modifiers"], f"{name}.modifiers")
        count += sum(
            _audit_value_node(
                child,
                name=f"{name}.modifiers[{index}]",
                dependencies=dependencies,
            )
            for index, child in enumerate(modifiers)
        )
    elif op == "modifier":
        _require_keys(node, {"op", "mode", "value", "condition"}, name)
        if node["mode"] not in {"add", "factor"}:
            raise PhaseEventEvaluationError(f"{name}.mode is unsupported")
        count += _audit_value_node(
            node["value"], name=f"{name}.value", dependencies=dependencies
        )
        count += _audit_value_node(
            node["condition"],
            name=f"{name}.condition",
            dependencies=dependencies,
        )
    return count


def _audit_effect_node(
    node_value: object,
    *,
    name: str,
    dependencies: frozenset[str],
    direct_calls: set[str],
) -> int:
    node = _mapping(node_value, name)
    op = _string(node.get("op"), f"{name}.op")
    if op not in _EFFECT_OPS:
        raise PhaseEventEvaluationError(f"{name} uses unsupported effect op {op!r}")
    count = 1
    if op == "sequence":
        allowed = {"op", "steps"}
        if "dependencies" in node:
            allowed.add("dependencies")
            _validate_dependencies(node["dependencies"], dependencies, name)
        _require_keys(node, allowed, name)
        steps = _sequence(node["steps"], f"{name}.steps")
        if not steps:
            raise PhaseEventEvaluationError(f"{name}.steps must not be empty")
        count += sum(
            _audit_effect_node(
                child,
                name=f"{name}.steps[{index}]",
                dependencies=dependencies,
                direct_calls=direct_calls,
            )
            for index, child in enumerate(steps)
        )
    elif op == "if":
        _require_keys(node, {"op", "condition", "then", "else"}, name)
        count += _audit_value_node(
            node["condition"], name=f"{name}.condition", dependencies=dependencies
        )
        count += _audit_effect_node(
            node["then"],
            name=f"{name}.then",
            dependencies=dependencies,
            direct_calls=direct_calls,
        )
        count += _audit_effect_node(
            node["else"],
            name=f"{name}.else",
            dependencies=dependencies,
            direct_calls=direct_calls,
        )
    elif op == "select_side_knight":
        _require_keys(
            node,
            {"op", "side", "filter", "weight", "order_policy", "on_selected"},
            name,
        )
        if (
            node["side"] != "enemy"
            or node["order_policy"] != _MANIFEST_CANDIDATE_ORDER_POLICY
        ):
            raise PhaseEventEvaluationError(f"{name} selection policy drifted")
        count += _audit_value_node(
            node["filter"], name=f"{name}.filter", dependencies=dependencies
        )
        count += _audit_value_node(
            node["weight"], name=f"{name}.weight", dependencies=dependencies
        )
        count += _audit_effect_node(
            node["on_selected"],
            name=f"{name}.on_selected",
            dependencies=dependencies,
            direct_calls=direct_calls,
        )
    elif op == "random_list":
        _require_keys(node, {"op", "order_policy", "branches"}, name)
        if node["order_policy"] != "source_order":
            raise PhaseEventEvaluationError(f"{name}.order_policy drifted")
        branches = _sequence(node["branches"], f"{name}.branches")
        if not branches:
            raise PhaseEventEvaluationError(f"{name}.branches must not be empty")
        count += sum(
            _audit_effect_node(
                branch,
                name=f"{name}.branches[{index}]",
                dependencies=dependencies,
                direct_calls=direct_calls,
            )
            for index, branch in enumerate(branches)
        )
    elif op == "random_branch":
        _require_keys(
            node,
            {"op", "key", "base_weight", "validity", "weight", "effect"},
            name,
        )
        _string(node["key"], f"{name}.key")
        count += _audit_value_node(
            node["base_weight"],
            name=f"{name}.base_weight",
            dependencies=dependencies,
        )
        count += _audit_value_node(
            node["validity"], name=f"{name}.validity", dependencies=dependencies
        )
        count += _audit_value_node(
            node["weight"], name=f"{name}.weight", dependencies=dependencies
        )
        count += _audit_effect_node(
            node["effect"],
            name=f"{name}.effect",
            dependencies=dependencies,
            direct_calls=direct_calls,
        )
    elif op == "call_transition":
        _require_keys(node, {"op", "key", "args", "dependencies"}, name)
        key = _string(node["key"], f"{name}.key")
        if key not in _DIRECT_TRANSITIONS:
            raise PhaseEventEvaluationError(
                f"{name} calls unsupported direct transition {key!r}"
            )
        _validate_dependencies(node["dependencies"], dependencies, name)
        _validate_transition_args(key, node["args"], name=name)
        direct_calls.add(key)
    return count


def _validate_transition_args(key: str, value: object, *, name: str) -> None:
    args = _mapping(value, f"{name}.args")
    plain = _thaw(args)
    if key == "no_op":
        if plain not in ({}, {"empty_effect_maps_to_null_event": True}):
            raise PhaseEventEvaluationError(f"{name}.args is not a known no-op")
    elif key == "increase_wound_or_die":
        if plain != {"target": "root", "reason": "fight"}:
            raise PhaseEventEvaluationError(f"{name}.args wound signature drifted")
    elif key == "maim_random":
        if plain != {
            "target": "root",
            "source_order_weights": [400000, 200000, 400000, 400000],
            "scale": FIXED_SCALE,
            "branches": list(_MAIM_BRANCHES),
        }:
            raise PhaseEventEvaluationError(f"{name}.args maim signature drifted")
    elif key == "kill_character":
        allowed = (
            {
                "target": "root",
                "reason": "death_battle",
                "killer": "selected_enemy_knight_or_null",
            },
            {
                "target": "root",
                "reason": "death_battle",
                "killer": "selected_enemy_knight_if_both_alive_else_null",
            },
            {
                "target": "selected_enemy_knight",
                "reason": "death_head_ripped_off",
                "killer": "root",
            },
        )
        if plain not in allowed:
            raise PhaseEventEvaluationError(f"{name}.args kill signature drifted")
    elif key == "knight_increase_prowess_chance":
        if plain not in (
            {"target": "root"},
            {"target": "selected_enemy_knight"},
        ):
            raise PhaseEventEvaluationError(f"{name}.args prowess signature drifted")
    elif key == "berserker_kill_random_reason":
        if plain != {
            "target": "selected_enemy_knight",
            "source_order_base_weights_raw": [
                1000000,
                1000000,
                1000000,
                1000000,
                1000000,
                1000000,
                100000,
                1000000,
                1000000,
            ],
            "fear_branch": {
                "invalid_if_brave": True,
                "add_raw_if_craven": 9900000,
                "scale": FIXED_SCALE,
            },
        }:
            raise PhaseEventEvaluationError(
                f"{name}.args berserker-kill signature drifted"
            )
    elif key == "shieldmaiden_kill_random_reason":
        if plain != {
            "target": "selected_enemy_knight",
            "source_order_weights_raw": [1000000] * 5,
            "scale": FIXED_SCALE,
        }:
            raise PhaseEventEvaluationError(
                f"{name}.args shieldmaiden-kill signature drifted"
            )
    elif key == "add_trait":
        if plain not in (
            {"target": "root", "trait": "berserker"},
            {"target": "root", "trait": "incapable"},
        ):
            raise PhaseEventEvaluationError(f"{name}.args trait signature drifted")
    elif key in {
        "require_character_stat_recompute",
        "require_participant_detach_recompute",
    }:
        if plain.get("target") not in {"root", "selected_enemy_knight"} or plain != {
            "target": plain.get("target"),
            "timing": "same_day_unverified",
        }:
            raise PhaseEventEvaluationError(f"{name}.args recompute signature drifted")
    elif key == "set_variable":
        root_attributes = {
            "target": "root",
            "value": True,
        }
        if plain == {
            "target": "root.liege",
            "name": "accolade_progress",
            "value_raw": 0,
            "scale": FIXED_SCALE,
        }:
            return
        if (
            set(plain) == {"target", "name", "value"}
            and plain.get("target") == root_attributes["target"]
            and plain.get("value") is True
            and plain.get("name")
            in {f"{branch}_attribute_unlock" for branch in _ACCOLADE_BRANCHES}
        ):
            return
        raise PhaseEventEvaluationError(f"{name}.args variable signature drifted")
    elif key == "observational_only":
        if set(plain) != {"effects"} or not isinstance(plain["effects"], list):
            raise PhaseEventEvaluationError(
                f"{name}.args observational schema drifted"
            )
        effects = plain["effects"]
        if not effects or len(effects) != len(set(effects)) or not set(effects) <= _OBSERVATIONAL_EFFECTS:
            raise PhaseEventEvaluationError(
                f"{name}.args contains unsupported observational effects"
            )


def _eval_bool(
    node_value: object,
    *,
    state: PhaseEventTrialState,
    name: str,
    candidate: dict[str, object] | None = None,
) -> bool:
    value = _eval_value(node_value, state=state, name=name, candidate=candidate)
    return _bool(value, name)


def _eval_fixed(
    node_value: object,
    *,
    state: PhaseEventTrialState,
    name: str,
    candidate: dict[str, object] | None = None,
) -> int:
    value = _eval_value(node_value, state=state, name=name, candidate=candidate)
    return _signed_int64(value, name)


def _eval_value(
    node_value: object,
    *,
    state: PhaseEventTrialState,
    name: str,
    candidate: dict[str, object] | None,
) -> object:
    node = _mapping(node_value, name)
    op = _string(node.get("op"), f"{name}.op")
    if op == "const_bool":
        return _bool(node.get("value"), f"{name}.value")
    if op == "const_fixed":
        if node.get("scale") != FIXED_SCALE:
            raise PhaseEventEvaluationError(f"{name}.scale is not Q100000")
        return _signed_int64(node.get("raw"), f"{name}.raw")
    if op == "state_ref":
        path = _string(node.get("path"), f"{name}.path")
        value = state.resolve_ref(path, candidate=candidate)
        value_type = node.get("value_type")
        if value_type == "bool":
            return _bool(value, path)
        if value_type == "fixed_q100000":
            return _signed_int64(value, path)
        raise PhaseEventEvaluationError(f"{name}.value_type is unsupported")
    if op == "all":
        for index, child in enumerate(_sequence(node.get("args"), f"{name}.args")):
            if not _eval_bool(
                child,
                state=state,
                name=f"{name}.args[{index}]",
                candidate=candidate,
            ):
                return False
        return True
    if op == "any":
        for index, child in enumerate(_sequence(node.get("args"), f"{name}.args")):
            if _eval_bool(
                child,
                state=state,
                name=f"{name}.args[{index}]",
                candidate=candidate,
            ):
                return True
        return False
    if op == "not":
        return not _eval_bool(
            node.get("arg"), state=state, name=f"{name}.arg", candidate=candidate
        )
    if op == "compare":
        left = _eval_value(
            node.get("left"), state=state, name=f"{name}.left", candidate=candidate
        )
        right = _eval_value(
            node.get("right"), state=state, name=f"{name}.right", candidate=candidate
        )
        if isinstance(left, bool) != isinstance(right, bool):
            raise PhaseEventEvaluationError(f"{name} compares unlike value types")
        operator = node.get("operator")
        if operator == "==":
            return left == right
        if isinstance(left, bool) or isinstance(right, bool):
            raise PhaseEventEvaluationError(f"{name} orders boolean values")
        left_int = _signed_int64(left, f"{name}.left")
        right_int = _signed_int64(right, f"{name}.right")
        if operator == "<":
            return left_int < right_int
        if operator == "<=":
            return left_int <= right_int
        if operator == ">":
            return left_int > right_int
        if operator == ">=":
            return left_int >= right_int
        raise PhaseEventEvaluationError(f"{name}.operator is unsupported")
    if op == "subtract":
        left = _eval_fixed(
            node.get("left"), state=state, name=f"{name}.left", candidate=candidate
        )
        right = _eval_fixed(
            node.get("right"), state=state, name=f"{name}.right", candidate=candidate
        )
        return _signed_int64(left - right, name)
    if op == "multiply":
        left = _eval_fixed(
            node.get("left"), state=state, name=f"{name}.left", candidate=candidate
        )
        right = _eval_fixed(
            node.get("right"), state=state, name=f"{name}.right", candidate=candidate
        )
        return _signed_int64(fixed_mul(left, right), name)
    if op == "divide":
        left = _eval_fixed(
            node.get("left"), state=state, name=f"{name}.left", candidate=candidate
        )
        right = _eval_fixed(
            node.get("right"), state=state, name=f"{name}.right", candidate=candidate
        )
        if right == 0:
            raise PhaseEventEvaluationError(f"{name} divides by zero")
        return _signed_int64(fixed_div(left, right), name)
    if op in {"floor", "ceiling"}:
        value = _eval_fixed(
            node.get("value"), state=state, name=f"{name}.value", candidate=candidate
        )
        limit = _eval_fixed(
            node.get("limit"), state=state, name=f"{name}.limit", candidate=candidate
        )
        return max(value, limit) if op == "floor" else min(value, limit)
    if op == "modifier_sequence":
        result = _eval_fixed(
            node.get("initial"), state=state, name=f"{name}.initial", candidate=candidate
        )
        for index, modifier_value in enumerate(
            _sequence(node.get("modifiers"), f"{name}.modifiers")
        ):
            modifier = _mapping(modifier_value, f"{name}.modifiers[{index}]")
            if modifier.get("op") != "modifier":
                raise PhaseEventEvaluationError(
                    f"{name}.modifiers[{index}] is not a modifier"
                )
            if not _eval_bool(
                modifier.get("condition"),
                state=state,
                name=f"{name}.modifiers[{index}].condition",
                candidate=candidate,
            ):
                continue
            value = _eval_fixed(
                modifier.get("value"),
                state=state,
                name=f"{name}.modifiers[{index}].value",
                candidate=candidate,
            )
            if modifier.get("mode") == "add":
                result = _signed_int64(result + value, name)
            elif modifier.get("mode") == "factor":
                result = _signed_int64(fixed_mul(result, value), name)
            else:
                raise PhaseEventEvaluationError(
                    f"{name}.modifiers[{index}].mode is unsupported"
                )
        return result
    raise PhaseEventEvaluationError(f"{name} uses unsupported value op {op!r}")


def _preflight_effect_node(
    node_value: object,
    *,
    state: PhaseEventTrialState,
    name: str,
) -> dict[str, object]:
    node = _mapping(node_value, name)
    op = _string(node.get("op"), f"{name}.op")
    if op == "call_transition":
        return {"op": op, "key": node["key"], "covered": True}
    if op == "sequence":
        return {
            "op": op,
            "steps": [
                _preflight_effect_node(
                    child, state=state, name=f"{name}.steps[{index}]"
                )
                for index, child in enumerate(
                    _sequence(node.get("steps"), f"{name}.steps")
                )
            ],
            "covered": True,
        }
    if op == "if":
        # An if nested under on_selected is evaluated while each candidate is
        # temporarily bound.  Outside that scope all current stock if nodes use
        # only root/derived refs.
        condition = _eval_bool(
            node.get("condition"), state=state, name=f"{name}.condition"
        )
        branch_key = "then" if condition else "else"
        return {
            "op": op,
            "condition": condition,
            "selected_branch": branch_key,
            "branch": _preflight_effect_node(
                node[branch_key], state=state, name=f"{name}.{branch_key}"
            ),
            "covered": True,
        }
    if op == "select_side_knight":
        eligible, weights_raw, materialization = (
            _materialize_side_knight_candidates(node, state=state, name=name)
        )
        candidate_rows: list[dict[str, object]] = []
        for candidate, weight in zip(eligible, weights_raw, strict=True):
            previous = state.selected_enemy_character_id
            state.selected_enemy_character_id = int(candidate["character_id"])
            selected_preflight = _preflight_effect_node(
                node.get("on_selected"),
                state=state,
                name=f"{name}.on_selected",
            )
            state.selected_enemy_character_id = previous
            candidate_rows.append(
                {
                    "character_id": candidate["character_id"],
                    "weight_raw": weight,
                    "weight_int32": _native_candidate_int_weight(weight),
                    "on_selected": selected_preflight,
                }
            )
        return {
            "op": op,
            "side": "enemy",
            "order_policy": _NATIVE_CANDIDATE_ORDER_POLICY,
            "algorithm_ready": True,
            "materialization_input_ready": (
                state.candidate_materialization_input_ready
            ),
            "materialization_and_order_ready": (
                state.candidate_materialization_input_ready
            ),
            "materialization": materialization,
            "post_compaction_candidates": candidate_rows,
            "covered": True,
        }
    if op == "random_list":
        branches = []
        for index, branch_value in enumerate(
            _sequence(node.get("branches"), f"{name}.branches")
        ):
            branch = _mapping(branch_value, f"{name}.branches[{index}]")
            valid = _eval_bool(
                branch.get("validity"),
                state=state,
                name=f"{name}.branches[{index}].validity",
            )
            base = _eval_fixed(
                branch.get("base_weight"),
                state=state,
                name=f"{name}.branches[{index}].base_weight",
            )
            factor = _eval_fixed(
                branch.get("weight"),
                state=state,
                name=f"{name}.branches[{index}].weight",
            )
            branches.append(
                {
                    "key": branch["key"],
                    "valid": valid,
                    "weight_raw": fixed_mul(base, factor) if valid else 0,
                }
            )
        return {
            "op": op,
            "order": "source_order",
            "branches": branches,
            "covered": True,
        }
    raise PhaseEventEvaluationError(f"{name} uses unsupported effect op {op!r}")


def _execute_effect_node(
    node_value: object,
    *,
    state: PhaseEventTrialState,
    tape: _DrawTape,
    name: str,
) -> None:
    node = _mapping(node_value, name)
    op = _string(node.get("op"), f"{name}.op")
    if op == "call_transition":
        _execute_transition(
            str(node["key"]), _mapping(node["args"], f"{name}.args"), state, tape
        )
        return
    if op == "sequence":
        for index, child in enumerate(
            _sequence(node.get("steps"), f"{name}.steps")
        ):
            _execute_effect_node(
                child, state=state, tape=tape, name=f"{name}.steps[{index}]"
            )
        return
    if op == "if":
        condition = _eval_bool(
            node.get("condition"), state=state, name=f"{name}.condition"
        )
        branch = "then" if condition else "else"
        _execute_effect_node(
            node[branch], state=state, tape=tape, name=f"{name}.{branch}"
        )
        return
    if op == "select_side_knight":
        eligible, weights_raw, materialization = (
            _materialize_side_knight_candidates(node, state=state, name=name)
        )
        selected_index = tape.take_native_side_knight(
            f"{name}:enemy_knight", weights_raw
        )
        if selected_index < 0:
            state.transition_log.append(
                {
                    "transition": "select_side_knight",
                    "selected_character_id": None,
                    "order_policy": _NATIVE_CANDIDATE_ORDER_POLICY,
                    "materialization": materialization,
                    "eligible_character_ids_compacted_order": [],
                    "weights_raw_compacted_order": [],
                    "weights_int32_compacted_order": [],
                }
            )
            return
        selected = eligible[selected_index]
        state.selected_enemy_character_id = int(selected["character_id"])
        state.transition_log.append(
            {
                "transition": "select_side_knight",
                "selected_character_id": state.selected_enemy_character_id,
                "order_policy": _NATIVE_CANDIDATE_ORDER_POLICY,
                "materialization": materialization,
                "eligible_character_ids_compacted_order": [
                    row["character_id"] for row in eligible
                ],
                "weights_raw_compacted_order": list(weights_raw),
                "weights_int32_compacted_order": [
                    _native_candidate_int_weight(weight) for weight in weights_raw
                ],
            }
        )
        _execute_effect_node(
            node.get("on_selected"),
            state=state,
            tape=tape,
            name=f"{name}.on_selected",
        )
        return
    if op == "random_list":
        branches = _sequence(node.get("branches"), f"{name}.branches")
        weights: list[int] = []
        for index, branch_value in enumerate(branches):
            branch = _mapping(branch_value, f"{name}.branches[{index}]")
            valid = _eval_bool(
                branch.get("validity"),
                state=state,
                name=f"{name}.branches[{index}].validity",
            )
            if not valid:
                weights.append(0)
                continue
            base = _eval_fixed(
                branch.get("base_weight"),
                state=state,
                name=f"{name}.branches[{index}].base_weight",
            )
            factor = _eval_fixed(
                branch.get("weight"),
                state=state,
                name=f"{name}.branches[{index}].weight",
            )
            weights.append(_signed_int64(fixed_mul(base, factor), name))
        selected_index = tape.take(f"{name}:random_list", weights)
        if selected_index < 0:
            state.transition_log.append(
                {
                    "transition": "random_list",
                    "selected_branch": None,
                    "weights_source_order": weights,
                }
            )
            return
        selected = _mapping(branches[selected_index], f"{name}.branches[{selected_index}]")
        state.transition_log.append(
            {
                "transition": "random_list",
                "selected_branch": selected["key"],
                "weights_source_order": weights,
            }
        )
        _execute_effect_node(
            selected.get("effect"),
            state=state,
            tape=tape,
            name=f"{name}.branches[{selected_index}].effect",
        )
        return
    raise PhaseEventEvaluationError(f"{name} uses unsupported effect op {op!r}")


def _materialize_side_knight_candidates(
    node: Mapping[str, Any],
    *,
    state: PhaseEventTrialState,
    name: str,
) -> tuple[list[dict[str, object]], list[int], dict[str, object]]:
    """Apply 0x3388410/0x19F4760 tail-swap filtering to observed rows."""

    source = list(state.candidates)
    source_ids = [int(row["character_id"]) for row in source]

    def normalized_filter(candidate: dict[str, object]) -> bool:
        return _eval_bool(
            node.get("filter"),
            state=state,
            name=f"{name}.filter",
            candidate=candidate,
        )

    candidates, evaluations, predicate_log = _native_tail_swap_filter(
        source,
        # The frozen stock AST has one normalized combined limit expression.
        # The exact native receiver ordering is still replayed: its separately
        # empty shared receiver evaluates true before that combined projection.
        shared_predicate=lambda _candidate: True,
        source_predicate=normalized_filter,
    )

    weights_raw = [
        _eval_fixed(
            node.get("weight"),
            state=state,
            name=f"{name}.weight",
            candidate=candidate,
        )
        for candidate in candidates
    ]
    trace: dict[str, object] = {
        "source_character_ids_observed_v3": source_ids,
        "candidate_source_proof_policy": state.candidate_source_proof[
            "policy"
        ],
        "candidate_source_sequence_sha256": state.candidate_source_proof[
            "sequence_sha256"
        ],
        "source_vector_equivalence_ready": (
            state.candidate_materialization_input_ready
        ),
        "predicate_receiver_order": "shared_then_source_empty_is_true",
        "shared_predicate_projection": "empty_true",
        "source_predicate_projection": "normalized_combined_filter_ast",
        "predicate_log": predicate_log,
        "limit_evaluations": evaluations,
        "post_compaction_character_ids": [
            int(row["character_id"]) for row in candidates
        ],
        "weights_raw_compacted_order": list(weights_raw),
        "weights_int32_compacted_order": [
            _native_candidate_int_weight(weight) for weight in weights_raw
        ],
    }
    return candidates, weights_raw, trace


def _native_tail_swap_filter(
    source: Sequence[dict[str, object]],
    *,
    shared_predicate: Callable[[dict[str, object]], bool],
    source_predicate: Callable[[dict[str, object]], bool],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[str]]:
    """Mirror shared-first/source-second 0x19F4760 compaction."""

    candidates = list(source)
    evaluations: list[dict[str, object]] = []
    predicate_log: list[str] = []
    index = 0
    while index < len(candidates):
        candidate = candidates[index]
        character_id = int(candidate["character_id"])
        predicate_log.append(f"shared:{character_id}")
        shared_valid = bool(shared_predicate(candidate))
        source_valid = False
        if shared_valid:
            predicate_log.append(f"source:{character_id}")
            source_valid = bool(source_predicate(candidate))
        valid = shared_valid and source_valid
        if valid:
            evaluations.append(
                {
                    "index": index,
                    "character_id": character_id,
                    "shared_predicate": True,
                    "source_predicate": True,
                    "action": "keep_advance",
                }
            )
            index += 1
            continue
        tail_id = int(candidates[-1]["character_id"])
        evaluations.append(
            {
                "index": index,
                "character_id": character_id,
                "shared_predicate": shared_valid,
                "source_predicate": source_valid if shared_valid else None,
                "action": "tail_swap_remove_recheck_same_index",
                "replacement_character_id": (
                    tail_id if index != len(candidates) - 1 else None
                ),
            }
        )
        candidates[index] = candidates[-1]
        candidates.pop()
    return candidates, evaluations, predicate_log


def _execute_transition(
    key: str,
    args: Mapping[str, Any],
    state: PhaseEventTrialState,
    tape: _DrawTape,
) -> None:
    if key == "no_op":
        state.transition_log.append({"transition": key, "applied": False})
    elif key == "observational_only":
        effects = list(_sequence(args.get("effects"), "observational effects"))
        for effect in effects:
            if effect not in state.observational_effects:
                state.observational_effects.append(str(effect))
            if effect in _DELAYED_OBSERVATIONAL_EFFECTS and effect not in state.delayed_effects:
                state.delayed_effects.append(str(effect))
        state.transition_log.append(
            {"transition": key, "effects": effects, "applied": True}
        )
    elif key == "increase_wound_or_die":
        _increase_wound_or_die(state, target="root", reason="fight")
    elif key == "maim_random":
        _maim_random(state, tape)
    elif key == "kill_character":
        killer: int | None = None
        killer_policy = args.get("killer")
        if killer_policy == "root":
            killer = state.root_character_id
        elif killer_policy == "selected_enemy_knight_or_null":
            killer = state.selected_enemy_character_id
        elif killer_policy == "selected_enemy_knight_if_both_alive_else_null":
            selected = state.selected_enemy_character_id
            if (
                selected is not None
                and _target_alive(state, "root")
                and _target_alive(state, "selected_enemy_knight")
            ):
                killer = selected
        _kill_character(
            state,
            target=str(args.get("target")),
            reason=str(args.get("reason")),
            killer_character_id=killer,
        )
    elif key == "knight_increase_prowess_chance":
        _knight_increase_prowess_chance(
            state, tape, target=str(args.get("target"))
        )
    elif key == "berserker_kill_random_reason":
        _berserker_kill_random_reason(state, tape)
    elif key == "shieldmaiden_kill_random_reason":
        _shieldmaiden_kill_random_reason(state, tape)
    elif key == "add_trait":
        _add_trait(state, target=str(args.get("target")), trait=str(args.get("trait")))
    elif key == "require_character_stat_recompute":
        _require_character_recompute(state, target=str(args.get("target")))
    elif key == "require_participant_detach_recompute":
        _detach_character(state, target=str(args.get("target")))
    elif key == "set_variable":
        _set_variable(state, args)
    else:
        raise PhaseEventEvaluationError(f"transition {key!r} has no executor")


def _target_character_id(state: PhaseEventTrialState, target: str) -> int:
    if target == "root":
        return state.root_character_id
    if target == "selected_enemy_knight":
        if state.selected_enemy_character_id is None:
            raise PhaseEventEvaluationError("selected enemy target is absent")
        return state.selected_enemy_character_id
    raise PhaseEventEvaluationError(f"unsupported character target {target!r}")


def _target_alive(state: PhaseEventTrialState, target: str) -> bool:
    if target == "root":
        return _bool(state.refs["root.alive"], "root.alive")
    selected_id = _target_character_id(state, target)
    candidate = state.candidate(selected_id)
    return _bool(
        _object(candidate["candidate_refs"], "candidate refs")["candidate.alive"],
        "candidate.alive",
    )


def _set_target_alive(
    state: PhaseEventTrialState, target: str, alive: bool
) -> None:
    if target == "root":
        state.refs["root.alive"] = alive
        return
    candidate = state.candidate(_target_character_id(state, target))
    _object(candidate["candidate_refs"], "candidate refs")["candidate.alive"] = alive
    _object(candidate["selected_enemy_knight_refs"], "selected enemy refs")[
        "selected_enemy_knight.alive"
    ] = alive


def _target_prowess_raw(state: PhaseEventTrialState, target: str) -> int:
    if target == "root":
        return _signed_int64(state.refs["root.skills.prowess_raw"], "root prowess")
    candidate = state.candidate(_target_character_id(state, target))
    return _signed_int64(
        _object(candidate["selected_enemy_knight_refs"], "selected enemy refs")[
            "selected_enemy_knight.skills.prowess_raw"
        ],
        "selected enemy prowess",
    )


def _set_target_prowess_raw(
    state: PhaseEventTrialState, target: str, value: int
) -> None:
    raw = _signed_int64(value, "updated prowess")
    if target == "root":
        state.refs["root.skills.prowess_raw"] = raw
        _recompute_root_derived_refs(state)
        return
    candidate = state.candidate(_target_character_id(state, target))
    _object(candidate["candidate_refs"], "candidate refs")[
        "candidate.skills.prowess_raw"
    ] = raw
    _object(candidate["selected_enemy_knight_refs"], "selected enemy refs")[
        "selected_enemy_knight.skills.prowess_raw"
    ] = raw


def _target_blademaster_container(
    state: PhaseEventTrialState, target: str
) -> dict[str, object]:
    if target == "root":
        return _object(
            state.refs["root.traits_and_culture_for_blademaster"],
            "root blademaster container",
        )
    candidate = state.candidate(_target_character_id(state, target))
    return _object(
        _object(candidate["selected_enemy_knight_refs"], "selected enemy refs")[
            "selected_enemy_knight.traits_and_culture_for_blademaster"
        ],
        "selected enemy blademaster container",
    )


def _target_learning_raw(state: PhaseEventTrialState, target: str) -> int:
    if target == "root":
        return _signed_int64(state.refs["root.skills.learning_raw"], "root learning")
    candidate = state.candidate(_target_character_id(state, target))
    return _signed_int64(
        _object(candidate["selected_enemy_knight_refs"], "selected enemy refs")[
            "selected_enemy_knight.skills.learning_raw"
        ],
        "selected enemy learning",
    )


def _target_warfare_legacy(state: PhaseEventTrialState, target: str) -> bool:
    if target == "root":
        return _bool(
            state.refs["root.dynasty.perks.warfare_legacy_3"],
            "root warfare legacy",
        )
    candidate = state.candidate(_target_character_id(state, target))
    return _bool(
        _object(candidate["selected_enemy_knight_refs"], "selected enemy refs")[
            "selected_enemy_knight.dynasty.perks.warfare_legacy_3"
        ],
        "selected enemy warfare legacy",
    )


def _add_trait(state: PhaseEventTrialState, *, target: str, trait: str) -> None:
    character_id = _target_character_id(state, target)
    if not _target_alive(state, target):
        state.transition_log.append(
            {
                "transition": "add_trait",
                "target_character_id": character_id,
                "trait": trait,
                "applied": False,
                "reason": "target_not_alive",
            }
        )
        return
    if target != "root":
        raise PhaseEventEvaluationError("stock add_trait target must be root")
    path = f"root.traits.{trait}"
    if path not in state.refs:
        raise PhaseEventEvaluationError(f"trait state ref {path!r} is missing")
    before = _bool(state.refs[path], path)
    state.refs[path] = True
    if trait == "incapable":
        state.refs["root.is_incapable"] = True
    _recompute_root_derived_refs(state)
    state.transition_log.append(
        {
            "transition": "add_trait",
            "target_character_id": character_id,
            "trait": trait,
            "before": before,
            "after": True,
            "applied": not before,
        }
    )


def _increase_wound_or_die(
    state: PhaseEventTrialState, *, target: str, reason: str
) -> None:
    character_id = _target_character_id(state, target)
    if not _target_alive(state, target):
        state.transition_log.append(
            {
                "transition": "increase_wound_or_die",
                "target_character_id": character_id,
                "applied": False,
                "reason": "target_not_alive",
            }
        )
        return
    if target != "root":
        raise PhaseEventEvaluationError("stock wound target must be root")
    rank = _signed_int64(
        state.refs["root.traits.wounded.rank_raw"], "root wounded rank"
    )
    if rank >= 300000:
        state.transition_log.append(
            {
                "transition": "increase_wound_or_die",
                "target_character_id": character_id,
                "before_rank_raw": rank,
                "after_rank_raw": rank,
                "applied": True,
                "outcome": "death",
            }
        )
        _kill_character(
            state,
            target="root",
            reason=f"death_{reason}",
            killer_character_id=state.selected_enemy_character_id,
        )
        return
    fragile_rank = _signed_int64(
        state.refs["root.traits.fragile_bones.rank_raw"],
        "root fragile-bones rank",
    )
    fragile_xp = _signed_int64(
        state.refs["root.traits.fragile_bones.xp_raw"],
        "root fragile-bones xp",
    )
    delta = 300000 if fragile_xp >= 5_000_000 else 200000 if fragile_rank > 0 else 100000
    updated = min(300000, rank + delta)
    state.refs["root.traits.wounded.rank_raw"] = updated
    _recompute_root_derived_refs(state)
    state.transition_log.append(
        {
            "transition": "increase_wound_or_die",
            "target_character_id": character_id,
            "before_rank_raw": rank,
            "rank_delta_raw": delta,
            "after_rank_raw": updated,
            "applied": True,
            "outcome": "wounded",
        }
    )
    _require_character_recompute(state, target="root")


def _maim_random(state: PhaseEventTrialState, tape: _DrawTape) -> None:
    if not _target_alive(state, "root"):
        state.transition_log.append(
            {"transition": "maim_random", "applied": False, "reason": "root_not_alive"}
        )
        return
    trait_by_branch = {
        "one_legged_then_wound": "one_legged",
        "disfigured_then_wound": "disfigured",
        "one_eyed_then_wound": "one_eyed",
        "maimed_plus_recently_maimed": "maimed",
    }
    weights = [400000, 200000, 400000, 400000]
    for index, branch in enumerate(_MAIM_BRANCHES):
        if _bool(state.refs[f"root.traits.{trait_by_branch[branch]}"], branch):
            weights[index] = 0
    selected = tape.take("maim_random:source_order", weights)
    if selected < 0:
        state.transition_log.append(
            {
                "transition": "maim_random",
                "applied": False,
                "reason": "no_valid_branch",
                "weights_source_order": weights,
            }
        )
        return
    branch = _MAIM_BRANCHES[selected]
    trait = trait_by_branch[branch]
    state.refs[f"root.traits.{trait}"] = True
    _recompute_root_derived_refs(state)
    state.transition_log.append(
        {
            "transition": "maim_random",
            "selected_branch": branch,
            "target_character_id": state.root_character_id,
            "trait": trait,
            "weights_source_order": weights,
            "applied": True,
        }
    )
    if branch == "maimed_plus_recently_maimed":
        state.delayed_effects.append("recently_maimed_modifier_one_year")
        _require_character_recompute(state, target="root")
    else:
        _increase_wound_or_die(state, target="root", reason="fight")


def _kill_character(
    state: PhaseEventTrialState,
    *,
    target: str,
    reason: str,
    killer_character_id: int | None,
) -> None:
    character_id = _target_character_id(state, target)
    was_alive = _target_alive(state, target)
    if was_alive:
        _set_target_alive(state, target, False)
    state.transition_log.append(
        {
            "transition": "kill_character",
            "target_character_id": character_id,
            "reason": reason,
            "killer_character_id": killer_character_id,
            "applied": was_alive,
        }
    )
    if was_alive:
        _detach_character(state, target=target)


def _knight_increase_prowess_chance(
    state: PhaseEventTrialState, tape: _DrawTape, *, target: str
) -> None:
    character_id = _target_character_id(state, target)
    learning = _target_learning_raw(state, target)
    no_op_weight = _signed_int64(6_000_000 - 2 * learning, "prowess no-op weight")
    if _target_warfare_legacy(state, target):
        no_op_weight = fixed_mul(no_op_weight, 50_000)
    container = _target_blademaster_container(state, target)
    _validate_blademaster_container(container, "blademaster transition container")
    blade_weight = 1_000_000
    if any(container["education_martial"]):
        blade_weight += 500_000
    for present, points in zip(
        container["education_martial_prowess"], (4, 8, 12, 16), strict=True
    ):
        if present:
            blade_weight += points * FIXED_SCALE
    if container["lifestyle_blademaster"]:
        blade_weight += 1_500_000
    if container["shrewd"]:
        blade_weight += 1_000_000
    if container["physique_good"]:
        blade_weight += 1_000_000
    for present, points in zip(
        container["intellect_good"], (5, 15, 30), strict=True
    ):
        if present:
            blade_weight += points * FIXED_SCALE
    if container["culture_blademaster_traits_more_common"]:
        blade_weight = fixed_mul(blade_weight, 300_000)
    if (
        container["lifestyle_blademaster"]
        and _signed_int64(
            container["lifestyle_blademaster_xp_raw"], "blademaster xp"
        )
        >= 10_000_000
    ):
        blade_weight = 0
    weights = [no_op_weight, 3_000_000, blade_weight]
    selected = tape.take("knight_increase_prowess:source_order", weights)
    if selected < 0:
        state.transition_log.append(
            {
                "transition": "knight_increase_prowess_chance",
                "target_character_id": character_id,
                "selected_branch": None,
                "weights_source_order": weights,
                "applied": False,
            }
        )
        return
    branch = ("no_op", "add_prowess", "rank_blademaster")[selected]
    recompute_required = False
    if branch == "add_prowess":
        before = _target_prowess_raw(state, target)
        _set_target_prowess_raw(state, target, before + FIXED_SCALE)
        recompute_required = True
    elif branch == "rank_blademaster":
        before_trait = bool(container["lifestyle_blademaster"])
        before_xp = _signed_int64(
            container["lifestyle_blademaster_xp_raw"], "blademaster xp"
        )
        if not before_trait:
            container["lifestyle_blademaster"] = True
            if target == "root":
                state.refs["root.traits.lifestyle_blademaster"] = True
        elif before_xp < 10_000_000:
            container["lifestyle_blademaster_xp_raw"] = min(
                10_000_000, before_xp + 1_000_000
            )
        recompute_required = True
    state.transition_log.append(
        {
            "transition": "knight_increase_prowess_chance",
            "target_character_id": character_id,
            "selected_branch": branch,
            "weights_source_order": weights,
            "applied": branch != "no_op",
        }
    )
    if recompute_required:
        _require_character_recompute(state, target=target)


def _berserker_kill_random_reason(
    state: PhaseEventTrialState, tape: _DrawTape
) -> None:
    if not _target_alive(state, "selected_enemy_knight"):
        state.transition_log.append(
            {
                "transition": "berserker_kill_random_reason",
                "applied": False,
                "reason": "target_not_alive",
            }
        )
        return
    selected = state.candidate(_target_character_id(state, "selected_enemy_knight"))
    refs = _object(selected["selected_enemy_knight_refs"], "selected enemy refs")
    brave = _bool(refs["selected_enemy_knight.traits.brave"], "selected brave")
    craven = _bool(refs["selected_enemy_knight.traits.craven"], "selected craven")
    weights = [1_000_000] * 9
    weights[6] = 0 if brave else 100_000 + (9_900_000 if craven else 0)
    branch = tape.take("berserker_kill_reason:source_order", weights)
    _kill_character(
        state,
        target="selected_enemy_knight",
        reason=f"berserker_battle_reason_{branch}",
        killer_character_id=state.root_character_id,
    )


def _shieldmaiden_kill_random_reason(
    state: PhaseEventTrialState, tape: _DrawTape
) -> None:
    if not _target_alive(state, "selected_enemy_knight"):
        state.transition_log.append(
            {
                "transition": "shieldmaiden_kill_random_reason",
                "applied": False,
                "reason": "target_not_alive",
            }
        )
        return
    weights = [1_000_000] * 5
    branch = tape.take("shieldmaiden_kill_reason:source_order", weights)
    _kill_character(
        state,
        target="selected_enemy_knight",
        reason=f"shieldmaiden_battle_reason_{branch}",
        killer_character_id=state.root_character_id,
    )


def _require_character_recompute(
    state: PhaseEventTrialState, *, target: str
) -> None:
    character_id = _target_character_id(state, target)
    _append_unique(state.character_stat_recompute_ids, character_id)
    side = state.combat_side_index if target == "root" else state.enemy_side_index
    _append_unique(state.side_strength_recompute_indices, side)
    _mark_advantage_recompute(state, character_id=character_id, detached=False)
    state.transition_log.append(
        {
            "transition": "require_character_stat_recompute",
            "target_character_id": character_id,
            "timing": "same_day_unverified",
            "applied": True,
        }
    )


def _detach_character(state: PhaseEventTrialState, *, target: str) -> None:
    character_id = _target_character_id(state, target)
    already_requested = character_id in state.participant_detach_recompute_ids
    _append_unique(state.participant_detach_recompute_ids, character_id)
    if target == "root":
        state.combat_membership = [
            value for value in state.combat_membership if value != character_id
        ]
        side = state.combat_side_index
        if state.combat_commander_character_id == character_id:
            state.combat_commander_character_id = None
    else:
        state.enemy_membership = [
            value for value in state.enemy_membership if value != character_id
        ]
        state.ordered_enemy_knights = [
            value for value in state.ordered_enemy_knights if value != character_id
        ]
        side = state.enemy_side_index
    _append_unique(state.side_strength_recompute_indices, side)
    _mark_advantage_recompute(state, character_id=character_id, detached=True)
    state.transition_log.append(
        {
            "transition": "require_participant_detach_recompute",
            "target_character_id": character_id,
            "side_index": side,
            "timing": "same_day_unverified",
            "applied": not already_requested,
            "reason": "already_detached" if already_requested else None,
        }
    )


def _set_variable(
    state: PhaseEventTrialState, args: Mapping[str, Any]
) -> None:
    target = args.get("target")
    name = _string(args.get("name"), "set_variable.name")
    if target == "root.liege":
        state.liege_variable_updates[name] = _signed_int64(
            args.get("value_raw"), "set_variable.value_raw"
        )
        state.refs["root.liege.accolade_progress_raw"] = state.liege_variable_updates[
            name
        ]
        value: object = state.liege_variable_updates[name]
    elif target == "root":
        value = _bool(args.get("value"), "set_variable.value")
        state.root_variable_updates[name] = value
    else:
        raise PhaseEventEvaluationError(f"unsupported variable target {target!r}")
    state.transition_log.append(
        {
            "transition": "set_variable",
            "target": target,
            "name": name,
            "value": value,
            "applied": True,
        }
    )


def _recompute_root_derived_refs(state: PhaseEventTrialState) -> None:
    rank = _signed_int64(
        state.refs["root.traits.wounded.rank_raw"], "root wounded rank"
    )
    prowess_raw = _signed_int64(
        state.refs["root.skills.prowess_raw"], "root prowess"
    )
    prowess = trunc_div_toward_zero(prowess_raw, FIXED_SCALE)
    maim = any(
        _bool(state.refs[f"root.traits.{key}"], f"root trait {key}")
        for key in ("one_legged", "disfigured", "one_eyed", "maimed")
    )
    wounded = rank in {100000, 200000, 300000}
    garuda = 8 if _bool(state.refs["root.court_positions.garuda"], "root garuda") else 0
    state.refs["root.traits.maim_injuries"] = maim
    state.refs["derived.root_has_any_maim_injury"] = maim
    state.refs["derived.root_has_any_wounded_rank_1_2_3"] = wounded
    state.refs["derived.root_is_wounded"] = wounded
    state.refs["derived.root_wounded_rank_3"] = rank == 300000
    wound_factor = 25000 if rank == 300000 else 50000 if rank in {100000, 200000} else 100000
    state.refs["derived.accolade_qualification_wound_factor_raw"] = wound_factor
    state.refs["derived.become_berserker_wound_factor_raw"] = wound_factor
    state.refs["derived.root_injury_factor_30_raw"] = _injury_factor(
        prowess, 30, 0
    )
    state.refs["derived.root_injury_factor_30_with_garuda_raw"] = _injury_factor(
        prowess, 30, garuda
    )
    state.refs["derived.root_injury_factor_40_with_garuda_raw"] = _injury_factor(
        prowess, 40, garuda
    )
    threshold = fixed_mul(prowess_raw, 80000)
    any_alive_below = False
    any_below = False
    for candidate in state.candidates:
        candidate_refs = _object(candidate["candidate_refs"], "candidate refs")
        selected_refs = _object(
            candidate["selected_enemy_knight_refs"], "selected enemy refs"
        )
        candidate_prowess = _signed_int64(
            candidate_refs["candidate.skills.prowess_raw"], "candidate prowess"
        )
        alive = _bool(candidate_refs["candidate.alive"], "candidate alive")
        below = candidate_prowess <= threshold
        any_below = any_below or below
        any_alive_below = any_alive_below or (alive and below)
        candidate_refs[
            "derived.candidate_prowess_at_or_above_root_opponent_threshold_without_alive_filter"
        ] = candidate_prowess >= threshold
        candidate_refs[
            "derived.candidate_prowess_at_or_below_root_opponent_threshold"
        ] = alive and below
        candidate_refs[
            "derived.candidate_prowess_at_or_below_root_opponent_threshold_without_alive_filter"
        ] = below
        # Keep selected aliases synchronized even when a candidate was killed.
        selected_refs["selected_enemy_knight.alive"] = alive
        selected_refs["selected_enemy_knight.skills.prowess_raw"] = candidate_prowess
    state.refs[
        "derived.enemy_alive_knight_at_or_below_root_opponent_threshold_exists"
    ] = any_alive_below
    state.refs["derived.qualifying_enemy_knight_exists"] = any_below


def _injury_factor(prowess: int, denominator: int, bonus: int) -> int:
    return max(
        trunc_div_toward_zero(
            (denominator - prowess + bonus) * FIXED_SCALE, denominator
        ),
        10000,
    )


def _initial_advantage_state(value: object | None) -> dict[str, object]:
    if value is None:
        return {
            "status": "not_supplied",
            "recompute_required": False,
            "invalidated_character_ids": [],
            "removed_commander_contributions": [],
            "resolved_advantage_raw": None,
        }
    model = _object(value, "advantage_model")
    if model.get("status") != "available":
        raise PhaseEventEvaluationError("advantage_model is not available")
    resolved = _object(model.get("resolved_dynamic"), "resolved_dynamic")
    sides = _array(resolved.get("sides"), "resolved_dynamic.sides")
    if len(sides) != 2:
        raise PhaseEventEvaluationError("resolved_dynamic must contain two sides")
    side_rows: list[dict[str, object]] = []
    for index, row_value in enumerate(sides):
        row = _object(row_value, f"resolved_dynamic.sides[{index}]")
        if row.get("side") != ("attacker" if index == 0 else "defender"):
            raise PhaseEventEvaluationError("resolved advantage side order drifted")
        side_rows.append(
            {
                "side_index": index,
                "side": row["side"],
                "battle_commander_character_id": row.get(
                    "battle_commander_character_id"
                ),
                "commander_dynamic_raw": _signed_int64(
                    row.get("commander_dynamic_raw"),
                    "resolved commander dynamic",
                ),
                "side_total_raw": _signed_int64(
                    row.get("side_total_raw"), "resolved side total"
                ),
            }
        )
    return {
        "status": "available",
        "base_static_accumulator_raw": _signed_int64(
            model.get("base_static_accumulator_raw"), "base static advantage"
        ),
        "side_rows": side_rows,
        "recompute_required": False,
        "invalidated_character_ids": [],
        "removed_commander_contributions": [],
        "resolved_advantage_raw": _signed_int64(
            resolved.get("resolved_advantage_at_zero_roll_raw"),
            "resolved advantage",
        ),
        "original_helper_match_after_transition": False,
        "original_trace_ready": False,
    }


def _mark_advantage_recompute(
    state: PhaseEventTrialState, *, character_id: int, detached: bool
) -> None:
    advantage = state.advantage_state
    if advantage["status"] != "available":
        return
    _append_unique(
        _array(
            advantage["invalidated_character_ids"],
            "advantage invalidated characters",
        ),
        character_id,
    )
    advantage["recompute_required"] = True
    side_rows = _array(advantage["side_rows"], "advantage side rows")
    for row_value in side_rows:
        row = _object(row_value, "advantage side row")
        if row.get("battle_commander_character_id") != character_id:
            continue
        if detached:
            removed = _signed_int64(
                row["commander_dynamic_raw"], "removed commander advantage"
            )
            row["battle_commander_character_id"] = None
            row["commander_dynamic_raw"] = 0
            row["side_total_raw"] = _signed_int64(
                _signed_int64(row["side_total_raw"], "side total") - removed,
                "updated side total",
            )
            removals = _array(
                advantage["removed_commander_contributions"],
                "removed commander contributions",
            )
            if not any(
                _object(item, "removed commander row").get("character_id")
                == character_id
                for item in removals
            ):
                removals.append(
                    {
                        "character_id": character_id,
                        "side_index": row["side_index"],
                        "removed_raw": removed,
                    }
                )
    if len(side_rows) == 2:
        base = _signed_int64(
            advantage["base_static_accumulator_raw"], "base static advantage"
        )
        side0 = _signed_int64(
            _object(side_rows[0], "side0")["side_total_raw"], "side0 total"
        )
        side1 = _signed_int64(
            _object(side_rows[1], "side1")["side_total_raw"], "side1 total"
        )
        advantage["resolved_advantage_raw"] = _signed_int64(
            base + side0 - side1, "updated resolved advantage"
        )


def _validate_blademaster_container(value: object, name: str) -> None:
    row = _object(value, name)
    _require_keys(
        row,
        {
            "education_martial",
            "education_martial_prowess",
            "lifestyle_blademaster",
            "lifestyle_blademaster_xp_raw",
            "shrewd",
            "physique_good",
            "intellect_good",
            "culture_blademaster_traits_more_common",
        },
        name,
    )
    for key, length in (
        ("education_martial", 5),
        ("education_martial_prowess", 4),
        ("intellect_good", 3),
    ):
        values = _array(row[key], f"{name}.{key}")
        if len(values) != length or any(not isinstance(item, bool) for item in values):
            raise PhaseEventEvaluationError(f"{name}.{key} is malformed")
    for key in (
        "lifestyle_blademaster",
        "shrewd",
        "physique_good",
        "culture_blademaster_traits_more_common",
    ):
        _bool(row[key], f"{name}.{key}")
    xp = _signed_int64(
        row["lifestyle_blademaster_xp_raw"],
        f"{name}.lifestyle_blademaster_xp_raw",
    )
    if xp < 0:
        raise PhaseEventEvaluationError(f"{name} blademaster XP is negative")


def _validate_dependencies(
    value: object, declared: frozenset[str], name: str
) -> None:
    dependencies = _sequence(value, f"{name}.dependencies")
    parsed = tuple(_string(item, f"{name}.dependencies item") for item in dependencies)
    if len(parsed) != len(set(parsed)) or not set(parsed) <= declared:
        raise PhaseEventEvaluationError(f"{name}.dependencies is malformed")


def _thaw(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _thaw(child) for key, child in value.items()}
    if isinstance(value, tuple):
        return [_thaw(child) for child in value]
    if isinstance(value, list):
        return [_thaw(child) for child in value]
    return value


def _append_unique(values: list[Any], item: Any) -> None:
    if item not in values:
        values.append(item)


def _mapping(value: object, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise PhaseEventEvaluationError(f"{name} must be an object")
    if any(not isinstance(key, str) for key in value):
        raise PhaseEventEvaluationError(f"{name} contains a non-string key")
    return value


def _object(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PhaseEventEvaluationError(f"{name} must be a mutable object")
    return value


def _require_keys(value: Mapping[str, Any], expected: set[str], name: str) -> None:
    if set(value) != expected:
        raise PhaseEventEvaluationError(
            f"{name} schema is malformed: expected {sorted(expected)!r}, "
            f"got {sorted(value)!r}"
        )


def _sequence(value: object, name: str) -> Sequence[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple)):
        raise PhaseEventEvaluationError(f"{name} must be an array")
    return value


def _array(value: object, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise PhaseEventEvaluationError(f"{name} must be an array")
    return value


def _string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise PhaseEventEvaluationError(f"{name} must be a nonempty string")
    return value


def _bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise PhaseEventEvaluationError(f"{name} must be boolean")
    return value


def _signed_int64(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not -(1 << 63) <= value <= (1 << 63) - 1
    ):
        raise PhaseEventEvaluationError(f"{name} must be signed int64")
    return value


def _wrap_signed_int32(value: int) -> int:
    normalized = int(value) & 0xFFFFFFFF
    return normalized - 0x100000000 if normalized >= 0x80000000 else normalized


def _native_candidate_int_weight(raw: int) -> int:
    """Mirror 0x337B310 Q100000 -> low signed-int32 conversion."""

    value = _signed_int64(raw, "native candidate weight raw")
    quotient = trunc_div_toward_zero(value, FIXED_SCALE)
    remainder = value - quotient * FIXED_SCALE
    if value > 0 and remainder != 0:
        quotient += 1
    return _wrap_signed_int32(quotient)


def _positive_int(value: object, name: str) -> int:
    result = _signed_int64(value, name)
    if result <= 0:
        raise PhaseEventEvaluationError(f"{name} must be positive")
    return result


def _side_index(value: object, name: str) -> int:
    if value not in {0, 1} or isinstance(value, bool):
        raise PhaseEventEvaluationError(f"{name} must be 0 or 1")
    return int(value)


def _id_list(value: object, name: str) -> list[int]:
    rows = _array(value, name)
    result = [_positive_int(item, f"{name} item") for item in rows]
    if len(result) != len(set(result)):
        raise PhaseEventEvaluationError(f"{name} repeats a CharacterID")
    return result
