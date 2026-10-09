"""Project a bounded window from the complete, current native route timelines.

The caller binds the normalized H1 result to its paused frame. This projection
does not change H1's one-day predicate: it repeats the native interval and edge
comparison over at most three days while the published routes remain fixed.
"""

from __future__ import annotations

from collections.abc import Mapping


_INT32_MIN = -(2**31)
_INT32_MAX = 2**31 - 1
_RAW_UNITS_PER_DAY = 24


def _int32(value: object) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and _INT32_MIN <= value <= _INT32_MAX
    )


def _intervals(
    route: Mapping[str, object], start: int, end: int,
) -> tuple[list[tuple[int, int, int]], list[tuple[int, int, int, int]]]:
    provinces = route["route_province_ids"]
    arrivals = route["arrival_date_raws"]
    current = route["current_province_id"]
    occupancy = [(current, start, arrivals[0] if arrivals else end)]
    edges = []
    origin, depart = current, start
    for index, (target, arrive) in enumerate(zip(provinces, arrivals)):
        edges.append((origin, target, depart, arrive))
        leave = arrivals[index + 1] if index + 1 < len(arrivals) else end
        occupancy.append((target, arrive, leave))
        origin, depart = target, arrive
    return occupancy, edges


def _overlap(
    left_start: int, left_end: int, right_start: int, right_end: int,
    start: int, end: int,
) -> tuple[int, int] | None:
    enter = max(left_start, right_start, start)
    leave = min(left_end, right_end, end)
    return (enter, leave) if enter <= leave else None


def project_route_contact_window_v1(
    horizon: object, *, horizon_days: int = 3,
) -> dict[str, object]:
    """Recompute closed province/edge contacts from a normalized H1 result.

    The interval construction matches ``ck3_12002_routes.cpp:816-916``. It
    predicts contacts on the routes held in this frame; subsequent native route,
    arrival, combat and pause observations determine actual progress.
    """
    if (
        isinstance(horizon_days, bool)
        or not isinstance(horizon_days, int)
        or not 1 <= horizon_days <= 3
    ):
        raise ValueError("route contact window must contain one to three days")
    result: dict[str, object] = {
        "status": "unavailable",
        "context_basis": "frozen_current_routes",
        "horizon_days": horizon_days,
        "window_start_date_raw": None,
        "window_end_date_raw": None,
        "contact_free": None,
        "conflicts": [],
        "first_contact_date_raw": None,
        "contact_free_whole_days": 0,
        "missing": [],
    }
    missing: list[str] = []
    if not isinstance(horizon, Mapping) or horizon.get("status") != "available":
        result["missing"] = ["available_route_contact_horizon"]
        return result
    start = horizon.get("date_raw")
    if not _int32(start) or start + horizon_days * _RAW_UNITS_PER_DAY > _INT32_MAX:
        result["missing"] = ["date_raw"]
        return result
    end = start + horizon_days * _RAW_UNITS_PER_DAY
    result["window_start_date_raw"] = start
    result["window_end_date_raw"] = end
    subject = horizon.get("subject_route")
    hostiles = horizon.get("hostile_routes")
    hostile_ids = horizon.get("hostile_army_ids")
    if not isinstance(subject, Mapping):
        missing.append("subject_route")
    if not isinstance(hostiles, list) or not isinstance(hostile_ids, list):
        missing.append("hostile_routes")
        hostiles = []
    elif (
        not hostile_ids
        or len(hostiles) != len(hostile_ids)
        or any(
            not isinstance(route, Mapping) or route.get("army_id") != army_id
            for route, army_id in zip(hostiles, hostile_ids)
        )
    ):
        missing.append("complete_hostile_routes")
    for name, route in [("subject_route", subject), *[
        (f"hostile_routes[{index}]", route)
        for index, route in enumerate(hostiles)
    ]]:
        if not isinstance(route, Mapping):
            if name not in missing:
                missing.append(name)
            continue
        provinces = route.get("route_province_ids")
        arrivals = route.get("arrival_date_raws")
        if (
            route.get("timeline_observable") is not True
            or not _int32(route.get("current_province_id"))
            or route["current_province_id"] <= 0
            or not isinstance(provinces, list)
            or not isinstance(arrivals, list)
            or len(provinces) != len(arrivals)
            or any(not _int32(province) or province <= 0 for province in provinces)
            or any(not _int32(arrival) or arrival < start for arrival in arrivals)
            or any(left > right for left, right in zip(arrivals, arrivals[1:]))
        ):
            missing.append(f"{name}.complete_timeline")
    if missing:
        result["missing"] = missing
        return result

    subject_occupancy, subject_edges = _intervals(subject, start, end)
    conflicts: list[dict[str, object]] = []
    for hostile in hostiles:
        hostile_occupancy, hostile_edges = _intervals(hostile, start, end)
        for left_province, left_enter, left_leave in subject_occupancy:
            for right_province, right_enter, right_leave in hostile_occupancy:
                overlap = _overlap(
                    left_enter, left_leave, right_enter, right_leave, start, end,
                )
                if left_province == right_province and overlap is not None:
                    conflict = {
                        "kind": "same_province",
                        "hostile_army_id": hostile["army_id"],
                        "province_id": left_province,
                        "overlap_start_date_raw": overlap[0],
                        "overlap_end_date_raw": overlap[1],
                    }
                    if conflict not in conflicts:
                        conflicts.append(conflict)
        for left_from, left_to, left_depart, left_arrive in subject_edges:
            for right_from, right_to, right_depart, right_arrive in hostile_edges:
                overlap = _overlap(
                    left_depart, left_arrive, right_depart, right_arrive, start, end,
                )
                if left_from == right_to and left_to == right_from and overlap is not None:
                    conflict = {
                        "kind": "opposing_edge",
                        "hostile_army_id": hostile["army_id"],
                        "subject_from_province_id": left_from,
                        "subject_to_province_id": left_to,
                        "hostile_from_province_id": right_from,
                        "hostile_to_province_id": right_to,
                        "overlap_start_date_raw": overlap[0],
                        "overlap_end_date_raw": overlap[1],
                    }
                    if conflict not in conflicts:
                        conflicts.append(conflict)
    first_contact = min(
        (conflict["overlap_start_date_raw"] for conflict in conflicts),
        default=None,
    )
    result.update({
        "status": "available",
        "contact_free": not conflicts,
        "conflicts": conflicts,
        "first_contact_date_raw": first_contact,
        "contact_free_whole_days": horizon_days if first_contact is None else max(
            0, min(horizon_days, (first_contact - start - 1) // _RAW_UNITS_PER_DAY),
        ),
    })
    return result
