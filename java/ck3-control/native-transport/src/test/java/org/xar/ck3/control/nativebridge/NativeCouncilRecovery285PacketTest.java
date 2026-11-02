package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.council.*;
import org.xar.ck3.control.application.action.council.CouncilContinuationModel.Request;
import org.xar.ck3.control.application.action.council.CouncilContinuationModel.Scope;
import org.xar.ck3.control.application.action.council.CouncilContinuationModel.Stage;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.capabilities.governance.CouncilContinuationPolicy;

/**
 * Native packet unit witness. Private test reflection supplies a controlled issuer and canonical
 * DATA, not actual Root authority, physical writer custody or real durable ISSUE qualification.
 * The actual Coordinator.requireCurrent, permit.consumeOnce, wire, chronology and transport run.
 * Historical artifacts are exact named inputs; no live pipe, Game, network, Win32 or JNA is used.
 */
@EnabledIfSystemProperty(named = "xar.council285.fixture.root", matches = ".+")
final class NativeCouncilRecovery285PacketTest {
    @TempDir Path temporary;
    private static final String ASSIGN = "private-assign-councillor-v1";
    private static final String STATUS = "private-council-application-main-status-v1";
    private static final String RECEIPT = "private-query-assign-councillor-receipt-v1";
    private static final String RECEIPT_FILE = "ef6a4ed4e213d27b36deb98db3432ace901a0a9531c06f043fa669c74c492c1d.json";
    private static final String BUILD = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";

    @Test void historicalFramedAckAndNewConnectionProduceOnlyThreeNewReadPackets() throws Exception {
        try (Fixture f = new Fixture()) {
            assertEquals(BigInteger.valueOf(18), f.attempt.guard().connectionGeneration());
            assertEquals(BigInteger.valueOf(19), f.transport.awaitHello(f.until).connectionGeneration());
            assertNotEquals(f.ack.custody().orElseThrow().session(), f.transport.awaitHello(f.until));
            Instant originalDeadline = f.command.deadline();
            assertTrue(originalDeadline.isBefore(Instant.now()), "the old immutable deadline remains historical DATA");
            assertTrue(f.transport.originalOutboundPacket(f.attempt.requestId()).isEmpty());
            assertTrue(f.transport.originalRequestChronology(f.attempt.requestId()).isEmpty());
            CouncilContinuationPolicy.requireOriginalPending(f.command, f.attempt, f.ack);
            var noRole = f.issue(Stage.HELPER_STATUS, "cold285-no-role", () -> { }, false);
            assertThrows(IOException.class, () -> f.transport.continueRecoveredCouncil(noRole, noRole.preparedRequest(), f.until));
            assertEquals(0, f.port.writes.size());
            AtomicInteger consumed = new AtomicInteger();
            for (Stage stage : List.of(Stage.HELPER_STATUS, Stage.RECEIPT_QUERY, Stage.RECEIPT_STATUS)) {
                String id = "cold285-" + stage.name().toLowerCase(java.util.Locale.ROOT);
                var permit = f.issue(stage, id, consumed::incrementAndGet, true);
                var outcome = assertInstanceOf(NativeActionPort.AckReceived.class,
                        f.transport.continueRecoveredCouncil(permit, permit.preparedRequest(), f.until));
                assertTrue(permit.consumed());
                assertEquals(id, outcome.requestId());
                assertEquals(id, outcome.outbound().orElseThrow().requestId());
                byte[] packet = f.port.writes.getLast();
                assertArrayEquals(packet, outcome.outbound().orElseThrow().originalPacket());
                var wire = NativeWire.decodeExecuteRequest(packet);
                assertEquals(id, wire.requestId()); assertEquals(stage.step(), wire.step());
                assertTrue(NativeWire.object(NativeWire.parse(wire.normalizedAdditionalFields().value())).isEmpty());
                assertTrue(wire.expectedSnapshotRevision().isEmpty());
                assertEquals(stage == Stage.RECEIPT_QUERY ? Optional.of(BigInteger.valueOf(111)) : Optional.empty(), wire.expectedRevision());
                var framed = assertInstanceOf(NativeWire.CommandResult.class, NativeWire.decode(outcome.originalPacket()));
                assertEquals(id, framed.requestId()); assertTrue(framed.nativeOk());
                assertTrue(CouncilContinuationPolicy.isPending(CouncilContinuationPolicy.result(outcome), stage.step()));
                var current = f.transport.originalRequestChronology(id).orElseThrow();
                assertEquals(BigInteger.valueOf(19), current.session().connectionGeneration());
                assertNotEquals(f.ack.custody().orElseThrow().custodyEpoch(), current.custodyEpoch());
                assertTrue(current.writeEntered().order().compareTo(current.writeCompleted().order()) < 0);
                assertTrue(current.writeCompleted().order().compareTo(current.responseReceived().order()) < 0);
                assertEquals(0, f.transport.mailboxDiagnostics().unresolvedRequestIds().size());
            }
            assertEquals(3, f.port.writes.size()); assertEquals(3, consumed.get());
            for (byte[] packet : f.port.writes) assertNotEquals(ASSIGN, NativeWire.decodeExecuteRequest(packet).step());
            assertEquals(originalDeadline, f.command.deadline());
            assertFalse(f.transport.mailboxDiagnostics().scopeHeld());
            assertTrue(f.transport.mailboxDiagnostics().poison().isEmpty());
            assertTrue(f.transport.originalOutboundPacket(f.attempt.requestId()).isEmpty());
            assertTrue(f.transport.originalRequestChronology(f.attempt.requestId()).isEmpty());
            assertTrue(f.parent.state() instanceof ActionState.Unknown, "pending read ACKs never settle the historical action");
        }
    }

    @Test void realConsumeCallbackFencesOtherProducersAndUnknownPreventsNextRead() throws Exception {
        try (Fixture f = new Fixture()) {
            AtomicInteger callbacks = new AtomicInteger();
            var permit = f.issue(Stage.HELPER_STATUS, "cold285-loss", () -> {
                callbacks.incrementAndGet();
                assertEquals(0, f.port.writes.size(), "callback must execute before its actual write");
                assertThrows(IOException.class, () -> f.transport.startHandshake(f.until));
                assertThrows(IOException.class, () -> f.transport.withMailbox(f.until, ignored -> null));
                try {
                    var refused = assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class, f.transport.readCoreFrame(f.until));
                    assertTrue(refused.proof().reason().contains("ordinary Native dispatch"), refused.proof().reason());
                } catch (InterruptedException interrupted) { throw new AssertionError(interrupted); }
                assertEquals(0, f.port.writes.size());
            }, true);
            f.port.loseResponse = true;
            var unknown = assertInstanceOf(NativeActionPort.Unknown.class,
                    f.transport.continueRecoveredCouncil(permit, permit.preparedRequest(), f.until));
            assertEquals(1, callbacks.get()); assertTrue(permit.consumed());
            assertEquals(1, f.port.writes.size());
            assertArrayEquals(f.port.writes.getFirst(), unknown.originalRequestPacket());
            assertArrayEquals(f.port.writes.getFirst(), f.transport.originalOutboundPacket(permit.requestId()).orElseThrow().originalPacket());
            assertTrue(f.transport.originalRequestChronology(permit.requestId()).isEmpty(), "no response chronology is invented");
            var next = f.issue(Stage.RECEIPT_QUERY, "cold285-after-loss", callbacks::incrementAndGet, true);
            assertThrows(IOException.class, () -> f.transport.continueRecoveredCouncil(next, next.preparedRequest(), f.until));
            assertFalse(next.consumed()); assertEquals(1, callbacks.get()); assertEquals(1, f.port.writes.size());
            assertFalse(f.transport.mailboxDiagnostics().scopeHeld());
        }
    }

    private final class Fixture implements AutoCloseable {
        final Instant until = Instant.now().plusSeconds(30);
        final ActionCommand command;
        final ActionState.Attempt attempt;
        final NativeActionPort.AckReceived ack;
        final ActionReceipt parent;
        final Replay port;
        final NativeGameTransport transport;
        final GuardEvidence currentGuard;
        final CouncilContinuationCoordinator coordinator;
        final CouncilContinuationCoordinator.RecoveryOriginal original;
        final ThreadLocal<Object> active, recovered, action;
        final Object oldActive, oldRecovered, oldAction;
        boolean closed;

        Fixture() throws Exception {
            var receipt = assertInstanceOf(ObjectNode.class, StrictJson.parse(held(RECEIPT_FILE, "ef6a4ed4e213d27b36deb98db3432ace901a0a9531c06f043fa669c74c492c1d")));
            command = ActionCodec.decodeCommand(StrictJson.canonical(receipt.get("command")));
            var state = receipt.get("state"); var oldAttempt = state.get("attempt");
            var request = new NativeRequest(ASSIGN, Optional.empty(),
                    new RawJson(held("prepared-fields208.json", "025744f8bcab0886e487e917dd219d120b7444b45e785dce757006b1e7aa0f85")));
            attempt = new ActionState.Attempt(StrictJson.text(oldAttempt.get("request_id")),
                    Instant.parse(StrictJson.text(oldAttempt.get("submitted_at"))), ActionReceiptCodec.decodeGuard(oldAttempt.get("guard")), request);
            byte[] outbound = NativeWire.packet(held("outbound208-BODY.json", "2be8d221d0673c57b6bc1a6537b95b6034585b19f420fd466e46bd96965c604a"));
            var framed = assertInstanceOf(NativeWire.CommandResult.class,
                    NativeWire.decode(NativeWire.packet(held("ack-frame208.json", "9f0cba99a07840f04c328506767b9cedb893f0a1c88d50102947f9113a3e2780"))));
            var dispatch = StrictJson.parse(held("dispatch208.json", "2cbeb7fc35bed0439a0735b6b62efaf25d2006dfbbde6be733de718d74c32b75"));
            ack = new NativeActionPort.AckReceived(framed.requestId(), framed.nativeOk(),
                    framed.result().token().map(x -> new RawJson(x.value())), new RawJson(framed.payload().value()), framed.packet().value(),
                    Optional.of(new NativeActionPort.OutboundPacket(attempt.requestId(), outbound)),
                    Optional.of(NativeRequestChronologyCodec.decode(dispatch.get("custody"))));
            List<ExactRef> evidence = new ArrayList<>(); state.get("evidence").forEach(x -> evidence.add(ExactRef.fromJson(x)));
            parent = new ActionReceipt(receipt.get("version").intValue(), receipt.get("sequence").longValue(), command,
                    StrictJson.text(receipt.get("body_sha256")), new ActionState.Unknown(Optional.of(attempt), Optional.of(ack), StrictJson.text(state.get("reason")), evidence));
            assertEquals(ActionCodec.bodySha256(command), parent.bodySha256());
            var config = new NativePipeEndpoint.Config("\\\\.\\pipe\\offline-council285", command.origin().machineId(), command.origin().game(),
                    command.sessionId(), "fixture285", BUILD, "ck3-1.20.0.4-msvc-x64");
            ObjectNode hello = StrictJson.object().put("type", "hello").put("protocol_version", 1).put("pid", config.game().pid())
                    .put("connection_generation", 19).put("bridge_version", "fixture285").put("expected_ck3_sha256", BUILD)
                    .put("expected_ck3_version", "1.20.0.4").put("game_adapter_id", config.expectedAdapterId())
                    .put("game_adapter_status", "ready").put("ck3_build_match", true);
            hello.putArray("capabilities").add("game.state.snapshot").add("game.command.pause-map").add("game.query.core-frame.v1");
            ObjectNode snapshot = StrictJson.object().put("type", "state_snapshot").put("protocol_version", 1).put("snapshot_id", "cold285-current").put("revision", 111);
            snapshot.putObject("state").put("date_raw", command.before().frame().identity().dateRaw()).put("paused", true).put("map_ready", true)
                    .putObject("played_character").put("character_id", command.before().frame().identity().player()).put("alive", true);
            port = new Replay(NativeWire.packet(StrictJson.canonical(hello)), NativeWire.packet(StrictJson.canonical(snapshot)));
            transport = new NativeGameTransport(port, config, 16, 16);
            var observed = transport.observe(until);
            var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(command.before().frame().identity().player(),
                    BigInteger.valueOf(111), command.before().frame().identity().dateRaw()), observed.snapshotId(), BigInteger.valueOf(111), command.before().frame().episodeRunId());
            var origin = new ProposalLifecycle.ObservationIdentity(config.machineId(), config.game(), frame, command.before().observationVersion());
            currentGuard = new GuardEvidence(origin, command.source(), command.sessionId(), BigInteger.valueOf(19), command.operation(),
                    ref("controlled-current-native", observed.originalPacket()), ref("controlled-current-hello", transport.originalHello().packet().value()),
                    attempt.guard().authorityId(), Instant.now(), until);
            ExactRef record = ref("controlled-canonical-record", held(RECEIPT_FILE, "ef6a4ed4e213d27b36deb98db3432ace901a0a9531c06f043fa669c74c492c1d"));
            ObjectNode ledger = StrictJson.object().put("schema", "root.ck3.continuity-window/v1").put("machine_id", config.machineId())
                    .put("sequence", parent.sequence()).put("window_id", 1).put("start_date_raw", 0).put("target_date_raw", 24).put("target_days", 1)
                    .put("status", "repair_required").put("last_settled_cycles", 0).put("last_settled_date_raw", 0);
            ledger.set(WriterContracts.ACTION_LIFECYCLE_FIELD, record.toJson());
            var head = new WriterContracts.Head(ContinuityState.fromJson(ledger, config.machineId()), List.of(), List.of(), List.of(), false);
            Path lock = temporary.resolve("packet285.lock").toAbsolutePath();
            var same = fixtureProxy(ContinuityStorePort.Session.class, (proxy, method, args) -> switch (method.getName()) {
                case "requireWriter" -> { assertFalse(closed); assertEquals(lock, args[0]); yield null; }
                case "head" -> { assertFalse(closed); yield head; }
                default -> throw new UnsupportedOperationException("unused software Session method: " + method.getName());
            });
            var archive = fixtureProxy(ActionPorts.OutcomeArchive.class, (proxy, method, args) -> switch (method.getName()) {
                case "withSession" -> { assertSame(same, args[0]); yield proxy; }
                case "loadRecord" -> { assertEquals(record, args[0]); yield new ActionRecord(parent, Optional.empty()); }
                default -> throw new UnsupportedOperationException("unused software archive method: " + method.getName());
            });
            coordinator = new CouncilContinuationCoordinator(lock, List.of(command.source().sourceRef()), Clock.systemUTC());
            coordinator.bind(unused(ActionJournal.class), archive, unused(CouncilContinuationPorts.GuardPort.class),
                    unused(CouncilContinuationPorts.NativePort.class), unused(CouncilContinuationPorts.Policy.class));
            Constructor<CouncilContinuationCoordinator.RecoveryOriginal> constructor = CouncilContinuationCoordinator.RecoveryOriginal.class
                    .getDeclaredConstructor(CouncilContinuationCoordinator.class, ContinuityStorePort.Session.class, ActionReceipt.class,
                            ActionState.Attempt.class, NativeActionPort.AckReceived.class, Instant.class);
            constructor.setAccessible(true); original = constructor.newInstance(coordinator, same, parent, attempt, ack, until);
            field(CouncilContinuationCoordinator.RecoveryOriginal.class, "qualifiedGuard").set(original, currentGuard);
            active = threadLocal(coordinator, "active"); recovered = threadLocal(coordinator, "recovered"); action = threadLocal(null, ActionScope.class, "CURRENT");
            oldActive = active.get(); oldRecovered = recovered.get(); oldAction = action.get();
            active.set(same); recovered.set(original); action.set(command.actionId());
            try { original.requireCurrent(); }
            catch (IOException | RuntimeException | Error failure) {
                closed = true; restore(action, oldAction); restore(recovered, oldRecovered); restore(active, oldActive);
                try { transport.close(); } catch (IOException closeFailure) { failure.addSuppressed(closeFailure); }
                throw failure;
            }
        }

        CouncilContinuationPermit issue(Stage stage, String id, Runnable checkIssued, boolean recovery) throws Exception {
            var prepared = new NativeRequest(stage.step(), Optional.empty(), new RawJson(new byte[] {'{', '}'}));
            ExactRef data = command.source().sourceRef();
            var request = new Request(new Scope(command.actionId(), parent.bodySha256(), attempt.requestId()), id, stage,
                    data, data, currentGuard, Instant.now(), until, 1, List.of(data));
            var constructor = CouncilContinuationPermit.class.getDeclaredConstructor(Request.class, NativeRequest.class, Runnable.class, Clock.class, Optional.class);
            constructor.setAccessible(true);
            return constructor.newInstance(request, prepared, checkIssued, Clock.systemUTC(), recovery ? Optional.of(original) : Optional.empty());
        }
        @Override public void close() throws IOException {
            closed = true; restore(action, oldAction); restore(recovered, oldRecovered); restore(active, oldActive); transport.close();
        }
    }

    private static byte[] held(String name, String expectedSha) throws IOException {
        String root = System.getProperty("xar.council285.fixture.root"); assertNotNull(root, "explicit frozen original artifact root required");
        byte[] raw = Files.readAllBytes(Path.of(root).resolve(name)); assertEquals(expectedSha, ActionCodec.sha256(raw), name); return raw;
    }
    private static ExactRef ref(String name, byte[] raw) { return new ExactRef(name, raw.length, ActionCodec.sha256(raw)); }
    private static Field field(Class<?> owner, String name) throws ReflectiveOperationException { Field f = owner.getDeclaredField(name); f.setAccessible(true); return f; }
    @SuppressWarnings("unchecked") private static ThreadLocal<Object> threadLocal(Object owner, Class<?> type, String name) throws ReflectiveOperationException {
        return (ThreadLocal<Object>) field(type, name).get(owner);
    }
    private static ThreadLocal<Object> threadLocal(Object owner, String name) throws ReflectiveOperationException { return threadLocal(owner, owner.getClass(), name); }
    private static void restore(ThreadLocal<Object> local, Object prior) { if (prior == null) local.remove(); else local.set(prior); }
    private static <T> T fixtureProxy(Class<T> type, InvocationHandler handler) {
        return type.cast(Proxy.newProxyInstance(type.getClassLoader(), new Class<?>[] {type}, (proxy, method, args) -> {
            if (method.getDeclaringClass() == Object.class) return switch (method.getName()) {
                case "equals" -> proxy == args[0]; case "hashCode" -> System.identityHashCode(proxy); case "toString" -> "controlled-" + type.getSimpleName();
                default -> throw new UnsupportedOperationException(method.getName());
            };
            return handler.invoke(proxy, method, args);
        }));
    }
    private static <T> T unused(Class<T> type) { return fixtureProxy(type, (p, m, a) -> { throw new UnsupportedOperationException("unused fixture runtime method: " + m.getName()); }); }
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> incoming = new ArrayDeque<>(); final List<byte[]> writes = new ArrayList<>();
        boolean loseResponse;
        Replay(byte[] hello, byte[] snapshot) { incoming.add(hello.clone()); incoming.add(snapshot.clone()); }
        @Override public void verify() { }
        @Override public void awaitConnection(Instant deadline) { }
        @Override public byte[] readPacket(Instant deadline) throws IOException {
            if (loseResponse) { loseResponse = false; throw new IOException("controlled response lost after actual packet write"); }
            if (incoming.isEmpty()) throw new IOException("controlled packet input exhausted"); return incoming.removeFirst().clone();
        }
        @Override public void writePacket(byte[] packet, Instant deadline) throws IOException {
            writes.add(packet.clone()); var request = NativeWire.decodeExecuteRequest(packet);
            ObjectNode result = StrictJson.object().put("private_council_transport", true).put("advertised", false).put("step", request.step()).put("status", "pending");
            ObjectNode response = StrictJson.object().put("type", "command_result").put("protocol_version", 1).put("request_id", request.requestId()).put("ok", true);
            response.set("result", result); incoming.add(NativeWire.packet(StrictJson.canonical(response)));
        }
        @Override public void close() { incoming.clear(); }
    }
}
