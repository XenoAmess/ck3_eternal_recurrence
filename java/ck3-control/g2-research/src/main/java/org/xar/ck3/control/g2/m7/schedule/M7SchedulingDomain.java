package org.xar.ck3.control.g2.m7.schedule;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.core.StreamReadFeature;
import java.io.IOException;
import java.util.HashSet;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Domain;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.m7.M7OrdinaryPlanConsumer;
import org.xar.ck3.control.g2.m7.M7Research;

/** Additive single-host M7 provider; the established M7 producer operations retain their implementation. */
public final class M7SchedulingDomain implements G2Domain {
    private static final JsonFactory JSON = JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build();
    private final M7Research existing = new M7Research();
    public enum Operation {
        NEW("ordinary_schedule_new"), READ("ordinary_schedule_read"),
        CONTINUE("ordinary_schedule_continue"), PLAN("ordinary_schedule_plan");
        private final String wire;
        Operation(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static Optional<Operation> fromWire(String wire) {
            for (Operation operation : values()) { if (operation.wire.equals(wire)) { return Optional.of(operation); } }
            return Optional.empty();
        }
    }
    @Override public Milestone milestone() { return Milestone.M7; }
    @Override public G2Response evaluate(G2Request request) {
        StrictJson.require(request.milestone() == milestone(), "M7 scheduling request milestone required");
        byte[] originalPayload = request.payload().bytes();
        Optional<Operation> selected = Operation.fromWire(operation(originalPayload));
        if (selected.isEmpty()) { return existing.evaluate(request); }
        Operation operation = selected.orElseThrow();
        byte[] originalInput = OrdinaryCampaignScheduleCodec.field(originalPayload, "input");
        StrictJson.object(StrictJson.parse(originalInput, M7OrdinaryPlanConsumer.MAX_BYTES), fields(operation));
        byte[] result = switch (operation) {
            case NEW, READ -> OrdinaryCampaignScheduleCodec.encodeState(
                    OrdinaryCampaignScheduleCodec.decodeState(originalInput));
            case CONTINUE -> OrdinaryCampaignScheduleCodec.encodeState(
                    OrdinaryCampaignSchedule.continueAfterReconciliation(
                            OrdinaryCampaignScheduleCodec.decodeState(OrdinaryCampaignScheduleCodec.field(originalInput, "state")),
                            GoalCodec.decodeReconciliation(OrdinaryCampaignScheduleCodec.field(originalInput, "reconciliation"))));
            case PLAN -> {
                var plan = OrdinaryCampaignScheduleCodec.compose(originalInput);
                StrictJson.require(plan.ordinaryPlan().observation().machineId().equals(request.source().machineId()),
                        "ordinary schedule observation must use the request source machine");
                yield OrdinaryCampaignScheduleCodec.encodePlan(plan);
            }
        };
        return new G2Response(request.requestId(), milestone(), request.source(), ProjectionJson.object(result, ProjectionJson.MAX_BYTES));
    }
    /** Inspect only the operation, preserving the old producer's complete original bytes and budgets. */
    private static String operation(byte[] originalPayload) {
        String operation = null; Set<String> seen = new HashSet<>();
        try (JsonParser parser = JSON.createParser(originalPayload)) {
            StrictJson.require(parser.nextToken() == JsonToken.START_OBJECT, "M7 payload object required");
            while (parser.nextToken() != JsonToken.END_OBJECT) {
                StrictJson.require(parser.currentToken() == JsonToken.FIELD_NAME, "M7 payload field required");
                String field = parser.currentName(); seen.add(field); JsonToken value = parser.nextToken();
                switch (field) {
                    case "operation" -> {
                        StrictJson.require(value == JsonToken.VALUE_STRING, "M7 operation string required");
                        operation = StrictJson.text(parser.getText());
                    }
                    case "input" -> {
                        StrictJson.require(value == JsonToken.START_OBJECT, "complete original M7 input object required");
                        parser.skipChildren();
                    }
                    default -> throw new IllegalArgumentException("unexpected M7 payload field: " + field);
                }
            }
            StrictJson.require(operation != null && seen.equals(Set.of("operation", "input")) && parser.nextToken() == null,
                    "exact M7 operation/input envelope required");
            return operation;
        } catch (IOException error) { throw new IllegalArgumentException("invalid M7 scheduling envelope", error); }
    }
    private static Set<String> fields(Operation operation) {
        return switch (operation) {
            case NEW, READ -> Set.of("schema", "goal", "deadline_configuration");
            case CONTINUE -> Set.of("state", "reconciliation");
            case PLAN -> Set.of("state", "ordinary_plan", "requested_clock_target_raw");
        };
    }
}
