"""Closed contract for the ZhongGuo manager-governance snapshot.

The provider exposes one product-shaped projection.  It is not an arbitrary
character-variable reader.  AI subjects require a native, typed direct-manager
selection; the caller cannot assert that authorization in the request.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Final


QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CAPABILITY: Final = (
    "game.command.query-zhongguo-manager-governance-snapshot-v1"
)
QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_STEP: Final = (
    "query-zhongguo-manager-governance-snapshot-v1"
)
QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_STEP_PREFIX: Final = (
    f"{QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_STEP}-"
)
ZHONGGUO_MANAGER_GOVERNANCE_CASE_KIND_V1: Final = (
    "zhongguo.manager-governance"
)
ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_GAME_VERSION: Final = "1.19.0.6"
ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_EXECUTABLE_SHA256: Final = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_BACKEND_ID: Final = (
    "ck3-1.19.0.6-native-zhongguo-manager-governance-snapshot-v1"
)
ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CONSUMER_ID: Final = (
    "xar-autoplayer-zhongguo-manager-governance-snapshot-v1"
)
ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_ALLOWLIST_ID: Final = (
    "zg361-manager-governance-v1"
)
ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_BRIDGE_VERSION: Final = "0.1.0"
ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_GAME_ADAPTER_ID: Final = (
    "ck3-1.19.0.6-msvc-x64"
)
ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_SOURCE_BACKEND_ID: Final = (
    "native-headless"
)
ZHONGGUO_BOUNDED_AI_MANAGER_DEPENDENCY_V1: Final = (
    "zg361-bounded-ai-direct-manager-selection-v1"
)

_NONCE_RE: Final = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\Z")
_TYPED_KEYS: Final = {"status", "value", "unavailable_reason"}
_FIELD_REASONS: Final = {
    "case_unavailable",
    "variable_absent",
    "value_type_mismatch",
    "value_out_of_range",
    "not_applicable",
    "lifecycle_not_reached",
    "receipt_not_recorded",
}
_TOP_REASONS: Final = {
    "unsupported_build",
    "requires_application_main",
    "requires_paused",
    "map_not_ready",
    "case_not_found",
    "case_inconsistent",
    "ai_manager_owner_not_player",
    "bounded_ai_manager_dependency_unavailable",
    "subject_not_bounded_ai_manager",
    "owner_filter_mismatch",
    "variable_identifier_unavailable",
    "variable_context_unavailable",
    "state_changed",
    "internal_error",
}
_SUBJECT_BINDING_KEYS: Final = {
    "kind",
    "manager_character_id",
    "owner_character_id",
    "bounded_ai_manager_dependency",
}
_CASE_KEYS: Final = {
    "owner_character_id",
    "subject_character_id",
    "cycle_serial",
    "case_serial",
    "state",
    "active",
    "revision",
}
_TEAM_KEYS: Final = {
    "status",
    "owner_character_id",
    "subject_character_id",
    "cycle_serial",
    "case_serial",
    "revision",
    "source_cycle",
    "cohort_n",
    "aggregates",
}
_AGGREGATE_KEYS: Final = {
    "targets",
    "jingcha",
    "calibration",
    "pip_success",
    "appeal_overturn",
    "retention",
    "hc_efficiency",
}
_RECEIPT_KEYS: Final = {
    "owner_character_id",
    "subject_character_id",
    "cycle_serial",
    "case_serial",
    "state",
    "choice",
}
_DISTRIBUTION_KEYS: Final = {
    "available",
    "mode",
    "rule_source",
    "top_slots",
    "middle_slots",
    "bottom_slots",
    "conserved_slots",
}
_POLICY_KEYS: Final = {
    "status",
    "owner_character_id",
    "subject_character_id",
    "source_reviewer_character_id",
    "source_cycle",
    "source_case",
    "source_revision",
    "input_revision",
    "mode",
    "rule_source",
    "due_cycle",
}
_EFFECTIVE_KEYS: Final = {
    "mode",
    "cycle",
    "source_cycle",
    "source_case",
    "input_revision",
    "settled_cycle",
    "settlement_receipt",
    "actual_cohort_n",
    "actual_bottom_slots",
}
_F035_KEYS: Final = {
    "receipt",
    "snapshot",
    "next_cycle_policy",
    "effective",
}
_SCORE_KEYS: Final = {"sum", "mode"}
_COMPONENT8_KEYS: Final = {
    "status",
    "owner_character_id",
    "subject_character_id",
    "source_cycle",
    "source_case",
    "source_revision",
    "input_revision",
    "component",
    "value",
    "due_cycle",
    "settled_by_owner_character_id",
    "settled_cycle",
    "settled_value",
    "settlement_receipt",
}
_F032_KEYS: Final = {"receipt", "manager_score", "component8"}
_READINESS_KEYS: Final = {
    "subject_binding_ready",
    "bounded_ai_dependency_ready",
    "case_identity_ready",
    "team_snapshot_ready",
    "f035_receipt_ready",
    "distribution_snapshot_ready",
    "distribution_conservation_ready",
    "next_cycle_policy_ready",
    "effective_distribution_ready",
    "distribution_settlement_ready",
    "actual_bottom_slots_ready",
    "distribution_lifecycle_ready",
    "f032_receipt_ready",
    "manager_score_ready",
    "component8_token_ready",
    "component8_settlement_ready",
    "component8_lifecycle_ready",
    "same_frame_ready",
    "ready",
}
_PROVENANCE_VALUES: Final = {
    "game_version": ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_GAME_VERSION,
    "executable_sha256": (
        ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_EXECUTABLE_SHA256
    ),
    "backend_id": ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_BACKEND_ID,
    "consumer_id": ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CONSUMER_ID,
    "allowlist_id": ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_ALLOWLIST_ID,
    "variable_context_for_scope_rva": "0x3329A40",
    "variable_identifier_table_rva": "0x3B971A0",
    "variable_identifier_lookup_rva": "0x3B97020",
    "variable_identifier_name_rva": "0x3B97090",
    "character_storage_slot_rva": "0x570C130",
}
_FRAME_KEYS: Final = {
    "schema_version",
    "status",
    "case_kind",
    "request_nonce",
    "snapshot_revision",
    "date_raw",
    "paused",
    "player_character_id",
    "subject_character_id",
    "requested_owner_character_id",
    "subject_binding",
    "f_case",
    "team_snapshot",
    "f035",
    "f032",
    "readiness",
    "unavailable_reason",
    "provenance",
}
_BUILD_KEYS: Final = {"version", "exe_sha256"}
_SOURCE_KEYS: Final = {
    "bridge_version",
    "game_adapter_id",
    "backend_id",
    "consumer_id",
    "connection_generation",
    "snapshot_id",
    "revision",
    "native_revision",
    "date_raw",
    "paused",
    "player_character_id",
}
_BINDING_KEYS: Final = {
    "request_nonce",
    "snapshot_id",
    "revision",
    "native_revision",
    "connection_generation",
    "date_raw",
    "paused",
    "player_character_id",
    "subject_character_id",
    "owner_character_id",
    "subject_binding_kind",
    "bounded_ai_manager_dependency",
    "expected_revision",
}
_FINAL_KEYS: Final = _FRAME_KEYS | {"build", "source", "binding"}


@dataclass(frozen=True)
class ZhongguoManagerGovernanceQueryV1:
    subject_character_id: int
    owner_character_id: int
    request_nonce: str


def _positive_int32(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= 2**31 - 1
    ):
        raise ValueError(f"{name} must be a positive signed int32")
    return value


def _integer(
    value: object, name: str, *, minimum: int, maximum: int
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value <= maximum
    ):
        raise ValueError(f"{name} must be an integer in range")
    return value


def _nonce(value: object) -> str:
    if not isinstance(value, str) or _NONCE_RE.fullmatch(value) is None:
        raise ValueError("request_nonce must be a 1-64 byte ASCII token")
    return value


def query_zhongguo_manager_governance_snapshot_v1_step(
    subject_character_id: object,
    owner_character_id: object,
    request_nonce: object,
) -> str:
    subject = _positive_int32(subject_character_id, "subject_character_id")
    owner = _positive_int32(owner_character_id, "owner_character_id")
    nonce = _nonce(request_nonce)
    return (
        f"{QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_STEP_PREFIX}"
        f"{subject}-{owner}-{nonce.encode('ascii').hex()}"
    )


def parse_query_zhongguo_manager_governance_snapshot_v1_step(
    step: object,
) -> ZhongguoManagerGovernanceQueryV1 | None:
    if not isinstance(step, str) or not step.startswith(
        QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_STEP_PREFIX
    ):
        return None
    parts = step.removeprefix(
        QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_STEP_PREFIX
    ).split("-", 2)
    if len(parts) != 3:
        return None
    try:
        subject = int(parts[0], 10)
        owner = int(parts[1], 10)
        if str(subject) != parts[0] or str(owner) != parts[1]:
            return None
        subject = _positive_int32(subject, "subject_character_id")
        owner = _positive_int32(owner, "owner_character_id")
        if not parts[2] or len(parts[2]) % 2:
            return None
        nonce = bytes.fromhex(parts[2]).decode("ascii")
        nonce = _nonce(nonce)
        if nonce.encode("ascii").hex() != parts[2]:
            return None
    except (UnicodeDecodeError, ValueError):
        return None
    return ZhongguoManagerGovernanceQueryV1(subject, owner, nonce)


def _exact(value: object, fields: set[str], name: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"{name} must contain exactly the v1 fields")
    return value


def _typed(value: object, name: str, kind: type) -> dict[str, object]:
    field = _exact(value, _TYPED_KEYS, name)
    status = field["status"]
    raw = field["value"]
    reason = field["unavailable_reason"]
    if status == "available":
        if reason is not None:
            raise ValueError(f"{name} available field has a reason")
        if kind is int:
            _integer(raw, name, minimum=-(2**63), maximum=2**63 - 1)
        elif kind is bool:
            if not isinstance(raw, bool):
                raise ValueError(f"{name} must contain a boolean")
        elif kind is str:
            if not isinstance(raw, str) or not raw:
                raise ValueError(f"{name} must contain a non-empty string")
        else:
            raise AssertionError("unsupported typed kind")
    elif status == "unavailable":
        if raw is not None or reason not in _FIELD_REASONS:
            raise ValueError(f"{name} has a malformed unavailable field")
    else:
        raise ValueError(f"{name} has an unknown typed status")
    return field


def _available(field: dict[str, object]) -> bool:
    return field["status"] == "available"


def _value(field: dict[str, object], name: str) -> object:
    if not _available(field):
        raise ValueError(f"{name} is unavailable")
    return field["value"]


def _all_unavailable(value: object) -> bool:
    if isinstance(value, dict):
        if set(value) == _TYPED_KEYS:
            return value.get("status") == "unavailable"
        return all(_all_unavailable(item) for item in value.values())
    return True


def _typed_group(
    value: object,
    keys: set[str],
    name: str,
    *,
    boolean_keys: set[str] = frozenset(),
    string_keys: set[str] = frozenset(),
) -> dict[str, dict[str, object]]:
    group = _exact(value, keys, name)
    return {
        key: _typed(
            group[key],
            f"{name}.{key}",
            bool if key in boolean_keys else str if key in string_keys else int,
        )
        for key in keys
    }


def _receipt_ready(
    receipt: dict[str, dict[str, object]],
    *,
    owner: int,
    subject: int,
    cycle: int,
    case_serial: int,
) -> bool:
    if not all(_available(receipt[key]) for key in _RECEIPT_KEYS):
        return False
    values = {key: _value(receipt[key], key) for key in _RECEIPT_KEYS}
    return values == {
        "owner_character_id": owner,
        "subject_character_id": subject,
        "cycle_serial": cycle,
        "case_serial": case_serial,
        "state": 1,
        "choice": values["choice"],
    } and values["choice"] in {1, 2, 3}


def _expected_bottom(cohort: int, mode: int) -> int:
    if mode == 1:
        return max(1 if cohort >= 5 else 0, cohort // 10)
    if mode == 2:
        return cohort // 20
    if mode == 3:
        return 0
    raise ValueError("distribution mode is outside 1..3")


def normalize_native_zhongguo_manager_governance_snapshot_v1(
    value: object,
    *,
    expected_query: ZhongguoManagerGovernanceQueryV1,
    expected_snapshot_revision: int,
    expected_date_raw: int,
    expected_player_character_id: int,
) -> dict[str, object]:
    frame = _exact(value, _FRAME_KEYS, "manager_governance_snapshot")
    expected_snapshot_revision = _integer(
        expected_snapshot_revision,
        "expected_snapshot_revision",
        minimum=1,
        maximum=2**64 - 1,
    )
    expected_date_raw = _integer(
        expected_date_raw,
        "expected_date_raw",
        minimum=-(2**31),
        maximum=2**31 - 1,
    )
    expected_player_character_id = _positive_int32(
        expected_player_character_id, "expected_player_character_id"
    )
    if frame["schema_version"] != 1:
        raise ValueError("schema_version must be 1")
    if frame["case_kind"] != ZHONGGUO_MANAGER_GOVERNANCE_CASE_KIND_V1:
        raise ValueError("case_kind is not manager-governance")
    if frame["request_nonce"] != expected_query.request_nonce:
        raise ValueError("request nonce drifted")
    if frame["snapshot_revision"] != expected_snapshot_revision:
        raise ValueError("snapshot revision drifted")
    if frame["date_raw"] != expected_date_raw or frame["paused"] is not True:
        raise ValueError("snapshot is not the expected paused frame")
    if frame["player_character_id"] != expected_player_character_id:
        raise ValueError("played character drifted")
    if frame["subject_character_id"] != expected_query.subject_character_id:
        raise ValueError("subject drifted")
    if (
        frame["requested_owner_character_id"]
        != expected_query.owner_character_id
    ):
        raise ValueError("owner filter drifted")
    provenance = _exact(
        frame["provenance"], set(_PROVENANCE_VALUES), "provenance"
    )
    if provenance != _PROVENANCE_VALUES:
        raise ValueError("provenance does not match the frozen ABI")
    readiness = _exact(frame["readiness"], _READINESS_KEYS, "readiness")
    if any(not isinstance(readiness[key], bool) for key in _READINESS_KEYS):
        raise ValueError("readiness must contain booleans")

    binding = _exact(
        frame["subject_binding"], _SUBJECT_BINDING_KEYS, "subject_binding"
    )
    binding_manager = _typed(
        binding["manager_character_id"],
        "subject_binding.manager_character_id",
        int,
    )
    binding_owner = _typed(
        binding["owner_character_id"],
        "subject_binding.owner_character_id",
        int,
    )
    binding_dependency = _typed(
        binding["bounded_ai_manager_dependency"],
        "subject_binding.bounded_ai_manager_dependency",
        str,
    )
    f_case = _typed_group(
        frame["f_case"], _CASE_KEYS, "f_case", boolean_keys={"active"}
    )
    team_raw = _exact(frame["team_snapshot"], _TEAM_KEYS, "team_snapshot")
    aggregates = _typed_group(
        team_raw["aggregates"], _AGGREGATE_KEYS, "team_snapshot.aggregates"
    )
    team = {
        key: _typed(team_raw[key], f"team_snapshot.{key}", int)
        for key in _TEAM_KEYS - {"aggregates"}
    }
    team.update(aggregates)
    f035_raw = _exact(frame["f035"], _F035_KEYS, "f035")
    f035_receipt = _typed_group(
        f035_raw["receipt"], _RECEIPT_KEYS, "f035.receipt"
    )
    distribution = _typed_group(
        f035_raw["snapshot"],
        _DISTRIBUTION_KEYS,
        "f035.snapshot",
        boolean_keys={"available"},
    )
    policy = _typed_group(
        f035_raw["next_cycle_policy"],
        _POLICY_KEYS,
        "f035.next_cycle_policy",
    )
    effective = _typed_group(
        f035_raw["effective"], _EFFECTIVE_KEYS, "f035.effective"
    )
    f032_raw = _exact(frame["f032"], _F032_KEYS, "f032")
    f032_receipt = _typed_group(
        f032_raw["receipt"], _RECEIPT_KEYS, "f032.receipt"
    )
    score = _typed_group(
        f032_raw["manager_score"], _SCORE_KEYS, "f032.manager_score"
    )
    component = _typed_group(
        f032_raw["component8"], _COMPONENT8_KEYS, "f032.component8"
    )

    status = frame["status"]
    if status == "unavailable":
        if frame["unavailable_reason"] not in _TOP_REASONS:
            raise ValueError("unavailable frame has an unknown reason")
        if binding["kind"] != "unavailable" or not all(
            _all_unavailable(group)
            for group in (
                binding_manager,
                binding_owner,
                binding_dependency,
                f_case,
                team,
                f035_receipt,
                distribution,
                policy,
                effective,
                f032_receipt,
                score,
                component,
            )
        ):
            raise ValueError("unavailable frame leaks manager semantics")
        if any(readiness.values()):
            raise ValueError("unavailable frame cannot be ready")
        return dict(frame)
    if status != "available" or frame["unavailable_reason"] is not None:
        raise ValueError("available frame has a malformed status")

    subject = expected_query.subject_character_id
    owner = expected_query.owner_character_id
    player = expected_player_character_id
    binding_ready = (
        _available(binding_manager)
        and _available(binding_owner)
        and _value(binding_manager, "binding manager") == subject
        and _value(binding_owner, "binding owner") == owner
    )
    bounded_ready = False
    if subject == player:
        binding_ready = binding_ready and binding["kind"] == "played_character"
        if (
            _available(binding_dependency)
            or binding_dependency["unavailable_reason"] != "not_applicable"
        ):
            raise ValueError("player subject invented an AI dependency")
    else:
        binding_ready = (
            binding_ready
            and owner == player
            and binding["kind"] == "bounded_ai_direct_manager"
            and _available(binding_dependency)
            and _value(binding_dependency, "bounded dependency")
            == ZHONGGUO_BOUNDED_AI_MANAGER_DEPENDENCY_V1
        )
        bounded_ready = binding_ready
    if not binding_ready:
        raise ValueError("available frame lacks its typed subject binding")

    case_ready = all(_available(f_case[key]) for key in _CASE_KEYS)
    if case_ready:
        case_values = {key: _value(f_case[key], key) for key in _CASE_KEYS}
        case_ready = (
            case_values["owner_character_id"] == owner
            and case_values["subject_character_id"] == subject
            and case_values["cycle_serial"] >= 1
            and case_values["case_serial"] >= 1
            and 1 <= case_values["state"] <= 5
            and case_values["revision"] >= 1
        )
    if not case_ready:
        raise ValueError("available frame lacks its F case identity")
    cycle = int(case_values["cycle_serial"])
    case_serial = int(case_values["case_serial"])

    team_values: dict[str, object] = {}
    team_ready = all(_available(team[key]) for key in team)
    if team_ready:
        team_values = {key: _value(team[key], key) for key in team}
        team_ready = (
            team_values["status"] == 1
            and team_values["owner_character_id"] == owner
            and team_values["subject_character_id"] == subject
            and team_values["cycle_serial"] == cycle
            and team_values["case_serial"] == case_serial
            and team_values["revision"] >= 1
            and team_values["source_cycle"] < cycle
            and team_values["cohort_n"] >= 0
        )
    team_revision = int(team_values["revision"]) if team_ready else -1
    cohort = int(team_values["cohort_n"]) if team_ready else -1

    f035_receipt_ready = _receipt_ready(
        f035_receipt,
        owner=owner,
        subject=subject,
        cycle=cycle,
        case_serial=case_serial,
    )
    distribution_ready = conservation_ready = policy_ready = False
    effective_ready = settlement_ready = actual_bottom_ready = False
    distribution_lifecycle_ready = False
    if f035_receipt_ready:
        f035_choice = int(_value(f035_receipt["choice"], "f035 choice"))
        if f035_choice == 3:
            if not all(
                _all_unavailable(group)
                for group in (distribution, policy, effective)
            ):
                raise ValueError("F035 C route leaks stale business values")
            distribution_lifecycle_ready = True
        else:
            d: dict[str, object] = {}
            mode = -1
            distribution_ready = all(
                _available(distribution[key]) for key in _DISTRIBUTION_KEYS
            )
            if distribution_ready:
                d = {
                    key: _value(distribution[key], key)
                    for key in _DISTRIBUTION_KEYS
                }
                mode = int(d["mode"])
                top = int(d["top_slots"])
                middle = int(d["middle_slots"])
                bottom = int(d["bottom_slots"])
                conserved = int(d["conserved_slots"])
                distribution_ready = (
                    d["available"] is True
                    and 1 <= mode <= 3
                    and 1 <= d["rule_source"] <= 3
                    and min(top, middle, bottom, conserved) >= 0
                    and top == cohort * 30 // 100
                    and bottom == _expected_bottom(cohort, mode)
                )
                conservation_ready = (
                    distribution_ready
                    and top + middle + bottom == conserved == cohort
                )
            policy_ready = all(_available(policy[key]) for key in _POLICY_KEYS)
            if policy_ready:
                p = {key: _value(policy[key], key) for key in _POLICY_KEYS}
                policy_ready = (
                    p["status"] in {1, 2}
                    and p["owner_character_id"] == subject
                    and p["subject_character_id"] == subject
                    and p["source_reviewer_character_id"] == owner
                    and p["source_cycle"] == cycle
                    and p["source_case"] == case_serial
                    and p["source_revision"] >= 1
                    and p["input_revision"] == team_revision
                    and p["mode"] == mode
                    and p["rule_source"] == d["rule_source"]
                    and p["due_cycle"] == cycle + 1
                )
            if policy_ready and p["status"] == 2:
                effective_ready = all(
                    _available(effective[key])
                    for key in {
                        "mode",
                        "cycle",
                        "source_cycle",
                        "source_case",
                        "input_revision",
                    }
                )
                if effective_ready:
                    e = {
                        key: _value(effective[key], key)
                        for key in _EFFECTIVE_KEYS
                        if _available(effective[key])
                    }
                    effective_ready = (
                        e["mode"] == mode
                        and e["cycle"] >= p["due_cycle"]
                        and e["source_cycle"] == p["source_cycle"]
                        and e["source_case"] == p["source_case"]
                        and e["input_revision"] == p["input_revision"]
                    )
                    settlement_ready = (
                        effective_ready
                        and _available(effective["settled_cycle"])
                        and _available(effective["settlement_receipt"])
                        and e["settled_cycle"] == e["cycle"]
                        and e["settlement_receipt"] == case_serial
                    )
                    actual_bottom_ready = (
                        effective_ready
                        and _available(effective["actual_cohort_n"])
                        and _available(effective["actual_bottom_slots"])
                        and e["actual_cohort_n"] >= 0
                        and e["actual_bottom_slots"]
                        == _expected_bottom(e["actual_cohort_n"], mode)
                    )
            else:
                if not _all_unavailable(effective):
                    raise ValueError("pending F035 token leaks effective values")
            distribution_lifecycle_ready = (
                distribution_ready
                and conservation_ready
                and policy_ready
                and (
                    p["status"] == 1
                    or (
                        effective_ready
                        and settlement_ready
                        and actual_bottom_ready
                    )
                )
            )

    f032_receipt_ready = _receipt_ready(
        f032_receipt,
        owner=owner,
        subject=subject,
        cycle=cycle,
        case_serial=case_serial,
    )
    score_ready = component_ready = component_settlement_ready = False
    component_lifecycle_ready = False
    if f032_receipt_ready:
        f032_choice = int(_value(f032_receipt["choice"], "f032 choice"))
        if f032_choice == 3:
            if not _all_unavailable(score) or not _all_unavailable(component):
                raise ValueError("F032 C route leaks stale business values")
            component_lifecycle_ready = True
        else:
            score_ready = all(_available(score[key]) for key in _SCORE_KEYS)
            if score_ready:
                score_sum = int(_value(score["sum"], "score sum"))
                score_ready = _value(score["mode"], "score mode") == f032_choice
            component_ready = all(
                _available(component[key])
                for key in _COMPONENT8_KEYS
                - {
                    "settled_by_owner_character_id",
                    "settled_cycle",
                    "settled_value",
                    "settlement_receipt",
                }
            )
            if component_ready:
                c = {
                    key: _value(component[key], key)
                    for key in _COMPONENT8_KEYS
                    if _available(component[key])
                }
                component_ready = (
                    score_ready
                    and c["status"] in {1, 2}
                    and c["owner_character_id"] == owner
                    and c["subject_character_id"] == subject
                    and c["source_cycle"] == cycle
                    and c["source_case"] == case_serial
                    and c["source_revision"] >= 1
                    and c["input_revision"] == team_revision
                    and c["component"] == 8
                    and c["value"] == score_sum
                    and c["due_cycle"] == cycle + 1
                )
                if component_ready and c["status"] == 2:
                    component_settlement_ready = all(
                        _available(component[key])
                        for key in {
                            "settled_by_owner_character_id",
                            "settled_cycle",
                            "settled_value",
                            "settlement_receipt",
                        }
                    ) and (
                        c["settled_cycle"] >= c["due_cycle"]
                        and c["settled_value"] == c["value"]
                        and c["settlement_receipt"] == case_serial
                    )
                elif component_ready and not _all_unavailable(
                    {
                        key: component[key]
                        for key in {
                            "settled_by_owner_character_id",
                            "settled_cycle",
                            "settled_value",
                            "settlement_receipt",
                        }
                    }
                ):
                    raise ValueError("pending component-8 token leaks settlement")
            component_lifecycle_ready = component_ready and (
                c["status"] == 1 or component_settlement_ready
            )

    computed = {
        "subject_binding_ready": binding_ready,
        "bounded_ai_dependency_ready": bounded_ready,
        "case_identity_ready": case_ready,
        "team_snapshot_ready": team_ready,
        "f035_receipt_ready": f035_receipt_ready,
        "distribution_snapshot_ready": distribution_ready,
        "distribution_conservation_ready": conservation_ready,
        "next_cycle_policy_ready": policy_ready,
        "effective_distribution_ready": effective_ready,
        "distribution_settlement_ready": settlement_ready,
        "actual_bottom_slots_ready": actual_bottom_ready,
        "distribution_lifecycle_ready": distribution_lifecycle_ready,
        "f032_receipt_ready": f032_receipt_ready,
        "manager_score_ready": score_ready,
        "component8_token_ready": component_ready,
        "component8_settlement_ready": component_settlement_ready,
        "component8_lifecycle_ready": component_lifecycle_ready,
        "same_frame_ready": True,
        "ready": (
            binding_ready
            and case_ready
            and team_ready
            and f035_receipt_ready
            and distribution_lifecycle_ready
            and f032_receipt_ready
            and component_lifecycle_ready
        ),
    }
    if readiness != computed:
        raise ValueError("readiness disagrees with manager lifecycle facts")
    return dict(frame)


def normalize_zhongguo_manager_governance_snapshot_v1_response(
    value: object,
    *,
    expected_query: ZhongguoManagerGovernanceQueryV1,
    expected_snapshot_id: str,
    expected_revision: int,
    expected_native_revision: int,
    expected_connection_generation: int,
    expected_date_raw: int,
    expected_player_character_id: int,
) -> dict[str, object]:
    final = _exact(value, _FINAL_KEYS, "manager_governance_response")
    native = normalize_native_zhongguo_manager_governance_snapshot_v1(
        {key: final[key] for key in _FRAME_KEYS},
        expected_query=expected_query,
        expected_snapshot_revision=expected_native_revision,
        expected_date_raw=expected_date_raw,
        expected_player_character_id=expected_player_character_id,
    )
    build = _exact(final["build"], _BUILD_KEYS, "build")
    if build != {
        "version": ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_GAME_VERSION,
        "exe_sha256": (
            ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_EXECUTABLE_SHA256
        ),
    }:
        raise ValueError("build does not match the exact CK3 build")
    source = _exact(final["source"], _SOURCE_KEYS, "source")
    expected_source = {
        "bridge_version": (
            ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_BRIDGE_VERSION
        ),
        "game_adapter_id": (
            ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_GAME_ADAPTER_ID
        ),
        "backend_id": (
            ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_SOURCE_BACKEND_ID
        ),
        "consumer_id": (
            ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CONSUMER_ID
        ),
        "connection_generation": expected_connection_generation,
        "snapshot_id": expected_snapshot_id,
        "revision": expected_revision,
        "native_revision": expected_native_revision,
        "date_raw": expected_date_raw,
        "paused": True,
        "player_character_id": expected_player_character_id,
    }
    if source != expected_source:
        raise ValueError("source does not match the paused snapshot")
    subject_binding = native["subject_binding"]
    assert isinstance(subject_binding, dict)
    dependency_field = subject_binding["bounded_ai_manager_dependency"]
    assert isinstance(dependency_field, dict)
    dependency = (
        dependency_field["value"]
        if dependency_field["status"] == "available"
        else None
    )
    binding = _exact(final["binding"], _BINDING_KEYS, "binding")
    expected_binding = {
        "request_nonce": expected_query.request_nonce,
        "snapshot_id": expected_snapshot_id,
        "revision": expected_revision,
        "native_revision": expected_native_revision,
        "connection_generation": expected_connection_generation,
        "date_raw": expected_date_raw,
        "paused": True,
        "player_character_id": expected_player_character_id,
        "subject_character_id": expected_query.subject_character_id,
        "owner_character_id": expected_query.owner_character_id,
        "subject_binding_kind": subject_binding["kind"],
        "bounded_ai_manager_dependency": dependency,
        "expected_revision": expected_revision,
    }
    if binding != expected_binding:
        raise ValueError("binding does not match the typed native result")
    return {**native, "build": dict(build), "source": dict(source), "binding": dict(binding)}
