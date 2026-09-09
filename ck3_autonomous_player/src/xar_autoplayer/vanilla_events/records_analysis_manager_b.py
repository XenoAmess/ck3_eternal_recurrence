"""Reusable analysis metadata for the 21 manager-B vanilla events.

This module migrates conclusions already recorded in the manager-B contracts,
their comments, and focused tests.  It does not claim a fresh exhaustive source
review and deliberately omits source hashes that the existing records did not
preserve.
"""

from __future__ import annotations

from typing import Final

from .registry import EXACT_CK3_BUILD, EXACT_CK3_EXE_SHA256


def _analysis(
    *,
    migrated_from: str,
    review_summary: str,
    safe_native_option_index: int,
    safe_option_number: int,
    safe_option_rationale: str,
    scope_boundary: str,
    option_boundary: str,
    reviewed_safe_native_indices: list[int] | None = None,
) -> dict[str, object]:
    """Build one detached, JSON-safe migrated analysis record."""
    return {
        "exact_build": {
            "game_version": EXACT_CK3_BUILD,
            "ck3_executable_sha256": EXACT_CK3_EXE_SHA256,
        },
        "migrated_from": migrated_from,
        "review_basis": "existing-contract-comments-docs-and-focused-tests",
        "review_summary": review_summary,
        "safe_option": {
            "preferred_native_option_index": safe_native_option_index,
            "preferred_option_number": safe_option_number,
            "reviewed_safe_native_indices": list(
                reviewed_safe_native_indices
                if reviewed_safe_native_indices is not None
                else [safe_native_option_index]
            ),
            "rationale": safe_option_rationale,
        },
        "scope_boundary": scope_boundary,
        "option_boundary": option_boundary,
    }


_IMPERIAL_SOURCE = "tools/zg361_phase2_promotion_manager_imperial_contracts.py"
_NICKNAME_SOURCE = "tools/zg361_phase2_promotion_manager_nickname_contracts.py"
_PARENT_SOURCE = "tools/zg361_phase2_promotion_manager_parent_contracts.py"
_PRISON_SOURCE = "tools/zg361_phase2_promotion_manager_prison_contracts.py"
_SPYMASTER_SOURCE = "tools/zg361_phase2_promotion_manager_spymaster_contracts.py"
_TGP_INTERACTION_SOURCE = (
    "tools/zg361_phase2_promotion_manager_tgp_interaction_contracts.py"
)
_TGP_MINISTRY_SOURCE = (
    "tools/zg361_phase2_promotion_manager_tgp_ministry_contracts.py"
)
_TGP_PETITION_SOURCE = (
    "tools/zg361_phase2_promotion_manager_tgp_petition_contracts.py"
)
_TRAIT_SOURCE = "tools/zg361_phase2_promotion_manager_trait_contracts.py"
_TRIBUTE_SOURCE = "tools/zg361_phase2_promotion_manager_tribute_contracts.py"


MANAGER_VANILLA_ANALYSIS_B: Final[dict[str, dict[str, object]]] = {
    "ep3_emperor_yearly.8010": _analysis(
        migrated_from=_IMPERIAL_SOURCE,
        review_summary=(
            "The fake-letter immediate creates a liar under a selected "
            "governor's house arrest and exposes the same liar as new_target."
        ),
        safe_native_option_index=0,
        safe_option_number=1,
        safe_option_rationale=(
            "Native 0 ends the prompt with only the reviewed small payment and "
            "opinion change; the alternatives add a courtier or hook, transfer "
            "influence and imprisonment, or execute the liar."
        ),
        scope_boundary=(
            "Require governor, liar, and new_target as typed characters; liar "
            "and new_target alias each other and remain distinct from governor."
        ),
        option_boundary="Exactly the four reviewed authored options are visible.",
    ),
    "ep3_emperor_yearly.8000": _analysis(
        migrated_from=_IMPERIAL_SOURCE,
        review_summary=(
            "The manpower request can materialize either three governor/county "
            "pairs or the reviewed two-pair partial random selection."
        ),
        safe_native_option_index=0,
        safe_option_number=1,
        safe_option_rationale=(
            "Native 0 takes the lighter governor-county sacrifice route and "
            "avoids the heavier development loss and modifier on the player's "
            "capital."
        ),
        scope_boundary=(
            "Accept only the reviewed two- or three-pair typed frames, with "
            "distinct governors and matching county/value scopes; identities "
            "are intentionally not universal."
        ),
        option_boundary=(
            "The full frame exposes native 0/1/2/3; the reviewed partial frame "
            "exposes native 0/1/3."
        ),
    ),
    "lifestyle_nicknames.1000": _analysis(
        migrated_from=_NICKNAME_SOURCE,
        review_summary=(
            "The nickname has already been assigned before this notification; "
            "the reviewed bad-nickname/free/capable projection renders one of "
            "six authored options."
        ),
        safe_native_option_index=1,
        safe_option_number=2,
        safe_option_rationale="Native 1 is the sole rendered route out of the prompt.",
        scope_boundary=(
            "Bind the three player aliases, the third-party informer, and the two "
            "reviewed boolean scopes as one inherited nickname frame."
        ),
        option_boundary="Only native 1 is visible in the reviewed six-option view.",
    ),
    "parent.1005": _analysis(
        migrated_from=_PARENT_SOURCE,
        review_summary=(
            "The learning-support offer either starts a beneficial but "
            "follow-up-producing meddling path or terminates with parent opinion."
        ),
        safe_native_option_index=1,
        safe_option_number=2,
        safe_option_rationale=(
            "Native 1 applies the bounded parent opinion loss without a follow-up "
            "ticket, modifier, or meddling-ledger increment."
        ),
        scope_boundary="Require exactly the reviewed typed parent distinct from root.",
        option_boundary="Exactly native options 0 and 1 are visible.",
    ),
    "prison_notification.2002": _analysis(
        migrated_from=_PRISON_SOURCE,
        review_summary=(
            "This popup reports that a player's heir or spouse was released; "
            "release and memory creation have already happened."
        ),
        safe_native_option_index=0,
        safe_option_number=1,
        safe_option_rationale="The sole authored option is an empty acknowledgement.",
        scope_boundary=(
            "Bind player, prisoner, imprisoner, release memory, and background "
            "imprisoner alias; prisoner and imprisoner must remain distinct."
        ),
        option_boundary="Exactly one authored acknowledgement, native 0, is visible.",
    ),
    "spymaster_task.3001": _analysis(
        migrated_from=_SPYMASTER_SOURCE,
        review_summary=(
            "A Find Secrets side effect offers continuation or termination of "
            "the current Spymaster task."
        ),
        safe_native_option_index=0,
        safe_option_number=1,
        safe_option_rationale=(
            "Native 0 preserves the task and confines the result to the reviewed "
            "prestige/opinion effects and target notification."
        ),
        scope_boundary="Bind the reviewed councillor, liege, and target character tuple.",
        option_boundary="Exactly native options 0 and 1 are visible.",
    ),
    "spymaster_task.0381": _analysis(
        migrated_from=_SPYMASTER_SOURCE,
        review_summary=(
            "This repeatable Find Secrets outcome offers hook fabrication or a "
            "decaying opinion consequence for one typed third party."
        ),
        safe_native_option_index=1,
        safe_option_number=2,
        safe_option_rationale=(
            "Native 1 avoids spending gold and fabricating a hook; it only adds "
            "the reviewed decaying opinion modifier."
        ),
        scope_boundary=(
            "Bind the task owner tuple, having_find_secrets_event, and a typed "
            "character_to_hook distinct from the reviewed player identities."
        ),
        option_boundary="Exactly two authored options are reviewed.",
    ),
    "spymaster_task.0399": _analysis(
        migrated_from=_SPYMASTER_SOURCE,
        review_summary=(
            "The Find Secrets 'found nothing' delivery saves exactly one of the "
            "no-secrets or secrets-remain boolean branches."
        ),
        safe_native_option_index=1,
        safe_option_number=2,
        safe_option_rationale="Native 1 preserves the current councillor task.",
        scope_boundary=(
            "Bind the councillor/liege/target tuple and exactly one reviewed "
            "boolean branch: no_secrets_here or secrets_to_be_found."
        ),
        option_boundary="Exactly two authored options are reviewed.",
    ),
    "spymaster_task.0342": _analysis(
        migrated_from=_SPYMASTER_SOURCE,
        review_summary=(
            "The discovered secret and its participants are fixed before this "
            "notification opens."
        ),
        safe_native_option_index=0,
        safe_option_number=1,
        safe_option_rationale=(
            "The sole acknowledgement reveals the already-selected secret."
        ),
        scope_boundary=(
            "Bind the reviewed task characters, active councillor, secret holder, "
            "typed secret, and upstream Find Secrets boolean."
        ),
        option_boundary="Exactly one authored acknowledgement is reviewed.",
    ),
    "spymaster_task.0344": _analysis(
        migrated_from=_SPYMASTER_SOURCE,
        review_summary=(
            "The murder-secret notification has two mutually exclusive source "
            "projections depending on whether a matching murder scheme exists."
        ),
        safe_native_option_index=1,
        safe_option_number=2,
        reviewed_safe_native_indices=[0, 1],
        safe_option_rationale=(
            "Select the sole rendered acknowledgement: native 0 reveals the "
            "secret without a matching scheme, while native 1 reveals it and "
            "advances the already-running matching scheme."
        ),
        scope_boundary=(
            "Accept only the reviewed ten-scope frame or its eleven-scope scheme "
            "variant, retaining character aliases, differences, and typed secret."
        ),
        option_boundary=(
            "Exactly one button is rendered: native 0 or native 1 according to "
            "the reviewed scheme projection."
        ),
    ),
    "spymaster_task.0346": _analysis(
        migrated_from=_SPYMASTER_SOURCE,
        review_summary=(
            "The lover-secret discovery is fixed before the notification and "
            "has reviewed transient-boolean and retained-task-container frames."
        ),
        safe_native_option_index=0,
        safe_option_number=1,
        safe_option_rationale="The sole acknowledgement reveals the fixed lover secret.",
        scope_boundary=(
            "Accept only the complete reviewed lover/holder/secret task frame or "
            "its exact upstream-boolean sibling; reject mixed scope shapes."
        ),
        option_boundary="Exactly one authored acknowledgement, native 0, is visible.",
    ),
    "spymaster_task.0359": _analysis(
        migrated_from=_SPYMASTER_SOURCE,
        review_summary=(
            "This repeatable fallback reports a discovered secret that has no "
            "more specific Find Secrets flavor event."
        ),
        safe_native_option_index=0,
        safe_option_number=1,
        safe_option_rationale="The sole option reveals the already-existing secret.",
        scope_boundary=(
            "Bind the complete reviewed ten-scope task frame, its aliases, and "
            "the typed secret rather than allowing the namespace generically."
        ),
        option_boundary="Exactly one authored acknowledgement, native 0, is visible.",
    ),
    "tgp_interaction_event.0010": _analysis(
        migrated_from=_TGP_INTERACTION_SOURCE,
        review_summary=(
            "A governor requests military aid; the reviewed views either hide "
            "the war-join option or render all three authored options."
        ),
        safe_native_option_index=1,
        safe_option_number=2,
        safe_option_rationale=(
            "Native 1 is the bounded AI-default response and assigns the saved "
            "joining governor; native 2 opens another interaction window."
        ),
        scope_boundary=(
            "Bind actor, player recipient, saved joining governor, war and "
            "interaction booleans as the complete reviewed request frame."
        ),
        option_boundary=(
            "Accept only native 1/2 or the source sibling native 0/1/2; select "
            "native 1 in both views."
        ),
    ),
    "tgp_interaction_event.0015": _analysis(
        migrated_from=_TGP_INTERACTION_SOURCE,
        review_summary=(
            "This notification arrives after another governor has already been "
            "added to the recipient's wars."
        ),
        safe_native_option_index=0,
        safe_option_number=1,
        safe_option_rationale=(
            "Immediate and option only show tooltips; the sole option adds no "
            "further gameplay mutation."
        ),
        scope_boundary=(
            "Bind the reviewed actor/recipient/governor relationship and complete "
            "war-response frame for each independent delivery."
        ),
        option_boundary="Exactly one authored acknowledgement, native 0, is visible.",
    ),
    "tgp_china_ministry.0100": _analysis(
        migrated_from=_TGP_MINISTRY_SOURCE,
        review_summary=(
            "The treasury-budget renewal offers a picker, current-allocation "
            "retention, or enactment of the steward's saved preference."
        ),
        safe_native_option_index=1,
        safe_option_number=2,
        safe_option_rationale=(
            "Native 1 preserves the current allocation and terminates the prompt."
        ),
        scope_boundary=(
            "Bind the player treasury aliases, typed third-party steward, and "
            "exactly one reviewed celestial or meritocratic preference scope."
        ),
        option_boundary="Exactly native options 0, 1, and 2 are visible.",
    ),
    "tgp_decision_events.0101": _analysis(
        migrated_from=_TGP_PETITION_SOURCE,
        review_summary=(
            "A movement petition reaches the played hegemon with reviewed law, "
            "examination, budget, retirement, and province/member scope shapes."
        ),
        safe_native_option_index=2,
        safe_option_number=3,
        safe_option_rationale=(
            "Native 2 refuses and clears petition variables without opening a "
            "follow-up chain or mutating the Phase-2 state machine."
        ),
        scope_boundary=(
            "Accept only enumerated five-scope direction frames or reviewed "
            "province/member variants, retaining petitioner/recipient aliases."
        ),
        option_boundary="Exactly native options 0, 1, and 2 are visible.",
    ),
    "trait_specific_ongoing.2001": _analysis(
        migrated_from=_TRAIT_SOURCE,
        review_summary=(
            "The possessed-character vision sets its lifetime flag and resolves "
            "one same-faith clergy witness before presenting three routes."
        ),
        safe_native_option_index=2,
        safe_option_number=3,
        safe_option_rationale=(
            "Native 2 only relieves stress and terminates; native 0 runs a duel "
            "and native 1 schedules a delayed witch-knowledge event."
        ),
        scope_boundary=(
            "Bind only the one typed non-player clergy witness; do not expand the "
            "record into general faith, doctrine, or witch strategy."
        ),
        option_boundary="Exactly native options 0, 1, and 2 are visible.",
    ),
    "trait_specific_ongoing.3009": _analysis(
        migrated_from=_TRAIT_SOURCE,
        review_summary=(
            "The depressed-character exhaustion event has already applied its "
            "recurrence flag and exhausted modifier before the empty prompt."
        ),
        safe_native_option_index=0,
        safe_option_number=1,
        safe_option_rationale="Native 0 is the sole empty acknowledgement.",
        scope_boundary="The reviewed frame has no saved scopes.",
        option_boundary="Exactly one authored acknowledgement, native 0, is visible.",
    ),
    "trait_specific_ongoing.3015": _analysis(
        migrated_from=_TRAIT_SOURCE,
        review_summary=(
            "The depressed-character criticism event resolves one unsympathetic "
            "critic and presents stress, opinion, or prestige consequences."
        ),
        safe_native_option_index=1,
        safe_option_number=2,
        safe_option_rationale=(
            "Native 1 only applies the reviewed opinion loss from the critic; "
            "native 0 and native 2 can add stress."
        ),
        scope_boundary="Bind exactly one typed unsympathetic critic distinct from root.",
        option_boundary="Exactly native options 0, 1, and 2 are visible.",
    ),
    "tribute_mission.1002": _analysis(
        migrated_from=_TRIBUTE_SOURCE,
        review_summary=(
            "The human-tribute receipt has reviewed concubine and eunuch branches "
            "whose mutually exclusive middle options produce different views."
        ),
        safe_native_option_index=3,
        safe_option_number=4,
        safe_option_rationale=(
            "Native 3 declines either offered character and changes no product "
            "state; the subsequent reward event remains independently contracted."
        ),
        scope_boundary=(
            "Accept only the reviewed fourteen-scope concubine or eunuch alias "
            "frame with typed reward metadata and unavailable intermediary scopes."
        ),
        option_boundary=(
            "The concubine view renders native 0/1/3 and the eunuch view renders "
            "native 0/2/3; select native 3 in either."
        ),
    ),
    "tribute_mission.1005": _analysis(
        migrated_from=_TRIBUTE_SOURCE,
        review_summary=(
            "The repeatable tribute reward decision follows human or non-human "
            "tribute routes and preserves their distinct scope shapes."
        ),
        safe_native_option_index=5,
        safe_option_number=6,
        safe_option_rationale=(
            "Native 5 grants generic legitimacy to the AI tributary without a "
            "player resource cost."
        ),
        scope_boundary=(
            "Accept only reviewed human, direct non-human, gold, or herd reward "
            "frames with exact actor/recipient aliases and typed reward metadata."
        ),
        option_boundary=(
            "The reviewed view renders native 0/1/2/3/5/6; native 4 remains hidden."
        ),
    ),
}


__all__ = ["MANAGER_VANILLA_ANALYSIS_B"]
