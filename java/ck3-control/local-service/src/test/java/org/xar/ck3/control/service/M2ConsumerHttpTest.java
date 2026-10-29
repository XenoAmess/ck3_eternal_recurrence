package org.xar.ck3.control.service;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.quarkus.test.common.http.TestHTTPResource;
import io.quarkus.test.junit.QuarkusTest;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.net.URI;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Duration;
import java.util.HexFormat;
import java.util.List;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.client.G2ClientConfig;
import org.xar.ck3.control.g2.client.G2ClientException;
import org.xar.ck3.control.g2.client.G2JavaClient;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.m2.M2Payload;
import org.xar.ck3.control.g2.m2.M2Payload.Operation;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventEvidenceJson;

/** Actual shared client and Quarkus route into the mechanical plan/before/after consumers.
 * Source-reading and the original offline writer are covered by M2LifecycleIntegrationTest separately.
 * This class grants no old Python SDK, source-reviewed HTTP, action or material acceptance credit.
 */
@QuarkusTest
class M2ConsumerHttpTest {
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build());
    private static final String CORPUS = "/unhandledevent/unhandled-event-golden-v1.json.gz";
    @TestHTTPResource(G2Wire.HTTP_PATH) URI endpoint;
    @TempDir Path temporary;

    @Test void actualProducerPlanAndBeforeAfterConsumersPersistTheSameIncidentWithoutTurningAckIntoCompletion() throws Exception {
        G2Request original = G2Wire.decodeRequest(resource("/g2-http/M2.request.json", G2Wire.MAX_REQUEST_BYTES));
        assertEquals(Milestone.M2, original.milestone());
        assertEquals(Operation.EVENT_PLAN_CANDIDATE, M2Payload.decode(original.payload()).operation());
        try (G2JavaClient client = client()) {
            G2Response planned = client.evaluate(original);
            assertEquals(parse(resource("/g2-http/M2.expected-result.json", M2Payload.MAX_BYTES)), parse(planned.result().bytes()));
            ObjectNode plan = object(M2Payload.unwrapResult(planned.result()).bytes());
            ObjectNode capture = object(plan.get("unhandled_event_fallback")); ObjectNode binding = object(capture.get("binding"));
            ObjectNode plannedInput = StrictJson.object(); plannedInput.set("snapshot_id", binding.get("snapshot_id"));
            plannedInput.set("revision", binding.get("revision")); plannedInput.set("plan", plan);
            ObjectNode beforeInput = StrictJson.object(); beforeInput.put("schema", UnhandledEventEvidenceJson.BEFORE_SCHEMA);
            beforeInput.set("planned", plannedInput); beforeInput.put("incident_id", "6".repeat(32));
            beforeInput.put("captured_at_utc", original.source().observedAtUtc());
            G2Response beforeResponse = call(client, original.source(), "m2-http-before", Operation.EVENT_BEFORE, beforeInput);
            byte[] beforeRaw = M2Payload.unwrapResult(beforeResponse.result()).bytes(); ObjectNode before = object(beforeRaw);
            assertFalse(bool(before, "dispatch_attempted")); assertEquals(capture.get("window_context"), before.get("window_context"));
            Path beforePath = temporary.resolve("incident.before.json"); Files.write(beforePath, beforeRaw, StandardOpenOption.CREATE_NEW);
            ExactRef beforeRef = new ExactRef(beforePath.toString(), beforeRaw.length, sha(beforeRaw));
            ObjectNode ticket = StrictJson.object(); ticket.set("incident_id", before.get("incident_id"));
            ticket.set("current_event_instance_id", before.get("current_event_instance_id"));
            ticket.set("selected_native_option_index", object(before.get("selection")).get("native_option_index"));
            ticket.set("before", beforeRef.toJson());
            ObjectNode result = StrictJson.object(); result.put("accepted", true); result.putNull("event_selection");
            ObjectNode outcome = StrictJson.object(); outcome.put("status", "available"); outcome.set("result", result);
            ObjectNode afterInput = StrictJson.object(); afterInput.put("schema", UnhandledEventEvidenceJson.AFTER_SCHEMA);
            afterInput.set("ticket", ticket); afterInput.set("outcome", outcome); afterInput.putNull("error");
            afterInput.put("captured_at_utc", original.source().observedAtUtc());
            G2Response afterResponse = call(client, original.source(), "m2-http-after", Operation.EVENT_AFTER, afterInput);
            ObjectNode after = object(M2Payload.unwrapResult(afterResponse.result()).bytes());
            assertTrue(bool(after, "command_acknowledged"));
            assertFalse(bool(after, "event_instance_advanced_verified")); assertFalse(bool(after, "replay_allowed"));
            assertEquals(beforeRef.toJson(), after.get("before")); assertEquals(before.get("incident_id"), after.get("incident_id"));
            Path persisted = temporary.resolve("incident.after.response.json");
            Files.write(persisted, G2Wire.encodeResponse(afterResponse), StandardOpenOption.CREATE_NEW);
            G2Response reloaded = G2Wire.decodeResponse(Files.readAllBytes(persisted));
            assertEquals(afterResponse.source(), reloaded.source()); assertEquals(afterResponse.requestId(), reloaded.requestId());
            assertArrayEquals(afterResponse.result().bytes(), reloaded.result().bytes());
            assertArrayEquals(beforeRaw, Files.readAllBytes(beforePath), "response consumption cannot replace the original incident evidence");
        }
    }

    @Test void allTwentyOneOriginalPlannerInputsReachTheSameHttpConsumerWithPublicAndNativeRevisionsSeparate() throws Exception {
        byte[] packed = resource(CORPUS, 65_536); byte[] raw;
        try (var input = new GZIPInputStream(new ByteArrayInputStream(packed))) {
            raw = input.readNBytes(1_048_577); assertTrue(raw.length <= 1_048_576);
        }
        ObjectNode corpus = object(raw); JsonNode rows = corpus.get("plan_cases"); assertNotNull(rows); assertTrue(rows.isArray()); assertEquals(21, rows.size());
        URI location = M2ConsumerHttpTest.class.getResource(CORPUS).toURI();
        G2Source source = new G2Source("portable-m2-http-corpus", "2026-10-22T00:00:00Z", "1.20.0.4",
                new ExactRef(location.toString(), packed.length, sha(packed)));
        int separate = 0;
        try (G2JavaClient client = client()) {
            int index = 0;
            for (JsonNode row : rows) {
                ObjectNode request = object(row.get("request"));
                G2Response response = call(client, source, "m2-http-oracle-" + index++, Operation.EVENT_PLAN_CANDIDATE, request);
                assertEquals(row.get("expected_plan"), parse(M2Payload.unwrapResult(response.result()).bytes()), row.path("name").textValue());
                JsonNode snapshot = request.get("snapshot");
                if (snapshot != null && snapshot.isObject() && snapshot.hasNonNull("revision")
                        && !snapshot.get("revision").equals(snapshot.get("native_revision"))) separate++;
            }
        }
        assertTrue(separate > 0, "equal-revision fixtures cannot replace the original public!=native cases");
    }

    @Test void invalidNativeIntegerTypesAreVerifiedHttpDomainRefusalsWithNoConsumerFallback() throws Exception {
        G2Request original = G2Wire.decodeRequest(resource("/g2-http/M2.request.json", G2Wire.MAX_REQUEST_BYTES));
        ObjectNode input = object(M2Payload.decode(original.payload()).input().bytes()); ObjectNode snapshot = object(input.get("snapshot"));
        try (G2JavaClient client = client()) {
            for (JsonNode invalid : List.of(JSON.getNodeFactory().booleanNode(true), JSON.getNodeFactory().numberNode(7.0), JSON.getNodeFactory().textNode("7"))) {
                ObjectNode wrongSnapshot = snapshot.deepCopy(); wrongSnapshot.set("native_revision", invalid);
                ObjectNode wrongInput = input.deepCopy(); wrongInput.set("snapshot", wrongSnapshot);
                G2ClientException refused = assertThrows(G2ClientException.class,
                        () -> call(client, original.source(), "m2-http-wrong-native", Operation.EVENT_PLAN_CANDIDATE, wrongInput));
                assertEquals(G2ClientException.Reason.HTTP_REJECTED, refused.reason());
                assertEquals(G2HttpError.Code.DOMAIN_REJECTED, refused.httpError().orElseThrow().code());
                assertTrue(refused.evidence().actualHttpInvoked()); assertTrue(refused.evidence().responseComplete());
            }
        }
    }

    private G2JavaClient client() {
        return new G2JavaClient(new G2ClientConfig(URI.create("http://127.0.0.1:" + endpoint.getPort()),
                Duration.ofSeconds(20), G2Wire.MAX_RESPONSE_BYTES));
    }
    private static G2Response call(G2JavaClient client, G2Source source, String requestId, Operation operation, ObjectNode input) throws IOException {
        G2Request request = new G2Request(requestId, Milestone.M2, source,
                M2Payload.input(operation, ProjectionJson.object(JSON.writeValueAsBytes(input), M2Payload.MAX_BYTES)));
        G2Response result = client.evaluate(request); assertEquals(requestId, result.requestId());
        assertEquals(source, result.source()); assertEquals(Milestone.M2, result.milestone());
        assertEquals(operation, M2Payload.decodeResult(result.result()).operation()); return result;
    }
    private static byte[] resource(String name, int maximum) throws IOException {
        try (var input = M2ConsumerHttpTest.class.getResourceAsStream(name)) {
            if (input == null) throw new IOException("mandatory actual producer HTTP fixture missing; NOT RUN: " + name);
            byte[] raw = input.readNBytes(maximum + 1); if (raw.length == 0 || raw.length > maximum) throw new IOException("bounded actual fixture required: " + name);
            return raw;
        }
    }
    private static JsonNode parse(byte[] raw) throws IOException {
        ProjectionJson.value(raw, M2Payload.MAX_BYTES); return JSON.readTree(raw);
    }
    private static ObjectNode object(byte[] raw) throws IOException { return object(parse(raw)); }
    private static ObjectNode object(JsonNode value) throws IOException {
        if (!(value instanceof ObjectNode object)) throw new IOException("actual object fixture required"); return object;
    }
    private static boolean bool(ObjectNode object, String field) throws IOException {
        JsonNode value = object.get(field);
        if (value == null || !value.isBoolean()) throw new IOException("required boolean response field: " + field);
        return value.booleanValue();
    }
    private static String sha(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
}
