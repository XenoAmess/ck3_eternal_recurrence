"""Independent stock education-point SOURCE components for CK3 1.20.0.4.

Consumes already qualified facts. It performs no acquisition or educator choice.
Rational source sums do not qualify native AST, random-list normalization,
scheduling, education outcomes, or engine arithmetic.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Mapping

CHILD_TRAIT_KEYS_12004 = (
    "intellect_good_1", "intellect_good_2", "intellect_good_3",
    "intellect_bad_1", "intellect_bad_2", "intellect_bad_3",
    "shrewd", "dull", "inbred",
)
EDUCATOR_TRAIT_KEYS_12004 = CHILD_TRAIT_KEYS_12004[:-1]
SOURCE_PACKET_SHA256_12004 = (
    "8b575eec9130fb1e4fbcfb380b2870e12fdb51c76993259ee88ef26f52e69230"
)


@dataclass(frozen=True, slots=True)
class EducationPointEducatorValues12004:
    """Qualified facts for the actual selected full ID, each independently optional."""

    character_id: int
    traits: Mapping[str, bool | None] | None = None
    focus_skill_value: int | None = None
    learning_skill_value: int | None = None
    better_ward_education: bool | None = None
    service_house_improved_educator_outcome_chance: bool | None = None


@dataclass(frozen=True, slots=True)
class EducationPointSourceInputs12004:
    """Facts bound to this current child; selection and affinity belong to other owners.

    A missing trait predicate is unknown, never false. educator_present=True can
    coexist with an unresolved random educator ID. Known-null is False only.
    Skill operands are qualified integer source values, not inferred displayed
    or unscaled native memory. Affinity predicates must already bind this child
    and its selected focus; this module does not resolve that focus.
    """

    child_character_id: int | None
    child_traits: Mapping[str, bool | None] | None = None
    child_traits_unavailable_reason: str | None = None
    educator_present: bool | None = None
    educator_id: int | None = None
    educator_values: EducationPointEducatorValues12004 | None = None
    focus_affinity: bool | None = None
    focus_disaffinity: bool | None = None


def _full_id(value: object) -> bool:
    return type(value) is int and -(2**31) <= value < 2**31 and value != -1


def _bool(value: object) -> bool | None:
    return value if type(value) is bool else None


def education_point_inputs_from_child_row_12004(
    row: Mapping[str, object] | None, **qualified_fields: object,
) -> EducationPointSourceInputs12004:
    """Adapt either the registered child row or owner46's copied direct row.

    observed_inputs_complete, age/sex, childhood_traits and native_focus do not
    gate this optional leaf. The caller first qualifies the current row/full ID;
    this adapter does not acquire or prove current native receiver generation.
    """
    raw = row if isinstance(row, Mapping) else {}
    character_id = raw.get("character_id")
    leaf = raw.get("education_point_traits")
    predicates = None
    reason = "education_point_traits_not_observed"
    if not _full_id(character_id):
        reason = "child_complete_character_id_unavailable"
    elif isinstance(leaf, Mapping):
        if leaf.get("status") == "unavailable":
            supplied_reason = leaf.get("unavailable_reason")
            reason = (supplied_reason if isinstance(supplied_reason, str) and supplied_reason
                      else "education_point_traits_unavailable")
        elif (leaf.get("source") == "native_character_has_trait"
              and leaf.get("status") == "available"
              and leaf.get("unavailable_reason") is None
              and leaf.get("queried_trait_keys") == list(CHILD_TRAIT_KEYS_12004)):
            present = leaf.get("present_trait_keys")
            if (isinstance(present, list)
                    and present == [key for key in CHILD_TRAIT_KEYS_12004 if key in present]):
                predicates = {key: key in present for key in CHILD_TRAIT_KEYS_12004}
                reason = None
            else:
                reason = "education_point_traits_malformed"
        else:
            reason = "education_point_traits_malformed"
    return EducationPointSourceInputs12004(
        child_character_id=character_id if _full_id(character_id) else None,
        child_traits=predicates,
        child_traits_unavailable_reason=reason,
        **qualified_fields,
    )


def _predicate(traits: Mapping[str, bool | None] | None,
               keys: tuple[str, ...]) -> bool | None:
    values = [_bool(traits.get(key)) if isinstance(traits, Mapping) else None for key in keys]
    if any(value is True for value in values):
        return True
    return False if all(value is False for value in values) else None


def _encoded(value: Fraction | None) -> dict[str, int] | None:
    return None if value is None else {
        "numerator": value.numerator, "denominator": value.denominator,
    }


def _component(key: str, lines: str, operation: str,
               predicate: bool | None, value: Fraction | None,
               reason: str | None = None, **details: object) -> dict[str, object]:
    return {
        "key": key,
        "source_lines": lines,
        "source_operation": operation,
        "predicate": predicate,
        "available": value is not None,
        "source_value": _encoded(value),
        "unavailable_reason": None if value is not None else reason or "source_operand_unavailable",
        **details,
    }


def _conditional(key: str, lines: str, predicate: bool | None, amount: int,
                 reason: str | None = None, operation: str = "add") -> dict[str, object]:
    value = None if predicate is None else Fraction(amount if predicate else 0)
    return _component(key, lines, operation, predicate, value, reason,
                      literal_amount=amount, operation_applied=predicate)


def _first_match(traits: Mapping[str, bool | None] | None,
                 groups: tuple[tuple[tuple[str, ...], int], ...]) -> tuple[Fraction | None, list[int]]:
    """Keep reachable first-match values, ignoring branches after a known match."""
    possible: list[int] = []
    for keys, amount in groups:
        predicate = _predicate(traits, keys)
        if predicate is not False:
            possible.append(amount)
        if predicate is True:
            break
    else:
        possible.append(0)
    possibilities = sorted(set(possible))
    return (Fraction(possibilities[0]) if len(possibilities) == 1 else None, possibilities)


def _decode(component: Mapping[str, object]) -> Fraction | None:
    raw = component["source_value"]
    return None if raw is None else Fraction(raw["numerator"], raw["denominator"])


def _sum(components: list[dict[str, object]], base: int = 0) -> dict[str, object]:
    values = [_decode(component) for component in components]
    missing = [component["key"] for component, value in zip(components, values) if value is None]
    known = sum((value for value in values if value is not None), Fraction(base))
    return {
        "available": not missing,
        "source_value": None if missing else _encoded(known),
        "known_source_subtotal": _encoded(known),
        "unavailable_components": missing,
        "qualification": "source_component_sum",
    }


def compute_education_point_source_modifiers_12004(
    inputs: EducationPointSourceInputs12004,
) -> dict[str, object]:
    """Return concrete groups and ordered educator expressions independently.

    The culture statement sets the educator-success expression to ten after
    its earlier trait and skill statements. A known true condition therefore
    closes this SOURCE expression even if overwritten earlier facts are absent.
    """
    child_id = inputs.child_character_id if _full_id(inputs.child_character_id) else None
    child_traits = inputs.child_traits if child_id is not None else None
    child_reason = (inputs.child_traits_unavailable_reason
                    or "child_trait_predicate_unavailable")
    child_success = [
        _conditional("child_success_good3", "effects:302-305",
                     _predicate(child_traits, ("intellect_good_3",)), 20, child_reason),
        _conditional("child_success_good2", "effects:306-309",
                     _predicate(child_traits, ("intellect_good_2",)), 15, child_reason),
        _conditional("child_success_good1_or_shrewd", "effects:310-316",
                     _predicate(child_traits, ("intellect_good_1", "shrewd")), 10, child_reason),
    ]
    child_failure = [
        _conditional("child_failure_bad3_or_inbred", "effects:384-390",
                     _predicate(child_traits, ("intellect_bad_3", "inbred")), 20, child_reason),
        _conditional("child_failure_bad2", "effects:391-394",
                     _predicate(child_traits, ("intellect_bad_2",)), 15, child_reason),
        _conditional("child_failure_bad1_or_dull", "effects:395-401",
                     _predicate(child_traits, ("intellect_bad_1", "dull")), 10, child_reason),
    ]
    presence = _bool(inputs.educator_present)
    selected_id = inputs.educator_id if _full_id(inputs.educator_id) else None
    values = inputs.educator_values
    bound = (presence is True and selected_id is not None
             and isinstance(values, EducationPointEducatorValues12004)
             and _full_id(values.character_id) and values.character_id == selected_id)
    traits = values.traits if bound else None
    educator_reason = ("educator_presence_unavailable" if presence is None
                       else "selected_educator_values_or_identity_unavailable")
    positive, positive_possible = _first_match(traits, (
        (("intellect_good_3",), 15), (("intellect_good_2",), 10),
        (("intellect_good_1", "shrewd"), 5),
    ))
    negative, negative_possible = _first_match(traits, (
        (("intellect_bad_3",), 15), (("intellect_bad_2",), 10),
        (("intellect_bad_1", "dull"), 5),
    ))
    if presence is False:
        positive = negative = Fraction(0)
        positive_possible = negative_possible = [0]
    elif not bound:
        positive = negative = None
    success_chain = _component(
        "educator_success_trait_chain", "effects:318-339", "value",
        presence, positive, educator_reason, possible_source_values=positive_possible,
    )
    failure_chain = _component(
        "educator_failure_trait_chain", "effects:403-429", "value",
        presence, negative, educator_reason, possible_source_values=negative_possible,
    )

    def skill_component(key: str, lines: str, raw: object, factor: Fraction) -> dict[str, object]:
        value = (Fraction(0) if presence is False else
                 Fraction(raw) * factor if bound and type(raw) is int else None)
        return _component(key, lines, "add", presence, value,
                          "selected_educator_skill_unavailable",
                          factor=_encoded(factor))

    skill = skill_component("educator_focus_skill", "effects:340-344; values:5",
                            values.focus_skill_value if bound else None, Fraction(2, 5))
    learning = skill_component("educator_learning", "effects:345-349; values:6",
                               values.learning_skill_value if bound else None, Fraction(1, 5))
    culture_predicate = (False if presence is False else
                         _bool(values.better_ward_education) if bound else None)
    culture = _conditional("educator_culture", "effects:350-354", culture_predicate, 10,
                           "selected_educator_culture_parameter_unavailable", operation="value")
    before_culture = _sum([success_chain, skill, learning])
    prior_value = (None if before_culture["source_value"] is None else
                   Fraction(before_culture["source_value"]["numerator"],
                            before_culture["source_value"]["denominator"]))
    if culture_predicate is True:
        educator_success_value = Fraction(10)
    elif culture_predicate is False:
        educator_success_value = prior_value
    else:
        # Either route gives the same source value only when prior is already ten.
        educator_success_value = Fraction(10) if prior_value == 10 else None
    educator_success = _component(
        "educator_success_expression", "effects:318-357", "add", presence,
        educator_success_value, "educator_success_expression_unavailable",
        ordered_component_keys=[success_chain["key"], skill["key"], learning["key"], culture["key"]],
        before_culture=before_culture,
        culture_statement="value = 10",
    )
    educator_failure = _component(
        "educator_failure_expression", "effects:403-429", "add", presence,
        negative, educator_reason,
    )
    house_predicate = (False if presence is False else
                       _bool(values.service_house_improved_educator_outcome_chance) if bound else None)
    house = _conditional("educator_house", "effects:371-374", house_predicate, 5,
                         "selected_educator_house_parameter_unavailable")
    affinity = _conditional("child_focus_affinity", "effects:359-363; values:3",
                            _bool(inputs.focus_affinity) if child_id is not None else None, 20,
                            "qualified_child_focus_affinity_unavailable")
    disaffinity = _conditional("child_focus_disaffinity", "effects:365-369; values:4",
                               _bool(inputs.focus_disaffinity) if child_id is not None else None, -20,
                               "qualified_child_focus_disaffinity_unavailable")
    no_educator = _conditional("no_educator_failure", "effects:430-435",
                              None if presence is None else not presence, 20,
                              "educator_presence_unavailable")
    components = (child_success + [success_chain, skill, learning, culture, educator_success,
                                   affinity, disaffinity, house] +
                  child_failure + [failure_chain, educator_failure, no_educator])
    return {
        "schema": "education_point_source_modifiers_12004.v1",
        "qualification": "pure_source_components_only",
        "source_packet_sha256": SOURCE_PACKET_SHA256_12004,
        "child_character_id": child_id,
        "child_identity_available": child_id is not None,
        "child_identity_unavailable_reason": (
            None if child_id is not None else "child_complete_character_id_unavailable"),
        "educator_present": presence,
        "educator_id": selected_id if presence is True else None,
        "educator_values_bound": bound,
        "components": {component["key"]: component for component in components},
        "child_success_traits": _sum(child_success),
        "child_failure_traits": _sum(child_failure),
        "success_source_components": _sum(
            child_success + [educator_success, affinity, disaffinity, house], base=60),
        "failure_source_components": _sum(
            child_failure + [educator_failure, no_educator], base=40),
        "normalized_success_probability": None,
        "full_native_ast_ready": False,
        "education_outcome_ready": False,
        "native_action_performed": False,
    }

