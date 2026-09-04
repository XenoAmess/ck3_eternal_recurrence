"""Small read-only contract for the next G2 Raiktor truce probe."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


EXPECTED_GAME_VERSION = "1.19.0.6"
EXPECTED_EXECUTABLE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
EXPECTED_TRUCE_OBSERVER = "ck3-1.19.0.6-native-raiktor-surrender-truce-v1"
REQUIRED_READ_ONLY_TOOLS = (
    "ck3_get_capabilities",
    "ck3_take_snapshot",
    "ck3_query_war_termination_terms",
)
FORBIDDEN_MUTATION_PREFIXES = (
    "surrender-war-",
    "offer-white-peace-",
    "enforce-demands-",
)


def _map(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _same_frame(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return bool(
        left.get("paused") is True
        and right.get("paused") is True
        and all(
            left.get(key) == right.get(key)
            for key in (
                "snapshot_id",
                "revision",
                "native_revision",
                "date_raw",
                "episode_run_id",
            )
        )
    )


def _war(snapshot: Mapping[str, Any], war_id: int) -> Mapping[str, Any]:
    rows = snapshot.get("active_wars")
    if isinstance(rows, list):
        for row in rows:
            candidate = _map(row)
            if candidate.get("war_id") == war_id:
                return candidate
    return {}


def _terms(result: object) -> Mapping[str, Any]:
    return _map(_map(result).get("war_termination_terms"))


def _nonnegative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def validate_pointer_contract(value: object) -> dict[str, bool]:
    """Check frozen fields identifying the pointer-only CAddTruce path."""

    contract = _map(value)
    shape = _map(contract.get("attacker_defeat_pointer_shape"))
    read = _map(contract.get("read_contract"))
    readiness = _map(contract.get("readiness"))
    checks = {
        "exact_build": contract.get("game_version") == EXPECTED_GAME_VERSION
        and contract.get("ck3_exe_sha256") == EXPECTED_EXECUTABLE_SHA256,
        "unique_caddtruce": shape.get("terminal") == "unique CAddTruce"
        and shape.get("scripted_child_index") == 7
        and shape.get("unique_hidden_child_index") == 1
        and _map(shape.get("root_span")) == {"capacity": 13, "count": 12}
        and _map(shape.get("default_span")) == {"capacity": 4, "count": 4}
        and _map(shape.get("hidden_span")) == {"capacity": 1, "count": 1}
        and _map(shape.get("context_span")) == {"capacity": 1, "count": 1}
        and shape.get("context_scope_count") == 1,
        "double_nonnegative_read": read.get("duration_evaluator_reads") == 2
        and read.get("requires_equal_non_negative_days") is True
        and read.get("requires_synchronous_native_leaf_context") is True
        and read.get("requires_leaf_evaluation_context_from_offset_0x28") is True
        and read.get("requires_preview_entry_target_match") is True,
        "same_paused_frame": read.get("requires_paused") is True
        and read.get("requires_identical_before_after_frame") is True,
        "expiry_not_claimed": read.get("expiry_observable") is False
        and readiness.get("public_wire_scope")
        == "evaluated_days_only; expiry_observable=false; expiry_date_raw=null",
    }
    checks["ok"] = all(checks.values())
    return checks


def validate_truce_probe(
    *,
    before: object,
    between: object,
    after: object,
    first: object,
    second: object,
    tool_names: Sequence[object],
    allowed_gameplay_commands: Sequence[object],
    mutation_commands: Sequence[object],
    expected_war_id: int,
    expected_character_id: int,
    expected_date_raw: int,
    pointer_contract_checks: Mapping[str, object] | None = None,
) -> dict[str, bool]:
    """Validate one exact-build MCP-first, paused, read-only sequence."""

    before_map, between_map, after_map = map(_map, (before, between, after))
    first_map, second_map = map(_map, (first, second))
    first_terms, second_terms = _terms(first), _terms(second)
    first_truce, second_truce = (
        _map(first_terms.get("truce")),
        _map(second_terms.get("truce")),
    )
    first_provenance, second_provenance = (
        _map(first_terms.get("provenance")),
        _map(second_terms.get("provenance")),
    )
    war = _war(before_map, expected_war_id)
    first_days, second_days = (
        first_truce.get("evaluated_days"),
        second_truce.get("evaluated_days"),
    )
    commands = list(allowed_gameplay_commands)
    mutations = list(mutation_commands)
    tool_set = {name for name in tool_names if isinstance(name, str)}
    forbidden = [
        command
        for command in [*commands, *mutations]
        if isinstance(command, str)
        and command.startswith(FORBIDDEN_MUTATION_PREFIXES)
    ]
    pointer = dict(pointer_contract_checks or {"ok": False})
    checks: dict[str, bool] = {
        "same_paused_frame": _same_frame(before_map, between_map)
        and _same_frame(before_map, after_map),
        "expected_player_and_date": _map(before_map.get("played_character")).get(
            "character_id"
        )
        == expected_character_id
        and before_map.get("date_raw") == expected_date_raw,
        "war_id_and_roles": (
            first_terms.get("war_id") == expected_war_id
            and second_terms.get("war_id") == expected_war_id
            and war.get("war_id") == expected_war_id
            and war.get("player_side") == "attacker"
            and war.get("player_is_primary_war_leader") is True
            and _nonnegative_int(war.get("primary_opponent_character_id"))
            and war.get("primary_opponent_character_id") > 0
            and war.get("primary_opponent_character_id") != expected_character_id
            and _nonnegative_int(first_terms.get("claimant_character_id"))
            and first_terms.get("claimant_character_id") > 0
            and first_terms.get("claimant_character_id") == second_terms.get(
                "claimant_character_id"
            )
        ),
        "exact_provenance": (
            first_provenance == second_provenance
            and first_provenance.get("game_version") == EXPECTED_GAME_VERSION
            and first_provenance.get("executable_sha256")
            == EXPECTED_EXECUTABLE_SHA256
            and first_provenance.get("truce_observer") == EXPECTED_TRUCE_OBSERVER
        ),
        "raiktor_truce_shape": all(
            truce.get("direction")
            == "primary_attacker_toward_primary_defender"
            and truce.get("result") == "defeat"
            and truce.get("evaluated_days_observable") is True
            and _nonnegative_int(truce.get("evaluated_days"))
            and truce.get("actual_expiry_observable") is False
            and truce.get("expiry_date_raw") is None
            for truce in (first_truce, second_truce)
        ),
        "evaluated_days_equal": first_days == second_days,
        "pointer_only_contract_bound": pointer.get("ok") is True,
        "query_bindings_match": all(
            result.get("queried_revision") == before_map.get("revision")
            and result.get("queried_snapshot_id") == before_map.get("snapshot_id")
            and result.get("queried_native_revision")
            == before_map.get("native_revision")
            for result in (first_map, second_map)
        ),
        "query_sequence_successor": (
            isinstance(first_map.get("query_sequence"), int)
            and isinstance(second_map.get("query_sequence"), int)
            and second_map.get("query_sequence")
            == first_map.get("query_sequence") + 1
        ),
        "read_only_tool_boundary": all(
            name in tool_set for name in REQUIRED_READ_ONLY_TOOLS
        )
        and commands
        == [
            f"query-war-termination-terms-v1-{expected_war_id}",
            f"query-war-termination-terms-v1-{expected_war_id}",
        ]
        and not mutations
        and not forbidden,
        "normalized_queries_equal": (
            {key: value for key, value in first_map.items() if key != "query_sequence"}
            == {
                key: value
                for key, value in second_map.items()
                if key != "query_sequence"
            }
        ),
    }
    checks["ok"] = all(checks.values())
    return checks


__all__ = [
    "EXPECTED_EXECUTABLE_SHA256",
    "EXPECTED_GAME_VERSION",
    "EXPECTED_TRUCE_OBSERVER",
    "FORBIDDEN_MUTATION_PREFIXES",
    "REQUIRED_READ_ONLY_TOOLS",
    "validate_pointer_contract",
    "validate_truce_probe",
]
