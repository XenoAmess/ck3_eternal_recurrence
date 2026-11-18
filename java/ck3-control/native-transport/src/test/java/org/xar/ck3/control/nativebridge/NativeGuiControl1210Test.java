package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
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
import org.xar.ck3.control.application.action.FullSnapshotGuiControl;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual C++ GUI producer data via private Full/query custody. No Game or completed UI business is asserted. */
final class NativeGuiControl1210Test {
    private static final BigInteger REVISION=BigInteger.valueOf(11), GENERATION=new BigInteger("9007199254740999");
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_1210;
    private static final String ROOT="xfm_market_entry";
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));

    @Test void actualCppFullGuiQueryAndHandledActivationRetainHighGenerationAndOriginalResult()throws Exception {
        try(var f=new Fixture("submitted-handled")) {
            var before=f.full();var gui=f.gui(before);assertEquals(GENERATION,gui.queryGeneration());
            assertEquals(2,gui.controls().size());assertFalse(gui.controls().getFirst().activatable());assertTrue(gui.controls().getLast().activatable());
            var prepared=f.prepared(gui,BigInteger.TWO);
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,f.transport.submitGuiControl(gui,prepared,f.deadline));
            var assessment=GuiControlResult.decode(ack,prepared.step(),REVISION,ROOT,GENERATION,BigInteger.TWO);
            assertEquals(GuiControlResult.Disposition.SUBMITTED,assessment.disposition());assertTrue(assessment.verificationPending());
            assertFalse(assessment.complete());assertArrayEquals(token("submitted-handled"),ack.originalResultToken().orElseThrow().bytes());
            zero(f.transport.submitGuiControl(gui,prepared,f.deadline));assertEquals(3,f.source.writes.size());
        }
    }
    @Test void rootIdentityAndOneActualQueryCannotBeSubstitutedOrExtended()throws Exception {
        try(var f=new Fixture("submitted-handled");var other=new Fixture("submitted-handled")) {
            var before=f.full();var gui=f.gui(before);
            assertSame(gui,f.transport.readGuiReceived(before,ROOT,f.deadline));
            var wrongRoot=assertInstanceOf(NativeGameTransport.GuiUnavailable.class,f.transport.readGuiReceived(before,"other_root",f.deadline));zero(wrongRoot.original());
            zero(other.transport.submitGuiControl(gui,f.prepared(gui,BigInteger.TWO),other.deadline));
            zero(f.transport.submitGuiControl(gui,f.prepared(gui,BigInteger.TWO),f.deadline.plusMillis(1)));
            assertEquals(2,f.source.writes.size());assertTrue(other.source.writes.isEmpty());
        }
    }
    @Test void nonClickableRootAndUnobservedWidgetCannotEnterDispatch()throws Exception {
        try(var f=new Fixture("submitted-handled")) {
            var gui=f.gui(f.full());
            for(BigInteger id:List.of(BigInteger.ONE,BigInteger.valueOf(999)))zero(f.transport.submitGuiControl(gui,f.prepared(gui,id),f.deadline));
            assertEquals(2,f.source.writes.size());
        }
    }
    @Test void quietFailureIsBeforeWriteAndDoesNotConsumeObservedControl()throws Exception {
        try(var f=new Fixture("submitted-handled")) {
            var before=f.full();f.source.quiet=false;
            var absent=assertInstanceOf(NativeGameTransport.GuiUnavailable.class,f.transport.readGuiReceived(before,ROOT,f.deadline));zero(absent.original());
            f.source.quiet=true;var gui=f.gui(before);f.source.quiet=false;
            zero(f.transport.submitGuiControl(gui,f.prepared(gui,BigInteger.TWO),f.deadline));assertEquals(2,f.source.writes.size());
            f.source.quiet=true;assertInstanceOf(NativeActionPort.AckReceived.class,f.transport.submitGuiControl(gui,f.prepared(gui,BigInteger.TWO),f.deadline));
        }
    }
    @Test void unhandledSubmittedAndIndeterminateRetainStickyUnknownAcrossAnotherFull()throws Exception {
        for(String producer:List.of("submitted","indeterminate"))try(var f=new Fixture(producer)) {
            var gui=f.gui(f.full());var request=f.prepared(gui,BigInteger.TWO);
            var unknown=assertInstanceOf(NativeActionPort.Unknown.class,f.transport.submitGuiControl(gui,request,f.deadline));
            var original=f.transport.originalIndeterminateFullClockAcknowledgement(unknown.requestId()).orElseThrow();
            assertArrayEquals(token(producer),original.originalResultToken().orElseThrow().bytes());
            assertArrayEquals(original.originalFrame().bytes(),unknown.rawReturn().orElseThrow().bytes());
            assertSame(unknown,f.transport.submitGuiControl(gui,request,f.deadline));
            var next=f.full();assertSame(unknown,f.transport.submitGuiControl(gui,request,f.deadline));
            assertEquals(4,f.source.writes.size());next.requireOriginal(f.transport,f.deadline);
        }
    }
    @Test void malformedGuiAckRemainsOriginalUnknownWithoutAnotherInvocation()throws Exception {
        try(var f=new Fixture("submitted-handled")) {
            f.source.corrupt=true;var gui=f.gui(f.full());var prepared=f.prepared(gui,BigInteger.TWO);
            var unknown=assertInstanceOf(NativeActionPort.Unknown.class,f.transport.submitGuiControl(gui,prepared,f.deadline));
            assertTrue(f.transport.originalIndeterminateFullClockAcknowledgement(unknown.requestId()).isPresent());
            assertSame(unknown,f.transport.submitGuiControl(gui,prepared,f.deadline));assertEquals(3,f.source.writes.size());
        }
    }
    private static void zero(NativeActionPort.DispatchOutcome value) {
        var rejected=assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,value);assertEquals(0,rejected.proof().requestBytesWritten());
        assertEquals(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE,rejected.proof().stage());
    }
    private static byte[] resource(String path)throws IOException {
        try(var in=NativeGuiControl1210Test.class.getResourceAsStream(path)){if(in==null)throw new IOException("C++ producer fixture missing: "+path);return in.readAllBytes();}
    }
    private static byte[] cpp(String kind)throws Exception {
        byte[] raw=resource("/newnative/gui-control1210/"+kind+".json");
        var manifest=NativeWire.object(NativeWire.parse(resource("/newnative/gui-control1210/producer.json")));int count=0;
        for(var row:manifest.path("packets"))if((kind+".json").equals(row.path("file").textValue())) {
            count++;assertEquals(raw.length,row.path("bytes").intValue());assertEquals(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)),row.path("sha256").textValue());
        }
        assertEquals(1,count);return raw;
    }
    private static byte[] token(String kind)throws Exception {return assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(NativeWire.packet(cpp(kind)))).result().token().orElseThrow().value();}
    private static final class Fixture implements AutoCloseable {
        final Instant now=Instant.now(),deadline=now.plusSeconds(120);final Replay source;final NativeGameTransport transport;
        Fixture(String selected)throws Exception {
            source=new Replay(selected);String slash=Character.toString(92);
            var config=new NativePipeEndpoint.Config(slash+slash+"."+slash+"pipe"+slash+"gui1210-software","gui1210-software",GAME,"gui1210-session","gui1210-software",BUILD.executableSha256(),"ck3-1.21.0-msvc-x64");
            transport=new NativeGameTransport(source,config,32,32,List.of(),Clock.fixed(now,ZoneOffset.UTC));
        }
        NativeGameTransport.FullClockReceived full()throws Exception{return assertInstanceOf(NativeGameTransport.FullClockReceived.class,transport.readFullClockFrameReceived(deadline));}
        NativeGameTransport.GuiReceived gui(NativeGameTransport.FullClockReceived before)throws Exception{return assertInstanceOf(NativeGameTransport.GuiReceived.class,transport.readGuiReceived(before,ROOT,deadline));}
        org.xar.ck3.control.application.action.NativeRequest prepared(NativeGameTransport.GuiReceived gui,BigInteger id){return FullSnapshotGuiControl.activate(gui.fullFrame().snapshotId(),REVISION,deadline,ROOT,gui.queryGeneration(),id);}
        @Override public void close()throws IOException {transport.close();}
    }
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets=new ArrayDeque<>();final List<byte[]> writes=new ArrayList<>();final String selected;boolean quiet=true,closed,corrupt;
        Replay(String selected)throws Exception {
            this.selected=selected;
            var hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",42).put("connection_generation",1)
                    .put("bridge_version","gui1210-software").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256())
                    .put("game_adapter_id","ck3-1.21.0-msvc-x64").put("game_adapter_status","ready").put("ck3_build_match",true);
            hello.putArray("capabilities").add("game.state.snapshot").add(NativeFreshSnapshotPort.CAPABILITY).add(FullSnapshotGuiControl.QUERY_CAPABILITY).add(FullSnapshotGuiControl.ACTIVATE_CAPABILITY);
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
                    byte[] full=resource("/newnative/full1210/full-snapshot-producer-102.json");
                    assertEquals("a27f2dd30ad69b8927a133509a25be216bf7ce250fdf0a9b325bece78d355ae5",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(full)));
                    String body=new String(full,StandardCharsets.UTF_8).replace("\"read_request_id\":\"full-producer-original\"","\"read_request_id\":\""+request.requestId()+"\"");
                    packets.add(NativeWire.packet(body.getBytes(StandardCharsets.UTF_8)));
                    var ack=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",request.requestId()).put("ok",true);
                    ack.putObject("result").put("schema",NativeFreshSnapshotPort.RESULT_SCHEMA).put("request_id",request.requestId()).put("snapshot_id","native:11").put("revision",REVISION);
                    packets.add(NativeWire.packet(StrictJson.canonical(ack)));
                } else {
                    assertEquals(Optional.of(REVISION),request.expectedRevision());
                    String kind=request.step().equals(FullSnapshotGuiControl.QUERY_STEP)?"query":selected;
                    byte[] original=cpp(kind);var decoded=(NativeWire.CommandResult)NativeWire.decode(NativeWire.packet(original));
                    String body=new String(original,StandardCharsets.UTF_8).replace("\"request_id\":\""+decoded.requestId()+"\"","\"request_id\":\""+request.requestId()+"\"");
                    if(corrupt&&!kind.equals("query"))body=body.replace("\"widget_id\":\"2\"","\"widget_id\":\"3\"");
                    packets.add(NativeWire.packet(body.getBytes(StandardCharsets.UTF_8)));
                }
            }catch(IOException error){throw error;}catch(Exception error){throw new IOException(error);}
        }
        @Override public void close(){closed=true;}
    }
}
