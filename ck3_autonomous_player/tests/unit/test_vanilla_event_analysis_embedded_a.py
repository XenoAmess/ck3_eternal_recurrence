from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

from xar_autoplayer.vanilla_events.records_analysis_embedded_a import (  # noqa: E402
    EMBEDDED_A_EVENT_KEYS,
    VANILLA_EMBEDDED_A_ANALYSIS,
)
from xar_autoplayer.vanilla_events.records_embedded import (  # noqa: E402
    EMBEDDED_VANILLA_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    EXACT_CK3_BUILD,
    EXACT_CK3_EXE_SHA256,
)


def test_analysis_exactly_covers_first_27_embedded_keys() -> None:
    expected = tuple(EMBEDDED_VANILLA_TIMELINE_CONTRACTS)[:27]
    assert EMBEDDED_A_EVENT_KEYS == expected
    assert tuple(VANILLA_EMBEDDED_A_ANALYSIS) == expected
    assert len(VANILLA_EMBEDDED_A_ANALYSIS) == 27


def test_analysis_is_json_safe_and_does_not_claim_source_hashes() -> None:
    encoded = json.dumps(VANILLA_EMBEDDED_A_ANALYSIS, sort_keys=True)
    assert json.loads(encoded) == VANILLA_EMBEDDED_A_ANALYSIS
    assert "source_sha256" not in encoded


def test_each_record_carries_exact_build_and_migration_boundary() -> None:
    for record in VANILLA_EMBEDDED_A_ANALYSIS.values():
        assert record["exact_build"] == {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
        }
        assert record["migrated_from"]["review_kind"] == (
            "migration-only-no-new-full-definition-review"
        )
        assert record["review_summary"]
        assert record["safe_option"]["rationale"]
        assert record["existing_boundaries"]["boundary_note"]


def test_safe_option_and_occurrence_fields_match_existing_contracts() -> None:
    for event_key, record in VANILLA_EMBEDDED_A_ANALYSIS.items():
        contract = EMBEDDED_VANILLA_TIMELINE_CONTRACTS[event_key]
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
