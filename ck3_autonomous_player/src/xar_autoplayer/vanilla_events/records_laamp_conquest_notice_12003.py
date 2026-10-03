"""Exact-source knowledge for the conquest loser's empty threat-letter reply."""

from typing import Final

from .builds import SUPPORTED_CK3_EXE_SHA256
from .registry import PLAYER_SENTINEL


_DEFINITION_PATH: Final = "events/dlc/ep3/ep3_laamp_events.txt"
_DEFINITION_SHA256: Final = (
    "BC5305EB51C0848D451E3815CFF60FC7719BE577BE3D50595E2682CBD4429C14"
)

LAAMP_CONQUEST_NOTICE_12003_RECORDS: Final = {
    "ep3_laamps.0003": {
        "contract": {
            "date_policy": "product-observation-window",
            "root_character_id": PLAYER_SENTINEL,
            "option_count": 1,
            "snapshot_option_count": 1,
            "native_option_indices": (0,),
            "selected_option_number": 1,
            "selected_native_option_index": 0,
            "occurrence_policy": "repeatable-within-product-observation-window",
            "scope_observation_policy": (
                "observe the actual native envelope; no saved-scope count or "
                "complete scope-name set is inferred from authored source"
            ),
        },
        "analysis": {
            "exact_build": {
                "game_version": "1.20.0.3",
                "ck3_executable_sha256": SUPPORTED_CK3_EXE_SHA256["1.20.0.3"],
                "steam_build_id": 25652598,
            },
            "source_sha256": {
                _DEFINITION_PATH: _DEFINITION_SHA256,
                "localization/simp_chinese/event_localization/laamp_events_l_simp_chinese.yml": (
                    "103A8E133C188595A9EFD9DB5DBA94785AEC46CC63CC9876ED0AC062EC0E67B4"
                ),
                "common/scripted_effects/07_dlc_ep3_scripted_effects.txt": (
                    "210FBB62DED6E6E48EFBD144CF60E01B66B7711BF79914BA70D8A6B5D841C7E6"
                ),
            },
            "definition_lines": "284-308",
            "definition_block_sha256": (
                "771F6C3FCBA164F88813D26089CE76F45C92E8DD7E3141809A45BCBB2C233237"
            ),
            "event_type": "letter_event",
            "event_trigger": "is_ai = no",
            "authored_scope_types": {
                "adventurer": "character",
                "lost_primary_title": "landed_title",
                "winner": "character",
            },
            "sender": "scope:adventurer",
            "producer_lines": "238-259",
            "producer_semantics": (
                "ep3_laamps.0002 creates the deposed or conquered AI's "
                "landless-adventurer title, then triggers this letter on winner"
            ),
            "immediate_effect_lines": "292-303",
            "immediate_effect": (
                "before the modal is acknowledged, set_relation_rival with "
                "scope:adventurer when not already rivals; reason rival_conquered_me. "
                "The adventurer-title helper at 07_dlc_ep3_scripted_effects.txt:813-820 "
                "contains only show_as_tooltip"
            ),
            "option_lines": "305-307",
            "option_semantics": {
                "0": "ep3_laamps.0003.a; empty acknowledgement, no authored effects"
            },
            "option_localization_keys": {"0": "ep3_laamps.0003.a"},
            "option_caption_simp_chinese": {"0": "哈！这蠢货还挺有精神！"},
            "native_ai_weights": {"0": "sole authored option; no ai_chance block"},
            "after_effect": None,
            "follow_up_event": None,
            "safe_option_rationale": (
                "only this exact definition's sole shown and enabled native 0 "
                "may be acknowledged after actual player-root, instance and "
                "revision binding; no permission for other ep3_laamps events "
                "or unidentified single-option modals"
            ),
            "selected_choice_effect_profile": {
                "schema": "xar.ck3.vanilla-event-choice-effect",
                "schema_version": 1,
                "selected_native_option_index": 0,
                "completeness": "all-authored-options-and-common-after-source-reviewed",
                "selected_option_effects": [],
                "common_after_effects": [],
                "observable_postcondition": None,
                "source_anchors": [f"{_DEFINITION_PATH}:284-308"],
                "source_sha256": _DEFINITION_SHA256,
            },
            "readiness": "static-ready",
            "new_live_evidence": False,
            "material_evidence_boundary": (
                "source knowledge only; actual saved scopes and successful "
                "acknowledgement are not claimed. Rivalry and title creation "
                "precede the reply and cannot supply selected-choice material credit"
            ),
        },
        "observations": {},
    },
}
