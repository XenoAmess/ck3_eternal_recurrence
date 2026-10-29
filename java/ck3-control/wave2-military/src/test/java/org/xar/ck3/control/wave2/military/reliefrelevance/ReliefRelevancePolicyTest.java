package org.xar.ck3.control.wave2.military.reliefrelevance;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegePolicy;
import org.xar.ck3.control.wave2.military.reliefrelevance.ReliefRelevancePolicy.Request;
import org.xar.ck3.control.wave2.military.reliefrelevance.ReliefRelevancePolicy.WarObjectives;

final class ReliefRelevancePolicyTest {
    private static JsonNode golden() throws IOException {
        try (InputStream input = ReliefRelevancePolicyTest.class.getResourceAsStream("/reliefrelevance/original-producer-golden-v1.json")) {
            assertNotNull(input, "real original consumer-function fixture required; absence is RED");
            return StrictJson.parse(input.readNBytes(71_681), 71_680);
        }
    }
    private static ObjectNode base(JsonNode fixture, String name) {
        for (JsonNode row : fixture.get("bases")) {
            if (row.get("name").textValue().equals(name)) { return row.get("request").deepCopy(); }
        }
        throw new IllegalStateException("frozen base missing: " + name);
    }
    private static ObjectNode base(String name) throws IOException { return base(golden(), name); }
    private static ObjectNode apply(JsonNode fixture, JsonNode vector) {
        ObjectNode request = base(fixture, vector.get("base").textValue());
        for (JsonNode operation : vector.get("patches")) {
            JsonNode path = operation.get("path"), parent = request;
            assertTrue(path.isArray() && !path.isEmpty());
            for (int index = 0; index < path.size() - 1; index++) {
                String key = path.get(index).textValue(); parent = parent.isArray() ? parent.get(Integer.parseInt(key)) : parent.get(key);
                assertNotNull(parent, "frozen local test path required");
            }
            String key = path.get(path.size() - 1).textValue(), kind = operation.get("operation").textValue();
            if (parent instanceof ObjectNode object) {
                if (kind.equals("remove")) { object.remove(key); }
                else { assertEquals("set", kind); object.set(key, operation.get("value").deepCopy()); }
            } else if (parent instanceof ArrayNode array) {
                if (kind.equals("remove")) { array.remove(Integer.parseInt(key)); }
                else { assertEquals("set", kind); array.set(Integer.parseInt(key), operation.get("value").deepCopy()); }
            } else { throw new IllegalArgumentException("frozen test patch needs a local container"); }
        }
        return request;
    }

    @TestFactory
    Stream<DynamicTest> originalActualConsumerFunctionAndObjectiveDependency() throws IOException {
        JsonNode fixture = golden(); assertFalse(fixture.get("actual_live_qualification").booleanValue());
        assertEquals(32, fixture.get("cases").size()); assertEquals(2, fixture.get("original_ast_extracts").size());
        List<DynamicTest> tests = new ArrayList<>();
        for (JsonNode vector : fixture.get("cases")) {
            tests.add(DynamicTest.dynamicTest(vector.get("name").textValue(), () -> {
                byte[] raw = StrictJson.canonical(apply(fixture, vector)); Request request = ReliefRelevanceCodec.decode(raw);
                assertEquals(vector.get("expected"), StrictJson.parse(ReliefRelevanceCodec.evaluate(raw)));
                Request roundTrip = ReliefRelevanceCodec.decode(ReliefRelevanceCodec.encodeRequest(request));
                assertEquals(request, roundTrip); assertEquals(ReliefRelevancePolicy.assess(request), ReliefRelevancePolicy.assess(roundTrip));
                if (Boolean.FALSE.equals(request.realmFrame().candidateWar().playerIsPrimaryWarLeader())) {
                    assertEquals(RealmSiegePolicy.qualifies(request.realmFrame().snapshot(), request.realmFrame().candidateWar(), request.realmFrame().candidateEnemy()),
                            ReliefRelevancePolicy.assess(request).candidateSiegeReliefRelevant());
                }
            }));
        }
        return tests.stream();
    }

    @Test
    void objectiveDependencyKeepsExactIntegerDomainAndFirstOccurrenceOrder() {
        BigInteger huge = BigInteger.ONE.shiftLeft(80);
        List<BigInteger> values = ReliefRelevancePolicy.warObjectiveProvinceIds(List.of(
                new WarObjectives(List.of(BigInteger.valueOf(3), BigInteger.ZERO, BigInteger.valueOf(3), BigInteger.valueOf(-1))),
                new WarObjectives(null), new WarObjectives(List.of(BigInteger.ZERO, huge, BigInteger.valueOf(2)))));
        assertEquals(List.of(BigInteger.valueOf(3), BigInteger.ZERO, BigInteger.valueOf(-1), huge, BigInteger.valueOf(2)), values);
    }

    @Test
    void primaryFactualTieDoesNotUpgradeTheNativeFrameQualification() throws IOException {
        ObjectNode input = base("actual"); ObjectNode snapshot = (ObjectNode) input.get("frame").get("snapshot");
        ObjectNode war = (ObjectNode) snapshot.get("active_wars").get(0); ObjectNode enemy = (ObjectNode) war.get("enemy_armies").get(0);
        war.put("player_is_primary_war_leader", true); war.putArray("war_objective_province_ids").add(enemy.get("current_province_id").bigIntegerValue());
        snapshot.put("source", "unknown"); Request request = ReliefRelevanceCodec.decode(StrictJson.canonical(input));
        assertTrue(ReliefRelevancePolicy.assess(request).candidateSiegeReliefRelevant());
        assertFalse(RealmSiegePolicy.qualifies(request.realmFrame().snapshot(), request.realmFrame().candidateWar(), request.realmFrame().candidateEnemy()));
    }

    @Test
    void candidateFactsCannotConflictWithTheSelectedActiveWarNode() throws IOException {
        Request request = ReliefRelevanceCodec.decode(StrictJson.canonical(base("actual")));
        assertThrows(IllegalArgumentException.class, () -> new Request(request.realmFrame(), List.of(BigInteger.valueOf(-999)),
                request.candidateEnemySiegeProvinceHolderCharacterId(), request.activeWarObjectivesInStoredOrder()));
        assertThrows(IllegalArgumentException.class, () -> new Request(request.realmFrame(), request.candidateWarObjectiveProvinceIds(),
                request.candidateEnemySiegeProvinceHolderCharacterId(), List.of()));
    }

    @Test
    void objectiveAndHolderWrongRawTokensReachTheActualDecoder() throws IOException {
        ObjectNode input = base("actual"); ObjectNode war = (ObjectNode) input.get("frame").get("snapshot").get("active_wars").get(0);
        war.putArray("war_objective_province_ids").add(123);
        ((ObjectNode) war.get("enemy_armies").get(0)).put("siege_province_holder_character_id", 29829);
        String canonical = new String(StrictJson.canonical(input), StandardCharsets.UTF_8);
        for (String replacement : List.of("123.0", "true", "\"123\"", "null")) {
            String raw = canonical.replace("\"war_objective_province_ids\":[123]", "\"war_objective_province_ids\":[" + replacement + "]");
            assertFalse(raw.equals(canonical));
            assertThrows(IllegalArgumentException.class, () -> ReliefRelevanceCodec.decode(raw.getBytes(StandardCharsets.UTF_8)));
        }
        for (String replacement : List.of("29829.0", "true", "\"29829\"")) {
            String raw = canonical.replace("\"siege_province_holder_character_id\":29829", "\"siege_province_holder_character_id\":" + replacement);
            assertFalse(raw.equals(canonical));
            assertThrows(IllegalArgumentException.class, () -> ReliefRelevanceCodec.decode(raw.getBytes(StandardCharsets.UTF_8)));
        }
    }

    @Test
    void extraSdkFieldsAreProjectedAndOuterWrapperIsStrict() throws IOException {
        String rawExtension = new String(StrictJson.canonical(base("nonleading")), StandardCharsets.UTF_8)
                .replace("\"snapshot\":{", "\"snapshot\":{\"future_sdk_fraction\":1.0,");
        assertTrue(ReliefRelevancePolicy.assess(ReliefRelevanceCodec.decode(rawExtension.getBytes(StandardCharsets.UTF_8))).candidateSiegeReliefRelevant());
        ObjectNode extra = base("actual"); extra.put("native_qualified", true);
        assertThrows(IllegalArgumentException.class, () -> ReliefRelevanceCodec.decode(StrictJson.canonical(extra)));
        ObjectNode missing = base("actual"); missing.remove("frame");
        assertThrows(IllegalArgumentException.class, () -> ReliefRelevanceCodec.decode(StrictJson.canonical(missing)));
        assertThrows(IllegalArgumentException.class, () -> ReliefRelevanceCodec.decode("{\"schema\":1,\"schema\":1}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> ReliefRelevanceCodec.decode(new byte[] {(byte) 0xc3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> ReliefRelevanceCodec.decode(new byte[65_537]));
    }
}
