#!/usr/bin/env python3
"""Read the exact CK3 source contracts used by the XQOL compatibility projection."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GAME = ROOT / "Crusader Kings III" / "game"
CONTRACT_PATH = Path(__file__).with_name("xqol_vanilla_1_20_0_2.json")
CONTRACT = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def source_errors(game: Path = GAME) -> list[str]:
    errors = []
    for relative, expected in CONTRACT["files"].items():
        path = game / relative
        if not path.is_file():
            errors.append(f"XQOL exact-build source missing: {relative}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            errors.append(f"XQOL exact-build source SHA-256 changed: {relative}")
    return errors


def require_sources(game: Path = GAME) -> None:
    errors = source_errors(game)
    if errors:
        raise ValueError("\n".join(errors))


def block(text: str, key: str, *, indentation: str = "") -> str:
    """Extract a named block, ignoring braces inside comments and quoted strings."""
    matches = list(re.finditer(
        rf"(?m)^{re.escape(indentation + key)}\s*=\s*\{{", text
    ))
    if len(matches) != 1:
        raise ValueError(f"expected one {key!r} block at indentation {indentation!r}")
    match = matches[0]
    opening = text.index("{", match.start())
    depth = 0
    quoted = comment = escaped = False
    for index in range(opening, len(text)):
        character = text[index]
        if comment:
            if character == "\n":
                comment = False
            continue
        if quoted:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quoted = False
            continue
        if character == "#":
            comment = True
        elif character == '"':
            quoted = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return text[match.start():index + 1]
    raise ValueError(f"unterminated {key!r} block")


def native_definition(relative: str, key: str) -> str:
    return block((GAME / relative).read_text(encoding="utf-8-sig"), key)


def native_conversion_acceptance(kind: str) -> str:
    """Project native acceptance with no hook, influence or paid concession option."""
    key = {
        "courtier": "ask_for_conversion_courtier_interaction",
        "ruler": "demand_conversion_vassal_ruler_interaction",
    }[kind]
    definition = native_definition("common/character_interactions/00_religious_interactions.txt", key)
    acceptance = block(definition, "ai_accept", indentation="\t")
    # The ruler-only concession and warning are send-option/UI clauses. XQOL
    # offers neither option, so mirror the four unconditional native clauses.
    required = (
        "celestial_hierarchy_acceptance_modifier",
        "religion_demand_conversion_default_modifier = yes",
        "religion_demand_conversion_christian_situation_modifier = yes",
        "add = 50",
    )
    for token in required:
        if acceptance.count(token) != 1:
            raise ValueError(f"native {kind} conversion acceptance changed: {token}")
    return (
        "\t\tbase = 0\n"
        "\t\t" + block(acceptance, "celestial_hierarchy_acceptance_modifier", indentation="\t\t").lstrip()
        + "\n\t\tmodifier = {\n\t\t\tadd = 50\n"
        "\t\t\tdesc = EDUCATE_CHILD_ACTOR_IS_MY_LIEGE\n\t\t}\n"
        "\t\treligion_demand_conversion_default_modifier = yes\n"
        "\t\treligion_demand_conversion_christian_situation_modifier = yes"
    )


def native_full_golden_obligation() -> str:
    """Keep the 1.20 native quote, excluding its available-wallet cap.

    The native capped value answers what can be collected now. XQOL's full
    payment mode instead requires the entire quote before consuming a hook.
    """
    definition = native_definition("common/script_values/00_interaction_values.txt", "golden_obligation_value")
    if definition.count("\tmax = gold\n") != 1:
        raise ValueError("native golden obligation wallet cap changed")
    return definition.replace("golden_obligation_value =", "xqol_full_golden_obligation_value =", 1).replace("\tmax = gold\n", "")
