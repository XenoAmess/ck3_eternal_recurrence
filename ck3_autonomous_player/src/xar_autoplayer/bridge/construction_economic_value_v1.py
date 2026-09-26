"""Narrow 1.19.0.6 authored province monthly-income values for new buildings.

The key is copied from the native legal CBuildingType in the current paused
frame. These are script values, not observed character tax or promised ROI.
Sources: game/common/buildings/00_standard_economy_buildings.txt SHA-256
355445C46F70B9015A5E2BE68EE9DDC1F4E3EEB8BE368D34A37FD8A8CC0F7153;
game/common/script_values/00_building_values.txt SHA-256
F436F7D9D5AC5506B38D715F0CE02C4F4257EEF3ADDF56597C18A526A6F66825.
"""

from __future__ import annotations


# Only new tier-one economic buildings whose province_modifier contains an
# unconditional positive monthly_income. Conditional extra effects are omitted.
_AUTHOR_MONTHLY_INCOME_HUNDREDTHS = {
    **dict.fromkeys(("caravanserai_01", "watermills_01", "windmills_01",
                     "farm_estates_01"), 70),
    **dict.fromkeys(("paddy_fields_01", "cereal_fields_01"), 50),
    **dict.fromkeys(("murex_farm_01", "spice_plantation_01",
                     "common_tradeport_01", "pastures_01", "orchards_01",
                     "logging_camps_01", "peat_quarries_01", "hill_farms_01",
                     "elephant_pens_01"), 35),
    **dict.fromkeys(("qanats_01", "hunting_grounds_01", "plantations_01",
                     "quarries_01"), 25),
}


def authored_monthly_income_hundredths(building_key: object) -> int | None:
    if not isinstance(building_key, str):
        return None
    return _AUTHOR_MONTHLY_INCOME_HUNDREDTHS.get(building_key)
