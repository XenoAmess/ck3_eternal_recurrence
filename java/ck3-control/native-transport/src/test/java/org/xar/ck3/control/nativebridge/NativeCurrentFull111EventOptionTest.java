package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionState.Attempt;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.NativeActionPort.AckReceived;
import org.xar.ck3.control.application.action.NativeActionPort.OutboundPacket;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.NativeRequestChronology;
import org.xar.ck3.control.application.action.NativeRequestChronology.Event;
import org.xar.ck3.control.application.action.NativeRequestChronology.PacketIdentity;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.CurrentFull111EventOption.Action;
import org.xar.ck3.control.nativebridge.CurrentFull111EventOption.Lineage;
import org.xar.ck3.control.nativebridge.CurrentFull111EventOption.Request;
import org.xar.ck3.control.nativebridge.CurrentFull111EventOption.Status;
import org.xar.ck3.control.nativebridge.CurrentFull111EventOption.TargetState;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

final class NativeCurrentFull111EventOptionTest {
    private static final ExactCk3Build BUILD = ExactCk3Build.CK3_121003_STEAM_26785313_FULL111;
    private static final Instant EFFECT_DEADLINE = Instant.ofEpochMilli(1795777200000L);
    private static final Instant EFFECT_WRITE = EFFECT_DEADLINE.minusSeconds(1);
    private static final Instant QUEUE_WRITE = EFFECT_DEADLINE.plusSeconds(1);
    private static final BigInteger SOURCE_REVISION = BigInteger.valueOf(12);
    private static final BigInteger ACTOR = BigInteger.valueOf(-16777215);
    private static final BigInteger RAW_DATE = BigInteger.valueOf(53144328);
    private static final UUID SOFTWARE_EPOCH = new UUID(1, 2);
    private static final String MACHINE = "full111-option-software";
    private static final TransportSession SESSION = new TransportSession(MACHINE,
            new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), BigInteger.valueOf(21), "event-option-test");
    private static final ExactRef REF = new ExactRef("software-option-evidence", 1, "1".repeat(64));

    @Test
    void nativePrepareAndSelectRemainSeparateFromProofOfGameEffect() throws Exception {
        var prepared = CurrentFull111EventOption.decodeOutcome(ack("v2-prepare-result", "v2-prepare-request",
                SOFTWARE_EPOCH, 1, EFFECT_WRITE.minusMillis(200)));
        var dispatch = effect();
        var selected = CurrentFull111EventOption.decodeOutcome(dispatch);
        assertEquals(Status.AVAILABLE, prepared.status());
        assertEquals(Status.SELECTION_DISPATCHED, selected.status());
        assertFalse(prepared.effectAttempted());
        assertTrue(selected.effectAttempted());
        assertTrue(selected.nativeReturned());
        assertTrue(prepared.queue().isEmpty());
        assertTrue(selected.queue().isEmpty());

        var quote = prepared.lineage().orElseThrow();
        var unprepared = new Lineage(quote.sourceRevision(), quote.rendererRequestId(), quote.rendererProviderGeneration(),
                quote.rendererQuerySequence(), Optional.empty(), BigInteger.ZERO, Optional.empty(), BigInteger.ZERO);
        var prepare = new Request(Action.PREPARE, new CoreFrame.Partial(BUILD, prepared.factsBefore().orElseThrow()),
                prepared.target().orElseThrow(), unprepared, EFFECT_DEADLINE);
        assertTrue(prepared.matchesSuccessfulRequest(prepare));
        assertSameWire(prepare.readPacket("event-prepare-v2"), "v2-prepare-request");

        var selection = Request.decodeSelectionRequest(selectionRequest());
        assertEquals(EFFECT_DEADLINE, selection.deadline());
        assertEquals(4, selection.target().authoredOptionIndex());
        assertEquals(quote, selection.lineage());
        assertTrue(selected.matchesSuccessfulRequest(selection));
        assertEquals(Optional.of(Action.SELECT.capability()), selection.selectionRequest().requiredCapability());
        assertThrows(IllegalArgumentException.class, () -> selection.readPacket(dispatch.requestId()));
    }

    @Test
    void onlyCompleteLaterQueueConfirmsAbsentAndKeepsTheOriginalDeadline() throws Exception {
        var dispatch = effect();
        var attempt = attempt(dispatch, SOURCE_REVISION, ACTOR);
        var absent = queue("v2-queue-absent", SOFTWARE_EPOCH, 10, QUEUE_WRITE);
        var query = Request.decodeQueueRequest(absent);
        assertSameWire(query.readPacket(absent.requestId()), "v2-queue-request");
        assertEquals(EFFECT_DEADLINE.plusSeconds(10), query.deadline());
        assertEquals(EFFECT_DEADLINE, Request.decodeSelectionRequest(attempt.preparedRequest()).deadline());
        assertEquals(List.of(), CurrentFull111EventOption.decodeOutcome(absent).queue().orElseThrow().instanceIds());
        assertTrue(CurrentFull111EventOption.confirmsAbsence(attempt, dispatch, query, absent));

        var present = queue("v2-queue-present", SOFTWARE_EPOCH, 10, QUEUE_WRITE);
        var retained = CurrentFull111EventOption.decodeOutcome(present).queue().orElseThrow();
        assertEquals(List.of(8, 7), retained.instanceIds());
        assertEquals(TargetState.PRESENT, retained.targetState());
        assertFalse(CurrentFull111EventOption.confirmsAbsence(attempt, dispatch, query, present));

        var unavailable = queue("v2-queue-unavailable", SOFTWARE_EPOCH, 10, QUEUE_WRITE);
        assertTrue(CurrentFull111EventOption.decodeOutcome(unavailable).queue().isEmpty());
        assertFalse(CurrentFull111EventOption.confirmsAbsence(attempt, dispatch, query, unavailable));
    }

    @Test
    void absentQueueCannotCrossTheOriginalActorRevisionOrEndpointCustody() throws Exception {
        var dispatch = effect();
        var attempt = attempt(dispatch, SOURCE_REVISION, ACTOR);
        var absent = queue("v2-queue-absent", SOFTWARE_EPOCH, 10, QUEUE_WRITE);
        var query = Request.decodeQueueRequest(absent);
        assertFalse(CurrentFull111EventOption.confirmsAbsence(attempt(dispatch, BigInteger.valueOf(13), ACTOR), dispatch, query, absent));
        assertFalse(CurrentFull111EventOption.confirmsAbsence(attempt(dispatch, SOURCE_REVISION, BigInteger.valueOf(77)), dispatch, query, absent));
        assertFalse(CurrentFull111EventOption.confirmsAbsence(attempt, dispatch, query,
                queue("v2-queue-absent", new UUID(2, 3), 10, QUEUE_WRITE)));
        assertFalse(CurrentFull111EventOption.confirmsAbsence(attempt, dispatch, query,
                queue("v2-queue-absent", SOFTWARE_EPOCH, 6, EFFECT_WRITE)));
        assertFalse(CurrentFull111EventOption.confirmsAbsence(attempt, dispatch, query,
                queue("v2-queue-absent", SOFTWARE_EPOCH, 10, query.deadline())));
        var altered = ack("v2-queue-absent", "v2-prepare-request", SOFTWARE_EPOCH, 10, QUEUE_WRITE);
        assertThrows(IOException.class, () -> Request.decodeQueueRequest(altered));
        assertFalse(CurrentFull111EventOption.confirmsAbsence(attempt, dispatch, query, altered));
    }

    @Test
    void originalSelectionCanBeReadConfirmedWhileTheAcceptedRawIsStillTheBeforeRevision() throws Exception {
        var dispatch = effect();
        var attempt = attempt(dispatch, SOURCE_REVISION, ACTOR);
        var custody = dispatch.custody().orElseThrow();
        var outbound = dispatch.outbound().orElseThrow();
        var selection = NativeGameTransport.readFull111SelectionOriginal(attempt, dispatch, outbound, custody,
                raw(SESSION, 12, "native:12", ACTOR, RAW_DATE, true)).orElseThrow();
        assertEquals(Status.SELECTION_DISPATCHED, selection.result().status());
        assertEquals(EFFECT_DEADLINE, selection.request().deadline());
        assertTrue(selection.result().queue().isEmpty());
        assertTrue(NativeGameTransport.readFull111SelectionOriginal(attempt, dispatch, outbound, custody,
                raw(SESSION, 13, "native:13", ACTOR, RAW_DATE, true)).isPresent());
    }

    @Test
    void originalSelectionRejectsAChangedRawOrAnUnretainedAck() throws Exception {
        var dispatch = effect();
        var attempt = attempt(dispatch, SOURCE_REVISION, ACTOR);
        var custody = dispatch.custody().orElseThrow();
        var outbound = dispatch.outbound().orElseThrow();
        var current = raw(SESSION, 12, "native:12", ACTOR, RAW_DATE, true);
        var other = new TransportSession(MACHINE, SESSION.game(), BigInteger.valueOf(22), SESSION.sessionId());
        var foreignEpoch = new NativeRequestChronology(SESSION, new UUID(2, 3), custody.requestId(),
                custody.originalRequest(), custody.originalResponse(), custody.writeEntered(),
                custody.writeCompleted(), custody.responseReceived());
        for (var wrong : List.of(raw(SESSION, 11, "native:11", ACTOR, RAW_DATE, true),
                raw(SESSION, 12, "wrong-native:12", ACTOR, RAW_DATE, true),
                raw(SESSION, 13, "native:13", BigInteger.valueOf(88), RAW_DATE, true),
                raw(SESSION, 13, "native:13", ACTOR, RAW_DATE.add(BigInteger.valueOf(24)), true),
                raw(SESSION, 13, "native:13", ACTOR, RAW_DATE, false), raw(other, 13, "native:13", ACTOR, RAW_DATE, true))) {
            assertTrue(NativeGameTransport.readFull111SelectionOriginal(attempt, dispatch, outbound, custody, wrong).isEmpty());
        }
        assertThrows(IllegalArgumentException.class,
                () -> NativeGameTransport.readFull111SelectionOriginal(attempt, dispatch, outbound, foreignEpoch, current));
        var wrongOutbound = new OutboundPacket(dispatch.requestId(), NativeWire.packet(load("v2-prepare-request")));
        assertTrue(NativeGameTransport.readFull111SelectionOriginal(attempt, dispatch, wrongOutbound, custody, current).isEmpty());
        var negativePacket = NativeWire.packet(load("v2-queue-unavailable"));
        var altered = new AckReceived(dispatch.requestId(), true, dispatch.originalResultToken(), dispatch.originalFrame(),
                negativePacket, dispatch.outbound(), dispatch.custody());
        assertTrue(NativeGameTransport.readFull111SelectionOriginal(attempt, altered, outbound, custody, current).isEmpty());
        var staleAttempt = new Attempt(attempt.requestId(), EFFECT_WRITE.plusMillis(1), attempt.guard(), attempt.preparedRequest());
        assertTrue(NativeGameTransport.readFull111SelectionOriginal(staleAttempt, dispatch, outbound, custody, current).isEmpty());
    }

    @Test
    void aDifferentHeldReceiverUsesNoIoToRejectAnArchivedSelection() throws Exception {
        var original = effect();
        var attempt = attempt(original, SOURCE_REVISION, ACTOR);
        var hello = StrictJson.object().put("type", "hello").put("protocol_version", 1).put("pid", SESSION.game().pid())
                .put("connection_generation", SESSION.connectionGeneration()).put("bridge_version", "option-test")
                .put("expected_ck3_version", BUILD.version()).put("expected_ck3_sha256", BUILD.executableSha256())
                .put("game_adapter_id", BUILD.coreFrameAdapterId()).put("game_adapter_status", "ready").put("ck3_build_match", true);
        hello.putArray("capabilities").add(Action.QUERY_QUEUE.capability());
        var endpoint = new HelloOnlyPort(NativeWire.packet(StrictJson.canonical(hello)));
        String slash = Character.toString(92);
        var config = new NativePipeEndpoint.Config(slash + slash + "." + slash + "pipe" + slash + "option-test",
                MACHINE, SESSION.game(),
                SESSION.sessionId(), "option-test", BUILD.executableSha256(), BUILD.coreFrameAdapterId());
        var until = Instant.now().plusSeconds(10);
        try (var actual = new NativeGameTransport(endpoint, config, 4, 4)) {
            assertEquals(SESSION, actual.awaitHello(until));
            assertEquals(1, endpoint.reads);
            int verifies = endpoint.verifies;
            assertFalse(actual.canConfirmFull111EventSelection(attempt, original));
            assertTrue(actual.readFull111EventQueue(attempt, original, until).isEmpty());
            assertEquals(1, endpoint.reads);
            assertEquals(verifies, endpoint.verifies);
        }
    }

    private static ObservedFrame raw(TransportSession session, long revision, String snapshot, BigInteger actor,
            BigInteger date, boolean paused) {
        var body = StrictJson.object().put("date_raw", date).put("paused", paused).put("map_ready", true);
        body.putObject("played_character").put("character_id", actor).put("alive", true);
        return new ObservedFrame(session, snapshot, BigInteger.valueOf(revision), new RawJson(StrictJson.canonical(body)),
                new byte[]{1}, EFFECT_WRITE.minusMillis(20));
    }

    private static final class HelloOnlyPort implements NativePacketPort {
        private final byte[] hello;
        private int reads;
        private int verifies;
        private HelloOnlyPort(byte[] hello) { this.hello = hello; }
        @Override public void verify() { verifies++; }
        @Override public void awaitConnection(Instant deadline) { }
        @Override public byte[] readPacket(Instant deadline) {
            assertEquals(0, reads++, "no new read is authorized");
            return hello.clone();
        }
        @Override public void writePacket(byte[] packet, Instant deadline) { throw new AssertionError("no write is authorized"); }
        @Override public void close() { }
    }

    private static Attempt attempt(AckReceived dispatch, BigInteger revision, BigInteger actor) throws IOException {
        var before = new ObservationIdentity(MACHINE, SESSION.game(), new ProposalFrame(
                new Frame(actor, revision, RAW_DATE), "native:" + revision, BigInteger.ONE, "full111-option-data"), 1);
        var source = new G2Source(MACHINE, EFFECT_WRITE.minusMillis(10).toString(), BUILD.executableSha256(), REF);
        var guard = new GuardEvidence(before, source, SESSION.sessionId(), SESSION.connectionGeneration(),
                new OperationKey(Action.SELECT.step()), REF, REF, "test-guard", EFFECT_WRITE.minusMillis(10), EFFECT_DEADLINE);
        return new Attempt(dispatch.requestId(), EFFECT_WRITE.minusMillis(1), guard, selectionRequest());
    }

    private static NativeRequest selectionRequest() throws IOException {
        var request = NativeWire.decodeExecuteRequest(NativeWire.packet(load("v2-select-request")));
        assertEquals(Optional.of(SOURCE_REVISION), request.expectedRevision());
        return new NativeRequest(request.step(), Action.SELECT.capability(), new RawJson(request.normalizedAdditionalFields().value()));
    }

    private static AckReceived effect() throws IOException {
        return ack("v2-select-result", "v2-select-request", SOFTWARE_EPOCH, 6, EFFECT_WRITE);
    }

    private static AckReceived queue(String reply, UUID epoch, long order, Instant written) throws IOException {
        return ack(reply, "v2-queue-request", epoch, order, written);
    }

    /** Native C++ fixture generated the complete request/ACK DATA. The endpoint chronology models a software test. */
    private static AckReceived ack(String reply, String request, UUID epoch, long order, Instant written) throws IOException {
        byte[] payload = load(reply);
        byte[] response = NativeWire.packet(payload);
        byte[] outbound = NativeWire.packet(load(request));
        var decoded = assertInstanceOf(NativeWire.CommandResult.class, NativeWire.decode(response));
        var id = decoded.requestId();
        var custody = new NativeRequestChronology(SESSION, epoch, id, PacketIdentity.of(outbound), PacketIdentity.of(response),
                new Event(BigInteger.valueOf(order), written), new Event(BigInteger.valueOf(order + 1), written.plusMillis(1)),
                new Event(BigInteger.valueOf(order + 2), written.plusMillis(2)));
        return new AckReceived(id, decoded.nativeOk(), decoded.result().token().map(value -> new RawJson(value.value())),
                new RawJson(payload), response, Optional.of(new OutboundPacket(id, outbound)), Optional.of(custody));
    }

    private static void assertSameWire(byte[] javaPacket, String nativeRequest) throws IOException {
        var javaWire = NativeWire.decodeExecuteRequest(javaPacket);
        var nativeWire = NativeWire.decodeExecuteRequest(NativeWire.packet(load(nativeRequest)));
        assertEquals(javaWire.requestId(), nativeWire.requestId());
        assertEquals(javaWire.step(), nativeWire.step());
        assertEquals(javaWire.expectedRevision(), nativeWire.expectedRevision());
        var javaBody = NativeWire.parse(javaWire.normalizedAdditionalFields().value());
        var nativeBody = NativeWire.parse(nativeWire.normalizedAdditionalFields().value());
        var nativeEvent = NativeWire.object(nativeBody.get("ordinary_event"));
        nativeEvent.put("executable_sha256", nativeEvent.get("executable_sha256").textValue().toLowerCase(Locale.ROOT));
        assertArrayEquals(StrictJson.canonical(javaBody), StrictJson.canonical(nativeBody));
    }

    private static byte[] load(String file) throws IOException {
        try (var input = NativeCurrentFull111EventOptionTest.class.getResourceAsStream("/current267-full111-event-option-cpp/" + file + ".json")) {
            assertNotNull(input, file);
            return input.readAllBytes();
        }
    }
}
