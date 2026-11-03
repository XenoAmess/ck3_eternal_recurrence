package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;

public final class PublicDataJsonObjectBoundaryTest {
    @Test
    public void objectValuesAndNestedContainersStayIndependentOfSourceAndOtherResults() {
        String document = "{\"z\":[{\"word\":\"\u96EA\uD83D\uDE80\",\"id\":9007199254740993,"
                + "\"zero\":-0.0,\"exp\":1e999}],\"a\":{\"flag\":true,\"nil\":null},\"empty\":\"\"}";
        byte[] expectedSource = document.getBytes(StandardCharsets.UTF_8);
        byte[] supplied = expectedSource.clone();
        RawJson actual = new RawJson(supplied);
        supplied[0] = 0;
        byte[] detachedBytes = actual.bytes();
        detachedBytes[detachedBytes.length - 1] = 0;

        ObjectNode first = PublicDataJson.object(actual);
        ObjectNode second = PublicDataJson.object(actual);
        List<String> keys = new ArrayList<>();
        first.fieldNames().forEachRemaining(keys::add);
        assertEquals(List.of("z", "a", "empty"), keys);

        ArrayNode firstRows = (ArrayNode) first.get("z");
        ObjectNode firstRow = (ObjectNode) firstRows.get(0);
        assertEquals("\u96EA\uD83D\uDE80", firstRow.get("word").textValue());
        assertTrue(firstRow.get("id").isBigInteger());
        assertEquals(new BigInteger("9007199254740993"), firstRow.get("id").bigIntegerValue());
        assertTrue(firstRow.get("zero").isFloatingPointNumber());
        assertEquals("-0.0", firstRow.get("zero").asText());
        assertTrue(firstRow.get("exp").isFloatingPointNumber());
        assertEquals("1e999", firstRow.get("exp").asText());
        assertTrue(first.get("a").get("flag").booleanValue());
        assertTrue(first.get("a").get("nil").isNull());
        assertNull(first.get("a").get("absent"));
        assertEquals("", first.get("empty").textValue());

        firstRow.put("word", "changed");
        firstRows.addNull();
        ((ObjectNode) first.get("a")).put("flag", false);
        assertEquals(1, second.get("z").size());
        assertEquals("\u96EA\uD83D\uDE80", second.get("z").get(0).get("word").textValue());
        assertTrue(second.get("a").get("flag").booleanValue());
        assertArrayEquals(expectedSource, actual.bytes());

        ObjectNode later = PublicDataJson.object(actual);
        assertEquals(1, later.get("z").size());
        assertEquals("\u96EA\uD83D\uDE80", later.get("z").get(0).get("word").textValue());
    }

    @Test
    public void nonObjectRootsKeepTheirExactPublicException() {
        for (String document : List.of("[]", "null", "7", "\"value\"")) {
            RawJson actual = new RawJson(document.getBytes(StandardCharsets.UTF_8));
            IllegalArgumentException failure = assertThrows(IllegalArgumentException.class,
                    () -> PublicDataJson.object(actual));

            assertEquals(IllegalArgumentException.class, failure.getClass());
            assertEquals("full JSON must be an object", failure.getMessage());
            assertNull(failure.getCause());
        }
    }

    @Test
    public void bomParsingFailurePrecedesRootShapeQualification() {
        byte[][] documents = {
                {(byte) 0xEF, (byte) 0xBB, (byte) 0xBF, (byte) 0x7B, (byte) 0x7D},
                {(byte) 0xEF, (byte) 0xBB, (byte) 0xBF, (byte) 0x5B, (byte) 0x5D}
        };
        for (byte[] document : documents) {
            RawJson actual = new RawJson(document);
            assertArrayEquals(document, actual.bytes());
            IllegalArgumentException failure = assertThrows(IllegalArgumentException.class,
                    () -> PublicDataJson.object(actual));

            assertEquals(IllegalArgumentException.class, failure.getClass());
            assertEquals("invalid complete JSON material", failure.getMessage());
            assertInstanceOf(IOException.class, failure.getCause());
        }
    }
}
