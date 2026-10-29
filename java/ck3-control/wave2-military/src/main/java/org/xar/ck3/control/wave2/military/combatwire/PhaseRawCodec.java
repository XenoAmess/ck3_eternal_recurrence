package org.xar.ck3.control.wave2.military.combatwire;

import static org.xar.ck3.control.wave2.military.combatwire.CombatWire.*;
import static org.xar.ck3.control.wave2.military.combatwire.CombatPhaseSchema.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

/** The dynamic native-JSON boundary; every raw leaf is validated before it is detached. */
final class PhaseRawCodec {
    private PhaseRawCodec() { }
    record CharacterIdentity(int characterId, int armyId, Integer regimentId, String role, List<String> phaseRoles) {
        CharacterIdentity { phaseRoles = List.copyOf(phaseRoles); }
    }
    static ObjectNode normalize(JsonNode value, ObjectNode base) {
        ObjectNode raw = object(value, "characters armies sides faith_hostility game_rules", "phase raw");
        ArrayNode baseArmies = array(base.get("armies"), "base armies"), sides = array(raw.get("sides"), "phase sides");
        require(sides.size() == 2, "phase needs exactly two sides");
        List<PhaseCandidateSourceProof> proofs = prevalidateProofs(sides, baseArmies, base.path("scenario"));
        List<CharacterIdentity> identities = expectedCharacters(baseArmies, proofs);
        ArrayNode characters = array(raw.get("characters"), "phase characters");
        require(characters.size() == identities.size(), "phase character roster differs from base");
        for (int index = 0; index < characters.size(); index++) validateCharacter(characters.get(index), identities.get(index));
        ArrayNode armies = array(raw.get("armies"), "phase armies"); require(armies.size() == baseArmies.size(), "phase army roster differs from base");
        for (int index = 0; index < armies.size(); index++) validateArmy(armies.get(index), baseArmies.get(index));
        for (int index = 0; index < 2; index++) validateSide(sides.get(index), index, base, characters, proofs.get(index));
        validateHostility(raw.get("faith_hostility"), characters, sides);
        ObjectNode rules = object(raw.get("game_rules"), "easy_difficulty very_easy_difficulty", "game_rules");
        require(!(bool(rules.get("easy_difficulty"), "easy") && bool(rules.get("very_easy_difficulty"), "very_easy")), "easy and very-easy cannot coexist");
        // Both flags are checked even when the first is false.
        bool(rules.get("very_easy_difficulty"), "very_easy");
        return raw.deepCopy();
    }
    private static List<PhaseCandidateSourceProof> prevalidateProofs(ArrayNode sides, ArrayNode baseArmies, JsonNode scenario) {
        List<PhaseCandidateSourceProof> proofs = new ArrayList<>();
        for (int index = 0; index < 2; index++) {
            String role = index == 0 ? "attacker" : "defender";
            ObjectNode side = object(sides.get(index), SIDES, "phase side");
            List<Integer> armyIds = ids(scenario.get(index == 0 ? "attacker_army_ids" : "defender_army_ids"), false, true, "scenario armies");
            require(i32(side.get("side_index"), "side_index") == index && text(side.get("encounter_role"), "encounter_role").equals(role)
                    && ids(side.get("ordered_army_ids"), false, true, "ordered_army_ids").equals(armyIds), "phase side identity/army order mismatch");
            PhaseCandidateSourceProof proof = PhaseCandidateSourceProof.normalize(side.get("candidate_source_proof"), index);
            List<PhaseCandidateSourceProof.Source> commanders = proof.orderedSources().stream().filter(s -> s.role() == PhaseCandidateSourceProof.Role.COMMANDER).toList();
            List<PhaseCandidateSourceProof.Source> knights = proof.orderedSources().stream().filter(s -> s.role() == PhaseCandidateSourceProof.Role.KNIGHT).toList();
            List<PhaseCandidateSourceProof.Source> expectedCommanders = new ArrayList<>(), expectedKnights = new ArrayList<>(), nativeArmyOrder = new ArrayList<>();
            for (JsonNode army : baseArmies) if (army.path("encounter_role").asText().equals(role)) {
                int armyId = nonnegative(army.get("army_id"), "base army_id"); JsonNode commander = army.get("commander");
                if (commander.path("status").asText().equals("available")) expectedCommanders.add(new PhaseCandidateSourceProof.Source(PhaseCandidateSourceProof.Role.COMMANDER, armyId, null, positive(commander.get("character_id"), "commander id")));
                for (JsonNode member : array(army.path("knights").get("members"), "base knight members"))
                    expectedKnights.add(new PhaseCandidateSourceProof.Source(PhaseCandidateSourceProof.Role.KNIGHT, armyId, positive(member.get("source_regiment_id"), "RegimentID"), positive(member.get("character_id"), "knight CharacterID")));
                for (PhaseCandidateSourceProof.Source source : knights) if (source.sourceArmyId() == armyId) nativeArmyOrder.add(source);
            }
            require(commanders.equals(expectedCommanders), "candidate source commanders differ from base");
            Comparator<PhaseCandidateSourceProof.Source> comparator = Comparator.comparingInt(PhaseCandidateSourceProof.Source::sourceArmyId).thenComparingInt(s -> s.sourceRegimentId()).thenComparingInt(PhaseCandidateSourceProof.Source::characterId);
            require(knights.stream().sorted(comparator).toList().equals(expectedKnights.stream().sorted(comparator).toList()), "candidate source knights differ from base");
            require(knights.equals(nativeArmyOrder), "candidate source knight army order differs from base");
            require(orderedPositiveIds(side.get("ordered_commander_ids")).equals(commanders.stream().map(PhaseCandidateSourceProof.Source::characterId).toList())
                    && orderedPositiveIds(side.get("ordered_knight_ids")).equals(knights.stream().map(PhaseCandidateSourceProof.Source::characterId).toList()), "phase side source order mismatch");
            proofs.add(proof);
        }
        return List.copyOf(proofs);
    }
    private static List<CharacterIdentity> expectedCharacters(ArrayNode armies, List<PhaseCandidateSourceProof> proofs) {
        List<CharacterIdentity> result = new ArrayList<>();
        for (JsonNode army : armies) {
            int armyId = nonnegative(army.get("army_id"), "army_id"); String role = text(army.get("encounter_role"), "role");
            JsonNode commander = army.get("commander");
            if (commander.path("status").asText().equals("available")) result.add(new CharacterIdentity(positive(commander.get("character_id"), "commander id"), armyId, null, role, List.of("commander")));
            for (PhaseCandidateSourceProof proof : proofs) for (PhaseCandidateSourceProof.Source source : proof.orderedSources()) {
                if (source.role() != PhaseCandidateSourceProof.Role.KNIGHT || source.sourceArmyId() != armyId) continue;
                int found = -1;
                for (int i = 0; i < result.size(); i++) if (result.get(i).characterId() == source.characterId() && result.get(i).armyId() == armyId) found = i;
                if (found >= 0) {
                    CharacterIdentity current = result.get(found); require(current.regimentId() == null, "base roster repeats a commander/knight");
                    result.set(found, new CharacterIdentity(source.characterId(), armyId, source.sourceRegimentId(), role, List.of("commander", "knight")));
                } else result.add(new CharacterIdentity(source.characterId(), armyId, source.sourceRegimentId(), role, List.of("knight")));
            }
        }
        return List.copyOf(result);
    }
    private static void validateCharacter(JsonNode value, CharacterIdentity expected) {
        ObjectNode row = object(value, CHARACTERS, "phase character");
        require(positive(row.get("character_id"), "character_id") == expected.characterId() && nonnegative(row.get("source_army_id"), "source_army_id") == expected.armyId()
                && text(row.get("encounter_role"), "encounter_role").equals(expected.role()) && strings(row.get("phase_roles"), "phase_roles").equals(expected.phaseRoles()), "phase character identity or role mismatch");
        if (expected.regimentId() == null) require(nil(row.get("source_regiment_id")), "commander-only row invented RegimentID");
        else require(positive(row.get("source_regiment_id"), "source_regiment_id") == expected.regimentId(), "phase knight RegimentID mismatch");
        for (String key : keys(CHARACTER_BOOLS)) bool(row.get(key), key);
        for (String key : keys(CHARACTER_I64)) i64(row.get(key), key);
        for (String key : List.of("martial", "learning", "prowess")) i32(row.get(key), key);
        namedFlags(row.get("traits_or_groups"), TRAITS); namedFlags(row.get("innovations"), INNOVATIONS); namedFlags(row.get("traditions"), TRADITIONS);
        namedFlags(row.get("culture_parameters"), CULTURE); namedFlags(row.get("accolade_parameters"), ACCOLADE); namedFlags(row.get("attribute_unlock_variables"), ATTRIBUTES);
        for (String key : keys(OPTIONAL_IDS)) optionalId(row.get(key), key);
        JsonNode traits = row.get("traits_or_groups"); long wounded = i64(row.get("wounded_rank_raw"), "wounded_rank_raw");
        int memberships = 0, rank = 0;
        for (int i = 1; i <= 3; i++) if (flag(traits, "wounded_" + i)) { memberships++; rank = i; }
        require(memberships <= 1 && wounded == rank * 100_000L, "wounded rank disagrees with traits");
        require(i64(row.get("fragile_bones_rank_raw"), "fragile rank") == (flag(traits, "fragile_bones") ? 100_000L : 0), "fragile-bones rank disagrees with trait");
        if (!present(row.get("liege"))) require(!present(row.get("liege_house")) && i64(row.get("liege_accolade_progress_raw"), "liege progress") == 0, "absent liege published house/progress");
        boolean acclaimed = present(row.get("accolade")); require(flag(row, "is_acclaimed") == acclaimed, "is_acclaimed differs from identity");
        if (!acclaimed) require(!flag(row, "accolade_has_men_at_arms_category") && !anyFlags(row.get("accolade_parameters")), "absent accolade published state");
        if (!present(row.get("employer"))) require(!present(row.get("employer_hold_court_8050_promise")), "absent employer published promise");
        if (!present(row.get("culture"))) require(!anyFlags(row.get("innovations")) && !anyFlags(row.get("traditions")) && !anyFlags(row.get("culture_parameters"))
                && !flag(row, "heritage_north_germanic") && !flag(row, "knights_slightly_more_prone_to_injury") && !flag(row, "blademaster_traits_more_common"), "absent culture published definitions");
        if (!present(row.get("faith"))) require(!flag(row, "death_is_glory") && !flag(row, "tenet_warmonger"), "absent faith published doctrine");
        if (!present(row.get("religion"))) require(!flag(row, "germanic_religion"), "absent religion published membership");
        for (String key : List.of("knights_slightly_more_prone_to_injury", "blademaster_traits_more_common")) require(flag(row, key) == flag(row.get("culture_parameters"), key), "culture mirror differs");
    }
    private static void validateArmy(JsonNode value, JsonNode expected) {
        ObjectNode row = object(value, "army_id native_carmy_id encounter_role maa_regiment_count_raw maa_counts_raw", "phase army");
        require(nonnegative(row.get("army_id"), "army_id") == nonnegative(expected.get("army_id"), "base army_id") && positive(row.get("native_carmy_id"), "native_carmy_id") == positive(expected.get("native_carmy_id"), "base native_carmy_id")
                && text(row.get("encounter_role"), "role").equals(text(expected.get("encounter_role"), "base role")), "phase army identity/role differs");
        ObjectNode counts = object(row.get("maa_counts_raw"), MAA, "maa_counts_raw"); BigInteger sum = BigInteger.ZERO;
        for (String key : keys(MAA)) { long count = nonnegative64(counts.get(key), key); require(count % 100_000 == 0, "MAA count is not whole Q100000"); sum = sum.add(BigInteger.valueOf(count)); }
        long total = nonnegative64(row.get("maa_regiment_count_raw"), "maa_regiment_count_raw");
        require(total % 100_000 == 0 && total / 100_000 <= Integer.MAX_VALUE && sum.compareTo(BigInteger.valueOf(total)) <= 0, "MAA family counts exceed whole signed-int32 total");
    }
    private static void validateSide(JsonNode value, int index, ObjectNode base, ArrayNode characters, PhaseCandidateSourceProof proof) {
        ObjectNode row = object(value, SIDES, "phase side"); String role = index == 0 ? "attacker" : "defender";
        List<Integer> armies = ids(base.path("scenario").get(index == 0 ? "attacker_army_ids" : "defender_army_ids"), false, true, "base side armies");
        List<Integer> expectedCharacters = new ArrayList<>();
        for (JsonNode character : characters) if (character.path("encounter_role").asText().equals(role)) expectedCharacters.add(positive(character.get("character_id"), "character_id"));
        List<Integer> commanders = proof.orderedSources().stream().filter(s -> s.role() == PhaseCandidateSourceProof.Role.COMMANDER).map(PhaseCandidateSourceProof.Source::characterId).toList();
        List<Integer> knights = proof.orderedSources().stream().filter(s -> s.role() == PhaseCandidateSourceProof.Role.KNIGHT).map(PhaseCandidateSourceProof.Source::characterId).toList();
        require(i32(row.get("side_index"), "side_index") == index && text(row.get("encounter_role"), "role").equals(role)
                && ids(row.get("ordered_army_ids"), false, true, "ordered_army_ids").equals(armies) && orderedPositiveIds(row.get("ordered_character_ids")).equals(expectedCharacters)
                && orderedPositiveIds(row.get("ordered_commander_ids")).equals(commanders) && orderedPositiveIds(row.get("ordered_knight_ids")).equals(knights), "phase side roster/order mismatch");
        ArrayNode participants = array(row.get("participants"), "participants"); List<int[]> expected = new ArrayList<>(); Set<Integer> seenOwners = new HashSet<>();
        for (int armyId : armies) for (JsonNode army : array(base.get("armies"), "base armies")) if (army.path("army_id").intValue() == armyId) {
            JsonNode owner = army.get("owner"); eq(owner.get("status"), "available", "phase participant owner unavailable"); int ownerId = positive(owner.get("character_id"), "owner CharacterID");
            if (seenOwners.add(ownerId)) expected.add(new int[]{armyId, ownerId});
        }
        require(!expected.isEmpty() && participants.size() == expected.size(), "participant first-seen owner roster differs");
        for (int i = 0; i < participants.size(); i++) {
            ObjectNode participant = object(participants.get(i), "source_army_id owner_character_id faith_id", "participant");
            require(nonnegative(participant.get("source_army_id"), "source_army_id") == expected.get(i)[0] && positive(participant.get("owner_character_id"), "owner_character_id") == expected.get(i)[1], "participant source order/identity differs"); positive(participant.get("faith_id"), "faith_id");
        }
        require(positive(row.get("primary_participant_character_id"), "primary_participant_character_id") == expected.getFirst()[1] && nonnegative(row.get("primary_source_army_id"), "primary_source_army_id") == armies.getFirst(), "primary participant differs");
        if (!nil(row.get("commander_character_id"))) require(commanders.contains(positive(row.get("commander_character_id"), "commander_character_id")), "battle commander outside side commanders");
        i32(row.get("side_strength_raw"), "side_strength_raw"); long armySize = nonnegative64(row.get("side_army_size_raw"), "side_army_size_raw");
        require(armySize % 100_000 == 0 && armySize / 100_000 <= Integer.MAX_VALUE, "side army size is not whole signed-int32 Q100000");
        for (PhaseCandidateSourceProof.Source source : proof.orderedSources()) {
            require(armies.contains(source.sourceArmyId()), "candidate source army outside side"); int matches = 0;
            for (JsonNode character : characters) if (character.path("encounter_role").asText().equals(role) && character.path("character_id").intValue() == source.characterId()
                    && character.path("source_army_id").intValue() == source.sourceArmyId() && strings(character.get("phase_roles"), "phase_roles").contains(source.role().wire())
                    && (source.role() == PhaseCandidateSourceProof.Role.COMMANDER || character.path("source_regiment_id").intValue() == source.sourceRegimentId())) matches++;
            require(matches == 1, "candidate source does not uniquely match normalized roster");
        }
    }
    private static void validateHostility(JsonNode value, ArrayNode characters, ArrayNode sides) {
        ArrayNode rows = array(value, "faith_hostility"); int ordinal = 0;
        for (JsonNode character : characters) {
            int enemy = character.path("encounter_role").asText().equals("attacker") ? 1 : 0;
            require(present(character.get("faith")), "phase root requires current faith");
            for (JsonNode participant : array(sides.get(enemy).get("participants"), "enemy participants")) {
                require(ordinal < rows.size(), "faith-hostility matrix lacks row");
                ObjectNode row = object(rows.get(ordinal++), "root_character_id enemy_side_index enemy_owner_character_id enemy_faith_id root_faith_id hostility_level_raw", "faith hostility");
                require(positive(row.get("root_character_id"), "root_character_id") == character.path("character_id").intValue() && i32(row.get("enemy_side_index"), "enemy_side_index") == enemy
                        && positive(row.get("enemy_owner_character_id"), "enemy_owner_character_id") == participant.path("owner_character_id").intValue()
                        && positive(row.get("enemy_faith_id"), "enemy_faith_id") == participant.path("faith_id").intValue()
                        && positive(row.get("root_faith_id"), "root_faith_id") == character.path("faith").path("value").intValue(), "faith-hostility matrix order/identity mismatch");
                int level = i32(row.get("hostility_level_raw"), "hostility_level_raw"); require(level >= 0 && level <= 3, "faith hostility outside exact enum");
            }
        }
        require(ordinal == rows.size(), "faith-hostility matrix extra rows");
    }
    static List<Integer> orderedPositiveIds(JsonNode value) {
        List<Integer> result = new ArrayList<>(); for (JsonNode item : array(value, "ordered IDs")) result.add(positive(item, "ordered ID")); return List.copyOf(result);
    }
    private static void namedFlags(JsonNode value, String schema) { ObjectNode row = object(value, schema, "named flags"); for (String key : keys(schema)) bool(row.get(key), key); }
    static boolean flag(JsonNode row, String key) { return row.get(key).booleanValue(); }
    static boolean anyFlags(JsonNode row) { for (JsonNode value : row) if (value.booleanValue()) return true; return false; }
    static boolean present(JsonNode row) { return row.path("status").asText().equals("available"); }
    private static void optionalId(JsonNode value, String name) {
        ObjectNode row = object(value, "status value", name); String status = token(row.get("status"), name + " status", "available", "absent");
        if (status.equals("available")) positive(row.get("value"), name + " value"); else require(nil(row.get("value")), "absent ID must be null");
    }
}
