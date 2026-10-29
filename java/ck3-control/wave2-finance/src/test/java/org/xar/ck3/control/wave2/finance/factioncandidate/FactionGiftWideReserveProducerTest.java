package org.xar.ck3.control.wave2.finance.factioncandidate;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.InputStream;
import java.math.BigInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.finance.factiongift.FactionGiftPolicy;
import static org.junit.jupiter.api.Assertions.*;

/** Original producer fixture through both real shared parsers, not a mirrored replacement policy. */
final class FactionGiftWideReserveProducerTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    @Test void publicPolicyRangeReachesTheRealCandidateProducerAndItsSharedGiftConsumer() throws Exception {
        JsonNode input = originalSelectedInput();
        for (int digits : new int[]{1500, 4300}) {
            BigInteger magnitude = new BigInteger("9".repeat(digits));
            for (BigInteger reserve : new BigInteger[]{magnitude, magnitude.negate()}) {
                String status = reserve.signum() < 0 ? "unavailable" : "budget_reject";
                String reason = reserve.signum() < 0 ? "enumeration_or_reserve_unproven" : "gold_reserve_not_satisfied";
                var result = FactionCandidateCodec.evaluatePrivateCandidate(
                        JSON.writeValueAsBytes(input.get("snapshot")),
                        FactionCandidateCodec.decodeRootProjection(JSON.writeValueAsBytes(input.get("root"))),
                        JSON.writeValueAsBytes(input.get("private_result")), reserve);
                JsonNode projected = JSON.readTree(FactionCandidateCodec.encodeCandidateResult(result));
                assertEquals(status, projected.get("status").textValue());
                assertEquals(reason, projected.get("reason").textValue());
                ObjectNode direct = JSON.createObjectNode();
                direct.putArray("observations").add(input.path("private_result").path("native").get("observation"));
                direct.put("complete_native_enumeration", true); direct.put("minimum_gold_reserve_raw", reserve);
                var decision = FactionGiftPolicy.choose(JSON.writeValueAsBytes(direct));
                JsonNode shared = JSON.readTree(FactionGiftPolicy.encode(decision));
                assertEquals(status, shared.get("status").textValue()); assertEquals(reason, shared.get("reason").textValue());
                assertEquals(decision, FactionGiftPolicy.decodeChoice(FactionGiftPolicy.encode(decision)));
                assertFalse(projected.get("gift_submission_enabled").booleanValue());
            }
        }
    }
    @Test void aboveOriginal4300DigitBoundaryStillRejectsBeforeASelection() throws Exception {
        JsonNode input = originalSelectedInput(); BigInteger tooWide = BigInteger.TEN.pow(4300);
        assertThrows(IllegalArgumentException.class, () -> FactionCandidateCodec.evaluatePrivateCandidate(
                JSON.writeValueAsBytes(input.get("snapshot")),
                FactionCandidateCodec.decodeRootProjection(JSON.writeValueAsBytes(input.get("root"))),
                JSON.writeValueAsBytes(input.get("private_result")), tooWide));
        ObjectNode direct = JSON.createObjectNode();
        direct.putArray("observations").add(input.path("private_result").path("native").get("observation"));
        direct.put("complete_native_enumeration", true); direct.put("minimum_gold_reserve_raw", tooWide);
        assertThrows(IllegalArgumentException.class, () -> FactionGiftPolicy.choose(JSON.writeValueAsBytes(direct)));
    }
    private static JsonNode originalSelectedInput() throws Exception {
        try (InputStream source = FactionGiftWideReserveProducerTest.class.getResourceAsStream("/factioncandidate/python-golden-v1.json")) {
            assertNotNull(source, "mandatory original faction-candidate producer fixture missing");
            JsonNode document = JSON.readTree(source);
            for (JsonNode row : document.get("cases")) if ("private-native-selected".equals(row.get("name").textValue()))
                return row.get("input");
            throw new IllegalStateException("mandatory original private-native-selected producer vector missing");
        }
    }
}
