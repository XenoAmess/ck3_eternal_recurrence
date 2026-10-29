package org.xar.ck3.control.wave2.events.mandatoryreceipt;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.mandatoryreceipt.MandatoryReceiptModel.*;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;

final class MandatoryReceiptProducerTest {
    private static final ObjectMapper JSON = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);
    @TestFactory Stream<DynamicTest> realImmutableBeforeAfterProducerRoundTrip() throws IOException {
        JsonNode golden = golden(); assertEquals(15, golden.path("cases").size());
        return StreamSupport.stream(golden.path("cases").spliterator(), false).map(row -> DynamicTest.dynamicTest(row.path("name").textValue(), () ->
                assertEquals(row.get("output"), JSON.readTree(MandatoryReceiptJson.produce(JSON.writeValueAsBytes(row.get("request")))))));
    }
    @Test void ackIsNotTheOriginalWindowPostconditionAndNeverGrantsReplayOrMaterialCredit() throws IOException {
        AfterResponse ack = new MandatoryReceiptProducer().produce(MandatoryReceiptJson.decode(JSON.writeValueAsBytes(request("ack_only"))));
        assertTrue(ack.commandAcknowledged()); assertFalse(ack.originalWindowAdvancedVerified());
        AfterResponse advanced = new MandatoryReceiptProducer().produce(MandatoryReceiptJson.decode(JSON.writeValueAsBytes(request("actual_complete_original_window_proof"))));
        assertTrue(advanced.originalWindowAdvancedVerified()); assertFalse(advanced.replayAllowed());
        assertFalse(advanced.materialEffectsVerified()); assertFalse(advanced.persistenceCommitted()); assertTrue(advanced.offlineFollowupRequired());
    }
    @Test void realConsumerPortIsInvokedOnceAndRetainsOriginalClaimErrorWithoutRetry() throws IOException {
        AtomicInteger calls = new AtomicInteger(); MandatoryReceiptPort concrete = new MandatoryReceiptProducer();
        MandatoryReceiptPort port = input -> { calls.incrementAndGet(); return concrete.produce(input); };
        JsonNode result = JSON.readTree(MandatoryReceiptJson.produce(JSON.writeValueAsBytes(request("unknown_error_keeps_original_claim")), port));
        assertEquals(1, calls.get()); assertFalse(result.path("command_acknowledged").booleanValue());
        assertFalse(result.path("replay_allowed").booleanValue());
        assertEquals("original-request", result.path("error").path("native_raw_receipt").path("request_id").textValue());
    }
    @Test void nativeBooleanAndIdentityTokensAreActuallyValidated() throws IOException {
        ObjectNode input = request("actual_complete_original_window_proof");
        ObjectNode result = (ObjectNode) input.path("outcome").get("result"); result.put("accepted", 1);
        assertThrows(IllegalArgumentException.class, () -> MandatoryReceiptJson.decode(JSON.writeValueAsBytes(input)));
        for (String token : new String[] {"true", "1.0"}) {
            String valid = JSON.writeValueAsString(request("actual_complete_original_window_proof"));
            String wrong = valid.replace("\"old_instance\":\"i1\"", "\"old_instance\":" + token);
            assertNotEquals(valid, wrong); assertThrows(IllegalArgumentException.class, () -> MandatoryReceiptJson.decode(wrong.getBytes(StandardCharsets.UTF_8)));
        }
        ObjectNode missingRef = request("ack_only"); ((ObjectNode) missingRef.path("ticket").get("before")).remove("sha256");
        assertThrows(IllegalArgumentException.class, () -> MandatoryReceiptJson.decode(JSON.writeValueAsBytes(missingRef)));
    }
    @Test void strictWrapperRejectsDuplicatesUnknownsAndMalformedUtf8() throws IOException {
        ObjectNode missing = request("ack_only"); missing.remove("outcome");
        assertThrows(IllegalArgumentException.class, () -> MandatoryReceiptJson.decode(JSON.writeValueAsBytes(missing)));
        ObjectNode unknown = request("ack_only"); unknown.put("force_advance", true);
        assertThrows(IllegalArgumentException.class, () -> MandatoryReceiptJson.decode(JSON.writeValueAsBytes(unknown)));
        String valid = JSON.writeValueAsString(request("ack_only"));
        assertThrows(IllegalArgumentException.class, () -> MandatoryReceiptJson.decode(("{\"schema\":\"dup\"," + valid.substring(1)).getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> MandatoryReceiptJson.decode((valid + " null").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> MandatoryReceiptJson.decode(new byte[] {(byte) 0xc3, 0x28}));
    }
    private static JsonNode golden() throws IOException {
        try (InputStream input = MandatoryReceiptProducerTest.class.getResourceAsStream("/mandatoryreceipt/producer-golden-v1.json")) {
            if (input == null) { throw new IOException("actual capture_after golden missing; capture not executed"); }
            return JSON.readTree(input);
        }
    }
    private static ObjectNode request(String name) throws IOException {
        for (JsonNode row : golden().path("cases")) { if (name.equals(row.path("name").textValue())) { return (ObjectNode) row.get("request").deepCopy(); } }
        throw new IOException("missing actual receipt case " + name);
    }
}
