"""Reusable analysis metadata for the migrated vanilla-event shards.

This module only promotes conclusions already encoded in the legacy contracts,
their source-review comments, and their focused tests.  It deliberately does
not claim a source hash where the prior review did not freeze one.
"""

from __future__ import annotations

from typing import Final

from .records_vanilla_shards import VANILLA_SHARD_TIMELINE_CONTRACTS
from .registry import EXACT_CK3_BUILD, EXACT_CK3_EXE_SHA256


_REVIEW_ROWS: Final[dict[str, dict[str, object]]] = {
    "ep2_accolade_events.0300": {
        "migrated_from": (
            "tools/zg361_phase2_promotion_vanilla_accolade_"
            "interrupt_contracts.py"
        ),
        "review_summary": (
            "Master of Revels training result: the reviewed root-only frame "
            "has one unavoidable terminal option, grants lifestyle_reveler "
            "to the root trainee, may reduce stress, and sends no follow-up."
        ),
    },
    "ep3_story_cycle_admin_eunuch.8010": {
        "migrated_from": (
            "tools/zg361_phase2_promotion_vanilla_admin_eunuch_"
            "interrupt_contracts.py"
        ),
        "review_summary": (
            "Administrative-eunuch death transition: the first two routes "
            "replace the deceased eunuch; the selected third route only "
            "clears the liege modifier and terminates the story."
        ),
    },
    "diarchy.8042": {
        "migrated_from": (
            "tools/zg361_phase2_promotion_vanilla_diarchy_"
            "interrupt_contracts.py"
        ),
        "review_summary": (
            "Co-emperor scapegoat-result letter: gameplay consequences occur "
            "before dispatch, while the recipient sees one empty authored "
            "acknowledgement after the complete interaction carry is bound."
        ),
    },
    "tgp_dynastic_cycle.0091": {
        "migrated_from": (
            "tools/zg361_phase2_promotion_vanilla_dynastic_cycle_"
            "interrupt_contracts.py"
        ),
        "review_summary": (
            "Instability transition notice for the current China holder: its "
            "sole option is an empty acknowledgement, and a later dynastic "
            "cycle can legitimately produce another notice."
        ),
        "source_sha256": {
            "events/dlc/tgp/tgp_dynastic_cycle_events.txt": (
                "C9904AAA01ABC8583E67D07866FAE8EF89274708BDA3929498DDDB2F24FC2153"
            ),
            "common/situation/situations/tgp_dynastic_cycle.txt": (
                "748F2AF8CBDF97E01182FEFADF0B975E62AECE57D09AB1515C02E112DB56FAEA"
            ),
        },
    },
    "ep1_flavor.1000": {
        "migrated_from": (
            "tools/zg361_phase2_promotion_vanilla_ep1_flavor_"
            "interrupt_contracts.py"
        ),
        "review_summary": (
            "Visiting-eunuch offer: native0/native1 hire or negotiate, while "
            "selected native2 declines, moves the visitor to the preselected "
            "pool court, and schedules no follow-up."
        ),
    },
    "ep3_emperor_yearly.2170": {
        "migrated_from": (
            "tools/zg361_phase2_promotion_vanilla_ep3_emperor_"
            "interrupt_contracts.py"
        ),
        "review_summary": (
            "Low-control county response: both routes add a long county "
            "modifier, but selected native0 avoids native1's additional "
            "25-year governor-efficiency character flag."
        ),
        "source_sha256": {
            "events/dlc/ep3/ep3_emperor_yearly_2.txt": (
                "5B59252EF885BB605529B1AE76964A03BA447255DB77951CDBF2CB2AE267BDCD"
            ),
        },
    },
    "ep3_emperor_yearly.2211": {
        "migrated_from": (
            "tools/zg361_phase2_promotion_vanilla_ep3_emperor_"
            "interrupt_contracts.py"
        ),
        "review_summary": (
            "Appointment-prophecy response: selected authored C/native3 only "
            "moves minor influence and avoids the hook, long modifier, "
            "appointment mutation, and follow-up used by other routes."
        ),
        "source_sha256": {
            "events/dlc/ep3/ep3_emperor_yearly_2.txt": (
                "5B59252EF885BB605529B1AE76964A03BA447255DB77951CDBF2CB2AE267BDCD"
            ),
            "localization/english/dlc/ep3/"
            "ep3_emperor_yearly_2_l_english.yml": (
                "1CE764CFEB02858BF5D978ED10DA7C1E68BE48A2281374F1FFE86C0F6DC4BBBE"
            ),
            "localization/simp_chinese/dlc/ep3/"
            "ep3_emperor_yearly_2_l_simp_chinese.yml": (
                "920FBE1BC3B5B3A46A009ECDD0C6C48AA2B5B5C676781530BBC289DC70FA928D"
            ),
        },
    },
    "ep3_powerful_families.8012": {
        "migrated_from": (
            "tools/zg361_phase2_promotion_vanilla_ep3_emperor_"
            "interrupt_contracts.py"
        ),
        "review_summary": (
            "Powerful-family war offer: selected native1 refuses, grants only "
            "minor influence to the family, does not add it to the war, and "
            "schedules no follow-up."
        ),
        "source_sha256": {
            "events/dlc/ep3/ep3_powerful_families_8.txt": (
                "CA19D38CD1C45783E32CF59E21A212642EA407B2DDD8EDE2467DF50ED9F7BC7A"
            ),
        },
    },
    "historical_char_creation_events.1": {
        "migrated_from": (
            "tools/zg361_phase2_promotion_vanilla_historical_character_"
            "interrupt_contracts.py"
        ),
        "review_summary": (
            "Historical-character arrival: in the reviewed human-player, "
            "no-explorer projection, selected native2 grants only minor "
            "prestige and reaches neither landless-adventurer branch."
        ),
        "source_sha256": {
            "events/historical_character_events.txt": (
                "ACE7B285D613419B17F2EC52BC1CE81A2DAAA8515B7CC159E0DC1E34BA4ACC8B"
            ),
            "common/scripted_effects/"
            "00_historical_characters_scripted_effects.txt": (
                "0742FC261C844979E9B6311B297502172400B8B5A6A70743122DDB30DE8B632D"
            ),
        },
    },
    "intrigue_temptation.3020": {
        "migrated_from": (
            "tools/zg361_phase2_promotion_vanilla_intrigue_temptation_"
            "interrupt_contracts.py"
        ),
        "review_summary": (
            "Intrigue temptation: native0 starts the multi-card romantic "
            "candidate chain; selected native1 terminates with only the "
            "five-year picky-about-partners modifier."
        ),
        "source_sha256": {
            "events/lifestyles/intrigue_lifestyle/"
            "intrigue_temptation_events.txt": (
                "C8413C1DE5EB1B29BC37A6F5A8A730290499A8FAE75578DBC6C085639B5C6248"
            ),
            "common/on_action/lifestyles/intrigue_lifestyle_on_actions.txt": (
                "E90B02C7E82F9D6B45BD4494DB5A4AD47E48C10232C3C1CF26BBFE9375EBA9CA"
            ),
        },
    },
    "natural_disaster.8001": {
        "migrated_from": (
            "tools/zg361_phase2_promotion_vanilla_natural_disaster_"
            "interrupt_contracts.py"
        ),
        "review_summary": (
            "Warning-phase join event: native0 is the sole acknowledgement "
            "and invokes only the warning tooltip; reviewed earthquake and "
            "flood scope shapes are both retained."
        ),
    },
    "natural_disaster.7021": {
        "migrated_from": (
            "tools/zg361_phase2_promotion_vanilla_natural_disaster_"
            "interrupt_contracts.py"
        ),
        "review_summary": (
            "Flood-warning pulse: selected native2 only renders the warning "
            "tooltip, avoiding native0 power sharing and native1 isolation; "
            "the common after block still records the first warning."
        ),
    },
    "natural_disaster.6901": {
        "migrated_from": (
            "tools/zg361_phase2_promotion_vanilla_natural_disaster_"
            "interrupt_contracts.py"
        ),
        "review_summary": (
            "Recovery-phase start notice: the situation has already "
            "published the flood context and native0 is the sole empty "
            "terminal acknowledgement."
        ),
    },
    "travel_danger_events.3002": {
        "migrated_from": (
            "tools/zg361_phase2_promotion_vanilla_natural_disaster_"
            "interrupt_contracts.py"
        ),
        "review_summary": (
            "Avalanche follow-up: selected native1 spends minor gold but "
            "avoids native0's four-year province penalty; both legal scope "
            "shapes retain dynamically selected participants."
        ),
        "source_sha256": {
            "events/travel_events/travel_danger_events_klank.txt": (
                "3345F8DDB93F72BFC20ACF6E2590C43DD884BFD91FE27525FFDB1C3286E3049F"
            ),
        },
    },
    "secrets.0108": {
        "migrated_from": (
            "tools/zg361_phase2_promotion_vanilla_secret_"
            "interrupt_contracts.py"
        ),
        "review_summary": (
            "Lover-secret notification: neither imprisonment option is legal "
            "in the reviewed projections, so native0 is the sole rendered "
            "route and its option body is empty."
        ),
    },
    "secrets.0112": {
        "migrated_from": (
            "tools/zg361_phase2_promotion_vanilla_secret_"
            "interrupt_contracts.py"
        ),
        "review_summary": (
            "Illegitimate-child or parent notification: secret-type effects "
            "occur before dispatch, while native0 is the sole rendered empty "
            "acknowledgement in both reviewed scope shapes."
        ),
    },
    "secrets.0122": {
        "migrated_from": (
            "tools/zg361_phase2_promotion_vanilla_secret_"
            "interrupt_contracts.py"
        ),
        "review_summary": (
            "Embezzlement exposure: selected authored C/native2 forgives with "
            "an opinion effect and trait-dependent stress, avoiding authored "
            "B's imprisonment and the larger unrelated realm mutation."
        ),
    },
    "seduce_outcome.4900": {
        "migrated_from": (
            "tools/zg361_phase2_promotion_vanilla_seduce_"
            "interrupt_contracts.py"
        ),
        "review_summary": (
            "Failed-seduction notification to the target liege: native0 is "
            "unavoidable and applies the already-determined publicised-crime "
            "outcome after the complete scheme scope carry is bound."
        ),
    },
    "seduce_outcome.3901": {
        "migrated_from": (
            "tools/zg361_phase2_promotion_vanilla_seduce_"
            "interrupt_contracts.py"
        ),
        "review_summary": (
            "Successful-seduction discovery notice to the target liege: its "
            "sole native0 route applies the authored discovery effect and "
            "has no inert alternative."
        ),
    },
}


_NATURAL_DISASTER_SOURCE_SHA256: Final[dict[str, str]] = {
    "events/situation_events/tgp_natural_disaster_events.txt": (
        "9595A5C28C14765142E83229EFC215FE06D457C447DC733537677629AD97DF68"
    ),
    "common/on_action/dlc/tgp/tgp_natural_disaster_on_actions.txt": (
        "7FA3F8BA729BAA8D4CE716F0DB88A19D8CE4D86C9BE441A6324759780E5F8D95"
    ),
    "common/scripted_effects/"
    "10_dlc_tgp_natural_disaster_scripted_effects.txt": (
        "48483CB13CF885203C43316C4990B684BC9D6ED5B5B3A664CCF228F59EAE44D7"
    ),
    "common/situation/situations/tgp_natural_disaster.txt": (
        "158984B899B9A8AA2667B2F67581C2C1C087B48DB9D14A3D934A68AEC4720E18"
    ),
}

for _event_key in (
    "natural_disaster.8001",
    "natural_disaster.7021",
    "natural_disaster.6901",
):
    _REVIEW_ROWS[_event_key]["source_sha256"] = dict(
        _NATURAL_DISASTER_SOURCE_SHA256
    )


def _json_safe(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _option_boundary(contract: dict[str, object]) -> dict[str, object]:
    boundary: dict[str, object] = {
        "rendered_option_count": contract["option_count"],
        "snapshot_option_count": contract.get(
            "snapshot_option_count", contract["option_count"]
        ),
        "native_option_indices": contract["native_option_indices"],
    }
    if "option_variants" in contract:
        boundary["variants"] = contract["option_variants"]
    return _json_safe(boundary)  # type: ignore[return-value]


def _scope_boundary(contract: dict[str, object]) -> dict[str, object]:
    boundary: dict[str, object] = {
        "saved_scope_name_sets": contract["saved_scope_name_sets"],
        "scope_types": contract["scope_types"],
        "boolean_scopes": contract.get("boolean_scopes", ()),
    }
    if "saved_scope_count" in contract:
        boundary["saved_scope_count"] = contract["saved_scope_count"]
    for field in (
        "unavailable_character_scopes",
        "unique_character_scope_excludes",
        "character_scope_matches_any",
        "character_scope_differs_from",
        "scope_variants",
    ):
        if field in contract:
            boundary[field] = contract[field]
    return _json_safe(boundary)  # type: ignore[return-value]


def _occurrence_boundary(contract: dict[str, object]) -> dict[str, object]:
    if "occurrence_policy" in contract:
        return {"policy": contract["occurrence_policy"]}
    return {"max_occurrences": contract["max_occurrences"]}


def _build_analysis() -> dict[str, dict[str, object]]:
    if set(_REVIEW_ROWS) != set(VANILLA_SHARD_TIMELINE_CONTRACTS):
        raise AssertionError("vanilla shard analysis keys must match contracts")

    analysis: dict[str, dict[str, object]] = {}
    for event_key, contract in VANILLA_SHARD_TIMELINE_CONTRACTS.items():
        review = _REVIEW_ROWS[event_key]
        record: dict[str, object] = {
            "exact_build": {
                "game_version": EXACT_CK3_BUILD,
                "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
            },
            "migrated_from": review["migrated_from"],
            "review_summary": review["review_summary"],
            "safe_option_number": contract["selected_option_number"],
            "safe_native_option_index": contract[
                "selected_native_option_index"
            ],
            "option_boundary": _option_boundary(contract),
            "scope_boundary": _scope_boundary(contract),
            "occurrence_boundary": _occurrence_boundary(contract),
        }
        if "source_sha256" in review:
            record["source_sha256"] = review["source_sha256"]
        analysis[event_key] = _json_safe(record)  # type: ignore[assignment]
    return analysis


VANILLA_SHARD_ANALYSIS: Final[dict[str, dict[str, object]]] = _build_analysis()


__all__ = ["VANILLA_SHARD_ANALYSIS"]
