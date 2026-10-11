"""Narrow exact-build authored province monthly-income values for buildings.

The key is copied from the native legal CBuildingType in the current paused
frame. These are script values, not observed character tax or promised ROI.
Sources: game/common/buildings/00_standard_economy_buildings.txt SHA-256
355445C46F70B9015A5E2BE68EE9DDC1F4E3EEB8BE368D34A37FD8A8CC0F7153;
game/common/script_values/00_building_values.txt SHA-256
F436F7D9D5AC5506B38D715F0CE02C4F4257EEF3ADDF56597C18A526A6F66825.
For 1.20.0.2, research/ck3_12002_construction_authored_income.json verifies
the same 19 keys and values against standard-economy SHA-256
33A6253E89ACD0DA1C0242BD441987817DC5386325694F92BBE635F657FBD0E8
and the unchanged building-values file. Effective costs always come from
the current native result, never the authored base-cost value.

The .3 existing-slot values below are the direct, unconditional authored
income for keys observed in Robert's raw53220624 material. They allow a
replacement to be compared with its actual occupant; conditional modifiers
and realised player/province tax remain separate observations.
Exact .3 additional definitions, all under game/common/buildings:
00_standard_economy_buildings.txt: farm_estates_02 line6631 and
common_tradeport_02 line4452, SHA-256
33A6253E89ACD0DA1C0242BD441987817DC5386325694F92BBE635F657FBD0E8;
00_standard_fortification_buildings.txt: curtain_walls_01 line582, SHA-256
30BB06D594F4059F2E5682BF551BF046F6ED237C6ED104DB4EA685EC96F81DFE;
00_temple_buildings.txt: monastic_schools_01 line4144, SHA-256
8425510998E7FA6700C0902A132EE65015FDB7E81006BD676C97AD47F3589B47;
00_standard_military_buildings.txt: military_camps_01 line2442, SHA-256
D40C015E0CF240B830D83C2CA8FC38190EAB2C5D4D8492D044DB8F1AED6B20C4.
The shared script-values SHA-256 above is unchanged. Actual frame/key proof
and noncash-effect limits are recorded in the native construction topic.

The actual 1.20.0.4 Steam build 25734779 reuses the accepted .3 table through
installed content depot 1158311, manifest 5078208590259867811, also containing
game/common/buildings. This is retained content-depot evidence, not a new local
file hash or a new review of the original 1.19.0.6 / .2 table. Actual .4 native
cost, legality and slot operands have separate finite executable source proof.
The explicit .4 economic upgrade targets through tier eight use the exact
excellent/normal/poor tax declarations and aliases in the same script-values file.
Their unconditional income also supplies the existing-slot comparison; it is
not observed effective tax, conditional income, completion or realised ROI.
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

# Exact .3 keys from the actual completed inventory. Target eligibility remains
# the tier-one table above on older builds. Actual .4 additionally reuses
# the two economic tier-two values as targets; other .3 keys stay old-slot only.
_AUTHOR_EXISTING_MONTHLY_INCOME_HUNDREDTHS_12003 = {
    **_AUTHOR_MONTHLY_INCOME_HUNDREDTHS,
    "farm_estates_02": 115,
    "common_tradeport_02": 55,
    "curtain_walls_01": 25,
    "monastic_schools_01": 25,
    "military_camps_01": 0,
}

# Explicit actual .4 upgrade targets and same-key existing-slot values.
# Preserve the older-build dictionaries; these values close the declared
# excellent/normal/poor aliases individually; no extrapolated income curve.
_AUTHOR_UPGRADE_MONTHLY_INCOME_HUNDREDTHS_12004 = {
    "farm_estates_02": 115,
    "farm_estates_03": 160,
    "farm_estates_04": 205,
    "farm_estates_05": 250,
    "farm_estates_06": 295,
    "farm_estates_07": 340,
    "farm_estates_08": 385,
    "common_tradeport_02": 55,
    "common_tradeport_03": 75,
    "common_tradeport_04": 95,
    "common_tradeport_05": 115,
    "common_tradeport_06": 135,
    "common_tradeport_07": 155,
    "common_tradeport_08": 175,
    "pastures_02": 55,
    "pastures_03": 75,
    "pastures_04": 95,
    "pastures_05": 115,
    "pastures_06": 135,
    "pastures_07": 155,
    "pastures_08": 175,
    "orchards_02": 55,
    "orchards_03": 75,
    "orchards_04": 95,
    "orchards_05": 115,
    "orchards_06": 135,
    "orchards_07": 155,
    "orchards_08": 175,
    "hunting_grounds_02": 40,
    "hunting_grounds_03": 55,
    "hunting_grounds_04": 70,
    "hunting_grounds_05": 85,
    "hunting_grounds_06": 100,
    "hunting_grounds_07": 115,
    "hunting_grounds_08": 130,
    "plantations_02": 40,
    "plantations_03": 55,
    "plantations_04": 70,
    "plantations_05": 85,
    "plantations_06": 100,
    "plantations_07": 115,
    "plantations_08": 130,
}


def authored_monthly_income_hundredths(
    building_key: object, *, exact_ck3_build: str = "1.19.0.6",
) -> int | None:
    if (not isinstance(building_key, str)
            or exact_ck3_build not in {"1.19.0.6", "1.20.0.2", "1.20.0.3", "1.20.0.4"}):
        return None
    if (exact_ck3_build == "1.20.0.4"
            and building_key in _AUTHOR_UPGRADE_MONTHLY_INCOME_HUNDREDTHS_12004):
        # Native legality/cost and the observed old slot still decide whether
        # this exact authored value can become a construction candidate.
        return _AUTHOR_UPGRADE_MONTHLY_INCOME_HUNDREDTHS_12004[building_key]
    return _AUTHOR_MONTHLY_INCOME_HUNDREDTHS.get(building_key)


def authored_existing_monthly_income_hundredths(
    building_key: object, *, exact_ck3_build: str = "1.20.0.3",
) -> int | None:
    if not isinstance(building_key, str):
        return None
    if (exact_ck3_build == "1.20.0.4"
            and building_key in _AUTHOR_UPGRADE_MONTHLY_INCOME_HUNDREDTHS_12004):
        return _AUTHOR_UPGRADE_MONTHLY_INCOME_HUNDREDTHS_12004[building_key]
    if exact_ck3_build in {"1.20.0.3", "1.20.0.4"}:
        return _AUTHOR_EXISTING_MONTHLY_INCOME_HUNDREDTHS_12003.get(building_key)
    return authored_monthly_income_hundredths(
        building_key, exact_ck3_build=exact_ck3_build)
