package org.xar.ck3.control.application.planning.finance.publicgift;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.finance.publicgift.FactionGiftPublicContract.*;

/** Original MCP argument shapes; software serde checks grant no native/ledger authority. */
final class FactionGiftPublicCodecTest {
    private static RawJson raw(String json) { return new RawJson(json.getBytes(StandardCharsets.UTF_8)); }
    @Test void originalCandidateDefaultAndNegativeReserveKeepTheirDistinctDomainInputs() {
        var omitted = (CandidateQuery) FactionGiftPublicCodec.decode(Method.CANDIDATE,
                raw("{\"expected_revision\":56,\"same_frame_root\":{}}"));
        assertEquals(DEFAULT_RESERVE, omitted.minimumGoldReserveRaw());
        var negative = (CandidateQuery) FactionGiftPublicCodec.decode(Method.CANDIDATE,
                raw("{\"expected_revision\":\"56\",\"same_frame_root\":{},\"minimum_gold_reserve_raw\":\"-1\"}"));
        assertEquals(BigInteger.ONE.negate(), negative.minimumGoldReserveRaw());
        BigInteger unbounded = BigInteger.ONE.shiftLeft(200);
        var large = new CandidateQuery(BigInteger.valueOf(56), new RootProjection(raw("{}")), unbounded);
        assertEquals(large, FactionGiftPublicCodec.decode(large.method(), FactionGiftPublicCodec.encode(large)));
        var maximumNegative = new CandidateQuery(BigInteger.ONE, new RootProjection(raw("{}")),
                new BigInteger("9".repeat(MAX_RESERVE_DIGITS)).negate());
        assertEquals(maximumNegative, FactionGiftPublicCodec.decode(Method.CANDIDATE, FactionGiftPublicCodec.encode(maximumNegative)));
        assertThrows(IllegalArgumentException.class, () -> new CandidateQuery(BigInteger.ONE,
                new RootProjection(raw("{}")), BigInteger.TEN.pow(MAX_RESERVE_DIGITS)));
    }
    @Test void theFiveOriginalSelectorsRoundTripWithoutAnInventedWireOperationOrPolicySelector() {
        List<Request> requests = List.of(
                new CandidateQuery(new BigInteger("18446744073709551615"), new RootProjection(raw("{}")), DEFAULT_RESERVE),
                new Send(BigInteger.valueOf(56), new NativeCandidate(raw("{}")), new Checkpoint(raw("{}"))),
                new ReceiptQuery(BigInteger.valueOf(56), new Pending(raw("{}"))),
                new ColdRecoveryQuery(BigInteger.valueOf(56), new Pending(raw("{}"))),
                new ResolvedQuery(BigInteger.valueOf(56), "faction-gift-original-request"));
        assertEquals(5, java.util.Arrays.stream(Method.values()).map(Method::originalName).distinct().count());
        for (Request request : requests) {
            RawJson encoded = FactionGiftPublicCodec.encode(request);
            assertEquals(request, FactionGiftPublicCodec.decode(request.method(), encoded));
            var fields = StrictJson.parse(encoded.bytes(), MAX_ARGUMENT_BYTES);
            assertTrue(fields.get("expected_revision").isTextual());
            assertFalse(fields.has("operation")); assertFalse(fields.has("contract_id"));
        }
    }
    @Test void missingNullBoolFloatUnsafeNumericAndUnknownFieldsNeverReachTheDomainProducer() {
        for (String input : List.of("{}", "{\"expected_revision\":null,\"same_frame_root\":{}}",
                "{\"expected_revision\":true,\"same_frame_root\":{}}", "{\"expected_revision\":56.0,\"same_frame_root\":{}}",
                "{\"expected_revision\":9007199254740992,\"same_frame_root\":{}}", "{\"expected_revision\":\"056\",\"same_frame_root\":{}}",
                "{\"expected_revision\":56,\"same_frame_root\":null}", "{\"expected_revision\":56,\"same_frame_root\":[]}",
                "{\"expected_revision\":56,\"same_frame_root\":{},\"minimum_gold_reserve_raw\":null}",
                "{\"expected_revision\":56,\"same_frame_root\":{},\"minimum_gold_reserve_raw\":true}",
                "{\"expected_revision\":56,\"same_frame_root\":{},\"minimum_gold_reserve_raw\":1.0}",
                "{\"expected_revision\":56,\"same_frame_root\":{},\"minimum_gold_reserve_raw\":\"-0\"}",
                "{\"expected_revision\":56,\"same_frame_root\":{},\"minimum_gold_reserve_raw\":9007199254740992}",
                "{\"expected_revision\":56,\"same_frame_root\":{},\"skip_checkpoint\":true}"))
            assertThrows(IllegalArgumentException.class, () -> FactionGiftPublicCodec.decode(Method.CANDIDATE, raw(input)));
        for (Method method : List.of(Method.RECEIPT, Method.COLD_RECOVERY))
            for (String input : List.of("{\"expected_revision\":56}", "{\"expected_revision\":56,\"pending\":null}",
                    "{\"expected_revision\":56,\"pending\":true}", "{\"expected_revision\":56,\"pending\":{},\"candidate\":{}}"))
                assertThrows(IllegalArgumentException.class, () -> FactionGiftPublicCodec.decode(method, raw(input)));
        for (String input : List.of("{\"expected_revision\":56,\"request_id\":null}", "{\"expected_revision\":56,\"request_id\":1}",
                "{\"expected_revision\":56,\"request_id\":\"\"}"))
            assertThrows(IllegalArgumentException.class, () -> FactionGiftPublicCodec.decode(Method.RESOLVED, raw(input)));
    }
}
