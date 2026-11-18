package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.FullSnapshotDateSentinelArm;
import org.xar.ck3.control.application.action.FullSnapshotClockControl;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.advance.AdvancePrimitives;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.reconciliation.LateOutcome;

/** C++ Snapshot/Date result tokens through the actual software port. No live Game, Root,
 * advance completion, implicit pause, private-role construction or refreshed parent lease. */
final class NativeDateSentinelArmPortTest {
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_1210;
    private static final String ADAPTER="ck3-1.21.0-msvc-x64",BRIDGE="software-date-arm1210";
    private static final String ARM=FullSnapshotDateSentinelArm.PREFIX+"123456-to-123480-speed-5-mode-terminal-a-0";
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private record Input(String name,int bytes,String sha256) { }
    private record SnapshotCpp(byte[] envelope,byte[] state,String id,BigInteger revision) { }
    private record Ack(byte[] envelope,byte[] token,String id,boolean ok) { }
    private static final Input FULL=new Input("full-snapshot-producer-002.json",1171,"5eca02fea7c3f5095d675238f59b69b8d166ed17a0bd4c208b0e133700d7e550");
    private static final Input STATUS_MANIFEST=new Input("status/ACTUAL-CPP-PACKETS02.json",3587,"965533f69a2190e889082893042a2030c6da4a99035131ead787306d2255b088");
    private static final Input NEGATIVE_MANIFEST=new Input("negative/ACTUAL-CPP-PACKETS02.json",4564,"d63e50ba5a649ac508c8b8f6fd27b2ff579cc6437ed4fd62be094e78eef70703");
    private static final Input ARMED=new Input("status/armed-generation1.json",707,"23c6c810b56277788c791944e42dc11b6adc1e577a59cf210b450dac7b2f0744");
    private static final Input TRIGGERED=new Input("status/triggered-generation1.json",693,"8304a787969ec09951b5bf54af228117741a00c505c5bcc741f51f067010cc4f");
    private static final Input EXPIRED=new Input("negative/expired.json",630,"b5952ed1b5b9a56b41dff00b0fde022be35c69233639826c4e4a54d271cdda90");
    private static final Input INDETERMINATE=new Input("negative/indeterminate.json",611,"0d86ad8c4850286e05b384b3d54aa92c0a8470b61629dd50487705783fd19405");
    private static final Input ATTEMPTED=new Input("negative/attempted-rejected.json",611,"07396619e04e667e5a9cc2e98edcb686bc0d9229b97655af377d609d74499768");

    private static final Input CANCEL_MANIFEST=new Input("cleanup/ACTUAL-CPP-CANCEL-PACKETS03.json",2818,"6a609632ae792d5e54efe25443cd5570a1c3ce9d969d62230dedb6f0eecb3fca");
    private static final Input CANCEL_TERMINAL=new Input("cleanup/cancel-terminal-generation1.json",713,"b67a15a7b88172fb76894ab393903b7d93543cd93ce9d9f81fff7e38024f8d0c");

    private static final Input CANCEL_IDLE=new Input("cleanup/cancel-paused-idle-generation1.json",687,"4cdad16ea7720d9315c6fe4b3be9994d6a61bf423ee0d32cffd1d4395b8097d4");

    @Test void parentSixHundredSecondsIsIndependentOfTheSixtySecondFullReadWindowAndAckCutoff() throws Exception {
        try(var f=new Fixture(ARMED,true)) {
            var before=f.received();assertEquals(f.parent,before.activeDeadline());
            assertEquals(f.clock.instant().plusSeconds(60),before.validUntil());
            assertEquals(before.validUntil(),f.source.lastFullDeadline);assertTrue(before.validUntil().isBefore(before.activeDeadline()));
            var until=f.clock.instant().plusSeconds(30);var prepared=prepared(before,ARM);
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,f.actual.submitDateSentinelArm(before,prepared,until));
            original(ack,f.source.arm, f.source.armAck,f.source.arms.getLast());
            assertTrue(ack.nativeOk());assertEquals(until,f.source.lastArmDeadline);
            var request=NativeWire.decodeExecuteRequest(f.source.arms.getLast());
            assertEquals(ARM,request.step());assertEquals(Optional.of(before.frame().nativeRevision()),request.expectedRevision());
            assertTrue(request.expectedRevision().orElseThrow().signum()>0);assertTrue(request.expectedSnapshotRevision().isEmpty());
            var fields=NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value()));assertEquals(1,fields.size());
            assertEquals(StrictJson.parse(prepared.additionalFields().bytes()),StrictJson.parse(request.normalizedAdditionalFields().value()));
            assertEquals(f.parent.toEpochMilli(),fields.path("date_sentinel_arm").path("deadline_unix_ms").longValue());
            var status=DateSentinelArmResult.decode(ack,ARM).status().orElseThrow();
            assertEquals(LateOutcome.State.ARMED,status.state());assertEquals("1",status.generation().decimal());
            assertEquals(123456,status.startingDateRaw());assertEquals(123480,status.targetDateRaw());assertEquals(5,status.speed());
            assertFalse(status.pauseObserved());assertEquals(f.parent,before.activeDeadline());counts(f,1,1,0,0);
        }
    }

    @Test void foreignSupersededExpiredReadAndChangedParentOrStartRefuseBeforeArmWrite() throws Exception {
        try(var owner=new Fixture(ARMED,true);var foreign=new Fixture(ARMED,true)) {
            var before=owner.received();assertEquals(owner.actual.awaitHello(before.validUntil()),foreign.actual.awaitHello(before.validUntil()));
            zero(foreign.actual.submitDateSentinelArm(before,prepared(before,ARM),foreign.clock.instant().plusSeconds(30)));
            counts(owner,1,0,0,0);counts(foreign,0,0,0,0);
        }
        try(var f=new Fixture(ARMED,true)) {
            var before=f.received();f.clock.set(before.validUntil().plusSeconds(1));assertTrue(f.clock.instant().isBefore(before.activeDeadline()));
            zero(f.actual.submitDateSentinelArm(before,prepared(before,ARM),f.clock.instant().plusSeconds(5)));counts(f,1,0,0,0);
        }
        try(var f=new Fixture(ARMED,true)) {
            var old=f.received();f.received();
            zero(f.actual.submitDateSentinelArm(old,prepared(old,ARM),f.clock.instant().plusSeconds(30)));counts(f,2,0,0,0);
        }
        try(var f=new Fixture(ARMED,true)) {
            var before=f.received();var until=f.clock.instant().plusSeconds(30);
            var changed=FullSnapshotDateSentinelArm.request(ARM,before.frame().snapshotId(),before.frame().nativeRevision(),before.activeDeadline().plusSeconds(1));
            zero(f.actual.submitDateSentinelArm(before,changed,until));
            for(String step:List.of(FullSnapshotDateSentinelArm.PREFIX+"24000-to-24024-speed-5-mode-terminal-a-0",
                    FullSnapshotDateSentinelArm.PREFIX+"123456-to-123480-speed-4-mode-terminal-a-0"))
                zero(f.actual.submitDateSentinelArm(before,prepared(before,step),until));
            counts(f,1,0,0,0);
        }
        try(var missing=new Fixture(ARMED,false)) {
            var before=missing.received();zero(missing.actual.submitDateSentinelArm(before,prepared(before,ARM),missing.clock.instant().plusSeconds(30)));
            counts(missing,1,0,0,0);
        }
    }
    @Test void failedBackgroundPolicyDoesNotConsumeTheOriginalDateFullRead() throws Exception {
        try(var f=new Fixture(ARMED,true)) {
            var before=f.received();var until=f.clock.instant().plusSeconds(30);var prepared=prepared(before,ARM);
            f.source.backgroundReady=false;zero(f.actual.submitDateSentinelArm(before,prepared,until));counts(f,1,0,0,0);
            f.source.backgroundReady=true;
            assertInstanceOf(NativeActionPort.AckReceived.class,f.actual.submitDateSentinelArm(before,prepared,until));counts(f,1,1,0,0);
        }
    }
    @Test void nativeExpiredIsDeterminateWhileIndeterminateAndAttemptedRejectionKeepStickyOriginalUnknown() throws Exception {
        try(var f=new Fixture(EXPIRED,true)) {
            var before=f.received();var until=f.clock.instant().plusSeconds(30);var prepared=prepared(before,ARM);
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,f.actual.submitDateSentinelArm(before,prepared,until));
            assertFalse(ack.nativeOk());original(ack,f.source.arm,f.source.armAck,f.source.arms.getLast());
            assertEquals(DateSentinelArmResult.Disposition.REJECTED_BEFORE_QUEUE,DateSentinelArmResult.decode(ack,ARM).disposition());
            zero(f.actual.submitDateSentinelArm(before,prepared,until));counts(f,1,1,0,0);
        }
        for(var input:List.of(INDETERMINATE,ATTEMPTED))try(var f=new Fixture(input,true)) {
            var before=f.received();var until=f.clock.instant().plusSeconds(30);var prepared=prepared(before,ARM);
            var unknown=assertInstanceOf(NativeActionPort.Unknown.class,f.actual.submitDateSentinelArm(before,prepared,until));
            var ack=f.actual.originalIndeterminateFullClockAcknowledgement(unknown.requestId()).orElseThrow();
            original(ack,f.source.arm,f.source.armAck,f.source.arms.getLast());
            assertArrayEquals(ack.originalFrame().bytes(),unknown.rawReturn().orElseThrow().bytes());
            assertArrayEquals(ack.outbound().orElseThrow().originalPacket(),unknown.originalRequestPacket());
            assertSame(unknown,f.actual.submitDateSentinelArm(before,prepared,until));
            assertSame(unknown,f.actual.cancelDateSentinel(before,until));counts(f,1,1,0,0);
        }
    }

    @Test void crossGenerationStatusKeepsItsAfterWriteUnknownAndCannotAuthorizeCleanup() throws Exception {
        try(var f=new Fixture(ARMED,true)) {
            var before=f.received();var until=f.clock.instant().plusSeconds(30);
            assertInstanceOf(NativeActionPort.AckReceived.class,f.actual.submitDateSentinelArm(before,prepared(before,ARM),until));
            zero(f.actual.cancelDateSentinel(before,until));counts(f,1,1,0,0);
            // Explicit negative derivative, not a claim that the C++ producer observed generation 2 here.
            var wrong=NativeWire.object(NativeWire.parse(f.source.status.envelope())).deepCopy();
            ((ObjectNode)wrong.path("result").path("tactical_daily_sentinel")).put("generation",2);
            f.source.status=ack(StrictJson.canonical(wrong));
            var unknown=assertInstanceOf(NativeActionPort.Unknown.class,f.actual.readDateSentinelStatus(before,until));
            assertArrayEquals(f.source.statusRequests.getLast(),unknown.originalRequestPacket());
            var response=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(f.source.statusAck));
            assertArrayEquals(response.payload().value(),unknown.rawReturn().orElseThrow().bytes());
            assertTrue(response.nativeOk());assertEquals(unknown.requestId(),response.requestId());
            zero(f.actual.cancelDateSentinel(before,until));counts(f,1,1,1,0);
            assertEquals(f.parent,before.activeDeadline());
        }
    }
    @Test void sameGenerationTerminalCancelPreservesTriggeredStatusWithoutPauseOrLeaseRefresh() throws Exception {
        try(var f=new Fixture(ARMED,true)) {
            var before=f.received();var originalRead=before.validUntil();
            assertInstanceOf(NativeActionPort.AckReceived.class,f.actual.submitDateSentinelArm(before,prepared(before,ARM),f.clock.instant().plusSeconds(30)));
            zero(f.actual.cancelDateSentinel(before,f.clock.instant().plusSeconds(30)));
            f.clock.set(f.parent.plusSeconds(1));var until=f.clock.instant().plusSeconds(30);
            var statusAck=assertInstanceOf(NativeActionPort.AckReceived.class,f.actual.readDateSentinelStatus(before,until));
            original(statusAck,f.source.status,f.source.statusAck,f.source.statusRequests.getLast());
            var status=ClockStatusRead.decode(statusAck);assertEquals(LateOutcome.State.TRIGGERED,status.state());assertTrue(status.pauseObserved());
            assertEquals(f.parent,before.activeDeadline());assertEquals(originalRead,before.validUntil());
            var cancelled=assertInstanceOf(NativeActionPort.AckReceived.class,f.actual.cancelDateSentinel(before,until));
            original(cancelled,f.source.cancel,f.source.cancelAck,f.source.cancels.getLast());
            var terminal=AdvancePrimitives.acknowledgedSentinel(cancelled,ClockStatusRead.CANCEL_PREFIX+"1");
            assertEquals(status,terminal);assertEquals(LateOutcome.State.TRIGGERED,terminal.state());
            var request=NativeWire.decodeExecuteRequest(f.source.cancels.getLast());
            assertEquals(ClockStatusRead.CANCEL_PREFIX+"1",request.step());assertEquals(Optional.of(before.frame().nativeRevision()),request.expectedRevision());
            assertEquals(0,NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value())).size());
            assertEquals("available",NativeWire.object(NativeWire.parse(cancelled.originalResultToken().orElseThrow().bytes())).path("status").textValue());
            zero(f.actual.cancelDateSentinel(before,until));counts(f,1,1,1,1);
        }
    }

    @Test void observedEvaluationFailureBlocksCleanupAndClockWritesWithoutRelabellingTheReadAsAWorldUnknown() throws Exception {
        try(var f=new Fixture(ARMED,true)) {
            var before=f.received();Instant originalLease=before.validUntil();var until=f.clock.instant().plusSeconds(30);
            assertInstanceOf(NativeActionPort.AckReceived.class,f.actual.submitDateSentinelArm(before,prepared(before,ARM),until));
            // Explicit negative derivative of the SHA-checked C++ TRIGGERED packet. This is not a new producer oracle.
            f.source.status=evaluationFailure(packet(TRIGGERED));
            var failed=assertInstanceOf(NativeActionPort.AckReceived.class,f.actual.readDateSentinelStatus(before,until));
            original(failed,f.source.status,f.source.statusAck,f.source.statusRequests.getLast());
            assertEquals(LateOutcome.State.FAILED,ClockStatusRead.decode(failed).state());
            assertTrue(ClockStatusRead.decode(failed).abnormal());
            zero(f.actual.cancelDateSentinel(before,until));counts(f,1,1,1,0);
            var full=assertInstanceOf(NativeGameTransport.FullClockReceived.class,f.actual.readFullClockFrameReceived(until));
            zero(f.actual.cancelDateSentinel(before,full,until));counts(f,2,1,1,0);
            var speed=FullSnapshotClockControl.request("set-speed-3",full.frame().snapshotId(),full.frame().nativeRevision(),until);
            zero(f.actual.submitFullClockControl(full,speed,until));counts(f,2,1,1,0);
            // A contradictory later peer read cannot erase the already retained failure or grant another control write.
            f.source.status=packet(TRIGGERED);
            assertInstanceOf(NativeActionPort.AckReceived.class,f.actual.readDateSentinelStatus(before,until));
            zero(f.actual.cancelDateSentinel(before,until));counts(f,2,1,2,0);
            assertEquals(originalLease,before.validUntil());assertEquals(f.parent,before.activeDeadline());
        }
    }

    @Test void anUncertainCancelKeepsItsActualOriginalAckAndNeverWritesAnotherRequest() throws Exception {
        try(var f=new Fixture(ARMED,true)) {
            var before=f.received();var until=f.clock.instant().plusSeconds(30);
            assertInstanceOf(NativeActionPort.AckReceived.class,f.actual.submitDateSentinelArm(before,prepared(before,ARM),until));
            assertInstanceOf(NativeActionPort.AckReceived.class,f.actual.readDateSentinelStatus(before,until));
            // Explicit conflicting-generation derivative; only the existing positive packet is the C++ oracle.
            ObjectNode wrong=NativeWire.object(NativeWire.parse(f.source.cancel.envelope())).deepCopy();
            ((ObjectNode)wrong.path("result").path("tactical_daily_sentinel")).put("generation",2);
            f.source.cancel=ack(StrictJson.canonical(wrong));
            var unknown=assertInstanceOf(NativeActionPort.Unknown.class,f.actual.cancelDateSentinel(before,until));
            var actual=f.actual.originalIndeterminateFullClockAcknowledgement(unknown.requestId()).orElseThrow();
            original(actual,f.source.cancel,f.source.cancelAck,f.source.cancels.getLast());
            assertArrayEquals(actual.originalFrame().bytes(),unknown.rawReturn().orElseThrow().bytes());
            assertArrayEquals(actual.outbound().orElseThrow().originalPacket(),unknown.originalRequestPacket());
            assertEquals(unknown,f.actual.cancelDateSentinel(before,until));counts(f,1,1,1,1);
            assertEquals(f.parent,before.activeDeadline());
        }
    }
    private static Ack evaluationFailure(Ack positive) throws IOException {
        ObjectNode frame=NativeWire.object(NativeWire.parse(positive.envelope())).deepCopy();
        var status=(ObjectNode)frame.path("result").path("tactical_daily_sentinel");
        status.put("state","failed").put("abnormal",true).put("trigger_flags",status.path("trigger_flags").longValue()|(1L<<15));
        ((com.fasterxml.jackson.databind.node.ArrayNode)status.path("trigger_reasons")).add("evaluation_failure");
        return ack(StrictJson.canonical(frame));
    }

    @Test void pausedIdleCleanupRequiresAnExplicitCurrentPrivateFullFromTheSameIssuer() throws Exception {
        try(var f=new Fixture(ARMED,true);var foreign=new Fixture(ARMED,true)) {
            var before=f.received();var until=f.clock.instant().plusSeconds(30);
            assertInstanceOf(NativeActionPort.AckReceived.class,f.actual.submitDateSentinelArm(before,prepared(before,ARM),until));
            zero(f.actual.cancelDateSentinel(before,until));counts(f,1,1,0,0);
            var paused=assertInstanceOf(NativeGameTransport.FullClockReceived.class,f.actual.readFullClockFrameReceived(until));
            var wrong=assertInstanceOf(NativeGameTransport.FullClockReceived.class,foreign.actual.readFullClockFrameReceived(until));
            zero(f.actual.cancelDateSentinel(before,wrong,until));counts(f,2,1,0,0);counts(foreign,1,0,0,0);
            f.source.cancel=packet(CANCEL_IDLE);
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,f.actual.cancelDateSentinel(before,paused,until));
            original(ack,f.source.cancel,f.source.cancelAck,f.source.cancels.getLast());
            var idle=AdvancePrimitives.acknowledgedSentinel(ack,ClockStatusRead.CANCEL_PREFIX+"1");
            assertEquals(LateOutcome.State.IDLE,idle.state());assertEquals("1",idle.generation().decimal());
            assertEquals("available",NativeWire.object(NativeWire.parse(ack.originalResultToken().orElseThrow().bytes())).path("status").textValue());
            var request=NativeWire.decodeExecuteRequest(f.source.cancels.getLast());
            assertEquals(0,NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value())).size());
            zero(f.actual.cancelDateSentinel(before,paused,until));
            var speed=FullSnapshotClockControl.request("set-speed-3",paused.frame().snapshotId(),paused.frame().nativeRevision(),until);
            zero(f.actual.submitFullClockControl(paused,speed,until));counts(f,2,1,0,1);
            assertEquals(f.parent,before.activeDeadline());
        }
    }

    private static NativeRequest prepared(NativeGameTransport.DateArmReceived before,String step) {
        return FullSnapshotDateSentinelArm.request(step,before.frame().snapshotId(),before.frame().nativeRevision(),before.activeDeadline());
    }
    private static void original(NativeActionPort.AckReceived ack,Ack cpp,byte[] response,byte[] request) throws Exception {
        assertEquals(cpp.ok(),ack.nativeOk());assertArrayEquals(cpp.token(),ack.originalResultToken().orElseThrow().bytes());
        assertArrayEquals(response,ack.originalPacket());assertArrayEquals(request,ack.outbound().orElseThrow().originalPacket());
        assertEquals(NativeWire.decodeExecuteRequest(request).requestId(),ack.requestId());ack.custody().orElseThrow().verify(ack);
    }
    private static void zero(NativeActionPort.DispatchOutcome outcome) {
        var zero=assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,outcome);
        assertEquals(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE,zero.proof().stage());assertEquals(0,zero.proof().requestBytesWritten());
    }
    private static void counts(Fixture f,int full,int arm,int status,int cancel) {
        assertEquals(full,f.source.fullQueries);assertEquals(arm,f.source.arms.size());assertEquals(status,f.source.statusRequests.size());assertEquals(cancel,f.source.cancels.size());
        assertEquals(full+arm+status+cancel,f.source.writes);assertEquals(0,f.source.pauseWrites);
    }

    private static SnapshotCpp snapshot() throws Exception {
        byte[] raw=fixture(FULL);var frame=assertInstanceOf(NativeWire.Snapshot.class,NativeWire.decode(NativeWire.packet(raw)));
        return new SnapshotCpp(raw,frame.state().value(),frame.snapshotId(),frame.revision());
    }
    private static Ack packet(Input input) throws Exception {
        Input manifest=input.name().startsWith("status/")?STATUS_MANIFEST:input.name().startsWith("negative/")?NEGATIVE_MANIFEST:CANCEL_MANIFEST;
        var rows=NativeWire.object(NativeWire.parse(fixture(manifest))).path("packets");int found=0;
        String name=input.name().substring(input.name().lastIndexOf('/')+1);
        for(var row:rows)if(row.path("path").textValue().replace((char)92,'/').endsWith("/"+name)) {
            assertEquals(input.bytes(),row.path("bytes").intValue());assertEquals(input.sha256(),row.path("sha256").textValue());found++;
        }
        assertEquals(1,found);return ack(fixture(input));
    }
    private static Ack ack(byte[] raw) throws IOException {
        var frame=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(NativeWire.packet(raw)));
        return new Ack(raw,frame.result().token().orElseThrow().value(),frame.requestId(),frame.nativeOk());
    }
    private static byte[] fixture(Input input) throws Exception {
        String directory=System.getProperty("xar.native.dateArm1210.fixtures");byte[] raw;
        if(directory==null||directory.isBlank()) {
            try(var stream=NativeDateSentinelArmPortTest.class.getResourceAsStream("/newnative/date-arm1210/"+input.name())) {
                if(stream==null)throw new IOException("exact C++ Date fixture missing: "+input.name());raw=stream.readNBytes(input.bytes()+1);
            }
        } else {
            var root=Path.of(directory);if(!root.isAbsolute())throw new IOException("absolute exact Date fixture directory required");
            try(var stream=Files.newInputStream(root.resolve(input.name()))){raw=stream.readNBytes(input.bytes()+1);}
        }
        assertEquals(input.bytes(),raw.length);assertEquals(input.sha256(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
        return raw;
    }
    private static ObjectNode hello(boolean dateCapabilities) {
        var row=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",1)
                .put("bridge_version",BRIDGE).put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256())
                .put("game_adapter_id",ADAPTER).put("game_adapter_status","ready").put("ck3_build_match",true);
        var caps=row.putArray("capabilities").add("game.state.snapshot").add(NativeFreshSnapshotPort.CAPABILITY).add("game.command.set-speed-3");
        if(dateCapabilities)caps.add(ClockStatusRead.ARM_CAP).add(ClockStatusRead.STATUS_CAP).add(ClockStatusRead.CANCEL_CAP).add("game.guard.date-only-postday.v1");
        return row;
    }
    private static final class Fixture implements AutoCloseable {
        final MutableClock clock=new MutableClock(Instant.now());final Instant parent=clock.instant().plusSeconds(600);
        final Replay source;final NativeGameTransport actual;
        Fixture(Input arm,boolean capabilities) throws Exception {
            source=new Replay(snapshot(),packet(arm),packet(TRIGGERED),packet(CANCEL_TERMINAL),hello(capabilities),clock);String slash=Character.toString(92);
            var config=new NativePipeEndpoint.Config(slash+slash+"."+slash+"pipe"+slash+"date-arm1210-software","date-arm1210-software",GAME,
                    "date-arm1210-session",BRIDGE,BUILD.executableSha256(),ADAPTER);
            actual=new NativeGameTransport(source,config,32,32,List.of(),clock,Duration.ofSeconds(60));
        }
        NativeGameTransport.DateArmReceived received() throws Exception {
            var before=assertInstanceOf(NativeGameTransport.DateArmReceived.class,actual.readDateSentinelArmReceived(parent));
            assertSame(before.frame(),before.original().originalFrame());assertArrayEquals(source.cpp.state(),before.frame().state().bytes());
            var read=before.original();NativeFreshSnapshotPort.verifyOriginal(read.acknowledgement(),read.originalFrame(),read.snapshotReceived());
            assertArrayEquals(source.fullSnapshot,read.originalFrame().originalPacket());assertArrayEquals(source.fullAck,read.acknowledgement().originalPacket());
            return before;
        }
        @Override public void close() throws IOException {actual.close();}
    }
    private static final class MutableClock extends Clock {
        private Instant now;MutableClock(Instant now){this.now=now;}
        void set(Instant next){assertFalse(next.isBefore(now));now=next;}
        @Override public ZoneId getZone(){return ZoneOffset.UTC;}
        @Override public Clock withZone(ZoneId zone){if(!ZoneOffset.UTC.equals(zone))throw new IllegalArgumentException("UTC software replay only");return this;}
        @Override public Instant instant(){return now;}
    }

    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets=new ArrayDeque<>();final SnapshotCpp cpp;final Ack arm;Ack status,cancel;final MutableClock clock;
        final List<byte[]> arms=new ArrayList<>(),statusRequests=new ArrayList<>(),cancels=new ArrayList<>();
        int fullQueries,writes,pauseWrites;boolean closed,backgroundReady=true;
        byte[] fullSnapshot,fullAck,armAck,statusAck,cancelAck;Instant lastFullDeadline,lastArmDeadline;
        Replay(SnapshotCpp cpp,Ack arm,Ack status,Ack cancel,ObjectNode hello,MutableClock clock) throws IOException {
            this.cpp=cpp;this.arm=arm;this.status=status;this.cancel=cancel;this.clock=clock;packets.add(NativeWire.packet(StrictJson.canonical(hello)));
        }
        @Override public void verify() throws IOException {if(closed)throw new IOException("software source closed");}
        @Override public void verifyCoreControlWindowPolicy() throws IOException {verify();if(!backgroundReady)throw new IOException("software min-policy failed");}
        private void check(Instant until) throws IOException {verify();if(!clock.instant().isBefore(until))throw new IOException("software operation deadline expired");}
        @Override public void awaitConnection(Instant until) throws IOException {check(until);}
        @Override public byte[] readPacket(Instant until) throws IOException {
            check(until);if(packets.isEmpty())throw new IOException("software response absent");return packets.removeFirst();
        }
        @Override public void writePacket(byte[] raw,Instant until) throws IOException {
            check(until);var request=NativeWire.decodeExecuteRequest(raw);writes++;
            if(request.step().equals(NativeFreshSnapshotPort.STEP)) {
                fullQueries++;lastFullDeadline=until;assertEquals(Optional.of(BigInteger.ZERO),request.expectedRevision());
                assertEquals(0,NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value())).size());
                String body=replaceOnce(new String(cpp.envelope(),StandardCharsets.UTF_8),field("read_request_id","full-producer-original"),field("read_request_id",request.requestId()));
                fullSnapshot=NativeWire.packet(body.getBytes(StandardCharsets.UTF_8));
                assertArrayEquals(cpp.state(),assertInstanceOf(NativeWire.Snapshot.class,NativeWire.decode(fullSnapshot)).state().value());
                // Explicit software fresh READ ACK; Snapshot state remains the actual C++ byte oracle.
                var ack=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",request.requestId()).put("ok",true);
                ack.putObject("result").put("schema",NativeFreshSnapshotPort.RESULT_SCHEMA).put("request_id",request.requestId()).put("snapshot_id",cpp.id()).put("revision",cpp.revision());
                fullAck=NativeWire.packet(StrictJson.canonical(ack));packets.add(fullSnapshot.clone());packets.add(fullAck.clone());return;
            }
            assertEquals(Optional.of(cpp.revision()),request.expectedRevision());assertTrue(request.expectedSnapshotRevision().isEmpty());
            Ack selected;
            if(request.step().startsWith(ClockStatusRead.ARM_PREFIX)) {
                assertEquals(ARM,request.step());arms.add(raw.clone());lastArmDeadline=until;selected=arm;
            } else if(request.step().equals(ClockStatusRead.STEP)) {
                statusRequests.add(raw.clone());selected=status;assertEquals(0,NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value())).size());
            } else if(request.step().startsWith(ClockStatusRead.CANCEL_PREFIX)) {
                assertEquals(ClockStatusRead.CANCEL_PREFIX+"1",request.step());cancels.add(raw.clone());selected=cancel;
                assertEquals(0,NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value())).size());
            } else {
                if(request.step().equals("pause-map"))pauseWrites++;
                throw new IOException("unexpected world command at software boundary: "+request.step());
            }
            // Only outer request_id is new. Original Native result/error fields and tokens are never re-encoded.
            String body=replaceOnce(new String(selected.envelope(),StandardCharsets.UTF_8),field("request_id",selected.id()),field("request_id",request.requestId()));
            byte[] response=NativeWire.packet(body.getBytes(StandardCharsets.UTF_8));
            var decoded=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(response));
            assertArrayEquals(selected.token(),decoded.result().token().orElseThrow().value());assertEquals(selected.ok(),decoded.nativeOk());
            if(request.step().startsWith(ClockStatusRead.ARM_PREFIX))armAck=response;
            else if(request.step().equals(ClockStatusRead.STEP))statusAck=response;else cancelAck=response;
            packets.add(response.clone());
        }
        private static String field(String name,String value){String q=Character.toString(34);return q+name+q+":"+q+value+q;}
        private static String replaceOnce(String body,String token,String replacement){
            int index=body.indexOf(token);assertTrue(index>=0);assertEquals(index,body.lastIndexOf(token));
            return body.substring(0,index)+replacement+body.substring(index+token.length());
        }
        @Override public void close(){closed=true;}
    }
}
