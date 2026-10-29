package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

final class NativeActiveWarsCodecTest {
    private record Case(String name, JsonNode input) { }

    @Test void fullWarProducerKeepsOccurrencesRolesObjectivesAndSerde() {
        ObjectNode war = war();
        war.set("objective_province_states", objectives(objective(10), objective(20)));
        war.withArray("allied_armies").add(army(0, true)).add(army(0, false));
        war.withArray("enemy_armies").add(army(9, false));
        war.put("ignored_original_extra", "not canonical");
        var decoded = NativeActiveWarsCodec.normalize(wars(war, war.deepCopy()));
        assertEquals(2, decoded.size(), "separate native War occurrences are retained");
        assertEquals(List.of(BigInteger.valueOf(9), BigInteger.valueOf(2), BigInteger.ZERO), decoded.getFirst().targetedTitleIds());
        assertEquals(List.of(BigInteger.TEN, BigInteger.valueOf(20)), decoded.getFirst().warObjectiveProvinceIds());
        assertEquals(2, decoded.getFirst().alliedArmies().size(), "same CUnit occurrences are not deduplicated here");
        assertEquals(1, decoded.getFirst().enemyArmies().size());
        ObjectNode canonical = NativeActiveWarsCodec.encodeWar(decoded.getFirst());
        assertFalse(canonical.has("ignored_original_extra"));
        assertEquals(NativeArmiesCodec.encode(decoded.getFirst().alliedArmies()), canonical.get("allied_armies"));
        assertEquals("native", canonical.get("source").textValue());
        assertEquals(decoded, NativeActiveWarsCodec.normalize(NativeActiveWarsCodec.encode(decoded)));
        assertEquals(0, NativeActiveWarsCodec.normalize((JsonNode) null).size());
        assertEquals(0, NativeActiveWarsCodec.normalize(com.fasterxml.jackson.databind.node.NullNode.instance).size());
    }

    @Test void fullSiegeUsesTheSingleSharedCodecAndKeepsMissingNullZeroAndRepeatedRegiments() {
        ObjectNode raw = objective(10); raw.put("siege_observable", true);
        ObjectNode siege = siege(); raw.set("active_siege", siege);
        ObjectNode war = war(); war.putArray("war_objective_province_ids").add(10);
        war.set("objective_province_states", objectives(raw));
        var decoded = NativeActiveWarsCodec.normalize(wars(war));
        var objective = decoded.getFirst().objectiveProvinceStates().getFirst();
        assertInstanceOf(Missing.class, objective.currentBesiegingArmySelection());
        assertEquals(ArmyWarOccupationCodec.siege(siege), objective.activeSiege().orElseThrow());
        ObjectNode out = NativeActiveWarsCodec.encodeWar(decoded.getFirst());
        JsonNode normalizedSiege = out.get("objective_province_states").get(0).get("active_siege");
        assertFalse(normalizedSiege.has("eligible_regiment_siege_work"));
        assertEquals(2, normalizedSiege.get("province_unit_occurrences").size());
        assertEquals(2, normalizedSiege.get("province_unit_occurrences").get(0).get("qualified_regiment_ids").size());
        assertEquals(0, normalizedSiege.get("siege_id").intValue(), "observed slot zero is valid");

        raw.putNull("current_besieging_army_selection"); siege.putNull("eligible_regiment_siege_work");
        var explicitNull = NativeActiveWarsCodec.normalize(wars(war)).getFirst().objectiveProvinceStates().getFirst();
        assertInstanceOf(NullValue.class, explicitNull.currentBesiegingArmySelection());
        assertTrue(explicitNull.activeSiege().orElseThrow().normalized().members().containsKey("eligible_regiment_siege_work"));

        raw.set("current_besieging_army_selection", empty());
        siege.set("eligible_regiment_siege_work", fixed(0));
        var measuredZero = NativeActiveWarsCodec.normalize(wars(war)).getFirst().objectiveProvinceStates().getFirst();
        assertInstanceOf(Present.class, measuredZero.currentBesiegingArmySelection());
        ObjectNode measured = NativeActiveWarsCodec.encodeObjective(measuredZero);
        assertEquals(0, measured.get("active_siege").get("eligible_regiment_siege_work").get("raw").intValue());
        assertTrue(measured.get("current_besieging_army_selection").get("native_carmy_id").isNull());
    }

    @Test void invalidTypesAndIncompleteObjectivesCannotPublishAValidWar() {
        for (Case sample : rejectedCases()) assertThrows(IllegalArgumentException.class,
                () -> NativeActiveWarsCodec.normalize(sample.input()), sample.name());
    }

    @Test void completeProducerMatchesThePinnedOriginalPythonNormalizerInOneIndependentProcess() throws Exception {
        String repositoryProperty = System.getProperty("xar.repository.root");
        String python = System.getProperty("xar.native.producer.python");
        assertNotNull(repositoryProperty, "whole CI must provide xar.repository.root; missing oracle is RED");
        assertNotNull(python, "whole CI must provide xar.native.producer.python; missing oracle is RED");
        Path repository = Path.of(repositoryProperty).toRealPath();
        Path original = repository.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py");
        assertEquals("b1b14953f01d66c9f6720e4c92cb6b30c26eb1946b20e9b4ba932c9b5e1f7937",
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(original))),
                "actual original source must match the source selection, not an invented oracle");
        requireOriginal(repository, "province_besieging_army_selection_contract.py",
                "0bf1ebd7ac1f77e607e0654b430e865546c04d72a3caa143541f799dc619f354");
        requireOriginal(repository, "siege_membership_contract.py",
                "501c9a24331a1a4121ea3bf0cd74ac63c954ca565ea5e5fb2e0a5b42a5ff23bf");
        List<Case> samples = new ArrayList<>(acceptedCases()); samples.addAll(rejectedCases());
        ArrayNode requests = com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.arrayNode();
        samples.forEach(sample -> requests.add(sample.input()));
        ObjectNode input = empty(); input.set("cases", requests);
        String script = """
                import json, sys
                sys.dont_write_bytecode = True
                sys.path.insert(0, sys.argv[1] + "/ck3_autonomous_player/src")
                from xar_autoplayer.bridge.war_contract import normalize_active_wars
                replies = []
                for raw in json.load(sys.stdin)["cases"]:
                    try:
                        replies.append({"ok": True, "value": normalize_active_wars(raw)})
                    except (ValueError, TypeError) as error:
                        replies.append({"ok": False})
                print(json.dumps({"cases": replies}, separators=(",", ":")))
                """;
        Process process = new ProcessBuilder(python, "-B", "-c", script, repository.toString())
                .redirectErrorStream(true).start();
        var executor = Executors.newSingleThreadExecutor();
        try {
            var output = executor.submit(() -> process.getInputStream().readNBytes(1024 * 1024 + 1));
            try (var stdin = process.getOutputStream()) { stdin.write(bytes(input)); }
            assertTrue(process.waitFor(60, TimeUnit.SECONDS), "single original Python oracle exceeded the full bounded deadline");
            byte[] stdout = output.get(5, TimeUnit.SECONDS);
            assertTrue(stdout.length <= 1024 * 1024, "oracle result exceeded bounded whole-case output");
            assertEquals(0, process.exitValue(), new String(stdout, StandardCharsets.UTF_8));
            JsonNode replies = parse(stdout).get("cases");
            assertEquals(samples.size(), replies.size());
            for (int index = 0; index < samples.size(); index++) {
                Case sample = samples.get(index); JsonNode expected = replies.get(index);
                try {
                    ArrayNode actual = NativeActiveWarsCodec.encode(NativeActiveWarsCodec.normalize(sample.input()));
                    assertTrue(expected.get("ok").booleanValue(), sample.name() + ": Java accepted a rejected original input");
                    ObjectNode normalizedActual = empty(); normalizedActual.set("value", actual);
                    ObjectNode normalizedExpected = empty(); normalizedExpected.set("value", expected.get("value"));
                    assertEquals(parse(bytes(normalizedExpected)), parse(bytes(normalizedActual)), sample.name());
                } catch (IllegalArgumentException rejected) {
                    assertFalse(expected.get("ok").booleanValue(), sample.name() + ": Java rejected an accepted original input: " + rejected);
                }
            }
        } finally { process.destroyForcibly(); executor.shutdownNow(); }
    }

    private static List<Case> acceptedCases() {
        List<Case> result = new ArrayList<>();
        result.add(new Case("null collection", com.fasterxml.jackson.databind.node.NullNode.instance));
        result.add(new Case("empty collection", wars()));
        result.add(new Case("ordered duplicate War occurrences", wars(war(), war())));
        ObjectNode omitted = empty().put("war_id", 0).put("player_side", "defender").put("player_relative_war_score", 0);
        result.add(new Case("omitted optional values and lists", wars(omitted)));
        ObjectNode nullable = omitted.deepCopy(); nullable.putNull("targeted_title_ids"); nullable.putNull("allied_armies");
        nullable.putNull("enemy_armies"); nullable.putNull("objective_province_states"); result.add(new Case("null lists", wars(nullable)));
        ObjectNode large = war().put("war_id", new BigInteger("18446744073709551617000"))
                .put("player_relative_war_score", new BigInteger("-18446744073709551617000"));
        large.putArray("war_objective_province_ids").add(new BigInteger("18446744073709551617000"));
        result.add(new Case("general original integer domain is lossless", wars(large)));
        ObjectNode armies = war(); armies.withArray("allied_armies").add(army(0, true)).add(army(0, false));
        armies.withArray("enemy_armies").add(army(Integer.MAX_VALUE, false));
        result.add(new Case("allied enemy roles and repeated Army occurrences", wars(armies)));
        for (int selection = 0; selection < 3; selection++) {
            ObjectNode row = objective(10).put("siege_observable", true), siege = siege();
            row.set("active_siege", siege);
            if (selection == 1) { row.putNull("current_besieging_army_selection"); siege.putNull("eligible_regiment_siege_work"); }
            if (selection == 2) {
                row.set("current_besieging_army_selection", empty().put("native_carmy_id", 0).put("public_unit_id", 0).put("controllable", false));
                siege.set("eligible_regiment_siege_work", fixed(0)); siege.put("highest_eligible_siege_tier", 0);
            }
            ObjectNode sample = war(); sample.putArray("war_objective_province_ids").add(10);
            sample.set("objective_province_states", objectives(row));
            result.add(new Case("complete Siege missing/null/measured zero " + selection, wars(sample)));
        }
        ObjectNode occupied = objective(10).put("occupation_observable", true).put("is_occupied", true).put("occupying_character_id", Integer.MAX_VALUE);
        occupied.put("fort_level", 0).put("garrison_size", 0).put("besieging_strength", 0);
        ObjectNode sample = war(); sample.putArray("war_objective_province_ids").add(10); sample.set("objective_province_states", objectives(occupied));
        result.add(new Case("actual occupied objective and measured zero counts", wars(sample)));
        occupied.put("is_occupied", false).putNull("occupying_character_id");
        result.add(new Case("actual unoccupied objective", wars(sample.deepCopy())));
        ObjectNode active = siege().put("assault_observable", true).put("breach_level", 2)
                .put("assault_in_progress", true).put("can_start_assault", false).put("can_stop_assault", true)
                .put("assault_daily_casualties", Integer.MAX_VALUE).put("prepared_selected_phase_event_enum", 5);
        active.set("assault_daily_progress", fixed(Long.MAX_VALUE));
        active.set("phase_event_state", empty().put("breach_level", 2).put("starvation_level", 0)
                .put("disease_level", 0).put("desertion_count", 0).put("stalemate_count", 0));
        sample = war(); sample.putArray("war_objective_province_ids").add(10);
        sample.set("objective_province_states", objectives(withField(objective(10).put("siege_observable", true), "active_siege", active)));
        result.add(new Case("whole observed assault and prepared phase state", wars(sample)));
        active.putNull("province_unit_occurrences"); active.putNull("phase_event_state");
        result.add(new Case("whole unknown occurrences and phase state remain explicit null", wars(sample)));
        return List.copyOf(result);
    }

    private static List<Case> rejectedCases() {
        List<Case> result = new ArrayList<>();
        result.add(new Case("collection is object", empty()));
        result.add(new Case("War occurrence is null", wars(com.fasterxml.jackson.databind.node.NullNode.instance)));
        for (String key : List.of("war_id", "primary_opponent_character_id", "enemy_primary_default_raise_province_id", "player_relative_war_score")) {
            ObjectNode value = war(); value.put(key, true); result.add(new Case(key + " bool is not integer", wars(value)));
            value = war(); value.put(key, 1.0); result.add(new Case(key + " float is not integer", wars(value)));
        }
        result.add(new Case("bad side", wars(war().put("player_side", "observer"))));
        result.add(new Case("War ID negative", wars(war().put("war_id", -1))));
        result.add(new Case("leader integer is not boolean", wars(war().put("player_is_primary_war_leader", 1))));
        ObjectNode value = war(); value.putArray("targeted_title_ids").add(false);
        result.add(new Case("boolean target", wars(value)));
        value = war(); value.set("war_objective_province_ids", empty()); result.add(new Case("objective IDs are not a list", wars(value)));
        value = war(); value.set("objective_province_states", objectives(objective(20), objective(10)));
        result.add(new Case("objective order differs", wars(value)));
        value = war(); value.set("objective_province_states", objectives(objective(10)));
        result.add(new Case("nonempty objective subset", wars(value)));
        value = war(); value.withArray("allied_armies").add(army(0, true).put("army_id", true));
        result.add(new Case("nested Army boolean ID", wars(value)));
        for (ObjectNode objective : List.of(
                objective(0), objective(10).put("occupation_observable", false).put("is_occupied", false),
                objective(10).put("occupation_observable", true).put("is_occupied", true),
                objective(10).put("occupation_observable", true).put("is_occupied", false).put("occupying_character_id", 2),
                objective(10).put("fort_level", 2147483648L),
                withField(objective(10), "active_siege", siege()),
                withField(objective(10), "current_besieging_army_selection", empty().put("native_carmy_id", -1)),
                withField(objective(10), "current_besieging_army_selection", empty().put("public_unit_id", 2147483648L)))) {
            value = war(); value.putArray("war_objective_province_ids").add(10); value.set("objective_province_states", objectives(objective));
            result.add(new Case("invalid exact objective " + result.size(), wars(value)));
        }
        for (ObjectNode invalidSiege : List.of(
                siege().put("siege_id", -1),
                siege().put("siege_id", 2147483648L),
                siege().put("breach_level", 1),
                siege().put("prepared_selected_phase_event_enum", 6),
                withField(siege(), "progress_fraction", fixed(100001)),
                withField(siege(), "province_unit_occurrences", wars(empty().put("occurrence_index", 1))),
                siege().put("assault_observable", true).put("breach_level", 3),
                siege().put("player_army_besieging", 1))) {
            value = war(); value.putArray("war_objective_province_ids").add(10);
            value.set("objective_province_states", objectives(withField(objective(10).put("siege_observable", true), "active_siege", invalidSiege)));
            result.add(new Case("invalid complete Siege subtree " + result.size(), wars(value)));
        }
        return List.copyOf(result);
    }

    private static ObjectNode war() {
        ObjectNode result = empty().put("war_id", 0).put("player_side", "attacker").put("player_relative_war_score", -17);
        result.putArray("targeted_title_ids").add(9).add(2).add(9).add(0);
        result.putArray("war_objective_province_ids").add(10).add(20).add(10);
        result.putArray("allied_armies"); result.putArray("enemy_armies"); return result;
    }
    private static ObjectNode army(int id, boolean controllable) {
        return empty().put("army_id", id).put("owner_character_id", 29829).put("soldiers", 0)
                .put("current_province_id", 10).putNull("move_target_province_id").put("controllable", controllable);
    }
    private static ObjectNode objective(int province) {
        return empty().put("province_id", province).put("occupation_observable", false).put("siege_observable", false);
    }
    private static ObjectNode siege() {
        ObjectNode result = empty().put("siege_id", 0).put("player_army_besieging", true);
        result.putNull("besieging_army_id"); result.set("progress_fraction", fixed(50000));
        result.set("current_work", fixed(7)); result.set("total_work", fixed(11));
        ArrayNode occurrences = result.putArray("province_unit_occurrences");
        for (int index = 0; index < 2; index++) {
            ObjectNode occurrence = empty().put("occurrence_index", index).put("public_unit_id", 0).put("native_carmy_id", 0).put("eligible", true);
            occurrence.putArray("qualified_regiment_ids").add(0).add(0); occurrences.add(occurrence);
        }
        return result;
    }
    private static ObjectNode fixed(long value) { return empty().put("raw", value).put("scale", 100000); }
    private static ObjectNode withField(ObjectNode target, String name, JsonNode value) {
        target.set(name, value); return target;
    }
    private static void requireOriginal(Path repository, String name, String sha256) throws Exception {
        Path source = repository.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge").resolve(name);
        assertEquals(sha256, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(source))),
                "same original imported contract source required: " + name);
    }
    private static ArrayNode wars(JsonNode... values) {
        ArrayNode result = com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.arrayNode();
        for (JsonNode value : values) result.add(value.deepCopy()); return result;
    }
    private static ArrayNode objectives(ObjectNode... values) {
        ArrayNode result = com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.arrayNode();
        for (ObjectNode value : values) result.add(value); return result;
    }
}
