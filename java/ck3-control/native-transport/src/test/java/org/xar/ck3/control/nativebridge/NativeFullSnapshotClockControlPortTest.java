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
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.FullSnapshotClockControl;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Real C++ DATA through the sole software receive/custody path. No Game, extra world
 * query, physical SAVE, complete Driver adoption or effect completion is qualified here. */
final class NativeFullSnapshotClockControlPortTest {
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_1210;
    private static final String ADAPTER="ck3-1.21.0-msvc-x64",BRIDGE="software-full-clock1210";
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private record Input(String name,int bytes,String sha256) { }
    private record SnapshotCpp(byte[] envelope,byte[] state,String id,BigInteger revision) { }
    private record AckCpp(byte[] envelope,byte[] token,String id,boolean nativeOk) { }
    private static final Input FULL=new Input("full-snapshot-producer-002.json",1171,"5eca02fea7c3f5095d675238f59b69b8d166ed17a0bd4c208b0e133700d7e550");
    private static final Input FULL_MANIFEST=new Input("FULL-SNAPSHOT-PRODUCER02.json",1053,"be2a4004b0ad1312708fd3b393b8cedca85b14a6da64bb2d807aa7eba631298b");
    private static final Input ACK_MANIFEST=new Input("FULL-CLOCK-ACK-PRODUCER01.json",3873,"58055e9ba6216b74c8b36227e428922245551fd427d95422aa7d3e4e89109025");
    private static final Input SUBMITTED=new Input("full-clock-ack-submitted01.json",531,"77f8f6680338ebda5030ed01a53ffcf66d0f942d5e61d4547561f988899209ef");
    private static final Input SAVE=new Input("full-clock-ack-save01.json",670,"39b71f7ec0baf811e18256cc1cac2fdf4b2e8e6523370b8ef41b77d57485e264");
    private static final Input EXPIRED=new Input("full-clock-ack-expired01.json",553,"378077bfec96774029e25ce1e74708de53c7df63b1e8fd3cbd5b763944346e2a");
    private static final Input INDETERMINATE=new Input("full-clock-ack-indeterminate01.json",533,"fc9b6e338c2fb775950830e0a2c8437df6c862c4a9c406635cf9feb595f2ffd0");
    private static final Input ATTEMPTED_REJECTED=new Input("full-clock-ack-attempted-rejected01.json",529,"40b1407689e45d5ba4c18309c83f81382b0d381120545dae66ba75e80adfac71");
    private static final Input CORE=new Input("core-producer-partial.json",599,"1d7df534e64680a88b4a40665b175c15b1928c47f0cdd0c5058ef381063d9ec6");
    private static final Input GOLD=new Input("personal-gold-producer-partial01.json",1233,"06fcc7b418e46dff6a27ab72533ca7b8444077d33ccc7aaeadd07cfbc93d208f");
    private static final Input ACTOR=new Input("actor-foundation-producer-empty01.json",1582,"e7c66e80cd0f45e238de06957de5b7e9789bdfae51f0c7c3c5d2b85e0dff57a0");

    @Test void actualFullReadAndSubmittedClockAckRetainPreparedRevisionDeadlineAndOneWrite() throws Exception {
        try(var f=new Fixture(SUBMITTED,true,null)) {
            var before=f.received();var until=before.validUntil().minusSeconds(5);var prepared=prepared(before,"set-speed-3",until);
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,f.actual.submitFullClockControl(before,prepared,until));
            assertTrue(ack.nativeOk());originalControl(f,ack,SUBMITTED,prepared,before,until);
            var data=NativeWire.object(NativeWire.parse(ack.originalResultToken().orElseThrow().bytes()));
            assertEquals("submitted",data.path("queue_status").textValue());assertTrue(data.path("accepted").booleanValue());
            assertTrue(data.path("effect_attempted").booleanValue());assertTrue(data.path("full_snapshot_before_verified").booleanValue());
            assertFalse(data.path("complete_snapshot").booleanValue());assertFalse(data.path("physical_save_confirmed").booleanValue());
            Object fullRole=before;assertFalse(fullRole instanceof NativeGameTransport.CoreRead);assertFalse(fullRole instanceof NativeGameTransport.CoreReceived);
            zero(f.actual.submitFullClockControl(before,prepared,until));counts(f,1,1,0);
        }
    }
    @Test void saveSubmissionPreservesNativeQueueFactsWithoutPhysicalSaveOrReplayCredit() throws Exception {
        try(var f=new Fixture(SAVE,true,null)) {
            var before=f.received();var until=before.validUntil().minusSeconds(5);var prepared=prepared(before,"save-checkpoint",until);
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,f.actual.submitFullClockControl(before,prepared,until));
            assertTrue(ack.nativeOk());originalControl(f,ack,SAVE,prepared,before,until);
            var data=NativeWire.object(NativeWire.parse(ack.originalResultToken().orElseThrow().bytes()));
            assertEquals("xar_checkpoint",data.path("save_name").textValue());assertEquals("submitted",data.path("status").textValue());
            assertEquals(19,data.path("submission").path("sequence").intValue());assertEquals(123456,data.path("submission").path("date_raw").intValue());
            assertFalse(data.path("physical_save_confirmed").booleanValue());assertFalse(data.path("complete_snapshot").booleanValue());
            zero(f.actual.submitFullClockControl(before,prepared,until));counts(f,1,1,0);
        }
    }
    @Test void missingCapabilityForeignIssuerAndChangedPreparedDataCannotEnterAControlWrite() throws Exception {
        try(var missing=new Fixture(SUBMITTED,false,null)) {
            var before=missing.received();var until=before.validUntil().minusSeconds(5);
            zero(missing.actual.submitFullClockControl(before,prepared(before,"set-speed-3",until),until));counts(missing,1,0,0);
        }
        try(var owner=new Fixture(SUBMITTED,true,null);var foreign=new Fixture(SUBMITTED,true,null)) {
            var before=owner.received();assertEquals(owner.actual.awaitHello(before.validUntil()),foreign.actual.awaitHello(before.validUntil()));var until=before.validUntil().minusSeconds(5);
            zero(foreign.actual.submitFullClockControl(before,prepared(before,"set-speed-3",until),until));
            counts(owner,1,0,0);counts(foreign,0,0,0);
        }
        try(var f=new Fixture(SUBMITTED,true,null)) {
            var before=f.received();var until=before.validUntil().minusSeconds(5);var canonical=prepared(before,"set-speed-3",until);
            for(String field:List.of("native_revision","snapshot_id","deadline_unix_ms")) {
                var body=NativeWire.object(NativeWire.parse(canonical.additionalFields().bytes())).deepCopy();
                var claim=(ObjectNode)body.get("full_snapshot_clock_control");
                if(field.equals("native_revision"))claim.put(field,before.frame().nativeRevision().add(BigInteger.ONE));
                else if(field.equals("snapshot_id"))claim.put(field,"native:999");else claim.put(field,until.plusMillis(1).toEpochMilli());
                var changed=new NativeRequest(canonical.step(),canonical.requiredCapability(),new RawJson(StrictJson.canonical(body)));
                zero(f.actual.submitFullClockControl(before,changed,until));counts(f,1,0,0);
            }
            var capability=new NativeRequest(canonical.step(),"game.command.pause-map",canonical.additionalFields());
            zero(f.actual.submitFullClockControl(before,capability,until));counts(f,1,0,0);
            assertInstanceOf(NativeActionPort.AckReceived.class,f.actual.submitFullClockControl(before,canonical,until));counts(f,1,1,0);
        }
    }

    @Test void extendedExpiredClosedAndSupersededFullOccurrencesRefuseWithoutControlWrites() throws Exception {
        try(var f=new Fixture(SUBMITTED,true,null)) {
            var before=f.received();var later=before.validUntil().plusNanos(1);
            zero(f.actual.submitFullClockControl(before,prepared(before,"set-speed-3",later),later));counts(f,1,0,0);
            f.clock.set(before.validUntil());
            zero(f.actual.submitFullClockControl(before,prepared(before,"set-speed-3",before.validUntil()),before.validUntil()));counts(f,1,0,0);
        }
        try(var f=new Fixture(SUBMITTED,true,null)) {
            var before=f.received();var until=before.validUntil().minusSeconds(5);f.actual.close();
            zero(f.actual.submitFullClockControl(before,prepared(before,"set-speed-3",until),until));counts(f,1,0,0);
        }
        try(var f=new Fixture(SUBMITTED,true,null)) {
            var older=f.received();var newer=f.received();assertNotSame(older.frame(),newer.frame());
            var until=older.validUntil().minusSeconds(5);
            zero(f.actual.submitFullClockControl(older,prepared(older,"set-speed-3",until),until));counts(f,2,0,0);
            newer.requireOriginal(f.actual,newer.validUntil());
        }
    }
    @Test void failedBackgroundPolicyDoesNotWriteOrConsumeTheOriginalFullClockReceipt() throws Exception {
        try(var f=new Fixture(SUBMITTED,true,null)) {
            var before=f.received();var until=before.validUntil().minusSeconds(5);var prepared=prepared(before,"set-speed-3",until);
            f.source.backgroundReady=false;zero(f.actual.submitFullClockControl(before,prepared,until));counts(f,1,0,0);
            f.source.backgroundReady=true;
            assertInstanceOf(NativeActionPort.AckReceived.class,f.actual.submitFullClockControl(before,prepared,until));counts(f,1,1,0);
        }
    }
    @Test void originalExpiredEffectFalseAckRemainsADeterminateNegativeWithoutInventingZeroDispatch() throws Exception {
        try(var f=new Fixture(EXPIRED,true,null)) {
            var before=f.received();var until=before.validUntil().minusSeconds(5);var prepared=prepared(before,"set-speed-3",until);
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,f.actual.submitFullClockControl(before,prepared,until));
            assertFalse(ack.nativeOk());originalControl(f,ack,EXPIRED,prepared,before,until);
            var result=NativeWire.object(NativeWire.parse(ack.originalResultToken().orElseThrow().bytes()));
            assertEquals("expired",result.path("queue_status").textValue());assertFalse(result.path("effect_attempted").booleanValue());
            assertTrue(f.actual.originalIndeterminateFullClockAcknowledgement(ack.requestId()).isEmpty());
            zero(f.actual.submitFullClockControl(before,prepared,until));counts(f,1,1,0);
        }
    }
    @Test void indeterminateAndAttemptedRejectionAreStickyUnknownWithOriginalAckAndNoSecondTokenWrite() throws Exception {
        for(var input:List.of(INDETERMINATE,ATTEMPTED_REJECTED))try(var f=new Fixture(input,true,null)) {
            var before=f.received();var until=before.validUntil().minusSeconds(5);var prepared=prepared(before,"set-speed-3",until);
            var unknown=assertInstanceOf(NativeActionPort.Unknown.class,f.actual.submitFullClockControl(before,prepared,until));
            var ack=f.actual.originalIndeterminateFullClockAcknowledgement(unknown.requestId()).orElseThrow();
            assertFalse(ack.nativeOk());originalControl(f,ack,input,prepared,before,until);
            assertArrayEquals(ack.originalFrame().bytes(),unknown.rawReturn().orElseThrow().bytes());
            assertArrayEquals(ack.outbound().orElseThrow().originalPacket(),unknown.originalRequestPacket());
            assertSame(unknown,f.actual.submitFullClockControl(before,prepared,until));counts(f,1,1,0);
            var second=f.received();var next=prepared(second,"save-checkpoint",until);
            assertSame(unknown,f.actual.submitFullClockControl(second,next,until));counts(f,2,1,0);
            second.requireOriginal(f.actual,until);
            assertSame(ack,f.actual.originalIndeterminateFullClockAcknowledgement(unknown.requestId()).orElseThrow());
        }
    }

    @Test void publicReceivedPartialCoreGoldActorAndCorePrivateRoleCannotMintFullClockCustody() throws Exception {
        var gold=ackData(GOLD).token();var actor=ackData(ACTOR).token();var core=fixture(CORE);
        for(byte[] partial:List.of(core,gold,actor))try(var f=new Fixture(SUBMITTED,true,partial)) {
            var unavailable=assertInstanceOf(NativeGameTransport.FullClockReadUnavailable.class,f.actual.readFullClockFrameReceived(f.deadline));
            var original=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,unavailable.original());
            assertTrue(assertInstanceOf(NativeActionPort.AckReceived.class,original.dispatch()).nativeOk());
            assertTrue(f.actual.latestAcceptedSnapshotRevision().isEmpty());counts(f,1,0,0);
        }
        try(var f=new Fixture(SUBMITTED,true,null)) {
            var publicReceived=assertInstanceOf(NativeFreshSnapshotPort.Received.class,f.actual.readFreshFullState(f.deadline));
            Object publicData=publicReceived;assertFalse(publicData instanceof NativeGameTransport.FullClockRead);
            var request=FullSnapshotClockControl.request("set-speed-3",publicReceived.originalFrame().snapshotId(),publicReceived.originalFrame().nativeRevision(),f.deadline);
            zero(f.actual.submitFullClockControl(null,request,f.deadline));counts(f,1,0,0);
        }
        try(var f=new Fixture(SUBMITTED,true,null)) {
            var coreReceived=assertInstanceOf(NativeGameTransport.CoreReceived.class,f.actual.readCoreFrameReceived(f.deadline));
            Object role=coreReceived;assertFalse(role instanceof NativeGameTransport.FullClockRead);assertFalse(role instanceof NativeGameTransport.FullClockReceived);
            var request=FullSnapshotClockControl.request("set-speed-3",f.source.cpp.id(),f.source.cpp.revision(),f.deadline);
            zero(f.actual.submitFullClockControl(null,request,f.deadline));counts(f,0,0,1);
        }
    }

    private static NativeRequest prepared(NativeGameTransport.FullClockReceived before,String step,Instant until) {
        return FullSnapshotClockControl.request(step,before.frame().snapshotId(),before.frame().nativeRevision(),until);
    }
    private static void originalControl(Fixture f,NativeActionPort.AckReceived ack,Input original,NativeRequest prepared,
            NativeGameTransport.FullClockReceived before,Instant until) throws Exception {
        var cpp=effect(original);assertArrayEquals(cpp.token(),ack.originalResultToken().orElseThrow().bytes());
        assertEquals(cpp.nativeOk(),ack.nativeOk());assertArrayEquals(f.source.lastControlAck,ack.originalPacket());
        byte[] outbound=f.source.controls.getLast();assertArrayEquals(outbound,ack.outbound().orElseThrow().originalPacket());
        var command=NativeWire.decodeExecuteRequest(outbound);assertEquals(ack.requestId(),command.requestId());
        assertEquals(prepared.step(),command.step());assertEquals(Optional.of(before.frame().nativeRevision()),command.expectedRevision());
        assertTrue(command.expectedRevision().orElseThrow().signum()>0);assertTrue(command.expectedSnapshotRevision().isEmpty());
        var fields=NativeWire.object(NativeWire.parse(command.normalizedAdditionalFields().value()));assertEquals(1,fields.size());
        assertEquals(StrictJson.parse(prepared.additionalFields().bytes()),StrictJson.parse(command.normalizedAdditionalFields().value()));
        var claim=fields.path("full_snapshot_clock_control");assertEquals(before.frame().snapshotId(),claim.path("snapshot_id").textValue());
        assertEquals(before.frame().nativeRevision(),claim.path("native_revision").bigIntegerValue());
        assertEquals(until.toEpochMilli(),claim.path("deadline_unix_ms").longValue());
        assertFalse(fields.has("core_clock_control"));assertFalse(fields.has("core_control_deadline_unix_ms"));
        var custody=ack.custody().orElseThrow();custody.verify(ack);
        assertTrue(custody.writeEntered().order().compareTo(custody.writeCompleted().order())<0);
        assertTrue(custody.writeCompleted().order().compareTo(custody.responseReceived().order())<0);
        assertEquals(before.frame().session(),custody.session());counts(f,1,1,0);
    }
    private static void zero(NativeActionPort.DispatchOutcome outcome) {
        var zero=assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,outcome);
        assertEquals(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE,zero.proof().stage());assertEquals(0,zero.proof().requestBytesWritten());
    }
    private static void counts(Fixture f,int fullQueries,int controls,int coreQueries) {
        assertEquals(fullQueries,f.source.fullQueries);assertEquals(controls,f.source.controls.size());assertEquals(coreQueries,f.source.coreQueries);
        assertEquals(fullQueries+controls+coreQueries,f.source.writes);
    }
    private static SnapshotCpp snapshot() throws Exception {
        manifestPin(FULL_MANIFEST,FULL);byte[] body=fixture(FULL);
        var decoded=assertInstanceOf(NativeWire.Snapshot.class,NativeWire.decode(NativeWire.packet(body)));
        return new SnapshotCpp(body,decoded.state().value(),decoded.snapshotId(),decoded.revision());
    }
    private static AckCpp effect(Input input) throws Exception {manifestPin(ACK_MANIFEST,input);return ackData(input);}
    private static AckCpp ackData(Input input) throws Exception {
        byte[] body=fixture(input);var decoded=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(NativeWire.packet(body)));
        return new AckCpp(body,decoded.result().token().orElseThrow().value(),decoded.requestId(),decoded.nativeOk());
    }
    private static void manifestPin(Input manifest,Input input) throws Exception {
        var rows=NativeWire.object(NativeWire.parse(fixture(manifest))).path("packets");assertTrue(rows.isArray());int found=0;
        for(var row:rows)if(row.path("path").textValue().replace((char)92,'/').endsWith("/"+input.name())) {
            assertEquals(input.bytes(),row.path("bytes").intValue());assertEquals(input.sha256(),row.path("sha256").textValue());found++;
        }
        assertEquals(1,found);
    }

    private static byte[] fixture(Input input) throws Exception {
        String directory=System.getProperty("xar.native.full-clock1210.fixtures");byte[] body;
        if(directory==null||directory.isBlank()) {
            try(var stream=NativeFullSnapshotClockControlPortTest.class.getResourceAsStream("/newnative/full-clock1210/"+input.name())) {
                if(stream==null)throw new IOException("exact C++ full-clock fixture missing: "+input.name());
                body=stream.readNBytes(input.bytes()+1);
            }
        } else {
            var root=Path.of(directory);if(!root.isAbsolute())throw new IOException("absolute exact C++ fixture directory required");
            try(var stream=Files.newInputStream(root.resolve(input.name()))){body=stream.readNBytes(input.bytes()+1);}
        }
        assertEquals(input.bytes(),body.length);assertEquals(input.sha256(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(body)));
        return body;
    }
    private static ObjectNode hello(boolean controls) {
        var row=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",1)
                .put("bridge_version",BRIDGE).put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256())
                .put("game_adapter_id",ADAPTER).put("game_adapter_status","ready").put("ck3_build_match",true);
        var caps=row.putArray("capabilities").add("game.state.snapshot").add(NativeFreshSnapshotPort.CAPABILITY).add(CoreFrame.CAPABILITY);
        if(controls)caps.add("game.command.set-speed-3").add("game.command.save-checkpoint");return row;
    }
    private static final class Fixture implements AutoCloseable {
        final MutableClock clock=new MutableClock(Instant.now());final Instant deadline=clock.instant().plusSeconds(120);
        final Replay source;final NativeGameTransport actual;
        Fixture(Input effect,boolean capabilities,byte[] negativeState) throws Exception {
            source=new Replay(snapshot(),effect(effect),fixture(CORE),hello(capabilities),negativeState,clock);
            String slash=Character.toString(92);
            var config=new NativePipeEndpoint.Config(slash+slash+"."+slash+"pipe"+slash+"full-clock1210-software","full-clock1210-software",GAME,
                    "full-clock1210-session",BRIDGE,BUILD.executableSha256(),ADAPTER);
            actual=new NativeGameTransport(source,config,32,32,List.of(),clock);
        }
        NativeGameTransport.FullClockReceived received() throws Exception {
            var actualRead=assertInstanceOf(NativeGameTransport.FullClockReceived.class,actual.readFullClockFrameReceived(deadline));
            assertSame(actualRead.original().originalFrame(),actualRead.frame());assertEquals(deadline,actualRead.validUntil());
            assertArrayEquals(source.cpp.state(),actualRead.frame().state().bytes());
            var read=actualRead.original();NativeFreshSnapshotPort.verifyOriginal(read.acknowledgement(),read.originalFrame(),read.snapshotReceived());
            assertArrayEquals(source.lastReadSnapshot,read.originalFrame().originalPacket());assertArrayEquals(source.lastReadAck,read.acknowledgement().originalPacket());
            actualRead.requireOriginal(actual,deadline);return actualRead;
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
        final ArrayDeque<byte[]> packets=new ArrayDeque<>();final List<byte[]> controls=new ArrayList<>();
        final SnapshotCpp cpp;final AckCpp effect;final byte[] core,negativeState;final MutableClock clock;
        int writes,fullQueries,coreQueries;boolean closed,backgroundReady=true;
        byte[] lastReadSnapshot,lastReadAck,lastControlAck;
        Replay(SnapshotCpp cpp,AckCpp effect,byte[] core,ObjectNode hello,byte[] negativeState,MutableClock clock) throws IOException {
            this.cpp=cpp;this.effect=effect;this.core=core.clone();this.clock=clock;this.negativeState=negativeState==null?null:negativeState.clone();
            packets.add(NativeWire.packet(StrictJson.canonical(hello)));
        }
        @Override public void verify() throws IOException {if(closed)throw new IOException("software source closed");}
        @Override public void verifyCoreControlWindowPolicy() throws IOException {verify();if(!backgroundReady)throw new IOException("software background guard unavailable");}
        private void check(Instant until) throws IOException {verify();if(!clock.instant().isBefore(until))throw new IOException("software operation deadline expired");}
        @Override public void awaitConnection(Instant until) throws IOException {check(until);}
        @Override public byte[] readPacket(Instant until) throws IOException {
            check(until);if(packets.isEmpty())throw new IOException("software original packet absent");return packets.removeFirst();
        }
        @Override public void writePacket(byte[] original,Instant until) throws IOException {
            check(until);var command=NativeWire.decodeExecuteRequest(original);writes++;
            if(command.step().equals(NativeFreshSnapshotPort.STEP)) {
                fullQueries++;assertEquals(Optional.of(BigInteger.ZERO),command.expectedRevision());
                assertEquals(0,NativeWire.object(NativeWire.parse(command.normalizedAdditionalFields().value())).size());
                var body=new String(cpp.envelope(),StandardCharsets.UTF_8);
                body=replaceOnce(body,field("read_request_id","full-producer-original"),field("read_request_id",command.requestId()));
                if(negativeState!=null)body=replaceOnce(body,new String(cpp.state(),StandardCharsets.UTF_8),new String(negativeState,StandardCharsets.UTF_8));
                lastReadSnapshot=NativeWire.packet(body.getBytes(StandardCharsets.UTF_8));
                if(negativeState==null)assertArrayEquals(cpp.state(),assertInstanceOf(NativeWire.Snapshot.class,NativeWire.decode(lastReadSnapshot)).state().value());
                // Explicit software fresh-read ACK. The Snapshot state is the actual pinned C++ original.
                var ack=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",command.requestId()).put("ok",true);
                ack.putObject("result").put("schema",NativeFreshSnapshotPort.RESULT_SCHEMA).put("request_id",command.requestId()).put("snapshot_id",cpp.id()).put("revision",cpp.revision());
                lastReadAck=NativeWire.packet(StrictJson.canonical(ack));packets.add(lastReadSnapshot.clone());packets.add(lastReadAck.clone());
            } else if(command.step().equals(CoreFrame.STEP)) {
                coreQueries++;assertEquals(Optional.of(BigInteger.ZERO),command.expectedRevision());
                var ack=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",command.requestId()).put("ok",true);ack.putNull("result");
                String quote=Character.toString(34);String raw=replaceOnce(new String(StrictJson.canonical(ack),StandardCharsets.UTF_8),quote+"result"+quote+":null",quote+"result"+quote+":"+new String(core,StandardCharsets.UTF_8));
                packets.add(NativeWire.packet(raw.getBytes(StandardCharsets.UTF_8)));
            } else {
                assertTrue(List.of("set-speed-3","save-checkpoint").contains(command.step()));controls.add(original.clone());
                assertEquals(Optional.of(cpp.revision()),command.expectedRevision());assertTrue(command.expectedSnapshotRevision().isEmpty());
                // Only the outer software correlation ID changes; the entire C++ result/error token stays original.
                String body=replaceOnce(new String(effect.envelope(),StandardCharsets.UTF_8),field("request_id",effect.id()),field("request_id",command.requestId()));
                lastControlAck=NativeWire.packet(body.getBytes(StandardCharsets.UTF_8));
                var ack=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(lastControlAck));
                assertArrayEquals(effect.token(),ack.result().token().orElseThrow().value());assertEquals(effect.nativeOk(),ack.nativeOk());
                packets.add(lastControlAck.clone());
            }
        }
        private static String field(String name,String value) {String q=Character.toString(34);return q+name+q+":"+q+value+q;}
        private static String replaceOnce(String body,String token,String replacement) {
            int index=body.indexOf(token);assertTrue(index>=0);assertEquals(index,body.lastIndexOf(token));
            return body.substring(0,index)+replacement+body.substring(index+token.length());
        }
        @Override public void close(){closed=true;}
    }
}
