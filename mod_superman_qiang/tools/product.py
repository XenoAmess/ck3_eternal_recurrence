"""Identity and reviewed release inventory for the original Superman Qiang mod."""

from __future__ import annotations

from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parents[1]
REPO = SOURCE.parent
PRODUCT_ID = "mod_superman_qiang"
PRODUCT_KEY = "superman-qiang"
VERSION = "1.0.0"
GAME_VERSION = "1.20.0.3"
TAG_PREFIX = "superman-qiang-v"
LANGUAGES = ("english", "simp_chinese", "french", "german", "japanese", "korean", "polish", "russian", "spanish")

# Explicit, immutable release inventory; filled from the reviewed runtime
# generator outputs, never from a directory glob.
RUNTIME_FILES = frozenset({
    "common/character_interactions/sxad_interactions.txt",
    "common/script_values/sxad_values.txt",
    "common/scripted_effects/sxad_experience_effects.txt",
    "common/scripted_effects/sxad_probe_skill_effects.txt",
    "common/scripted_effects/sxad_transfer_effects.txt",
    "common/scripted_effects/zz_sxad_had_sex_with_effect.txt",
    "common/scripted_effects/zz_sxad_had_sex_with_unknown_effect.txt",
    "common/traits/sxad_traits.txt",
    "descriptor.mod",
    "events/sxad_events.txt",
    "gfx/interface/icons/traits/sxad_sex_experience.dds",
    "localization/english/sxad_l_english.yml",
    "localization/french/sxad_l_french.yml",
    "localization/german/sxad_l_german.yml",
    "localization/japanese/sxad_l_japanese.yml",
    "localization/korean/sxad_l_korean.yml",
    "localization/polish/sxad_l_polish.yml",
    "localization/russian/sxad_l_russian.yml",
    "localization/simp_chinese/sxad_l_simp_chinese.yml",
    "localization/spanish/sxad_l_spanish.yml",
    "thumbnail.png",
})


def spec():
    sys.path.insert(0, str(REPO / "tools"))
    from independent_mod_release import ProductSpec

    return ProductSpec(PRODUCT_ID, SOURCE, RUNTIME_FILES, None, TAG_PREFIX)
