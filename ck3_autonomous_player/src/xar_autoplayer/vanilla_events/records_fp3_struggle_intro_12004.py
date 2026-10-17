"""Reviewed Persian struggle bookmark introduction; no choice gameplay effects."""
from typing import Final

from .builds import SUPPORTED_CK3_EXE_SHA256
from .registry import PLAYER_SENTINEL

EVENT_KEY: Final = "fp3_struggle.0051"
SOURCE_PATH: Final = "events/dlc/fp3/fp3_struggle_events.txt"
SOURCE_SHA256: Final = "31989C33ECAEA73D2F2ED536813B8815B0CD90CB2A824E6DC9D85BC47A531C52"
FP3_STRUGGLE_INTRO_12004_RECORD: Final = {
    "contract": {
        "date_policy": "product-observation-window", "root_character_id": PLAYER_SENTINEL,
        "option_count": 1, "snapshot_option_count": 1, "native_option_indices": (0,),
        "selected_option_number": 1, "selected_native_option_index": 0,
        "saved_scope_count": 5,
        "saved_scope_name_sets": (("start", "Mutawakkil", "Muntasir", "Mustain", "Mostaza"),),
        "scope_types": {"start":"boolean", "Mutawakkil":"character", "Muntasir":"character",
            "Mustain":"character", "Mostaza":"character"},
        "occurrence_policy": "once-per-character-intro-flag", "startup_acknowledgement": True,
    },
    "analysis": {
        "exact_build": {"game_version":"1.20.0.4", "ck3_executable_sha256":SUPPORTED_CK3_EXE_SHA256["1.20.0.4"]},
        "source_sha256": {SOURCE_PATH:SOURCE_SHA256}, "definition_lines":"102-222",
        "definition_block_utf8_sha256":"DFAEFDA8591838035E846C2954408E8EAB5DD4BB7BA9B3A52D1E507568692731",
        "event_type":"character_event", "window":"fullscreen_event",
        "trigger":"Human player in persian_struggle without fp3_struggle_intro_event_flag; cooldown 100 years.",
        "immediate_effect_lines":"187-204",
        "immediate_effect":"Music, intro flag, global intro-flag list, start=yes and four historical LOC scopes are applied before choosing.",
        "option_lines":"205-221", "option_semantics":{"0":"Acknowledge introduction; dynamic first_valid a/b changes only its label; clicksound only."},
        "native_ai_weights":{"0":"sole authored option; no authored ai_chance"},
        "after_effect":None, "follow_up_event":None,
        "safe_option_rationale":"Current exact native event/root, one shown enabled native0/public1; independently observe old instance advancing, including a queued successor.",
        "selected_choice_effect_profile": {
            "schema":"xar.ck3.vanilla-event-choice-effect", "schema_version":1,
            "selected_native_option_index":0, "completeness":"all-authored-options-and-common-after-source-reviewed",
            "selected_option_effects":[], "common_after_effects":[], "observable_postcondition":None,
            "source_anchors":[f"{SOURCE_PATH}:102-222"], "source_sha256":SOURCE_SHA256,
        },
        "readiness":"static-ready", "new_live_evidence":False,
        "material_evidence_boundary":"Observed typed window is not selection credit. No faith/rite/piety/date change is predicted by this option; immediate effects are not attributed to its confirmation.",
    },
    "observations": {"exemplars":[{
        "machine_id":"4-8e1c2f1861", "observed_at_utc":"2026-10-17T08:30:51.334897Z",
        "kind":"actual-startup-readonly-contract-red", "run":"4-8e1c2f1861--faith-and-power--R0001",
        "artifact":"C:/workspace/ck3-faith-and-power-20261017/episode01/live/4-8e1c2f1861--faith-and-power--R0001/native-report.json",
        "bridge_pid":18236, "connection_generation":1, "event_instance_id":2,
        "root_character_id":15893, "native_revision":3, "public_revision":4, "date_raw":51394920,
        "typed_event_context_observed":True, "mcp_selection_attempted":False,
        "boundary":"Original host expected the later fixture preparation card; this earlier vanilla card remained unselected at this observation.",
    }]},
}
