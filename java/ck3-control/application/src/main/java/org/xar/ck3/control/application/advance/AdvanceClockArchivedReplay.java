package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.reconciliation.LateOutcome.State;

/** Original primitive and independent Status replay, shared by life and exact route clocks. */
public final class AdvanceClockArchivedReplay {
    private final AdvancePrimitiveArchivedReplay primitives;
    private final NativeEffectEvidence.FrameLoader frames;
    public AdvanceClockArchivedReplay(NativeEffectEvidence.FrameLoader frames) { this.frames = Objects.requireNonNull(frames); primitives = new AdvancePrimitiveArchivedReplay(frames); }
    public static void verifyChildBindings(ActionCommand parent, List<ActionReceipt> children) {
        Objects.requireNonNull(parent); children = List.copyOf(children); require(children.size() <= 256, "finite original timeline child list required");
        var ids = new HashSet<String>(); long previousSequence = 0;
        for (ActionReceipt child : children) {
            var command = child.command();
            require(child.settled() && ids.add(command.actionId()) && !command.actionId().equals(parent.actionId()) && child.sequence() > previousSequence
                    && child.bodySha256().equals(ActionCodec.bodySha256(command)), "unresolved, duplicate, reordered or altered timeline child");
            previousSequence = child.sequence();
            require(command.origin() instanceof CommandOrigin.Gameplay && AdvancePrimitives.supports(command.operation())
                    && command.source().equals(parent.source()) && command.sessionId().equals(parent.sessionId()) && command.claims().equals(parent.claims())
                    && !command.deadline().isAfter(parent.deadline()) && command.before().game().equals(parent.before().game())
                    && command.before().machineId().equals(parent.before().machineId())
                    && command.before().frame().episodeRunId().equals(parent.before().frame().episodeRunId())
                    && command.before().frame().identity().player().equals(parent.before().frame().identity().player())
                    && command.before().frame().identity().dateRaw().compareTo(parent.before().frame().identity().dateRaw()) >= 0
                    && command.before().frame().identity().nativeRevision().compareTo(parent.before().frame().identity().nativeRevision()) >= 0,
                    "timeline child crossed original source/session/Game/episode/actor/claims/deadline");
        }
    }
    public void verify(ActionCommand parent, AdvancePlan plan, AdvanceObservationPort.Frame starting, AdvanceObservationPort.Frame ending,
            AdvanceClock.ProgressStatus progress, Optional<ClockStatusRead.Observation> terminal, List<ActionReceipt> children, ActionPorts.OutcomeArchive archive) {
        verifyChildBindings(parent, children); require(starting.identity().equals(parent.before()), "clock original entry frame differs");
        AdvanceWait.binding(parent, starting, ending);
        require(AdvancePolicy.truth(ending.semantic(), "paused") && AdvancePolicy.truth(ending.semantic(), "map_ready"), "clock original endpoint is not paused and ready");
        for (ActionReceipt child : children) primitives.verify(child, archive);
        if (plan.dailyWatch().isPresent()) verifyWatch(parent, plan, starting, ending, children, archive);
        verifySequence(plan, starting, ending, progress, terminal, children);
        terminal.ifPresent(read -> {
            primitives.verifyIndependentRead(parent, read.receipt(), archive);
            require(read.status().equals(ClockStatusRead.decode(read.receipt().original()))
                    && read.originalEvidence().equals(archive.referenceOf(read.receipt().original())), "clock final independent Status original changed");
            require(!ending.observedAt().isBefore(read.receipt().after().binding().observedAt())
                    && ending.provenance().independentOf(read.receipt().requestId()), "clock endpoint predates or aliases the terminal Status read");
        });
    }
    private void verifyWatch(ActionCommand parent, AdvancePlan plan, AdvanceObservationPort.Frame starting, AdvanceObservationPort.Frame ending,
            List<ActionReceipt> children, ActionPorts.OutcomeArchive archive) {
        var watch = plan.dailyWatch().orElseThrow();
        require(watch.starting().equals(starting.identity()) && watch.sameOwner(ending)
                && org.xar.ck3.control.planning.opportunity.OpportunityJson.integer(ending.semantic().get("speed"), "speed").intValueExact() == 2,
                "archived daily watch entry/ending owner or speed changed");
        for (ActionReceipt child : children) {
            String step = child.command().operation().value();
            if (!step.equals(plan.armStep()) && !step.equals("resume-map") && !step.equals("pause-map")) continue;
            require(child.state() instanceof ActionState.Settled, "daily watch original mutation has no actual settled attempt");
            var actual = RootGuardEvidence.loadFrame(((ActionState.Settled)child.state()).attempt().guard(), archive, frames);
            var push = new ObservationProvenance.Push(actual.identity().frame().snapshotId(), actual.identity().frame().identity().nativeRevision(), actual.originalEvidence());
            var original = new AdvanceObservationPort.Frame(actual.identity(), actual.source(), actual.sessionId(), actual.semantic(), push, actual.observedAt(), actual.originalEvidence());
            if (step.equals("pause-map")) {
                AdvanceClock.requirePauseFrame(parent, plan.dailyWatch(), original);
                var settled = (ActionState.Settled) child.state();
                if (settled.settlement() instanceof ActionState.Applied || settled.settlement() instanceof ActionState.PauseConfirmed) {
                    var after = AdvancePrimitiveEvidence.load(child, archive, frames);
                    var afterPush = new ObservationProvenance.Push(after.identity().frame().snapshotId(), after.identity().frame().identity().nativeRevision(), after.originalEvidence());
                    AdvanceClock.requirePauseFrame(parent, plan.dailyWatch(), new AdvanceObservationPort.Frame(after.identity(),
                            after.source(), after.sessionId(), after.semantic(), afterPush, after.observedAt(), after.originalEvidence()));
                }
                continue;
            }
            require(watch.readyToArm(original), "daily watch original arm/resume lost its full owner/roster/speed contract");
            if (step.equals("resume-map")) require(ending.identity().frame().revision().compareTo(original.identity().frame().revision()) > 0
                    || ending.identity().frame().identity().dateRaw().compareTo(plan.targetDateRaw()) < 0 && lawfulWatchBoundary(watch, ending),
                    "daily watch date alone cannot prove the original single resume stopped");
        }
        require(watch.boundary(ending).isEmpty() || lawfulWatchBoundary(watch, ending), "daily watch archived ending crossed unavailable owner/connection/map/frame boundary");
    }
    private static boolean lawfulWatchBoundary(WarDailyWatch.Context watch, AdvanceObservationPort.Frame frame) {
        return watch.boundary(frame).filter(boundary -> switch (boundary) {
            case ACTIVE_EVENT, PENDING_INTERACTION, EXCLUSIVE_MODAL_OR_UNKNOWN -> true;
            default -> false;
        }).isPresent();
    }
    /** Pure sequence check is useful for diagnostics; only verify also reopens original archive inputs. */
    public static void verifySequence(AdvancePlan plan, AdvanceObservationPort.Frame starting, AdvanceObservationPort.Frame ending,
            AdvanceClock.ProgressStatus progress, Optional<ClockStatusRead.Observation> terminal, List<ActionReceipt> children) {
        BigInteger end = ending.identity().frame().identity().dateRaw(); BigInteger delta = end.subtract(plan.startingDateRaw());
        require(starting.identity().frame().identity().dateRaw().equals(plan.startingDateRaw()) && delta.signum() >= 0 && delta.mod(AdvancePlan.DAY).signum() == 0,
                "clock original date delta must be nonnegative whole days");
        boolean early = end.compareTo(plan.targetDateRaw()) < 0, zero = delta.signum() == 0;
        boolean boundary = AdvanceProgress.boundary(ending, starting, plan).isPresent();
        boolean modal = AdvanceProgress.newModal(ending.semantic(), starting.identity(), Optional.of(starting.semantic())).isPresent();
        if (plan.exactOneDay() || plan.clockMode() != AdvancePlan.ClockMode.POLLED) require(end.compareTo(plan.targetDateRaw()) <= 0, "clock overshot its immutable target");
        int armIndex = -1, resumeIndex = -1, cancelIndex = -1; boolean canceled = false;
        for (int index = 0; index < children.size(); index++) {
            var child = children.get(index); String step = child.command().operation().value();
            require(child.settled(), "UNKNOWN child cannot be replayed as completed clock");
            if (step.equals("pause-map")) {
                require(!(child.state() instanceof ActionState.RejectedBeforeDispatch), "zero-write pause cannot complete an original clock");
                if (child.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.Rejected)
                    org.xar.ck3.control.application.effects.control.ControlSequenceObservation.requireMapUnavailable(child);
            }
            if (step.equals("resume-map")) { require(resumeIndex < 0, "only one original submitted resume is allowed"); resumeIndex = index;
                require(child.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED, "unconfirmed submitted resume remains UNKNOWN"); }
            else if (step.startsWith(ClockStatusRead.ARM_PREFIX)) { require(plan.clockMode() != AdvancePlan.ClockMode.POLLED && armIndex < 0 && step.equals(plan.armStep()), "missing, duplicate or foreign original arm"); armIndex = index; }
            else if (step.startsWith(ClockStatusRead.CANCEL_PREFIX)) { require(cancelIndex < 0, "duplicate original cancel"); cancelIndex = index; }
            else require(step.equals("pause-map") || step.equals("set-speed-" + plan.speed()), "foreign clock child operation");
            if (step.startsWith("set-speed-")) require(armIndex < 0 && resumeIndex < 0, "speed mutation after original arm/resume is illegal");
        }
        if (plan.clockMode() != AdvancePlan.ClockMode.POLLED) {
            require(armIndex >= 0 && (resumeIndex < 0 || armIndex < resumeIndex), "native clock lacks its original arm before resume");
            var read = terminal.orElseThrow(() -> new IllegalArgumentException("native clock lacks original independent terminal Status"));
            var arm = AdvancePrimitives.acknowledgedSentinel(children.get(armIndex).ack().orElseThrow(), plan.armStep()); AdvanceClock.validateArm(arm, plan);
            if (read.status().state() == State.TRIGGERED) { require(cancelIndex < 0, "normally triggered clock must not be canceled"); AdvanceClock.validateStop(arm, read.status(), plan, end); }
            else {
                require(early && boundary && cancelIndex > armIndex && (resumeIndex < 0 || cancelIndex > resumeIndex)
                        && children.get(cancelIndex).command().operation().value().equals(ClockStatusRead.CANCEL_PREFIX + arm.generation().decimal())
                        && children.get(cancelIndex).outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED, "clock lacks original early-boundary cancellation");
                AdvanceClock.validateCancellation(arm, read.status(), plan, end); canceled = true;
                var settlement = (ActionState.Settled) children.get(cancelIndex).state();
                require(settlement.settlement() instanceof ActionState.ControlApplied, "cancel child has no independent Status settlement");
                var cancel = (ActionState.ControlApplied) settlement.settlement();
                require(!cancel.read().requestId().equals(read.receipt().requestId()) && ClockStatusRead.decode(cancel.read().original()).equals(read.status()), "cancel ACK or reused child Status cannot replace terminal query");
            }
        } else require(terminal.isEmpty() && armIndex < 0 && cancelIndex < 0, "polled clock cannot claim native sentinel control proof");
        require(resumeIndex >= 0 || !AdvancePolicy.truth(starting.semantic(), "paused") && plan.clockMode() == AdvancePlan.ClockMode.POLLED
                || zero && canceled && boundary, "clock lacks its single original resume or zero-day pre-resume cancellation");
        if (zero && resumeIndex < 0) require(canceled && boundary, "zero-day no-resume clock is only a generation-bound control interruption");
        switch (progress) {
            case MODAL_INTERRUPTED -> require(early && modal, "clock modal progress differs from original complete frames");
            case BOUNDARY_INTERRUPTED -> require(early && boundary, "clock early boundary is absent");
            case WALL_TIMEOUT_WITH_DATE_PROGRESS -> require(!zero, "clock timeout has no actual game date progress");
            case POSTCONDITION -> require(!zero && (!early || boundary), "clock completed no original day or horizon/boundary");
        }
    }
}
