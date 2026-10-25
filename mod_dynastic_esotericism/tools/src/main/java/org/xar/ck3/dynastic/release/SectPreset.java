package org.xar.ck3.dynastic.release;

import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.stream.Stream;

/** Reviewed static presets, independent of a particular machine's CK3 installation. */
public enum SectPreset {
    PROCREATION("des_procreation", List.of("tenet_be_fruitful_and_multiply", "tenet_carnal_exaltation", "tenet_sacred_childbirth"),
            List.of("special_doctrine_is_jewish_faith", "special_doctrine_is_christian_faith", "special_doctrine_is_islamic_faith",
                    "special_doctrine_is_sinitic_faith", "special_doctrine_is_eastern_faith", "special_doctrine_is_gnostic_faith",
                    "special_doctrine_jizya", "special_doctrine_pope_blessing")),
    VIVHITE("des_vivhite", List.of("tenet_warmonger", "tenet_miles_christi", "tenet_pursuit_of_power"),
            List.of("special_doctrine_jizya", "special_doctrine_pope_blessing"));

    public static final String FAITH_FILE = "common/religion/faith_types/des_faiths.txt";
    public static final String RITE_FILE = "common/religion/rite_types/des_rites.txt";
    public static final String COAT_OF_ARMS_FILE = "common/coat_of_arms/coat_of_arms/des_rite_coa.txt";
    public static final String RELIGION = "christianity_religion";
    public static final List<String> LOCALIZATION_SUFFIXES = List.of("", "_adj", "_adherent", "_adherent_plural", "_desc");
    public static final List<String> ORDINARY_DOCTRINES = List.of(
            "doctrine_gender_equal", "doctrine_pluralism_righteous", "doctrine_theocracy_temporal", "doctrine_temporal_head",
            "doctrine_pilgrimage_encouraged", "doctrine_polytheist", "des_doctrine_dynastic", "doctrine_concubines",
            "doctrine_divorce_allowed", "doctrine_bastardry_none", "doctrine_consanguinity_unrestricted",
            "doctrine_homosexuality_accepted", "doctrine_deviancy_virtuous", "doctrine_adultery_men_accepted",
            "doctrine_adultery_women_accepted", "doctrine_kinslaying_extended_family_crime", "doctrine_witchcraft_virtuous",
            "doctrine_clerical_function_recruitment", "doctrine_clerical_gender_either", "doctrine_clerical_marriage_allowed",
            "doctrine_clerical_succession_temporal_appointment", "doctrine_funeral_sky_burial", "doctrine_anointment_permitted",
            "doctrine_monasticism_encouraged", "doctrine_sacraments_central");

    private final String icon;
    private final List<String> tenets;
    private final List<String> specialDoctrines;

    SectPreset(String icon, List<String> tenets, List<String> specialDoctrines) {
        this.icon = icon;
        this.tenets = List.copyOf(tenets);
        this.specialDoctrines = List.copyOf(specialDoctrines);
    }

    public String faithId() { return icon + "_faith"; }
    public String riteId() { return icon + "_rite"; }
    public String icon() { return icon; }
    public String iconPath() { return "gfx/interface/icons/faith/" + icon + ".dds"; }
    public String coatOfArmsId() { return riteId() + "_coa"; }
    public String coatOfArmsTexturePath() { return "gfx/coat_of_arms/textured_emblems/" + icon + ".dds"; }
    public List<String> tenets() { return tenets; }
    public List<String> specialDoctrines() { return specialDoctrines; }
    public List<String> doctrines() { return Stream.concat(ORDINARY_DOCTRINES.stream(), specialDoctrines.stream()).toList(); }

    public static Set<String> localizationKeys() {
        return Stream.of(values()).flatMap(preset -> Stream.of(preset.faithId(), preset.riteId()))
                .flatMap(id -> LOCALIZATION_SUFFIXES.stream().map(suffix -> id + suffix))
                .collect(Collectors.toUnmodifiableSet());
    }
}
