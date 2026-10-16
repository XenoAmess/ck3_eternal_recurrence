"""Spend one observed point in any authored lifestyle using native final legality."""

from __future__ import annotations

from typing import Mapping

from .all_lifestyle_catalog_v1 import LIFESTYLE_KEYS, authored_perks


def _nonnegative(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _progress(snapshot: Mapping[str, object]) -> tuple[dict[str, dict], bool] | None:
    observed = snapshot.get("all_lifestyle_progress_v3")
    if not isinstance(observed, Mapping) or observed.get("status") not in {"complete", "partial"}:
        return None
    for field, original in (
        ("snapshot_id", "snapshot_id"), ("native_revision", "native_revision"),
        ("date_raw", "date_raw"), ("player_character_id", "player_character_id"),
        ("episode_run_id", "episode_run_id"),
    ):
        if observed.get(field) != snapshot.get(original):
            return None
    rows = observed.get("rows")
    if not isinstance(rows, list) or len(rows) != len(LIFESTYLE_KEYS):
        return None
    by_lifestyle: dict[str, dict] = {}
    incomplete = False
    for row in rows:
        if not isinstance(row, Mapping) or row.get("lifestyle_key") not in LIFESTYLE_KEYS:
            return None
        key = row["lifestyle_key"]
        if key in by_lifestyle:
            return None
        status = row.get("status")
        if status == "unavailable":
            if not isinstance(row.get("unavailable_reason"), str) or not row["unavailable_reason"]:
                return None
            incomplete = True
        elif status == "available":
            fields = ("xp_total_raw", "xp_within_level_raw", "xp_per_level",
                      "unspent_perk_points", "used_perk_points")
            if not all(_nonnegative(row.get(name)) for name in fields):
                return None
            if row["xp_per_level"] == 0 or row["xp_within_level_raw"] >= row["xp_per_level"] * 100000:
                return None
        else:
            return None
        by_lifestyle[key] = dict(row)
    if set(by_lifestyle) != LIFESTYLE_KEYS or incomplete == (observed["status"] == "complete"):
        return None
    return by_lifestyle, incomplete


def choose_all_lifestyle_perk_v3(
    snapshot: Mapping[str, object], binding: Mapping[str, object],
    owned: list[str],
) -> dict[str, object]:
    """Return a recommendation only for a same-frame, positive-point legal target.

    A missing progress class is unknown rather than zero. Native chooses the
    single final-legal target after reading all six classes. This consumer only
    authorizes that exact target, never its own inferred parent/availability.
    """
    parsed = _progress(snapshot)
    if parsed is None:
        return {"status": "observation_unavailable", "reason": "all_lifestyle_progress_binding_invalid"}
    progress, incomplete = parsed
    catalogue = authored_perks()
    candidates = snapshot.get("legal_perk_candidates")
    if (not isinstance(candidates, Mapping)
            or candidates.get("status") != "available"
            or candidates.get("scope") != "policy_target"):
        return {"status": "legal_candidates_unavailable"}
    items = candidates.get("items")
    if not isinstance(items, list) or len(items) > 1:
        return {"status": "legal_candidates_unavailable", "reason": "policy_target_cardinality_invalid"}
    if not items:
        if incomplete:
            return {"status": "observation_unavailable", "reason": "progress_partial_no_target",
                    "unavailable_lifestyles": sorted(key for key, row in progress.items()
                                                     if row["status"] == "unavailable")}
        positive = {key: row["unspent_perk_points"] for key, row in progress.items()
                    if row["unspent_perk_points"] > 0}
        return {"status": "no_legal_minimum",
                "reason": "native_final_legal_none_with_unspent_points" if positive
                else "no_unspent_points_across_all_lifestyles",
                "observed_positive_points": positive}
    target = items[0]
    if not isinstance(target, Mapping):
        return {"status": "legal_candidates_unavailable"}
    key, lifestyle = target.get("key"), target.get("lifestyle_key")
    if not isinstance(key, str) or catalogue.get(key) != lifestyle:
        return {"status": "observation_unavailable", "reason": "target_outside_authored_lifestyle"}
    row = progress[lifestyle]
    if row["status"] != "available" or row["unspent_perk_points"] <= 0:
        return {"status": "observation_unavailable", "reason": "target_progress_not_positive"}
    if key in owned:
        return {"status": "observation_unavailable", "reason": "native_legal_target_already_owned"}
    return {
        "status": "recommend_action",
        "selected_action": {
            "kind": "perk", "target_key": key, "target_lifestyle_key": lifestyle,
            "expected": dict(binding),
            "reason": "all_lifestyle_native_final_legal_with_observed_point",
        },
        "progress_status": "partial" if incomplete else "complete",
        "observed_target_points": row["unspent_perk_points"],
    }
