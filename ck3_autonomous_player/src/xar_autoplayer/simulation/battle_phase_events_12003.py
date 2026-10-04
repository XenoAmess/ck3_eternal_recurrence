"""Caller-conditioned CK3 1.20.0.3 phase-event effect transitions.

The caller supplies the selected stock row, each script random branch, and
each enemy CharacterID.  This module applies the supported primary character
effects to an isolated state; it never selects an event, draws a random value,
or imports the 1.19.0.6 native candidate-source proof.  The stock data identity
and executable identity are reported separately.  Script callbacks, resources,
delayed health effects, native refresh timing, and complete battle forecasting
remain outside this bounded primitive.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from importlib import resources
import json
from pathlib import Path
from typing import Sequence

from .combat_core import fixed_mul
from .phase_event_evaluator import (
    PhaseEventEvaluationError,
    PhaseEventTrialState,
    _audit_effect_node,
    _audit_value_node,
    _bool,
    _canonical_digest,
    _eval_bool,
    _eval_fixed,
    _execute_transition,
    _id_list,
    _increase_wound_or_die,
    _initial_advantage_state,
    _kill_character,
    _mapping,
    _object,
    _positive_int,
    _public_cunit_int32,
    _recompute_root_derived_refs,
    _require_character_recompute,
    _sequence,
    _side_index,
    _signed_int64,
    _string,
    _target_alive,
)
from .phase_event_manifest import (
    FrozenPhaseEventCompleteness,
    FrozenPhaseEventManifest,
    FrozenPhaseEventRow,
    FrozenPhaseEventSource,
    PhaseEventManifestError,
    _EXPECTED_ROW_KEYS,
    _EXPECTED_TOP_LEVEL_KEYS,
    _SHA256,
    _canonical_hash,
    _freeze_json,
    _integer,
    _string_tuple,
    _validate_ast_row,
)


GAME_VERSION_12003 = "1.20.0.3"
EXECUTABLE_SHA256_12003 = (
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"
)
STOCK_PHASE_EVENT_MANIFEST_SHA256_12003 = (
    "38BB943E208F53D106B90A2F6B895189ECA6471ED7B9888AC5A8454E7CD60240"
)
PHASE_EVENT_TRANSITION_VERSION_12003 = "ck3-1.20.0.3-caller-selected-primary-effects-v1"
_MANIFEST_RESOURCE = "data/ck3_1_20_0_3_stock_combat_phase_events.json"
SUPPORTED_SELECTED_EVENT_KEYS_12003 = (
    "commander_none",
    "commander_wounded",
    "commander_maimed",
    "commander_killed",
    "knight_none",
    "knight_wounded",
    "knight_maimed",
)
_CALLER_TARGET_POLICY = "caller_explicit_character_targets_no_native_order_claim"
_CONTEXT_KEYS = frozenset(
    {
        "root_character_id", "root_source_army_id", "root_source_regiment_id",
        "phase_roles", "combat_side_index", "enemy_side_index",
        "native_state_refs", "offline_state_refs", "candidate_rows",
    }
)


@dataclass(frozen=True, slots=True)
class PhaseEventScriptOutcome12003:
    """One caller-supplied script choice at a named execution boundary.

    A branch outcome has ``branch_index`` and no CharacterID.  An enemy target
    has a CharacterID and no branch index.  A target with both fields ``None``
    explicitly represents an empty eligible target set.  It is accepted only
    when the supplied condition has no qualifying enemy.
    """

    purpose: str
    branch_index: int | None = None
    character_id: int | None = None

    def __post_init__(self) -> None:
        _string(self.purpose, "script outcome purpose")
        if self.branch_index is not None:
            if (
                isinstance(self.branch_index, bool)
                or not isinstance(self.branch_index, int)
                or self.branch_index < 0
            ):
                raise PhaseEventEvaluationError("branch_index must be nonnegative")
        if self.character_id is not None:
            _positive_int(self.character_id, "script outcome character_id")
        if self.branch_index is not None and self.character_id is not None:
            raise PhaseEventEvaluationError("an outcome cannot name both a branch and target")


@dataclass(slots=True)
class _ExplicitOutcomeTape:
    outcomes: tuple[PhaseEventScriptOutcome12003, ...]
    position: int = 0
    records: list[dict[str, object]] = field(default_factory=list)

    @classmethod
    def from_value(cls, value: Sequence[PhaseEventScriptOutcome12003]) -> "_ExplicitOutcomeTape":
        if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
            raise PhaseEventEvaluationError("script_outcomes must be a sequence")
        if any(not isinstance(item, PhaseEventScriptOutcome12003) for item in value):
            raise PhaseEventEvaluationError("script_outcomes must contain typed outcomes")
        return cls(tuple(value))

    def _consume(self, purpose: str) -> PhaseEventScriptOutcome12003:
        if self.position >= len(self.outcomes):
            raise PhaseEventEvaluationError(f"script outcome tape exhausted at {purpose}")
        outcome = self.outcomes[self.position]
        if outcome.purpose != purpose:
            raise PhaseEventEvaluationError(
                f"script outcome {self.position} names {outcome.purpose!r}; expected {purpose!r}"
            )
        self.position += 1
        return outcome

    def take(self, purpose: str, weights: Sequence[int]) -> int:
        """Duck-typed choice input for the existing pure transition helpers."""

        normalized = tuple(_signed_int64(weight, f"{purpose}.weight") for weight in weights)
        if not any(weight > 0 for weight in normalized):
            return -1
        outcome = self._consume(purpose)
        index = outcome.branch_index
        if outcome.character_id is not None or index is None:
            raise PhaseEventEvaluationError(f"{purpose} needs an explicit branch_index")
        if index >= len(normalized) or normalized[index] <= 0:
            raise PhaseEventEvaluationError(f"{purpose} selects an unavailable script branch")
        self.records.append(
            {
                "ordinal": self.position - 1,
                "purpose": purpose,
                "selection_origin": "caller_conditional",
                "branch_index": index,
                "weights_source_order_raw": list(normalized),
            }
        )
        return index

    def target(self, purpose: str, eligible_ids: Sequence[int]) -> int | None:
        outcome = self._consume(purpose)
        if outcome.branch_index is not None:
            raise PhaseEventEvaluationError(f"{purpose} needs an explicit character_id")
        target = outcome.character_id
        if (target is None and eligible_ids) or (target is not None and target not in eligible_ids):
            raise PhaseEventEvaluationError(f"{purpose} selects an unavailable enemy target")
        self.records.append(
            {
                "ordinal": self.position - 1,
                "purpose": purpose,
                "selection_origin": "caller_conditional",
                "character_id": target,
                "eligible_character_ids_caller_order": list(eligible_ids),
            }
        )
        return target


def load_stock_phase_events_12003(path: str | Path | None = None) -> FrozenPhaseEventManifest:
    """Load the independent .3 stock inventory, without enabling native fidelity."""

    text = (
        Path(path).read_text(encoding="utf-8")
        if path is not None
        else resources.files("xar_autoplayer.simulation").joinpath(_MANIFEST_RESOURCE).read_text(encoding="utf-8")
    )
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise PhaseEventManifestError("phase-event manifest is not valid JSON") from exc
    if not isinstance(payload, dict) or tuple(payload) != _EXPECTED_TOP_LEVEL_KEYS:
        raise PhaseEventManifestError(".3 phase-event manifest top-level schema/order drifted")
    canonical = payload["canonical_manifest_sha256"]
    if canonical != STOCK_PHASE_EVENT_MANIFEST_SHA256_12003 or _canonical_hash(payload) != canonical:
        raise PhaseEventManifestError(".3 phase-event manifest canonical hash drifted")
    if (
        payload["schema_version"] != 1
        or payload["game_version"] != GAME_VERSION_12003
        or payload["executable_sha256"] != EXECUTABLE_SHA256_12003
        or payload["rules_source"] != "stock-installation-static-manifest"
    ):
        raise PhaseEventManifestError(".3 phase-event source identity drifted")
    raw_files = payload["files"]
    if not isinstance(raw_files, list) or len(raw_files) != 11:
        raise PhaseEventManifestError(".3 phase-event source inventory must contain 11 files")
    sources: list[FrozenPhaseEventSource] = []
    for index, source in enumerate(raw_files):
        if not isinstance(source, dict) or set(source) != {"relative_path", "sha256", "load_order"}:
            raise PhaseEventManifestError(".3 phase-event source schema drifted")
        if _SHA256.fullmatch(str(source["sha256"])) is None or source["load_order"] != index:
            raise PhaseEventManifestError(".3 phase-event source hash/order drifted")
        sources.append(FrozenPhaseEventSource(
            relative_path=_string(source["relative_path"], "source.relative_path"),
            sha256=source["sha256"], load_order=index,
        ))
    supported = _string_tuple(payload["supported_transition_opcodes"], "supported transitions")
    raw_rows = payload["event_rows"]
    if not isinstance(raw_rows, list) or len(raw_rows) != 13:
        raise PhaseEventManifestError(".3 stock phase inventory must contain 13 rows")
    rows: list[FrozenPhaseEventRow] = []
    type_counts = {"commander": 0, "knight": 0}
    for index, row in enumerate(raw_rows):
        if not isinstance(row, dict) or set(row) != _EXPECTED_ROW_KEYS:
            raise PhaseEventManifestError(".3 stock phase row schema drifted")
        role = row["type"]
        if role not in type_counts or row["global_load_index"] != index or row["type_load_index"] != type_counts[role]:
            raise PhaseEventManifestError(".3 phase-event load order drifted")
        _validate_ast_row(row, name=f"event_rows[{index}]", supported_transitions=frozenset(supported))
        dependencies = frozenset(row["state_dependencies"])
        for name in ("validity_ast", "chance_ast"):
            _audit_value_node(row[name], name=f"{row['key']}.{name}", dependencies=dependencies)
        if row["key"] in SUPPORTED_SELECTED_EVENT_KEYS_12003:
            _audit_effect_node(row["effect_ast"], name=f"{row['key']}.effect_ast", dependencies=dependencies, direct_calls=set())
        rows.append(FrozenPhaseEventRow(
            global_load_index=index, type_load_index=type_counts[role],
            key=_string(row["key"], "event key"), event_type=role,
            base_weight=_integer(row["base_weight"], "base_weight"),
            validity_ast=_freeze_json(row["validity_ast"]),
            chance_ast=_freeze_json(row["chance_ast"]),
            effect_ast=_freeze_json(row["effect_ast"]),
            transition_tags=_string_tuple(row["transition_tags"], "transition_tags"),
            state_dependencies=_string_tuple(row["state_dependencies"], "state_dependencies"),
        ))
        type_counts[role] += 1
    if type_counts != {"commander": 4, "knight": 9} or len({row.key for row in rows}) != 13:
        raise PhaseEventManifestError(".3 stock phase role/key inventory drifted")
    flags = payload["completeness"]
    if not isinstance(flags, dict) or set(flags) != {
        "loaded_playset_verified", "ast_evaluator_ready", "original_trace_ready", "unsupported_opcodes",
    }:
        raise PhaseEventManifestError(".3 phase-event completeness schema drifted")
    for name in ("loaded_playset_verified", "ast_evaluator_ready", "original_trace_ready"):
        if not isinstance(flags[name], bool):
            raise PhaseEventManifestError(".3 phase-event completeness flags must be booleans")
    return FrozenPhaseEventManifest(
        schema_version=1, game_version=GAME_VERSION_12003,
        executable_sha256=EXECUTABLE_SHA256_12003, rules_source=payload["rules_source"],
        files=tuple(sources), event_rows=tuple(rows), supported_transition_opcodes=supported,
        completeness=FrozenPhaseEventCompleteness(
            loaded_playset_verified=flags["loaded_playset_verified"],
            ast_evaluator_ready=flags["ast_evaluator_ready"],
            original_trace_ready=flags["original_trace_ready"],
            unsupported_opcodes=_string_tuple(flags["unsupported_opcodes"], "unsupported_opcodes"),
        ),
        canonical_manifest_sha256=canonical,
    )


def _caller_condition_state(context_value: object, advantage_model: object | None) -> PhaseEventTrialState:
    context = _object(context_value, ".3 caller condition")
    if not _CONTEXT_KEYS <= set(context) or set(context) - _CONTEXT_KEYS - {"candidate_source_proof"}:
        raise PhaseEventEvaluationError(".3 caller condition schema is malformed")
    native = copy.deepcopy(_object(context["native_state_refs"], "caller native refs"))
    offline = copy.deepcopy(_object(context["offline_state_refs"], "caller offline refs"))
    if set(native) & set(offline):
        raise PhaseEventEvaluationError("caller native/offline refs overlap")
    refs = {**native, **offline}
    root_id = _positive_int(context["root_character_id"], "root_character_id")
    if refs.get("root.exists") is not True:
        raise PhaseEventEvaluationError("caller root does not exist")
    side = _side_index(context["combat_side_index"], "combat_side_index")
    enemy_side = _side_index(context["enemy_side_index"], "enemy_side_index")
    if enemy_side != 1 - side:
        raise PhaseEventEvaluationError("enemy side must be opposite combat side")
    roles = tuple(_sequence(context["phase_roles"], "phase_roles"))
    if not roles or len(set(roles)) != len(roles) or not set(roles) <= {"commander", "knight"}:
        raise PhaseEventEvaluationError("phase_roles is malformed")
    membership = _id_list(refs.get("combat_side.character_membership"), "combat membership")
    enemy_membership = _id_list(refs.get("enemy_side.character_membership"), "enemy membership")
    ordered_enemy = _id_list(refs.get("combat_side.ordered_enemy_knights"), "caller enemy list")
    if root_id not in membership:
        raise PhaseEventEvaluationError("root is absent from caller combat membership")
    commander = refs.get("combat_side.commander")
    if commander is not None and _positive_int(commander, "commander") not in membership:
        raise PhaseEventEvaluationError("commander is absent from caller combat membership")
    candidates: list[dict[str, object]] = []
    seen: set[int] = set()
    for value in _sequence(context["candidate_rows"], "candidate_rows"):
        candidate = _object(value, "caller enemy candidate")
        if set(candidate) != {"character_id", "candidate_refs", "selected_enemy_knight_refs"}:
            raise PhaseEventEvaluationError("caller candidate schema is malformed")
        character_id = _positive_int(candidate["character_id"], "candidate character_id")
        if character_id in seen or character_id not in enemy_membership:
            raise PhaseEventEvaluationError("caller candidate identity/membership is malformed")
        seen.add(character_id)
        candidates.append({
            "character_id": character_id,
            "candidate_refs": copy.deepcopy(_object(candidate["candidate_refs"], "candidate refs")),
            "selected_enemy_knight_refs": copy.deepcopy(_object(candidate["selected_enemy_knight_refs"], "selected target refs")),
        })
    if set(ordered_enemy) != seen:
        raise PhaseEventEvaluationError("caller enemy list differs from candidate identities")
    regiment = context["root_source_regiment_id"]
    return PhaseEventTrialState(
        root_character_id=root_id,
        root_source_army_id=_public_cunit_int32(context["root_source_army_id"], "root source army"),
        root_source_regiment_id=None if regiment is None else _positive_int(regiment, "root source regiment"),
        phase_roles=roles, combat_side_index=side, enemy_side_index=enemy_side,
        refs=refs, candidates=candidates, combat_membership=membership,
        enemy_membership=enemy_membership, ordered_enemy_knights=ordered_enemy,
        candidate_source_proof={
            "policy": _CALLER_TARGET_POLICY, "source_vector_equivalence": False,
            "sequence_sha256": _canonical_digest({"side_index": enemy_side, "caller_character_ids": ordered_enemy}),
        },
        candidate_materialization_input_ready=False,
        combat_commander_character_id=commander, selected_enemy_character_id=None,
        root_variable_updates={}, liege_variable_updates={}, observational_effects=[],
        delayed_effects=[], transition_log=[], character_stat_recompute_ids=[],
        participant_detach_recompute_ids=[], side_strength_recompute_indices=[],
        advantage_state=_initial_advantage_state(advantage_model),
    )


def _record_pending(state: PhaseEventTrialState, effect: str, *, delayed: bool = False) -> None:
    if effect not in state.observational_effects:
        state.observational_effects.append(effect)
    if delayed and effect not in state.delayed_effects:
        state.delayed_effects.append(effect)


def _primary_wound_12003(state: PhaseEventTrialState) -> None:
    if not _target_alive(state, "root"):
        _increase_wound_or_die(state, target="root", reason="fight")
        return
    rank = _signed_int64(state.refs["root.traits.wounded.rank_raw"], "root wounded rank")
    if rank == 300_000:
        state.transition_log.append({
            "transition": "increase_wound_or_die", "target_character_id": state.root_character_id,
            "before_rank_raw": rank, "after_rank_raw": rank, "applied": True,
            "outcome": "death", "source_projection": "primary_injury_projection",
        })
        # Current increase_wounds_effect has no killer assignment in this branch.
        _kill_character(state, target="root", reason="death_fight", killer_character_id=None)
    elif 0 <= rank < 300_000:
        _increase_wound_or_die(state, target="root", reason="fight")
        _record_pending(state, "wound_piety_stress_safe_treatment_and_delayed_health", delayed=True)
    else:
        raise PhaseEventEvaluationError("wounded rank is outside the supported primary projection")


def _primary_maim_12003(state: PhaseEventTrialState, tape: _ExplicitOutcomeTape) -> None:
    if not _target_alive(state, "root"):
        state.transition_log.append({"transition": "maim_random", "applied": False, "reason": "root_not_alive"})
        return
    traits = ("one_legged", "disfigured", "one_eyed", "maimed")
    weights = [400_000, 200_000, 400_000, 400_000]
    for index, trait in enumerate(traits):
        if _bool(state.refs[f"root.traits.{trait}"], trait):
            weights[index] = 0
    selected = tape.take("maim_random:source_order", weights)
    if selected < 0:
        state.transition_log.append({"transition": "maim_random", "applied": False, "reason": "no_valid_branch"})
        return
    trait = traits[selected]
    state.refs[f"root.traits.{trait}"] = True
    _recompute_root_derived_refs(state)
    state.transition_log.append({
        "transition": "maim_random", "target_character_id": state.root_character_id,
        "selected_branch_index": selected, "trait": trait, "applied": True,
        "source_projection": "primary_injury_projection",
    })
    if selected == 3:
        _record_pending(state, "recently_maimed_modifier", delayed=True)
        _require_character_recompute(state, target="root")
    else:
        _primary_wound_12003(state)
    if selected in (1, 2, 3):
        _record_pending(state, "epilepsy_brain_trauma_risk", delayed=True)


def _execute_selected_effect_12003(node_value: object, *, state: PhaseEventTrialState, tape: _ExplicitOutcomeTape, name: str) -> None:
    node = _mapping(node_value, name)
    op = node["op"]
    if op == "sequence":
        for index, child in enumerate(_sequence(node["steps"], f"{name}.steps")):
            _execute_selected_effect_12003(child, state=state, tape=tape, name=f"{name}.steps[{index}]")
    elif op == "if":
        branch = "then" if _eval_bool(node["condition"], state=state, name=f"{name}.condition") else "else"
        _execute_selected_effect_12003(node[branch], state=state, tape=tape, name=f"{name}.{branch}")
    elif op == "select_side_knight":
        eligible = [
            candidate for candidate in state.candidates
            if int(candidate["character_id"]) in state.enemy_membership
            and _eval_bool(node["filter"], state=state, candidate=candidate, name=f"{name}.filter")
        ]
        target = tape.target(f"{name}:enemy_knight", [int(candidate["character_id"]) for candidate in eligible])
        state.selected_enemy_character_id = target
        state.transition_log.append({
            "transition": "select_side_knight", "selected_character_id": target,
            "selection_origin": "caller_conditional", "native_order_ready": False,
        })
        if target is not None:
            _execute_selected_effect_12003(node["on_selected"], state=state, tape=tape, name=f"{name}.on_selected")
    elif op == "random_list":
        branches = _sequence(node["branches"], f"{name}.branches")
        weights = []
        for index, branch in enumerate(branches):
            branch = _mapping(branch, f"{name}.branches[{index}]")
            valid = _eval_bool(branch["validity"], state=state, name=f"{name}.branches[{index}].validity")
            weights.append(fixed_mul(
                _eval_fixed(branch["base_weight"], state=state, name=f"{name}.branches[{index}].base_weight"),
                _eval_fixed(branch["weight"], state=state, name=f"{name}.branches[{index}].weight"),
            ) if valid else 0)
        selected = tape.take(f"{name}:random_list", weights)
        if selected >= 0:
            _execute_selected_effect_12003(branches[selected]["effect"], state=state, tape=tape, name=f"{name}.branches[{selected}].effect")
    elif op == "call_transition":
        key = str(node["key"])
        if key == "increase_wound_or_die":
            _primary_wound_12003(state)
        elif key == "maim_random":
            _primary_maim_12003(state, tape)
        else:
            _execute_transition(key, _mapping(node["args"], f"{name}.args"), state, tape)
            if key == "knight_increase_prowess_chance":
                _record_pending(state, "impressive_knight_variables_flags_liege_list_and_delayed_maintenance", delayed=True)
    else:
        raise PhaseEventEvaluationError(f"{name} is outside the supported .3 effect primitive")


def execute_selected_phase_event_12003(
    context: object,
    *,
    event_key: str | None,
    script_outcomes: Sequence[PhaseEventScriptOutcome12003] = (),
    advantage_model: object | None = None,
    manifest: FrozenPhaseEventManifest | None = None,
) -> dict[str, object]:
    """Apply one caller-selected supported row, or an explicit no-event step.

    Context has the old normalized root/refs/candidate *shape*, but any supplied
    ``candidate_source_proof`` is ignored.  Refs and target membership are
    caller conditions, not a claim that .3 native reads produced those values.
    Every outcome is consumed in effect execution order.  No random values,
    native candidate compaction, day schedule, event weights, or next-day
    combat transitions are inferred.
    """

    stock = manifest or load_stock_phase_events_12003()
    if (
        stock.game_version != GAME_VERSION_12003
        or stock.executable_sha256 != EXECUTABLE_SHA256_12003
        or stock.canonical_manifest_sha256 != STOCK_PHASE_EVENT_MANIFEST_SHA256_12003
    ):
        raise PhaseEventManifestError("selected effect requires the independent .3 manifest")
    state = _caller_condition_state(context, advantage_model)
    before = state.snapshot()
    tape = _ExplicitOutcomeTape.from_value(script_outcomes)
    event: dict[str, object] | None = None
    if event_key is not None:
        key = _string(event_key, "event_key")
        if key not in SUPPORTED_SELECTED_EVENT_KEYS_12003:
            raise PhaseEventEvaluationError(f"event {key!r} is not supported by the bounded .3 primitive")
        row = next(row for row in stock.event_rows if row.key == key)
        if row.event_type not in state.phase_roles:
            raise PhaseEventEvaluationError(f"root has no {row.event_type} phase role")
        trigger_valid = _eval_bool(row.validity_ast, state=state, name=f"{row.key}.validity")
        if not trigger_valid:
            raise PhaseEventEvaluationError(f"selected phase-event row {key!r} is not valid")
        event = {
            "key": key, "type": row.event_type, "global_load_index": row.global_load_index,
            "type_load_index": row.type_load_index, "trigger_valid": True,
            "selection_origin": "caller_conditional",
        }
        _execute_selected_effect_12003(row.effect_ast, state=state, tape=tape, name=f"{row.key}.effect_ast")
    if tape.position != len(tape.outcomes):
        raise PhaseEventEvaluationError("selected phase-event transition has unused script outcomes")
    after = state.snapshot()
    result: dict[str, object] = {
        "schema_version": 1,
        "status": "primary_selected_effect_transition_applied" if event_key is not None else "explicit_no_event_unchanged",
        "transition_version": PHASE_EVENT_TRANSITION_VERSION_12003,
        "data_provenance": {
            "rules_source": stock.rules_source, "canonical_manifest_sha256": stock.canonical_manifest_sha256,
            "source_files": [{"relative_path": source.relative_path, "sha256": source.sha256} for source in stock.files],
            "loaded_playset_verified": stock.completeness.loaded_playset_verified,
            "stock_source_closure_sha256": "76F752C0A794346D4FDCD29FB8721B1A878ED6108B6C2DBA226CFDDD3D797E58",
            "primary_feedback_source_ledger_sha256": "AC7BC5B9D2928E191B0EDCE8AAA9F4C2E645EBC162B7DC8D3869BB1419DBDB9E",
        },
        "executable_provenance": {"game_version": GAME_VERSION_12003, "executable_sha256": EXECUTABLE_SHA256_12003},
        "context_provenance": "CURRENT_CALLER_CONDITION",
        "event": event, "before_state_sha256": before["state_sha256"],
        "after_state": after, "state_changed": before["state_sha256"] != after["state_sha256"],
        "script_outcomes": {
            "provided_count": len(tape.outcomes), "consumed_count": tape.position,
            "records": copy.deepcopy(tape.records), "native_rng_trace_claimed": False,
        },
        "transition_log": copy.deepcopy(state.transition_log),
        "feedback_pending": list(state.observational_effects),
        "primary_selected_effect_transition_ready": True,
        "native_event_selector_ready": False, "native_candidate_source_equivalence_ready": False,
        "full_script_feedback_ready": False, "original_trace_ready": False,
        "battle_forecast_ready": False, "planner_usable": False,
    }
    result["result_sha256"] = _canonical_digest(result)
    return result


__all__ = [
    "GAME_VERSION_12003", "EXECUTABLE_SHA256_12003",
    "STOCK_PHASE_EVENT_MANIFEST_SHA256_12003", "SUPPORTED_SELECTED_EVENT_KEYS_12003",
    "PHASE_EVENT_TRANSITION_VERSION_12003", "PhaseEventScriptOutcome12003",
    "load_stock_phase_events_12003", "execute_selected_phase_event_12003",
]
