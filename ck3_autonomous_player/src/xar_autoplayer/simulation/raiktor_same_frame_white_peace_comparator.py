"""Bind Raiktor source, white-peace, and surrender terms to one frame.

This is a pure static comparator.  It consumes the durable pre-mutation
source checkpoint produced by the source-specific lifecycle, one white-peace
terms observation, and one six-domain surrender aggregate.  It can publish a
field-by-field terms comparison, but never utility, a preferred outcome, or
an action.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re

from xar_autoplayer.bridge.raiktor_surrender_six_domain_contract import (
    normalize_raiktor_surrender_six_domain,
)
from xar_autoplayer.simulation.raiktor_continue_vs_surrender_policy import (
    canonical_policy_input_sha256,
)
from xar_autoplayer.simulation.raiktor_white_peace_comparison_contracts import (
    OBSERVATION_COMPLETENESS_KEYS,
    WhitePeaceComparisonProviderError,
    normalize_white_peace_terms_observation,
)


PROVIDER_SCHEMA = "xar.ck3.raiktor_same_frame_white_peace_comparator.v1"
SOURCE_SCHEMA = "xar.ck3.g2_source_specific_pre_mutation_checkpoint.v1"
COMPARISON_CONTRACT = "raiktor-same-frame-white-peace-comparison-v1"

_SOURCE_KEYS = {
    "schema",
    "retention_ticket_id",
    "source_set_sha256",
    "checkpoint",
    "frame",
    "frame_checks",
    "binding_sha256",
}
_SOURCE_FRAME_KEYS = {
    "ck3_pid",
    "connection_generation",
    "episode_run_id",
    "character_id",
    "war_id",
    "snapshot_id",
    "revision",
    "native_revision",
    "date_raw",
    "paused",
}
_SOURCE_CHECK_KEYS = {
    "same_pid",
    "same_connection",
    "same_snapshot",
    "same_revision",
    "same_native_revision",
    "same_date",
    "same_episode",
    "same_character",
    "paused",
    "war_still_active",
}
_CHECKPOINT_KEYS = {"path", "name", "size", "sha256", "date_raw"}
_WHITE_FRAME_KEYS = {
    "snapshot_id",
    "snapshot_revision",
    "native_revision",
    "date_raw",
    "connection_id",
    "episode_id",
    "ck3_pid",
    "paused",
    "war_id",
    "active_casus_belli_database_index",
    "active_casus_belli_key",
    "primary_attacker_character_id",
    "primary_defender_character_id",
    "claimant_character_id",
}
_WHITE_TERM_KEYS = {
    "declared_target_title_ids",
    "retained_target_title_ids",
    "claim_disposition",
    "title_holder_change_count",
    "primary_gold_transfer_raw",
    "attacker_prestige_delta_raw",
    "truce_evaluated_days",
    "prisoner_release_pairs",
    "favor_hook_will_apply",
    "hostage_variant",
}
_SHA256_RE = re.compile(r"^[0-9A-F]{64}$")


class SameFrameWhitePeaceComparisonError(ValueError):
    """A supplied comparison input is malformed or self-inconsistent."""


def provide_raiktor_same_frame_white_peace_comparison(
    *,
    source_checkpoint_value: object | None,
    white_peace_observation_value: object | None,
    surrender_terms_value: object | None,
) -> dict[str, object]:
    """Return a static terms comparison or a typed evidence requirement."""

    missing = [
        reason
        for value, reason in (
            (source_checkpoint_value, "source_checkpoint_unavailable"),
            (
                white_peace_observation_value,
                "white_peace_terms_observation_unavailable",
            ),
            (surrender_terms_value, "surrender_terms_unavailable"),
        )
        if value is None
    ]
    if missing:
        return _result(blockers=missing)

    source = _normalize_source_checkpoint(source_checkpoint_value)
    try:
        white = normalize_white_peace_terms_observation(
            white_peace_observation_value
        )
    except WhitePeaceComparisonProviderError as error:
        raise SameFrameWhitePeaceComparisonError(str(error)) from error
    white_frame = _normalize_white_frame(white["frame"])
    surrender_frame = _normalize_surrender_frame(surrender_terms_value)
    try:
        surrender = normalize_raiktor_surrender_six_domain(
            surrender_terms_value,
            expected_war_id=surrender_frame["war_id"],
            expected_snapshot_revision=surrender_frame["snapshot_revision"],
            expected_native_revision=surrender_frame["native_revision"],
            expected_date_raw=surrender_frame["date_raw"],
            expected_attacker_character_id=surrender_frame[
                "primary_attacker_character_id"
            ],
            expected_defender_character_id=surrender_frame[
                "primary_defender_character_id"
            ],
            expected_claimant_character_id=surrender_frame[
                "claimant_character_id"
            ],
        )
    except ValueError as error:
        raise SameFrameWhitePeaceComparisonError(str(error)) from error

    source_frame = source["frame"]
    surrender_sha256 = canonical_policy_input_sha256(surrender)
    checks = {
        "source_checkpoint_complete": all(source["frame_checks"].values()),
        "white_peace_complete": white["status"] == "complete"
        and white["same_frame_stable"] is True
        and all(white["completeness"].values()),
        "surrender_complete": surrender["status"] == "complete"
        and surrender["readiness"]["same_frame_stable"] is True
        and surrender["readiness"]["action_terms_ready"] is True,
        "source_white_snapshot_id_equal": source_frame["snapshot_id"]
        == white_frame["snapshot_id"],
        "source_white_revision_equal": source_frame["revision"]
        == white_frame["snapshot_revision"],
        "source_white_native_revision_equal": source_frame["native_revision"]
        == white_frame["native_revision"],
        "source_white_war_id_equal": source_frame["war_id"]
        == white_frame["war_id"],
        "source_surrender_revision_equal": source_frame["revision"]
        == surrender_frame["snapshot_revision"],
        "source_surrender_native_revision_equal": source_frame[
            "native_revision"
        ]
        == surrender_frame["native_revision"],
        "source_surrender_war_id_equal": source_frame["war_id"]
        == surrender_frame["war_id"],
        "source_white_date_equal": source_frame["date_raw"]
        == white_frame["date_raw"],
        "source_surrender_date_equal": source_frame["date_raw"]
        == surrender_frame["date_raw"],
        "source_white_pid_equal": source_frame["ck3_pid"]
        == white_frame["ck3_pid"],
        "source_player_is_primary_attacker": source_frame["character_id"]
        == white_frame["primary_attacker_character_id"]
        == surrender_frame["primary_attacker_character_id"],
        "white_surrender_frame_equal": _coarse_white_frame(white_frame)
        == surrender_frame,
        "white_observation_binds_surrender_sha256": white[
            "evaluated_surrender_terms_sha256"
        ]
        == surrender_sha256,
        "surrender_snapshot_transitively_bound": source_frame["snapshot_id"]
        == white_frame["snapshot_id"]
        and white["evaluated_surrender_terms_sha256"] == surrender_sha256,
    }
    blockers = [name for name, ready in checks.items() if not ready]
    if blockers:
        return _result(
            blockers=blockers,
            source=source,
            white=white,
            surrender=surrender,
            checks=checks,
        )

    white_terms = _normalize_white_terms(white["terms"])
    comparison = _comparison_vector(white_terms, surrender)
    binding = {
        "snapshot_id": source_frame["snapshot_id"],
        "revision": source_frame["revision"],
        "native_revision": source_frame["native_revision"],
        "war_id": source_frame["war_id"],
    }
    certificate_body = {
        "schema_version": 1,
        "contract": COMPARISON_CONTRACT,
        "status": "static-ready",
        "frame_binding": binding,
        "source_checkpoint_sha256": source["binding_sha256"],
        "white_peace_observation_sha256": canonical_policy_input_sha256(
            white
        ),
        "surrender_terms_sha256": surrender_sha256,
        "checks": checks,
        "terms_comparison": comparison,
        "utility_compared": False,
        "preferred_outcome": None,
    }
    certificate = copy.deepcopy(certificate_body)
    certificate["certificate_sha256"] = canonical_policy_input_sha256(
        certificate_body
    )
    return _result(
        blockers=[],
        source=source,
        white=white,
        surrender=surrender,
        checks=checks,
        certificate=certificate,
    )


def _normalize_source_checkpoint(value: object) -> dict[str, object]:
    item = _exact_dict(value, _SOURCE_KEYS, "source checkpoint")
    if item["schema"] != SOURCE_SCHEMA:
        raise SameFrameWhitePeaceComparisonError("source schema drifted")
    frame_item = _exact_dict(item["frame"], _SOURCE_FRAME_KEYS, "source frame")
    frame = {
        "ck3_pid": _positive_int(frame_item["ck3_pid"], "source.ck3_pid"),
        "connection_generation": _positive_int(
            frame_item["connection_generation"], "source.connection_generation"
        ),
        "episode_run_id": _text(
            frame_item["episode_run_id"], "source.episode_run_id"
        ),
        "character_id": _full_id(
            frame_item["character_id"], "source.character_id"
        ),
        "war_id": _full_id(frame_item["war_id"], "source.war_id"),
        "snapshot_id": _text(
            frame_item["snapshot_id"], "source.snapshot_id"
        ),
        "revision": _positive_int(frame_item["revision"], "source.revision"),
        "native_revision": _positive_int(
            frame_item["native_revision"], "source.native_revision"
        ),
        "date_raw": _integer(frame_item["date_raw"], "source.date_raw"),
        "paused": _boolean(frame_item["paused"], "source.paused"),
    }
    if frame["paused"] is not True:
        raise SameFrameWhitePeaceComparisonError("source frame must be paused")
    checkpoint_item = _exact_dict(
        item["checkpoint"], _CHECKPOINT_KEYS, "source checkpoint materialization"
    )
    checkpoint = {
        "path": _text(checkpoint_item["path"], "checkpoint.path"),
        "name": _text(checkpoint_item["name"], "checkpoint.name"),
        "size": _positive_int(checkpoint_item["size"], "checkpoint.size"),
        "sha256": _sha256(checkpoint_item["sha256"], "checkpoint.sha256"),
        "date_raw": _integer(checkpoint_item["date_raw"], "checkpoint.date_raw"),
    }
    if checkpoint["date_raw"] != frame["date_raw"]:
        raise SameFrameWhitePeaceComparisonError("checkpoint date drifted")
    check_item = _exact_dict(
        item["frame_checks"], _SOURCE_CHECK_KEYS, "source frame checks"
    )
    checks = {key: _boolean(check_item[key], f"frame_checks.{key}") for key in sorted(_SOURCE_CHECK_KEYS)}
    normalized_body = {
        "schema": SOURCE_SCHEMA,
        "retention_ticket_id": _sha256(
            item["retention_ticket_id"], "retention_ticket_id"
        ),
        "source_set_sha256": _sha256(
            item["source_set_sha256"], "source_set_sha256"
        ),
        "checkpoint": checkpoint,
        "frame": frame,
        "frame_checks": checks,
    }
    binding_sha = _sha256(item["binding_sha256"], "binding_sha256")
    if binding_sha != _canonical_sha256(normalized_body):
        raise SameFrameWhitePeaceComparisonError("source binding SHA drifted")
    return {**normalized_body, "binding_sha256": binding_sha}


def _normalize_white_frame(value: object) -> dict[str, object]:
    item = _exact_dict(value, _WHITE_FRAME_KEYS, "white-peace frame")
    frame = {
        "snapshot_id": _text(item["snapshot_id"], "white.snapshot_id"),
        "snapshot_revision": _positive_int(
            item["snapshot_revision"], "white.snapshot_revision"
        ),
        "native_revision": _positive_int(
            item["native_revision"], "white.native_revision"
        ),
        "date_raw": _integer(item["date_raw"], "white.date_raw"),
        "connection_id": _text(item["connection_id"], "white.connection_id"),
        "episode_id": _text(item["episode_id"], "white.episode_id"),
        "ck3_pid": _positive_int(item["ck3_pid"], "white.ck3_pid"),
        "paused": _boolean(item["paused"], "white.paused"),
        "war_id": _full_id(item["war_id"], "white.war_id"),
        "active_casus_belli_database_index": _nonnegative_int(
            item["active_casus_belli_database_index"], "white.cb_index"
        ),
        "active_casus_belli_key": _text(
            item["active_casus_belli_key"], "white.cb_key"
        ),
        "primary_attacker_character_id": _full_id(
            item["primary_attacker_character_id"], "white.attacker"
        ),
        "primary_defender_character_id": _full_id(
            item["primary_defender_character_id"], "white.defender"
        ),
        "claimant_character_id": _full_id(
            item["claimant_character_id"], "white.claimant"
        ),
    }
    if frame["paused"] is not True or frame["active_casus_belli_key"] != "raiktor_claim_cb":
        raise SameFrameWhitePeaceComparisonError("white-peace frame is not paused Raiktor")
    return frame


def _normalize_surrender_frame(value: object) -> dict[str, object]:
    root = _object(value, "surrender terms")
    frame = _object(root.get("frame"), "surrender frame")
    keys = _WHITE_FRAME_KEYS - {
        "snapshot_id",
        "connection_id",
        "episode_id",
        "ck3_pid",
    }
    return _coarse_white_frame(_normalize_white_frame({
        **frame,
        "snapshot_id": "transitive-via-white-observation",
        "connection_id": "transitive-via-white-observation",
        "episode_id": "transitive-via-white-observation",
        "ck3_pid": 1,
    })) if set(frame) == keys else _raise_schema("surrender frame")


def _coarse_white_frame(frame: dict[str, object]) -> dict[str, object]:
    return {
        key: frame[key]
        for key in (
            "snapshot_revision",
            "native_revision",
            "date_raw",
            "paused",
            "war_id",
            "active_casus_belli_database_index",
            "active_casus_belli_key",
            "primary_attacker_character_id",
            "primary_defender_character_id",
            "claimant_character_id",
        )
    }


def _normalize_white_terms(value: object) -> dict[str, object]:
    item = _exact_dict(value, _WHITE_TERM_KEYS, "white-peace terms")
    pairs_value = item["prisoner_release_pairs"]
    if not isinstance(pairs_value, list):
        raise SameFrameWhitePeaceComparisonError("white prisoner pairs must be a list")
    pairs = []
    for pair in pairs_value:
        row = _exact_dict(
            pair,
            {"jailer_character_id", "prisoner_character_id"},
            "white prisoner pair",
        )
        pairs.append(
            {
                "jailer_character_id": _full_id(row["jailer_character_id"], "jailer"),
                "prisoner_character_id": _full_id(row["prisoner_character_id"], "prisoner"),
            }
        )
    return {
        "declared_target_title_ids": _id_list(item["declared_target_title_ids"], "declared titles"),
        "retained_target_title_ids": _id_list(item["retained_target_title_ids"], "retained titles"),
        "claim_disposition": _text(item["claim_disposition"], "claim disposition"),
        "title_holder_change_count": _nonnegative_int(item["title_holder_change_count"], "title holder changes"),
        "primary_gold_transfer_raw": _nonnegative_int(item["primary_gold_transfer_raw"], "white gold"),
        "attacker_prestige_delta_raw": _integer(item["attacker_prestige_delta_raw"], "white prestige"),
        "truce_evaluated_days": _nonnegative_int(item["truce_evaluated_days"], "white truce"),
        "prisoner_release_pairs": pairs,
        "favor_hook_will_apply": _boolean(item["favor_hook_will_apply"], "white favor"),
        "hostage_variant": _text(item["hostage_variant"], "white hostage variant"),
    }


def _comparison_vector(
    white: dict[str, object], surrender: dict[str, object]
) -> dict[str, object]:
    claims = surrender["claims_base"]["payload"]
    domains = surrender["domains"]
    surrender_pairs = [
        {
            "jailer_character_id": row["jailer_character_id"],
            "prisoner_character_id": row["prisoner_character_id"],
        }
        for row in domains["prisoner_release"]["payload"]["release_pairs"]
    ]
    return {
        "declared_target_title_ids": {
            "white_peace": white["declared_target_title_ids"],
            "surrender": claims["target_title_ids"],
        },
        "claim_disposition": {
            "white_peace": white["claim_disposition"],
            "surrender": claims["attacker_defeat"]["claim_disposition"],
        },
        "primary_gold_transfer_raw": {
            "white_peace": white["primary_gold_transfer_raw"],
            "surrender": domains["gold"]["payload"]["actual_transfer"]["value"]["raw"],
        },
        "attacker_prestige_delta_raw": {
            "white_peace": white["attacker_prestige_delta_raw"],
            "surrender": domains["prestige"]["payload"]["attacker_prestige_delta"]["value"]["raw"],
        },
        "truce_evaluated_days": {
            "white_peace": white["truce_evaluated_days"],
            "surrender": domains["truce"]["payload"]["evaluated_days"],
        },
        "prisoner_release_pairs": {
            "white_peace": white["prisoner_release_pairs"],
            "surrender": surrender_pairs,
        },
        "favor_hook_will_apply": {
            "white_peace": white["favor_hook_will_apply"],
            "surrender": domains["favor_hook"]["payload"]["will_apply"],
        },
        "hostage_variant": {
            "white_peace": white["hostage_variant"],
            "surrender": "not_observed_by_six_domain_v1",
        },
    }


def _result(
    *,
    blockers: list[str],
    source: dict[str, object] | None = None,
    white: dict[str, object] | None = None,
    surrender: dict[str, object] | None = None,
    checks: dict[str, bool] | None = None,
    certificate: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "schema": PROVIDER_SCHEMA,
        "status": "static-ready" if certificate is not None else "evidence_required",
        "same_frame_comparison_ready": certificate is not None,
        "input_sha256": {
            "source": source.get("binding_sha256") if source else None,
            "white_peace": canonical_policy_input_sha256(white) if white else None,
            "surrender": canonical_policy_input_sha256(surrender) if surrender else None,
        },
        "checks": checks or {},
        "blockers": blockers,
        "comparison_certificate": certificate,
        "production_live": False,
        "production_recommendation_ready": False,
        "action_ready": False,
        "action_literal": None,
        "automatic_surrender_ready": False,
        "gen034_closed": False,
        "boundaries": [
            "static_terms_comparison_only",
            "no_owner_utility_model_or_preference",
            "no_ck3_query_launch_attach_or_mutation",
            "source_white_surrender_exact_frame_binding_required",
        ],
    }


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest().upper()


def _exact_dict(value: object, keys: set[str], name: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise SameFrameWhitePeaceComparisonError(f"{name} has a malformed schema")
    return value


def _object(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise SameFrameWhitePeaceComparisonError(f"{name} must be an object")
    return value


def _raise_schema(name: str) -> dict[str, object]:
    raise SameFrameWhitePeaceComparisonError(f"{name} has a malformed schema")


def _boolean(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise SameFrameWhitePeaceComparisonError(f"{name} must be a boolean")
    return value


def _integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SameFrameWhitePeaceComparisonError(f"{name} must be an integer")
    return value


def _positive_int(value: object, name: str) -> int:
    result = _integer(value, name)
    if result <= 0:
        raise SameFrameWhitePeaceComparisonError(f"{name} must be positive")
    return result


def _nonnegative_int(value: object, name: str) -> int:
    result = _integer(value, name)
    if result < 0:
        raise SameFrameWhitePeaceComparisonError(f"{name} must be nonnegative")
    return result


def _full_id(value: object, name: str) -> int:
    result = _integer(value, name)
    if result == -1 or result < -(2**31) or result > 2**31 - 1:
        raise SameFrameWhitePeaceComparisonError(f"{name} is not a full ID")
    return result


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SameFrameWhitePeaceComparisonError(f"{name} must be nonempty")
    return value


def _sha256(value: object, name: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise SameFrameWhitePeaceComparisonError(f"{name} must be an uppercase SHA-256")
    return value


def _id_list(value: object, name: str) -> list[int]:
    if not isinstance(value, list) or not value:
        raise SameFrameWhitePeaceComparisonError(f"{name} must be nonempty")
    result = [_full_id(item, f"{name}[]") for item in value]
    if len(result) != len(set(result)):
        raise SameFrameWhitePeaceComparisonError(f"{name} has duplicates")
    return result


__all__ = [
    "COMPARISON_CONTRACT",
    "PROVIDER_SCHEMA",
    "SOURCE_SCHEMA",
    "SameFrameWhitePeaceComparisonError",
    "provide_raiktor_same_frame_white_peace_comparison",
]
