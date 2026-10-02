"""Identity and reviewed runtime allowlist for the maintained holding converter."""

from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
REPO = SOURCE.parent
PRODUCT_ID = "mod_change_holding_types"
UPSTREAM_ITEM_ID = "3337428403"
TAG_PREFIX = "change-holding-types-v"
LANGUAGES = ("english", "simp_chinese", "french", "german", "japanese", "korean", "polish", "russian", "spanish")
TARGETS = (
    ("castle", "castle_holding", "castle_01"),
    ("city", "city_holding", "city_01"),
    ("temple", "church_holding", "temple_01"),
    ("nomad", "nomad_holding", "nomadic_camp_01"),
    ("tribal", "tribal_holding", "tribe_01"),
    ("temple_citadel", "temple_citadel_holding", "temple_citadel_01"),
)
RUNTIME_FILES = frozenset({
    "common/decision_group_types/ch_decision_group_types.txt",
    "common/decisions/00_convert_holdings_decisions.txt",
    "common/scripted_effects/cht_conversion_effects.txt",
    "common/scripted_triggers/00_convert_holdings_scripted_triggers.txt",
    "common/trigger_localization/00_convert_holdings_requirement_triggers.txt",
    "descriptor.mod",
    "gui/decision_view_widgets/decision_view_widget_ch_convert_holding.gui",
    "localization/english/00_convert_holdings_l_english.yml",
    "localization/simp_chinese/00_convert_holdings_l_simp_chinese.yml",
    "thumbnail.png",
})

def runtime_files(release_localization: bool = False) -> frozenset[str]:
    optional = {
        f"localization/{language}/00_convert_holdings_l_{language}.yml"
        for language in LANGUAGES[2:]
        if release_localization or (SOURCE / f"localization/{language}/00_convert_holdings_l_{language}.yml").is_file()
    }
    return RUNTIME_FILES | optional


def spec(release_localization: bool = False):
    import sys
    sys.path.insert(0, str(REPO / "tools"))
    from independent_mod_release import ProductSpec
    return ProductSpec(PRODUCT_ID, SOURCE, runtime_files(release_localization), UPSTREAM_ITEM_ID, TAG_PREFIX)
