"""Bounded, read-only CK3 1.19.0.6 MAA refresh witness for RegimentID 87.

This proves one cached-versus-current observation and selected exact-build
input-routing instructions. It does not identify a modifier that caused it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pefile


EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
DATA = Path(__file__).resolve().parents[1] / "src/xar_autoplayer/simulation/data"
FIXTURES = {
    11: (
        "ck3_1_19_0_6_episode01_messina_daily_stat_refresh_day11_v1.json",
        "E36224201492080046FE37E6C27653B6F38D8C7B97651BBEC86EC718A8A3AB06",
        "ck3_1_19_0_6_episode01_messina_paused_stat_eval_day11_v1.json",
        "70940B9F47392EEF8953014EC0095B2AD5F2BFF14B6B3679926CF10E01D35F98",
        53146488,
    ),
    21: (
        "ck3_1_19_0_6_episode01_messina_daily_stat_refresh_day21_v1.json",
        "26569235A6B1507B6693E381335A46B56F632E2D6F9DD0B9D825A2C46F8833AE",
        "ck3_1_19_0_6_episode01_messina_paused_stat_eval_day21_v1.json",
        "2A52B38050D1882FE5D4F34C0221B9A4FB5415C6B8D1BC19FF38879BE3A023DA",
        53146728,
    ),
}
SITES = {
    0x239CCD4: "4533c9",  # standard CRegiment evaluator: xor r9d,r9d
    0x239CCDC: "4c8bc6",  # r8 = target Province* saved in rsi
    0x239CCE2: "e8b9248f00",  # call 0x2C8F1A0
    0x2C8F1CD: "4d8be1",  # r12 = r9, optional extra context
    0x2C8F1D6: "4c8baa18010000",  # type = CRegiment+0x118
    0x2C8F35E: "4c8b8b20010000",  # r9 = CRegiment+0x120 to base helper
    0x2C8F36C: "e81ff7ffff",  # call type/base helper 0x2C8EA90
    0x2C8F792: "4d85e4",  # optional r12 branch
    0x2C8F795: "741a",  # zero skips 0x2C91060 extra-context merger
    0x2C8F7B9: "e8323673ff",  # call 0x23C2DF0 fixed-point applier
    0x2C8F8E2: "488b85d0070000",  # original r8 target Province*
    0x2C8F8E9: "488b4020",  # target+0x20
    0x2C8F8ED: "488b80b8000000",  # target subobject+0xB8
    0x2C8F8FF: "e80c92ffff",  # call 0x2C88B10, six-stat contribution
    0x2C8FA78: "4c8badd0070000",  # original r8 again
    0x2C8FA7F: "4d8bad28060000",  # target+0x628 optional subobject
}


def _verified_json(name: str, expected_sha: str) -> dict:
    raw = (DATA / name).read_bytes()
    actual = hashlib.sha256(raw).hexdigest().upper()
    if actual != expected_sha:
        raise ValueError(f"frozen fixture changed: {name}: {actual}")
    return json.loads(raw)


def _one(rows: list[dict]) -> dict:
    selected = [r for r in rows if r.get("regiment_id") == 87 and r.get("side_index") == 0]
    if len(selected) != 1:
        raise ValueError(f"expected one side-0 RegimentID 87, got {len(selected)}")
    return selected[0]


def project(exe: Path) -> dict:
    raw = exe.read_bytes()
    actual = hashlib.sha256(raw).hexdigest().upper()
    if actual != EXE_SHA256:
        raise ValueError(f"unexpected ck3.exe SHA-256: {actual}")
    pe = pefile.PE(data=raw, fast_load=True)
    for rva, expected_hex in SITES.items():
        expected = bytes.fromhex(expected_hex)
        if pe.get_data(rva, len(expected)) != expected:
            raise ValueError(f"exact-build source-routing instruction changed at {rva:#x}")

    cases = []
    for day, (refresh_name, refresh_sha, direct_name, direct_sha, expected_date) in FIXTURES.items():
        refresh = _verified_json(refresh_name, refresh_sha)
        direct = _verified_json(direct_name, direct_sha)
        if (refresh.get("date_raw"), direct.get("date_raw")) != (expected_date, expected_date):
            raise ValueError(f"source date changed on day {day}")
        if (refresh.get("combat_id"), direct.get("combat_id")) != (16777218, 16777218):
            raise ValueError(f"CombatID changed on day {day}")
        old_new = _one(refresh["changed_regiments"])
        parity = _one(direct["per_regiment_comparison"])
        if parity["kind"] != "men_at_arms":
            raise ValueError(f"RegimentID 87 is not MAA on day {day}")
        expected = {
            "old_damage_raw": 4500000,
            "new_damage_raw": 4500000,
            "old_toughness_raw": 2500000,
            "new_toughness_raw": 2625000,
        }
        if any(old_new[k] != v for k, v in expected.items()):
            raise ValueError(f"cached/schedule vector changed on day {day}")
        for name, source_key in (
            ("old_cached_damage_raw", "old_damage_raw"),
            ("old_cached_toughness_raw", "old_toughness_raw"),
            ("paused_direct_damage_raw", "new_damage_raw"),
            ("paused_direct_toughness_raw", "new_toughness_raw"),
            ("next_schedule_damage_raw", "new_damage_raw"),
            ("next_schedule_toughness_raw", "new_toughness_raw"),
        ):
            if parity[name] != old_new[source_key]:
                raise ValueError(f"direct/schedule parity changed on day {day}: {name}")
        cases.append({
            "source_day": day,
            "date_raw": expected_date,
            "regiment_id": 87,
            "kind": "men_at_arms",
            "side_index": 0,
            **expected,
            "paused_direct_equals_schedule": True,
        })

    old = cases[0]["old_toughness_raw"]
    new = cases[0]["new_toughness_raw"]
    if old * 105000 // 100000 != new or old + 125000 != new:
        raise ValueError("illustrative arithmetic witnesses changed")
    return {
        "schema": "ck3.maa_regiment87_refresh_source_boundary.v1",
        "game_build": "1.19.0.6",
        "exe_sha256": EXE_SHA256,
        "combat_id": 16777218,
        "cases": cases,
        "toughness_delta_raw": new - old,
        "relative_delta_percent": 5,
        "arithmetic_witnesses_only": ["2500000*105000/100000=2625000", "2500000+125000=2625000"],
        "standard_r9_optional_context_zero": True,
        "target_province_six_stat_path_reachable": True,
        "specific_modifier_cause_proven": False,
        "other_changed_maa_explained": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(project(args.exe), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
