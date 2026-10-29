package org.xar.ck3.control.nativebridge.capabilities.governance;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.governance.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.council.CouncilPrivateCodec;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.optionalcadence.CadenceModels;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Actual writer/collector/coordinator/NGT/archive with controlled software packet loss. No native/Game qualification. */
final class CouncilTechnicalReadIntegrationTest {
    @TempDir Path temporary;
    private static final String SHA = "ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d";
    private enum Edge {
        NEGATIVE_ACK(1), LOST_ACK(1), MALFORMED_RESULT(1), NORMAL_RESULT(1), STALE_REJECTION(1),
        PENDING_NEGATIVE_ACK(2), PENDING_MALFORMED_RESULT(2), PENDING_ONLY(5);
        private final int expectedReads;
        Edge(int expectedReads) { this.expectedReads = expectedReads; }
        boolean pending() { return this == PENDING_NEGATIVE_ACK || this == PENDING_MALFORMED_RESULT || this == PENDING_ONLY; }
    }
    private record Scene(ActionWriterIntegrationFixture actual, PlanningRequest request, ActionCommand basis,
            Read<CouncilSelection.Query> result, NativeCouncilReadPort port, int writesBefore, int expectedReads) { }
    @FunctionalInterface private interface Check { void run(Scene scene) throws Exception; }

    private static NativeCouncilReadPort.SessionAccess sessions(ActionWriterIntegrationFixture actual) {
        return new NativeCouncilReadPort.SessionAccess() {
            @Override public <T> T withSession(PlanningRequest request, NativeCouncilReadPort.SessionWork<T> work)
                    throws IOException, InterruptedException {
                var borrowed = actual.writer.activeSession();
                if (borrowed.isPresent()) {
                    actual.writer.requireSession(borrowed.orElseThrow());
                    return work.run(borrowed.orElseThrow());
                }
                try {
                    return actual.writer.locked(same -> {
                        try { return work.run(same); }
                        catch (InterruptedException interrupted) { throw new IOException(interrupted); }
                    });
                } catch (IOException failure) {
                    if (failure.getCause() instanceof InterruptedException interrupted) throw interrupted;
                    throw failure;
                }
            }
        };
    }
    private void scene(String name, Edge edge, Check check) throws Exception {
        var definitions = new AtomicReference<PrivateCouncilReads>();
        var publicReads = new AtomicReference<GovernanceNativeReads>();
        var scenario = new ActionWriterIntegrationFixture.SoftwareReadScenario(SHA, "council-technical-read-software", source -> {
            var privateDefinitions = new PrivateCouncilReads(source); definitions.set(privateDefinitions);
            publicReads.set(new GovernanceNativeReads(source, "1.20.0.2", SHA));
            return privateDefinitions.registeredContracts();
        }, prepared -> new RawJson(StrictJson.canonical(edge.pending()
                && (edge == Edge.PENDING_ONLY || !prepared.step().equals(CouncilPrivateCodec.STATUS))
                ? StrictJson.object().put("private_council_transport", true).put("advertised", false).put("step", prepared.step()).put("status", "pending")
                : StrictJson.object())), Optional.of("1.20.0.2"), Set.of());
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve(name), false, scenario)) {
            ActionCommand basis = actual.command("council-read-policy-basis");
            PlanningRequest request = Objects.requireNonNull(actual.lastPublishedReady.get());
            if (edge == Edge.NEGATIVE_ACK) actual.rejectNextScenarioRead();
            if (edge == Edge.LOST_ACK) actual.loseReadAckOnce();
            if (edge == Edge.MALFORMED_RESULT) actual.malformedNextScenarioReadResult();
            if (edge == Edge.STALE_REJECTION) actual.rejectNextScenarioReadAsStale();
            if (edge == Edge.PENDING_NEGATIVE_ACK) actual.rejectNextScenarioReadAfter(1);
            if (edge == Edge.PENDING_MALFORMED_RESULT) actual.malformedNextScenarioReadResultAfter(1);
            var transport = actual.physicalInputs().transport();
            var port = new NativeCouncilReadPort(actual.reads, publicReads.get(), definitions.get(), transport,
                    sessions(actual), actual.root.resolve("ROOT-CONTINUITY-WINDOW.lock").toAbsolutePath(),
                    actual.archive, Clock.systemUTC(), 4, "1.20.0.2", SHA);
            // The ordinary producer already owns this real planning source and writer Session.
            // Count only the native READ and after path once that source has actually been established.
            var captured = new AtomicReference<Scene>();
            actual.writer.locked(same -> actual.collector.current(same, request.before(), request.deadline(), lease -> {
                assertEquals(request.before(), lease.frame().identity());
                int before = actual.nativeReadWrites();
                var result = port.readPrivate(request, CouncilSelection.Position.STEWARD);
                captured.set(new Scene(actual, request, basis, result, port, before, edge.expectedReads));
                return null;
            }));
            check.run(Objects.requireNonNull(captured.get()));
        }
    }
    private static Unavailable<CouncilSelection.Query> unavailable(Scene scene) {
        if (scene.result() instanceof Unavailable<CouncilSelection.Query> actual) return actual;
        throw new AssertionError("actual failed private READ must remain Unavailable");
    }
    private static CouncilTechnicalReadFailure technical(Scene scene) {
        return unavailable(scene).councilTechnicalReadFailure().orElseThrow();
    }
    private static void requireOneReadNoActions(Scene scene) {
        assertEquals(scene.writesBefore() + scene.expectedReads(), scene.actual().nativeReadWrites(), "held after verification must not issue a nested READ");
        assertEquals(scene.expectedReads(), scene.actual().scenarioReadWrites());
        assertEquals(0, scene.actual().nativeActionWrites());
    }
    private static void requireRealAfter(Scene scene) {
        var actual = technical(scene);
        assertNotSame(actual.failure().before(), actual.failure().after(), "before cannot be reused as after");
        assertEquals(scene.request().before(), actual.failure().after().binding().observed());
        assertTrue(actual.failure().after().paused());
        assertTrue(actual.failure().after().mapReady());
        assertTrue(actual.failure().after().playerAlive());
        assertTrue(actual.originals().contains(actual.failure().originalRef()));
        assertTrue(actual.originals().contains(actual.failure().preparedRef()));
        assertFalse(scene.actual().physicalInputs().transport().mailboxDiagnostics().scopeHeld());
        assertTrue(scene.actual().physicalInputs().transport().mailboxDiagnostics().poison().isEmpty());
    }

    @Test void actualNegativeReadProducerFeedsPortOriginalReplayAndRealCouncilPolicy() throws Exception {
        scene("negative", Edge.NEGATIVE_ACK, scene -> {
            var failure = technical(scene);
            assertFalse(assertInstanceOf(NativeActionPort.AckReceived.class, failure.failure().original()).nativeOk());
            requireRealAfter(scene); requireOneReadNoActions(scene);
            scene.actual().writer.locked(same -> {
                var replayed = scene.port().replayTechnicalReadFailure(failure.diagnostic(), scene.actual().archive.withSession(same));
                assertEquals(failure, replayed); return null;
            });
            requirePolicyKeepsOriginalAdvance(scene);
            requireOneReadNoActions(scene);
        });
    }

    @Test void actualLostReadAckGetsHeldAfterAndReadonlyExitWithoutReplayOrBusinessCredit() throws Exception {
        scene("lost", Edge.LOST_ACK, scene -> {
            var failure = technical(scene);
            assertInstanceOf(NativeActionPort.Unknown.class, failure.failure().original());
            requireRealAfter(scene); requireOneReadNoActions(scene);
            scene.actual().writer.locked(same -> {
                var restored = scene.port().replayTechnicalReadFailure(failure.diagnostic(), scene.actual().archive.withSession(same));
                assertEquals(failure, restored);
                assertThrows(RuntimeException.class, () -> scene.actual().collector.currentHeldOriginal(same,
                        failure.failure().request(), ignored -> null), "the completed source scope must not escape");
                return null;
            });
            requirePolicyKeepsOriginalAdvance(scene);
            requireOneReadNoActions(scene);
        });
    }

    @Test void actualSuccessfulAckWithNonObjectResultUsesTheSameTechnicalDomainAsTransport() throws Exception {
        scene("malformed-result", Edge.MALFORMED_RESULT, scene -> {
            var failure = technical(scene);
            var ack = assertInstanceOf(NativeActionPort.AckReceived.class, failure.failure().original());
            assertTrue(ack.nativeOk());
            var token = StrictJson.parse(ack.originalResultToken().orElseThrow().bytes());
            assertTrue(token.isArray());
            assertEquals(token, StrictJson.parse(ack.originalFrame().bytes()).get("result"));
            CouncilTechnicalReadFailures.requireTechnicalReadFailure(failure.failure());
            requireRealAfter(scene); requireOneReadNoActions(scene);
            scene.actual().writer.locked(same -> {
                assertEquals(failure, scene.port().replayTechnicalReadFailure(failure.diagnostic(), scene.actual().archive.withSession(same)));
                return null;
            });
            requirePolicyKeepsOriginalAdvance(scene); requireOneReadNoActions(scene);
        });
    }

    @Test void actualPendingThenRejectedOrMalformedStatusRetainsEveryOriginalWithoutRequeue() throws Exception {
        for (var edge : List.of(Edge.PENDING_NEGATIVE_ACK, Edge.PENDING_MALFORMED_RESULT)) {
            scene("pending-" + edge.name(), edge, scene -> {
                var failure = technical(scene);
                assertEquals(1, failure.priorReads().size());
                assertEquals(CouncilPrivateCodec.GATES, failure.priorReads().getFirst().request().operation().value());
                assertEquals(CouncilPrivateCodec.STATUS, failure.failure().request().operation().value());
                assertEquals(new Obj(java.util.Map.of()), failure.failure().request().arguments());
                requireRealAfter(scene); requireOneReadNoActions(scene);
                scene.actual().writer.locked(same -> {
                    assertEquals(failure, scene.port().replayTechnicalReadFailure(failure.diagnostic(), scene.actual().archive.withSession(same)));
                    return null;
                });
                requirePolicyKeepsOriginalAdvance(scene); requireOneReadNoActions(scene);
            });
        }
    }

    @Test void actualStaleRejectionRequiresSourceRefreshAndNeverGetsTechnicalCadenceCredit() throws Exception {
        scene("stale", Edge.STALE_REJECTION, scene -> {
            assertTrue(unavailable(scene).councilTechnicalReadFailure().isEmpty());
            assertTrue(scene.actual().physicalInputs().transport().mailboxDiagnostics().poison().isEmpty(),
                    "an initial negative ACK queued no mailbox operation");
            requireOneReadNoActions(scene);
        });
    }

    @Test void successfulPendingStatusCannotBeRelabelledAsTechnicalAndKeepsMailboxPoisoned() throws Exception {
        scene("pending-only", Edge.PENDING_ONLY, scene -> {
            assertTrue(unavailable(scene).councilTechnicalReadFailure().isEmpty());
            var mailbox = scene.actual().physicalInputs().transport().mailboxDiagnostics();
            assertTrue(mailbox.poison().isPresent());
            assertEquals(5, mailbox.unresolvedRequestIds().size());
            requireOneReadNoActions(scene);
        });
    }

    @Test void completedCommandResultWithBadPayloadDoesNotAcquireTechnicalDeferral() throws Exception {
        scene("bad-payload", Edge.NORMAL_RESULT, scene -> {
            assertTrue(unavailable(scene).councilTechnicalReadFailure().isEmpty());
            assertTrue(scene.actual().physicalInputs().transport().mailboxDiagnostics().poison().isPresent(),
                    "an unconsumed normal native result cannot be relabelled as a technical exit");
            requireOneReadNoActions(scene);
        });
    }

    @Test void unresolvedBusinessAndMissingObservedFailureCannotConsumeTheActualReadProof() throws Exception {
        scene("policy-negative", Edge.NEGATIVE_ACK, scene -> {
            var advance = advance(scene); var before = cadence(scene);
            for (var status : List.of(DomainStatus.UNKNOWN, DomainStatus.PENDING)) {
                var supplier = new PolicyInputs(scene, before, status, unavailable(scene));
                assertInstanceOf(OrdinaryPolicy.Wait.class, new GovernancePolicies.Council(supplier, scene.request().source().sourceRef())
                        .evaluate(scene.request(), advance));
                assertEquals(0, supplier.councilCalls, "business pending/UNKNOWN must be handled before optional technical reads");
            }
            var missing = new PolicyInputs(scene, before, DomainStatus.KNOWN_CLEAR, new Unavailable<>("no actual failed-after observation"));
            assertInstanceOf(OrdinaryPolicy.Stop.class, new GovernancePolicies.Council(missing, scene.request().source().sourceRef())
                    .evaluate(scene.request(), advance));
            requireOneReadNoActions(scene);
        });
    }

    @Test void retainedCouncilIndexRejectsChangedRoleAndCannotBeReboundToAnotherQuery() throws Exception {
        scene("changed-index", Edge.NEGATIVE_ACK, scene -> {
            var original = technical(scene);
            scene.actual().writer.locked(same -> {
                var archive = scene.actual().archive.withSession(same);
                var body = (ObjectNode) StrictJson.parse(archive.loadMaterial(original.diagnostic()).bytes());
                body.put("position_key", "councillor_chancellor");
                var altered = archive.preserveMaterial(new RawJson(StrictJson.canonical(body)));
                assertThrows(IllegalArgumentException.class, () -> scene.port().replayTechnicalReadFailure(altered, archive));
                return null;
            });
            requireOneReadNoActions(scene);
        });
    }

    @Test void actualHeldSourceRejectsAnAcceptedRawSnapshotDriftWithoutIssuingAnotherRead() throws Exception {
        scene("raw-drift", Edge.NEGATIVE_ACK, scene -> {
            var entered = new AtomicBoolean(); var afterRejected = new AtomicBoolean();
            assertThrows(Exception.class, () -> scene.actual().writer.locked(same ->
                    scene.actual().collector.withHeldReadScope(same, scene.actual().observationIdentity(), scene.request().deadline(), frame -> {
                        var initial = technical(scene).failure().request();
                        scene.actual().collector.currentHeldOriginal(same, initial, lease -> null); entered.set(true);
                        var transport = scene.actual().physicalInputs().transport();
                        var previous = transport.currentSnapshot(scene.request().deadline());
                        byte[] packet = previous.originalPacket();
                        var value = (ObjectNode) StrictJson.parse(Arrays.copyOfRange(packet, 4, packet.length));
                        value.put("snapshot_id", previous.snapshotId() + "-actual-software-drift");
                        value.put("revision", previous.nativeRevision().add(java.math.BigInteger.ONE));
                        scene.actual().enqueueSoftwareNativePacket(NativeWire.packet(StrictJson.canonical(value)));
                        try { transport.waitForSnapshot(Instant.now().plusMillis(50), scene.request().deadline()); }
                        catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IOException(interrupted); }
                        assertEquals(previous.nativeRevision().add(java.math.BigInteger.ONE),
                                transport.currentSnapshot(scene.request().deadline()).nativeRevision());
                        assertThrows(RuntimeException.class, () -> scene.actual().collector.currentHeldOriginal(same, initial, lease -> null));
                        afterRejected.set(true); return null;
                    })));
            assertTrue(entered.get()); assertTrue(afterRejected.get());
            requireOneReadNoActions(scene);
        });
    }

    private static CadenceModels.State cadence(Scene scene) {
        var identity = scene.request().before().frame();
        var previous = new CadenceModels.Marker(identity.identity().dateRaw().subtract(java.math.BigInteger.ONE), identity.identity().nativeRevision());
        return CadenceModels.State.empty(identity.episodeRunId()).with(CadenceModels.Domain.COUNCIL,
                new CadenceModels.Row(2, Optional.empty(), Optional.of(previous), Optional.of(previous), Optional.of("software-retained-catalogue"), Optional.empty()));
    }
    /** Unsubmitted selected intent for policy retention; it is never offered to an action coordinator. */
    private static OrdinaryPolicy.Draft advance(Scene scene) {
        var basis = scene.basis();
        var command = new ActionCommand("unsubmitted-selected-life-advance", basis.origin(), basis.source(), basis.sessionId(),
                new OperationKey("life-advance"), new Obj(java.util.Map.of()), basis.expectation(), basis.claims(), basis.deadline());
        return new OrdinaryPolicy.Draft("selected-software-advance", "ordinary", "selected advance input", OrdinaryPolicy.Kind.ORDINARY,
                Optional.of(command), OrdinaryPolicy.Purpose.DATE_ADVANCE, Optional.empty(), new Obj(java.util.Map.of()));
    }
    private static void requirePolicyKeepsOriginalAdvance(Scene scene) {
        var before = cadence(scene); var previous = advance(scene);
        var supplier = new PolicyInputs(scene, before, DomainStatus.KNOWN_CLEAR, unavailable(scene));
        var decision = new GovernancePolicies.Council(supplier, scene.request().source().sourceRef()).evaluate(scene.request(), previous);
        var retained = assertInstanceOf(OrdinaryPolicy.Replace.class, decision).draft();
        assertSame(previous.command().orElseThrow(), retained.command().orElseThrow());
        assertEquals(new Bool(false), retained.detail().get("council_observation_consumed"));
        var plan = GovernanceCadencePublication.fromDetail(retained.detail()).orElseThrow();
        assertEquals(plan, GovernanceCadencePublication.decode(GovernanceCadencePublication.encode(plan)));
        assertTrue(plan.completeNoActionDomains().isEmpty());
        var row = GovernanceCadencePublication.reduce(plan).row(CadenceModels.Domain.COUNCIL);
        assertEquals(2, row.consecutiveNoAction());
        assertEquals(before.row(CadenceModels.Domain.COUNCIL).lastActualActionFrame(), row.lastActualActionFrame());
        assertEquals(before.row(CadenceModels.Domain.COUNCIL).nativeCatalogue(), row.nativeCatalogue());
        assertEquals(technical(scene).diagnostic().path(), row.technicalDefer().orElseThrow().evidencePath());
        assertTrue(row.nextDueDateRaw().orElseThrow().compareTo(scene.request().before().frame().identity().dateRaw()) > 0);
        assertEquals(1, supplier.councilCalls);
        // Real domain-body publication/private transcript replay is covered separately; this test grants no publication authority.
    }
    private static final class PolicyInputs implements GovernanceObservationSupplier {
        private final Scene scene; private final CadenceModels.State cadence; private final DomainStatus status;
        private final Read<CouncilSelection.Query> result; int councilCalls;
        private PolicyInputs(Scene scene, CadenceModels.State cadence, DomainStatus status, Read<CouncilSelection.Query> result) {
            this.scene = scene; this.cadence = cadence; this.status = status; this.result = result;
        }
        @Override public Read<Durable> durable(PlanningRequest request) {
            var pending = status == DomainStatus.PENDING ? Optional.of(new Obj(java.util.Map.of("status", new Text("controlled-original-pending")))) : Optional.<Obj>empty();
            var domain = new DomainState(status, Optional.empty(), pending, new Obj(java.util.Map.of()));
            return new Known<>(new Durable(request.before(), request.sessionId(), Optional.of(cadence), Optional.empty(),
                    Optional.of(domain), Optional.empty()), technical(scene).originals());
        }
        @Override public Read<CouncilSelection.Query> council(PlanningRequest request, CouncilSelection.Position position) {
            assertEquals(scene.request(), request); assertEquals(CouncilSelection.Position.STEWARD, position);
            councilCalls++; return result;
        }
        private static <T> Read<T> unused() { throw new AssertionError("this original Council failure route must not collect another native/domain input"); }
        @Override public Read<Life> lifestyle(PlanningRequest r, String focus, boolean opening) { return unused(); }
        @Override public Read<OpeningComparison> openingComparison(PlanningRequest r) { return unused(); }
        @Override public Read<CouncilSelection.Query> coreCouncil(PlanningRequest r) { return unused(); }
        @Override public Read<CouncilRoot> councilRoot(PlanningRequest r) { return unused(); }
        @Override public Read<Crown> crown(PlanningRequest r) { return unused(); }
        @Override public Read<org.xar.ck3.control.wave3.governance.crownretry.CrownRetryCodec.MatchRequest> crownRetry(PlanningRequest r, String key) { return unused(); }
        @Override public Read<org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldownCodec.ClockRequest> crownCooldown(PlanningRequest r) { return unused(); }
    }
}
