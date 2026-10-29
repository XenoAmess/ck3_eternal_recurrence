package org.xar.ck3.control.wave2.military.refuge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.BooleanNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.wave2.military.exitcomparison.DefenderExitObservation;
import org.xar.ck3.control.wave2.military.exitcomparison.DefenderExitObservationCodec;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservation;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservationCodec;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegeCodec;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegePolicy;
import org.xar.ck3.control.wave2.military.reliefrelevance.ReliefRelevanceConsumerTransfer;

/** One existing operation. Every branch consumes original observations, never a qualification flag. */
public final class ConsumerTransferProjectionPort implements ProjectionPort<ConsumerTransferProjectionPort.Request, ConsumerTransferProjectionPort.Response> {
    public static final String REALM_SCHEMA = "xar.realm-siege-transfer-input.v1";
    public static final String FORMAL_SCHEMA = "xar.formal-defender-exit-transfer-input.v1";
    public static final String ORDINARY_SCHEMA = "xar.ordinary-war-exit-transfer-input.v1";
    private static final Set<String> ORDINARY_FIELDS = Set.of("before_snapshot", "post_snapshot", "action_result",
            "claims_result", "title_holder_results", "truce_result");

    /** Immutable, syntax-validated bounded JSON at codecs that already own combined decode/evaluate APIs. */
    public record SerializedProjection(byte[] bytes) {
        public SerializedProjection {
            Objects.requireNonNull(bytes);
            bytes = bytes.clone();
            StrictJson.parse(bytes, StrictJson.INPUT_MAX_BYTES);
        }
        @Override public byte[] bytes() { return bytes.clone(); }
    }
    public enum RealmConsumer { ENEMY, WAR }
    public sealed interface Request permits RefugeInput, ReliefInput, RealmInput, FormalInput, OrdinaryInput { }
    public record RefugeInput(DefenderRefugeConsumerTransfer.Request input) implements Request {
        public RefugeInput { Objects.requireNonNull(input); }
    }
    public record ReliefInput(ReliefRelevanceConsumerTransfer.Request input) implements Request {
        public ReliefInput { Objects.requireNonNull(input); }
    }
    public record RealmInput(RealmConsumer consumer, RealmSiegePolicy.Request input) implements Request {
        public RealmInput { Objects.requireNonNull(consumer); Objects.requireNonNull(input); }
    }
    public record FormalInput(SerializedProjection snapshot, boolean handoff, String selectedStep) implements Request {
        public FormalInput { Objects.requireNonNull(snapshot); }
    }
    public record OrdinaryInput(SerializedProjection adapter) implements Request {
        public OrdinaryInput {
            Objects.requireNonNull(adapter);
            StrictJson.object(StrictJson.parse(adapter.bytes()), ORDINARY_FIELDS);
        }
    }
    public sealed interface Response permits RefugeOutput, ReliefOutput, RealmOutput, FormalOutput, OrdinaryOutput { }
    public record RefugeOutput(DefenderRefugeConsumerTransfer.Response result) implements Response {
        public RefugeOutput { Objects.requireNonNull(result); }
    }
    public record ReliefOutput(ReliefRelevanceConsumerTransfer.Response result) implements Response {
        public ReliefOutput { Objects.requireNonNull(result); }
    }
    public record RealmOutput(boolean observed) implements Response { }
    public record FormalOutput(DefenderExitObservation.Result result, boolean handoff, String selectedStep) implements Response {
        public FormalOutput { Objects.requireNonNull(result); }
    }
    /** A null receipt is the original explicit not-applicable result, not a missing Response. */
    public record OrdinaryOutput(OrdinaryWarExitObservation.Receipt result) implements Response { }

    @Override public ProjectionOperation operation() { return ProjectionOperation.MILITARY_CONSUMER_TRANSFER; }
    @Override public int inputMaximumBytes() { return 131_072; }
    @Override public int outputMaximumBytes() { return 65_536; }

    @Override public Request decode(byte[] raw) {
        ObjectNode node = StrictJson.object(StrictJson.parse(raw, inputMaximumBytes()), Set.of("schema", "consumer", "input"));
        String schema = StrictJson.text(node.get("schema"));
        if (DefenderRefugeConsumerTransfer.INPUT_SCHEMA.equals(schema)) {
            return new RefugeInput(DefenderRefugeConsumerTransfer.decode(raw));
        }
        if (ReliefRelevanceConsumerTransfer.INPUT_SCHEMA.equals(schema)) {
            return new ReliefInput(ReliefRelevanceConsumerTransfer.decode(raw));
        }
        String consumer = StrictJson.text(node.get("consumer"));
        return switch (schema) {
            case REALM_SCHEMA -> new RealmInput(switch (consumer) {
                case "realm_enemy" -> RealmConsumer.ENEMY;
                case "realm_war" -> RealmConsumer.WAR;
                default -> throw new IllegalArgumentException("unknown original realm consumer");
            }, RealmSiegeCodec.decode(serialized(node.get("input")).bytes()));
            case FORMAL_SCHEMA -> {
                boolean handoff = switch (consumer) {
                    case "formal_observer" -> false;
                    case "formal_strategy" -> true;
                    default -> throw new IllegalArgumentException("unknown original formal consumer");
                };
                ObjectNode input = StrictJson.object(node.get("input"), Set.of("snapshot", "selected_step"));
                JsonNode selected = input.get("selected_step");
                StrictJson.require(selected.isNull() || selected.isTextual(), "nullable selected step string required");
                StrictJson.require(handoff || selected.isNull(), "observer has no tactical handoff input");
                yield new FormalInput(serialized(input.get("snapshot")), handoff, selected.isNull() ? null : selected.textValue());
            }
            case ORDINARY_SCHEMA -> {
                StrictJson.require("ordinary_composer".equals(consumer), "unknown original ordinary composer");
                StrictJson.object(node.get("input"), ORDINARY_FIELDS);
                yield new OrdinaryInput(serialized(node.get("input")));
            }
            default -> throw new IllegalArgumentException("unknown military transfer schema");
        };
    }

    private static SerializedProjection serialized(JsonNode node) {
        Objects.requireNonNull(node);
        // Jackson retains numeric token kind (1.0 remains a decimal); canonical() would reject it too early.
        return new SerializedProjection(node.toString().getBytes(StandardCharsets.UTF_8));
    }

    @Override public Response project(Request request) {
        Objects.requireNonNull(request);
        return switch (request) {
            case RefugeInput refuge -> new RefugeOutput(DefenderRefugeConsumerTransfer.apply(refuge.input()));
            case ReliefInput relief -> new ReliefOutput(ReliefRelevanceConsumerTransfer.apply(relief.input()));
            case RealmInput realm -> new RealmOutput(realm.consumer() == RealmConsumer.ENEMY
                    ? RealmSiegePolicy.qualifies(realm.input().snapshot(), realm.input().candidateWar(), realm.input().candidateEnemy())
                    : RealmSiegePolicy.warQualifies(realm.input().snapshot(), realm.input().candidateWar()));
            case FormalInput formal -> new FormalOutput(DefenderExitObservationCodec.decodeAndObserve(formal.snapshot().bytes()),
                    formal.handoff(), formal.selectedStep());
            case OrdinaryInput ordinary -> new OrdinaryOutput(OrdinaryWarExitObservationCodec.decodeAndCompose(ordinary.adapter().bytes()));
        };
    }

    @Override public byte[] encode(Response response) {
        Objects.requireNonNull(response);
        // Expected schema/type refusals occur at decode, not through a catch-all project exception translation.
        // Existing combined codecs preserve their own RED/unbound branches; algorithm/serializer bugs stay INTERNAL_ERROR.
        return switch (response) {
            case RefugeOutput refuge -> DefenderRefugeConsumerTransfer.encode(refuge.result()); // original 16 KiB
            case ReliefOutput relief -> ReliefRelevanceConsumerTransfer.encode(relief.result()); // original 16 KiB
            case RealmOutput realm -> StrictJson.canonical(BooleanNode.valueOf(realm.observed()), StrictJson.OUTPUT_MAX_BYTES);
            case FormalOutput formal -> formal.handoff()
                    ? DefenderExitObservationCodec.encodeWithContinuationHandoff(formal.result(), formal.selectedStep())
                    : DefenderExitObservationCodec.encode(formal.result()); // original 64 KiB
            case OrdinaryOutput ordinary -> OrdinaryWarExitObservationCodec.encode(ordinary.result()); // original 64 KiB
        };
    }
}
