package org.xar.ck3.control.g2.m7;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Domain;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.wave2.governance.government.GovernmentContextCodec;

/** Executable M7 research domain. Existing process/binder/writer authorities stay outside this pure port. */
public final class M7Research implements G2Domain {
    private static final JsonFactory JSON = JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build();
    @Override public Milestone milestone() { return Milestone.M7; }
    @Override public G2Response evaluate(G2Request request) {
        StrictJson.require(request.milestone() == milestone(), "M7 request milestone required");
        Envelope envelope = envelope(request.payload().bytes());
        byte[] result = switch (envelope.operation()) {
            case "goal_new" -> newGoal(envelope.input());
            case "goal_normalize" -> GoalCodec.encodeGoal(GoalCodec.decodeGoal(envelope.input()));
            case "goal_continue" -> continueGoal(envelope.input());
            case "goal_plan" -> GoalCodec.encodePlan(OrdinaryCampaignGoal.plan(GoalCodec.decodeGoal(envelope.input())));
            case "government_context" -> GovernmentContextCodec.compose(envelope.input());
            case "government_normalize_adapter" -> GovernmentContextCodec.normalizeAdapter(envelope.input());
            case "checkpoint_compare" -> compare(envelope.input(), request.source().machineId());
            case "ordinary_plan_consume" -> consume(envelope.input(), request.source().machineId());
            default -> throw new IllegalArgumentException("unsupported M7 operation: " + envelope.operation());
        };
        return new G2Response(request.requestId(), milestone(), request.source(), ProjectionJson.object(result, ProjectionJson.MAX_BYTES));
    }
    private static byte[] newGoal(byte[] raw) {
        ObjectNode row = StrictJson.object(StrictJson.parse(raw), Set.of("campaign_id", "character_id"));
        return GoalCodec.encodeGoal(OrdinaryCampaignGoal.newGoal(StrictJson.text(row.get("campaign_id")),
                NativeCharacterId.fromJson(row.get("character_id")).value()));
    }
    private static byte[] continueGoal(byte[] raw) {
        ObjectNode row = StrictJson.object(StrictJson.parse(raw, StrictJson.EXPLICIT_MAX_BYTES), Set.of("goal", "reconciliation"));
        return GoalCodec.encodeGoal(OrdinaryCampaignGoal.continueGoal(GoalCodec.decodeGoal(StrictJson.canonical(row.get("goal"))),
                GoalCodec.decodeReconciliation(StrictJson.canonical(row.get("reconciliation"), StrictJson.EXPLICIT_MAX_BYTES))));
    }
    private static byte[] consume(byte[] raw, String machineId) {
        byte[] result = M7OrdinaryPlanConsumer.compose(raw);
        StrictJson.require(M7OrdinaryPlanConsumer.decode(result).observation().machineId().equals(machineId),
                "M7 request source machine must equal the actual plan observation machine");
        return result;
    }
    private static byte[] compare(byte[] raw, String machineId) {
        ObjectNode row = StrictJson.object(StrictJson.parse(raw, StrictJson.EXPLICIT_MAX_BYTES), Set.of("before", "after"));
        var before = CheckpointContinuity.decodeObservation(StrictJson.canonical(row.get("before"), StrictJson.EXPLICIT_MAX_BYTES));
        var after = CheckpointContinuity.decodeObservation(StrictJson.canonical(row.get("after"), StrictJson.EXPLICIT_MAX_BYTES));
        StrictJson.require(after.machineId().equals(machineId), "M7 comparison current observation uses the request source machine");
        return CheckpointContinuity.encodeComparison(CheckpointContinuity.compare(before, after));
    }
    private record Envelope(String operation, byte[] input) { }
    /** Retain the original complete input slice, including float tokens used by existing native DTOs. */
    private static Envelope envelope(byte[] raw) {
        ProjectionJson.object(raw, ProjectionJson.MAX_BYTES);
        String operation = null; byte[] input = null; Set<String> seen = new HashSet<>();
        try (JsonParser parser = JSON.createParser(raw)) {
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
                        int start = Math.toIntExact(parser.currentTokenLocation().getByteOffset()); parser.skipChildren();
                        int end = Math.toIntExact(parser.currentLocation().getByteOffset()); input = Arrays.copyOfRange(raw, start, end);
                    }
                    default -> throw new IllegalArgumentException("unexpected M7 payload field: " + field);
                }
            }
            StrictJson.require(seen.equals(Set.of("operation", "input")) && operation != null && input != null
                    && parser.nextToken() == null, "exact M7 operation/input envelope required");
            return new Envelope(operation, input);
        } catch (IOException error) { throw new IllegalArgumentException("invalid M7 payload", error); }
    }
}
