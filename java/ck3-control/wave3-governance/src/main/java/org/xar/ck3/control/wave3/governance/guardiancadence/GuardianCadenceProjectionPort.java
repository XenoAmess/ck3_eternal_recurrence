package org.xar.ck3.control.wave3.governance.guardiancadence;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.wave2.governance.educationpreference.EducationBatchJson;
import org.xar.ck3.control.wave3.governance.guardiancadence.GuardianCadenceModel.*;

/** Existing cadence operations share one typed host port and the original writer-owned state. */
public final class GuardianCadenceProjectionPort implements ProjectionPort<GuardianCadenceProjectionPort.Request, GuardianCadenceProjectionPort.Result> {
    public static final String SCHEMA = "xar.java.guardian-negative-cadence-operation/v2";
    public enum Mode {
        EVALUATE("evaluate"), SOURCE_SCOPE("source_scope"), DEFERRED("deferred"), OBSERVE("observe");
        private final String wire;
        Mode(String wire) { this.wire = wire; }
        static Mode parse(String wire) {
            for (Mode mode : values()) { if (mode.wire.equals(wire)) { return mode; } }
            throw new IllegalArgumentException("unknown guardian cadence mode");
        }
    }
    public sealed interface Request permits Evaluate, Scope, Defer, Observe { }
    public record Evaluate(Input input) implements Request { }
    public record Scope(Frame frame, Optional<ScopeMaterials> materials, Long heirId) implements Request { }
    public record Defer(State state, Optional<SourceScope> scope, Frame frame) implements Request { }
    public record Observe(State state, Optional<SourceScope> scope, Frame frame, QueryRead query,
                          List<Attempt> attempts, String selectedStep) implements Request {
        public Observe { attempts = List.copyOf(attempts); }
    }
    public sealed interface Result permits Evaluated, Scoped, DeferredResult, Observed { }
    public record Evaluated(Evaluation value) implements Result { }
    public record Scoped(Optional<SourceScope> value) implements Result { }
    public record DeferredResult(Optional<Deferred> value) implements Result { }
    public record Observed(ObservationResult value) implements Result { }

    @Override public ProjectionOperation operation() { return ProjectionOperation.EDUCATION_CADENCE; }
    @Override public int inputMaximumBytes() { return EducationBatchJson.MAX_BYTES; }
    @Override public int outputMaximumBytes() { return EducationBatchJson.MAX_BYTES; }
    @Override public Request decode(byte[] rawPayload) {
        JsonNode input = EducationBatchJson.decode(rawPayload);
        StrictJson.require(GuardianCadenceCodec.text(input, "schema").equals(SCHEMA), "guardian cadence operation schema");
        Mode mode = Mode.parse(GuardianCadenceCodec.text(input, "mode"));
        return switch (mode) {
            case EVALUATE -> {
                StrictJson.object(input, Set.of("schema", "mode", "frame", "needs", "heir_id", "state", "default_query", "attempts", "selected_step"));
                ObjectNode legacy = ((ObjectNode) input).deepCopy();
                legacy.remove("mode"); legacy.put("schema", GuardianCadenceCodec.SCHEMA);
                yield new Evaluate(GuardianCadenceCodec.projectParsedInput(legacy));
            }
            case SOURCE_SCOPE -> {
                StrictJson.object(input, Set.of("schema", "mode", "frame", "needs", "heir_id"));
                yield new Scope(GuardianCadenceCodec.frame(GuardianCadenceCodec.required(input, "frame")),
                        GuardianCadenceCodec.materials(GuardianCadenceCodec.required(input, "needs")),
                        GuardianCadenceCodec.nullableId(input, "heir_id"));
            }
            case DEFERRED -> {
                StrictJson.object(input, Set.of("schema", "mode", "frame", "state", "scope"));
                yield new Defer(GuardianCadenceCodec.state(GuardianCadenceCodec.required(input, "state")),
                        scope(input), GuardianCadenceCodec.frame(GuardianCadenceCodec.required(input, "frame")));
            }
            case OBSERVE -> {
                StrictJson.object(input, Set.of("schema", "mode", "frame", "state", "scope", "default_query", "attempts", "selected_step"));
                yield new Observe(GuardianCadenceCodec.state(GuardianCadenceCodec.required(input, "state")), scope(input),
                        GuardianCadenceCodec.frame(GuardianCadenceCodec.required(input, "frame")),
                        GuardianCadenceCodec.query(GuardianCadenceCodec.required(input, "default_query")),
                        GuardianCadenceCodec.attempts(GuardianCadenceCodec.required(input, "attempts")),
                        GuardianCadenceCodec.text(input, "selected_step"));
            }
        };
    }
    private static Optional<SourceScope> scope(JsonNode input) {
        JsonNode scope = GuardianCadenceCodec.required(input, "scope");
        return scope.isNull() ? Optional.empty() : Optional.of(GuardianCadenceCodec.sourceScope(scope));
    }
    @Override public Result project(Request request) {
        return switch (request) {
            case Evaluate value -> new Evaluated(GuardianNegativeCadence.evaluate(value.input()));
            case Scope value -> new Scoped(GuardianNegativeCadence.sourceScope(value.frame(), value.materials(), value.heirId()));
            case Defer value -> new DeferredResult(GuardianNegativeCadence.deferred(value.state(), value.scope(), value.frame()));
            case Observe value -> new Observed(GuardianNegativeCadence.observe(value.state(), value.scope(), value.frame(), value.query(), value.attempts(), value.selectedStep()));
        };
    }
    @Override public byte[] encode(Result result) {
        JsonNode output = switch (result) {
            case Evaluated value -> GuardianCadenceCodec.evaluationNode(value.value());
            case Scoped value -> value.value().<JsonNode>map(GuardianCadenceCodec::scope).orElseGet(() -> StrictJson.object().nullNode());
            case DeferredResult value -> value.value().<JsonNode>map(GuardianCadenceCodec::deferred).orElseGet(() -> StrictJson.object().nullNode());
            case Observed value -> {
                ObjectNode node = StrictJson.object();
                node.set("state", GuardianCadenceCodec.state(value.value().state()));
                node.set("observation", value.value().observation().<JsonNode>map(GuardianCadenceCodec::observation).orElseGet(() -> node.nullNode()));
                yield node;
            }
        };
        return EducationBatchJson.encode(output);
    }
}
