package org.xar.ck3.control.wave3.development.wartimeconstructioncash;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanCodec;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanModel;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanModel.ExpectedFrame;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanModel.ObservedDecision;
import org.xar.ck3.control.wave2.finance.holyloan.LoanFinancingCodec;
import org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec;
import static org.junit.jupiter.api.Assertions.*;

public final class M4LoanInputProducerTest {
    @Test public void originalProducerAndAllFourCapturedConsumerProjectionsRemainEqual() throws Exception {
        M4OriginalCorpus.LoanCorpus corpus = M4OriginalCorpus.loan();
        assertEquals("xar.holyloan-rawcash-original-golden.v1", corpus.header().path("schema").textValue());
        assertTrue(corpus.header().path("passed").intValue() > 100);
        assertEquals(0, corpus.header().path("skips").intValue());
        assertEquals(7, corpus.header().path("test_modules").size());
        Set<String> operations = new HashSet<>();
        for (M4OriginalCorpus.LoanVector vector : corpus.vectors()) {
            operations.add(vector.operation());
            if ("invalid_contract".equals(vector.expectedKind())) {
                assertThrows(IllegalArgumentException.class, () -> evaluate(vector.requestUtf8()), vector.operation());
            } else {
                assertEquals(vector.expected(), StrictJson.parse(evaluate(vector.requestUtf8())), vector.operation());
            }
        }
        assertEquals(Set.of("project", "normalize", "monthly", "financing"), operations);
    }

    @Test public void everyProjectedLoanRoundTripsAndNativeGatesNeverGrantMoneyOrActions() throws Exception {
        for (M4OriginalCorpus.LoanVector vector : M4OriginalCorpus.loan().vectors()) {
            if (!"project".equals(vector.operation()) || !"result".equals(vector.expectedKind())) { continue; }
            byte[] projected = evaluate(vector.requestUtf8());
            JsonNode output = StrictJson.parse(projected);
            assertEquals(output, StrictJson.parse(HolyLoanCodec.encode(HolyLoanCodec.decodeObservation(projected))));
            assertFalse(output.get("complete_loan_terms").booleanValue());
            assertFalse(output.get("submission_qualified").booleanValue());
            assertFalse(output.get("received_funds_verified").booleanValue());
            assertEquals(BigInteger.ZERO, output.get("funding_credit_raw").bigIntegerValue());
            for (String field : List.of("principal_quote_raw", "existing_debt_principal_raw", "repayment_total_outlay_raw", "selected_action")) {
                assertTrue(output.get(field).isNull(), field);
                ObjectNode forged = output.deepCopy(); forged.put(field, 1);
                assertThrows(IllegalArgumentException.class, () -> HolyLoanCodec.decodeObservation(M4OriginalCorpus.wire(forged)), field);
            }
        }
    }

    @Test public void maximumCaptureEpochAndAllSignedResourceSlotsRemainExactAndImmutable() throws Exception {
        ObjectNode arguments = firstProjectArguments();
        ObjectNode nativeValue = (ObjectNode) arguments.get("value");
        nativeValue.put("capture_epoch", HolyLoanModel.UINT64_MAX);
        ObjectNode expected = expectedNode(arguments); expected.put("capture_epoch", HolyLoanModel.UINT64_MAX);
        var costs = ((ObjectNode) nativeValue.get("borrow_decision")).putArray("costs_raw_by_native_index");
        costs.add(Long.MIN_VALUE); costs.add(Long.MAX_VALUE);
        for (int index = 2; index < 10; index++) { costs.add(0); }
        var produced = M4LoanInputProducer.produce(M4OriginalCorpus.wire(nativeValue), M4OriginalCorpus.wire(expected));
        assertEquals(HolyLoanModel.UINT64_MAX, produced.observation().source().captureEpoch());
        var observed = (ObservedDecision) produced.observation().borrowDecision();
        assertEquals(List.of(Long.MIN_VALUE, Long.MAX_VALUE), observed.declaredCostsRaw().subList(0, 2));
        assertThrows(UnsupportedOperationException.class, () -> observed.declaredCostsRaw().clear());
        byte[] copied = produced.utf8(); copied[0] = '[';
        assertEquals(produced.observation(), HolyLoanCodec.decodeObservation(produced.utf8()));
    }

    @Test public void externalOwnerFrameAndNativeAmountsRejectBooleanFloatAndStringBeforeConstruction() throws Exception {
        ObjectNode arguments = firstProjectArguments();
        String nativeRaw = new String(M4OriginalCorpus.wire(arguments.get("value")), StandardCharsets.UTF_8);
        String frameRaw = new String(M4OriginalCorpus.wire(expectedNode(arguments)), StandardCharsets.UTF_8);
        for (String token : List.of("true", "123.0", "\"123\"")) {
            String nativeBad = nativeRaw.replaceFirst("\"capture_epoch\":[0-9]+", "\"capture_epoch\":" + token);
            String frameBad = frameRaw.replaceFirst("\"capture_epoch\":[0-9]+", "\"capture_epoch\":" + token);
            assertNotEquals(nativeRaw, nativeBad); assertNotEquals(frameRaw, frameBad);
            assertThrows(IllegalArgumentException.class, () -> M4LoanInputProducer.produce(
                    nativeBad.getBytes(StandardCharsets.UTF_8), frameRaw.getBytes(StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class, () -> M4LoanInputProducer.produce(
                    nativeRaw.getBytes(StandardCharsets.UTF_8), frameBad.getBytes(StandardCharsets.UTF_8)));
        }
        byte[] wrongSlotCount = nativeRaw.replaceFirst("\"resource_slot_count\":10", "\"resource_slot_count\":10.0")
                .getBytes(StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class,
                () -> M4LoanInputProducer.produce(wrongSlotCount, frameRaw.getBytes(StandardCharsets.UTF_8)));
    }

    /** Dispatches captured calls to the existing four Java consumers; no policy arithmetic is duplicated. */
    private static byte[] evaluate(byte[] requestUtf8) {
        JsonNode input = StrictJson.object(StrictJson.parse(requestUtf8), Set.of("operation", "arguments"));
        JsonNode arguments = input.get("arguments");
        return switch (StrictJson.text(input.get("operation"))) {
            case "project" -> {
                StrictJson.object(arguments, Set.of("value", "expected_played_character_id", "expected_date_raw", "expected_capture_epoch"));
                yield M4LoanInputProducer.produce(M4OriginalCorpus.wire(arguments.get("value")),
                        M4OriginalCorpus.wire(expectedNode(arguments))).utf8();
            }
            case "normalize" -> {
                StrictJson.object(arguments, Set.of("value", "snapshot"));
                yield RawCashCodec.normalize(M4OriginalCorpus.wire(arguments.get("value")), M4OriginalCorpus.wire(arguments.get("snapshot"))).toJson();
            }
            case "monthly" -> {
                StrictJson.object(arguments, Set.of("current"));
                RawCashCodec.validateMonthlyFlow(M4OriginalCorpus.wire(arguments.get("current")));
                yield new byte[] {'n', 'u', 'l', 'l'};
            }
            case "financing" -> {
                StrictJson.object(arguments, Set.of("snapshot", "cash_resources", "cash_source_frame"));
                yield LoanFinancingCodec.encode(LoanFinancingCodec.decodeAndProject(M4OriginalCorpus.wire(arguments)));
            }
            default -> throw new IllegalArgumentException("unknown original captured operation");
        };
    }

    private static ObjectNode expectedNode(JsonNode arguments) {
        ObjectNode expected = StrictJson.object();
        expected.set("played_character_id", arguments.get("expected_played_character_id"));
        expected.set("date_raw", arguments.get("expected_date_raw"));
        expected.set("capture_epoch", arguments.get("expected_capture_epoch"));
        return expected;
    }

    private static ObjectNode firstProjectArguments() throws Exception {
        for (M4OriginalCorpus.LoanVector vector : M4OriginalCorpus.loan().vectors()) {
            if ("project".equals(vector.operation()) && "result".equals(vector.expectedKind())) {
                return (ObjectNode) StrictJson.parse(vector.requestUtf8()).get("arguments");
            }
        }
        throw new IllegalStateException("actual original loan project vector required");
    }
}
