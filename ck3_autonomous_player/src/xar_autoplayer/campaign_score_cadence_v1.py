"""Pure CK3 monthly score cadence; no clock actions, RPC, SAVE or file IO.

Calendar source: exact 1.20.0.4 CDate Decode and native month-length table,
documented in native71-conception-last-child-date-12004.md. Positive game
years only: fixed 365 days, no Gregorian leap days, 24 raw ticks per day.
"""
from __future__ import annotations

from bisect import bisect_left
from decimal import Decimal
from functools import lru_cache
from typing import Mapping

from .campaign_development_score_v1 import UNITS

CALENDAR_PROFILE = "ck3-1.20.0.4-cdate-fixed365-raw24/v1"
RAW_EPOCH = 43_800_000
TICKS_PER_DAY = 24
MONTH_LENGTHS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
ANCHOR_KEYS = ("campaign_id", "founder_character_id", "founding_house_id", "founding_dynasty_id")


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _parts(date: str) -> tuple[int, int, int]:
    _need(isinstance(date, str), "CK3 date must be year.month.day")
    pieces = date.split(".")
    _need(len(pieces) == 3 and all(p.isascii() and p.isdecimal() for p in pieces),
          "CK3 date must be year.month.day")
    year, month, day = map(int, pieces)
    _need(1 <= year <= 9999 and 1 <= month <= 12
          and 1 <= day <= MONTH_LENGTHS[month - 1], "Invalid fixed-365 CK3 date")
    return year, month, day


def date_to_raw(date: str) -> int:
    year, month, day = _parts(date)
    return RAW_EPOCH + TICKS_PER_DAY * (year * 365 + sum(MONTH_LENGTHS[:month - 1]) + day - 1)


def raw_to_date(raw: int) -> str:
    _need(type(raw) is int and (raw - RAW_EPOCH) % TICKS_PER_DAY == 0,
          "A whole native CK3 day is required")
    year, index = divmod((raw - RAW_EPOCH) // TICKS_PER_DAY, 365)
    _need(1 <= year <= 9999, "CK3 year outside this positive-year cadence profile")
    month = 1
    for length in MONTH_LENGTHS:
        if index < length:
            return f"{year}.{month}.{index + 1}"
        month += 1
        index -= length
    raise ValueError("Invalid native day index")


@lru_cache(maxsize=16)
def month_boundaries(start_date: str, months: int = 360) -> tuple[tuple[str, int], ...]:
    """Baseline slot 0 plus months 1..360; preserve the founding day anchor.

    A starting day beyond a later month's end clamps only that month's sample;
    it never moves the founding day for subsequent months.
    """
    year, month, day = _parts(start_date)
    _need(type(months) is int and 1 <= months <= 360, "Cadence requires 1..360 months")
    rows = []
    for index in range(months + 1):
        target_year, target_month_zero = divmod(year * 12 + month - 1 + index, 12)
        target_month = target_month_zero + 1
        target_day = min(day, MONTH_LENGTHS[target_month_zero])
        target_date = f"{target_year}.{target_month}.{target_day}"
        rows.append((target_date, date_to_raw(target_date)))
    return tuple(rows)


def plan_advance_cap(current_raw: int, proposed_target_raw: int, *, start_date: str,
                     next_sample_index: int, months: int = 360) -> dict:
    """Plan an absolute cap; the owner must apply it to a native deadline.

    An unrecorded exact boundary requires its existing ordinary observation
    before another advance. Skipped slots stay missing: this helper does not
    fabricate a historic sample or prevent lawful continuation to the next one.
    """
    raw_to_date(current_raw)
    raw_to_date(proposed_target_raw)
    rows = month_boundaries(start_date, months)
    _need(current_raw >= rows[0][1] and proposed_target_raw > current_raw,
          "Advance must move forward from the campaign start")
    _need(type(next_sample_index) is int and 0 <= next_sample_index <= months + 1,
          "Invalid next sample slot")
    missed = []
    index = next_sample_index
    while index <= months and rows[index][1] < current_raw:
        missed.append(index)
        index += 1
    endpoint = rows[-1][1]
    result = {"calendar_profile": CALENDAR_PROFILE, "missed_sample_indices": missed,
              "endpoint_date_raw": endpoint, "new_clock_actions": 0,
              "native_deadline_still_required": True}
    if current_raw >= endpoint:
        return {**result, "status": "endpoint_due" if current_raw == endpoint else "endpoint_overshot",
                "next_sample_index": months, "target_date_raw": None}
    _need(index <= months, "A future sample slot is required before the endpoint")
    boundary = rows[index][1]
    return {**result, "status": "sample_due" if boundary == current_raw else "advance",
            "next_sample_index": index, "boundary_date_raw": boundary,
            "target_date_raw": None if boundary == current_raw else min(proposed_target_raw, boundary)}


def ordinary_sample_candidate(snapshot: Mapping, *, start_date: str, machine_id: str,
                              observed_at_utc: str, campaign_anchor: Mapping,
                              months: int = 360) -> dict | None:
    """Project only an already available ordinary semantic frame at a slot.

    The queue adds its actual response path/SHA after normal paired settlement.
    This is an incomplete scoring input, never a score or a query instruction.
    Primary-title heirs are not proven legal player heirs; net income is not
    gross income; direct county/domain counts are not quality-weighted realm.
    """
    _need(isinstance(snapshot, Mapping) and isinstance(campaign_anchor, Mapping), "Sample inputs must be objects")
    rows = month_boundaries(start_date, months)
    date_raw = snapshot.get("date_raw")
    _need(type(date_raw) is int, "Sample lacks native date")
    slot = bisect_left(rows, date_raw, key=lambda row: row[1])
    if slot == len(rows) or rows[slot][1] != date_raw:
        return None
    _need(snapshot.get("paused") is True, "A score sample requires the existing paused ordinary frame")
    _need(isinstance(machine_id, str) and bool(machine_id)
          and isinstance(observed_at_utc, str) and bool(observed_at_utc), "Sample requires actual machine/time")
    _need(isinstance(campaign_anchor.get("campaign_id"), str) and bool(campaign_anchor["campaign_id"])
          and type(campaign_anchor.get("founder_character_id")) is int
          and campaign_anchor["founder_character_id"] > 0, "A fixed founding campaign anchor is required")
    for key in ("snapshot_id", "revision", "native_revision"):
        _need(snapshot.get(key) is not None, "Sample lacks its ordinary frame binding")
    played = snapshot.get("played_character")
    played = played if isinstance(played, Mapping) else {}
    frame = {key: snapshot.get(key) for key in ("snapshot_id", "revision", "native_revision", "date_raw",
             "episode_run_id", "episode_character_id", "one_life_terminal", "one_life_terminal_reason")}
    frame.update(actor_character_id=played.get("character_id"), actor_alive=played.get("alive"), paused=True)
    metrics = {key: {"value": None, "unit": unit, "availability": "unknown", "source_ref": "ordinary_frame",
                     "reason_zh": "当前普通帧未提供同口径、同范围的该评分输入。"}
               for key, unit in UNITS.items()}
    gold = snapshot.get("played_character_gold")
    if isinstance(gold, Mapping) and type(gold.get("raw")) is int and gold.get("scale") == 100_000:
        metrics["gold"] = {"value": format(Decimal(gold["raw"]) / Decimal(100_000), "f"),
                           "unit": UNITS["gold"], "availability": "observed", "source_ref": "ordinary_frame"}
    wars = snapshot.get("active_wars")
    war_rows = None
    if isinstance(wars, list) and len(wars) <= 128 and all(isinstance(row, Mapping) for row in wars):
        war_rows = [{key: row.get(key) for key in ("war_id", "player_side", "primary_opponent_character_id",
                     "player_relative_war_score")} for row in wars]
    return {"schema": "xar.ck3.campaign-score-month-observation/v1", "calendar_profile": CALENDAR_PROFILE,
            "machine_id": machine_id, "observed_at_utc": observed_at_utc, "month_index": slot,
            "date": rows[slot][0], "date_raw": date_raw,
            "campaign_anchor": {key: campaign_anchor.get(key) for key in ANCHOR_KEYS},
            "baseline_date": rows[0][0], "baseline_date_raw": rows[0][1],
            "endpoint_date": rows[-1][0], "endpoint_date_raw": rows[-1][1],
            "frame": frame, "raw_metrics": metrics, "observed_player_wars": war_rows,
            "sources": [{"id": "ordinary_frame", "kind": "existing_ordinary_semantic_snapshot", "binding": frame}],
            "status": "OBSERVED_EXACT_SLOT_INCOMPLETE_SCORING_INPUT",
            "source_response_binding_pending": True, "new_RPC_calls": 0, "new_SAVE_exports": 0,
            "historic_slots_reconstructed": False, "score_or_complete_history_claimed": False}
