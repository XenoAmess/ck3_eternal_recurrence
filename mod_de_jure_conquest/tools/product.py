"""Frozen maintained-product identity and runtime projection."""

from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
ROOT = SOURCE.parent
PRODUCT_ID = "mod_de_jure_conquest"
UPSTREAM_ITEM_ID = "3600021457"
VERSION = "1.0.0"
SUPPORTED_VERSION = "1.20.*"
TAG_PREFIX = "de-jure-conquest-v"
LANGUAGES = ("english", "simp_chinese", "french", "german", "japanese", "korean", "polish", "russian", "spanish")
RUNTIME_FILES = frozenset({
    "common/casus_belli_types/duchy_de_jure_greatwar.txt",
    "common/casus_belli_types/kingdom_de_jure_greatwar.txt",
    "common/casus_belli_types/empire_de_jure_greatwar.txt",
    "common/on_action/greatwar.txt",
    "common/scripted_effects/djc_war_effects.txt",
    *(f"localization/{language}/greatwar_l_{language}.yml" for language in LANGUAGES),
    "descriptor.mod",
    "thumbnail.png",
})
CB_CONTRACT = {
    "duchy": {"prestige_level": "2", "prestige": "100", "piety": "200"},
    "kingdom": {"prestige_level": "3", "prestige": "500", "piety": "1000"},
    "empire": {"prestige_level": "4", "prestige": "2500", "piety": "5000"},
}


def product_spec():
    import sys
    sys.path.insert(0, str(ROOT / "tools"))
    from independent_mod_release import ProductSpec
    return ProductSpec(PRODUCT_ID, SOURCE, RUNTIME_FILES, UPSTREAM_ITEM_ID, TAG_PREFIX)
