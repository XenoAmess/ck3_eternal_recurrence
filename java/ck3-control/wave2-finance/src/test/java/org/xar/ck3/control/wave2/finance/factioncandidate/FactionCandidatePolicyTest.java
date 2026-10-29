package org.xar.ck3.control.wave2.finance.factioncandidate;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.finance.factiongift.FactionGiftChoice;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;

import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidatePolicy.*;

final class FactionCandidatePolicyTest {
    private static final ObjectMapper JSON = new ObjectMapper();

    @TestFactory
    List<DynamicTest> originalProducerToSharedJavaGiftPolicyAndLegacyWire() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.ck3.java.faction-candidate-producer-golden/v1", golden.path("schema").textValue());
        assertEquals(2, golden.path("original_zero_argument_tests_executed").size());
        assertEquals(0, golden.path("capture").path("native_rpc_count").intValue());
        assertTrue(golden.path("cases").size() >= 45);
        List<DynamicTest> tests = new ArrayList<>();
        for (JsonNode vector : golden.path("cases")) {
            tests.add(DynamicTest.dynamicTest(vector.path("name").textValue(), () -> {
                byte[] input = JSON.writeValueAsBytes(vector.path("input"));
                JsonNode actual = evaluate(vector.path("operation").textValue(), input);
                assertEquals(vector.path("expected"), actual);
                assertEquals(actual, evaluate(vector.path("operation").textValue(), JSON.writeValueAsBytes(JSON.readTree(input))));
                if (actual.path("status").asText().equals("selected")) {
                    assertFalse(actual.path("gift_submission_enabled").booleanValue());
                    assertFalse(actual.path("public_capability_advertised").booleanValue());
                }
            }));
        }
        return List.copyOf(tests);
    }

    @Test
    void rawFloatingPointAndBooleanTokensCannotQualifyFramesOrReceiverZero() throws IOException {
        String root = JSON.writeValueAsString(vectorInput("latest-root-targeting-present"));
        RootView floatFrame = latestSameFrameRoot(FactionCandidateCodec.decodeRootSearch(utf8(
                root.replace("\"native_revision\":412", "\"native_revision\":412.0"))));
        assertEquals(RootStatus.FRAME_UNAVAILABLE, floatFrame.status());
        RootView boolCount = latestSameFrameRoot(FactionCandidateCodec.decodeRootSearch(utf8(
                root.replace("\"player_targeting_faction_count\":1", "\"player_targeting_faction_count\":true"))));
        assertEquals(RootStatus.ROOT_FACTION_FACTS_UNKNOWN, boolCount.status());
        String candidate = JSON.writeValueAsString(vectorInput("private-native-selected"));
        CandidateResult floatZero = choosePrivateCandidate(FactionCandidateCodec.decodeCandidateInput(utf8(
                candidate.replace("\"failure_flags\":0", "\"failure_flags\":0.0"))), FactionCandidateCodec.existingJavaGiftDecision());
        assertEquals(RejectionReason.NATIVE_PREVIEW_RECEIVER_RED, assertInstanceOf(Rejected.class, floatZero).reason());
        CandidateResult falseZero = choosePrivateCandidate(FactionCandidateCodec.decodeCandidateInput(utf8(
                candidate.replace("\"failure_flags\":0", "\"failure_flags\":false"))), FactionCandidateCodec.existingJavaGiftDecision());
        assertEquals(RejectionReason.NATIVE_PREVIEW_RECEIVER_RED, assertInstanceOf(Rejected.class, falseZero).reason());
    }

    @Test
    void sdkContainersKeepExtensionsButOperationEnvelopesRejectUnknownMissingAndDuplicateFields() throws IOException {
        ObjectNode request = (ObjectNode) vectorInput("latest-root-targeting-present").deepCopy();
        ObjectNode context = (ObjectNode) request.path("history").get(0).path("result").path("campaign_root_context");
        context.putObject("extension").putArray("retained").addNull().add(false).add(new BigInteger("18446744073709551615"));
        RootView selected = latestSameFrameRoot(FactionCandidateCodec.decodeRootSearch(JSON.writeValueAsBytes(request)));
        assertEquals(context, JSON.readTree(FactionCandidateCodec.encodeRootView(selected)).path("root"));
        byte[] cloned = selected.root().orElseThrow().original().json();
        cloned[0] = 0;
        assertEquals(context, JSON.readTree(selected.root().orElseThrow().original().json()));
        request.put("unknown", true);
        assertThrows(IllegalArgumentException.class, () -> FactionCandidateCodec.decodeRootSearch(JSON.writeValueAsBytes(request)));
        request.remove("unknown");
        request.remove("history");
        assertThrows(IllegalArgumentException.class, () -> FactionCandidateCodec.decodeRootSearch(JSON.writeValueAsBytes(request)));
        assertThrows(IllegalArgumentException.class, () -> FactionCandidateCodec.decodeRootSearch(utf8(
                "{\"snapshot\":{},\"history\":[],\"history\":[]}")));
        assertThrows(IllegalArgumentException.class, () -> FactionCandidateCodec.decodeCandidateInput(utf8("{} {}")));
    }

    @Test
    void rejectsMalformedEncodingAndBoundedInputWithoutConvertingToKnownEmpty() {
        assertThrows(IllegalArgumentException.class, () -> FactionCandidateCodec.decodeRootSearch(new byte[0]));
        assertThrows(IllegalArgumentException.class, () -> FactionCandidateCodec.decodeCandidateInput(
                new byte[FactionCandidateCodec.MAX_BYTES + 1]));
        byte[] malformed = {'{', '"', (byte) 0xC3, '"', ':', '0', '}'};
        assertThrows(IllegalArgumentException.class, () -> FactionCandidateCodec.decodeRootProjection(malformed));
    }

    @Test
    void privateEvaluationCallsExistingJavaLeafOnceAndEarlyRejectionDoesNotCallIt() throws IOException {
        CandidateInput selected = FactionCandidateCodec.decodeCandidateInput(JSON.writeValueAsBytes(vectorInput("private-native-selected")));
        AtomicInteger calls = new AtomicInteger();
        GiftDecisionPort realLeaf = FactionCandidateCodec.existingJavaGiftDecision();
        GiftDecisionPort counted = (observation, reserve) -> {
            calls.incrementAndGet();
            return realLeaf.choose(observation, reserve);
        };
        assertInstanceOf(Evaluated.class, choosePrivateCandidate(selected, counted));
        assertEquals(1, calls.get());
        CandidateInput absent = FactionCandidateCodec.decodeCandidateInput(JSON.writeValueAsBytes(vectorInput("private-no-targeting-vector")));
        assertInstanceOf(Rejected.class, choosePrivateCandidate(absent, counted));
        assertEquals(1, calls.get());
    }

    @Test
    void rootProjectionParserIsNotRootSelectionAndRecordsKeepOriginalIntegerPrecision() throws IOException {
        ObjectNode input = (ObjectNode) vectorInput("private-native-selected");
        RootProjection projected = FactionCandidateCodec.decodeRootProjection(JSON.writeValueAsBytes(input.path("root")));
        assertEquals(projected.frame().orElseThrow().nativeRevision(), BigInteger.valueOf(412));
        assertThrows(IllegalArgumentException.class, () -> new RootView(RootStatus.KNOWN_EMPTY, Optional.empty()));
        Frame exact = new Frame(BigInteger.ONE.shiftLeft(100), BigInteger.valueOf(-1), BigInteger.ONE.shiftLeft(80));
        assertEquals(BigInteger.ONE.shiftLeft(100), exact.nativeRevision());
    }

    @Test
    void rootProducerFeedsActualPrivateCandidateApplicationAndExistingJavaGiftDecision() throws IOException {
        JsonNode rootInput = vectorInput("latest-root-targeting-present");
        RootView root = latestSameFrameRoot(FactionCandidateCodec.decodeRootSearch(JSON.writeValueAsBytes(rootInput)));
        assertEquals(RootStatus.TARGETING_PRESENT, root.status());
        JsonNode privateInput = vectorInput("private-native-selected");
        CandidateResult candidate = FactionCandidateCodec.evaluatePrivateCandidate(
                JSON.writeValueAsBytes(privateInput.path("snapshot")), root.root().orElseThrow(),
                JSON.writeValueAsBytes(privateInput.path("private_result")), BigInteger.valueOf(10_000_000));
        JsonNode expected = evaluate("candidate", JSON.writeValueAsBytes(privateInput));
        assertEquals(expected, JSON.readTree(FactionCandidateCodec.encodeCandidateResult(candidate)));
    }

    @Test
    void applicationReencodingCannotTurnFloatingReceiverOrCostTokensIntoIntegerEligibility() throws IOException {
        JsonNode input = vectorInput("private-native-selected");
        byte[] snapshot = JSON.writeValueAsBytes(input.path("snapshot"));
        RootProjection root = FactionCandidateCodec.decodeRootProjection(JSON.writeValueAsBytes(input.path("root")));
        String preview = JSON.writeValueAsString(input.path("private_result"));
        assertTrue(preview.contains("\"failure_flags\":0"));
        for (String floatingZero : List.of("0.0", "0e0")) {
            CandidateResult result = FactionCandidateCodec.evaluatePrivateCandidate(snapshot, root,
                    utf8(preview.replace("\"failure_flags\":0", "\"failure_flags\":" + floatingZero)),
                    BigInteger.valueOf(10_000_000));
            assertEquals(RejectionReason.NATIVE_PREVIEW_RECEIVER_RED, assertInstanceOf(Rejected.class, result).reason());
        }
        String cost = "\"gold_cost_raw\":" + input.path("private_result").path("native")
                .path("observation").path("gift_preview").path("gold_cost_raw").bigIntegerValue();
        assertTrue(preview.contains(cost), "the actual unchanged producer fixture must contain its cost");
        CandidateResult floatCost = FactionCandidateCodec.evaluatePrivateCandidate(snapshot, root,
                utf8(preview.replace(cost, cost + ".0")), BigInteger.valueOf(10_000_000));
        assertInstanceOf(FactionGiftChoice.Declined.class, assertInstanceOf(Evaluated.class, floatCost).choice());
    }

    @Test
    void opaqueRootDecimalsKeepPrecisionMagnitudeAndFloatingTokenDomainAcrossConsumers() throws IOException {
        String root = JSON.writeValueAsString(vectorInput("private-native-selected").path("root"));
        String wire = root.substring(0, root.length() - 1)
                + ",\"decimal_extension\":{\"zero\":0e0,\"fraction\":0.12345678901234567890123456789,\"huge\":1e400}}";
        RootProjection projected = FactionCandidateCodec.decodeRootProjection(utf8(wire));
        byte[] encoded = FactionCandidateCodec.encodeRootView(new RootView(RootStatus.TARGETING_PRESENT, Optional.of(projected)));
        ObjectMapper exact = new ObjectMapper().enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS);
        JsonNode extension = exact.readTree(encoded).path("root").path("decimal_extension");
        assertTrue(extension.path("zero").isFloatingPointNumber());
        assertTrue(extension.path("huge").isFloatingPointNumber());
        assertEquals(0, new BigDecimal("0.12345678901234567890123456789").compareTo(extension.path("fraction").decimalValue()));
        assertEquals(0, new BigDecimal("1e400").compareTo(extension.path("huge").decimalValue()));
    }

    private static JsonNode evaluate(String operation, byte[] input) throws IOException {
        if (operation.equals("root")) {
            return JSON.readTree(FactionCandidateCodec.encodeRootView(latestSameFrameRoot(FactionCandidateCodec.decodeRootSearch(input))));
        }
        if (!operation.equals("candidate")) throw new IllegalArgumentException("unknown golden operation");
        return JSON.readTree(FactionCandidateCodec.encodeCandidateResult(choosePrivateCandidate(
                FactionCandidateCodec.decodeCandidateInput(input), FactionCandidateCodec.existingJavaGiftDecision())));
    }

    private static JsonNode vectorInput(String name) throws IOException {
        for (JsonNode vector : golden().path("cases")) if (vector.path("name").textValue().equals(name)) return vector.path("input");
        throw new IllegalArgumentException("missing mandatory golden " + name);
    }

    private static JsonNode golden() throws IOException {
        try (InputStream input = FactionCandidatePolicyTest.class.getResourceAsStream("/factioncandidate/python-golden-v1.json")) {
            assertNotNull(input, "committed original producer golden is mandatory");
            byte[] bytes = input.readNBytes(95_001);
            assertTrue(bytes.length <= 95_000, "bounded original-producer golden");
            return JSON.readTree(bytes);
        }
    }

    private static byte[] utf8(String text) { return text.getBytes(StandardCharsets.UTF_8); }
}
