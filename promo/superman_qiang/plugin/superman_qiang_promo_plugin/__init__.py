"""Project-only policy factories resolved by the official xar-promo CLI.

No capture, media rendering, process execution, or framework implementation lives
in this registration package. Factories describe the accepted inputs and approved
project policy; the project composer consumes both resolved values.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PreparedStillsPolicy:
    adapter_id: str = "superman-qiang-prepared-stills"
    accepted_source_kinds: tuple[str, ...] = ("art", "genuine-screenshot", "schematic")
    launches_game: bool = False
    requires_frozen_source_hashes: bool = True
    genuine_screenshots_preserve_aspect_ratio: bool = True


@dataclass(frozen=True)
class PlayerTrailerPolicy:
    preset_id: str = "superman-qiang-player-trailer"
    narration_locale: str = "zh-CN"
    subtitle_locales: tuple[str, ...] = ("zh-CN",)
    voice: str = "zh-CN-XiaoxiaoNeural"
    frame: tuple[int, int, int] = (1920, 1080, 30)
    minimum_duration_seconds: float = 90.0
    maximum_duration_seconds: float = 300.0
    head_seconds: tuple[float, ...] = (1.4, 0.9, 0.8, 0.7, 1.0, 0.9, 0.8, 0.9, 0.75, 0.9)
    tail_seconds: tuple[float, ...] = (2.0, 2.2, 2.4, 2.4, 4.0, 3.4, 2.6, 2.8, 2.1, 6.0)
    music_source_count: int = 1
    audience: str = "CK3 players and potential players"


def prepared_stills_adapter(*, config: Any) -> PreparedStillsPolicy:
    policy = PreparedStillsPolicy()
    if config.adapter != policy.adapter_id:
        raise ValueError("Prepared-stills adapter received another adapter ID")
    return policy


def player_trailer_preset(*, config: Any) -> PlayerTrailerPolicy:
    policy = PlayerTrailerPolicy()
    if config.preset != policy.preset_id:
        raise ValueError("Player-trailer preset received another preset ID")
    if config.narration_locale != policy.narration_locale or config.subtitle_locales != policy.subtitle_locales:
        raise ValueError("The approved player trailer requires Chinese narration and subtitles")
    if len(config.chapters) != len(policy.head_seconds):
        raise ValueError("The player-trailer preset requires the ten approved scenes")
    return policy
