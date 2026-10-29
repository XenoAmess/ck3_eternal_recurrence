package org.xar.ck3.control.wave2.events.eventoutcome;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Produces an intent document only. The original Native writer must create/fsync/read it before submitting. */
public final class EventOptionSubmissionClaim {
    public static final int MAXIMUM_BYTES = 16_384;
    public static final String REQUEST_SCHEMA = "xar.event-option-once-claim-request/v1";
    public static final String CLAIM_SCHEMA = "xar.native-event-option-once-claim/v1";
    private EventOptionSubmissionClaim() { }

    public record Identity(long gamePid, String episodeRunId, int eventInstanceId) {
        public Identity {
            StrictJson.require(gamePid > 0 && gamePid <= 0xffff_ffffL, "actual native Game PID required");
            StrictJson.text(episodeRunId);
            StrictJson.require(episodeRunId.length() <= 256 && eventInstanceId > 0, "bounded actual episode/event identity required");
        }
    }

    public record Request(String requestId, Identity identity, int selectedOptionNumber, String sourceProgramSha256) {
        public Request {
            StrictJson.text(requestId); Objects.requireNonNull(identity, "identity");
            StrictJson.require(requestId.matches("event-option-[0-9a-f]{32}"), "original event submission request identity required");
            StrictJson.require(selectedOptionNumber > 0, "positive public native option number required");
            StrictJson.require(sourceProgramSha256 != null && sourceProgramSha256.matches("[0-9a-f]{64}"),
                    "qualified Java producer program SHA-256 required");
        }
    }

    /** Raw authored document text is preserved by the original mechanical writer. It is not an issued claim. */
    public record Document(String claimKey, String claimDocumentJson) {
        public Document {
            StrictJson.require(claimKey != null && claimKey.matches("[0-9a-f]{64}"), "canonical native claim key required");
            StrictJson.text(claimDocumentJson);
            ObjectNode claim = StrictJson.object(StrictJson.parse(claimDocumentJson.getBytes(StandardCharsets.UTF_8), MAXIMUM_BYTES),
                    Set.of("schema", "request_id", "identity", "selected_option_number", "source_program_sha256", "status"));
            StrictJson.require(StrictJson.text(claim.get("schema")).equals(CLAIM_SCHEMA)
                    && StrictJson.text(claim.get("status")).equals("claimed_result_unknown_no_retry"), "event claim version/state differs");
            ObjectNode identity = StrictJson.object(claim.get("identity"), Set.of("kind", "game_pid", "episode_run_id", "event_instance_id"));
            StrictJson.require(StrictJson.text(identity.get("kind")).equals("native_event_option"), "native event claim namespace differs");
            new Request(StrictJson.text(claim.get("request_id")), new Identity(
                    StrictJson.integer(identity.get("game_pid"), 1, 0xffff_ffffL), StrictJson.text(identity.get("episode_run_id")),
                    (int) StrictJson.integer(identity.get("event_instance_id"), 1, Integer.MAX_VALUE)),
                    (int) StrictJson.integer(claim.get("selected_option_number"), 1, Integer.MAX_VALUE),
                    StrictJson.text(claim.get("source_program_sha256")));
            StrictJson.require(claimKey.equals(sha256(StrictJson.canonical(identity, MAXIMUM_BYTES))), "event claim key/document identity differs");
            StrictJson.require(claimDocumentJson.equals(new String(StrictJson.canonical(claim, MAXIMUM_BYTES), StandardCharsets.UTF_8) + "\n"),
                    "canonical authored event claim bytes required");
        }
    }

    public static Request decode(byte[] raw) {
        ObjectNode root = StrictJson.object(StrictJson.parse(raw, MAXIMUM_BYTES), Set.of(
                "schema", "request_id", "game_pid", "episode_run_id", "event_instance_id",
                "selected_option_number", "source_program_sha256"));
        StrictJson.require(StrictJson.text(root.get("schema")).equals(REQUEST_SCHEMA), "event claim request version differs");
        Identity identity = new Identity(StrictJson.integer(root.get("game_pid"), 1, 0xffff_ffffL),
                StrictJson.text(root.get("episode_run_id")),
                (int) StrictJson.integer(root.get("event_instance_id"), 1, Integer.MAX_VALUE));
        return new Request(StrictJson.text(root.get("request_id")), identity,
                (int) StrictJson.integer(root.get("selected_option_number"), 1, Integer.MAX_VALUE),
                StrictJson.text(root.get("source_program_sha256")));
    }

    public static Document prepare(Request request) {
        Objects.requireNonNull(request, "request");
        ObjectNode identity = StrictJson.object();
        // Neither source/option/request changes nor a pipe reconnect can reopen the same native event.
        identity.put("kind", "native_event_option");
        identity.put("game_pid", request.identity().gamePid());
        identity.put("episode_run_id", request.identity().episodeRunId());
        identity.put("event_instance_id", request.identity().eventInstanceId());
        String key = sha256(StrictJson.canonical(identity, MAXIMUM_BYTES));
        ObjectNode claim = StrictJson.object();
        claim.put("schema", CLAIM_SCHEMA); claim.put("request_id", request.requestId());
        claim.set("identity", identity); claim.put("selected_option_number", request.selectedOptionNumber());
        claim.put("source_program_sha256", request.sourceProgramSha256());
        // Conservative reservation predates native dispatch and is never rewritten as a native outcome.
        claim.put("status", "claimed_result_unknown_no_retry");
        return new Document(key, new String(StrictJson.canonical(claim, MAXIMUM_BYTES), StandardCharsets.UTF_8) + "\n");
    }

    public static byte[] encode(Document document) {
        Objects.requireNonNull(document, "document");
        ObjectNode result = StrictJson.object();
        result.put("claim_key", document.claimKey()); result.put("claim_document_json", document.claimDocumentJson());
        return StrictJson.canonical(result, MAXIMUM_BYTES);
    }

    private static String sha256(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException failure) { throw new IllegalStateException("SHA-256 unavailable", failure); }
    }
}
