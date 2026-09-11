from __future__ import annotations

import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator
import pytest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

from xar_autoplayer.vanilla_events import (  # noqa: E402
    DEFAULT_VANILLA_EVENT_ANALYSIS,
    DEFAULT_VANILLA_EVENT_OBSERVATIONS,
    DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS,
    EXACT_CK3_BUILD,
)
from xar_autoplayer.vanilla_events.discovery import (  # noqa: E402
    ck3_list_vanilla_event_knowledge_v1,
)


SCHEMA_PATH = (
    ROOT
    / "ck3_autonomous_player"
    / "schemas"
    / "vanilla-event-knowledge-index-v1.schema.json"
)


def _validate(result: dict[str, object]) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(result)
    json.dumps(result, ensure_ascii=False, allow_nan=False)


def test_all_184_keys_are_stably_keyset_paginated() -> None:
    expected = sorted(DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS)
    found: list[str] = []
    after_key = None
    dataset_sha256 = None

    while True:
        result = ck3_list_vanilla_event_knowledge_v1(
            after_key=after_key,
            limit=7,
        )
        _validate(result)
        assert result["status"] == "available"
        assert result["total_matches"] == 184
        assert result["dataset_summary"]["total_events"] == 184
        if dataset_sha256 is None:
            dataset_sha256 = result["dataset_sha256"]
        assert result["dataset_sha256"] == dataset_sha256
        found.extend(item["event_definition_key"] for item in result["items"])
        after_key = result["next_after_key"]
        if after_key is None:
            break

    assert found == expected
    assert len(found) == len(set(found)) == 184


def test_filters_search_and_counts_match_the_canonical_metadata() -> None:
    source_expected = {
        key
        for key, metadata in DEFAULT_VANILLA_EVENT_ANALYSIS.items()
        if metadata.get("source_sha256")
    }
    observation_expected = set(DEFAULT_VANILLA_EVENT_OBSERVATIONS)

    source = ck3_list_vanilla_event_knowledge_v1(
        evidence_class="source-reviewed",
        limit=100,
    )
    migration = ck3_list_vanilla_event_knowledge_v1(
        evidence_class="migration-only",
        limit=100,
    )
    observed = ck3_list_vanilla_event_knowledge_v1(
        has_observations=True,
        limit=100,
    )
    unobserved = ck3_list_vanilla_event_knowledge_v1(
        has_observations=False,
        limit=100,
    )

    assert source["total_matches"] == len(source_expected)
    assert source["match_summary"]["migration_only_events"] == 0
    assert migration["total_matches"] == 184 - len(source_expected)
    assert migration["match_summary"]["source_reviewed_events"] == 0
    assert observed["total_matches"] == len(observation_expected)
    assert unobserved["total_matches"] == 184 - len(observation_expected)

    namespace = ck3_list_vanilla_event_knowledge_v1(
        namespace="tgp_dynastic_cycle",
        limit=100,
    )
    assert namespace["total_matches"] > 0
    assert {item["namespace"] for item in namespace["items"]} == {
        "tgp_dynastic_cycle"
    }

    search = ck3_list_vanilla_event_knowledge_v1(
        query="dynastic cycle",
        limit=100,
    )
    assert search["total_matches"] > 0
    assert any(
        item["event_definition_key"] == "tgp_dynastic_cycle.0091"
        for item in search["items"]
    )
    source_path_search = ck3_list_vanilla_event_knowledge_v1(
        query="events/dlc/tgp/tgp_dynastic_cycle_events.txt",
        limit=100,
    )
    assert any(
        item["event_definition_key"] == "tgp_dynastic_cycle.0091"
        for item in source_path_search["items"]
    )


def test_portable_evidence_is_opt_in_and_changes_the_dataset_identity() -> None:
    default = ck3_list_vanilla_event_knowledge_v1(limit=1)
    injected = ck3_list_vanilla_event_knowledge_v1(
        limit=100,
        portable_event_keys={
            "tgp_dynastic_cycle.0091": {"artifact": "portable"},
            "prison_notification.2002": {"artifact": "portable"},
        },
    )

    assert default["dataset_summary"]["portable_events"] == 0
    assert injected["dataset_summary"]["portable_events"] == 2
    assert injected["dataset_sha256"] != default["dataset_sha256"]
    for event_key in ("tgp_dynastic_cycle.0091", "prison_notification.2002"):
        found = ck3_list_vanilla_event_knowledge_v1(
            query=event_key,
            portable_event_keys={
                "tgp_dynastic_cycle.0091",
                "prison_notification.2002",
            },
        )
        assert found["total_matches"] == 1
        assert found["items"][0]["portable_evidence_count"] == 1


@pytest.mark.parametrize(
    ("kwargs", "reason", "parameter"),
    [
        ({"build": "1.19.0.7"}, "unsupported_ck3_build", "build"),
        ({"query": 4}, "invalid_filter", "query"),
        ({"namespace": ""}, "invalid_filter", "namespace"),
        ({"evidence_class": "reviewed"}, "invalid_filter", "evidence_class"),
        ({"evidence_class": []}, "invalid_filter", "evidence_class"),
        ({"has_observations": "yes"}, "invalid_filter", "has_observations"),
        ({"limit": 0}, "invalid_limit", "limit"),
        ({"limit": 101}, "invalid_limit", "limit"),
        ({"limit": True}, "invalid_limit", "limit"),
        ({"after_key": ""}, "invalid_cursor", "after_key"),
        ({"after_key": "not_registered.1"}, "invalid_cursor", "after_key"),
    ],
)
def test_invalid_build_filter_limit_and_cursor_are_typed_unavailable(
    kwargs: dict[str, object],
    reason: str,
    parameter: str,
) -> None:
    result = ck3_list_vanilla_event_knowledge_v1(**kwargs)

    _validate(result)
    assert result["status"] == "unavailable"
    assert result["unavailable_reason"] == reason
    assert result["invalid_parameter"] == parameter
    assert result["items"] == []
    assert result["dataset_sha256"] is None


def test_injected_catalog_is_deterministic_and_schema_valid() -> None:
    contracts = {
        "zeta.2": {"root_character_id": "$player", "selected": 0},
        "alpha.1": {"root_character_id": "$player", "selected": 1},
    }
    analysis = {
        "alpha.1": {"review_summary": "Alpha terminal route"},
        "zeta.2": {
            "review_summary": "Zeta source-reviewed route",
            "source_sha256": {"events/zeta.txt": "A" * 64},
        },
    }
    observations = {"alpha.1": {"exemplars": [{"run": "fixture"}]}}

    first = ck3_list_vanilla_event_knowledge_v1(
        contracts=contracts,
        analysis=analysis,
        observations=observations,
    )
    second = ck3_list_vanilla_event_knowledge_v1(
        contracts=dict(reversed(tuple(contracts.items()))),
        analysis=dict(reversed(tuple(analysis.items()))),
        observations=observations,
    )

    _validate(first)
    assert first == second
    assert [item["event_definition_key"] for item in first["items"]] == [
        "alpha.1",
        "zeta.2",
    ]
    assert first["dataset_summary"] == {
        "total_events": 2,
        "source_reviewed_events": 1,
        "migration_only_events": 1,
        "events_with_observations": 1,
        "portable_events": 0,
    }
    assert first["ck3_build"] == EXACT_CK3_BUILD
