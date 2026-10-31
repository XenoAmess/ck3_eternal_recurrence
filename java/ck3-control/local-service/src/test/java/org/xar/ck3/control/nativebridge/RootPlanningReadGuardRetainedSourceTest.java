package org.xar.ck3.control.nativebridge;
import java.lang.reflect.Proxy;
import java.lang.reflect.InvocationHandler;
import java.util.HashSet;
import java.util.function.Function;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.ActionRecord;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadGuard;
import org.xar.ck3.control.application.action.PlanningReadFailure;
import org.xar.ck3.control.contracts.presentation.PresentationOriginals;
import org.xar.ck3.control.contracts.presentation.FrontendWindowCaptureRequest;
import org.xar.ck3.control.contracts.presentation.FrontendWindowCaptureOutcome;
import org.xar.ck3.control.contracts.presentation.OriginalOutcome;
import org.xar.ck3.control.contracts.presentation.PresentationObservation;
import java.lang.reflect.Method;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.effects.RootPlanningReadGuard;
import org.xar.ck3.control.application.readiness.*;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameLifecycle;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Actual Root guard and collector over the existing software transport/Driver/writer/archive fixture.
 * Implementation source identity stays retained metadata; live source authority checks independent DATA. */
final class RootPlanningReadGuardRetainedSourceTest {
    @TempDir Path temporary;

    @Test void changedImplementationOriginalDoesNotBlockTheActualCurrentReadGuard() throws Exception {
        withReady("implementation-change", (actual, probe, same, ready, guard) -> {
            ExactRef retained = actual.observationSource().sourceRef();
            assertEquals(retained, actual.readContract.sourceRef()); // Both references came from the actual fixture producer.
            Files.writeString(Path.of(retained.path()), "updated implementation source after installation", StandardOpenOption.TRUNCATE_EXISTING);
            assertNotEquals(retained.bytes(), Files.size(Path.of(retained.path())));
            int packets = actual.nativePacketReads(), queries = actual.nativeReadWrites(), checks = probe.currentChecks.get();
            long sequence = same.head().state().sequence(); String head = same.head().digest();
            PlanningReadGuard verified;
            try {
                verified = guard.verify(same.head(), request(ready, actual.readContract), actual.readContract);
            } catch (UncheckedIOException oldImplementationGate) {
                assertTrue(hasImplementationExactFailure(oldImplementationGate),
                        "baseline RED must arise from the retained implementation file in LedgerFiles.exact");
                assertEquals(checks, probe.currentChecks.get(), "the obsolete implementation gate ran before actual authority");
                throw oldImplementationGate;
            }
            assertTrue(probe.currentChecks.get() > checks, "the actual current source callback must still run");
            assertTrue(verified.paused() && verified.mapReady() && verified.playerAlive());
            assertEquals(ready.request().before(), verified.binding().observed());
            assertEquals(actual.observationSource(), verified.binding().source());
            assertEquals(ready.request().sessionId(), verified.binding().sessionId());
            RootGuardEvidence.requireHistory(verified.binding(), actual.archive.withSession(same), same);
            assertEquals(ready.request().before(), RootGuardEvidence.loadFrame(verified.binding(),
                    actual.archive.withSession(same), actual.frameLoader()).identity());
            assertEquals(packets, actual.nativePacketReads()); assertEquals(queries, actual.nativeReadWrites());
            assertEquals(sequence, same.head().state().sequence()); assertEquals(head, same.head().digest());
            assertEquals(0, actual.nativeActionWrites());
        });
    }

    @Test void identicalInstalledContractSessionSourceAndCurrentAuthorityStillApply() throws Exception {
        withReady("typed-current", (actual, probe, same, ready, guard) -> {
            PlanningReadRequest original = request(ready, actual.readContract);
            int packets = actual.nativePacketReads(), queries = actual.nativeReadWrites();
            ReadContract<RawJson> clone = ActionWriterIntegrationFixture.contract(actual.readContract.sourceRef());
            assertThrows(IllegalArgumentException.class, () -> guard.verify(same.head(), original, clone));
            var wrongSession = new PlanningReadRequest(original.before(), original.source(), original.sessionId()+"-other",
                    original.operation(), original.arguments(), original.deadline());
            assertThrows(IllegalArgumentException.class, () -> guard.verify(same.head(), wrongSession, actual.readContract));
            G2Source changed = new G2Source(original.source().machineId(), Instant.now().toString(), "other-source", original.source().sourceRef());
            var wrongSource = new PlanningReadRequest(original.before(), changed, original.sessionId(), original.operation(), original.arguments(), original.deadline());
            assertThrows(IllegalArgumentException.class, () -> guard.verify(same.head(), wrongSource, actual.readContract));
            int checks = probe.currentChecks.get(); probe.currentValid.set(false);
            var denied = assertThrows(UncheckedIOException.class, () -> guard.verify(same.head(), original, actual.readContract));
            assertTrue(denied.getCause().getMessage().contains("actual current DATA authority unavailable"));
            assertTrue(probe.currentChecks.get() > checks);
            probe.currentValid.set(true);
            assertNotNull(guard.verify(same.head(), original, actual.readContract));
            assertEquals(packets, actual.nativePacketReads()); assertEquals(queries, actual.nativeReadWrites());
            assertEquals(0, actual.nativeActionWrites());
        });
    }

    @Test void realArchivedSemanticAndNativePacketTamperingStillReject() throws Exception {
        for (boolean nativePacket : List.of(false, true)) {
            withReady(nativePacket ? "native-data-change" : "semantic-data-change", (actual, probe, same, ready, guard) -> {
                PlanningReadRequest original = request(ready, actual.readContract);
                assertNotNull(guard.verify(same.head(), original, actual.readContract));
                var semantic = ready.semanticEvidence().orElseThrow();
                ExactRef data = nativePacket ? semantic.originalNativePacket() : semantic.semantic();
                Files.write(Path.of(data.path()), "changed actual immutable DATA".getBytes(StandardCharsets.UTF_8), StandardOpenOption.TRUNCATE_EXISTING);
                int checks = probe.currentChecks.get(), packets = actual.nativePacketReads(), queries = actual.nativeReadWrites();
                String head = same.head().digest();
                assertThrows(UncheckedIOException.class, () -> guard.verify(same.head(), original, actual.readContract));
                assertTrue(probe.currentChecks.get() > checks, "actual current authority must be reached before DATA binding refuses");
                assertEquals(head, same.head().digest());
                assertEquals(packets, actual.nativePacketReads()); assertEquals(queries, actual.nativeReadWrites());
                assertEquals(0, actual.nativeActionWrites());
            });
        }
    }

    @Test void anActualUnresolvedActionCannotBecomeReadinessOrBeReplayed() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("unknown"), true)) {
            var before = actual.ready();
            var command = actual.command("retained-unknown");
            ActionReceipt unknown = actual.coordinator.execute(command);
            assertEquals(ActionReceipt.Outcome.UNRESOLVED, unknown.outcome());
            int writes = actual.nativeActionWrites(); long sequence = actual.sequence();
            Probe probe = new Probe(actual);
            actual.writer.locked(same -> {
                var incomplete = actual.driverAuthority().withFrozenFacts(same, frozen -> {
                    var known = assertInstanceOf(org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known.class, frozen.state());
                    return assertInstanceOf(org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Incomplete.class,
                            org.xar.ck3.control.application.driver.DriverStateAssembler.projectObservation(known, frozen.actions(), frozen.activeActionId()));
                });
                assertTrue(incomplete.missingOrUnreconciledFields().contains("unreconciled_action:" + command.actionId()),
                        incomplete.toString());
                RootPlanningReadGuard guard = guard(actual, probe);
                int queries = actual.nativeReadWrites();
                var retained = before.request();
                var currentRead = new PlanningReadRequest(retained.before(), retained.source(), retained.sessionId(),
                        actual.readContract.operation(), new Obj(Map.of()), Instant.now().plusSeconds(30));
                RuntimeException refused = assertThrows(RuntimeException.class,
                        () -> guard.verify(same.head(), currentRead, actual.readContract));
                assertTrue(String.valueOf(refused.getMessage()).contains("incomplete") || String.valueOf(refused.getMessage()).contains("unresolved"),
                        () -> "UNKNOWN refusal must be its actual incomplete/unresolved Driver, not an unrelated failure: " + refused);
                assertEquals(queries, actual.nativeReadWrites());
                return null;
            });
            assertEquals(unknown, actual.coordinator.execute(command));
            assertEquals(writes, actual.nativeActionWrites()); assertEquals(sequence, actual.sequence());
            assertEquals(unknown, actual.snapshot().actions().stream()
                    .filter(receipt -> receipt.command().actionId().equals(command.actionId())).findFirst().orElseThrow());
        }
    }

    private static PlanningReadRequest request(SessionPorts.Ready ready, ReadContract<?> contract) {
        var original = ready.request();
        return new PlanningReadRequest(original.before(), original.source(), original.sessionId(), contract.operation(),
                new Obj(Map.of()), original.deadline());
    }
    private static boolean hasImplementationExactFailure(Throwable failure) {
        for (Throwable current = failure; current != null; current = current.getCause()) {
            if (Arrays.stream(current.getStackTrace()).anyMatch(frame -> frame.getClassName().endsWith("LedgerFiles")
                    && frame.getMethodName().equals("exact"))) return true;
        }
        return false;
    }
    private static RootPlanningReadGuard guard(ActionWriterIntegrationFixture actual, Probe probe) {
        return new RootPlanningReadGuard(probe.collector, () -> {
            try { return actual.writer.borrowedSession(); }
            catch (IOException failure) { throw new UncheckedIOException(failure); }
        }, actual.archive, actual.observationSource(), Clock.systemUTC(), "retained-source-regression",
                actual.physicalInputs().originals(), actual.actualReadCatalog());
    }
    @FunctionalInterface private interface ReadyWork {
        void run(ActionWriterIntegrationFixture actual, Probe probe, ContinuityStorePort.Session same,
                SessionPorts.Ready ready, RootPlanningReadGuard guard) throws IOException;
    }
    private void withReady(String name, ReadyWork work) throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve(name), false)) {
            actual.ready();
            Probe probe = new Probe(actual);
            actual.writer.locked(same -> {
                try {
                    return probe.collector.withPlanningRound(same, () -> {
                        var ready = assertInstanceOf(SessionPorts.Ready.class,
                                probe.collector.observe(same, actual.observationIdentity(), Instant.now().plusSeconds(45)));
                        work.run(actual, probe, same, ready, guard(actual, probe)); return null;
                    });
                } catch (InterruptedException interrupted) {
                    Thread.currentThread().interrupt(); throw new IOException(interrupted);
                }
            });
        }
    }
    /** Uses the genuine physical producer chain. The source callback validates actual preserved DATA,
     * while retained implementation metadata is deliberately not a second file-qualification gate. */
    private static final class Probe {
        final NativeReadinessCollector collector;
        final AtomicBoolean currentValid = new AtomicBoolean(true);
        final AtomicInteger currentChecks = new AtomicInteger();
        final AtomicReference<ExactRef> dataProof = new AtomicReference<>();
        Probe(ActionWriterIntegrationFixture actual) {
            var physical = actual.physicalInputs();
            Set<String> capabilities = Set.of("game.command.pause-map", "game.query.fixture-status");
            Set<OperationKey> actions = Set.of(new OperationKey("pause-map"));
            collector = new NativeReadinessCollector(actual.observationIdentity(), actual.writer, physical.transport(),
                    physical.driverAssembler(), physical.observationAssembler(),
                    (game, deadline) -> new GameLifecycle.Running(game, physical.source().sourceRef()),
                    (same, role, bytes) -> actual.archive.preserveArtifact(same, bytes, role.maximumBytes()),
                    new NativeSemanticEvidenceVerifier((same, ref, maximum) -> actual.archive.readArtifact(same, ref, maximum)),
                    (same, identity, frame, known, received, process, deadline) -> {
                        actual.writer.requireSession(same); assertEquals(actual.observationIdentity(), identity);
                        assertEquals(physical.source(), frame.source()); assertEquals(identity.game(), process.measured());
                        ExactRef proof = actual.archive.preserveArtifact(same,
                                "{\"schema\":\"fixture.actual-current-data/v1\",\"received\":true}".getBytes(StandardCharsets.UTF_8), 65_536);
                        dataProof.set(proof); var pin = same.capturePin(proof, 65_536); same.verifyPin(pin);
                        return new NativeReadinessCollector.SourceQualification(proof, borrowed -> {
                            assertSame(same, borrowed); actual.writer.requireSession(borrowed); borrowed.verifyPin(pin);
                            currentChecks.incrementAndGet();
                            if (!currentValid.get()) throw new IOException("actual current DATA authority unavailable");
                        });
                    },
                    (same, frame, known, received, deadline) -> new NativeReadinessCollector.ExecutableCapabilities(actions, capabilities, Optional.empty()),
                    (same, frame, known, received, deadline) -> new NativeReadinessCollector.PlanningInputs(actions, capabilities,
                            Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false, Optional.empty()),
                    new NativeReadiness.Policy(false, false, Optional.of(BigInteger.valueOf(73)), Duration.ZERO, false),
                    Duration.ofSeconds(45), Clock.systemUTC());
            collector.bindObservationSession(actual.writer::requireSession);
            collector.bindActiveObservationSession(actual.writer::activeSession);
            collector.bindReadyPublication((same, request, frame, known, source) -> {
                actual.writer.requireSession(same); source.assertCurrent(same);
                assertEquals(frame.identity(), request.before()); assertEquals(physical.source(), request.source());
            });
        }
    }

    private static ActionPorts.OutcomeArchive countingArchive(ActionPorts.OutcomeArchive delegate, Set<ExactRef> forbidden, AtomicInteger reloads, AtomicInteger preserves, AtomicInteger loads) {
        return (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(delegate.getClass().getClassLoader(), new Class<?>[]{ActionPorts.OutcomeArchive.class}, new InvocationHandler() {
            @SuppressWarnings("unchecked") @Override public Object invoke(Object proxy, java.lang.reflect.Method method, Object[] args) throws Throwable {
                String name = method.getName();
                if (name.equals("withSession")) return countingArchive(delegate.withSession((ContinuityStorePort.Session) args[0]), forbidden, reloads, preserves, loads);
                if (name.equals("inSession")) {
                    Function<ActionPorts.OutcomeArchive, ?> work = (Function<ActionPorts.OutcomeArchive, ?>) args[1];
                    return delegate.inSession((ContinuityStorePort.Session) args[0], (ActionPorts.OutcomeArchive inner) -> work.apply(countingArchive(inner, forbidden, reloads, preserves, loads)));
                }
                if (name.equals("preserveMaterial")) preserves.incrementAndGet();
                if (name.equals("loadMaterial") || name.equals("loadFullMaterial") || name.equals("loadNativeFrame") || name.equals("readOriginalPacket")) {
                    ExactRef ref = (ExactRef) args[0];
                    if (forbidden.contains(ref)) reloads.incrementAndGet();
                    if (name.equals("loadMaterial")) loads.incrementAndGet();
                }
                try { return method.invoke(delegate, args); } catch (java.lang.reflect.InvocationTargetException failure) { throw failure.getCause(); }
            }
        });
    }
    private static ActionPorts.OutcomeArchive countingArchive(ActionPorts.OutcomeArchive actual, AtomicInteger loadMaterial, AtomicInteger loadFullMaterial, AtomicInteger loadNativeFrame) {
        return (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(actual.getClass().getClassLoader(), new Class<?>[]{ActionPorts.OutcomeArchive.class}, new InvocationHandler() {
            @SuppressWarnings("unchecked") public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
                if (method.getName().equals("withSession")) {
                    Object result = method.invoke(actual, args);
                    return countingArchive((ActionPorts.OutcomeArchive) result, loadMaterial, loadFullMaterial, loadNativeFrame);
                }
                if (method.getName().equals("inSession")) {
                    java.util.function.Function<ActionPorts.OutcomeArchive, ?> work =
                            (java.util.function.Function<ActionPorts.OutcomeArchive, ?>) args[1];
                    return actual.inSession((ContinuityStorePort.Session) args[0],
                            inner -> work.apply(countingArchive(inner, loadMaterial, loadFullMaterial, loadNativeFrame)));
                }
                if (method.getName().equals("loadMaterial")) loadMaterial.incrementAndGet();
                if (method.getName().equals("loadFullMaterial")) loadFullMaterial.incrementAndGet();
                if (method.getName().equals("loadNativeFrame")) loadNativeFrame.incrementAndGet();
                try {
                    return method.invoke(actual, args);
                } catch (java.lang.reflect.InvocationTargetException e) {
                    throw e.getCause();
                }
            }
        });
    }
    private static void assertRoleExtractionCounts(AtomicInteger loadMaterial, AtomicInteger loadFullMaterial, AtomicInteger loadNativeFrame) {
        assertTrue(loadMaterial.get() > 0, "role extraction must read the actual basis metadata");
        assertEquals(0, loadFullMaterial.get(), "role extraction must not read full material payloads");
        assertEquals(0, loadNativeFrame.get(), "role extraction must not read native frame payloads");
    }
    @Test void readBindingDoesNotReloadOldLeasePayloads() throws Exception {
        withReady("read-binding-no-reload", (actual, probe, same, ready, guard) -> {
            var semantic = ready.semanticEvidence().orElseThrow();
            Set<ExactRef> forbidden = new HashSet<>();
            forbidden.add(semantic.originalNativePacket());
            forbidden.add(semantic.semantic());
            forbidden.add(semantic.driverStamp());
            forbidden.add(semantic.originalDriver());
            AtomicInteger reloads = new AtomicInteger(), preserves = new AtomicInteger(), loads = new AtomicInteger();
            ActionPorts.OutcomeArchive counter = countingArchive(actual.archive, forbidden, reloads, preserves, loads);
            RootPlanningReadGuard countingGuard = new RootPlanningReadGuard(probe.collector, () -> same, counter, actual.observationSource(), Clock.systemUTC(), "test-authority", actual.physicalInputs().originals(), actual.actualReadCatalog());
            PlanningReadRequest original = request(ready, actual.readContract);
            PlanningReadGuard verified = countingGuard.verify(same.head(), original, actual.readContract);
            assertEquals(0, reloads.get(), "readBinding must not reload old lease native/SEM/stamp/driver payloads");
            assertTrue(preserves.get() > 0, "Root basis metadata must be preserved");
            assertTrue(loads.get() > 0, "Root basis metadata must be loaded/readback");
            assertEquals(ready.request().before(), verified.binding().observed());
            assertEquals(actual.observationSource(), verified.binding().source());
            assertEquals(ready.request().sessionId(), verified.binding().sessionId());
            assertTrue(verified.paused() && verified.mapReady() && verified.playerAlive());
            assertEquals(0, actual.nativeActionWrites());
        });
    }
    @Test void roleGettersDoNotReadFullPayloads() throws Exception {
        withReady("role-getter-counting", (actual, probe, same, ready, guard) -> {
            PlanningReadRequest original = request(ready, actual.readContract);
            PlanningReadGuard verified = guard.verify(same.head(), original, actual.readContract);
            GuardEvidence basis = verified.binding();

            AtomicInteger loadMaterial = new AtomicInteger();
            AtomicInteger loadFullMaterial = new AtomicInteger();
            AtomicInteger loadNativeFrame = new AtomicInteger();
            ActionPorts.OutcomeArchive counted = countingArchive(actual.archive.withSession(same), loadMaterial, loadFullMaterial, loadNativeFrame);

            var sourceQual = RootGuardEvidence.sourceQualification(basis, counted);
            var semanticRef = RootGuardEvidence.semanticReference(basis, counted);
            var driverSource = RootGuardEvidence.originalDriverSource(basis, counted);
            var writerPoint = RootGuardEvidence.writerPoint(basis, counted);
            var frameBasis = RootGuardEvidence.frameBasis(basis, counted);
            int metadataBefore = loadMaterial.get();
            AtomicInteger callbacks = new AtomicInteger();
            ExactRef inSessionSemantic = counted.inSession(same, view -> {
                callbacks.incrementAndGet(); return RootGuardEvidence.semanticReference(basis, view);
            });
            assertEquals(semanticRef, inSessionSemantic); assertEquals(1, callbacks.get());
            assertTrue(loadMaterial.get() > metadataBefore, "the inSession callback must use the shared counted view");

            assertRoleExtractionCounts(loadMaterial, loadFullMaterial, loadNativeFrame);

            assertEquals(same.head().state().sequence(), writerPoint.sequence());
            assertEquals(same.head().digest(), writerPoint.digest());
            assertEquals(basis.nativeEvidence(), frameBasis.nativeFrame());
            assertEquals(basis.source(), actual.observationSource());
            assertEquals(basis.sessionId(), ready.request().sessionId());
        });
    }
    @Test void loadFrameStillReadsFullPayloads() throws Exception {
        withReady("load-frame-counting", (actual, probe, same, ready, guard) -> {
            PlanningReadRequest original = request(ready, actual.readContract);
            PlanningReadGuard verified = guard.verify(same.head(), original, actual.readContract);
            GuardEvidence basis = verified.binding();

            AtomicInteger loadMaterial = new AtomicInteger();
            AtomicInteger loadFullMaterial = new AtomicInteger();
            AtomicInteger loadNativeFrame = new AtomicInteger();
            ActionPorts.OutcomeArchive counted = countingArchive(actual.archive.withSession(same), loadMaterial, loadFullMaterial, loadNativeFrame);

            // loadFrame uses the actual frame loader which internally calls archive methods.
            // The proxy counts these calls on the 'counted' archive instance passed to loadFrame.
            DriverObservationAssembler.Complete frame = RootGuardEvidence.loadFrame(basis, counted, actual.frameLoader());

            assertTrue(loadFullMaterial.get() > 0, "loadFrame must read full material payloads");
            assertTrue(loadNativeFrame.get() > 0, "loadFrame must read native frame payloads");

            assertEquals(basis.observed(), frame.identity());
            assertEquals(basis.source(), frame.source());
            assertEquals(basis.sessionId(), frame.sessionId());
            assertEquals(basis.connectionGeneration(), frame.connectionGeneration());
            assertEquals(basis.observedAt(), frame.observedAt());
        });
    }
}
