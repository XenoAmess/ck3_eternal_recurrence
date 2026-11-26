"""Check custom wars that retain the previous NWar ticking values."""

from __future__ import annotations

from extract_auto_upgrade_buildings import Block, Entry


# Florin documents zero for omitted CB ticking values, even though the NWar
# defines still contain the earlier daily rates and delays.
_LEGACY_TIMING: tuple[tuple[Entry, str], ...] = (
    (Entry("attacker_ticking_warscore", "=", "0.055"), "0.055 per day"),
    (Entry("defender_ticking_warscore", "=", "0.055"), "0.055 per day"),
    (Entry("attacker_ticking_warscore_delay", "=", Block((Entry("days", "=", "0"),))), "0 days"),
    (Entry("defender_ticking_warscore_delay", "=", Block((Entry("days", "=", "365"),))), "365 days"),
)


def legacy_ticking_warscore_errors(cb: Block) -> list[str]:
    errors: list[str] = []
    for expected, description in _LEGACY_TIMING:
        entries = tuple(entry for entry in cb.entries if entry.key == expected.key)
        if entries != (expected,):
            errors.append(f"{expected.key} must explicitly preserve {description}")
    return errors
