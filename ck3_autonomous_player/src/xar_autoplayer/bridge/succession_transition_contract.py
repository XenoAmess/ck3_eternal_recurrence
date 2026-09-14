"""Pure pre-death expectation and post-succession reconciliation contract."""

from __future__ import annotations

import copy
from typing import Final

from .turn_bundle_contract import TURN_BUNDLE_V1_SCHEMA


SUCCESSION_EXPECTATION_V1_SCHEMA: Final = (
    "xar.ck3.succession-expectation/v1"
)
SUCCESSION_RECONCILIATION_V1_SCHEMA: Final = (
    "xar.ck3.succession-reconciliation/v1"
)


def _positive_int(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= 2**31 - 1
    ):
        raise ValueError(f"{name} must be a positive int32")
    return value


def _uint64(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 2**64 - 1
    ):
        raise ValueError(f"{name} must be a uint64")
    return value


def _date_raw(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not -(2**31) <= value <= 2**31 - 1
    ):
        raise ValueError(f"{name} must be an int32")
    return value


def _binding(bundle: dict[str, object], name: str) -> dict[str, object]:
    binding = bundle.get("binding")
    if not isinstance(binding, dict):
        raise ValueError(f"{name} binding is malformed")
    snapshot_id = binding.get("snapshot_id")
    if not isinstance(snapshot_id, str) or not snapshot_id:
        raise ValueError(f"{name} snapshot_id is malformed")
    return {
        "snapshot_id": snapshot_id,
        "revision": _uint64(binding.get("revision"), f"{name} revision"),
        "native_revision": _uint64(
            binding.get("native_revision"), f"{name} native_revision"
        ),
        "date_raw": _date_raw(binding.get("date_raw"), f"{name} date_raw"),
    }


def _available_value(
    component: object,
    name: str,
) -> object:
    if not isinstance(component, dict) or component.get("status") != "available":
        raise ValueError(f"{name} is not available")
    if component.get("unavailable_reason") is not None:
        raise ValueError(f"{name} carries an unavailable reason")
    return component.get("value")


def _succession_partition(
    bundle: dict[str, object],
    name: str,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    if bundle.get("schema") != TURN_BUNDLE_V1_SCHEMA:
        raise ValueError(f"{name} is not a turn-bundle v1")
    if bundle.get("status") not in {"available", "partial"}:
        raise ValueError(f"{name} is unavailable")
    succession = _available_value(bundle.get("succession_state"), name)
    if not isinstance(succession, dict):
        raise ValueError(f"{name} succession state is malformed")
    partition = _available_value(
        succession.get("partition"), f"{name} succession partition"
    )
    if not isinstance(partition, dict):
        raise ValueError(f"{name} succession partition is malformed")
    rows = partition.get("title_heirs")
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{name} title-heir rows are malformed")
    normalized_rows: list[dict[str, object]] = []
    seen: set[int] = set()
    primary_rows = 0
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != {
            "title",
            "first_heir_character_id",
            "primary",
        }:
            raise ValueError(f"{name} title-heir row {index} is malformed")
        title = row.get("title")
        if not isinstance(title, dict):
            raise ValueError(f"{name} title-heir row {index} lacks a title")
        title_id = _positive_int(
            title.get("title_id"), f"{name} title-heir row {index} title_id"
        )
        if title_id in seen:
            raise ValueError(f"{name} repeats title {title_id}")
        seen.add(title_id)
        primary = row.get("primary")
        if not isinstance(primary, bool):
            raise ValueError(f"{name} title-heir row {index} primary is malformed")
        primary_rows += int(primary)
        heir = row.get("first_heir_character_id")
        if heir is not None:
            heir = _positive_int(
                heir, f"{name} title-heir row {index} first heir"
            )
        normalized_rows.append(
            {
                "title": copy.deepcopy(title),
                "first_heir_character_id": heir,
                "primary": primary,
            }
        )
    if primary_rows != 1:
        raise ValueError(f"{name} must contain exactly one primary title")
    return succession, normalized_rows


def freeze_succession_expectation_v1(
    turn_bundle: object,
    *,
    episode_run_id: str,
    episode_character_id: int,
) -> dict[str, object]:
    """Freeze the engine's current per-title first-heir projection."""

    if not isinstance(turn_bundle, dict):
        raise ValueError("turn_bundle must be an object")
    if not isinstance(episode_run_id, str) or not episode_run_id:
        raise ValueError("episode_run_id must be a nonempty string")
    episode_character_id = _positive_int(
        episode_character_id, "episode_character_id"
    )
    binding = _binding(turn_bundle, "turn_bundle")
    succession, rows = _succession_partition(turn_bundle, "turn_bundle")
    ruler = _available_value(turn_bundle.get("ruler_state"), "turn_bundle ruler")
    if (
        not isinstance(ruler, dict)
        or _positive_int(ruler.get("character_id"), "ruler character_id")
        != episode_character_id
        or ruler.get("alive") is not True
    ):
        raise ValueError("turn_bundle ruler does not bind the living episode ruler")
    primary_heir_component = succession.get("primary_title_heir_character_id")
    if not isinstance(primary_heir_component, dict):
        raise ValueError("primary-title heir component is malformed")
    if primary_heir_component.get("status") == "available":
        expected_successor = _positive_int(
            primary_heir_component.get("value"), "expected successor"
        )
        expectation_state = "successor_expected"
    elif (
        primary_heir_component.get("status") == "not_applicable"
        and primary_heir_component.get("value") is None
        and isinstance(primary_heir_component.get("unavailable_reason"), str)
    ):
        expected_successor = None
        expectation_state = "no_primary_heir"
    else:
        raise ValueError("primary-title heir component is malformed")
    primary_rows = [row for row in rows if row["primary"]]
    if primary_rows[0]["first_heir_character_id"] != expected_successor:
        raise ValueError("primary-title row disagrees with expected successor")
    return {
        "schema": SUCCESSION_EXPECTATION_V1_SCHEMA,
        "status": "available",
        "binding": {
            **binding,
            "episode_run_id": episode_run_id,
            "episode_character_id": episode_character_id,
        },
        "expectation_state": expectation_state,
        "predecessor_character_id": episode_character_id,
        "expected_successor_character_id": expected_successor,
        "title_expectations": rows,
        "risk_state": _available_value(
            succession.get("partition"), "turn_bundle succession partition"
        ).get("risk_state"),
        "unavailable_reason": None,
    }


def reconcile_succession_transition_v1(
    expectation: object,
    post_snapshot: object,
    post_turn_bundle: object,
) -> dict[str, object]:
    """Compare one real played-character transition with a frozen projection."""

    if (
        not isinstance(expectation, dict)
        or expectation.get("schema") != SUCCESSION_EXPECTATION_V1_SCHEMA
        or expectation.get("status") != "available"
    ):
        raise ValueError("succession expectation is malformed")
    if not isinstance(post_snapshot, dict) or not isinstance(post_turn_bundle, dict):
        raise ValueError("post-transition inputs must be objects")
    pre_binding = expectation.get("binding")
    if not isinstance(pre_binding, dict):
        raise ValueError("succession expectation binding is malformed")
    predecessor_id = _positive_int(
        expectation.get("predecessor_character_id"), "predecessor_character_id"
    )
    if (
        pre_binding.get("episode_character_id") != predecessor_id
        or post_snapshot.get("episode_character_id") != predecessor_id
        or post_snapshot.get("one_life_terminal_reason")
        != "played_character_changed"
        or post_snapshot.get("one_life_terminal") is not True
        or post_snapshot.get("paused") is not True
    ):
        raise ValueError("post snapshot is not the expected paused succession transition")
    played = post_snapshot.get("played_character")
    if not isinstance(played, dict) or played.get("alive") is not True:
        raise ValueError("post snapshot lacks a living played successor")
    actual_successor_id = _positive_int(
        played.get("character_id"), "actual successor character_id"
    )
    if actual_successor_id == predecessor_id:
        raise ValueError("post snapshot did not change played character")
    post_binding = _binding(post_turn_bundle, "post_turn_bundle")
    for key in ("snapshot_id", "revision", "native_revision", "date_raw"):
        if post_snapshot.get(key) != post_binding[key]:
            raise ValueError(f"post snapshot and turn bundle disagree on {key}")
    if post_binding["date_raw"] < _date_raw(pre_binding.get("date_raw"), "pre date"):
        raise ValueError("post-transition date precedes the expectation")
    post_succession, post_rows = _succession_partition(
        post_turn_bundle, "post_turn_bundle"
    )
    del post_succession
    post_ruler = _available_value(
        post_turn_bundle.get("ruler_state"), "post_turn_bundle ruler"
    )
    if (
        not isinstance(post_ruler, dict)
        or post_ruler.get("character_id") != actual_successor_id
        or post_ruler.get("alive") is not True
    ):
        raise ValueError("post turn bundle ruler disagrees with played successor")
    expected_successor = expectation.get("expected_successor_character_id")
    if expected_successor is not None:
        expected_successor = _positive_int(expected_successor, "expected successor")
    expected_rows = expectation.get("title_expectations")
    if not isinstance(expected_rows, list) or not expected_rows:
        raise ValueError("succession expectation lacks title rows")
    expected_title_ids: set[int] = set()
    expected_inherited: list[int] = []
    expected_elsewhere: list[int] = []
    expected_without_heir: list[int] = []
    for index, row in enumerate(expected_rows):
        if not isinstance(row, dict) or not isinstance(row.get("title"), dict):
            raise ValueError(f"expectation title row {index} is malformed")
        title_id = _positive_int(
            row["title"].get("title_id"), f"expectation title row {index}"
        )
        if title_id in expected_title_ids:
            raise ValueError("succession expectation repeats a title")
        expected_title_ids.add(title_id)
        heir_id = row.get("first_heir_character_id")
        if heir_id is None:
            expected_without_heir.append(title_id)
        elif heir_id == expected_successor:
            expected_inherited.append(title_id)
        else:
            _positive_int(heir_id, f"expectation title row {index} first heir")
            expected_elsewhere.append(title_id)
    observed_title_ids = sorted(
        _positive_int(row["title"].get("title_id"), "post title_id")
        for row in post_rows
    )
    observed_set = set(observed_title_ids)
    matched = sorted(set(expected_inherited) & observed_set)
    missing = sorted(set(expected_inherited) - observed_set)
    unexpected_retained = sorted(
        (set(expected_elsewhere) | set(expected_without_heir)) & observed_set
    )
    additional = sorted(observed_set - expected_title_ids)
    successor_match = actual_successor_id == expected_successor
    title_distribution_match = not missing and not unexpected_retained
    verdict = (
        "matched"
        if successor_match and title_distribution_match
        else "unexpected_successor"
        if not successor_match
        else "title_distribution_mismatch"
    )
    return {
        "schema": SUCCESSION_RECONCILIATION_V1_SCHEMA,
        "status": "available",
        "predecessor_binding": copy.deepcopy(pre_binding),
        "successor_binding": post_binding,
        "predecessor_character_id": predecessor_id,
        "expected_successor_character_id": expected_successor,
        "actual_successor_character_id": actual_successor_id,
        "successor_match": successor_match,
        "expected_inherited_title_ids": sorted(expected_inherited),
        "matched_inherited_title_ids": matched,
        "missing_expected_inherited_title_ids": missing,
        "unexpected_retained_predecessor_title_ids": unexpected_retained,
        "expected_other_heir_title_ids": sorted(expected_elsewhere),
        "expected_without_heir_title_ids": sorted(expected_without_heir),
        "observed_additional_successor_title_ids": additional,
        "title_distribution_match": title_distribution_match,
        "verdict": verdict,
        "unavailable_reason": None,
    }
