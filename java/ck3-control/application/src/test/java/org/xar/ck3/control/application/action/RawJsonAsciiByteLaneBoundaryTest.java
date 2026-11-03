package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.core.JsonParseException;
import java.io.ByteArrayOutputStream;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;

/** Public DATA boundaries when only the discarded strict decoder result is optional. */
class RawJsonAsciiByteLaneBoundaryTest {
    private static byte[] ascii(String value) { return value.getBytes(StandardCharsets.US_ASCII); }
    private static byte[] joined(byte[]... pieces) {
        var output = new ByteArrayOutputStream();
        for (byte[] piece : pieces) output.writeBytes(piece);
        return output.toByteArray();
    }

    @Test void asciiControlsStillUseTheOriginalByteParserAndEncodingDetection() {
        StringBuilder escapes = new StringBuilder();
        for (int value = 0; value <= 127; value++)
            escapes.append('\\').append('u').append(String.format("%04x", value));
        byte[] legal = ascii("{\"v\":\"" + escapes + "\"}");
        RawJson retained = new RawJson(legal);
        assertArrayEquals(legal, retained.bytes());
        assertEquals(Set.of("v"), retained.objectFieldNames());
        for (int control = 0; control < 32; control++) {
            byte[] invalid = joined(ascii("{\"v\":\""), new byte[] {(byte) control}, ascii("\"}"));
            IllegalArgumentException failure = assertThrows(IllegalArgumentException.class,
                    () -> new RawJson(invalid));
            JsonParseException cause = assertInstanceOf(JsonParseException.class, failure.getCause());
            assertTrue(cause.getLocation().getByteOffset() >= 0);
            assertEquals(-1L, cause.getLocation().getCharOffset());
        }
        byte[] del = joined(ascii("{\"v\":\""), new byte[] {127}, ascii("\"}"));
        assertArrayEquals(del, new RawJson(del).bytes());
        // Every byte is ASCII, including NUL, but the original byte parser recognizes UTF-32BE.
        byte[] zeroPrefixed = {0, 0, 0, '[', 0, 0, 0, '1', 0, 0, 0, ']'};
        RawJson array = new RawJson(zeroPrefixed);
        assertArrayEquals(zeroPrefixed, array.bytes());
        assertThrows(IllegalArgumentException.class, array::objectFieldNames);
        assertDoesNotThrow(() -> RawJson.fullMaterial(zeroPrefixed).requireProtocolBound());
    }

    @Test void firstAndLateNegativeBytesRetainTheEntireStrictDecodeBeforeJsonParsing() {
        byte[] prefix = ascii("{\"v\":\"");
        byte[] suffix = ascii("\"}");
        byte[] validCodePoint = {(byte) 0xe4, (byte) 0xb8, (byte) 0xad};
        byte[] valid = joined(prefix, validCodePoint, suffix);
        RawJson ordinary = new RawJson(valid);
        assertArrayEquals(valid, ordinary.bytes());
        assertEquals(Set.of("v"), ordinary.objectFieldNames());
        assertDoesNotThrow(() -> RawJson.fullMaterial(valid).requireProtocolBound());
        for (byte[] invalidSequence : List.of(
                new byte[] {(byte) 0xc0, (byte) 0x80},
                new byte[] {(byte) 0xed, (byte) 0xa0, (byte) 0x80},
                new byte[] {(byte) 0xe2, (byte) 0x82})) {
            byte[] early = joined(prefix, invalidSequence, suffix);
            byte[] late = joined(prefix, ascii("a".repeat(8192)), validCodePoint, invalidSequence, suffix);
            assertTrue(late.length < 16 * 1024);
            for (byte[] invalid : List.of(early, late)) {
                IllegalArgumentException ordinaryFailure = assertThrows(IllegalArgumentException.class,
                        () -> new RawJson(invalid));
                assertInstanceOf(CharacterCodingException.class, ordinaryFailure.getCause());
                IllegalArgumentException materialFailure = assertThrows(IllegalArgumentException.class,
                        () -> RawJson.fullMaterial(invalid));
                assertInstanceOf(CharacterCodingException.class, materialFailure.getCause());
                assertEquals("invalid UTF-8/duplicate/token Native JSON", ordinaryFailure.getMessage());
            }
        }
    }
}
