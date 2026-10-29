package org.xar.ck3.control.wave2.military.refuge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

final class DefenderRefugeConsumerTransferTest {
    private static ObjectNode input() throws IOException {
        try (InputStream stream = DefenderRefugeConsumerTransferTest.class.getResourceAsStream("/refuge/original-producer-golden-v1.json")) {
            assertNotNull(stream, "mandatory unchanged original producer golden");
            return StrictJson.parse(stream.readNBytes(71_681), 71_680).get("bases").get(0).get("request").deepCopy();
        }
    }
    private static ObjectNode request(DefenderRefugeConsumerTransfer.Consumer consumer, ObjectNode input) {
        ObjectNode result = StrictJson.object(); result.put("schema", DefenderRefugeConsumerTransfer.INPUT_SCHEMA);
        result.put("consumer", consumer.wire()); result.set("input", input); return result;
    }
    @Test
    void everyOriginalImportGetsItsExactExistingSerializedValueAndFixedSourceMap() throws IOException {
        ObjectNode input = input(); JsonNode expected = StrictJson.parse(DefenderRefugeCodec.evaluate(StrictJson.canonical(input)));
        for (var consumer : DefenderRefugeConsumerTransfer.Consumer.values()) {
            ConsumerTransferProjectionPort port = new ConsumerTransferProjectionPort();
            byte[] raw = StrictJson.canonical(request(consumer, input));
            assertArrayEquals(DefenderRefugeConsumerTransfer.evaluate(raw), port.encode(port.project(port.decode(raw))));
            assertEquals("military-consumer-transfer", port.operation().wire());
            var decoded = DefenderRefugeConsumerTransfer.decode(StrictJson.canonical(request(consumer, input)));
            var typed = DefenderRefugeConsumerTransfer.apply(decoded);
            JsonNode encoded = StrictJson.parse(DefenderRefugeConsumerTransfer.encode(typed));
            String field = switch (consumer) {
                case STRATEGY_CAPITALS -> "direct_vassal_capital_province_ids";
                case STRATEGY_LIFECYCLE -> "lifecycle_scope";
                case NATIVE_CAPABILITIES -> "same_frame_cached_scope";
            };
            assertEquals(expected.get(field), encoded.get("value"));
            assertEquals(consumer.sourcePath(), encoded.get("source_path").textValue());
            assertEquals(consumer.importedFunction(), encoded.get("imported_function").textValue());
            assertFalse(encoded.get("native_action_authorized").booleanValue());
            assertEquals(typed.value().available() ? "available" : "unavailable", encoded.get("observation_status").textValue());
            assertEquals(encoded, StrictJson.parse(DefenderRefugeConsumerTransfer.evaluate(StrictJson.canonical(request(consumer, input)))));
        }
    }
    @Test
    void missingScopeRemainsNullAndCompleteEmptyCapitalsRemainAnAvailableEmptyList() throws IOException {
        ObjectNode missing = input(); missing.putNull("snapshot"); missing.putNull("root"); missing.putNull("cached_query");
        for (var consumer : DefenderRefugeConsumerTransfer.Consumer.values()) {
            JsonNode value = StrictJson.parse(DefenderRefugeConsumerTransfer.evaluate(StrictJson.canonical(request(consumer, missing))));
            assertEquals("unavailable", value.get("observation_status").textValue()); assertTrue(value.get("value").isNull());
        }
        var empty = new DefenderRefugeConsumerTransfer.Response(DefenderRefugeConsumerTransfer.Consumer.STRATEGY_CAPITALS,
                new DefenderRefugeConsumerTransfer.Capitals(List.of()));
        JsonNode encoded = StrictJson.parse(DefenderRefugeConsumerTransfer.encode(empty));
        assertEquals("available", encoded.get("observation_status").textValue()); assertTrue(encoded.get("value").isEmpty());
        assertThrows(IllegalArgumentException.class, () -> new DefenderRefugeConsumerTransfer.Response(
                DefenderRefugeConsumerTransfer.Consumer.NATIVE_CAPABILITIES, new DefenderRefugeConsumerTransfer.Capitals(List.of())));
    }
    @Test
    void rawWrongIntegerTypesAndUnmappedOrAddedWrapperFieldsAreRejectedBeforeTransfer() throws IOException {
        ObjectNode value = request(DefenderRefugeConsumerTransfer.Consumer.STRATEGY_LIFECYCLE, input());
        ObjectNode snapshot = (ObjectNode) value.get("input").get("snapshot"); snapshot.put("native_revision", 123);
        String canonical = new String(StrictJson.canonical(value), StandardCharsets.UTF_8);
        for (String token : List.of("123.0", "true", "\"123\"")) {
            String raw = canonical.replace("\"native_revision\":123", "\"native_revision\":" + token);
            assertNotEquals(canonical, raw);
            assertThrows(IllegalArgumentException.class, () -> DefenderRefugeConsumerTransfer.evaluate(raw.getBytes(StandardCharsets.UTF_8)));
        }
        value.put("qualified", true);
        assertThrows(IllegalArgumentException.class, () -> DefenderRefugeConsumerTransfer.decode(StrictJson.canonical(value)));
        value.remove("qualified"); value.put("consumer", "caller-supplied-authority");
        assertThrows(IllegalArgumentException.class, () -> DefenderRefugeConsumerTransfer.decode(StrictJson.canonical(value)));
        value.put("schema", "unregistered-transfer");
        assertThrows(IllegalArgumentException.class, () -> new ConsumerTransferProjectionPort().decode(StrictJson.canonical(value)));
        assertThrows(NullPointerException.class, () -> new ConsumerTransferProjectionPort.RefugeInput(null));
    }
}
