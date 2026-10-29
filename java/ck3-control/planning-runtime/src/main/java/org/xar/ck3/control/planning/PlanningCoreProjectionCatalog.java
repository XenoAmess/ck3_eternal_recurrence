package org.xar.ck3.control.planning;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.planning.opportunity.ObservedOpportunitySelector;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.optionalcadence.CadenceJson;
import org.xar.ck3.control.planning.optionalcadence.CadenceModels;
import org.xar.ck3.control.planning.optionalcadence.OptionalCheckCadence;

/** Existing planning core only. The original caller retains file publication and action authority. */
public final class PlanningCoreProjectionCatalog implements ProjectionPortCatalog {
    public static final String CADENCE_REQUEST = "xar.planning.optional-cadence.request.v1";
    public static final String CADENCE_RESULT = "xar.planning.optional-cadence.result.v1";
    public static final int CADENCE_INPUT_MAX_BYTES = 196_608;
    public static final int CADENCE_OUTPUT_MAX_BYTES = 67_584;

    @Override public List<RegisteredProjection> registrations() {
        return List.of(RegisteredProjection.of(new CadencePort()),
                RegisteredProjection.of(new OpportunityPort(ProjectionOperation.PLANNING_OPPORTUNITY_SELECT)),
                RegisteredProjection.of(new OpportunityPort(ProjectionOperation.PLANNING_OPPORTUNITY_NORMALIZE)),
                RegisteredProjection.of(new OpportunityPort(ProjectionOperation.PLANNING_OBSERVED_FRAME)));
    }

    private record OpportunityPort(ProjectionOperation operation)
            implements ProjectionPort<OpportunityJson.Obj, OpportunityJson.Obj> {
        @Override public int inputMaximumBytes() { return 131_072; }
        @Override public int outputMaximumBytes() { return 131_072; }
        @Override public OpportunityJson.Obj decode(byte[] rawPayload) {
            return OpportunityJson.object(OpportunityJson.parse(rawPayload), "planning core request");
        }
        @Override public OpportunityJson.Obj project(OpportunityJson.Obj input) {
            byte[] raw = OpportunityJson.encode(input);
            byte[] result = switch (operation) {
                case PLANNING_OPPORTUNITY_SELECT -> ObservedOpportunitySelector.select(raw);
                case PLANNING_OPPORTUNITY_NORMALIZE -> ObservedOpportunitySelector.normalizeProposal(raw);
                case PLANNING_OBSERVED_FRAME -> ObservedOpportunitySelector.observedFrame(raw);
                default -> throw new IllegalArgumentException("unsupported planning core operation");
            };
            return OpportunityJson.object(OpportunityJson.parse(result), "planning core result");
        }
        @Override public byte[] encode(OpportunityJson.Obj result) { return OpportunityJson.encode(result); }
    }

    private sealed interface CadenceInput permits Load, ReadFrame, Deferred, ActionRecorded, RecordCheck,
            Requalify, DeferCouncil { }
    private record Load(CadenceModels.State state) implements CadenceInput { }
    private record ReadFrame(Optional<CadenceModels.Frame> frame) implements CadenceInput { }
    private record Deferred(CadenceModels.State state, CadenceModels.Domain domain,
                            CadenceModels.Frame current) implements CadenceInput { }
    private record ActionRecorded(CadenceModels.State state, CadenceModels.Domain domain,
                                  CadenceModels.Frame current) implements CadenceInput { }
    private record RecordCheck(CadenceModels.State state, CadenceModels.Domain domain,
                          CadenceModels.Frame current, boolean actualAction) implements CadenceInput { }
    private record Requalify(CadenceModels.State state, CadenceModels.Frame current,
                             String catalogue) implements CadenceInput { }
    private record DeferCouncil(CadenceModels.State state, CadenceModels.Frame current,
                                String evidencePath) implements CadenceInput { }

    private sealed interface OutputValue permits NullValue, BooleanValue, FrameValue, DeferredValue, DomainValue { }
    private record NullValue() implements OutputValue { }
    private record BooleanValue(boolean value) implements OutputValue { }
    private record FrameValue(Optional<CadenceModels.Frame> frame) implements OutputValue { }
    private record DeferredValue(Optional<CadenceModels.Deferred> deferred) implements OutputValue { }
    private record DomainValue(CadenceModels.Domain domain) implements OutputValue { }
    private sealed interface CadenceOutput permits StateOutput, ValueOutput { }
    private record StateOutput(CadenceModels.State state, boolean writeRequired,
                               OutputValue value) implements CadenceOutput { }
    private record ValueOutput(OutputValue value) implements CadenceOutput { }

    private static final class CadencePort implements ProjectionPort<CadenceInput, CadenceOutput> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.PLANNING_OPTIONAL_CADENCE_PROJECT; }
        @Override public int inputMaximumBytes() { return CADENCE_INPUT_MAX_BYTES; }
        @Override public int outputMaximumBytes() { return CADENCE_OUTPUT_MAX_BYTES; }

        @Override public CadenceInput decode(byte[] rawPayload) {
            JsonNode root = StrictJson.parse(rawPayload, CADENCE_INPUT_MAX_BYTES);
            StrictJson.require(root.isObject() && CADENCE_REQUEST.equals(StrictJson.text(root.get("schema"))),
                    "unknown optional cadence request schema");
            String action = StrictJson.text(root.get("action"));
            return switch (action) {
                case "load" -> {
                    fields(root, "episode_run_id", "state_json");
                    yield new Load(state(root, StrictJson.text(root.get("episode_run_id"))));
                }
                case "frame" -> {
                    fields(root, "snapshot_json");
                    yield new ReadFrame(CadenceJson.readFrame(utf8(root.get("snapshot_json"))));
                }
                case "deferred", "action_recorded", "record" -> {
                    if (action.equals("record")) { fields(root, "state_json", "current", "domain", "actual_action"); }
                    else { fields(root, "state_json", "current", "domain"); }
                    CadenceModels.Frame current = frame(root.get("current"));
                    CadenceModels.State state = state(root, current.episodeRunId());
                    CadenceModels.Domain domain = CadenceModels.Domain.fromWire(StrictJson.text(root.get("domain")));
                    if (action.equals("deferred")) { yield new Deferred(state, domain, current); }
                    if (action.equals("action_recorded")) { yield new ActionRecorded(state, domain, current); }
                    JsonNode actual = root.get("actual_action");
                    StrictJson.require(actual.isBoolean(), "actual_action must be a boolean token");
                    yield new RecordCheck(state, domain, current, actual.booleanValue());
                }
                case "requalify" -> {
                    fields(root, "state_json", "current", "native_catalogue");
                    CadenceModels.Frame current = frame(root.get("current"));
                    yield new Requalify(state(root, current.episodeRunId()), current,
                            StrictJson.text(root.get("native_catalogue")));
                }
                case "defer_council" -> {
                    fields(root, "state_json", "current", "evidence_path");
                    CadenceModels.Frame current = frame(root.get("current"));
                    yield new DeferCouncil(state(root, current.episodeRunId()), current,
                            StrictJson.text(root.get("evidence_path")));
                }
                default -> throw new IllegalArgumentException("unsupported optional cadence action");
            };
        }

        @Override public CadenceOutput project(CadenceInput input) {
            return switch (input) {
                case Load value -> new StateOutput(value.state(), false, new NullValue());
                case ReadFrame value -> new ValueOutput(new FrameValue(value.frame()));
                case Deferred value -> new ValueOutput(new DeferredValue(OptionalCheckCadence.deferred(
                        value.state(), value.domain(), value.current())));
                case ActionRecorded value -> new ValueOutput(new BooleanValue(OptionalCheckCadence.actionRecorded(
                        value.state(), value.domain(), value.current())));
                case RecordCheck value -> {
                    CadenceModels.State next = OptionalCheckCadence.record(value.state(), value.domain(),
                            value.current(), value.actualAction());
                    yield new StateOutput(next, !next.equals(value.state()), new DomainValue(value.domain()));
                }
                case Requalify value -> {
                    CadenceModels.Requalification next = OptionalCheckCadence.requalifyLifestyleFrontierOnce(
                            value.state(), value.current(), value.catalogue());
                    yield new StateOutput(next.state(), next.changed(), new BooleanValue(next.changed()));
                }
                case DeferCouncil value -> {
                    CadenceModels.State next = OptionalCheckCadence.deferCouncilTechnicalRead(
                            value.state(), value.current(), value.evidencePath());
                    yield new StateOutput(next, !next.equals(value.state()), new DomainValue(CadenceModels.Domain.COUNCIL));
                }
            };
        }

        @Override public byte[] encode(CadenceOutput result) {
            ObjectNode root = StrictJson.object(); root.put("schema", CADENCE_RESULT);
            OutputValue value;
            if (result instanceof StateOutput state) {
                root.set("state", StrictJson.parse(CadenceJson.writeState(state.state())));
                root.put("write_required", state.writeRequired()); value = state.value();
            } else if (result instanceof ValueOutput answer) {
                root.putNull("state"); root.put("write_required", false); value = answer.value();
            } else { throw new IllegalArgumentException("unknown cadence output branch"); }
            switch (value) {
                case NullValue ignored -> root.putNull("value");
                case BooleanValue answer -> root.put("value", answer.value());
                case DomainValue answer -> root.put("value", answer.domain().wire());
                case FrameValue answer -> {
                    if (answer.frame().isEmpty()) { root.putNull("value"); }
                    else {
                        CadenceModels.Frame current = answer.frame().orElseThrow();
                        root.putArray("value").add(current.episodeRunId()).add(current.dateRaw()).add(current.nativeRevision());
                    }
                }
                case DeferredValue answer -> root.set("value", StrictJson.parse(CadenceJson.writeDeferred(answer.deferred())));
            }
            return StrictJson.canonical(root, CADENCE_OUTPUT_MAX_BYTES);
        }
    }

    private static void fields(JsonNode root, String... extra) {
        java.util.HashSet<String> expected = new java.util.HashSet<>(List.of("schema", "action"));
        expected.addAll(List.of(extra)); StrictJson.object(root, Set.copyOf(expected));
    }
    private static byte[] utf8(JsonNode value) {
        return StrictJson.text(value).getBytes(StandardCharsets.UTF_8);
    }
    private static CadenceModels.State state(JsonNode root, String episode) {
        JsonNode state = root.get("state_json");
        // Keep original JSON tokens and the existing independent 64 KiB persisted-state guard.
        return state.isNull() ? CadenceModels.State.empty(episode) : CadenceJson.readState(utf8(state), episode);
    }
    private static CadenceModels.Frame frame(JsonNode value) {
        StrictJson.object(value, Set.of("episode_run_id", "date_raw", "native_revision"));
        return new CadenceModels.Frame(StrictJson.text(value.get("episode_run_id")),
                integer(value.get("date_raw")), integer(value.get("native_revision")));
    }
    private static BigInteger integer(JsonNode value) {
        StrictJson.require(value != null && value.isIntegralNumber(), "exact frame integer token required");
        return value.bigIntegerValue();
    }
}
