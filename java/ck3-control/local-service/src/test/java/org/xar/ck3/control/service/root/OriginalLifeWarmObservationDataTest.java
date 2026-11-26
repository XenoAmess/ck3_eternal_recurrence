package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.session.SessionPorts.*;

import java.io.IOException;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Base64;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionReceiptCodec;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.ActionTransitions;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.advance.ResumeCoreObservation;
import org.xar.ck3.control.application.planning.PlanTrace;
import org.xar.ck3.control.application.session.BatchReport;
import org.xar.ck3.control.application.session.ContinuityBatchJournal;
import org.xar.ck3.control.application.session.SessionClock;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.PortableRecoveryDataArchive;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedText;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey;

/** Frozen receipt DATA and existing STOP/default-denial seams; never a Root/Native authority fixture. */
final class OriginalLifeWarmObservationDataTest {
    @Test void frozenFailureQualificationAndStopNeverDispatch() throws Exception {
        byte[] parentBytes = fixture("receipt-754.json", "896b54ed5e1454dc8fff7e2d93cb4dc3ea78fd1fce070af1d8df5816153be87f");
        byte[] runningBytes = fixture("receipt-749.json", "9939118ac797dcbebf4feba3951a6ebe20c9b36e8e8f9e07bd3543266a4cbcea");
        byte[] childBytes = fixture("receipt-753.json", "3cd59508cbacfed5ae0d4b91056e265b9ec4625830ae36cb0e3a092d04842144");
        // These composite DATA branches decode without resolving any archive reference.
        ActionReceipt parent = ActionReceiptCodec.decodeReceipt(parentBytes, null);
        ActionReceipt running = ActionReceiptCodec.decodeReceipt(runningBytes, null);
        var command = parent.command();
        byte[] originalCommand = ActionCodec.encodeCommand(command);
        var owner = new SessionIdentity(command.origin().machineId(), command.origin().game(), command.sessionId());
        var tick = new SessionClock.Tick(0L, Instant.parse("2026-11-06T00:00:00Z"));
        var returned = new BatchReport.PhaseSpan(BatchReport.Phase.ACTION, tick, tick, BatchReport.PhaseTerminal.RETURNED);
        var turn = turn(parent, 1);
        BatchReport failure = report(owner, BatchReport.Terminal.ACTION_UNKNOWN, "original action remains UNRESOLVED", tick, List.of(returned), List.of(turn));
        assertSame(parent, RootOrdinaryWorkerLoop.postAckLifeReadFailure(failure).orElseThrow());
        assertTrue(RootOrdinaryWorkerLoop.postAckLifeReadFailure(report(owner, BatchReport.Terminal.WRITER_UNKNOWN, failure.detail(), tick, List.of(returned), List.of(turn))).isEmpty());
        assertTrue(RootOrdinaryWorkerLoop.postAckLifeReadFailure(report(owner, failure.terminal(), "foreign failure", tick, List.of(returned), List.of(turn))).isEmpty());
        var foreign = new SessionIdentity(owner.machineId(), owner.game(), "foreign-session");
        assertTrue(RootOrdinaryWorkerLoop.postAckLifeReadFailure(report(foreign, failure.terminal(), failure.detail(), tick, List.of(returned), List.of(turn))).isEmpty());
        var failed = new BatchReport.PhaseSpan(BatchReport.Phase.ACTION, tick, tick, BatchReport.PhaseTerminal.FAILED);
        assertTrue(RootOrdinaryWorkerLoop.postAckLifeReadFailure(report(owner, failure.terminal(), failure.detail(), tick, List.of(failed), List.of(turn))).isEmpty());
        assertTrue(RootOrdinaryWorkerLoop.postAckLifeReadFailure(report(owner, failure.terminal(), failure.detail(), tick, List.of(returned), List.of())).isEmpty());
        assertTrue(RootOrdinaryWorkerLoop.postAckLifeReadFailure(report(owner, failure.terminal(), failure.detail(), tick, List.of(returned), List.of(turn(running, 1), turn(parent, 2)))).isEmpty());

        // A reason is only a scheduling filter, never proof of Native ACK/custody or a permit.
        String reason = StrictJson.parse(childBytes).path("state").path("reason").asText();
        assertTrue(RootOrdinaryWorkerLoop.knownNegativeFreshRead(reason));
        assertFalse(RootOrdinaryWorkerLoop.knownNegativeFreshRead(reason.replace("native_ok=false", "native_ok=true")));
        assertFalse(RootOrdinaryWorkerLoop.knownNegativeFreshRead(reason.replace("fresh_full_state_native_read_unavailable", "other_native_error")));
        assertFalse(RootOrdinaryWorkerLoop.knownNegativeFreshRead(reason + "; guard rejected"));
        assertFalse(RootOrdinaryWorkerLoop.knownNegativeFreshRead("postcondition unavailable:java.io.IOException: guard rejected"));
        assertTrue(RootOrdinaryWorkerLoop.knownNegativeFreshRead(reason));

        AtomicInteger dispatched = new AtomicInteger();
        RootOrdinaryWorkerLoop.BatchCall refusing = limits -> { dispatched.incrementAndGet(); throw new AssertionError("new batch dispatched"); };
        assertFalse(refusing.recoverPostAckLifeRead(failure, 23L, tick.utc().plusSeconds(300)));
        assertEquals(0, dispatched.get());
        AtomicInteger accesses = new AtomicInteger();
        AtomicInteger callbacks = new AtomicInteger();
        var control = new RootOrdinaryWorkerLoop.Control() {
            @Override public boolean stopRequested() { return true; }
            @Override public void onBatchCompleted(BatchReport report, long next) { callbacks.incrementAndGet(); }
        };
        var configuration = new RootOrdinaryWorkerLoop.Configuration("warm-data", 1, Duration.ofMinutes(20), Duration.ofMinutes(2), Duration.ofMillis(100), 1);
        var loop = new RootOrdinaryWorkerLoop(configuration, control, Clock.fixed(tick.utc(), ZoneOffset.UTC));
        RootOrdinaryWorkerLoop.BatchAccess access = () -> { accesses.incrementAndGet(); throw new AssertionError("STOP opened a Root"); };
        var stopped = loop.run(access, 23L);
        assertEquals(RootOrdinaryWorkerLoop.StopReason.OPERATOR_STOP, stopped.stopReason());
        assertEquals(23L, stopped.nextBatchSequence());
        assertTrue(stopped.lastReport().isEmpty());
        assertTrue(stopped.failureDetail().isEmpty());
        assertEquals(0, accesses.get()); assertEquals(0, callbacks.get()); assertEquals(0, dispatched.get());
        assertSame(parent, RootOrdinaryWorkerLoop.postAckLifeReadFailure(failure).orElseThrow());
        assertArrayEquals(originalCommand, ActionCodec.encodeCommand(parent.command()));
        assertEquals(Instant.parse("2026-11-05T21:53:40.942612100Z"), parent.command().deadline());
        assertArrayEquals(parentBytes, fixture("receipt-754.json", ActionCodec.sha256(parentBytes)));
        assertArrayEquals(runningBytes, fixture("receipt-749.json", ActionCodec.sha256(runningBytes)));
        assertArrayEquals(childBytes, fixture("receipt-753.json", ActionCodec.sha256(childBytes)));
        System.out.println("WARM_DATA_PASS original_receipts=3 report_denials=6 reason_denials=4 stop_access=0 default_dispatch=0 original_command_preserved=true private_root_recovery_exercised=false");
    }

    @Test void expiredCurrentFull111CoreResumeAllowsOriginalReadWithoutChangingEitherAction() throws Exception {
        var originalActions = source56Actions();
        var parent = ContinuityBatchJournal.readOnlyLifeRecoveryRoot(originalActions).orElseThrow();
        var children = ActionTransitions.composite(parent.state()).orElseThrow().children();
        var last = children.getLast();
        var resume = originalActions.stream().filter(action -> action.command().actionId().equals(last.actionId()))
                .findFirst().orElseThrow();
        Instant deadline = parent.command().deadline();
        Instant expired = deadline.plusNanos(1);

        // The original Source56 child remained ACKed UNKNOWN and cannot qualify through the new path.
        assertInstanceOf(ActionState.Unknown.class, resume.state());
        assertTrue(resume.ack().orElseThrow().nativeOk());
        assertTrue(RootOrdinaryWorkerLoop.expiredCoreResumeRead(parent, originalActions, expired).isEmpty());
        assertFalse(RootOrdinaryWorkerLoop.knownPostAckLifeRead(parent, originalActions));

        // Future role DATA only. Test references have no archive originals and grant no authority.
        var observation = new ResumeCoreObservation(new ExactRef("fixture/pre-resume", 1, "a".repeat(64)),
                new ExactRef("fixture/core-after", 1, "b".repeat(64)), resume.command().deadline());
        var core = new ActionReceipt(resume.version(), resume.sequence(), resume.command(), resume.bodySha256(),
                new ActionState.Settled(ActionTransitions.attempt(resume.state()).orElseThrow(),
                        resume.ack().orElseThrow(), new ActionState.ResumeCoreApplied(observation)));
        var afterCore = originalActions.stream().map(action -> action.equals(resume) ? core : action).toList();
        assertSame(core, RootOrdinaryWorkerLoop.expiredCoreResumeRead(parent, afterCore, expired).orElseThrow());
        assertTrue(RootOrdinaryWorkerLoop.expiredCoreResumeRead(parent, afterCore, deadline).isEmpty());
        assertTrue(RootOrdinaryWorkerLoop.expiredCoreResumeRead(parent, afterCore, deadline.minusNanos(1)).isEmpty());
        assertTrue(RootOrdinaryWorkerLoop.expiredCoreResumeRead(parent,
                afterCore.stream().filter(action -> action != core).toList(), expired).isEmpty());
        var duplicate = new java.util.ArrayList<>(afterCore);
        duplicate.add(core);
        assertTrue(RootOrdinaryWorkerLoop.expiredCoreResumeRead(parent, duplicate, expired).isEmpty());
        var forgedAck = new org.xar.ck3.control.application.action.NativeActionPort.AckReceived(
                resume.ack().orElseThrow().requestId(), true, Optional.empty(),
                resume.ack().orElseThrow().originalFrame(), resume.ack().orElseThrow().originalPacket());
        assertThrows(IllegalArgumentException.class, () -> new ActionReceipt(resume.version(), resume.sequence(),
                resume.command(), resume.bodySha256(), new ActionState.Settled(
                ActionTransitions.attempt(resume.state()).orElseThrow(), forgedAck,
                new ActionState.ResumeCoreApplied(observation))));
        var oldParent = ActionReceiptCodec.decodeReceipt(fixture("receipt-754.json",
                "896b54ed5e1454dc8fff7e2d93cb4dc3ea78fd1fce070af1d8df5816153be87f"), null);
        assertTrue(RootOrdinaryWorkerLoop.expiredCoreResumeRead(oldParent, afterCore, expired).isEmpty());

        var command = parent.command();
        var owner = new SessionIdentity(command.origin().machineId(), command.origin().game(), command.sessionId());
        var at = new SessionClock.Tick(0L, expired);
        var returned = new BatchReport.PhaseSpan(BatchReport.Phase.ACTION, at, at, BatchReport.PhaseTerminal.RETURNED);
        var failure = report(owner, BatchReport.Terminal.ACTION_UNKNOWN, "original action remains UNRESOLVED",
                at, List.of(returned), List.of(turn(parent, 1)));
        assertSame(parent, RootOrdinaryWorkerLoop.postAckLifeReadFailure(failure).orElseThrow());
        assertFalse(RootOrdinaryWorkerLoop.knownPostAckLifeRead(parent, afterCore));
        assertEquals(ActionReceipt.Outcome.UNRESOLVED, parent.outcome());
        assertEquals(deadline, parent.command().deadline());
        assertEquals(resume.command().deadline(), core.command().deadline());
        assertArrayEquals(ActionCodec.encodeCommand(resume.command()), ActionCodec.encodeCommand(core.command()));
        assertEquals(resume.ack(), core.ack());
    }

    @Test void ordinaryVisibleAppliedWithoutAdvanceCreditCannotBeReadAsExpiryTerminal() throws Exception {
        var ordinary = source56Actions().stream()
                .filter(receipt -> receipt.state() instanceof ActionState.CompositeSettled && receipt.eligibleAdvance())
                .findFirst().orElseThrow();
        var settled = (ActionState.CompositeSettled) ordinary.state();
        var observation = ordinary.applied().orElseThrow().observation();
        var actual = observation.actual().stream().map(value -> value instanceof ExpectedText text
                && text.field().equals(new FieldKey("progress_status"))
                        ? new ExpectedText(text.field(), "boundary_interrupted") : value).toList();
        var nonEligible = new ActionState.EffectObservation(observation.after(), observation.source(),
                observation.sessionId(), observation.observerSchema(), actual, observation.provenance(),
                ordinary.command().deadline().plusNanos(1), observation.originalEvidence(), observation.supportingEvidence());
        var candidate = new ActionReceipt(ordinary.version(), ordinary.sequence(), ordinary.command(), ordinary.bodySha256(),
                new ActionState.CompositeSettled(settled.execution(), new ActionState.Applied(nonEligible)));
        assertTrue(candidate.visibleGameplay());
        assertFalse(candidate.eligibleAdvance());
        var unreadable = new PortableRecoveryDataArchive(
                same -> { throw new AssertionError("non-expiry result cannot acquire a writer"); },
                (ref, maximum) -> { throw new AssertionError("non-expiry result cannot read terminal evidence"); }).proxy();
        assertFalse(RootOrdinaryWorkerLoop.recoveredExpiredLifeReceipt(candidate, Optional.of(candidate), unreadable));
        assertFalse(RootOrdinaryWorkerLoop.recoveredExpiredLifeReceipt(candidate, Optional.of(ordinary), unreadable));
    }

    private List<ActionReceipt> source56Actions() throws IOException {
        try (var input = getClass().getResourceAsStream(
                "/org/xar/ck3/control/application/session/source56-interrupted-recovery-prefix.json.gz")) {
            assertNotNull(input);
            try (var gzip = new GZIPInputStream(input)) {
                var data = FullJsonTree.parse(gzip.readNBytes(1 << 20), 1 << 20);
                var head = ContinuityJson.parseObject(Base64.getDecoder().decode(data.get("head").textValue()), 1 << 20);
                var archive = new PortableRecoveryDataArchive(same -> {
                    throw new AssertionError("warm admission fixture cannot acquire a writer");
                }, (ref, maximum) -> {
                    var material = data.path("artifacts").get(ref.sha256());
                    assertNotNull(material);
                    return Base64.getDecoder().decode(material.textValue());
                }).proxy();
                return ContinuityActionJournal.receipts(
                        ContinuityState.fromJson(head, head.get("machine_id").textValue()), archive);
            }
        }
    }

    /** Real archived negative READ packets plus synthetic rejection mutations; no live custody/lease is issued. */
    @Test void verifiedNegativeReadPacketsKeepScopeAndFailuresDistinct() throws Exception {
        byte[] dispatch=fixture("negative-dispatch.json","d1bcb9392328b890e7d8f46df77e1903bc97b69d0dab59219e7e74eb802db369");
        byte[] packet=fixture("negative-packet.bin","3f9cdbc98fb3bd61436558ce24504cee11a5f0dd4f719bfedf9cb36d0cb30a05");
        byte[] outbound=fixture("negative-outbound.bin","2ebc069d1a4ba5db3501b7c6e44ec10173be3af9802138995c2d5cdfff35285b");
        byte[] frame=fixture("negative-frame.bin","456dd3624da90e3adef9c556e6925826bac76857c3fdb6fbe9dd1d13ee185060");
        var row=StrictJson.parse(dispatch);var custody=row.path("custody");
        byte[] parentBytes=fixture("receipt-754.json","896b54ed5e1454dc8fff7e2d93cb4dc3ea78fd1fce070af1d8df5816153be87f");
        var parent=ActionReceiptCodec.decodeReceipt(parentBytes,null);
        assertEquals(StrictJson.parse(parentBytes).path("command").path("before").path("game"),custody.path("session").path("game"));
        var owner=new org.xar.ck3.control.application.action.NativeObservationPort.TransportSession(
                custody.path("session").path("machine_id").asText(),parent.command().origin().game(),
                new java.math.BigInteger(custody.path("session").path("connection_generation").asText()),custody.path("session").path("session_id").asText());
        var chronology=new org.xar.ck3.control.application.action.NativeRequestChronology(owner,
                java.util.UUID.fromString(custody.path("custody_epoch").asText()),row.path("request_id").asText(),
                org.xar.ck3.control.application.action.NativeRequestChronology.PacketIdentity.of(outbound),
                org.xar.ck3.control.application.action.NativeRequestChronology.PacketIdentity.of(packet),
                event(custody.path("write_entered")),event(custody.path("write_completed")),event(custody.path("response_received")));
        assertEquals(custody.path("original_request").path("sha256").asText(),chronology.originalRequest().sha256());
        assertEquals(custody.path("original_response").path("sha256").asText(),chronology.originalResponse().sha256());
        var ack=negativeAck(row.path("request_id").asText(),packet,outbound,frame,Optional.of(chronology),false);
        var result=new org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort.Unavailable(ack,"archived negative READ DATA");
        assertSame(ack,RootLifecycleAuthority.verifiedNegativeFreshRead(result,owner).orElseThrow());
        var foreign=new org.xar.ck3.control.application.action.NativeObservationPort.TransportSession(owner.machineId(),owner.game(),owner.connectionGeneration(),"foreign-session");
        assertThrows(RuntimeException.class,()->RootLifecycleAuthority.verifiedNegativeFreshRead(result,foreign));
        var missing=negativeAck(ack.requestId(),packet,outbound,frame,Optional.empty(),false);
        assertThrows(IOException.class,()->RootLifecycleAuthority.verifiedNegativeFreshRead(new org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort.Unavailable(missing,"no custody DATA"),owner));
        var positive=negativeAck(ack.requestId(),packet,outbound,frame,Optional.of(chronology),true);
        assertTrue(RootLifecycleAuthority.verifiedNegativeFreshRead(new org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort.Unavailable(positive,"positive flag DATA is not negative qualification"),owner).isEmpty());
        var timeout=new org.xar.ck3.control.application.action.NativeActionPort.Unknown(ack.requestId(),"timeout DATA",outbound,Optional.empty());
        assertTrue(RootLifecycleAuthority.verifiedNegativeFreshRead(new org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort.Unavailable(timeout,"not an ACK"),owner).isEmpty());

        // Recompute packet DATA digests for a synthetic different error, so rejection reaches the error classifier.
        var other=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(frame);other.put("error","other_native_error");
        byte[] otherFrame=StrictJson.canonical(other),otherPacket=framed(otherFrame);
        var otherCustody=new org.xar.ck3.control.application.action.NativeRequestChronology(owner,chronology.custodyEpoch(),ack.requestId(),chronology.originalRequest(),
                org.xar.ck3.control.application.action.NativeRequestChronology.PacketIdentity.of(otherPacket),chronology.writeEntered(),chronology.writeCompleted(),chronology.responseReceived());
        var otherAck=negativeAck(ack.requestId(),otherPacket,outbound,otherFrame,Optional.of(otherCustody),false);
        assertTrue(RootLifecycleAuthority.verifiedNegativeFreshRead(new org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort.Unavailable(otherAck,"other error DATA"),owner).isEmpty());
        byte[] badOutbound=outbound.clone();badOutbound[0]=0;
        var badCustody=new org.xar.ck3.control.application.action.NativeRequestChronology(owner,chronology.custodyEpoch(),ack.requestId(),
                org.xar.ck3.control.application.action.NativeRequestChronology.PacketIdentity.of(badOutbound),chronology.originalResponse(),chronology.writeEntered(),chronology.writeCompleted(),chronology.responseReceived());
        var malformed=negativeAck(ack.requestId(),packet,badOutbound,frame,Optional.of(badCustody),false);
        assertThrows(RuntimeException.class,()->RootLifecycleAuthority.verifiedNegativeFreshRead(new org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort.Unavailable(malformed,"malformed framing DATA"),owner));
        var wrongFrame=negativeAck(ack.requestId(),packet,outbound,otherFrame,Optional.of(chronology),false);
        assertThrows(RuntimeException.class,()->RootLifecycleAuthority.verifiedNegativeFreshRead(new org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort.Unavailable(wrongFrame,"frame mismatch DATA"),owner));
        var generic=new IOException("actual fresh reconciliation read unavailable or failed closed");
        assertTrue(RootOrdinaryWorkerLoop.negativeFreshReadFailure(generic).isEmpty());
        assertTrue(RootOrdinaryWorkerLoop.negativeFreshReadFailure(new IOException("unresolved original reconciliation failed",new IllegalArgumentException("guard rejected"))).isEmpty());
        generic.addSuppressed(new IOException("close failed"));
        assertTrue(RootOrdinaryWorkerLoop.negativeFreshReadFailure(generic).isEmpty());
        assertSame(ack,RootLifecycleAuthority.verifiedNegativeFreshRead(result,owner).orElseThrow());
        assertArrayEquals(dispatch,fixture("negative-dispatch.json",ActionCodec.sha256(dispatch)));
        assertArrayEquals(packet,fixture("negative-packet.bin",ActionCodec.sha256(packet)));
        assertArrayEquals(outbound,fixture("negative-outbound.bin",ActionCodec.sha256(outbound)));
        assertArrayEquals(frame,fixture("negative-frame.bin",ActionCodec.sha256(frame)));
        System.out.println("VERIFIED_NEGATIVE_DATA_PASS real_negative=1 foreign=denied missing_custody=denied positive=denied timeout_unknown=denied other_error=denied malformed=denied frame_mismatch=denied generic_IO=denied guard_cause=denied suppressed=denied physical_lease_or_live_retry_exercised=false");
    }

    private static org.xar.ck3.control.application.action.NativeRequestChronology.Event event(com.fasterxml.jackson.databind.JsonNode row) {
        return new org.xar.ck3.control.application.action.NativeRequestChronology.Event(new java.math.BigInteger(row.path("order").asText()),Instant.parse(row.path("observed_at").asText()));
    }
    private static org.xar.ck3.control.application.action.NativeActionPort.AckReceived negativeAck(String id,byte[] packet,byte[] outbound,byte[] frame,
            Optional<org.xar.ck3.control.application.action.NativeRequestChronology> custody,boolean ok) {
        return new org.xar.ck3.control.application.action.NativeActionPort.AckReceived(id,ok,Optional.empty(),new org.xar.ck3.control.application.action.RawJson(frame),packet,
                Optional.of(new org.xar.ck3.control.application.action.NativeActionPort.OutboundPacket(id,outbound)),custody);
    }
    private static byte[] framed(byte[] payload) {
        return java.nio.ByteBuffer.allocate(payload.length+4).order(java.nio.ByteOrder.LITTLE_ENDIAN).putInt(payload.length).put(payload).array();
    }

    private static BatchReport.Turn turn(ActionReceipt receipt, int index) {
        var before = receipt.command().before();
        return new BatchReport.Turn(index, before, new PlanTrace(before, List.of(), Optional.empty()), receipt, new TurnFacts(false, false, List.of()));
    }

    private static BatchReport report(SessionIdentity owner, BatchReport.Terminal terminal, String detail,
            SessionClock.Tick tick, List<BatchReport.PhaseSpan> phases, List<BatchReport.Turn> turns) {
        return new BatchReport(owner, "warm-data-22", terminal, detail, tick, tick, phases, turns,
                List.of(), List.of(), List.of(), List.of(), Optional.empty(), Optional.empty(), Optional.empty(),
                Optional.empty(), Optional.empty(), 0L, 0, true, List.of(), List.of(), List.of());
    }

    private static byte[] fixture(String name, String sha) throws IOException {
        try (var input = OriginalLifeWarmObservationDataTest.class.getResourceAsStream("/warm-life-observation/" + name)) {
            if (input == null) throw new IOException("missing exact frozen receipt resource: " + name);
            byte[] bytes = input.readAllBytes(); assertEquals(sha, ActionCodec.sha256(bytes)); return bytes;
        }
    }
}
