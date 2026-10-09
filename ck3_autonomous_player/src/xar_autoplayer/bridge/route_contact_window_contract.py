"""Explicit bounded route advancement using existing same-frame timelines."""

from .public_unit_contract import canonical_public_cunit_decimal, public_cunit_id

ADVANCE_ROUTE_CONTACT_WINDOW_STEP_PREFIX = "advance-route-contact-window-v1-"


def advance_route_contact_window_step(
    subject_army_id: int, target_province_id: int, hostile_army_ids: object,
    *, horizon_days: int = 3,
) -> str:
    subject = public_cunit_id(subject_army_id, "subject_army_id")
    if type(target_province_id) is not int or not 0 < target_province_id < 2**31:
        raise ValueError("target_province_id must be positive int32")
    if type(horizon_days) is not int or horizon_days not in {2, 3}:
        raise ValueError("route window must be two or three days")
    if not isinstance(hostile_army_ids, (tuple, list, set)):
        raise ValueError("hostile_army_ids must be a complete sequence")
    hostiles = sorted({public_cunit_id(value, "hostile_army_id")
                       for value in hostile_army_ids})
    if not 0 < len(hostiles) <= 64 or subject in hostiles:
        raise ValueError("route window hostile scope is malformed")
    return (f"{ADVANCE_ROUTE_CONTACT_WINDOW_STEP_PREFIX}{subject}-to-"
            f"{target_province_id}-days-{horizon_days}-h-{len(hostiles)}-"
            + "-".join(map(str, hostiles)))


def parse_advance_route_contact_window_step(
    step: object,
) -> tuple[int, int, tuple[int, ...], int] | None:
    if not isinstance(step, str) or not step.startswith(ADVANCE_ROUTE_CONTACT_WINDOW_STEP_PREFIX):
        return None
    parts = step.removeprefix(ADVANCE_ROUTE_CONTACT_WINDOW_STEP_PREFIX).split("-")
    if len(parts) < 8 or parts[1] != "to" or parts[3] != "days" or parts[5] != "h":
        return None
    numbers = (parts[0], parts[2], parts[4], parts[6], *parts[7:])
    if not all(canonical_public_cunit_decimal(value) for value in numbers):
        return None
    subject, target, days, count, *hostiles = map(int, numbers)
    if count != len(hostiles):
        return None
    try:
        canonical = advance_route_contact_window_step(subject, target, hostiles, horizon_days=days)
    except ValueError:
        return None
    if canonical != step:
        return None
    return subject, target, tuple(hostiles), days
