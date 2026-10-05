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
from copy import deepcopy
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
    "4991A7DD79EF1453EFC69838DBAE762308D0DF79E66F67E0D283DB8B482491F9"
)
PHASE_EVENT_TRANSITION_VERSION_12003 = "ck3-1.20.0.3-caller-selected-primary-and-requested-effects-v5"
_MANIFEST_RESOURCE = "data/ck3_1_20_0_3_stock_combat_phase_events.json"
SUPPORTED_SELECTED_EVENT_KEYS_12003 = (
    "commander_none",
    "commander_wounded",
    "commander_maimed",
    "commander_killed",
    "knight_none",
    "knight_becomes_incapable",
    "knight_become_berserker",
    "knight_shieldmaiden_attack",
    "knight_wounded",
    "knight_maimed",
    "knight_killed",
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
            _audit_selected_effect_12003(row["effect_ast"], name=f"{row['key']}.effect_ast", dependencies=dependencies)
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



_REQUEST_TRANSITIONS_12003 = frozenset((
    "request_effect_12003", "request_kill_prestige_12003",
    "request_knight_growth_12003", "request_cranial_trophy_12003",
))
KNIGHT_KILLED_SOURCE_API_SHA256_12003 = "8120F8760091DE225CACF0FED2EFBEC0AB0A09E111EF823CC139FBD62FBE4FA7"
KNIGHT_BECOME_BERSERKER_SOURCE_API_SHA256_12003 = "DF07DA498EA68E64CE2754B831A341EEE983E3BAD75D9E3B2E141B3EFF5BE6AC"
KNIGHT_SHIELDMAIDEN_SOURCE_API_SHA256_12003 = "CA3DC05906297D9F229AC350621A22F9B55200DD42AE0CD93FA292FA7D0893F6"


def _audit_selected_effect_12003(node, *, name, dependencies):
    # The existing AST audit still checks order, conditions and dependencies.
    # New leaves name authored requests, without invoking old commit helpers.
    def primitive(value):
        if isinstance(value, dict):
            if value.get("op") == "call_transition" and value.get("key") in _REQUEST_TRANSITIONS_12003:
                _mapping(value.get("args"), name + ".request.args")
                return {**value, "key": "no_op", "args": {}}
            return {key: primitive(child) for key, child in value.items()}
        if isinstance(value, list):
            return [primitive(child) for child in value]
        return value
    _audit_effect_node(primitive(node), name=name, dependencies=dependencies, direct_calls=set())


def _request_value_12003(state, path):
    if path == "@root_character_id":
        return state.root_character_id
    if path == "@selected_enemy_character_id":
        return state.selected_enemy_character_id
    if path.startswith("selected_enemy_knight."):
        if state.selected_enemy_character_id is None:
            return None
        return state.candidate(state.selected_enemy_character_id)["selected_enemy_knight_refs"].get(path)
    return state.refs.get(path)


def _request_effect_12003(state, *, operation, target, payload=None, refs=None,
                          source_event_key="knight_killed"):
    values = deepcopy(dict(payload or {}))
    missing = []
    for key, path in (refs or {}).items():
        value = _request_value_12003(state, path)
        values[key] = deepcopy(value)
        if value is None and not path.startswith("@"):
            missing.append(path)
    character_id = (state.root_character_id if target == "root" else
                    state.selected_enemy_character_id if target == "selected_enemy_knight" else None)
    record = {"transition": "selected_effect_request", "stage": "requested",
        "operation": operation, "source_event_key": source_event_key,
        "target_scope": target, "target_character_id": character_id,
        "payload": values, "unavailable_operands": missing,
        "committed": False, "queue_admission_observed": False,
        "native_callback_admission_observed": False}
    if operation == "death":
        record.update(reason_key=values["reason_key"],
                      killer_character_id=values.get("killer_character_id"))
    state.transition_log.append(record)
    _record_pending(state, "requested_" + operation + "_native_commit")


def _request_kill_prestige_12003(state, *, target="selected_enemy_knight",
                                  source_event_key="knight_killed"):
    # The recipient's reward is calculated from the opposing victim's title.
    victim = "selected_enemy_knight" if target == "root" else "root"
    value = 15000000
    has_title = _bool(_request_value_12003(state, victim + ".primary_title.exists"),
                      victim + ".primary_title.exists")
    if has_title:
        tier = _signed_int64(_request_value_12003(state, victim + ".primary_title.tier_raw"),
                             victim + ".primary_title.tier_raw")
        if tier > 0:
            value = fixed_mul(value, tier)
    if _bool(_request_value_12003(state, victim + ".is_lowborn"), victim + ".is_lowborn"):
        value //= 2
    _request_effect_12003(state, operation="add_prestige", target=target,
                         payload={"value_raw": value, "scale": 100000},
                         source_event_key=source_event_key)


def _request_knight_growth_12003(state, tape, *, target="selected_enemy_knight",
                                  source_event_key="knight_killed"):
    refs = (state.refs if target == "root" else
            state.candidate(state.selected_enemy_character_id)["selected_enemy_knight_refs"])
    prefix = target + "."
    learning = _signed_int64(refs[prefix + "skills.learning_raw"], "selected learning")
    container = _mapping(refs[prefix + "traits_and_culture_for_blademaster"], "selected blademaster")
    no_op = 6000000 - 2 * learning
    warfare = _bool(refs[prefix + "dynasty.perks.warfare_legacy_3"], "selected warfare legacy")
    if warfare:
        no_op = fixed_mul(no_op, 50000)
    blade = 1000000
    if any(_bool(x, "martial education") for x in container["education_martial"]):
        blade += 500000
    for present, points in zip(container["education_martial_prowess"], (4, 8, 12, 16), strict=True):
        if _bool(present, "martial prowess education"):
            blade += points * 100000
    for key, points in (("lifestyle_blademaster", 15), ("shrewd", 10), ("physique_good", 10)):
        if _bool(container[key], key):
            blade += points * 100000
    for present, points in zip(container["intellect_good"], (5, 15, 30), strict=True):
        if _bool(present, "intellect education"):
            blade += points * 100000
    if _bool(container["culture_blademaster_traits_more_common"], "blademaster culture"):
        blade = fixed_mul(blade, 300000)
    has_blade = _bool(container["lifestyle_blademaster"], "blademaster trait")
    xp = _signed_int64(container["lifestyle_blademaster_xp_raw"], "blademaster XP")
    if has_blade and xp >= 10000000:
        blade = 0
    selected = tape.take("knight_increase_prowess:source_order", (no_op, 3000000, blade))
    if selected == 1:
        _request_effect_12003(state, source_event_key=source_event_key, operation="add_prowess_skill", target=target,
                             payload={"value_raw": 100000, "scale": 100000})
    elif selected == 2 and not has_blade:
        _request_effect_12003(state, source_event_key=source_event_key, operation="add_trait", target=target,
                             payload={"trait": "lifestyle_blademaster"})
    elif selected == 2 and xp < 10000000:
        _request_effect_12003(state, source_event_key=source_event_key, operation="add_trait_xp", target=target,
                             payload={"trait": "lifestyle_blademaster", "value_raw": 1000000, "scale": 100000})
    state.transition_log.append({"transition": "knight_growth_selection_12003", "branch_index": selected,
                                 "weights_raw": [no_op, 3000000, blade], "committed": False})
    if not _bool(refs[prefix + "liege.exists"], "selected liege exists"):
        return
    if (_bool(refs[prefix + "liege.is_ai"], "selected liege is_ai") or
            _bool(refs[prefix + "flags.was_the_target_of_event_court_5060"], "court 5060 flag")):
        return
    exists = _bool(refs[prefix + "variables.number_of_impressive_knight_things.exists"], "impressive count exists")
    _request_effect_12003(state, source_event_key=source_event_key, operation="change_variable" if exists else "set_variable",
        target=target, payload={"name": "number_of_impressive_knight_things",
            "add_raw" if exists else "value_raw": 100000, "scale": 100000})
    if not _bool(refs[prefix + "flags.is_schedueled_for_court_5061_maintenance"], "court maintenance flag"):
        _request_effect_12003(state, source_event_key=source_event_key, operation="add_character_flag", target=target,
            payload={"flag": "is_schedueled_for_court_5061_maintenance", "years": 4})
        _request_effect_12003(state, source_event_key=source_event_key, operation="trigger_event", target=target,
            payload={"id": "court.5061", "years": 4})
    _request_effect_12003(state, source_event_key=source_event_key, operation="add_to_variable_list", target=target + ".liege",
        payload={"name": "impressive_knights"}, refs={"value": "@root_character_id" if target == "root" else "@selected_enemy_character_id"})


def _request_cranial_trophy_12003(state):
    refs = state.candidate(state.selected_enemy_character_id)["selected_enemy_knight_refs"]
    if any(_bool(refs[key], key) for key in (
        "selected_enemy_knight.faith.tengri", "selected_enemy_knight.traits.greatest_of_khans",
        "selected_enemy_knight.traits.nomadic_philosophy")):
        return
    tier = state.refs.get("root.highest_held_title_tier")
    tiers = {"tier_hegemony": (6, "illustrious"), "tier_empire": (5, "illustrious"),
        "tier_kingdom": (4, "famed"), "tier_duchy": (3, "famed"),
        "tier_county": (2, "masterwork"), "tier_barony": (1, "masterwork")}
    modifier, rarity = tiers.get(tier, (0, "common"))
    _request_effect_12003(state, operation="create_artifact", target="selected_enemy_knight",
        payload={"name": "tgp_cranial_trophy_artifact", "description": "tgp_cranial_trophy_artifact_desc",
            "rarity": rarity if tier is not None else None, "type": "miscellaneous",
            "modifier": "cranial_trophy_modifier_t" + str(modifier) if tier is not None else None,
            "decaying": True, "template": "tgp_severed_head_template", "visuals": "pocket_severed_head",
            "save_scope_as": "new_head_artifact"}, refs={"creator": "@root_character_id",
            "highest_held_title_tier": "root.highest_held_title_tier"})
    _request_effect_12003(state, operation="flag_as_trash_artifact", target="new_head_artifact", payload={"value": True})
    if _bool(refs["selected_enemy_knight.rite.decapitation_steals_prestige_as_piety"], "piety rite"):
        prestige = state.refs.get("root.prestige_raw")
        _request_effect_12003(state, operation="add_piety", target="selected_enemy_knight",
            payload={"value_raw": None if prestige is None else fixed_mul(max(_signed_int64(prestige, "victim prestige"), 0), 25000),
                "scale": 100000}, refs={"source_prestige_raw": "root.prestige_raw"})
    if _bool(refs["selected_enemy_knight.personal_tenet.cranial_trophies_spiritual_fulfillment"], "fulfillment tenet"):
        prestige = state.refs.get("root.prestige_raw")
        if prestige is None:
            _record_pending(state, "cranial_spiritual_fulfillment_victim_prestige_operand")
        elif _signed_int64(prestige, "victim prestige") > 0:
            limit = state.refs.get("caller.minor_spiritual_fulfillment_value_raw")
            value = None if limit is None else min(fixed_mul(prestige, 1000), _signed_int64(limit, "minor fulfillment value"))
            _request_effect_12003(state, operation="change_spiritual_fulfillment", target="selected_enemy_knight",
                payload={"value_raw": value, "scale": 100000},
                refs={"source_limit_raw": "caller.minor_spiritual_fulfillment_value_raw"})


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
        if name.startswith(("knight_become_berserker.", "knight_shieldmaiden_attack.")):
            purpose = name.split(".", 1)[0] + ":enemy_knight"
            candidate_weights = [
                {"character_id": int(candidate["character_id"]),
                 "weight_raw": _eval_fixed(node["weight"], state=state, candidate=candidate,
                                           name=f"{name}.weight")}
                for candidate in eligible
            ]
        else:
            purpose = "knight_killed:enemy_knight" if name.startswith("knight_killed.") else f"{name}:enemy_knight"
            candidate_weights = None
        target = tape.target(purpose, [int(candidate["character_id"]) for candidate in eligible])
        state.selected_enemy_character_id = target
        state.transition_log.append({
            "transition": "select_side_knight", "selected_character_id": target,
            "selection_origin": "caller_conditional", "native_order_ready": False,
        })
        if candidate_weights is not None:
            state.transition_log[-1]["candidate_weights_caller_order_raw"] = candidate_weights
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
        purpose = ("shieldmaiden_kill_version_randomisation:source_order"
                   if name.startswith("knight_shieldmaiden_attack.") else f"{name}:random_list")
        selected = tape.take(purpose, weights)
        if selected >= 0:
            _execute_selected_effect_12003(branches[selected]["effect"], state=state, tape=tape, name=f"{name}.branches[{selected}].effect")
    elif op == "call_transition":
        key = str(node["key"])
        args = _mapping(node["args"], f"{name}.args")
        if key == "request_effect_12003":
            _request_effect_12003(state, **dict(args))
        elif key == "request_kill_prestige_12003":
            _request_kill_prestige_12003(state, **dict(args))
        elif key == "request_knight_growth_12003":
            _request_knight_growth_12003(state, tape, **dict(args))
        elif key == "request_cranial_trophy_12003":
            _request_cranial_trophy_12003(state)
        elif key == "increase_wound_or_die":
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
        if key == "knight_killed":
            state.refs["derived.enemy_knight_meets_opponent_threshold_exists"] = any(
                _signed_int64(row["candidate_refs"]["candidate.skills.prowess_raw"], "candidate prowess")
                >= fixed_mul(_signed_int64(state.refs["root.skills.prowess_raw"], "root prowess"), 80000)
                for row in state.candidates if row["character_id"] in state.enemy_membership
            )
        if key == "knight_become_berserker":
            state.refs["derived.enemy_knight_at_or_below_berserker_threshold_exists"] = any(
                _signed_int64(row["candidate_refs"]["candidate.skills.prowess_raw"], "candidate prowess")
                <= fixed_mul(_signed_int64(state.refs["root.skills.prowess_raw"], "root prowess"), 80000)
                for row in state.candidates if row["character_id"] in state.enemy_membership
            )
        if key == "knight_shieldmaiden_attack":
            state.refs["derived.enemy_alive_knight_at_or_below_root_opponent_threshold_exists"] = any(
                _bool(row["candidate_refs"]["candidate.alive"], "candidate alive")
                and _signed_int64(row["candidate_refs"]["candidate.skills.prowess_raw"], "candidate prowess")
                <= fixed_mul(_signed_int64(state.refs["root.skills.prowess_raw"], "root prowess"), 80000)
                for row in state.candidates if row["character_id"] in state.enemy_membership
            )
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
    effect_requests = [deepcopy(row) for row in state.transition_log
                       if row.get("transition") == "selected_effect_request"]
    result: dict[str, object] = {
        "schema_version": 1,
        "status": "primary_selected_effect_transition_applied" if event_key is not None else "explicit_no_event_unchanged",
        "transition_version": PHASE_EVENT_TRANSITION_VERSION_12003,
        "effect_requests": effect_requests,
        "requested_effects_committed": False,
        "native_queue_admission_observed": False,
        "data_provenance": {
            "rules_source": stock.rules_source, "canonical_manifest_sha256": stock.canonical_manifest_sha256,
            "source_files": [{"relative_path": source.relative_path, "sha256": source.sha256} for source in stock.files],
            "loaded_playset_verified": stock.completeness.loaded_playset_verified,
            "knight_incapable_source_api_sha256": "F4DC41DD8D419DCA6DD5BED7A08CC3C426A16EAEFCB4F532ABE54CBA73D70D57",
            "knight_killed_source_api_sha256": KNIGHT_KILLED_SOURCE_API_SHA256_12003,
            "knight_become_berserker_source_api_sha256": KNIGHT_BECOME_BERSERKER_SOURCE_API_SHA256_12003,
            "knight_shieldmaiden_source_api_sha256": KNIGHT_SHIELDMAIDEN_SOURCE_API_SHA256_12003,
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
