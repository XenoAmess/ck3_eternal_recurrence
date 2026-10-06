"""Exact 1.20.0.3 bookmark introduction; acknowledging it changes presentation."""

from typing import Final

from .builds import SUPPORTED_CK3_EXE_SHA256
from .registry import PLAYER_SENTINEL


_PATH: Final = "events/dlc/tgp/tgp_dynastic_cycle_events.txt"
_SHA256: Final = "C2DB00C1C245131DC78741C2BDAC7232C97B22DB2212205FFD327CA4CB0E3CB7"

DYNASTIC_CYCLE_INTRO_12003_RECORDS: Final = {
    "tgp_dynastic_cycle.0051": {
        "contract": {
            "date_policy": "product-observation-window",
            "root_character_id": PLAYER_SENTINEL,
            "option_count": 1,
            "snapshot_option_count": 1,
            "native_option_indices": (0,),
            "selected_option_number": 1,
            "selected_native_option_index": 0,
            "occurrence_policy": "once-per-character-intro-flag",
            "startup_acknowledgement": True,
        },
        "analysis": {
            "exact_build": {
                "game_version": "1.20.0.3",
                "ck3_executable_sha256": SUPPORTED_CK3_EXE_SHA256["1.20.0.3"],
            },
            "source_sha256": {_PATH: _SHA256},
            "definition_lines": "44-218",
            "event_type": "character_event",
            "window": "fullscreen_event",
            "immediate_effect_lines": "184-191",
            "immediate_effect": (
                "music cue, tgp_dynastic_cycle_intro_event_flag and saved start=yes "
                "are applied before the choice"
            ),
            "authored_scope_boundary": (
                "start is saved by immediate; the custom situation widget saves "
                "situation; inherited runtime scopes have not been observed for a78. "
                "The sole option reads no scope for a gameplay effect: its three "
                "conditional names only select presentation. Preserve raw scopes."
            ),
            "option_lines": "192-217",
            "option_semantics": {
                "0": "acknowledge the introduction; conditional label and clicksound only",
            },
            "native_ai_weights": {"0": "sole authored option; no ai_chance"},
            "after_effect": None,
            "follow_up_event": None,
            "safe_option_rationale": (
                "typed exact event/build, current player ROOT, sole shown enabled "
                "native0 and matching public option1; verify a later event-free frame"
            ),
            "selected_choice_effect_profile": {
                "schema": "xar.ck3.vanilla-event-choice-effect",
                "schema_version": 1,
                "selected_native_option_index": 0,
                "completeness": "all-authored-options-and-common-after-source-reviewed",
                "selected_option_effects": [],
                "common_after_effects": [],
                "observable_postcondition": "same paused actor/date/process; active_event is null",
                "source_anchors": [f"{_PATH}:44-218"],
                "source_sha256": _SHA256,
            },
            "readiness": "static-ready",
            "new_live_evidence": False,
            "material_evidence_boundary": (
                "a78's screenshot and source identify the introduction; its manual "
                "dismissal is not typed MCP selection credit or product acceptance"
            ),
        },
        "observations": {
            "exemplars": [{
                "kind": "closed-production-readiness-red",
                "run": "4-8e1c2f1861--celestial-commerce-corruption--R0005",
                "artifact": "C:/workspace/ck3-upgrade-20261006/resume-root-01/a78-intro-before-01.png",
                "root_observation": "C:/workspace/ck3-upgrade-20261006/resume-root-01/a78-hot-observe-current-root-06.result.json",
                "root_observation_sha256": "2D96E56AE5891162A4887B3E8C464EA3C1853DDE6110B3AF604CE104F111A6B2",
                "root_character_id": 34422,
                "date_raw": 53144328,
                "bridge_pid": 12492,
                "connection_generation": 1,
                "typed_event_context_observed": False,
                "mcp_selection_attempted": False,
                "boundary": "manual intro dismissal followed by actual event-free owner frames and native root; original timeout remains RED",
            }],
        },
    },
}
