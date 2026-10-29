package org.xar.ck3.control.application.effects;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** The composition root installs exact operations once. This class has no Native submission method. */
public final class NativeEffectRegistry implements ActionPorts.PreparationPort, ActionPorts.PostconditionPort {
    public record Projected(ActionPorts.PostconditionResult result, Optional<RawJson> compatibleResult) {
        public Projected {
            Objects.requireNonNull(result); compatibleResult = Objects.requireNonNull(compatibleResult);
            StrictJson.require(compatibleResult.isEmpty() || result instanceof ActionPorts.PauseObserved || result instanceof ActionPorts.EffectObserved || result instanceof ActionPorts.ControlObserved
                            || result instanceof ActionPorts.FrontendObserved || result instanceof ActionPorts.GameplayEntryObserved
                            || result instanceof ActionPorts.TerminalObserved || result instanceof ActionPorts.NativeSourceObserved || result instanceof ActionPorts.NormalExitPhaseObserved || result instanceof ActionPorts.OperatorRebindObserved,
                    "unverified ACK/pending cannot become a successful compatible history result");
            if (result instanceof ActionPorts.TerminalObserved terminal && compatibleResult.isPresent()) {
                var body = EffectJson.object(EffectJson.parse(compatibleResult.orElseThrow()));
                String expected = terminal.observation().disposition() instanceof ActionTerminalObservation.PrisonerTransferred ? "transferred" : "dead";
                StrictJson.require(expected.equals(StrictJson.text(body.get("status"))) && !EffectJson.bool(body.get("postcondition_verified")),
                        "non-applied terminal history cannot report successful gameplay");
            }
        }
        public static Projected pending(String reason, List<ExactRef> evidence) {
            return new Projected(new ActionPorts.Pending(reason, evidence), Optional.empty());
        }
    }
    @FunctionalInterface public interface Observer {
        Projected observe(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch);
    }
    public record Binding(OperationKey operation, ExactRef producerSource,
            ActionPorts.PreparationPort preparation, Observer observer) {
        public Binding {
            Objects.requireNonNull(operation); Objects.requireNonNull(producerSource);
            NativeStepDiscriminator.requireKind(operation, ExecutableStepBindings.Kind.ACTION);
            StrictJson.require(producerSource.bytes() > 0, "actual registered producer source required");
            Objects.requireNonNull(preparation); Objects.requireNonNull(observer);
        }
        /** Event/SAVE/clock keep their sole producer instance; absent compatible output stays absent. */
        public static Binding existing(OperationKey operation, ExactRef producerSource,
                ActionPorts.PreparationPort preparation, ActionPorts.PostconditionPort observer) {
            Objects.requireNonNull(observer);
            return new Binding(operation, producerSource, preparation,
                    (command, attempt, dispatch) -> new Projected(observer.observe(command, attempt, dispatch), Optional.empty()));
        }
    }
    private record Key(String actionId, String requestId) { }
    private final Map<OperationKey, Binding> bindings;
    private final RootExecutableBindings catalog;
    private final Map<Key, RawJson> compatible = new HashMap<>();
    private final int retainedLimit;
    private long retainedBytes;
    private static final long MAXIMUM_MATERIAL_BYTES = 16L * 1024 * 1024;

    public NativeEffectRegistry(List<Binding> installed, int retainedLimit) {
        StrictJson.require(installed != null && installed.size() <= 4096 && retainedLimit > 0 && retainedLimit <= 4096,
                "finite exact registry and history bounds required");
        Map<OperationKey, Binding> index = new HashMap<>();
        for (Binding binding : List.copyOf(installed))
            StrictJson.require(index.putIfAbsent(binding.operation(), binding) == null, "two handlers claim the same exact operation");
        this.bindings = Map.copyOf(index); this.catalog = null; this.retainedLimit = retainedLimit;
    }
    public NativeEffectRegistry(RootExecutableBindings actualCatalog, int retainedLimit) {
        this.catalog = Objects.requireNonNull(actualCatalog); this.bindings = Map.of();
        StrictJson.require(retainedLimit > 0 && retainedLimit <= 4096, "finite exact effect history bounds required"); this.retainedLimit = retainedLimit;
    }
    private Binding binding(OperationKey operation) { return catalog == null ? bindings.get(operation) : catalog.actualActionBinding(operation).orElse(null); }
    public boolean supports(OperationKey operation) { return binding(operation) != null; }
    public List<Binding> installed() { return catalog == null ? bindings.values().stream().sorted(java.util.Comparator.comparing(b -> b.operation().value())).toList()
            : catalog.actionBindings().stream().map(RootExecutableBindings.ActionBinding::effect).toList(); }
    @Override public void requireProtocolIdentity(ActionCommand command) {
        Objects.requireNonNull(command);
        if (catalog != null) { catalog.requireProtocolIdentity(command); return; }
        Binding actual = binding(command.operation());
        StrictJson.require(actual != null, "no installed source-owned original protocol ID policy");
        actual.preparation().requireProtocolIdentity(command);
    }
    @Override public NativeRequest prepare(ActionCommand command) {
        return prepared(command, null, null);
    }
    @Override public NativeRequest prepare(ActionCommand command, String requestId) {
        StrictJson.text(requestId); return prepared(command, requestId, null);
    }
    @Override public NativeRequest prepare(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed, ActionCommand command, String requestId) {
        Objects.requireNonNull(borrowed); StrictJson.text(requestId); return prepared(command, requestId, borrowed);
    }
    private NativeRequest prepared(ActionCommand command, String requestId, org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed) {
        Binding binding = binding(command.operation());
        if (binding == null) throw new UnsupportedOperationException("no installed Native action/effect handler: " + command.operation().value());
        NativeRequest request = Objects.requireNonNull(borrowed != null ? binding.preparation().prepare(borrowed, command, requestId)
                : requestId == null ? binding.preparation().prepare(command) : binding.preparation().prepare(command, requestId));
        NativeStepDiscriminator.requireRequest(command.operation(), ExecutableStepBindings.Kind.ACTION, request);
        return request;
    }
    @Override public synchronized ActionPorts.PostconditionResult observe(ActionCommand command,
            ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch) {
        Binding binding = binding(command.operation());
        if (binding == null) return new ActionPorts.Pending("no installed independent Native effect reader", List.of(attempt.guard().nativeEvidence()));
        StrictJson.require(attempt.requestId().equals(dispatch.requestId()), "effect request/operation drift");
        NativeStepDiscriminator.requireRequest(command.operation(), ExecutableStepBindings.Kind.ACTION, attempt.preparedRequest());
        Projected observed = Objects.requireNonNull(binding.observer().observe(command, attempt, dispatch));
        ActionState.Settlement settlement = primitiveSettlement(observed.result());
        if (settlement != null) {
            // Validate before retaining a legacy-compatible result, exactly as the authoritative reducer does.
            ActionEffects.validate(command, attempt, dispatch, settlement);
            observed.compatibleResult().ifPresent(result -> {
                Key key = new Key(command.actionId(), attempt.requestId());
                RawJson previous = compatible.get(key);
                StrictJson.require(previous == null || previous.equals(result), "conflicting material history projection");
                StrictJson.require(previous != null || compatible.size() < retainedLimit, "effect history retention bound reached");
                StrictJson.require(previous != null || retainedBytes + result.bytes().length <= MAXIMUM_MATERIAL_BYTES, "effect history material byte bound reached");
                if (previous == null) { compatible.put(key, result); retainedBytes += result.bytes().length; }
            });
        }
        return observed.result();
    }
    private static ActionState.Settlement primitiveSettlement(ActionPorts.PostconditionResult result) {
        if (result instanceof ActionPorts.PauseObserved pause) return new ActionState.PauseConfirmed(pause.observation());
        if (result instanceof ActionPorts.OperatorRebindObserved rebound) return new ActionState.OperatorRebound(rebound.observation());
        if (result instanceof ActionPorts.NativeSourceObserved source) return new ActionState.NativeSourceCompleted(source.observation());
        if (result instanceof ActionPorts.NormalExitPhaseObserved phase) return new ActionState.NormalExitPhaseConfirmed(phase.observation());
        if (result instanceof ActionPorts.EffectObserved effect) return new ActionState.Applied(effect.observation());
        if (result instanceof ActionPorts.ControlObserved control) return control.observation();
        if (result instanceof ActionPorts.FrontendObserved frontend) return new ActionState.FrontendApplied(frontend.observation());
        if (result instanceof ActionPorts.GameplayEntryObserved entry) return new ActionState.GameplayEntered(entry.observation());
        if (result instanceof ActionPorts.TerminalObserved terminal) return new ActionState.NonAppliedTerminal(terminal.observation());
        if (result instanceof ActionPorts.LifecycleControlObserved control) return new ActionState.LifecycleControlApplied(control.observation());
        if (result instanceof ActionPorts.FamilySendObserved send) return new ActionState.FamilySendConfirmed(send.observation());
        return null;
    }
    /** Only a handler's verified original/material result is returned; callers archive its exact bytes. */
    public synchronized Optional<RawJson> compatibleResult(String actionId, String requestId) {
        StrictJson.text(actionId); StrictJson.text(requestId); return Optional.ofNullable(compatible.get(new Key(actionId, requestId)));
    }
    /** Uses the existing immutable outcome archive; this is not an action journal or another writer. */
    public synchronized Optional<ExactRef> archiveCompatibleResult(String actionId, String requestId, ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(archive);
        return compatibleResult(actionId, requestId).map(raw -> {
            ExactRef ref = archive.preserveMaterial(raw);
            StrictJson.require(raw.equals(archive.loadMaterial(ref)), "material archive readback differs from the actual verifier result");
            return ref;
        });
    }
}
