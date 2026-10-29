package org.xar.ck3.control.wave2.events.eventoutcome;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

final class EventOptionSubmissionClaimTest {
    private static EventOptionSubmissionClaim.Request request(int instance, int option, String source) {
        return new EventOptionSubmissionClaim.Request("event-option-" + "1".repeat(32),
                new EventOptionSubmissionClaim.Identity(12345, "native-fixture-episode", instance), option, source.repeat(64));
    }
    @Test void sourceOptionAndRequestChangesCannotReopenSameNativeInstance() {
        EventOptionSubmissionClaim.Document original = EventOptionSubmissionClaim.prepare(request(600, 1, "a"));
        EventOptionSubmissionClaim.Document changed = EventOptionSubmissionClaim.prepare(new EventOptionSubmissionClaim.Request(
                "event-option-" + "2".repeat(32), new EventOptionSubmissionClaim.Identity(12345, "native-fixture-episode", 600),
                2, "b".repeat(64)));
        assertEquals(original.claimKey(), changed.claimKey());
        assertNotEquals(original.claimDocumentJson(), changed.claimDocumentJson());
        assertNotEquals(original.claimKey(), EventOptionSubmissionClaim.prepare(request(601, 1, "a")).claimKey());
    }
    @Test void authoredDocumentAndWireRoundtripUseOneStrictFieldContract() {
        EventOptionSubmissionClaim.Document prepared = EventOptionSubmissionClaim.prepare(request(600, 1, "a"));
        ObjectNode wire = StrictJson.object(StrictJson.parse(EventOptionSubmissionClaim.encode(prepared)),
                Set.of("claim_key", "claim_document_json"));
        assertEquals(prepared.claimDocumentJson(), StrictJson.text(wire.get("claim_document_json")));
        ObjectNode claim = StrictJson.object(StrictJson.parse(prepared.claimDocumentJson().getBytes(StandardCharsets.UTF_8)),
                Set.of("schema", "request_id", "identity", "selected_option_number", "source_program_sha256", "status"));
        assertEquals("claimed_result_unknown_no_retry", StrictJson.text(claim.get("status")));
        assertEquals(1L, StrictJson.integer(claim.get("selected_option_number"), 1, Integer.MAX_VALUE));
    }
    @Test void malformedTypesMissingExtraAndOldVersionsAreRejected() {
        String valid = "{\"schema\":\"xar.event-option-once-claim-request/v1\",\"request_id\":\"event-option-"
                + "1".repeat(32) + "\",\"game_pid\":12345,\"episode_run_id\":\"fixture\",\"event_instance_id\":600,"
                + "\"selected_option_number\":1,\"source_program_sha256\":\"" + "a".repeat(64) + "\"}";
        assertEquals(600, EventOptionSubmissionClaim.decode(valid.getBytes(StandardCharsets.UTF_8)).identity().eventInstanceId());
        for (String bad : new String[] {valid.replace("\"event_instance_id\":600", "\"event_instance_id\":true"),
                valid.replace("\"event_instance_id\":600", "\"event_instance_id\":600.0"),
                valid.replace("\"event_instance_id\":600", "\"event_instance_id\":null"),
                valid.replace("\"selected_option_number\":1,", ""),
                valid.replace("\"game_pid\":12345", "\"game_pid\":\"12345\""),
                valid.replace("request/v1", "request/v0"), valid.substring(0, valid.length() - 1) + ",\"extra\":true}"}) {
            assertThrows(IllegalArgumentException.class,
                    () -> EventOptionSubmissionClaim.decode(bad.getBytes(StandardCharsets.UTF_8)));
        }
    }
}
