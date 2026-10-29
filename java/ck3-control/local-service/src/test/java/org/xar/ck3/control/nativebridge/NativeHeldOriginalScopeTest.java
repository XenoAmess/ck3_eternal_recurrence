package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Map;
import java.util.List;
import java.util.Set;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.effects.RootPlanningReadGuard;
import org.xar.ck3.control.application.readiness.*;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.GameLifecycle;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual shared writer/transport/Driver/source/Root guard producer; controlled physical edges grant no Game qualification. */
final class NativeHeldOriginalScopeTest {
    @TempDir Path temporary;

    private static final class Probe {
        final NativeReadinessCollector collector;
        final AtomicBoolean currentSource = new AtomicBoolean(true);
        final AtomicInteger sourceChecks = new AtomicInteger(), ordinaryCapabilities = new AtomicInteger();
        Probe(ActionWriterIntegrationFixture actual, Clock clock) {
            var physical = actual.physicalInputs();
            collector = new NativeReadinessCollector(actual.observationIdentity(), actual.writer, physical.transport(),
                    physical.driverAssembler(), physical.observationAssembler(),
                    (game, deadline) -> new GameLifecycle.Running(game, physical.source().sourceRef()),
                    (same, role, bytes) -> actual.archive.preserveArtifact(same, bytes, role.maximumBytes()),
                    new NativeSemanticEvidenceVerifier((same, ref, maximum) -> actual.archive.readArtifact(same, ref, maximum)),
                    (same, identity, frame, known, received, process, deadline) -> {
                        actual.writer.requireSession(same); assertEquals(actual.observationIdentity(), identity);
                        assertEquals(physical.source(), frame.source()); assertEquals(identity.game(), process.measured());
                        var pin = same.capturePin(physical.source().sourceRef(), 65_536); same.verifyPin(pin);
                        var proof = actual.archive.preserveArtifact(same, DriverJson.encode(new Obj(Map.of("scope", new OpportunityJson.Text("controlled-test-source")))), 65_536);
                        return new NativeReadinessCollector.SourceQualification(proof, borrowed -> {
                            actual.writer.requireSession(borrowed); assertSame(same, borrowed); borrowed.verifyPin(pin);
                            sourceChecks.incrementAndGet(); if (!currentSource.get()) throw new IOException("actual source witness changed");
                        });
                    }, (same, frame, known, received, deadline) -> {
                        ordinaryCapabilities.incrementAndGet(); throw new AssertionError("held reads cannot collect ordinary executable capabilities");
                    }, (same, frame, known, received, deadline) -> { throw new AssertionError("held reads cannot execute planning inputs"); },
                    new NativeReadiness.Policy(false, false, Optional.of(BigInteger.valueOf(73)), Duration.ZERO, false),
                    Duration.ofSeconds(30), clock);
            collector.bindObservationSession(actual.writer::requireSession);
            collector.bindActiveObservationSession(actual.writer::activeSession);
            collector.bindReadyPublication((same, request, frame, known, source) -> { throw new AssertionError("held original cannot publish M7/Ready"); });
        }
    }

    @Test void actualReceivedSnapshotAndFrozenDriverIssueHeldOnlyRootGuardWithoutAnotherPacketOrQuery() throws Exception {
        var selected = new AtomicReference<ReadContract<RawJson>>();
        var scenario = new ActionWriterIntegrationFixture.SoftwareReadScenario("3".repeat(64), "held-original-read", source -> {
            var operation = new OperationKey("query-held-original"); String capability = "game.query.held-original";
            var contract = new ReadContract<RawJson>("held-original/v1", operation, Optional.of(capability), "held-original",
                    ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP,
                    ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, source,
                    (request, requestId) -> new NativeRequest(operation.value(), capability, new RawJson("{}".getBytes(StandardCharsets.UTF_8))),
                    receipt -> receipt.original().originalResultToken().orElseThrow(), receipt -> receipt.original().originalResultToken().orElseThrow());
            selected.set(contract); return List.of(contract);
        }, request -> new RawJson("{}".getBytes(StandardCharsets.UTF_8)), Optional.empty(), Set.of("game.query.held-original"));
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("held-original"), false, scenario)) {
            var ready = actual.ready(); var probe = new Probe(actual, Clock.systemUTC());
            var contract = selected.get(); assertTrue(contract.hasPureReplay());
            int packets = actual.nativePacketReads(), queries = actual.nativeReadWrites(), planning = actual.nestedPlanningReads.get();
            var retainedReady = actual.lastPublishedReady.get();
            actual.writer.locked(same -> {
                String head = same.head().digest(); var driver = actual.driverAuthority().withFrozenFacts(same, frozen -> frozen.state());
                var guard = new RootPlanningReadGuard(probe.collector, () -> {
                    try { return actual.writer.borrowedSession(); }
                    catch (IOException failure) { throw new UncheckedIOException(failure); }
                }, actual.archive,
                        actual.observationSource(), Clock.systemUTC(), "held-original-regression", actual.physicalInputs().originals(), actual.actualReadCatalog());
                probe.collector.withHeldReadScope(same, actual.observationIdentity(), Instant.now().plusSeconds(20), frame -> {
                    assertEquals(ready.request().before(), frame.identity()); probe.collector.requireHeldFrame(same, frame);
                    var request = new PlanningReadRequest(frame.identity(), frame.source(), frame.sessionId(), contract.operation(), new Obj(Map.of()), Instant.now().plusSeconds(15));
                    ReadinessAuthority application = probe.collector;
                    application.currentHeldOriginal(same, request, lease -> {
                        assertSame(frame, lease.frame()); assertEquals(frame.identity(), lease.semantic().frame());
                        assertTrue(lease.bridgeCapabilities().contains(contract.requiredCapability().orElseThrow()));
                        return null;
                    });
                    var originalGuard = guard.verifyOriginalCurrent(same.head(), request, contract);
                    assertTrue(originalGuard.paused() && originalGuard.mapReady() && originalGuard.playerAlive());
                    assertEquals(frame.fullBindingSha256(), originalGuard.originalBindingSha256());
                    RootGuardEvidence.requireHistory(originalGuard.binding(), actual.archive.withSession(same), same);
                    assertEquals(frame, RootGuardEvidence.loadFrame(originalGuard.binding(), actual.archive.withSession(same), actual.frameLoader()));
                    assertThrows(IllegalArgumentException.class, () -> probe.collector.current(same, frame.identity(), request.deadline(), lease -> null));
                    assertThrows(IllegalArgumentException.class, () -> probe.collector.withOwnedPlanning(same, actual.observationIdentity(), request.deadline(), (plan, lease) -> null));
                    assertEquals(driver, actual.driverAuthority().withFrozenFacts(same, frozen -> frozen.state()));
                    assertEquals(head, same.head().digest()); return null;
                });
                var original = ready.request();
                var request = new PlanningReadRequest(original.before(), original.source(), original.sessionId(), contract.operation(), new Obj(Map.of()), Instant.now().plusSeconds(10));
                assertThrows(IllegalArgumentException.class, () -> guard.verifyOriginalCurrent(same.head(), request, contract));
                return null;
            });
            assertEquals(packets, actual.nativePacketReads()); assertEquals(queries, actual.nativeReadWrites());
            assertEquals(planning, actual.nestedPlanningReads.get()); assertSame(retainedReady, actual.lastPublishedReady.get());
            assertEquals(0, probe.ordinaryCapabilities.get()); assertTrue(probe.sourceChecks.get() > 0); assertEquals(0, actual.nativeActionWrites());
        }
    }

    @Test void sourceOwnedUnpausedDataMayExplainStaleCollectionButCannotIssueAnOriginalReadGuard() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("held-unpaused"), false)) {
            actual.ready();
            var received = actual.physicalInputs().transport().currentSnapshot(Instant.now().plusSeconds(20));
            var state = DriverJson.object(received.state().bytes(), DriverJson.MAX_NATIVE_BYTES).with("paused", new OpportunityJson.Bool(false));
            var snapshot = new Obj(Map.of("type", new OpportunityJson.Text("state_snapshot"),
                    "protocol_version", new OpportunityJson.IntegerValue(BigInteger.ONE),
                    "snapshot_id", new OpportunityJson.Text("held-unpaused-snapshot"),
                    "revision", new OpportunityJson.IntegerValue(received.nativeRevision().add(BigInteger.ONE)), "state", state));
            actual.enqueueSoftwareNativePacket(NativeWire.packet(DriverJson.encode(snapshot)));
            assertInstanceOf(org.xar.ck3.control.application.session.SessionPorts.Waiting.class,
                    actual.collector.observe(actual.observationIdentity(), Instant.now().plusSeconds(20)));
            var probe = new Probe(actual, Clock.systemUTC()); int packets = actual.nativePacketReads(), queries = actual.nativeReadWrites();
            actual.writer.locked(same -> probe.collector.withHeldReadScope(same, actual.observationIdentity(), Instant.now().plusSeconds(20), frame -> {
                assertEquals(new OpportunityJson.Bool(false), frame.semantic().get("paused"));
                probe.collector.requireHeldFrame(same, frame);
                var request = new PlanningReadRequest(frame.identity(), frame.source(), frame.sessionId(), actual.readContract.operation(), new Obj(Map.of()), Instant.now().plusSeconds(10));
                assertThrows(IllegalArgumentException.class, () -> probe.collector.currentHeldOriginal(same, request, lease -> null)); return null;
            }));
            assertEquals(packets, actual.nativePacketReads()); assertEquals(queries, actual.nativeReadWrites()); assertEquals(0, probe.ordinaryCapabilities.get());
        }
    }

    @Test void cloneSourceSessionDeadlineAndEscapedFrameCannotBecomeHeldAuthority() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("held-drift"), false)) {
            actual.ready(); var probe = new Probe(actual, Clock.systemUTC()); var escaped = new AtomicReference<Complete>();
            int packets = actual.nativePacketReads(), queries = actual.nativeReadWrites();
            actual.writer.locked(same -> {
                probe.collector.withHeldReadScope(same, actual.observationIdentity(), Instant.now().plusSeconds(20), frame -> {
                    escaped.set(frame);
                    var clone = new Complete(frame.identity(), frame.source(), frame.sessionId(), frame.connectionGeneration(), frame.semantic(), frame.originalEvidence(), frame.observedAt(), frame.fullBindingSha256());
                    assertEquals(frame, clone); assertThrows(IllegalArgumentException.class, () -> probe.collector.requireHeldFrame(same, clone));
                    var wrongSource = new G2Source(frame.source().machineId(), Instant.now().toString(), "changed-source", frame.source().sourceRef());
                    var source = new PlanningReadRequest(frame.identity(), wrongSource, frame.sessionId(), actual.readContract.operation(), new Obj(Map.of()), Instant.now().plusSeconds(10));
                    assertThrows(IllegalArgumentException.class, () -> probe.collector.currentHeldOriginal(same, source, lease -> null));
                    var session = new PlanningReadRequest(frame.identity(), frame.source(), frame.sessionId()+"-other", actual.readContract.operation(), new Obj(Map.of()), source.deadline());
                    assertThrows(IllegalArgumentException.class, () -> probe.collector.currentHeldOriginal(same, session, lease -> null));
                    var expired = new PlanningReadRequest(frame.identity(), frame.source(), frame.sessionId(), actual.readContract.operation(), new Obj(Map.of()), Instant.now().minusSeconds(1));
                    assertThrows(IllegalArgumentException.class, () -> probe.collector.currentHeldOriginal(same, expired, lease -> null));
                    probe.collector.requireHeldFrame(same, frame); return null;
                });
                assertThrows(IllegalArgumentException.class, () -> probe.collector.requireHeldFrame(same, escaped.get()));
                var frame = escaped.get(); var request = new PlanningReadRequest(frame.identity(), frame.source(), frame.sessionId(), actual.readContract.operation(), new Obj(Map.of()), Instant.now().plusSeconds(10));
                assertThrows(IllegalArgumentException.class, () -> probe.collector.currentHeldOriginal(same, request, lease -> null)); return null;
            });
            assertEquals(packets, actual.nativePacketReads()); assertEquals(queries, actual.nativeReadWrites()); assertEquals(0, actual.nativeActionWrites());
        }
    }

    @Test void staleSourceMutationConsumerFailureAndForeignWriterDoNotRefreshOrLeakScope() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("held-failure"), false);
             var other = new ActionWriterIntegrationFixture(temporary.resolve("foreign-held"), false)) {
            actual.ready(); var probe = new Probe(actual, Clock.systemUTC());
            int packets = actual.nativePacketReads(), queries = actual.nativeReadWrites();
            other.writer.locked(foreign -> {
                assertThrows(IOException.class, () -> probe.collector.withHeldReadScope(foreign, actual.observationIdentity(), Instant.now().plusSeconds(20), frame -> null)); return null;
            });
            actual.writer.locked(same -> {
                var owner = actual.observationIdentity();
                assertThrows(IllegalArgumentException.class, () -> probe.collector.withHeldReadScope(same,
                        new SessionIdentity(owner.machineId(), owner.game(), owner.sessionId()+"-other"), Instant.now().plusSeconds(20), frame -> null));
                var expiredClock = Clock.fixed(Instant.now().plusSeconds(31), ZoneOffset.UTC); var stale = new Probe(actual, expiredClock);
                stale.collector.withHeldReadScope(same, owner, expiredClock.instant().plusSeconds(20), frame -> {
                    assertTrue(frame.observedAt().isBefore(expiredClock.instant().minusSeconds(30)));
                    stale.collector.requireHeldFrame(same, frame); return null;
                });
                assertThrows(IllegalArgumentException.class, () -> stale.collector.withHeldReadScope(same, owner,
                        expiredClock.instant().minusNanos(1), frame -> null));
                assertThrows(IOException.class, () -> probe.collector.withHeldReadScope(same, owner, Instant.now().plusSeconds(20), frame -> { throw new IOException("consumer stopped"); }));
                assertThrows(IOException.class, () -> probe.collector.withHeldReadScope(same, owner, Instant.now().plusSeconds(20), frame -> { probe.currentSource.set(false); return null; }));
                probe.currentSource.set(true);
                probe.collector.withHeldReadScope(same, owner, Instant.now().plusSeconds(20), frame -> { probe.collector.requireHeldFrame(same, frame); return null; });
                return null;
            });
            assertEquals(packets, actual.nativePacketReads()); assertEquals(queries, actual.nativeReadWrites()); assertEquals(0, probe.ordinaryCapabilities.get());
        }
    }

    @Test void applicationDefaultHeldAdmissionRefusesWithoutInvokingOrdinaryCurrent() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("held-default"), false)) {
            var ready = actual.ready().request(); var ordinary = new AtomicInteger();
            ReadinessAuthority absent = new ReadinessAuthority() {
                @Override public <T> T current(ContinuityStorePort.Session same, ObservationIdentity expected, Instant callerDeadline, CheckedWork<T> work) {
                    ordinary.incrementAndGet(); throw new AssertionError("held original default cannot delegate to current");
                }
            };
            var request = new PlanningReadRequest(ready.before(), ready.source(), ready.sessionId(), actual.readContract.operation(), new Obj(Map.of()), Instant.now().plusSeconds(10));
            actual.writer.locked(same -> { assertThrows(IOException.class, () -> absent.currentHeldOriginal(same, request, lease -> null)); return null; });
            assertEquals(0, ordinary.get());
        }
    }

    @Test void missingReceivedSnapshotOrDriverObservationRefusesBeforeAnyNativeDeliveryIsConsumed() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("held-missing"), false)) {
            var probe = new Probe(actual, Clock.systemUTC()); int packets = actual.nativePacketReads(), queries = actual.nativeReadWrites();
            actual.writer.locked(same -> {
                if (actual.physicalInputs().transport().latestObservedSnapshot().isEmpty()) {
                    assertThrows(IOException.class, () -> probe.collector.withHeldReadScope(same, actual.observationIdentity(), Instant.now().plusSeconds(20), frame -> null));
                } else {
                    assertThrows(IllegalStateException.class, () -> probe.collector.withHeldReadScope(same, actual.observationIdentity(), Instant.now().plusSeconds(20), frame -> null));
                }
                return null;
            });
            assertEquals(packets, actual.nativePacketReads()); assertEquals(queries, actual.nativeReadWrites()); assertEquals(0, actual.nativeActionWrites());
        }
    }
}
