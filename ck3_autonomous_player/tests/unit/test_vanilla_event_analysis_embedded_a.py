from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

from xar_autoplayer.vanilla_events.records_analysis_embedded_a import (  # noqa: E402
    EMBEDDED_A_EVENT_KEYS,
    VANILLA_EMBEDDED_A_ANALYSIS,
    VANILLA_EMBEDDED_A_OBSERVATIONS,
)
from xar_autoplayer.vanilla_events.records_embedded_a import (  # noqa: E402
    EMBEDDED_A_VANILLA_OBSERVATIONS,
    EMBEDDED_A_VANILLA_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    EXACT_CK3_BUILD,
    EXACT_CK3_EXE_SHA256,
    PLAYER_SENTINEL,
    materialize_vanilla_timeline_contract,
    query_vanilla_event_knowledge_v1,
)


def test_analysis_exactly_covers_first_27_embedded_keys() -> None:
    expected = tuple(EMBEDDED_A_VANILLA_TIMELINE_CONTRACTS)
    assert EMBEDDED_A_EVENT_KEYS == expected
    assert tuple(VANILLA_EMBEDDED_A_ANALYSIS) == expected
    assert len(VANILLA_EMBEDDED_A_ANALYSIS) == 27


def test_analysis_is_json_safe_and_only_reviewed_event_claims_source_hashes() -> None:
    encoded = json.dumps(VANILLA_EMBEDDED_A_ANALYSIS, sort_keys=True)
    assert json.loads(encoded) == VANILLA_EMBEDDED_A_ANALYSIS
    for event_key, record in VANILLA_EMBEDDED_A_ANALYSIS.items():
        if event_key == "stress_threshold.1721":
            assert len(record["source_sha256"]) == 6
        elif event_key == "tgp_movement_events.0070":
            assert len(record["source_sha256"]) == 3
        else:
            assert "source_sha256" not in record


def test_each_record_carries_exact_build_and_migration_boundary() -> None:
    for event_key, record in VANILLA_EMBEDDED_A_ANALYSIS.items():
        assert record["exact_build"] == {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
        }
        expected_review = {
            "stress_threshold.1721": (
                "exact-build-original-definition-and-live-variant-review"
            ),
            "tgp_movement_events.0070": (
                "exact-build-original-definition-and-live-repeat-review"
            ),
        }.get(event_key, "migration-only-no-new-full-definition-review")
        assert record["migrated_from"]["review_kind"] == expected_review
        assert record["review_summary"]
        assert record["safe_option"]["rationale"]
        assert record["existing_boundaries"]["boundary_note"]
        assert record["existing_boundaries"][
            "campaign_specific_binding_fields"
        ] == []
        assert record["existing_boundaries"]["date_policy"] == (
            "product-observation-window"
        )


def test_migration_observations_join_existing_live_evidence() -> None:
    assert len(EMBEDDED_A_VANILLA_OBSERVATIONS) == 26
    assert len(VANILLA_EMBEDDED_A_OBSERVATIONS) == 27
    for event_key, observation in EMBEDDED_A_VANILLA_OBSERVATIONS.items():
        migrated = VANILLA_EMBEDDED_A_OBSERVATIONS[event_key]
        if event_key == "tgp_movement_events.0070":
            assert migrated["exemplars"][0] == observation["exemplars"][0]
        else:
            assert migrated == observation
        exemplar = observation["exemplars"][0]
        assert exemplar["run"] == "legacy-migrated"
        assert exemplar["kind"] == "legacy-live-binding"
        assert exemplar["review_kind"] == "migration-only"

    assert "stress_threshold.1721" not in EMBEDDED_A_VANILLA_OBSERVATIONS
    assert VANILLA_EMBEDDED_A_OBSERVATIONS[
        "stress_threshold.1721"
    ]["exemplars"][0]["run"] == "R372"


def test_tgp_movement_study_repeat_is_source_reviewed_and_live_bounded() -> None:
    event_key = "tgp_movement_events.0070"
    contract = EMBEDDED_A_VANILLA_TIMELINE_CONTRACTS[event_key]
    analysis = VANILLA_EMBEDDED_A_ANALYSIS[event_key]
    legacy, first_green, repeat_red, repeat_green = VANILLA_EMBEDDED_A_OBSERVATIONS[
        event_key
    ]["exemplars"]

    assert "max_occurrences" not in contract
    assert contract["occurrence_policy"] == (
        "repeatable-within-product-observation-window"
    )
    assert analysis["definition_lines"] == "1426-1598"
    assert "ten-year cooldown" in analysis["caller_semantics"]
    assert analysis["safe_option"]["selected_native_option_index"] == 0
    assert legacy["run"] == "legacy-migrated"
    assert first_green["run"] == "R418-attempt-04"
    assert first_green["event_instance_id"] == 1099
    assert first_green["selected_native_option_index"] == 0
    assert first_green["postcondition_verified"] is True
    assert first_green["ending_snapshot_id"] == "native:1377"
    assert repeat_red["run"] == "R418-attempt-05"
    assert repeat_red["event_instance_id"] == 1108
    assert repeat_red["date_raw"] > first_green["date_raw"]
    assert repeat_red["selection_attempted"] is False
    assert repeat_red["retained_red"] is True
    assert repeat_red["artifact_sha256"] == first_green["artifact_sha256"]
    assert repeat_green["run"] == "R418-attempt-06"
    assert repeat_green["event_instance_id"] == repeat_red["event_instance_id"]
    assert repeat_green["selected_native_option_index"] == 0
    assert repeat_green["postcondition_verified"] is True
    assert repeat_green["starting_snapshot_id"] == "native:2692"
    assert repeat_green["ending_snapshot_id"] == "native:2693"
    assert repeat_green["artifact_sha256"] != repeat_red["artifact_sha256"]
    assert repeat_green["bridge_pid"] == first_green["bridge_pid"]
    assert repeat_green["connection_generation"] == 1


def test_safe_option_and_occurrence_fields_match_existing_contracts() -> None:
    for event_key, record in VANILLA_EMBEDDED_A_ANALYSIS.items():
        contract = EMBEDDED_A_VANILLA_TIMELINE_CONTRACTS[event_key]
        safe_option = record["safe_option"]
        assert safe_option["selected_option_number"] == contract[
            "selected_option_number"
        ]
        assert safe_option["selected_native_option_index"] == contract[
            "selected_native_option_index"
        ]

        occurrence = record["existing_boundaries"]["occurrence"]
        if "occurrence_policy" in contract:
            assert occurrence == {
                "occurrence_policy": contract["occurrence_policy"]
            }
        elif "max_occurrences" in contract:
            assert occurrence == {"max_occurrences": contract["max_occurrences"]}
        else:
            assert occurrence == {
                "status": "not-specified-in-existing-contract"
            }


def test_known_multi_projection_records_preserve_json_safe_variants() -> None:
    for event_key in (
        "adultery.0002",
        "stress_threshold_special.1001",
        "epidemic_events.1100",
        "faction_demand.0101",
        "faction_demand.1001",
    ):
        variants = VANILLA_EMBEDDED_A_ANALYSIS[event_key]["safe_option"][
            "variants"
        ]
        assert isinstance(variants, list)
        assert variants
        assert all(
            isinstance(variant["native_option_indices"], list)
            for variant in variants
        )


def test_impostor_break_exact_review_and_live_red_are_query_safe() -> None:
    contract = EMBEDDED_A_VANILLA_TIMELINE_CONTRACTS[
        "stress_threshold.1721"
    ]
    record = VANILLA_EMBEDDED_A_ANALYSIS["stress_threshold.1721"]
    assert contract["root_character_id"] == PLAYER_SENTINEL
    assert contract["character_scopes"]["stress_character"] == PLAYER_SENTINEL
    assert "date_raw" not in contract
    assert "max_occurrences" not in contract
    assert contract["occurrence_policy"] == (
        "repeatable-within-product-observation-window"
    )
    materialized = materialize_vanilla_timeline_contract(contract, 47001)
    assert materialized["root_character_id"] == 47001
    assert materialized["character_scopes"]["stress_character"] == 47001
    assert contract["root_character_id"] == PLAYER_SENTINEL

    assert record["option_semantics"]["10"].startswith("minor stress loss")
    assert "starvation" in record["safe_option"]["rationale"]
    assert record["existing_boundaries"][
        "campaign_specific_binding_fields"
    ] == []
    scope_variant = record["existing_boundaries"]["scope_shape"][
        "scope_variants"
    ][0]
    assert scope_variant["native_option_indices"] == [7, 10, 12]
    assert scope_variant["selected_native_option_index"] == 10
    assert scope_variant["option_variants"][0]["native_option_indices"] == [
        7,
        9,
        12,
    ]
    assert scope_variant["option_variants"][0][
        "selected_native_option_index"
    ] == 9
    assert [
        route["selected_native_option_index"]
        for route in record["safe_routes_by_live_projection"]
    ] == [9, 10, 9]

    (
        exemplar,
        failed_retry,
        current_red,
        current_green,
    ) = VANILLA_EMBEDDED_A_OBSERVATIONS["stress_threshold.1721"]["exemplars"]
    assert exemplar["kind"] == "pre-selection-live-red"
    assert exemplar["rendered_native_option_indices"] == [7, 10, 12]
    assert exemplar["selection_attempted"] is False
    assert json.loads(json.dumps(exemplar, sort_keys=True)) == exemplar
    assert failed_retry["kind"] == (
        "same-process-hot-recovery-contract-resolution-red"
    )
    assert failed_retry["contract_reload_applied"] is True
    assert failed_retry["failure_stage"] == (
        "submission_re_resolved_base_contract"
    )
    assert failed_retry["selected_native_option_index"] == 9
    assert failed_retry["expected_reviewed_native_option_index"] == 10
    assert failed_retry["postcondition_verified"] is True
    assert current_red["run"] == "R375"
    assert current_red["artifact"].endswith("-red-freeze.json")
    assert current_red["saved_scope_raw_types"] == {
        "stress_character": 4,
        "deceased_character": 4,
    }
    assert current_red["rendered_native_option_indices"] == [7, 9, 12]
    assert current_red["selection_attempted"] is False
    assert current_green["kind"] == "same-process-hot-recovery-green"
    assert current_green["production_live_ordinal"] == 17
    assert current_green["artifact"].endswith(
        "r375-live-017-stress-threshold-1721-green.json"
    )
    assert current_green["artifact_sha256"] == (
        "869BFE72B6FF2ABEF55FF3F4191F13D3A9F57E696F02B011367527256AD57EF3"
    )
    assert current_green["event_instance_id"] == current_red["event_instance_id"]
    assert current_green["bridge_pid"] == current_red["bridge_pid"]
    assert current_green["connection_generation"] == (
        current_red["connection_generation"]
    )
    assert current_green["context_query_driver_command_index"] == 371
    assert current_green["selection_driver_command_index"] == 372
    assert current_green["selected_option_number"] == 10
    assert current_green["selected_native_option_index"] == 9
    assert current_green["postcondition_verified"] is True
    assert current_green["ending_snapshot_id"] == "native:441"
    assert current_green["process_restart_required"] is False
    assert current_green["mcp_only"] is True
    for forbidden_mode in (
        "fixture_used",
        "ocr_used",
        "coordinates_used",
        "console_used",
    ):
        assert current_green[forbidden_mode] is False

    contract_repr = repr(contract)
    for observation_only in (
        53387208,
        53611536,
        627,
        1060,
        32904,
        37337,
        180544,
        371,
        372,
        "native:440",
        "native:441",
    ):
        assert str(observation_only) not in contract_repr

    response = query_vanilla_event_knowledge_v1("stress_threshold.1721")
    assert response["status"] == "available"
    assert response["contract"]["root_character_id"] == "$player"
    assert response["contract"]["scope_variants"][0]["option_variants"][0][
        "selected_native_option_index"
    ] == 9
    assert response["observations"]["exemplars"][2]["event_instance_id"] == 1060
    assert response["observations"]["exemplars"][3]["kind"] == (
        "same-process-hot-recovery-green"
    )
    assert response["observations"]["exemplars"][3][
        "postcondition_verified"
    ] is True
    json.dumps(response, allow_nan=False)
