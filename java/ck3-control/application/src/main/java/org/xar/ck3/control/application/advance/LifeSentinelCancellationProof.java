package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;

/** Pure replay of this source's finite, never-resumed initialization and cancellation. */
final class LifeSentinelCancellationProof {
    private LifeSentinelCancellationProof() { }

    static void parent(ActionCommand parent, CompositeExecution execution) {
        require(parent.origin() instanceof CommandOrigin.Gameplay && LifeAdvanceComposite.accepts(parent.operation().value())
                && execution.handlerId().equals(LifeAdvanceComposite.HANDLER)
                && parent.origin().acceptsGuard(execution.guard().origin())
                && execution.guard().source().equals(parent.source()) && execution.guard().sessionId().equals(parent.sessionId())
                && execution.guard().operation().equals(parent.operation()), "original Life cancellation parent/guard differs");
        AdvancePlan plan = AdvancePlan.decode(parent);
        require(plan.clockMode() != AdvancePlan.ClockMode.POLLED && plan.dailyWatch().isEmpty()
                && parent.expected().observerSchema().equals(AdvancePlan.OBSERVER) && parent.expected().values().equals(plan.expected()),
                "exact original unwatched native Life plan required for initialization cancellation");
    }

    static ActionReceipt prefix(ActionCommand parent, CompositeExecution execution, List<ActionReceipt> children, boolean canceled) {
        parent(parent, execution);
        AdvancePlan plan = AdvancePlan.decode(parent);
        require(children.size() == execution.children().size() && children.size() >= (canceled ? 2 : 1)
                && children.size() <= (canceled ? 4 : 3), "complete finite original Life prefix required");
        int index = 0; long previous = 0;
        if (children.get(index).command().operation().value().equals("pause-map")) index++;
        if (index < children.size() && children.get(index).command().operation().value().equals("set-speed-" + plan.speed())) index++;
        require(index < children.size() && children.get(index).command().operation().value().equals(plan.armStep())
                && children.size() == index + (canceled ? 2 : 1), "Life cancellation permits only optional pause/speed, original ARM, and one CANCEL");
        ActionReceipt arm = children.get(index);
        Status armed = confirmedArm(parent, arm);
        for (int ordinal = 0; ordinal < children.size(); ordinal++) {
            ActionReceipt child = children.get(ordinal); ActionCommand command = child.command();
            CompositeExecution.Child bound = execution.children().get(ordinal);
            boolean cancel = canceled && ordinal == children.size() - 1;
            boolean confirmedPause = command.operation().value().equals("pause-map") && child.state() instanceof ActionState.Settled pause
                    && pause.settlement() instanceof ActionState.PauseConfirmed;
            require(child.settled() && (child.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED || confirmedPause)
                    && child.sequence() > previous && child.bodySha256().equals(ActionCodec.bodySha256(command))
                    && bound.actionId().equals(command.actionId()) && bound.bodySha256().equals(child.bodySha256())
                    && command.actionId().equals(ActionIds.child(parent.actionId(), ordinal + 1, command.operation()))
                    && command.origin() instanceof CommandOrigin.Gameplay && command.source().equals(parent.source())
                    && command.sessionId().equals(parent.sessionId()) && command.claims().equals(parent.claims())
                    && command.arguments().members().isEmpty()
                    && command.expected().equals(AdvancePrimitives.expected(command.before(), command.source(), command.operation(), command.arguments()))
                    && (cancel || !command.deadline().isAfter(parent.deadline())),
                    "Life cancellation child is not the complete canonical ordered source-bound timeline child");
            sameFrame(parent, command.before());
            require(child.state() instanceof ActionState.Settled, "Life initialization child needs its real native attempt");
            ActionState.Settled settled = (ActionState.Settled) child.state();
            ActionEffects.validate(command, settled.attempt(), settled.dispatch(), settled.settlement());
            previous = child.sequence();
        }
        if (canceled) {
            ActionReceipt cancel = children.getLast();
            require(cancel.command().operation().value().equals(ClockStatusRead.CANCEL_PREFIX + armed.generation().decimal()),
                    "Life cancellation targets another native generation");
            var state = (ActionState.Settled) cancel.state();
            require(state.settlement() instanceof ActionState.ControlApplied, "original cancel lacks its independent native Status");
            Status idle = ClockStatusRead.decode(((ActionState.ControlApplied) state.settlement()).read().original());
            AdvanceClock.validateCancellation(armed, idle, plan, plan.startingDateRaw());
        }
        return arm;
    }

    static Status confirmedArm(ActionCommand parent, ActionReceipt arm) {
        AdvancePlan plan = AdvancePlan.decode(parent);
        require(arm.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.ControlApplied,
                "original ARM needs its independently confirmed canonical ControlApplied");
        var state = (ActionState.Settled) arm.state();
        var control = (ActionState.ControlApplied) state.settlement();
        require(control.observerSchema().equals(AdvancePrimitives.CLOCK_OBSERVER), "original ARM observer differs");
        Status ack = AdvancePrimitives.acknowledgedSentinel(arm.ack().orElseThrow(), plan.armStep());
        Status actual = ClockStatusRead.decode(control.read().original());
        AdvanceClock.validateArm(ack, plan);
        require(actual.equals(ack) && control.actual().equals(AdvancePrimitives.statusValues(actual)),
                "original ARM ACK has no equal independent Status confirmation");
        return actual;
    }

    static void sameFrame(ActionCommand parent, ObservationIdentity actual) {
        var original = parent.before();
        require(actual.machineId().equals(original.machineId()) && actual.game().equals(original.game())
                && actual.frame().episodeRunId().equals(original.frame().episodeRunId())
                && actual.frame().identity().player().equals(original.frame().identity().player())
                && actual.frame().identity().dateRaw().equals(original.frame().identity().dateRaw())
                && actual.frame().identity().nativeRevision().compareTo(original.frame().identity().nativeRevision()) >= 0,
                "initialization cancellation changed the original Game/episode/actor/date or regressed native state");
    }

    static ObservationIdentity factual(GuardEvidence guard) {
        return guard.origin() instanceof CommandOrigin.Reconciliation reconciliation ? reconciliation.identity().factual() : guard.observed();
    }

    static NativeRequestChronology physical(ActionCommand parent, PlanningReadReceipt read) {
        require(read.contractId().equals(PhysicalStatusIdentity.CONTRACT_ID)
                && read.request().origin() instanceof CommandOrigin.PhysicalStatusOnly
                && read.request().operation().value().equals(ClockStatusRead.STEP) && read.request().arguments().members().isEmpty()
                && read.request().source().equals(parent.source()) && read.request().sessionId().equals(parent.sessionId())
                && read.before().guardMode() == ReadContract.GuardMode.STATUS_ONLY && read.after().guardMode() == ReadContract.GuardMode.STATUS_ONLY,
                "exact actual source-owned physical Status read required");
        for (var guard : List.of(read.before().binding(), read.after().binding())) {
            var identity = guard.origin().requirePhysicalStatusOnly();
            require(identity.machineId().equals(parent.before().machineId()) && identity.game().equals(parent.before().game())
                    && identity.source().equals(parent.source()) && identity.sessionId().equals(parent.sessionId())
                    && identity.nativeRevision().compareTo(parent.before().frame().identity().nativeRevision()) >= 0,
                    "Life physical Status crossed its original machine/Game/source/session or native state");
        }
        var custody = read.original().custody().orElseThrow(); custody.verify(read); return custody;
    }

    static void terminal(ActionCommand parent, CompositeExecution execution, CompositeControlObservation control,
            List<ActionReceipt> children) {
        ActionReceipt arm = prefix(parent, execution, children, true);
        Status armed = confirmedArm(parent, arm);
        Status idle = ClockStatusRead.decode(control.terminalStatus().original());
        AdvancePlan plan = AdvancePlan.decode(parent);
        AdvanceClock.validateCancellation(armed, idle, plan, plan.startingDateRaw());
        PlanningReadReceipt terminal = control.terminalStatus();
        require(terminal.request().operation().value().equals(ClockStatusRead.STEP) && terminal.request().arguments().members().isEmpty()
                && terminal.contractId().equals(PhysicalStatusIdentity.CONTRACT_ID)
                && terminal.request().origin() instanceof CommandOrigin.PhysicalStatusOnly
                && terminal.before().guardMode() == ReadContract.GuardMode.STATUS_ONLY
                && terminal.after().guardMode() == ReadContract.GuardMode.STATUS_ONLY,
                "Life cancellation terminal requires its independent source-owned physical Status contract");
        ActionState.Settled canceledState = (ActionState.Settled) children.getLast().state();
        PlanningReadReceipt canceledRead = ((ActionState.ControlApplied) canceledState.settlement()).read();
        require(control.supportingReads().equals(List.of(canceledRead)) && !terminal.requestId().equals(canceledRead.requestId())
                && idle.equals(ClockStatusRead.decode(canceledRead.original())), "parent cancellation must read the confirmed idle slot independently after its child");
        NativeRequestChronology query = physical(parent, terminal);
        NativeRequestChronology canceledQuery = canceledRead.original().custody().orElseThrow(); canceledQuery.verify(canceledRead);
        require(!query.writeEntered().observedAt().isBefore(canceledQuery.responseReceived().observedAt()),
                "parent terminal query predates its canonical cancel child observation");
        for (var guard : List.of(terminal.before().binding(), terminal.after().binding())) {
            var identity = guard.origin().requirePhysicalStatusOnly();
            require(identity.machineId().equals(parent.before().machineId()) && identity.game().equals(parent.before().game())
                    && identity.source().equals(parent.source()) && identity.sessionId().equals(parent.sessionId())
                    && identity.nativeRevision().compareTo(parent.before().frame().identity().nativeRevision()) >= 0,
                    "Life cancellation physical terminal crossed its original machine/Game/source/session or native state");
        }
        var semantic = control.semantic(); sameFrame(parent, semantic.after());
        require(semantic.source().equals(parent.source()) && semantic.sessionId().equals(parent.sessionId())
                && semantic.observerSchema().equals(AdvancePlan.OBSERVER) && semantic.supportingEvidence().size() == 1
                && semantic.provenance().independentOf(terminal.requestId())
                && semantic.after().frame().identity().nativeRevision().compareTo(terminal.after().binding().origin().requirePhysicalStatusOnly().nativeRevision()) >= 0
                && !semantic.observedAt().isBefore(query.responseReceived().observedAt()),
                "cancelled initialization lacks its independent complete same-Game semantic ending");
        List<ExpectedValue> expected = new ArrayList<>(plan.expected());
        expected.add(new ExpectedBoolean(new FieldKey("native.gameplay_verified"), false));
        expected.add(new ExpectedBoolean(new FieldKey("timeline.advance_verified"), false));
        expected.add(new ExpectedBoolean(new FieldKey("timeline.checkpoint_eligible"), false));
        expected.add(new ExpectedText(new FieldKey("progress_status"), "initialization_cancelled"));
        expected.add(new ExpectedInteger(new FieldKey("advance.ending_date_raw"), plan.startingDateRaw()));
        require(semantic.actual().equals(expected), "cancelled initialization cannot claim date advance, gameplay or SAVE credit");
        require(terminal.request().source().equals(parent.source()) && terminal.request().sessionId().equals(parent.sessionId()),
                "cancelled initialization physical Status belongs to another source/session");
    }
}
