#!/usr/bin/env python3
"""Machine-authoritative scoring schema and offline reference model."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Mapping


@dataclass(frozen=True)
class AttributeRule:
    source: str
    suffix: str
    label: str
    coefficient: Decimal


@dataclass(frozen=True)
class ResourceRule:
    source: str
    suffix: str
    label: str
    coefficient: Decimal


@dataclass(frozen=True)
class TitleRule:
    key: str
    tier: str
    label: str
    coefficient: Decimal


@dataclass(frozen=True)
class Descendant:
    key: str
    depth: int
    same_dynasty: bool = False
    same_house: bool = False
    highest_title: str | None = None
    alive: bool = True


@dataclass(frozen=True)
class ScoreResult:
    subtotal: Decimal
    final: Decimal
    absolute_subtotal: Decimal


def decimal(value: int | float | str | Decimal) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


ATTRIBUTES = (
    AttributeRule("diplomacy", "dip", "外交", Decimal("1")),
    AttributeRule("martial", "mar", "军事", Decimal("1")),
    AttributeRule("stewardship", "ste", "管理", Decimal("1")),
    AttributeRule("intrigue", "int", "谋略", Decimal("1")),
    AttributeRule("learning", "lea", "学识", Decimal("1")),
    AttributeRule("prowess", "pro", "勇武", Decimal("1")),
)

RESOURCES = (
    ResourceRule("gold", "gold", "金钱", Decimal("5")),
    ResourceRule("prestige", "pres", "威望", Decimal("3")),
    ResourceRule("piety", "pie", "虔诚", Decimal("3")),
    ResourceRule("influence", "inf", "影响力", Decimal("3")),
)

HELD_TITLE_TIERS = (
    TitleRule("t1", "tier_county", "伯爵级", Decimal("1")),
    TitleRule("t2", "tier_duchy", "公国级", Decimal("2.5")),
    TitleRule("t3", "tier_kingdom", "王国级", Decimal("5")),
    TitleRule("t4", "tier_empire", "帝国级", Decimal("10")),
    TitleRule("t5", "tier_hegemony", "霸权级", Decimal("20")),
)

DESCENDANT_TITLE_TIERS = (
    TitleRule("t1", "tier_county", "伯爵级", Decimal("0.25")),
    TitleRule("t2", "tier_duchy", "公国级", Decimal("1")),
    TitleRule("t3", "tier_kingdom", "王国级", Decimal("2.5")),
    TitleRule("t4", "tier_empire", "帝国级", Decimal("5")),
    TitleRule("t5", "tier_hegemony", "霸权级", Decimal("10")),
)

DYNASTY_DESCENDANT_COEFFICIENT = Decimal("0.1")
HOUSE_DESCENDANT_COEFFICIENT = Decimal("0.1")
REALM_SIZE_COEFFICIENT = Decimal("10")
DESCENDANT_DEPTH = 5
LOG2_MAX_EXPONENT = 30
REFUSAL_MULTIPLIER_PER_COUNT = Decimal("0.01")
CONTRACT_PROGRESS_COEFFICIENT = Decimal("10")


def floor_log2_capped(value: int | float | str | Decimal) -> int:
    """Mirror the generated CK3 power ladder, including its exponent cap."""
    value = decimal(value)
    result = 0
    for exponent in range(1, LOG2_MAX_EXPONENT + 1):
        if value >= 2 ** exponent:
            result += 1
    return result


def reference_score(
        *,
        attributes: Mapping[str, int | float | str | Decimal] | None = None,
        resources: Mapping[str, int | float | str | Decimal] | None = None,
        held_titles: Mapping[str, int] | None = None,
        descendants: Iterable[Descendant] = (),
        realm_size: int | float | str | Decimal = 0,
        landed: bool = False,
        refusals: int = 0,
        basis: str = "absolute",
        baseline_subtotal: int | float | str | Decimal = 0,
        contract_progress: int = 0,
) -> ScoreResult:
    """Calculate production-equivalent subtotal and final score without CK3."""
    attributes = attributes or {}
    resources = resources or {}
    held_titles = held_titles or {}
    subtotal = Decimal("0")

    for rule in ATTRIBUTES:
        subtotal += decimal(attributes.get(rule.source, 0)) * rule.coefficient
    for rule in RESOURCES:
        subtotal += floor_log2_capped(resources.get(rule.source, 0)) * rule.coefficient
    for rule in HELD_TITLE_TIERS:
        subtotal += held_titles.get(rule.tier, 0) * rule.coefficient

    descendant_titles = {rule.tier: rule.coefficient for rule in DESCENDANT_TITLE_TIERS}
    seen = set()
    for descendant in descendants:
        if (not descendant.alive or descendant.depth < 1
                or descendant.depth > DESCENDANT_DEPTH or descendant.key in seen):
            continue
        seen.add(descendant.key)
        if descendant.same_dynasty:
            subtotal += DYNASTY_DESCENDANT_COEFFICIENT
        if descendant.same_house:
            subtotal += HOUSE_DESCENDANT_COEFFICIENT
        subtotal += descendant_titles.get(descendant.highest_title, Decimal("0"))

    if landed:
        subtotal += floor_log2_capped(realm_size) * REALM_SIZE_COEFFICIENT
    subtotal += max(0, min(10, contract_progress)) * CONTRACT_PROGRESS_COEFFICIENT

    absolute_subtotal = subtotal
    if basis == "growth":
        subtotal = max(Decimal("0"), subtotal - decimal(baseline_subtotal))
    elif basis != "absolute":
        raise ValueError(f"unknown score basis: {basis}")

    multiplier = max(
        Decimal("0"),
        Decimal("1") - max(0, refusals) * REFUSAL_MULTIPLIER_PER_COUNT,
    )
    return ScoreResult(
        subtotal=subtotal,
        final=subtotal * multiplier,
        absolute_subtotal=absolute_subtotal,
    )


LOG2_BOUNDARY_VECTORS = ((0, 0), (1, 0), (2, 1), (3, 1), (4, 2))
HELD_TITLE_BOUNDARY_VECTORS = (
    ("tier_county", Decimal("1")),
    ("tier_duchy", Decimal("2.5")),
    ("tier_kingdom", Decimal("5")),
    ("tier_empire", Decimal("10")),
    ("tier_hegemony", Decimal("20")),
)
DESCENDANT_TITLE_BOUNDARY_VECTORS = (
    ("tier_county", Decimal("0.25")),
    ("tier_duchy", Decimal("1")),
    ("tier_kingdom", Decimal("2.5")),
    ("tier_empire", Decimal("5")),
    ("tier_hegemony", Decimal("10")),
)
REFUSAL_BOUNDARY_VECTORS = (
    (0, Decimal("100")),
    (1, Decimal("99")),
    (100, Decimal("0")),
)


def assert_reference_vectors() -> None:
    for source, expected in LOG2_BOUNDARY_VECTORS:
        actual = floor_log2_capped(source)
        if actual != expected:
            raise AssertionError(f"log2 boundary {source}: {actual} != {expected}")

    for tier, expected in HELD_TITLE_BOUNDARY_VECTORS:
        actual = reference_score(held_titles={tier: 1}).final
        if actual != expected:
            raise AssertionError(f"held title {tier}: {actual} != {expected}")
    for tier, expected in DESCENDANT_TITLE_BOUNDARY_VECTORS:
        descendant = Descendant(f"title-{tier}", 1, highest_title=tier)
        actual = reference_score(descendants=(descendant,)).final
        if actual != expected:
            raise AssertionError(f"descendant title {tier}: {actual} != {expected}")

    for refusals, expected in REFUSAL_BOUNDARY_VECTORS:
        actual = reference_score(attributes={"diplomacy": 100}, refusals=refusals).final
        if actual != expected:
            raise AssertionError(
                f"refusal boundary {refusals}: {actual} != {expected}")

    for baseline, current, expected in ((100, 130, 30), (100, 90, 0), (100, 100, 0)):
        actual = reference_score(
            attributes={"diplomacy": current},
            basis="growth",
            baseline_subtotal=baseline,
        ).final
        if actual != expected:
            raise AssertionError(f"growth {baseline}->{current}: {actual} != {expected}")
    penalized = reference_score(
        attributes={"diplomacy": 130},
        basis="growth",
        baseline_subtotal=100,
        refusals=1,
    ).final
    if penalized != Decimal("29.7"):
        raise AssertionError(f"growth refusal: {penalized} != 29.7")
    contract = reference_score(contract_progress=10).final
    if contract != Decimal("100"):
        raise AssertionError(f"contract progress: {contract} != 100")
