package org.xar.ck3.control.wave2.military.prestore;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

final class MovementConsumerTransportTest {
    private static byte[] frame(int sequence, String operation, String input) {
        ObjectNode node = StrictJson.object(); node.put("sequence", sequence); node.put("operation", operation);
        node.put("input_json", input); node.put("input_sha256", MovementConsumerTransport.sha256(input.getBytes(StandardCharsets.UTF_8)));
        return StrictJson.canonical(node, MovementConsumerTransport.MAX_FRAME_BYTES);
    }
    private static String leaf(String days) {
        return "{\"schema_version\":1,\"source\":\"native_current_disembark_penalty_days_12003\",\"status\":\"available\",\"remaining_days\":"
                + days + ",\"unavailable_reason\":null}";
    }
    @Test void actualCompiledNormalizerReceivesOriginalFloatAndBooleanTokenBytes() {
        for (String bad : new String[]{"1.0", "true", "\"1\""}) {
            String raw = leaf(bad);
            var decoded = MovementConsumerTransport.decode(frame(1, "DISEMBARK_NORMALIZE", raw), 1);
            assertEquals(raw, decoded.inputJson());
            var result = MovementConsumerTransport.evaluate(decoded);
            assertEquals(MovementConsumerTransport.Status.REJECTED, result.status());
            assertNull(result.resultJson());
            assertEquals(decoded.inputSha256(), result.inputSha256());
        }
    }
    @Test void actualJavaReturnBytesSurviveOuterSerializationAndShaRoundtrip() {
        var request = MovementConsumerTransport.decode(frame(3, "DISEMBARK_NORMALIZE", leaf("-2147483648")), 3);
        var result = MovementConsumerTransport.evaluate(request);
        assertEquals(MovementConsumerTransport.Status.ACCEPTED, result.status());
        var outer = StrictJson.parse(MovementConsumerTransport.encode(result));
        byte[] returned = outer.get("result_json").textValue().getBytes(StandardCharsets.UTF_8);
        assertEquals(result.resultSha256(), MovementConsumerTransport.sha256(returned));
        assertEquals(-2147483648L, StrictJson.parse(returned).get("remaining_days").longValue());
    }
    @Test void wrongSequenceShaFieldsAndScalarTypesFailBeforeDomainCode() {
        byte[] correct = frame(1, "MOVEMENT_NORMALIZE", "null");
        assertThrows(IllegalArgumentException.class, () -> MovementConsumerTransport.decode(correct, 2));
        ObjectNode root = (ObjectNode) StrictJson.parse(correct);
        root.put("input_sha256", "0".repeat(64));
        byte[] wrongSha = StrictJson.canonical(root);
        assertThrows(IllegalArgumentException.class, () -> MovementConsumerTransport.decode(wrongSha, 1));
        root = (ObjectNode) StrictJson.parse(correct); root.put("sequence", true);
        byte[] bool = StrictJson.canonical(root);
        assertThrows(IllegalArgumentException.class, () -> MovementConsumerTransport.decode(bool, 1));
        root = (ObjectNode) StrictJson.parse(correct); root.putNull("input_json");
        byte[] missing = StrictJson.canonical(root);
        assertThrows(IllegalArgumentException.class, () -> MovementConsumerTransport.decode(missing, 1));
        root = (ObjectNode) StrictJson.parse(correct); root.put("future_alias", true);
        byte[] extra = StrictJson.canonical(root);
        assertThrows(IllegalArgumentException.class, () -> MovementConsumerTransport.decode(extra, 1));
    }
    @Test void uncompiledStatusCannotBePromotedToExecutableQualification() {
        assertThrows(IllegalArgumentException.class, () -> ProbeCompiledMovementConsumers.decode(
                "{\"schema\":\"xar.compiled-movement-consumer-inputs/v1\",\"status\":\"SOURCE_READY_UNCOMPILED\"}".getBytes(StandardCharsets.UTF_8)));
    }
}
