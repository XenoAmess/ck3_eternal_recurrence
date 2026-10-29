package org.xar.ck3.control.g2.m7;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m7.CheckpointContinuity.GameIdentity;
import org.xar.ck3.control.g2.m7.CheckpointContinuity.Observation;

/** Original raw floating tokens must reach their typed validator without a JSON text roundtrip. */
class M7NestedTokenTest {
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static String text(byte[] value) { return new String(value, StandardCharsets.UTF_8); }
    private static Observation frame() {
        return new Observation("synthetic-token-machine", "a".repeat(64),
                new GameIdentity(10, "20261023123045.123456+480", "D:\\game\\ck3.exe"), "native:8", 9, 8,
                "native-100-fixture", 100, 53279400, OrdinaryCampaignGoal.newGoal("native-100-fixture", 100), null, null);
    }
    @Test void directTreeGoalAndPlanDecodersRejectTheirOriginalFloatingTokens() {
        String goal = text(GoalCodec.encodeGoal(frame().goal()));
        String plan = text(GoalCodec.encodePlan(OrdinaryCampaignGoal.plan(frame().goal())));
        assertThrows(IllegalArgumentException.class, () -> GoalCodec.parseGoal(StrictJson.parse(bytes(
                goal.replace("\"format_version\":1", "\"format_version\":1.0")))));
        assertThrows(IllegalArgumentException.class, () -> GoalCodec.parsePlan(StrictJson.parse(bytes(
                plan.replace("\"priority\":100", "\"priority\":100.0")))));
    }
    @Test void originalConsumerBytesRejectNestedFrameAndGoalFloatingControlIds() {
        String observation = text(CheckpointContinuity.encodeObservation(frame()));
        for (String field : List.of("revision", "native_revision", "actor_character_id", "current_character_id")) {
            String old = switch (field) {
                case "revision" -> "9";
                case "native_revision" -> "8";
                default -> "100";
            };
            String malformed = observation.replace("\"" + field + "\":" + old, "\"" + field + "\":" + old + ".0");
            byte[] input = bytes("{\"schema\":\"xar.g2.m7.ordinary-plan-input/v1\",\"publication\":\"ordinary_plan\","
                    + "\"observation\":" + malformed + ",\"selected_step\":\"life-advance\",\"government_context\":null}");
            assertThrows(IllegalArgumentException.class, () -> M7OrdinaryPlanConsumer.compose(input), field);
        }
    }
    @Test void persistedOriginalConsumerBytesRejectAFloatPriorityWithoutReencodingItFirst() {
        var consumed = M7OrdinaryPlanConsumer.consume(M7OrdinaryPlanConsumer.Publication.ORDINARY_PLAN,
                frame(), "life-advance", Optional.empty());
        String valid = text(M7OrdinaryPlanConsumer.encode(consumed));
        assertThrows(IllegalArgumentException.class, () -> M7OrdinaryPlanConsumer.decode(bytes(
                valid.replace("\"priority\":100", "\"priority\":100.0"))));
    }
}
