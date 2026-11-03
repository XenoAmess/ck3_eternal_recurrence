package org.xar.ck3.control.contracts;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.DoubleNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.TextNode;
import java.io.Serial;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.Iterator;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.function.Executable;

final class StrictJsonCanonicalQuotePublicBoundaryTest {
    private static final JsonNodeFactory NODES = JsonNodeFactory.instance;

    @Test
    void canonicalPreservesLiteralQuotesAndAdjacentUtf16Pairs() {
        String rocket = new String(new char[] {(char) 0xd83d, (char) 0xde80});
        String payload = new String(new char[] {
                '"', '\\', '\b', '\f', '\n', '\r', '\t', (char) 0, (char) 0x1f,
                '/', (char) 0x96ea, (char) 0xd83d, (char) 0xde80});
        byte[] literal = HexFormat.of().parseHex(
                "225c225c5c5c625c665c6e5c725c745c75303030305c75303031662fe99baaf09f9a8022");
        assertArrayEquals(literal, StrictJson.canonical(new TextNode(payload)));
        assertArrayEquals(new byte[] {'"', '"'}, StrictJson.canonical(new TextNode(""), 2));
        assertArrayEquals(HexFormat.of().parseHex("22f090808022"), StrictJson.canonical(
                new TextNode(new String(new char[] {(char) 0xd800, (char) 0xdc00}))));

        ObjectNode object = NODES.objectNode();
        object.set("\"\n" + rocket, new TextNode(payload));
        object.set("", new TextNode(""));
        assertArrayEquals(HexFormat.of().parseHex(
                "7b22223a22222c225c225c6ef09f9a80223a"
                + "225c225c5c5c625c665c6e5c725c745c75303030305c75303031662fe99baaf09f9a8022"
                + "7d"), StrictJson.canonical(object));
    }

    @Test
    void canonicalPreservesNullLengthAndUnicodeFirstErrors() {
        RuntimeException unseen = new IllegalStateException("must not visit the text payload");
        TextNode probe = new ThrowingTextNode(unseen);
        contractFailure("explicit JSON output byte budget", () -> StrictJson.canonical(probe, 0));
        contractFailure("explicit JSON output byte budget", () -> StrictJson.canonical(null, 1_048_577));
        contractFailure("missing JSON node cannot be serialized as null", () -> StrictJson.canonical(null, 1));
        assertArrayEquals("null".getBytes(StandardCharsets.UTF_8), StrictJson.canonical(NODES.nullNode(), 4));

        TextNode nullPayload = new TextNode((String) null);
        NullPointerException nullFailure = assertThrows(NullPointerException.class,
                () -> StrictJson.canonical(nullPayload, 1));
        assertEquals(NullPointerException.class, nullFailure.getClass());
        assertNull(nullFailure.getCause());
        contractFailure("canonical JSON exceeds shared receipt byte budget",
                () -> StrictJson.canonical(new TextNode(""), 1));

        String high = String.valueOf((char) 0xd800);
        TextNode tooLongAndMalformed = new TextNode(high + "a".repeat(32_768));
        contractFailure("nonempty bounded text required",
                () -> StrictJson.canonical(tooLongAndMalformed, 1_048_576));
        TextNode boundedAndMalformed = new TextNode(high + "a".repeat(32_767));
        contractFailure("unpaired Unicode surrogate",
                () -> StrictJson.canonical(boundedAndMalformed, 1_048_576));
        for (char[] units : new char[][] {
                {(char) 0xd800}, {(char) 0xdc00},
                {(char) 0xd800, (char) 0xd800, (char) 0xdc00},
                {(char) 0xd800, (char) 0xdc00, (char) 0xdc00},
                {(char) 0xdc00, (char) 0xd800, (char) 0xdc00},
                {(char) 0xd800, (char) 0xdc00, (char) 0xd800}}) {
            TextNode malformed = new TextNode(new String(units));
            contractFailure("unpaired Unicode surrogate", () -> StrictJson.canonical(malformed, 1));
        }

        String pair = new String(new char[] {(char) 0xd83d, (char) 0xde80});
        String maximumText = pair.repeat(32_768);
        TextNode maximumNode = new TextNode(maximumText);
        byte[] expected = ("\"" + maximumText + "\"").getBytes(StandardCharsets.UTF_8);
        assertEquals(131_074, expected.length);
        assertArrayEquals(expected, StrictJson.canonical(maximumNode, 1_048_576));
        contractFailure("canonical JSON exceeds shared receipt byte budget",
                () -> StrictJson.canonical(maximumNode));
        TextNode tooManyPairs = new TextNode(pair.repeat(32_769));
        contractFailure("nonempty bounded text required",
                () -> StrictJson.canonical(tooManyPairs, 1_048_576));
    }

    @Test
    void canonicalPreservesKeyCollectionAndLaterNodeFailureOrder() {
        String badKey = String.valueOf((char) 0xdc00);
        List<String> keyEvents = new ArrayList<>();
        RuntimeException forbiddenGet = new IllegalStateException("get must follow a valid key");
        NameProbeObject badKeyObject = new NameProbeObject(List.of(badKey), keyEvents, null, forbiddenGet);
        badKeyObject.set(badKey, new TextNode(""));
        contractFailure("unpaired Unicode surrogate", () -> StrictJson.canonical(badKeyObject));
        assertEquals(List.of("fieldNames", "name:" + badKey), keyEvents);

        List<String> nameEvents = new ArrayList<>();
        RuntimeException namesFailure = new IllegalStateException("field enumeration failed");
        NameProbeObject incompleteNames = new NameProbeObject(
                List.of(badKey), nameEvents, namesFailure, forbiddenGet);
        incompleteNames.set(badKey, new TextNode(""));
        assertSame(namesFailure, assertThrows(RuntimeException.class,
                () -> StrictJson.canonical(incompleteNames)));
        assertEquals(List.of("fieldNames", "name:" + badKey, "namesThrow"), nameEvents);

        List<String> orderedEvents = new ArrayList<>();
        NameProbeObject duplicateNames = new NameProbeObject(
                List.of("b", "a", "a"), orderedEvents, null, null);
        duplicateNames.set("b", NODES.booleanNode(true));
        duplicateNames.set("a", new TextNode(""));
        assertArrayEquals("{\"a\":\"\",\"b\":true}".getBytes(StandardCharsets.UTF_8),
                StrictJson.canonical(duplicateNames));
        assertEquals(List.of("fieldNames", "name:b", "name:a", "name:a", "get:a", "get:b"), orderedEvents);

        TextNode malformed = new TextNode(String.valueOf((char) 0xd800));
        var stringFirst = NODES.arrayNode().add(malformed).add(DoubleNode.valueOf(1.0));
        contractFailure("unpaired Unicode surrogate", () -> StrictJson.canonical(stringFirst));
        var numberFirst = NODES.arrayNode().add(DoubleNode.valueOf(1.0)).add(malformed);
        contractFailure("non-integer JSON number is outside this canonical contract",
                () -> StrictJson.canonical(numberFirst));
        var lateNumber = NODES.arrayNode().add(new TextNode("ok")).add(DoubleNode.valueOf(1.0));
        contractFailure("non-integer JSON number is outside this canonical contract",
                () -> StrictJson.canonical(lateNumber, 1));

        RuntimeException payloadFailure = new IllegalStateException("later text payload failed");
        TextNode throwing = new ThrowingTextNode(payloadFailure);
        var lateCallback = NODES.arrayNode().add(new TextNode("ok")).add(throwing);
        assertSame(payloadFailure, assertThrows(RuntimeException.class,
                () -> StrictJson.canonical(lateCallback, 1)));
        var earlierMalformed = NODES.arrayNode().add(malformed).add(throwing);
        contractFailure("unpaired Unicode surrogate", () -> StrictJson.canonical(earlierMalformed));
    }

    private static void contractFailure(String expectedMessage, Executable action) {
        ContractViolationException failure = assertThrows(ContractViolationException.class, action);
        assertEquals(ContractViolationException.class, failure.getClass());
        assertEquals(expectedMessage, failure.getMessage());
        assertNull(failure.getCause());
    }

    private static final class ThrowingTextNode extends TextNode {
        @Serial private static final long serialVersionUID = 1L;
        private final transient RuntimeException failure;

        private ThrowingTextNode(RuntimeException failure) {
            super("unused");
            this.failure = failure;
        }

        @Override public String textValue() { throw failure; }
    }

    // ObjectNode's covariant deepCopy inherits JsonNode's generic return contract.
    @SuppressWarnings("unchecked")
    private static final class NameProbeObject extends ObjectNode {
        @Serial private static final long serialVersionUID = 1L;
        private final transient List<String> names;
        private final transient List<String> events;
        private final transient RuntimeException namesFailure;
        private final transient RuntimeException getFailure;

        private NameProbeObject(List<String> names, List<String> events,
                                RuntimeException namesFailure, RuntimeException getFailure) {
            super(NODES);
            this.names = names;
            this.events = events;
            this.namesFailure = namesFailure;
            this.getFailure = getFailure;
        }

        @Override public Iterator<String> fieldNames() {
            events.add("fieldNames");
            Iterator<String> actual = names.iterator();
            return new Iterator<>() {
                @Override public boolean hasNext() {
                    if (actual.hasNext()) { return true; }
                    if (namesFailure != null) {
                        events.add("namesThrow");
                        throw namesFailure;
                    }
                    return false;
                }

                @Override public String next() {
                    String name = actual.next();
                    events.add("name:" + name);
                    return name;
                }
            };
        }

        @Override public JsonNode get(String name) {
            events.add("get:" + name);
            if (getFailure != null) { throw getFailure; }
            return super.get(name);
        }
    }
}
