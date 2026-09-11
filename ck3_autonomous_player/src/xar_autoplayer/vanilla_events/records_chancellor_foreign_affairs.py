"""Reusable CK3 1.19.0.6 record for the foreign-affairs failure letter."""

from __future__ import annotations

from typing import Final

from .registry import EXACT_CK3_BUILD, EXACT_CK3_EXE_SHA256, PLAYER_SENTINEL


VANILLA_CHANCELLOR_FOREIGN_AFFAIRS_TIMELINE_CONTRACTS: Final[
    dict[str, dict[str, object]]
] = {
    "chancellor_task.1004": {
        # This source-defined letter has exactly one unconditional option.  The
        # R445 frame was identified visually, so campaign scope identities stay
        # out of the portable contract until a native paused frame observes them.
        "date_policy": "product-observation-window",
        "root_character_id": PLAYER_SENTINEL,
        "option_count": 1,
        "snapshot_option_count": 1,
        "native_option_indices": (0,),
        "selected_option_number": 1,
        "selected_native_option_index": 0,
        "occurrence_policy": "repeatable-within-product-observation-window",
    },
}


VANILLA_CHANCELLOR_FOREIGN_AFFAIRS_ANALYSIS: Final[
    dict[str, dict[str, object]]
] = {
    "chancellor_task.1004": {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
            "steam_build_id": 23530548,
            "branch": "titus/release/1.19.0",
        },
        "source_sha256": {
            "events/councillor_task_events/chancellor_task_events.txt": (
                "EAF95612E4AEC6BF0CEDBC1ACA1C66C8087DD280BC42A60296F824437A5A46EB"
            ),
            "common/on_action/councillor_on_actions.txt": (
                "5629D03928014BAFDAB3E42576D20BBE13F2A76F0BECC0219B729515010EA95E"
            ),
            "common/council_tasks/00_chancellor_tasks.txt": (
                "503E04F591067DE14E8EC50D435717100BFC0BD678A032E7BF4052CB4FBF9A84"
            ),
            "localization/english/event_localization/councillor_task_events/"
            "chancellor_task_events_l_english.yml": (
                "8CF9446933CB9AC961E4DB042EEF3C95C96FFB50E12CC72732BE777FEBC3677F"
            ),
            "localization/simp_chinese/event_localization/councillor_task_events/"
            "chancellor_task_events_l_simp_chinese.yml": (
                "CDCBE4B082018E3BE75C5D64A08627B6F3BE2C57D83B6E3F0D2FF45ED6F19474"
            ),
        },
        "definition_lines": "508-525",
        "caller_event_lines": "383-505 (direct trigger at 470)",
        "on_action_lines": "245-264 (weighted candidate at 259)",
        "council_task_lines": "1-150 (monthly on_action at 150)",
        "caller_semantics": (
            "task_foreign_affairs runs task_foreign_affairs_side_effects monthly. "
            "Its weighted pool may select hidden chancellor_task.1003, which "
            "chooses a neighboring ruler and directly triggers .1004 when that "
            "neighbor meets the source-defined rank condition"
        ),
        "trigger_boundary": (
            ".1004 has no independent trigger; the hidden .1003 caller already "
            "validated the active chancellor, low diplomacy, neighbor, war, and "
            "five-year message cooldown conditions"
        ),
        "scope_boundary": (
            "R445 proves the rendered letter and localized option, but no native "
            "event-window query was attached. Dynamic councillor and neighbor "
            "identities therefore remain observation-pending and are not encoded "
            "as campaign constants"
        ),
        "immediate_effect": None,
        "option_semantics": {
            0: (
                "the selected neighbor gains "
                "chancellor_task_neighbor_decreased_opinion toward ROOT for "
                "chancellor_task_modifier_duration"
            ),
        },
        "after_effect": None,
        "follow_up_event": None,
        "repeatability": (
            "the hidden caller sets had_msg_chancellor_task_1003 for five years "
            "and had_chancellor_task_side_effect for the configured side-effect "
            "cooldown; the letter has no additional one-shot flag"
        ),
        "safe_option_rationale": (
            "authored option 1/native 0 is unconditional, terminal, and the only "
            "rendered route. Its negative opinion effect is unavoidable once the "
            "letter opens; selecting it resumes the timeline without adding any "
            "resource, war, title, imprisonment, injury, death, or follow-up effect"
        ),
    },
}


VANILLA_CHANCELLOR_FOREIGN_AFFAIRS_OBSERVATIONS: Final[
    dict[str, dict[str, object]]
] = {
    "chancellor_task.1004": {
        "exemplars": [{
            "run": "R445",
            "kind": "retained-visual-harness-red",
            "artifact": (
                "_runtime/g2-source-specific-r445-resume-20260911/"
                "live-artifacts/ui/"
                "bargain_g2-no-modal-stall-5_speed_5_stalled.png"
            ),
            "artifact_sha256": (
                "6CDFD461E08A80F197778CD748FC05239856A30FDD0BE7AEB4A0F2FC5B9D3D57"
            ),
            "displayed_date": "1069-08-16",
            "option_ocr_center": [1266, 984],
            "option_localization_key": "chancellor_task.1003.a",
            "native_event_context_available": False,
            "selection_attempted": False,
            "retained_red": True,
            "process_restart_required": True,
            "mcp_only": False,
            "fixture_used": False,
            "ocr_used": True,
            "coordinates_used": False,
            "console_used": False,
        }],
    },
}


__all__ = [
    "VANILLA_CHANCELLOR_FOREIGN_AFFAIRS_ANALYSIS",
    "VANILLA_CHANCELLOR_FOREIGN_AFFAIRS_OBSERVATIONS",
    "VANILLA_CHANCELLOR_FOREIGN_AFFAIRS_TIMELINE_CONTRACTS",
]
