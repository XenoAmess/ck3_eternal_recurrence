package org.xar.ck3.control.wave2.development.constructionvalue;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.OptionalInt;
import org.xar.ck3.control.wave2.development.constructionvalue.ConstructionValueModel.Build;
import org.xar.ck3.control.wave2.development.constructionvalue.ConstructionValueModel.Field;

/** Exact retained authored declarations. Values are explicit, never a fitted upgrade curve or ROI. */
public final class AuthoredConstructionIncome {
    private static final Map<String, Integer> TIER_ONE = tierOne();
    private static final Map<String, Integer> EXISTING_12003 = existing();
    private static final Map<String, Integer> UPGRADES_12004 = upgrades();
    private AuthoredConstructionIncome() { }

    public static OptionalInt target(Field<String> buildingKey, Build build) {
        if (!buildingKey.known() || build == Build.UNSUPPORTED) { return OptionalInt.empty(); }
        Integer income = build == Build.V12004 ? UPGRADES_12004.get(buildingKey.value()) : null;
        if (income == null) { income = TIER_ONE.get(buildingKey.value()); }
        return income == null ? OptionalInt.empty() : OptionalInt.of(income);
    }
    public static OptionalInt existing(Field<String> buildingKey, Build build) {
        if (!buildingKey.known()) { return OptionalInt.empty(); }
        Integer income = build == Build.V12004 ? UPGRADES_12004.get(buildingKey.value()) : null;
        if (income != null) { return OptionalInt.of(income); }
        if (build == Build.V12003 || build == Build.V12004) {
            income = EXISTING_12003.get(buildingKey.value()); return income == null ? OptionalInt.empty() : OptionalInt.of(income);
        }
        return target(buildingKey, build);
    }

    private static Map<String, Integer> tierOne() {
        Map<String, Integer> result = new HashMap<>();
        put(result, 70, "caravanserai_01", "watermills_01", "windmills_01", "farm_estates_01");
        put(result, 50, "paddy_fields_01", "cereal_fields_01");
        put(result, 35, "murex_farm_01", "spice_plantation_01", "common_tradeport_01", "pastures_01", "orchards_01",
                "logging_camps_01", "peat_quarries_01", "hill_farms_01", "elephant_pens_01");
        put(result, 25, "qanats_01", "hunting_grounds_01", "plantations_01", "quarries_01");
        return Map.copyOf(result);
    }
    private static Map<String, Integer> existing() {
        Map<String, Integer> result = new HashMap<>(TIER_ONE);
        result.put("farm_estates_02", 115); result.put("common_tradeport_02", 55);
        result.put("curtain_walls_01", 25); result.put("monastic_schools_01", 25); result.put("military_camps_01", 0);
        return Map.copyOf(result);
    }
    private static Map<String, Integer> upgrades() {
        Map<String, Integer> result = new HashMap<>();
        // Lists enumerate exact tier 2..8 declarations copied from the original producer, without extrapolation.
        explicit(result, List.of(115, 160, 205, 250, 295, 340, 385), "farm_estates", "caravanserai", "watermills", "windmills");
        explicit(result, List.of(55, 75, 95, 115, 135, 155, 175), "common_tradeport", "pastures", "orchards", "murex_farm",
                "spice_plantation", "logging_camps", "peat_quarries", "hill_farms", "elephant_pens");
        explicit(result, List.of(40, 55, 70, 85, 100, 115, 130), "hunting_grounds", "plantations", "qanats", "quarries");
        explicit(result, List.of(80, 110, 140, 170, 200, 230, 260), "paddy_fields", "cereal_fields");
        return Map.copyOf(result);
    }
    private static void explicit(Map<String, Integer> target, List<Integer> declaredValues, String... families) {
        if (declaredValues.size() != 7) { throw new IllegalArgumentException("seven retained upgrade declarations required"); }
        for (String family : families) {
            for (int index = 0; index < declaredValues.size(); index++) { target.put(family + "_0" + (index + 2), declaredValues.get(index)); }
        }
    }
    private static void put(Map<String, Integer> target, int value, String... keys) {
        for (String key : keys) { target.put(key, value); }
    }
}
