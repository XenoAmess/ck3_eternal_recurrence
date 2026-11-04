package org.xar.ck3.control.nativebridge.capabilities.governance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Clock;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Supplier;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.governance.CouncilSelection;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.council.CouncilPrivateCodec;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.NativeWire;

/**
 * New terminal/failure edges through the actual public readPrivate consumer,
 * writer, source guard, read coordinator, transport and original archive.
 * The original 213 token supplies DATA only. Its owner/native frame is explicitly
 * projected into the actual software fixture request; original files are untouched.
 * No Guard/Session/permit/issuer is constructed, and no scope completion or poison
 * clearing method is invoked by this test. The production caller owns its closure.
 * ORACLE-FROZEN.json precedes this candidate. No client repair candidate was read.
 */
final class CouncilTerminalFailurePublicDataP0Test {
    @TempDir Path temporary;
    private static final String SHA = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    private static final String TERMINAL_SHA = "de3c1855ae750a2a340ccc87035f95e714f558c29f106afd5ab98073d26f4e43";
    private enum Fault { NONE, AFTER_GUARD, KNOWN_CALLBACK }
    private enum Shape { BOUND_TERMINAL, WRONG_NATIVE_FRAME, PENDING_STATUS }
    private static final class Recorded {
        final ArrayList<PlanningReadReceipt> knownPrefix = new ArrayList<>();
        final AtomicReference<PlanningReadResult.Unavailable<?>> statusUnavailable = new AtomicReference<>();
        final AtomicBoolean statusResponseProduced = new AtomicBoolean();
        final AtomicBoolean injected = new AtomicBoolean();
        final AtomicReference<RawJson> statusToken = new AtomicReference<>();
    }
    private record Scene(ActionWriterIntegrationFixture actual, PlanningRequest request,
            Read<CouncilSelection.Query> result, Recorded recorded, int writesBefore) { }
    @FunctionalInterface private interface Check { void run(Scene scene) throws Exception; }

    @Test void actualPendingAndBoundTerminalCompleteThroughTheOrdinaryPublicConsumer() throws Exception {
        scene("terminal-control", Fault.NONE, Shape.BOUND_TERMINAL, scene -> {
            assertInstanceOf(Known.class, scene.result());
            requireWireAndNoActions(scene);
            assertEquals(2, scene.recorded().knownPrefix.size());
            assertInstanceOf(CouncilPrivateCodec.Terminal.class, CouncilPrivateCodec.decodeReply(
                    scene.recorded().statusToken.get().bytes(), CouncilPrivateCodec.STATUS));
            assertFalse(scene.recorded().injected.get());
            requireClosed(scene);
        });
    }

    @Test void boundTerminalWithActualAfterGuardFailureStaysUnavailableAndClosesOnlyConsumedCustody() throws Exception {
        scene("terminal-after-guard", Fault.AFTER_GUARD, Shape.BOUND_TERMINAL, scene -> {
            requireUnavailableWithOriginalAckAndNoCredit(scene);
            assertTrue(scene.recorded().injected.get());
            assertEquals(1, scene.recorded().knownPrefix.size(), "a failed after guard cannot manufacture the terminal READ receipt");
            requireBoundOriginalTerminal(scene);
            requireClosed(scene);
        });
    }

    @Test void archivedTypedTerminalWithActualKnownCallbackFailureStaysUnavailableWithoutNativePoison() throws Exception {
        scene("terminal-known-callback", Fault.KNOWN_CALLBACK, Shape.BOUND_TERMINAL, scene -> {
            requireUnavailableWithOriginalAckAndNoCredit(scene);
            assertTrue(scene.recorded().injected.get());
            assertEquals(2, scene.recorded().knownPrefix.size(), "callback receives the actual already-archived typed terminal");
            var status = scene.recorded().knownPrefix.getLast();
            assertSame(scene.recorded().statusUnavailable.get().original().orElseThrow(), status.original());
            status.original().custody().orElseThrow().verify(status);
            requireBoundOriginalTerminal(scene);
            requireClosed(scene);
        });
    }

    @Test void wrongNativeFrameTerminalAfterGuardFailureCannotCloseOrBecomeTechnicalCredit() throws Exception {
        scene("wrong-frame-after-guard", Fault.AFTER_GUARD, Shape.WRONG_NATIVE_FRAME, scene -> {
            requireUnavailableWithOriginalAckAndNoCredit(scene);
            assertTrue(scene.recorded().injected.get());
            var terminal = assertInstanceOf(CouncilPrivateCodec.Terminal.class, CouncilPrivateCodec.decodeReply(
                    scene.recorded().statusToken.get().bytes(), CouncilPrivateCodec.STATUS));
            assertThrows(IllegalArgumentException.class, () -> CouncilPrivateCodec.requireTerminalBinding(terminal,
                    CouncilPrivateCodec.GATES, PrivateCouncilReads.nativeFrame(scene.recorded().knownPrefix.getFirst().request())));
            requireUnresolved(scene);
        });
    }

    @Test void pendingStatusAfterGuardFailureCannotMasqueradeAsConsumedTerminal() throws Exception {
        scene("pending-status-after-guard", Fault.AFTER_GUARD, Shape.PENDING_STATUS, scene -> {
            requireUnavailableWithOriginalAckAndNoCredit(scene);
            assertTrue(scene.recorded().injected.get());
            assertInstanceOf(CouncilPrivateCodec.Pending.class, CouncilPrivateCodec.decodeReply(
                    scene.recorded().statusToken.get().bytes(), CouncilPrivateCodec.STATUS));
            requireUnresolved(scene);
        });
    }

    private void scene(String name, Fault fault, Shape shape, Check check) throws Exception {
        ObjectNode originalToken = originalTerminalToken();
        var definitions = new AtomicReference<PrivateCouncilReads>();
        var publicReads = new AtomicReference<GovernanceNativeReads>();
        var request = new AtomicReference<PlanningRequest>();
        var recorded = new Recorded();
        var scenario = new ActionWriterIntegrationFixture.SoftwareReadScenario(SHA, "terminal-failure-public-data", source -> {
            var actual = new PrivateCouncilReads(source); definitions.set(actual);
            publicReads.set(new GovernanceNativeReads(source, "1.20.0.4", SHA));
            return actual.registeredContracts();
        }, prepared -> {
            if (prepared.step().equals(CouncilPrivateCodec.GATES)) return pending(CouncilPrivateCodec.GATES);
            assertEquals(CouncilPrivateCodec.STATUS, prepared.step());
            RawJson token = shape == Shape.PENDING_STATUS ? pending(CouncilPrivateCodec.STATUS)
                    : projectedTerminal(originalToken, Objects.requireNonNull(request.get()), shape);
            recorded.statusToken.set(token);
            recorded.statusResponseProduced.set(true);
            return token;
        }, Optional.of("1.20.0.4"), Set.of());

        // The decorator delegates every real source/Root guard. It may only add a
        // controlled exception after the actual STATUS response and real after verify.
        var decoration = (ActionWriterIntegrationFixture.SoftwareReadGuardDecoration) context ->
                new PlanningReadCoordinator.ReadGuardPort() {
                    @Override public PlanningReadGuard verify(WriterContracts.Head head, PlanningReadRequest query, ReadContract<?> contract) {
                        PlanningReadGuard actual = context.guard().verify(head, query, contract);
                        if (fault == Fault.AFTER_GUARD && contract.operation().value().equals(CouncilPrivateCodec.STATUS)
                                && recorded.statusResponseProduced.get() && recorded.injected.compareAndSet(false, true))
                            throw new IllegalStateException("controlled failure after original Root STATUS after guard verification");
                        return actual;
                    }
                    @Override public <T> T withOriginalReadSource(WriterContracts.Head head, PlanningReadRequest query,
                            ReadContract<?> contract, Supplier<T> work) {
                        return context.guard().withOriginalReadSource(head, query, contract, work);
                    }
                    @Override public PlanningReadGuard verifyOriginalCurrent(WriterContracts.Head head,
                            PlanningReadRequest query, ReadContract<?> contract) {
                        return context.guard().verifyOriginalCurrent(head, query, contract);
                    }
                };
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve(name), false, scenario, decoration)) {
            actual.bindKnownReadObserver(new PlanningReadCoordinator.KnownReadObserver() {
                @Override public void afterKnown(ContinuityStorePort.Session same, ReadContract<?> contract, PlanningReadResult.Known<?> known) {
                    if (!Set.of(CouncilPrivateCodec.GATES, CouncilPrivateCodec.STATUS).contains(contract.operation().value())) return;
                    recorded.knownPrefix.add(known.receipt());
                    if (fault == Fault.KNOWN_CALLBACK && contract.operation().value().equals(CouncilPrivateCodec.STATUS)
                            && recorded.injected.compareAndSet(false, true))
                        throw new IllegalStateException("controlled actual archived terminal known-read observer failure");
                }
                @Override public void afterUnavailable(ContinuityStorePort.Session same, ReadContract<?> contract,
                        PlanningReadRequest query, PlanningReadResult.Unavailable<?> unavailable,
                        Optional<PlanningReadCoordinator.FailedReadAttempt> attempted) {
                    if (contract.operation().value().equals(CouncilPrivateCodec.STATUS)) recorded.statusUnavailable.set(unavailable);
                }
            });
            actual.command("terminal-failure-read-basis"); // Establishes the existing real planning source; it executes no action.
            PlanningRequest input = Objects.requireNonNull(actual.lastPublishedReady.get()); request.set(input);
            var port = new NativeCouncilReadPort(actual.reads, publicReads.get(), definitions.get(), actual.physicalInputs().transport(),
                    sessions(actual), actual.root.resolve("ROOT-CONTINUITY-WINDOW.lock").toAbsolutePath(), actual.archive,
                    Clock.systemUTC(), 4, "1.20.0.4", SHA);
            var captured = new AtomicReference<Scene>();
            actual.writer.locked(same -> actual.collector.current(same, input.before(), input.deadline(), lease -> {
                assertEquals(input.before(), lease.frame().identity());
                int before = actual.nativeReadWrites();
                Read<CouncilSelection.Query> result = port.readPrivate(input, CouncilSelection.Position.STEWARD);
                captured.set(new Scene(actual, input, result, recorded, before));
                return null;
            }));
            check.run(Objects.requireNonNull(captured.get()));
        }
    }

    private static void requireWireAndNoActions(Scene scene) {
        assertEquals(2, scene.actual().scenarioReadWrites(), "one QUERY and its one STATUS, without native requeue");
        assertEquals(scene.writesBefore() + 2, scene.actual().nativeReadWrites(), "failed callback must not issue another physical query");
        assertEquals(0, scene.actual().nativeActionWrites());
        var initial = scene.recorded().knownPrefix.getFirst();
        assertEquals(CouncilPrivateCodec.GATES, initial.request().operation().value());
        assertInstanceOf(CouncilPrivateCodec.Pending.class, CouncilPrivateCodec.decodeReply(
                initial.original().originalResultToken().orElseThrow().bytes(), CouncilPrivateCodec.GATES));
    }
    private static void requireUnavailableWithOriginalAckAndNoCredit(Scene scene) throws Exception {
        var unavailable = assertInstanceOf(Unavailable.class, scene.result());
        assertTrue(unavailable.councilTechnicalReadFailure().isEmpty(), "Java after/callback failure is not verified technical READ cadence");
        var status = Objects.requireNonNull(scene.recorded().statusUnavailable.get());
        assertTrue(status.observedFailure().isEmpty(), "failed after or known callback cannot mint a verified failed-read after");
        assertTrue(status.decodeFailure().isEmpty(), "no decoder error may be invented from an after/callback exception");
        var original = assertInstanceOf(NativeActionPort.AckReceived.class, status.original().orElseThrow());
        assertTrue(original.nativeOk());
        assertArrayEquals(scene.recorded().statusToken.get().bytes(), original.originalResultToken().orElseThrow().bytes());
        original.custody().orElseThrow().verify(original);
        var outbound = NativeWire.decodeExecuteRequest(original.outbound().orElseThrow().originalPacket());
        assertEquals(CouncilPrivateCodec.STATUS, outbound.step());
        assertEquals(original.requestId(), outbound.requestId());
        assertTrue(outbound.expectedRevision().isEmpty());
        assertTrue(outbound.expectedSnapshotRevision().isEmpty());
        scene.actual().writer.locked(same -> scene.actual().archive.inSession(same, bound -> {
            assertEquals(original, bound.load(bound.referenceOf(original)));
            return null;
        }));
        requireWireAndNoActions(scene);
    }
    private static void requireBoundOriginalTerminal(Scene scene) {
        var terminal = assertInstanceOf(CouncilPrivateCodec.Terminal.class, CouncilPrivateCodec.decodeReply(
                scene.recorded().statusToken.get().bytes(), CouncilPrivateCodec.STATUS));
        CouncilPrivateCodec.requireTerminalBinding(terminal, CouncilPrivateCodec.GATES,
                PrivateCouncilReads.nativeFrame(scene.recorded().knownPrefix.getFirst().request()));
    }
    private static void requireClosed(Scene scene) {
        var mailbox = scene.actual().physicalInputs().transport().mailboxDiagnostics();
        assertFalse(mailbox.scopeHeld());
        assertTrue(mailbox.poison().isEmpty(), "only the proven consumed terminal closes transport custody; the read remains unavailable when Java failed");
        assertTrue(mailbox.unresolvedRequestIds().isEmpty());
        assertTrue(scene.actual().physicalInputs().transport().deferredMailboxRead().isEmpty(), "terminal closure is not optional technical deferral");
    }
    private static void requireUnresolved(Scene scene) {
        var mailbox = scene.actual().physicalInputs().transport().mailboxDiagnostics();
        assertFalse(mailbox.scopeHeld());
        assertTrue(mailbox.poison().isPresent());
        assertEquals(List.of(scene.recorded().knownPrefix.getFirst().requestId(),
                scene.recorded().statusUnavailable.get().original().orElseThrow().requestId()), mailbox.unresolvedRequestIds());
        assertTrue(scene.actual().physicalInputs().transport().deferredMailboxRead().isEmpty());
    }
    private static RawJson pending(String step) {
        return new RawJson(StrictJson.canonical(StrictJson.object().put("private_council_transport", true)
                .put("advertised", false).put("step", step).put("status", "pending")));
    }
    private static RawJson projectedTerminal(ObjectNode original, PlanningRequest request, Shape shape) {
        ObjectNode value = original.deepCopy();
        var frame = request.before().frame().identity();
        value.put("snapshot_revision", shape == Shape.WRONG_NATIVE_FRAME ? frame.nativeRevision().add(BigInteger.ONE) : frame.nativeRevision());
        ObjectNode gates = (ObjectNode) value.get("council_final_gates");
        ObjectNode candidates = (ObjectNode) gates.get("council_composition_candidates");
        ObjectNode snapshot = (ObjectNode) candidates.get("snapshot");
        snapshot.put("snapshot_id", "native:" + frame.nativeRevision()).put("public_revision", frame.nativeRevision())
                .put("native_revision", frame.nativeRevision()).put("date_raw", frame.dateRaw()).put("paused", true);
        candidates.put("owner_character_id", frame.player());
        ObjectNode position = (ObjectNode) candidates.get("position");
        ((ObjectNode) position.get("current_task_owner_domain_tax_mult_v1")).put("owner_character_id", frame.player());
        return new RawJson(StrictJson.canonical(value));
    }
    private static ObjectNode originalTerminalToken() throws Exception {
        String configured = System.getProperty("xar.restore117.terminal.token");
        if (configured == null || configured.isBlank())
            throw new IllegalStateException("NOT EXECUTED: mandatory original DATA property xar.restore117.terminal.token");
        Path path = Path.of(configured);
        if (!path.isAbsolute()) throw new IllegalArgumentException("absolute original terminal token path required");
        byte[] original = Files.readAllBytes(path);
        assertEquals(8506, original.length);
        assertEquals(TERMINAL_SHA, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)));
        assertInstanceOf(CouncilPrivateCodec.Terminal.class, CouncilPrivateCodec.decodeReply(original, CouncilPrivateCodec.STATUS));
        return assertInstanceOf(ObjectNode.class, StrictJson.parse(original));
    }
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
}