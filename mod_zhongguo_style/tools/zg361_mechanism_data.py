#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Authoritative parser and balance profiles for the 361 mechanism catalogue.

The prose authority remains docs/361-expansion-options.md.  This module turns
that numbered catalogue plus reviewed choice overrides into generator input.
It deliberately keeps the ledger vocabulary small: 361 policies interact
through shared organizational state instead of inventing 361 disconnected
currencies.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from pathlib import Path
from typing import Final


MECHANISM_COUNT: Final = 361

LEDGERS: Final[tuple[str, ...]] = (
    "evidence",
    "trust",
    "admin_load",
    "appeal_risk",
    "delivery",
    "stability",
    "tech_debt",
    "data_quality",
    "burnout",
    "talent",
    "hc_pressure",
    "pay_debt",
    "policy_debt",
    "budget_pressure",
)


@dataclass(frozen=True)
class Mechanism:
    id: int
    group_code: str
    group_title: str
    title_cn: str
    title_en: str
    priority: str
    decision_cn: str
    consequence_cn: str
    acceptance_cn: str
    option_a_cn: str
    option_a_en: str
    option_b_cn: str
    option_b_en: str
    profile: str
    reference_choice: str


# A = evidence-rich / durable but costly; B = fast / forceful but risky;
# C = defer and explicitly carry policy debt.  None is universally optimal.
PROFILE_DELTAS: Final[dict[str, dict[str, dict[str, int]]]] = {
    "assessment": {
        "a": {"evidence": 3, "trust": 1, "admin_load": 2, "appeal_risk": -2},
        "b": {"delivery": 2, "admin_load": -1, "trust": -2, "appeal_risk": 2},
    },
    "calibration": {
        "a": {"evidence": 2, "trust": 2, "admin_load": 2, "appeal_risk": -2},
        "b": {"delivery": 1, "admin_load": -1, "trust": -2, "appeal_risk": 3},
    },
    "pip": {
        "a": {"talent": 2, "trust": 1, "admin_load": 2, "burnout": -1},
        "b": {"delivery": 2, "talent": -1, "burnout": 2, "appeal_risk": 2},
    },
    "promotion": {
        "a": {"talent": 3, "trust": 1, "admin_load": 1, "hc_pressure": 1},
        "b": {"delivery": 2, "pay_debt": 1, "trust": -1, "appeal_risk": 1},
    },
    "compensation": {
        "a": {"pay_debt": -3, "trust": 2, "budget_pressure": 3},
        "b": {"delivery": 1, "budget_pressure": -2, "pay_debt": 2, "trust": -1},
    },
    "hc": {
        "a": {"talent": 2, "hc_pressure": -2, "budget_pressure": 2, "admin_load": 1},
        "b": {"delivery": 2, "budget_pressure": -1, "hc_pressure": 2, "burnout": 1},
    },
    "incident": {
        "a": {"stability": 3, "tech_debt": -1, "delivery": -1, "admin_load": 1},
        "b": {"delivery": 3, "stability": -2, "tech_debt": 2, "burnout": 1},
    },
    "technology": {
        "a": {"stability": 2, "tech_debt": -3, "delivery": -1, "budget_pressure": 1},
        "b": {"delivery": 3, "tech_debt": 2, "stability": -1, "burnout": 1},
    },
    "platform": {
        "a": {"delivery": 1, "stability": 2, "tech_debt": -2, "admin_load": 1},
        "b": {"delivery": 2, "budget_pressure": -1, "tech_debt": 1, "trust": -1},
    },
    "data": {
        "a": {"data_quality": 3, "evidence": 1, "admin_load": 1, "delivery": -1},
        "b": {"delivery": 2, "data_quality": -2, "appeal_risk": 1},
    },
    "workload": {
        "a": {"burnout": -3, "trust": 2, "delivery": -1, "admin_load": 1},
        "b": {"delivery": 3, "burnout": 2, "trust": -1, "stability": -1},
    },
    "external": {
        "a": {"talent": 1, "hc_pressure": -1, "evidence": 1, "budget_pressure": 2},
        "b": {"delivery": 2, "budget_pressure": -1, "trust": -1, "appeal_risk": 1},
    },
    "organization": {
        "a": {"trust": 3, "talent": 2, "admin_load": 1, "budget_pressure": 1},
        "b": {"delivery": 2, "admin_load": -1, "trust": -2, "talent": -1},
    },
    "learning": {
        "a": {"talent": 3, "delivery": -1, "budget_pressure": 1, "admin_load": 1},
        "b": {"delivery": 2, "talent": -1, "burnout": 1, "trust": -1},
    },
    "delivery": {
        "a": {"delivery": 3, "data_quality": 1, "admin_load": 1, "budget_pressure": 1},
        "b": {"delivery": 2, "stability": -1, "tech_debt": 1, "appeal_risk": 1},
    },
    "governance": {
        "a": {"evidence": 2, "trust": 2, "data_quality": 1, "admin_load": 2},
        "b": {"delivery": 1, "admin_load": -2, "trust": -1, "policy_debt": 1},
    },
    "endgame": {
        "a": {"evidence": 2, "trust": 2, "stability": 2, "admin_load": 2},
        "b": {"delivery": 3, "trust": -2, "burnout": 2, "appeal_risk": 2},
    },
}

DEFER_DELTAS: Final[dict[str, int]] = {
    "admin_load": -1,
    "budget_pressure": -1,
    "policy_debt": 3,
    "trust": -1,
}


def _catalogue_lines(document: Path) -> list[str]:
    text = document.read_text(encoding="utf-8-sig")
    start = text.index("## 三、候选功能包")
    end = text.index("## 四、应当砍掉或延后的伪功能")
    return text[start:end].splitlines()


def parse_catalogue(document: Path) -> dict[int, dict[str, str]]:
    """Parse the exact 1..361 catalogue and its authoritative Chinese prose."""
    entry_re = re.compile(r"^(\d+)\. \*\*(.+?)\*\*\s*$")
    group_re = re.compile(r"^### ([A-Z]+)\. (.+?)\s*$")
    entries: dict[int, dict[str, str]] = {}
    current_group = ""
    current_group_title = ""
    current_id: int | None = None

    for line in _catalogue_lines(document):
        group_match = group_re.match(line)
        if group_match:
            current_group, current_group_title = group_match.groups()
            continue
        entry_match = entry_re.match(line)
        if entry_match:
            current_id = int(entry_match.group(1))
            raw_title = entry_match.group(2).strip()
            priority_match = re.search(r"（(P[012])(?:，[^）]+)?）", raw_title)
            priority = priority_match.group(1) if priority_match else "P1"
            title = re.sub(r"（P[012](?:，[^）]+)?）", "", raw_title).strip()
            entries[current_id] = {
                "group_code": current_group,
                "group_title": current_group_title,
                "title_cn": title,
                "priority": priority,
                "decision_cn": "",
                "consequence_cn": "",
                "acceptance_cn": "",
            }
            continue
        if current_id is None:
            continue
        stripped = line.strip()
        for prefix, field in (
            ("- 决策：", "decision_cn"),
            ("- 后果：", "consequence_cn"),
            ("- 验收：", "acceptance_cn"),
        ):
            if stripped.startswith(prefix):
                entries[current_id][field] = stripped[len(prefix) :].strip()
                break

    expected = list(range(1, MECHANISM_COUNT + 1))
    if sorted(entries) != expected:
        missing = sorted(set(expected) - set(entries))
        extra = sorted(set(entries) - set(expected))
        raise ValueError(f"catalogue must be exactly 1..361; missing={missing}, extra={extra}")
    for mechanism_id, fields in entries.items():
        if not fields["group_code"] or not fields["title_cn"]:
            raise ValueError(f"mechanism {mechanism_id} lacks group/title")
        if not fields["decision_cn"] or not fields["consequence_cn"]:
            raise ValueError(f"mechanism {mechanism_id} lacks decision/consequence prose")
    return entries


def load_choice_overrides(folder: Path) -> dict[int, dict[str, object]]:
    overrides: dict[int, dict[str, object]] = {}
    for path in sorted(folder.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"choice file must contain an object: {path}")
        for raw_id, raw_fields in payload.items():
            mechanism_id = int(raw_id)
            if mechanism_id in overrides:
                raise ValueError(f"duplicate choice override for {mechanism_id}")
            if not isinstance(raw_fields, dict):
                raise ValueError(f"choice override {mechanism_id} must be an object")
            overrides[mechanism_id] = raw_fields
    return overrides


def load_mechanisms(mod_root: Path, *, require_reviewed_choices: bool = True) -> list[Mechanism]:
    catalogue = parse_catalogue(mod_root / "docs" / "361-expansion-options.md")
    overrides = load_choice_overrides(mod_root / "tools" / "mechanism_choices")
    if require_reviewed_choices and sorted(overrides) != list(range(1, MECHANISM_COUNT + 1)):
        missing = sorted(set(range(1, MECHANISM_COUNT + 1)) - set(overrides))
        extra = sorted(set(overrides) - set(range(1, MECHANISM_COUNT + 1)))
        raise ValueError(
            "reviewed choices must cover exactly 1..361; "
            f"missing={missing[:20]}{'...' if len(missing) > 20 else ''}, extra={extra}"
        )

    mechanisms: list[Mechanism] = []
    for mechanism_id, fields in catalogue.items():
        override = overrides.get(mechanism_id, {})
        profile = str(override.get("profile", "governance"))
        if profile not in PROFILE_DELTAS:
            raise ValueError(f"mechanism {mechanism_id} has unknown profile {profile!r}")
        reference_choice = str(override.get("reference_choice", "a"))
        if reference_choice not in {"a", "b", "c"}:
            raise ValueError(
                f"mechanism {mechanism_id} has bad reference_choice {reference_choice!r}"
            )
        mechanisms.append(
            Mechanism(
                id=mechanism_id,
                group_code=fields["group_code"],
                group_title=fields["group_title"],
                title_cn=fields["title_cn"],
                title_en=str(override.get("title_en", f"Mechanism {mechanism_id}")),
                priority=fields["priority"],
                decision_cn=fields["decision_cn"],
                consequence_cn=fields["consequence_cn"],
                acceptance_cn=fields["acceptance_cn"],
                option_a_cn=str(override.get("option_a_cn", f"按证据落实“{fields['title_cn']}”")),
                option_a_en=str(override.get("option_a_en", "Adopt the evidence-led policy")),
                option_b_cn=str(override.get("option_b_cn", f"以短期结果重塑“{fields['title_cn']}”")),
                option_b_en=str(override.get("option_b_en", "Prioritize the short-term result")),
                profile=profile,
                reference_choice=reference_choice,
            )
        )
    return mechanisms


def mechanism_deltas(mechanism: Mechanism, choice: str) -> dict[str, int]:
    if choice == "c":
        return dict(DEFER_DELTAS)
    return dict(PROFILE_DELTAS[mechanism.profile][choice])
