package org.xar.ck3.control.nativebridge.capabilities.governance;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.governance.*;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.planning.optionalcadence.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Controlled packets exercise the real READ/port/policy/transcript/writer chain. No native or Game qualification. */
final class CouncilCadenceTechnicalReadReplayIntegrationTest {
    @TempDir Path temporary;
    private static final String SHA = "ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d";
    private static final byte[] SEED = StrictJson.canonical(StrictJson.object().put("schema", "controlled-software-cadence-seed-v1"));
    private enum Edge { NEGATIVE_ACK, LOST_ACK, MALFORMED_RESULT, STATUS_NEGATIVE_ACK, STATUS_MALFORMED_RESULT }
    private record Produced(OrdinaryPolicy.Draft retained, int readsBefore, int readsAfter) { }

    private static NativeCouncilReadPort.SessionAccess sessions(ActionWriterIntegrationFixture actual) {
        return new NativeCouncilReadPort.SessionAccess() {
            @Override public <T> T withSession(PlanningRequest request, NativeCouncilReadPort.SessionWork<T> work)
                    throws IOException, InterruptedException {
                var borrowed = actual.writer.activeSession();
                if (borrowed.isEmpty()) throw new IOException("test requires the original held writer Session");
                actual.writer.requireSession(borrowed.orElseThrow());
                return work.run(borrowed.orElseThrow());
            }
        };
    }
    private static DomainBodies.Available available(ContinuityStorePort.Session same) throws IOException {
        var read = same.readDomain(DomainBodies.Slot.OPTIONAL_CADENCE);
        if (read instanceof DomainBodies.Available actual) return actual;
        throw new IOException("controlled original cadence body unavailable");
    }
    private static CadenceModels.State initial(PlanningRequest request) {
        var frame = request.before().frame();
        var previous = new CadenceModels.Marker(frame.identity().dateRaw().subtract(java.math.BigInteger.ONE), frame.identity().nativeRevision());
        return CadenceModels.State.empty(frame.episodeRunId()).with(CadenceModels.Domain.COUNCIL,
                new CadenceModels.Row(2, Optional.empty(), Optional.of(previous), Optional.of(previous), Optional.of("retained-software-catalogue"), Optional.empty()));
    }
    /** Only test setup is seeded. Every later change uses the actual production cadence verifier. */
    private static DomainBodies.Verifier verifier(AtomicReference<GovernanceCadencePublication> publisher,
            AtomicReference<CadenceModels.State> baseline) {
        return new DomainBodies.Verifier() {
            @Override public String verify(ContinuityState head, Optional<DomainBodies.BodyRef> previous,
                    DomainBodies.ImportRequest request, byte[] body) throws IOException {
                throw new IOException("actual same-head verification required");
            }
            @Override public String verify(WriterContracts.Head head, Optional<DomainBodies.BodyRef> previous,
                    DomainBodies.ImportRequest request, byte[] body) throws IOException {
                if (java.util.Arrays.equals(request.producerInput(), SEED)) {
                    assertTrue(previous.isEmpty()); assertEquals(0, head.state().sequence());
                    var expected = Objects.requireNonNull(baseline.get());
                    var state = CadenceJson.readState(body, expected.episodeRunId()); assertEquals(expected, state);
                    assertEquals(2, state.row(CadenceModels.Domain.COUNCIL).consecutiveNoAction());
                    assertTrue(state.row(CadenceModels.Domain.COUNCIL).technicalDefer().isEmpty());
                    return ActionCodec.sha256(body);
                }
                return Objects.requireNonNull(publisher.get()).verify(head, previous, request, body);
            }
        };
    }
    private void actualFailurePublishes(Edge edge) throws Exception {
        var definitions = new AtomicReference<PrivateCouncilReads>();
        var publicReads = new AtomicReference<GovernanceNativeReads>();
        var publisher = new AtomicReference<GovernanceCadencePublication>();
        var producer = new AtomicReference<ExactRef>();
        var baseline = new AtomicReference<CadenceModels.State>();
        var scenario = new ActionWriterIntegrationFixture.SoftwareReadScenario(SHA, "council-cadence-replay-software", source -> {
            var privateDefinitions = new PrivateCouncilReads(source); definitions.set(privateDefinitions);
            publicReads.set(new GovernanceNativeReads(source, "1.20.0.2", SHA)); return privateDefinitions.registeredContracts();
        }, prepared -> edge == Edge.STATUS_NEGATIVE_ACK || edge == Edge.STATUS_MALFORMED_RESULT
                ? new RawJson(StrictJson.canonical(StrictJson.object()
                        .put("private_council_transport", true).put("advertised", false).put("step", prepared.step()).put("status", "pending")))
                : new RawJson(new byte[] {'{', '}'}), Optional.of("1.20.0.2"), Set.of());
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve(edge.name()), false, scenario, List.of(), List.of(), source -> {
            producer.set(source); return List.of(new DomainBodies.Registration(DomainBodies.Slot.OPTIONAL_CADENCE,
                    CadenceModels.SCHEMA, 1_048_576, List.of(source), verifier(publisher, baseline)));
        })) {
            ActionCommand basis = actual.command("council-cadence-unsubmitted-basis");
            PlanningRequest request = Objects.requireNonNull(actual.lastPublishedReady.get());
            var before = initial(request); baseline.set(before);
            var replay = new GovernanceCadenceReplay(() -> {
                try { return actual.writer.activeSession().orElse(null); }
                catch (IOException failure) { throw new java.io.UncheckedIOException(failure); }
            }, actual.writer::requireSession,
                    (same, ref) -> actual.archive.readArtifact(same, ref, 1_048_576));
            var publication = new GovernanceCadencePublication(actual.root.resolve("ROOT-CONTINUITY-WINDOW.lock").toAbsolutePath(),
                    actual.writer::requireSession, List.of(producer.get()), replay,
                    (id, bytes) -> actual.archive.withSession(actual.writer.activeSession().orElseThrow()).preserveMaterial(new RawJson(bytes)));
            publisher.set(publication);
            switch (edge) {
                case NEGATIVE_ACK -> actual.rejectNextScenarioRead();
                case LOST_ACK -> actual.loseReadAckOnce();
                case MALFORMED_RESULT -> actual.malformedNextScenarioReadResult();
                case STATUS_NEGATIVE_ACK -> actual.rejectNextScenarioReadAfter(1);
                case STATUS_MALFORMED_RESULT -> actual.malformedNextScenarioReadResultAfter(1);
            }
            // A nonempty controlled fixture baseline is explicit; this does not test fresh-Game initialization.
            actual.writer.locked(same -> {
                var ref = actual.archive.withSession(same).preserveMaterial(new RawJson(CadenceJson.writeState(before)));
                var input = new DomainBodies.ImportRequest(DomainBodies.Slot.OPTIONAL_CADENCE, CadenceModels.SCHEMA, ref,
                        SEED, List.of(producer.get()), "controlled-council-cadence-seed");
                same.commitImport(same.previewImport(input)); assertEquals(before, CadenceJson.readState(available(same).canonicalBody(), before.episodeRunId()));
                return null;
            });
            var port = new NativeCouncilReadPort(actual.reads, publicReads.get(), definitions.get(), actual.physicalInputs().transport(),
                    sessions(actual), actual.root.resolve("ROOT-CONTINUITY-WINDOW.lock").toAbsolutePath(), actual.archive, Clock.systemUTC(), 4, "1.20.0.2", SHA);
            var previous = advance(basis);
            var inputs = new Inputs(actual, port, before, producer.get());
            var policy = replay.record(new GovernancePolicies.Council(replay.observe(inputs), producer.get()));
            actual.writer.locked(same -> {
                var collected = new AtomicReference<Produced>();
                actual.collector.current(same, request.before(), request.deadline(), lease -> {
                    int reads = actual.nativeReadWrites();
                    var decision = assertInstanceOf(OrdinaryPolicy.Replace.class, policy.evaluate(request, previous));
                    collected.set(new Produced(decision.draft(), reads, actual.nativeReadWrites())); return null;
                });
                var produced = Objects.requireNonNull(collected.get());
                var retained = produced.retained(); assertSame(previous.command().orElseThrow(), retained.command().orElseThrow());
                var technical = inputs.actualFailure.orElseThrow();
                technical.requireCurrent(request, CouncilSelection.Position.STEWARD);
                assertThrows(IllegalArgumentException.class, () -> technical.requireCurrent(request, CouncilSelection.Position.CHANCELLOR));
                requireChangedFailureDeadlineRejected(technical, request);
                if (edge == Edge.NEGATIVE_ACK || edge == Edge.STATUS_NEGATIVE_ACK)
                    assertFalse(assertInstanceOf(NativeActionPort.AckReceived.class, technical.failure().original()).nativeOk());
                else if (edge == Edge.LOST_ACK) assertInstanceOf(NativeActionPort.Unknown.class, technical.failure().original());
                else {
                    var ack = assertInstanceOf(NativeActionPort.AckReceived.class, technical.failure().original()); assertTrue(ack.nativeOk());
                    assertTrue(StrictJson.parse(ack.originalFrame().bytes()).get("result").isArray());
                }
                assertNotSame(technical.failure().before(), technical.failure().after());
                var plan = GovernanceCadencePublication.fromDetail(retained.detail()).orElseThrow();
                assertEquals(new Bool(false), retained.detail().get("council_observation_consumed"));
                var defer = object(retained.detail().get("council_technical_defer"), "actual technical Council intent");
                assertEquals(new Bool(false), defer.get("business_submission")); assertEquals(new Bool(false), defer.get("action_credit"));
                assertEquals(new Bool(false), defer.get("no_action_counter_incremented"));
                assertEquals(plan, GovernanceCadencePublication.decode(GovernanceCadencePublication.encode(plan)));
                assertTrue(plan.completeNoActionDomains().isEmpty()); assertEquals(Optional.of(technical.diagnostic()), plan.councilTechnicalFailure());
                var evidence = java.util.stream.Stream.concat(java.util.stream.Stream.of(producer.get()), technical.originals().stream()).distinct().toList();
                var original = available(same); var oldHead = same.head();
                int readsAfterCollection = actual.nativeReadWrites();
                boolean statusFailure = edge == Edge.STATUS_NEGATIVE_ACK || edge == Edge.STATUS_MALFORMED_RESULT;
                assertEquals(produced.readsBefore() + (statusFailure ? 2 : 1), readsAfterCollection);
                assertEquals(statusFailure ? 1 : 0, technical.priorReads().size());
                assertEquals(produced.readsAfter(), readsAfterCollection);
                var material = replay.replay(oldHead, original.reference(), plan, evidence);
                assertEquals(plan, material.actualReplayedPlan()); assertEquals(evidence, material.originalReadEvidence());
                assertEquals(readsAfterCollection, actual.nativeReadWrites(), "private material replay must not dispatch another READ");
                var changed = assertInstanceOf(GovernanceCadencePublication.Changed.class, publication.publish(same, plan, evidence));
                assertEquals(changed.body(), available(same).reference().payload());
                var after = CadenceJson.readState(available(same).canonicalBody(), before.episodeRunId());
                assertEquals(GovernanceCadencePublication.reduce(plan), after);
                var row = after.row(CadenceModels.Domain.COUNCIL); var prior = before.row(CadenceModels.Domain.COUNCIL);
                assertEquals(prior.consecutiveNoAction(), row.consecutiveNoAction());
                assertEquals(prior.lastActualActionFrame(), row.lastActualActionFrame()); assertEquals(prior.nativeCatalogue(), row.nativeCatalogue());
                assertEquals(technical.diagnostic().path(), row.technicalDefer().orElseThrow().evidencePath());
                assertEquals(readsAfterCollection, actual.nativeReadWrites()); assertEquals(1, inputs.calls);
                assertEquals(0, actual.nativeActionWrites());
                assertFalse(actual.physicalInputs().transport().mailboxDiagnostics().scopeHeld());
                assertTrue(actual.physicalInputs().transport().mailboxDiagnostics().poison().isEmpty());
                // The recorded original still cannot be rebound after the writer body changed.
                assertThrows(IllegalArgumentException.class, () -> publication.publish(same, plan, evidence));
                return null;
            });
        }
    }
    @Test void negativeAckUsesActualCouncilProducerAndSameWriterTechnicalPublication() throws Exception { actualFailurePublishes(Edge.NEGATIVE_ACK); }
    @Test void lostAckUsesActualCouncilProducerAndSameWriterTechnicalPublicationWithoutAnotherNativeWrite() throws Exception { actualFailurePublishes(Edge.LOST_ACK); }
    @Test void malformedTrueResultUsesActualCouncilProducerAndSameWriterTechnicalPublication() throws Exception { actualFailurePublishes(Edge.MALFORMED_RESULT); }
    @Test void pendingThenRejectedStatusReplaysTheEntireActualChainIntoTheSameWriter() throws Exception { actualFailurePublishes(Edge.STATUS_NEGATIVE_ACK); }
    @Test void pendingThenMalformedStatusReplaysTheEntireActualChainIntoTheSameWriter() throws Exception { actualFailurePublishes(Edge.STATUS_MALFORMED_RESULT); }

    private static void requireChangedFailureDeadlineRejected(CouncilTechnicalReadFailure actual, PlanningRequest request) {
        var failed = actual.failure(); var old = failed.request();
        var changedRequest = new PlanningReadRequest(old.before(), old.source(), old.sessionId(), old.operation(), old.arguments(), old.deadline().plusMillis(1));
        var changed = new PlanningReadFailure(changedRequest, failed.contractId(), failed.requestId(), failed.before(), failed.after(), failed.prepared(),
                failed.original(), failed.originalRef(), failed.preparedRef(), failed.headSequence(), failed.headDigest());
        var rebound = new CouncilTechnicalReadFailure(actual.originalRequest(), changed, actual.priorReads(), actual.originals(), actual.diagnostic());
        assertThrows(IllegalArgumentException.class, () -> rebound.requireCurrent(request, CouncilSelection.Position.STEWARD));
    }

    private static OrdinaryPolicy.Draft advance(ActionCommand basis) {
        var command = new ActionCommand("unsubmitted-council-cadence-life-advance", basis.origin(), basis.source(), basis.sessionId(),
                new OperationKey("life-advance"), new Obj(java.util.Map.of()), basis.expectation(), basis.claims(), basis.deadline());
        return new OrdinaryPolicy.Draft("controlled-selected-advance", "ordinary", "controlled original advance", OrdinaryPolicy.Kind.ORDINARY,
                Optional.of(command), OrdinaryPolicy.Purpose.DATE_ADVANCE, Optional.empty(), new Obj(java.util.Map.of()));
    }
    private static final class Inputs implements GovernanceObservationSupplier {
        private final ActionWriterIntegrationFixture actual; private final NativeCouncilReadPort port;
        private final CadenceModels.State before; private final ExactRef producer;
        int calls; Optional<CouncilTechnicalReadFailure> actualFailure = Optional.empty();
        private Inputs(ActionWriterIntegrationFixture actual, NativeCouncilReadPort port, CadenceModels.State before, ExactRef producer) {
            this.actual = actual; this.port = port; this.before = before; this.producer = producer;
        }
        @Override public Read<Durable> durable(PlanningRequest request) {
            try {
                var same = actual.writer.activeSession().orElseThrow();
                assertEquals(before, CadenceJson.readState(available(same).canonicalBody(), before.episodeRunId()));
            } catch (IOException failure) { throw new java.io.UncheckedIOException(failure); }
            var domain = new DomainState(DomainStatus.KNOWN_CLEAR, Optional.empty(), Optional.empty(), new Obj(java.util.Map.of()));
            return new Known<>(new Durable(request.before(), request.sessionId(), Optional.of(before), Optional.empty(), Optional.of(domain), Optional.empty()), List.of(producer));
        }
        @Override public Read<CouncilSelection.Query> council(PlanningRequest request, CouncilSelection.Position position) {
            assertEquals(CouncilSelection.Position.STEWARD, position); calls++;
            var read = port.readPrivate(request, position);
            if (!(read instanceof Unavailable<CouncilSelection.Query> unavailable)) throw new AssertionError("failed actual Council READ must remain Unavailable");
            actualFailure = unavailable.councilTechnicalReadFailure(); assertTrue(actualFailure.isPresent()); return read;
        }
        private static <T> Read<T> unused() { throw new AssertionError("actual technical path must not collect another domain input"); }
        @Override public Read<Life> lifestyle(PlanningRequest request, String focus, boolean opening) { return unused(); }
        @Override public Read<OpeningComparison> openingComparison(PlanningRequest request) { return unused(); }
        @Override public Read<CouncilSelection.Query> coreCouncil(PlanningRequest request) { return unused(); }
        @Override public Read<CouncilRoot> councilRoot(PlanningRequest request) { return unused(); }
        @Override public Read<Crown> crown(PlanningRequest request) { return unused(); }
        @Override public Read<org.xar.ck3.control.wave3.governance.crownretry.CrownRetryCodec.MatchRequest> crownRetry(PlanningRequest request, String law) { return unused(); }
        @Override public Read<org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldownCodec.ClockRequest> crownCooldown(PlanningRequest request) { return unused(); }
    }
}
