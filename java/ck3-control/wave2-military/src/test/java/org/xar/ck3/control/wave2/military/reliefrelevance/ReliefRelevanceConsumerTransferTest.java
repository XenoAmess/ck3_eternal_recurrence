package org.xar.ck3.control.wave2.military.reliefrelevance;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.refuge.ConsumerTransferProjectionPort;
import static org.junit.jupiter.api.Assertions.*;

final class ReliefRelevanceConsumerTransferTest {
    private static ObjectNode input() throws IOException {
        try (InputStream stream = ReliefRelevanceConsumerTransferTest.class.getResourceAsStream("/reliefrelevance/original-producer-golden-v1.json")) {
            assertNotNull(stream, "mandatory unchanged original producer golden");
            return StrictJson.parse(stream.readNBytes(71_681), 71_680).get("bases").get(1).get("request").deepCopy();
        }
    }
    private static ObjectNode request(ReliefRelevanceConsumerTransfer.Consumer consumer, ObjectNode input) {
        ObjectNode result = StrictJson.object(); result.put("schema", ReliefRelevanceConsumerTransfer.INPUT_SCHEMA);
        result.put("consumer", consumer.wire()); result.set("input", input); return result;
    }
    @Test
    void allFourRealConsumersGetTheExistingBooleanThroughTheTypedWire() throws IOException {
        ObjectNode input = input(); boolean expected = ReliefRelevancePolicy.assess(ReliefRelevanceCodec.decode(StrictJson.canonical(input))).candidateSiegeReliefRelevant();
        for (var consumer : ReliefRelevanceConsumerTransfer.Consumer.values()) {
            ConsumerTransferProjectionPort port = new ConsumerTransferProjectionPort();
            byte[] raw = StrictJson.canonical(request(consumer, input));
            assertArrayEquals(ReliefRelevanceConsumerTransfer.evaluate(raw), port.encode(port.project(port.decode(raw))));
            assertEquals(ReliefRelevanceConsumerTransfer.INPUT_MAX_BYTES, port.inputMaximumBytes());
            assertEquals(ReliefRelevanceConsumerTransfer.OUTPUT_MAX_BYTES, port.outputMaximumBytes());
            var decoded = ReliefRelevanceConsumerTransfer.decode(StrictJson.canonical(request(consumer, input)));
            var typed = ReliefRelevanceConsumerTransfer.apply(decoded);
            assertInstanceOf(ReliefRelevanceConsumerTransfer.Observed.class, typed.value());
            JsonNode wire = StrictJson.parse(ReliefRelevanceConsumerTransfer.encode(typed));
            assertEquals(expected, wire.get("value").booleanValue()); assertEquals("available", wire.get("observation_status").textValue());
            assertEquals(consumer.function(), wire.get("consumer_function").textValue());
            assertEquals(ReliefRelevanceConsumerTransfer.SOURCE_PATH, wire.get("source_path").textValue());
            assertFalse(wire.get("native_action_authorized").booleanValue());
            assertEquals(wire, StrictJson.parse(ReliefRelevanceConsumerTransfer.evaluate(StrictJson.canonical(request(consumer, input)))));
        }
    }
    @Test
    void explicitNoCandidateKeepsGreenFalseWhileMissingContractAndWrongMembershipAreNotLaundered() throws IOException {
        ObjectNode input = input(); ObjectNode frame = (ObjectNode) input.get("frame");
        frame.putNull("candidate_enemy_ref");
        var response = ReliefRelevanceConsumerTransfer.apply(ReliefRelevanceConsumerTransfer.decode(StrictJson.canonical(request(ReliefRelevanceConsumerTransfer.Consumer.RELIEF_ASSESSMENT, input))));
        assertEquals(new ReliefRelevanceConsumerTransfer.Observed(false), response.value());
        JsonNode wire = StrictJson.parse(ReliefRelevanceConsumerTransfer.encode(response));
        assertEquals(false, wire.get("value").booleanValue()); assertEquals("available", wire.get("observation_status").textValue());
        assertTrue(wire.get("required_observation").isNull());
        frame.putNull("candidate_war_ref");
        assertFalse(((ReliefRelevanceConsumerTransfer.Observed) ReliefRelevanceConsumerTransfer.apply(
                ReliefRelevanceConsumerTransfer.decode(StrictJson.canonical(request(ReliefRelevanceConsumerTransfer.Consumer.RELIEF_ASSESSMENT, input)))).value()).relevant());
        frame.remove("candidate_enemy_ref");
        assertThrows(IllegalArgumentException.class, () -> ReliefRelevanceConsumerTransfer.decode(
                StrictJson.canonical(request(ReliefRelevanceConsumerTransfer.Consumer.RELIEF_ASSESSMENT, input))));
        ObjectNode detached = input(); ObjectNode detachedFrame = (ObjectNode) detached.get("frame");
        detachedFrame.putArray("detached_wars").add(detachedFrame.get("snapshot").get("active_wars").get(0).deepCopy());
        ObjectNode reference = detachedFrame.putObject("candidate_war_ref"); reference.put("collection", "detached_wars"); reference.put("index", 0);
        JsonNode detachedWire = StrictJson.parse(ReliefRelevanceConsumerTransfer.evaluate(StrictJson.canonical(
                request(ReliefRelevanceConsumerTransfer.Consumer.RELIEF_ASSESSMENT, detached))));
        assertFalse(detachedWire.get("value").booleanValue()); assertFalse(detachedWire.get("native_action_authorized").booleanValue());
    }
    @Test
    void wrongRawObjectiveTokensAndUnknownConsumerCannotBeNormalizedIntoAnObservation() throws IOException {
        ObjectNode value = request(ReliefRelevanceConsumerTransfer.Consumer.RESERVE_RAISE, input());
        ObjectNode war = (ObjectNode) value.get("input").get("frame").get("snapshot").get("active_wars").get(0);
        war.putArray("war_objective_province_ids").add(123);
        String canonical = new String(StrictJson.canonical(value), StandardCharsets.UTF_8);
        for (String token : List.of("123.0", "true", "\"123\"")) {
            String raw = canonical.replace("\"war_objective_province_ids\":[123]", "\"war_objective_province_ids\":[" + token + "]");
            assertNotEquals(canonical, raw);
            assertThrows(IllegalArgumentException.class, () -> ReliefRelevanceConsumerTransfer.evaluate(raw.getBytes(StandardCharsets.UTF_8)));
        }
        value.put("consumer", "unmapped-service");
        assertThrows(IllegalArgumentException.class, () -> ReliefRelevanceConsumerTransfer.decode(StrictJson.canonical(value)));
    }
}
