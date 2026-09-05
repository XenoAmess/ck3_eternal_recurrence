#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared player-facing Simplified Chinese terminology normalization."""

from __future__ import annotations

import re


# Longer phrases must be replaced before their component words.
TERM_REPLACEMENTS = (
    ("Good Leaver", "正常离任"),
    ("Bad Leaver", "有责离任"),
    ("Good leaver", "正常离任"),
    ("Bad leaver", "有责离任"),
    ("onboarding", "入职融入"),
    ("management", "管理层"),
    ("backfill", "补岗"),
    ("Sponsor", "提名担保人"),
    ("sponsor", "提名担保人"),
    ("manager", "直属上司"),
    ("leader", "负责人"),
    ("owner", "责任人"),
    ("Offer", "录用邀约"),
    ("offer", "录用邀约"),
    ("Cliff", "归属等待期"),
    ("FIFO", "先进先出"),
    ("WIP", "在制任务"),
    ("SLA", "服务承诺"),
    ("toil", "重复运维"),
    ("HC", "编制名额"),
    ("PIP", "绩效改进计划"),
    ("KPI", "绩效指标"),
)


def normalize_player_chinese(value: str) -> str:
    """Translate project jargon while preserving CK3 commands in ``[...]``."""

    parts = re.split(r"(\[[^\]]*\])", value)
    for index in range(0, len(parts), 2):
        for source, replacement in TERM_REPLACEMENTS:
            parts[index] = parts[index].replace(source, replacement)
        parts[index] = re.sub(
            r"(?<=[\u3400-\u9fff]) +(?=[\u3400-\u9fff])", "", parts[index]
        )
    return "".join(parts)


def normalize_localization_rows(rows: list[str]) -> list[str]:
    """Normalize only quoted loc values, never localization keys or headers."""

    normalized: list[str] = []
    for row in rows:
        match = re.match(r'^(\s*[^:]+:\d+\s+")(.*)("\s*)$', row)
        if match is None:
            normalized.append(row)
            continue
        normalized.append(
            match.group(1) + normalize_player_chinese(match.group(2)) + match.group(3)
        )
    return normalized


def normalize_localization_document(document: str) -> str:
    """Normalize a complete CK3 localization document line by line."""

    return "\n".join(normalize_localization_rows(document.splitlines()))
