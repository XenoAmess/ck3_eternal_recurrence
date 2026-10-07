"""Use existing native child-House previews for the ordinary continuity goal."""

from __future__ import annotations

from copy import deepcopy
from typing import Mapping, Sequence

from .first_heir_native_reproductive_preference import (
    prioritize_observed_native_reproductive_choices,
)


def choose_native_lineage_opportunity(
    driver: object, *, snapshot: Mapping[str, object],
    legality: Mapping[str, object], projection: Mapping[str, object],
    choices: Sequence[Mapping[str, object]],
) -> tuple[dict[str, object] | None, list[dict[str, object]]]:
    """Prefer observed reproductive comparisons, then use native House previews.

    The caller has already established the current unpartnered first heir and
    exact five rich final-legal rows. This reads those existing opportunities;
    every positive choice remains available in stable comparison classes. It
    neither enumerates another pool nor forecasts a birth.
    """
    rows = {row["candidate_character_id"]: row
            for row in projection["rows"]}
    observations = []
    ordered_choices = prioritize_observed_native_reproductive_choices(
        choices, projection["rows"])
    for choice in ordered_choices:
        candidate = choice["candidate_character_id"]
        row = rows[candidate]
        observation = driver.query_family_obligations_private_v1(
            expected_revision=snapshot["revision"],
            subject_character_id=legality["observed_first_heir_character_id"],
            candidate_character_id=candidate,
            request_matrilineal_option=row["matrilineal_option_selected"])
        preview = observation["native_child_house_preview"]
        if (observation.get("queried_native_revision") != snapshot["native_revision"]
                or observation["frame"]["date_raw"] != snapshot["date_raw"]
                or preview["subject_character_id"] != row["heir_character_id"]
                or preview["candidate_character_id"] != candidate):
            raise ValueError("first-heir native lineage preview changed its candidate frame")
        reason = preview["reason"]
        positive = False
        if preview["status"] == "available":
            if (preview["selected_matrilineal_option"] != row["matrilineal_option_selected"]
                    or preview["effective_matrilineal_if_accepted"] !=
                    row["effective_matrilineal_if_accepted"]):
                raise ValueError("first-heir native lineage preview changed its proposal option")
            reason = ("native_can_send_not_true"
                      if preview["complete_can_send"] is not True else
                      "native_preview_not_played_dynasty"
                      if preview["dynasty_id"] != row["played_dynasty_id"] else
                      "native_main_dynasty_opportunity")
            positive = (preview["complete_can_send"] is True
                        and preview["dynasty_id"] == row["played_dynasty_id"])
        observations.append({"candidate_character_id": candidate,
                             "reason": reason,
                             "observation": deepcopy(observation)})
        if positive:
            return {**choice,
                    "dynasty_continuity_source": "native_child_house_preview",
                    "native_child_house_preview": deepcopy(observation)}, observations
    return None, observations
