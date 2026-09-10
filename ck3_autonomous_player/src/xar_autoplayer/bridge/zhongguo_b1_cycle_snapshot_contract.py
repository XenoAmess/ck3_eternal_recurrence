"""Portable read-only contract for the played manager's B1 cycle."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Final


QUERY_ZHONGGUO_B1_CYCLE_SNAPSHOT_V1_CAPABILITY: Final = (
    "game.command.query-zhongguo-b1-cycle-snapshot-v1"
)
QUERY_ZHONGGUO_B1_CYCLE_SNAPSHOT_V1_STEP: Final = (
    "query-zhongguo-b1-cycle-snapshot-v1"
)
QUERY_ZHONGGUO_B1_CYCLE_SNAPSHOT_V1_STEP_PREFIX: Final = (
    f"{QUERY_ZHONGGUO_B1_CYCLE_SNAPSHOT_V1_STEP}-"
)
ZHONGGUO_B1_CYCLE_CASE_KIND_V1: Final = "zhongguo.b1.cycle"
ZHONGGUO_B1_CYCLE_GAME_VERSION_V1: Final = "1.19.0.6"
ZHONGGUO_B1_CYCLE_EXE_SHA256_V1: Final = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
ZHONGGUO_B1_CYCLE_BACKEND_ID_V1: Final = (
    "ck3-1.19.0.6-native-zhongguo-b1-cycle-snapshot-v1"
)
ZHONGGUO_B1_CYCLE_CONSUMER_ID_V1: Final = (
    "xar-autoplayer-zhongguo-b1-cycle-snapshot-v1"
)
ZHONGGUO_B1_CYCLE_ALLOWLIST_ID_V1: Final = "zg361-b1-cycle-manager-v1"

_NONCE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\Z")
_TYPED = {"status", "value", "unavailable_reason"}
_FIELD_REASONS = {
    "cycle_unavailable",
    "variable_absent",
    "value_type_mismatch",
    "value_out_of_range",
    "lifecycle_not_reached",
}
_TOP_REASONS = {
    "unsupported_build",
    "requires_application_main",
    "requires_paused",
    "map_not_ready",
    "cycle_not_found",
    "cycle_inconsistent",
    "variable_identifier_unavailable",
    "variable_context_unavailable",
    "state_changed",
    "internal_error",
}
_GROUPS: Final = {
    "cycle": {
        "cycle_serial": "int",
        "case_serial": "int",
        "state": "int",
        "open_year": "int",
        "runtime_schema": "int",
        "active": "bool",
    },
    "roster": {
        "subject_count": "int",
        "before_prune_count": "int",
        "pruned_count": "int",
        "amendment_count": "int",
        "audit_version": "int",
        "reopen_required": "bool",
    },
    "processing": {
        "count": "int",
        "agenda_count": "int",
        "local_candidate_count": "int",
        "pre_calibration_valid_count": "int",
    },
    "quota": {
        "rebuild_generation": "int",
        "built_case_serial": "int",
        "book_version": "int",
        "target_top": "int",
        "target_middle": "int",
        "target_bottom": "int",
        "recount_top": "int",
        "recount_middle": "int",
        "recount_bottom": "int",
        "pre_calibration_expected_count": "int",
        "pre_calibration_mismatch": "bool",
        "pool_membership": "bool",
    },
    "closure": {
        "calibration_finalized": "bool",
        "state": "int",
        "rewards_issued": "bool",
        "publication_blocked": "bool",
    },
    "pending": {
        "open_count": "int",
        "slot_used": "int",
        "reward_expected_count": "int",
        "rewards_paid_count": "int",
        "rewards_committed": "bool",
        "watchdog_cancelled_count": "int",
        "watchdog_orphan_count": "int",
    },
}
_READINESS = {
    "manager_binding_ready",
    "cycle_identity_ready",
    "roster_ready",
    "processing_ready",
    "quota_ready",
    "closure_ready",
    "pending_ready",
    "same_frame_ready",
    "ready",
}
_PROVENANCE = {
    "game_version": ZHONGGUO_B1_CYCLE_GAME_VERSION_V1,
    "executable_sha256": ZHONGGUO_B1_CYCLE_EXE_SHA256_V1,
    "backend_id": ZHONGGUO_B1_CYCLE_BACKEND_ID_V1,
    "consumer_id": ZHONGGUO_B1_CYCLE_CONSUMER_ID_V1,
    "allowlist_id": ZHONGGUO_B1_CYCLE_ALLOWLIST_ID_V1,
    "variable_context_for_scope_rva": "0x3329A40",
    "variable_identifier_table_rva": "0x3B971A0",
    "variable_identifier_lookup_rva": "0x3B97020",
    "variable_identifier_name_rva": "0x3B97090",
    "character_storage_slot_rva": "0x570C130",
}
_FRAME = {
    "schema_version", "status", "case_kind", "request_nonce",
    "snapshot_revision", "date_raw", "paused", "player_character_id",
    "manager_character_id", *_GROUPS, "readiness", "unavailable_reason",
    "provenance",
}


@dataclass(frozen=True)
class ZhongguoB1CycleQueryV1:
    request_nonce: str


def validate_b1_cycle_request_nonce_v1(value: object) -> str:
    if not isinstance(value, str) or not _NONCE.fullmatch(value):
        raise ValueError("request_nonce must be bounded portable ASCII")
    return value


def query_zhongguo_b1_cycle_snapshot_v1_step(request_nonce: object) -> str:
    nonce = validate_b1_cycle_request_nonce_v1(request_nonce)
    return QUERY_ZHONGGUO_B1_CYCLE_SNAPSHOT_V1_STEP_PREFIX + nonce.encode("ascii").hex()


def parse_query_zhongguo_b1_cycle_snapshot_v1_step(
    step: object,
) -> ZhongguoB1CycleQueryV1 | None:
    if not isinstance(step, str) or not step.startswith(
        QUERY_ZHONGGUO_B1_CYCLE_SNAPSHOT_V1_STEP_PREFIX
    ):
        return None
    encoded = step.removeprefix(QUERY_ZHONGGUO_B1_CYCLE_SNAPSHOT_V1_STEP_PREFIX)
    try:
        if not encoded or len(encoded) % 2:
            return None
        nonce = bytes.fromhex(encoded).decode("ascii")
        nonce = validate_b1_cycle_request_nonce_v1(nonce)
        if nonce.encode("ascii").hex() != encoded:
            return None
    except (UnicodeDecodeError, ValueError):
        return None
    return ZhongguoB1CycleQueryV1(nonce)


def _exact(value: object, keys: set[str], name: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{name} must contain exactly the v1 fields")
    return value


def _uint(value: object, name: str, *, positive: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < int(positive):
        raise ValueError(f"{name} must be a bounded integer")
    return value


def _typed(value: object, kind: str, name: str) -> dict[str, object]:
    field = _exact(value, _TYPED, name)
    status, raw, reason = field["status"], field["value"], field["unavailable_reason"]
    if status == "available":
        if reason is not None or (kind == "bool" and not isinstance(raw, bool)) or (
            kind == "int" and (isinstance(raw, bool) or not isinstance(raw, int))
        ):
            raise ValueError(f"{name} has invalid available value")
    elif status == "unavailable":
        if raw is not None or reason not in _FIELD_REASONS:
            raise ValueError(f"{name} has invalid unavailable value")
    else:
        raise ValueError(f"{name}.status is invalid")
    return dict(field)


def _value(groups: dict[str, dict[str, dict[str, object]]], group: str, key: str):
    field = groups[group][key]
    return field["value"] if field["status"] == "available" else None


def _derive(
    groups: dict[str, dict[str, dict[str, object]]],
) -> tuple[dict[str, object], list[str]]:
    state = _value(groups, "cycle", "state")
    active = _value(groups, "cycle", "active")
    subject_n = _value(groups, "roster", "subject_count")
    processing_n = _value(groups, "processing", "count")
    target = [
        _value(groups, "quota", f"target_{band}")
        for band in ("top", "middle", "bottom")
    ]
    recount = [
        _value(groups, "quota", f"recount_{band}")
        for band in ("top", "middle", "bottom")
    ]
    open_n = _value(groups, "pending", "open_count")
    closure = _value(groups, "closure", "state")
    finalized = _value(groups, "closure", "calibration_finalized")
    rewards = _value(groups, "closure", "rewards_issued")
    generation = _value(groups, "quota", "rebuild_generation")
    counted = (subject_n, processing_n, open_n, generation, *target, *recount)
    if state is None:
        closed_coherent = None
    elif state != 8:
        closed_coherent = True
    elif closure is None or finalized is None or rewards is None:
        closed_coherent = None
    else:
        closed_coherent = closure == 4 and finalized is True and rewards is True
    invariants: dict[str, object] = {
        "active_matches_state": (
            None if state is None or active is None else active is (state < 8)
        ),
        "counts_nonnegative": (
            None if any(value is None for value in counted)
            else all(value >= 0 for value in counted)
        ),
        "processing_within_roster": (
            None if subject_n is None or processing_n is None
            else processing_n <= subject_n
        ),
        "quota_target_conserved": (
            None if processing_n is None or any(v is None for v in target)
            else sum(target) == processing_n
        ),
        "quota_recount_conserved": (
            None if processing_n is None or any(v is None for v in recount)
            else sum(recount) == processing_n
        ),
        "quota_target_matches_recount": (
            None if any(v is None for v in (*target, *recount))
            else target == recount
        ),
        "closed_state_coherent": closed_coherent,
    }
    anomalies: list[str] = []
    if state is not None and active is not (state < 8):
        anomalies.append("active_state_mismatch")
    if subject_n == 0 and active is True:
        anomalies.append("active_zero_roster")
    if (
        subject_n is not None
        and processing_n is not None
        and processing_n > subject_n
    ):
        anomalies.append("processing_exceeds_roster")
    if (
        all(v is not None for v in target)
        and processing_n is not None
        and sum(target) != processing_n
    ):
        anomalies.append("quota_target_processing_mismatch")
    if (
        all(v is not None for v in recount)
        and processing_n is not None
        and sum(recount) != processing_n
    ):
        anomalies.append("quota_recount_processing_mismatch")
    if all(v is not None for v in (*target, *recount)) and target != recount:
        anomalies.append("quota_target_recount_mismatch")
    if (
        generation is not None
        and generation > 0
        and _value(groups, "quota", "built_case_serial")
        != _value(groups, "cycle", "case_serial")
    ):
        anomalies.append("quota_generation_case_mismatch")
    if open_n is not None and open_n < 0:
        anomalies.append("negative_pending_count")
    if state == 8 and invariants["closed_state_coherent"] is False:
        anomalies.append("closed_state_incomplete")
    return invariants, anomalies


def normalize_native_zhongguo_b1_cycle_snapshot_v1(
    value: object,
    *,
    expected_query: ZhongguoB1CycleQueryV1,
    expected_snapshot_revision: int,
    expected_date_raw: int,
    expected_player_character_id: int,
) -> dict[str, object]:
    frame = _exact(value, _FRAME, "b1_cycle_snapshot")
    if (
        frame["schema_version"] != 1
        or frame["case_kind"] != ZHONGGUO_B1_CYCLE_CASE_KIND_V1
    ):
        raise ValueError("B1 cycle schema/case binding changed")
    if frame["request_nonce"] != expected_query.request_nonce:
        raise ValueError("request nonce binding changed")
    if (
        _uint(frame["snapshot_revision"], "snapshot_revision", positive=True)
        != expected_snapshot_revision
    ):
        raise ValueError("snapshot revision binding changed")
    if frame["date_raw"] != expected_date_raw or frame["paused"] is not True:
        raise ValueError("paused date binding changed")
    player = _uint(
        frame["player_character_id"], "player_character_id", positive=True
    )
    manager = _uint(
        frame["manager_character_id"], "manager_character_id", positive=True
    )
    if player != expected_player_character_id or manager != player:
        raise ValueError("played-manager binding changed")
    groups = {
        group: {
            key: _typed(
                _exact(frame[group], set(spec), group)[key],
                kind,
                f"{group}.{key}",
            )
            for key, kind in spec.items()
        }
        for group, spec in _GROUPS.items()
    }
    readiness = _exact(frame["readiness"], _READINESS, "readiness")
    if not all(isinstance(value, bool) for value in readiness.values()):
        raise ValueError("readiness must be boolean")
    provenance = _exact(frame["provenance"], set(_PROVENANCE), "provenance")
    if provenance != _PROVENANCE:
        raise ValueError("exact-build provenance changed")
    status, reason = frame["status"], frame["unavailable_reason"]
    if status == "available":
        if reason is not None or not readiness["ready"]:
            raise ValueError("available B1 cycle is not ready")
        cycle = groups["cycle"]
        if any(
            cycle[key]["status"] != "available"
            for key in ("cycle_serial", "case_serial", "state", "active")
        ):
            raise ValueError("available B1 cycle identity is partial")
        if not (1 <= cycle["state"]["value"] <= 8):
            raise ValueError("B1 cycle state is out of range")
    elif status == "unavailable":
        if reason not in _TOP_REASONS or readiness["ready"]:
            raise ValueError("unavailable B1 cycle leaks readiness")
    else:
        raise ValueError("invalid B1 cycle status")
    invariants, anomalies = _derive(groups)
    return {
        **frame,
        **groups,
        "readiness": dict(readiness),
        "provenance": dict(provenance),
        "invariants": invariants,
        "anomalies": anomalies,
    }


def query_zhongguo_b1_cycle_snapshot_v1_step_payload(request_nonce: object) -> dict[str, object]:
    return {"step": QUERY_ZHONGGUO_B1_CYCLE_SNAPSHOT_V1_STEP,
            "request_nonce": validate_b1_cycle_request_nonce_v1(request_nonce)}
