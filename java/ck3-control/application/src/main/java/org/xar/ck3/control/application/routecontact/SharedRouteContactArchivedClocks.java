package org.xar.ck3.control.application.routecontact;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.advance.*;
import org.xar.ck3.control.application.battleadvance.*;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.reconciliation.LateOutcome.Mode;

/** Route consumers use the same archived original primitive/Status replay as life and battle. */
public final class SharedRouteContactArchivedClocks implements RouteContactArchivedVerifier.ClockReplay {
    private final AdvanceClockArchivedReplay exact;
    private final BattleAdvanceArchivedReplay window;
    private final BattleAdvancePlan.Configuration configuration;
    private final NativeEffectEvidence.FrameLoader frames;
    public SharedRouteContactArchivedClocks(NativeEffectEvidence.FrameLoader frames, BattleAdvancePlan.Configuration configuration) {
        this.frames = Objects.requireNonNull(frames); this.configuration = Objects.requireNonNull(configuration);
        exact = new AdvanceClockArchivedReplay(frames); window = new BattleAdvanceArchivedReplay(frames);
    }
    @Override public org.xar.ck3.control.application.action.RawJson pauseResult(ActionReceipt child, ActionPorts.OutcomeArchive archive) {
        return AdvancePrimitiveEvidence.compatiblePauseResult(child, archive, frames);
    }
    @Override public void verifyPause(ActionReceipt child, ActionPorts.OutcomeArchive archive) {
        new AdvancePrimitiveArchivedReplay(frames).verify(child, archive);
    }
    @Override public RouteContactComposite.ClockResult replay(WriterContracts.Head head, ActionCommand parent,
            AdvanceObservationPort.Frame starting, RouteContactModel.Proof proof, RouteContactComposite.ClockResult retained,
            List<ActionReceipt> clockChildren, ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(head);
        StrictJson.require(retained.nativeClockVerified() && !retained.unknown(), "unresolved route clock cannot grant archive credit");
        var start = RouteContactCodec.frame(starting); var end = RouteContactCodec.frame(retained.ending());
        StrictJson.require(RouteContactProofs.sameFrame(start, proof.query()), "route replay proof crossed its original clock entry");
        if (proof.kind() == RouteContactModel.ProofKind.BOUNDED_FROZEN_ROUTE_WINDOW) {
            var cap = CampaignDeadline.deadline(configuration.campaignDeadline(), BigInteger.valueOf(start.dateRaw()), BigInteger.valueOf(proof.targetDateRaw()));
            cap.ifPresent(value -> StrictJson.require(value.status() == CampaignDeadline.Status.ADVANCE
                    && value.targetDateRaw().intValueExact() == proof.targetDateRaw(), "route replay window crossed its configured campaign boundary"));
            var plan = new BattleAdvancePlan(parent.operation().value(), start.dateRaw(), proof.targetDateRaw(), retained.timelineSpeed(),
                    Mode.TERMINAL_OR_SENTINEL, BattleAdvanceStep.Scope.ROUTE_CONTACT_WINDOW, proof.watchArmyIds(), cap);
            if (retained.originalReport().isPresent()) BattleAdvanceResultCodec.verifyWindowReport(window, parent, plan, starting, retained.ending(),
                    retained.nativeStopRead().orElseThrow(), clockChildren, retained.originalReport().orElseThrow(), archive);
            else window.verify(parent, plan, starting, retained.ending(), retained.nativeStopRead().orElseThrow(), clockChildren, archive); // Explicit legacy v2/v3 DATA.
            var boundary = BattleAdvanceFrame.boundary(BattleAdvanceFrame.decode(starting), BattleAdvanceFrame.decode(retained.ending()));
            var progress = boundary.map(value -> switch (value.kind()) {
                case ACTIVE_EVENT, PENDING_CHARACTER_INTERACTION -> RouteContactComposite.ClockProgress.MODAL_INTERRUPTED;
                default -> RouteContactComposite.ClockProgress.BOUNDARY_INTERRUPTED;
            }).orElse(RouteContactComposite.ClockProgress.POSTCONDITION);
            StrictJson.require(retained.timelinePolicy().equals("bounded_frozen_route_window") && retained.progressStatus() == progress
                    && retained.checkpointEligible() == boundary.isEmpty(), "route window progress/policy/checkpoint flags differ from original native frames");
        } else {
            String policy = proof.kind() == RouteContactModel.ProofKind.CONTACT_FREE
                    ? "exact_one_day_contact_free_speed_" + retained.timelineSpeed() : "exact_one_day_unavoidable_contact";
            var plan = new AdvancePlan(BigInteger.valueOf(start.dateRaw()), BigInteger.valueOf(proof.targetDateRaw()), 1,
                    retained.timelineSpeed(), policy, true, retained.nativeStopRead().isPresent()
                    ? AdvancePlan.ClockMode.EXACT_SENTINEL : AdvancePlan.ClockMode.POLLED, Optional.empty());
            var progress = AdvanceClock.ProgressStatus.valueOf(retained.progressStatus().name());
            StrictJson.require(retained.timelinePolicy().equals(policy)
                    && retained.checkpointEligible() == (progress == AdvanceClock.ProgressStatus.POSTCONDITION), "route exact-day policy/checkpoint flags differ");
            if (retained.originalReport().isPresent()) AdvanceResult.verifyClockReport(exact, parent, plan, starting, retained.ending(), progress,
                    retained.nativeStopRead(), clockChildren, retained.originalReport().orElseThrow(), archive);
            else exact.verify(parent, plan, starting, retained.ending(), progress, retained.nativeStopRead(), clockChildren, archive); // Explicit legacy v2/v3 DATA.
        }
        StrictJson.require(end.dateRaw() >= start.dateRaw() && end.dateRaw() <= proof.targetDateRaw(), "route clock endpoint crossed its immutable proof target");
        return retained;
    }
}
