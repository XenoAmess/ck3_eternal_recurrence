package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.FullSnapshotEventOptionControl;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual C++ Full and ACK result bytes through the original receiver. Software custody is not Game proof. */
final class NativeEventOptionControl1210Test {
    private static final BigInteger REVISION=BigInteger.valueOf(11);
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_1210;
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));

    @Test void actualCppFullQueryAndCommandKeepAuthoredOneBasedStepAndZeroBasedOption()throws Exception {
        try(var f=new Fixture("submitted.json",false)) {
            var before=f.full();var query=f.query(before);assertEquals(42,query.eventInstanceId());
            assertEquals(List.of(new EventOptionControlResult.Option(0,true),new EventOptionControlResult.Option(1,true)),query.options());
            assertSame(query,f.transport.readEventOptionsReceived(before,42,f.deadline));assertEquals(2,f.source.writes.size());
            var prepared=FullSnapshotEventOptionControl.select(before.frame().snapshotId(),REVISION,f.deadline,42,1);
            assertEquals("select-event-option-2",prepared.step());
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,f.transport.submitEventOption(query,prepared,f.deadline));
            assertTrue(ack.nativeOk());assertEquals(EventOptionControlResult.Disposition.SUBMITTED,EventOptionControlResult.decode(ack,prepared.step(),REVISION,42).disposition());
            assertArrayEquals(resultToken("submitted.json"),ack.originalResultToken().orElseThrow().bytes());
            assertEquals(3,f.source.writes.size());
            zero(f.transport.submitEventOption(query,prepared,f.deadline));assertEquals(3,f.source.writes.size());
        }
    }
    @Test void unseenDisabledBorrowedAndExtendedOccurrencesNeverEnterACommandWrite()throws Exception {
        try(var f=new Fixture("submitted.json",false);var other=new Fixture("submitted.json",false)) {
            var before=f.full();var query=f.query(before);
            var unseen=FullSnapshotEventOptionControl.select(before.frame().snapshotId(),REVISION,f.deadline,42,2);
            zero(f.transport.submitEventOption(query,unseen,f.deadline));
            var correct=FullSnapshotEventOptionControl.select(before.frame().snapshotId(),REVISION,f.deadline,42,1);
            zero(other.transport.submitEventOption(query,correct,other.deadline));
            zero(f.transport.submitEventOption(query,correct,f.deadline.plusMillis(1)));
            assertEquals(2,f.source.writes.size());assertEquals(0,other.source.writes.size());
        }
    }
    @Test void quietPolicyFailureIsBeforeWriteAndDoesNotConsumeTheActualSource()throws Exception {
        try(var f=new Fixture("submitted.json",false)) {
            var before=f.full();f.source.quiet=false;
            var absent=assertInstanceOf(NativeGameTransport.EventOptionsUnavailable.class,f.transport.readEventOptionsReceived(before,42,f.deadline));zero(absent.original());
            assertEquals(1,f.source.writes.size());f.source.quiet=true;
            var query=f.query(before);f.source.quiet=false;
            var request=FullSnapshotEventOptionControl.select(before.frame().snapshotId(),REVISION,f.deadline,42,1);
            zero(f.transport.submitEventOption(query,request,f.deadline));assertEquals(2,f.source.writes.size());
            f.source.quiet=true;assertInstanceOf(NativeActionPort.AckReceived.class,f.transport.submitEventOption(query,request,f.deadline));
        }
    }
    @Test void actualCppHandledNegativeIsADeterminateRejectionDespiteOuterOkTrue()throws Exception {
        try(var f=new Fixture("option-disabled.json",false)) {
            var before=f.full();var query=f.query(before);var request=FullSnapshotEventOptionControl.select(before.frame().snapshotId(),REVISION,f.deadline,42,1);
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,f.transport.submitEventOption(query,request,f.deadline));
            assertTrue(ack.nativeOk());assertEquals(EventOptionControlResult.Disposition.REJECTED_BEFORE_EFFECT,EventOptionControlResult.decode(ack,request.step(),REVISION,42).disposition());
            assertArrayEquals(resultToken("option-disabled.json"),ack.originalResultToken().orElseThrow().bytes());
        }
    }
    @Test void malformedAfterWriteIsStickyUnknownWithOriginalBytesAndNoReplayAcrossNewFull()throws Exception {
        try(var f=new Fixture("submitted.json",true)) {
            var before=f.full();var query=f.query(before);var request=FullSnapshotEventOptionControl.select(before.frame().snapshotId(),REVISION,f.deadline,42,1);
            var unknown=assertInstanceOf(NativeActionPort.Unknown.class,f.transport.submitEventOption(query,request,f.deadline));
            var ack=f.transport.originalIndeterminateFullClockAcknowledgement(unknown.requestId()).orElseThrow();
            assertArrayEquals(ack.originalFrame().bytes(),unknown.rawReturn().orElseThrow().bytes());
            assertSame(unknown,f.transport.submitEventOption(query,request,f.deadline));
            var next=f.full();assertSame(unknown,f.transport.submitEventOption(query,request,f.deadline));
            assertEquals(4,f.source.writes.size());next.requireOriginal(f.transport,f.deadline);
        }
    }
    @Test void sourceEventMismatchIsBeforeQueryWrite()throws Exception {
        try(var f=new Fixture("submitted.json",false)) {
            var before=f.full();var absent=assertInstanceOf(NativeGameTransport.EventOptionsUnavailable.class,f.transport.readEventOptionsReceived(before,43,f.deadline));
            zero(absent.original());assertEquals(1,f.source.writes.size());
        }
    }
    private static void zero(NativeActionPort.DispatchOutcome value) {
        var rejected=assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,value);
        assertEquals(0,rejected.proof().requestBytesWritten());assertEquals(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE,rejected.proof().stage());
    }
    private static byte[] resource(String path)throws IOException {
        try(var in=NativeEventOptionControl1210Test.class.getResourceAsStream(path)) {
            if(in==null)throw new IOException("C++ producer fixture missing: "+path);return in.readAllBytes();
        }
    }
    private static byte[] cpp(String name)throws Exception {
        var manifest=NativeWire.object(NativeWire.parse(resource("/newnative/event-options1210/producer.json")));
        assertFalse(manifest.path("live").booleanValue());assertEquals("4-8e1c2f1861",manifest.path("machine_id").textValue());
        byte[] raw=resource("/newnative/event-options1210/"+name);int found=0;
        for(var row:manifest.path("packets"))if(name.equals(row.path("file").textValue())) {
            found++;assertEquals(raw.length,row.path("bytes").intValue());
            assertEquals(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)),row.path("sha256").textValue());
        }
        assertEquals(1,found);return raw;
    }
    private static byte[] resultToken(String name)throws Exception {
        return assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(NativeWire.packet(cpp(name)))).result().token().orElseThrow().value();
    }
    private static final class Fixture implements AutoCloseable {
        final Instant now=Instant.now(),deadline=now.plusSeconds(120);
        final Replay source;final NativeGameTransport transport;
        Fixture(String selected,boolean malformed)throws Exception {
            source=new Replay(selected,malformed);
            String slash=Character.toString(92);var config=new NativePipeEndpoint.Config(slash+slash+"."+slash+"pipe"+slash+"event1210-software",
                    "event1210-software",GAME,"event1210-software-session","event1210-software",BUILD.executableSha256(),"ck3-1.21.0-msvc-x64");
            transport=new NativeGameTransport(source,config,32,32,List.of(),Clock.fixed(now,ZoneOffset.UTC));
        }
        NativeGameTransport.FullClockReceived full()throws Exception {
            return assertInstanceOf(NativeGameTransport.FullClockReceived.class,transport.readFullClockFrameReceived(deadline));
        }
        NativeGameTransport.EventOptionsReceived query(NativeGameTransport.FullClockReceived before)throws Exception {
            return assertInstanceOf(NativeGameTransport.EventOptionsReceived.class,transport.readEventOptionsReceived(before,42,deadline));
        }
        @Override public void close()throws IOException {transport.close();}
    }
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets=new ArrayDeque<>();final List<byte[]> writes=new ArrayList<>();
        final String selected;final boolean malformed;boolean quiet=true,closed;
        Replay(String selected,boolean malformed)throws Exception {
            this.selected=selected;this.malformed=malformed;
            var hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",42).put("connection_generation",1)
                    .put("bridge_version","event1210-software").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256())
                    .put("game_adapter_id","ck3-1.21.0-msvc-x64").put("game_adapter_status","ready").put("ck3_build_match",true);
            hello.putArray("capabilities").add("game.state.snapshot").add(NativeFreshSnapshotPort.CAPABILITY)
                    .add(FullSnapshotEventOptionControl.QUERY_CAPABILITY).add("game.command.select-event-option-2");
            packets.add(NativeWire.packet(StrictJson.canonical(hello)));
        }
        @Override public void verify()throws IOException {if(closed)throw new IOException("software source closed");}
        @Override public void verifyCoreControlWindowPolicy()throws IOException {verify();if(!quiet)throw new IOException("software quiet guard false");}
        @Override public void awaitConnection(Instant until)throws IOException {verify();}
        @Override public byte[] readPacket(Instant until)throws IOException {verify();if(packets.isEmpty())throw new IOException("software packet absent");return packets.removeFirst();}
        @Override public void writePacket(byte[] packet,Instant until)throws IOException {
            verify();writes.add(packet.clone());var request=NativeWire.decodeExecuteRequest(packet);
            try {
                if(request.step().equals(NativeFreshSnapshotPort.STEP)) {
                    byte[] original=resource("/newnative/full1210/full-snapshot-producer-102.json");
                    assertEquals("a27f2dd30ad69b8927a133509a25be216bf7ce250fdf0a9b325bece78d355ae5",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)));
                    String body=new String(original,StandardCharsets.UTF_8).replace("\"read_request_id\":\"full-producer-original\"","\"read_request_id\":\""+request.requestId()+"\"");
                    packets.add(NativeWire.packet(body.getBytes(StandardCharsets.UTF_8)));
                    var ack=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",request.requestId()).put("ok",true);
                    ack.putObject("result").put("schema",NativeFreshSnapshotPort.RESULT_SCHEMA).put("request_id",request.requestId()).put("snapshot_id","native:11").put("revision",REVISION);
                    packets.add(NativeWire.packet(StrictJson.canonical(ack)));
                } else {
                    assertEquals(Optional.of(REVISION),request.expectedRevision());
                    byte[] original=cpp(request.step().equals(FullSnapshotEventOptionControl.QUERY_STEP)?"available.json":selected);
                    String body=new String(original,StandardCharsets.UTF_8).replace("\"request_id\":\"event-option-test\"","\"request_id\":\""+request.requestId()+"\"");
                    if(malformed&&!request.step().equals(FullSnapshotEventOptionControl.QUERY_STEP))body=body.replace("\"native_option_index\":1","\"native_option_index\":0");
                    packets.add(NativeWire.packet(body.getBytes(StandardCharsets.UTF_8)));
                }
            }catch(IOException error){throw error;}catch(Exception error){throw new IOException(error);}
        }
        @Override public void close(){closed=true;}
    }
}
