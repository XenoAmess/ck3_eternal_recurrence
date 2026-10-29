package org.xar.ck3.control.contracts.semantic;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.MissingNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.junit.jupiter.api.Test;

final class NativePlayedResourcesTest {
    private static JsonNode json(String text) {
        return StrictJson.parse(text.getBytes(StandardCharsets.UTF_8));
    }

    @Test
    void allThreeShareOneExactSigned64ParserAndJsonRepresentation() {
        for (long raw : new long[] {Long.MIN_VALUE, -9_007_199_254_740_993L, -1, 0, 1,
                9_007_199_254_740_993L, Long.MAX_VALUE}) {
            for (NativePlayedResources.Resource resource : NativePlayedResources.Resource.values()) {
                ObjectNode source = StrictJson.object();
                source.set(resource.wire(), json("{\"raw\":" + raw + ",\"scale\":100000}"));
                NativePlayedResources.Fields decoded = NativePlayedResources.decodeState(source);
                assertEquals(new NativePlayedResources.Amount(raw), decoded.resource(resource));
                ObjectNode encoded = StrictJson.object();
                NativePlayedResources.writeFields(encoded, decoded);
                assertArrayEquals(StrictJson.canonical(source), StrictJson.canonical(encoded));
                assertEquals(decoded, NativePlayedResources.decodeState(
                        StrictJson.parse(StrictJson.canonical(encoded))));
                assertEquals(100_000,
                        assertInstanceOf(NativePlayedResources.Amount.class, decoded.resource(resource)).scale());
            }
        }
    }

    @Test
    void missingNullAndZeroRemainDifferentAcrossTheActualEnclosingSerde() {
        NativePlayedResources.Fields source = new NativePlayedResources.Fields(
                new NativePlayedResources.Missing(), new NativePlayedResources.NullValue(),
                new NativePlayedResources.Amount(0));
        ObjectNode output = StrictJson.object().put("unrelated", "retained");
        output.put(NativePlayedResources.Resource.GOLD.wire(), "stale");
        NativePlayedResources.writeFields(output, source);
        assertFalse(output.has("played_character_gold"));
        assertTrue(output.has("played_character_prestige"));
        assertTrue(output.get("played_character_prestige").isNull());
        assertEquals(0, output.get("played_character_piety").get("raw").longValue());
        assertEquals("retained", output.get("unrelated").textValue());
        assertEquals(source, NativePlayedResources.decodeState(
                StrictJson.parse(StrictJson.canonical(output))));
        assertInstanceOf(NativePlayedResources.Missing.class, NativePlayedResources.decode(null));
        assertEquals(NativePlayedResources.decode(null),
                NativePlayedResources.decode(MissingNode.getInstance()));
        assertNotEquals(NativePlayedResources.decode(null), NativePlayedResources.decode(NullNode.getInstance()));
        assertThrows(ContractViolationException.class,
                () -> StrictJson.canonical(NativePlayedResources.encode(new NativePlayedResources.Missing())));
        for (NativePlayedResources.Resource resource : NativePlayedResources.Resource.values()) {
            assertEquals(NullNode.getInstance(), NativePlayedResources.normalize(null, resource));
            assertEquals(NullNode.getInstance(), NativePlayedResources.normalize(MissingNode.getInstance(), resource));
            assertEquals(NullNode.getInstance(), NativePlayedResources.normalize(NullNode.getInstance(), resource));
            assertArrayEquals(StrictJson.canonical(json("{\"raw\":0,\"scale\":100000}")),
                    StrictJson.canonical(NativePlayedResources.normalize(
                            json("{\"raw\":0,\"scale\":100000}"), resource)));
        }
    }

    @Test
    void malformedExactObjectFieldsAndEveryWrongNumericTokenAreRejectedAtReceive() {
        List<String> malformed = List.of("false", "[]", "0", "\"resource\"", "{}",
                "{\"raw\":0}", "{\"scale\":100000}",
                "{\"raw\":0,\"scale\":100000,\"source\":\"native\"}",
                "{\"raw\":true,\"scale\":100000}",
                "{\"raw\":1.0,\"scale\":100000}",
                "{\"raw\":1e0,\"scale\":100000}",
                "{\"raw\":\"9223372036854775807\",\"scale\":100000}",
                "{\"raw\":9223372036854775808,\"scale\":100000}",
                "{\"raw\":-9223372036854775809,\"scale\":100000}",
                "{\"raw\":0,\"scale\":true}",
                "{\"raw\":0,\"scale\":100000.0}",
                "{\"raw\":0,\"scale\":1e5}",
                "{\"raw\":0,\"scale\":\"100000\"}",
                "{\"raw\":0,\"scale\":99999}",
                "{\"raw\":0,\"scale\":null}");
        for (String text : malformed) {
            assertThrows(ContractViolationException.class,
                    () -> NativePlayedResources.decode(json(text)), text);
            for (NativePlayedResources.Resource resource : NativePlayedResources.Resource.values()) {
                ObjectNode state = StrictJson.object();
                state.set(resource.wire(), json(text));
                assertThrows(ContractViolationException.class,
                        () -> NativePlayedResources.decodeState(state), resource + ": " + text);
            }
        }
        assertThrows(ContractViolationException.class,
                () -> NativePlayedResources.decode(json("{\"raw\":0,\"raw\":1,\"scale\":100000}")));
        assertThrows(ContractViolationException.class,
                () -> NativePlayedResources.decodeState(NullNode.getInstance()));
    }

    @Test
    void immutableModelDoesNotKeepMutableWireNodesAndOutputsAreIndependent() {
        ObjectNode input = assertInstanceOf(ObjectNode.class,
                json("{\"raw\":9007199254740993,\"scale\":100000}"));
        NativePlayedResources.Field amount = NativePlayedResources.decode(input);
        input.put("raw", 0);
        ObjectNode first = assertInstanceOf(ObjectNode.class, NativePlayedResources.encode(amount));
        first.put("raw", 1);
        assertEquals(9_007_199_254_740_993L, NativePlayedResources.encode(amount).get("raw").longValue());
        assertThrows(NullPointerException.class,
                () -> new NativePlayedResources.Fields(null,
                        new NativePlayedResources.NullValue(), new NativePlayedResources.NullValue()));
    }
}
