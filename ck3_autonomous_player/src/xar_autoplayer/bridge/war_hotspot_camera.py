"""Presentation-only map follow for observed native war hotspots.

The selector consumes the same war snapshot used by the autonomous player.
It never creates a gameplay step or treats camera position as battle evidence.
"""

from __future__ import annotations

import copy
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
    snapshot: Mapping[str, object], index: LandedProvinceIndex,
    *, campaign_root_result: object = None,
) -> dict[str, object] | None:
    """Prioritize observed war activity, then the player's observed land anchor.

    Sea provinces have no landed-title mapping, so they cannot become targets.
    Ties are stable by war and army ID; the selector uses no invented location.
    """

    wars = snapshot.get("active_wars")
    if not isinstance(wars, list):
        return None
    candidates: list[tuple[int, int, int | None, int, str]] = []
    for war in wars:
        if not isinstance(war, dict):
            continue
        war_id = _positive_int(war.get("war_id")) or 2**31 - 1
        allied = war.get("allied_armies")
        if isinstance(allied, list):
            for army in allied:
                if not isinstance(army, dict):
                    continue
                army_id = _army_id(army.get("army_id"))
                current = _positive_int(army.get("current_province_id"))
                if army.get("in_combat") is True:
                    _add(candidates, index,
                         0 if army.get("controllable") is True else 1,
                         war_id, army_id, current, "battle")
                elif army.get("army_state") in {"siege", "sieging"} or army.get("siege_days_left") is not None:
                    _add(candidates, index,
                         2 if army.get("controllable") is True else 3,
                         war_id, army_id, current, "siege")
                if army.get("controllable") is True and army.get("retreating") is not True:
                    target = _positive_int(army.get("move_target_province_id"))
                    if target is not None:
                        # Follow the moving army's observed position while it
                        # remains on land. A far route endpoint is only a
                        # fallback if the army itself is currently at sea.
                        _add(candidates, index, 5, war_id, army_id, current, "moving_player_army")
                        _add(candidates, index, 6, war_id, army_id, target, "army_destination")
                    else:
                        _add(candidates, index, 8, war_id, army_id, current, "player_army")
        states = war.get("objective_province_states")
        if isinstance(states, list):
            for row in states:
                if not isinstance(row, dict):
                    continue
                province = _positive_int(row.get("province_id"))
                if row.get("active_siege") is not None:
                    _add(candidates, index, 4, war_id, None, province, "objective_siege")
                _add(candidates, index, 7, war_id, None, province, "war_objective")
        objectives = war.get("war_objective_province_ids")
        if isinstance(objectives, list):
            for province in objectives:
                _add(candidates, index, 7, war_id, None, _positive_int(province), "war_objective")
    if not candidates:
        return _player_land_anchor(snapshot, index, campaign_root_result)
    priority, war_id, army_id, province, reason = min(
        candidates, key=lambda row: (
            row[0], row[1], row[2] is None,
            row[2] if row[2] is not None else 0, row[3], row[4],
        ),
    )
    return {
        "reason": reason,
        "priority": priority,
        "war_id": war_id,
        "army_id": army_id,
        "province_id": province,
        "title_key": index.barony_by_province[province],
        "county_key": index.county_by_province.get(province),
    }


def _camera_anchor_key(snapshot: Mapping[str, object], hotspot: Mapping[str, object]) -> tuple | None:
    played, diagnostics = snapshot.get("played_character"), snapshot.get("diagnostics")
    if (snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or not isinstance(played, dict) or played.get("alive") is not True
            or not isinstance(diagnostics, dict)):
        return None
    ids = (snapshot.get("revision"), snapshot.get("native_revision"), snapshot.get("date_raw"),
           played.get("character_id"), diagnostics.get("bridge_pid"),
           diagnostics.get("connection_generation"))
    strings = (snapshot.get("snapshot_id"), snapshot.get("episode_run_id"),
               hotspot.get("title_key"))
    if any(type(v) is not int or v < 0 for v in ids) or any(
            not isinstance(v, str) or not v for v in strings):
        return None
    return (*strings, *ids, hotspot.get("province_id"))


def follow_war_hotspot(
    service: object,
    snapshot: Mapping[str, object],
    index: LandedProvinceIndex,
    *,
    park_cursor: Callable[[], dict[str, object]] | None = None,
    campaign_root_result: object = None,
    reuse_same_frame: bool = False,
) -> dict[str, object]:
    """Center once per exact automatic frame; explicit navigation stays immediate."""

    hotspot = select_war_hotspot(
        snapshot, index, campaign_root_result=campaign_root_result,
    )
    if hotspot is None:
        if reuse_same_frame:
            service._war_hotspot_camera_anchor = None
        return {"status": "no_observable_land_hotspot", "hotspot": None}
    anchor_key = _camera_anchor_key(snapshot, hotspot) if reuse_same_frame else None
    previous = getattr(service, "_war_hotspot_camera_anchor", None)
    if anchor_key is not None and isinstance(previous, dict) and previous.get("key") == anchor_key:
        return {"status": "reused_same_frame_anchor", "hotspot": hotspot,
                "native_command_submitted": False,
                "anchor_source": dict(previous["source"]),
                "camera_receipt": copy.deepcopy(previous["receipt"]),
                "camera_receipt_source": "previous_same_frame"}
    revision = snapshot.get("revision")
    if type(revision) is not int or revision < 0:
        raise ValueError("hotspot camera requires a bound snapshot revision")
    cursor_park = park_cursor() if park_cursor is not None else None
    if park_cursor is not None and (
        not isinstance(cursor_park, dict)
        or cursor_park.get("status") not in {"parked", "skipped_minimized", "skipped_other_virtual_desktop"}
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
    if anchor_key is not None:
        service._war_hotspot_camera_anchor = {
            "key": anchor_key, "receipt": copy.deepcopy(result), "source": {
            "snapshot_id": snapshot["snapshot_id"], "revision": snapshot["revision"],
            "native_revision": snapshot["native_revision"], "date_raw": snapshot["date_raw"],
            "episode_run_id": snapshot["episode_run_id"], "title_key": hotspot["title_key"],
            "postcondition_verified": True}}
    return {"status": result["status"], "hotspot": hotspot,
            "cursor_park": cursor_park, "camera_receipt": result}


def _positive_int(value: object) -> int | None:
    return value if type(value) is int and value > 0 else None


def _army_id(value: object) -> int | None:
    return value if type(value) is int and value >= 0 else None


def _player_land_anchor(
    snapshot: Mapping[str, object], index: LandedProvinceIndex,
    campaign_root_result: object,
) -> dict[str, object] | None:
    """Use an already observed same-frame root, never invent a title or point."""
    from .current_first_heir_relationship_private_transport import (
        _same_frame_campaign_root_result,
    )

    played = snapshot.get("played_character")
    if (snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or not isinstance(played, dict) or played.get("alive") is not True
            or _positive_int(played.get("character_id")) is None):
        return None
    observed = _same_frame_campaign_root_result(campaign_root_result, dict(snapshot))
    if observed is None:
        return None
    root = observed["campaign_root_context"]
    readiness = root.get("readiness")
    if not isinstance(readiness, dict):
        return None
    capital = _positive_int(root.get("capital_province_id"))
    reason, priority, held_title_id = "player_capital", 9, None
    if readiness.get("capital_ready") is not True or capital not in index.barony_by_province:
        partition = root.get("held_title_partition")
        if readiness.get("held_title_partition_ready") is not True or not isinstance(partition, list):
            return None
        counties = []
        for row in partition:
            title = row.get("title") if isinstance(row, dict) else None
            province = _positive_int(row.get("capital_province_id")) if isinstance(row, dict) else None
            if (isinstance(title, dict) and title.get("tier_raw") == 2
                    and title.get("tier_key") == "county"
                    and _positive_int(title.get("title_id")) is not None
                    and province in index.barony_by_province):
                counties.append((title["title_id"], province))
        if not counties:
            return None
        held_title_id, capital = min(counties)
        reason, priority = "player_held_county_capital", 10
    return {
        "reason": reason, "priority": priority, "war_id": None, "army_id": None,
        "province_id": capital, "title_key": index.barony_by_province[capital],
        "county_key": index.county_by_province.get(capital),
        "source": "same_frame_campaign_root_context_v1",
        "query_sequence": observed["query_sequence"],
        "held_title_id": held_title_id,
    }


def _add(
    candidates: list[tuple[int, int, int | None, int, str]],
    index: LandedProvinceIndex,
    priority: int,
    war_id: int,
    army_id: int | None,
    province: int | None,
    reason: str,
) -> None:
    if province is not None and province in index.barony_by_province:
        candidates.append((priority, war_id, army_id, province, reason))
