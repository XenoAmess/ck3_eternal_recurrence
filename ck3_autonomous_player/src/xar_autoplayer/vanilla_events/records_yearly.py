"""Reusable CK3 1.19.0.6 records for reviewed yearly events.

The contract is source-shaped and campaign-neutral.  R414 contributes the
first paused native observation; its date, process, event-instance, and
character identities remain evidence metadata only.
"""

from __future__ import annotations

from typing import Final

from .registry import (
    EXACT_CK3_BUILD,
    EXACT_CK3_EXE_SHA256,
    PLAYER_SENTINEL,
)


VANILLA_YEARLY_TIMELINE_CONTRACTS: Final[dict[str, dict[str, object]]] = {
    "yearly.0003": {
        # The event always saves two different relatives and their lover
        # secret.  Authored option 4 is trigger-gated and was hidden in R414;
        # retain the three rendered native rows and choose the protective,
        # terminal first option.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "child": (PLAYER_SENTINEL,),
            "relative": (PLAYER_SENTINEL,),
        },
        "character_scope_differs_from": {
            "child": ("relative",),
            "relative": ("child",),
        },
        "scope_types": {
            "child": "character",
            "relative": "character",
            "secret": "secret",
        },
        "saved_scope_name_sets": (("child", "relative", "secret"),),
        "saved_scope_count": 3,
        "boolean_scopes": (),
        "option_count": 3,
        "snapshot_option_count": 4,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
    "yearly.1030": {
        # A hooked character offers a third party's secret. The exact source
        # makes the target ineligible when ROOT already has a hook on them, so
        # the two saved characters are distinct AI characters. Choose the
        # peaceful exchange: release the existing hook, learn the secret, and
        # avoid the coercive wound roll or declining the information.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "character_scopes": {},
        "unique_character_scope_excludes": {
            "secret_character": (PLAYER_SENTINEL,),
            "hooked": (PLAYER_SENTINEL,),
        },
        "character_scope_differs_from": {
            "secret_character": ("hooked",),
            "hooked": ("secret_character",),
        },
        "scope_types": {
            "secret_character": "character",
            "secret": "secret",
            "hooked": "character",
        },
        "saved_scope_name_sets": (("secret_character", "secret", "hooked"),),
        "saved_scope_count": 3,
        "boolean_scopes": (),
        "option_count": 3,
        "snapshot_option_count": 3,
        "native_option_indices": (0, 1, 2),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


VANILLA_YEARLY_ANALYSIS: Final[dict[str, dict[str, object]]] = {
    "yearly.0003": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
            "steam_build_id": 23530548,
            "branch": "titus/release/1.19.0",
        },
        "source_sha256": {
            "events/yearly_events/yearly_events.txt": (
                "FBBD29C7C9ECDCB84342EF4F00E92358412781B27E0686DCC220592996FEF0E5"
            ),
            "common/on_action/yearly_on_actions.txt": (
                "0FC85A284224A68D1CA0A4EF071D4F4A4F49896753AEC463975A12EE4E1116FA"
            ),
        },
        "definition_lines": "766-1103",
        "trigger_lines": "789-798",
        "weight_multiplier_lines": "800-829",
        "immediate_effect_lines": "831-956",
        "option_lines": "958-1102",
        "yearly_pulse_lines": "2522-2563",
        "yearly_pool_lines": "2933-2941",
        "caller_semantics": (
            "code invokes random_yearly_playable_pulse once per playable "
            "character at an independently random point each year; that pulse "
            "can choose on_yearly_events with group weight six, whose inner "
            "twenty-five-percent random-event pool assigns this event weight ten"
        ),
        "frequency_boundary": (
            "the exact annual probability varies with valid outer groups and "
            "inner candidates. The event is a yearly-pulse candidate, has no "
            "daily poll, and defines no cooldown or one-shot flag"
        ),
        "trigger_boundary": (
            "ROOT must have an eligible child who in turn has an eligible close "
            "or extended family member for the forbidden-love pairing"
        ),
        "weight_boundary": (
            "base event weight is one half, rises for eligible lustful or deviant "
            "children, and receives an additional five for a human ROOT"
        ),
        "immediate_effect": (
            "selects the child and relative, establishes their lover relation "
            "when permitted, saves the matching lover secret, and reveals that "
            "secret privately to ROOT before any player option is chosen"
        ),
        "scope_boundary": (
            "child and relative are distinct non-ROOT characters; secret is a "
            "generic secret scope whose stable identity is not exposed by the "
            "current bridge. Campaign identities do not enter the contract"
        ),
        "option_semantics": {
            0: (
                "protects both characters: each gains fifty grateful opinion of "
                "ROOT, child gains the protection modifier for fifteen years, "
                "and relative gains it too when ROOT is their liege; zealous or "
                "vengeful ROOT can take minor stress"
            ),
            1: (
                "gains minor piety and publicly exposes the lover secret; cynical "
                "or lustful ROOT can take minor stress"
            ),
            2: (
                "gains minor dread, attempts source-defined imprisonment for each "
                "eligible participant, then exposes the lover secret; lustful, "
                "forgiving, or compassionate ROOT can take minor stress"
            ),
            3: (
                "is trigger-gated by approval and cheating predicates; it can "
                "establish lover relations with ROOT, performs two sex effects, "
                "creates a threesome memory, and has chaste or zealous stress"
            ),
        },
        "native_ai_boundary": (
            "the four options define no explicit ai_chance blocks in the exact "
            "source. This record therefore does not infer a hidden native utility "
            "ranking; its selection is the bounded product continuation policy"
        ),
        "after_effect": None,
        "follow_up_event": None,
        "repeatability": (
            "the definition has no cooldown or one-shot flag, so another eligible "
            "yearly pulse may select it later"
        ),
        "safe_option_rationale": (
            "authored option 1/native 0 is terminal and avoids public exposure, "
            "imprisonment attempts, dread/piety policy changes, and the sexual "
            "effects of the gated fourth option. Its bounded downside is only the "
            "declared minor stress for zealous or vengeful ROOT"
        ),
    },
    "yearly.1030": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
            "steam_build_id": 23530548,
            "branch": "titus/release/1.19.0",
        },
        "source_sha256": {
            "events/yearly_events/yearly_events_2.txt": (
                "64B778B7B3DFE1056EB0151A7ED3AA7CFB3E6E738E68144006BAF97E93E0A3E8"
            ),
            "common/on_action/yearly_on_actions.txt": (
                "0FC85A284224A68D1CA0A4EF071D4F4A4F49896753AEC463975A12EE4E1116FA"
            ),
            "localization/english/event_localization/yearly_events/"
            "yearly_events_2_l_english.yml": (
                "49FEA5E7066464140EBAF10421C356DF3CED5DB1370C11210F658E446DC16440"
            ),
            "localization/simp_chinese/event_localization/yearly_events/"
            "yearly_events_2_l_simp_chinese.yml": (
                "F6A248C14B923AA4ED33753C766DE302D67705DFC2065CBB27A6A4A04FF18631"
            ),
        },
        "definition_lines": "2927-3277",
        "trigger_lines": "2957-2977",
        "immediate_effect_lines": "2979-3103",
        "option_lines": "3105-3276",
        "yearly_pool_lines": "2933-2946",
        "caller_semantics": (
            "code invokes random_yearly_playable_pulse once per playable "
            "character at an independently random point each year; the selected "
            "on_yearly_events pool has a twenty-five-percent chance to produce an "
            "event and gives yearly.1030 weight one hundred among valid candidates"
        ),
        "frequency_boundary": (
            "the event adds had_event_yearly_1030 for two thousand days in immediate. "
            "It can recur after that flag expires if ROOT again has both an eligible "
            "hooked character and an eligible secret target"
        ),
        "trigger_boundary": (
            "ROOT must have an available AI adult hooked character at ROOT's "
            "location and a separate eligible rival, spouse, powerful vassal, "
            "councillor, or liege whose secret ROOT does not already know and on "
            "whom ROOT has no hook"
        ),
        "immediate_effect": (
            "sets the two-thousand-day cooldown flag, chooses secret_character, "
            "creates an eligible secret for that character only when necessary, "
            "saves the secret scope, and chooses the hooked character who offers it"
        ),
        "scope_boundary": (
            "secret_character and hooked are distinct non-player character scopes. "
            "secret is a generic secret scope whose stable identity is not exposed "
            "by the current bridge; campaign identities do not enter the contract"
        ),
        "option_semantics": {
            0: (
                "removes ROOT's hook on hooked, reveals secret to ROOT, and gives "
                "hooked ten grateful opinion of ROOT; declared personality stress "
                "can apply to arrogant, ambitious, greedy, deceitful, paranoid, "
                "callous, sadistic, or vengeful ROOT"
            ),
            1: (
                "keeps the hook and forces disclosure, gives hooked thirty negative "
                "cruelty opinion, and has a thirty-three-percent wound roll; declared "
                "personality stress can also apply"
            ),
            2: (
                "keeps the hook but declines the secret, giving hooked ten negative "
                "disappointed opinion; ambitious, vengeful, or paranoid ROOT can "
                "take declared stress"
            ),
        },
        "native_ai_weights": {
            0: "base 100 with opinion and personality modifiers",
            1: "base 100 with opinion, personality, and compassion modifiers",
            2: "base 100 with opinion and personality modifiers",
        },
        "after_effect": None,
        "follow_up_event": None,
        "safe_option_rationale": (
            "authored option 1/native 0 is the only route that reveals the secret "
            "without coercion, a wound roll, or negative opinion. Its bounded costs "
            "are surrendering the existing hook and any declared personality stress"
        ),
    },
}


VANILLA_YEARLY_OBSERVATIONS: Final[dict[str, dict[str, object]]] = {
    "yearly.0003": {
        "exemplars": [{
            "run": "R414",
            "kind": "retained-live-contract-red",
            "red_classification": "harness-route-red",
            "product_failure_proven": False,
            "artifact": (
                "_runtime/p1-post-chaos-terminal-r414-20260911/"
                "live-artifacts/terminal-stages-red.json"
            ),
            "artifact_sha256": (
                "7C41E07DA8BD1ACA6F3DB14EF208E35030A63EEAD99D86B7179638FB1A328279"
            ),
            "date_raw": 53639352,
            "event_instance_id": 1064,
            "root_character_id": 32904,
            "saved_character_ids": {
                "child": 37804,
                "relative": 33606148,
            },
            "saved_scope_raw_types": {
                "child": 4,
                "relative": 4,
                "secret": 7,
            },
            "snapshot_option_count": 4,
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
    "yearly.1030": {
        "exemplars": [{
            "run": "R418-retry-03",
            "kind": "retained-live-contract-red",
            "red_classification": "harness-route-red",
            "product_failure_proven": False,
            "artifact": (
                "_runtime/p1-terminal-resume-r418-20260911/live-artifacts/"
                "terminal-stages-red-attempt-03.json"
            ),
            "artifact_sha256": (
                "A814FA6203FC0EC0E1BAA17E2D9DC7C3CA586E3F69B12A0B33CAC30832B89E90"
            ),
            "date_raw": 53943096,
            "event_instance_id": 1096,
            "root_character_id": 32904,
            "snapshot_id": "native:456",
            "revision": 457,
            "native_revision": 456,
            "saved_character_ids": {
                "secret_character": 50407232,
                "hooked": 88187,
            },
            "saved_scope_raw_types": {
                "secret_character": 4,
                "secret": 7,
                "hooked": 4,
            },
            "rendered_native_option_indices": [0, 1, 2],
            "selected_option_number": None,
            "selected_native_option_index": None,
            "selection_attempted": False,
            "retained_red": True,
            "process_id": 204536,
            "connection_generation": 1,
            "process_restart_required": False,
            "mcp_only": True,
            "fixture_used": False,
            "ocr_used": False,
            "coordinates_used": False,
            "console_used": False,
        }, {
            "run": "R418-attempt-04",
            "kind": "same-process-hot-recovery-green",
            "artifact": (
                "_runtime/p1-terminal-resume-r418-20260911/live-artifacts/"
                "terminal-stages-red-attempt-04.json"
            ),
            "artifact_sha256": (
                "5F1710E928F214C28FF4DF19478117F333E22473BF9E9713F0039AE766138146"
            ),
            "date_raw": 53943096,
            "event_instance_id": 1096,
            "root_character_id": 32904,
            "bridge_pid": 204536,
            "connection_generation": 1,
            "selected_option_number": 1,
            "selected_native_option_index": 0,
            "starting_snapshot_id": "native:457",
            "starting_revision": 458,
            "ending_snapshot_id": "native:458",
            "ending_revision": 459,
            "postcondition_verified": True,
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
    "VANILLA_YEARLY_ANALYSIS",
    "VANILLA_YEARLY_OBSERVATIONS",
    "VANILLA_YEARLY_TIMELINE_CONTRACTS",
]
