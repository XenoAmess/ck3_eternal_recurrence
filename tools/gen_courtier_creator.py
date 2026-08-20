#!/usr/bin/env python3
"""Generate courtier creator trait catalogs from checked-in vanilla metadata."""

from __future__ import annotations

import argparse
import codecs
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MOD = ROOT / "XenoAmess_s_Eternal_Recurrence"
SNAPSHOT = Path(__file__).resolve().with_name("courtier_traits_1_19_0_6.json")
HEADER = (
    "# GENERATED FILE - do not edit. Regenerate with "
    "tools/gen_courtier_creator.py"
)
CATALOG_NAMES = ("education", "commander", "physical", "personality", "other")
EXPECTED_COUNTS = {
    "education": 25,
    "commander": 17,
    "physical": 38,
    "personality": 36,
    "other": 108,
}
EXPECTED_UNION_COUNT = 224
EXPECTED_VISIBLE_COUNT = 223
OUTPUTS = {
    MOD
    / "common/scripted_effects/xar_generated_courtier_catalog_effects.txt": "effects",
    MOD
    / "common/scripted_triggers/xar_generated_courtier_catalog_triggers.txt": "triggers",
    MOD
    / "common/script_values/xar_generated_courtier_catalog_values.txt": "values",
}
REQUIRED_TRAIT_FIELDS = {
    "key",
    "category",
    "physical",
    "shown_in_ruler_designer",
    "ruler_designer_cost",
    "minimum_age",
    "maximum_age",
    "valid_sex",
    "group",
    "group_equivalence",
    "opposites",
    "level",
    "has_track",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def is_optional_string(value: object) -> bool:
    return value is None or isinstance(value, str)


def is_optional_int(value: object) -> bool:
    return value is None or (isinstance(value, int) and not isinstance(value, bool))


def load_snapshot(path: Path = SNAPSHOT) -> tuple[dict[str, object], list[dict[str, object]]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    require(payload.get("schema_version") == 1, "unsupported courtier trait schema")
    source = payload.get("source")
    require(isinstance(source, dict), "snapshot source metadata is missing")
    require(source.get("game_version") == "1.19.0.6", "unexpected source game version")
    require(
        isinstance(source.get("sha256"), str)
        and re.fullmatch(r"[0-9a-f]{64}", source["sha256"]) is not None,
        "invalid source SHA256",
    )

    traits = payload.get("traits")
    require(isinstance(traits, list), "snapshot traits must be a list")
    require(payload.get("trait_count") == len(traits), "snapshot trait_count drift")
    seen: set[str] = set()
    for index, trait in enumerate(traits):
        require(isinstance(trait, dict), f"trait at index {index} is not an object")
        missing = REQUIRED_TRAIT_FIELDS - trait.keys()
        require(not missing, f"trait at index {index} is missing {sorted(missing)}")
        key = trait["key"]
        require(
            isinstance(key, str) and re.fullmatch(r"[A-Za-z0-9_]+", key) is not None,
            f"invalid trait key {key!r}",
        )
        require(key not in seen, f"duplicate trait key {key!r}")
        seen.add(key)
        require(is_optional_string(trait["category"]), f"invalid category for {key}")
        require(isinstance(trait["physical"], bool), f"invalid physical flag for {key}")
        require(
            isinstance(trait["shown_in_ruler_designer"], bool),
            f"invalid ruler designer visibility for {key}",
        )
        require(
            isinstance(trait["ruler_designer_cost"], int)
            and not isinstance(trait["ruler_designer_cost"], bool),
            f"invalid ruler designer cost for {key}",
        )
        require(is_optional_int(trait["minimum_age"]), f"invalid minimum_age for {key}")
        require(is_optional_int(trait["maximum_age"]), f"invalid maximum_age for {key}")
        require(trait["valid_sex"] in {"all", "male", "female"}, f"invalid valid_sex for {key}")
        require(is_optional_string(trait["group"]), f"invalid group for {key}")
        require(
            is_optional_string(trait["group_equivalence"]),
            f"invalid group_equivalence for {key}",
        )
        require(
            isinstance(trait["opposites"], list)
            and all(isinstance(item, str) for item in trait["opposites"]),
            f"invalid opposites for {key}",
        )
        require(is_optional_int(trait["level"]), f"invalid level for {key}")
        require(isinstance(trait["has_track"], bool), f"invalid has_track for {key}")
    return source, traits


def build_catalogs(
    traits: list[dict[str, object]],
) -> tuple[dict[str, list[dict[str, object]]], list[dict[str, object]]]:
    catalogs = {
        "education": [trait for trait in traits if trait["category"] == "education"],
        "commander": [
            trait
            for trait in traits
            if trait["category"] in {"commander", "winter_commander"}
        ],
        "physical": [trait for trait in traits if trait["physical"]],
        "personality": [trait for trait in traits if trait["category"] == "personality"],
    }
    prior_keys = {
        trait["key"]
        for name in ("education", "commander", "physical", "personality")
        for trait in catalogs[name]
    }
    catalogs["other"] = [
        trait
        for trait in traits
        if trait["shown_in_ruler_designer"] and trait["key"] not in prior_keys
    ]

    for name in CATALOG_NAMES:
        require(
            len(catalogs[name]) == EXPECTED_COUNTS[name],
            f"{name} catalog has {len(catalogs[name])} traits, expected {EXPECTED_COUNTS[name]}",
        )

    education_levels = Counter(trait["level"] for trait in catalogs["education"])
    require(
        education_levels == Counter({level: 5 for level in range(1, 6)}),
        f"education levels are not five complete 1-5 sets: {dict(education_levels)}",
    )

    memberships: dict[str, list[str]] = defaultdict(list)
    for name in CATALOG_NAMES:
        for trait in catalogs[name]:
            memberships[trait["key"]].append(name)
    overlaps = {key: names for key, names in memberships.items() if len(names) != 1}
    require(not overlaps, f"catalog overlap: {overlaps}")

    union_keys = set(memberships)
    require(
        len(union_keys) == EXPECTED_UNION_COUNT,
        f"catalog union has {len(union_keys)} traits, expected {EXPECTED_UNION_COUNT}",
    )
    visible_keys = {trait["key"] for trait in traits if trait["shown_in_ruler_designer"]}
    hidden_catalog_keys = union_keys - visible_keys
    require(
        hidden_catalog_keys == {"impotent"},
        f"unexpected hidden catalog traits: {sorted(hidden_catalog_keys)}",
    )
    require(
        len(visible_keys) == EXPECTED_VISIBLE_COUNT,
        f"snapshot has {len(visible_keys)} visible traits, expected {EXPECTED_VISIBLE_COUNT}",
    )
    require(
        visible_keys == union_keys - {"impotent"},
        "visible ruler designer traits do not match the catalog union",
    )
    union = [trait for trait in traits if trait["key"] in union_keys]
    return catalogs, union


def build_conflicts(
    traits: list[dict[str, object]], union: list[dict[str, object]]
) -> dict[str, list[str]]:
    trait_by_key = {trait["key"]: trait for trait in traits}
    source_order = {trait["key"]: index for index, trait in enumerate(traits)}
    candidate_keys = {trait["key"] for trait in union}
    direct_groups: dict[str, list[str]] = defaultdict(list)
    equivalence_groups: dict[str, list[str]] = defaultdict(list)
    for trait in traits:
        if trait["group"] is not None:
            direct_groups[trait["group"]].append(trait["key"])
        if trait["group_equivalence"] is not None:
            equivalence_groups[trait["group_equivalence"]].append(trait["key"])

    conflict_sets = {trait["key"]: set() for trait in union}
    for trait in union:
        key = trait["key"]
        related: set[str] = set()
        for opposite in trait["opposites"]:
            resolved = False
            if opposite in trait_by_key:
                related.add(opposite)
                resolved = True
            if opposite in direct_groups:
                related.update(direct_groups[opposite])
                resolved = True
            require(resolved, f"{key} has unresolved opposite trait/group {opposite!r}")

        # Education is represented by a dedicated single-selection list. Its
        # five levels per discipline are replaced there rather than conflicted.
        if trait["group"] is not None and trait["category"] != "education":
            related.update(direct_groups[trait["group"]])
        if trait["group_equivalence"] is not None:
            related.update(equivalence_groups[trait["group_equivalence"]])

        for other in related:
            if other != key and other in candidate_keys:
                conflict_sets[key].add(other)
                conflict_sets[other].add(key)

    return {
        key: sorted(values, key=source_order.__getitem__)
        for key, values in conflict_sets.items()
    }


def catalog_membership(
    catalogs: dict[str, list[dict[str, object]]]
) -> dict[str, str]:
    return {
        trait["key"]: name
        for name in CATALOG_NAMES
        for trait in catalogs[name]
    }


def generated_effects(
    catalogs: dict[str, list[dict[str, object]]],
    union: list[dict[str, object]],
    conflicts: dict[str, list[str]],
) -> str:
    membership = catalog_membership(catalogs)
    lines = [HEADER, "# Vanilla trait catalogs and deterministic conflict removal.", ""]
    lines.extend(["xar_cc_rebuild_trait_catalogs_effect = {", "\troot = {"])
    for name in CATALOG_NAMES:
        lines.append(f"\t\tclear_variable_list = xar_cc_catalog_{name}")
    lines.extend(["\t}", ""])
    for trait in union:
        key = trait["key"]
        lines.extend(
            [
                f"\ttrait:{key} = {{ save_scope_as = xar_cc_catalog_entry }}",
                "\troot = {",
                "\t\tadd_to_variable_list = {",
                f"\t\t\tname = xar_cc_catalog_{membership[key]}",
                "\t\t\ttarget = scope:xar_cc_catalog_entry",
                "\t\t}",
                "\t}",
            ]
        )
    lines.extend(["}", "", "xar_cc_remove_selected_trait_conflicts_effect = {"])
    for trait in union:
        key = trait["key"]
        if not conflicts[key]:
            continue
        lines.extend(
            [
                "\tif = {",
                f"\t\tlimit = {{ scope:xar_cc_candidate_trait = trait:{key} }}",
            ]
        )
        for conflict in conflicts[key]:
            lines.append(
                "\t\txar_cc_remove_selected_trait_effect = "
                f"{{ TRAIT = trait:{conflict} }}"
            )
        lines.append("\t}")
    lines.extend(["}", ""])
    return "\n".join(lines)


def metadata_checks(trait: dict[str, object]) -> list[str]:
    checks = [f"scope:xar_cc_candidate_trait = trait:{trait['key']}"]
    if trait["minimum_age"] is not None:
        checks.append(f"var:xar_cc_age >= {trait['minimum_age']}")
    if trait["maximum_age"] is not None:
        checks.append(f"var:xar_cc_age <= {trait['maximum_age']}")
    if trait["valid_sex"] == "male":
        checks.append("var:xar_cc_female = 0")
    elif trait["valid_sex"] == "female":
        checks.append("var:xar_cc_female = 1")
    return checks


def conflict_pairs(
    union: list[dict[str, object]], conflicts: dict[str, list[str]]
) -> list[tuple[str, str]]:
    order = {trait["key"]: index for index, trait in enumerate(union)}
    pairs = [
        (trait["key"], other)
        for trait in union
        for other in conflicts[trait["key"]]
        if order[trait["key"]] < order[other]
    ]
    require(
        all(left in conflicts[right] for left, right in pairs),
        "conflict relation is not symmetric",
    )
    return pairs


def generated_triggers(
    union: list[dict[str, object]], conflicts: dict[str, list[str]]
) -> str:
    lines = [HEADER, "# Candidate metadata and selected-trait compatibility.", ""]
    lines.extend(["xar_cc_candidate_trait_metadata_valid_trigger = {", "\tOR = {"])
    for trait in union:
        checks = metadata_checks(trait)
        if len(checks) == 1:
            lines.append(f"\t\t{checks[0]}")
            continue
        lines.append("\t\tAND = {")
        lines.extend(f"\t\t\t{check}" for check in checks)
        lines.append("\t\t}")
    lines.extend(["\t}", "}", "", "xar_cc_candidate_replaces_selected_trait_trigger = {", "\tOR = {"])
    for trait in union:
        key = trait["key"]
        if not conflicts[key]:
            continue
        lines.extend(
            [
                "\t\tAND = {",
                f"\t\t\tscope:xar_cc_candidate_trait = trait:{key}",
                "\t\t\tOR = {",
            ]
        )
        for conflict in conflicts[key]:
            lines.append(
                "\t\t\t\txar_cc_trait_is_selected_trigger = "
                f"{{ TRAIT = trait:{conflict} }}"
            )
        lines.extend(["\t\t\t}", "\t\t}"])
    lines.extend(["\t}", "}", "", "xar_cc_selected_traits_compatible_trigger = {"])
    for left, right in conflict_pairs(union, conflicts):
        lines.extend(
            [
                "\tNAND = {",
                "\t\txar_cc_trait_is_selected_trigger = "
                f"{{ TRAIT = trait:{left} }}",
                "\t\txar_cc_trait_is_selected_trigger = "
                f"{{ TRAIT = trait:{right} }}",
                "\t}",
            ]
        )
    lines.extend(["}", ""])
    return "\n".join(lines)


def generated_values(union: list[dict[str, object]]) -> str:
    lines = [HEADER, "# Native ruler designer point total for selected traits.", ""]
    lines.extend(["xar_cc_selected_trait_cost = {", "\tvalue = 0"])
    for trait in union:
        lines.extend(
            [
                "\tif = {",
                "\t\tlimit = { xar_cc_trait_is_selected_trigger = "
                f"{{ TRAIT = trait:{trait['key']} }} }}",
                f"\t\tadd = {trait['ruler_designer_cost']}",
                "\t}",
            ]
        )
    lines.extend(["}", ""])
    return "\n".join(lines)


def render_all() -> tuple[dict[Path, str], dict[str, int], str, int]:
    source, traits = load_snapshot()
    catalogs, union = build_catalogs(traits)
    conflicts = build_conflicts(traits, union)
    rendered_by_kind = {
        "effects": generated_effects(catalogs, union, conflicts),
        "triggers": generated_triggers(union, conflicts),
        "values": generated_values(union),
    }
    rendered = {path: rendered_by_kind[kind] for path, kind in OUTPUTS.items()}
    counts = {name: len(catalogs[name]) for name in CATALOG_NAMES}
    return rendered, counts, source["sha256"], len(conflict_pairs(union, conflicts))


def encoded_script(content: str) -> bytes:
    return codecs.BOM_UTF8 + content.encode("utf-8")


def generated_file_matches(path: Path, content: str) -> bool:
    if not path.exists():
        return False
    actual = path.read_bytes()
    if not actual.startswith(codecs.BOM_UTF8):
        return False
    try:
        actual_text = actual[len(codecs.BOM_UTF8) :].decode("utf-8")
    except UnicodeDecodeError:
        return False
    # Git uses CRLF in Windows worktrees unless the repository pins an EOL.
    return actual_text.replace("\r\n", "\n") == content


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit nonzero if generated files differ; do not modify them",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rendered, counts, digest, pair_count = render_all()
    drift: list[Path] = []
    for path, content in rendered.items():
        expected = encoded_script(content)
        if args.check:
            if not generated_file_matches(path, content):
                drift.append(path)
        else:
            path.write_bytes(expected)

    count_text = ", ".join(f"{name}={counts[name]}" for name in CATALOG_NAMES)
    if args.check and drift:
        for path in drift:
            print(f"generated file drift: {path.relative_to(ROOT)}")
        return 1
    verb = "checked" if args.check else "generated"
    print(
        f"{verb} courtier catalogs: {count_text}, union={sum(counts.values())}, "
        f"conflict_pairs={pair_count}, source_sha256={digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
