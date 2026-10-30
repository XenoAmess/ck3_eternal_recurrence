package org.xar.ck3.control.application.planning.events;

import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.ObservationProvenance;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedInteger;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedText;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedValue;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.eventtraits.EventTraitMembership;
import org.xar.ck3.control.wave2.events.eventtraits.EventTraitMembershipCodec;
import org.xar.ck3.control.wave2.events.eventtraits.EventEffectPhase;
import org.xar.ck3.control.wave2.events.eventtraits.PoetTraitOutcome;

/** Actual Driver old-instance comparison, executed only on an independently read later semantic frame. */
public final class NativeEventPostconditionPort implements EventPolicies.NativeExpectationPort, ActionPorts.PostconditionPort {
    public static final String EVENT_SCHEMA = "xar.ck3.native-event-instance-postcondition/v1";
    public static final String PENDING_SCHEMA = "xar.ck3.native-pending-instance-postcondition/v1";
    private final IndependentReadPort reader;
    public NativeEventPostconditionPort(IndependentReadPort reader) { this.reader = Objects.requireNonNull(reader); }
    /** Assembly binds the original native packet to the public semantic identity and archives it first. No submit method exists. */
    @FunctionalInterface public interface IndependentReadPort { BoundSnapshot read(ActionCommand command, Instant deadline) throws InterruptedException; }
    public record BoundSnapshot(ObservationIdentity after, G2Source source, String sessionId, OpportunityJson.Obj snapshot,
                                ObservationProvenance provenance, Instant observedAt, ExactRef originalEvidence) {
        public BoundSnapshot {
            Objects.requireNonNull(after); Objects.requireNonNull(source); StrictJson.text(sessionId); Objects.requireNonNull(snapshot);
            Objects.requireNonNull(provenance); Objects.requireNonNull(observedAt); Objects.requireNonNull(originalEvidence);
            StrictJson.require(originalEvidence.bytes() > 0, "independent original native evidence required");
            provenance.validate(after, originalEvidence);
            StrictJson.require(after.frame().snapshotId().equals(text(snapshot.get("snapshot_id")))
                && after.frame().revision().equals(integer(snapshot.get("revision")))
                && after.frame().identity().nativeRevision().equals(integer(snapshot.get("native_revision")))
                && after.frame().identity().dateRaw().equals(integer(snapshot.get("date_raw")))
                && after.frame().episodeRunId().equals(text(snapshot.get("episode_run_id")))
                && after.frame().identity().player().equals(integer(object(snapshot.get("played_character")).get("character_id"))),
                "native semantic snapshot differs from its observation identity");
        }
        /** Compatibility for actual query producers. Push producers use the explicit sealed branch. */
        public BoundSnapshot(ObservationIdentity after, G2Source source, String sessionId, OpportunityJson.Obj snapshot,
                String requestId, Instant observedAt, ExactRef originalEvidence) {
            this(after, source, sessionId, snapshot, new ObservationProvenance.Query(requestId), observedAt, originalEvidence);
        }
    }
    @Override public Optional<ExpectedPostcondition> expected(PlanningRequest request, OperationKey operation,
            OpportunityJson.Obj plan, Optional<PoetTraitOutcome.Expectation> traitMaterial) {
        return expected(request.before(), request.source(), request.observations().snapshot(), operation, plan, traitMaterial);
    }
    /** The same pure semantic producer for an actual private snapshot. Callers retain their own source/read admission. */
    public static Optional<ExpectedPostcondition> expected(ObservationIdentity before, G2Source source,
            OpportunityJson.Obj actualSnapshot, OperationKey operation, OpportunityJson.Obj plan,
            Optional<PoetTraitOutcome.Expectation> traitMaterial) {
        String schema = schema(operation.value()); if (schema == null) return Optional.empty();
        String field = EVENT_SCHEMA.equals(schema) ? "active_event" : "pending_character_interaction";
        OpportunityJson.Value original = actualSnapshot.get(field);
        if (!(original instanceof OpportunityJson.Obj instance)) return Optional.empty();
        BigInteger old = integer(instance.get("instance_id")); validateInstance(old, EVENT_SCHEMA.equals(schema));
        List<ExpectedValue> values = new ArrayList<>(); values.add(new ExpectedInteger(new FieldKey("old_instance_id"), old));
        values.add(new ExpectedBoolean(new FieldKey("old_instance_advanced"), true));
        values.add(new ExpectedInteger(new FieldKey("actor_id"), before.frame().identity().player()));
        values.add(new ExpectedText(new FieldKey("connection_generation_decimal"), integer(object(actualSnapshot.get("diagnostics")).get("connection_generation")).toString()));
        // Independent observation establishes current-window advancement. Its material result is recorded separately by
        // NativeEventEffects through the same original-source evaluator as Python. An unavailable or
        // failed material effect cannot erase independently observed current-window advancement and trigger replay.
        Objects.requireNonNull(traitMaterial); Objects.requireNonNull(plan);
        return Optional.of(new ExpectedPostcondition(1, before, source, schema, values));
    }
    @Override public ActionPorts.PostconditionResult observe(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch) {
        if (!command.expected().observerSchema().equals(schema(command.operation().value()))) return pending("event observer does not handle this operation/schema");
        BoundSnapshot after;
        try { after = reader.read(command, command.deadline()); }
        catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); return pending("independent event read was interrupted; original dispatch remains unresolved"); }
        if (after == null || !after.provenance().independentOf(attempt.requestId()) || after.observedAt().isBefore(attempt.submittedAt()))
            return pending("no independent post-dispatch event read");
        Optional<List<ExpectedValue>> facts = project(command.before(), command.source(), command.sessionId(), command.expected(), command.arguments(), after);
        if (facts.isEmpty()) return new ActionPorts.Pending("old instance remains or independent Game/episode/frame/material binding is unavailable", List.of(after.originalEvidence()));
        return new ActionPorts.EffectObserved(new ActionState.EffectObservation(after.after(), after.source(), after.sessionId(),
            command.expected().observerSchema(), facts.orElseThrow(), after.provenance(), after.observedAt(), after.originalEvidence()));
    }
    /** No currently missing effect produces a rejection, and no observation ever requests another selection. */
    public static Optional<List<ExpectedValue>> project(ObservationIdentity before, G2Source source, String session,
            ExpectedPostcondition expected, OpportunityJson.Obj arguments, BoundSnapshot after) {
        if (!before.equals(expected.before()) || !source.equals(expected.source()) || !source.equals(after.source()) || !session.equals(after.sessionId())
                || !before.machineId().equals(after.after().machineId()) || !before.game().equals(after.after().game())
                || !before.frame().episodeRunId().equals(after.after().frame().episodeRunId())
                || !before.frame().identity().player().equals(after.after().frame().identity().player())
                || !before.frame().identity().dateRaw().equals(after.after().frame().identity().dateRaw())
                || before.frame().snapshotId().equals(after.after().frame().snapshotId())
                || after.after().frame().revision().compareTo(before.frame().revision()) <= 0
                || after.after().frame().identity().nativeRevision().compareTo(before.frame().identity().nativeRevision()) <= 0
                || !yes(after.snapshot().get("paused")) || !yes(after.snapshot().get("map_ready"))) return Optional.empty();
        boolean event = EVENT_SCHEMA.equals(expected.observerSchema());
        if (!event && !PENDING_SCHEMA.equals(expected.observerSchema())) return Optional.empty();
        OpportunityJson.Obj diagnostics = object(after.snapshot().get("diagnostics"));
        if (!integer(diagnostics.get("bridge_pid")).equals(BigInteger.valueOf(before.game().pid()))) return Optional.empty();
        BigInteger old = expected.values().stream().filter(value -> value.field().value().equals("old_instance_id"))
            .filter(ExpectedInteger.class::isInstance).map(ExpectedInteger.class::cast).map(ExpectedInteger::value).findFirst().orElse(null);
        if (old == null) return Optional.empty(); validateInstance(old, event);
        OpportunityJson.Value next = after.snapshot().get(event ? "active_event" : "pending_character_interaction");
        if (next == null || !(next == OpportunityJson.Nil.INSTANCE || next instanceof OpportunityJson.Obj)) return Optional.empty();
        if (next instanceof OpportunityJson.Obj active) {
            BigInteger newId = integer(active.get("instance_id")); validateInstance(newId, event);
            if (old.equals(newId)) return Optional.empty();
        }
        List<ExpectedValue> actual = new ArrayList<>(); actual.add(new ExpectedInteger(new FieldKey("old_instance_id"), old));
        actual.add(new ExpectedBoolean(new FieldKey("old_instance_advanced"), true));
        actual.add(new ExpectedInteger(new FieldKey("actor_id"), after.after().frame().identity().player()));
        actual.add(new ExpectedText(new FieldKey("connection_generation_decimal"), integer(diagnostics.get("connection_generation")).toString()));
        Optional<EventEffectPhase.Phases> phases = phases(arguments);
        boolean traitObserved = false;
        for (EventTraitMembership.Trait trait : EventTraitMembership.Trait.values()) {
            if (expected.values().stream().noneMatch(value -> value.field().value().equals(traitField(trait)))) continue;
            // A tooltip or immediate recovery can never satisfy an option-phase trait addition.
            if (phases.isEmpty() || !phases.orElseThrow().optionAdds(trait)
                || !source.exactBuild().equals(phases.orElseThrow().source().ck3Build())) return Optional.empty();
            if (!(arguments.get("event_material_postcondition") instanceof OpportunityJson.Obj saved)) return Optional.empty();
            if (!new OpportunityJson.Text(PoetTraitOutcome.EVENT).equals(saved.get("event_definition_key"))
                || !new OpportunityJson.Text(trait.wire()).equals(saved.get("trait_key")) || !new OpportunityJson.Bool(false).equals(saved.get("starting_value"))
                || !integer(saved.get("starting_native_revision")).equals(before.frame().identity().nativeRevision())
                || !text(saved.get("starting_snapshot_id")).equals(before.frame().snapshotId())
                || !integer(saved.get("starting_revision")).equals(before.frame().revision())
                || !integer(saved.get("character_id")).equals(before.frame().identity().player())
                || !integer(saved.get("date_raw")).equals(before.frame().identity().dateRaw())) return Optional.empty();
            if (!integer(saved.get("selected_native_option_index")).equals(BigInteger.valueOf(phases.orElseThrow().nativeIndex()))) return Optional.empty();
            var nativeFrame = new EventTraitMembership.Frame(after.after().frame().identity().nativeRevision(),
                after.after().frame().identity().dateRaw().intValueExact(), after.after().frame().identity().player().intValueExact());
            var raw = object(after.snapshot().get("played_character")).get("event_trait_membership");
            if (raw == null || raw == OpportunityJson.Nil.INSTANCE) return Optional.empty();
            var observed = EventTraitMembershipCodec.decode(OpportunityJson.encode(raw), nativeFrame);
            if (!(observed instanceof EventTraitMembership.Available available) || !available.traits().contains(trait)) return Optional.empty();
            actual.add(new ExpectedBoolean(new FieldKey(traitField(trait)), true));
            traitObserved = true;
        }
        if (traitObserved) actual.add(new ExpectedInteger(new FieldKey("event_effect_native_index"), BigInteger.valueOf(phases.orElseThrow().nativeIndex())));
        if (ProposalLifecycle.compare(expected, after.after(), after.source(), expected.observerSchema(), actual)
            != ProposalLifecycle.ObservationComparison.EXPECTED_FIELDS_MATCH) return Optional.empty();
        return Optional.of(List.copyOf(actual));
    }
    private static String schema(String step) {
        if (step.startsWith("select-event-option-")) return EVENT_SCHEMA;
        return SetHolder.REPLIES.contains(step) ? PENDING_SCHEMA : null;
    }
    private static final class SetHolder { private static final java.util.Set<String> REPLIES = java.util.Set.of("accept-pending-character-interaction", "reject-pending-character-interaction", "block-pending-character-interaction", "acknowledge-pending-character-interaction"); }
    private static String traitField(EventTraitMembership.Trait trait) { return "trait_" + trait.wire() + "_added"; }
    private static Optional<EventEffectPhase.Phases> phases(OpportunityJson.Obj plan) {
        OpportunityJson.Value raw = plan.get("event_effect_phase");
        if (!(raw instanceof OpportunityJson.Obj)) return Optional.empty();
        try { return Optional.of(EventEffectPhase.decode(OpportunityJson.encode(raw))); }
        catch (IllegalArgumentException malformed) { return Optional.empty(); }
    }
    private static void validateInstance(BigInteger id, boolean event) { StrictJson.require(id.bitLength() <= 31 && (event ? id.signum() > 0 : !id.equals(BigInteger.valueOf(-1))), "full native signed int32 instance required"); }
    private static ActionPorts.Pending pending(String reason) { return new ActionPorts.Pending(reason, List.of()); }
    private static boolean yes(OpportunityJson.Value value) { return new OpportunityJson.Bool(true).equals(value); }
    private static OpportunityJson.Obj object(OpportunityJson.Value value) { return OpportunityJson.object(value, "native event object"); }
    private static BigInteger integer(OpportunityJson.Value value) { return OpportunityJson.integer(value, "native event integer"); }
    private static String text(OpportunityJson.Value value) { return OpportunityJson.text(value, "native event text"); }
}
