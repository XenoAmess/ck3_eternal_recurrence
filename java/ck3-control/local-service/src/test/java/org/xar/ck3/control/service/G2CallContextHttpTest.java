package org.xar.ck3.control.service;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import io.quarkus.test.common.http.TestHTTPResource;
import io.quarkus.test.junit.QuarkusTest;
import io.quarkus.test.junit.QuarkusTestProfile;
import io.quarkus.test.junit.TestProfile;
import jakarta.inject.Inject;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Duration;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.context.G2CallContextProducer;
import org.xar.ck3.control.g2.context.G2CallContextWire;

/** Synthetic protocol coverage only: this test grants no retained-source or native qualification. */
@QuarkusTest
@TestProfile(G2CallContextHttpTest.SyntheticProviderProfile.class)
public class G2CallContextHttpTest {
    /** Separate host generation preserves production no-rebind for other default tests. */
    public static final class SyntheticProviderProfile implements QuarkusTestProfile { }
    @TestHTTPResource(G2CallContextWire.HTTP_PATH) URI endpoint;
    @Inject G2CallContextHost host;
    private final HttpClient client = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build();

    @Test void absentRootCapabilityFailsClosedAndExplicitSyntheticCapabilityBindsOnlyOriginalPayload() throws Exception {
        byte[] valid = fixture("context-input.json");
        byte[] expectedBytes = fixture("context-result.json");
        G2CallContextProducer.Context expected = G2CallContextWire.decodeContext(expectedBytes);
        assertError(post(valid), G2HttpError.Code.ENGINE_UNAVAILABLE);
        for (String raw : List.of("{}", "{\"milestone\":\"G2-M1\",\"payload\":null}",
                "{\"milestone\":true,\"payload\":{}}", "{\"milestone\":\"G2-M8\",\"payload\":{}}",
                "{\"milestone\":\"G2-M1\",\"payload\":{},\"source_ref\":\"caller-selected-root\"}",
                "{\"milestone\":\"G2-M1\",\"milestone\":\"G2-M1\",\"payload\":{}}", "{} {}")) {
            assertError(post(utf8(raw)), G2HttpError.Code.MALFORMED_REQUEST);
        }
        AtomicInteger calls = new AtomicInteger();
        G2CallContextProducer.Provider provider = (milestone, payload) -> {
            calls.incrementAndGet();
            String digest = new String(payload.bytes(), StandardCharsets.UTF_8).contains("wrong_digest")
                    ? "0".repeat(64) : sha256(payload.bytes());
            return new G2CallContextProducer.Available(new G2CallContextProducer.Context(expected.source(),
                    expected.requestId(), digest));
        };
        host.installRootProvider(provider);
        host.installRootProvider(provider);
        HttpResponse<byte[]> response = post(valid);
        assertEquals(200, response.statusCode()); headers(response);
        G2CallContextProducer.Context context = G2CallContextWire.decodeContext(response.body());
        assertEquals(expected, context);
        assertArrayEquals(expectedBytes, response.body(), "actual producer export must survive the same host protocol unchanged");
        assertEquals(sha256(G2CallContextWire.decodeInput(valid).payload().bytes()), context.payloadSha256());
        assertTrue(new String(response.body(), StandardCharsets.UTF_8).startsWith("{"));
        assertEquals(1, calls.get());
        assertError(post(utf8("{\"milestone\":\"G2-M1\",\"payload\":{\"wrong_digest\":true}}")),
                G2HttpError.Code.ENGINE_UNAVAILABLE);
        assertEquals(2, calls.get());
        assertThrows(IllegalStateException.class, () -> host.installRootProvider((milestone, payload) ->
                new G2CallContextProducer.Unavailable(G2CallContextProducer.Reason.OWNER_FAILED, "another owner")));
    }

    private HttpResponse<byte[]> post(byte[] raw) throws Exception {
        URI target = URI.create("http://127.0.0.1:" + endpoint.getPort() + G2CallContextWire.HTTP_PATH);
        return client.send(HttpRequest.newBuilder(target).timeout(Duration.ofSeconds(20))
                .header("Content-Type", "application/json").POST(HttpRequest.BodyPublishers.ofByteArray(raw)).build(),
                HttpResponse.BodyHandlers.ofByteArray());
    }

    private static void assertError(HttpResponse<byte[]> response, G2HttpError.Code expected) {
        assertEquals(expected.httpStatus(), response.statusCode()); headers(response);
        assertEquals(expected, G2Wire.decodeError(response.body()).code());
        assertFalse(new String(response.body(), StandardCharsets.UTF_8).contains("provider context does not bind"));
    }

    private static void headers(HttpResponse<byte[]> response) {
        assertEquals(G2CallContextWire.PRODUCER, response.headers().firstValue("X-Xar-Producer").orElseThrow());
        assertEquals(G2CallContextWire.PRODUCER_VERSION,
                response.headers().firstValue("X-Xar-Producer-Version").orElseThrow());
        assertEquals(G2CallContextWire.SCHEMA, response.headers().firstValue("X-Xar-Contract-Revision").orElseThrow());
    }

    private static byte[] utf8(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static byte[] fixture(String name) throws IOException {
        try (var input = G2CallContextHttpTest.class.getResourceAsStream("/g2-context/" + name)) {
            assertNotNull(input, "actual synthetic producer export required: " + name);
            byte[] raw = input.readNBytes(G2CallContextWire.MAX_INPUT_BYTES + 1);
            assertTrue(raw.length > 0 && raw.length <= G2CallContextWire.MAX_INPUT_BYTES);
            return raw;
        }
    }
    private static String sha256(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (java.security.NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
}
