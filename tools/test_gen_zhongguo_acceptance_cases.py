#!/usr/bin/env python3
"""Deterministic contract tests for the ZhongGuo 361 live batch fixture."""

from __future__ import annotations

import re

import gen_zhongguo_acceptance_cases as generator


def main() -> int:
    payload = generator.render()
    assert payload.startswith(generator.BOM)
    text = payload.decode("utf-8-sig")
    case_ids = [
        int(value)
        for value in re.findall(r'ZGA: MECHANISM CASE PASS (\d{3})"', text)
    ]
    assert case_ids == list(range(1, 362)), case_ids
    assert text.count("ZGA: MECHANISM LEDGER PASS") == 1
    assert text.count("ZGA: MECHANISM IDEMPOTENCE PASS") == 1
    assert text.count("ZG361_adopt_reference_charter_effect") == 0
    assert text.count("zg361_adopt_reference_charter_effect = yes") == 2
    assert len(re.findall(r"has_variable = zg361_sb_m_\d{2}_char", text)) == generator.SCOREBOARD_SLOT_COUNT
    assert len(re.findall(r"ZGA: DATA player_scoreboard_row \d{2}", text)) == generator.SCOREBOARD_SLOT_COUNT
    for field in ("title", "promotion", "pip"):
        assert len(re.findall(rf"has_variable = zg361_sb_m_\d{{2}}_{field}", text)) == generator.SCOREBOARD_SLOT_COUNT
    expected_checksum, expected_ledgers = generator.expected_portfolio()
    assert f"var:zg361_mechanism_checksum = {expected_checksum}" in text
    for ledger, value in expected_ledgers.items():
        assert f"var:zg361_org_{ledger} = {value}" in text
    assert generator.main(["--check"]) == 0
    print("GREEN: ZhongGuo 361 live fixture generator contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
