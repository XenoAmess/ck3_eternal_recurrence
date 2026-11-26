package org.xar.ck3.dynastic.acceptance;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.save.Clausewitz;
import org.xar.ck3.save.Clausewitz.Block;
import org.xar.ck3.save.Clausewitz.Entry;
import org.xar.ck3.save.SaveJson;

/** Checks the emitted synthetic fixture and its operator sequence. */
final class StockCrimePreparationContractTest {
    private static final String PREPARE = "des_acceptance_stock_crime_prepare_decision";
    private static final String CRIME = "des_acceptance_stock_crime_decision";
    private static final String TARGET = "scope:des_test_target";
    private static final String PRIMARY = "scope:des_test_primary";
    private static final String OWNER = "global_var:des_test_extended_owner";
    private static final String PREPARE_STARTED = "des_test_stock_crime_prepare_started";
    private static final String CRIME_STARTED = "des_test_stock_crime_started";
    private static final String READY = "des_test_stock_crime_primary_ready";
    private static final String INPUT_DATE = "des_test_stock_crime_return_input_date";
    private static final String READY_DATE = "des_test_stock_crime_ready_readback_date";
    private static final String STOCK_OPINION = "attempted_murder_me_crime";
    private static final String PRODUCT_OPINION = "des_apostasy_opinion";

    @TempDir Path temporary;

    @Test
    void emittedFixtureSeparatesReturnedMembershipFromCrimeAndMatchesOperatorSequence() throws IOException {
        verify(emit("actual"));

        Path contract = repository().resolve("tools/ck3_mod_acceptance_cases/dynastic_esotericism_core.json");
        JsonNode configuration = SaveJson.read(Files.readAllBytes(contract), JsonNode.class);
        JsonNode phases = configuration.path("gui_phases");
        JsonNode sequence = StreamSupport.stream(phases.spliterator(), false)
                .filter(phase -> "actual-repentance-disable-and-reenable-ui".equals(phase.path("id").asText()))
                .findFirst().orElseThrow().path("operator_sequence");
        List<String> steps = StreamSupport.stream(sequence.spliterator(), false).map(JsonNode::asText).toList();
        int migration = steps.indexOf("des_acceptance_cross_migration_decision_and1_natural_day");
        assertTrue(migration >= 0);
        assertEquals(List.of(
                PREPARE + "_once_and_wait_at_least1_natural_day_for_actual_ready_literal",
                "actual_native_and_independent_Save_prove_same_target_primary_Rite_bound_Dynasty_join_House_and_adopted_source_before_stock_crime",
                CRIME + "_and1_natural_day"), steps.subList(migration + 1, migration + 4));
    }

    @Test
    void rejectsSameTickInputAndMissingReadbackGuards() throws IOException {
        Fixture fixture = emit("mutations");
        String decisions = fixture.decisions();
        String events = fixture.events();
        for (String changed : List.of(
                decisions.replace("subtract = 1", "subtract = 0"),
                decisions.replace("id = des_acceptance_extended.18 days = 1", "id = des_acceptance_extended.18 days = 0"),
                decisions.replace("var:des_adopted_bound_rite = " + PRIMARY, "always = yes"),
                decisions.replace(TARGET + " = { set_character_rite = scope:des_test_source_rite }",
                        TARGET + " = { set_character_rite = " + PRIMARY + " set_character_rite = scope:des_test_source_rite }"),
                decisions.replace("NOT = { has_character_flag = " + PREPARE_STARTED + " }", ""),
                decisions.replace("dynasty = scope:des_test_dynasty", "dynasty = scope:des_test_second_dynasty"),
                decisions.replace("house = " + PRIMARY + ".var:des_join_house", "house = root.house"),
                decisions.replace("modifier = " + STOCK_OPINION, "modifier = " + PRODUCT_OPINION))) {
            assertNotEquals(decisions, changed);
            assertThrows(AssertionError.class, () -> verify(new Fixture(changed, events)));
        }
        for (String changed : List.of(
                events.replace("delayed = yes", "delayed = no"),
                events.replace("subtract = 1", "subtract = 0"))) {
            assertNotEquals(events, changed);
            assertThrows(AssertionError.class, () -> verify(new Fixture(decisions, changed)));
        }
    }

    private record Fixture(String decisions, String events) { }

    private static Path repository() {
        return Path.of(System.getProperty("dynastic.source")).toAbsolutePath().normalize().getParent();
    }

    private Fixture emit(String name) throws IOException {
        Path path = FixtureEmitter.emit(repository(), temporary.resolve(name), "authored-machine").fixture();
        return new Fixture(
                Files.readString(path.resolve("common/decisions/des_acceptance_extended_decisions.txt")),
                Files.readString(path.resolve("events/des_acceptance_extended_events.txt")));
    }

    private static void verify(Fixture fixture) {
        Block decisions = Clausewitz.parse(fixture.decisions());
        Block events = Clausewitz.parse(fixture.events());
        Block preparation = decisionInput(decisions, PREPARE, PREPARE_STARTED);
        Block preparationGate = decisions.block(PREPARE).block("is_shown");
        atom(preparationGate, "has_character_flag", "des_test_cross_migration_verified");
        assertTrue(negated(preparationGate, "has_character_flag", CRIME_STARTED));

        Block input = preparation.block("if");
        atom(input.block("limit"), "this", OWNER);
        atom(input.block("set_variable"), "name", INPUT_DATE);
        atom(input.block("set_variable"), "value", "current_date");
        atom(input.block(TARGET), "set_character_rite", PRIMARY);
        atom(input.block("trigger_event"), "id", "des_acceptance_extended.18");
        atom(input.block("trigger_event"), "days", "1");
        assertEquals(1, count(preparation, "set_character_rite"));
        assertEquals(0, count(preparation, "add_opinion"));

        Block deferred = events.block("des_acceptance_extended.18").block("immediate").block("trigger_event");
        atom(deferred, "id", "des_acceptance_extended.19");
        atom(deferred, "delayed", "yes");
        Block readback = events.block("des_acceptance_extended.19").block("immediate");
        Block ready = readback.block("if");
        Block readyLimit = ready.block("limit");
        membershipGuard(readyLimit);
        assertTrue(negated(readyLimit, "has_character_flag", CRIME_STARTED));
        assertTrue(negated(readyLimit, "has_character_flag", READY));
        atom(ready, "add_character_flag", READY);
        atom(ready.block("set_variable"), "name", READY_DATE);
        atom(ready.block("set_variable"), "value", "current_date");
        atom(ready, "debug_log", "\"DESAF: PRECONDITION PASS stock_crime_primary_membership_ready\"");
        fixtureOnly(readback);
        assertEquals(0, count(readback, "add_opinion"));
        assertEquals(0, count(readback, "set_character_rite"));

        Block crime = decisionInput(decisions, CRIME, CRIME_STARTED);
        atom(decisions.block(CRIME).block("is_shown"), "has_character_flag", READY);
        Block applied = crime.block("if");
        Block appliedLimit = applied.block("limit");
        membershipGuard(appliedLimit);
        assertTrue(appliedLimit.named("has_character_flag").stream().anyMatch(entry -> entry.value().equals(new Clausewitz.Atom(READY))));
        assertEquals(1, count(crime, "set_character_rite"));
        assertEquals(1, count(crime, "add_opinion"));
        atom(applied.block("add_opinion"), "target", TARGET);
        atom(applied.block("add_opinion"), "modifier", STOCK_OPINION);
        assertTrue(position(applied, "add_opinion") < position(applied, TARGET));
        atom(applied.block(TARGET), "set_character_rite", "scope:des_test_source_rite");
        atom(applied.block("trigger_event"), "id", "des_acceptance_extended.20");
        atom(applied.block("trigger_event"), "days", "1");

        Block result = events.block("des_acceptance_extended.20").block("immediate").block("if").block("limit");
        assertEquals(6, result.entries().size());
        atom(result.block(TARGET), "des_is_apostate_trigger", "yes");
        assertEquals(2, result.named("has_opinion_modifier").size());
        Set<String> opinions = result.named("has_opinion_modifier").stream().map(entry -> {
            Block opinion = assertInstanceOf(Block.class, entry.value());
            atom(opinion, "target", TARGET);
            return opinion.atom("modifier", null);
        }).collect(Collectors.toSet());
        assertEquals(Set.of(PRODUCT_OPINION, STOCK_OPINION), opinions);
        for (String reason : List.of("has_imprisonment_reason", "has_banish_reason", "has_execute_reason")) {
            atom(result, reason, TARGET);
        }
    }

    private static Block decisionInput(Block decisions, String name, String started) {
        Block decision = decisions.block(name);
        Block shown = decision.block("is_shown");
        atom(shown, "this", OWNER);
        assertTrue(negated(shown, "has_character_flag", started));
        Block hidden = decision.block("effect").block("hidden_effect");
        atom(hidden, "add_character_flag", started);
        assertTrue(position(hidden, "add_character_flag") < position(hidden, "if"));
        fixtureOnly(hidden);
        return hidden;
    }

    private static void membershipGuard(Block guard) {
        atom(guard, "this", OWNER);
        atom(guard, "has_variable", INPUT_DATE);
        assertTrue(guard.named("has_character_flag").stream()
                .anyMatch(entry -> entry.value().equals(new Clausewitz.Atom(PREPARE_STARTED))));
        Entry observedDay = guard.named("var:" + INPUT_DATE).getFirst();
        assertEquals("<=", observedDay.operator());
        Block date = assertInstanceOf(Block.class, observedDay.value());
        atom(date, "value", "current_date");
        atom(date, "subtract", "1");

        Block target = guard.block(TARGET);
        atom(target, "is_alive", "yes");
        atom(target, "rite", PRIMARY);
        atom(target, "dynasty", "scope:des_test_dynasty");
        atom(target, "house", PRIMARY + ".var:des_join_house");
        atom(target, "var:des_adopted_bound_rite", PRIMARY);
        assertTrue(negated(target, "des_is_apostate_trigger", "yes"));
        assertTrue(negated(target, "has_trait", "des_apostate"));
    }

    private static boolean negated(Block block, String key, String value) {
        return block.named("NOT").stream().anyMatch(entry -> entry.value() instanceof Block condition
                && value.equals(condition.atom(key, null)));
    }

    private static void fixtureOnly(Block block) {
        Set<String> prohibited = Set.of("set_house", "set_dynasty", "create_dynasty", "add_trait", "remove_trait",
                "des_sync_character_effect", "des_sync_rite_effect", "remove_character_flag");
        assertTrue(walk(block).noneMatch(entry -> prohibited.contains(entry.key())));
        walk(block).filter(entry -> entry.key().equals("set_variable")).forEach(entry ->
                assertTrue(assertInstanceOf(Block.class, entry.value()).atom("name", "").startsWith("des_test_")));
    }

    private static int position(Block block, String key) {
        return block.entries().indexOf(block.named(key).getFirst());
    }

    private static long count(Block block, String key) {
        return walk(block).filter(entry -> entry.key().equals(key)).count();
    }

    private static Stream<Entry> walk(Block block) {
        return block.entries().stream().flatMap(entry -> Stream.concat(Stream.of(entry),
                entry.value() instanceof Block child ? walk(child) : Stream.empty()));
    }

    private static void atom(Block block, String key, String expected) {
        assertEquals(expected, block.atom(key, null), key);
    }
}
