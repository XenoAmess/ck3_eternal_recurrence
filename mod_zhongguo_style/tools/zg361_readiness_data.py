#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Authoritative per-mechanism readiness ledger for Zhongguo 361.

This module records the highest evidence tier reached by every mechanism ID.
It deliberately does not discover files at runtime: an uncommitted generated
file in a dirty worktree must never promote readiness.  Update these explicit
claims only after the named package is committed to ``master`` and reviewed at
the stated boundary.

The generic 361 policy cards and aggregate organization-ledger fixture are not
domain-runtime evidence.  ``central-wired`` means only that a committed central
product hook reaches the package; it is not full semantic completion.  The
highest tier here is bounded CK3 fixture evidence, never production-live.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from types import MappingProxyType
from typing import Final, Iterable, Mapping


MECHANISM_COUNT: Final = 361


class ReadinessLevel(IntEnum):
    """Ordered, mutually exclusive highest-evidence tiers."""

    DESIGN_ONLY = 0
    PYTHON_L0 = 1
    CK3_STATIC_READY = 2
    CENTRAL_WIRED = 3
    CK3_LIVE = 4

    @property
    def key(self) -> str:
        return {
            ReadinessLevel.DESIGN_ONLY: "design-only",
            ReadinessLevel.PYTHON_L0: "python-l0",
            ReadinessLevel.CK3_STATIC_READY: "ck3-static-ready",
            ReadinessLevel.CENTRAL_WIRED: "central-wired",
            ReadinessLevel.CK3_LIVE: "ck3-live",
        }[self]


LEVELS: Final = tuple(ReadinessLevel)
LEVEL_BY_KEY: Final[Mapping[str, ReadinessLevel]] = MappingProxyType(
    {level.key: level for level in LEVELS}
)


def mechanism_ids(*parts: int | range) -> tuple[int, ...]:
    """Flatten explicit IDs/ranges while retaining declaration order."""

    result: list[int] = []
    for part in parts:
        if isinstance(part, range):
            result.extend(part)
        elif isinstance(part, int) and not isinstance(part, bool):
            result.append(part)
        else:
            raise TypeError(f"unsupported mechanism ID declaration: {part!r}")
    return tuple(result)


@dataclass(frozen=True, slots=True)
class ReadinessClaim:
    ids: tuple[int, ...]
    level: ReadinessLevel
    package: str
    evidence: tuple[str, ...]
    note: str


@dataclass(frozen=True, slots=True)
class ReadinessRecord:
    mechanism_id: int
    level: ReadinessLevel
    package: str
    evidence: tuple[str, ...]
    note: str

    def manifest_payload(self) -> dict[str, object]:
        return {
            "highest_level": self.level.key,
            "ordinal": int(self.level),
            "package": self.package,
            "evidence": list(self.evidence),
            "note": self.note,
            "cumulative_gates": {
                level.key: self.level >= level for level in LEVELS
            },
        }


@dataclass(frozen=True, slots=True)
class ProductAcceptanceSnapshot:
    """Latest whole-product run, kept separate from per-ID readiness claims."""

    run_id: str
    observed_at: str
    result: str
    product_commit: str
    projection: str
    verified_file_count: int
    product_tree_sha256: str
    release_manifest_sha256: str
    loader_database_nodes: int
    loader_fatal_count: int
    speed: int
    observation_days: int
    native_observations: int
    drained_event_keys: tuple[str, ...]
    cleared_product_signatures: tuple[str, ...]
    evidence: tuple[str, ...]
    boundary: str


CENTRAL_WIRING_BOUNDARY: Final = (
    "central-wired records committed hook reachability only; it does not prove "
    "complete per-ID semantics, a complete player-visible loop, or CK3 live acceptance"
)
CORE_EFFECT_EVIDENCE: Final = (
    "common/scripted_effects/zg361_core_review_cycle_effects.txt",
    "common/scripted_effects/zg361_core_result_delivery_effects.txt",
    "common/scripted_effects/zg361_core_appeal_scoreboard_effects.txt",
    "common/scripted_effects/zg361_core_elimination_effects.txt",
)
CENTRAL_RUNTIME_EVIDENCE: Final = (
    "tools/gen_361_phase2_central_runtime.py",
    "tools/test_zg361_phase2_central_runtime.py",
    "docs/361-phase2-central-runtime-spec.md",
    *CORE_EFFECT_EVIDENCE,
)
CENTRAL_CONDITIONAL_EXTERNAL_WAIT_BOUNDARY: Final = (
    "central-wired records committed reachability to the Workforce adapter and its "
    "typed external-wait/resume seam; #360-361 remain conditional on real 357-359 "
    "receipts and are not central-completable, CK3 live, or complete"
)
LIVE_BOUNDARY: Final = (
    "ck3-live means bounded fixture-live evidence for the named slice; no mechanism "
    "is promoted here to production-live or full semantic completion"
)

LATEST_PRODUCT_ACCEPTANCE: Final = ProductAcceptanceSnapshot(
    run_id="R99",
    observed_at="2026-09-06 00:18 Asia/Shanghai",
    result="RED",
    product_commit="2d45678",
    projection="phase2-full-release-r99-2d45678",
    verified_file_count=937,
    product_tree_sha256="1C69EC7277F144E90EE4CB337F5C952EEECC40E5E099555B206F517D6C7D689E",
    release_manifest_sha256="A27E3A87F15957070FDE15C43662200EE42876121B7D5648631AFEDD5564F21C",
    loader_database_nodes=303,
    loader_fatal_count=0,
    speed=5,
    observation_days=966,
    native_observations=239,
    drained_event_keys=(
        "zg361b2.40",
        "spymaster_task.0381",
        "zg361.40",
        "ep3_governor_yearly.3060",
        "spymaster_task.0381",
        "spymaster_task.0381",
        "zg361.40",
        "tgp_dynastic_cycle_events.0040",
        "zg361b1.200",
        "zg361b1.201",
        "zg361b1.126",
        "zg361.40",
    ),
    cleared_product_signatures=(
        "Unknown effect: has_variable (R98 compensation portfolio dispatch)",
        "loader-attributed project errors",
    ),
    evidence=(
        "docs/phase2-promo/promotion-source-checkpoint-choreography-forensics-2026-09-04.md",
        "docs/phase2-promo/phase2-acceptance-case-index.md",
        r"Z:\b3r99_retry1\evidence-index.json",
        r"Z:\b3r99_retry1\cell\02_loader_error_scan.json",
        r"Z:\b3r99_retry1\cell\03_promotion_source_production_entry.json",
        r"Z:\b3r99_resume1\03_promotion_source_production_entry.json",
        r"Z:\b3r99_retry1_native_state\profile\logs\error.log",
        r"Z:\b3r99_retry1_native_state\profile\logs\debug.log",
    ),
    boundary=(
        "The committed R99 release-identical product loaded 303/303 database nodes with "
        "fatal 0 and zero loader-attributed project errors. One retained CK3 PID advanced "
        "from date_raw 53147016 to 53170200 at speed 5 across 239 paused observations and "
        "12 exact event drains. The first client stopped only because the exact same "
        "spymaster_task.0381 appeared a third time; the harness contract was widened from "
        "two to the three live-observed occurrences and the same PID resumed without a "
        "restart. A fresh player B1 cycle then consumed zg361b1.200, .201 and .126. The "
        "resume bound ended only 217 game days after that fresh cycle opened, before its "
        "authored D+300 boundary, so it is not evidence that the cycle is stuck. Runtime "
        "logs nevertheless exposed four product regressions: a weak archived manager "
        "write, deferred compensation against missing payer-share fields and a dead payer, "
        "jingcha opinion against a dead superior, and delayed promotion receipt revision "
        "increments before first initialization. Their minimal source fixes are "
        "static-ready for R100 and require a fresh process because mod bytes changed. "
        "This was not an illness-death failure; the consecutive counter remains 0/3 and "
        "no health or survivability fixture was applied. This whole-product RED does not "
        "promote any per-ID tier."
    ),
)


CLAIMS: Final[tuple[ReadinessClaim, ...]] = (
    ReadinessClaim(
        mechanism_ids(range(242, 278), range(355, 357)),
        ReadinessLevel.CENTRAL_WIRED,
        "workforce-endgame-ck3-runtime",
        (
            "tools/gen_361_workforce_endgame_runtime.py",
            "tools/test_zg361_workforce_endgame_runtime.py",
            "docs/361-workforce-endgame-ck3-runtime-spec.md",
        ) + CENTRAL_RUNTIME_EVIDENCE,
        CENTRAL_WIRING_BOUNDARY,
    ),
    ReadinessClaim(
        mechanism_ids(range(360, 362)),
        ReadinessLevel.CENTRAL_WIRED,
        "workforce-endgame-conditional-external-wait",
        (
            "tools/gen_361_workforce_endgame_runtime.py",
            "tools/test_zg361_workforce_endgame_runtime.py",
            "docs/361-workforce-endgame-ck3-runtime-spec.md",
        ) + CENTRAL_RUNTIME_EVIDENCE,
        CENTRAL_CONDITIONAL_EXTERNAL_WAIT_BOUNDARY,
    ),
    ReadinessClaim(
        mechanism_ids(range(26, 32), range(54, 69), range(129, 135)),
        ReadinessLevel.CENTRAL_WIRED,
        "credit-project-ck3-runtime",
        (
            "tools/gen_361_credit_project_runtime.py",
            "tools/test_gen_361_credit_project_runtime.py",
            "docs/361-phase3-credit-project-ck3-runtime-spec.md",
        ) + CENTRAL_RUNTIME_EVIDENCE,
        CENTRAL_WIRING_BOUNDARY,
    ),
    ReadinessClaim(
        mechanism_ids(range(312, 334)),
        ReadinessLevel.CENTRAL_WIRED,
        "career-learning-ck3-runtime",
        (
            "tools/gen_361_career_learning_runtime.py",
            "tools/test_zg361_career_learning_runtime.py",
            "docs/361-phase2-career-learning-ck3-runtime-spec.md",
        ) + CENTRAL_RUNTIME_EVIDENCE,
        CENTRAL_WIRING_BOUNDARY,
    ),
    ReadinessClaim(
        mechanism_ids(range(82, 92), range(278, 301)),
        ReadinessLevel.CENTRAL_WIRED,
        "compensation-lti-ck3-runtime",
        (
            "tools/gen_361_compensation_runtime.py",
            "tools/test_zg361_compensation_runtime.py",
            "docs/361-compensation-lti-ck3-runtime-spec.md",
        ) + CENTRAL_RUNTIME_EVIDENCE,
        CENTRAL_WIRING_BOUNDARY,
    ),
    ReadinessClaim(
        mechanism_ids(range(146, 192)),
        ReadinessLevel.CENTRAL_WIRED,
        "feedback-promotion-pip-ck3-runtime",
        (
            "tools/gen_361_feedback_promotion_pip_runtime.py",
            "tools/test_zg361_feedback_promotion_pip_runtime.py",
            "docs/361-feedback-promotion-pip-ck3-runtime-spec.md",
        ) + CENTRAL_RUNTIME_EVIDENCE,
        CENTRAL_WIRING_BOUNDARY,
    ),
    ReadinessClaim(
        mechanism_ids(range(19, 26), range(92, 129)),
        ReadinessLevel.CENTRAL_WIRED,
        "career-hc-ck3-runtime",
        (
            "tools/gen_361_career_hc_runtime.py",
            "tools/test_zg361_career_hc_runtime.py",
            "docs/361-career-hc-ck3-runtime-spec.md",
        ) + CENTRAL_RUNTIME_EVIDENCE,
        CENTRAL_WIRING_BOUNDARY,
    ),
    ReadinessClaim(
        mechanism_ids(range(32, 37), range(345, 355)),
        ReadinessLevel.CENTRAL_WIRED,
        "manager-governance-ck3-runtime",
        (
            "tools/gen_361_manager_governance_runtime.py",
            "tools/test_zg361_manager_governance_runtime.py",
            "docs/361-phase2-manager-governance-ck3-runtime-spec.md",
        ) + CENTRAL_RUNTIME_EVIDENCE,
        CENTRAL_WIRING_BOUNDARY,
    ),
    ReadinessClaim(
        mechanism_ids(range(192, 229)),
        ReadinessLevel.CENTRAL_WIRED,
        "incident-platform-ck3-runtime",
        (
            "tools/gen_361_incident_platform_runtime.py",
            "tools/test_zg361_incident_platform_runtime.py",
            "docs/361-phase3-incident-platform-ck3-runtime-spec.md",
        ) + CENTRAL_RUNTIME_EVIDENCE,
        CENTRAL_WIRING_BOUNDARY,
    ),
    ReadinessClaim(
        mechanism_ids(range(229, 242), range(301, 312), range(334, 345)),
        ReadinessLevel.CENTRAL_WIRED,
        "metrics-delivery-ck3-runtime",
        (
            "tools/gen_361_phase3_metrics_delivery_runtime.py",
            "tools/test_zg361_phase3_metrics_delivery_runtime.py",
            "docs/361-phase3-metrics-delivery-runtime-spec.md",
        ) + CENTRAL_RUNTIME_EVIDENCE,
        CENTRAL_WIRING_BOUNDARY,
    ),
    ReadinessClaim(
        mechanism_ids(range(2, 14), range(37, 54), range(135, 146)),
        ReadinessLevel.CENTRAL_WIRED,
        "b1-performance-season-runtime",
        (
            "tools/zg361_b1_runtime_data.py",
            "tools/gen_361_b1_runtime.py",
            "tools/test_zg361_b1_runtime.py",
            "docs/361-b1-runtime-spec.md",
        ),
        CENTRAL_WIRING_BOUNDARY,
    ),
    ReadinessClaim(
        mechanism_ids(range(14, 18), range(70, 82), range(358, 360)),
        ReadinessLevel.CENTRAL_WIRED,
        "b2-delivery-appeal-runtime",
        (
            "tools/gen_361_b2_runtime.py",
            "tools/test_gen_361_b2_runtime.py",
            *CORE_EFFECT_EVIDENCE,
        ),
        CENTRAL_WIRING_BOUNDARY,
    ),
    ReadinessClaim(
        mechanism_ids(1, 357),
        ReadinessLevel.CK3_LIVE,
        "first-slice-facts-quota-live",
        ("docs/phase2-slice-001-018-069-357.md",),
        "Bounded fixture-live covers frozen facts and fact-versus-quota reasons only; broader semantics remain incomplete.",
    ),
    ReadinessClaim(
        mechanism_ids(69),
        ReadinessLevel.CK3_LIVE,
        "first-slice-delivery-live",
        ("docs/phase2-slice-001-018-069-357.md",),
        "Bounded fixture-live covers refusal, D+7 witnessed delivery, and the same-case receipt path.",
    ),
    ReadinessClaim(
        mechanism_ids(18),
        ReadinessLevel.CK3_LIVE,
        "first-slice-settlement-live",
        ("docs/phase2-slice-001-018-069-357.md",),
        "Only receipt/refund behavior is fixture-live; reopening zg361.53 remains CK3 static-ready.",
    ),
)


def _build_records() -> Mapping[int, ReadinessRecord]:
    records: dict[int, ReadinessRecord] = {}
    for claim in CLAIMS:
        if not claim.ids or not claim.evidence:
            raise ValueError(f"readiness claim {claim.package!r} is incomplete")
        for mechanism_id in claim.ids:
            if isinstance(mechanism_id, bool) or not 1 <= mechanism_id <= MECHANISM_COUNT:
                raise ValueError(f"invalid readiness mechanism ID: {mechanism_id!r}")
            if mechanism_id in records:
                raise ValueError(f"mechanism {mechanism_id:03d} has multiple readiness claims")
            records[mechanism_id] = ReadinessRecord(
                mechanism_id,
                claim.level,
                claim.package,
                claim.evidence,
                claim.note,
            )
    expected = set(range(1, MECHANISM_COUNT + 1))
    if set(records) != expected:
        missing = sorted(expected - set(records))
        extra = sorted(set(records) - expected)
        raise ValueError(f"readiness ledger is not exact; missing={missing}, extra={extra}")
    return MappingProxyType(dict(sorted(records.items())))


READINESS_BY_ID: Final = _build_records()


def ids_at_level(level: ReadinessLevel) -> tuple[int, ...]:
    return tuple(
        mechanism_id
        for mechanism_id, record in READINESS_BY_ID.items()
        if record.level is level
    )


def ids_at_least(level: ReadinessLevel) -> tuple[int, ...]:
    return tuple(
        mechanism_id
        for mechanism_id, record in READINESS_BY_ID.items()
        if record.level >= level
    )


def compress_ranges(ids: Iterable[int]) -> tuple[tuple[int, int], ...]:
    ordered = tuple(sorted(set(ids)))
    if not ordered:
        return ()
    result: list[tuple[int, int]] = []
    first = last = ordered[0]
    for mechanism_id in ordered[1:]:
        if mechanism_id == last + 1:
            last = mechanism_id
            continue
        result.append((first, last))
        first = last = mechanism_id
    result.append((first, last))
    return tuple(result)


def format_ranges(ids: Iterable[int]) -> str:
    return ", ".join(
        f"{first:03d}" if first == last else f"{first:03d}-{last:03d}"
        for first, last in compress_ranges(ids)
    )


EXCLUSIVE_COUNTS: Final[Mapping[str, int]] = MappingProxyType(
    {level.key: len(ids_at_level(level)) for level in LEVELS}
)
CUMULATIVE_COUNTS: Final[Mapping[str, int]] = MappingProxyType(
    {level.key: len(ids_at_least(level)) for level in LEVELS}
)

EXPECTED_EXCLUSIVE_RANGES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "design-only": "",
        "python-l0": "",
        "ck3-static-ready": "",
        "central-wired": "002-017, 019-068, 070-356, 358-361",
        "ck3-live": "001, 018, 069, 357",
    }
)
EXPECTED_CUMULATIVE_RANGES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "design-only": "001-361",
        "python-l0": "001-361",
        "ck3-static-ready": "001-361",
        "central-wired": "001-361",
        "ck3-live": "001, 018, 069, 357",
    }
)
EXPECTED_EXCLUSIVE_COUNTS: Final[Mapping[str, int]] = MappingProxyType(
    {
        "design-only": 0,
        "python-l0": 0,
        "ck3-static-ready": 0,
        "central-wired": 357,
        "ck3-live": 4,
    }
)
EXPECTED_CUMULATIVE_COUNTS: Final[Mapping[str, int]] = MappingProxyType(
    {
        "design-only": 361,
        "python-l0": 361,
        "ck3-static-ready": 361,
        "central-wired": 361,
        "ck3-live": 4,
    }
)


def validate_readiness() -> None:
    if tuple(READINESS_BY_ID) != tuple(range(1, MECHANISM_COUNT + 1)):
        raise ValueError("readiness IDs must be exactly 001-361 in order")
    if tuple(level.key for level in LEVELS) != tuple(LEVEL_BY_KEY):
        raise ValueError("readiness level keys are not ordered")
    exclusive_ranges = {
        level.key: format_ranges(ids_at_level(level)) for level in LEVELS
    }
    cumulative_ranges = {
        level.key: format_ranges(ids_at_least(level)) for level in LEVELS
    }
    if exclusive_ranges != dict(EXPECTED_EXCLUSIVE_RANGES):
        raise ValueError(f"exclusive readiness range drift: {exclusive_ranges!r}")
    if cumulative_ranges != dict(EXPECTED_CUMULATIVE_RANGES):
        raise ValueError(f"cumulative readiness range drift: {cumulative_ranges!r}")
    if dict(EXCLUSIVE_COUNTS) != dict(EXPECTED_EXCLUSIVE_COUNTS):
        raise ValueError(f"exclusive readiness count drift: {dict(EXCLUSIVE_COUNTS)!r}")
    if dict(CUMULATIVE_COUNTS) != dict(EXPECTED_CUMULATIVE_COUNTS):
        raise ValueError(f"cumulative readiness count drift: {dict(CUMULATIVE_COUNTS)!r}")
    cumulative = tuple(CUMULATIVE_COUNTS[level.key] for level in LEVELS)
    if any(left < right for left, right in zip(cumulative, cumulative[1:])):
        raise ValueError("readiness cumulative gates are not monotonic")


validate_readiness()


__all__ = [
    "CENTRAL_WIRING_BOUNDARY",
    "CENTRAL_CONDITIONAL_EXTERNAL_WAIT_BOUNDARY",
    "CENTRAL_RUNTIME_EVIDENCE",
    "CLAIMS",
    "CUMULATIVE_COUNTS",
    "EXPECTED_CUMULATIVE_COUNTS",
    "EXPECTED_CUMULATIVE_RANGES",
    "EXPECTED_EXCLUSIVE_COUNTS",
    "EXPECTED_EXCLUSIVE_RANGES",
    "EXCLUSIVE_COUNTS",
    "LEVELS",
    "LEVEL_BY_KEY",
    "LIVE_BOUNDARY",
    "LATEST_PRODUCT_ACCEPTANCE",
    "MECHANISM_COUNT",
    "ProductAcceptanceSnapshot",
    "READINESS_BY_ID",
    "ReadinessClaim",
    "ReadinessLevel",
    "ReadinessRecord",
    "compress_ranges",
    "format_ranges",
    "ids_at_least",
    "ids_at_level",
    "validate_readiness",
]
