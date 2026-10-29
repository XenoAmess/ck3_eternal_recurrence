package org.xar.ck3.control.wave2.military.refuge;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;

/** Mandatory old producer vectors through the actual single port, not a replacement oracle. */
final class BattleProducerProjectionPortTest {
    private final ConsumerTransferProjectionPort port = new ConsumerTransferProjectionPort();

    @Test void realmOriginalGoldensReachBothOriginalBooleanApis() throws Exception {
        JsonNode golden = resource("/realmsiege/original-producer-golden-v1.json.gz");
        assertEquals(32, golden.get("cases").size());
        for (JsonNode vector : golden.get("cases")) {
            assertEquals(vector.get("expected").get("candidate_enemy_scope_observed"),
                    call(ConsumerTransferProjectionPort.REALM_SCHEMA, "realm_enemy", vector.get("request")));
            assertEquals(vector.get("expected").get("candidate_war_scope_observed"),
                    call(ConsumerTransferProjectionPort.REALM_SCHEMA, "realm_war", vector.get("request")));
        }
    }

    @Test void formalOriginalObserverAndActualStrategyHandoffVectorsRemainSeparate() throws Exception {
        JsonNode golden = resource("/exitcomparison/producer-golden-v1.json");
        assertEquals(16, golden.get("cases").size());
        JsonNode current = null;
        for (JsonNode vector : golden.get("cases")) {
            ObjectNode input = StrictJson.object(); input.set("snapshot", vector.get("snapshot")); input.putNull("selected_step");
            assertEquals(vector.get("expected"), call(ConsumerTransferProjectionPort.FORMAL_SCHEMA, "formal_observer", input));
            if ("current-native-options".equals(vector.get("name").textValue())) { current = vector.get("snapshot"); }
        }
        assertNotNull(current);
        for (JsonNode vector : golden.get("handoffs")) {
            ObjectNode input = StrictJson.object(); input.set("snapshot", current); input.set("selected_step", vector.get("selected_step"));
            JsonNode result = call(ConsumerTransferProjectionPort.FORMAL_SCHEMA, "formal_strategy", input);
            assertEquals(vector.get("expected"), result.get("continuation_handoff"));
            assertTrue(result.get("action_literal").isNull());
        }
    }

    @Test void ordinaryCompleteComposerClosureAnd4096TargetBoundaryUseOriginalResults() throws Exception {
        JsonNode golden = resource("/exitresult/producer-golden-v1.json");
        assertEquals(18, golden.get("cases").size());
        for (JsonNode vector : golden.get("cases")) {
            ObjectNode input = golden.get("base_input").deepCopy();
            for (JsonNode patch : vector.get("patches")) { patch(input, patch); }
            assertEquals(vector.get("expected"), call(ConsumerTransferProjectionPort.ORDINARY_SCHEMA, "ordinary_composer", input));
        }
        JsonNode large = resource("/exitresult/large-targets-golden-v1.json");
        assertEquals(large.get("expected"), call(ConsumerTransferProjectionPort.ORDINARY_SCHEMA, "ordinary_composer", large.get("input")));
    }

    @Test void shapeTypeRefusalsHappenAtDecodeAndUnexpectedFailuresAreNotDomainMarkers() {
        assertEquals(131_072, port.inputMaximumBytes()); assertEquals(65_536, port.outputMaximumBytes());
        ObjectNode input = StrictJson.object(); input.putNull("snapshot"); input.put("selected_step", 1.0);
        byte[] invalid = envelope(ConsumerTransferProjectionPort.FORMAL_SCHEMA, "formal_strategy", input);
        var error = assertThrows(IllegalArgumentException.class, () -> port.decode(invalid));
        assertFalse(error instanceof ProjectionDomainRejection);
        assertThrows(NullPointerException.class, () -> port.project(null));
        assertThrows(NullPointerException.class, () -> port.encode(null));
        input.remove("selected_step");
        assertThrows(ContractViolationException.class, () -> port.decode(envelope(ConsumerTransferProjectionPort.FORMAL_SCHEMA, "formal_strategy", input)));
        ObjectNode ordinary = StrictJson.object(); ordinary.putNull("before_snapshot");
        assertThrows(ContractViolationException.class, () -> port.decode(envelope(ConsumerTransferProjectionPort.ORDINARY_SCHEMA, "ordinary_composer", ordinary)));
        byte[] bytes = "null".getBytes(StandardCharsets.UTF_8);
        var immutable = new ConsumerTransferProjectionPort.SerializedProjection(bytes); bytes[0] = 'x';
        assertArrayEquals("null".getBytes(StandardCharsets.UTF_8), immutable.bytes());
        byte[] accessor = immutable.bytes(); accessor[0] = 'x';
        assertArrayEquals("null".getBytes(StandardCharsets.UTF_8), immutable.bytes());
    }

    @Test void originalInner64KiBBoundaryRemainsExplicitWithoutSilentClipping() {
        byte[] accepted = ("null" + " ".repeat(65_532)).getBytes(StandardCharsets.UTF_8);
        assertEquals(65_536, new ConsumerTransferProjectionPort.SerializedProjection(accepted).bytes().length);
        byte[] rejected = ("null" + " ".repeat(65_533)).getBytes(StandardCharsets.UTF_8);
        assertThrows(ContractViolationException.class, () -> new ConsumerTransferProjectionPort.SerializedProjection(rejected));
        assertEquals(65_536, port.outputMaximumBytes());
        assertEquals(16_384, DefenderRefugeConsumerTransfer.OUTPUT_MAX_BYTES);
        assertEquals(16_384, org.xar.ck3.control.wave2.military.reliefrelevance.ReliefRelevanceConsumerTransfer.OUTPUT_MAX_BYTES);
    }

    private JsonNode call(String schema, String consumer, JsonNode input) {
        return StrictJson.parse(port.encode(port.project(port.decode(envelope(schema, consumer, input)))));
    }
    private static byte[] envelope(String schema, String consumer, JsonNode input) {
        ObjectNode value = StrictJson.object(); value.put("schema", schema); value.put("consumer", consumer); value.set("input", input);
        // Retain raw floating tokens in negative vectors; canonical() would reject them before the port.
        return value.toString().getBytes(StandardCharsets.UTF_8);
    }
    private static JsonNode resource(String name) throws Exception {
        try (InputStream original = BattleProducerProjectionPortTest.class.getResourceAsStream(name)) {
            assertNotNull(original, "mandatory original producer resource " + name);
            try (InputStream stream = name.endsWith(".gz") ? new GZIPInputStream(original) : original) {
                byte[] raw = stream.readNBytes(131_073); assertTrue(raw.length <= 131_072);
                return StrictJson.parse(raw, 131_072);
            }
        }
    }
    private static void patch(ObjectNode input, JsonNode patch) {
        JsonNode path = patch.get("path"); JsonNode owner = input;
        for (int index = 0; index < path.size() - 1; index++) {
            owner = path.get(index).isIntegralNumber() ? owner.get(path.get(index).intValue()) : owner.get(path.get(index).textValue());
        }
        JsonNode last = path.get(path.size() - 1);
        if (last.isIntegralNumber()) { ((ArrayNode) owner).set(last.intValue(), patch.get("value").deepCopy()); }
        else { ((ObjectNode) owner).set(last.textValue(), patch.get("value").deepCopy()); }
    }
}
