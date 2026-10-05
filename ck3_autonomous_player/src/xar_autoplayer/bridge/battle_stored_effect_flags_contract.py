"""Optional observed raw loaded effect bytes used by nested19F membership."""

from __future__ import annotations


def normalize_stored_effect_flags_v1(value: object, *, field: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {
        'status', 'flag88_raw', 'flag89_raw', 'unavailable_reason',
    }:
        raise ValueError(f'{field} has invalid effect flag fields')
    status, raw88, raw89, reason = (value[name] for name in
        ('status', 'flag88_raw', 'flag89_raw', 'unavailable_reason'))
    if status == 'available':
        if (type(raw88) is not int or not 0 <= raw88 <= 255
                or type(raw89) is not int or not 0 <= raw89 <= 255 or reason is not None):
            raise ValueError(f'{field} available flags require raw uint8 and null reason')
    elif (status != 'unavailable' or raw88 is not None or raw89 is not None
          or not isinstance(reason, str) or not reason):
        raise ValueError(f'{field} unavailable flags require nulls and reason')
    return {'status': status, 'flag88_raw': raw88, 'flag89_raw': raw89, 'unavailable_reason': reason}
