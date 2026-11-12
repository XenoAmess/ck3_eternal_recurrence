package org.xar.ck3.control.contracts;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.CharBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.core.JsonParseException;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.SerializerProvider;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.function.Supplier;
import org.junit.jupiter.api.Test;

/** Public tree DATA versus the exact whole active legacy implementation; no new UTF8 scanner or parser is mirrored. */
final class FullJsonTreeByteParserDataTest {
    private static final int LIMIT = 256 * 1024;

    @Test void originalTreesNumericLexemesFieldOrderAndEscapedUnicodeRemainExact() {
        String slash = Character.toString((char)92), escape = slash + "u";
        String bmp = Character.toString((char)0x96ea);
        String emoji = new String(Character.toChars(0x1f600));
        String lastScalar = new String(Character.toChars(0x10ffff));
        for (String raw : List.of(
                " \n\t{\"z\":1,\"a\":2,\"nested\":{\"y\":true,\"x\":null}} \r\n",
                "\"ASCII " + bmp + emoji + lastScalar + "\"",
                "{\"" + bmp + emoji + "\":[\"" + bmp + "\",\"\",true,false,null]}",
                "\"" + escape + "D800\"", "\"" + escape + "DC00\"",
                "{\"" + escape + "D800\":1}", "{\"" + escape + "DC00\":2}",
                "{\"" + escape + "D83D" + escape + "DE00\":\"" + escape + "D83D" + escape + "DE00\"}",
                "{\"literal\":\"" + slash + slash + "uD800\",\"nul\":\"" + escape + "0000\"}",
                "{\"n\":18446744073709551616000000000000000001,\"neg\":-123456789012345678901234567890,\"d\":-0.000e+0,\"e\":1e2147483648,\"i\":-0}",
                "null", "true", "false", "[]", "{}", "\"\"")) {
            assertAccepted(utf8(raw), LIMIT);
        }
        var numbers = FullJsonTree.parse(utf8("{\"big\":18446744073709551616000000000000000001,\"d\":-0.000e+0,\"e\":1e2147483648,\"i\":-0}"), LIMIT);
        assertEquals(new BigInteger("18446744073709551616000000000000000001"), numbers.get("big").bigIntegerValue());
        assertEquals("-0.000e+0", assertInstanceOf(DecimalTokenNode.class, numbers.get("d")).originalToken());
        assertEquals("1e2147483648", assertInstanceOf(DecimalTokenNode.class, numbers.get("e")).originalToken());
        assertTrue(numbers.get("i").isIntegralNumber()); assertEquals(BigInteger.ZERO, numbers.get("i").bigIntegerValue());
    }

    @Test void decodedCharacterThresholdAndOriginalCharacterFailureLocationsRemainExact() {
        String bmp = Character.toString((char)0x96ea), emoji = new String(Character.toChars(0x1f600));
        for (int documentChars : new int[] {32768,32769}) {
            for (String unit : List.of("a", bmp, emoji)) {
                int contentChars = documentChars - 2;
                String value = unit.repeat(contentChars / unit.length()) + "a".repeat(contentChars % unit.length());
                String document = "\"" + value + "\"";
                assertEquals(documentChars, document.length());
                assertAccepted(utf8(document), LIMIT);
                String prefix = "{\"" + unit + "\":";
                String malformed = prefix + " ".repeat(documentChars - prefix.length() - 1) + "}";
                assertEquals(documentChars, malformed.length());
                Outcome old = capture(() -> LegacyFullJsonTree.parse(utf8(malformed), LIMIT));
                Outcome actual = capture(() -> FullJsonTree.parse(utf8(malformed), LIMIT));
                assertNotNull(old.error()); assertThrowableData(old.error(), actual.error());
                var cause = assertInstanceOf(JsonParseException.class, actual.error().getCause());
                assertEquals(-1L, cause.getLocation().getByteOffset());
                assertTrue(cause.getLocation().getCharOffset() >= 0);
                assertNull(cause.getLocation().contentReference().getRawContent());
            }
        }
    }

    @Test void wholeMalformedUtf8AlwaysPrecedesEarlierTokenDuplicateOrDepthFailures() {
        for (byte[] raw : List.of(
                new byte[] {(byte)0x80}, new byte[] {(byte)0xc0,(byte)0xaf}, new byte[] {(byte)0xc2},
                new byte[] {(byte)0xe2,(byte)0x82}, new byte[] {(byte)0xf0,(byte)0x9f,(byte)0x98},
                new byte[] {(byte)0xe2,0x28,(byte)0xa1}, new byte[] {(byte)0xe2,(byte)0x82,0x28},
                new byte[] {(byte)0xf0,(byte)0x90,0x28,(byte)0x80},
                new byte[] {(byte)0xf0,(byte)0x90,(byte)0x80,0x28},
                new byte[] {(byte)0xe0,(byte)0x80,(byte)0x80},
                new byte[] {(byte)0xed,(byte)0xa0,(byte)0x80},
                new byte[] {(byte)0xf4,(byte)0x90,(byte)0x80,(byte)0x80},
                append(utf8("{\"x\":1,\"x\":2}"), (byte)0x80),
                append(utf8("{?"), (byte)0xff), append(utf8("0 "), (byte)0xc3),
                append(utf8("[".repeat(65) + "0" + "]".repeat(65)), (byte)0x80),
                append(new byte[] {(byte)0xef,(byte)0xbb,(byte)0xbf,'{','}'}, (byte)0x80))) {
            Outcome old = capture(() -> LegacyFullJsonTree.parse(raw, LIMIT));
            Outcome actual = capture(() -> FullJsonTree.parse(raw, LIMIT));
            assertNotNull(old.error()); assertThrowableData(old.error(), actual.error());
            assertEquals("invalid complete JSON material", actual.error().getMessage());
            assertInstanceOf(java.nio.charset.CharacterCodingException.class, actual.error().getCause());
        }
    }

    @Test void bomAndWideEncodingAdmissionIsDeterminedByTheWholeLegacyCharacterRoute() {
        byte[] bom = new byte[] {(byte)0xef,(byte)0xbb,(byte)0xbf};
        for (byte[] raw : List.of(bom, concat(bom, utf8("{}")), concat(bom, utf8("\"value\"")),
                concat(utf8(" \n"), concat(bom, utf8("{}"))),
                concat(bom, concat(bom, utf8("{}"))),
                new byte[] {0,0x22,(byte)0xd8,(byte)0xbc,0,0x22},
                new byte[] {(byte)0xff,(byte)0xfe,'{',0,'}',0},
                new byte[] {(byte)0xfe,(byte)0xff,0,'{',0,'}'},
                new byte[] {0,0,(byte)0xfe,(byte)0xff,0,0,0,'{',0,0,0,'}'},
                new byte[] {(byte)0xff,(byte)0xfe,0,0,'{',0,0,0,'}',0,0,0})) {
            assertLegacyResult(raw, LIMIT);
        }
        String textBom = Character.toString((char)0xfeff);
        assertAccepted(utf8("\"" + textBom + "\""), LIMIT);
        assertAccepted(utf8("{\"" + textBom + "\":1}"), LIMIT);
        for (int width : new int[] {2,4}) for (boolean little : new boolean[] {false,true}) {
            byte[] raw = wideAscii("{\"value\":\"ascii\",\"n\":1}", width, little);
            Outcome old = capture(() -> LegacyFullJsonTree.parse(raw, LIMIT));
            assertNotNull(old.error(), "old character route must not autodetect ASCII wide encodings");
            assertThrowableData(old.error(), capture(() -> FullJsonTree.parse(raw, LIMIT)).error());
        }
    }

    @Test void originalBoundsDepthDuplicateTrailingAndOtherErrorsKeepTheirOrder() {
        for (int limit : new int[] {0,-1,LegacyFullJsonTree.MAXIMUM_DRIVER_BYTES + 1})
            assertLegacyResult(new byte[] {(byte)0x80}, limit);
        assertLegacyResult(null, 1); assertLegacyResult(new byte[0], 1);
        assertLegacyResult(utf8("{}"), 1); assertLegacyResult(new byte[] {(byte)0x80,(byte)0x80}, 1);
        assertAccepted(utf8("[".repeat(64) + "0" + "]".repeat(64)), LIMIT);
        String slash = Character.toString((char)92);
        for (String raw : List.of(" \t", "{} []", "true false", "{\"x\":1,\"x\":2}",
                "{\"a\":0,\"" + slash + "u0061\":1}", "{\"x\":", "[0", "\"" + slash + "u12X4\"",
                "[".repeat(65) + "0" + "]".repeat(65), "{\"control\":\"" + Character.toString((char)1) + "\"}")) {
            Outcome old = capture(() -> LegacyFullJsonTree.parse(utf8(raw), LIMIT));
            assertNotNull(old.error()); assertThrowableData(old.error(), capture(() -> FullJsonTree.parse(utf8(raw), LIMIT)).error());
        }
    }

    @Test void callerArraysAndReturnedTreesAreDetachedAndOriginalEncoderCallbacksRemainVisible() {
        byte[] input = utf8("{\"z\":1,\"a\":[2,3],\"s\":\"original\"}"), backup = input.clone();
        JsonNode old = LegacyFullJsonTree.parse(input, LIMIT), actual = FullJsonTree.parse(input, LIMIT);
        assertTreeData(old, actual); Arrays.fill(input, (byte)'!'); assertTreeData(old, actual);
        assertArrayEquals(backup, FullJsonTree.encode(actual, LIMIT));
        ObjectNode second = assertInstanceOf(ObjectNode.class, FullJsonTree.parse(backup, LIMIT));
        assertInstanceOf(ObjectNode.class, actual).put("s", "changed");
        assertEquals("original", old.get("s").textValue()); assertEquals("original", second.get("s").textValue());
        assertArrayEquals(backup, FullJsonTree.encode(second, LIMIT));
        for (JsonNode bad : List.of(JsonNodeFactory.instance.missingNode(), JsonNodeFactory.instance.numberNode(Double.NaN)))
            assertThrowableData(capture(() -> LegacyFullJsonTree.encode(bad, LIMIT)).error(),
                    capture(() -> FullJsonTree.encode(bad, LIMIT)).error());
        var events = new ArrayList<String>(); var sentinel = new IllegalStateException("original encode callback sentinel");
        var callback = new FailingObjectNode(events, sentinel);
        Outcome before = capture(() -> LegacyFullJsonTree.encode(callback, LIMIT));
        assertEquals(List.of("serialize"), events);
        Outcome after = capture(() -> FullJsonTree.encode(callback, LIMIT));
        assertEquals(List.of("serialize", "serialize"), events);
        assertThrowableData(before.error(), after.error());
        assertTrue(containsIdentity(before.error(), sentinel)); assertTrue(containsIdentity(after.error(), sentinel));
    }

    private static void assertAccepted(byte[] raw, int limit) {
        Outcome old = capture(() -> LegacyFullJsonTree.parse(raw, limit));
        assertNull(old.error(), "accepted fixture must follow the original whole parser");
        Outcome actual = capture(() -> FullJsonTree.parse(raw, limit));
        assertThrowableData(old.error(), actual.error());
        assertTreeData((JsonNode)old.value(), (JsonNode)actual.value());
    }
    private static void assertLegacyResult(byte[] raw, int limit) {
        Outcome old = capture(() -> LegacyFullJsonTree.parse(raw, limit));
        Outcome actual = capture(() -> FullJsonTree.parse(raw, limit));
        assertThrowableData(old.error(), actual.error());
        if (old.error() == null) assertTreeData((JsonNode)old.value(), (JsonNode)actual.value());
    }
    private static void assertTreeData(JsonNode old, JsonNode actual) {
        assertEquals(old, actual); assertEquals(old.getNodeType(), actual.getNodeType());
        assertArrayEquals(LegacyFullJsonTree.encode(old, LIMIT), FullJsonTree.encode(actual, LIMIT));
    }
    private static Outcome capture(Supplier<?> operation) {
        try { return new Outcome(operation.get(), null); }
        catch (RuntimeException failure) { return new Outcome(null, failure); }
    }
    private static void assertThrowableData(Throwable old, Throwable actual) {
        if (old == null) { assertNull(actual); return; }
        assertNotNull(actual); assertEquals(old.getClass(), actual.getClass());
        if (old.getMessage() != null && old.getMessage().startsWith("bounded complete JSON material required: ")) {
            String expectedPrefix = old.getMessage().substring(0, old.getMessage().indexOf(" callers=") + 9);
            assertTrue(actual.getMessage().startsWith(expectedPrefix));
            requireCallerShape(old.getMessage().substring(expectedPrefix.length()));
            requireCallerShape(actual.getMessage().substring(expectedPrefix.length()));
        } else assertEquals(old.getMessage(), actual.getMessage());
        if (old instanceof JsonProcessingException oe && actual instanceof JsonProcessingException ae) {
            var ol = oe.getLocation(); var al = ae.getLocation();
            if (ol == null) assertNull(al);
            else {
                assertNotNull(al); assertEquals(ol.getLineNr(), al.getLineNr()); assertEquals(ol.getColumnNr(), al.getColumnNr());
                assertEquals(ol.getByteOffset(), al.getByteOffset()); assertEquals(ol.getCharOffset(), al.getCharOffset());
                assertEquals(ol.contentReference().getRawContent(), al.contentReference().getRawContent());
            }
        }
        assertEquals(old.getSuppressed().length, actual.getSuppressed().length);
        for (int i=0; i<old.getSuppressed().length; i++) assertThrowableData(old.getSuppressed()[i],actual.getSuppressed()[i]);
        assertThrowableData(old.getCause(), actual.getCause());
    }
    private static void requireCallerShape(String frames) {
        assertFalse(frames.isBlank()); assertTrue(frames.length() <= 768);
        String[] entries = frames.split(";"); assertTrue(entries.length <= 5);
        for (String entry : entries) assertTrue(entry.matches("[^:;]+\\.[^:;]+:-?[0-9]+"));
    }
    private static boolean containsIdentity(Throwable error, Throwable sentinel) {
        for (Throwable current=error; current!=null; current=current.getCause()) if (current==sentinel) return true;
        return false;
    }
    private static byte[] utf8(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    private static byte[] append(byte[] raw, byte tail) { byte[] result=Arrays.copyOf(raw,raw.length+1);result[raw.length]=tail;return result; }
    private static byte[] concat(byte[] a, byte[] b) { byte[] result=Arrays.copyOf(a,a.length+b.length);System.arraycopy(b,0,result,a.length,b.length);return result; }
    private static byte[] wideAscii(String text, int width, boolean little) {
        byte[] raw=new byte[text.length()*width];
        for (int i=0;i<text.length();i++) {int c=text.charAt(i);assertTrue(c<128);raw[i*width+(little?0:width-1)]=(byte)c;}
        return raw;
    }
    private record Outcome(Object value, RuntimeException error) { }
    @SuppressWarnings("unchecked") // Inherited ObjectNode generic deepCopy bridge only.
    private static final class FailingObjectNode extends ObjectNode {
        @java.io.Serial private static final long serialVersionUID = 1L;
        private final transient List<String> events; private final RuntimeException sentinel;
        FailingObjectNode(List<String> events,RuntimeException sentinel) {super(JsonNodeFactory.instance);this.events=events;this.sentinel=sentinel;}
        @Override public void serialize(JsonGenerator generator, SerializerProvider provider) throws IOException {
            events.add("serialize"); throw sentinel;
        }
    }

    // Exact whole6865 active legacy body. Only self-name/outer nesting/indentation are mechanical.
    private static final class LegacyFullJsonTree {
        public static final int MAXIMUM_BYTES = 64 * 1024 * 1024;
        public static final int MAXIMUM_DRIVER_BYTES = 256 * 1024 * 1024;
        private static final JsonFactory FACTORY = JsonFactory.builder()
                .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
                .streamReadConstraints(StreamReadConstraints.builder().maxNestingDepth(64)
                        .maxStringLength(MAXIMUM_DRIVER_BYTES).maxNumberLength(MAXIMUM_DRIVER_BYTES).build()).build();
        private static final ObjectMapper JSON = new ObjectMapper(FACTORY);
        private LegacyFullJsonTree() { }

        /** No field normalization is applied. Decimal tokens, integer tokens, missing and null stay distinct. */
        public static JsonNode parse(byte[] original, int maximumBytes) {
            requireLimit(maximumBytes);
            if (original == null || original.length == 0 || original.length > maximumBytes) {
                String frames = StackWalker.getInstance().walk(stream -> stream.skip(1).limit(5)
                        .map(frame -> {
                            String name = frame.getClassName();
                            return name.substring(name.lastIndexOf('.') + 1) + "." + frame.getMethodName()
                                    + ":" + frame.getLineNumber();
                        }).collect(java.util.stream.Collectors.joining(";")));
                if (frames.length() > 768) frames = frames.substring(0, 768);
                StrictJson.require(false, "bounded complete JSON material required: input="
                        + (original == null ? "null" : original.length) + " max=" + maximumBytes
                        + " callers=" + frames);
            }
            try {
                CharBuffer decoded = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                        .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(original));
                // Match the original String API's short fixed-buffer parser route; keep its large Reader route.
                try (JsonParser parser = decoded.hasArray() && decoded.remaining() <= 0x8000
                        ? FACTORY.createParser(decoded.array(), decoded.arrayOffset() + decoded.position(), decoded.remaining())
                        : FACTORY.createParser(decoded.toString())) {
                    // The parser owns its input; do not retain the decoded backing array in this local during tree construction.
                    decoded = null;
                    StrictJson.require(parser.nextToken() != null, "complete JSON value required");
                    JsonNode result = read(parser, 0);
                    StrictJson.require(parser.nextToken() == null, "trailing complete JSON rejected");
                    return result;
                }
            } catch (IOException failure) { throw new IllegalArgumentException("invalid complete JSON material", failure); }
        }
        private static JsonNode read(JsonParser parser, int depth) throws IOException {
            StrictJson.require(depth <= 64, "bounded complete JSON depth required");
            var factory = JsonNodeFactory.instance;
            return switch (parser.currentToken()) {
                case START_OBJECT -> {
                    var result = factory.objectNode();
                    while (parser.nextToken() != JsonToken.END_OBJECT) {
                        StrictJson.require(parser.currentToken() == JsonToken.FIELD_NAME, "complete JSON member required");
                        String key = parser.currentName();
                        StrictJson.require(parser.nextToken() != null, "missing complete JSON value");
                        result.set(key, read(parser, depth + 1));
                    }
                    yield result;
                }
                case START_ARRAY -> {
                    var result = factory.arrayNode();
                    while (parser.nextToken() != JsonToken.END_ARRAY) {
                        StrictJson.require(parser.currentToken() != null, "incomplete complete JSON array");
                        result.add(read(parser, depth + 1));
                    }
                    yield result;
                }
                case VALUE_STRING -> factory.textNode(parser.getText());
                case VALUE_NUMBER_INT -> factory.numberNode(parser.getBigIntegerValue());
                case VALUE_NUMBER_FLOAT -> new DecimalTokenNode(parser.getText());
                case VALUE_TRUE -> factory.booleanNode(true);
                case VALUE_FALSE -> factory.booleanNode(false);
                case VALUE_NULL -> factory.nullNode();
                default -> throw new IllegalArgumentException("unsupported complete JSON token");
            };
        }
        public static byte[] encode(JsonNode normalized, int maximumBytes) {
            requireLimit(maximumBytes); validate(normalized, 0);
            try {
                byte[] result = JSON.writeValueAsBytes(normalized);
                StrictJson.require(result.length <= maximumBytes, "complete JSON material exceeds its explicit lease");
                return result;
            } catch (IOException failure) { throw new IllegalArgumentException("complete JSON encoding failed", failure); }
        }
        private static void requireLimit(int maximumBytes) {
            StrictJson.require(maximumBytes > 0 && maximumBytes <= MAXIMUM_DRIVER_BYTES, "finite complete JSON material lease required");
        }
        private static void validate(JsonNode value, int depth) {
            StrictJson.require(value != null && depth <= 64 && !value.isMissingNode(), "bounded complete JSON tree required");
            if (value.isContainerNode()) { value.forEach(child -> validate(child, depth + 1)); return; }
            StrictJson.require(value.isTextual() || value.isNumber() || value.isBoolean() || value.isNull(), "unsupported complete JSON node");
            if (value.isFloatingPointNumber() && !(value instanceof DecimalTokenNode)) {
                // Derived binary64 values must be finite; original opaque tokens are never rounded to test finiteness.
                if (value.isDouble() || value.isFloat()) StrictJson.require(Double.isFinite(value.doubleValue()), "finite derived JSON float required");
            }
        }
    }
}
