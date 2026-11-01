package org.xar.ck3.control.application.driver;

import java.lang.reflect.Proxy;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.application.capabilities.CapabilityFileProbe;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWindowAttempts;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWindowCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.junit.jupiter.api.Assertions.*;

/** Owned-temp writer/archive plus controlled software read port; no Game or native endpoint. */
final class DriverUnavailablePublication272Test {
    @TempDir Path temporary;

    private record Bound(DriverCapabilityRuntime runtime, ArmyWindowAttempts.Store windows,
            DriverObservationAssembler.Complete frame, PlanningReadGuard guard) { }

    private Bound runtime(ActionWriterIntegrationFixture fixture, Session same, RootReadContractCatalog catalog) throws Exception {
        var known = fixture.driverAuthority().withFrozenFacts(same, frozen ->
                assertInstanceOf(DriverSnapshotFacts.Known.class, frozen.state()));
        assertFalse(known.auxiliary().members().containsKey("capability_observed_native_source"));
        var repository = new DriverFactsRepository(known);
        var producer = new NativeDriverObservationProducer(repository, fixture.physicalInputs().transport(),
                fixture.observationSource(), bytes -> fixture.archive.preserveMaterial(RawJson.fullMaterial(bytes)));
        var authority = new DriverStateAssembler(new ActionSnapshotReader(fixture.journal), repository, producer);
        var files = (CheckpointFiles) Proxy.newProxyInstance(CheckpointFiles.class.getClassLoader(),
                new Class<?>[]{CheckpointFiles.class}, (proxy, method, args) -> {
                    throw new AssertionError("unavailable publication must not probe checkpoint files: " + method.getName());
                });
        var runtime = new DriverCapabilityRuntime(authority, fixture.archive, fixture.journal::borrowedWriterSession,
                fixture.actualBindings(), new CapabilityFileProbe(files, Optional.empty()), borrowed -> {
                    throw new AssertionError("unavailable publication must not probe retreat state");
                });
        runtime.bindReadHistoryPublisher(new DriverReadHistoryPublisher(authority, fixture.archive, catalog,
                List.of(fixture.observationSource().sourceRef())));
        var windows = new ArmyWindowAttempts.Store(fixture.archive);
        runtime.bindWindowAttempts(windows);
        var guard = fixture.lastNestedRead.get().before();
        var frame = RootGuardEvidence.loadFrame(guard.binding(), fixture.archive, fixture.frameLoader());
        return new Bound(runtime, windows, frame, guard);
    }

    private static PlanningReadGuard forOperation(PlanningReadGuard original, OperationKey operation) {
        var before = original.binding();
        var binding = new GuardEvidence(before.origin(), before.source(), before.sessionId(), before.connectionGeneration(),
                operation, before.nativeEvidence(), before.capabilityEvidence(), before.authorityId(),
                before.observedAt(), before.validUntil(), before.supportingEvidence());
        return new PlanningReadGuard(binding, original.paused(), original.mapReady(), original.playerAlive(),
                original.originalBindingSha256());
    }

    @Test void guardAndPrepareFailuresRetainTheirCauseWithoutAnUnrelatedWindowRefresh() throws Exception {
        for (boolean guardFailure : List.of(true, false)) {
            try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("pre-" + guardFailure), false)) {
                fixture.ready();
                fixture.writer.locked(same -> {
                    var operation = new OperationKey(ClockStatusRead.STEP);
                    var contract = new ReadContract<RawJson>("software-status-272", operation, Optional.empty(), "status-272",
                            ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.EXECUTE_STEP,
                            ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, fixture.observationSource().sourceRef(),
                            (request, id) -> { throw new IllegalArgumentException("controlled preparation refusal"); },
                            receipt -> receipt.original().originalResultToken().orElseThrow(),
                            receipt -> receipt.original().originalResultToken().orElseThrow());
                    var catalog = RootReadContractCatalog.staticOnly(List.of(contract));
                    Bound bound;
                    try { bound = runtime(fixture, same, catalog); } catch (Exception failure) { throw new RuntimeException(failure); }
                    var tokens = new AtomicInteger();
                    var observed = new AtomicReference<Optional<PlanningReadCoordinator.FailedReadAttempt>>();
                    var observer = new PlanningReadCoordinator.KnownReadObserver() {
                        @Override public void afterKnown(Session original, ReadContract<?> actual, PlanningReadResult.Known<?> result) {
                            fail("pre-permit failure is not Known");
                        }
                        @Override public void afterUnavailable(Session original, ReadContract<?> actual, PlanningReadRequest request,
                                PlanningReadResult.Unavailable<?> unavailable, Optional<PlanningReadCoordinator.FailedReadAttempt> attempt) {
                            observed.set(attempt);
                            bound.runtime().afterUnavailable(original, actual, request, unavailable, attempt);
                        }
                    };
                    var reads = new PlanningReadCoordinator(catalog, fixture.journal, (head, request, actual) -> {
                        if (guardFailure) throw new IllegalArgumentException("capability_session_paths must be an object");
                        return forOperation(bound.guard(), operation);
                    }, (permit, prepared, deadline) -> { tokens.incrementAndGet(); throw new AssertionError("pre-permit must not dispatch"); },
                            fixture.archive, Clock.fixed(bound.guard().binding().observedAt(), ZoneOffset.UTC), observer);
                    var request = new PlanningReadRequest(bound.frame().identity(), bound.frame().source(), bound.frame().sessionId(),
                            operation, new Obj(Map.of()), Instant.now().plusSeconds(30));
                    var result = assertInstanceOf(PlanningReadResult.Unavailable.class, reads.read(same, contract, request));
                    assertEquals("IllegalArgumentException:" + (guardFailure ? "capability_session_paths must be an object"
                            : "controlled preparation refusal"), result.reason());
                    assertTrue(result.original().isEmpty());
                    assertNotNull(observed.get());
                    assertTrue(observed.get().isEmpty());
                    assertEquals(0, tokens.get());
                    return null;
                });
            }
        }
    }

    @Test void consumedStatusUnknownKeepsItsExactOutcomeAndFailedAttempt() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("unknown"), false)) {
            fixture.ready();
            fixture.writer.locked(same -> {
                var contract = ClockStatusRead.registeredContract(fixture.observationSource().sourceRef());
                var catalog = RootReadContractCatalog.staticOnly(List.of(contract));
                Bound bound;
                try { bound = runtime(fixture, same, catalog); } catch (Exception failure) { throw new RuntimeException(failure); }
                var outgoing = new AtomicReference<NativeActionPort.Unknown>();
                var observerCalls = new AtomicInteger();
                var portCalls = new AtomicInteger();
                var observer = new PlanningReadCoordinator.KnownReadObserver() {
                    @Override public void afterKnown(Session original, ReadContract<?> actual, PlanningReadResult.Known<?> result) {
                        fail("controlled unknown is not Known");
                    }
                    @Override public void afterUnavailable(Session original, ReadContract<?> actual, PlanningReadRequest request,
                            PlanningReadResult.Unavailable<?> unavailable, Optional<PlanningReadCoordinator.FailedReadAttempt> attempt) {
                        observerCalls.incrementAndGet();
                        var proof = attempt.orElseThrow();
                        try { proof.requireOriginal(original, actual, request, unavailable, fixture.archive.withSession(original)); }
                        catch (java.io.IOException failure) { throw new java.io.UncheckedIOException(failure); }
                        assertSame(outgoing.get(), proof.original());
                        assertEquals(outgoing.get(), fixture.archive.load(proof.originalRef()));
                        bound.runtime().afterUnavailable(original, actual, request, unavailable, attempt);
                    }
                };
                var reads = new PlanningReadCoordinator(catalog, fixture.journal,
                        (head, request, actual) -> forOperation(bound.guard(), contract.operation()),
                        (permit, prepared, deadline) -> {
                            portCalls.incrementAndGet(); permit.consumeOnce();
                            var unknown = new NativeActionPort.Unknown(permit.requestId(), "controlled software unknown",
                                    "controlled outgoing request".getBytes(StandardCharsets.UTF_8), Optional.empty());
                            outgoing.set(unknown); return unknown;
                        }, fixture.archive, Clock.fixed(bound.guard().binding().observedAt(), ZoneOffset.UTC), observer);
                var request = new PlanningReadRequest(bound.frame().identity(), bound.frame().source(), bound.frame().sessionId(),
                        contract.operation(), new Obj(Map.of()), Instant.now().plusSeconds(30));
                var result = assertInstanceOf(PlanningReadResult.Unavailable.class, reads.read(same, contract, request));
                assertEquals("native query returned unavailable or an unbound ACK", result.reason());
                assertSame(outgoing.get(), result.original().orElseThrow());
                assertEquals(1, portCalls.get()); assertEquals(1, observerCalls.get());
                return null;
            });
        }
    }

    @Test void bothActualWindowKindsStillRetainFailureAndRejectMissingPublicationBasis() throws Exception {
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("windows"), false)) {
            fixture.ready();
            fixture.writer.locked(same -> {
                Bound bound;
                try { bound = runtime(fixture, same, fixture.actualReadCatalog()); } catch (Exception failure) { throw new RuntimeException(failure); }
                for (var kind : ArmyWindowCodec.Kind.values()) {
                    var operation = new OperationKey(kind.step(ArmyWindowCodec.Operation.QUERY));
                    var contract = new ReadContract<RawJson>("window-272-" + kind, operation, Optional.empty(), "window-272-" + kind,
                            ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.EXECUTE_STEP,
                            ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, fixture.observationSource().sourceRef(),
                            (request, id) -> new NativeRequest(operation.value(), Optional.empty(), new RawJson(new byte[]{'{','}'})),
                            receipt -> receipt.original().originalResultToken().orElseThrow(),
                            receipt -> receipt.original().originalResultToken().orElseThrow());
                    var request = new PlanningReadRequest(bound.frame().identity(), bound.frame().source(), bound.frame().sessionId(),
                            operation, new Obj(Map.of()), Instant.now().plusSeconds(30));
                    var context = new ArmyTypes.Context(request.before(), request.source(), request.sessionId(), request.deadline());
                    String id = "controlled-window-" + kind;
                    var prepared = contract.prepare(request, id);
                    bound.windows().prepared(contract, kind, context, bound.frame().connectionGeneration(), request, id, prepared);
                    var unknown = new NativeActionPort.Unknown(id, "controlled unknown", new byte[]{1,2,3,4}, Optional.empty());
                    var unavailable = new PlanningReadResult.Unavailable<RawJson>("controlled fixed-window failure", Optional.of(unknown));
                    var failure = assertThrows(IllegalArgumentException.class,
                            () -> bound.runtime().afterUnavailable(same, contract, request, unavailable));
                    assertTrue(failure.getMessage().contains("exact reference must be an object"));
                    ArmyWindowAttempts.Snapshot snapshot;
                    try { snapshot = bound.windows().current(same, bound.frame()); }
                    catch (java.io.IOException error) { throw new java.io.UncheckedIOException(error); }
                    var actual = (kind == ArmyWindowCodec.Kind.OVERVIEW ? snapshot.overview() : snapshot.results()).orElseThrow();
                    assertEquals(ArmyWindowAttempts.Status.FAILED, actual.status());
                    assertEquals(unknown, fixture.archive.load(actual.originalOutcome().orElseThrow()));
                    assertEquals("failed", ((org.xar.ck3.control.planning.opportunity.OpportunityJson.Text) actual.normalized().get("status")).value());
                }
                return null;
            });
        }
    }
}
