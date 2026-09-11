"""Frozen CK3 1.19.0.6 metadata for Auto Upgrade Buildings.

Only the standard innovation route is represented. Cultural parameters that let
some vanilla buildings skip an era gate are deliberately outside the product
contract.
"""

from __future__ import annotations

from dataclasses import dataclass


InnovationGate = tuple[str, ...] | None


@dataclass(frozen=True)
class BuildingChain:
    name: str
    label: str
    cost_family: str = "normal"
    innovations: tuple[InnovationGate, ...] = ()
    holding_levels: tuple[int | None, ...] = ()
    cost_tiers: tuple[int, ...] = (2, 3, 4, 5, 6, 7, 8)
    payer_triggers: tuple[str, ...] = ()


REGULAR_LEVELS = (1, 2, 2, 3, 3, 4, 4)
NO_LEVELS = (None,) * 7
MILITARY_EARLY_LEVELS = (None, 2, 2, 3, 3, 4, 4)

ECONOMY = (
    ("innovation_crop_rotation",),
    ("innovation_manorialism",),
    ("innovation_manorialism",),
    ("innovation_guilds",),
    ("innovation_guilds",),
    ("innovation_cranes",),
    ("innovation_cranes",),
)
MILLS = (
    ("innovation_windmills",),
    ("innovation_windmills",),
    ("innovation_windmills",),
    ("innovation_windmills",),
    ("innovation_cranes",),
    ("innovation_cranes",),
    ("innovation_cranes",),
)
CARAVANS = (
    ("innovation_guilds",),
    ("innovation_guilds",),
    ("innovation_guilds",),
    ("innovation_guilds",),
    ("innovation_cranes",),
    ("innovation_cranes",),
    ("innovation_cranes",),
)
NO_INNOVATIONS = (None,) * 7
PADDY = (
    None,
    ("innovation_manorialism",),
    ("innovation_manorialism",),
    ("innovation_guilds",),
    ("innovation_guilds",),
    ("innovation_cranes",),
    ("innovation_cranes",),
)
MILITARY = (
    ("innovation_barracks",),
    ("innovation_burhs",),
    ("innovation_burhs",),
    ("innovation_castle_baileys",),
    ("innovation_castle_baileys",),
    ("innovation_royal_armory",),
    ("innovation_royal_armory",),
)
WIND_FURNACE = (
    ("innovation_barracks",),
    ("innovation_burhs",),
    ("innovation_burhs",),
    ("innovation_castle_baileys",),
    ("innovation_royal_armory",),
    ("innovation_royal_armory",),
    ("innovation_royal_armory",),
)
WORKSHOPS = (
    ("innovation_advanced_bowmaking",),
    ("innovation_advanced_bowmaking",),
    ("innovation_advanced_bowmaking",),
    ("innovation_advanced_bowmaking",),
    ("innovation_royal_armory",),
    ("innovation_royal_armory",),
    ("innovation_royal_armory",),
)
FORTIFICATION = (
    ("innovation_motte",),
    ("innovation_battlements",),
    ("innovation_battlements",),
    ("innovation_hoardings",),
    ("innovation_hoardings",),
    ("innovation_machicolations",),
    ("innovation_machicolations",),
)
COMMON = (
    ("innovation_city_planning",),
    ("innovation_manorialism",),
    ("innovation_manorialism",),
    ("innovation_windmills",),
    ("innovation_windmills",),
    ("innovation_cranes",),
    ("innovation_cranes",),
)
GUILD_HALLS = (
    ("innovation_crop_rotation",),
    ("innovation_manorialism",),
    ("innovation_manorialism",),
    ("innovation_guilds",),
    ("innovation_guilds",),
    ("innovation_cranes",),
    ("innovation_cranes",),
)
MONASTIC_SCHOOLS = (
    ("innovation_city_planning",),
    ("innovation_city_planning", "innovation_manorialism"),
    ("innovation_city_planning", "innovation_manorialism"),
    ("innovation_city_planning", "innovation_windmills"),
    ("innovation_city_planning", "innovation_windmills"),
    ("innovation_windmills", "innovation_cranes"),
    ("innovation_windmills", "innovation_cranes"),
)
MEGALITH = (
    None,
    ("innovation_city_planning",),
    ("innovation_city_planning",),
    ("innovation_city_planning",),
    ("innovation_city_planning",),
    ("innovation_city_planning",),
    ("innovation_city_planning",),
)
BREWERIES = (
    ("innovation_city_planning",),
    ("innovation_city_planning",),
    ("innovation_manorialism",),
    ("innovation_windmills",),
    ("innovation_windmills",),
    ("innovation_cranes",),
    ("innovation_cranes",),
)


def chain(
    name: str,
    label: str,
    innovations: tuple[InnovationGate, ...],
    *,
    cost_family: str = "normal",
    holding_levels: tuple[int | None, ...] = REGULAR_LEVELS,
    cost_tiers: tuple[int, ...] = (2, 3, 4, 5, 6, 7, 8),
    payer_triggers: tuple[str, ...] = (),
) -> BuildingChain:
    return BuildingChain(
        name=name,
        label=label,
        cost_family=cost_family,
        innovations=innovations,
        holding_levels=holding_levels,
        cost_tiers=cost_tiers,
        payer_triggers=payer_triggers,
    )


CHAINS = (
    chain("caravanserai", "Caravanserai", CARAVANS, cost_family="expensive"),
    chain("watermills", "Watermills", MILLS, cost_family="expensive"),
    chain("windmills", "Windmills", MILLS, cost_family="expensive"),
    chain("common_tradeport", "Tradeport", ECONOMY),
    chain("pastures", "Pastures", ECONOMY),
    chain("hunting_grounds", "Hunting Grounds", ECONOMY, cost_family="cheap"),
    chain("orchards", "Orchards", ECONOMY),
    chain("farm_estates", "Farm Estates", ECONOMY),
    chain("cereal_fields", "Cereal Fields", ECONOMY),
    chain("logging_camps", "Logging Camps", ECONOMY, cost_family="cheap"),
    chain("peat_quarries", "Peat Quarries", ECONOMY, cost_family="cheap"),
    chain("hill_farms", "Hill Farms", ECONOMY, cost_family="cheap"),
    chain("elephant_pens", "Elephant Pens", ECONOMY),
    chain("plantations", "Plantations", ECONOMY, cost_family="cheap"),
    chain("quarries", "Quarries", ECONOMY, cost_family="cheap"),
    chain("qanats", "Qanats", NO_INNOVATIONS),
    chain("murex_farm", "Murex Farm", NO_INNOVATIONS),
    chain("waterworks", "Waterworks", NO_INNOVATIONS),
    chain("spice_plantation", "Spice Plantation", NO_INNOVATIONS),
    chain("paddy_fields", "Paddy Fields", PADDY),
    chain("wind_furnace", "Wind Furnace", WIND_FURNACE),
    chain("workshops", "Workshops", WORKSHOPS, cost_family="expensive"),
    chain("horse_pastures", "Horse Pastures", MILITARY, cost_family="cheap", holding_levels=MILITARY_EARLY_LEVELS),
    chain("hillside_grazing", "Hillside Grazing", MILITARY, cost_family="cheap", holding_levels=MILITARY_EARLY_LEVELS),
    chain("warrior_lodges", "Warrior Lodges", MILITARY, cost_family="cheap", holding_levels=MILITARY_EARLY_LEVELS),
    chain("military_camps", "Military Camps", MILITARY, cost_family="cheap"),
    chain("regimental_grounds", "Regimental Grounds", MILITARY, cost_family="expensive"),
    chain("outposts", "Outposts", MILITARY, cost_family="cheap"),
    chain("barracks", "Barracks", MILITARY),
    chain("camel_farms", "Camel Farms", MILITARY),
    chain("stables", "Stables", MILITARY),
    chain("smiths", "Smiths", MILITARY),
    chain("ramparts", "Ramparts", FORTIFICATION, cost_family="cheap"),
    chain("curtain_walls", "Curtain Walls", FORTIFICATION, cost_family="cheap"),
    chain("watchtowers", "Watchtowers", FORTIFICATION, cost_family="cheap"),
    chain("hill_forts", "Hill Forts", FORTIFICATION, cost_family="cheap"),
    chain("hospices", "Hospices", COMMON),
    chain("guild_halls", "Guild Halls", GUILD_HALLS, holding_levels=NO_LEVELS),
    chain("scriptorium", "Scriptorium", COMMON, holding_levels=NO_LEVELS),
    chain("monastic_schools", "Monastic Schools", MONASTIC_SCHOOLS, holding_levels=NO_LEVELS),
    chain(
        "megalith",
        "Megalith",
        MEGALITH,
        holding_levels=NO_LEVELS,
        cost_tiers=(2, 3, 4, 5, 5, 5, 5),
    ),
    chain("breweries", "Breweries", BREWERIES, holding_levels=NO_LEVELS),
    chain(
        "capital_bureau",
        "Capital Bureau",
        COMMON,
        payer_triggers=("government_has_flag = government_is_administrative",),
    ),
)


def validate_data() -> None:
    if len(CHAINS) != 43 or len({item.name for item in CHAINS}) != 43:
        raise ValueError("expected 43 unique upstream building chains")
    for item in CHAINS:
        if item.cost_family not in {"cheap", "normal", "expensive"}:
            raise ValueError(f"invalid cost family for {item.name}")
        if not (
            len(item.innovations)
            == len(item.holding_levels)
            == len(item.cost_tiers)
            == 7
        ):
            raise ValueError(f"tier metadata length mismatch for {item.name}")


validate_data()
