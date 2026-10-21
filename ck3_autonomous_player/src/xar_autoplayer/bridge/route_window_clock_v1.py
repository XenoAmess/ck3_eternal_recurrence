"""Frozen configuration for route_contact_window only; no live qualification."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, TypedDict

RouteWindowSpeedV1 = Literal[3, 4, 5]

class RouteWindowClockJsonV1(TypedDict):
    timeline_speed: RouteWindowSpeedV1
    research_high_speed_ab: bool

def _speed(value: object) -> RouteWindowSpeedV1:
    if type(value) is not int:
        raise ValueError("route-window speed must be an exact integer")
    if value == 3:
        return 3
    if value == 4:
        return 4
    if value == 5:
        return 5
    raise ValueError("route-window speed must be 3, 4, or 5")

def _permission(value: object) -> bool:
    if not isinstance(value, bool):
        raise ValueError("route-window A/B permission must be an exact boolean")
    return value

@dataclass(frozen=True, slots=True)
class RouteWindowClockConfigV1:
    timeline_speed: RouteWindowSpeedV1 = 3
    research_high_speed_ab: bool = False

    def __post_init__(self) -> None:
        speed = _speed(self.timeline_speed)
        admitted = _permission(self.research_high_speed_ab)
        if speed > 3 and admitted is not True:
            raise ValueError("route-window speed 4/5 requires explicit research A/B")

DEFAULT_ROUTE_WINDOW_CLOCK_V1 = RouteWindowClockConfigV1()

def validate_route_window_clock_v1(value: object) -> RouteWindowClockConfigV1:
    if not isinstance(value, RouteWindowClockConfigV1) or type(value) is not RouteWindowClockConfigV1:
        raise ValueError("route-window clock must use the shared frozen model")
    return RouteWindowClockConfigV1(_speed(value.timeline_speed),
                                  _permission(value.research_high_speed_ab))

def parse_route_window_clock_v1(value: object) -> RouteWindowClockConfigV1:
    # This is the sole dynamic JSON boundary. Values are individually validated
    # before constructing the internal model; missing/null never mean default.
    if not isinstance(value, dict) or set(value) != {"timeline_speed", "research_high_speed_ab"}:
        raise ValueError("route-window JSON requires exactly its two canonical fields")
    return RouteWindowClockConfigV1(_speed(value["timeline_speed"]),
                                  _permission(value["research_high_speed_ab"]))

def route_window_clock_json_v1(value: RouteWindowClockConfigV1) -> RouteWindowClockJsonV1:
    checked = validate_route_window_clock_v1(value)
    return {"timeline_speed": checked.timeline_speed,
            "research_high_speed_ab": checked.research_high_speed_ab}
