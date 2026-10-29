package org.xar.ck3.control.wave2.events.integration;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.wave2.events.choiceplanning.ChoicePlanningJson;
import org.xar.ck3.control.wave2.events.mandatoryreceipt.MandatoryReceiptJson;
import org.xar.ck3.control.wave2.events.mandatoryreceipt.MandatoryReceiptModel;
import org.xar.ck3.control.wave2.events.mandatoryreceipt.MandatoryReceiptProducer;
import org.xar.ck3.control.wave2.events.uirecoveryidentity.UiRecoveryIdentityJson;

/** Actual saved producer vectors cross the Java consumer chain; mixed original postconditions cannot advance it. */
final class NativeChoiceProducerConsumerTest {
    private static final ObjectMapper JSON = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);

    @Test void realP09QuerySelectionAndSourceIdentityRejectAnotherIncidentNativeAck() throws IOException {
        JsonNode planning = caseNamed(read("/choiceplanning/producer-golden-v1.json.gz", true), "actual_p09_same_root_unavailable_event");
        JsonNode plan = JSON.readTree(ChoicePlanningJson.plan(JSON.writeValueAsBytes(planning.get("request"))));
        assertEquals(planning.get("output"), plan);
        JsonNode capture = plan.get("unknown_mandatory_choice_v1");
        JsonNode window = capture.get("native_window");
        JsonNode selected = capture.get("selection");

        JsonNode identityOracle = caseNamed(read("/uirecoveryidentity/producer-golden-v1.json", false), "native_numeric_rva_parallel_catalogue");
        ObjectNode sourceRequest = JSON.createObjectNode(); sourceRequest.put("schema", UiRecoveryIdentityJson.SCHEMA);
        sourceRequest.set("window", window); sourceRequest.set("backend_sha256", identityOracle.path("request").get("backend_sha256"));
        JsonNode identity = JSON.readTree(UiRecoveryIdentityJson.fingerprint(JSON.writeValueAsBytes(sourceRequest)));
        assertTrue(identity.path("source_key").textValue().matches("[0-9a-f]{64}"));
        assertEquals(window.path("source_identity").get("root_runtime_name"), identity.path("stable_source").get("root_runtime_name"));
        assertEquals(window.path("choices").size(), identity.path("stable_source").path("choice_catalogue").size());
        assertTrue(capture.path("typed_event_unavailable_same_root_fallback").booleanValue());

        JsonNode afterOracle = caseNamed(read("/mandatoryreceipt/producer-golden-v1.json", false), "actual_complete_original_window_proof");
        ObjectNode request = (ObjectNode) afterOracle.get("request").deepCopy();
        ObjectNode ticket = (ObjectNode) request.get("ticket");
        assertNotEquals(ticket.get("instance"), window.get("window_instance_id"), "vectors must describe different original instances");
        ticket.set("window_id", window.get("window_id")); ticket.set("instance", window.get("window_instance_id"));
        ticket.set("choice_id", selected.get("choice_id"));
        MandatoryReceiptModel.AfterResponse after = new MandatoryReceiptProducer().produce(MandatoryReceiptJson.decode(JSON.writeValueAsBytes(request)));
        assertTrue(after.commandAcknowledged(), "retain the actual original ACK as a separate fact");
        assertFalse(after.originalWindowAdvancedVerified(), "the other incident's true postcondition cannot complete this window");
        assertFalse(after.persistenceCommitted()); assertFalse(after.replayAllowed()); assertFalse(after.materialEffectsVerified());
        JsonNode encoded = JSON.readTree(MandatoryReceiptJson.encode(after));
        assertEquals(request.path("outcome").get("result"), encoded.get("action_receipt"), "retain mismatching evidence for diagnosis");
    }

    private static JsonNode caseNamed(JsonNode golden, String name) throws IOException {
        for (JsonNode row : golden.path("cases")) { if (name.equals(row.path("name").textValue())) { return row; } }
        throw new IOException("missing actual producer case " + name);
    }
    private static JsonNode read(String path, boolean compressed) throws IOException {
        try (InputStream resource = NativeChoiceProducerConsumerTest.class.getResourceAsStream(path)) {
            if (resource == null) { throw new IOException("required actual producer golden has not been captured: " + path); }
            try (InputStream input = compressed ? new GZIPInputStream(resource) : resource) {
                byte[] raw = input.readNBytes(102_401); if (raw.length > 102_400) { throw new IOException("bounded actual golden exceeded"); }
                return JSON.readTree(raw);
            }
        }
    }
}
