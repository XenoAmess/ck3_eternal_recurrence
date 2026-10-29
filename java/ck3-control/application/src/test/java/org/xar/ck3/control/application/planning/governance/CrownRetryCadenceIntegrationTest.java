package org.xar.ck3.control.application.planning.governance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityCodec;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy;
import org.xar.ck3.control.planning.optionalcadence.CadenceModels;
import org.xar.ck3.control.planning.optionalcadence.OptionalCheckCadence;
import org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldownCodec;
import org.xar.ck3.control.wave3.governance.crownretry.CrownRetryCodec;

/** Real synthetic publisher/private proof -> same-scope state -> policy/forwarder/transcript. No actual Native/Game qualification. */
final class CrownRetryCadenceIntegrationTest {
    private static CadenceModels.State futureCadence(CrownRetryDueTest.CapturedDue original) {
        String episode = original.observed().frame().episodeRunId();
        CadenceModels.State state = CadenceModels.State.empty(episode);
        BigInteger oldDate = original.proof().input().currentObserved().frame().identity().dateRaw();
        for (int i = 1; i <= 3; i++) state = OptionalCheckCadence.observeRead(state, CadenceModels.Domain.CROWN,
                new CadenceModels.Frame(episode, oldDate, BigInteger.valueOf(i)), CadenceModels.ReadCompletion.COMPLETE_NO_ACTION);
        return state;
    }
    private static PlanningRequest request(CrownRetryDueTest.CapturedDue original) {
        // Reuse the complete ordinary software fixture; the publisher retains every original frame field.
        Obj snapshot = GovernanceFixtures.request().observations().snapshot();
        for (var entry : original.semantic().members().entrySet()) snapshot = snapshot.with(entry.getKey(), entry.getValue());
        var observation = new PlanningObservation(snapshot, List.of(), Set.of(new OperationKey("life-advance"), GovernancePolicies.CROWN),
                Set.of(), Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false);
        return new PlanningRequest(original.observed(), original.source(), "synthetic-current-session",
                Instant.parse(original.source().observedAtUtc()).plusSeconds(60), observation);
    }
    private static OrdinaryPolicy.Draft advance(PlanningRequest request) {
        var expected = new ExpectedPostcondition(1, request.before(), request.source(), "synthetic-timeline/v1",
                List.of(new ExpectedBoolean(new FieldKey("paused"), true)));
        var command = new ActionCommand("synthetic-retained-advance", request.before(), request.source(), request.sessionId(),
                new OperationKey("life-advance"), new Obj(java.util.Map.of()), expected, new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), request.deadline());
        return new OrdinaryPolicy.Draft("synthetic-core", "ordinary", "original advance", OrdinaryPolicy.Kind.ORDINARY,
                Optional.of(command), OrdinaryPolicy.Purpose.DATE_ADVANCE, Optional.empty(), new Obj(java.util.Map.of()));
    }
    private static final class ActualReads implements GovernanceObservationSupplier {
        private final GovernanceStateSupplier states;
        private final CrownRetryDueTest.CapturedDue original;
        private int crownReads, clockReads;
        private boolean forbidNewQueries;
        private ActualReads(CrownRetryDueTest.CapturedDue original, boolean proofPresent) {
            this.original = original;
            var scope = new GovernanceBorrowedSession(original.borrowed(), original.writerLock(), same -> assertSame(original.borrowed(), same));
            var frames = GovernanceStateSupplier.verifiedCrownRetryFrames(scope, original.publication(),
                    () -> proofPresent ? Optional.of(original.proof()) : Optional.empty(), original.producer());
            var cadence = (DomainBodies.Available) readCadence(original);
            states = new GovernanceStateSupplier(scope, Optional.of(GovernanceStateSupplier.cadence(cadence.reference().producerSources())),
                    Optional.empty(), Optional.empty(), Optional.of(GovernanceStateSupplier.legacyCrown(
                            original.proof().body().contractSchema(), original.proof().body().producerSources())), frames);
        }
        @Override public Read<Durable> durable(PlanningRequest request) { return states.read(request); }
        @Override public Read<CrownRetryDue.VerifiedDue> crownRetryDue(PlanningRequest request) { return states.crownRetryDue(request); }
        @Override public Read<CrownRetryCodec.MatchRequest> crownRetry(PlanningRequest request, String law) { return states.crownRetry(request, law); }
        @Override public Read<Crown> crown(PlanningRequest request) {
            assertFalse(forbidNewQueries, "replay must consume actual prior typed query"); crownReads++;
            var old = GovernanceFixtures.crown(request).readback();
            var blocked = new CrownAuthorityPolicy.Readback(old.schema(), old.available(), old.paused(), old.groupKey(), old.activeLawKey(),
                    old.candidates().stream().map(row -> row.active() ? row : new CrownAuthorityPolicy.Candidate(row.lawKey(), false,
                            row.engineFinalOnly(), false, "actual synthetic engine block retained", row.costs())).toList(),
                    old.resources(), old.titleSuccessors(), old.sourceFrame(), old.readOnly(), old.advertised());
            return new Known<>(new Crown(blocked, object(parse(CrownAuthorityCodec.encodeReadback(blocked)), "synthetic complete Crown query")),
                    List.of(original.proof().input().crownReadback()));
        }
        @Override public Read<CrownCooldownCodec.ClockRequest> crownCooldown(PlanningRequest request) {
            assertFalse(forbidNewQueries, "replay must not execute another native clock query"); clockReads++;
            return new Unavailable<>("fresh synthetic final-terms query unavailable; no law or retry may be fabricated");
        }
        @Override public Read<Life> lifestyle(PlanningRequest request, String focus, boolean opening) { throw new AssertionError("unrelated LIFE read"); }
        @Override public Read<OpeningComparison> openingComparison(PlanningRequest request) { throw new AssertionError("unrelated opening read"); }
        @Override public Read<CouncilSelection.Query> council(PlanningRequest request, CouncilSelection.Position position) { throw new AssertionError("unrelated Council read"); }
        @Override public Read<CouncilSelection.Query> coreCouncil(PlanningRequest request) { throw new AssertionError("unrelated core Council read"); }
        @Override public Read<CouncilRoot> councilRoot(PlanningRequest request) { throw new AssertionError("unrelated Council root read"); }
    }
    private static DomainBodies.Read readCadence(CrownRetryDueTest.CapturedDue original) {
        try { return original.borrowed().readDomain(DomainBodies.Slot.OPTIONAL_CADENCE); }
        catch (java.io.IOException unavailable) { throw new java.io.UncheckedIOException(unavailable); }
    }

    @Test void realPrivateDueBypassesThirtyDayCadenceAndRequeriesBlockedLawWithoutCadenceCredit() throws Exception {
        var basis = CrownRetryDueTest.publishedDueFixtureAtDays(11);
        var cadence = futureCadence(basis); var original = basis.withCadence(cadence);
        var request = request(original); var reads = new ActualReads(original, true);
        var forwarded = new GovernanceCouncilSupplier(reads, new GovernanceCouncilSupplier.CouncilReadPort() {
            public Read<CouncilSelection.Query> readPrivate(PlanningRequest ignored, CouncilSelection.Position position) { throw new AssertionError("unrelated Council query"); }
            public Read<CouncilSelection.Query> readCore(PlanningRequest ignored) { throw new AssertionError("unrelated Council core query"); }
        });
        var policy = new GovernancePolicies.Crown(forwarded, original.proof().input().runtimeSources().getFirst());
        var result = assertInstanceOf(OrdinaryPolicy.Replace.class, policy.evaluate(request, advance(request)));
        assertEquals(1, reads.crownReads); assertEquals(1, reads.clockReads);
        assertEquals(OrdinaryPolicy.Purpose.DATE_ADVANCE, result.draft().purpose());
        assertTrue(GovernanceCadencePublication.fromDetail(result.draft().detail()).isEmpty());
        assertEquals(cadence, ((Known<Durable>) reads.durable(request)).value().cadence().orElseThrow());
        assertFalse(original.due().authorizesAction());
    }

    @Test void futureOrMissingPrivateProofRetainsOptionalCadenceWithoutAnotherQuery() throws Exception {
        for (boolean proof : List.of(false, true)) {
            var basis = CrownRetryDueTest.publishedDueFixtureAtDays(proof ? 1 : 11);
            var original = basis.withCadence(futureCadence(basis)); var request = request(original); var reads = new ActualReads(original, proof);
            var result = new GovernancePolicies.Crown(reads, original.proof().input().runtimeSources().getFirst()).evaluate(request, advance(request));
            assertInstanceOf(OrdinaryPolicy.Keep.class, result); assertEquals(0, reads.crownReads); assertEquals(0, reads.clockReads);
        }
    }

    @Test void normalCompletedReviewReplaysPrivateDueTapeAndAllOriginalReadsWithoutAnotherQuery() throws Exception {
        var basis = CrownRetryDueTest.publishedDueFixtureAtDays(1);
        var original = basis.withCadence(CadenceModels.State.empty(basis.observed().frame().episodeRunId()));
        var request = request(original); var reads = new ActualReads(original, true);
        var available = assertInstanceOf(DomainBodies.Available.class, readCadence(original));
        var replay = new GovernanceCadenceReplay(() -> original.borrowed(), same -> assertSame(original.borrowed(), same),
                (same, ref) -> { assertEquals(available.reference().payload(), ref); return available.canonicalBody(); });
        var policy = replay.record(new GovernancePolicies.Crown(replay.observe(reads), original.proof().input().runtimeSources().getFirst()));
        var produced = assertInstanceOf(OrdinaryPolicy.Replace.class, policy.evaluate(request, advance(request)));
        var plan = GovernanceCadencePublication.fromDetail(produced.draft().detail()).orElseThrow();
        assertEquals(List.of(CadenceModels.Domain.CROWN), plan.completeNoActionDomains()); assertEquals(1, reads.crownReads); assertEquals(0, reads.clockReads);
        reads.forbidNewQueries = true;
        var evidence = List.of(original.proof().input().runtimeSources().getFirst(), original.borrowed().persistedHead(),
                available.reference().payload(), available.reference().producerSources().getFirst(), original.proof().body().payload(),
                original.proof().input().crownReadback(), original.proof().input().finalTermsConsume(), original.proof().input().source().sourceRef());
        // References come from the actual typed publisher/domain reads; private transcript replay independently checks their order.
        var material = replay.replay(original.borrowed().head(), available.reference(), plan, evidence);
        assertEquals(plan, material.actualReplayedPlan());
        assertEquals(1, GovernanceCadencePublication.reduce(plan).row(CadenceModels.Domain.CROWN).consecutiveNoAction());
        assertTrue(evidence.contains(original.proof().body().payload()));
        assertThrows(IllegalArgumentException.class, () -> replay.replay(original.borrowed().head(), available.reference(), plan, List.of()));
    }
}
