package org.xar.ck3.control.application.planning.events;

import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.function.BiFunction;
import java.util.function.Function;
import java.util.function.Predicate;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.effects.EventMaterialQuerySource;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** One typed read publication path, with distinct material-source and original-receipt inputs. */
public final class EventReadBinding<T> {
    @FunctionalInterface public interface Publication<T> {
        EventPolicies.ReadPublication publish(PlanningRequest actual, T decoded, RawJson actualEncoded);
    }
    private sealed interface Input<T> permits Material, Receipt, ReceiptFamily { }
    /** A finite installed family resolves only the operation chosen by the existing event policy. */
    public record ReceiptResolution<T>(ReadContract<T> contract, OpportunityJson.Obj arguments,
            Function<PlanningReadResult.Known<T>,EventPolicies.ReadPublication> publication) {
        public ReceiptResolution { Objects.requireNonNull(contract); Objects.requireNonNull(arguments); Objects.requireNonNull(publication); }
    }
    @FunctionalInterface public interface ReceiptResolver<T> {
        ReceiptResolution<T> resolve(PlanningRequest actual, OperationKey selected);
    }
    private record ReceiptFamily<T>(OperationKey descriptor, Predicate<OperationKey> supports,
            ReceiptResolver<T> resolver) implements Input<T> {
        private ReceiptFamily { Objects.requireNonNull(descriptor); Objects.requireNonNull(supports); Objects.requireNonNull(resolver); }
    }
    private record Material<T>(EventMaterialQuerySource<T> query, Publication<T> publication) implements Input<T> {
        private Material { Objects.requireNonNull(query); Objects.requireNonNull(publication); }
    }
    private record Receipt<T>(ReadContract<T> contract, Function<PlanningRequest,OpportunityJson.Obj> arguments,
            Function<PlanningReadResult.Known<T>,EventPolicies.ReadPublication> publication) implements Input<T> {
        private Receipt { Objects.requireNonNull(contract); Objects.requireNonNull(arguments); Objects.requireNonNull(publication); }
    }
    private final Input<T> input;
    public EventReadBinding(EventMaterialQuerySource<T> query, Publication<T> publication) {
        input = new Material<>(query, publication);
    }
    /** Pure typed-value projections may ignore the verified encoding; no second selection is issued. */
    public EventReadBinding(EventMaterialQuerySource<T> query, BiFunction<PlanningRequest,T,EventPolicies.ReadPublication> pureProjection) {
        this(query, (actual, decoded, actualEncoded) -> pureProjection.apply(actual, decoded));
        Objects.requireNonNull(pureProjection);
    }
    private EventReadBinding(Receipt<T> receipt) { input = Objects.requireNonNull(receipt); }
    private EventReadBinding(ReceiptFamily<T> family) { input = Objects.requireNonNull(family); }
    public static <T> EventReadBinding<T> actualReceiptFamily(OperationKey descriptor, Predicate<OperationKey> supports,
            ReceiptResolver<T> resolver) {
        return new EventReadBinding<>(new ReceiptFamily<>(descriptor, supports, resolver));
    }
    public boolean supports(OperationKey selected) {
        Objects.requireNonNull(selected);
        return input instanceof ReceiptFamily<T> family ? family.supports().test(selected) : operation().equals(selected);
    }
    /** Original-receipt publishers need neither a fabricated DTO encoder nor an M2 material source. */
    public static <T> EventReadBinding<T> actualReceipt(ReadContract<T> sameContract,
            Function<PlanningRequest,OpportunityJson.Obj> arguments,
            Function<PlanningReadResult.Known<T>,EventPolicies.ReadPublication> originalPublication) {
        return new EventReadBinding<>(new Receipt<>(sameContract, arguments, originalPublication));
    }
    public EventMaterialQuerySource<T> query() {
        if (input instanceof Material<T> material) return material.query();
        throw new IllegalStateException("Original-receipt publication is not an M2 material source");
    }
    public Publication<T> publication() {
        if (input instanceof Material<T> material) return material.publication();
        throw new IllegalStateException("Original-receipt publication has no material encoding projection");
    }
    public OperationKey operation() {
        return switch (input) {
            case Material<T> material -> material.query().operation();
            case Receipt<T> receipt -> receipt.contract().operation();
            case ReceiptFamily<T> family -> family.descriptor();
        };
    }
    /** Actual typed query outcome; unavailable retains its original reason and evidence without Known credit. */
    public sealed interface Outcome permits Captured, Unavailable { }
    public record Unavailable(PlanningReadResult.Unavailable<?> result) implements Outcome {
        public Unavailable { Objects.requireNonNull(result); }
    }
    public record Captured(EventPolicies.ReadPublication publication, OperationKey operation, String requestId,
            String contractId, ExactRef originalReceipt, Optional<ExactRef> replayContext) implements Outcome {
        public Captured {
            Objects.requireNonNull(publication); Objects.requireNonNull(operation); StrictJson.text(requestId);
            StrictJson.text(contractId); Objects.requireNonNull(originalReceipt); Objects.requireNonNull(replayContext);
        }
        /** Sole history serializer for the registered core and event continuation collector. */
        public OpportunityJson.Obj history() {
            var row = new OpportunityJson.Obj(Map.of("command", new OpportunityJson.Text(operation.value()),
                    "ok", new OpportunityJson.Bool(true), "result", publication.result(),
                    "native_read_request_id", new OpportunityJson.Text(requestId),
                    "read_contract_id", new OpportunityJson.Text(contractId), "native_read_original_receipt",
                    OpportunityJson.parse(StrictJson.canonical(originalReceipt.toJson()))));
            return replayContext.map(ref -> row.with("native_read_replay_context",
                    OpportunityJson.parse(StrictJson.canonical(ref.toJson())))).orElse(row);
        }
    }
    public Outcome read(PlanningReadPort reads, PlanningRequest current) {
        Objects.requireNonNull(reads); Objects.requireNonNull(current);
        StrictJson.require(!(input instanceof ReceiptFamily<T>), "dynamic event read requires the policy's actual selected operation");
        return read(reads, current, operation());
    }
    public Outcome read(PlanningReadPort reads, PlanningRequest current, OperationKey selected) {
        return read(reads, current, selected, (actual, plan) -> { });
    }
    public Outcome read(PlanningReadPort reads, PlanningRequest current, OperationKey selected,
            EventIncidentCapturePort incidents) {
        Objects.requireNonNull(reads); Objects.requireNonNull(current); Objects.requireNonNull(incidents);
        StrictJson.require(supports(selected), "event read binding does not support the selected operation");
        if (input instanceof ReceiptFamily<T> family) {
            ReceiptResolution<T> resolved = Objects.requireNonNull(family.resolver().resolve(current, selected));
            StrictJson.require(resolved.contract().operation().equals(selected), "event family changed selected native operation");
            return readReceipt(new Receipt<>(resolved.contract(), ignored -> resolved.arguments(), resolved.publication()), reads, current, incidents);
        }
        if (input instanceof Receipt<T> receipt) return readReceipt(receipt, reads, current, incidents);
        var frame = new EventMaterialQuerySource.Frame(current.before(), current.source(), current.sessionId(),
                current.observations().snapshot(), current.deadline());
        EventMaterialQuerySource.Resolved<T> resolved = Objects.requireNonNull(query().resolve(frame));
        resolved.requireFrame(frame, operation());
        PlanningReadResult<T> result = incidents.read(reads, resolved.contract(), resolved.request(), current);
        return switch (result) {
            case PlanningReadResult.Unavailable<T> unavailable -> new Unavailable(unavailable);
            case PlanningReadResult.Known<T> known -> {
                RawJson original = resolved.decode(known.receipt());
                RawJson projected = Objects.requireNonNull(resolved.encode().apply(known.value()));
                StrictJson.require(original.equals(projected), "event typed publication differs from its original installed decoder");
                EventPolicies.ReadPublication value = Objects.requireNonNull(publication().publish(current, known.value(), projected));
                value.snapshot().ifPresent(next -> sameFrame(current.observations().snapshot(), next));
                yield captured(value, known, resolved.replayContext());
            }
        };
    }
    private Outcome readReceipt(Receipt<T> inputReceipt, PlanningReadPort reads, PlanningRequest current, EventIncidentCapturePort incidents) {
        var contract = inputReceipt.contract();
        var request = new PlanningReadRequest(current.before(), current.source(), current.sessionId(), contract.operation(),
                Objects.requireNonNull(inputReceipt.arguments().apply(current)), current.deadline());
        PlanningReadResult<T> result = incidents.read(reads, contract, request, current);
        return switch (result) {
            case PlanningReadResult.Unavailable<T> unavailable -> new Unavailable(unavailable);
            case PlanningReadResult.Known<T> known -> {
                StrictJson.require(known.receipt().request().equals(request) && known.receipt().contractId().equals(contract.contractId()),
                        "Original-receipt publication crossed its actual installed request or contract");
                // Rebuild with the sole original decoder. No DTO JSON or current-selection substitute exists here.
                var verified = new PlanningReadResult.Known<>(contract.decode(known.receipt()), known.receipt(), known.originalReceipt());
                EventPolicies.ReadPublication value = Objects.requireNonNull(inputReceipt.publication().apply(verified));
                value.snapshot().ifPresent(next -> sameFrame(current.observations().snapshot(), next));
                yield captured(value, verified, Optional.empty());
            }
        };
    }
    private Captured captured(EventPolicies.ReadPublication publication, PlanningReadResult.Known<T> known, Optional<ExactRef> replayContext) {
        return new Captured(publication, known.receipt().request().operation(), known.receipt().requestId(), known.receipt().contractId(), known.originalReceipt(), replayContext);
    }
    private static void sameFrame(OpportunityJson.Obj before, OpportunityJson.Obj after) {
        for (String key : java.util.List.of("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id", "paused", "map_ready",
                "active_event", "current_event", "pending_character_interaction", "one_life_terminal_reason"))
            StrictJson.require(Objects.equals(before.get(key), after.get(key)), "event publication changed frozen frame " + key);
        for (String key : java.util.List.of("character_id", "alive"))
            StrictJson.require(Objects.equals(field(before, "played_character", key), field(after, "played_character", key)), "event publication changed player " + key);
        for (String key : java.util.List.of("bridge_pid", "connection_generation"))
            StrictJson.require(Objects.equals(field(before, "diagnostics", key), field(after, "diagnostics", key)), "event publication changed native connection " + key);
    }
    private static OpportunityJson.Value field(OpportunityJson.Obj snapshot, String object, String key) {
        OpportunityJson.Value raw = snapshot.get(object); return raw instanceof OpportunityJson.Obj row ? row.get(key) : null;
    }
}

