package org.xar.ck3.control.wave2.governance.succession;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.governance.succession.PrisonerSubmissionEvidence12004.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider;

final class PrisonerSubmissionEvidence12004Test {
    @Test void exactNativePreMailboxRejectionIsDistinctFromPipeBeforeWriteAndFromGenericRed() {
        for (boolean release : new boolean[]{true, false}) {
            Request request = request(release);
            String specific = release ? "private release terms or request are stale" : "private ransom quote or request is stale";
            for (String text : new String[]{"prisoner request revision or paused player frame is stale", specific}) {
                Observation observation = response(error(text), request);
                assertEquals(State.PRE_SUBMIT_REJECTION_OBSERVED, observation.state());
                assertFalse(observation.terminalProofInIsolation()); assertFalse(observation.replayAuthorized()); assertFalse(observation.releaseOrPaymentProven());
            }
            for (String text : new String[]{"private release submit unresolved or rejected", "private ransom submit unresolved or rejected",
                    "prisoner application-main result or frame unavailable", "prisoner application-main executor unavailable", specific + " ",
                    release ? "private ransom quote or request is stale" : "private release terms or request are stale"}) {
                assertEquals(State.SUBMISSION_UNKNOWN, response(error(text), request).state());
            }
        }
    }
    @Test void submittedAckNeverProvesReleaseOrPaymentAndMustNameTheActualStep() {
        Request request = request(true); ObjectNode ack = envelope(true); ack.putObject("result").put("step", RELEASE_STEP).put("accepted", true).put("status", "submitted_verification_pending");
        Observation observation = response(ack, request); assertEquals(State.SUBMITTED_PENDING, observation.state()); assertFalse(observation.releaseOrPaymentProven());
        ((ObjectNode) ack.get("result")).put("step", RANSOM_STEP);
        assertThrows(IllegalArgumentException.class, () -> response(ack, request));
    }
    @Test void coercionsMissingAndDuplicateFieldsAreRejectedWithoutChangingUnknownToRejection() {
        for (String token : new String[]{"true", "1.0", "\"1\""}) {
            ObjectNode request = requestNode(true); request.set("expected_revision", json(token)); byte[] bytes = bytes(request);
            assertThrows(IllegalArgumentException.class, () -> parseRequest(bytes, ref(bytes), scope()));
        }
        Request request = request(true); ObjectNode wrong = error("private release terms or request are stale"); wrong.put("request_id", "other");
        assertThrows(IllegalArgumentException.class, () -> response(wrong, request));
        byte[] duplicate = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"prisoner\",\"ok\":false,\"ok\":false,\"error\":\"private release terms or request are stale\"}".getBytes(StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> parseResponse(duplicate, ref(duplicate), request));
    }
    @Test void exactSourceClosureAndCanonicalSourceEpochAreRequiredForThisInterpretation() {
        Scope original = scope();
        assertThrows(IllegalArgumentException.class, () -> new Scope(original.session(), original.loadedNative(), "01", original.nativeQualification(), original.mailboxSource(), original.routerSource()));
        ExactRef drift = new ExactRef(original.mailboxSource().path(), original.mailboxSource().bytes(), "0".repeat(64));
        assertThrows(IllegalArgumentException.class, () -> new Scope(original.session(), original.loadedNative(), original.sourceEpoch(), original.nativeQualification(), drift, original.routerSource()));
        assertEquals("16888498602938861", original.session().executableFileId());
    }
    private static Scope scope() {
        return new Scope(NativeTimelineBlocker12004Test.binding().session(), new ExactRef("D:/fixtures/bridge.dll", 42, "1".repeat(64)), "3",
                new ExactRef("D:/fixtures/root-native-custody.json", 42, "2".repeat(64)),
                new ExactRef("D:/fixtures/ck3_12004_prisoner_mailbox.cpp", 26343, MAILBOX_SHA256),
                new ExactRef("D:/fixtures/ck3_12002_nonwar_router.cpp", 55344, ROUTER_SHA256));
    }
    private static ObjectNode requestNode(boolean release) {
        ObjectNode request = StrictJson.object().put("type", "execute_step").put("protocol_version", 1).put("request_id", "prisoner")
                .put("step", release ? RELEASE_STEP : RANSOM_STEP).put("expected_revision", 31).put("prisoner_character_id", 67108867);
        if (release) request.put("release_query_sequence", 9).put("release_option_mask_bits", 0);
        else request.put("quote_query_sequence", 9).put("payer_character_id", 21).put("quoted_gold_raw", 1000000);
        return request;
    }
    private static Request request(boolean release) { byte[] raw = bytes(requestNode(release)); return parseRequest(raw, ref(raw), scope()); }
    private static ObjectNode envelope(boolean ok) { return StrictJson.object().put("type", "command_result").put("protocol_version", 1).put("request_id", "prisoner").put("ok", ok); }
    private static ObjectNode error(String error) { return envelope(false).put("error", error); }
    private static Observation response(ObjectNode response, Request request) { byte[] raw = bytes(response); return parseResponse(raw, ref(raw), request); }
    private static byte[] bytes(JsonNode value) { return StrictJson.canonical(value); }
    private static JsonNode json(String raw) { return StrictJson.parse(raw.getBytes(StandardCharsets.UTF_8)); }
    private static ExactRef ref(byte[] raw) { return new ExactRef("D:/fixtures/" + G2RetainedNativeSourceProvider.sha256(raw) + ".json", raw.length, G2RetainedNativeSourceProvider.sha256(raw)); }
}
