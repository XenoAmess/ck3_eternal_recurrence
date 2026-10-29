package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;
import java.util.HexFormat;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Default Maven tests consume the immutable actual Python corpus; no alternate canonical producer. */
final class RetainedCanonicalTest {
    @Test void allCapturedPythonBinary64VectorsRetainCanonicalUtf8AndBits() throws IOException {
        byte[] corpus;
        try (InputStream stream = getClass().getResourceAsStream("/typedindex/python-canonical-oracle-v1.json")) {
            if (stream == null) { throw new IOException("actual Python canonical corpus required; never skip"); }
            corpus = stream.readAllBytes();
        }
        assertEquals(184240, corpus.length);
        assertEquals("b5fe2d9ebd985d2c992dfa262ca84db25a4a39d33479bd0dcf7069f4c7da0c7e", sha256(corpus));
        JsonNode captured = StrictJson.parse(corpus, 1_048_576);
        assertEquals("xar.python-scoped-canonical-oracle/v1", captured.path("schema").textValue());
        JsonNode provider = captured.path("actual_provider");
        StrictJson.trueValue(provider.get("provider_sources_post_match"));
        assertTrue(provider.path("python_version").textValue().startsWith("3.13.2 "));
        int vectors = 0, rejected = 0;
        for (JsonNode row : provider.path("vectors")) {
            RetainedJson.Value source = RetainedJson.parse(row.path("input_json").textValue().getBytes(StandardCharsets.UTF_8));
            RetainedJson.Value scalar = row.path("kind").textValue().equals("scalar")
                    ? source : RetainedJson.object(source).get("😀");
            RetainedJson.FloatingValue floating = assertInstanceOf(RetainedJson.FloatingValue.class, scalar);
            assertEquals(Long.parseUnsignedLong(row.path("bits").textValue(), 16), Double.doubleToRawLongBits(floating.value()));
            byte[] expected = row.path("canonical_utf8").textValue().getBytes(StandardCharsets.UTF_8);
            RetainedJson.CanonicalForm actual = RetainedJson.pythonCanonical(source,
                    new RetainedJson.CanonicalBudget(expected.length, 100_000, 128));
            assertArrayEquals(expected, actual.bytes(), row.path("bits").textValue());
            assertEquals(row.path("canonical_bytes").intValue(), actual.size());
            assertEquals(row.path("canonical_sha256").textValue(), actual.sha256());
            byte[] mutableCopy = actual.bytes(); mutableCopy[0] ^= 1;
            assertArrayEquals(expected, actual.bytes());
            if (expected.length > 1) {
                assertThrows(IllegalArgumentException.class, () -> RetainedJson.pythonCanonical(source,
                        new RetainedJson.CanonicalBudget(expected.length - 1, 100_000, 128)));
                rejected++;
            }
            if (source instanceof RetainedJson.ObjectValue) {
                assertThrows(IllegalArgumentException.class, () -> RetainedJson.pythonCanonical(source,
                        new RetainedJson.CanonicalBudget(expected.length, 1, 128)));
                assertThrows(IllegalArgumentException.class, () -> RetainedJson.pythonCanonical(source,
                        new RetainedJson.CanonicalBudget(expected.length, 100_000, 0)));
                rejected += 2;
            }
            vectors++;
        }
        assertEquals(690, vectors);
        assertEquals(818, rejected);
    }

    @Test void explicitStreamingLeaseRetainsTheWholeLargeInputAndRejectsInvalidTail() {
        byte[] input = ("{\"opaque\":\"" + "x".repeat(9 << 20)
                + "\",\"identity\":\"18446744073709551615\",\"tail\":[true,null,{}]}").getBytes(StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> RetainedJson.parse(input));
        RetainedJson.ObjectValue complete = RetainedJson.object(RetainedJson.parse(input,
                new RetainedJson.ParseBudget(input.length, 7, 3)));
        assertEquals(9 << 20, RetainedJson.string(complete.get("opaque")).length());
        assertEquals("18446744073709551615", RetainedJson.string(complete.get("identity")));
        RetainedJson.ArrayValue tail = assertInstanceOf(RetainedJson.ArrayValue.class, complete.get("tail"));
        assertEquals(3, tail.values().size());
        assertInstanceOf(RetainedJson.NullValue.class, tail.values().get(1));
        assertInstanceOf(RetainedJson.ObjectValue.class, tail.values().get(2));
        assertThrows(IllegalArgumentException.class, () -> RetainedJson.parse(input,
                new RetainedJson.ParseBudget(input.length - 1, 7, 3)));
        assertThrows(IllegalArgumentException.class, () -> RetainedJson.parse(input,
                new RetainedJson.ParseBudget(input.length, 6, 3)));
        assertThrows(IllegalArgumentException.class, () -> RetainedJson.parse(input,
                new RetainedJson.ParseBudget(input.length, 7, 1)));
        byte[] invalidTail = Arrays.copyOf(input, input.length + 1); invalidTail[input.length] = (byte) 0xff;
        assertThrows(IllegalArgumentException.class, () -> RetainedJson.parse(invalidTail,
                new RetainedJson.ParseBudget(invalidTail.length, 7, 3)));
    }

    private static String sha256(byte[] value) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value)); }
        catch (NoSuchAlgorithmException error) { throw new AssertionError(error); }
    }
}
