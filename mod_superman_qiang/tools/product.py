"""Identity and reviewed release inventory for the original Superman Qiang mod."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from independent_mod_release import ProductSpec

SOURCE = Path(__file__).resolve().parents[1]
REPO = SOURCE.parent
PRODUCT_ID = "mod_superman_qiang"
PRODUCT_KEY = "superman-qiang"
VERSION = "1.2.0"
GAME_VERSION = "1.20.0.4"
TAG_PREFIX = "superman-qiang-v"
RELEASE_TAG_ALIASES: frozenset[str] = frozenset()
LANGUAGES = ("english", "simp_chinese", "french", "german", "japanese", "korean", "polish", "russian", "spanish")

# Explicit, immutable release inventory; filled from the reviewed runtime
# generator outputs, never from a directory glob.
RUNTIME_FILES = frozenset({
    "common/on_action/sxad_natural_on_actions.txt",
    "common/character_interactions/sxad_interactions.txt",
    "common/modifiers/sxad_skill_balance_modifiers.txt",
    "common/script_values/sxad_values.txt",
    "common/script_values/sxad_natural_values.txt",
    "common/scripted_effects/sxad_experience_effects.txt",
    "common/scripted_effects/sxad_natural_effects.txt",
    "common/scripted_effects/sxad_probe_skill_effects.txt",
    "common/scripted_effects/sxad_transfer_effects.txt",
    "common/scripted_effects/zz_sxad_had_sex_with_effect.txt",
    "common/scripted_effects/zz_sxad_had_sex_with_unknown_effect.txt",
    "common/scripted_effects/zz_sxad_rakish_brothel_night_effect.txt",
    "common/scripted_effects/zz_sxad_mandala_story_creation_aspect_get_kids_effect.txt",
    "common/traits/sxad_traits.txt",
    "descriptor.mod",
    "events/sxad_events.txt",
    "events/sxad_natural_events.txt",
    "events/zz_sxad_learning_medicine_2022.txt",
    "events/zz_sxad_learning_medicine_2023.txt",
    "events/zz_sxad_pilgrimage_2101.txt",
    "events/zz_sxad_stewardship_duty_1055.txt",
    "events/zz_sxad_mpo_temujin_flavor_0030.txt",
    "events/zz_sxad_mpo_events_tova_0035.txt",
    "events/zz_sxad_fund_inspiration_6513.txt",
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


def spec() -> ProductSpec:
    sys.path.insert(0, str(REPO / "tools"))
    from independent_mod_release import ProductSpec

    return ProductSpec(PRODUCT_ID, SOURCE, RUNTIME_FILES, None, TAG_PREFIX, release_tag_aliases=RELEASE_TAG_ALIASES)
