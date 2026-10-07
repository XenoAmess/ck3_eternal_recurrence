"""One new source-primitive/production-normalizer case; authored, not run."""

from xar_autoplayer.bridge.crown_authority_cooldown_clock_12004 import (
    NATIVE_DURATION_FACTORS_12004,
    interpret_crown_cooldown_native_clock_12004,
    scale_native_duration_literal_12004,
)
from xar_autoplayer.bridge.realm_law_paused_private_transport import (
    COOLDOWN_EXPIRY_TYPE,
    COOLDOWN_REMAINING_UNIT,
)


def test_actual_duration_factors_and_same_query_clock_meaning_12004():
    # Native token IDs, not invented mappings from English unit names.
    assert NATIVE_DURATION_FACTORS_12004 == ((1300, 1), (1301, 30), (1302, 365), (1327, 7))
    scales = (
        (1300, 13, 13),
        (1301, -3, -90),
        (1302, 20, 7300),
        (1327, 2, 14),
        (1302, 0, 0),
        (1302, 2147483647, 2147483283),
        (1327, -2147483648, -2147483648),
    )
    for token, literal, expected in scales:
        result = scale_native_duration_literal_12004(token, literal)
        assert result.accepted and result.clock_steps_i32 == expected
    rejected = scale_native_duration_literal_12004(0x1300, 20)
    assert not rejected.accepted and rejected.multiplier_i32 == 0
    assert rejected.clock_steps_i32 is None

    date = 53288232
    raw = {
        "read_available": True, "present": True, "timed": True,
        "expiry_raw": 7304, "current_clock_raw": 4, "remaining_raw": 7300,
        "retry_date_raw": None, "expiry_type": COOLDOWN_EXPIRY_TYPE,
        "remaining_unit": COOLDOWN_REMAINING_UNIT,
    }
    original = dict(raw)
    timed = interpret_crown_cooldown_native_clock_12004(raw, date_raw=date)
    assert timed.state == "timed" and timed.native_clock_deadline_raw == 7304
    assert timed.current_clock_raw == 4 and timed.remaining_native_clock_steps == 7300
    assert timed.remaining_native_clock_steps == scale_native_duration_literal_12004(1302, 20).clock_steps_i32
    assert timed.duration_token_factors == NATIVE_DURATION_FACTORS_12004
    assert not timed.keyword_names_qualified and not timed.calendar_deadline_ready
    assert timed.query_retry_date_raw is None and raw == original

    # A computed native-1 is not absence. Zero also retains a real deadline.
    for expiry, clock, remaining in ((7, 8, -1), (8, 8, 0), (0, -2147483648, -2147483648)):
        row = dict(raw, expiry_raw=expiry, current_clock_raw=clock, remaining_raw=remaining)
        observed = interpret_crown_cooldown_native_clock_12004(row, date_raw=date)
        assert observed.state == "timed" and observed.native_clock_deadline_raw == expiry
        assert observed.remaining_native_clock_steps == remaining
        assert not observed.calendar_deadline_ready and observed.query_retry_date_raw is None

    absent = interpret_crown_cooldown_native_clock_12004(
        dict(raw, present=False, timed=False, expiry_raw=None, remaining_raw=-1, retry_date_raw=date),
        date_raw=date,
    )
    assert absent.state == "absent" and absent.native_clock_deadline_raw is None
    assert absent.query_retry_date_raw == date and absent.remaining_native_clock_steps == -1
    untimed = interpret_crown_cooldown_native_clock_12004(
        dict(raw, timed=False, expiry_raw=-1, remaining_raw=-1), date_raw=date,
    )
    assert untimed.state == "untimed" and untimed.native_clock_deadline_raw is None
    assert untimed.query_retry_date_raw is None and untimed.remaining_native_clock_steps == -1
    unavailable = interpret_crown_cooldown_native_clock_12004(
        dict(raw, read_available=False, present=None, timed=None, expiry_raw=None,
             current_clock_raw=None, remaining_raw=None), date_raw=date,
    )
    assert unavailable.state == "unavailable" and unavailable.current_clock_raw is None
    assert unavailable.remaining_native_clock_steps is None and not unavailable.calendar_deadline_ready
