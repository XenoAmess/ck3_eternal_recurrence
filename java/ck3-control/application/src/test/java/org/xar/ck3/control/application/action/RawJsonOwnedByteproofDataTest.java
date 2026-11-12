package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;
import java.util.List;
import java.util.function.Supplier;
import org.junit.jupiter.api.Test;

/** Public API differential DATA against the exact frozen whole legacy class; no new-proof algorithm is copied. */
final class RawJsonOwnedByteproofDataTest {
    @Test void utf8LiteralAndEscapedDocumentsMatchBothLegacyProfilesAndAllPublicMethods() {
        String slash = Character.toString((char)92);
        String escape = slash + "u";
        String bmp = Character.toString((char)0x6c49) + Character.toString((char)0x5b57);
        String emoji = new String(Character.toChars(0x1f600));
        List<String> documents = List.of(
                "{\"plain\":\"ASCII\",\"number\":-0.00e+03,\"array\":[true,false,null,7]}",
                "{\"" + bmp + "\":\"" + bmp + "\"}",
                "{\"" + emoji + "\":\"" + emoji + "\"}",
                "{\"" + escape + "D83D" + escape + "DE00\":\"" + escape + "D83D" + escape + "DE00\"}",
                "{\"" + escape + "0061\":\"" + escape + "0000\"}",
                "{\"literal\":\"" + slash + slash + "uD800\",\"" + slash + slash + "uDC00\":12}",
                "{\"escaped\":\"" + slash + "n" + slash + "t" + slash + Character.toString((char)34) + slash + slash + "\"}",
                "[\"" + emoji + "\",{\"nested\":\"" + bmp + "\"},0]",
                "{\"long\":\"" + "x".repeat(8193) + "\"}",
                "{\"long\":\"" + "x".repeat(8193) + slash + "n" + "\"}",
                "\"text\"", "123", "1.2300e+004", "true", "false", "null", " { } \r\n");
        for (String document : documents) {
            byte[] raw = utf8(document);
            byte[] before = raw.clone();
            assertAccepted(raw, false); assertAccepted(raw, true);
            assertArrayEquals(before, raw);
        }
    }

    @Test void malformedUtf8EscapesUnicodeTokensAndFailureCausesMatchWholeLegacy() {
        String slash = Character.toString((char)92);
        String escape = slash + "u";
        List<String> documents = List.of(
                "\"" + escape + "D800\"", "\"" + escape + "DC00\"",
                "{\"" + escape + "D800\":0}", "{\"" + escape + "DC00\":0}",
                "\"" + escape + "D800x\"", "\"" + escape + "DC00" + escape + "D800\"",
                "\"" + slash + "q\"", "\"" + escape + "123x\"", "\"" + escape + "12\"",
                "\"" + "x".repeat(8193),
                "{\"long\":\"" + "x".repeat(8193) + slash + "q\"}",
                "\"unterminated", "{\"a\":\"unterminated", "{", "[", "[1,", "{\"a\":}",
                "{\"duplicate\":1,\"duplicate\":2}", "{\"a\":0,\"" + escape + "0061\":1}",
                "{} []", "true false", "01", "-", "1e", "1.", "[true,,false]",
                "{\"control\":\"x" + Character.toString((char)1) + "y\"}",
                "{\"nul\":\"x" + Character.toString((char)0) + "y\"}");
        for (String document : documents) {
            byte[] raw = utf8(document); byte[] before = raw.clone();
            assertRejected(raw, false); assertRejected(raw, true);
            assertArrayEquals(before, raw);
        }
        for (byte[] raw : List.of(
                new byte[] {'{', (byte)0xff},
                new byte[] {'"', (byte)0xc0, (byte)0xaf, '"'},
                new byte[] {'"', (byte)0xed, (byte)0xa0, (byte)0x80, '"'},
                new byte[] {'"', (byte)0xe2, '"'},
                new byte[] {'{', '"', 'x', '"', ':', '?', (byte)0xff, '}'})) {
            assertRejected(raw, false); assertRejected(raw, true);
            var old = capture(() -> new LegacyRawJson(raw));
            var actual = capture(() -> new RawJson(raw));
            assertEquals("invalid UTF-8/duplicate/token Native JSON", old.error().getMessage());
            assertInstanceOf(java.nio.charset.CharacterCodingException.class, old.error().getCause());
            assertThrowableData(old.error(), actual.error());
        }
    }

    @Test void nulAndOriginalUtf16Utf32AutodetectionRetainExactlyTheLegacyDomain() {
        String document = "{\"original\":\"ascii\",\"array\":[1,true,null],\"tail\":0}";
        for (int width : new int[] {2, 4}) for (boolean little : new boolean[] {false, true}) {
            byte[] raw = wideAscii(document, width, little); byte[] before = raw.clone();
            assertAccepted(raw, false); assertAccepted(raw, true);
            assertArrayEquals(before, raw);
        }
        // Preserve the exact six-byte counterexample. Its whole legacy exception
        // chain, including an earlier parser rejection, determines the expected result.
        byte[] originalCounterexample = new byte[] {0x00,0x22,(byte)0xd8,(byte)0xbc,0x00,0x22};
        assertRejected(originalCounterexample, false); assertRejected(originalCounterexample, true);
        for (byte[] raw : List.of(new byte[] {0}, new byte[] {0,0,0},
                new byte[] {'"',0,'"'}, new byte[] {0,'{',0},
                new byte[] {0,0,(byte)0xff,'{'})) {
            assertRejected(raw, false); assertRejected(raw, true);
        }
    }

    @Test void protocolNumberAndDepthLimitsRemainIndependentOfTheFullMaterialProfile() {
        byte[] at = utf8("7".repeat(4300));
        byte[] above = utf8("7".repeat(4301));
        byte[] wider = utf8("{\"large\":" + "7".repeat(8000) + "}");
        assertAccepted(at, false); assertAccepted(at, true);
        assertRejected(above, false); assertAccepted(above, true);
        assertRejected(wider, false); assertAccepted(wider, true);
        assertThrows(IllegalArgumentException.class, () -> RawJson.fullMaterial(above).requireProtocolBound());
        assertThrows(IllegalArgumentException.class, () -> RawJson.fullMaterial(wider).requireProtocolBound());
        byte[] maximumDepth = utf8("[".repeat(1000) + "0" + "]".repeat(1000));
        byte[] excessiveDepth = utf8("[".repeat(1001) + "0" + "]".repeat(1001));
        assertAccepted(maximumDepth, false); assertAccepted(maximumDepth, true);
        assertRejected(excessiveDepth, false); assertRejected(excessiveDepth, true);
    }

    @Test void rawInputsGetterCopiesEqualityAndObjectFieldNamesRetainPublicOwnership() {
        byte[] raw = utf8("{\"ordered\":1,\"second\":{\"x\":2}}"); byte[] before = raw.clone();
        var old = new LegacyRawJson(raw); var actual = new RawJson(raw);
        var oldFull = LegacyRawJson.fullMaterial(raw); var actualFull = RawJson.fullMaterial(raw);
        assertTrue(old.equals(oldFull)); assertTrue(actual.equals(actualFull));
        assertEquals(old.hashCode(), actual.hashCode());
        assertEquals(Set.of("ordered", "second"), actual.objectFieldNames());
        assertPublicData(old, actual, before); assertPublicData(oldFull, actualFull, before);
        Arrays.fill(raw, (byte)0);
        assertArrayEquals(before, old.bytes()); assertArrayEquals(before, actual.bytes());
        byte[] oldReturned = old.bytes(); byte[] actualReturned = actual.bytes();
        Arrays.fill(oldReturned, (byte)0); Arrays.fill(actualReturned, (byte)0);
        assertPublicData(old, actual, before);
        assertFalse(old.contentEquals(null)); assertFalse(actual.contentEquals(null));
        assertFalse(old.contentEquals(new byte[0])); assertFalse(actual.contentEquals(new byte[0]));
        assertFalse(old.equals(new Object())); assertFalse(actual.equals(new Object()));
        assertFalse(old.equals(null)); assertFalse(actual.equals(null));
        assertFalse(old.equals(new LegacyRawJson(utf8("{}"))));
        assertFalse(actual.equals(new RawJson(utf8("{}"))));
        assertThrows(UnsupportedOperationException.class, () -> actual.objectFieldNames().clear());
    }

    @Test void nullEmptyAndOneOversizeArrayRejectBeforeAnyTokenInterpretation() {
        assertRejected(null, false); assertRejected(null, true);
        assertRejected(new byte[0], false); assertRejected(new byte[0], true);
        assertEquals(64 * 1024 * 1024, RawJson.MAXIMUM_BYTES);
        // One finite MAX+1 array only; all four constructors reject before clone/parser.
        // No accepted 64MiB document, duplicate huge arrays or large parsed tree is created.
        byte[] oversized = new byte[RawJson.MAXIMUM_BYTES + 1];
        assertRejected(oversized, false); assertRejected(oversized, true);
    }

    private static void assertAccepted(byte[] raw, boolean full) {
        Outcome old = capture(() -> full ? LegacyRawJson.fullMaterial(raw) : new LegacyRawJson(raw));
        assertNull(old.error(), "legacy fixture must actually be accepted");
        Outcome actual = capture(() -> full ? RawJson.fullMaterial(raw) : new RawJson(raw));
        assertThrowableData(old.error(), actual.error());
        assertPublicData((LegacyRawJson)old.value(), (RawJson)actual.value(), raw);
    }
    private static void assertRejected(byte[] raw, boolean full) {
        Outcome old = capture(() -> full ? LegacyRawJson.fullMaterial(raw) : new LegacyRawJson(raw));
        assertNotNull(old.error(), "legacy fixture must actually be rejected");
        Outcome actual = capture(() -> full ? RawJson.fullMaterial(raw) : new RawJson(raw));
        assertThrowableData(old.error(), actual.error());
    }
    private static void assertPublicData(LegacyRawJson old, RawJson actual, byte[] original) {
        assertArrayEquals(original, old.bytes()); assertArrayEquals(old.bytes(), actual.bytes());
        assertEquals(old.hashCode(), actual.hashCode());
        assertEquals(old.contentEquals(original), actual.contentEquals(original));
        assertTrue(actual.contentEquals(original));
        assertEquals(old.equals(LegacyRawJson.fullMaterial(original)), actual.equals(RawJson.fullMaterial(original)));
        assertOutcomeData(capture(old::objectFieldNames), capture(actual::objectFieldNames));
        assertOutcomeData(capture(() -> { old.requireProtocolBound(); return null; }),
                capture(() -> { actual.requireProtocolBound(); return null; }));
    }
    private static Outcome capture(Supplier<?> operation) {
        try { return new Outcome(operation.get(), null); }
        catch (RuntimeException failure) { return new Outcome(null, failure); }
    }
    private static void assertOutcomeData(Outcome old, Outcome actual) {
        assertThrowableData(old.error(), actual.error());
        if (old.error() == null) assertEquals(old.value(), actual.value());
    }
    private static void assertThrowableData(Throwable old, Throwable actual) {
        if (old == null) { assertNull(actual); return; }
        assertNotNull(actual); assertEquals(old.getClass(), actual.getClass());
        assertEquals(old.getMessage(), actual.getMessage());
        assertEquals(old.getSuppressed().length, actual.getSuppressed().length);
        for (int i = 0; i < old.getSuppressed().length; i++)
            assertThrowableData(old.getSuppressed()[i], actual.getSuppressed()[i]);
        assertThrowableData(old.getCause(), actual.getCause());
    }
    private static byte[] utf8(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static byte[] wideAscii(String value, int width, boolean little) {
        byte[] raw = new byte[value.length() * width];
        for (int i = 0; i < value.length(); i++) {
            int ch = value.charAt(i); assertTrue(ch < 128);
            raw[i * width + (little ? 0 : width - 1)] = (byte)ch;
        }
        return raw;
    }
    private record Outcome(Object value, RuntimeException error) { }

    // Exact whole5905 legacy algorithm below. Only the enclosing/class self-name and
    // indentation are changed; the frozen original is retained beside this Test.
    private static final class LegacyRawJson {
        public static final int MAXIMUM_BYTES = 64 * 1024 * 1024;
        private static final JsonFactory FACTORY = factory(4300);
        private static final JsonFactory MATERIAL_FACTORY = factory(MAXIMUM_BYTES);
        private static JsonFactory factory(int maximumNumberLength) {
            return JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
                    .streamReadConstraints(StreamReadConstraints.builder().maxStringLength(MAXIMUM_BYTES)
                            .maxNumberLength(maximumNumberLength).maxNestingDepth(1000).build()).build();
        }
        private final byte[] bytes;
        private final JsonFactory factory;
        /** Original Native/public token lane; its existing 4300 digit bound is unchanged. */
        public LegacyRawJson(byte[] input) { this(input,FACTORY); }
        /** Complete Driver/auxiliary material only. Role-specific decoding and source qualification remain mandatory. */
        public static LegacyRawJson fullMaterial(byte[] input) { return new LegacyRawJson(input,MATERIAL_FACTORY); }
        private LegacyRawJson(byte[] input,JsonFactory actualFactory) {
            factory=actualFactory;
            if (input == null || input.length < 1 || input.length > MAXIMUM_BYTES) throw new IllegalArgumentException("bounded original Native token required");
            bytes = input.clone();
            try {
                boolean ascii = true;
                for (byte value : bytes) {
                    if (value < 0) { ascii = false; break; }
                }
                // All nonnegative bytes are valid UTF-8; the original byte parser still validates JSON.
                if (!ascii) StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                        .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes));
                validateDocument(factory);
            } catch (IOException error) { throw new IllegalArgumentException("invalid UTF-8/duplicate/token Native JSON", error); }
        }
        public byte[] bytes() { return bytes.clone(); }
        /** Explicit complete material cannot bypass the original Native/public protocol number bound. */
        public void requireProtocolBound() {
            if(factory==FACTORY)return;
            try { validateDocument(FACTORY); }
            catch(IOException error) { throw new IllegalArgumentException("complete material exceeds the original Native token contract",error); }
        }
        private void validateDocument(JsonFactory actualFactory)throws IOException {
            try(JsonParser parser=actualFactory.createParser(bytes)) {
                if(parser.nextToken()==null)throw new IOException("JSON value required");
                validate(parser);
                if(parser.nextToken()!=null)throw new IOException("trailing Native JSON value");
            }
        }
        /** Validates object shape without exposing an untyped Java map to producers or consumers. */
        public Set<String> objectFieldNames() {
            try (JsonParser parser = factory.createParser(bytes)) {
                if (parser.nextToken() != JsonToken.START_OBJECT) throw new IllegalArgumentException("Native additional fields must be an object");
                Set<String> fields = new HashSet<>();
                while (parser.nextToken() != JsonToken.END_OBJECT) {
                    fields.add(parser.currentName()); parser.nextToken(); parser.skipChildren();
                }
                return Set.copyOf(fields);
            } catch (IOException error) { throw new IllegalArgumentException("invalid Native object token", error); }
        }
        private static void validate(JsonParser parser) throws IOException {
            JsonToken token = parser.currentToken();
            if (token == JsonToken.START_OBJECT) {
                while (parser.nextToken() != JsonToken.END_OBJECT) {
                    if (parser.currentToken() != JsonToken.FIELD_NAME) throw new IOException("JSON object field required");
                    unicode(parser.currentName()); parser.nextToken(); validate(parser);
                }
            } else if (token == JsonToken.START_ARRAY) {
                while (parser.nextToken() != JsonToken.END_ARRAY) validate(parser);
            } else if (token == JsonToken.VALUE_STRING) unicode(parser.getText());
            else if (token == null || !token.isScalarValue()) throw new IOException("JSON scalar value required");
        }
        private static void unicode(String value) throws IOException {
            for (int index = 0; index < value.length(); index++) {
                char current = value.charAt(index);
                if (Character.isHighSurrogate(current)) {
                    if (index + 1 >= value.length() || !Character.isLowSurrogate(value.charAt(++index))) throw new IOException("unpaired JSON surrogate");
                } else if (Character.isLowSurrogate(current)) throw new IOException("unpaired JSON surrogate");
            }
        }
        @Override public boolean equals(Object other) { return other instanceof LegacyRawJson raw && Arrays.equals(bytes, raw.bytes); }
        @Override public int hashCode() { return Arrays.hashCode(bytes); }

        /** Compares actual original bytes without exposing, cloning or retaining the caller's array. */
        public boolean contentEquals(byte[] expected) {
            return Arrays.equals(expected, bytes);
        }
    }
}
