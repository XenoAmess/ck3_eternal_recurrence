package org.xar.ck3.control.contracts;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.Test;

/** Finite public DATA checks against the frozen String-parser algorithm, without private access. */
class FullJsonTreeCharBuffer358Test {
    private static final int OLD_MAXIMUM_BYTES = 256 * 1024 * 1024;
    private static final JsonFactory ORIGINAL_FACTORY = JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxNestingDepth(64)
                    .maxStringLength(OLD_MAXIMUM_BYTES).maxNumberLength(OLD_MAXIMUM_BYTES).build()).build();

    @Test
    void finiteAsciiMultibyteAndOpaqueValuesMatchOriginalStringTokenReader() {
        String high = "\\" + "uD800";
        String low = "\\" + "uDC00";
        List<String> material = List.of(
                " \n\t{\"ascii\":\"abc\",\"n\":123} \r\n",
                "\"é雪😀\"",
                "{\"é\":[\"雪\",\"\\u0000\",\"\\n\",\"\"]}",
                "{\"f\":-0.000e+0,\"n\":1e2147483648,\"z\":-0}",
                "null", "true", "[]", "{}", "\"\"",
                "{\"" + high + low + "\":\"" + high + low + "\"}",
                "\"" + high + "\"", "\"" + low + "\"",
                "{\"" + high + "\":1}");
        for (String text : material) {
            byte[] raw = utf8(text);
            JsonNode expected = originalStringParse(raw, raw.length);
            JsonNode actual = FullJsonTree.parse(raw, raw.length);
            assertEquals(expected, actual, "original token/category/text equality");
            assertArrayEquals(FullJsonTree.encode(expected, 4096), FullJsonTree.encode(actual, 4096));
        }
        JsonNode numbers = FullJsonTree.parse(utf8(material.get(3)), 128);
        assertEquals("-0.000e+0", assertInstanceOf(DecimalTokenNode.class, numbers.get("f")).originalToken());
        assertEquals("1e2147483648", assertInstanceOf(DecimalTokenNode.class, numbers.get("n")).originalToken());
        assertTrue(numbers.get("z").isIntegralNumber());
        assertArrayEquals(utf8("{\"f\":-0.000e+0,\"n\":1e2147483648,\"z\":0}"), FullJsonTree.encode(numbers, 128));
    }

    @Test
    void malformedUtf8AndTokenFailuresKeepOriginalFirstErrorCategories() {
        List<byte[]> malformed = List.of(
                new byte[] {(byte) 0xc0, (byte) 0xaf},
                new byte[] {(byte) 0xe2, (byte) 0x82},
                new byte[] {(byte) 0xed, (byte) 0xa0, (byte) 0x80},
                new byte[] {(byte) 0xf4, (byte) 0x90, (byte) 0x80, (byte) 0x80},
                new byte[] {(byte) 0x80},
                new byte[] {'0', ' ', (byte) 0xc3});
        for (byte[] raw : malformed) {
            sameFailure(raw, 128);
            IllegalArgumentException actual = assertThrows(IllegalArgumentException.class,
                    () -> FullJsonTree.parse(raw, 128));
            assertEquals("invalid complete JSON material", actual.getMessage());
            assertInstanceOf(java.nio.charset.MalformedInputException.class, actual.getCause());
        }
        for (String text : List.of(" \t", "{} []", "{\"x\":1,\"x\":2}",
                "{\"x\":", "[0", "\"\\u12X4\"", "[".repeat(65) + "0" + "]".repeat(65))) {
            sameFailure(utf8(text), 4096);
        }
        // Whole strict UTF8 decoding precedes token parsing: a valid prefix cannot hide a bad tail.
        byte[] duplicatePrefix = utf8("{\"x\":1,\"x\":2}");
        byte[] duplicateThenBadUtf8 = Arrays.copyOf(duplicatePrefix, duplicatePrefix.length + 1);
        duplicateThenBadUtf8[duplicateThenBadUtf8.length - 1] = (byte) 0x80;
        sameFailure(duplicateThenBadUtf8, 128);
        assertInstanceOf(java.nio.charset.MalformedInputException.class,
                assertThrows(IllegalArgumentException.class,
                        () -> FullJsonTree.parse(duplicateThenBadUtf8, 128)).getCause());
    }

    @Test
    void explicitByteLeaseDepthAndRepeatedCallerArraysRemainStrictAndDetached() {
        byte[] multibyte = utf8("\"é\"");
        assertEquals(4, multibyte.length);
        assertEquals("é", FullJsonTree.parse(multibyte, 4).textValue());
        sameFailure(multibyte, 3);
        sameFailure(null, 1);
        sameFailure(new byte[0], 1);
        sameFailure(utf8("{}"), 1);
        sameFailure(new byte[] {(byte) 0xc0}, 0);
        sameFailure(new byte[] {(byte) 0xc0}, OLD_MAXIMUM_BYTES + 1);
        sameFailure(utf8("null"), -1);
        sameFailure(new byte[] {(byte) 0xe2, (byte) 0x82}, 1);
        String depth64 = "[".repeat(64) + "0" + "]".repeat(64);
        assertArrayEquals(utf8(depth64), FullJsonTree.encode(FullJsonTree.parse(utf8(depth64), 1024), 1024));
        sameFailure(utf8("[".repeat(65) + "0" + "]".repeat(65)), 1024);

        JsonNode detached = FullJsonTree.parse(multibyte, 4);
        Arrays.fill(multibyte, (byte) '!');
        assertEquals("é", detached.textValue());
        byte[] sameArray = utf8("\"A\"");
        JsonNode first = FullJsonTree.parse(sameArray, 3);
        sameArray[1] = (byte) 'B';
        JsonNode second = FullJsonTree.parse(sameArray, 3);
        assertEquals("A", first.textValue());
        assertEquals("B", second.textValue());
        assertEquals("null", new String(FullJsonTree.encode(FullJsonTree.parse(utf8("null"), 4), 4), StandardCharsets.UTF_8));
    }

    private static void sameFailure(byte[] raw, int lease) {
        IllegalArgumentException expected = assertThrows(IllegalArgumentException.class,
                () -> originalStringParse(raw, lease));
        IllegalArgumentException actual = assertThrows(IllegalArgumentException.class,
                () -> FullJsonTree.parse(raw, lease));
        assertEquals(expected.getClass(), actual.getClass());
        if (expected.getMessage().startsWith("bounded complete JSON material required")) {
            assertTrue(actual.getMessage().startsWith("bounded complete JSON material required"));
        } else {
            assertEquals(expected.getMessage(), actual.getMessage());
        }
        // String versus char[] parser source references and full diagnostic text may legitimately differ.
        Throwable expectedCause = expected.getCause();
        Throwable actualCause = actual.getCause();
        while (expectedCause != null || actualCause != null) {
            assertEquals(expectedCause == null ? null : expectedCause.getClass(),
                    actualCause == null ? null : actualCause.getClass());
            expectedCause = expectedCause == null ? null : expectedCause.getCause();
            actualCause = actualCause == null ? null : actualCause.getCause();
        }
    }

    private static JsonNode originalStringParse(byte[] raw, int lease) {
        StrictJson.require(lease > 0 && lease <= OLD_MAXIMUM_BYTES, "finite complete JSON material lease required");
        StrictJson.require(raw != null && raw.length > 0 && raw.length <= lease,
                "bounded complete JSON material required");
        try {
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
            try (JsonParser parser = ORIGINAL_FACTORY.createParser(text)) {
                StrictJson.require(parser.nextToken() != null, "complete JSON value required");
                JsonNode value = originalRead(parser, 0);
                StrictJson.require(parser.nextToken() == null, "trailing complete JSON rejected");
                return value;
            }
        } catch (IOException failure) {
            throw new IllegalArgumentException("invalid complete JSON material", failure);
        }
    }

    private static JsonNode originalRead(JsonParser parser, int depth) throws IOException {
        StrictJson.require(depth <= 64, "bounded complete JSON depth required");
        var factory = JsonNodeFactory.instance;
        return switch (parser.currentToken()) {
            case START_OBJECT -> {
                var result = factory.objectNode();
                while (parser.nextToken() != JsonToken.END_OBJECT) {
                    StrictJson.require(parser.currentToken() == JsonToken.FIELD_NAME, "complete JSON member required");
                    String name = parser.currentName();
                    StrictJson.require(parser.nextToken() != null, "missing complete JSON value");
                    result.set(name, originalRead(parser, depth + 1));
                }
                yield result;
            }
            case START_ARRAY -> {
                var result = factory.arrayNode();
                while (parser.nextToken() != JsonToken.END_ARRAY) {
                    StrictJson.require(parser.currentToken() != null, "incomplete complete JSON array");
                    result.add(originalRead(parser, depth + 1));
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

    private static byte[] utf8(String text) { return text.getBytes(StandardCharsets.UTF_8); }
}
