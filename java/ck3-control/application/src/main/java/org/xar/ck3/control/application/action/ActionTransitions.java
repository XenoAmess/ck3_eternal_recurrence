package org.xar.ck3.control.application.action;

import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;

/** The real writer and coordinator use the same transition reducer; no runner-local state machine. */
public final class ActionTransitions {
    private ActionTransitions() { }
    public static void validate(Optional<ActionReceipt> previous, ActionCommand command, String bodySha256, ActionState next) {
        Objects.requireNonNull(previous); Objects.requireNonNull(command); Objects.requireNonNull(next);
        StrictJson.require(bodySha256.equals(ActionCodec.bodySha256(command)), "canonical body mismatch");
        if(previous.isEmpty()&&next instanceof ActionState.ReservedPreparedCleanupNoEffectConfirmed){
            StrictJson.require(command.origin() instanceof CommandOrigin.Gameplay&&command.arguments().members().isEmpty()
                    &&command.operation().value().startsWith(org.xar.ck3.control.application.advance.ClockStatusRead.CANCEL_PREFIX),
                    "only an independently source-qualified exact reserved CANCEL may first terminate by NoEffect");return;
        }
        if(previous.isEmpty()&&next instanceof PreparedCleanupAction prepared){
            StrictJson.require(prepared.phase()==PreparedCleanupAction.Phase.PREPARED
                    &&command.origin() instanceof CommandOrigin.Gameplay&&command.arguments().members().isEmpty()
                    &&command.operation().value().startsWith(org.xar.ck3.control.application.advance.ClockStatusRead.CANCEL_PREFIX),
                    "only an independently source-qualified prepared CANCEL may begin in PREPARED");return;
        }
        if (previous.isEmpty()) { StrictJson.require(next instanceof ActionState.IntentDurable, "first durable action event must be intent"); return; }
        ActionReceipt old = previous.orElseThrow();
        StrictJson.require(old.command().actionId().equals(command.actionId()) && old.bodySha256().equals(bodySha256), "same action ID requires identical complete body");
        StrictJson.require(!old.settled(), "settled action is immutable");
        boolean allowed = switch (old.state()) {
            case PhysicalActionState physical -> next instanceof PhysicalActionState after && !physical.terminal() && PhysicalActionCodec.sameAttempt(physical, after)
                    && (physical.outcome().isEmpty() || physical.outcome().equals(after.outcome()))
                    && (physical.phase() == PhysicalActionState.Phase.SUBMITTING
                        ? after.phase() == PhysicalActionState.Phase.UNKNOWN || after.phase() == PhysicalActionState.Phase.NOT_POSTED
                        : after.phase() == PhysicalActionState.Phase.UNKNOWN || after.phase() == PhysicalActionState.Phase.COMPLETED);
            case ActionState.IntentDurable ignored -> next instanceof PhysicalActionState physical && (physical.phase() == PhysicalActionState.Phase.SUBMITTING
                    || command.arguments().get("automatic_intent") instanceof org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj
                       && (physical.phase()==PhysicalActionState.Phase.UNKNOWN||physical.phase()==PhysicalActionState.Phase.NOT_POSTED)) || next instanceof ActionState.Submitting || next instanceof ActionState.Unknown || next instanceof ActionState.CompositeRunning || next instanceof ActionState.RejectedBeforeDispatch || next instanceof ActionState.IntentAbandoned;
            case ActionState.Submitting ignored -> next instanceof ActionState.AckReceived || next instanceof ActionState.Unknown || next instanceof ActionState.RejectedBeforeDispatch;
            case ActionState.AckReceived ignored -> next instanceof ActionState.Unknown || next instanceof ActionState.Settled;
            case ActionState.Unknown ignored -> next instanceof ActionState.Unknown || next instanceof ActionState.Settled || next instanceof ActionState.CleanupNoEffectConfirmed;
            case PreparedCleanupAction before -> next instanceof PreparedCleanupAction after&&PreparedCleanupActionCodec.follows(before,after)
                    ||next instanceof ActionState.PreparedCleanupNoEffectConfirmed terminal&&before.equals(terminal.originalPreparedState());
            case ActionState.ReservedPreparedCleanupNoEffectConfirmed ignored -> false;
            case ActionState.PreparedCleanupNoEffectConfirmed ignored -> false;
            case ActionState.CleanupNoEffectConfirmed ignored -> false;
            case ActionState.Settled ignored -> false;
            case ActionState.IntentAbandoned ignored -> false;
            case ActionState.RejectedBeforeDispatch ignored -> false;
            case ActionState.CompositeRunning ignored -> next instanceof ActionState.CompositeRunning || next instanceof ActionState.CompositeUnknown || next instanceof ActionState.CompositeSettled;
            case ActionState.CompositeUnknown ignored -> next instanceof ActionState.CompositeUnknown || next instanceof ActionState.CompositeSettled || next instanceof ActionState.CompositeOperatorQuarantined;
            case ActionState.CompositeSettled ignored -> false;
            case ActionState.CompositeOperatorQuarantined ignored -> false;
        };
        StrictJson.require(allowed, "invalid action transition; UNKNOWN must never return to dispatch");
        if(next instanceof ActionState.PreparedCleanupNoEffectConfirmed terminal){
            StrictJson.require(old.state() instanceof PreparedCleanupAction before&&!before.terminal()
                    &&before.equals(terminal.originalPreparedState()),"prepared NoEffect must retain all six original state fields exactly");
            StrictJson.require(command.operation().value().startsWith(org.xar.ck3.control.application.advance.ClockStatusRead.CANCEL_PREFIX),
                    "prepared NoEffect cannot settle another operation");
        }
        if(next instanceof ActionState.CleanupNoEffectConfirmed terminal) {
            StrictJson.require(old.state() instanceof ActionState.Unknown,"NoEffect may only reconcile its original UNKNOWN");
            var unknown=(ActionState.Unknown)old.state();
            StrictJson.require(unknown.attempt().equals(terminal.originalAttempt())
                    &&unknown.dispatch().equals(terminal.originalDispatch()),"NoEffect must preserve both original optionals exactly");
            StrictJson.require(command.operation().value().startsWith(org.xar.ck3.control.application.advance.ClockStatusRead.CANCEL_PREFIX),
                    "cleanup NoEffect cannot settle another primitive");
        }
        if (next instanceof ActionState.Settled settled) ActionEffects.validate(command, settled.attempt(), settled.dispatch(), settled.settlement());
        if (next instanceof ActionState.CompositeSettled settled) ActionEffects.validateComposite(command, settled.execution(), settled.settlement());
        Optional<CompositeExecution> oldComposite = composite(old.state()), nextComposite = composite(next);
        if (oldComposite.isPresent()) {
            StrictJson.require(nextComposite.isPresent(), "composite child history cannot be erased");
            CompositeExecution before = oldComposite.orElseThrow(), after = nextComposite.orElseThrow();
            StrictJson.require(before.handlerId().equals(after.handlerId()) && before.startedAt().equals(after.startedAt()) && before.guard().equals(after.guard()), "composite origin cannot change");
            StrictJson.require(after.children().size() >= before.children().size() && after.children().subList(0, before.children().size()).equals(before.children()), "durable child body/order cannot change");
            boolean sourceContinuation = old.state() instanceof ActionState.CompositeUnknown && next instanceof ActionState.CompositeUnknown
                    && (command.origin() instanceof CommandOrigin.LifecycleTerminal
                        && command.lifecycleExpected().operation() == LifecycleExpectedPostcondition.Operation.CONTINUE_SUCCESSOR
                        || lifeCancellationReservation(command, before, after)
                        || next instanceof ActionState.CompositeUnknown successor
                            &&successor.reason().startsWith(org.xar.ck3.control.application.advance.PreparedCleanupSuccessorEvidence.CURSOR_PREFIX)
                            &&lifePreparedSuccessorReservation(command,before,after));
            StrictJson.require(next instanceof ActionState.CompositeRunning || sourceContinuation
                    ? after.children().size() <= before.children().size() + 1 : after.children().equals(before.children()),
                    "only a running or source-verified exact successor continuation may reserve one child");
        } else if (nextComposite.isPresent()) StrictJson.require(nextComposite.orElseThrow().children().isEmpty(), "composite begins with no child submissions");
        Optional<ActionState.Attempt> beforeAttempt = attempt(old.state()), afterAttempt = attempt(next);
        if (beforeAttempt.isPresent()) StrictJson.require(beforeAttempt.equals(afterAttempt), "original durable submission attempt cannot change");
        Optional<NativeActionPort.DispatchOutcome> previousDispatch = dispatch(old.state());
        if (previousDispatch.isPresent()) StrictJson.require(previousDispatch.equals(dispatch(next)), "an original ACK or unknown dispatch record cannot be erased or replaced");
    }
    /** Cold structural shape only. The registered source and its actual Children still authorize each CANCEL. */
    private static boolean lifePreparedSuccessorReservation(ActionCommand command,CompositeExecution before,CompositeExecution after){
        if(!(command.origin() instanceof CommandOrigin.Gameplay)||!org.xar.ck3.control.application.advance.LifeAdvanceComposite.accepts(command.operation().value())
                ||!before.handlerId().equals(org.xar.ck3.control.application.advance.LifeAdvanceComposite.HANDLER)
                ||before.children().size()!=5||after.children().size()!=6)return false;
        var guard=before.guard();
        if(!command.origin().acceptsGuard(guard.origin())||!command.source().equals(guard.source())
                ||!command.sessionId().equals(guard.sessionId())||!command.operation().equals(guard.operation()))return false;
        var plan=org.xar.ck3.control.application.advance.AdvancePlan.decode(command);
        return plan.clockMode()!=org.xar.ck3.control.application.advance.AdvancePlan.ClockMode.POLLED&&plan.dailyWatch().isEmpty()
                &&command.expected().observerSchema().equals(org.xar.ck3.control.application.advance.AdvancePlan.OBSERVER)
                &&command.expected().values().equals(plan.expected());
    }
    private static boolean lifeCancellationReservation(ActionCommand command, CompositeExecution before, CompositeExecution after) {
        if (!(command.origin() instanceof CommandOrigin.Gameplay)
                || !org.xar.ck3.control.application.advance.LifeAdvanceComposite.accepts(command.operation().value())
                || !before.handlerId().equals(org.xar.ck3.control.application.advance.LifeAdvanceComposite.HANDLER)
                || before.children().isEmpty() || before.children().size() > 4
                || after.children().size() != before.children().size() + 1 || after.children().size() > 5) return false;
        GuardEvidence guard = before.guard();
        if (!command.origin().acceptsGuard(guard.origin()) || !command.source().equals(guard.source())
                || !command.sessionId().equals(guard.sessionId()) || !command.operation().equals(guard.operation())) return false;
        var plan = org.xar.ck3.control.application.advance.AdvancePlan.decode(command);
        return plan.clockMode() != org.xar.ck3.control.application.advance.AdvancePlan.ClockMode.POLLED
                && plan.dailyWatch().isEmpty()
                && command.expected().observerSchema().equals(org.xar.ck3.control.application.advance.AdvancePlan.OBSERVER)
                && command.expected().values().equals(plan.expected());
    }
    public static Optional<ActionState.Attempt> attempt(ActionState state) {
        return switch (state) {
            case PhysicalActionState ignored -> Optional.empty();
            case ActionState.IntentDurable ignored -> Optional.empty();
            case ActionState.IntentAbandoned ignored -> Optional.empty();
            case ActionState.Submitting value -> Optional.of(value.attempt());
            case ActionState.AckReceived value -> Optional.of(value.attempt());
            case ActionState.Unknown value -> value.attempt();
            case PreparedCleanupAction ignored -> Optional.empty();
            case ActionState.ReservedPreparedCleanupNoEffectConfirmed ignored -> Optional.empty();
            case ActionState.PreparedCleanupNoEffectConfirmed ignored -> Optional.empty();
            case ActionState.CleanupNoEffectConfirmed value -> value.originalAttempt();
            case ActionState.Settled value -> Optional.of(value.attempt());
            case ActionState.RejectedBeforeDispatch value -> Optional.of(value.attempt());
            case ActionState.CompositeRunning ignored -> Optional.empty();
            case ActionState.CompositeUnknown ignored -> Optional.empty();
            case ActionState.CompositeSettled ignored -> Optional.empty();
            case ActionState.CompositeOperatorQuarantined ignored -> Optional.empty();
        };
    }
    public static Optional<NativeActionPort.DispatchOutcome> dispatch(ActionState state) {
        return switch (state) {
            case ActionState.AckReceived value -> Optional.of(value.dispatch());
            case ActionState.Unknown value -> value.dispatch();
            case PreparedCleanupAction value -> value.originalDispatch();
            case ActionState.PreparedCleanupNoEffectConfirmed value -> value.originalPreparedState().originalDispatch();
            case ActionState.CleanupNoEffectConfirmed value -> value.originalDispatch();
            case ActionState.Settled value -> Optional.of(value.dispatch());
            case ActionState.RejectedBeforeDispatch value -> Optional.of(value.dispatch());
            default -> Optional.empty();
        };
    }
    public static Optional<CompositeExecution> composite(ActionState state) {
        if (state instanceof ActionState.CompositeRunning value) return Optional.of(value.execution());
        if (state instanceof ActionState.CompositeUnknown value) return Optional.of(value.execution());
        if (state instanceof ActionState.CompositeSettled value) return Optional.of(value.execution());
        if (state instanceof ActionState.CompositeOperatorQuarantined value) return Optional.of(value.execution());
        return Optional.empty();
    }
}

