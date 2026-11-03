package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.BigIntegerNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.NoSuchElementException;
import org.junit.jupiter.api.Test;

public final class PublicDataJsonArrayCapturePublicBoundaryTest {
    private static final JsonNodeFactory NODES = JsonNodeFactory.instance;

    @Test
    void completedSmallArraysAndFallbackPreserveBytesAndInputs() {
        List<ArrayNode> inputs = List.of(
                NODES.arrayNode(),
                NODES.arrayNode().addNull(),
                NODES.arrayNode().add(1).add(NODES.objectNode().put("b", 2).put("a", 1)),
                NODES.arrayNode().add(1).add(2).add(3).add(4));
        List<String> expected = List.of("[]", "[null]", "[1,{\"a\":1,\"b\":2}]", "[1,2,3,4]");
        for (int index = 0; index < inputs.size(); index++) {
            ArrayNode input = inputs.get(index);
            String before = input.toString();
            assertArrayEquals(utf8(expected.get(index)), PublicDataJson.encode(input).bytes());
            assertEquals(before, input.toString());
            assertArrayEquals(utf8(expected.get(index)), PublicDataJson.encodeFullMaterial(input).bytes());
            assertEquals(before, input.toString());
        }

        RuntimeException forbiddenSize = new IllegalStateException("backing-list size callback");
        ArrayList<JsonNode> backing = new ArrayList<>() {
            private static final long serialVersionUID = 1L;
            @Override public int size() { throw forbiddenSize; }
        };
        backing.add(NODES.numberNode(1));
        backing.add(NODES.numberNode(2));
        ArrayNode external = new ArrayNode(NODES, backing);
        assertArrayEquals(utf8("[1,2]"), PublicDataJson.encode(external).bytes());
        assertArrayEquals(utf8("[1,2]"), PublicDataJson.encodeFullMaterial(external).bytes());
    }

    @Test
    void childCapturePrecedesNextMutationAndLaterIteratorFailure() {
        for (boolean full : new boolean[] {false, true}) {
            ObjectNode first = NODES.objectNode().put("v", 1);
            @SuppressWarnings("unchecked")
            ArrayNode changing = new ArrayNode(NODES) {
                private static final long serialVersionUID = 1L;
                @Override public Iterator<JsonNode> elements() {
                    return new Iterator<>() {
                        private int position;
                        @Override public boolean hasNext() { return position < 2; }
                        @Override public JsonNode next() {
                            if (position == 0) { position = 1; return first; }
                            if (position == 1) {
                                position = 2;
                                first.put("v", 2);
                                return NODES.nullNode();
                            }
                            throw new NoSuchElementException();
                        }
                    };
                }
            };
            assertArrayEquals(utf8("[{\"v\":1},null]"), encode(changing, full));
            assertEquals(2, first.get("v").intValue());

            RuntimeException childFailure = new IllegalStateException("child get failure");
            RuntimeException laterFailure = new IllegalStateException("later hasNext failure");
            @SuppressWarnings("unchecked")
            ObjectNode failingChild = new ObjectNode(NODES) {
                private static final long serialVersionUID = 1L;
                @Override public JsonNode get(String fieldName) { throw childFailure; }
            };
            failingChild.put("v", 1);
            @SuppressWarnings("unchecked")
            ArrayNode failing = new ArrayNode(NODES) {
                private static final long serialVersionUID = 1L;
                @Override public Iterator<JsonNode> elements() {
                    return new Iterator<>() {
                        private boolean delivered;
                        @Override public boolean hasNext() {
                            if (delivered) throw laterFailure;
                            return true;
                        }
                        @Override public JsonNode next() {
                            if (delivered) throw new NoSuchElementException();
                            delivered = true;
                            return failingChild;
                        }
                    };
                }
            };
            assertSame(childFailure, assertThrows(RuntimeException.class, () -> encode(failing, full)));
        }
    }

    @Test
    void numericPayloadAliasIsReadAfterCaptureAndNullPayloadRemainsJsonNull() {
        for (boolean full : new boolean[] {false, true}) {
            MutableIntegerText number = new MutableIntegerText();
            BigIntegerNode first = new BigIntegerNode(number);
            @SuppressWarnings("unchecked")
            ArrayNode changing = new ArrayNode(NODES) {
                private static final long serialVersionUID = 1L;
                @Override public Iterator<JsonNode> elements() {
                    return new Iterator<>() {
                        private int position;
                        @Override public boolean hasNext() { return position < 2; }
                        @Override public JsonNode next() {
                            if (position == 0) { position = 1; return first; }
                            if (position == 1) {
                                position = 2;
                                number.text = "2";
                                return NODES.numberNode(0);
                            }
                            throw new NoSuchElementException();
                        }
                    };
                }
            };
            assertArrayEquals(utf8("[2,0]"), encode(changing, full));
            assertEquals("2", number.text);
            ArrayNode nullable = NODES.arrayNode().add(new BigIntegerNode((BigInteger) null));
            assertArrayEquals(utf8("[null]"), encode(nullable, full));
        }
    }

    private static byte[] encode(JsonNode value, boolean full) {
        return (full ? PublicDataJson.encodeFullMaterial(value) : PublicDataJson.encode(value)).bytes();
    }

    private static byte[] utf8(String value) {
        return value.getBytes(StandardCharsets.UTF_8);
    }

    private static final class MutableIntegerText extends BigInteger {
        private static final long serialVersionUID = 1L;
        private String text = "1";
        private MutableIntegerText() { super("1"); }
        @Override public String toString() { return text; }
    }
}
