package org.xar.ck3.control.contracts;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.core.JsonParseException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;

/** Public complete-tree boundaries for the unchanged short character-parser route. */
class FullJsonTreeDecodedBufferBoundaryTest {
    private static byte[] utf8(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    private static final int LIMIT = 64 * 1024;

    @Test void independentlyOwnedTreesPreserveIntegerAndDecimalTokensWithoutAddingUnicodeRules() {
        String integer = "123456789012345678901234567890";
        byte[] input = utf8("{\"n\":" + integer + ",\"d\":-0.0,\"e\":1e999,\"s\":\"safe\"}");
        byte[] original = input.clone();
        ObjectNode first = assertInstanceOf(ObjectNode.class, FullJsonTree.parse(input, LIMIT));
        JsonNode second = FullJsonTree.parse(original, LIMIT);
        input[0] = '[';
        assertEquals(new BigInteger(integer), first.get("n").bigIntegerValue());
        assertEquals("-0.0", assertInstanceOf(DecimalTokenNode.class, first.get("d")).originalToken());
        assertEquals("1e999", assertInstanceOf(DecimalTokenNode.class, first.get("e")).originalToken());
        String encoded = new String(FullJsonTree.encode(first, LIMIT), StandardCharsets.UTF_8);
        assertTrue(encoded.contains("\"n\":" + integer));
        assertTrue(encoded.contains("\"d\":-0.0"));
        assertTrue(encoded.contains("\"e\":1e999"));
        assertEquals("safe", first.get("s").asText());
        first.put("n", 0);
        first.put("s", "changed");
        assertEquals(new BigInteger(integer), second.get("n").bigIntegerValue());
        assertEquals("safe", second.get("s").asText());
        assertArrayEquals(original, utf8("{\"n\":" + integer + ",\"d\":-0.0,\"e\":1e999,\"s\":\"safe\"}"));
        // FullJsonTree retains escaped UTF-16 tokens; it does not apply RawJson's surrogate visitor.
        JsonNode legacy = FullJsonTree.parse(utf8("\"" + "\\" + "ud800\""), LIMIT);
        assertEquals(1, legacy.asText().length());
        assertTrue(Character.isHighSurrogate(legacy.asText().charAt(0)));
    }

    @Test void shortAndReaderBoundariesKeepOriginalCharacterFailuresAndDepthAdmission() {
        for (int documentChars : new int[] {32768, 32769}) {
            String value = "a".repeat(documentChars - 2);
            byte[] input = utf8("\"" + value + "\"");
            assertEquals(documentChars, input.length);
            assertEquals(value, FullJsonTree.parse(input, LIMIT).asText());
            String malformed = "{\"v\":" + " ".repeat(documentChars - 6) + "}";
            assertEquals(documentChars, malformed.length());
            IllegalArgumentException failure = assertThrows(IllegalArgumentException.class,
                    () -> FullJsonTree.parse(utf8(malformed), LIMIT));
            assertEquals("invalid complete JSON material", failure.getMessage());
            JsonParseException cause = assertInstanceOf(JsonParseException.class, failure.getCause());
            assertEquals(-1L, cause.getLocation().getByteOffset());
            assertTrue(cause.getLocation().getCharOffset() >= 0);
            assertNull(cause.getLocation().contentReference().getRawContent());
        }
        IllegalArgumentException utf8Failure = assertThrows(IllegalArgumentException.class,
                () -> FullJsonTree.parse(new byte[] {(byte) 0xc3, 0x28}, LIMIT));
        assertInstanceOf(CharacterCodingException.class, utf8Failure.getCause());
        JsonNode maximumDepth = FullJsonTree.parse(utf8("[".repeat(64) + "0" + "]".repeat(64)), LIMIT);
        assertTrue(maximumDepth.isArray());
        assertThrows(IllegalArgumentException.class,
                () -> FullJsonTree.parse(utf8("[".repeat(65) + "0" + "]".repeat(65)), LIMIT));
        assertThrows(IllegalArgumentException.class, () -> FullJsonTree.parse(utf8("{}[]"), LIMIT));
    }
}
