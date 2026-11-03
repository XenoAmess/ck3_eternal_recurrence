package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.BigIntegerNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.DecimalTokenNode;

public final class DriverJsonEncodeNodeBoundaryTest {
    @Test
    public void changingIntegerKeepsTheSecondEncodedValue() {
        JsonNode input = new BigIntegerNode(new ChangingInteger(null));

        assertArrayEquals("2".getBytes(StandardCharsets.UTF_8), DriverJson.encodeNode(input));
    }

    @Test
    public void secondIntegerEncodingKeepsTheOriginalRuntimeFailure() {
        IllegalStateException sentinel = new IllegalStateException("second encoding witness");
        JsonNode input = new BigIntegerNode(new ChangingInteger(sentinel));

        IllegalStateException thrown = assertThrows(IllegalStateException.class,
                () -> DriverJson.encodeNode(input));
        assertSame(sentinel, thrown);
    }

    @Test
    public void nullIntegerAndStableMixedTreeKeepTheirOriginalBytes() {
        assertArrayEquals("null".getBytes(StandardCharsets.UTF_8),
                DriverJson.encodeNode(new BigIntegerNode(null)));

        var factory = JsonNodeFactory.instance;
        var input = factory.objectNode();
        input.put("empty", "");
        input.put("unicode", "雪");
        input.put("lone", "\uD800");
        input.set("integer", new BigIntegerNode(new BigInteger("9007199254740993")));
        input.set("decimal", new DecimalTokenNode("-0.0"));
        input.set("hugeExponent", new DecimalTokenNode("1e999"));
        input.put("flag", true);
        input.putNull("nil");
        var rows = input.putArray("array");
        rows.add(new BigIntegerNode(BigInteger.valueOf(7)));
        rows.add("q");
        rows.add(false);

        String expected = "{\"empty\":\"\",\"unicode\":\"雪\",\"lone\":\"\\uD800\","
                + "\"integer\":9007199254740993,\"decimal\":-0.0,\"hugeExponent\":1e999,"
                + "\"flag\":true,\"nil\":null,\"array\":[7,\"q\",false]}";
        assertArrayEquals(expected.getBytes(StandardCharsets.UTF_8), DriverJson.encodeNode(input));
    }

    private static final class ChangingInteger extends BigInteger {
        private static final long serialVersionUID = 1L;
        private final IllegalStateException secondFailure;
        private boolean first = true;

        private ChangingInteger(IllegalStateException secondFailure) {
            super("1");
            this.secondFailure = secondFailure;
        }

        @Override
        public String toString() {
            if (first) {
                first = false;
                return "1";
            }
            if (secondFailure != null) {
                throw secondFailure;
            }
            return "2";
        }
    }
}
