package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Typed original packet custody -> strict durable codec -> sampling validation. No native/Game authority. */
final class NativeRequestChronologyTest {
    private static final Instant T = Instant.parse("2026-10-24T00:00:00Z");
    private static final UUID EPOCH = UUID.fromString("cf539187-7770-46fc-b99d-a9e12285a067");
    private static final BigInteger GENERATION = new BigInteger("18446744073709551615");
    private static final GameGeneration GAME = new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001")));
    private static final NativeObservationPort.TransportSession SESSION = new NativeObservationPort.TransportSession("chronology-fixture", GAME, GENERATION, "held-session");
    private static final OperationKey QUERY = new OperationKey("query-army-sampling-state-v1"), ACTION = new OperationKey("sample-army-position-v1");
    private static ExactRef ref(String name, char hash) { return new ExactRef("D:/chronology-fixture/" + name, 10, String.valueOf(hash).repeat(64)); }
    private static final G2Source SOURCE = new G2Source(SESSION.machineId(), T.toString(), "1.20.0.4", ref("source.java", 'a'));
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static byte[] packet(String value) {
        byte[] raw = bytes(value); return ByteBuffer.allocate(raw.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(raw.length).put(raw).array();
    }
    private static GuardEvidence guard(OperationKey operation) {
        var identity = new FrontendIdentity(SESSION.machineId(), GAME, SESSION.sessionId(), GENERATION, 123,
                new FrontendFrame.Menu(BigInteger.ONE), ref("unchanged-old-native.packet", 'b'), ref("hello.packet", 'c'));
        return new GuardEvidence(new CommandOrigin.Frontend(identity), SOURCE, SESSION.sessionId(), GENERATION, operation,
                identity.nativeEvidence(), identity.capabilityEvidence(), "held-source-authority", T.minusSeconds(60), T.plusSeconds(60), List.of(ref("actual-source-proof.json", 'd')));
    }
    private static NativeActionPort.AckReceived ack(String requestId, long order, Instant entered) {
        String outgoing = "{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":\"" + requestId
                + "\",\"step\":\"query-army-sampling-state-v1\",\"expected_revision\":0}";
        String incoming = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"" + requestId
                + "\",\"ok\":true,\"result\":{\"status\":\"available\"}}";
        byte[] outbound = packet(outgoing), inbound = packet(incoming);
        var chronology = new NativeRequestChronology(SESSION, EPOCH, requestId, NativeRequestChronology.PacketIdentity.of(outbound),
                NativeRequestChronology.PacketIdentity.of(inbound), new NativeRequestChronology.Event(BigInteger.valueOf(order), entered),
                new NativeRequestChronology.Event(BigInteger.valueOf(order + 1), entered.plusMillis(1)),
                new NativeRequestChronology.Event(BigInteger.valueOf(order + 2), entered.plusMillis(2)));
        return new NativeActionPort.AckReceived(requestId, true, Optional.of(new RawJson(bytes("{\"status\":\"available\"}"))),
                new RawJson(bytes(incoming)), inbound, Optional.of(new NativeActionPort.OutboundPacket(requestId, outbound)), Optional.of(chronology));
    }
    private static NativeActionPort.AckReceived with(NativeActionPort.AckReceived value, Optional<NativeRequestChronology> chronology) {
        return new NativeActionPort.AckReceived(value.requestId(), value.nativeOk(), value.originalResultToken(), value.originalFrame(), value.originalPacket(), value.outbound(), chronology);
    }
    private static ActionState.Attempt attempt(String requestId) {
        return new ActionState.Attempt(requestId, T, guard(ACTION), new NativeRequest(ACTION.value(),
                "game.command." + ACTION.value(), new RawJson(bytes("{}"))));
    }
    private static PlanningReadReceipt read(NativeActionPort.AckReceived response) {
        GuardEvidence guard = guard(QUERY);
        var request = new PlanningReadRequest(guard.origin(), SOURCE, SESSION.sessionId(), QUERY, new OpportunityJson.Obj(Map.of()), T.plusSeconds(30));
        var readGuard = new PlanningReadGuard(guard, "e".repeat(64));
        return new PlanningReadReceipt(request, "actual-sampling/v1", response.requestId(), readGuard, readGuard, response);
    }
    @Test void anActualNewQueryAfterTheAckWorksWithAnUnchangedOlderSemanticGuard() {
        var attempt = attempt("submitted"); var submitted = ack(attempt.requestId(), 4, T.plusMillis(1));
        var query = read(ack("independent-query", 7, T.plusMillis(4)));
        assertTrue(query.before().binding().observedAt().isBefore(attempt.submittedAt()));
        assertDoesNotThrow(() -> NativeRequestChronology.requireSampledAfter(query, attempt, submitted));
        assertEquals(T.minusSeconds(60), query.before().binding().observedAt());
        assertEquals(query.before().binding().nativeEvidence(), query.after().binding().nativeEvidence());
    }
    @Test void beforeOrConcurrentQueryAndRegressedGlobalClockCannotBeRelabeledAsPostSampling() {
        var attempt = attempt("submitted"); var submitted = ack(attempt.requestId(), 4, T.plusMillis(1));
        assertThrows(IllegalArgumentException.class, () -> NativeRequestChronology.requireSampledAfter(read(ack("earlier", 1, T.minusMillis(5))), attempt, submitted));
        assertThrows(IllegalArgumentException.class, () -> NativeRequestChronology.requireSampledAfter(read(ack("same-order", 6, T.plusMillis(4))), attempt, submitted));
        assertThrows(IllegalArgumentException.class, () -> NativeRequestChronology.requireSampledAfter(read(ack("clock-went-back", 7, T)), attempt, submitted));
        assertThrows(IllegalArgumentException.class, () -> NativeRequestChronology.requireSampledAfter(read(ack("submitted", 7, T.plusMillis(4))), attempt, submitted));
    }
    @Test void missingActualWriteCompletionOrHistoricalAckNeverInventsQueryFreshness() {
        var attempt = attempt("submitted"); var submitted = ack(attempt.requestId(), 4, T.plusMillis(1)); var query = ack("independent-query", 7, T.plusMillis(4));
        var historicalQuery = new NativeActionPort.AckReceived(query.requestId(), query.nativeOk(), query.originalResultToken(), query.originalFrame(), query.originalPacket(), query.outbound());
        assertThrows(IllegalArgumentException.class, () -> NativeRequestChronology.requireSampledAfter(read(historicalQuery), attempt, submitted));
        assertThrows(IllegalArgumentException.class, () -> NativeRequestChronology.requireSampledAfter(read(query), attempt, with(submitted, Optional.empty())));
        var chronology = query.custody().orElseThrow();
        assertThrows(IllegalArgumentException.class, () -> new NativeRequestChronology(chronology.session(), chronology.custodyEpoch(), chronology.requestId(), chronology.originalRequest(),
                chronology.originalResponse(), chronology.writeEntered(), chronology.writeEntered(), chronology.responseReceived()));
    }
    @Test void exactOriginalOutboundInboundAndHeldConnectionAreRequiredAfterColdDecode() {
        var attempt = attempt("submitted"); var submitted = ack(attempt.requestId(), 4, T.plusMillis(1)); var query = ack("independent-query", 7, T.plusMillis(4));
        var chronology = NativeRequestChronologyCodec.decode(NativeRequestChronologyCodec.encode(query.custody().orElseThrow()));
        var restored = with(query, Optional.of(chronology)); assertDoesNotThrow(() -> NativeRequestChronology.requireSampledAfter(read(restored), attempt, submitted));
        byte[] changedPacket = query.originalPacket(); changedPacket[changedPacket.length - 1] ^= 1;
        var changed = new NativeActionPort.AckReceived(query.requestId(), true, query.originalResultToken(), query.originalFrame(), changedPacket, query.outbound(), Optional.of(chronology));
        assertThrows(IllegalArgumentException.class, () -> chronology.verify(changed));
        var otherSession = new NativeObservationPort.TransportSession(SESSION.machineId(), GAME, BigInteger.TWO, SESSION.sessionId());
        var crossed = new NativeRequestChronology(otherSession, chronology.custodyEpoch(), chronology.requestId(), chronology.originalRequest(), chronology.originalResponse(),
                chronology.writeEntered(), chronology.writeCompleted(), chronology.responseReceived());
        assertThrows(IllegalArgumentException.class, () -> NativeRequestChronology.requireSampledAfter(read(with(query, Optional.of(crossed))), attempt, submitted));
    }
    @Test void initialStatusMustReallyPrecedeTheOriginalWriteAndRemainsIndependent() {
        var attempt = attempt("submitted"); var submitted = ack(attempt.requestId(), 4, T.plusMillis(1));
        var initial = read(ack("actual-before-status", 1, T.minusMillis(3)));
        assertDoesNotThrow(() -> NativeRequestChronology.requireBeforeSubmission(initial, attempt, submitted));
        assertThrows(IllegalArgumentException.class, () -> NativeRequestChronology.requireBeforeSubmission(read(ack("late-status", 7, T.plusMillis(4))), attempt, submitted));
        var rejected = new NativeActionPort.AckReceived(submitted.requestId(), false, submitted.originalResultToken(), submitted.originalFrame(), submitted.originalPacket(),
                submitted.outbound(), submitted.custody());
        assertThrows(IllegalArgumentException.class, () -> NativeRequestChronology.requireSampledAfter(read(ack("post-rejected", 7, T.plusMillis(4))), attempt, rejected));
    }
    @Test void aNewLocalTransportCounterEpochCannotBorrowAnOldAckEvenWithTheSameNativeSessionAndLaterTime() {
        var attempt = attempt("submitted"); var submitted = ack(attempt.requestId(), 4, T.plusMillis(1)); var query = ack("independent-query", 70, T.plusMillis(4));
        var original = query.custody().orElseThrow();
        var otherEpoch = new NativeRequestChronology(original.session(), UUID.fromString("291afee4-9873-41a3-a8d5-1c2b3164f7b0"), original.requestId(),
                original.originalRequest(), original.originalResponse(), original.writeEntered(), original.writeCompleted(), original.responseReceived());
        assertEquals(original.session(), otherEpoch.session()); assertTrue(otherEpoch.writeEntered().order().compareTo(submitted.custody().orElseThrow().responseReceived().order()) > 0);
        assertThrows(IllegalArgumentException.class, () -> NativeRequestChronology.requireSampledAfter(read(with(query, Optional.of(otherEpoch))), attempt, submitted));
        var restoredSubmission = with(submitted, Optional.of(NativeRequestChronologyCodec.decode(NativeRequestChronologyCodec.encode(submitted.custody().orElseThrow()))));
        var restoredQuery = with(query, Optional.of(NativeRequestChronologyCodec.decode(NativeRequestChronologyCodec.encode(original))));
        assertDoesNotThrow(() -> NativeRequestChronology.requireSampledAfter(read(restoredQuery), attempt, restoredSubmission));
    }
    @Test void actualQueryTimesMustStillFitTheOriginalGuardAndRequestDeadline() {
        var query = ack("independent-query", 7, T.plusMillis(4)); PlanningReadReceipt original = read(query);
        var deadline = new PlanningReadRequest(original.request().origin(), SOURCE, SESSION.sessionId(), QUERY,
                original.request().arguments(), T.plusMillis(5));
        var late = new PlanningReadReceipt(deadline, original.contractId(), original.requestId(), original.before(), original.after(), query);
        assertThrows(IllegalArgumentException.class, () -> query.custody().orElseThrow().verify(late));
        var before = original.before().binding();
        var expired = new GuardEvidence(before.origin(), before.source(), before.sessionId(), before.connectionGeneration(), before.operation(),
                before.nativeEvidence(), before.capabilityEvidence(), before.authorityId(), before.observedAt(), T.plusMillis(2), before.supportingEvidence());
        var badGuard = new PlanningReadGuard(expired, original.before().originalBindingSha256());
        var outside = new PlanningReadReceipt(original.request(), original.contractId(), original.requestId(), badGuard, badGuard, query);
        assertThrows(IllegalArgumentException.class, () -> query.custody().orElseThrow().verify(outside));
    }
    @Test void chronologyCodecPreservesU64DecimalStringsAndRejectsMalformedOrAliasedFields() {
        var value = ack("strict-roundtrip", 7, T.plusMillis(4)).custody().orElseThrow();
        var row = NativeRequestChronologyCodec.encode(value); assertEquals(value, NativeRequestChronologyCodec.decode(row));
        assertEquals("18446744073709551615", row.get("session").get("connection_generation").textValue());
        assertEquals("7", row.get("write_entered").get("order").textValue());
        assertEquals(EPOCH.toString(), row.get("custody_epoch").textValue());
        var missing = row.deepCopy(); missing.remove("write_completed"); assertThrows(IllegalArgumentException.class, () -> NativeRequestChronologyCodec.decode(missing));
        var alias = row.deepCopy(); alias.set("sent", alias.remove("write_entered")); assertThrows(IllegalArgumentException.class, () -> NativeRequestChronologyCodec.decode(alias));
        var numeric = row.deepCopy(); ((com.fasterxml.jackson.databind.node.ObjectNode) numeric.get("write_entered")).put("order", 7);
        assertThrows(IllegalArgumentException.class, () -> NativeRequestChronologyCodec.decode(numeric));
        var bool = row.deepCopy(); ((com.fasterxml.jackson.databind.node.ObjectNode) bool.get("original_response")).put("bytes", true);
        assertThrows(IllegalArgumentException.class, () -> NativeRequestChronologyCodec.decode(bool));
        var floatTime = row.deepCopy(); ((com.fasterxml.jackson.databind.node.ObjectNode) floatTime.get("response_received")).put("observed_at", 1.5);
        assertThrows(IllegalArgumentException.class, () -> NativeRequestChronologyCodec.decode(floatTime));
        var zeroOrder = row.deepCopy(); ((com.fasterxml.jackson.databind.node.ObjectNode) zeroOrder.get("write_entered")).put("order", "0");
        assertThrows(IllegalArgumentException.class, () -> NativeRequestChronologyCodec.decode(zeroOrder));
        var wrongClock = row.deepCopy(); ((com.fasterxml.jackson.databind.node.ObjectNode) wrongClock.get("write_completed")).put("observed_at", T.toString());
        assertThrows(IllegalArgumentException.class, () -> NativeRequestChronologyCodec.decode(wrongClock));
    }
}
