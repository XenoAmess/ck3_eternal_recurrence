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


CENTRAL_WIRING_BOUNDARY: Final = (
    "central-wired records committed hook reachability only; it does not prove "
    "complete per-ID semantics, a complete player-visible loop, or CK3 live acceptance"
)
LIVE_BOUNDARY: Final = (
    "ck3-live means bounded fixture-live evidence for the named slice; no mechanism "
    "is promoted here to production-live or full semantic completion"
)


CLAIMS: Final[tuple[ReadinessClaim, ...]] = (
    ReadinessClaim(
        mechanism_ids(range(242, 278), range(355, 357), range(360, 362)),
        ReadinessLevel.PYTHON_L0,
        "workforce-endgame-python-model",
        (
            "tools/zg361_phase3_workforce_endgame_model.py",
            "tools/test_zg361_phase3_workforce_endgame_model.py",
            "docs/361-phase3-workforce-endgame-runtime-spec.md",
        ),
        "Committed deterministic Python reference model; CK3 product projection is not counted.",
    ),
    ReadinessClaim(
        mechanism_ids(range(26, 32), range(54, 69), range(129, 135)),
        ReadinessLevel.CK3_STATIC_READY,
        "credit-project-ck3-runtime",
        (
            "tools/gen_361_credit_project_runtime.py",
            "tools/test_gen_361_credit_project_runtime.py",
            "docs/361-phase3-credit-project-ck3-runtime-spec.md",
        ),
        "Generated CK3 effects/events and L0 contracts exist; no central hook or live claim is counted.",
    ),
    ReadinessClaim(
        mechanism_ids(range(312, 334)),
        ReadinessLevel.PYTHON_L0,
        "manager-talent-python-model-remainder",
        (
            "tools/zg361_phase2_manager_talent_model.py",
            "tools/test_zg361_phase2_manager_talent_model.py",
        ),
        "Committed deterministic Python reference model; CK3 product projection is not counted.",
    ),
    ReadinessClaim(
        mechanism_ids(range(82, 92), range(278, 301)),
        ReadinessLevel.CK3_STATIC_READY,
        "compensation-lti-ck3-runtime",
        (
            "tools/gen_361_compensation_runtime.py",
            "tools/test_zg361_compensation_runtime.py",
            "docs/361-compensation-lti-ck3-runtime-spec.md",
        ),
        "Generated CK3 effects/events and L0 contracts exist; no central hook or live claim is counted.",
    ),
    ReadinessClaim(
        mechanism_ids(range(146, 157), range(181, 192)),
        ReadinessLevel.PYTHON_L0,
        "b2-reference-model-remainder",
        (
            "tools/zg361_b2_runtime_data.py",
            "tools/test_zg361_b2_runtime.py",
        ),
        "B2 reference contracts exist, but these IDs have no committed CK3 product projection.",
    ),
    ReadinessClaim(
        mechanism_ids(range(157, 181)),
        ReadinessLevel.PYTHON_L0,
        "career-panel-python-model-remainder",
        (
            "tools/zg361_phase2_career_model.py",
            "tools/test_zg361_phase2_career_model.py",
        ),
        "Promotion-panel Python semantics exist, but these IDs have no committed CK3 product projection.",
    ),
    ReadinessClaim(
        mechanism_ids(range(19, 26), range(92, 129)),
        ReadinessLevel.CK3_STATIC_READY,
        "career-hc-ck3-runtime",
        (
            "tools/gen_361_career_hc_runtime.py",
            "tools/test_zg361_career_hc_runtime.py",
            "docs/361-career-hc-ck3-runtime-spec.md",
        ),
        "Generated CK3 effects/events and L0 contracts exist; no central hook or live claim is counted.",
    ),
    ReadinessClaim(
        mechanism_ids(range(32, 37), range(345, 355)),
        ReadinessLevel.CK3_STATIC_READY,
        "manager-governance-ck3-runtime",
        (
            "tools/gen_361_manager_governance_runtime.py",
            "tools/test_zg361_manager_governance_runtime.py",
            "docs/361-phase2-manager-governance-ck3-runtime-spec.md",
        ),
        "Generated CK3 effects/events and L0 contracts exist; no central hook or live claim is counted.",
    ),
    ReadinessClaim(
        mechanism_ids(range(192, 229)),
        ReadinessLevel.CK3_STATIC_READY,
        "incident-platform-ck3-runtime",
        (
            "tools/gen_361_incident_platform_runtime.py",
            "tools/test_zg361_incident_platform_runtime.py",
            "docs/361-phase3-incident-platform-ck3-runtime-spec.md",
        ),
        "Generated CK3 effects/events and L0 contracts exist; no central hook or live claim is counted.",
    ),
    ReadinessClaim(
        mechanism_ids(range(229, 242), range(301, 312), range(334, 345)),
        ReadinessLevel.CK3_STATIC_READY,
        "metrics-delivery-ck3-runtime",
        (
            "tools/gen_361_phase3_metrics_delivery_runtime.py",
            "tools/test_zg361_phase3_metrics_delivery_runtime.py",
            "docs/361-phase3-metrics-delivery-runtime-spec.md",
        ),
        "Generated CK3 effects/events and L0 contracts exist; no central hook or live claim is counted.",
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
            "common/scripted_effects/zg361_effects.txt",
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
        "python-l0": "146-191, 242-277, 312-333, 355-356, 360-361",
        "ck3-static-ready": "019-036, 054-068, 082-134, 192-241, 278-311, 334-354",
        "central-wired": "002-017, 037-053, 070-081, 135-145, 358-359",
        "ck3-live": "001, 018, 069, 357",
    }
)
EXPECTED_CUMULATIVE_RANGES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "design-only": "001-361",
        "python-l0": "001-361",
        "ck3-static-ready": "001-145, 192-241, 278-311, 334-354, 357-359",
        "central-wired": "001-018, 037-053, 069-081, 135-145, 357-359",
        "ck3-live": "001, 018, 069, 357",
    }
)
EXPECTED_EXCLUSIVE_COUNTS: Final[Mapping[str, int]] = MappingProxyType(
    {
        "design-only": 0,
        "python-l0": 108,
        "ck3-static-ready": 191,
        "central-wired": 58,
        "ck3-live": 4,
    }
)
EXPECTED_CUMULATIVE_COUNTS: Final[Mapping[str, int]] = MappingProxyType(
    {
        "design-only": 361,
        "python-l0": 361,
        "ck3-static-ready": 253,
        "central-wired": 62,
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
    "MECHANISM_COUNT",
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
