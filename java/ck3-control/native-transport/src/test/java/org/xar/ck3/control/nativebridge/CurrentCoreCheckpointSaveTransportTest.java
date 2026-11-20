package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayDeque;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;

/** Actual C++ SAVE results through real transport/custody. Core software frames are explicitly Java DATA. */
final class CurrentCoreCheckpointSaveTransportTest {
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    private static Instant deadline(){return Instant.now().plusSeconds(20);}
    private static NativePipeEndpoint.Config config(){return new NativePipeEndpoint.Config("\\\\.\\pipe\\checkpoint-save-data","checkpoint-save-data",GAME,"checkpoint-save-session","checkpoint-save-data",BUILD.executableSha256(),BUILD.coreFrameAdapterId());}
    private static NativeGameTransport transport(Replay r){return new NativeGameTransport(r,config(),16,12);}
    private static NativeGameTransport.CoreReceived core(NativeGameTransport t)throws Exception{return assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(deadline()));}
    @Test void prepareArchivesOriginalBeforeOneWriteAndDuplicateCoreCannotBuyAnotherSave()throws Exception {
        var source=new Replay("submitted",true);
        try(var t=transport(source)) {
            var before=core(t);var prepared=t.prepareCurrentCoreCheckpoint(before,before.validUntil());
            assertSame(prepared,t.prepareCurrentCoreCheckpoint(before,prepared.deadline()));assertEquals(0,source.saveWrites);
            var request=NativeWire.decodeExecuteRequest(prepared.originalPacket().value());assertEquals(prepared.requestId(),request.requestId());assertEquals(CurrentCoreCheckpointSave.STEP,request.step());
            assertEquals(BigInteger.ZERO,request.expectedRevision().orElseThrow());assertTrue(request.expectedSnapshotRevision().isEmpty());
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentCoreCheckpoint(prepared));
            assertTrue(ack.nativeOk());assertEquals(prepared.requestId(),ack.requestId());ack.custody().orElseThrow().verify(ack);
            assertArrayEquals(prepared.originalPacket().value(),ack.outbound().orElseThrow().originalPacket());
            assertArrayEquals(CurrentCheckpointCppFrames.result("submitted"),ack.originalResultToken().orElseThrow().bytes());
            assertSame(ack,t.submitCurrentCoreCheckpoint(prepared));assertEquals(1,source.saveWrites);
            assertThrows(IOException.class,()->t.prepareCurrentCoreCheckpoint(before,before.validUntil()));
        }
    }
    @Test void laterActualCoreDateGetsFreshIdAfterKnownTerminalWithoutPermanentSingleBool()throws Exception {
        var source=new Replay("submitted",true);source.nextDate=true;
        try(var t=transport(source)) {
            var a=core(t);var one=t.prepareCurrentCoreCheckpoint(a,a.validUntil());assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentCoreCheckpoint(one));
            var b=core(t);var two=t.prepareCurrentCoreCheckpoint(b,b.validUntil());assertNotEquals(one.requestId(),two.requestId());assertTrue(two.sourceDateRaw()>one.sourceDateRaw());
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentCoreCheckpoint(two));assertTrue(ack.nativeOk());assertEquals(2,source.saveWrites);
        }
    }
    @Test void indeterminateAndLostReplyKeepOriginalAndBlockCrossIdFollowups()throws Exception {
        for(String mode:new String[]{"indeterminate","lost-reply","wrong-envelope"}) {
            var source=new Replay(mode,true);
            try(var t=transport(source)) {
                var before=core(t);var prepared=t.prepareCurrentCoreCheckpoint(before,before.validUntil());
                var unknown=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentCoreCheckpoint(prepared));
                assertEquals(prepared.requestId(),unknown.requestId());assertSame(unknown,t.submitCurrentCoreCheckpoint(prepared));
                assertThrows(IOException.class,()->t.prepareCurrentCoreCheckpoint(before,before.validUntil()));
                assertSame(unknown,t.submitCoreNormalExit(before,before.validUntil()));assertEquals(1,source.saveWrites);
                if(mode.equals("indeterminate"))assertTrue(t.originalIndeterminateCoreAcknowledgement(prepared.requestId()).isPresent());
            }
        }
    }
    @Test void noCapabilityForeignCoreAndExtendedOriginalDeadlineRefuseBeforeSaveWrite()throws Exception {
        var source=new Replay("submitted",false);try(var t=transport(source)) {var a=core(t);assertThrows(IOException.class,()->t.prepareCurrentCoreCheckpoint(a,a.validUntil()));assertEquals(0,source.saveWrites);}
        var first=new Replay("submitted",true);var second=new Replay("submitted",true);
        try(var t=transport(first);var other=transport(second)) {
            var a=core(t);assertThrows(IOException.class,()->other.prepareCurrentCoreCheckpoint(a,a.validUntil()));
            assertThrows(IOException.class,()->t.prepareCurrentCoreCheckpoint(a,a.validUntil().plusMillis(1)));assertEquals(0,first.saveWrites);assertEquals(0,second.saveWrites);
        }
    }
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets=new ArrayDeque<>();final String mode;boolean closed,nextDate;int coreWrites,saveWrites;
        Replay(String mode,boolean capability)throws Exception {
            this.mode=mode;var hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",1)
                    .put("bridge_version","checkpoint-save-data").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256())
                    .put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            var caps=hello.putArray("capabilities");caps.add(CoreFrame.CAPABILITY);if(capability)caps.add(CurrentCoreCheckpointSave.CAPABILITY);
            packets.add(NativeWire.packet(StrictJson.canonical(hello)));
        }
        public void verify()throws IOException{if(closed)throw new IOException("Software source closed");}
        public void verifyCoreControlWindowPolicy()throws IOException{verify();}
        public void awaitConnection(Instant until)throws IOException{verify();}
        public byte[] readPacket(Instant until)throws IOException{verify();if(packets.isEmpty())throw new IOException("Actual DATA missing reply");return packets.removeFirst();}
        public void writePacket(byte[] packet,Instant until)throws IOException {
            verify();var request=NativeWire.decodeExecuteRequest(packet);byte[] body;boolean ok;
            try {
                if(request.step().equals(CoreFrame.STEP)) {
                    // Real Java serializer DATA copied from exact C++ claim scalars; never called a live/C++ Core producer.
                    var prefix=CurrentCheckpointCppFrames.core(nextDate&&coreWrites>0?"request-e2":"request");coreWrites++;
                    body=CoreFramePublicCodec.encode(prefix).bytes();ok=true;
                } else {
                    assertEquals(CurrentCoreCheckpointSave.STEP,request.step());saveWrites++;
                    if(mode.equals("lost-reply"))return;
                    String name=mode.equals("wrong-envelope")?"submitted":mode.equals("submitted")&&saveWrites>1?"submitted-e2":mode;
                    var original=CurrentCheckpointCppFrames.response(name);body=original.result().token().orElseThrow().value();ok=original.nativeOk();
                }
            }catch(Exception e){throw new IOException("Actual pinned producer fixture unavailable",e);}
            var out=new ByteArrayOutputStream();out.writeBytes(("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+request.requestId()+"\",\"ok\":"+ok+",\"result\":").getBytes(StandardCharsets.UTF_8));out.writeBytes(body);if(mode.equals("wrong-envelope")&&!request.step().equals(CoreFrame.STEP))out.writeBytes(",\"unexpected\":true".getBytes(StandardCharsets.UTF_8));out.write('}');packets.add(NativeWire.packet(out.toByteArray()));
        }
        public void close(){closed=true;}
    }
}
