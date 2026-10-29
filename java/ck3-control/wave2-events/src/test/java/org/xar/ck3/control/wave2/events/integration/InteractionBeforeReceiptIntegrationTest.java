package org.xar.ck3.control.wave2.events.integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.interactionbefore.InteractionBeforeComposer;
import org.xar.ck3.control.wave2.events.interactionbefore.InteractionBeforeEvidence.GuiSourcePin;
import org.xar.ck3.control.wave2.events.interactionbefore.InteractionBeforeEvidence.Identity;
import org.xar.ck3.control.wave2.events.interactionbefore.InteractionBeforeEvidence.Prepared;
import org.xar.ck3.control.wave2.events.interactionreceipt.InteractionReceipt;
import org.xar.ck3.control.wave2.events.interactionreceipt.InteractionReceiptCodec;

/** Original producer fixtures exercise the before-to-response boundary, without a dispatch or incident settlement. */
final class InteractionBeforeReceiptIntegrationTest {
    @Test void originalLeftReplyBeforeFeedsConsumerWithoutGrantingIncidentCompletion() throws IOException {
        JsonNode beforeCorpus = fixture("/interactionbefore/legacy-producer-golden-v1.json");
        JsonNode receiptCorpus = fixture("/interactionreceipt/legacy-producer-golden-v1.json");
        JsonNode receiptCase = sample(receiptCorpus, "service_reject");
        Prepared known = compose(beforeCorpus, "known");
        Prepared unknown = compose(beforeCorpus, "unknown");

        JsonNode before = StrictJson.parse(known.json());
        assertTrue(before.get("registry_known").booleanValue());
        assertEquals("before_submission", before.get("stage").textValue());
        assertEquals("left", before.get("selection").get("position").textValue());
        assertEquals("reject", before.get("selection").get("action").textValue());
        assertEquals("reject-pending-character-interaction", known.selectedStep().orElseThrow());
        assertEquals(known.identity().incidentId(), before.get("incident_id").textValue());

        byte[] originalResponse = receiptCase.get("response_utf8").textValue().getBytes(StandardCharsets.UTF_8);
        InteractionReceipt.Response response = InteractionReceiptCodec.parseResponse(
                originalResponse, receiptCase.get("response_sha256").textValue());
        assertEquals("reply_api", receiptCase.get("origin").textValue());
        assertEquals("reject", receiptCase.get("action").textValue());
        assertEquals(Boolean.FALSE, response.accepted().value());
        assertEquals(receiptCase.get("response_sha256").textValue(), response.originalSha256());
        assertFalse(StrictJson.parse(originalResponse).has("incident_id"));

        // These are separately captured original producer cases, on synthetic native seams.
        // Matching pending IDs do not bind the service response to either before incident.
        assertNotEquals(known.identity().incidentId(), unknown.identity().incidentId());
        assertEquals(known.pendingInteractionId(), unknown.pendingInteractionId());
        assertEquals(known.pendingInteractionId(), receiptCase.get("pending_interaction_id").intValue());
        for (Prepared prepared : new Prepared[] {known, unknown}) {
            InteractionReceipt.Expected expected = new InteractionReceipt.Expected(prepared.pendingInteractionId(),
                    InteractionReceipt.Action.valueOf(prepared.action().name()));
            InteractionReceipt.Assessment claim = InteractionReceipt.assess(expected,
                    InteractionReceipt.Origin.REPLY_API, response, null);
            assertEquals(InteractionReceipt.Action.REJECT, expected.action());
            assertEquals(Boolean.FALSE, claim.replyAcceptArgument());
            assertEquals(InteractionReceipt.Ack.NOT_REPORTED_AS_ACK, claim.commandAcknowledged());
            assertFalse(claim.legacyCaptureWouldMarkAdvanced());
            assertTrue(claim.originalPendingAdvancedInResponse(), "response-only claim; no incident binding or settlement");
            assertTrue(claim.gaps().isEmpty());
            assertFalse(claim.materialEffectsVerified());
            assertFalse(claim.replayAllowed());
            assertFalse(prepared.dispatchAttempted());
            assertFalse(prepared.durableBeforeWritten());
            assertFalse(prepared.replayAllowed());
            assertEquals(prepared.identity().incidentId(), StrictJson.parse(prepared.json()).get("incident_id").textValue());
            JsonNode encoded = StrictJson.parse(InteractionReceiptCodec.encodeAssessment(claim));
            assertEquals("not_reported_as_ack", encoded.get("command_acknowledged").textValue());
            assertFalse(encoded.get("reply_accept_argument").booleanValue());
            assertFalse(encoded.has("incident_id"), "response assessment has no authority to bind or complete an incident");
        }
    }

    private static Prepared compose(JsonNode corpus, String name) {
        JsonNode row = sample(corpus, name);
        JsonNode result = row.get("result");
        assertEquals("prepared", result.get("status").textValue());
        Identity identity = new Identity(result.get("incident_id").textValue(),
                result.get("captured_at_utc").textValue(), corpus.get("machine_id").textValue());
        return assertInstanceOf(Prepared.class, InteractionBeforeComposer.compose(
                row.get("planned_utf8").textValue().getBytes(StandardCharsets.UTF_8),
                row.get("planned_sha256").textValue(), identity,
                new GuiSourcePin(corpus.get("gui_source").textValue(), corpus.get("gui_sha256").textValue())));
    }

    private static JsonNode sample(JsonNode corpus, String name) {
        for (JsonNode row : corpus.get("cases")) {
            if (name.equals(row.get("name").textValue())) { return row; }
        }
        throw new AssertionError("required original producer case missing: " + name);
    }

    private static JsonNode fixture(String resource) throws IOException {
        try (var input = InteractionBeforeReceiptIntegrationTest.class.getResourceAsStream(resource)) {
            assertNotNull(input, "original producer fixture required: " + resource);
            byte[] raw = input.readNBytes(98_305);
            assertTrue(raw.length <= 98_304, "bounded committed producer fixture required");
            return new ObjectMapper().readTree(raw);
        }
    }
}
