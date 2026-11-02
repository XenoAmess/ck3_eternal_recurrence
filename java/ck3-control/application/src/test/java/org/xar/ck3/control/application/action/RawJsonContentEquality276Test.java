package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import org.junit.jupiter.api.Test;

/** Public original-byte and alias contracts only; no source or runtime authority. */
final class RawJsonContentEquality276Test {
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }

    @Test void constructorAndGetterAliasesCannotChangeContent() {
        byte[] original = bytes(" {\"number\":1.0,\"opaque\":\"\\u0061\"} ");
        byte[] expected = original.clone();
        RawJson value = new RawJson(original);
        Arrays.fill(original, (byte) 0);
        byte[] returned = value.bytes();
        Arrays.fill(returned, (byte) 1);
        assertTrue(value.contentEquals(expected));
        assertArrayEquals(expected, value.bytes());
        assertEquals(new RawJson(expected), value);
    }

    @Test void comparisonUsesExactCurrentArgumentWithoutRetainingIt() {
        byte[] original = bytes("{\"number\":1}");
        RawJson value = new RawJson(original);
        byte[] expected = original.clone();
        assertTrue(value.contentEquals(expected));
        expected[expected.length - 2] = (byte) '2';
        assertFalse(value.contentEquals(expected));
        assertTrue(value.contentEquals(original));
        assertArrayEquals(original, value.bytes());
        assertFalse(value.contentEquals(bytes("{\"number\":1.0}")));
        assertFalse(value.contentEquals(bytes(" {\"number\":1}")));
        assertFalse(value.contentEquals(new byte[0]));
        assertFalse(value.contentEquals(null));
    }

    @Test void fullMaterialEqualityDoesNotGrantProtocolNumberAdmission() {
        byte[] original = bytes("{\"large\":" + "7".repeat(5000) + "}");
        RawJson value = RawJson.fullMaterial(original);
        assertTrue(value.contentEquals(original));
        assertThrows(IllegalArgumentException.class, value::requireProtocolBound);
        assertThrows(IllegalArgumentException.class, () -> new RawJson(original));
        byte[] detached = value.bytes();
        detached[detached.length - 2] = (byte) '6';
        assertFalse(value.contentEquals(detached));
        assertTrue(value.contentEquals(original));
    }
}
