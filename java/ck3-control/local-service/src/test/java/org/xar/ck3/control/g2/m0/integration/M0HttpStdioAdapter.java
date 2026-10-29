package org.xar.ck3.control.g2.m0.integration;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.util.Set;
import java.util.UUID;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.client.G2CallEvidence;
import org.xar.ck3.control.g2.client.G2ClientConfig;
import org.xar.ck3.control.g2.client.G2ClientException;
import org.xar.ck3.control.g2.client.G2Evaluation;
import org.xar.ck3.control.g2.client.G2JavaClient;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;

/** Test-only original-consumer transport through the one real shared Java HTTP client. */
public final class M0HttpStdioAdapter {
    private static final int MAXIMUM_CALLS = 1024;
    private M0HttpStdioAdapter() { }
    public static void main(String[] args) throws IOException {
        if (args.length != 1 || !args[0].equals("--stdio")) throw new IllegalArgumentException("finite --stdio test transport required");
        M0FixtureConfig config = M0FixtureConfig.fromEnvironment();
        ObjectNode row = StrictJson.object(StrictJson.parse(Files.readAllBytes(Path.of(config.httpSourceMetadata().path()))),
                Set.of("machine_id", "observed_at_utc", "exact_build", "source_ref"));
        G2Source source = new G2Source(StrictJson.text(row.get("machine_id")), StrictJson.text(row.get("observed_at_utc")),
                StrictJson.text(row.get("exact_build")), ExactRef.fromJson(row.get("source_ref")));
        String receiptLocation = System.getenv("XAR_G2_M0_HTTP_CALL_EVIDENCE");
        if (receiptLocation == null || receiptLocation.isBlank()) throw new IllegalStateException("admitted M0 HTTP evidence output missing");
        Path receiptPath = Path.of(receiptLocation).toAbsolutePath().normalize();
        if (!receiptPath.startsWith(config.outputRoot()) || Files.exists(receiptPath)) throw new IllegalArgumentException("fresh M0 HTTP evidence within admitted output root required");
        ArrayNode evidence = StrictJson.object().putArray("calls");
        int calls = 0, verified = 0, unknown = 0;
        try (G2JavaClient client = new G2JavaClient(new G2ClientConfig(config.httpBaseUri().orElseThrow(
                () -> new IllegalStateException("actual shared G2 HTTP endpoint missing")), Duration.ofSeconds(10), G2Wire.MAX_RESPONSE_BYTES))) {
            byte[] raw;
            while ((raw = readLine()) != null) {
                if (++calls > MAXIMUM_CALLS) throw new IllegalArgumentException("finite M0 HTTP call count exceeded");
                G2Request request = new G2Request("m0-consumer-http-" + UUID.randomUUID(), Milestone.M0, source,
                        ProjectionJson.object(raw, ProjectionJson.MAX_BYTES));
                byte[] result;
                try {
                    G2Evaluation evaluated = client.evaluateWithEvidence(request);
                    evidence.add(encode(evaluated.evidence())); verified++;
                    result = evaluated.response().result().bytes();
                } catch (G2ClientException failure) {
                    evidence.add(encode(failure.evidence()));
                    if (failure.reason() == G2ClientException.Reason.HTTP_REJECTED
                            && failure.httpError().orElseThrow().code() == G2HttpError.Code.DOMAIN_REJECTED) {
                        verified++;
                        ObjectNode rejected = StrictJson.object().put("rejected", true).put("message", failure.getMessage());
                        result = StrictJson.canonical(rejected, 8192);
                    } else { unknown++; throw failure; }
                }
                System.out.write(result); System.out.write('\n'); System.out.flush();
            }
        } finally {
            ObjectNode receipt = StrictJson.object(); receipt.put("schema", "xar.g2-m0-actual-http-calls/v1");
            boolean actualHttp = calls > 0 && evidence.size() == calls;
            for (var value : evidence) actualHttp &= value.path("actual_http_invoked").isBoolean() && value.path("actual_http_invoked").booleanValue();
            receipt.put("machine_id", source.machineId()); receipt.put("actual_http", actualHttp);
            receipt.put("calls", calls); receipt.put("verified_responses", verified); receipt.put("unknown", unknown);
            receipt.set("call_evidence", evidence); receipt.put("action_submitted", false); receipt.put("game_completion_credit", 0);
            config.verify();
            Files.write(receiptPath, StrictJson.canonical(receipt, 131_072), StandardOpenOption.CREATE_NEW);
        }
    }
    private static ObjectNode encode(G2CallEvidence value) {
        ObjectNode row = StrictJson.object(); row.put("request_id", value.requestId()); row.put("endpoint", value.endpoint().toString());
        row.put("started_at_utc", value.startedAtUtc().toString()); row.put("completed_at_utc", value.completedAtUtc().toString());
        row.put("elapsed_nanos", Long.toString(value.elapsedNanos())); row.put("request_bytes", value.requestBytes());
        row.put("request_sha256", value.requestSha256()); row.put("response_bytes", value.observedResponseBytes());
        row.put("response_sha256", value.retainedResponseSha256()); row.put("response_complete", value.responseComplete());
        row.put("actual_http_invoked", value.actualHttpInvoked());
        if (value.httpStatus().isPresent()) row.put("http_status", value.httpStatus().getAsInt()); else row.putNull("http_status");
        return row;
    }
    private static byte[] readLine() throws IOException {
        ByteArrayOutputStream line = new ByteArrayOutputStream();
        for (int value; (value = System.in.read()) != -1;) {
            if (value == '\n') return line.toByteArray();
            if (line.size() >= ProjectionJson.MAX_BYTES) throw new IllegalArgumentException("finite M0 semantic input required");
            line.write(value);
        }
        return line.size() == 0 ? null : line.toByteArray();
    }
}
