package org.xar.ck3.control.g2.client;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.time.Instant;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Compact strict summary only; original request/result tokens stay in existing G2Wire. */
public final class G2ClientBatchWire {
    public static final String SCHEMA = "xar.g2-client-batch-summary/v1";
    private static final Set<String> FIELDS = Set.of("schema", "machine_id", "started_at_utc", "finished_at_utc", "elapsed_nanos",
            "stop", "submitted_requests", "verified_responses", "consumed_responses", "last_request_id", "client_failure_reason");
    private G2ClientBatchWire() { }

    public static byte[] encode(G2ClientBatchSession.Summary summary) {
        ObjectNode row = StrictJson.object();
        row.put("schema", SCHEMA);
        row.put("machine_id", summary.machineId());
        row.put("started_at_utc", summary.startedAtUtc().toString());
        row.put("finished_at_utc", summary.finishedAtUtc().toString());
        row.put("elapsed_nanos", Long.toString(summary.elapsedNanos()));
        row.put("stop", summary.stop().name());
        row.put("submitted_requests", summary.submittedRequests());
        row.put("verified_responses", summary.verifiedResponses());
        row.put("consumed_responses", summary.consumedResponses());
        if (summary.lastRequestId().isPresent()) row.put("last_request_id", summary.lastRequestId().orElseThrow());
        else row.putNull("last_request_id");
        if (summary.clientFailureReason().isPresent()) row.put("client_failure_reason", summary.clientFailureReason().orElseThrow().name());
        else row.putNull("client_failure_reason");
        return StrictJson.canonical(row);
    }

    public static G2ClientBatchSession.Summary decode(byte[] raw) {
        ObjectNode row = StrictJson.object(StrictJson.parse(raw), FIELDS);
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))), "batch summary schema mismatch");
        String nanos = StrictJson.text(row.get("elapsed_nanos"));
        StrictJson.require(nanos.matches("0|[1-9][0-9]{0,18}"), "canonical nonnegative decimal nanoseconds required");
        return new G2ClientBatchSession.Summary(
                StrictJson.text(row.get("machine_id")),
                Instant.parse(StrictJson.utc(StrictJson.text(row.get("started_at_utc")))),
                Instant.parse(StrictJson.utc(StrictJson.text(row.get("finished_at_utc")))),
                Long.parseLong(nanos), G2ClientBatchSession.Stop.valueOf(StrictJson.text(row.get("stop"))),
                Math.toIntExact(StrictJson.integer(row.get("submitted_requests"), 0, G2ClientBatchSession.MAX_REQUESTS)),
                Math.toIntExact(StrictJson.integer(row.get("verified_responses"), 0, G2ClientBatchSession.MAX_REQUESTS)),
                Math.toIntExact(StrictJson.integer(row.get("consumed_responses"), 0, G2ClientBatchSession.MAX_REQUESTS)),
                nullableText(row.get("last_request_id")), nullableText(row.get("client_failure_reason")).map(G2ClientException.Reason::valueOf));
    }

    private static Optional<String> nullableText(JsonNode value) {
        return value.isNull() ? Optional.empty() : Optional.of(StrictJson.text(value));
    }
}
