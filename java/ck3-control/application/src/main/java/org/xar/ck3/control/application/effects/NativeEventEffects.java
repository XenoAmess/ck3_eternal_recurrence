package org.xar.ck3.control.application.effects;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.planning.events.NativeEventPostconditionPort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.eventmaterial.Bookmark1070Material;
import org.xar.ck3.control.wave2.events.eventmaterial.RiteGrowthMaterial;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Sole mutable-event projector plus durable replay of its actual original frames and material reads. */
public final class NativeEventEffects implements NativeEffectRegistry.Observer {
    /** The installed typed transport decoder remains authoritative; this adapter only retains its complete JSON projection. */
    public record MaterialQuery<T>(ReadContract<T> contract, Function<T, RawJson> encode, Function<OpportunityJson.Obj, OpportunityJson.Obj> arguments) implements EventMaterialQuerySource<T> {
        public MaterialQuery { Objects.requireNonNull(contract); Objects.requireNonNull(encode); Objects.requireNonNull(arguments); }
        @Override public OperationKey operation() { return contract.operation(); }
        @Override public EventMaterialQuerySource.Resolved<T> resolve(EventMaterialQuerySource.Frame frame) {
            return new EventMaterialQuerySource.Resolved<>(contract, new PlanningReadRequest(frame.before(), frame.source(), frame.sessionId(),
                operation(), Objects.requireNonNull(arguments.apply(frame.semantic())), frame.deadline()), encode, Optional.empty());
        }
        @Override public EventMaterialQuerySource.Resolved<T> restore(EventMaterialQuerySource.Frame frame, PlanningReadReceipt original,
                Optional<ExactRef> context, ActionPorts.OutcomeArchive archive) {
            StrictJson.require(context.isEmpty(), "fixed material contract cannot consume a dynamic family preimage");
            return resolve(frame);
        }
    }
    public record MaterialQueries(Optional<EventMaterialQuerySource<?>> armyStrength, Optional<EventMaterialQuerySource<?>> religionContext) {
        public MaterialQueries { Objects.requireNonNull(armyStrength); Objects.requireNonNull(religionContext); }
    }
    /** Selects only readers actually installed in this command's current observation scope. */
    @FunctionalInterface
    public interface MaterialQuerySelection {
        MaterialQueries forCommand(ActionCommand command);
    }
    private enum Interpretation { LIVE, ARCHIVED }
    private enum EventResultVersion { LEGACY_ARCHIVE, ACTUAL_AFTER_V2, ACTUAL_AFTER_V3 }
    private static final String EVENT_RESULT_SCHEMA_V2="xar.java-native-event-result/v2";
    private static final String EVENT_RESULT_SCHEMA_V3="xar.java-native-event-result/v3";
    private record ReadValue(PlanningReadReceipt receipt, RawJson value, EventMaterialQuerySource.Resolved<?> resolved, Interpretation interpretation) {
        private ReadValue { Objects.requireNonNull(receipt); Objects.requireNonNull(value); Objects.requireNonNull(resolved); Objects.requireNonNull(interpretation); }
    }
    /** Receives the exact independent frames only after the original durable basis exists. */
    @FunctionalInterface
    public interface ObservedAfter {
        void record(ActionCommand command, ActionState.Attempt attempt, NativeEffectSnapshots.Pair actualPair,
                    NativeEffectRegistry.Projected actualWithEvidence);
        /** Actual diagnostic only. It is never an EffectObserved or permission to replay. */
        default void recordUnsettled(ActionCommand command,ActionState.Attempt attempt,UnsettledObservation actual) { }
        /** Explicitly disables incident journaling; this does not qualify an incident-collection deployment. */
        static ObservedAfter none() { return (command, attempt, actualPair, actualWithEvidence) -> { }; }
    }
    public record UnsettledObservation(NativeEffectSnapshots.Pair frames,NativeActionPort.DispatchOutcome dispatch,String reason) {
        public UnsettledObservation { Objects.requireNonNull(frames);Objects.requireNonNull(dispatch);StrictJson.text(reason); }
    }
    private final ObservedAfter observedAfter;
    private final NativeEffectSnapshots snapshots;
    private final PlanningReadPort reads;
    private final MaterialQuerySelection queries;

    /** Non-journal consumers only. Production incident collection must use the four-argument constructor. */
    public NativeEventEffects(NativeEffectSnapshots snapshots, PlanningReadPort reads, MaterialQueries queries) {
        this(snapshots, reads, queries, ObservedAfter.none());
    }
    public NativeEventEffects(NativeEffectSnapshots snapshots, PlanningReadPort reads, MaterialQueries queries, ObservedAfter observedAfter) {
        this(snapshots, reads, constantQueries(queries), observedAfter);
    }
    public NativeEventEffects(NativeEffectSnapshots snapshots, PlanningReadPort reads, MaterialQuerySelection queries, ObservedAfter observedAfter) {
        this.snapshots = Objects.requireNonNull(snapshots); this.reads = Objects.requireNonNull(reads); this.queries = Objects.requireNonNull(queries);
        this.observedAfter = Objects.requireNonNull(observedAfter);
    }
    private static MaterialQuerySelection constantQueries(MaterialQueries queries) {
        Objects.requireNonNull(queries); return command -> queries;
    }
    public static boolean supports(OperationKey operation) {
        String key = Objects.requireNonNull(operation).value();
        return key.matches("select-event-option-[1-9][0-9]{0,8}") || List.of("accept-pending-character-interaction",
            "reject-pending-character-interaction", "block-pending-character-interaction", "acknowledge-pending-character-interaction").contains(key);
    }
    @Override public NativeEffectRegistry.Projected observe(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch) {
        StrictJson.require(supports(command.operation()), "exact event/pending action required");
        NativeEffectSnapshots.Pair pair = snapshots.read(command, attempt);
        // A material query is useful only after the original instance has actually advanced.
        if (facts(command, pair.after()).isEmpty()) {
            String reason="old event/pending instance remains or its later binding is unavailable";
            observedAfter.recordUnsettled(command,attempt,new UnsettledObservation(pair,dispatch,reason));
            return NativeEffectRegistry.Projected.pending(reason,List.of(pair.after().originalEvidence()));
        }
        Optional<EventMaterialQuerySource<?>> selected = query(command, Objects.requireNonNull(queries.forCommand(command)));
        List<ReadValue> material = new ArrayList<>();
        selected.ifPresent(source -> read(source, frame(pair.after(), ActionObservationWindow.deadline(command)), reads).ifPresent(material::add));
        snapshots.withArchive(archive -> {
            for (ReadValue read : material) read.resolved().replayContext().ifPresent(ref -> requireContext(archive, ref));
            return null;
        });
        NativeEffectRegistry.Projected projected = project(command, attempt, dispatch, pair, selected, material,EventResultVersion.ACTUAL_AFTER_V3);
        if (!(projected.result() instanceof ActionPorts.EffectObserved)) return projected;
        List<ExactRef> contexts = material.stream().flatMap(read -> read.resolved().replayContext().stream()).toList();
        ExactRef basis = snapshots.evidence(command, attempt, pair, material.stream().map(ReadValue::receipt).toList(), projected.compatibleResult().orElseThrow(), contexts);
        List<ExactRef> closure = new ArrayList<>(); closure.add(basis); closure.addAll(contexts);
        NativeEffectRegistry.Projected durable = NativeEffectSnapshots.withEvidence(projected, closure);
        // UNKNOWN transport may have a real independent after-frame. Only EffectObserved reaches here;
        // pending or an ACK with an unchanged modal cannot manufacture an after incident.
        observedAfter.record(command, attempt, pair, durable);
        return durable;
    }
    private static Optional<EventMaterialQuerySource<?>> query(ActionCommand command, MaterialQueries queries) {
        OpportunityJson.Value value = command.arguments().get("event_material_postcondition");
        if (!(value instanceof OpportunityJson.Obj expectation)) return Optional.empty();
        OpportunityJson.Value key = expectation.get("event_definition_key");
        if (new OpportunityJson.Text(Bookmark1070Material.EVENT).equals(key)) return queries.armyStrength();
        if (new OpportunityJson.Text(RiteGrowthMaterial.EVENT).equals(key)) return queries.religionContext();
        return Optional.empty();
    }
    private static EventMaterialQuerySource.Frame frame(Complete actual, java.time.Instant deadline) {
        return new EventMaterialQuerySource.Frame(actual.identity(), actual.source(), actual.sessionId(), actual.semantic(), deadline);
    }
    private static <T> Optional<ReadValue> read(EventMaterialQuerySource<T> source, EventMaterialQuerySource.Frame frame, PlanningReadPort reads) {
        var resolved = Objects.requireNonNull(source.resolve(frame)); resolved.requireFrame(frame, source.operation());
        PlanningReadResult<T> result = reads.read(resolved.contract(), resolved.request());
        if (!(result instanceof PlanningReadResult.Known<T> known)) return Optional.empty();
        return Optional.of(new ReadValue(known.receipt(), Objects.requireNonNull(resolved.encode().apply(known.value())), resolved, Interpretation.LIVE));
    }
    private static Optional<List<org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedValue>> facts(ActionCommand command, Complete after) {
        var provenance = new ObservationProvenance.Push(after.identity().frame().snapshotId(), after.identity().frame().identity().nativeRevision(), after.originalEvidence());
        var bound = new NativeEventPostconditionPort.BoundSnapshot(after.identity(), after.source(), after.sessionId(), after.semantic(),
            provenance, after.observedAt(), after.originalEvidence());
        return NativeEventPostconditionPort.project(command.before(), command.source(), command.sessionId(), command.expected(), command.arguments(), bound);
    }
    private static NativeEffectRegistry.Projected project(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch,
            NativeEffectSnapshots.Pair pair, Optional<EventMaterialQuerySource<?>> selected, List<ReadValue> material,EventResultVersion eventResultVersion) {
        StrictJson.require(supports(command.operation()) && material.size() <= 1, "one source-bound event material read at most");
        StrictJson.require(pair.before().identity().equals(command.before()) && pair.before().source().equals(command.source())
            && pair.before().sessionId().equals(command.sessionId()) && pair.before().originalEvidence().equals(attempt.guard().nativeEvidence()), "original event before frame differs");
        var actual = facts(command, pair.after());
        if (actual.isEmpty()) return NativeEffectRegistry.Projected.pending("independent event instance/material not observed", List.of(pair.after().originalEvidence()));
        JsonNode additional = null;
        if (!material.isEmpty()) {
            StrictJson.require(selected.isPresent(), "unexpected event material read");
            ReadValue read = material.getFirst(); EventMaterialQuerySource<?> source = selected.orElseThrow();
            NativeEffectSnapshots.requireAfterRead(command, attempt, pair.after(), read.receipt(), source.operation());
            read.resolved().requireFrame(frame(pair.after(), read.receipt().request().deadline()), source.operation());
            RawJson decoded = read.interpretation() == Interpretation.ARCHIVED ? read.resolved().replay(read.receipt()) : read.resolved().decode(read.receipt());
            StrictJson.require(decoded.equals(read.value()), "typed event material projection changed after original decode");
            additional = EffectJson.parse(decoded);
        }
        ObjectNode compatible = StrictJson.object();
        if (dispatch instanceof NativeActionPort.AckReceived ack && ack.originalResultToken().isPresent()) {
            compatible = EffectJson.object(EffectJson.parse(ack.originalResultToken().orElseThrow())).deepCopy();
            StrictJson.require(command.operation().value().equals(StrictJson.text(compatible.get("step"))), "event original action token changed exact step");
        }
        compatible.remove("event_material_query_context");
        if (!material.isEmpty()) {
            ReadValue read = material.getFirst();
            if (read.resolved().replayContext().isPresent()) compatible.set("event_material_query_context",
                compatibleContext(read, read.resolved().replayContext().orElseThrow()));
        }
        compatible.put("step", command.operation().value()).put("progress_status", "postcondition");
        if (command.operation().value().startsWith("select-event-option-")) {
            ObjectNode selection = EventSelectionMaterial.selection(command, pair, additional);
            compatible.set("event_selection", selection);
            if(eventResultVersion!=EventResultVersion.LEGACY_ARCHIVE) {
            // Native ACKs can describe the pre-dispatch frame. The public Driver result uses
            // this independent changed frame, exactly as the original event-selection path did.
            ObjectNode changed = EffectJson.object(pair.after().semantic());
            compatible.set("active_event", changed.get("active_event"));
            compatible.put("paused", true).put("snapshot_id", pair.after().identity().frame().snapshotId())
                .put("revision", pair.after().identity().frame().revision());
            // These are the original select_event_option service metadata, bound to the
            // sole independently checked selection rather than an unverified ACK mirror.
            compatible.set("event_instance_id", selection.get("old_event_instance_id"));
            compatible.set("option_number", selection.get("selected_option_number"));
            compatible.set("option_index", selection.get("selected_native_option_index"));
            compatible.put("event_result_projection_schema",eventResultVersion==EventResultVersion.ACTUAL_AFTER_V2?EVENT_RESULT_SCHEMA_V2:EVENT_RESULT_SCHEMA_V3);
            }
            Optional<ObjectNode> evaluation = EventSelectionMaterial.evaluation(command, selection);
            if (evaluation.isPresent()) compatible.set("event_material_postcondition", evaluation.orElseThrow());
        } else {
            ObjectNode pending = compatible.putObject("pending_character_interaction_selection");
            pending.put("postcondition_verified", true).put("starting_snapshot_id", pair.before().identity().frame().snapshotId())
                .put("ending_snapshot_id", pair.after().identity().frame().snapshotId());
            if(eventResultVersion==EventResultVersion.ACTUAL_AFTER_V3) {
                ObjectNode original=EffectJson.object(EffectJson.object(pair.before().semantic()).get("pending_character_interaction"));
                ObjectNode changed=EffectJson.object(pair.after().semantic());
                JsonNode remaining=changed.get("pending_character_interaction");
                StrictJson.require(remaining!=null&&(remaining.isNull()||remaining.isObject()),"explicit actual remaining pending observation required");
                String operation=command.operation().value();
                String status=operation.equals("acknowledge-pending-character-interaction")?"acknowledged"
                    :operation.startsWith("accept-")?"accepted":"rejected";
                ObjectNode result=compatible.putObject("interaction_result").put("status",status);
                result.set("instance_id",original.get("instance_id"));
                JsonNode sender=original.get("sender_character_id");
                if(sender==null)result.putNull("sender_character_id");else result.set("sender_character_id",sender);
                compatible.set("remaining_pending_character_interaction",remaining);
                compatible.put("paused",true).put("snapshot_id",pair.after().identity().frame().snapshotId())
                    .put("revision",pair.after().identity().frame().revision()).put("event_result_projection_schema",EVENT_RESULT_SCHEMA_V3);
            }
        }
        var after = pair.after();
        var proof = new ActionState.EffectObservation(after.identity(), after.source(), after.sessionId(), command.expected().observerSchema(), actual.orElseThrow(),
            new ObservationProvenance.Push(after.identity().frame().snapshotId(), after.identity().frame().identity().nativeRevision(), after.originalEvidence()),
            after.observedAt(), after.originalEvidence(), List.of());
        ActionEffects.validate(command, attempt, new ActionState.Applied(proof));
        return new NativeEffectRegistry.Projected(new ActionPorts.EffectObserved(proof), Optional.of(EffectJson.raw(compatible)));
    }
    private static ObjectNode compatibleContext(ReadValue read, ExactRef reference) {
        ObjectNode context = StrictJson.object().put("schema", "xar.event-material-query-context/v1")
            .put("operation", read.receipt().request().operation().value()).put("contract_id", read.receipt().contractId())
            .put("request_id", read.receipt().requestId());
        context.set("original_context", reference.toJson()); return context;
    }
    private static Optional<ExactRef> context(RawJson compatible, PlanningReadReceipt original) {
        JsonNode raw = EffectJson.object(EffectJson.parse(compatible)).get("event_material_query_context");
        if (raw == null) return Optional.empty();
        ObjectNode node = StrictJson.object(raw, Set.of("schema", "operation", "contract_id", "request_id", "original_context"));
        StrictJson.require("xar.event-material-query-context/v1".equals(StrictJson.text(node.get("schema")))
            && original.request().operation().value().equals(StrictJson.text(node.get("operation")))
            && original.contractId().equals(StrictJson.text(node.get("contract_id"))) && original.requestId().equals(StrictJson.text(node.get("request_id"))),
            "archived material context crossed its exact original read");
        return Optional.of(ExactRef.fromJson(node.get("original_context")));
    }
    private static void requireContext(ActionPorts.OutcomeArchive archive, ExactRef ref) {
        RawJson raw = Objects.requireNonNull(archive.loadMaterial(ref));
        StrictJson.require(raw.bytes().length == ref.bytes() && ActionCodec.sha256(raw.bytes()).equals(ref.sha256()), "original material context archive bytes changed");
    }
    private static <T> ReadValue restore(EventMaterialQuerySource<T> source, Complete originalFrame, PlanningReadReceipt original,
            Optional<ExactRef> context, ActionPorts.OutcomeArchive archive) {
        context.ifPresent(ref -> requireContext(archive, ref));
        var frame = frame(originalFrame, original.request().deadline());
        var resolved = Objects.requireNonNull(source.restore(frame, original, context, archive)); resolved.requireFrame(frame, source.operation());
        StrictJson.require(resolved.replayContext().equals(context), "material replay substituted its original context reference");
        return new ReadValue(original, resolved.replay(original), resolved, Interpretation.ARCHIVED);
    }
    public static NativeRecordedEvidenceVerifier.Binding archivedVerifier(OperationKey operation, ExactRef source,
            NativeEffectEvidence.FrameLoader frames, MaterialQueries queries) {
        StrictJson.require(supports(operation), "exact event/pending verifier operation required"); Objects.requireNonNull(frames); Objects.requireNonNull(queries);
        return new NativeRecordedEvidenceVerifier.Binding(operation, source, (head, receipt, archive) -> {
            NativeEffectEvidence.Original original = NativeEffectEvidence.load(receipt, archive, frames);
            var settled = (ActionState.Settled) receipt.state();
            Optional<EventMaterialQuerySource<?>> selected = query(receipt.command(), queries);
            StrictJson.require(original.independentReads().size() <= 1 && (original.independentReads().isEmpty() || selected.isPresent()), "event archive contains an unregistered material read");
            if (original.independentReads().isEmpty()) StrictJson.require(EffectJson.object(EffectJson.parse(original.compatibleResult())).get("event_material_query_context") == null,
                "material context without an original independent read");
            List<ReadValue> material = original.independentReads().stream().map(read -> restore(selected.orElseThrow(), original.frames().after(), read,
                context(original.compatibleResult(), read), archive)).toList();
            StrictJson.require(original.supportingMaterials().equals(material.stream().flatMap(read -> read.resolved().replayContext().stream()).toList()),
                "event material context differs from its explicit original basis closure");
            NativeEffectRegistry.Projected replayed = project(receipt.command(), settled.attempt(), settled.dispatch(), original.frames(), selected, material,eventResultVersion(original.compatibleResult()));
            replayed = NativeEffectSnapshots.withEvidence(replayed, ((ActionState.Applied) settled.settlement()).observation().supportingEvidence());
            NativeEffectEvidence.requireSame(settled.settlement(), replayed, original.compatibleResult());
        });
    }
    /** Missing marker is the exact old archive scope, never a new live fallback or current-after assertion. */
    private static EventResultVersion eventResultVersion(RawJson original) {
        JsonNode marker=EffectJson.object(EffectJson.parse(original)).get("event_result_projection_schema");
        if(marker==null)return EventResultVersion.LEGACY_ARCHIVE;
        StrictJson.require(marker.isTextual(),"unknown explicit event result archive projection version");
        if(EVENT_RESULT_SCHEMA_V2.equals(marker.textValue()))return EventResultVersion.ACTUAL_AFTER_V2;
        StrictJson.require(EVENT_RESULT_SCHEMA_V3.equals(marker.textValue()),"unknown explicit event result archive projection version");
        return EventResultVersion.ACTUAL_AFTER_V3;
    }
}
