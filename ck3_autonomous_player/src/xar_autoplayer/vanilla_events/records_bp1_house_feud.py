"""Reusable CK3 1.19.0.6 record for a house-feud reveal prompt."""

from __future__ import annotations

from typing import Final

from .registry import EXACT_CK3_BUILD, EXACT_CK3_EXE_SHA256, PLAYER_SENTINEL


_SCOPE_NAMES: Final = (
    "mother",
    "father",
    "real_father",
    "is_child_of_concubine",
    "matrilineal",
    "spouse",
    "adultery_spouse",
    "assumed_father",
    "secret_exposer",
    "sex_partner",
    "adulterer_check",
    "house_feud_spouse",
    "house_feud_rival",
    "house_feud_attacker",
    "house_feud_victim",
)


VANILLA_BP1_HOUSE_FEUD_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "bp1_house_feud.0014": {
        # The secret-exposure caller contributes birth/adultery aliases in
        # addition to the four house-feud scopes.  Freeze the observed exact
        # alias groups and choose the terminal forgive route; none of the R414
        # character identities are portable contract values.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "mother": (PLAYER_SENTINEL,),
            "father": (PLAYER_SENTINEL,),
            "real_father": (PLAYER_SENTINEL,),
        },
        "character_scope_matches_any": {
            "adulterer_check": ("mother",),
            "house_feud_spouse": ("mother",),
            "spouse": ("father",),
            "adultery_spouse": ("father",),
            "assumed_father": ("father",),
            "secret_exposer": ("father",),
            "house_feud_victim": ("father",),
            "sex_partner": ("real_father",),
            "house_feud_rival": ("real_father",),
            "house_feud_attacker": ("real_father",),
        },
        "character_scope_differs_from": {
            "mother": ("father", "real_father"),
            "father": ("mother", "real_father"),
            "real_father": ("mother", "father"),
        },
        "scope_types": {
            name: (
                "boolean"
                if name in {"is_child_of_concubine", "matrilineal"}
                else "character"
            )
            for name in _SCOPE_NAMES
        },
        "boolean_scopes": ("is_child_of_concubine", "matrilineal"),
        "saved_scope_name_sets": (_SCOPE_NAMES,),
        "saved_scope_count": 15,
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 3,
        "selected_native_option_index": 2,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


VANILLA_BP1_HOUSE_FEUD_ANALYSIS: Final[dict[str, dict[str, object]]] = {
    "bp1_house_feud.0014": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
            "steam_build_id": 23530548,
            "branch": "titus/release/1.19.0",
        },
        "source_sha256": {
            "events/dlc/bp1/bp1_house_feud.txt": (
                "37B6E662C4FC388E51D5B8EBC6F0FBCE7AE3FDCB825BFE121D23B971966469DA"
            ),
            "common/scripted_effects/03_bp1_scripted_effects.txt": (
                "30F4823A7A77C3FF6D96C5E43F3F4FC3F531D4A8584EDC8E99177A2BFE468ADB"
            ),
            "common/opinion_modifiers/01_dlc_bp1_opinions.txt": (
                "CF91227ABBABEC17D456BBFACE9FE68B7FF86C49A5990D26215EC41CD74002CE"
            ),
        },
        "definition_lines": "2310-2433",
        "trigger_lines": "2335-2343",
        "immediate_effect_lines": "2345-2348",
        "option_lines": "2350-2431",
        "caller_effect_lines": "467-529",
        "caller_event_lines": "519-525",
        "feud_start_effect_lines": "6-120",
        "vengeful_stress_effect_lines": "411-420",
        "ignored_opinion_lines": "113-117",
        "caller_semantics": (
            "house_feud_lover_exposure_effect runs when the lover secret is "
            "exposed, requires the BP1 feature and an eligible married character, "
            "then gives the relevant house head a seventy-five-percent base chance "
            "to schedule this close-family variant five to fifteen days later"
        ),
        "frequency_boundary": (
            "the event has no daily poll. Its exposure caller is conditional and "
            "the event itself declares a five-year cooldown; the exact campaign "
            "frequency depends on secret exposure and valid feud targets"
        ),
        "trigger_boundary": (
            "ROOT must remain a valid feud participant against house_feud_attacker, "
            "and ROOT's house must have no relation carrying house_feud_cooldown"
        ),
        "immediate_effect": (
            "plays the negative music cue and preserves any ongoing relation "
            "between ROOT's house and the saved rival house; it does not itself "
            "start a new feud"
        ),
        "scope_boundary": (
            "R414 inherited fifteen exact scopes from the secret-exposure chain. "
            "They resolve into three distinct non-ROOT character alias groups "
            "plus is_child_of_concubine and matrilineal boolean scopes"
        ),
        "option_semantics": {
            0: (
                "starts a family_cuckolded house feud through house_feud_start_effect, "
                "which can establish feud and rival or nemesis relations and a "
                "twenty-five-year relation cooldown, then gives the victim a "
                "source-defined feud opinion modifier toward ROOT"
            ),
            1: (
                "when ROOT can form the relation and is not already the attacker's "
                "rival, creates that personal rival relation and gives the victim "
                "the rival-opinion modifier; forgiving ROOT can gain minor stress"
            ),
            2: (
                "starts neither feud nor rival relation. The victim receives the "
                "Ignored Plight opinion modifier toward ROOT: minus fifteen, "
                "decaying over five years. ROOT gains source-defined stress when "
                "vengeful, arbitrary, wrathful, brave, ambitious, or arrogant"
            ),
        },
        "native_ai_weights": {
            0: (
                "base 25, scaled toward boldness and vengefulness, with factor "
                "1.25 for cultures where house hostility is more common"
            ),
            1: "base 25, boldness -0.5 and vengefulness +0.5",
            2: "base 25, boldness -1 and vengefulness -1",
        },
        "after_effect": None,
        "follow_up_event": None,
        "repeatability": (
            "the five-year event cooldown bounds recurrence; a later qualifying "
            "lover-secret exposure can schedule it again"
        ),
        "safe_option_rationale": (
            "authored option 3/native 2 is the only route that avoids creating a "
            "house feud or personal rivalry. Its bounded cost is the victim's "
            "minus-fifteen decaying opinion and the listed trait-dependent stress"
        ),
    },
}


VANILLA_BP1_HOUSE_FEUD_OBSERVATIONS: Final[dict[str, dict[str, object]]] = {
    "bp1_house_feud.0014": {
        "exemplars": [{
            "run": "R414",
            "kind": "retained-live-contract-red",
            "red_classification": "harness-route-red",
            "product_failure_proven": False,
            "artifact": (
                "_runtime/p1-post-chaos-terminal-r414-20260911/live-artifacts/"
                "terminal-stages-red-attempt-02.json"
            ),
            "artifact_sha256": (
                "A0837453C72CB67300AE07EB76EB2B53A75CB511838543696F2891BD2AF80346"
            ),
            "date_raw": 53671224,
            "event_instance_id": 1066,
            "root_character_id": 32904,
            "snapshot_id": "native:520",
            "revision": 521,
            "native_revision": 520,
            "saved_character_ids": {
                "mother": 81924,
                "father": 33606629,
                "real_father": 16850404,
            },
            "saved_scope_raw_types": {
                name: (2 if name in {"is_child_of_concubine", "matrilineal"} else 4)
                for name in _SCOPE_NAMES
            },
            "rendered_native_option_indices": [0, 1, 2],
            "selected_option_number": None,
            "selected_native_option_index": None,
            "selection_attempted": False,
            "retained_red": True,
            "process_restart_required": False,
            "mcp_only": True,
            "fixture_used": False,
            "ocr_used": False,
            "coordinates_used": False,
            "console_used": False,
        }],
    },
}


__all__ = [
    "PLAYER_SENTINEL",
    "VANILLA_BP1_HOUSE_FEUD_ANALYSIS",
    "VANILLA_BP1_HOUSE_FEUD_OBSERVATIONS",
    "VANILLA_BP1_HOUSE_FEUD_TIMELINE_CONTRACTS",
]
