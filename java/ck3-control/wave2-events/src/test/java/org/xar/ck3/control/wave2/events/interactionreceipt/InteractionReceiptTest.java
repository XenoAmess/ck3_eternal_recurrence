package org.xar.ck3.control.wave2.events.interactionreceipt;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Locale;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistryCodec;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.interactionreceipt.InteractionReceipt.*;

class InteractionReceiptTest {
    private static final String RESOURCE = "/interactionreceipt/legacy-producer-golden-v1.json";

    @Test void actualSharedProducerChainKeepsLegacyOutcomeProjectionForAllCases() throws IOException {
        JsonNode golden = golden(); assertEquals(23, golden.get("cases").size()); assertTrue(golden.get("actual_method_calls").size() >= 6);
        for (JsonNode row : golden.get("cases")) {
            Assessment value = assess(row);
            assertEquals(row.get("legacy_original_pending_advanced_verified").booleanValue(), value.legacyCaptureWouldMarkAdvanced(), row.get("name").textValue());
            if (value.origin() != Origin.REPLY_API) {
                assertEquals(row.get("legacy_command_acknowledged").booleanValue(), value.commandAcknowledged() == Ack.ACKNOWLEDGED, row.get("name").textValue());
            } else { assertEquals(Ack.NOT_REPORTED_AS_ACK, value.commandAcknowledged()); }
            assertFalse(value.materialEffectsVerified()); assertFalse(value.replayAllowed());
        }
    }

    @Test void realServiceRejectResponseAcceptedFalseIsBusinessIntentAndNeverAckFailure() throws IOException {
        JsonNode row = sample("service_reject"); Response response = response(row); Assessment value = assess(row);
        assertEquals(Boolean.FALSE, response.accepted().value()); assertEquals(Boolean.FALSE, value.replyAcceptArgument());
        assertEquals(Ack.NOT_REPORTED_AS_ACK, value.commandAcknowledged()); assertTrue(value.originalPendingAdvancedInResponse());
        assertFalse(value.legacyCaptureWouldMarkAdvanced()); assertTrue(value.gaps().isEmpty());
        // The adapter supplies the actual registered route; accepted=false alone cannot guess a route.
        Assessment wrongRoute = InteractionReceipt.assess(expected(row), Origin.EXECUTE_STEP, response, null);
        assertEquals(Ack.NOT_ACKNOWLEDGED, wrongRoute.commandAcknowledged()); assertFalse(wrongRoute.originalPendingAdvancedInResponse());
        assertTrue(assess(sample("service_accept")).originalPendingAdvancedInResponse());
        assertTrue(assess(sample("service_acknowledge")).originalPendingAdvancedInResponse());
    }

    @Test void ackOnlyStaleOrContradictoryResponseDoesNotResolveOriginalRequest() throws IOException {
        for (String name : List.of("ack_only", "same_pending", "wrong_original", "wrong_status", "unpaused", "missing_remaining", "accepted_false",
                "accepted_missing", "accepted_null", "missing_step", "wrong_step", "reply_wrong_intent", "reply_wrong_wrapper", "ack_wrong_wrapper_flag", "error_only")) {
            assertFalse(assess(sample(name)).originalPendingAdvancedInResponse(), name);
        }
        assertTrue(assess(sample("remaining_other")).originalPendingAdvancedInResponse());
        assertTrue(assess(sample("execute_reject")).originalPendingAdvancedInResponse());
        assertTrue(assess(sample("execute_accept")).originalPendingAdvancedInResponse());
        assertTrue(assess(sample("execute_acknowledge")).originalPendingAdvancedInResponse());
        assertTrue(assess(sample("missing_step")).legacyCaptureWouldMarkAdvanced(), "legacy difference is preserved explicitly");
    }

    @Test void originalErrorsStaySeparateFromSourceResponseAndNeverAuthorizeReplay() throws IOException {
        JsonNode row = sample("error_with_response"); Assessment error = assess(row);
        assertNotNull(error.error()); assertTrue(error.gaps().contains(Gap.ERROR_PRESENT));
        assertEquals(row.get("error").get("type").textValue(), error.error().type());
        assertEquals(row.get("error").get("message").textValue(), error.error().message());
        assertTrue(error.originalPendingAdvancedInResponse(), "response claim remains separate from later verification error");
        assertFalse(error.replayAllowed()); assertFalse(error.materialEffectsVerified());
        Assessment unknown = assess(sample("error_only")); assertTrue(unknown.gaps().contains(Gap.NO_RESPONSE)); assertFalse(unknown.originalPendingAdvancedInResponse());
    }

    @Test void sourcePinDuplicateMalformedJsonAndInvalidBooleanTokensAreRejected() throws IOException {
        JsonNode row = sample("execute_reject"); byte[] raw = utf8(row.get("response_utf8").textValue());
        assertThrows(ContractViolationException.class, () -> InteractionReceiptCodec.parseResponse(raw, "0".repeat(64)));
        String valid = new String(raw, StandardCharsets.UTF_8);
        for (String token : List.of("1", "1.0", "\"true\"", "[]", "{}")) {
            String bad = valid.replace("\"accepted\":true", "\"accepted\":" + token); assertTrue(bad.contains("\"accepted\":" + token));
            assertThrows(ContractViolationException.class, () -> parse(utf8(bad)), token);
        }
        String duplicate = valid.replaceFirst("\\{", "{\"accepted\":true,");
        assertThrows(ContractViolationException.class, () -> parse(utf8(duplicate)));
        assertThrows(ContractViolationException.class, () -> parse(new byte[] {(byte) 0xff}));
        assertThrows(ContractViolationException.class, () -> parse(utf8(valid + " {}")));
        assertThrows(ContractViolationException.class, () -> parse(new byte[65_537]));
    }

    @Test void signedIdsNeverCoerceBooleanFloatOrInvalidSentinel() throws IOException {
        String valid = sample("execute_reject").get("response_utf8").textValue();
        for (String token : List.of("true", "301989889.0", "301989889e0", "\"301989889\"", "-2147483649", "2147483648", "-1")) {
            String bad = valid.replace("\"instance_id\":301989889", "\"instance_id\":" + token);
            assertTrue(bad.contains("\"instance_id\":" + token)); assertThrows(ContractViolationException.class, () -> parse(utf8(bad)), token);
        }
        for (int id : List.of(Integer.MIN_VALUE, Integer.MAX_VALUE)) {
            String wire = valid.replace("\"instance_id\":301989889", "\"instance_id\":" + id);
            Assessment result = InteractionReceipt.assess(new Expected(id, Action.REJECT), Origin.EXECUTE_STEP, parse(utf8(wire)), null);
            assertTrue(result.originalPendingAdvancedInResponse());
        }
        assertThrows(ContractViolationException.class, () -> new Expected(-1, Action.REJECT));
    }

    @Test void missingNullEmptyAndExtensibleSdkFieldsHaveDeclaredSemantics() throws IOException {
        Response missing = response(sample("accepted_missing")); Response explicitNull = response(sample("accepted_null"));
        assertEquals(Presence.MISSING, missing.accepted().presence()); assertEquals(Presence.NULL, explicitNull.accepted().presence());
        assertEquals(Presence.NULL, parse(utf8("null")).presence()); assertThrows(ContractViolationException.class, () -> parse(utf8("[]")));
        String valid = sample("execute_reject").get("response_utf8").textValue();
        String empty = valid.replace("\"remaining_pending_character_interaction\":null", "\"remaining_pending_character_interaction\":{}");
        assertThrows(ContractViolationException.class, () -> parse(utf8(empty)));
        String extended = valid.replaceFirst("\\{", "{\"sdk_extension\":{\"count\":7},");
        Assessment value = InteractionReceipt.assess(new Expected(301989889, Action.REJECT), Origin.EXECUTE_STEP, parse(utf8(extended)), null);
        assertTrue(value.originalPendingAdvancedInResponse()); assertEquals(InteractionRegistryCodec.digest(utf8(extended)), value.originalSha256());
        assertThrows(ContractViolationException.class, () -> InteractionReceipt.assess(new Expected(301989889, Action.ACKNOWLEDGE), Origin.REPLY_API, parse(utf8(valid)), null));
    }

    @Test void assessmentSerializationPreservesOriginalSourceDigestErrorsAndUnmodifiableGaps() throws IOException {
        Assessment value = assess(sample("error_with_response")); byte[] encoded = InteractionReceiptCodec.encodeAssessment(value); JsonNode json = StrictJson.parse(encoded);
        assertEquals(value.originalSha256(), json.get("original_sha256").textValue()); assertEquals(value.error().message(), json.get("error").get("message").textValue());
        assertEquals(value.originalPendingAdvancedInResponse(), json.get("original_pending_advanced_in_response").booleanValue());
        assertFalse(json.get("material_effects_verified").booleanValue()); assertFalse(json.get("replay_allowed").booleanValue());
        assertArrayEquals(encoded, StrictJson.canonical(json, 16_384)); assertThrows(UnsupportedOperationException.class, () -> value.gaps().clear());
    }

    private static Assessment assess(JsonNode row) {
        JsonNode error = row.get("error"); ErrorInfo actual = error.isNull() ? null : new ErrorInfo(error.get("type").textValue(), error.get("message").textValue());
        return InteractionReceipt.assess(expected(row), Origin.valueOf(row.get("origin").textValue().toUpperCase(Locale.ROOT)), response(row), actual);
    }
    private static Expected expected(JsonNode row) { return new Expected(row.get("pending_interaction_id").intValue(), Action.valueOf(row.get("action").textValue().toUpperCase(Locale.ROOT))); }
    private static Response response(JsonNode row) { return InteractionReceiptCodec.parseResponse(utf8(row.get("response_utf8").textValue()), row.get("response_sha256").textValue()); }
    private static Response parse(byte[] raw) { return InteractionReceiptCodec.parseResponse(raw, InteractionRegistryCodec.digest(raw)); }
    private static byte[] utf8(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static JsonNode sample(String name) throws IOException { for (JsonNode row : golden().get("cases")) { if (row.get("name").textValue().equals(name)) { return row; } } throw new AssertionError(name); }
    private static JsonNode golden() throws IOException { try (var stream = InteractionReceiptTest.class.getResourceAsStream(RESOURCE)) { assertNotNull(stream, "committed actual shared-producer golden required"); return StrictJson.parse(stream.readAllBytes()); } }
}
