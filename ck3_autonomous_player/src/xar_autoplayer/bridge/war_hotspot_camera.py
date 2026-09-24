"""Presentation-only map follow for observed native war hotspots.

The selector consumes the same war snapshot used by the autonomous player.
It never creates a gameplay step or treats camera position as battle evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from collections.abc import Callable
from typing import Mapping


_TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|#[^\r\n]*|[{}=]|[A-Za-z_][A-Za-z0-9_]*|\d+')


@dataclass(frozen=True)
class LandedProvinceIndex:
    """Vanilla province-to-barony mapping from this installation's title files."""

    barony_by_province: Mapping[int, str]
    county_by_province: Mapping[int, str]
    source_files: tuple[str, ...]

    @classmethod
    def from_game_dir(cls, game_dir: str | Path) -> "LandedProvinceIndex":
        title_dir = Path(game_dir) / "game" / "common" / "landed_titles"
        files = sorted(title_dir.glob("*.txt"))
        if not files:
            raise FileNotFoundError(f"no CK3 landed-title files in {title_dir}")
        baronies: dict[int, str] = {}
        counties: dict[int, str] = {}
        for path in files:
            tokens = [
                match.group(0)
                for match in _TOKEN.finditer(path.read_text(encoding="utf-8-sig"))
                if not match.group(0).startswith(("#", '"'))
            ]
            scopes: list[str | None] = []
            for pos, token in enumerate(tokens):
                if token == "{":
                    name = tokens[pos - 2] if pos >= 2 and tokens[pos - 1] == "=" else None
                    scopes.append(name)
                elif token == "}":
                    if not scopes:
                        raise ValueError(f"unbalanced title braces in {path}")
                    scopes.pop()
                elif (
                    token == "province"
                    and pos + 2 < len(tokens)
                    and tokens[pos + 1] == "="
                    and tokens[pos + 2].isdigit()
                    and scopes
                    and isinstance(scopes[-1], str)
                    and scopes[-1].startswith("b_")
                ):
                    province = int(tokens[pos + 2])
                    if province <= 0:
                        continue
                    barony = scopes[-1]
                    county = next(
                        (scope for scope in reversed(scopes) if isinstance(scope, str) and scope.startswith("c_")),
                        None,
                    )
                    old = baronies.get(province)
                    if old is not None and old != barony:
                        raise ValueError(f"province {province} maps to both {old} and {barony}")
                    baronies[province] = barony
                    if county is not None:
                        counties[province] = county
            if scopes:
                raise ValueError(f"unbalanced title braces in {path}")
        if not baronies:
            raise ValueError("landed-title files yielded no barony provinces")
        return cls(baronies, counties, tuple(str(path.resolve()) for path in files))


def select_war_hotspot(
    snapshot: Mapping[str, object], index: LandedProvinceIndex
) -> dict[str, object] | None:
    """Prioritize an observed battle, siege, route endpoint, then objective.

    Sea provinces have no landed-title mapping, so they cannot become targets.
    Ties are stable by war and army ID; the selector uses no invented location.
    """

    wars = snapshot.get("active_wars")
    if not isinstance(wars, list):
        return None
    candidates: list[tuple[int, int, int, int, str]] = []
    for war in wars:
        if not isinstance(war, dict):
            continue
        war_id = _positive_int(war.get("war_id")) or 2**31 - 1
        allied = war.get("allied_armies")
        if isinstance(allied, list):
            for army in allied:
                if not isinstance(army, dict):
                    continue
                army_id = _positive_int(army.get("army_id")) or 2**31 - 1
                current = _positive_int(army.get("current_province_id"))
                if army.get("in_combat") is True:
                    _add(candidates, index,
                         0 if army.get("controllable") is True else 1,
                         war_id, army_id, current, "battle")
                elif army.get("army_state") == "siege" or army.get("siege_days_left") is not None:
                    _add(candidates, index,
                         2 if army.get("controllable") is True else 3,
                         war_id, army_id, current, "siege")
                if army.get("controllable") is True and army.get("retreating") is not True:
                    target = _positive_int(army.get("move_target_province_id"))
                    if target is not None:
                        _add(candidates, index, 5, war_id, army_id, target, "army_destination")
                    _add(candidates, index, 7, war_id, army_id, current, "player_army")
        states = war.get("objective_province_states")
        if isinstance(states, list):
            for row in states:
                if not isinstance(row, dict):
                    continue
                province = _positive_int(row.get("province_id"))
                if row.get("active_siege") is not None:
                    _add(candidates, index, 4, war_id, 0, province, "objective_siege")
                _add(candidates, index, 6, war_id, 0, province, "war_objective")
        objectives = war.get("war_objective_province_ids")
        if isinstance(objectives, list):
            for province in objectives:
                _add(candidates, index, 6, war_id, 0, _positive_int(province), "war_objective")
    if not candidates:
        return None
    priority, war_id, army_id, province, reason = min(candidates)
    return {
        "reason": reason,
        "priority": priority,
        "war_id": war_id,
        "army_id": army_id if army_id else None,
        "province_id": province,
        "title_key": index.barony_by_province[province],
        "county_key": index.county_by_province.get(province),
    }


def follow_war_hotspot(
    service: object,
    snapshot: Mapping[str, object],
    index: LandedProvinceIndex,
    *,
    park_cursor: Callable[[], dict[str, object]] | None = None,
) -> dict[str, object]:
    """Center on the selected land hotspot and preserve the native receipt."""

    hotspot = select_war_hotspot(snapshot, index)
    if hotspot is None:
        return {"status": "no_observable_land_hotspot", "hotspot": None}
    revision = snapshot.get("revision")
    if type(revision) is not int or revision < 0:
        raise ValueError("hotspot camera requires a bound snapshot revision")
    cursor_park = park_cursor() if park_cursor is not None else None
    if park_cursor is not None and (
        not isinstance(cursor_park, dict) or cursor_park.get("status") != "parked"
    ):
        raise ValueError(f"CK3 cursor was not parked inside the map window: {cursor_park}")
    result = service.center_map_on_landed_title_v1(
        str(hotspot["title_key"]), expected_revision=revision
    )
    if result.get("status") not in {"centered", "already_centered"} or (
        result.get("camera_center") or {}
    ).get("postcondition_verified") is not True:
        raise ValueError("hotspot camera lacks a verified native postcondition")
    if (result.get("title") or {}).get("key") != hotspot["title_key"]:
        raise ValueError("hotspot camera resolved a different landed title")
    return {"status": result["status"], "hotspot": hotspot,
            "cursor_park": cursor_park, "camera_receipt": result}


def _positive_int(value: object) -> int | None:
    return value if type(value) is int and value > 0 else None


def _add(
    candidates: list[tuple[int, int, int, int, str]],
    index: LandedProvinceIndex,
    priority: int,
    war_id: int,
    army_id: int,
    province: int | None,
    reason: str,
) -> None:
    if province is not None and province in index.barony_by_province:
        candidates.append((priority, war_id, army_id, province, reason))
