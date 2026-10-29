package org.xar.ck3.control.wave2.military.combatwire;

import static org.xar.ck3.control.wave2.military.combatwire.CombatWire.*;
import static org.xar.ck3.control.wave2.military.combatwire.CombatPhaseSchema.*;
import static org.xar.ck3.control.wave2.military.combatwire.PhaseRawCodec.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

/** Deterministic stock projection only. No native transition, RNG draw, or actual phase is executed. */
final class PhaseContextDerivation {
    private PhaseContextDerivation() { }
    private static final JsonNodeFactory J = JsonNodeFactory.instance;
    static ArrayNode derive(ObjectNode raw, PhaseRefPartition partition) {
        ArrayNode characters = array(raw.get("characters"), "characters"), armies = array(raw.get("armies"), "armies"), sides = array(raw.get("sides"), "sides");
        ArrayNode contexts = J.arrayNode();
        for (JsonNode root : characters) {
            int sideIndex = root.path("encounter_role").asText().equals("attacker") ? 0 : 1, enemyIndex = 1 - sideIndex;
            JsonNode own = sides.get(sideIndex), enemy = sides.get(enemyIndex), rootArmy = null;
            for (JsonNode army : armies) if (army.path("army_id").intValue() == root.path("source_army_id").intValue()) rootArmy = army;
            require(rootArmy != null, "phase root army missing");
            List<JsonNode> enemyKnights = new ArrayList<>();
            for (int id : orderedPositiveIds(enemy.get("ordered_knight_ids"))) enemyKnights.add(character(characters, enemyIndex, id));
            ArrayNode ownAccolades = orderedAccolades(own, characters), enemyAccolades = orderedAccolades(enemy, characters), hostility = J.arrayNode();
            for (JsonNode row : raw.get("faith_hostility")) if (row.path("root_character_id").intValue() == root.path("character_id").intValue()) hostility.add(row.deepCopy());
            ObjectNode nativeRefs = rootRefs(root, rootArmy);
            for (String key : List.of("character_membership", "commander", "ordered_enemy_knights", "side_army_size_raw", "side_strength_raw")) {
                JsonNode value = switch (key) { case "character_membership" -> own.get("ordered_character_ids"); case "commander" -> own.get("commander_character_id"); case "ordered_enemy_knights" -> enemy.get("ordered_knight_ids"); default -> own.get(key); };
                nativeRefs.set("combat_side." + key, value.deepCopy());
            }
            nativeRefs.set("enemy_side.character_membership", enemy.get("ordered_character_ids").deepCopy());
            nativeRefs.set("enemy_side.side_army_size_raw", enemy.get("side_army_size_raw").deepCopy()); nativeRefs.set("enemy_side.side_strength_raw", enemy.get("side_strength_raw").deepCopy());
            nativeRefs.set("game_rules.easy_difficulty", raw.path("game_rules").get("easy_difficulty").deepCopy()); nativeRefs.set("game_rules.very_easy_difficulty", raw.path("game_rules").get("very_easy_difficulty").deepCopy());
            ObjectNode offline = offlineRefs(root, rootArmy, own, enemy, enemyKnights, ownAccolades, enemyAccolades, hostility, raw.get("game_rules"));
            ArrayNode candidates = J.arrayNode();
            for (JsonNode candidate : enemyKnights) {
                ObjectNode candidateRefs = candidateRefs(candidate), selectedRefs = selectedRefs(candidate);
                BigInteger threshold = qmul(n(root.path("prowess").longValue()).multiply(n(100_000)), n(80_000)), prowess = n(candidate.path("prowess").longValue()).multiply(n(100_000));
                candidateRefs.put("derived.candidate_prowess_at_or_above_root_opponent_threshold_without_alive_filter", prowess.compareTo(threshold) >= 0);
                candidateRefs.put("derived.candidate_prowess_at_or_below_root_opponent_threshold", flag(candidate, "alive") && prowess.compareTo(threshold) <= 0);
                candidateRefs.put("derived.candidate_prowess_at_or_below_root_opponent_threshold_without_alive_filter", prowess.compareTo(threshold) <= 0);
                candidateRefs.put("derived.stock_enemy_knight_selection_weight_raw", selectionWeight(candidate));
                selectedRefs.set("selected_enemy_knight.traits_and_culture_for_blademaster", blademaster(candidate));
                ObjectNode row = J.objectNode().put("character_id", candidate.path("character_id").intValue()); row.set("candidate_refs", candidateRefs); row.set("selected_enemy_knight_refs", selectedRefs); candidates.add(row);
            }
            validateCoverage(nativeRefs, offline, candidates, partition);
            ObjectNode context = J.objectNode().put("root_character_id", root.path("character_id").intValue()).put("root_source_army_id", root.path("source_army_id").intValue());
            context.set("root_source_regiment_id", root.get("source_regiment_id").deepCopy()); context.set("phase_roles", root.get("phase_roles").deepCopy());
            context.put("combat_side_index", sideIndex).put("enemy_side_index", enemyIndex); context.set("native_state_refs", nativeRefs); context.set("offline_state_refs", offline);
            context.set("candidate_source_proof", enemy.get("candidate_source_proof").deepCopy()); context.set("candidate_rows", candidates); contexts.add(context);
        }
        return contexts;
    }
    private static JsonNode character(ArrayNode rows, int sideIndex, int id) {
        JsonNode result = null; String role = sideIndex == 0 ? "attacker" : "defender";
        for (JsonNode row : rows) if (row.path("encounter_role").asText().equals(role) && row.path("character_id").intValue() == id) result = row;
        require(result != null, "phase side character missing"); return result;
    }
    private static ObjectNode rootRefs(JsonNode root, JsonNode army) {
        ObjectNode out = J.objectNode().put("root.exists", true); JsonNode traits = root.get("traits_or_groups");
        for (String key : List.of("alive", "is_ai", "is_acclaimed", "can_be_acclaimed")) out.set("root." + key, root.get(key).deepCopy());
        out.set("root.is_incapable", traits.get("incapable").deepCopy());
        for (String key : List.of("martial", "learning", "prowess")) out.put("root.skills." + key + "_raw", root.path(key).longValue() * 100_000L);
        out.set("root.house_id", root.path("house").get("value").deepCopy()); out.set("root.liege", root.path("liege").get("value").deepCopy()); out.set("root.liege.house_id", root.path("liege_house").get("value").deepCopy());
        copy(out, "root.liege.accolade_progress_raw", root, "liege_accolade_progress_raw"); copy(out, "root.dynasty.perks.warfare_legacy_3", root, "warfare_legacy_3"); copy(out, "root.perks.stalwart_leader", root, "stalwart_leader");
        copy(out, "root.culture.heritage_north_germanic", root, "heritage_north_germanic"); copy(out, "root.culture.parameters.knights_slightly_more_prone_to_injury", root, "knights_slightly_more_prone_to_injury");
        copy(out, "root.faith.parameters.death_is_glory", root, "death_is_glory"); copy(out, "root.faith.tenets.warmonger", root, "tenet_warmonger"); copy(out, "root.religion.germanic", root, "germanic_religion"); copy(out, "root.court_positions.garuda", root, "garuda_court_position");
        copy(out, "root.knight_army.maa_regiment_count_raw", army, "maa_regiment_count_raw"); copy(out, "root.traits.wounded.rank_raw", root, "wounded_rank_raw"); copy(out, "root.traits.fragile_bones.rank_raw", root, "fragile_bones_rank_raw"); copy(out, "root.traits.fragile_bones.xp_raw", root, "fragile_bones_xp_raw");
        out.put("root.traits.maim_injuries", hasMaim(root));
        for (String key : keys(ROOT_TRAITS)) copy(out, "root.traits." + key, traits, key);
        army.path("maa_counts_raw").properties().forEach(entry -> out.set("root.knight_army.maa_counts." + entry.getKey(), entry.getValue().deepCopy())); return out;
    }
    private static ObjectNode candidateRefs(JsonNode candidate) {
        ObjectNode out = J.objectNode(); copy(out, "candidate.alive", candidate, "alive"); copy(out, "candidate.dynasty.perks.warfare_legacy_3", candidate, "warfare_legacy_3");
        copy(out, "candidate.is_acclaimed", candidate, "is_acclaimed"); copy(out, "candidate.perks.stalwart_leader", candidate, "stalwart_leader");
        return out.put("candidate.skills.prowess_raw", candidate.path("prowess").longValue() * 100_000);
    }
    private static ObjectNode selectedRefs(JsonNode candidate) {
        ObjectNode out = J.objectNode(); copy(out, "selected_enemy_knight.alive", candidate, "alive"); copy(out, "selected_enemy_knight.dynasty.perks.warfare_legacy_3", candidate, "warfare_legacy_3");
        out.set("selected_enemy_knight.faith", candidate.path("faith").get("value").deepCopy()); copy(out, "selected_enemy_knight.is_acclaimed", candidate, "is_acclaimed"); copy(out, "selected_enemy_knight.perks.stalwart_leader", candidate, "stalwart_leader");
        out.put("selected_enemy_knight.skills.learning_raw", candidate.path("learning").longValue() * 100_000).put("selected_enemy_knight.skills.prowess_raw", candidate.path("prowess").longValue() * 100_000);
        copy(out, "selected_enemy_knight.traits.brave", candidate.get("traits_or_groups"), "brave"); copy(out, "selected_enemy_knight.traits.craven", candidate.get("traits_or_groups"), "craven"); return out;
    }
    private static ObjectNode offlineRefs(JsonNode root, JsonNode army, JsonNode own, JsonNode enemy, List<JsonNode> enemyKnights, ArrayNode ownAccolades, ArrayNode enemyAccolades, ArrayNode hostility, JsonNode rules) {
        long wounded = root.path("wounded_rank_raw").longValue(), ownStrength = own.path("side_strength_raw").longValue(), enemyStrength = enemy.path("side_strength_raw").longValue();
        boolean stronger = ownStrength > enemyStrength, sameHouse = present(root.get("house")) && present(root.get("liege_house")) && root.path("house").path("value").intValue() == root.path("liege_house").path("value").intValue();
        String ownTier = sameHouse ? tier(ownAccolades, "accolade_defends_family") : null, enemyTier = tier(enemyAccolades, "accolade_increase_hostile_knight_death");
        long family = ownTier == null ? 100_000 : switch (ownTier) { case "low" -> 75_000; case "medium" -> 50_000; default -> 25_000; };
        long hostile = enemyTier == null ? 100_000 : switch (enemyTier) { case "low" -> 125_000; case "medium" -> 150_000; default -> 175_000; };
        BigInteger threshold = qmul(n(root.path("prowess").longValue()).multiply(n(100_000)), n(80_000)); boolean anyBelow = false, aliveBelow = false;
        for (JsonNode candidate : enemyKnights) if (n(candidate.path("prowess").longValue()).multiply(n(100_000)).compareTo(threshold) <= 0) { anyBelow = true; aliveBelow |= flag(candidate, "alive"); }
        BigInteger outnumber = stronger && ownStrength != 0 ? qmul(qdiv(n(enemyStrength), n(ownStrength)), n(140_000)).min(n(100_000)) : n(100_000);
        ObjectNode accolades = unlocks(root, army.get("maa_counts_raw"), own, enemy, hostility), out = J.objectNode();
        ObjectNode relations = out.putObject("root.house_and_liege_relations"); for (String key : List.of("house", "liege", "liege_house")) relations.set(key, root.get(key).deepCopy()); relations.put("same_house", sameHouse);
        out.set("root.knight_army.maa_counts", army.get("maa_counts_raw").deepCopy()); out.set("game_rules", rules.deepCopy()); out.set("root.traits_and_culture_for_blademaster", blademaster(root));
        out.putObject("root.variables").set("hold_court_8050_knight", root.get("hold_court_8050_knight").deepCopy()); ObjectNode employer = out.putObject("root.employer.variables"); employer.set("employer", root.get("employer").deepCopy()); employer.set("hold_court_8050_promise", root.get("employer_hold_court_8050_promise").deepCopy());
        out.put("root.ai_should_get_extreme_conqueror_bonuses", flag(root, "conqueror_variable_present") && flag(root, "ai_extreme_conqueror_modifier"));
        LinkedHashSet<Integer> faiths = new LinkedHashSet<>(); for (JsonNode row : hostility) faiths.add(row.path("enemy_faith_id").intValue()); ArrayNode faithRows = out.putArray("combat_side.enemy_faiths"); faiths.forEach(faithRows::add);
        out.set("combat_side.ordered_commanders_and_knights_with_accolade_parameters", ownAccolades); out.set("root.accolade_unlocks", accolades);
        long woundFactor = wounded == 300_000 ? 25_000 : wounded == 100_000 || wounded == 200_000 ? 50_000 : 100_000;
        out.put("derived.accolade_qualification_wound_factor_raw", woundFactor).put("derived.become_berserker_wound_factor_raw", woundFactor);
        out.put("derived.enemy_alive_knight_at_or_below_root_opponent_threshold_exists", aliveBelow).put("derived.qualifying_enemy_knight_exists", anyBelow);
        out.put("derived.outnumbering_injury_factor_raw", outnumber).put("derived.own_side_more_than_five_times_enemy", n(ownStrength).compareTo(qmul(n(enemyStrength), n(500_000))) > 0).put("derived.own_side_stronger", stronger);
        out.put("derived.root_has_any_maim_injury", hasMaim(root)).put("derived.root_has_any_wounded_rank_1_2_3", wounded > 0).put("derived.root_is_wounded", wounded > 0).put("derived.root_wounded_rank_3", wounded == 300_000);
        long prowess = root.path("prowess").longValue(); int bonus = flag(root, "garuda_court_position") ? 8 : 0;
        out.put("derived.root_injury_factor_30_raw", injury(prowess, 30, 0)).put("derived.root_injury_factor_30_with_garuda_raw", injury(prowess, 30, bonus)).put("derived.root_injury_factor_40_with_garuda_raw", injury(prowess, 40, bonus));
        out.put("derived.root_player_stalwart", flag(root, "stalwart_leader") && !flag(root, "is_ai")).put("derived.root_ai_stalwart", flag(root, "stalwart_leader") && flag(root, "is_ai"));
        out.put("derived.same_house_defends_family_any_tier", ownTier != null).put("derived.same_house_defends_family_factor_raw", family).put("derived.same_house_defends_family_tier_high", "high".equals(ownTier)).put("derived.same_house_defends_family_tier_low_only", "low".equals(ownTier)).put("derived.same_house_defends_family_tier_medium_only", "medium".equals(ownTier));
        out.put("derived.enemy_hostile_knight_death_accolade_any_tier", enemyTier != null).put("derived.enemy_hostile_knight_death_accolade_factor_raw", hostile);
        accolades.properties().forEach(entry -> out.set("root.accolade_unlocks." + entry.getKey() + ".valid", entry.getValue().get("valid").deepCopy())); return out;
    }
    private static ObjectNode unlocks(JsonNode root, JsonNode maa, JsonNode own, JsonNode enemy, ArrayNode hostility) {
        JsonNode traits = root.get("traits_or_groups"), innovations = root.get("innovations"), traditions = root.get("traditions"), parameters = root.get("culture_parameters"), unlock = root.get("attribute_unlock_variables");
        long bow = root.path("tourney_bow_xp_raw").longValue(), foot = root.path("tourney_foot_xp_raw").longValue(), horse = root.path("tourney_horse_xp_raw").longValue();
        boolean allowance = !present(root.get("accolade")) || !flag(root, "accolade_has_men_at_arms_category");
        boolean vanguard = any(innovations, "innovation_quilted_armor innovation_sarawit innovation_legionnaires") || any(traditions, "tradition_fp1_coastal_warriors tradition_hird tradition_futuwaa tradition_druzhina tradition_khadga_puja tradition_garuda_warriors tradition_himalayan_settlers tradition_mubarizuns tradition_burman_royal_army tradition_mountaineer_ruralism") || any(parameters, "unlock_zhanmadao unlock_burenjia");
        boolean lancer = any(innovations, "innovation_arched_saddle innovation_valets innovation_tiefutu") || any(traditions, "tradition_caucasian_wolves tradition_roman_legacy tradition_ep3_audacious_cadets tradition_ep3_imperial_tagmata") || any(parameters, "unlock_maa_cataphract_archers unlock_maa_black_armor_cavalry");
        boolean horseCulture = any(parameters, "unlock_maa_horse_archers unlock_maa_mangudai unlock_emishi_horse_archers_units unlock_mounted_samurai_units unlock_maa_cataphract_archers");
        ObjectNode out = J.objectNode();
        valid(out, "skirmisher", maa.path("skirmishers_raw").longValue() > 0 && !((flag(unlock, "skirmisher") || bow >= 3_000_000 || foot >= 3_000_000 || any(traits, "winter_soldier jungle_stalker")) && allowance));
        valid(out, "archer", maa.path("non_crossbow_archers_raw").longValue() > 0 && !((flag(unlock, "archer") || bow >= 3_000_000 || flag(traits, "forest_fighter")) && allowance));
        valid(out, "crossbowmen", maa.path("crossbow_family_raw").longValue() > 0 && !((flag(unlock, "crossbowmen") || bow >= 3_000_000 || flag(traits, "cautious_leader")) && any(innovations, "innovation_advanced_bowmaking innovation_repeating_crossbow") && allowance));
        valid(out, "pike", maa.path("pikemen_raw").longValue() > 0 && !((flag(unlock, "pike") || foot >= 3_000_000 || flag(traits, "rough_terrain_expert")) && allowance));
        valid(out, "vanguard", maa.path("heavy_infantry_raw").longValue() > 0 && !((flag(unlock, "vanguard") || any(traits, "strong athletic physique_good") || foot >= 3_000_000) && vanguard && allowance));
        valid(out, "outrider", maa.path("light_cavalry_raw").longValue() > 0 && !((flag(unlock, "outrider") || horse >= 3_000_000 || flag(traits, "open_terrain_expert")) && allowance));
        valid(out, "lancer", maa.path("heavy_cavalry_raw").longValue() > 0 && !((flag(unlock, "lancer") || horse >= 3_000_000 || flag(traits, "aggressive_attacker")) && lancer && allowance));
        valid(out, "camelry", maa.path("camel_cavalry_raw").longValue() > 0 && !((flag(unlock, "camelry") || horse >= 3_000_000 || flag(traits, "desert_warrior")) && flag(innovations, "innovation_war_camels") && allowance));
        valid(out, "elephantry", maa.path("elephant_cavalry_raw").longValue() > 0 && !((flag(unlock, "elephantry") || horse >= 3_000_000 || flag(traits, "jungle_stalker")) && flag(innovations, "innovation_elephantry") && allowance));
        valid(out, "horse_archer", maa.path("archer_cavalry_raw").longValue() > 0 && !((flag(unlock, "horse_archer") || horse >= 3_000_000 || bow >= 3_000_000 || flag(traits, "flexible_leader")) && (horseCulture || flag(root, "government_is_nomadic") || flag(traits, "nomadic_philosophy")) && allowance));
        valid(out, "gunpowder", maa.path("gunpowder_raw").longValue() > 0 && !((flag(unlock, "gunpowder") || flag(traits, "scholar") || root.path("learning").intValue() >= 12) && any(innovations, "innovation_gunpowder innovation_fire_medicine") && allowance));
        boolean fanatic = false; for (JsonNode row : hostility) fanatic |= row.path("hostility_level_raw").intValue() >= 3; valid(out, "fanatic", fanatic);
        valid(out, "valiant", n(own.path("side_army_size_raw").longValue()).compareTo(qmul(n(enemy.path("side_army_size_raw").longValue()), n(66_000))) >= 0 && !(flag(unlock, "valiant") || any(traits, "brave berserker reckless"))); return out;
    }
    private static ArrayNode orderedAccolades(JsonNode side, ArrayNode characters) {
        ArrayNode out = J.arrayNode(); int index = side.path("side_index").intValue();
        for (String role : List.of("commander", "knight")) for (int id : orderedPositiveIds(side.get(role.equals("commander") ? "ordered_commander_ids" : "ordered_knight_ids"))) {
            JsonNode character = character(characters, index, id); ObjectNode row = J.objectNode().put("role", role).put("character_id", id).put("source_army_id", character.path("source_army_id").intValue());
            if (role.equals("commander")) row.putNull("source_regiment_id"); else row.set("source_regiment_id", character.get("source_regiment_id").deepCopy());
            row.set("accolade", character.get("accolade").deepCopy()); row.set("parameters", character.get("accolade_parameters").deepCopy()); out.add(row);
        }
        return out;
    }
    private static String tier(ArrayNode rows, String prefix) { for (String tier : List.of("high", "medium", "low")) for (JsonNode row : rows) if (flag(row.get("parameters"), prefix + "_" + tier)) return tier; return null; }
    private static ObjectNode blademaster(JsonNode character) {
        JsonNode traits = character.get("traits_or_groups"); ObjectNode out = J.objectNode(); ArrayNode martial = out.putArray("education_martial"), prowess = out.putArray("education_martial_prowess"), intellect = out.putArray("intellect_good");
        for (int i = 1; i <= 5; i++) martial.add(flag(traits, "education_martial_" + i)); for (int i = 1; i <= 4; i++) prowess.add(flag(traits, "education_martial_prowess_" + i)); for (int i = 1; i <= 3; i++) intellect.add(flag(traits, "intellect_good_" + i));
        copy(out, "lifestyle_blademaster", traits, "lifestyle_blademaster"); copy(out, "lifestyle_blademaster_xp_raw", character, "lifestyle_blademaster_xp_raw"); copy(out, "shrewd", traits, "shrewd"); copy(out, "physique_good", traits, "physique_good"); copy(out, "culture_blademaster_traits_more_common", character, "blademaster_traits_more_common"); return out;
    }
    private static void validateCoverage(ObjectNode nativeRefs, ObjectNode offlineRefs, ArrayNode candidates, PhaseRefPartition partition) {
        Set<String> nativePaths = new HashSet<>(), offlinePaths = new HashSet<>(); nativeRefs.fieldNames().forEachRemaining(nativePaths::add); offlineRefs.fieldNames().forEachRemaining(offlinePaths::add);
        for (String path : partition.nativeRefs()) if (path.startsWith("candidate.") || path.startsWith("selected_enemy_knight.")) nativePaths.add(path);
        for (String path : partition.offlineRefs()) if (path.startsWith("derived.candidate_") || path.equals("derived.stock_enemy_knight_selection_weight_raw") || path.startsWith("selected_enemy_knight.")) offlinePaths.add(path);
        for (JsonNode candidate : candidates) {
            for (String key : List.of("candidate_refs", "selected_enemy_knight_refs")) candidate.get(key).fieldNames().forEachRemaining(path -> { nativePaths.add(path); if (partition.offlineRefs().contains(path)) offlinePaths.add(path); });
            nativePaths.removeAll(partition.offlineRefs());
        }
        require(nativePaths.equals(partition.nativeRefs()) && offlinePaths.equals(partition.offlineRefs()), "derived contexts do not cover exact 132-ref partition");
    }
    private static boolean hasMaim(JsonNode root) { return any(root.get("traits_or_groups"), "one_legged disfigured one_eyed maimed"); }
    private static boolean any(JsonNode row, String names) { for (String key : keys(names)) if (flag(row, key)) return true; return false; }
    private static void valid(ObjectNode row, String key, boolean value) { row.putObject(key).put("valid", value); }
    private static void copy(ObjectNode out, String path, JsonNode source, String key) { out.set(path, source.get(key).deepCopy()); }
    private static long selectionWeight(JsonNode root) { long result = 10_000_000; for (String key : List.of("is_acclaimed", "stalwart_leader", "warfare_legacy_3")) if (flag(root, key)) result = qmul(n(result), n(75_000)).longValueExact(); return result; }
    private static long injury(long prowess, long denominator, long bonus) { return Math.max((denominator - prowess + bonus) * 100_000 / denominator, 10_000); }
    private static BigInteger n(long value) { return BigInteger.valueOf(value); }
    private static BigInteger qmul(BigInteger left, BigInteger right) { return left.multiply(right).divide(n(100_000)); }
    private static BigInteger qdiv(BigInteger left, BigInteger right) { require(right.signum() != 0, "phase fixed-point division by zero"); return left.multiply(n(100_000)).divide(right); }
}

