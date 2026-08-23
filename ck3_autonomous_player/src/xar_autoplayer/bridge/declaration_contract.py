"""Canonical native CK3 war-declaration discovery and command contract."""

from __future__ import annotations

import re


QUERY_DECLARABLE_WARS_STEP = "query-declarable-wars"
DECLARE_WAR_CAPABILITY = "game.command.declare-war-N"
_DECLARATION_ID = re.compile(
    r"(?P<target>\d+)-(?P<casus_belli>\d+)-(?P<configuration>-1|\d+)"
)


def normalize_declarable_wars(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise ValueError("native declarable_wars must be an array")
    result: list[dict[str, object]] = []
    seen: set[str] = set()
    for index, raw in enumerate(value):
        if not isinstance(raw, dict):
            raise ValueError(f"native declarable_wars[{index}] must be an object")
        target = _non_negative(raw.get("target_character_id"), "target_character_id")
        casus_belli_index = _non_negative(
            raw.get("casus_belli_index"), "casus_belli_index"
        )
        configuration_index = raw.get("configuration_index")
        if (
            isinstance(configuration_index, bool)
            or not isinstance(configuration_index, int)
            or configuration_index < -1
        ):
            raise ValueError("configuration_index must be -1 or a non-negative integer")
        claimant = raw.get("claimant_character_id")
        if (
            isinstance(claimant, bool)
            or not isinstance(claimant, int)
            or claimant < -1
        ):
            raise ValueError("claimant_character_id must be -1 or a non-negative integer")
        casus_belli_key = raw.get("casus_belli_key")
        if not isinstance(casus_belli_key, str) or not casus_belli_key:
            raise ValueError("casus_belli_key must be a non-empty string")
        raw_titles = raw.get("target_title_ids")
        if not isinstance(raw_titles, list):
            raise ValueError("target_title_ids must be an array")
        title_ids = [
            _non_negative(item, "target_title_id") for item in raw_titles
        ]
        declaration_id = f"{target}-{casus_belli_index}-{configuration_index}"
        if raw.get("declaration_id") != declaration_id:
            raise ValueError(
                f"native declarable_wars[{index}].declaration_id is malformed"
            )
        if declaration_id in seen:
            raise ValueError("native declarable_wars contains a duplicate declaration")
        seen.add(declaration_id)
        result.append(
            {
                "declaration_id": declaration_id,
                "target_character_id": target,
                "casus_belli_index": casus_belli_index,
                "casus_belli_key": casus_belli_key,
                "configuration_index": configuration_index,
                "claimant_character_id": claimant,
                "target_title_ids": title_ids,
                "source": "native",
            }
        )
    return result


def declare_war_step(declaration_id: str) -> str:
    if not isinstance(declaration_id, str) or _DECLARATION_ID.fullmatch(
        declaration_id
    ) is None:
        raise ValueError("declaration_id is malformed")
    return f"declare-war-{declaration_id}"


def parse_declare_war_step(step: object) -> str | None:
    if not isinstance(step, str) or not step.startswith("declare-war-"):
        return None
    declaration_id = step.removeprefix("declare-war-")
    return declaration_id if _DECLARATION_ID.fullmatch(declaration_id) else None


def is_native_declaration_step(step: object) -> bool:
    return step == QUERY_DECLARABLE_WARS_STEP or parse_declare_war_step(step) is not None


def _non_negative(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value
