#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Authoritative B1 stage bindings for the 42-mechanism performance season.

This table is deliberately separate from readiness.  A row says where the
mechanism must execute and which gameplay record consumes its write; it does
not claim that the CK3 implementation or live acceptance is complete.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


STAGE_SEQUENCE: Final[tuple[str, ...]] = (
    "TARGETS_OPEN",
    "MIDCYCLE_OPEN",
    "PEER_OPEN",
    "FACTS_FROZEN",
    "SHADOW_OPEN",
    "QUOTA_READY",
    "CALIBRATION_OPEN",
    "PUBLISHED",
)


@dataclass(frozen=True)
class B1Binding:
    mechanism_id: int
    stage: str
    scope: str
    hook: str
    meaningful_write: str
    consumer: str


def _b(
    mechanism_id: int,
    stage: str,
    scope: str,
    hook: str,
    meaningful_write: str,
    consumer: str,
) -> B1Binding:
    return B1Binding(
        mechanism_id,
        stage,
        scope,
        hook,
        meaningful_write,
        consumer,
    )


B1_BINDINGS: Final[tuple[B1Binding, ...]] = (
    _b(1, "FACTS_FROZEN", "subject", "freeze_evidence_sheet", "immutable eight-part fact sheet", "KPI, statement and facts tab"),
    _b(2, "TARGETS_OPEN", "subject", "freeze_goal_contract", "goal direction, strength, baseline, weights and cap", "facts score explanation"),
    _b(3, "MIDCYCLE_OPEN", "subject", "midcycle_rebaseline", "old/new target version and support obligation", "final target interpretation"),
    _b(4, "PEER_OPEN", "subject", "submit_self_review", "sealed self score and representative evidence", "self-gap and visibility input"),
    _b(5, "TARGETS_OPEN", "subject", "freeze_role_scorecard", "role and scorecard version", "facts score weights"),
    _b(6, "TARGETS_OPEN", "subject", "freeze_difficulty_baseline", "raw/adjusted baseline and hard cap", "difficulty adjustment"),
    _b(7, "PEER_OPEN", "subject", "open_peer_slots", "three evaluator/subject/cycle slots", "peer aggregate"),
    _b(8, "FACTS_FROZEN", "evaluator", "normalize_evaluator", "raw/normalized score and evaluator credit", "peer aggregate weight"),
    _b(9, "CALIBRATION_OPEN", "manager", "record_atomic_swap", "calibration swap journal", "final grade and quota conservation"),
    _b(10, "CALIBRATION_OPEN", "manager", "record_bottom_protection", "C carrier, protected subject and paid protection cost", "final grade and next manager KPI"),
    _b(11, "CALIBRATION_OPEN", "superior", "record_skip_level_review", "one procedural return receipt", "publication gate"),
    _b(12, "CALIBRATION_OPEN", "manager", "freeze_conflict_recusal", "conflict, recusal and replacement seat", "grade-write ACL"),
    _b(13, "PUBLISHED", "manager", "project_disclosure_acl", "viewer mode and author ACL", "scoreboard/MCP projection"),
    _b(37, "QUOTA_READY", "superior", "settle_quota_trade", "creditor/debtor/due and opposite deltas", "quota allocation receipts"),
    _b(38, "QUOTA_READY", "superior", "pool_small_teams", "one pooled denominator and projected owners", "pooled ranks and quotas"),
    _b(39, "FACTS_FROZEN", "subject", "lock_cohort_membership", "owner/cycle/include reason and amendment", "quota denominator"),
    _b(40, "FACTS_FROZEN", "subject", "classify_leaver", "leaver/backfill route and manager responsibility", "quota eligibility and audit"),
    _b(41, "TARGETS_OPEN", "subject", "bind_newcomer_route", "protection/full/sacrifice route and mentor", "C eligibility"),
    _b(42, "FACTS_FROZEN", "subject", "audit_rotating_bottom", "three-cycle grade/rank/evidence history", "collusion audit consequence"),
    _b(43, "CALIBRATION_OPEN", "manager", "allocate_attention", "seat budget and displaced case", "swap eligibility and cost"),
    _b(44, "FACTS_FROZEN", "subject", "freeze_blind_named_diff", "blind and named ranks plus reason", "bias audit"),
    _b(45, "PUBLISHED", "subject", "detect_feedback_debt", "warning/ack/objection and debt", "manager next-cycle KPI and appeal"),
    _b(46, "MIDCYCLE_OPEN", "subject", "record_opportunity_grant", "project/resource/exposure grant", "bounded difficulty correction"),
    _b(47, "FACTS_FROZEN", "subject", "freeze_evidence_windows", "early/mid/late raw, weight and weighted sum", "KPI component"),
    _b(48, "PEER_OPEN", "evaluator", "reserve_peer_capacity", "cap/used/over-cap/fatigue", "peer weight and stress"),
    _b(49, "FACTS_FROZEN", "subject", "seal_peer_deadline", "submission/day/seal/timeliness", "edit guard and aggregate"),
    _b(50, "FACTS_FROZEN", "subject", "audit_reciprocity", "reciprocal evidence and symmetric weight delta", "peer aggregate and evaluator credit"),
    _b(51, "PUBLISHED", "subject", "project_anonymous_summary", "author count and threshold result", "viewer ACL"),
    _b(52, "FACTS_FROZEN", "subject", "compute_peer_shape", "mean, variance, role means and shape", "coaching and manager risk"),
    _b(53, "TARGETS_OPEN", "manager", "freeze_peer_use_mode", "development/pay mode and weight cap", "KPI inclusion boundary"),
    _b(135, "SHADOW_OPEN", "subject", "open_shadow_response", "shadow grade, notice and evidence deadline", "calibration input only"),
    _b(136, "QUOTA_READY", "superior", "run_pre_huddle", "3-4 manager attendance and suggested diff", "formal calibration comparison"),
    _b(137, "CALIBRATION_OPEN", "manager", "freeze_agenda", "unique case order and attention decay", "swap eligibility"),
    _b(138, "QUOTA_READY", "superior", "round_quota", "raw fractions, rounding, remainder and rotation", "exact three-grade counts"),
    _b(139, "QUOTA_READY", "superior", "settle_quota_debt", "borrowed slot, due cycle and one-shot settlement", "future quota bank"),
    _b(140, "FACTS_FROZEN", "subject", "freeze_reorg_owner", "old/new manager, service days and evidence segments", "single cohort ownership"),
    _b(141, "CALIBRATION_OPEN", "superior", "record_must_review", "one agenda insertion and attention debit", "independent review, never direct grade"),
    _b(142, "CALIBRATION_OPEN", "manager", "open_pending_milestone", "one pending subject, reserved slot and guarded deadline", "deferred final grade/payment"),
    _b(143, "PUBLISHED", "manager", "reopen_symmetric_case", "severity, old/new seal and one reopen receipt", "pre-payment result replacement"),
    _b(144, "CALIBRATION_OPEN", "manager", "record_dissent", "named subject, fact reason and attention debit", "independent re-review"),
    _b(145, "CALIBRATION_OPEN", "subject", "freeze_band_order", "within-band order and use mode", "coaching/opportunity only"),
    _b(357, "FACTS_FROZEN", "subject", "resolve_fact_then_quota", "fact close, quota snapshot, final reason and forced-down flag", "result statement and scoreboard"),
)

B1_IDS: Final[tuple[int, ...]] = tuple(row.mechanism_id for row in B1_BINDINGS)


def validate_b1_bindings() -> None:
    expected = (
        tuple(range(1, 14))
        + tuple(range(37, 54))
        + tuple(range(135, 146))
        + (357,)
    )
    if B1_IDS != expected:
        raise ValueError("B1 bindings must cover the exact 42-item batch in order")
    if len(set(B1_IDS)) != 42:
        raise ValueError("B1 mechanism ids must be unique")
    allowed_scopes = {"subject", "evaluator", "manager", "superior"}
    for row in B1_BINDINGS:
        if row.stage not in STAGE_SEQUENCE:
            raise ValueError(f"B1 mechanism {row.mechanism_id:03d} has an invalid stage")
        if row.scope not in allowed_scopes:
            raise ValueError(f"B1 mechanism {row.mechanism_id:03d} has an invalid scope")
        if not row.hook or not row.meaningful_write or not row.consumer:
            raise ValueError(f"B1 mechanism {row.mechanism_id:03d} has an empty runtime binding")


validate_b1_bindings()
