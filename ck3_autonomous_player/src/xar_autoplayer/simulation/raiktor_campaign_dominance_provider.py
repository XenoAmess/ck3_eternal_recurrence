"""Turn a stable active-war power query into a factual dominance certificate.

The provider classifies only the measured strategic-power relation.  It does
not forecast battles, value exit terms, recommend an outcome, or authorize a
CK3 command.  Five values are required so the certificate is bound to one
unchanged paused frame around two official MCP queries.
"""

from __future__ import annotations

import hashlib
import json
import re


CONTRACT = "raiktor-campaign-dominance-certificate-v2"
PROVIDER_ID = "raiktor-active-war-power-dominance-provider-v1"
PROVIDER_SCHEMA = "xar.ck3.raiktor_campaign_dominance_provider.v1"
_SHA256_RE = re.compile(r"^[0-9A-F]{64}$")


def provide_raiktor_campaign_dominance(
    before_snapshot_value: object,
    first_query_value: object,
    between_snapshot_value: object,
    second_query_value: object,
    after_snapshot_value: object,
    *,
    war_id: int,
    opponent_character_id: int,
    source_artifact_sha256: str,
) -> dict[str, object]:
    """Return one stable measured-power certificate or raise ``ValueError``."""

    requested_war_id = _full_id(war_id, "war_id")
    requested_opponent = _full_id(
        opponent_character_id, "opponent_character_id"
    )
    source_sha = _sha256(source_artifact_sha256, "source_artifact_sha256")

    snapshots = [
        _normalize_snapshot(value, requested_war_id, requested_opponent)
        for value in (
            before_snapshot_value,
            between_snapshot_value,
            after_snapshot_value,
        )
    ]
    if snapshots[1:] != snapshots[:1] * 2:
        raise ValueError("snapshot frame changed across the two queries")
    frame = snapshots[0]

    first = _normalize_query(
        first_query_value, frame, requested_opponent, expected_sequence=None
    )
    second = _normalize_query(
        second_query_value,
        frame,
        requested_opponent,
        expected_sequence=first["query_sequence"] + 1,
    )
    first_power = first["power"]
    second_power = second["power"]
    if first_power != second_power:
        raise ValueError("strategic-power payload changed across the two queries")

    actor_total = first_power["actor_power_total_raw"]
    target_total = first_power["target_power_total_raw"]
    if target_total > actor_total:
        relation = "opponent_stronger"
    elif target_total < actor_total:
        relation = "actor_stronger"
    else:
        relation = "equal"

    certificate = {
        "schema_version": 2,
        "contract": CONTRACT,
        "status": "complete",
        "frame": frame,
        "power": {
            **first_power,
            "relation": relation,
            "target_minus_actor_raw": target_total - actor_total,
        },
        "evidence": {
            "first_query_sequence": first["query_sequence"],
            "second_query_sequence": second["query_sequence"],
            "double_sample_stable": True,
            "source_artifact_sha256": source_sha,
            "query_payload_sha256": _canonical_sha256(first_power),
        },
        "producer": {
            "producer_id": PROVIDER_ID,
            "producer_version": "1.0.0",
            "production_live_input": True,
        },
        "boundaries": {
            "measured_strategic_power_ready": True,
            "campaign_outcome_forecast_ready": False,
            "exit_utility_ready": False,
            "recommended_outcome": None,
            "action_ready": False,
            "action_literal": None,
        },
    }
    return {
        "schema": PROVIDER_SCHEMA,
        "provider": PROVIDER_ID,
        "status": "available",
        "certificate_available": True,
        "campaign_dominance_certificate": certificate,
        "blockers": [],
        "boundaries": [
            "factual_power_relation_only",
            "not_a_campaign_outcome_probability",
            "not_an_exit_utility_evaluation",
            "does_not_recommend_or_submit_an_action",
        ],
    }


def normalize_raiktor_campaign_dominance_certificate(
    value: object,
) -> dict[str, object]:
    """Validate a provider result by deterministic re-rendering rules."""

    item = _dict(value, "certificate")
    if (
        item.get("schema_version") != 2
        or item.get("contract") != CONTRACT
        or item.get("status") != "complete"
    ):
        raise ValueError("campaign dominance certificate identity drifted")
    frame = _dict(item.get("frame"), "certificate.frame")
    power = _dict(item.get("power"), "certificate.power")
    evidence = _dict(item.get("evidence"), "certificate.evidence")
    producer = _dict(item.get("producer"), "certificate.producer")
    boundaries = _dict(item.get("boundaries"), "certificate.boundaries")
    if set(item) != {
        "schema_version", "contract", "status", "frame", "power",
        "evidence", "producer", "boundaries",
    }:
        raise ValueError("campaign dominance certificate keys drifted")
    if frame.get("paused") is not True:
        raise ValueError("campaign dominance certificate must be paused")
    for key in (
        "connection_generation", "ck3_pid",
    ):
        _positive_int32(frame.get(key), f"frame.{key}")
    for key in ("snapshot_revision", "native_revision"):
        _positive_int64(frame.get(key), f"frame.{key}")
    for key in ("war_id", "actor_character_id", "opponent_character_id"):
        _full_id(frame.get(key), f"frame.{key}")
    actor = _positive_int64(
        power.get("actor_power_total_raw"), "actor_power_total_raw"
    )
    target = _positive_int64(
        power.get("target_power_total_raw"), "target_power_total_raw"
    )
    scale = _positive_int32(power.get("fixed_point_scale"), "fixed_point_scale")
    ratio = _positive_int64(
        power.get("actual_power_ratio_raw"), "actual_power_ratio_raw"
    )
    if ratio != target * scale // actor:
        raise ValueError("campaign dominance ratio is inconsistent")
    expected_relation = (
        "opponent_stronger" if target > actor else
        "actor_stronger" if target < actor else "equal"
    )
    if power.get("relation") != expected_relation:
        raise ValueError("campaign dominance relation is inconsistent")
    if power.get("target_minus_actor_raw") != target - actor:
        raise ValueError("campaign dominance margin is inconsistent")
    if evidence.get("double_sample_stable") is not True:
        raise ValueError("campaign dominance double sample is not stable")
    _sha256(evidence.get("source_artifact_sha256"), "source artifact")
    _sha256(evidence.get("query_payload_sha256"), "query payload")
    if (
        producer.get("producer_id") != PROVIDER_ID
        or producer.get("production_live_input") is not True
        or boundaries != {
            "measured_strategic_power_ready": True,
            "campaign_outcome_forecast_ready": False,
            "exit_utility_ready": False,
            "recommended_outcome": None,
            "action_ready": False,
            "action_literal": None,
        }
    ):
        raise ValueError("campaign dominance boundary drifted")
    return item


def _normalize_snapshot(
    value: object, war_id: int, opponent_character_id: int
) -> dict[str, object]:
    snapshot = _structured(value, "snapshot")
    diagnostics = _dict(snapshot.get("diagnostics"), "snapshot.diagnostics")
    played = _dict(snapshot.get("played_character"), "played_character")
    actor = _full_id(played.get("character_id"), "played_character_id")
    wars = snapshot.get("active_wars")
    if not isinstance(wars, list):
        raise ValueError("active_wars must be a list")
    matches = [row for row in wars if isinstance(row, dict) and row.get("war_id") == war_id]
    if len(matches) != 1:
        raise ValueError("active war identity is not unique")
    war = matches[0]
    if (
        war.get("player_side") != "attacker"
        or war.get("player_is_primary_war_leader") is not True
        or war.get("primary_opponent_character_id") != opponent_character_id
    ):
        raise ValueError("active war opponent binding drifted")
    if snapshot.get("paused") is not True or snapshot.get("map_ready") is not True:
        raise ValueError("snapshot must be a paused ready map")
    return {
        "snapshot_id": _text(snapshot.get("snapshot_id"), "snapshot_id"),
        "snapshot_revision": _positive_int64(snapshot.get("revision"), "revision"),
        "native_revision": _positive_int64(snapshot.get("native_revision"), "native_revision"),
        "date_raw": _int32(snapshot.get("date_raw"), "date_raw"),
        "connection_generation": _positive_int32(
            diagnostics.get("connection_generation"), "connection_generation"
        ),
        "ck3_pid": _positive_int32(diagnostics.get("bridge_pid"), "bridge_pid"),
        "episode_run_id": _text(snapshot.get("episode_run_id"), "episode_run_id"),
        "paused": True,
        "war_id": war_id,
        "actor_character_id": actor,
        "opponent_character_id": opponent_character_id,
    }


def _normalize_query(
    value: object,
    frame: dict[str, object],
    opponent_character_id: int,
    *,
    expected_sequence: int | None,
) -> dict[str, object]:
    query = _structured(value, "query")
    sequence = _positive_int32(query.get("query_sequence"), "query_sequence")
    if expected_sequence is not None and sequence != expected_sequence:
        raise ValueError("strategic-power query sequence is not consecutive")
    if (
        query.get("accepted") is not True
        or query.get("status") != "available"
        or query.get("queried_snapshot_id") != frame["snapshot_id"]
        or query.get("queried_revision") != frame["snapshot_revision"]
        or query.get("queried_native_revision") != frame["native_revision"]
    ):
        raise ValueError("strategic-power query frame binding drifted")
    scopes = query.get("target_scopes")
    if scopes != [{"target_character_id": opponent_character_id,
                   "sources": ["active_war_primary_opponent"]}]:
        raise ValueError("strategic-power target scope drifted")
    observation = _dict(query.get("war_entry_assessments"), "assessment")
    rows = observation.get("assessments")
    readiness = _dict(observation.get("readiness"), "assessment.readiness")
    provenance = _dict(observation.get("provenance"), "assessment.provenance")
    if (
        observation.get("status") != "available"
        or observation.get("snapshot_revision") != frame["native_revision"]
        or observation.get("date_raw") != frame["date_raw"]
        or observation.get("actor_character_id") != frame["actor_character_id"]
        or observation.get("requested_target_character_ids") != [opponent_character_id]
        or not isinstance(rows, list) or len(rows) != 1
        or readiness.get("ready") is not True
        or any(value is not True for value in readiness.values())
    ):
        raise ValueError("strategic-power observation is incomplete")
    row = _dict(rows[0], "assessment row")
    if (
        row.get("target_character_id") != opponent_character_id
        or row.get("effective_target_character_id") != opponent_character_id
    ):
        raise ValueError("strategic-power assessment target drifted")
    scale = _positive_int32(provenance.get("fixed_point_scale"), "fixed_point_scale")
    power = {
        key: _int64(row.get(key), key)
        for key in (
            "actor_power_base_raw", "actor_network_contribution_raw",
            "actor_power_total_raw", "target_power_base_raw",
            "target_network_contribution_raw", "target_pre_adjustment_total_raw",
            "target_adjustment_delta_raw", "target_power_total_raw",
            "actual_power_ratio_raw",
        )
    }
    power["fixed_point_scale"] = scale
    if power["actor_power_total_raw"] <= 0 or power["target_power_total_raw"] <= 0:
        raise ValueError("strategic-power totals must be positive")
    if power["actual_power_ratio_raw"] != (
        power["target_power_total_raw"] * scale // power["actor_power_total_raw"]
    ):
        raise ValueError("strategic-power ratio is inconsistent")
    return {"query_sequence": sequence, "power": power}


def _structured(value: object, name: str) -> dict[str, object]:
    item = _dict(value, name)
    nested = item.get("structured_content")
    return _dict(nested, f"{name}.structured_content") if nested is not None else item


def _dict(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")
    return value


def _sha256(value: object, name: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{name} must be an uppercase SHA-256")
    return value


def _int32(value: object, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not -(2**31) <= value < 2**31:
        raise ValueError(f"{name} must be int32")
    return value


def _positive_int32(value: object, name: str) -> int:
    result = _int32(value, name)
    if result <= 0:
        raise ValueError(f"{name} must be positive")
    return result


def _full_id(value: object, name: str) -> int:
    result = _int32(value, name)
    if result == -1:
        raise ValueError(f"{name} is missing")
    return result


def _int64(value: object, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not -(2**63) <= value < 2**63:
        raise ValueError(f"{name} must be int64")
    return value


def _positive_int64(value: object, name: str) -> int:
    result = _int64(value, name)
    if result <= 0:
        raise ValueError(f"{name} must be positive")
    return result


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest().upper()


__all__ = [
    "CONTRACT", "PROVIDER_ID", "PROVIDER_SCHEMA",
    "normalize_raiktor_campaign_dominance_certificate",
    "provide_raiktor_campaign_dominance",
]
