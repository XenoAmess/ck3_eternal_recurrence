package org.xar.ck3.control.wave2.planning.rootavailability;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

final class RootAvailabilityTest {
    private static final ObjectMapper JSON = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);

    @Test void matchesActualOriginalHelperAcrossCompletedAndStaleHistory() throws IOException {
        JsonNode fixture = fixture(); assertEquals(17, fixture.get("cases").size());
        for (JsonNode scenario : fixture.get("cases")) {
            RootAvailability.Result result = RootAvailability.recognize(RootAvailability.decode(JSON.writeValueAsBytes(scenario.get("input"))));
            assertEquals(scenario.get("expected_same_frame_unavailable").booleanValue(), result.sameFrameRootReturnedUnavailable(), scenario.get("name").textValue());
            JsonNode index = scenario.get("expected_history_index");
            assertEquals(index.isNull() ? -1 : index.intValue(), result.matchingHistoryIndex());
            assertFalse(result.formalActionReady());
        }
    }

    @Test void integerIdentityTokensCannotBeSuppliedAsFloatBooleanStringOrNull() throws IOException {
        String input = JSON.writeValueAsString(valid());
        for (String token : new String[] {"3.0", "true", "\"3\"", "null"}) {
            String resultOnly = input.replace("\"snapshot_revision\":3", "\"snapshot_revision\":" + token);
            RootAvailability.Result result = RootAvailability.recognize(RootAvailability.decode(resultOnly.getBytes(StandardCharsets.UTF_8)));
            assertFalse(result.sameFrameRootReturnedUnavailable(), token);
            assertEquals(RootAvailability.IgnoredReason.malformed_frame,
                    ((RootAvailability.Ignored) RootAvailability.decode(resultOnly.getBytes(StandardCharsets.UTF_8)).history().getFirst()).reason());
        }
        for (String token : new String[] {"3.0", "true", "\"3\"", "null"}) {
            String invalidSnapshot = input.replaceFirst("\"native_revision\":3", "\"native_revision\":" + token);
            assertThrows(IllegalArgumentException.class, () -> RootAvailability.decode(invalidSnapshot.getBytes(StandardCharsets.UTF_8)));
        }
    }

    @Test void missingOrNullResultIsDifferentFromACompletedUnavailableRead() throws IOException {
        ObjectNode input = valid();
        ObjectNode row = (ObjectNode) input.get("history").get(0); row.remove("result");
        RootAvailability.Request missing = RootAvailability.decode(JSON.writeValueAsBytes(input));
        assertEquals(RootAvailability.IgnoredReason.unreadable_result, ((RootAvailability.Ignored) missing.history().getFirst()).reason());
        row.putNull("result");
        assertFalse(RootAvailability.recognize(RootAvailability.decode(JSON.writeValueAsBytes(input))).sameFrameRootReturnedUnavailable());
        ((ArrayNode) input.get("history")).removeAll();
        assertFalse(RootAvailability.recognize(RootAvailability.decode(JSON.writeValueAsBytes(input))).sameFrameRootReturnedUnavailable());
    }

    @Test void malformedEnvelopeAndDuplicateFieldsAreRejectedWithoutIssuingQuery() throws IOException {
        ObjectNode input = valid(); input.put("unexpected", 1); byte[] unknown = JSON.writeValueAsBytes(input);
        assertThrows(IllegalArgumentException.class, () -> RootAvailability.decode(unknown));
        input = valid(); input.remove("history"); byte[] missing = JSON.writeValueAsBytes(input);
        assertThrows(IllegalArgumentException.class, () -> RootAvailability.decode(missing));
        String duplicate = JSON.writeValueAsString(valid()).replaceFirst("\\{", "{\"history\":[],");
        assertThrows(IllegalArgumentException.class, () -> RootAvailability.decode(duplicate.getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> RootAvailability.decode(new byte[] {(byte) 0xc3, (byte) 0x28}));
        JsonNode output = StrictJson.parse(RootAvailability.recognize(JSON.writeValueAsBytes(valid())));
        assertFalse(output.get("query_issued").booleanValue()); assertTrue(output.get("selected_step").isNull());
    }

    @Test void immutableHistoryAndSerializationRoundTripRetainRecognition() throws IOException {
        RootAvailability.Request request = RootAvailability.decode(JSON.writeValueAsBytes(valid()));
        assertThrows(UnsupportedOperationException.class, () -> request.history().clear());
        byte[] output = RootAvailability.recognize(JSON.writeValueAsBytes(valid()));
        assertEquals(StrictJson.parse(output), StrictJson.parse(StrictJson.canonical(StrictJson.parse(output))));
        JsonNode roundTripInput = JSON.readTree(JSON.writeValueAsBytes(valid()));
        assertEquals(RootAvailability.recognize(request), RootAvailability.recognize(RootAvailability.decode(JSON.writeValueAsBytes(roundTripInput))));
    }

    private static ObjectNode valid() throws IOException { return (ObjectNode) fixture().get("cases").get(1).get("input").deepCopy(); }
    private static JsonNode fixture() throws IOException {
        try (InputStream stream = RootAvailabilityTest.class.getResourceAsStream("/rootavailability/original-producer-golden.json")) {
            if (stream == null) { throw new IOException("actual original-helper golden required; test is not skipped"); }
            return JSON.readTree(stream);
        }
    }
}
