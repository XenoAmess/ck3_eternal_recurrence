package org.xar.ck3.control.g2.m2;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.projection.ProjectionJson;

final class M2PayloadTest {
    @Test void preservesTheOriginalIntegerDecimalNullArrayAndEscapedUnicodeBytes() {
        byte[] original = "{\"id\":18446744073709551615,\"decimal\":1.0,\"null\":null,\"empty\":[],\"unicode\":\"\\uD83D\\uDE00\"}".getBytes(StandardCharsets.UTF_8);
        ProjectionJson wrapped = M2Payload.input(M2Payload.Operation.EVENT_PLAN_CANDIDATE, ProjectionJson.object(original, M2Payload.MAX_BYTES));
        M2Payload.Input decoded = M2Payload.decode(wrapped);
        assertEquals(M2Payload.Operation.EVENT_PLAN_CANDIDATE, decoded.operation());
        assertArrayEquals(original, decoded.input().bytes());
    }

    @Test void preservesObjectArrayAndNullResultsWithoutReencodingTokens() {
        for (String value : List.of("null", "{\"value\":1.0}", "[18446744073709551615,null,[]]")) {
            byte[] original = value.getBytes(StandardCharsets.UTF_8);
            ProjectionJson result = M2Payload.output(M2Payload.Operation.EVENT_AFTER, ProjectionJson.value(original, M2Payload.MAX_BYTES));
            assertEquals(M2Payload.Operation.EVENT_AFTER, M2Payload.decodeResult(result).operation());
            assertArrayEquals(original, M2Payload.unwrapResult(result).bytes());
        }
    }

    @Test void addsRoutingWithoutShrinkingTheOriginalOneMiBRole() {
        byte[] original = ("{\"retained\":\"" + "a".repeat(1_048_550) + "\"}").getBytes(StandardCharsets.UTF_8);
        ProjectionJson body = ProjectionJson.object(original, 1_048_576);
        ProjectionJson wrapped = M2Payload.input(M2Payload.Operation.EVENT_PLAN_CANDIDATE, body);
        assertArrayEquals(original, M2Payload.decode(wrapped).input().bytes());
    }

    @Test void refusesMissingNullUnknownAndWrongVersionRoutingFields() {
        for (String raw : List.of(
                "{\"schema\":\"xar.g2.m2.research-input/v1\",\"operation\":\"event_before\"}",
                "{\"schema\":\"xar.g2.m2.research-input/v1\",\"operation\":\"event_before\",\"input\":null}",
                "{\"schema\":\"xar.g2.m2.research-input/v1\",\"operation\":true,\"input\":{}}",
                "{\"schema\":\"xar.g2.m2.research-input/v1\",\"operation\":\"publish_knowledge\",\"input\":{}}",
                "{\"schema\":\"xar.g2.m2.research-input/v2\",\"operation\":\"event_before\",\"input\":{}}",
                "{\"schema\":\"xar.g2.m2.research-input/v1\",\"operation\":\"event_before\",\"input\":{},\"write_root\":\"caller\"}")) {
            ProjectionJson wrapper = ProjectionJson.object(raw.getBytes(StandardCharsets.UTF_8), M2Payload.MAX_BYTES);
            assertThrows(IllegalArgumentException.class, () -> M2Payload.decode(wrapper));
        }
    }
}
