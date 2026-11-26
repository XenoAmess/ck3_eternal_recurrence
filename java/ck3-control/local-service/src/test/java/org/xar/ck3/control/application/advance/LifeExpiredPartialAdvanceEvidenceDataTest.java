package org.xar.ck3.control.application.advance;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.Base64;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.ActionTransitions;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.application.action.NativeRequestChronology;
import org.xar.ck3.control.application.action.ObservationProvenance;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.session.ContinuityBatchJournal;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.PortableRecoveryDataArchive;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.reconciliation.LateOutcome.Mode;
import org.xar.ck3.control.reconciliation.LateOutcome.State;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;
import org.xar.ck3.control.wave2.runtime.deadlinetransport.SentinelObservation;

/** Original interrupted Life DATA and a test-only model of the source-owned expiry wire field. */
final class LifeExpiredPartialAdvanceEvidenceDataTest {
    @Test void originalAckedUnknownTimelineRemainsUnqualifiedAfterItsDeadline() throws Exception {
        try (var resource = getClass().getResourceAsStream("/org/xar/ck3/control/application/session/source56-interrupted-recovery-prefix.json.gz")) {
            assertNotNull(resource);
            try (var gzip = new GZIPInputStream(resource)) {
                byte[] fixture = gzip.readNBytes(1 << 20);
                assertTrue(fixture.length < 1 << 20);
                var data = FullJsonTree.parse(fixture, 1 << 20);
                var row = ContinuityJson.parseObject(Base64.getDecoder().decode(data.get("head").textValue()), 1 << 20);
                var archive = new PortableRecoveryDataArchive(same -> { throw new AssertionError("fixture makes no writer call"); }, (ref, maximum) -> {
                    var material = data.path("artifacts").get(ref.sha256());
                    assertNotNull(material);
                    return Base64.getDecoder().decode(material.textValue());
                }).proxy();
                var actions = ContinuityActionJournal.receipts(ContinuityState.fromJson(row, row.get("machine_id").textValue()), archive);
                var parent = ContinuityBatchJournal.readOnlyLifeRecoveryRoot(actions).orElseThrow();
                var children = ActionTransitions.composite(parent.state()).orElseThrow().children().stream()
                        .map(binding -> actions.stream().filter(receipt -> receipt.command().actionId().equals(binding.actionId())).findFirst().orElseThrow()).toList();
                var deadline = parent.command().deadline();

                assertFalse(LifeExpiredPartialAdvanceEvidence.accepts(parent, children, deadline));
                assertFalse(LifeExpiredPartialAdvanceEvidence.accepts(parent, children, deadline.plusNanos(1)));
                assertEquals(55, children.getLast().sequence());
                assertInstanceOf(ActionState.Unknown.class, children.getLast().state());
                assertTrue(children.getLast().ack().orElseThrow().nativeOk());
                assertFalse(LifeExpiredPartialAdvanceEvidence.accepts(parent, children.reversed(), deadline.plusNanos(1)));
                assertFalse(LifeExpiredPartialAdvanceEvidence.accepts(parent, List.of(children.getFirst()), deadline.plusNanos(1)));
                assertEquals(ActionReceipt.Outcome.UNRESOLVED, parent.outcome());
                assertEquals(ActionReceipt.Outcome.UNRESOLVED, children.getLast().outcome());
                assertFalse(parent.eligibleAdvance());
                assertEquals(deadline, parent.command().deadline());

                // Only the future receipt role is modeled here. These refs have no
                // originals in this fixture and cannot pass production archive replay.
                var legacyResume = children.getLast();
                var attempt = ActionTransitions.attempt(legacyResume.state()).orElseThrow();
                var unqualifiedFixtureCore = new ResumeCoreObservation(
                        new ExactRef("fixture/before-core", 1, "5".repeat(64)),
                        new ExactRef("fixture/core-ack", 1, "6".repeat(64)), legacyResume.command().deadline());
                var futureReceiptShape = new ActionReceipt(legacyResume.version(), legacyResume.sequence(), legacyResume.command(),
                        legacyResume.bodySha256(), new ActionState.Settled(attempt, legacyResume.ack().orElseThrow(),
                                new ActionState.ResumeCoreApplied(unqualifiedFixtureCore)));
                assertTrue(LifeExpiredPartialAdvanceEvidence.accepts(parent,
                        List.of(children.getFirst(), futureReceiptShape), deadline.plusNanos(1)));
                assertFalse(LifeExpiredPartialAdvanceEvidence.accepts(parent,
                        List.of(children.getFirst(), futureReceiptShape), deadline));

                var plan = AdvancePlan.decode(parent.command());
                var status = ClockStatusRead.decode(ack(token(1 << 15, "evaluation_failure")));
                BigInteger partialDate = BigInteger.valueOf(53179944);
                assertEquals(24L, LifeExpiredPartialAdvanceEvidence.partialDays(plan, status, partialDate));
                var wrongPause = token(1 << 15, "evaluation_failure");
                ((ObjectNode) wrongPause.get("tactical_daily_sentinel")).put("pause_observed", false);
                assertThrows(IllegalArgumentException.class, () ->
                        LifeExpiredPartialAdvanceEvidence.partialDays(plan, ClockStatusRead.decode(ack(wrongPause)), partialDate));
                for (var rejected : List.of(plan.startingDateRaw(), plan.targetDateRaw(),
                        plan.targetDateRaw().add(AdvancePlan.DAY), partialDate.add(BigInteger.ONE),
                        partialDate.subtract(AdvancePlan.DAY))) {
                    assertThrows(IllegalArgumentException.class, () -> LifeExpiredPartialAdvanceEvidence.partialDays(plan, status, rejected));
                }
            }
        }
    }

    @Test void fullReadNeedsSameHeldSetterOrAnExactNewConnectionWatch() {
        var game = new org.xar.ck3.control.contracts.GameGeneration(50372,
                new org.xar.ck3.control.contracts.PythonOnlyUInt64(BigInteger.valueOf(134401544348311914L)));
        var session = new TransportSession("fixture-machine", game, BigInteger.valueOf(16), "fixture-session");
        var newConnection = new TransportSession(session.machineId(), game, BigInteger.valueOf(17), session.sessionId());
        var differentGame = new TransportSession(session.machineId(),
                new org.xar.ck3.control.contracts.GameGeneration(50373, game.creationFiletime()),
                newConnection.connectionGeneration(), session.sessionId());
        var oldEpoch = UUID.fromString("8c799220-1674-4572-9dca-7a0e40d20b45");
        var newEpoch = UUID.fromString("8c799220-1674-4572-9dca-7a0e40d20b46");
        var resume = chronology(session, oldEpoch, "resume", 10);
        var full = chronology(session, oldEpoch, "full", 20);
        var reconnected = chronology(newConnection, newEpoch, "full-reconnected", 20);
        var foreign = chronology(differentGame, newEpoch, "full-foreign", 20);
        var parentRef = new ExactRef("fixture/parent", 1, "1".repeat(64));
        var coreReceipt = new ExactRef("fixture/core-resume", 1, "2".repeat(64));
        var positiveAck = new ExactRef("fixture/resume-ack", 1, "3".repeat(64));
        var live = new ObservationProvenance.LiveAfterSetter(positiveAck);
        var watch = new ObservationProvenance.SameGameWatch(parentRef, coreReceipt);
        assertDoesNotThrow(() -> LifeExpiredPartialAdvanceEvidence.requireFreshBasis(live, parentRef, coreReceipt, positiveAck, resume, full));
        assertDoesNotThrow(() -> LifeExpiredPartialAdvanceEvidence.requireFreshBasis(watch, parentRef, coreReceipt, positiveAck, resume, reconnected));
        assertThrows(IllegalArgumentException.class, () ->
                LifeExpiredPartialAdvanceEvidence.requireFreshBasis(live, parentRef, coreReceipt, positiveAck, resume, reconnected));
        assertThrows(IllegalArgumentException.class, () ->
                LifeExpiredPartialAdvanceEvidence.requireFreshBasis(watch, parentRef, coreReceipt, positiveAck, resume, full));
        assertThrows(IllegalArgumentException.class, () ->
                LifeExpiredPartialAdvanceEvidence.requireFreshBasis(watch, parentRef, coreReceipt, positiveAck, resume, foreign));
        assertThrows(IllegalArgumentException.class, () ->
                LifeExpiredPartialAdvanceEvidence.requireFreshBasis(watch, parentRef, positiveAck, positiveAck, resume, reconnected));
        var oldCold = new ObservationProvenance.ColdAfterAcknowledgement(coreReceipt);
        assertThrows(IllegalArgumentException.class, () ->
                LifeExpiredPartialAdvanceEvidence.requireFreshBasis(oldCold, parentRef, coreReceipt, positiveAck, resume, reconnected));
    }

    private static NativeRequestChronology chronology(TransportSession session, UUID epoch, String id, long order) {
        var packet = new NativeRequestChronology.PacketIdentity(1,"4".repeat(64));
        var time = Instant.parse("2026-11-26T11:18:01Z");
        return new NativeRequestChronology(session, epoch, id, packet, packet,
                event(order,time),event(order+1,time),event(order+2,time));
    }

    private static NativeRequestChronology.Event event(long order, Instant time) {
        return new NativeRequestChronology.Event(BigInteger.valueOf(order),time.plusNanos(order));
    }

    @Test void legacyFailedStatusAndHeartbeatFlagsProveNoExpiry() {
        var legacy = token(32, "combat_unavailable");
        var heartbeat = legacy.putObject("heartbeat");
        heartbeat.put("failure_flags", 32).put("armed", false).put("shutdown_safe", true);
        assertTrue(LifeExpiredPartialAdvanceEvidence.expiryStatus(ack(legacy)).isEmpty());
    }

    @Test void onlyTheVersionedDisarmedSameGenerationFieldCanSupplyExpiryFacts() {
        var source = token(1 << 15, "evaluation_failure");
        source.putObject(LifeExpiredPartialAdvanceEvidence.EXPIRY_STATUS_FIELD)
                .put("schema", LifeExpiredPartialAdvanceEvidence.EXPIRY_STATUS_SCHEMA)
                .put("generation", 2).put("original_deadline_unix_ms", 1795691880125L).put("failure_flags", 32)
                .put("armed", false).put("shutdown_safe", true).put("access_cleanup_unknown", false);
        var actual = LifeExpiredPartialAdvanceEvidence.expiryStatus(ack(source)).orElseThrow();
        assertEquals(BigInteger.TWO, actual.generation());
        assertEquals(1795691880125L, actual.nativeDeadlineMillis());

        assertRejected(source, "generation", 3);
        assertRejected(source, "failure_flags", 33);
        assertRejected(source, "original_deadline_unix_ms", 0);
        assertRejected(source, "armed", true);
        assertRejected(source, "shutdown_safe", false);
        assertRejected(source, "access_cleanup_unknown", true);
    }

    private static void assertRejected(ObjectNode source, String field, boolean value) {
        var changed = source.deepCopy();
        ((ObjectNode) changed.get(LifeExpiredPartialAdvanceEvidence.EXPIRY_STATUS_FIELD)).put(field, value);
        assertThrows(IllegalArgumentException.class, () -> LifeExpiredPartialAdvanceEvidence.expiryStatus(ack(changed)));
    }

    private static void assertRejected(ObjectNode source, String field, int value) {
        var changed = source.deepCopy();
        ((ObjectNode) changed.get(LifeExpiredPartialAdvanceEvidence.EXPIRY_STATUS_FIELD)).put(field, value);
        assertThrows(IllegalArgumentException.class, () -> LifeExpiredPartialAdvanceEvidence.expiryStatus(ack(changed)));
    }

    private static ObjectNode token(int flags, String reason) {
        var slot = new Status(State.FAILED, new CrossJsDecimalUInt64("2"), 53179368, 53180088, 53179944, 53179944, 5,
                Mode.TERMINAL_OR_SENTINEL, 0, 0, 24, 0, flags, List.of(reason), -144, 0, true, true, false, true);
        var value = StrictJson.object().put("step", ClockStatusRead.STEP).put("accepted", true).put("status", "available");
        value.set("tactical_daily_sentinel", SentinelObservation.toJson(slot));
        return value;
    }

    private static NativeActionPort.AckReceived ack(ObjectNode token) {
        byte[] raw = StrictJson.canonical(token);
        var body = new RawJson(raw);
        return new NativeActionPort.AckReceived("fixture-status", true, Optional.of(body), body, raw);
    }
}
