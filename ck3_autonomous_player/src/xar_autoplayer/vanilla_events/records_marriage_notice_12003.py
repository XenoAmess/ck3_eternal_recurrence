"""The observed 1.20.0.3 marriage acceptance letter's empty acknowledgement."""

from typing import Final

from .builds import SUPPORTED_CK3_EXE_SHA256
from .registry import PLAYER_SENTINEL


_DEFINITION_PATH: Final = "events/interaction_events/marriage_interaction_events.txt"
_DEFINITION_SHA256: Final = (
    "78C367BA0B32A374E5BE5D88F7660E7898EF9DBC44412049521F64A472E4DCA5"
)
_SCOPE_TYPES: Final = {
    "actor": "character",
    "recipient": "character",
    "secondary_actor": "character",
    "secondary_recipient": "character",
    "intermediary": "character-or-unavailable",
    "puppet_or_actor": "character",
    "is_puppet_action": "boolean",
    "grand_wedding_promise": "boolean",
    "matrilineal": "boolean",
    "hook": "boolean",
    "piety_cost_reduction": "boolean",
    "influence_send_option": "boolean",
    "herd_send_option": "boolean",
}

MARRIAGE_NOTICE_12003_RECORDS: Final = {
    "marriage_interaction.0010": {
        "contract": {
            "date_policy": "product-observation-window",
            "root_character_id": PLAYER_SENTINEL,
            "scope_types": _SCOPE_TYPES,
            "saved_scope_name_sets": (tuple(_SCOPE_TYPES),),
            "saved_scope_count": len(_SCOPE_TYPES),
            "option_count": 1,
            "snapshot_option_count": 1,
            "native_option_indices": (0,),
            "selected_option_number": 1,
            "selected_native_option_index": 0,
            "occurrence_policy": "repeatable-within-product-observation-window",
        },
        "analysis": {
            "exact_build": {
                "game_version": "1.20.0.3",
                "ck3_executable_sha256": SUPPORTED_CK3_EXE_SHA256["1.20.0.3"],
                "steam_build_id": 25652598,
            },
            "source_sha256": {_DEFINITION_PATH: _DEFINITION_SHA256},
            "definition_lines": "381-1039",
            "definition_block_sha256": (
                "8E5ACF62D61EB56689DEDA043D99245C57CD122668A8FFEC5B4D935761F7633A"
            ),
            "event_type": "letter_event",
            "immediate_effect_lines": "1016-1034",
            "immediate_effect": (
                "show_as_tooltip describes the previously accepted marriage or "
                "betrothal; acknowledging this letter does not create either relation"
            ),
            "option_lines": "1036-1038",
            "option_semantics": {"0": "EXCELLENT; empty acknowledgement option"},
            "native_ai_weights": {"0": "sole authored option; no ai_chance block"},
            "after_effect": None,
            "follow_up_event": None,
            "scope_boundary": (
                "the observed thirteen interaction scopes include a null intermediary; "
                "its character type can be available while its typed identity is unavailable"
            ),
            "safe_option_rationale": (
                "choose the sole shown and enabled native 0 only when the player root, "
                "observed scope envelope and option projection match"
            ),
            "selected_choice_effect_profile": {
                "schema": "xar.ck3.vanilla-event-choice-effect",
                "schema_version": 1,
                "selected_native_option_index": 0,
                "completeness": "all-authored-options-and-common-after-source-reviewed",
                "selected_option_effects": [],
                "common_after_effects": [],
                "observable_postcondition": None,
                "source_anchors": [f"{_DEFINITION_PATH}:381-1039"],
                "source_sha256": _DEFINITION_SHA256,
            },
            "readiness": "static-ready",
            "new_live_evidence": False,
            "material_evidence_boundary": (
                "modal dismissal is acknowledgement only; marriage results precede "
                "the modal and cannot supply M2 selected-choice material credit"
            ),
        },
        "observations": {
            "exemplars": [{
                "kind": "closed-production-red",
                "artifact": (
                    "artifacts/g2-maintainer-2026-10-02/resume-12003/"
                    "m7-murchad/formal-v10-01/turn-004/natural-event/result.json"
                ),
                "checkpoint_sha256": (
                    "5789934E31C255740A09EBF71F80429B949147815626A5163DDAE6D2DCF23CFC"
                ),
                "event_instance_id": 13,
                "root_character_id": 31853,
                "date_raw": 53328600,
                "selection_attempted": False,
                "boundary": "saved checkpoint and authored-source review; no live acknowledgement",
            }],
        },
    },
}
