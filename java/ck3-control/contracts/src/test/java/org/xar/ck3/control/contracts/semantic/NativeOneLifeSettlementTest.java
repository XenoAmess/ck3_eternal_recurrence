package org.xar.ck3.control.contracts.semantic;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.MissingNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;

/** DATA contract tests; no episode eligibility, writer, native/Game or persistence authority. */
final class NativeOneLifeSettlementTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final int LEASE = 1 << 20;

    @Test void absentNullAndPendingRemainDifferentFromMalformedReady() {
        assertTrue(NativeOneLifeSettlement.normalize(MissingNode.getInstance()).isNull());
        assertTrue(NativeOneLifeSettlement.normalize(NullNode.instance).isNull());
        assertThrows(NullPointerException.class, () -> NativeOneLifeSettlement.normalize(null));
        for (JsonNode flag : List.of(JSON.getNodeFactory().booleanNode(false), JSON.getNodeFactory().numberNode(0))) {
            ObjectNode raw = JSON.createObjectNode().set("ready", flag);
            raw.putObject("ignored").put("malformed", true);
            var normalized = (ObjectNode) NativeOneLifeSettlement.normalize(raw);
            assertEquals(2, normalized.size()); assertTrue(normalized.get("commit_serial").isNull());
            assertEquals(new NativeOneLifeSettlement.Pending(java.util.Optional.empty()), NativeOneLifeSettlement.decodeNormalized(normalized));
            raw.put("commit_serial", new BigInteger("18446744073709551616"));
            assertEquals(raw.get("commit_serial"), NativeOneLifeSettlement.normalize(raw).get("commit_serial"));
            raw.put("commit_serial", 1.0);
            assertThrows(IllegalArgumentException.class, () -> NativeOneLifeSettlement.normalize(raw));
        }
        assertThrows(IllegalArgumentException.class, () -> NativeOneLifeSettlement.decodeNormalized(MissingNode.getInstance()));
    }

    @Test void normalizedSerdePreservesRatioIntegralFloatAndNegativeZero() throws Exception {
        var raw = ready(); raw.set("final_score", fixed(BigInteger.ONE.shiftLeft(53).add(BigInteger.ONE), BigInteger.ONE.shiftLeft(53)));
        raw.set("score_before_reject", fixed(BigInteger.ONE.negate(), BigInteger.ONE.shiftLeft(1075)));
        var state = NativeOneLifeSettlement.decodeNative(raw);
        byte[] wire = NativeOneLifeSettlement.encode(state, LEASE);
        String text = new String(wire, StandardCharsets.UTF_8);
        assertTrue(text.contains("\"final_score\":1.0")); assertTrue(text.contains("\"score_before_reject\":-0.0"));
        var restored = NativeOneLifeSettlement.decodeNormalized(wire, LEASE);
        assertEquals(state, restored);
        var normalized = NativeOneLifeSettlement.encode(restored);
        assertTrue(normalized.get("final_score").isFloatingPointNumber());
        assertEquals(Long.MIN_VALUE, Double.doubleToRawLongBits(normalized.get("score_before_reject").doubleValue()));
        // This source distinction is why normalized SEM must never be sent to decodeNative a second time.
        assertTrue(NativeOneLifeSettlement.normalize(normalized).get("final_score").isIntegralNumber());
        assertThrows(IllegalArgumentException.class, () -> NativeOneLifeSettlement.decodeNormalized(wire, wire.length - 1));
        assertThrows(IllegalArgumentException.class, () -> NativeOneLifeSettlement.encode(state, 1));
        assertThrows(IllegalArgumentException.class, () -> NativeOneLifeSettlement.decodeNormalized((text + " null").getBytes(StandardCharsets.UTF_8), LEASE));
        assertThrows(IllegalArgumentException.class, () -> NativeOneLifeSettlement.decodeNormalized(text.replace("\"ready\":true", "\"ready\":true,\"ready\":true").getBytes(StandardCharsets.UTF_8), LEASE));
    }

    @Test void strictNormalizedSchemaRejectsLegacyFlagsMissingNullAndWrongNumericKinds() {
        var normalized = (ObjectNode) NativeOneLifeSettlement.normalize(ready());
        for (String field : List.of("ready", "commit_serial", "source_character_id", "final_score", "score_before_reject", "record_candidate",
                "old_record", "record_delta", "blessing_count", "refusal_count", "contract_progress", "record_written")) {
            var missing = normalized.deepCopy(); missing.remove(field);
            assertThrows(IllegalArgumentException.class, () -> NativeOneLifeSettlement.decodeNormalized(missing), field);
            var nil = normalized.deepCopy(); nil.putNull(field);
            assertThrows(IllegalArgumentException.class, () -> NativeOneLifeSettlement.decodeNormalized(nil), field);
        }
        for (String field : List.of("ready", "record_written")) {
            var integerFlag = normalized.deepCopy(); integerFlag.put(field, 1);
            assertThrows(IllegalArgumentException.class, () -> NativeOneLifeSettlement.decodeNormalized(integerFlag));
        }
        var extra = normalized.deepCopy().put("extra", 1);
        assertThrows(IllegalArgumentException.class, () -> NativeOneLifeSettlement.decodeNormalized(extra));
        var badScore = normalized.deepCopy(); badScore.set("final_score", fixed(BigInteger.ONE, BigInteger.TWO));
        assertThrows(IllegalArgumentException.class, () -> NativeOneLifeSettlement.decodeNormalized(badScore));
        badScore.put("final_score", Double.NaN);
        assertThrows(IllegalArgumentException.class, () -> NativeOneLifeSettlement.decodeNormalized(badScore));
    }

    @Test void rawIntegerFlagsAndFixedFieldsHaveExactRuntimeTypesAndRecordConsistency() {
        var legacy = ready().put("ready", 1).put("record_written", 1); legacy.put("ignored", "original outer compatibility");
        assertInstanceOf(NativeOneLifeSettlement.Ready.class, NativeOneLifeSettlement.decodeNative(legacy));
        for (String field : List.of("commit_serial", "source_character_id", "record_candidate", "old_record", "record_delta", "blessing_count", "refusal_count", "contract_progress")) {
            for (JsonNode wrong : List.of(JSON.getNodeFactory().booleanNode(true), JSON.getNodeFactory().numberNode(1.0), JSON.getNodeFactory().textNode("1"))) {
                var bad = ready(); bad.set(field, wrong);
                assertThrows(IllegalArgumentException.class, () -> NativeOneLifeSettlement.decodeNative(bad), field);
            }
        }
        for (String flag : List.of("ready", "record_written")) {
            var bad = ready().put(flag, 1.0);
            assertThrows(IllegalArgumentException.class, () -> NativeOneLifeSettlement.decodeNative(bad));
        }
        var delta = ready().put("record_delta", 0);
        assertThrows(IllegalArgumentException.class, () -> NativeOneLifeSettlement.decodeNative(delta));
        var written = ready().put("record_candidate", 5).put("old_record", 5).put("record_delta", 0);
        assertThrows(IllegalArgumentException.class, () -> NativeOneLifeSettlement.decodeNative(written));
        assertInstanceOf(NativeOneLifeSettlement.Ready.class, NativeOneLifeSettlement.decodeNative(written.put("record_written", false)));
        var score = fixed(BigInteger.ONE, BigInteger.ONE).put("extra", 1);
        assertThrows(IllegalArgumentException.class, () -> NativeOneLifeSettlement.normalizeScore(score, "score"));
        assertThrows(IllegalArgumentException.class, () -> NativeOneLifeSettlement.normalizeScore(fixed(BigInteger.ONE, BigInteger.ZERO), "score"));
        score.remove("extra"); score.put("raw", true);
        assertThrows(IllegalArgumentException.class, () -> NativeOneLifeSettlement.normalizeScore(score, "score"));
    }

    @Test void originalExactRatioCanExceedScalarFloatRangeAndRoundTripPastGenericJsonCap() {
        BigInteger enormous = BigInteger.TEN.pow(400);
        var raw = ready(); raw.set("final_score", fixed(enormous, BigInteger.ONE));
        var normalized = NativeOneLifeSettlement.normalize(raw);
        assertEquals(enormous, normalized.get("final_score").bigIntegerValue());
        raw.put("final_score", enormous);
        assertThrows(IllegalArgumentException.class, () -> NativeOneLifeSettlement.normalize(raw));
        // A legal unbounded original exact quotient exercises the dedicated lease, without raising generic StrictJson's cap.
        BigInteger huge = BigInteger.ONE.shiftLeft(3_500_000);
        var state = new NativeOneLifeSettlement.Ready(BigInteger.ONE, new NativeOneLifeSettlement.Integral(huge),
                new NativeOneLifeSettlement.Integral(BigInteger.ZERO), BigInteger.ONE, BigInteger.ZERO, BigInteger.ONE,
                BigInteger.ZERO, BigInteger.ZERO, BigInteger.ZERO, true);
        byte[] wire = NativeOneLifeSettlement.encode(state, 2 << 20);
        assertTrue(wire.length > 1 << 20);
        assertEquals(state, NativeOneLifeSettlement.decodeNormalized(wire, 2 << 20));
        assertThrows(IllegalArgumentException.class, () -> NativeOneLifeSettlement.decodeNormalized(wire, 1 << 20));
    }

    private static ObjectNode fixed(BigInteger raw, BigInteger scale) { return JSON.createObjectNode().put("raw", raw).put("scale", scale); }
    private static ObjectNode ready() {
        return JSON.createObjectNode().put("ready", true).put("commit_serial", 1).put("source_character_id", 73)
                .put("final_score", 5).put("score_before_reject", 6).put("record_candidate", 5).put("old_record", 4).put("record_delta", 1)
                .put("blessing_count", 0).put("refusal_count", 0).put("contract_progress", 0).put("record_written", true);
    }
}
