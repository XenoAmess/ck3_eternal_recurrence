package org.xar.ck3.control.application.action;

import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;

/** Authoritative writer projection; sequence is assigned by the one durable writer, never by an HTTP caller. */
public record ActionReceipt(int version, long sequence, ActionCommand command, String bodySha256, ActionState state) {
    public enum Outcome { UNRESOLVED, APPLIED_CONFIRMED, SEND_CONFIRMED, REJECTED_CONFIRMED, REJECTED_BEFORE_DISPATCH, TERMINAL_WITHOUT_EFFECT }
    public ActionReceipt {
        StrictJson.require(version == 1, "action receipt version 1 required"); StrictJson.safe(sequence, 1);
        Objects.requireNonNull(command); Objects.requireNonNull(state);
        StrictJson.require(bodySha256 != null && bodySha256.matches("[0-9a-f]{64}") && bodySha256.equals(ActionCodec.bodySha256(command)), "complete canonical action body SHA required");
    }
    public Outcome outcome() {
        if (state instanceof PhysicalActionState physical) return physical.terminal() ? Outcome.TERMINAL_WITHOUT_EFFECT : Outcome.UNRESOLVED;
        if (state instanceof ActionState.Settled settled) return classify(settled.settlement());
        if (state instanceof ActionState.CompositeSettled settled) return classify(settled.settlement());
        return state instanceof ActionState.RejectedBeforeDispatch ? Outcome.REJECTED_BEFORE_DISPATCH : Outcome.UNRESOLVED;
    }
    private static Outcome classify(ActionState.Settlement settlement) {
        if (settlement instanceof ActionState.FixtureStarted || settlement instanceof ActionState.FixtureBusinessCompleted || settlement instanceof ActionState.DirectFixedWindowCompleted || settlement instanceof ActionState.PauseConfirmed || settlement instanceof ActionState.ControlSequenceCompleted || settlement instanceof ActionState.NativeSourceCompleted || settlement instanceof ActionState.NormalExitPhaseConfirmed || settlement instanceof ActionState.OperatorRebound) return Outcome.TERMINAL_WITHOUT_EFFECT;
        if (settlement instanceof ActionState.LifeControlPrefixInterrupted) return Outcome.TERMINAL_WITHOUT_EFFECT;
        if (settlement instanceof ActionState.FamilySendConfirmed) return Outcome.SEND_CONFIRMED;
        if (settlement instanceof ActionState.Rejected || settlement instanceof ActionState.CompositeRejected) return Outcome.REJECTED_CONFIRMED;
        if (settlement instanceof ActionState.NonAppliedTerminal) return Outcome.TERMINAL_WITHOUT_EFFECT;
        if (settlement instanceof ActionState.CompositeNoGameplayWrite) return Outcome.TERMINAL_WITHOUT_EFFECT;
        return Outcome.APPLIED_CONFIRMED;
    }
    public boolean settled() { return outcome() != Outcome.UNRESOLVED; }
    public boolean visibleGameplay() {
        return applied().isPresent() || state instanceof ActionState.CompositeSettled settled
                && settled.settlement() instanceof ActionState.SwaySchedulerCompleted scheduler && scheduler.proof().newlyAppliedBusiness().isPresent();
    }
    public boolean eligibleAdvance() {
        Optional<ActionState.Applied> effect = applied(); if (effect.isEmpty()) return false; ActionState.Applied applied = effect.orElseThrow();
        return visibleGameplay() && appliedFlag("timeline.advance_verified") && appliedFlag("timeline.checkpoint_eligible")
                && applied.observation().after().frame().identity().dateRaw().compareTo(command.before().frame().identity().dateRaw()) > 0
                && applied.observation().actual().contains(new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedText(
                        new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("progress_status"), "postcondition"));
    }
    private boolean appliedFlag(String field) {
        return applied().map(applied -> applied.observation().actual().contains(new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean(
                        new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey(field), true))).orElse(false);
    }
    public Optional<ActionState.Applied> applied() {
        if (state instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.Applied applied) return Optional.of(applied);
        if (state instanceof ActionState.CompositeSettled settled && settled.settlement() instanceof ActionState.Applied applied) return Optional.of(applied);
        return Optional.empty();
    }
    public Optional<NativeActionPort.AckReceived> ack() {
        if (state instanceof ActionState.AckReceived value) return Optional.of(value.dispatch());
        if (state instanceof ActionState.Settled value && value.dispatch() instanceof NativeActionPort.AckReceived ack) return Optional.of(ack);
        if (state instanceof ActionState.Unknown value && value.dispatch().orElse(null) instanceof NativeActionPort.AckReceived ack) return Optional.of(ack);
        return Optional.empty();
    }
}
