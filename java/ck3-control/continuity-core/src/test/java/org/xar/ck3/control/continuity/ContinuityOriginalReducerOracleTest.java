package org.xar.ck3.control.continuity;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;

/** Captured original pure reducer calls from preserved small metadata; no consumer/SDK credit. */
class ContinuityOriginalReducerOracleTest {
    @Test void actualProducerMatchesCapturedOriginalReducerAndSerialization() throws IOException {
        ObjectNode fixture;
        try (InputStream compressed = getClass().getResourceAsStream("/original-reducer-calls-v2.json.gz")) {
            assertNotNull(compressed, "actual original reducer capture must exist; no skip");
            try (InputStream in = new GZIPInputStream(compressed)) {
                byte[] raw = in.readNBytes(1_048_577);
                fixture = ContinuityJson.object(org.xar.ck3.control.contracts.StrictJson.parse(raw, 1_048_576));
            }
        }
        assertEquals("xar.continuity-original-reducer-delta-calls/v2", fixture.get("schema").textValue());
        assertTrue(fixture.get("cases").isArray()); assertEquals(7, fixture.get("cases").size());
        assertTrue(fixture.get("float_cases").isArray()); assertTrue(fixture.get("float_cases").size() >= 100);
        for (var value : fixture.get("float_cases")) {
            byte[] raw = value.textValue().getBytes(StandardCharsets.UTF_8);
            assertArrayEquals(raw, ContinuityJson.canonical(ContinuityJson.parseObject(raw, 65_536)));
        }
        ObjectNode documents = ContinuityJson.object(fixture.get("documents"));
        ObjectNode requestBase = JsonNodeFactory.instance.objectNode();
        fixture.get("base_request_fields").properties().forEach(field ->
            requestBase.set(field.getKey(), document(documents, field.getValue())));
        ObjectNode responseBase = ContinuityJson.object(document(documents, fixture.get("base_response_document")));
        int matches = 0;
        for (var entry : fixture.get("cases")) {
            ObjectNode row = ContinuityJson.object(entry);
            byte[] request = ContinuityJson.canonical(apply(requestBase, row.get("request_patch")), ContinuityJson.TRANSPORT_MAX_BYTES);
            assertEquals(row.get("request_sha256").textValue(), sha256(request)); matches++;
            if (row.get("rejected").booleanValue()) {
                assertThrows(IllegalArgumentException.class, () -> SavedContinuityAttachment.reduce(request));
            } else {
                byte[] actual = SavedContinuityAttachment.reduce(request);
                byte[] expected = ContinuityJson.canonical(apply(responseBase, row.get("response_patch")));
                assertEquals(row.get("response_sha256").textValue(), sha256(expected)); matches++;
                assertArrayEquals(expected, actual);
            }
        }
        assertEquals(11, matches);
        assertEquals(matches, fixture.get("decoded_request_response_byte_matches").intValue());
    }

    private static JsonNode document(ObjectNode documents, JsonNode key) {
        assertTrue(key.isTextual()); JsonNode value = documents.get(key.textValue());
        assertNotNull(value); assertTrue(value.isTextual());
        byte[] raw = value.textValue().getBytes(StandardCharsets.UTF_8);
        assertEquals(key.textValue(), sha256(raw));
        return value(value.textValue());
    }

    private static JsonNode value(String json) {
        return ContinuityJson.parseObject(("{\"v\":" + json + "}").getBytes(StandardCharsets.UTF_8), 262_144).get("v");
    }

    /** Generic lossless fixture codec; does not implement any continuity transition. */
    private static ObjectNode apply(ObjectNode base, JsonNode patches) {
        assertTrue(patches.isArray()); ObjectNode result = base.deepCopy();
        for (JsonNode patch : patches) {
            JsonNode path = patch.get("path"); assertTrue(path.isArray()); assertFalse(path.isEmpty());
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
                default -> fail("unknown fixture operation");
            }
        }
        return result;
    }

    private static String sha256(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }
}
