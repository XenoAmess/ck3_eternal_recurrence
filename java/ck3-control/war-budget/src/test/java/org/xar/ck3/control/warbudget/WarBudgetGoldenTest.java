package org.xar.ck3.control.warbudget;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.stream.Stream;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** Committed vectors only: no Python, Service, filesystem ledger or native process in default CI. */
final class WarBudgetGoldenTest {
    private static final String RESOURCE = "/org/xar/ck3/control/warbudget/budget_golden_v1.jsonl.gz";
    private static final Set<String> OPERATIONS = Set.of("priority_emergency_level_v1", "observe_emergency_policy_v1",
        "valid_saved_emergency_revision_v1", "emergency_quote_budget_v1", "observe_emergency_recovery_v1");
    private record Vector(ObjectNode metadata, byte[] request, JsonNode expected) { }
    private record Corpus(ObjectNode header, List<Vector> vectors) { }

    @TestFactory
    Stream<DynamicTest> frozenOriginalProducerConsumerVectors() throws IOException {
        return corpus().vectors().stream().map(vector -> DynamicTest.dynamicTest(
            vector.metadata().path("ordinal") + " " + vector.metadata().path("test_case").textValue(), () -> {
                if (vector.metadata().path("expected_kind").asText().equals("invalid_contract")) {
                    assertThrows(ContractViolationException.class, () -> WarBudgetCodec.evaluate(vector.request()));
                } else {
                    byte[] output = WarBudgetCodec.evaluate(vector.request());
                    assertArrayEquals(StrictJson.canonical(vector.expected()), output);
                    assertEquals(StrictJson.parse(output), StrictJson.parse(StrictJson.canonical(StrictJson.parse(output))));
                }
            }));
    }
    @Test
    void fullCaptureHasAllOperationsExactSourcesAndNoSkippedOriginalTests() throws IOException {
        Corpus corpus = corpus(); JsonNode header = corpus.header();
        assertEquals("g2.war-budget-golden/v1", header.path("schema").textValue());
        assertEquals("frozen_vectors_only", header.path("default_ci_mode").textValue());
        assertTrue(header.path("original_tests").path("passed").intValue() > 0);
        assertEquals(0, header.path("original_tests").path("failed").intValue());
        assertEquals(0, header.path("original_tests").path("skipped").intValue());
        assertEquals(0, header.path("native_game_rpc_count").intValue());
        assertEquals(corpus.vectors().size(), header.path("vector_count").intValue());
        assertFalse(StrictJson.text(header.get("machine_id")).isEmpty());
        Set<String> operations = new HashSet<>(); int index = 0;
        for (Vector vector : corpus.vectors()) {
            assertEquals(++index, vector.metadata().path("ordinal").intValue());
            WarBudgetCodec.Request request = WarBudgetCodec.parse(vector.request()); operations.add(request.operation().wire());
        }
        assertEquals(OPERATIONS, operations);
        JsonNode pins = header.path("source_sha256");
        assertTrue(pins.size() >= 12);
        pins.elements().forEachRemaining(value -> assertTrue(value.textValue().matches("[0-9a-f]{64}")));
    }
    @Test
    void thresholdBoundariesKeepRawNegativeDeadlineAndUnboundedScore() {
        ObjectNode war = BudgetJson.obj().put("primary_player_war", true).put("player_side", "defender").put("raised_force_deficit", true);
        war.putObject("target_stakes_v1").put("current_root_available", true).put("primary_title_targeted", true);
        war.putArray("observed_primary_opponent_objective_occupation_province_ids");
        war.putArray("observed_hostile_siege_in_player_subrealm_army_ids").add(1);
        war.put("player_relative_war_score", -75).put("observed_risk_deadline_days", 7);
        assertEquals(2, WarEmergencyBudget.priorityLevel(war));
        war.put("observed_risk_deadline_days", 8); assertEquals(1, WarEmergencyBudget.priorityLevel(war));
        war.put("observed_risk_deadline_days", -1); assertEquals(2, WarEmergencyBudget.priorityLevel(war));
        war.put("player_relative_war_score", BigInteger.ONE.shiftLeft(90).negate()); assertEquals(2, WarEmergencyBudget.priorityLevel(war));
        war.putNull("observed_risk_deadline_days"); assertEquals(1, WarEmergencyBudget.priorityLevel(war));
        war.put("player_relative_war_score", -49); assertEquals(0, WarEmergencyBudget.priorityLevel(war));
        war.putArray("observed_primary_opponent_objective_occupation_province_ids").add(1);
        war.put("player_relative_war_score", -25); assertEquals(1, WarEmergencyBudget.priorityLevel(war));
        war.put("player_relative_war_score", -24); assertEquals(0, WarEmergencyBudget.priorityLevel(war));
    }
    @Test
    void publicWireRejectsWrongMissingExtraAndFloatingIntegerAmounts() throws IOException {
        ObjectNode outer = BudgetJson.obj().put("schema", WarBudgetCodec.SCHEMA).put("operation", "priority_emergency_level_v1");
        outer.putObject("arguments").putObject("war");
        byte[] raw = StrictJson.canonical(outer);
        assertArrayEquals(raw, StrictJson.canonical(WarBudgetCodec.parse(raw).toJson()));
        ObjectNode bad = outer.deepCopy(); bad.put("extra", true); invalid(bad);
        bad = outer.deepCopy(); bad.remove("arguments"); invalid(bad);
        bad = outer.deepCopy(); ((ObjectNode) bad.get("arguments")).put("war", true); invalid(bad);
        assertThrows(ContractViolationException.class, () -> WarBudgetCodec.evaluate(
            (new String(raw, StandardCharsets.UTF_8) + " false").getBytes(StandardCharsets.UTF_8)));
        assertThrows(ContractViolationException.class, () -> BudgetJson.integer(StrictJson.parse("true".getBytes(StandardCharsets.UTF_8))));
        assertThrows(ContractViolationException.class, () -> BudgetJson.integer(StrictJson.parse("1.0".getBytes(StandardCharsets.UTF_8))));
        assertThrows(ContractViolationException.class, () -> BudgetJson.integer(StrictJson.parse("\"1\"".getBytes(StandardCharsets.UTF_8))));
        ObjectNode missing = BudgetJson.obj(); assertEquals(BigInteger.ZERO, BudgetJson.defaultInteger(missing, "committed", BigInteger.ZERO));
        missing.putNull("committed"); assertThrows(ContractViolationException.class, () -> BudgetJson.defaultInteger(missing, "committed", BigInteger.ZERO));
        assertThrows(ContractViolationException.class, () -> BudgetJson.listPresent(BudgetJson.obj().putArray("x").add(true)));
        assertThrows(ContractViolationException.class, () -> WarEmergencyBudget.recovery(BudgetJson.obj(),
            BudgetJson.obj().putNull("observed"), com.fasterxml.jackson.databind.node.NullNode.instance));
    }
    @Test
    void epochHashUsesDefaultPythonAsciiSpacingAndOrderedWarIds() {
        ObjectNode frame = BudgetJson.obj().put("played_character_id", 7).put("native_revision", 2).put("date_raw", 3)
            .put("snapshot_id", "native:2").put("revision", 4).put("episode_run_id", "轮回😀");
        StringBuilder text = new StringBuilder(); BudgetJson.pythonDefault(frame, text);
        assertTrue(text.toString().contains(": ")); assertTrue(text.toString().contains(", "));
        assertTrue(text.toString().contains("\\u8f6e\\u56de\\ud83d\\ude00"));
        assertEquals(BudgetJson.fallbackEpoch(frame, List.of(BigInteger.TWO, BigInteger.ONE)),
            BudgetJson.fallbackEpoch(frame, List.of(BigInteger.ONE, BigInteger.TWO)));
        assertEquals(24, BudgetJson.fallbackEpoch(frame, List.of(BigInteger.ONE)).length());
    }
    @Test
    void negativeTreasuryDoesNotBecomeUnsignedAndOneTimeQuoteIsNotMultiplied() {
        ObjectNode snapshot = BudgetJson.obj().put("native_revision", 2).put("date_raw", 3);
        snapshot.putObject("played_character").put("character_id", 7);
        snapshot.putObject("played_character_gold").put("raw", -5).put("scale", 100000);
        ObjectNode root = BudgetJson.obj().put("status", "available").put("player_character_id", 7).put("snapshot_revision", 2).put("date_raw", 3);
        root.putObject("player_monthly_gold_income").put("raw", -10).put("scale", 100000);
        root.putObject("player_max_monthly_gold_maintenance_v1").put("status", "available")
            .putObject("value").put("raw", 2).put("scale", 100000);
        JsonNode price = BudgetJson.obj().put("x", 3).get("x"), months = BudgetJson.obj().put("x", 18).get("x");
        JsonNode finance = BudgetObservations.finance(snapshot, root, price, months, BigInteger.ZERO, 6, BigInteger.ONE);
        assertEquals("available", finance.path("status").textValue());
        assertEquals(BigInteger.valueOf(-8), finance.path("gold_after_contract_raw").bigIntegerValue());
        assertEquals(BigInteger.valueOf(13), finance.path("required_gold_reserve_raw").bigIntegerValue());
        assertEquals(0, finance.path("future_gross_income_credited_raw").intValue());
        assertFalse(finance.path("retains_military_allocation").booleanValue());
    }
    private static void invalid(ObjectNode value) { assertThrows(ContractViolationException.class, () -> WarBudgetCodec.evaluate(StrictJson.canonical(value))); }
    private static Corpus corpus() throws IOException {
        try (InputStream resource = WarBudgetGoldenTest.class.getResourceAsStream(RESOURCE)) {
            if (resource == null) { throw new AssertionError("committed budget golden absent; no default skip"); }
            try (GZIPInputStream gzip = new GZIPInputStream(resource)) {
                byte[] raw = gzip.readNBytes(8 * 1024 * 1024 + 1); assertTrue(raw.length <= 8 * 1024 * 1024);
                String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
                String[] lines = text.split("\n", -1); assertEquals("", lines[lines.length - 1]); assertEquals(0, (lines.length - 2) % 3);
                ObjectNode header = BudgetJson.record(StrictJson.parse(lines[0].getBytes(StandardCharsets.UTF_8)));
                List<Vector> vectors = new ArrayList<>();
                for (int i = 1; i < lines.length - 1; i += 3) {
                    vectors.add(new Vector(BudgetJson.record(StrictJson.parse(lines[i].getBytes(StandardCharsets.UTF_8))),
                        lines[i + 1].getBytes(StandardCharsets.UTF_8), StrictJson.parse(lines[i + 2].getBytes(StandardCharsets.UTF_8))));
                }
                return new Corpus(header, List.copyOf(vectors));
            }
        }
    }
}
