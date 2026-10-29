package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Path;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual shared request/writer/collector scope. No RootContext, Native permit or ROOT packet is invented. */
final class RootTurnBundleReadSourceTest {
    @TempDir Path root;

    @Test void originalPlanningRoundReusesExactFrameForSequentialReadsAndClearsOnFailure() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("round"), false)) {
            fixture.collector.bindPlanningEvidence((same, request, lease) -> {
                fixture.writer.requireSession(same); assertEquals(request.observations().snapshot(), lease.frame().semantic());
            });
            fixture.writer.locked(same -> {
                try { return fixture.collector.withPlanningRound(same, () -> {
                    var ready = assertInstanceOf(org.xar.ck3.control.application.session.SessionPorts.Ready.class,
                            fixture.collector.observe(same, fixture.observationIdentity(), java.time.Instant.now().plusSeconds(40)));
                    var request = ready.request(); var first = new AtomicReference<Complete>();
                    int reads = fixture.nativePacketReads(), checks = fixture.sourceChecks.get();
                    fixture.collector.currentPlanning(same, request, request.deadline(), (original, lease) -> { first.set(lease.frame()); return null; });
                    fixture.collector.currentPlanning(same, request, request.deadline(), (original, lease) -> {
                        assertSame(first.get(), lease.frame()); assertEquals(request.before(), lease.frame().identity());
                        assertThrows(IllegalArgumentException.class, () -> fixture.collector.current(same,
                                new org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity(request.before().machineId(),
                                        request.before().game(), request.before().frame(), request.before().observationVersion()+1),
                                request.deadline(), ignored -> null));
                        return null;
                    });
                    assertEquals(reads, fixture.nativePacketReads());
                    assertTrue(fixture.sourceChecks.get() > checks); // Existing source checks run; no fresh qualification is minted.
                    throw new java.io.IOException("controlled policy failure");
                }); } catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new java.io.IOException(interrupted); }
                catch (java.io.IOException failure) { assertEquals("controlled policy failure", failure.getMessage()); return null; }
            });
            // A failed round releases its scope; a new turn creates a distinct real observation normally.
            fixture.ready(); assertEquals(0, fixture.nativeActionWrites());
        }
    }

    @Test void realHeldFrameCheckUsesOriginalWriterAndCannotEscapeOrBeCloned() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("held"), false)) {
            PlanningRequest request = fixture.ready().request(); var escaped = new AtomicReference<Complete>();
            long originalSequence = fixture.sequence();
            fixture.writer.locked(same -> fixture.collector.currentPlanning(same, request, request.deadline(), (retained, lease) -> {
                Complete actual = lease.frame(); escaped.set(actual);
                RootTurnBundleReadSource.requirePlanningFrame(retained, actual);
                int captures = fixture.collectorLocks.get();
                fixture.collector.requireHeldFrame(same, actual); fixture.collector.requireHeldFrame(same, actual);
                assertEquals(captures, fixture.collectorLocks.get(), "held-frame validation must not reopen the collector writer lock");
                Complete identicalData = new Complete(actual.identity(), actual.source(), actual.sessionId(), actual.connectionGeneration(),
                        actual.semantic(), actual.originalEvidence(), actual.observedAt(), actual.fullBindingSha256());
                RootTurnBundleReadSource.requirePlanningFrame(retained, identicalData); // DATA equality is not scope authority.
                assertThrows(IllegalArgumentException.class, () -> fixture.collector.requireHeldFrame(same, identicalData));
                return null;
            }));
            fixture.writer.locked(same -> {
                assertThrows(IllegalArgumentException.class, () -> fixture.collector.requireHeldFrame(same, escaped.get())); return null;
            });
            assertEquals(originalSequence, fixture.sequence(), "read-only guard validation must not append canonical action events");
        }
    }

    @Test void actualPlanningProducerCannotBeReplacedByAnotherSessionOrChangedCompleteSnapshot() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("request"), false)) {
            PlanningRequest request = fixture.ready().request();
            long originalSequence = fixture.sequence();
            fixture.writer.locked(same -> fixture.collector.currentPlanning(same, request, request.deadline(), (retained, lease) -> {
                var observation = retained.observations();
                var changedSession = new PlanningRequest(retained.before(), retained.source(), retained.sessionId() + "-other", retained.deadline(), observation);
                assertThrows(IllegalArgumentException.class, () -> RootTurnBundleReadSource.requirePlanningFrame(changedSession, lease.frame()));
                var changedObservation = new PlanningObservation(observation.snapshot().with("paused", new OpportunityJson.Bool(false)),
                        observation.history(), observation.actionSteps(), observation.bridgeCapabilities(), observation.battleSpeedReadiness(),
                        observation.actionFacts(), observation.campaignGoal(), observation.crossRunPlan(), observation.initialLifestyleFocusRequired());
                var changed = new PlanningRequest(retained.before(), retained.source(), retained.sessionId(), retained.deadline(), changedObservation);
                assertThrows(IllegalArgumentException.class, () -> RootTurnBundleReadSource.requirePlanningFrame(changed, lease.frame()));
                fixture.collector.requireHeldFrame(same, lease.frame()); return null;
            }));
            assertEquals(originalSequence, fixture.sequence());
        }
    }
}
