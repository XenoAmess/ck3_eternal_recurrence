#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the isolated Workforce #269 attribution-signature fact package.

The package never accepts attribution basis points from a public caller.  It
joins the already-consumed #267 interview ballot and #272 offer manifests only
after #274 has produced a real native appointment receipt, asks the real final
approver to sign one of three explicit lead-responsibility allocations, and
freezes an actor/evidence-bound receipt.  AI approvers use a deterministic rule
over the three sealed votes; no random or equal-share fallback exists.
"""

from __future__ import annotations

import argparse
import hashlib
from dataclasses import dataclass
from pathlib import Path
import textwrap
from typing import Final


MOD_ROOT = Path(__file__).resolve().parent.parent
BOM = b"\xef\xbb\xbf"
PREFIX: Final[str] = "zg361_workforce_attribution_fact"
NAMESPACE: Final[str] = "zg361workforceattributionfact"
WORKFORCE_PREFIX: Final[str] = "zg361_we"
PROBATION_PREFIX: Final[str] = "zg361_workforce_probation_fact"
READINESS: Final[str] = "ck3-script-static-ready-not-live"
HEADER = "# GENERATED FILE -- edit tools/gen_zg361_workforce_attribution_fact.py\n"
ALLOCATION_POLICY_VERSION: Final[int] = 1
ALLOCATION_POLICY_BASIS: Final[int] = 1  # lead-responsibility policy
SIGNATURE_MODE_PLAYER: Final[int] = 1
SIGNATURE_MODE_AI: Final[int] = 2
AI_TIE_RULE_FIRST_HIGHEST: Final[int] = 1

LANGUAGES: Final[tuple[str, ...]] = (
    "english",
    "french",
    "german",
    "japanese",
    "korean",
    "polish",
    "russian",
    "simp_chinese",
    "spanish",
)

LEGACY_EFFECT_FILENAME: Final[str] = f"{PREFIX}_effects.txt"
LEGACY_EVENT_FILENAME: Final[str] = f"{PREFIX}_events.txt"
LEGACY_EFFECT_PATH = (
    MOD_ROOT / "common" / "scripted_effects" / LEGACY_EFFECT_FILENAME
)
LEGACY_EVENT_PATH = MOD_ROOT / "events" / LEGACY_EVENT_FILENAME
EFFECT_SHARD_GLOB: Final[str] = f"{PREFIX}*_effects.txt"
EVENT_SHARD_GLOB: Final[str] = f"{PREFIX}*_events.txt"
HISTORICAL_EFFECT_COUNT: Final[int] = 7
HISTORICAL_EFFECT_BYTES: Final[int] = 96536
HISTORICAL_EFFECT_SHA256: Final[str] = (
    "f541b448b84327147caab66d30c46c2090025fd4332366bdd5e13daf5cc023a4"
)
HISTORICAL_EVENT_COUNT: Final[int] = 3
HISTORICAL_EVENT_BYTES: Final[int] = 6116
HISTORICAL_EVENT_SHA256: Final[str] = (
    "bd8215c385113f4f63a6fdf4adcc001804ae58a70ffb16b6a0f993cbaad4d60c"
)
EFFECT_TARGET_MAX: Final[int] = 10
EFFECT_HARD_MAX: Final[int] = 20
EFFECT_HARD_LIMIT_EXCEPTIONS: dict[str, tuple[str, str]] = {}


@dataclass(frozen=True)
class EffectGroup:
    filename: str
    purpose: str
    effect_names: tuple[str, ...]


@dataclass(frozen=True)
class EventGroup:
    filename: str
    purpose: str
    event_names: tuple[str, ...]


# The five seed-reachable definitions are a two-shard exact union: signature
# collection plus the independent #269 debt-cancellation path.  The remaining
# publish/ACK pair belongs to the later probation handoff and stays selectable
# as one complete purpose shard.
EFFECT_GROUPS: Final[tuple[EffectGroup, ...]] = (
    EffectGroup(
        f"{PREFIX}_signature_effects.txt",
        "arm, dispatch, resolve, and sign the attribution allocation",
        (
            f"{PREFIX}_dispatch_signature_effect",
            f"{PREFIX}_resolve_ai_signature_effect",
            f"{PREFIX}_sign_effect",
            f"{PREFIX}_begin_signature_effect",
        ),
    ),
    EffectGroup(
        f"{PREFIX}_probation_publish_effects.txt",
        "publish the signed result to probation and acknowledge its frozen tuple",
        (
            f"{PREFIX}_publish_result_effect",
            f"{PREFIX}_ack_probation_publish_effect",
        ),
    ),
    EffectGroup(
        f"{PREFIX}_m269_debt_cancel_effects.txt",
        "cancel attribution after an exact #269 route-C debt",
        (f"{PREFIX}_cancel_from_m269_debt_effect",),
    ),
)

EVENT_GROUPS: Final[tuple[EventGroup, ...]] = (
    EventGroup(
        f"{PREFIX}_signature_events.txt",
        "collect the player signature or dispatch the AI signature next frame",
        (f"{NAMESPACE}.1", f"{NAMESPACE}.2"),
    ),
    EventGroup(
        f"{PREFIX}_probation_publish_events.txt",
        "acknowledge the later probation publication on its next-frame carrier",
        (f"{NAMESPACE}.3",),
    ),
)

SEED_EFFECT_CLOSURE_NAMES: Final[tuple[str, ...]] = (
    *EFFECT_GROUPS[0].effect_names,
    *EFFECT_GROUPS[2].effect_names,
)
SEED_EVENT_CLOSURE_NAMES: Final[tuple[str, ...]] = EVENT_GROUPS[0].event_names
DEFERRED_EFFECT_NAMES: Final[tuple[str, ...]] = EFFECT_GROUPS[1].effect_names
DEFERRED_EVENT_NAMES: Final[tuple[str, ...]] = EVENT_GROUPS[1].event_names

# Each policy names the lead interviewer.  The numbers are explicit signed
# responsibility, not a hidden default or an approximation of one third.
ALLOCATION_POLICIES: Final[dict[int, tuple[int, int, int]]] = {
    1: (6000, 2000, 2000),
    2: (2000, 6000, 2000),
    3: (2000, 2000, 6000),
}


def select_ai_policy(votes: tuple[int, int, int]) -> int:
    """Choose the first highest sealed vote, matching the generated CK3 rule."""

    if len(votes) != 3 or any(vote not in (1, 2, 3) for vote in votes):
        raise ValueError("AI attribution requires exactly three bounded sealed votes")
    highest = max(votes)
    return votes.index(highest) + 1


def validate_contract() -> None:
    if tuple(ALLOCATION_POLICIES) != (1, 2, 3):
        raise ValueError("attribution policies must remain ordered by interviewer slot")
    for policy, shares in ALLOCATION_POLICIES.items():
        if len(shares) != 3 or sum(shares) != 10000:
            raise ValueError(f"policy {policy} must conserve exactly 10000 bp")
        if shares[policy - 1] != 6000 or sorted(shares) != [2000, 2000, 6000]:
            raise ValueError(f"policy {policy} must bind the named lead to 6000 bp")
    if len(LANGUAGES) != 9 or {LANGUAGES[0], LANGUAGES[7]} != {"english", "simp_chinese"}:
        raise ValueError("localization contract must keep zh/en plus seven placeholders")
    if READINESS != "ck3-script-static-ready-not-live":
        raise ValueError("an unwired fact package cannot claim live readiness")
    if (ALLOCATION_POLICY_VERSION, ALLOCATION_POLICY_BASIS) != (1, 1):
        raise ValueError("signed allocation policy identity drifted")


def clean(text: str) -> str:
    return "\n".join(line.rstrip() for line in textwrap.dedent(text).strip().splitlines()) + "\n"


def generated(text: str) -> bytes:
    return BOM + (HEADER + f"# readiness: {READINESS}\n\n" + clean(text)).encode("utf-8")


def localized(text: str) -> bytes:
    return BOM + clean(text).encode("utf-8")


def _policy_guard() -> str:
    rows: list[str] = []
    for policy, shares in ALLOCATION_POLICIES.items():
        rows.append(
            """AND = {
    $POLICY$ = @POLICY@
    $BPS_1$ = @BPS1@
    $BPS_2$ = @BPS2@
    $BPS_3$ = @BPS3@
    var:@P@_interviewer_@POLICY@ = $LEAD$
}"""
            .replace("@POLICY@", str(policy))
            .replace("@BPS1@", str(shares[0]))
            .replace("@BPS2@", str(shares[1]))
            .replace("@BPS3@", str(shares[2]))
            .replace("@P@", PREFIX)
        )
    return "\n".join(" " * 16 + line if line else line for row in rows for line in row.splitlines())


def render_effects() -> bytes:
    """Render the frozen historical aggregate for parity validation only."""

    template = r'''
    # ZhongGuo 361 Workforce #269 attribution-signature fact.
    # Public ABI 1 (current scope = candidate/subject):
    #   @P@_begin_signature_effect = {
    #       TICKET_OWNER = <AD case owner> TICKET_SUBJECT = <candidate>
    #       TICKET_CYCLE = <AD cycle> TICKET_CASE = <AD case>
    #   }
    # Public ABI 2 (current scope = hired/result subject):
    #   @P@_publish_result_effect = { OWNER = <same AD owner> }
    # Public ABI 3 (current scope = hired subject, after a #269 route-C debt):
    #   @P@_cancel_from_m269_debt_effect = { OWNER = <same AD owner> }
    # Neither public ABI accepts basis points, interviewer identities, evidence,
    # a signer, success flags, receipt IDs or hashes.

    @P@_dispatch_signature_effect = {
        save_scope_as = @P@_subject_scope
        var:@P@_interviewer_1 = { save_scope_as = @P@_interviewer_1_scope }
        var:@P@_interviewer_2 = { save_scope_as = @P@_interviewer_2_scope }
        var:@P@_interviewer_3 = { save_scope_as = @P@_interviewer_3_scope }
        var:@P@_final_approver = {
            save_scope_as = @P@_approver_scope
            if = {
                limit = { is_ai = yes }
                scope:@P@_subject_scope = {
                    @P@_resolve_ai_signature_effect = { SIGNER = scope:@P@_approver_scope }
                }
            }
            else = { trigger_event = { id = @N@.1 } }
        }
    }

    # AI chooses the first highest of the three real sealed votes.  Slot order
    # is the documented deterministic tie-break; no random list or fallback
    # allocation is consulted.
    @P@_resolve_ai_signature_effect = {
        if = {
            limit = {
                has_variable = @P@_signature_pending
                var:@P@_signature_pending = 1
                var:@P@_final_approver = $SIGNER$
                $SIGNER$ = { is_ai = yes zg361_is_celestial_liege_trigger = yes }
                var:@P@_vote_1 >= var:@P@_vote_2
                var:@P@_vote_1 >= var:@P@_vote_3
            }
            @P@_sign_effect = {
                SIGNER = $SIGNER$ POLICY = 1 LEAD = var:@P@_interviewer_1
                BPS_1 = 6000 BPS_2 = 2000 BPS_3 = 2000
                SIGNATURE_MODE = 2 TIE_RULE = 1
            }
        }
        else_if = {
            limit = {
                has_variable = @P@_signature_pending
                var:@P@_signature_pending = 1
                var:@P@_final_approver = $SIGNER$
                $SIGNER$ = { is_ai = yes zg361_is_celestial_liege_trigger = yes }
                var:@P@_vote_2 >= var:@P@_vote_1
                var:@P@_vote_2 >= var:@P@_vote_3
            }
            @P@_sign_effect = {
                SIGNER = $SIGNER$ POLICY = 2 LEAD = var:@P@_interviewer_2
                BPS_1 = 2000 BPS_2 = 6000 BPS_3 = 2000
                SIGNATURE_MODE = 2 TIE_RULE = 1
            }
        }
        else_if = {
            limit = {
                has_variable = @P@_signature_pending
                var:@P@_signature_pending = 1
                var:@P@_final_approver = $SIGNER$
                $SIGNER$ = { is_ai = yes zg361_is_celestial_liege_trigger = yes }
                var:@P@_vote_3 > var:@P@_vote_1
                var:@P@_vote_3 > var:@P@_vote_2
            }
            @P@_sign_effect = {
                SIGNER = $SIGNER$ POLICY = 3 LEAD = var:@P@_interviewer_3
                BPS_1 = 2000 BPS_2 = 2000 BPS_3 = 6000
                SIGNATURE_MODE = 2 TIE_RULE = 1
            }
        }
        else = {
            set_variable = { name = @P@_status value = 4 }
            set_variable = { name = @P@_red_code value = 26913 }
        }
    }

    # Private commit primitive.  Values are accepted only when they match one
    # of the three event-owned policy rows below.  The complete #267, #272 and
    # native #274 source tuple is rechecked before any receipt write.
    @P@_sign_effect = {
        remove_variable = @P@_status
        remove_variable = @P@_red_code
        save_temporary_scope_value_as = {
            name = @P@_submitted_total_bps
            value = { value = $BPS_1$ add = $BPS_2$ add = $BPS_3$ }
        }
        if = {
            limit = {
                has_variable = @P@_signature_pending
                var:@P@_signature_pending = 1
                trigger_if = { limit = { has_variable = @P@_signature_committed } var:@P@_signature_committed = 0 }
                trigger_else = { always = yes }
                var:@P@_state = 1
                var:@P@_subject = this
                has_variable = @P@_m267_operation_choice
                has_variable = @P@_m272_operation_choice
                has_variable = @P@_m274_operation_choice
                has_variable = @P@_m272_due_cycle
                has_variable = @P@_position_type_id
                has_variable = @P@_probation_due_cycle
            var:@P@_final_approver = $SIGNER$
            $SIGNER$ = { zg361_is_celestial_liege_trigger = yes }
            scope:@P@_submitted_total_bps = 10000
            OR = {
                AND = { $SIGNATURE_MODE$ = 1 $TIE_RULE$ = 0 $SIGNER$ = { is_ai = no } }
                AND = { $SIGNATURE_MODE$ = 2 $TIE_RULE$ = 1 $SIGNER$ = { is_ai = yes } }
            }
            OR = {
@POLICY_GUARD@
                }
                has_variable = @W@_m267_business_object_created
                has_variable = @W@_m267_object_type_code
                has_variable = @W@_m267_object_interview_ballot
                has_variable = @W@_m267_object_owner
                has_variable = @W@_m267_object_subject
                has_variable = @W@_m267_object_cycle
                has_variable = @W@_m267_object_case
                has_variable = @W@_m267_object_state
                has_variable = @W@_m267_object_id
                has_variable = @W@_m267_object_consumed
                has_variable = @W@_m267_consumer_contract
                has_variable = @W@_m267_resource_interview
                has_variable = @W@_m267_resource_evidence
                has_variable = @W@_m267_consumer_seal_interview_votes_267
                has_variable = @W@_m267_choice
                has_variable = @W@_m267_receipt_owner
                has_variable = @W@_m267_receipt_subject
                has_variable = @W@_m267_receipt_cycle
                has_variable = @W@_m267_receipt_case
                has_variable = @W@_m267_receipt_state
                has_variable = @W@_m267_receipt_choice
                var:@W@_m267_business_object_created = 1
                var:@W@_m267_object_type_code = 267
                var:@W@_m267_object_interview_ballot = 1
                var:@W@_m267_object_owner = var:@P@_owner
                var:@W@_m267_object_subject = this
                var:@W@_m267_object_cycle = var:@P@_cycle
                var:@W@_m267_object_case = var:@P@_case
                var:@W@_m267_object_state = 1
                var:@W@_m267_object_id = var:@P@_m267_object_id
                var:@W@_m267_object_consumed = 1
                var:@W@_m267_consumer_contract = 267
                var:@W@_m267_resource_interview = 1
                var:@W@_m267_resource_evidence = 1
                var:@W@_m267_consumer_seal_interview_votes_267 = 1
                OR = { var:@P@_m267_operation_choice = 1 var:@P@_m267_operation_choice = 2 }
                var:@W@_m267_choice = var:@P@_m267_operation_choice
                var:@W@_m267_receipt_owner = var:@P@_owner
                var:@W@_m267_receipt_subject = this
                var:@W@_m267_receipt_cycle = var:@P@_cycle
                var:@W@_m267_receipt_case = var:@P@_case
                var:@W@_m267_receipt_state = 1
                var:@W@_m267_receipt_choice = var:@P@_m267_operation_choice
                has_variable = @W@_m267_raw_votes_frozen
                has_variable = @W@_m267_candidate_frozen
                has_variable = @W@_m267_interviewer_1
                has_variable = @W@_m267_interviewer_2
                has_variable = @W@_m267_interviewer_3
                has_variable = @W@_m267_vote_1
                has_variable = @W@_m267_vote_2
                has_variable = @W@_m267_vote_3
                has_variable = @W@_m267_vote_evidence_1
                has_variable = @W@_m267_vote_evidence_2
                has_variable = @W@_m267_vote_evidence_3
                var:@W@_m267_raw_votes_frozen = 1
                var:@W@_m267_candidate_frozen = this
                var:@W@_m267_interviewer_1 = var:@P@_interviewer_1
                var:@W@_m267_interviewer_2 = var:@P@_interviewer_2
                var:@W@_m267_interviewer_3 = var:@P@_interviewer_3
                var:@W@_m267_vote_1 = var:@P@_vote_1
                var:@W@_m267_vote_2 = var:@P@_vote_2
                var:@W@_m267_vote_3 = var:@P@_vote_3
                var:@W@_m267_vote_evidence_1 = var:@P@_evidence_1
                var:@W@_m267_vote_evidence_2 = var:@P@_evidence_2
                var:@W@_m267_vote_evidence_3 = var:@P@_evidence_3
                has_variable = @W@_m272_business_object_created
                has_variable = @W@_m272_object_type_code
                has_variable = @W@_m272_object_offer
                has_variable = @W@_m272_object_owner
                has_variable = @W@_m272_object_subject
                has_variable = @W@_m272_object_cycle
                has_variable = @W@_m272_object_case
                has_variable = @W@_m272_object_state
                has_variable = @W@_m272_object_id
                has_variable = @W@_m272_object_consumed
                has_variable = @W@_m272_consumer_contract
                has_variable = @W@_m272_resource_gold
                has_variable = @W@_m272_resource_offer
                has_variable = @W@_m272_resource_promotion
                has_variable = @W@_m272_object_due_cycle
                has_variable = @W@_m272_consumer_issue_offer_272
                has_variable = @W@_m272_choice
                has_variable = @W@_m272_receipt_owner
                has_variable = @W@_m272_receipt_subject
                has_variable = @W@_m272_receipt_cycle
                has_variable = @W@_m272_receipt_case
                has_variable = @W@_m272_receipt_state
                has_variable = @W@_m272_receipt_choice
                var:@W@_m272_business_object_created = 1
                var:@W@_m272_object_type_code = 272
                var:@W@_m272_object_offer = 1
                var:@W@_m272_object_owner = var:@P@_owner
                var:@W@_m272_object_subject = this
                var:@W@_m272_object_cycle = var:@P@_cycle
                var:@W@_m272_object_case = var:@P@_case
                var:@W@_m272_object_state = 3
                var:@W@_m272_object_id = var:@P@_m272_object_id
                var:@W@_m272_object_consumed = 1
                var:@W@_m272_consumer_contract = 272
                var:@W@_m272_resource_gold = 1
                var:@W@_m272_resource_offer = 1
                var:@W@_m272_resource_promotion = 1
                var:@W@_m272_object_due_cycle = var:@P@_m272_due_cycle
                var:@W@_m272_consumer_issue_offer_272 = 1
                OR = { var:@P@_m272_operation_choice = 1 var:@P@_m272_operation_choice = 2 }
                var:@W@_m272_choice = var:@P@_m272_operation_choice
                var:@W@_m272_receipt_owner = var:@P@_owner
                var:@W@_m272_receipt_subject = this
                var:@W@_m272_receipt_cycle = var:@P@_cycle
                var:@W@_m272_receipt_case = var:@P@_case
                var:@W@_m272_receipt_state = 3
                var:@W@_m272_receipt_choice = var:@P@_m272_operation_choice
                has_variable = @W@_m272_offer_candidate
                has_variable = @W@_m272_offer_approver
                has_variable = @W@_m272_offer_terms_frozen
                var:@W@_m272_offer_candidate = this
                var:@W@_m272_offer_approver = $SIGNER$
                var:@W@_m272_offer_terms_frozen = 1
                has_variable = @W@_m274_business_object_created
                has_variable = @W@_m274_object_type_code
                has_variable = @W@_m274_object_counteroffer
                has_variable = @W@_m274_object_owner
                has_variable = @W@_m274_object_subject
                has_variable = @W@_m274_object_cycle
                has_variable = @W@_m274_object_case
                has_variable = @W@_m274_object_state
                has_variable = @W@_m274_object_id
                has_variable = @W@_m274_object_consumed
                has_variable = @W@_m274_consumer_contract
                has_variable = @W@_m274_resource_gold
                has_variable = @W@_m274_resource_offer
                has_variable = @W@_m274_resource_formal_hc
                has_variable = @W@_m274_consumer_resolve_counteroffer_274
                has_variable = @W@_m274_choice
                has_variable = @W@_m274_receipt_owner
                has_variable = @W@_m274_receipt_subject
                has_variable = @W@_m274_receipt_cycle
                has_variable = @W@_m274_receipt_case
                has_variable = @W@_m274_receipt_state
                has_variable = @W@_m274_receipt_choice
                has_variable = @W@_m274_hired
                has_variable = @W@_m274_hire_case
                has_variable = @W@_m274_appointed_character
                has_variable = @W@_m274_native_appointment_confirmed
                has_variable = @W@_m274_position_receipt_id
                has_variable = @W@_m274_position_receipt_hash
                has_variable = @W@_m274_position_type_id
                has_variable = @W@_m274_probation_due_cycle
                var:@W@_m274_business_object_created = 1
                var:@W@_m274_object_type_code = 274
                var:@W@_m274_object_counteroffer = 1
                var:@W@_m274_object_owner = var:@P@_owner
                var:@W@_m274_object_subject = this
                var:@W@_m274_object_cycle = var:@P@_cycle
                var:@W@_m274_object_case = var:@P@_case
                var:@W@_m274_object_state = 4
                var:@W@_m274_object_id = var:@P@_m274_object_id
                var:@W@_m274_object_consumed = 1
                var:@W@_m274_consumer_contract = 274
                var:@W@_m274_resource_gold = 1
                var:@W@_m274_resource_offer = 1
                var:@W@_m274_resource_formal_hc = 1
                var:@W@_m274_consumer_resolve_counteroffer_274 = 1
                var:@P@_m274_operation_choice = 1
                var:@W@_m274_choice = var:@P@_m274_operation_choice
                var:@W@_m274_receipt_owner = var:@P@_owner
                var:@W@_m274_receipt_subject = this
                var:@W@_m274_receipt_cycle = var:@P@_cycle
                var:@W@_m274_receipt_case = var:@P@_case
                var:@W@_m274_receipt_state = 4
                var:@W@_m274_receipt_choice = var:@P@_m274_operation_choice
                var:@W@_m274_hired = 1
                var:@W@_m274_hire_case = var:@P@_case
                var:@W@_m274_appointed_character = this
                var:@W@_m274_native_appointment_confirmed = 1
                var:@W@_m274_position_receipt_id = var:@P@_appointment_receipt_id
                var:@W@_m274_position_receipt_hash = var:@P@_appointment_receipt_hash
                var:@W@_m274_position_type_id = var:@P@_position_type_id
                var:@W@_m274_probation_due_cycle = var:@P@_probation_due_cycle
            }
            set_variable = { name = @P@_signature_policy value = $POLICY$ }
            set_variable = { name = @P@_signature_policy_version value = 1 }
            set_variable = { name = @P@_signature_policy_basis value = 1 }
            set_variable = { name = @P@_signature_mode value = $SIGNATURE_MODE$ }
            set_variable = { name = @P@_signature_tie_rule value = $TIE_RULE$ }
            set_variable = { name = @P@_signature_actor value = $SIGNER$ }
            set_variable = { name = @P@_lead_interviewer value = $LEAD$ }
            set_variable = { name = @P@_attribution_bps_1 value = $BPS_1$ }
            set_variable = { name = @P@_attribution_bps_2 value = $BPS_2$ }
            set_variable = { name = @P@_attribution_bps_3 value = $BPS_3$ }
            set_variable = { name = @P@_attribution_total_bps value = scope:@P@_submitted_total_bps }
            set_variable = { name = @P@_receipt_owner value = var:@P@_owner }
            set_variable = { name = @P@_receipt_subject value = this }
            set_variable = { name = @P@_receipt_cycle value = var:@P@_cycle }
            set_variable = { name = @P@_receipt_case value = var:@P@_case }
            set_variable = { name = @P@_receipt_signer value = $SIGNER$ }
            set_variable = { name = @P@_receipt_policy_version value = 1 }
            set_variable = { name = @P@_receipt_policy_basis value = 1 }
            set_variable = { name = @P@_receipt_signature_mode value = $SIGNATURE_MODE$ }
            set_variable = { name = @P@_receipt_tie_rule value = $TIE_RULE$ }
            set_variable = { name = @P@_receipt_interviewer_1 value = var:@P@_interviewer_1 }
            set_variable = { name = @P@_receipt_interviewer_2 value = var:@P@_interviewer_2 }
            set_variable = { name = @P@_receipt_interviewer_3 value = var:@P@_interviewer_3 }
            set_variable = { name = @P@_receipt_evidence_1 value = var:@P@_evidence_1 }
            set_variable = { name = @P@_receipt_evidence_2 value = var:@P@_evidence_2 }
            set_variable = { name = @P@_receipt_evidence_3 value = var:@P@_evidence_3 }
            set_variable = { name = @P@_receipt_m267_object_id value = var:@P@_m267_object_id }
            set_variable = { name = @P@_receipt_m272_object_id value = var:@P@_m272_object_id }
            set_variable = { name = @P@_receipt_m274_object_id value = var:@P@_m274_object_id }
            set_variable = { name = @P@_receipt_m267_operation_choice value = var:@P@_m267_operation_choice }
            set_variable = { name = @P@_receipt_m272_operation_choice value = var:@P@_m272_operation_choice }
            set_variable = { name = @P@_receipt_m274_operation_choice value = var:@P@_m274_operation_choice }
            set_variable = { name = @P@_receipt_m272_due_cycle value = var:@P@_m272_due_cycle }
            set_variable = { name = @P@_receipt_position_type_id value = var:@P@_position_type_id }
            set_variable = { name = @P@_receipt_probation_due_cycle value = var:@P@_probation_due_cycle }
            set_variable = { name = @P@_receipt_appointment_id value = var:@P@_appointment_receipt_id }
            set_variable = { name = @P@_receipt_appointment_hash value = var:@P@_appointment_receipt_hash }
            set_variable = {
                name = @P@_receipt_id
                value = { value = var:@P@_case multiply = 1000 add = 269 }
            }
            set_variable = {
                name = @P@_receipt_hash
                value = {
                    value = var:@P@_evidence_1 multiply = 1000000
                    add = { value = var:@P@_evidence_2 multiply = 10000 }
                    add = { value = var:@P@_evidence_3 multiply = 100 }
                    add = $POLICY$
                }
            }
            set_variable = { name = @P@_consumed value = 0 }
            set_variable = { name = @P@_signature_pending value = 0 }
            set_variable = { name = @P@_state value = 2 }
            set_variable = { name = @P@_status value = 1 }
            set_variable = { name = @P@_signature_committed value = 1 } # commit marker is last
            debug_log = "ZG361WAF: final approver signed a conserved three-interviewer attribution receipt"
        }
        else_if = {
            limit = {
                has_variable = @P@_signature_committed
                has_variable = @P@_state
                has_variable = @P@_consumed
                has_variable = @P@_owner
                has_variable = @P@_subject
                has_variable = @P@_signature_actor
                has_variable = @P@_final_approver
                has_variable = @P@_receipt_signer
                has_variable = @P@_interviewer_1
                has_variable = @P@_interviewer_2
                has_variable = @P@_interviewer_3
                has_variable = @P@_evidence_1
                has_variable = @P@_evidence_2
                has_variable = @P@_evidence_3
                has_variable = @P@_attribution_bps_1
                has_variable = @P@_attribution_bps_2
                has_variable = @P@_attribution_bps_3
                has_variable = @P@_attribution_total_bps
                has_variable = @P@_receipt_m267_object_id
                has_variable = @P@_receipt_m272_object_id
                has_variable = @P@_receipt_m274_object_id
                has_variable = @P@_receipt_m267_operation_choice
                has_variable = @P@_receipt_m272_operation_choice
                has_variable = @P@_receipt_m274_operation_choice
                has_variable = @P@_receipt_appointment_id
                has_variable = @P@_receipt_appointment_hash
                var:@P@_signature_committed = 1
                var:@P@_state = 2
                var:@P@_subject = this
                var:@P@_signature_actor = $SIGNER$
                var:@P@_signature_policy = $POLICY$
                var:@P@_signature_policy_version = 1
                var:@P@_signature_policy_basis = 1
                var:@P@_signature_mode = $SIGNATURE_MODE$
                var:@P@_signature_tie_rule = $TIE_RULE$
                var:@P@_lead_interviewer = $LEAD$
                var:@P@_attribution_bps_1 = $BPS_1$
                var:@P@_attribution_bps_2 = $BPS_2$
                var:@P@_attribution_bps_3 = $BPS_3$
                var:@P@_attribution_total_bps = 10000
                var:@P@_receipt_m267_object_id = var:@P@_m267_object_id
                var:@P@_receipt_m272_object_id = var:@P@_m272_object_id
                var:@P@_receipt_m274_object_id = var:@P@_m274_object_id
                var:@P@_receipt_m267_operation_choice = var:@P@_m267_operation_choice
                var:@P@_receipt_m272_operation_choice = var:@P@_m272_operation_choice
                var:@P@_receipt_m274_operation_choice = var:@P@_m274_operation_choice
                var:@P@_receipt_appointment_id = var:@P@_appointment_receipt_id
                var:@P@_receipt_appointment_hash = var:@P@_appointment_receipt_hash
            }
            set_variable = { name = @P@_status value = 2 }
        }
        else = {
            set_variable = { name = @P@_status value = 4 }
            set_variable = { name = @P@_red_code value = 26912 }
            debug_log = "ZG361WAF RED 26912: attribution signature lacked exact actor/evidence/manifest provenance"
        }
    }

    @P@_begin_signature_effect = {
        remove_variable = @P@_status
        remove_variable = @P@_red_code
        save_scope_as = @P@_begin_subject_scope
        $TICKET_OWNER$ = { save_scope_as = @P@_begin_owner_scope }
        save_temporary_scope_value_as = {
            name = @P@_expected_m267_object_id
            value = { value = $TICKET_CASE$ multiply = 1000 add = 267 }
        }
        save_temporary_scope_value_as = {
            name = @P@_expected_m272_object_id
            value = { value = $TICKET_CASE$ multiply = 1000 add = 272 }
        }
        save_temporary_scope_value_as = {
            name = @P@_expected_m274_object_id
            value = { value = $TICKET_CASE$ multiply = 1000 add = 274 }
        }
        save_temporary_scope_value_as = {
            name = @P@_expected_due_cycle
            value = { value = $TICKET_CYCLE$ add = 1 }
        }
        if = {
            limit = {
                has_variable = @P@_signature_committed
                var:@P@_signature_committed = 1
                var:@P@_state = 2
                var:@P@_owner = $TICKET_OWNER$
                var:@P@_subject = $TICKET_SUBJECT$
                var:@P@_cycle = $TICKET_CYCLE$
                var:@P@_case = $TICKET_CASE$
                var:@P@_receipt_owner = $TICKET_OWNER$
                var:@P@_receipt_subject = $TICKET_SUBJECT$
                var:@P@_receipt_cycle = $TICKET_CYCLE$
                var:@P@_receipt_case = $TICKET_CASE$
                var:@P@_receipt_signer = var:@P@_final_approver
                var:@P@_receipt_interviewer_1 = var:@P@_interviewer_1
                var:@P@_receipt_interviewer_2 = var:@P@_interviewer_2
                var:@P@_receipt_interviewer_3 = var:@P@_interviewer_3
                var:@P@_receipt_evidence_1 = var:@P@_evidence_1
                var:@P@_receipt_evidence_2 = var:@P@_evidence_2
                var:@P@_receipt_evidence_3 = var:@P@_evidence_3
                has_variable = @P@_receipt_m267_object_id
                has_variable = @P@_receipt_m272_object_id
                has_variable = @P@_receipt_m274_object_id
                has_variable = @P@_receipt_m267_operation_choice
                has_variable = @P@_receipt_m272_operation_choice
                has_variable = @P@_receipt_m274_operation_choice
                has_variable = @P@_receipt_id
                has_variable = @P@_receipt_hash
                var:@P@_receipt_m267_object_id = var:@P@_m267_object_id
                var:@P@_receipt_m272_object_id = var:@P@_m272_object_id
                var:@P@_receipt_m274_object_id = var:@P@_m274_object_id
                var:@P@_receipt_m267_operation_choice = var:@P@_m267_operation_choice
                var:@P@_receipt_m272_operation_choice = var:@P@_m272_operation_choice
                var:@P@_receipt_m274_operation_choice = var:@P@_m274_operation_choice
                var:@P@_receipt_appointment_id = var:@P@_appointment_receipt_id
                var:@P@_receipt_appointment_hash = var:@P@_appointment_receipt_hash
                var:@P@_receipt_id > 0
                var:@P@_receipt_hash > 0
                var:@P@_signature_policy_version = 1
                var:@P@_signature_policy_basis = 1
                var:@P@_receipt_policy_version = 1
                var:@P@_receipt_policy_basis = 1
                var:@P@_receipt_signature_mode = var:@P@_signature_mode
                var:@P@_receipt_tie_rule = var:@P@_signature_tie_rule
                var:@P@_attribution_total_bps = 10000
            }
            set_variable = { name = @P@_status value = 2 }
        }
        else_if = {
            limit = {
                has_variable = @P@_signature_pending
                var:@P@_signature_pending = 1
                trigger_if = { limit = { has_variable = @P@_signature_committed } var:@P@_signature_committed = 0 }
                trigger_else = { always = yes }
                var:@P@_state = 1
                var:@P@_owner = $TICKET_OWNER$
                var:@P@_subject = $TICKET_SUBJECT$
                var:@P@_cycle = $TICKET_CYCLE$
                var:@P@_case = $TICKET_CASE$
            }
            set_variable = { name = @P@_status value = 5 }
        }
        else_if = {
            limit = {
                zg361_case_kernel_full_guard_trigger = {
                    OWNER_VAR = zg361_case_ad_owner SUBJECT_VAR = zg361_case_ad_subject
                    CYCLE_VAR = zg361_case_ad_cycle_serial CASE_VAR = zg361_case_ad_case_serial
                    STATE_VAR = zg361_case_ad_state ACTIVE_VAR = zg361_case_ad_active
                    EXPECTED_OWNER = $TICKET_OWNER$ EXPECTED_SUBJECT = $TICKET_SUBJECT$
                    EXPECTED_CYCLE = $TICKET_CYCLE$ EXPECTED_CASE = $TICKET_CASE$ EXPECTED_STATE = 4
                }
                this = $TICKET_SUBJECT$
                $TICKET_OWNER$ = { zg361_is_celestial_liege_trigger = yes }
                $TICKET_SUBJECT$ = { is_alive = yes }
                trigger_if = { limit = { has_variable = @P@_signature_pending } var:@P@_signature_pending = 0 }
                trigger_else = { always = yes }
                trigger_if = { limit = { has_variable = @P@_signature_committed } var:@P@_signature_committed = 0 }
                trigger_else = { always = yes }
                has_variable = @W@_m267_business_object_created
                has_variable = @W@_m267_object_type_code
                has_variable = @W@_m267_object_interview_ballot
                has_variable = @W@_m267_object_owner
                has_variable = @W@_m267_object_subject
                has_variable = @W@_m267_object_cycle
                has_variable = @W@_m267_object_case
                has_variable = @W@_m267_object_state
                has_variable = @W@_m267_object_id
                has_variable = @W@_m267_object_consumed
                has_variable = @W@_m267_consumer_contract
                has_variable = @W@_m267_resource_interview
                has_variable = @W@_m267_resource_evidence
                has_variable = @W@_m267_consumer_seal_interview_votes_267
                has_variable = @W@_m267_choice
                has_variable = @W@_m267_receipt_owner
                has_variable = @W@_m267_receipt_subject
                has_variable = @W@_m267_receipt_cycle
                has_variable = @W@_m267_receipt_case
                has_variable = @W@_m267_receipt_state
                has_variable = @W@_m267_receipt_choice
                var:@W@_m267_business_object_created = 1
                var:@W@_m267_object_type_code = 267
                var:@W@_m267_object_interview_ballot = 1
                var:@W@_m267_object_owner = $TICKET_OWNER$
                var:@W@_m267_object_subject = $TICKET_SUBJECT$
                var:@W@_m267_object_cycle = $TICKET_CYCLE$
                var:@W@_m267_object_case = $TICKET_CASE$
                var:@W@_m267_object_state = 1
                var:@W@_m267_object_id = scope:@P@_expected_m267_object_id
                var:@W@_m267_object_consumed = 1
                var:@W@_m267_consumer_contract = 267
                var:@W@_m267_resource_interview = 1
                var:@W@_m267_resource_evidence = 1
                var:@W@_m267_consumer_seal_interview_votes_267 = 1
                OR = { var:@W@_m267_choice = 1 var:@W@_m267_choice = 2 }
                var:@W@_m267_receipt_owner = $TICKET_OWNER$
                var:@W@_m267_receipt_subject = $TICKET_SUBJECT$
                var:@W@_m267_receipt_cycle = $TICKET_CYCLE$
                var:@W@_m267_receipt_case = $TICKET_CASE$
                var:@W@_m267_receipt_state = 1
                var:@W@_m267_receipt_choice = var:@W@_m267_choice
                has_variable = @W@_m267_raw_votes_frozen
                has_variable = @W@_m267_candidate_frozen
                has_variable = @W@_m267_vote_count
                has_variable = @W@_m267_evidence_count
                var:@W@_m267_raw_votes_frozen = 1
                var:@W@_m267_candidate_frozen = $TICKET_SUBJECT$
                var:@W@_m267_vote_count = 3
                var:@W@_m267_evidence_count = 3
                has_variable = @W@_m267_interviewer_1
                has_variable = @W@_m267_interviewer_2
                has_variable = @W@_m267_interviewer_3
                has_variable = @W@_m267_vote_1
                has_variable = @W@_m267_vote_2
                has_variable = @W@_m267_vote_3
                has_variable = @W@_m267_vote_evidence_1
                has_variable = @W@_m267_vote_evidence_2
                has_variable = @W@_m267_vote_evidence_3
                var:@W@_m267_interviewer_1 = { zg361_is_celestial_liege_trigger = yes NOT = { this = scope:@P@_begin_subject_scope } }
                var:@W@_m267_interviewer_2 = { zg361_is_celestial_liege_trigger = yes NOT = { this = scope:@P@_begin_subject_scope } }
                var:@W@_m267_interviewer_3 = { zg361_is_celestial_liege_trigger = yes NOT = { this = scope:@P@_begin_subject_scope } }
                NOT = { var:@W@_m267_interviewer_1 = var:@W@_m267_interviewer_2 }
                NOT = { var:@W@_m267_interviewer_1 = var:@W@_m267_interviewer_3 }
                NOT = { var:@W@_m267_interviewer_2 = var:@W@_m267_interviewer_3 }
                var:@W@_m267_vote_1 >= 1
                var:@W@_m267_vote_1 <= 3
                var:@W@_m267_vote_2 >= 1
                var:@W@_m267_vote_2 <= 3
                var:@W@_m267_vote_3 >= 1
                var:@W@_m267_vote_3 <= 3
                var:@W@_m267_vote_evidence_1 > 0
                var:@W@_m267_vote_evidence_2 > 0
                var:@W@_m267_vote_evidence_3 > 0
                NOT = { var:@W@_m267_vote_evidence_1 = var:@W@_m267_vote_evidence_2 }
                NOT = { var:@W@_m267_vote_evidence_1 = var:@W@_m267_vote_evidence_3 }
                NOT = { var:@W@_m267_vote_evidence_2 = var:@W@_m267_vote_evidence_3 }
                has_variable = @W@_m272_business_object_created
                has_variable = @W@_m272_object_type_code
                has_variable = @W@_m272_object_offer
                has_variable = @W@_m272_object_owner
                has_variable = @W@_m272_object_subject
                has_variable = @W@_m272_object_cycle
                has_variable = @W@_m272_object_case
                has_variable = @W@_m272_object_state
                has_variable = @W@_m272_object_id
                has_variable = @W@_m272_object_consumed
                has_variable = @W@_m272_consumer_contract
                has_variable = @W@_m272_resource_gold
                has_variable = @W@_m272_resource_offer
                has_variable = @W@_m272_resource_promotion
                has_variable = @W@_m272_object_due_cycle
                has_variable = @W@_m272_consumer_issue_offer_272
                has_variable = @W@_m272_choice
                has_variable = @W@_m272_receipt_owner
                has_variable = @W@_m272_receipt_subject
                has_variable = @W@_m272_receipt_cycle
                has_variable = @W@_m272_receipt_case
                has_variable = @W@_m272_receipt_state
                has_variable = @W@_m272_receipt_choice
                var:@W@_m272_business_object_created = 1
                var:@W@_m272_object_type_code = 272
                var:@W@_m272_object_offer = 1
                var:@W@_m272_object_owner = $TICKET_OWNER$
                var:@W@_m272_object_subject = $TICKET_SUBJECT$
                var:@W@_m272_object_cycle = $TICKET_CYCLE$
                var:@W@_m272_object_case = $TICKET_CASE$
                var:@W@_m272_object_state = 3
                var:@W@_m272_object_id = scope:@P@_expected_m272_object_id
                var:@W@_m272_object_consumed = 1
                var:@W@_m272_consumer_contract = 272
                var:@W@_m272_resource_gold = 1
                var:@W@_m272_resource_offer = 1
                var:@W@_m272_resource_promotion = 1
                var:@W@_m272_object_due_cycle = scope:@P@_expected_due_cycle
                var:@W@_m272_consumer_issue_offer_272 = 1
                OR = { var:@W@_m272_choice = 1 var:@W@_m272_choice = 2 }
                var:@W@_m272_receipt_owner = $TICKET_OWNER$
                var:@W@_m272_receipt_subject = $TICKET_SUBJECT$
                var:@W@_m272_receipt_cycle = $TICKET_CYCLE$
                var:@W@_m272_receipt_case = $TICKET_CASE$
                var:@W@_m272_receipt_state = 3
                var:@W@_m272_receipt_choice = var:@W@_m272_choice
                has_variable = @W@_m272_offer_candidate
                has_variable = @W@_m272_offer_approver
                has_variable = @W@_m272_offer_terms_frozen
                var:@W@_m272_offer_candidate = $TICKET_SUBJECT$
                var:@W@_m272_offer_approver = { zg361_is_celestial_liege_trigger = yes }
                var:@W@_m272_offer_approver = $TICKET_OWNER$
                var:@W@_m272_offer_terms_frozen = 1
                has_variable = @W@_m274_business_object_created
                has_variable = @W@_m274_object_type_code
                has_variable = @W@_m274_object_counteroffer
                has_variable = @W@_m274_object_owner
                has_variable = @W@_m274_object_subject
                has_variable = @W@_m274_object_cycle
                has_variable = @W@_m274_object_case
                has_variable = @W@_m274_object_state
                has_variable = @W@_m274_object_id
                has_variable = @W@_m274_object_consumed
                has_variable = @W@_m274_consumer_contract
                has_variable = @W@_m274_resource_gold
                has_variable = @W@_m274_resource_offer
                has_variable = @W@_m274_resource_formal_hc
                has_variable = @W@_m274_consumer_resolve_counteroffer_274
                has_variable = @W@_m274_choice
                has_variable = @W@_m274_receipt_owner
                has_variable = @W@_m274_receipt_subject
                has_variable = @W@_m274_receipt_cycle
                has_variable = @W@_m274_receipt_case
                has_variable = @W@_m274_receipt_state
                has_variable = @W@_m274_receipt_choice
                has_variable = @W@_m274_hired
                has_variable = @W@_m274_hire_case
                has_variable = @W@_m274_appointed_character
                has_variable = @W@_m274_native_appointment_confirmed
                has_variable = @W@_m274_position_receipt_id
                has_variable = @W@_m274_position_receipt_hash
                has_variable = @W@_m274_position_type_id
                has_variable = @W@_m274_probation_due_cycle
                var:@W@_m274_business_object_created = 1
                var:@W@_m274_object_type_code = 274
                var:@W@_m274_object_counteroffer = 1
                var:@W@_m274_object_owner = $TICKET_OWNER$
                var:@W@_m274_object_subject = $TICKET_SUBJECT$
                var:@W@_m274_object_cycle = $TICKET_CYCLE$
                var:@W@_m274_object_case = $TICKET_CASE$
                var:@W@_m274_object_state = 4
                var:@W@_m274_object_id = scope:@P@_expected_m274_object_id
                var:@W@_m274_object_consumed = 1
                var:@W@_m274_consumer_contract = 274
                var:@W@_m274_resource_gold = 1
                var:@W@_m274_resource_offer = 1
                var:@W@_m274_resource_formal_hc = 1
                var:@W@_m274_consumer_resolve_counteroffer_274 = 1
                var:@W@_m274_choice = 1
                var:@W@_m274_receipt_owner = $TICKET_OWNER$
                var:@W@_m274_receipt_subject = $TICKET_SUBJECT$
                var:@W@_m274_receipt_cycle = $TICKET_CYCLE$
                var:@W@_m274_receipt_case = $TICKET_CASE$
                var:@W@_m274_receipt_state = 4
                var:@W@_m274_receipt_choice = 1
                var:@W@_m274_hired = 1
                var:@W@_m274_hire_case = $TICKET_CASE$
                var:@W@_m274_appointed_character = $TICKET_SUBJECT$
                var:@W@_m274_native_appointment_confirmed = 1
                var:@W@_m274_position_receipt_id > 0
                var:@W@_m274_position_receipt_hash > 0
                var:@W@_m274_position_type_id > 0
                var:@W@_m274_probation_due_cycle = scope:@P@_expected_due_cycle
            }
            set_variable = { name = @P@_owner value = $TICKET_OWNER$ }
            set_variable = { name = @P@_subject value = $TICKET_SUBJECT$ }
            set_variable = { name = @P@_cycle value = $TICKET_CYCLE$ }
            set_variable = { name = @P@_case value = $TICKET_CASE$ }
            set_variable = { name = @P@_m267_object_id value = var:@W@_m267_object_id }
            set_variable = { name = @P@_m272_object_id value = var:@W@_m272_object_id }
            set_variable = { name = @P@_m274_object_id value = var:@W@_m274_object_id }
            set_variable = { name = @P@_m267_operation_choice value = var:@W@_m267_choice }
            set_variable = { name = @P@_m272_operation_choice value = var:@W@_m272_choice }
            set_variable = { name = @P@_m274_operation_choice value = var:@W@_m274_choice }
            set_variable = { name = @P@_m272_due_cycle value = var:@W@_m272_object_due_cycle }
            set_variable = { name = @P@_position_type_id value = var:@W@_m274_position_type_id }
            set_variable = { name = @P@_probation_due_cycle value = var:@W@_m274_probation_due_cycle }
            set_variable = { name = @P@_interviewer_1 value = var:@W@_m267_interviewer_1 }
            set_variable = { name = @P@_interviewer_2 value = var:@W@_m267_interviewer_2 }
            set_variable = { name = @P@_interviewer_3 value = var:@W@_m267_interviewer_3 }
            set_variable = { name = @P@_vote_1 value = var:@W@_m267_vote_1 }
            set_variable = { name = @P@_vote_2 value = var:@W@_m267_vote_2 }
            set_variable = { name = @P@_vote_3 value = var:@W@_m267_vote_3 }
            set_variable = { name = @P@_evidence_1 value = var:@W@_m267_vote_evidence_1 }
            set_variable = { name = @P@_evidence_2 value = var:@W@_m267_vote_evidence_2 }
            set_variable = { name = @P@_evidence_3 value = var:@W@_m267_vote_evidence_3 }
            set_variable = { name = @P@_final_approver value = var:@W@_m272_offer_approver }
            set_variable = { name = @P@_appointment_receipt_id value = var:@W@_m274_position_receipt_id }
            set_variable = { name = @P@_appointment_receipt_hash value = var:@W@_m274_position_receipt_hash }
            set_variable = { name = @P@_consumed value = 0 }
            set_variable = { name = @P@_state value = 1 }
            set_variable = { name = @P@_status value = 1 }
            set_variable = { name = @P@_signature_pending value = 1 } # arm commit marker is last
            trigger_event = { id = @N@.2 days = 1 }
        }
        else = {
            set_variable = { name = @P@_status value = 4 }
            set_variable = { name = @P@_red_code value = 26911 }
            debug_log = "ZG361WAF RED 26911: #267/#272/#274 manifests cannot authorize an attribution signature"
        }
    }

    # Result adapter: the caller supplies only the real owner.  The two values
    # awaited by the probation producer come exclusively from the signed fact.
    # The producer call and its read-side ACK are deliberately separated by a
    # hidden D+1 event; no value written by probation is read in this chain.
    @P@_publish_result_effect = {
        remove_variable = @P@_status
        remove_variable = @P@_red_code
        if = {
            limit = {
                has_variable = @P@_attribution_bps_1
                has_variable = @P@_attribution_bps_2
                has_variable = @P@_attribution_bps_3
            }
            save_temporary_scope_value_as = {
                name = @P@_frozen_total_bps
                value = {
                    value = var:@P@_attribution_bps_1
                    add = var:@P@_attribution_bps_2
                    add = var:@P@_attribution_bps_3
                }
            }
        }
        if = {
            limit = {
                has_variable = @P@_consumed
                has_variable = @P@_owner
                has_variable = @P@_subject
                has_variable = @P@_cycle
                has_variable = @P@_case
                has_variable = @P@_receipt_id
                has_variable = @P@_receipt_hash
                has_variable = @P@_consume_owner
                has_variable = @P@_consume_subject
                has_variable = @P@_consume_hire_cycle
                has_variable = @P@_consume_hire_case
                has_variable = @P@_consume_result_owner
                has_variable = @P@_consume_result_subject
                has_variable = @P@_consume_result_cycle
                has_variable = @P@_consume_result_case
                has_variable = @P@_consume_result_state
                has_variable = @P@_consume_result_settlement_receipt
                has_variable = @P@_consume_result_grade
                has_variable = @P@_consume_result_reason
                has_variable = @P@_consume_result_kpi
                has_variable = @P@_consume_result_rank
                has_variable = @P@_consume_attribution_receipt_id
                has_variable = @P@_consume_attribution_receipt_hash
                has_variable = @P@_consume_probation_receipt_id
                has_variable = @P@_consume_probation_receipt_hash
                has_variable = zg361_result_case_owner
                has_variable = zg361_result_cycle_serial
                has_variable = zg361_result_case_serial
                has_variable = zg361_result_case_state
                has_variable = zg361_result_settlement_posted_serial
                has_variable = zg361_result_grade
                has_variable = zg361_result_grade_reason
                has_variable = zg361_result_kpi_frozen
                has_variable = zg361_result_rank_frozen
                var:@P@_consumed = 1
                var:@P@_owner = $OWNER$
                var:@P@_subject = this
                var:@P@_consume_owner = $OWNER$
                var:@P@_consume_subject = this
                var:@P@_consume_hire_cycle = var:@P@_cycle
                var:@P@_consume_hire_case = var:@P@_case
                var:@P@_consume_result_owner = $OWNER$
                var:@P@_consume_result_subject = this
                var:@P@_consume_result_cycle = var:zg361_result_cycle_serial
                var:@P@_consume_result_case = var:zg361_result_case_serial
                var:@P@_consume_result_state = var:zg361_result_case_state
                var:@P@_consume_result_settlement_receipt = var:zg361_result_settlement_posted_serial
                var:@P@_consume_result_grade = var:zg361_result_grade
                var:@P@_consume_result_reason = var:zg361_result_grade_reason
                var:@P@_consume_result_kpi = var:zg361_result_kpi_frozen
                var:@P@_consume_result_rank = var:zg361_result_rank_frozen
                var:@P@_consume_attribution_receipt_id = var:@P@_receipt_id
                var:@P@_consume_attribution_receipt_hash = var:@P@_receipt_hash
                var:zg361_result_case_owner = $OWNER$
            }
            set_variable = { name = @P@_status value = 2 }
        }
        else_if = {
            limit = {
                has_variable = @P@_dispatch_committed
                has_variable = @P@_dispatch_pending
                has_variable = @P@_consumed
                has_variable = @P@_dispatch_owner
                has_variable = @P@_dispatch_subject
                has_variable = @P@_dispatch_hire_cycle
                has_variable = @P@_dispatch_hire_case
                has_variable = @P@_dispatch_result_owner
                has_variable = @P@_dispatch_result_subject
                has_variable = @P@_dispatch_result_cycle
                has_variable = @P@_dispatch_result_case
                has_variable = @P@_dispatch_result_state
                has_variable = @P@_dispatch_result_settlement_receipt
                has_variable = @P@_dispatch_result_grade
                has_variable = @P@_dispatch_result_reason
                has_variable = @P@_dispatch_result_kpi
                has_variable = @P@_dispatch_result_rank
                has_variable = @P@_dispatch_attribution_receipt_id
                has_variable = @P@_dispatch_attribution_receipt_hash
                has_variable = zg361_result_case_owner
                has_variable = zg361_result_cycle_serial
                has_variable = zg361_result_case_serial
                has_variable = zg361_result_case_state
                has_variable = zg361_result_settlement_posted_serial
                has_variable = zg361_result_grade
                has_variable = zg361_result_grade_reason
                has_variable = zg361_result_kpi_frozen
                has_variable = zg361_result_rank_frozen
                var:@P@_dispatch_committed = 1
                var:@P@_dispatch_pending = 1
                var:@P@_consumed = 0
                var:@P@_owner = $OWNER$
                var:@P@_subject = this
                var:@P@_dispatch_owner = $OWNER$
                var:@P@_dispatch_subject = this
                var:@P@_dispatch_hire_cycle = var:@P@_cycle
                var:@P@_dispatch_hire_case = var:@P@_case
                var:@P@_dispatch_result_owner = $OWNER$
                var:@P@_dispatch_result_subject = this
                var:@P@_dispatch_result_cycle = var:zg361_result_cycle_serial
                var:@P@_dispatch_result_case = var:zg361_result_case_serial
                var:@P@_dispatch_result_state = var:zg361_result_case_state
                var:@P@_dispatch_result_settlement_receipt = var:zg361_result_settlement_posted_serial
                var:@P@_dispatch_result_grade = var:zg361_result_grade
                var:@P@_dispatch_result_reason = var:zg361_result_grade_reason
                var:@P@_dispatch_result_kpi = var:zg361_result_kpi_frozen
                var:@P@_dispatch_result_rank = var:zg361_result_rank_frozen
                var:@P@_dispatch_attribution_receipt_id = var:@P@_receipt_id
                var:@P@_dispatch_attribution_receipt_hash = var:@P@_receipt_hash
                var:zg361_result_case_owner = $OWNER$
            }
            set_variable = { name = @P@_status value = 5 }
            trigger_event = { id = @N@.3 days = 1 }
        }
        else_if = {
            limit = {
                trigger_if = { limit = { has_variable = @P@_dispatch_committed } var:@P@_dispatch_committed = 0 }
                trigger_else = { always = yes }
                has_variable = @P@_signature_committed
                has_variable = @P@_state
                has_variable = @P@_consumed
                has_variable = @P@_owner
                has_variable = @P@_subject
                has_variable = @P@_cycle
                has_variable = @P@_case
                has_variable = @P@_signature_actor
                has_variable = @P@_final_approver
                has_variable = @P@_signature_mode
                has_variable = @P@_signature_tie_rule
                has_variable = @P@_receipt_id
                has_variable = @P@_receipt_hash
                has_variable = @P@_receipt_signer
                has_variable = @P@_receipt_interviewer_1
                has_variable = @P@_receipt_interviewer_2
                has_variable = @P@_receipt_interviewer_3
                has_variable = @P@_receipt_evidence_1
                has_variable = @P@_receipt_evidence_2
                has_variable = @P@_receipt_evidence_3
                has_variable = @P@_interviewer_1
                has_variable = @P@_interviewer_2
                has_variable = @P@_interviewer_3
                has_variable = @P@_evidence_1
                has_variable = @P@_evidence_2
                has_variable = @P@_evidence_3
                has_variable = @P@_attribution_bps_1
                has_variable = @P@_attribution_bps_2
                has_variable = @P@_attribution_bps_3
                has_variable = @P@_attribution_total_bps
                has_variable = zg361_result_case_owner
                has_variable = zg361_result_cycle_serial
                has_variable = zg361_result_case_serial
                has_variable = zg361_result_case_state
                has_variable = zg361_result_settlement_posted_serial
                has_variable = zg361_result_grade
                has_variable = zg361_result_grade_reason
                has_variable = zg361_result_kpi_frozen
                has_variable = zg361_result_rank_frozen
                var:@P@_signature_committed = 1
                var:@P@_state = 2
                var:@P@_consumed = 0
                var:@P@_owner = $OWNER$
                var:@P@_subject = this
                var:@P@_signature_actor = var:@P@_final_approver
                var:@P@_receipt_signer = var:@P@_final_approver
                var:@P@_signature_policy_version = 1
                var:@P@_signature_policy_basis = 1
                var:@P@_receipt_policy_version = 1
                var:@P@_receipt_policy_basis = 1
                var:@P@_receipt_signature_mode = var:@P@_signature_mode
                var:@P@_receipt_tie_rule = var:@P@_signature_tie_rule
                var:@P@_receipt_interviewer_1 = var:@P@_interviewer_1
                var:@P@_receipt_interviewer_2 = var:@P@_interviewer_2
                var:@P@_receipt_interviewer_3 = var:@P@_interviewer_3
                var:@P@_receipt_evidence_1 = var:@P@_evidence_1
                var:@P@_receipt_evidence_2 = var:@P@_evidence_2
                var:@P@_receipt_evidence_3 = var:@P@_evidence_3
                scope:@P@_frozen_total_bps = 10000
                var:@P@_attribution_total_bps = 10000
                var:@P@_attribution_bps_1 >= 0
                var:@P@_attribution_bps_2 >= 0
                var:@P@_attribution_bps_3 >= 0
                var:zg361_result_case_owner = $OWNER$
                var:zg361_result_cycle_serial > var:@P@_cycle
                var:zg361_result_case_serial > 0
                OR = { var:zg361_result_case_state = 3 var:zg361_result_case_state = 5 }
                var:zg361_result_settlement_posted_serial = var:zg361_result_case_serial
                OR = { var:zg361_result_grade = 1 var:zg361_result_grade = 2 var:zg361_result_grade = 3 }
                has_variable = @W@_m267_candidate_frozen
                has_variable = @W@_m267_interviewer_1
                has_variable = @W@_m267_interviewer_2
                has_variable = @W@_m267_interviewer_3
                has_variable = @W@_m267_vote_evidence_1
                has_variable = @W@_m267_vote_evidence_2
                has_variable = @W@_m267_vote_evidence_3
                has_variable = @W@_m272_offer_candidate
                has_variable = @W@_m272_offer_approver
                var:@W@_m267_candidate_frozen = this
                var:@W@_m267_interviewer_1 = var:@P@_interviewer_1
                var:@W@_m267_interviewer_2 = var:@P@_interviewer_2
                var:@W@_m267_interviewer_3 = var:@P@_interviewer_3
                var:@W@_m267_vote_evidence_1 = var:@P@_evidence_1
                var:@W@_m267_vote_evidence_2 = var:@P@_evidence_2
                var:@W@_m267_vote_evidence_3 = var:@P@_evidence_3
                var:@W@_m272_offer_candidate = this
                var:@W@_m272_offer_approver = var:@P@_final_approver
            }
            set_variable = { name = @P@_dispatch_owner value = $OWNER$ }
            set_variable = { name = @P@_dispatch_subject value = this }
            set_variable = { name = @P@_dispatch_hire_cycle value = var:@P@_cycle }
            set_variable = { name = @P@_dispatch_hire_case value = var:@P@_case }
            set_variable = { name = @P@_dispatch_result_owner value = $OWNER$ }
            set_variable = { name = @P@_dispatch_result_subject value = this }
            set_variable = { name = @P@_dispatch_result_cycle value = var:zg361_result_cycle_serial }
            set_variable = { name = @P@_dispatch_result_case value = var:zg361_result_case_serial }
            set_variable = { name = @P@_dispatch_result_state value = var:zg361_result_case_state }
            set_variable = { name = @P@_dispatch_result_settlement_receipt value = var:zg361_result_settlement_posted_serial }
            set_variable = { name = @P@_dispatch_result_grade value = var:zg361_result_grade }
            set_variable = { name = @P@_dispatch_result_reason value = var:zg361_result_grade_reason }
            set_variable = { name = @P@_dispatch_result_kpi value = var:zg361_result_kpi_frozen }
            set_variable = { name = @P@_dispatch_result_rank value = var:zg361_result_rank_frozen }
            set_variable = { name = @P@_dispatch_signature_actor value = var:@P@_signature_actor }
            set_variable = { name = @P@_dispatch_attribution_receipt_id value = var:@P@_receipt_id }
            set_variable = { name = @P@_dispatch_attribution_receipt_hash value = var:@P@_receipt_hash }
            set_variable = { name = @P@_dispatch_bps_1 value = var:@P@_attribution_bps_1 }
            set_variable = { name = @P@_dispatch_bps_2 value = var:@P@_attribution_bps_2 }
            set_variable = { name = @P@_dispatch_bps_3 value = var:@P@_attribution_bps_3 }
            set_variable = { name = @P@_dispatch_evidence_1 value = var:@P@_evidence_1 }
            set_variable = { name = @P@_dispatch_evidence_2 value = var:@P@_evidence_2 }
            set_variable = { name = @P@_dispatch_evidence_3 value = var:@P@_evidence_3 }
            set_variable = { name = @P@_dispatch_pending value = 1 }
            set_variable = { name = @P@_status value = 5 }
            set_variable = { name = @P@_dispatch_committed value = 1 } # dispatch receipt commit marker is last
            @Q@_publish_from_result_effect = {
                OWNER = $OWNER$
                ATTRIBUTION_BPS_2 = var:@P@_attribution_bps_2
                ATTRIBUTION_BPS_3 = var:@P@_attribution_bps_3
            }
            trigger_event = { id = @N@.3 days = 1 }
            debug_log = "ZG361WAF: signed attribution dispatched; probation ACK deferred to D+1"
        }
        else = {
            set_variable = { name = @P@_status value = 4 }
            set_variable = { name = @P@_red_code value = 26921 }
        }
    }

    # Read-side ACK for the D+1 hidden event.  It binds the probation fact to
    # the exact result tuple frozen before dispatch, then consumes this slot.
    @P@_ack_probation_publish_effect = {
        remove_variable = @P@_status
        remove_variable = @P@_red_code
        if = {
            limit = {
                has_variable = @P@_consumed
                has_variable = @P@_consume_owner
                has_variable = @P@_consume_subject
                has_variable = @P@_consume_attribution_receipt_id
                has_variable = @P@_consume_attribution_receipt_hash
                var:@P@_consumed = 1
                var:@P@_consume_owner = var:@P@_dispatch_owner
                var:@P@_consume_subject = this
                var:@P@_consume_attribution_receipt_id = var:@P@_dispatch_attribution_receipt_id
                var:@P@_consume_attribution_receipt_hash = var:@P@_dispatch_attribution_receipt_hash
            }
            set_variable = { name = @P@_status value = 2 }
        }
        else_if = {
            limit = {
                has_variable = @P@_dispatch_committed
                has_variable = @P@_dispatch_pending
                has_variable = @P@_consumed
                has_variable = @P@_owner
                has_variable = @P@_subject
                has_variable = @P@_cycle
                has_variable = @P@_case
                has_variable = @P@_receipt_id
                has_variable = @P@_receipt_hash
                has_variable = @P@_dispatch_owner
                has_variable = @P@_dispatch_subject
                has_variable = @P@_dispatch_hire_cycle
                has_variable = @P@_dispatch_hire_case
                has_variable = @P@_dispatch_result_owner
                has_variable = @P@_dispatch_result_subject
                has_variable = @P@_dispatch_result_cycle
                has_variable = @P@_dispatch_result_case
                has_variable = @P@_dispatch_result_state
                has_variable = @P@_dispatch_result_settlement_receipt
                has_variable = @P@_dispatch_result_grade
                has_variable = @P@_dispatch_result_reason
                has_variable = @P@_dispatch_result_kpi
                has_variable = @P@_dispatch_result_rank
                has_variable = @P@_dispatch_attribution_receipt_id
                has_variable = @P@_dispatch_attribution_receipt_hash
                has_variable = @P@_dispatch_bps_1
                has_variable = @P@_dispatch_bps_2
                has_variable = @P@_dispatch_bps_3
                has_variable = @P@_dispatch_evidence_1
                has_variable = @P@_dispatch_evidence_2
                has_variable = @P@_dispatch_evidence_3
                has_variable = @Q@_state
                has_variable = @Q@_adapter_status
                has_variable = @Q@_owner
                has_variable = @Q@_subject
                has_variable = @Q@_hire_cycle
                has_variable = @Q@_hire_case
                has_variable = @Q@_source_result_owner
                has_variable = @Q@_source_result_subject
                has_variable = @Q@_source_result_cycle
                has_variable = @Q@_source_result_case
                has_variable = @Q@_source_result_state
                has_variable = @Q@_source_result_settlement_receipt
                has_variable = @Q@_source_result_grade
                has_variable = @Q@_source_result_reason
                has_variable = @Q@_source_result_kpi
                has_variable = @Q@_source_result_rank
                has_variable = @Q@_attribution_bps_1
                has_variable = @Q@_attribution_bps_2
                has_variable = @Q@_attribution_bps_3
                has_variable = @Q@_outcome_dimension_1
                has_variable = @Q@_outcome_dimension_2
                has_variable = @Q@_outcome_dimension_3
                has_variable = @Q@_attribution_receipt_id
                has_variable = @Q@_attribution_receipt_hash
                var:@P@_dispatch_committed = 1
                var:@P@_dispatch_pending = 1
                var:@P@_consumed = 0
                var:@P@_owner = var:@P@_dispatch_owner
                var:@P@_subject = this
                var:@P@_dispatch_subject = this
                var:@P@_dispatch_hire_cycle = var:@P@_cycle
                var:@P@_dispatch_hire_case = var:@P@_case
                var:@P@_dispatch_attribution_receipt_id = var:@P@_receipt_id
                var:@P@_dispatch_attribution_receipt_hash = var:@P@_receipt_hash
                var:@Q@_state >= 2
                var:@Q@_state <= 4
                OR = { var:@Q@_adapter_status = 1 var:@Q@_adapter_status = 2 var:@Q@_adapter_status = 3 var:@Q@_adapter_status = 4 }
                var:@Q@_owner = var:@P@_dispatch_owner
                var:@Q@_subject = this
                var:@Q@_hire_cycle = var:@P@_dispatch_hire_cycle
                var:@Q@_hire_case = var:@P@_dispatch_hire_case
                var:@Q@_source_result_owner = var:@P@_dispatch_result_owner
                var:@Q@_source_result_subject = this
                var:@Q@_source_result_cycle = var:@P@_dispatch_result_cycle
                var:@Q@_source_result_case = var:@P@_dispatch_result_case
                var:@Q@_source_result_state = var:@P@_dispatch_result_state
                var:@Q@_source_result_settlement_receipt = var:@P@_dispatch_result_settlement_receipt
                var:@Q@_source_result_grade = var:@P@_dispatch_result_grade
                var:@Q@_source_result_reason = var:@P@_dispatch_result_reason
                var:@Q@_source_result_kpi = var:@P@_dispatch_result_kpi
                var:@Q@_source_result_rank = var:@P@_dispatch_result_rank
                var:@Q@_attribution_bps_1 = var:@P@_dispatch_bps_1
                var:@Q@_attribution_bps_2 = var:@P@_dispatch_bps_2
                var:@Q@_attribution_bps_3 = var:@P@_dispatch_bps_3
                var:@Q@_outcome_dimension_1 = var:@P@_dispatch_evidence_1
                var:@Q@_outcome_dimension_2 = var:@P@_dispatch_evidence_2
                var:@Q@_outcome_dimension_3 = var:@P@_dispatch_evidence_3
                var:@Q@_attribution_receipt_id > 0
                var:@Q@_attribution_receipt_hash > 0
            }
            set_variable = { name = @P@_consume_owner value = var:@P@_dispatch_owner }
            set_variable = { name = @P@_consume_subject value = this }
            set_variable = { name = @P@_consume_hire_cycle value = var:@P@_dispatch_hire_cycle }
            set_variable = { name = @P@_consume_hire_case value = var:@P@_dispatch_hire_case }
            set_variable = { name = @P@_consume_result_owner value = var:@P@_dispatch_result_owner }
            set_variable = { name = @P@_consume_result_subject value = this }
            set_variable = { name = @P@_consume_result_cycle value = var:@P@_dispatch_result_cycle }
            set_variable = { name = @P@_consume_result_case value = var:@P@_dispatch_result_case }
            set_variable = { name = @P@_consume_result_state value = var:@P@_dispatch_result_state }
            set_variable = { name = @P@_consume_result_settlement_receipt value = var:@P@_dispatch_result_settlement_receipt }
            set_variable = { name = @P@_consume_result_grade value = var:@P@_dispatch_result_grade }
            set_variable = { name = @P@_consume_result_reason value = var:@P@_dispatch_result_reason }
            set_variable = { name = @P@_consume_result_kpi value = var:@P@_dispatch_result_kpi }
            set_variable = { name = @P@_consume_result_rank value = var:@P@_dispatch_result_rank }
            set_variable = { name = @P@_consume_attribution_receipt_id value = var:@P@_dispatch_attribution_receipt_id }
            set_variable = { name = @P@_consume_attribution_receipt_hash value = var:@P@_dispatch_attribution_receipt_hash }
            set_variable = { name = @P@_consume_probation_receipt_id value = var:@Q@_attribution_receipt_id }
            set_variable = { name = @P@_consume_probation_receipt_hash value = var:@Q@_attribution_receipt_hash }
            set_variable = { name = @P@_dispatch_pending value = 0 }
            set_variable = { name = @P@_dispatch_acked value = 1 }
            set_variable = { name = @P@_state value = 3 }
            set_variable = { name = @P@_status value = 1 }
            set_variable = { name = @P@_consumed value = 1 } # consume marker is last
            debug_log = "ZG361WAF: D+1 probation ACK consumed the exact signed attribution/result tuple"
        }
        else = {
            set_variable = { name = @P@_status value = 4 }
            set_variable = { name = @P@_red_code value = 26922 }
            debug_log = "ZG361WAF RED 26922: probation ACK did not match the frozen dispatch tuple"
        }
    }

    # Route C creates a policy-debt receipt instead of a #269 outcome object.
    # This adapter lets the central integration close the signed slot without
    # pretending that probation consumed it.  Call only on a later event/frame
    # after the debt manifest and its read-side visibility marker exist.
    @P@_cancel_from_m269_debt_effect = {
        remove_variable = @P@_status
        remove_variable = @P@_red_code
        if = {
            limit = { has_variable = @P@_cycle has_variable = @P@_case }
            save_temporary_scope_value_as = {
                name = @P@_expected_m269_debt_id
                value = {
                    value = var:@P@_cycle multiply = 1000000
                    add = { value = var:@P@_case multiply = 1000 }
                    add = 269
                }
            }
            save_temporary_scope_value_as = {
                name = @P@_expected_m269_debt_due_cycle
                value = { value = var:@P@_cycle add = 1 }
            }
        }
        if = {
            limit = {
                has_variable = @P@_consumed
                has_variable = @P@_canceled
                has_variable = @P@_cancel_owner
                has_variable = @P@_cancel_subject
                has_variable = @P@_cancel_cycle
                has_variable = @P@_cancel_case
                has_variable = @P@_cancel_reason
                has_variable = @P@_cancel_debt_id
                has_variable = @P@_cancel_debt_due_cycle
                has_variable = @P@_cancel_debt_escalation_count
                has_variable = @P@_cancel_m269_receipt_owner
                has_variable = @P@_cancel_m269_receipt_subject
                has_variable = @P@_cancel_m269_receipt_cycle
                has_variable = @P@_cancel_m269_receipt_case
                has_variable = @P@_cancel_m269_receipt_state
                has_variable = @P@_cancel_m269_receipt_choice
                var:@P@_consumed = 1
                var:@P@_canceled = 1
                var:@P@_owner = $OWNER$
                var:@P@_subject = this
                var:@P@_cancel_owner = $OWNER$
                var:@P@_cancel_subject = this
                var:@P@_cancel_cycle = var:@P@_cycle
                var:@P@_cancel_case = var:@P@_case
                var:@P@_cancel_reason = 1
                var:@P@_cancel_debt_id = scope:@P@_expected_m269_debt_id
                var:@P@_cancel_debt_due_cycle = scope:@P@_expected_m269_debt_due_cycle
                var:@P@_cancel_debt_escalation_count = 0
                var:@P@_cancel_m269_receipt_owner = $OWNER$
                var:@P@_cancel_m269_receipt_subject = this
                var:@P@_cancel_m269_receipt_cycle = var:@P@_cycle
                var:@P@_cancel_m269_receipt_case = var:@P@_case
                var:@P@_cancel_m269_receipt_state = 5
                var:@P@_cancel_m269_receipt_choice = 3
            }
            set_variable = { name = @P@_status value = 2 }
        }
        else_if = {
            limit = {
                has_variable = @P@_signature_committed
                var:@P@_signature_committed = 1
                var:@P@_state = 2
                var:@P@_consumed = 0
                var:@P@_owner = $OWNER$
                var:@P@_subject = this
                has_variable = @W@_m269_write_owner
                has_variable = @W@_m269_write_subject
                has_variable = @W@_m269_write_cycle
                has_variable = @W@_m269_write_case
                has_variable = @W@_m269_write_state
                has_variable = @W@_m269_choice
                has_variable = @W@_m269_business_object_created
                has_variable = @W@_m269_receipt_owner
                has_variable = @W@_m269_receipt_subject
                has_variable = @W@_m269_receipt_cycle
                has_variable = @W@_m269_receipt_case
                has_variable = @W@_m269_receipt_state
                has_variable = @W@_m269_receipt_choice
                has_variable = @W@_m269_debt_owner
                has_variable = @W@_m269_debt_subject
                has_variable = @W@_m269_debt_cycle
                has_variable = @W@_m269_debt_case
                has_variable = @W@_m269_debt_state
                has_variable = @W@_m269_debt_type_code
                has_variable = @W@_m269_debt_id
                has_variable = @W@_m269_debt_consumer_contract
                has_variable = @W@_m269_debt_due_cycle
                has_variable = @W@_m269_debt_open
                has_variable = @W@_m269_debt_consumed
                has_variable = @W@_m269_debt_escalation_count
                has_variable = @W@_m269_debt_visible_to_settlement
                var:@W@_m269_write_owner = $OWNER$
                var:@W@_m269_write_subject = this
                var:@W@_m269_write_cycle = var:@P@_cycle
                var:@W@_m269_write_case = var:@P@_case
                var:@W@_m269_write_state = 5
                var:@W@_m269_choice = 3
                var:@W@_m269_business_object_created = 0
                var:@W@_m269_receipt_owner = $OWNER$
                var:@W@_m269_receipt_subject = this
                var:@W@_m269_receipt_cycle = var:@P@_cycle
                var:@W@_m269_receipt_case = var:@P@_case
                var:@W@_m269_receipt_state = 5
                var:@W@_m269_receipt_choice = 3
                var:@W@_m269_debt_owner = $OWNER$
                var:@W@_m269_debt_subject = this
                var:@W@_m269_debt_cycle = var:@P@_cycle
                var:@W@_m269_debt_case = var:@P@_case
                var:@W@_m269_debt_state = 5
                var:@W@_m269_debt_type_code = 269
                var:@W@_m269_debt_consumer_contract = 269
                var:@W@_m269_debt_due_cycle = scope:@P@_expected_m269_debt_due_cycle
                var:@W@_m269_debt_open = 1
                var:@W@_m269_debt_consumed = 0
                var:@W@_m269_debt_escalation_count = 0
                var:@W@_m269_debt_visible_to_settlement = 1
            }
            if = {
                limit = { var:@W@_m269_debt_id = scope:@P@_expected_m269_debt_id }
                set_variable = { name = @P@_cancel_owner value = $OWNER$ }
                set_variable = { name = @P@_cancel_subject value = this }
                set_variable = { name = @P@_cancel_cycle value = var:@P@_cycle }
                set_variable = { name = @P@_cancel_case value = var:@P@_case }
                set_variable = { name = @P@_cancel_debt_id value = var:@W@_m269_debt_id }
                set_variable = { name = @P@_cancel_debt_due_cycle value = var:@W@_m269_debt_due_cycle }
                set_variable = { name = @P@_cancel_debt_escalation_count value = var:@W@_m269_debt_escalation_count }
                set_variable = { name = @P@_cancel_m269_receipt_owner value = var:@W@_m269_receipt_owner }
                set_variable = { name = @P@_cancel_m269_receipt_subject value = var:@W@_m269_receipt_subject }
                set_variable = { name = @P@_cancel_m269_receipt_cycle value = var:@W@_m269_receipt_cycle }
                set_variable = { name = @P@_cancel_m269_receipt_case value = var:@W@_m269_receipt_case }
                set_variable = { name = @P@_cancel_m269_receipt_state value = var:@W@_m269_receipt_state }
                set_variable = { name = @P@_cancel_m269_receipt_choice value = var:@W@_m269_receipt_choice }
                set_variable = { name = @P@_cancel_reason value = 1 }
                set_variable = { name = @P@_canceled value = 1 }
                set_variable = { name = @P@_state value = 3 }
                set_variable = { name = @P@_status value = 1 }
                set_variable = { name = @P@_consumed value = 1 } # cancel/consume marker is last
            }
            else = {
                set_variable = { name = @P@_status value = 4 }
                set_variable = { name = @P@_red_code value = 26932 }
            }
        }
        else = {
            set_variable = { name = @P@_status value = 4 }
            set_variable = { name = @P@_red_code value = 26931 }
        }
    }
    '''
    rendered = (
        template.replace("@POLICY_GUARD@", _policy_guard())
        .replace("@P@", PREFIX)
        .replace("@N@", NAMESPACE)
        .replace("@W@", WORKFORCE_PREFIX)
        .replace("@Q@", PROBATION_PREFIX)
    )
    return generated(rendered)


def _skip_comment(text: str, index: int) -> int:
    newline = text.find("\n", index)
    return len(text) if newline < 0 else newline + 1


def _skip_quoted_string(text: str, index: int) -> int:
    index += 1
    escaped = False
    while index < len(text):
        char = text[index]
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == '"':
            return index + 1
        index += 1
    raise ValueError("unterminated quoted string in attribution fact script")


def _block_end(text: str, index: int) -> int:
    depth = 0
    while index < len(text):
        char = text[index]
        if char == "#":
            index = _skip_comment(text, index)
            continue
        if char == '"':
            index = _skip_quoted_string(text, index)
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index + 1
            if depth < 0:
                raise ValueError("unbalanced attribution fact script block")
        index += 1
    raise ValueError("unterminated attribution fact script block")


def top_level_blocks(payload: bytes | str) -> tuple[tuple[str, str], ...]:
    """Return exact top-level assignment blocks, ignoring comments/strings."""

    text = (
        payload.decode("utf-8-sig")
        if isinstance(payload, bytes)
        else payload.lstrip("\ufeff")
    )
    blocks: list[tuple[str, str]] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char == "#":
            index = _skip_comment(text, index)
            continue
        if char == '"':
            index = _skip_quoted_string(text, index)
            continue
        if not (char.isalpha() or char == "_"):
            index += 1
            continue
        start = index
        index += 1
        while index < len(text) and (
            text[index].isalnum() or text[index] in "_."
        ):
            index += 1
        name = text[start:index]
        cursor = index
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if cursor >= len(text) or text[cursor] != "=":
            continue
        cursor += 1
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if cursor >= len(text) or text[cursor] != "{":
            continue
        end = _block_end(text, cursor)
        blocks.append((name, text[start:end]))
        index = end
    return tuple(blocks)


def _validate_historical_aggregate(
    *,
    label: str,
    aggregate: bytes,
    source_blocks: tuple[tuple[str, str], ...],
    expected_bytes: int,
    expected_sha256: str,
    expected_count: int,
) -> tuple[str, ...]:
    if len(aggregate) != expected_bytes:
        raise ValueError(
            f"Workforce attribution {label} aggregate byte count drifted: "
            f"expected {expected_bytes}, found {len(aggregate)}"
        )
    aggregate_sha256 = hashlib.sha256(aggregate).hexdigest()
    if aggregate_sha256 != expected_sha256:
        raise ValueError(
            f"Workforce attribution {label} aggregate SHA-256 drifted: "
            f"expected {expected_sha256}, found {aggregate_sha256}"
        )
    source_names = tuple(name for name, _block in source_blocks)
    if len(source_names) != expected_count:
        raise ValueError(
            f"Workforce attribution {label} aggregate must contain "
            f"{expected_count} top-level definitions, found {len(source_names)}"
        )
    if len(source_names) != len(set(source_names)):
        raise ValueError(
            f"Workforce attribution {label} aggregate contains duplicate definitions"
        )
    return source_names


def _validate_effect_groups(
    aggregate: bytes, source_blocks: tuple[tuple[str, str], ...]
) -> None:
    source_names = _validate_historical_aggregate(
        label="effect",
        aggregate=aggregate,
        source_blocks=source_blocks,
        expected_bytes=HISTORICAL_EFFECT_BYTES,
        expected_sha256=HISTORICAL_EFFECT_SHA256,
        expected_count=HISTORICAL_EFFECT_COUNT,
    )
    configured_names = tuple(
        name for group in EFFECT_GROUPS for name in group.effect_names
    )
    filenames = tuple(group.filename for group in EFFECT_GROUPS)
    if len(filenames) != len(set(filenames)):
        raise ValueError("Workforce attribution effect shard filenames must be unique")
    if len(configured_names) != len(set(configured_names)):
        raise ValueError("Workforce attribution purpose groups duplicate an effect")
    if configured_names != source_names:
        missing = sorted(set(source_names) - set(configured_names))
        extra = sorted(set(configured_names) - set(source_names))
        raise ValueError(
            "Workforce attribution purpose groups must preserve the exact "
            f"historical effect order; missing={missing}, extra={extra}"
        )
    seed_closure = set(SEED_EFFECT_CLOSURE_NAMES)
    selected = [
        group for group in EFFECT_GROUPS
        if seed_closure.intersection(group.effect_names)
    ]
    mixed = [
        group.filename
        for group in selected
        if not set(group.effect_names).issubset(seed_closure)
    ]
    selected_names = {
        name for group in selected for name in group.effect_names
    }
    deferred = set(source_names) - seed_closure
    if (
        len(seed_closure) != 5
        or len(selected) != 2
        or mixed
        or selected_names != seed_closure
        or deferred != set(DEFERRED_EFFECT_NAMES)
        or len(deferred) != 2
    ):
        raise ValueError(
            "Workforce attribution seed effects must be an exact two-shard "
            f"5/7 union; mixed={mixed}, missing={sorted(seed_closure - selected_names)}, "
            f"extra={sorted(selected_names - seed_closure)}, "
            f"deferred={sorted(deferred)}"
        )

    _validate_effect_size_policy()


def _validate_effect_size_policy() -> None:
    for group in EFFECT_GROUPS:
        if not group.effect_names:
            raise ValueError(f"{group.filename} must contain at least one effect")
        if not group.purpose.strip():
            raise ValueError(f"{group.filename} must declare a purpose")

    over_hard = {
        group.filename
        for group in EFFECT_GROUPS
        if len(group.effect_names) > EFFECT_HARD_MAX
    }
    if set(EFFECT_HARD_LIMIT_EXCEPTIONS) != over_hard:
        raise ValueError(
            "Workforce attribution hard-limit exceptions must exactly match "
            f"shards above {EFFECT_HARD_MAX} effects"
        )
    for filename in sorted(over_hard):
        reason, live_evidence = EFFECT_HARD_LIMIT_EXCEPTIONS[filename]
        if not reason.strip() or not live_evidence.strip():
            raise ValueError(
                f"{filename} exceeds {EFFECT_HARD_MAX} effects without both "
                "a reason and CK3 live evidence"
            )


def effect_target_deviations() -> tuple[EffectGroup, ...]:
    """Return reportable >10 shards without treating 11-20 as invalid."""

    return tuple(
        group
        for group in EFFECT_GROUPS
        if len(group.effect_names) > EFFECT_TARGET_MAX
    )


def render_effect_parts() -> dict[str, bytes]:
    """Render purpose shards with every effect definition byte-identical."""

    aggregate = render_effects()
    source_blocks = top_level_blocks(aggregate)
    _validate_effect_groups(aggregate, source_blocks)
    by_name = dict(source_blocks)
    return {
        group.filename: generated(
            f"# PURPOSE: {group.purpose}.\n\n"
            + "\n\n".join(by_name[name] for name in group.effect_names)
        )
        for group in EFFECT_GROUPS
    }


def render_events() -> bytes:
    """Render the frozen historical event aggregate for parity validation."""

    option_rows: list[str] = []
    for policy, shares in ALLOCATION_POLICIES.items():
        option_rows.append(
            f'''
            option = {{
                name = {NAMESPACE}.1.option_{policy}
                hidden_effect = {{
                    scope:{PREFIX}_subject_scope = {{
                        {PREFIX}_sign_effect = {{
                            SIGNER = root POLICY = {policy}
                            LEAD = scope:{PREFIX}_interviewer_{policy}_scope
                            BPS_1 = {shares[0]} BPS_2 = {shares[1]} BPS_3 = {shares[2]}
                            SIGNATURE_MODE = {SIGNATURE_MODE_PLAYER} TIE_RULE = 0
                        }}
                    }}
                }}
            }}
            '''
        )
    return generated(
        f'''
        namespace = {NAMESPACE}

        {NAMESPACE}.1 = {{
            type = character_event
            theme = vassal
            title = {NAMESPACE}.1.title
            desc = {NAMESPACE}.1.desc
            trigger = {{
                is_ai = no
                exists = scope:{PREFIX}_subject_scope
                exists = scope:{PREFIX}_approver_scope
                exists = scope:{PREFIX}_interviewer_1_scope
                exists = scope:{PREFIX}_interviewer_2_scope
                exists = scope:{PREFIX}_interviewer_3_scope
                this = scope:{PREFIX}_approver_scope
                zg361_is_celestial_liege_trigger = yes
                scope:{PREFIX}_subject_scope = {{
                    has_variable = {PREFIX}_owner
                    has_variable = {PREFIX}_subject
                    has_variable = {PREFIX}_cycle
                    has_variable = {PREFIX}_case
                    has_variable = {PREFIX}_m267_object_id
                    has_variable = {PREFIX}_m272_object_id
                    has_variable = {PREFIX}_m274_object_id
                    has_variable = {PREFIX}_appointment_receipt_id
                    has_variable = {PREFIX}_appointment_receipt_hash
                    has_variable = {PREFIX}_signature_pending
                    var:{PREFIX}_signature_pending = 1
                    var:{PREFIX}_state = 1
                    var:{PREFIX}_owner = root
                    var:{PREFIX}_subject = this
                    var:{PREFIX}_final_approver = root
                    trigger_if = {{ limit = {{ has_variable = {PREFIX}_signature_committed }} var:{PREFIX}_signature_committed = 0 }}
                    trigger_else = {{ always = yes }}
                    var:{PREFIX}_interviewer_1 = scope:{PREFIX}_interviewer_1_scope
                    var:{PREFIX}_interviewer_2 = scope:{PREFIX}_interviewer_2_scope
                    var:{PREFIX}_interviewer_3 = scope:{PREFIX}_interviewer_3_scope
                }}
            }}
            {''.join(option_rows)}
        }}

        # Both player and AI approvers are dispatched from a later carrier
        # event, so every variable frozen by the arm effect is from a prior
        # frame.  The carrier is scheduled exactly once by a successful arm.
        {NAMESPACE}.2 = {{
            type = character_event
            hidden = yes
            trigger = {{
                has_variable = {PREFIX}_signature_pending
                has_variable = {PREFIX}_state
                has_variable = {PREFIX}_subject
                var:{PREFIX}_signature_pending = 1
                var:{PREFIX}_state = 1
                var:{PREFIX}_subject = this
                trigger_if = {{ limit = {{ has_variable = {PREFIX}_signature_committed }} var:{PREFIX}_signature_committed = 0 }}
                trigger_else = {{ always = yes }}
            }}
            immediate = {{
                set_variable = {{ name = {PREFIX}_signature_dispatch_issued value = 1 }}
                {PREFIX}_dispatch_signature_effect = yes
            }}
        }}

        # Cross-package ACK carrier.  The probation producer ran in the prior
        # frame; only this event may verify its frozen read-side tuple.
        {NAMESPACE}.3 = {{
            type = character_event
            hidden = yes
            trigger = {{
                has_variable = {PREFIX}_dispatch_committed
                has_variable = {PREFIX}_dispatch_pending
                has_variable = {PREFIX}_consumed
                has_variable = {PREFIX}_subject
                var:{PREFIX}_dispatch_committed = 1
                var:{PREFIX}_dispatch_pending = 1
                var:{PREFIX}_consumed = 0
                var:{PREFIX}_subject = this
            }}
            immediate = {{ {PREFIX}_ack_probation_publish_effect = yes }}
        }}
        '''
    )


def _validate_event_groups(
    aggregate: bytes, source_blocks: tuple[tuple[str, str], ...]
) -> None:
    source_names = _validate_historical_aggregate(
        label="event",
        aggregate=aggregate,
        source_blocks=source_blocks,
        expected_bytes=HISTORICAL_EVENT_BYTES,
        expected_sha256=HISTORICAL_EVENT_SHA256,
        expected_count=HISTORICAL_EVENT_COUNT,
    )
    configured_names = tuple(
        name for group in EVENT_GROUPS for name in group.event_names
    )
    filenames = tuple(group.filename for group in EVENT_GROUPS)
    if len(filenames) != len(set(filenames)):
        raise ValueError("Workforce attribution event shard filenames must be unique")
    if len(configured_names) != len(set(configured_names)):
        raise ValueError("Workforce attribution purpose groups duplicate an event")
    if configured_names != source_names:
        missing = sorted(set(source_names) - set(configured_names))
        extra = sorted(set(configured_names) - set(source_names))
        raise ValueError(
            "Workforce attribution purpose groups must preserve the exact "
            f"historical event order; missing={missing}, extra={extra}"
        )
    for group in EVENT_GROUPS:
        if not group.event_names:
            raise ValueError(f"{group.filename} must contain at least one event")
        if not group.purpose.strip():
            raise ValueError(f"{group.filename} must declare a purpose")

    seed_closure = set(SEED_EVENT_CLOSURE_NAMES)
    selected = [
        group for group in EVENT_GROUPS
        if seed_closure.intersection(group.event_names)
    ]
    mixed = [
        group.filename
        for group in selected
        if not set(group.event_names).issubset(seed_closure)
    ]
    selected_names = {
        name for group in selected for name in group.event_names
    }
    deferred = set(source_names) - seed_closure
    if (
        len(seed_closure) != 2
        or len(selected) != 1
        or mixed
        or selected_names != seed_closure
        or deferred != set(DEFERRED_EVENT_NAMES)
        or len(deferred) != 1
    ):
        raise ValueError(
            "Workforce attribution seed events must be an exact one-shard "
            f"2/3 union; mixed={mixed}, missing={sorted(seed_closure - selected_names)}, "
            f"extra={sorted(selected_names - seed_closure)}, "
            f"deferred={sorted(deferred)}"
        )


def render_event_parts() -> dict[str, bytes]:
    """Render purpose shards with every event definition byte-identical."""

    aggregate = render_events()
    source_blocks = top_level_blocks(aggregate)
    _validate_event_groups(aggregate, source_blocks)
    by_name = dict(source_blocks)
    return {
        group.filename: generated(
            f"# PURPOSE: {group.purpose}.\n\n"
            f"namespace = {NAMESPACE}\n\n"
            + "\n\n".join(by_name[name] for name in group.event_names)
        )
        for group in EVENT_GROUPS
    }


LOCALIZATION_EN: Final[dict[str, str]] = {
    "1.title": "Sign the Interview Accountability Split",
    "1.desc": (
        "The offer is frozen and the three interview ballots still have names attached. "
        "Choose which interviewer owns the lead share of the later quality writeback: "
        "[scope:zg361_workforce_attribution_fact_interviewer_1_scope.GetShortUIName], "
        "[scope:zg361_workforce_attribution_fact_interviewer_2_scope.GetShortUIName], or "
        "[scope:zg361_workforce_attribution_fact_interviewer_3_scope.GetShortUIName]. "
        "Your signature binds all three evidence receipts and exactly 10,000 basis points."
    ),
    "1.option_1": "First interviewer leads: 60% / 20% / 20%",
    "1.option_2": "Second interviewer leads: 20% / 60% / 20%",
    "1.option_3": "Third interviewer leads: 20% / 20% / 60%",
}

LOCALIZATION_CN: Final[dict[str, str]] = {
    "1.title": "请最终拍板者签署面试责任分配",
    "1.desc": (
        "Offer 已冻结，三张面试票也都还实名挂着。请决定后续录用质量回写由谁承担主责："
        "[scope:zg361_workforce_attribution_fact_interviewer_1_scope.GetShortUIName]、"
        "[scope:zg361_workforce_attribution_fact_interviewer_2_scope.GetShortUIName]，或"
        "[scope:zg361_workforce_attribution_fact_interviewer_3_scope.GetShortUIName]。"
        "你的签字会同时绑定三份证据回执，并把整整一万个基点分完；这口锅不能平均到小数点后。"
    ),
    "1.option_1": "第一席主责：60% / 20% / 20%",
    "1.option_2": "第二席主责：20% / 60% / 20%",
    "1.option_3": "第三席主责：20% / 20% / 60%",
}


def esc(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def render_localization(language: str) -> bytes:
    values = LOCALIZATION_CN if language == "simp_chinese" else LOCALIZATION_EN
    rows = [f"l_{language}:"]
    rows.extend(f' {NAMESPACE}.{key}:0 "{esc(value)}"' for key, value in values.items())
    return localized("\n".join(rows))


def outputs() -> dict[Path, bytes]:
    validate_contract()
    rendered: dict[Path, bytes] = {}
    rendered.update(
        {
            MOD_ROOT / "common" / "scripted_effects" / filename: payload
            for filename, payload in render_effect_parts().items()
        }
    )
    rendered.update(
        {
            MOD_ROOT / "events" / filename: payload
            for filename, payload in render_event_parts().items()
        }
    )
    for language in LANGUAGES:
        rendered[
            MOD_ROOT / "localization" / language / f"{PREFIX}_l_{language}.yml"
        ] = render_localization(language)
    return rendered


def unexpected_effect_paths(
    rendered: dict[Path, bytes], effects_dir: Path | None = None
) -> tuple[Path, ...]:
    effects_dir = effects_dir or MOD_ROOT / "common" / "scripted_effects"
    expected = {path for path in rendered if path.parent == effects_dir}
    return tuple(sorted(set(effects_dir.glob(EFFECT_SHARD_GLOB)) - expected))


def unexpected_event_paths(
    rendered: dict[Path, bytes], events_dir: Path | None = None
) -> tuple[Path, ...]:
    events_dir = events_dir or MOD_ROOT / "events"
    expected = {path for path in rendered if path.parent == events_dir}
    return tuple(sorted(set(events_dir.glob(EVENT_SHARD_GLOB)) - expected))


def print_effect_target_deviations() -> None:
    for group in effect_target_deviations():
        print(
            f"WARN: {group.filename} has {len(group.effect_names)} effects; "
            f"target is 1-{EFFECT_TARGET_MAX}"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = outputs()
    stale = [path for path, payload in rendered.items() if not path.is_file() or path.read_bytes() != payload]
    unexpected_effects = unexpected_effect_paths(rendered)
    unexpected_events = unexpected_event_paths(rendered)
    if args.check:
        if stale or unexpected_effects or unexpected_events:
            print("RED: stale Workforce attribution fact generated files:")
            for path in stale:
                print(path.relative_to(MOD_ROOT))
            for path in unexpected_effects:
                print(
                    f"{path.relative_to(MOD_ROOT)} "
                    "(unexpected effect shard or legacy monolith)"
                )
            for path in unexpected_events:
                print(
                    f"{path.relative_to(MOD_ROOT)} "
                    "(unexpected event shard or legacy monolith)"
                )
            return 1
        print(f"GREEN: {len(rendered)} Workforce attribution fact files are current ({READINESS})")
        print_effect_target_deviations()
        return 0
    for path in (*unexpected_effects, *unexpected_events):
        path.unlink()
    for path, payload in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print(f"GREEN: generated {len(rendered)} Workforce attribution fact runtime files")
    print_effect_target_deviations()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
