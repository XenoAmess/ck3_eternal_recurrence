package org.xar.ck3.control.application.battleadvance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import java.util.List;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.*;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.reconciliation.LateOutcome.State;

/** The same actual tactical-clock replay is used by the battle parent and route-window parent. */
public final class BattleAdvanceArchivedReplay {
    private final AdvancePrimitiveArchivedReplay primitives;
    public BattleAdvanceArchivedReplay(NativeEffectEvidence.FrameLoader frames) { primitives = new AdvancePrimitiveArchivedReplay(frames); }
    public void verify(ActionCommand parent, BattleAdvancePlan plan, AdvanceObservationPort.Frame starting, AdvanceObservationPort.Frame ending,
            ClockStatusRead.Observation terminal, List<ActionReceipt> children, ActionPorts.OutcomeArchive archive) {
        AdvanceClockArchivedReplay.verifyChildBindings(parent, children);
        for (ActionReceipt child : children) primitives.verify(child, archive);
        var before = BattleAdvanceFrame.decode(starting); var after = BattleAdvanceFrame.decode(ending);
        BattleAdvanceFrame.bind(parent, before, true); BattleAdvanceFrame.bind(parent, after, false);
        require(after.paused() && after.mapReady() && before.owner().same(after.owner(), false, false)
                && after.nativeRevision().compareTo(before.nativeRevision()) >= 0, "tactical clock original endpoint ownership/paused state differs");
        long delta = (long) after.owner().dateRaw() - plan.startingDateRaw();
        require(before.owner().dateRaw() == plan.startingDateRaw() && delta >= 0 && delta % 24 == 0 && after.owner().dateRaw() <= plan.targetDateRaw(), "tactical clock original date delta invalid");
        primitives.verifyIndependentRead(parent, terminal.receipt(), archive);
        require(terminal.status().equals(ClockStatusRead.decode(terminal.receipt().original()))
                && terminal.originalEvidence().equals(archive.referenceOf(terminal.receipt().original())), "tactical final independent Status original differs");
        int armIndex = -1, resumeIndex = -1, cancelIndex = -1;
        for (int index = 0; index < children.size(); index++) {
            String step = children.get(index).command().operation().value();
            if (step.startsWith(ClockStatusRead.ARM_PREFIX)) { require(armIndex < 0 && step.equals(plan.armStep()), "foreign or duplicate tactical arm"); armIndex = index; }
            else if (step.equals("resume-map")) { require(resumeIndex < 0 && armIndex >= 0, "duplicate resume or resume before tactical arm"); resumeIndex = index; }
            else if (step.startsWith(ClockStatusRead.CANCEL_PREFIX)) { require(cancelIndex < 0 && armIndex >= 0, "duplicate cancel or cancel before tactical arm"); cancelIndex = index; }
            else require(step.equals("pause-map") || step.equals("set-speed-" + plan.speed()) && armIndex < 0, "foreign or late tactical timeline child");
        }
        require(armIndex >= 0, "tactical clock lacks its actual original arm");
        var arm = AdvancePrimitives.acknowledgedSentinel(children.get(armIndex).ack().orElseThrow(), plan.armStep());
        BattleSentinelValidation.arm(arm, plan.startingDateRaw(), plan.targetDateRaw(), plan.speed(), plan.mode(), plan.watchArmyIds(), plan.scope());
        var boundary = BattleAdvanceFrame.boundary(before, after);
        require(boundary.isEmpty() || boundary.orElseThrow().kind() == BattleAdvanceFrame.Kind.ACTIVE_WAR_SET_CHANGED || BattleAdvanceFrame.isNew(before, after), "tactical boundary is not new to the original entry frame");
        boolean canceled = terminal.status().state() == State.IDLE;
        if (canceled) {
            require(boundary.isPresent() && cancelIndex > armIndex && (resumeIndex < 0 || cancelIndex > resumeIndex), "tactical cancellation lacks its original fresh boundary/order");
            ActionReceipt child = children.get(cancelIndex);
            require(child.command().operation().value().equals(ClockStatusRead.CANCEL_PREFIX + arm.generation().decimal())
                    && child.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.ControlApplied, "tactical cancellation differs from original generation");
            var control = (ActionState.ControlApplied) ((ActionState.Settled)child.state()).settlement();
            require(!control.read().requestId().equals(terminal.receipt().requestId())
                    && ClockStatusRead.decode(control.read().original()).equals(terminal.status()), "tactical parent terminal reused cancel child read or changed its slot");
            require(!ending.observedAt().isBefore(terminal.receipt().after().binding().observedAt())
                    && ending.provenance().independentOf(terminal.receipt().requestId()), "tactical post-cancel semantic frame predates/aliases final independent Status");
        } else require(cancelIndex < 0, "normally triggered tactical clock must not submit cancellation");
        if (boundary.isPresent()) BattleSentinelValidation.decision(terminal.status(), arm, plan.startingDateRaw(), plan.targetDateRaw(), after.owner().dateRaw(),
                plan.speed(), plan.mode(), plan.watchArmyIds(), boundary.orElseThrow(), canceled);
        else BattleSentinelValidation.stop(terminal.status(), arm, plan.startingDateRaw(), plan.targetDateRaw(), after.owner().dateRaw(), plan.speed(), plan.mode(), plan.watchArmyIds());
        require(resumeIndex >= 0 || canceled && delta == 0 && boundary.isPresent(), "tactical clock lacks one original resume or pre-resume zero-day cancellation");
    }
}
