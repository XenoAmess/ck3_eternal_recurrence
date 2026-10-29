package org.xar.ck3.control.application.routecontact;

import static org.xar.ck3.control.application.routecontact.RouteContactModel.*;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.AdvanceClock;
import org.xar.ck3.control.application.advance.AdvanceObservationPort;
import org.xar.ck3.control.application.advance.AdvancePrimitives;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.routecontact.RouteContactComposite.ClockResult;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Lock-held route replay. All three Root ports are mandatory and read archived inputs; none may query or submit Native. */
public final class RouteContactArchivedVerifier {
    public enum FailureKind { STEP_POSTCONDITION_ERROR }
    /** Verified original failure DATA, never a settled action, Ready lease or retry permission. */
    public static final class FailureReport {
        private final String message; private final RawJson numericPartial; private final ExactRef domainEvidence;
        private FailureReport(String message, RawJson numericPartial, ExactRef domainEvidence) {
            this.message = message; this.numericPartial = numericPartial; this.domainEvidence = domainEvidence;
        }
        public FailureKind kind() { return FailureKind.STEP_POSTCONDITION_ERROR; }
        public String message() { return message; }
        public RawJson numericPartial() { return numericPartial; }
        public ExactRef domainEvidence() { return domainEvidence; }
    }
    @FunctionalInterface public interface FrameReplay {
        /** Rebuild from the original native packet and the actual complete Driver; retained semantic JSON alone is insufficient. */
        AdvanceObservationPort.Frame replay(WriterContracts.Head head, AdvanceObservationPort.Frame retained, ActionPorts.OutcomeArchive archive);
    }
    public interface HistoryReplay {
        List<RouteContactProofs.QueryEntry> queries(WriterContracts.Head head, ActionCommand parent, AdvanceObservationPort.Frame starting, ActionPorts.OutcomeArchive archive);
        List<TimelineEntry> timeline(WriterContracts.Head head, ActionCommand parent, AdvanceObservationPort.Frame starting, ActionPorts.OutcomeArchive archive);
    }
    @FunctionalInterface public interface ClockReplay {
        /** Shared life/battle owner must replay the original primitive/status contracts, including polled exact-day mode and canceled no-resume modal. */
        ClockResult replay(WriterContracts.Head head, ActionCommand parent, AdvanceObservationPort.Frame starting,
                Proof proof, ClockResult retained, List<ActionReceipt> clockChildren, ActionPorts.OutcomeArchive archive);
        default RawJson pauseResult(ActionReceipt child, ActionPorts.OutcomeArchive archive) {
            throw new IllegalStateException("actual original pause Driver result replay is unavailable");
        }
        default void verifyPause(ActionReceipt child, ActionPorts.OutcomeArchive archive) {
            throw new IllegalStateException("actual original pause Native/Driver replay is unavailable");
        }
    }
    private final FrameReplay frames;
    private final HistoryReplay history;
    private final ClockReplay clocks;
    private final boolean explicitCampaignDeadline;
    public RouteContactArchivedVerifier(FrameReplay frames, HistoryReplay history, ClockReplay clocks, boolean explicitCampaignDeadline) {
        this.frames = Objects.requireNonNull(frames); this.history = Objects.requireNonNull(history); this.clocks = Objects.requireNonNull(clocks);
        this.explicitCampaignDeadline = explicitCampaignDeadline;
    }
    public NativeRecordedEvidenceVerifier.Binding binding(OperationKey exactOperation, ExactRef definitionSource) {
        StrictJson.require(RouteContactSteps.supports(exactOperation.value()), "exact route verifier operation required");
        return new NativeRecordedEvidenceVerifier.Binding(exactOperation, definitionSource, this::verify);
    }
    public void verify(WriterContracts.Head head, ActionReceipt actual, ActionPorts.OutcomeArchive archive) {
        StrictJson.require(actual.state() instanceof ActionState.CompositeSettled, "route verifier requires the real composite settlement");
        var settled = (ActionState.CompositeSettled)actual.state();
        ActionState.EffectObservation semantic;
        if (settled.settlement() instanceof ActionState.Applied applied) semantic = applied.observation();
        else if (settled.settlement() instanceof ActionState.CompositeControlApplied control) semantic = control.observation().semantic();
        else throw new IllegalArgumentException("route verifier cannot replace an original rejection");
        var document = RouteContactEvidenceCodec.decode(archive.loadFullMaterial(RouteContactEvidenceArchive.basis(semantic)), archive);
        StrictJson.require(document instanceof RouteContactEvidenceCodec.Completed && document.parent().equals(actual.command())
                && actual.bodySha256().equals(ActionCodec.bodySha256(document.parent())), "route completion original parent differs");
        var completion = ((RouteContactEvidenceCodec.Completed)document).completion();
        var startingBasis = RootGuardEvidence.frameBasis(settled.execution().guard(), archive);
        StrictJson.require(startingBasis.nativeFrame().equals(completion.starting().originalEvidence())
                && startingBasis.driverFacts().equals(DriverObservationEvidenceReader.reference(completion.starting().semantic().get("java_driver_facts_evidence"))),
                "route starting history/frame basis differs from its original guarded submission");
        StrictJson.require(completion.children().size() == settled.execution().children().size(), "route canonical child count differs");
        for (int index = 0; index < completion.children().size(); index++) {
            ActionReceipt child = completion.children().get(index); CompositeExecution.Child canonical = settled.execution().children().get(index);
            StrictJson.require(child.command().actionId().equals(canonical.actionId()) && child.bodySha256().equals(canonical.bodySha256())
                    && (child.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED || RouteContactComposite.currentPauseConfirmed(child)),
                    "route original canonical child differs or lacks its applied/typed pause settlement");
            requireCurrentPauseOriginal(child);
        }
        AdvanceObservationPort.Frame startRaw = frames.replay(head, completion.starting(), archive), endRaw = frames.replay(head, completion.ending(), archive);
        StrictJson.require(startRaw.equals(completion.starting()) && endRaw.equals(completion.ending()), "route full Driver/native frame replay differs");
        Frame start = RouteContactCodec.frame(startRaw), end = RouteContactCodec.frame(endRaw);
        StrictJson.require(start.mapReady() && start.paused() && !start.playerDecision(), "route starting admission differs");
        var requested = RouteContactSteps.parse(actual.command().operation().value());
        var days = RouteContactProofs.oneDayEntries(start, history.queries(head, actual.command(), startRaw, archive), history.timeline(head, actual.command(), startRaw, archive));
        Proof proof = requested.days() == 1 ? days.get(requested.scope())
                : RouteContactProofs.window(start, days, requested.scope(), requested.days(), explicitCampaignDeadline).orElse(null);
        StrictJson.require(proof != null && proof.equals(completion.proof()), "route original complete surviving-history proof differs");
        if (completion.clockResult().originalReport().isPresent()) RouteContactComposite.requireIntent(actual.command(), start, proof);
        if (requested.days() > 1) StrictJson.require(start.ownArmies().stream().filter(Army::controllable).noneMatch(army -> army.inCombat() || army.retreating()), "route bounded admission acquired combat or retreat");
        AdvanceObservationPort.Frame clockEnd = frames.replay(head, completion.clockResult().ending(), archive);
        StrictJson.require(clockEnd.equals(completion.clockResult().ending()), "route original clock endpoint differs");
        boolean refreshed = !clockEnd.equals(endRaw); List<ActionReceipt> clockChildren = completion.children();
        if (completion.clockResult().originalReport().isPresent()) StrictJson.require(refreshed == completion.refresh().isPresent(), "current route refresh report presence differs from actual clock/publication");
        if (completion.refresh().isPresent()) {
            var originalRefresh = completion.refresh().orElseThrow();
            verifyRefreshResult(originalRefresh, archive);
            StrictJson.require(originalRefresh.from().equals(clockEnd) && originalRefresh.published().equals(Optional.of(endRaw))
                    && originalRefresh.child().equals(clockChildren.isEmpty() ? Optional.empty() : Optional.of(clockChildren.getLast()))
                    && originalRefresh.ackStatus().equals(Optional.of("already_paused")), "route retained refresh fields differ from actual child and frames");
        }
        if (refreshed) {
            StrictJson.require(proof.kind() == ProofKind.UNAVOIDABLE_CURRENT_PROVINCE_CONTACT && !clockChildren.isEmpty()
                    && RouteContactPostconditions.observed(start, RouteContactCodec.frame(clockEnd), proof).isEmpty(), "route refresh occurred outside original contact branch");
            ActionReceipt refresh = clockChildren.getLast();
            StrictJson.require(refresh.command().operation().value().equals("pause-map") && refresh.command().before().equals(clockEnd.identity())
                    && (RouteContactComposite.currentPauseConfirmed(refresh) || refresh.applied().isPresent())
                    && refresh.ack().isPresent() && AdvancePrimitives.nativeResult(refresh.ack().orElseThrow(), "pause-map").path("status").asText().equals("already_paused")
                    && RouteContactPostconditions.samePausedRefreshOwner(RouteContactCodec.frame(clockEnd), end), "route one same-date refresh original contract differs");
            clockChildren = List.copyOf(clockChildren.subList(0, clockChildren.size() - 1));
        }
        ClockResult clock = clocks.replay(head, actual.command(), startRaw, proof, completion.clockResult(), clockChildren, archive);
        StrictJson.require(clock.equals(completion.clockResult()) && clock.nativeClockVerified() && !clock.unknown(), "route shared clock original replay differs");
        boolean controlOnly = settled.settlement() instanceof ActionState.CompositeControlApplied;
        Optional<Transition> transition = Optional.empty();
        if (!controlOnly && proof.kind() == ProofKind.UNAVOIDABLE_CURRENT_PROVINCE_CONTACT) {
            transition = RouteContactPostconditions.observed(start, end, proof);
            if (transition.isEmpty() && refreshed) transition = RouteContactPostconditions.predictedEndpoint(start, end, proof);
            StrictJson.require(transition.isPresent(), "route unavoidable contact original transition is absent");
        }
        StrictJson.require(transition.equals(completion.transition()) && semantic.after().equals(endRaw.identity()) && semantic.source().equals(endRaw.source())
                && semantic.sessionId().equals(endRaw.sessionId()) && semantic.observerSchema().equals(RouteContactComposite.OBSERVER)
                && semantic.provenance().equals(endRaw.provenance()) && semantic.observedAt().equals(endRaw.observedAt())
                && semantic.originalEvidence().equals(endRaw.originalEvidence())
                && semantic.actual().equals(RouteContactComposite.actualValues(start, end, proof, transition, clock, controlOnly)), "route effect values differ from original replay");
        if (controlOnly) {
            StrictJson.require(!refreshed && end.playerDecision() && end.owner().equals(start.owner()) && end.mapReady() && end.paused()
                    && end.dateRaw() == start.dateRaw() && end.nativeRevision().equals(start.nativeRevision()) && clock.nativeStopRead().isPresent(), "route zero-day control boundary differs");
            var reconstructed = AdvanceClock.compositeControlTerminal(actual.command(), clock.nativeStopRead().orElseThrow(), completion.children(), semantic);
            StrictJson.require(reconstructed.equals(((ActionState.CompositeControlApplied)settled.settlement()).observation()), "route original cancellation/status/semantic control evidence differs");
        } else StrictJson.require(end.mapReady() && end.paused() && RouteContactPostconditions.newer(start, end)
                && end.dateRaw() >= start.dateRaw() && end.dateRaw() <= proof.targetDateRaw(), "route original final paused/date successor differs");
    }
    /** Reopens a canonical failed contact branch without changing UNKNOWN or granting action/day/save credit. */
    public Optional<FailureReport> verifyFailure(WriterContracts.Head head, ActionReceipt actual, ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(head); Objects.requireNonNull(actual); Objects.requireNonNull(archive);
        StrictJson.require(actual.state() instanceof ActionState.CompositeUnknown && RouteContactSteps.supports(actual.command().operation().value()), "real canonical route UNKNOWN required");
        StrictJson.require(ContinuityActionJournal.lookup(head.state(), actual.command().actionId(), archive).filter(actual::equals).isPresent(), "failed route is not the exact current canonical receipt");
        var unknown = (ActionState.CompositeUnknown) actual.state();
        if (unknown.evidence().isEmpty()) return Optional.empty();
        ExactRef domain = unknown.evidence().getFirst();
        var document = RouteContactEvidenceCodec.decode(archive.loadFullMaterial(domain), archive);
        StrictJson.require(document instanceof RouteContactEvidenceCodec.Failed && document.parent().equals(actual.command())
                && actual.bodySha256().equals(ActionCodec.bodySha256(document.parent())), "route failure original parent differs");
        var failure = ((RouteContactEvidenceCodec.Failed) document).failure();
        if (failure.clockResult().isEmpty() || failure.originalErrorMessage().isEmpty()) return Optional.empty();
        StrictJson.require(unknown.reason().equals(failure.originalErrorMessage().orElseThrow()) && failure.refresh().isPresent(), "failed contact error differs from its original canonical source branch");
        var startingBasis = RootGuardEvidence.frameBasis(unknown.execution().guard(), archive);
        StrictJson.require(unknown.execution().handlerId().equals(RouteContactComposite.HANDLER)
                && unknown.execution().guard().observed().equals(actual.command().before())
                && unknown.execution().guard().source().equals(actual.command().source())
                && unknown.execution().guard().sessionId().equals(actual.command().sessionId())
                && unknown.execution().guard().operation().equals(actual.command().operation())
                && startingBasis.nativeFrame().equals(failure.starting().originalEvidence())
                && startingBasis.driverFacts().equals(DriverObservationEvidenceReader.reference(failure.starting().semantic().get("java_driver_facts_evidence"))), "failed route original guard/frame differs");
        StrictJson.require(failure.children().size() == unknown.execution().children().size(), "failed route canonical child count differs");
        for (int index = 0; index < failure.children().size(); index++) {
            ActionReceipt child = failure.children().get(index); var reference = unknown.execution().children().get(index);
            StrictJson.require(child.command().actionId().equals(reference.actionId()) && child.bodySha256().equals(reference.bodySha256())
                    && ContinuityActionJournal.lookup(head.state(), reference.actionId(), archive).filter(child::equals).isPresent(), "failed route child differs from actual canonical writer");
        }
        var starting = frames.replay(head, failure.starting(), archive); var ending = frames.replay(head, failure.ending(), archive);
        StrictJson.require(starting.equals(failure.starting()) && ending.equals(failure.ending()), "failed route original full frames differ");
        Frame start = RouteContactCodec.frame(starting);
        StrictJson.require(start.mapReady() && start.paused() && !start.playerDecision(), "failed route original admission differs");
        var request = RouteContactSteps.parse(actual.command().operation().value());
        var days = RouteContactProofs.oneDayEntries(start, history.queries(head, actual.command(), starting, archive), history.timeline(head, actual.command(), starting, archive));
        Proof proof = request.days() == 1 ? days.get(request.scope()) : RouteContactProofs.window(start, days, request.scope(), request.days(), explicitCampaignDeadline).orElse(null);
        StrictJson.require(proof != null && proof.equals(failure.proof()) && proof.kind() == ProofKind.UNAVOIDABLE_CURRENT_PROVINCE_CONTACT, "failed contact original same-frame proof differs");
        RouteContactComposite.requireIntent(actual.command(), start, proof);
        var clock = failure.clockResult().orElseThrow(); var clockEnd = frames.replay(head, clock.ending(), archive);
        StrictJson.require(clockEnd.equals(clock.ending()) && RouteContactPostconditions.observed(start, RouteContactCodec.frame(clockEnd), proof).isEmpty(), "failed refresh did not follow the original missing contact transition");
        var refresh = failure.refresh().orElseThrow(); StrictJson.require(refresh.from().equals(clockEnd), "failed refresh crossed original clock endpoint");
        if (refresh.child().filter(RouteContactComposite::currentPauseConfirmed).isPresent() && refresh.originalDriverResult().isEmpty()) return Optional.empty();
        verifyRefreshResult(refresh, archive);
        List<ActionReceipt> clockChildren = failure.children();
        if (refresh.child().isPresent()) {
            var child = refresh.child().orElseThrow(); StrictJson.require(!clockChildren.isEmpty() && clockChildren.getLast().equals(child), "failed refresh is not its actual last child");
            requireCurrentPauseOriginal(child);
            clockChildren = List.copyOf(clockChildren.subList(0, clockChildren.size() - 1));
            if (refresh.ackStatus().isPresent()) StrictJson.require(RouteContactComposite.currentPauseConfirmed(child)
                    && refresh.ackStatus().orElseThrow().equals(AdvancePrimitives.nativeResult(child.ack().orElseThrow(), "pause-map").path("status").asText()), "failed refresh ACK status changed");
        }
        if (refresh.published().isPresent()) {
            var publication = frames.replay(head, refresh.published().orElseThrow(), archive);
            StrictJson.require(publication.equals(refresh.published().orElseThrow()) && publication.equals(ending)
                    && RouteContactPostconditions.newer(RouteContactCodec.frame(clockEnd), RouteContactCodec.frame(publication)), "failed refresh publication differs");
            Frame end = RouteContactCodec.frame(publication);
            boolean validTransition = RouteContactPostconditions.observed(start, end, proof).isPresent()
                    || !proof.strictFollowup() && RouteContactPostconditions.predictedEndpoint(start, end, proof).isPresent();
            StrictJson.require(!RouteContactPostconditions.samePausedRefreshOwner(RouteContactCodec.frame(clockEnd), end) || !validTransition, "a successful contact transition cannot become an original postcondition failure");
        }
        StrictJson.require(clocks.replay(head, actual.command(), starting, proof, clock, clockChildren, archive).equals(clock), "failed contact original successful clock report changed");
        return Optional.of(new FailureReport(failure.originalErrorMessage().orElseThrow(), RawJson.fullMaterial(org.xar.ck3.control.application.driver.DriverJson.encode(RouteContactEvidenceCodec.result(document))), domain));
    }
    private static void requireCurrentPauseOriginal(ActionReceipt child) {
        if (RouteContactComposite.currentPauseConfirmed(child)) {
            var settled = (ActionState.Settled) child.state();
            PauseConfirmation.validate(child.command(), settled.attempt(), settled.dispatch(), ((ActionState.PauseConfirmed) settled.settlement()).observation());
        }
    }
    private void verifyRefreshResult(RouteContactComposite.ContactRefresh refresh, ActionPorts.OutcomeArchive archive) {
        if (refresh.originalDriverResult().isPresent()) StrictJson.require(refresh.originalDriverResult().orElseThrow().equals(
                clocks.pauseResult(refresh.child().orElseThrow(), archive)), "retained complete pause Driver result differs from its actual original Native/Driver replay");
        else refresh.child().filter(RouteContactComposite::currentPauseConfirmed).ifPresent(child -> clocks.verifyPause(child, archive));
    }
}
