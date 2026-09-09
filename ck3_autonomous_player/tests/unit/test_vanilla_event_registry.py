from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

from xar_autoplayer.vanilla_events import (  # noqa: E402
    DEFAULT_VANILLA_EVENT_ANALYSIS,
    DEFAULT_VANILLA_EVENT_CONTRACT_GROUPS,
    DEFAULT_VANILLA_EVENT_OBSERVATIONS,
    DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS,
    EXACT_CK3_BUILD,
    EXACT_CK3_EXE_SHA256,
    VANILLA_EVENT_TIMELINE_CONTRACTS,
    build_vanilla_event_registry,
    materialize_vanilla_timeline_contract,
    query_vanilla_event_knowledge_v1,
)
from xar_autoplayer.vanilla_events.records_prebootstrap import (  # noqa: E402
    PREBOOTSTRAP_VANILLA_TIMELINE_CONTRACTS,
)


@pytest.fixture(autouse=True)
def _default_registry() -> None:
    build_vanilla_event_registry(
        DEFAULT_VANILLA_EVENT_CONTRACT_GROUPS,
        analysis=DEFAULT_VANILLA_EVENT_ANALYSIS,
        observations=DEFAULT_VANILLA_EVENT_OBSERVATIONS,
    )
    yield
    build_vanilla_event_registry(
        DEFAULT_VANILLA_EVENT_CONTRACT_GROUPS,
        analysis=DEFAULT_VANILLA_EVENT_ANALYSIS,
        observations=DEFAULT_VANILLA_EVENT_OBSERVATIONS,
    )


def test_build_accepts_multiple_groups_and_deduplicates_identical_keys() -> None:
    first = {"health.1": {"steps": [{"scope": "$player"}], "days": 2}}
    duplicate = {"health.1": {"days": 2, "steps": [{"scope": "$player"}]}}
    second = {"secrets.1": {"steps": [], "days": 0}}

    built = build_vanilla_event_registry([first, duplicate, second])
    first["health.1"]["days"] = 999
    built["health.1"]["steps"].append({"scope": "tampered"})

    response = query_vanilla_event_knowledge_v1("health.1")
    assert response == {
        "schema": "xar.ck3.vanilla-event-knowledge",
        "schema_version": 1,
        "status": "available",
        "event_definition_key": "health.1",
        "ck3_build": EXACT_CK3_BUILD,
        "ck3_exe_sha256": EXACT_CK3_EXE_SHA256,
        "contract": {"steps": [{"scope": "$player"}], "days": 2},
        "analysis": None,
        "observations": None,
        "unavailable_reason": None,
    }
    json.dumps(response, allow_nan=False)

    response["contract"]["days"] = 88
    assert query_vanilla_event_knowledge_v1("health.1")["contract"]["days"] == 2


def test_package_import_registers_one_disjoint_default_catalog() -> None:
    expected_count = sum(len(group) for group in DEFAULT_VANILLA_EVENT_CONTRACT_GROUPS)

    assert expected_count == 164
    assert len(DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS) == expected_count
    assert len(DEFAULT_VANILLA_EVENT_ANALYSIS) == expected_count
    assert set(DEFAULT_VANILLA_EVENT_ANALYSIS) == set(
        DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS
    )
    assert VANILLA_EVENT_TIMELINE_CONTRACTS is (
        DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS
    )
    for group in DEFAULT_VANILLA_EVENT_CONTRACT_GROUPS:
        for event_key, canonical_contract in group.items():
            assert (
                DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS[event_key]
                is canonical_contract
            )
    assert query_vanilla_event_knowledge_v1("prison_notification.2002")[
        "status"
    ] == "available"
    manager_contract = query_vanilla_event_knowledge_v1("spymaster_task.0381")[
        "contract"
    ]
    assert manager_contract["date_raw"] == [53148768, 53152656]
    for event_key in DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS:
        response = query_vanilla_event_knowledge_v1(event_key)
        assert response["status"] == "available"
        assert response["analysis"] is not None
        json.dumps(response, allow_nan=False)


def test_conflicting_duplicate_is_rejected_without_replacing_active_registry() -> None:
    build_vanilla_event_registry({"existing.1": {"days": 4}})

    with pytest.raises(ValueError, match="conflicting vanilla event contract"):
        build_vanilla_event_registry(
            [{"same.1": {"days": 1}}, {"same.1": {"days": 2}}]
        )

    assert query_vanilla_event_knowledge_v1("existing.1")["status"] == "available"
    assert query_vanilla_event_knowledge_v1("same.1")["status"] == "unavailable"


@pytest.mark.parametrize(
    ("event_key", "build", "reason"),
    [
        ("missing.1", EXACT_CK3_BUILD, "event_definition_key_not_registered"),
        ("missing.1", "1.19.0.7", "unsupported_ck3_build"),
        ("", EXACT_CK3_BUILD, "invalid_event_definition_key"),
    ],
)
def test_query_returns_json_safe_unavailable_rows(
    event_key: str,
    build: str,
    reason: str,
) -> None:
    response = query_vanilla_event_knowledge_v1(event_key, build)

    assert response["status"] == "unavailable"
    assert response["contract"] is None
    assert response["unavailable_reason"] == reason
    assert response["ck3_exe_sha256"] == (
        EXACT_CK3_EXE_SHA256 if build == EXACT_CK3_BUILD else None
    )
    json.dumps(response, allow_nan=False)


def test_build_rejects_non_json_contract_content() -> None:
    with pytest.raises(ValueError, match="unsupported contract value"):
        build_vanilla_event_registry({"broken.1": {"bad": object()}})

    with pytest.raises(ValueError, match="NaN or infinity"):
        build_vanilla_event_registry({"broken.2": {"bad": float("nan")}})


def test_materialize_replaces_only_exact_player_sentinels_recursively() -> None:
    contract = {
        "root_scope": "$player",
        "nested": [
            "$player",
            {"saved_scope": "$player", "literal": "prefix-$player"},
        ],
        "unchanged": None,
    }
    player = {"character_id": 29037}

    materialized = materialize_vanilla_timeline_contract(contract, player)

    assert materialized == {
        "root_scope": {"character_id": 29037},
        "nested": [
            {"character_id": 29037},
            {
                "saved_scope": {"character_id": 29037},
                "literal": "prefix-$player",
            },
        ],
        "unchanged": None,
    }
    assert contract["root_scope"] == "$player"
    materialized["root_scope"]["character_id"] = 1
    assert materialized["nested"][0]["character_id"] == 29037
    assert player == {"character_id": 29037}
    json.dumps(materialized, allow_nan=False)


def test_real_migrated_group_preserves_tuples_until_json_query_boundary() -> None:
    built = build_vanilla_event_registry(
        PREBOOTSTRAP_VANILLA_TIMELINE_CONTRACTS
    )

    internal_contract = built["spymaster_task.0381"]
    assert internal_contract["native_option_indices"] == (0, 1)
    assert isinstance(internal_contract["native_option_indices"], tuple)
    materialized = materialize_vanilla_timeline_contract(
        internal_contract, 29037
    )
    assert isinstance(materialized["native_option_indices"], tuple)

    response = query_vanilla_event_knowledge_v1("spymaster_task.0381")
    assert response["status"] == "available"
    assert response["contract"]["native_option_indices"] == [0, 1]
    assert isinstance(response["contract"]["native_option_indices"], list)
    json.dumps(response, allow_nan=False)
