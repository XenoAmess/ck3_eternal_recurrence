package org.xar.ck3.control.wave2.planning.reinforcementcount;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.planning.reinforcementcount.ReinforcementCounts.*;

final class ReinforcementCountsTest {
    private static final ObjectMapper JSON = new ObjectMapper();

    @Test
    void realOldHelpersMatchAllCapturedCasesAndCountsRoundtrip() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.reinforcement-count.golden.v1", golden.get("schema").textValue());
        assertEquals(0, golden.get("producer_exit_code").intValue());
        assertFalse(golden.get("machine_id").textValue().isBlank());
        assertEquals("d9f32c208fa47a0b2007f4a5194462a9929fac2f636c8e58ba25a8cffb1a089c",
                golden.path("producer_ref").path("sha256").textValue());
        int cases = 0;
        for (JsonNode sample : golden.get("cases")) {
            byte[] wire = bytes(sample.get("request_json").textValue());
            if ("count".equals(sample.get("operation").textValue())) {
                Optional<BigInteger> result = count(ReinforcementCountsCodec.decodeCount(wire));
                JsonNode expected = sample.get("expected_result");
                assertEquals(expected.isNull() ? Optional.empty() : Optional.of(expected.bigIntegerValue()), result,
                        sample.get("name").textValue());
                assertEquals(result, ReinforcementCountsCodec.decodeCountResult(ReinforcementCountsCodec.encodeCount(result)));
            } else {
                assertEquals(sample.get("expected_result").booleanValue(),
                        stationaryStaging(ReinforcementCountsCodec.decodeStaging(wire)), sample.get("name").textValue());
            }
            cases++;
        }
        assertEquals(28, cases);
    }

    @Test
    void duplicateArmiesCountOnceAndConflictingCountsRemainUnknown() {
        CountInput same = noCache(List.of(army(1, 800), army(1, 800)));
        assertEquals(Optional.of(BigInteger.valueOf(800)), count(same));
        assertTrue(count(noCache(List.of(army(1, 800), army(1, 801)))).isEmpty());
        assertEquals(Optional.of(BigInteger.valueOf(1_500)), count(noCache(List.of(army(1, 800), army(2, 700)))));
    }

    @Test
    void explicitlyEmptyCollectionIsZeroAndUnknownObservationIsNeverZero() {
        assertEquals(Optional.of(BigInteger.ZERO), count(noCache(List.of())));
        assertTrue(count(noCache(List.of(new Army(Optional.of(BigInteger.ONE), Optional.empty())))).isEmpty());
        Army missingIdentity = new Army(Optional.empty(), Optional.of(BigInteger.ZERO));
        assertTrue(count(noCache(List.of(missingIdentity))).isEmpty());
        assertTrue(count(noCache(List.of(army(1, -1)))).isEmpty());
    }

    @Test
    void cacheRequiresCurrentBindingAndUniqueMatchingRoleAndWarScope() throws IOException {
        ObjectNode request = countRequest();
        assertEquals(Optional.of(BigInteger.valueOf(900)), count(decodeCount(request)));
        for (String field : new String[]{"army_strengths_queried_snapshot_id", "army_strengths_queried_revision"}) {
            ObjectNode stale = request.deepCopy();
            ((ObjectNode) stale.get("snapshot")).remove(field);
            assertEquals(Optional.of(BigInteger.valueOf(800)), count(decodeCount(stale)));
        }
        ObjectNode wrongRole = request.deepCopy(); wrongRole.put("role", "active_war_enemy");
        assertEquals(Optional.of(BigInteger.valueOf(800)), count(decodeCount(wrongRole)));
        ObjectNode wrongWar = request.deepCopy(); wrongWar.put("war_id", 100);
        assertEquals(Optional.of(BigInteger.valueOf(800)), count(decodeCount(wrongWar)));
        ObjectNode correctWar = request.deepCopy(); correctWar.put("war_id", 99);
        assertEquals(Optional.of(BigInteger.valueOf(900)), count(decodeCount(correctWar)));
    }

    @Test
    void exactIdentityAndCountTokensRejectBoolFloatStringWithoutRounding() throws IOException {
        String baseline = golden().get("cases").get(0).get("request_json").textValue();
        for (String token : new String[]{"true", "800.0", "\"800\""}) {
            byte[] raw = bytes(baseline.replace("\"soldiers\":800", "\"soldiers\":" + token));
            assertThrows(IllegalArgumentException.class, () -> ReinforcementCountsCodec.decodeCount(raw));
        }
        for (String token : new String[]{"true", "1.0", "\"1\""}) {
            byte[] raw = bytes(baseline.replace("\"army_id\":1", "\"army_id\":" + token));
            assertThrows(IllegalArgumentException.class, () -> ReinforcementCountsCodec.decodeCount(raw));
        }
    }

    @Test
    void stationaryPredicatePreservesMissingNullEmptyAndExactFalseGuards() throws IOException {
        ObjectNode request = stagingRequest();
        assertTrue(stationaryStaging(decodeStaging(request)));
        for (String field : new String[]{"route_province_ids", "in_combat", "retreating", "controllable"}) {
            ObjectNode missing = request.deepCopy(); ((ObjectNode) missing.get("row")).remove(field);
            assertFalse(stationaryStaging(decodeStaging(missing)));
        }
        ObjectNode nil = request.deepCopy(); ((ObjectNode) nil.get("row")).putNull("route_province_ids");
        assertFalse(stationaryStaging(decodeStaging(nil)));
        ObjectNode bad = request.deepCopy(); ((ObjectNode) bad.get("row")).put("in_combat", 0);
        byte[] raw = JSON.writeValueAsBytes(bad);
        assertThrows(IllegalArgumentException.class, () -> ReinforcementCountsCodec.decodeStaging(raw));
    }

    @Test
    void extensibleSnapshotAndArmyRowsAreProjectedButRequestSchemaIsExact() throws IOException {
        ObjectNode request = countRequest();
        ((ObjectNode) request.get("snapshot")).putObject("future_native_extension").put("x", 1);
        ((ObjectNode) request.path("rows").get(0)).put("future_army_extension", true);
        assertEquals(Optional.of(BigInteger.valueOf(900)), count(decodeCount(request)));
        ObjectNode extra = request.deepCopy(); extra.put("cache_ready_green", true);
        byte[] raw = JSON.writeValueAsBytes(extra);
        assertThrows(IllegalArgumentException.class, () -> ReinforcementCountsCodec.decodeCount(raw));
        for (String field : new String[]{"schema", "rows", "snapshot", "role", "war_id"}) {
            ObjectNode missing = request.deepCopy(); missing.remove(field);
            byte[] invalid = JSON.writeValueAsBytes(missing);
            assertThrows(IllegalArgumentException.class, () -> ReinforcementCountsCodec.decodeCount(invalid));
        }
    }

    @Test
    void boundaryRejectsDuplicatesInvalidUtf8OversizeAndMalformedCountResult() {
        assertThrows(IllegalArgumentException.class, () -> ReinforcementCountsCodec.decodeCount(bytes("{\"schema\":1,\"schema\":2}")));
        assertThrows(IllegalArgumentException.class, () -> ReinforcementCountsCodec.decodeCount(new byte[]{(byte) 0xc3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> ReinforcementCountsCodec.decodeCount(new byte[65_537]));
        for (String result : new String[]{"{}", "{\"count\":true}", "{\"count\":1.0}", "{\"count\":-1}", "{\"count\":0,\"ready\":true}"}) {
            assertThrows(IllegalArgumentException.class, () -> ReinforcementCountsCodec.decodeCountResult(bytes(result)));
        }
        assertThrows(IllegalArgumentException.class, () -> ReinforcementCountsCodec.encodeCount(Optional.of(BigInteger.ONE.negate())));
    }

    @Test
    void largeCountsAreExactAndInputCollectionsAreDefensivelyCopied() {
        BigInteger huge = BigInteger.ONE.shiftLeft(100);
        CountInput input = noCache(List.of(new Army(Optional.of(huge), Optional.of(huge)), army(1, 1)));
        assertEquals(Optional.of(huge.add(BigInteger.ONE)), count(input));
        assertThrows(UnsupportedOperationException.class, () -> input.rows().clear());
        assertThrows(UnsupportedOperationException.class, () -> input.strengths().clear());
        assertEquals(count(input), ReinforcementCountsCodec.decodeCountResult(ReinforcementCountsCodec.encodeCount(count(input))));
    }

    private static Army army(long identity, long number) {
        return new Army(Optional.of(BigInteger.valueOf(identity)), Optional.of(BigInteger.valueOf(number)));
    }
    private static CountInput noCache(List<Army> rows) {
        return new CountInput(rows, "frame", BigInteger.ONE, CacheStatus.OTHER, Optional.empty(), Optional.empty(),
                List.of(), "player", Optional.empty());
    }
    private static JsonNode golden() throws IOException {
        try (InputStream stream = ReinforcementCountsTest.class.getResourceAsStream("/reinforcementcount/golden.json")) {
            if (stream == null) { throw new IllegalStateException("real helper golden missing; capture not executed"); }
            return JSON.readTree(stream);
        }
    }
    private static ObjectNode countRequest() throws IOException {
        return (ObjectNode) JSON.readTree(golden().get("cases").get(0).get("request_json").textValue());
    }
    private static ObjectNode stagingRequest() throws IOException {
        for (JsonNode sample : golden().get("cases")) {
            if ("ordinary-stationary-staging".equals(sample.get("name").textValue())) {
                return (ObjectNode) JSON.readTree(sample.get("request_json").textValue());
            }
        }
        throw new IllegalStateException("staging golden case absent");
    }
    private static CountInput decodeCount(ObjectNode request) throws IOException { return ReinforcementCountsCodec.decodeCount(JSON.writeValueAsBytes(request)); }
    private static StagingInput decodeStaging(ObjectNode request) throws IOException { return ReinforcementCountsCodec.decodeStaging(JSON.writeValueAsBytes(request)); }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
}
