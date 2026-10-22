package org.xar.ck3.control.contracts;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

final class StrictJsonBudgetTest {
    @Test
    void explicitLeafBudgetAcceptsLargeReceiptsWhileDefaultMapStillRefuses() {
        ObjectNode receipt = StrictJson.object();
        ArrayNode rows = receipt.putArray("rows");
        for (int index = 0; index < 4; index++) {
            rows.add("观".repeat(10_000));
        }
        byte[] raw = StrictJson.canonical(receipt, 1_048_576);
        assertThrows(ContractViolationException.class, () -> StrictJson.parse(raw));
        assertThrows(ContractViolationException.class, () -> StrictJson.canonical(receipt));
        JsonNode parsed = StrictJson.parse(raw, 1_048_576);
        assertEquals(receipt, parsed);
        assertArrayEquals(raw, StrictJson.canonical(parsed, 1_048_576));
        assertThrows(ContractViolationException.class, () -> CampaignMapAdmissionComposer.compose(raw));
    }

    @Test
    void inputBudgetUsesActualUtf8BytesAndExactInclusiveLimit() {
        byte[] raw = "{\"text\":\"观\"}".getBytes(StandardCharsets.UTF_8);
        assertEquals("观", StrictJson.parse(raw, raw.length).get("text").textValue());
        assertThrows(ContractViolationException.class, () -> StrictJson.parse(raw, raw.length - 1));
    }

    @Test
    void callersCannotDisableOrExceedExplicitBudgets() {
        byte[] raw = "{}".getBytes(StandardCharsets.UTF_8);
        for (int maximum : new int[] {-1, 0, 1_048_577, Integer.MAX_VALUE}) {
            assertThrows(ContractViolationException.class, () -> StrictJson.parse(raw, maximum));
            assertThrows(ContractViolationException.class,
                    () -> StrictJson.canonical(StrictJson.object(), maximum));
        }
        assertThrows(ContractViolationException.class,
                () -> StrictJson.parse(new byte[1_048_577], 1_048_576));
    }

    @Test
    void largerLeafBudgetRetainsDuplicateUtf8AndNumericTokenGuards() {
        assertThrows(ContractViolationException.class,
                () -> StrictJson.parse("{\"x\":1,\"x\":2}".getBytes(StandardCharsets.UTF_8), 1_048_576));
        assertThrows(ContractViolationException.class,
                () -> StrictJson.parse(new byte[] {(byte) 0xc3, (byte) 0x28}, 1_048_576));
        for (String literal : new String[] {"1.0", "1e2", "true", "\"1\"", "null"}) {
            JsonNode node = StrictJson.parse(literal.getBytes(StandardCharsets.UTF_8), 1_048_576);
            assertThrows(ContractViolationException.class, () -> StrictJson.integer(node, 0, 1000));
        }
    }
}
