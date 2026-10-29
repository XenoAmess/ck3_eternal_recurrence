package org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.religion.PlayerReligionContext.Build;

/** Original C++ packet subtrees passed through the pinned Python normalizers, not game evidence. */
final class ReligionReformDraftPythonParityTest {
    private static final String CORPUS = "/org/xar/ck3/control/religion/religion-reform-draft-parity14.json";
    private static final String SHA256 = "8d6e0d167e1082a7a8980b9332e4b2289d93f9595184f577b177a347ee992ffa";

    @Test void allSixOriginalReadTreesPreservePartialValuesAndRejectMalformedSchemas() throws Exception {
        byte[] bytes;
        try (InputStream input = getClass().getResourceAsStream(CORPUS)) {
            assertNotNull(input, "original producer/Python oracle corpus is required");
            bytes = input.readAllBytes();
        }
        assertEquals(SHA256, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        JsonNode corpus = StrictJson.parse(bytes, 262144);
        assertEquals("xar.religion-reform-draft.python-oracle/v1", corpus.path("schema").textValue());
        int values = 0;
        int rejects = 0;
        for (JsonNode item : corpus.path("cases")) {
            String name = item.path("name").textValue();
            var kind = ReligionDoctrineDraftReads.Kind.valueOf(item.path("kind").textValue());
            Build build = switch (item.path("build").textValue()) {
                case "1.20.0.2" -> Build.CROZIER2;
                case "1.20.0.3" -> Build.CROZIER3;
                case "1.20.0.4" -> Build.CROZIER4;
                default -> throw new IllegalArgumentException("unmapped original fixture build");
            };
            var frame = new ReligionTemporalFinance.Frame(build, BigInteger.valueOf(702), BigInteger.valueOf(701),
                    new BigInteger(item.path("date").textValue()), new BigInteger(item.path("actor").textValue()),
                    1234L, BigInteger.ONE, "offline:original-draft-packet", "offline:original-draft-parity");
            assertTrue(item.path("value").isObject(), name);
            ObjectNode input = (ObjectNode) item.path("value");
            ObjectNode before = input.deepCopy();
            if (item.path("accepted").booleanValue()) {
                ObjectNode result = ReligionReformDraftValidation.normalize(kind, input, frame);
                assertNotSame(input, result, name);
                assertEquals(input, result, name);
                assertEquals(result, StrictJson.parse(result.toString().getBytes(StandardCharsets.UTF_8), 262144), name);
                values++;
            } else {
                assertThrows(IllegalArgumentException.class,
                        () -> ReligionReformDraftValidation.normalize(kind, input, frame), name);
                rejects++;
            }
            assertEquals(before, input, name + " must retain the original native tree");
        }
        assertEquals(20, values);
        assertEquals(24, rejects);
    }
}
