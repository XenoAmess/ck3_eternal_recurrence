"""Stable preference from already observed fertility and applicable age branches.

Every existing positive choice remains in the result. These classes order
comparative observations; they are neither eligibility nor total quality.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Mapping, Sequence


BASIS = "native_reproductive_branch_preference_v1"


def _observed_comparison(value: object) -> bool | None:
    if (isinstance(value, Mapping) and value.get("ready") is True
            and type(value.get("passes")) is bool):
        return value["passes"]
    return None


def prioritize_observed_native_reproductive_choices(
    choices: Sequence[Mapping[str, object]], rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    """Prefer pass, then partial/absent, then fail; retain stable fallback.

    The owning continuity loop supplies matching strict rich rows. A floor
    failure ignores its unused later age branch. Selector-zero readiness is
    consumed from the existing age observer, without reproducing its kernel.
    """
    by_id = {row.get("candidate_character_id"): row for row in rows}
    preferred = []
    for choice in choices:
        candidate = choice.get("candidate_character_id")
        row = by_id.get(candidate, {})
        floor = row.get("candidate_native_fertility_floor_comparison_v1")
        floor_passes = _observed_comparison(floor)
        age = None
        age_considered = floor_passes is True
        preference_class = 1
        comparison_status = "partial_or_absent"
        if floor_passes is False:
            preference_class, comparison_status = 2, "observed_fail"
        elif floor_passes is True:
            age = row.get("candidate_native_scorer_age_branch_v1")
            age_passes = _observed_comparison(age)
            if age_passes is not None:
                preference_class = 0 if age_passes else 2
                comparison_status = "observed_pass" if age_passes else "observed_fail"
        preferred.append({**deepcopy(dict(choice)), BASIS: {
            "source": "derived_observed_native_reproductive_comparison_preference",
            "candidate_character_id": candidate,
            "preference_class": preference_class,
            "comparison_status": comparison_status,
            "floor_comparison": deepcopy(dict(floor)) if isinstance(floor, Mapping) else None,
            "age_comparison": deepcopy(dict(age)) if isinstance(age, Mapping) else None,
            "age_considered": age_considered,
        }})
    return sorted(preferred, key=lambda choice: choice[BASIS]["preference_class"])
