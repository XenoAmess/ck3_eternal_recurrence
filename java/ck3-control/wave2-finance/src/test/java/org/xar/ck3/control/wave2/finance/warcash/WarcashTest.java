package org.xar.ck3.control.wave2.finance.warcash;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.finance.warcash.WarcashModel.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Stream;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

final class WarcashTest {
    private record Vector(ObjectNode metadata, byte[] request, JsonNode expected) { }
    private record Corpus(ObjectNode header, List<Vector> vectors) { }
    @TestFactory
    Stream<DynamicTest> originalProducerAndAllConsumerVectors() throws IOException {
        return corpus().vectors().stream().map(vector -> DynamicTest.dynamicTest(
            vector.metadata().path("ordinal") + " " + vector.metadata().path("test_case").asText(), () -> {
                if (vector.metadata().path("expected_kind").asText().equals("invalid_contract")) {
                    assertThrows(ContractViolationException.class, () -> WarcashCodec.evaluate(vector.request()));
                } else {
                    byte[] actual = WarcashCodec.evaluate(vector.request());
                    assertArrayEquals(StrictJson.canonical(vector.expected()), actual);
                    JsonNode parsed = StrictJson.parse(actual);
                    assertArrayEquals(actual, StrictJson.canonical(parsed));
                    assertFalse(parsed.path("formal_action_ready").asBoolean(), "read-only cash never grants an action");
                }
            }));
    }
    @Test
    void realCaptureMetadataHasAllFourOperationsAndNoSkippedOriginalTests() throws IOException {
        Corpus corpus = corpus(); JsonNode header = corpus.header();
        assertEquals("g2.wave2-finance.warcash-golden/v1", header.path("schema").asText());
        assertTrue(header.path("original_tests").intValue() > 0); assertEquals(0, header.path("skips").intValue());
        assertEquals(0, header.path("native_game_rpc_count").intValue()); assertFalse(header.path("live_adoption").booleanValue());
        assertEquals(corpus.vectors().size(), header.path("vector_count").intValue());
        assertFalse(StrictJson.text(header.get("machine_id")).isBlank()); StrictJson.text(header.get("observed_at_utc"));
        Set<String> sourcePaths = new HashSet<>();
        header.path("source_sha256").fieldNames().forEachRemaining(sourcePaths::add);
        assertEquals(Set.of(
            "ck3_autonomous_player/src/xar_autoplayer/m5_war_cash_resource_v1.py",
            "ck3_autonomous_player/src/xar_autoplayer/m5_observed_opportunity_selector.py",
            "ck3_autonomous_player/src/xar_autoplayer/m5_formal_proposal_collector.py",
            "ck3_autonomous_player/src/xar_autoplayer/m5_joint_dispatch.py",
            "ck3_autonomous_player/src/xar_autoplayer/m5_joint_budget_selector.py",
            "ck3_autonomous_player/src/xar_autoplayer/bridge/service.py",
            "ck3_autonomous_player/src/xar_autoplayer/bridge/faction_gift_formal_route_v1.py",
            "ck3_autonomous_player/src/xar_autoplayer/war_mercenary_consumer_v1.py",
            "ck3_autonomous_player/src/xar_autoplayer/bridge/readonly_planning_retry_v1.py",
            "ck3_autonomous_player/src/xar_autoplayer/native_auto_run.py",
            "ck3_autonomous_player/src/xar_autoplayer/ordinary_player_risk_context_v1.py",
            "ck3_autonomous_player/tests/unit/test_m5_war_cash_resource_v1.py",
            "ck3_autonomous_player/tests/unit/test_m5_public_army_zero_claims.py",
            "ck3_autonomous_player/tests/unit/test_m5_observed_opportunity_selector.py",
            "ck3_autonomous_player/tests/unit/test_m5_formal_proposal_collector.py"), sourcePaths);
        header.path("source_sha256").elements().forEachRemaining(value -> assertTrue(value.textValue().matches("[0-9a-f]{64}")));
        Set<String> operations = new HashSet<>(); int ordinal = 0;
        for (Vector vector : corpus.vectors()) {
            assertEquals(++ordinal, vector.metadata().path("ordinal").intValue());
            operations.add(StrictJson.parse(vector.request()).path("operation").asText());
        }
        assertEquals(Set.of("observe_active_war_cash_resource_v1", "require_complete_war_cash_resource_v1",
            "observe_aggregate_active_war_cash_resource_v1", "require_complete_aggregate_war_cash_resource_v1"), operations);
    }
    @Test
    void sourcedZeroAndAbsentAmountRemainDifferentFacts() {
        Frame frame = frame(); BigInteger war = BigInteger.ONE;
        World world = new World(frame, true, true, BigInteger.valueOf(-50), List.of(war));
        Map<Amount, AmountFact> unknown = new EnumMap<>(Amount.class);
        for (Amount key : Amount.values()) { unknown.put(key, new MissingAmount()); }
        SingleReceipt missing = WarcashPolicy.observe(world, new Input(frame, war, unknown, Optional.empty(), Optional.empty(), Optional.empty()));
        assertFalse(missing.complete()); assertTrue(missing.value(Amount.PENDING).isEmpty()); assertTrue(missing.jointReserve().isEmpty());
        Map<Amount, AmountFact> zero = new EnumMap<>(Amount.class);
        for (Amount key : Amount.values()) { zero.put(key, new Measured(new Observation(BigInteger.ZERO, "observed-absence", frame, war, Optional.of(List.of())))); }
        Claims claims = new Claims("observed-occupation", frame, war, List.of(BigInteger.ZERO), List.of(), List.of(), List.of());
        Input input = new Input(frame, war, zero, Optional.of(BigInteger.valueOf(7)), Optional.of(List.of("bounded original observation")), Optional.of(claims));
        AggregateReceipt complete = WarcashPolicy.aggregate(world, List.of(WarcashPolicy.observe(world, input)));
        assertTrue(complete.complete()); assertEquals(BigInteger.ZERO, complete.jointReserve().orElseThrow());
        assertEquals(List.of(BigInteger.ZERO), complete.occupied().orElseThrow().armyIds());
        assertEquals(BigInteger.valueOf(-50), complete.treasuryRaw());
    }
    @Test
    void sharedResourcesCountOnceAndFeeAlternativesStayPerWar() {
        Frame frame = frame(); List<BigInteger> wars = List.of(BigInteger.ONE, BigInteger.TWO);
        World world = new World(frame, true, true, BigInteger.valueOf(10000), wars);
        List<SingleReceipt> rows = new ArrayList<>();
        for (BigInteger war : wars) {
            Map<Amount, AmountFact> amounts = new EnumMap<>(Amount.class);
            for (Amount key : Amount.values()) {
                boolean shared = key != Amount.IMMEDIATE && key != Amount.PENDING;
                Component component = new Component(new ResourceKey("observed-cost", key.wire() + (shared ? "" : war), BigInteger.valueOf(7)),
                    BigInteger.TEN, "actual-resource-observation", frame, shared ? wars : List.of(war));
                amounts.put(key, new Measured(new Observation(BigInteger.TEN, "observed-amount", frame, war, Optional.of(List.of(component)))));
            }
            Claims claims = new Claims("observed-claims", frame, war, List.of(BigInteger.ZERO), List.of(), List.of(), List.of("war:" + war));
            rows.add(WarcashPolicy.observe(world, new Input(frame, war, amounts, Optional.of(BigInteger.valueOf(7)), Optional.of(List.of("bounded")), Optional.of(claims))));
        }
        AggregateReceipt aggregate = WarcashPolicy.aggregate(world, rows);
        assertEquals(BigInteger.valueOf(20), aggregate.values().get(Amount.PENDING).orElseThrow());
        assertEquals(BigInteger.valueOf(20), aggregate.future().orElseThrow());
        assertEquals(BigInteger.valueOf(30), aggregate.jointReserve().orElseThrow());
        JsonNode rendered = WarcashCodec.aggregate(aggregate);
        assertEquals(10, rendered.path("immediate_war_action_costs_raw").path("1").intValue());
        assertEquals(10, rendered.path("immediate_war_action_costs_raw").path("2").intValue());
        assertFalse(rendered.path("formal_action_ready").booleanValue());
        AggregateReceipt partial = WarcashPolicy.aggregate(world, rows.subList(0, 1));
        assertFalse(partial.complete()); assertTrue(partial.future().isEmpty()); assertTrue(partial.occupied().isEmpty());
    }
    @Test
    void typedModelsCannotForgeKnownAmountOrMutateSharedClaims() {
        Frame frame = frame(); BigInteger war = BigInteger.ONE;
        List<BigInteger> mutable = new ArrayList<>(List.of(BigInteger.ZERO));
        Claims claims = new Claims("source", frame, war, mutable, List.of(), List.of(), List.of());
        mutable.add(BigInteger.ONE); assertEquals(List.of(BigInteger.ZERO), claims.armyIds());
        assertThrows(UnsupportedOperationException.class, () -> claims.armyIds().add(BigInteger.TWO));
        assertThrows(IllegalArgumentException.class, () -> new Claims("source", frame, war, List.of(BigInteger.valueOf(-1)), List.of(), List.of(), List.of()));
        assertThrows(IllegalArgumentException.class, () -> new Observation(BigInteger.ONE, "source", frame, war, Optional.of(List.of())));
        assertThrows(IllegalArgumentException.class, () -> new ResourceKey("source", "id", BigInteger.ZERO));
        Map<Amount, AmountFact> facts = new EnumMap<>(Amount.class);
        for (Amount key : Amount.values()) { facts.put(key, new MissingAmount()); }
        Input input = new Input(frame, war, facts, Optional.empty(), Optional.empty(), Optional.empty());
        assertThrows(IllegalArgumentException.class, () -> new SingleReceipt(frame, war, BigInteger.ZERO, input, Map.of()));
    }
    @Test
    void wrongFieldDuplicateAndRawFloatingWarIdAreRejected() throws IOException {
        byte[] original = corpus().vectors().stream().map(Vector::request)
            .filter(raw -> StrictJson.parse(raw).path("operation").asText().equals("observe_active_war_cash_resource_v1"))
            .findFirst().orElseThrow();
        String raw = new String(original, StandardCharsets.UTF_8);
        ObjectNode tree = (ObjectNode) StrictJson.parse(original); tree.put("unexpected", true);
        assertThrows(ContractViolationException.class, () -> WarcashCodec.evaluate(StrictJson.canonical(tree)));
        for (String token : List.of("true", "1.0", "\"1\"")) {
            ObjectNode request = (ObjectNode) StrictJson.parse(original); ObjectNode args = (ObjectNode) request.get("arguments");
            args.remove("war_id"); String body = args.toString();
            String invalidArgs = "{\"war_id\":" + token + (body.length() == 2 ? "}" : "," + body.substring(1));
            String invalid = "{\"schema\":\"" + WarcashCodec.REQUEST_SCHEMA + "\",\"operation\":\"observe_active_war_cash_resource_v1\",\"arguments\":" + invalidArgs + "}";
            assertThrows(ContractViolationException.class, () -> WarcashCodec.evaluate(invalid.getBytes(StandardCharsets.UTF_8)));
        }
        assertThrows(ContractViolationException.class, () -> WarcashCodec.evaluate(("{\"schema\":\"duplicate\"," + raw.substring(1)).getBytes(StandardCharsets.UTF_8)));
        assertThrows(ContractViolationException.class, () -> WarcashCodec.evaluate((raw + "null").getBytes(StandardCharsets.UTF_8)));
    }
    @Test
    void opaqueFrameIntegersAreNotNarrowedToLongOrJavascriptNumber() {
        BigInteger wide = BigInteger.ONE.shiftLeft(80).add(BigInteger.ONE);
        Frame frame = new Frame(BigInteger.valueOf(7), wide, BigInteger.valueOf(3), "opaque-snapshot", wide.add(BigInteger.TWO), "episode");
        Map<Amount, AmountFact> amounts = new EnumMap<>(Amount.class); for (Amount key : Amount.values()) { amounts.put(key, new MissingAmount()); }
        SingleReceipt receipt = WarcashPolicy.observe(new World(frame, true, true, wide.negate(), List.of(BigInteger.ONE)),
            new Input(frame, BigInteger.ONE, amounts, Optional.empty(), Optional.empty(), Optional.empty()));
        JsonNode decoded = StrictJson.parse(StrictJson.canonical(WarcashCodec.single(receipt)));
        assertEquals(wide, decoded.path("source_frame").path("native_revision").bigIntegerValue());
        assertEquals(wide.negate(), decoded.path("observed_treasury_raw").bigIntegerValue());
    }
    private static Frame frame() { return new Frame(BigInteger.valueOf(7), BigInteger.TWO, BigInteger.valueOf(3), "native:2", BigInteger.valueOf(4), "episode"); }
    private static Corpus corpus() throws IOException {
        try (InputStream input = WarcashTest.class.getResourceAsStream("/warcash/original-v1.jsonl.gz")) {
            if (input == null) { throw new AssertionError("committed original producer golden missing; not a skipped pass"); }
            try (GZIPInputStream gzip = new GZIPInputStream(input)) {
                byte[] raw = gzip.readNBytes(8 * 1024 * 1024 + 1); assertTrue(raw.length <= 8 * 1024 * 1024);
                String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
                String[] lines = text.split("\n", -1); assertEquals("", lines[lines.length - 1]); assertEquals(0, (lines.length - 2) % 3);
                ObjectNode header = (ObjectNode) StrictJson.parse(lines[0].getBytes(StandardCharsets.UTF_8)); List<Vector> vectors = new ArrayList<>();
                for (int i = 1; i < lines.length - 1; i += 3) {
                    vectors.add(new Vector((ObjectNode) StrictJson.parse(lines[i].getBytes(StandardCharsets.UTF_8)), lines[i + 1].getBytes(StandardCharsets.UTF_8), StrictJson.parse(lines[i + 2].getBytes(StandardCharsets.UTF_8))));
                }
                return new Corpus(header, List.copyOf(vectors));
            }
        }
    }
}
