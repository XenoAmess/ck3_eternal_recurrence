package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;

/** The real Army native/public producer and common consumer use the full native-token budget. */
final class ArmyFullFrameBoundaryTest {
    @Test void realPublicNumberProducerAndCodecConsumerAcceptLargeOriginalWithoutChangingNativeIdentity() {
        ObjectNode original = ArmyJson.empty().put("context", "x".repeat(1_100_000));
        original.putArray("rows").addObject().put("army_id", 7).put("weight", Long.MIN_VALUE)
                .put("revision", new BigInteger("18446744073709551615"));
        RawJson retained = new RawJson(ArmyJson.bytes(original)); byte[] before = retained.bytes();
        RawJson publicResult = ArmyStrengthsPublicNumbers.encode(retained, List.of(
                new ArmyStrengthsPublicNumbers.Rule("/rows/*/weight", ArmyStrengthsPublicNumbers.Domain.SIGNED_64),
                new ArmyStrengthsPublicNumbers.Rule("/rows/*/revision", ArmyStrengthsPublicNumbers.Domain.UNSIGNED_64)));
        JsonNode decodedNative = ArmyStrengthsCodec.parseValue(retained), decodedPublic = ArmyStrengthsCodec.parseValue(publicResult);
        assertEquals(new BigInteger("18446744073709551615"), decodedNative.at("/rows/0/revision").bigIntegerValue());
        assertEquals("18446744073709551615", decodedPublic.at("/rows/0/revision").textValue());
        assertEquals(Long.toString(Long.MIN_VALUE), decodedPublic.at("/rows/0/weight").textValue());
        assertEquals(7, decodedPublic.at("/rows/0/army_id").intValue());
        assertEquals(decodedNative, ArmyStrengthsCodec.parseValue(new RawJson(ArmyJson.bytes(decodedNative))));
        assertArrayEquals(before, retained.bytes());
    }
    @Test void arrayScalarAndNullFamiliesRetainTheOriginalJsonTypeDomain() {
        for (String token : List.of("null", "[]", "[null,[],{},true,1,1.0,\"1\"]", "9007199254740993", "true", "1.0000000000000000001")) {
            JsonNode first = ArmyStrengthsCodec.parseValue(raw(token));
            JsonNode second = ArmyStrengthsCodec.parseValue(new RawJson(ArmyJson.bytes(first)));
            assertEquals(first, second, token);
        }
        JsonNode row = ArmyStrengthsCodec.parseValue(raw("{\"absent_test\":{},\"nullable\":null,\"empty\":[]}"));
        assertFalse(row.has("missing")); assertTrue(row.get("nullable").isNull()); assertTrue(row.get("empty").isArray());
        assertThrows(IllegalArgumentException.class, () -> ArmyJson.parse(bytes("[]")));
    }
    @Test void explicitBudgetAndMalformedOriginalsStillRefuseAtTheOneBoundary() {
        byte[] value = bytes("{\"value\":1}");
        assertDoesNotThrow(() -> ArmyJson.parseValue(value, value.length));
        assertThrows(IllegalArgumentException.class, () -> ArmyJson.parseValue(value, value.length - 1));
        assertThrows(IllegalArgumentException.class, () -> ArmyJson.parseValue(value, 0));
        assertThrows(IllegalArgumentException.class, () -> ArmyJson.parseValue(value, RawJson.MAXIMUM_BYTES + 1));
        for (String token : List.of("{\"a\":1,\"a\":2}", "[] null", "{\"a\":}", "\"\\uD800\""))
            assertThrows(IllegalArgumentException.class, () -> ArmyJson.parseValue(bytes(token), RawJson.MAXIMUM_BYTES), token);
        assertThrows(IllegalArgumentException.class, () -> ArmyJson.parseValue(new byte[]{(byte) 0xc0, (byte) 0x80}, RawJson.MAXIMUM_BYTES));
        assertThrows(IllegalArgumentException.class, () -> ArmyJson.parseValue(null, RawJson.MAXIMUM_BYTES));
    }
    @Test void boundedMapProtocolHasNotBeenWidenedToTheNativeFrameBudget() {
        assertEquals(1_048_576, StrictJson.EXPLICIT_MAX_BYTES);
        assertThrows(IllegalArgumentException.class, () -> StrictJson.parse(bytes("{}"), RawJson.MAXIMUM_BYTES));
        assertDoesNotThrow(() -> ArmyStrengthsCodec.parseValue(raw("{}")));
    }
    private static byte[] bytes(String token) { return token.getBytes(StandardCharsets.UTF_8); }
    private static RawJson raw(String token) { return new RawJson(bytes(token)); }
}
