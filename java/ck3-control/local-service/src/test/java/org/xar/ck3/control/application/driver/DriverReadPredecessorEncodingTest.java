package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.capabilities.CapabilitySessionPresentation;
import org.xar.ck3.control.application.capabilities.DynamicCapabilities;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.planning.military.MilitaryReadObservation;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;

/** Owned software writer/read originals. This supplies no live Native or Root qualification. */
final class DriverReadPredecessorEncodingTest {
    private static final String STEP = "preview-move-army-0-to-4";
    private static final String CAP = "game.command.preview-move-army-N-to-N";
    @TempDir Path directory;

    private static final class MutableActor extends BigInteger {
        private static final long serialVersionUID = 1L;
        private final String original;
        private boolean armed;
        private int serializations;
        MutableActor(BigInteger value) { super(value.toString()); original = value.toString(); }
        @Override public String toString() {
            if (!armed || ++serializations == 1) return original;
            return original.equals("1") ? "2" : "1";
        }
    }

    private final class Run implements AutoCloseable {
        final ActionWriterIntegrationFixture fixture;
        final SessionPorts.Ready ready;
        final ReadContract<MilitaryReadObservation> contract;
        final DriverStateAssembler authority;
        final DriverSnapshotFacts.Known before;
        final DriverReadHistoryPublisher publisher;
        final MutableActor actor;
        Run(String name, boolean mutable) throws Exception {
            var installed = new AtomicReference<ReadContract<MilitaryReadObservation>>();
            var scenario = new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64), "read-predecessor-software", source -> {
                java.util.function.Function<PlanningReadReceipt, MilitaryReadObservation> decoder = DriverReadPredecessorEncodingTest::decode;
                var actual = new ReadContract<MilitaryReadObservation>("physical-original-route-preview", new OperationKey(STEP), Optional.of(CAP), CAP,
                        ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP,
                        ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, source,
                        (request, id) -> new NativeRequest(STEP, Optional.of(CAP), new RawJson(new byte[] {'{', '}'})), decoder, decoder,
                        (original, value, current, semantic) -> StrictJson.require(current.before().equals(original.request().before())
                                && current.source().equals(original.request().source()) && current.sessionId().equals(original.request().sessionId())
                                && current.arguments().equals(original.request().arguments()), "software route native operands changed"));
                installed.set(actual); return List.of(actual);
            }, request -> new RawJson(DriverJson.encode(new Obj(Map.of("step", new Text(STEP), "accepted", new Bool(true), "status", new Text("available"),
                    "route_preview", new Obj(Map.of("army_id", new IntegerValue(BigInteger.ZERO), "origin_province_id", new IntegerValue(BigInteger.ONE),
                            "target_province_id", new IntegerValue(BigInteger.valueOf(4)), "status", new Text("available"),
                            "route_province_ids", new Arr(List.of(new IntegerValue(BigInteger.ONE), new IntegerValue(BigInteger.valueOf(4)))))))))));
            fixture = new ActionWriterIntegrationFixture(directory.resolve(name), false, scenario);
            try {
                ready = fixture.ready(); contract = installed.get();
                fixture.writer.locked(same -> {
                    fixture.collector.current(same, ready.request().before(), Instant.now().plusSeconds(20), lease -> {
                        var configuration = new DynamicCapabilities.Configuration(Optional.empty(), Optional.empty(), 3, 3, false, false);
                        var session = new CapabilitySessionPresentation(false, Optional.empty(), Optional.of(CapabilitySessionPresentation.RestoreKind.NEW_EPISODE),
                                CapabilitySessionPresentation.BindingState.ACTIVE_NEW, Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty());
                        var policy = fixture.archive.preserveMaterial(new RawJson("{\"actual_software_start_policy\":true}".getBytes(StandardCharsets.UTF_8)));
                        var produced = DriverCapabilityStateProducer.initializeNewEpisode(lease.frame(), lease.driver(), configuration, session, policy, fixture.archive.withSession(same));
                        fixture.driverAuthority().publishCapabilityInputs(same, lease.driver().stamp(), produced.expectedAuxiliarySha256(), produced);
                        return null;
                    }); return null;
                });
                var original = fixture.writer.locked(same -> fixture.driverAuthority().withFrozenFacts(same,
                        frozen -> (DriverSnapshotFacts.Known) frozen.state()));
                actor = mutable ? new MutableActor(original.driver().session().actorId()) : null;
                var driver = original.driver();
                if (actor != null) {
                    var session = driver.session();
                    driver = new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session(session.pipeName(), session.bridgePid(), actor, session.episodeRunId()),
                            driver.commandHistory(), driver.lastCheckpoint(), driver.rollbackWarFailure(), driver.managedRestoreTransaction(),
                            driver.successionExpectation(), driver.successionLifecycle(), driver.campaignGoal(), driver.rollbackWarFailures());
                }
                before = new DriverSnapshotFacts.Known(driver, original.stamp(), original.originalHistoryBasis(), original.actionRows(),
                        original.auxiliary(), original.loop(), original.observation());
                authority = new DriverStateAssembler(new ActionSnapshotReader(fixture.journal), new DriverFactsRepository(before),
                        frame -> { throw new AssertionError("publication must use its actual retained observation"); });
                authority.bindHistoryArchive(fixture.archive, fixture.journal::borrowedWriterSession);
                publisher = new DriverReadHistoryPublisher(authority, fixture.archive, fixture.reads.catalog(), List.of(contract.sourceRef()));
                fixture.bindAdditionalTransitionAuthority(WriterContracts.DRIVER_READ_HISTORY_KIND, publisher);
            } catch (Exception | Error failure) {
                try { fixture.close(); } catch (Exception closing) { failure.addSuppressed(closing); }
                throw failure;
            }
        }
        PlanningReadResult.Known<MilitaryReadObservation> queue(ContinuityStorePort.Session same) throws IOException {
            var retained = new AtomicReference<PlanningReadResult.Known<MilitaryReadObservation>>();
            fixture.collector.current(same, ready.request().before(), Instant.now().plusSeconds(20), lease -> {
                var request = new PlanningReadRequest(lease.frame().identity(), lease.frame().source(), lease.frame().sessionId(),
                        contract.operation(), new Obj(Map.of()), Instant.now().plusSeconds(20));
                var result = fixture.reads.read(same, contract, request);
                if (!(result instanceof PlanningReadResult.Known<MilitaryReadObservation> known)) throw new AssertionError(result);
                publisher.enqueue(same, contract, known); retained.set(known); return null;
            });
            assertTrue(publisher.hasPending(same)); return retained.get();
        }
        @Override public void close() throws IOException { fixture.close(); }
    }

    @Test void actualReadCommitsOnceWithCompleteDriverAndOriginalReceipt() throws Exception {
        try (var run = new Run("normal", false)) {
            run.fixture.writer.locked(same -> {
                var original = run.queue(same);
                int reads = run.fixture.nativeReadWrites(), actions = run.fixture.nativeActionWrites();
                var committed = run.publisher.flushActualReads(same).orElseThrow();
                assertEquals(0, committed.predecessor().state().sequence());
                assertEquals(1, committed.actual().head().sequence());
                assertFalse(run.publisher.hasPending(same)); assertTrue(run.publisher.flushActualReads(same).isEmpty());
                run.authority.withFrozenFacts(same, frozen -> {
                    var current = assertInstanceOf(DriverSnapshotFacts.Known.class, frozen.state());
                    assertEquals(run.before.stamp().driverVersion() + 1, current.stamp().driverVersion());
                    assertEquals(run.before.driver().commandHistory().size() + 1, current.driver().commandHistory().size());
                    var row = org.xar.ck3.control.application.history.DriverReadHistoryRowProducer.decode(current.driver().commandHistory().getLast().originalRow().json());
                    assertEquals(original.originalReceipt(), row.provenance().originalReceipt());
                    assertEquals(original.receipt(), run.fixture.archive.withSession(same).loadRead(original.originalReceipt()));
                    return null;
                });
                assertEquals(reads, run.fixture.nativeReadWrites()); assertEquals(actions, run.fixture.nativeActionWrites());
                return null;
            });
        }
    }

    @Test void mutableActorStillRejectsBeforeCanonicalPublication() throws Exception {
        try (var run = new Run("mutable", true)) {
            run.fixture.writer.locked(same -> {
                run.queue(same); var head = same.head();
                int reads = run.fixture.nativeReadWrites(), actions = run.fixture.nativeActionWrites();
                run.actor.armed = true;
                var failure = assertThrows(IllegalArgumentException.class, () -> run.publisher.flushActualReads(same));
                assertEquals("read-history Driver prefix/version changed", failure.getMessage());
                assertEquals(2, run.actor.serializations);
                assertEquals(head.digest(), same.head().digest()); assertEquals(head.state().sequence(), same.head().state().sequence());
                assertTrue(run.publisher.hasPending(same));
                assertEquals(reads, run.fixture.nativeReadWrites()); assertEquals(actions, run.fixture.nativeActionWrites());
                return null;
            });
        }
    }

    private static MilitaryReadObservation decode(PlanningReadReceipt receipt) {
        Obj raw = DriverJson.object(receipt.original().originalResultToken().orElseThrow().bytes(), DriverJson.MAX_NATIVE_BYTES);
        var frame = receipt.request().before().frame();
        Obj result = raw.with("queried_snapshot_id", new Text(frame.snapshotId())).with("queried_revision", new IntegerValue(frame.revision()))
                .with("queried_native_revision", new IntegerValue(frame.identity().nativeRevision()))
                .with("queried_connection_generation", new IntegerValue(receipt.before().binding().connectionGeneration()))
                .with("queried_episode_run_id", new Text(frame.episodeRunId()));
        return new MilitaryReadObservation(MilitaryReadObservation.Kind.ROUTE_PREVIEW, result);
    }
}
