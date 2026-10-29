package org.xar.ck3.control.service;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.quarkus.test.common.http.TestHTTPResource;
import io.quarkus.test.junit.QuarkusTest;
import java.io.InputStream;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Duration;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.SavedContinuityAttachment;
import org.xar.ck3.control.contracts.StrictJson;

/** Original captured pure calls over the existing host; no SDK, writer or live qualification. */
@QuarkusTest
class SavedContinuityHttpTest {
    @TestHTTPResource("/v1/continuity/saved-attachment") URI endpoint;

    @Test void originalAcceptedAndRejectedCallsCrossActualHttpWithExactResponseBytes() throws Exception {
        ObjectNode fixture = fixture();
        ObjectNode documents = ContinuityJson.object(fixture.get("documents"));
        ObjectNode requests = StrictJson.object();
        fixture.get("base_request_fields").properties().forEach(field ->
                requests.set(field.getKey(), document(documents, field.getValue())));
        ObjectNode responses = ContinuityJson.object(document(documents, fixture.get("base_response_document")));
        int accepted = 0;
        int rejected = 0;
        try (HttpClient client = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10))
                .followRedirects(HttpClient.Redirect.NEVER).build()) {
            for (JsonNode row : fixture.get("cases")) {
                byte[] request = ContinuityJson.canonical(apply(requests, row.get("request_patch")),
                        ContinuityJson.TRANSPORT_MAX_BYTES);
                assertEquals(row.get("request_sha256").textValue(), sha256(request));
                HttpResponse<byte[]> response = post(client, request);
                identified(response);
                if (row.get("rejected").booleanValue()) {
                    assertEquals(400, response.statusCode());
                    assertEquals("rejected", StrictJson.parse(response.body()).get("status").textValue());
                    rejected++;
                } else {
                    byte[] expected = ContinuityJson.canonical(apply(responses, row.get("response_patch")));
                    assertEquals(row.get("response_sha256").textValue(), sha256(expected));
                    assertEquals(200, response.statusCode());
                    assertArrayEquals(expected, response.body(),
                            "The original response must preserve pending/UNKNOWN and zero credit byte-for-byte");
                    accepted++;
                }
            }
        }
        assertEquals(4, accepted);
        assertEquals(3, rejected);
    }

    @Test void malformedContractAndExcessiveContinuityRoleAreTypedHttpRefusals() throws Exception {
        byte[] oversized = new byte[ContinuityJson.TRANSPORT_MAX_BYTES + 1];
        Arrays.fill(oversized, (byte) ' ');
        try (HttpClient client = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10))
                .followRedirects(HttpClient.Redirect.NEVER).build()) {
            for (byte[] body : new byte[][] {
                    "{\"schema\":true}".getBytes(StandardCharsets.UTF_8),
                    "{\"schema\":\"wrong\"}".getBytes(StandardCharsets.UTF_8), oversized }) {
                HttpResponse<byte[]> response = post(client, body);
                assertEquals(400, response.statusCode());
                identified(response);
                JsonNode error = StrictJson.parse(response.body());
                assertEquals("xar.java-contract-error/v1", error.get("schema").textValue());
                assertEquals("rejected", error.get("status").textValue());
            }
        }
    }

    private HttpResponse<byte[]> post(HttpClient client, byte[] body) throws Exception {
        HttpRequest request = HttpRequest.newBuilder(endpoint).timeout(Duration.ofSeconds(20))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofByteArray(body)).build();
        return client.send(request, HttpResponse.BodyHandlers.ofByteArray());
    }

    private static void identified(HttpResponse<byte[]> response) {
        assertEquals(SavedContinuityResource.PRODUCER,
                response.headers().firstValue("X-Xar-Producer").orElseThrow());
        assertEquals(SavedContinuityAttachment.REQUEST_SCHEMA,
                response.headers().firstValue("X-Xar-Contract-Revision").orElseThrow());
    }

    private static ObjectNode fixture() throws Exception {
        try (InputStream compressed = SavedContinuityHttpTest.class
                .getResourceAsStream("/original-reducer-calls-v2.json.gz")) {
            assertNotNull(compressed, "original producer fixture is mandatory; never skip or synthesize");
            try (InputStream in = new GZIPInputStream(compressed)) {
                ObjectNode value = ContinuityJson.object(StrictJson.parse(in.readNBytes(1_048_577), 1_048_576));
                assertEquals("xar.continuity-original-reducer-delta-calls/v2", value.get("schema").textValue());
                assertEquals(7, value.get("cases").size());
                return value;
            }
        }
    }

    private static JsonNode document(ObjectNode documents, JsonNode key) {
        assertTrue(key.isTextual());
        JsonNode value = documents.get(key.textValue());
        assertNotNull(value);
        assertTrue(value.isTextual());
        byte[] raw = value.textValue().getBytes(StandardCharsets.UTF_8);
        assertEquals(key.textValue(), sha256(raw));
        return value(value.textValue());
    }

    private static JsonNode value(String json) {
        return ContinuityJson.parseObject(("{\"v\":" + json + "}").getBytes(StandardCharsets.UTF_8),
                ContinuityJson.TRANSPORT_MAX_BYTES).get("v");
    }

    /** Only the lossless captured-fixture codec; no transition or expected result is recalculated. */
    private static ObjectNode apply(ObjectNode base, JsonNode patches) {
        assertTrue(patches.isArray());
        ObjectNode result = base.deepCopy();
        for (JsonNode patch : patches) {
            JsonNode path = patch.get("path");
            assertTrue(path.isArray());
            assertFalse(path.isEmpty());
            ObjectNode parent = result;
            for (int index = 0; index < path.size() - 1; index++) {
                assertTrue(path.get(index).isTextual());
                parent = ContinuityJson.object(parent.get(path.get(index).textValue()));
            }
            assertTrue(path.get(path.size() - 1).isTextual());
            String key = path.get(path.size() - 1).textValue();
            switch (patch.get("op").textValue()) {
                case "SET" -> parent.set(key, value(patch.get("value_json").textValue()));
                case "REMOVE" -> assertNotNull(parent.remove(key));
                default -> fail("unknown original fixture operation");
            }
        }
        return result;
    }

    private static String sha256(byte[] raw) {
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));
        } catch (NoSuchAlgorithmException error) {
            throw new IllegalStateException(error);
        }
    }
}
