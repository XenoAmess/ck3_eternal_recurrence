package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.util.List;
import java.util.Optional;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.ObjectValue;

/** Original producer corpus through both actual after-response consumers. */
final class UnhandledEventAfterPresenceTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final String RESOURCE = "/unhandledevent/unhandled-event-evidence-body-golden-v1.json.gz";
    private static final String CLEARED = "independent-next-none-verified";

    private static JsonNode row(String collection, String name) throws IOException {
        try (InputStream input = UnhandledEventAfterPresenceTest.class.getResourceAsStream(RESOURCE)) {
            assertNotNull(input, "the original producer corpus is mandatory; missing evidence must not skip tests");
            try (GZIPInputStream uncompressed = new GZIPInputStream(input)) {
                JsonNode corpus = JSON.readTree(uncompressed);
                for (JsonNode item : corpus.path(collection)) {
                    if (name.equals(item.path("name").textValue())) return item;
                }
            }
        }
        throw new IllegalStateException("required original producer case missing: " + collection + "/" + name);
    }

    private static ObjectNode request(JsonNode row, String field) {
        JsonNode value = row.path(field).deepCopy();
        if (!(value instanceof ObjectNode object)) throw new IllegalStateException("original request must be an object");
        return object;
    }

    private static ObjectNode selection(ObjectNode request) {
        JsonNode value = request.path("outcome").path("result").path("event_selection");
        if (!(value instanceof ObjectNode object)) throw new IllegalStateException("original selection must be an object");
        return object;
    }

    private static UnhandledEventFallback.AfterAssessment assessment(ObjectNode request) throws IOException {
        UnhandledEventCodec.AfterInput input = UnhandledEventCodec.decodeAfter(JSON.writeValueAsBytes(request));
        return UnhandledEventFallback.assessAfter(input.ticket(), input.observation()).orElseThrow();
    }

    @Test void originalExplicitNullStillVerifiesClearedWindowInAfterAssessment() throws IOException {
        JsonNode original = row("after_cases", CLEARED);
        ObjectNode request = request(original, "request");
        assertTrue(selection(request).has("new_event_instance_id"));
        assertTrue(selection(request).path("new_event_instance_id").isNull());
        UnhandledEventFallback.AfterAssessment assessment = assessment(request);
        assertTrue(assessment.commandAcknowledged());
        assertTrue(assessment.eventInstanceAdvancedVerified());
        assertFalse(assessment.replayAllowed());
        assertEquals(RetainedJson.parse(JSON.writeValueAsBytes(original.get("expected"))),
                RetainedJson.parse(UnhandledEventCodec.encodeAfter(Optional.of(assessment))));
    }

    @Test void missingNextInstanceCannotVerifyAnAfterAssessment() throws IOException {
        ObjectNode request = request(row("after_cases", CLEARED), "request");
        selection(request).remove("new_event_instance_id");
        assertFalse(selection(request).has("new_event_instance_id"));
        assertThrows(IllegalArgumentException.class, () -> UnhandledEventCodec.decodeAfter(JSON.writeValueAsBytes(request)));
    }

    @Test void originalExplicitNullStillMatchesCompleteEvidenceBodyAndSerialization() throws IOException {
        JsonNode original = row("body_cases", CLEARED);
        ObjectNode request = request(original, "after_request");
        UnhandledEventEvidenceJson.AfterInput input = UnhandledEventEvidenceJson.decodeAfter(JSON.writeValueAsBytes(request));
        Optional<ObjectValue> body = UnhandledEventEvidenceJson.after(input);
        byte[] encoded = UnhandledEventEvidenceJson.encodeBody(body);
        assertEquals(RetainedJson.parse(JSON.writeValueAsBytes(original.get("expected_after"))), RetainedJson.parse(encoded));
        assertEquals(RetainedJson.parse(encoded), RetainedJson.parse(RetainedJson.encode(RetainedJson.parse(encoded))));
        JsonNode actual = JSON.readTree(encoded);
        assertTrue(actual.path("command_acknowledged").booleanValue());
        assertTrue(actual.path("event_instance_advanced_verified").booleanValue());
        assertTrue(actual.path("event_selection").has("new_event_instance_id"));
        assertTrue(actual.path("event_selection").path("new_event_instance_id").isNull());
        assertFalse(actual.path("replay_allowed").booleanValue());
    }

    @Test void missingNextInstanceIsRejectedByEvidenceDecode() throws IOException {
        ObjectNode request = request(row("body_cases", CLEARED), "after_request");
        selection(request).remove("new_event_instance_id");
        assertThrows(IllegalArgumentException.class, () -> UnhandledEventEvidenceJson.decodeAfter(JSON.writeValueAsBytes(request)));
    }

    @Test void directTypedEvidenceInputCannotBypassTheNestedReceiptBoundary() throws IOException {
        ObjectNode request = request(row("body_cases", CLEARED), "after_request");
        selection(request).remove("new_event_instance_id");
        ObjectValue ticket = RetainedJson.object(RetainedJson.parse(JSON.writeValueAsBytes(request.get("ticket"))));
        ObjectValue outcome = RetainedJson.object(RetainedJson.parse(JSON.writeValueAsBytes(request.get("outcome"))));
        UnhandledEventEvidenceJson.AfterInput input = new UnhandledEventEvidenceJson.AfterInput(
                Optional.of(ticket), Optional.of(outcome), RetainedJson.NULL, request.path("captured_at_utc").textValue());
        assertThrows(IllegalArgumentException.class, () -> UnhandledEventEvidenceJson.after(input));
    }

    @Test void bothConsumersKeepRejectingBooleanFloatingAndStringNextInstanceIds() throws IOException {
        List<JsonNode> invalid = List.of(JSON.getNodeFactory().booleanNode(true),
                JSON.getNodeFactory().numberNode(42.0), JSON.getNodeFactory().textNode("42"));
        for (JsonNode value : invalid) {
            ObjectNode assessmentRequest = request(row("after_cases", CLEARED), "request");
            selection(assessmentRequest).set("new_event_instance_id", value);
            assertThrows(IllegalArgumentException.class, () -> UnhandledEventCodec.decodeAfter(JSON.writeValueAsBytes(assessmentRequest)));
            ObjectNode evidenceRequest = request(row("body_cases", CLEARED), "after_request");
            selection(evidenceRequest).set("new_event_instance_id", value);
            assertThrows(IllegalArgumentException.class, () -> UnhandledEventEvidenceJson.decodeAfter(JSON.writeValueAsBytes(evidenceRequest)));
        }
    }

    @Test void acknowledgementWithoutASelectionStaysAcknowledgedAndUnverified() throws IOException {
        ObjectNode assessmentRequest = request(row("after_cases", "ack-only"), "request");
        UnhandledEventFallback.AfterAssessment assessment = assessment(assessmentRequest);
        assertTrue(assessment.commandAcknowledged());
        assertFalse(assessment.eventInstanceAdvancedVerified());
        assertFalse(assessment.replayAllowed());
        ObjectNode evidenceRequest = request(row("body_cases", "ack-only"), "after_request");
        byte[] raw = UnhandledEventEvidenceJson.encodeBody(UnhandledEventEvidenceJson.after(
                UnhandledEventEvidenceJson.decodeAfter(JSON.writeValueAsBytes(evidenceRequest))));
        JsonNode body = JSON.readTree(raw);
        assertTrue(body.path("command_acknowledged").booleanValue());
        assertFalse(body.path("event_instance_advanced_verified").booleanValue());
        assertFalse(body.path("replay_allowed").booleanValue());
    }
}
