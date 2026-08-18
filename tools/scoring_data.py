#!/usr/bin/env python3
"""Machine-authoritative scoring schema and offline reference model."""

from collections import deque
from dataclasses import dataclass, replace
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


def walk_descendant_graph(
        root: str,
        children: Mapping[str, Iterable[str]],
        people: Mapping[str, Descendant],
) -> tuple[Descendant, ...]:
    """Flatten a pedigree by shortest path while traversing through the dead."""
    queue = deque((key, 1) for key in children.get(root, ()))
    seen = set()
    result = []
    while queue:
        key, depth = queue.popleft()
        if key in seen or depth > DESCENDANT_DEPTH:
            continue
        seen.add(key)
        result.append(replace(people[key], depth=depth))
        queue.extend(
            (child, depth + 1) for child in children.get(key, ()))
    return tuple(result)


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
    (99, Decimal("1")),
    (100, Decimal("0")),
    (101, Decimal("0")),
)


def assert_reference_vectors() -> None:
    # These expectations are deliberately independent of the generation loops.
    # Any balance change must update this reviewed contract as a second action.
    expected_attributes = {
        "diplomacy": "1", "martial": "1", "stewardship": "1",
        "intrigue": "1", "learning": "1", "prowess": "1",
    }
    expected_resources = {
        "gold": "5", "prestige": "3", "piety": "3", "influence": "3",
    }
    expected_held = {
        "tier_county": "1", "tier_duchy": "2.5", "tier_kingdom": "5",
        "tier_empire": "10", "tier_hegemony": "20",
    }
    expected_descendant = {
        "tier_county": "0.25", "tier_duchy": "1", "tier_kingdom": "2.5",
        "tier_empire": "5", "tier_hegemony": "10",
    }
    actual_attributes = {rule.source: str(rule.coefficient) for rule in ATTRIBUTES}
    actual_resources = {rule.source: str(rule.coefficient) for rule in RESOURCES}
    actual_held = {rule.tier: str(rule.coefficient) for rule in HELD_TITLE_TIERS}
    actual_descendant = {
        rule.tier: str(rule.coefficient) for rule in DESCENDANT_TITLE_TIERS
    }
    if actual_attributes != expected_attributes:
        raise AssertionError(f"attribute coefficient contract: {actual_attributes}")
    if actual_resources != expected_resources:
        raise AssertionError(f"resource coefficient contract: {actual_resources}")
    if actual_held != expected_held:
        raise AssertionError(f"held-title coefficient contract: {actual_held}")
    if actual_descendant != expected_descendant:
        raise AssertionError(f"descendant-title coefficient contract: {actual_descendant}")
    scalar_contract = {
        "dynasty": DYNASTY_DESCENDANT_COEFFICIENT,
        "house": HOUSE_DESCENDANT_COEFFICIENT,
        "realm": REALM_SIZE_COEFFICIENT,
        "depth": DESCENDANT_DEPTH,
        "log_cap": LOG2_MAX_EXPONENT,
        "refusal": REFUSAL_MULTIPLIER_PER_COUNT,
        "contract": CONTRACT_PROGRESS_COEFFICIENT,
    }
    expected_scalars = {
        "dynasty": Decimal("0.1"), "house": Decimal("0.1"),
        "realm": Decimal("10"), "depth": 5, "log_cap": 30,
        "refusal": Decimal("0.01"), "contract": Decimal("10"),
    }
    if scalar_contract != expected_scalars:
        raise AssertionError(f"scalar scoring contract: {scalar_contract}")

    for source in (-100, -1, 0, 1):
        if floor_log2_capped(source) != 0:
            raise AssertionError(f"log2 lower boundary {source}")
    for exponent in range(1, 31):
        power = 2 ** exponent
        for source, expected in (
                (power - 1, exponent - 1),
                (power, exponent),
                (power + 1, exponent)):
            actual = floor_log2_capped(source)
            if actual != expected:
                raise AssertionError(
                    f"log2 boundary {source}: {actual} != {expected}")
    for source in (2 ** 31, 10 ** 20):
        if floor_log2_capped(source) != 30:
            raise AssertionError(f"log2 cap boundary {source}")

    for rule in ATTRIBUTES:
        actual = reference_score(attributes={rule.source: 1}).final
        if actual != rule.coefficient:
            raise AssertionError(f"attribute {rule.source}: {actual}")
    for rule in RESOURCES:
        actual = reference_score(resources={rule.source: 2}).final
        if actual != rule.coefficient:
            raise AssertionError(f"resource {rule.source}: {actual}")

    for tier, expected in HELD_TITLE_BOUNDARY_VECTORS:
        actual = reference_score(held_titles={tier: 1}).final
        if actual != expected:
            raise AssertionError(f"held title {tier}: {actual} != {expected}")
    for tier, expected in DESCENDANT_TITLE_BOUNDARY_VECTORS:
        descendant = Descendant(f"title-{tier}", 1, highest_title=tier)
        actual = reference_score(descendants=(descendant,)).final
        if actual != expected:
            raise AssertionError(f"descendant title {tier}: {actual} != {expected}")

    blood = reference_score(descendants=(
        Descendant("dynasty", 1, same_dynasty=True),
        Descendant("house", 1, same_dynasty=True, same_house=True),
    )).final
    if blood != Decimal("0.3"):
        raise AssertionError(f"descendant blood coefficients: {blood} != 0.3")
    depth_and_dedup = reference_score(descendants=(
        Descendant("depth-0", 0, same_dynasty=True),
        Descendant("depth-1", 1, same_dynasty=True),
        Descendant("depth-5", 5, same_dynasty=True),
        Descendant("depth-6", 6, same_dynasty=True),
        Descendant("duplicate", 2, same_dynasty=True, highest_title="tier_empire"),
        Descendant("duplicate", 3, same_dynasty=True, highest_title="tier_empire"),
        Descendant("dead", 2, same_dynasty=True, highest_title="tier_hegemony", alive=False),
    )).final
    if depth_and_dedup != Decimal("5.3"):
        raise AssertionError(
            f"descendant depth/dedup contract: {depth_and_dedup} != 5.3")

    people = {
        key: Descendant(key, 0, same_dynasty=True, alive=key != "dead-parent")
        for key in ("left", "right", "shared", "dead-parent", "living-grandchild",
                    "d3", "d4", "d5", "d6")
    }
    graph = {
        "root": ("left", "right", "dead-parent"),
        "left": ("shared",),
        "right": ("shared",),
        "dead-parent": ("living-grandchild",),
        "living-grandchild": ("d3",),
        "d3": ("d4",),
        "d4": ("d5",),
        "d5": ("d6",),
    }
    walked = walk_descendant_graph("root", graph, people)
    depths = {person.key: person.depth for person in walked}
    expected_depths = {
        "left": 1, "right": 1, "dead-parent": 1, "shared": 2,
        "living-grandchild": 2, "d3": 3, "d4": 4, "d5": 5,
    }
    if depths != expected_depths:
        raise AssertionError(f"pedigree traversal: {depths} != {expected_depths}")
    graph_score = reference_score(descendants=walked).final
    if graph_score != Decimal("0.7"):
        raise AssertionError(
            f"dead-intermediate pedigree score: {graph_score} != 0.7")

    mixed_titles = reference_score(held_titles={
        "tier_county": 2, "tier_duchy": 1, "tier_kingdom": 1,
        "tier_empire": 1, "tier_hegemony": 1,
    }).final
    if mixed_titles != Decimal("39.5"):
        raise AssertionError(f"mixed held titles: {mixed_titles} != 39.5")
    for landed, size, expected in (
            (False, 1024, 0), (True, 0, 0), (True, 1, 0),
            (True, 2, 10), (True, 1024, 100)):
        actual = reference_score(landed=landed, realm_size=size).final
        if actual != expected:
            raise AssertionError(f"realm boundary {landed}/{size}: {actual} != {expected}")
    for progress, expected in (
            (-1, 0), (0, 0), (1, 10), (9, 90), (10, 100), (11, 100)):
        actual = reference_score(contract_progress=progress).final
        if actual != expected:
            raise AssertionError(
                f"contract boundary {progress}: {actual} != {expected}")

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

    golden = reference_score(
        attributes={rule.source: index for index, rule in enumerate(ATTRIBUTES, 1)},
        resources={"gold": 8, "prestige": 4, "piety": 2, "influence": 1},
        held_titles={
            "tier_county": 2, "tier_duchy": 1, "tier_kingdom": 1,
            "tier_empire": 1, "tier_hegemony": 1,
        },
        descendants=(
            Descendant("county-house", 1, True, True, "tier_county"),
            Descendant("empire-dynasty", 2, True, False, "tier_empire"),
        ),
        realm_size=8,
        landed=True,
        contract_progress=9,
    )
    if golden != ScoreResult(Decimal("210.05"), Decimal("210.05"), Decimal("210.05")):
        raise AssertionError(f"golden mixed score: {golden}")
