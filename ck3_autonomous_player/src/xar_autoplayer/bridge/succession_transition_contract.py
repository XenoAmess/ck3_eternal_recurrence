"""Pure pre-death expectation and post-succession reconciliation contract."""

from __future__ import annotations

import copy
import re
from typing import Final

from .turn_bundle_contract import TURN_BUNDLE_V1_SCHEMA


SUCCESSION_EXPECTATION_V1_SCHEMA: Final = (
    "xar.ck3.succession-expectation/v1"
)
SUCCESSION_RECONCILIATION_V1_SCHEMA: Final = (
    "xar.ck3.succession-reconciliation/v1"
)
CONTINUE_AS_RECONCILED_SUCCESSOR_STEP: Final = (
    "continue-as-reconciled-successor"
)
SUCCESSION_LIFECYCLE_BINDING_V1_SCHEMA: Final = (
    "xar.ck3.succession-lifecycle-binding/v1"
)
ROGUE_ONE_LIFE: Final = "rogue_one_life"
ORDINARY_CAMPAIGN_SUCCESSION: Final = "ordinary_campaign_succession"
UNKNOWN_SUCCESSION_LIFECYCLE: Final = "unknown"
_SUCCESSION_LIFECYCLES: Final = {
    ROGUE_ONE_LIFE,
    ORDINARY_CAMPAIGN_SUCCESSION,
    UNKNOWN_SUCCESSION_LIFECYCLE,
}
_LIFECYCLE_BINDING_FIELDS: Final = {
    "schema",
    "lifecycle",
    "xar_enabled",
    "pact_contract",
    "source",
    "environment_sha256",
}
_EXPECTATION_FIELDS: Final = {
    "schema",
    "status",
    "binding",
    "expectation_state",
    "predecessor_character_id",
    "expected_successor_character_id",
    "title_expectations",
    "risk_state",
    "unavailable_reason",
}
_EXPECTATION_BINDING_FIELDS: Final = {
    "snapshot_id",
    "revision",
    "native_revision",
    "date_raw",
    "episode_run_id",
    "episode_character_id",
}


def legacy_rogue_one_life_binding_v1() -> dict[str, object]:
    """Return the pre-profile-binding behavior for old driver call sites."""

    return {
        "schema": SUCCESSION_LIFECYCLE_BINDING_V1_SCHEMA,
        "lifecycle": ROGUE_ONE_LIFE,
        "xar_enabled": "xar_on",
        "pact_contract": "terminal_settlement_required",
        "source": "legacy-driver-default",
        "environment_sha256": None,
    }


def unknown_succession_lifecycle_binding_v1() -> dict[str, object]:
    """Return an explicit fail-closed binding for an unclassified save."""

    return {
        "schema": SUCCESSION_LIFECYCLE_BINDING_V1_SCHEMA,
        "lifecycle": UNKNOWN_SUCCESSION_LIFECYCLE,
        "xar_enabled": None,
        "pact_contract": "unknown",
        "source": "unbound",
        "environment_sha256": None,
    }


def normalize_succession_lifecycle_binding_v1(
    value: object,
) -> dict[str, object]:
    """Validate the frozen support profile used across succession recovery."""

    if not isinstance(value, dict) or set(value) != _LIFECYCLE_BINDING_FIELDS:
        raise ValueError("succession lifecycle binding is malformed")
    if value.get("schema") != SUCCESSION_LIFECYCLE_BINDING_V1_SCHEMA:
        raise ValueError("succession lifecycle binding schema is malformed")
    lifecycle = value.get("lifecycle")
    if lifecycle not in _SUCCESSION_LIFECYCLES:
        raise ValueError("succession lifecycle is malformed")
    xar_enabled = value.get("xar_enabled")
    pact_contract = value.get("pact_contract")
    source = value.get("source")
    environment_sha256 = value.get("environment_sha256")
    if not isinstance(source, str) or not source:
        raise ValueError("succession lifecycle source is malformed")
    if environment_sha256 is not None and not (
        isinstance(environment_sha256, str)
        and re.fullmatch(r"[0-9a-f]{64}", environment_sha256)
    ):
        raise ValueError("succession lifecycle environment digest is malformed")
    expected = {
        ROGUE_ONE_LIFE: ("xar_on", "terminal_settlement_required"),
        ORDINARY_CAMPAIGN_SUCCESSION: (
            "xar_off",
            "absent_by_fresh_campaign_xar_off_contract",
        ),
        UNKNOWN_SUCCESSION_LIFECYCLE: (None, "unknown"),
    }[str(lifecycle)]
    if (xar_enabled, pact_contract) != expected:
        raise ValueError("succession lifecycle support profile is inconsistent")
    if lifecycle == ORDINARY_CAMPAIGN_SUCCESSION and environment_sha256 is None:
        raise ValueError(
            "ordinary campaign succession requires a frozen environment"
        )
    return {
        "schema": SUCCESSION_LIFECYCLE_BINDING_V1_SCHEMA,
        "lifecycle": lifecycle,
        "xar_enabled": xar_enabled,
        "pact_contract": pact_contract,
        "source": source,
        "environment_sha256": environment_sha256,
    }


def bind_succession_lifecycle_from_environment_v1(
    manifest: object,
    *,
    lifecycle: str,
    ordinary_campaign_no_pact: bool = False,
) -> dict[str, object]:
    """Bind a run to one prepared rule profile without inferring save state.

    The ordinary mode is intentionally explicit: the prepared profile must
    select ``xar_off`` and the caller must attest that the candidate is a
    fresh campaign in which no pact was signed.  A legacy ``xar_on`` save is
    therefore never reclassified merely because its settlement is absent.
    """

    if not isinstance(manifest, dict):
        raise ValueError("prepared environment manifest is malformed")
    rules = manifest.get("rules")
    profile = rules.get("profile") if isinstance(rules, dict) else None
    if not isinstance(profile, list):
        raise ValueError("prepared environment game-rule profile is malformed")
    xar_settings = [
        row.get("setting")
        for row in profile
        if isinstance(row, dict) and row.get("rule") == "xar_enabled"
    ]
    if len(xar_settings) != 1 or xar_settings[0] not in {"xar_on", "xar_off"}:
        raise ValueError("prepared environment lacks one frozen xar_enabled rule")
    environment_sha256 = manifest.get("environment_sha256")
    if not (
        isinstance(environment_sha256, str)
        and re.fullmatch(r"[0-9a-f]{64}", environment_sha256)
    ):
        raise ValueError("prepared environment digest is malformed")
    if lifecycle == ROGUE_ONE_LIFE:
        if xar_settings[0] != "xar_on":
            raise ValueError("rogue one-life mode requires frozen xar_on")
        if ordinary_campaign_no_pact:
            raise ValueError("rogue one-life mode cannot claim ordinary no-pact")
        pact_contract = "terminal_settlement_required"
    elif lifecycle == ORDINARY_CAMPAIGN_SUCCESSION:
        if xar_settings[0] != "xar_off":
            raise ValueError("ordinary campaign succession requires frozen xar_off")
        if ordinary_campaign_no_pact is not True:
            raise ValueError(
                "ordinary campaign succession requires a fresh no-pact contract"
            )
        pact_contract = "absent_by_fresh_campaign_xar_off_contract"
    else:
        raise ValueError("production succession lifecycle must be explicit")
    return normalize_succession_lifecycle_binding_v1(
        {
            "schema": SUCCESSION_LIFECYCLE_BINDING_V1_SCHEMA,
            "lifecycle": lifecycle,
            "xar_enabled": xar_settings[0],
            "pact_contract": pact_contract,
            "source": "prepared-environment-manifest",
            "environment_sha256": environment_sha256,
        }
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
    current_row_fields = {
        "title",
        "first_heir_character_id",
        "capital_province_id",
        "primary",
    }
    legacy_row_fields = current_row_fields - {"capital_province_id"}
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or frozenset(row) not in {
            frozenset(current_row_fields),
            frozenset(legacy_row_fields),
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
        capital_province_id = row.get("capital_province_id")
        if capital_province_id is not None:
            _positive_int(
                capital_province_id,
                f"{name} title-heir row {index} capital province",
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
    return normalize_succession_expectation_v1({
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
    })


def normalize_succession_expectation_v1(value: object) -> dict[str, object]:
    """Validate a persisted expectation without consulting live CK3 state."""

    if not isinstance(value, dict) or set(value) != _EXPECTATION_FIELDS:
        raise ValueError("succession expectation envelope is malformed")
    if (
        value.get("schema") != SUCCESSION_EXPECTATION_V1_SCHEMA
        or value.get("status") != "available"
        or value.get("unavailable_reason") is not None
    ):
        raise ValueError("succession expectation identity is malformed")
    binding = value.get("binding")
    if not isinstance(binding, dict) or set(binding) != _EXPECTATION_BINDING_FIELDS:
        raise ValueError("succession expectation binding is malformed")
    snapshot_id = binding.get("snapshot_id")
    episode_run_id = binding.get("episode_run_id")
    if (
        not isinstance(snapshot_id, str)
        or not snapshot_id
        or not isinstance(episode_run_id, str)
        or not episode_run_id
    ):
        raise ValueError("succession expectation string binding is malformed")
    predecessor_id = _positive_int(
        value.get("predecessor_character_id"), "predecessor_character_id"
    )
    episode_character_id = _positive_int(
        binding.get("episode_character_id"), "binding episode_character_id"
    )
    if episode_character_id != predecessor_id:
        raise ValueError("succession expectation predecessor binding disagrees")
    normalized_binding = {
        "snapshot_id": snapshot_id,
        "revision": _uint64(binding.get("revision"), "binding revision"),
        "native_revision": _uint64(
            binding.get("native_revision"), "binding native_revision"
        ),
        "date_raw": _date_raw(binding.get("date_raw"), "binding date_raw"),
        "episode_run_id": episode_run_id,
        "episode_character_id": episode_character_id,
    }
    expectation_state = value.get("expectation_state")
    expected_successor = value.get("expected_successor_character_id")
    if expectation_state == "successor_expected":
        expected_successor = _positive_int(
            expected_successor, "expected_successor_character_id"
        )
        if expected_successor == predecessor_id:
            raise ValueError("succession expectation points back to predecessor")
    elif expectation_state == "no_primary_heir":
        if expected_successor is not None:
            raise ValueError("no-primary-heir expectation invented a successor")
    else:
        raise ValueError("succession expectation state is malformed")
    risk_state = value.get("risk_state")
    if risk_state not in {
        "single_successor",
        "split_successors",
        "no_primary_heir",
    }:
        raise ValueError("succession expectation risk state is malformed")
    if (expected_successor is None) is not (risk_state == "no_primary_heir"):
        raise ValueError("succession expectation risk and successor disagree")
    rows = value.get("title_expectations")
    if not isinstance(rows, list) or not rows:
        raise ValueError("succession expectation title rows are malformed")
    normalized_rows: list[dict[str, object]] = []
    seen: set[int] = set()
    primary_rows = 0
    primary_heir: int | None = None
    prior_title_id = 0
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != {
            "title",
            "first_heir_character_id",
            "primary",
        }:
            raise ValueError(f"succession expectation row {index} is malformed")
        title = row.get("title")
        if not isinstance(title, dict):
            raise ValueError(f"succession expectation row {index} lacks a title")
        title_id = _positive_int(
            title.get("title_id"), f"succession expectation row {index} title_id"
        )
        if title_id in seen or title_id <= prior_title_id:
            raise ValueError("succession expectation title order is not canonical")
        seen.add(title_id)
        prior_title_id = title_id
        primary = row.get("primary")
        if not isinstance(primary, bool):
            raise ValueError(f"succession expectation row {index} primary is malformed")
        heir = row.get("first_heir_character_id")
        if heir is not None:
            heir = _positive_int(
                heir, f"succession expectation row {index} first heir"
            )
            if heir == predecessor_id:
                raise ValueError("succession expectation title points to predecessor")
        if primary:
            primary_rows += 1
            primary_heir = heir
        normalized_rows.append(
            {
                "title": copy.deepcopy(title),
                "first_heir_character_id": heir,
                "primary": primary,
            }
        )
    if primary_rows != 1 or primary_heir != expected_successor:
        raise ValueError("succession expectation primary title disagrees")
    return {
        "schema": SUCCESSION_EXPECTATION_V1_SCHEMA,
        "status": "available",
        "binding": normalized_binding,
        "expectation_state": expectation_state,
        "predecessor_character_id": predecessor_id,
        "expected_successor_character_id": expected_successor,
        "title_expectations": normalized_rows,
        "risk_state": risk_state,
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
