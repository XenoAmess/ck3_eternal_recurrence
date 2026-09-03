#!/usr/bin/env python3
"""Stable identities for the two ZhongGuo phase-two editorial cuts.

The reusable promo preset owns the eight-span capture contract.  This module
owns project-local editorial identity so two cuts can reuse the exact same
verified source bytes without sharing run, deliverable, or output names.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Phase2PromoReprise:
    """Insert one short, silent cut-back to an already-verified source chapter.

    Reprises never change capture order or create a second evidence claim.  The
    project composer trims the source visual to this explicit duration and
    supplies newly generated silence instead of replaying the original
    narration.
    """

    source_chapter_id: str
    after_chapter_id: str
    duration_seconds: float
    start_offset_seconds: float = 0.0

    def __post_init__(self) -> None:
        if (
            isinstance(self.duration_seconds, bool)
            or not isinstance(self.duration_seconds, (int, float))
            or not math.isfinite(float(self.duration_seconds))
            or self.duration_seconds <= 0
        ):
            raise ValueError("reprise duration_seconds must be finite and positive")
        if (
            isinstance(self.start_offset_seconds, bool)
            or not isinstance(self.start_offset_seconds, (int, float))
            or not math.isfinite(float(self.start_offset_seconds))
            or self.start_offset_seconds < 0
        ):
            raise ValueError(
                "reprise start_offset_seconds must be finite and non-negative"
            )


@dataclass(frozen=True, slots=True)
class Phase2PromoCut:
    cut_id: str
    project_config_name: str
    authoring_ledger_name: str
    default_run_id: str
    deliverable_artifact_id: str
    deliverable_relative_path: Path
    editorial_chapter_order: tuple[str, ...]
    reprises: tuple[Phase2PromoReprise, ...] = ()


CANONICAL_CHAPTER_ORDER = (
    "phase2_minimal_recap",
    "phase2_fact_quota_calibration",
    "phase2_receipt_appeal_pip",
    "phase2_manager_governance",
    "phase2_promotion_compensation",
    "phase2_hc_workforce",
    "phase2_projects_metrics",
    "phase2_incidents_operations",
    "phase2_cross_cycle_endgame",
    "phase2_finale",
)


CHARACTER_CUT = Phase2PromoCut(
    cut_id="character-led",
    project_config_name="phase2-promo-character-project.json",
    authoring_ledger_name="phase2-authoring-character-claims.json",
    default_run_id="phase2-character-led-candidate",
    deliverable_artifact_id="zhongguo-361-phase2-character-led-video",
    deliverable_relative_path=Path("deliverable/zhongguo-361-phase2-character-led.mp4"),
    editorial_chapter_order=CANONICAL_CHAPTER_ORDER,
)

INSTITUTION_CUT = Phase2PromoCut(
    cut_id="institution-led",
    project_config_name="phase2-promo-institution-project.json",
    authoring_ledger_name="phase2-authoring-institution-claims.json",
    default_run_id="phase2-institution-led-candidate",
    deliverable_artifact_id="zhongguo-361-phase2-institution-led-video",
    deliverable_relative_path=Path("deliverable/zhongguo-361-phase2-institution-led.mp4"),
    editorial_chapter_order=(
        "phase2_minimal_recap",
        "phase2_fact_quota_calibration",
        "phase2_manager_governance",
        "phase2_receipt_appeal_pip",
        "phase2_promotion_compensation",
        "phase2_hc_workforce",
        "phase2_projects_metrics",
        "phase2_incidents_operations",
        "phase2_cross_cycle_endgame",
        "phase2_finale",
    ),
    reprises=(
        Phase2PromoReprise(
            source_chapter_id="phase2_receipt_appeal_pip",
            after_chapter_id="phase2_projects_metrics",
            duration_seconds=2.0,
        ),
        Phase2PromoReprise(
            source_chapter_id="phase2_manager_governance",
            after_chapter_id="phase2_cross_cycle_endgame",
            duration_seconds=2.0,
        ),
    ),
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
    editorial_chapter_order=CANONICAL_CHAPTER_ORDER,
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
    "CANONICAL_CHAPTER_ORDER",
    "Phase2PromoCut",
    "Phase2PromoReprise",
    "SUPPORTED_CUTS",
    "cut_for_config_name",
    "cut_for_id",
]
