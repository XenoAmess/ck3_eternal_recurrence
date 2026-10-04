"""Offline projection of the exact .3 calendar/bucket clock, not troop or cash updates.

Inputs are admitted dates and an optional observed ArmyManager bucket.  The
calendar tables are the native bytes sealed by source-clock-new-spans and embedded here.  No
Army ID is converted to a bucket here: registration is a separate source gap.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

EPOCH_RAW = 0x29C55C0
CALENDAR_SOURCE = 'embedded exact 1.20.0.3 native365day tables'
DAY_TABLE_HEX = '000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e000102030405060708090a0b0c0d0e0f101112131415161718191a1b000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e'
MONTH_TABLE_HEX = '000000000000000000000000000000000000000000000000000000000000000101010101010101010101010101010101010101010101010101010102020202020202020202020202020202020202020202020202020202020202030303030303030303030303030303030303030303030303030303030303040404040404040404040404040404040404040404040404040404040404040505050505050505050505050505050505050505050505050505050505050606060606060606060606060606060606060606060606060606060606060607070707070707070707070707070707070707070707070707070707070707080808080808080808080808080808080808080808080808080808080808090909090909090909090909090909090909090909090909090909090909090a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b'


def trunc0(numerator: int, denominator: int) -> int:
    return (1 if numerator >= 0 else -1) * (abs(numerator) // denominator)


def signed32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value if value < 0x80000000 else value - 0x100000000


def native_tables() -> tuple[bytes, bytes]:
    return bytes.fromhex(DAY_TABLE_HEX), bytes.fromhex(MONTH_TABLE_HEX)


def preview(current_raw: int, admitted_days: int, observed_army_bucket: int | None = None) -> dict:
    day_table, month_table = native_tables()
    rows = []
    for ordinal in range(1, admitted_days + 1):
        next_raw = signed32(current_raw + ordinal * 24)
        native_day = trunc0(signed32(next_raw - EPOCH_RAW), 24)
        year_day = native_day % 365
        bucket = (native_day & 0xFFFFFFFF) % 30
        month_first = day_table[year_day] == 0
        order = []
        if month_first:
            order.append('pre: prepare persistent monthly fraction cache')
        order.append('admit: date+24 and GameState+9C')
        if month_first:
            order.extend(('post: regular persistent integer fill', 'post: refresh raised/army strengths'))
        order.append('post: select actual ArmyManager day bucket')
        rows.append({
            'prospective_day': ordinal,
            'date_raw': next_raw,
            'native_day': native_day,
            'year_day_index': year_day,
            'month_index': month_table[year_day],
            'day_of_month_index': day_table[year_day],
            'calendar_month_first': month_first,
            'actual_manager_bucket_phase': bucket,
            'observed_army_bucket': observed_army_bucket,
            'army_selected_by_bucket': None if observed_army_bucket is None else bucket == observed_army_bucket,
            'ordered_clock_stages': order,
        })
    return {
        'schema': 'ck3.exact_12003.offline_native_clock_preview.v1',
        'qualification': 'prospective clock only; no execution, soldiers, supply amount, or cash posting prediction',
        'current_date_raw': current_raw,
        'prospective_admitted_days': admitted_days,
        'observed_army_bucket': observed_army_bucket,
        'calendar_table_source': CALENDAR_SOURCE,
        'calendar_day_native_sha256': '49cfa7734c595821c26db19fac8d0427fa12adc3e8988e04e0d94198d8f35517',
        'calendar_month_native_sha256': '218539a9f584e576a0912771d97ac39c5042fc9169e2b5d250069a88d1478f0a',
        'rows': rows,
        'unprojected_inputs': [
            'actual ArmyManager bucket membership when not supplied',
            'prepared persistent fraction and every eligible chunk at execution',
            'native supply success/date-anchor/grace inputs',
            'siege/raid loss inputs and cash posting clock',
        ],
        'new_actual_days': 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--current-raw', type=int, required=True)
    parser.add_argument('--days', type=int, required=True)
    parser.add_argument('--observed-army-bucket', type=int)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = preview(args.current_raw, args.days, args.observed_army_bucket)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
