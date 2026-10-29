package org.xar.ck3.control.wave2.finance.rawcash;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

final class SdkProjectionJsonTest {
    @Test void explicitRoleBudgetDoesNotWidenDefaultAndCountsActualUtf8Bytes() {
        ArrayNode large = StrictJson.object().arrayNode();
        for (int index = 0; index < 4; index++) { large.add("x".repeat(20_000)); }
        byte[] explicit = SdkProjectionJson.encode(large, 512 * 1024);
        assertTrue(explicit.length > 65_536);
        assertThrows(IllegalArgumentException.class, () -> SdkProjectionJson.encode(large));
        assertArrayEquals(explicit, SdkProjectionJson.encode(large, explicit.length));
        assertThrows(IllegalArgumentException.class, () -> SdkProjectionJson.encode(large, explicit.length - 1));
        assertEquals(large, StrictJson.parse(explicit, 512 * 1024));

        ArrayNode unicode = StrictJson.object().arrayNode();
        unicode.add("é".repeat(16_382)); unicode.add("é".repeat(16_382));
        assertEquals(65_535, SdkProjectionJson.encode(unicode).length);
        unicode.set(1, StrictJson.object().textNode("é".repeat(16_383)));
        assertThrows(IllegalArgumentException.class, () -> SdkProjectionJson.encode(unicode));
    }

    @Test void explicitBudgetRetainsFloatingIntegerAndMissingNullEmptyDomains() {
        JsonNode original = StrictJson.parse(("{\"identity\":18446744073709551615,\"floating\":1.0,"
                + "\"falseFlag\":false,\"nullValue\":null,\"empty\":[]}").getBytes(StandardCharsets.UTF_8));
        byte[] encoded = SdkProjectionJson.encode(original, 512 * 1024);
        JsonNode roundTrip = StrictJson.parse(encoded, 512 * 1024);
        assertEquals(original, roundTrip);
        assertEquals(new BigInteger("18446744073709551615"), roundTrip.get("identity").bigIntegerValue());
        assertTrue(roundTrip.get("floating").isFloatingPointNumber());
        assertThrows(IllegalArgumentException.class, () -> StrictJson.integer(roundTrip.get("floating"), 0, 10));
        assertTrue(roundTrip.get("nullValue").isNull());
        assertTrue(roundTrip.get("empty").isArray());
        assertEquals(null, roundTrip.get("missing"));
        assertTrue(roundTrip.get("falseFlag").isBoolean());
    }

    @Test void invalidExplicitBudgetsAndAbsentNodesRefuse() {
        JsonNode value = StrictJson.object();
        for (int maximum : new int[] {0, -1, StrictJson.EXPLICIT_MAX_BYTES + 1}) {
            assertThrows(IllegalArgumentException.class, () -> SdkProjectionJson.encode(value, maximum));
        }
        assertThrows(IllegalArgumentException.class, () -> SdkProjectionJson.encode(null, 512 * 1024));
    }
}
