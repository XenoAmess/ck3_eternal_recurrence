#!/usr/bin/env python3
"""Stable identities for the two ZhongGuo phase-two editorial cuts.

The reusable promo preset owns the eight-span capture contract.  This module
owns project-local editorial identity so two cuts can reuse the exact same
verified source bytes without sharing run, deliverable, or output names.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Phase2PromoCut:
    cut_id: str
    project_config_name: str
    authoring_ledger_name: str
    default_run_id: str
    deliverable_artifact_id: str
    deliverable_relative_path: Path


CHARACTER_CUT = Phase2PromoCut(
    cut_id="character-led",
    project_config_name="phase2-promo-character-project.json",
    authoring_ledger_name="phase2-authoring-character-claims.json",
    default_run_id="phase2-character-candidate",
    deliverable_artifact_id="zhongguo-361-phase2-character-video",
    deliverable_relative_path=Path("deliverable/zhongguo-361-phase2-character.mp4"),
)

INSTITUTION_CUT = Phase2PromoCut(
    cut_id="institution-led",
    project_config_name="phase2-promo-institution-project.json",
    authoring_ledger_name="phase2-authoring-institution-claims.json",
    default_run_id="phase2-institution-candidate",
    deliverable_artifact_id="zhongguo-361-phase2-institution-video",
    deliverable_relative_path=Path("deliverable/zhongguo-361-phase2-institution.mp4"),
)

# Compatibility only.  Existing validate-only commands and old frozen receipts
# keep resolving exactly as before; new production should select one of the two
# explicit cuts above.
LEGACY_CUT = Phase2PromoCut(
    cut_id="legacy-single-cut",
    project_config_name="phase2-promo-project.json",
    authoring_ledger_name="phase2-authoring-claims.json",
    default_run_id="phase2-candidate",
    deliverable_artifact_id="zhongguo-361-phase2-video",
    deliverable_relative_path=Path("deliverable/zhongguo-361-phase2.mp4"),
)

CUTS = (CHARACTER_CUT, INSTITUTION_CUT)
SUPPORTED_CUTS = (*CUTS, LEGACY_CUT)
CUT_BY_ID = {cut.cut_id: cut for cut in SUPPORTED_CUTS}
CUT_BY_CONFIG_NAME = {cut.project_config_name: cut for cut in SUPPORTED_CUTS}


def cut_for_id(cut_id: str) -> Phase2PromoCut:
    try:
        return CUT_BY_ID[cut_id]
    except KeyError as exc:
        raise ValueError(f"unsupported ZhongGuo phase-two promo cut id: {cut_id!r}") from exc


def cut_for_config_name(name: str) -> Phase2PromoCut:
    try:
        return CUT_BY_CONFIG_NAME[name]
    except KeyError as exc:
        raise ValueError(f"unsupported ZhongGuo phase-two promo config name: {name!r}") from exc


__all__ = [
    "CHARACTER_CUT",
    "CUTS",
    "CUT_BY_ID",
    "CUT_BY_CONFIG_NAME",
    "INSTITUTION_CUT",
    "LEGACY_CUT",
    "Phase2PromoCut",
    "SUPPORTED_CUTS",
    "cut_for_config_name",
    "cut_for_id",
]
