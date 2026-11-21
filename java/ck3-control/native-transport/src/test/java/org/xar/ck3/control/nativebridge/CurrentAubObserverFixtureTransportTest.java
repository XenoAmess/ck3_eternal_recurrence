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
import com.fasterxml.jackson.databind.node.ObjectNode;

/** Real C++ result tokens through production transport/custody. Fresh-ID wrappers and Core are explicit Java NoGame DATA. */
final class CurrentAubObserverFixtureTransportTest {
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    private static Instant deadline(){return Instant.now().plusSeconds(20);}
    private static NativePipeEndpoint.Config config(){return new NativePipeEndpoint.Config("\\\\.\\pipe\\aub-observer-data","aub-observer-data",GAME,"aub-observer-session","aub-observer-data",BUILD.executableSha256(),BUILD.coreFrameAdapterId());}
    private static NativeGameTransport transport(Replay r){return new NativeGameTransport(r,config(),16,12);}
    private static NativeGameTransport.CoreReceived core(NativeGameTransport t)throws Exception{return assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(deadline()));}
    @Test void actualCoreAndCppResultPassOneArchivedRequestWithoutDuplicateWrite()throws Exception {
        var source=new Replay("dispatched",true);
        try(var t=transport(source)) {
            var before=core(t);var prepared=t.prepareCurrentAubObserverFixture(before,before.validUntil());
            assertSame(prepared,t.prepareCurrentAubObserverFixture(before,prepared.deadline()));assertEquals(0,source.fixtureWrites);
            var request=NativeWire.decodeExecuteRequest(prepared.originalPacket().value());assertEquals(CurrentAubObserverFixture.STEP,request.step());assertEquals(BigInteger.ZERO,request.expectedRevision().orElseThrow());
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentAubObserverFixture(prepared));
            assertTrue(ack.nativeOk());ack.custody().orElseThrow().verify(ack);assertEquals(prepared.requestId(),ack.requestId());
            assertArrayEquals(prepared.originalPacket().value(),ack.outbound().orElseThrow().originalPacket());assertArrayEquals(CurrentAubObserverCppFrames.result("dispatched"),ack.originalResultToken().orElseThrow().bytes());
            assertSame(ack,t.submitCurrentAubObserverFixture(prepared));assertEquals(1,source.fixtureWrites);
            assertThrows(IOException.class,()->t.prepareCurrentAubObserverFixture(before,before.validUntil()));
            var later=core(t);assertThrows(IOException.class,()->t.prepareCurrentAubObserverFixture(later,later.validUntil()));assertEquals(1,source.fixtureWrites);
        }
    }
    @Test void indeterminateLostMalformedAndWrongOwnerStayUnknownAndBlockOtherCoreEffects()throws Exception {
        for(String mode:new String[]{"indeterminate","lost-reply","wrong-envelope","wrong-owner","wrong-core","false-afterwrite"}) {
            var source=new Replay(mode,true);try(var t=transport(source)) {
                var before=core(t);var prepared=t.prepareCurrentAubObserverFixture(before,before.validUntil());
                var unknown=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentAubObserverFixture(prepared));
                assertEquals(prepared.requestId(),unknown.requestId());assertSame(unknown,t.submitCurrentAubObserverFixture(prepared));
                assertThrows(IOException.class,()->t.prepareCurrentAubObserverFixture(before,before.validUntil()));
                assertSame(unknown,t.submitCoreNormalExit(before,before.validUntil()));assertEquals(1,source.fixtureWrites);
                if(!mode.equals("lost-reply")&&!mode.equals("wrong-envelope"))assertTrue(t.originalIndeterminateCoreAcknowledgement(prepared.requestId()).isPresent());
            }
        }
    }
    @Test void missingCapabilityForeignCoreOrExtendedDeadlineRefuseBeforeFixtureWrite()throws Exception {
        var source=new Replay("dispatched",false);try(var t=transport(source)) {var before=core(t);assertThrows(IOException.class,()->t.prepareCurrentAubObserverFixture(before,before.validUntil()));assertEquals(0,source.fixtureWrites);}
        var first=new Replay("dispatched",true);var second=new Replay("dispatched",true);
        try(var t=transport(first);var other=transport(second)) {
            var before=core(t);assertThrows(IOException.class,()->other.prepareCurrentAubObserverFixture(before,before.validUntil()));
            assertThrows(IOException.class,()->t.prepareCurrentAubObserverFixture(before,before.validUntil().plusMillis(1)));assertEquals(0,first.fixtureWrites);assertEquals(0,second.fixtureWrites);
        }
    }
    @Test void aPreparationCannotCrossReceiverOrBeReplacedWithANewId()throws Exception {
        var first=new Replay("dispatched",true);var second=new Replay("dispatched",true);
        try(var t=transport(first);var other=transport(second)) {
            var before=core(t);var prepared=t.prepareCurrentAubObserverFixture(before,before.validUntil());
            var refused=assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,other.submitCurrentAubObserverFixture(prepared));assertEquals(0,refused.proof().requestBytesWritten());assertEquals(0,second.fixtureWrites);
            var another=core(t);assertThrows(IOException.class,()->t.prepareCurrentAubObserverFixture(another,another.validUntil()));assertEquals(0,first.fixtureWrites);
        }
    }
    @Test void knownNativeConsumedRefusalRetainsOriginalButNeverCreatesAnotherAttempt()throws Exception {
        var source=new Replay("claim-consumed",true);try(var t=transport(source)) {
            var before=core(t);var prepared=t.prepareCurrentAubObserverFixture(before,before.validUntil());
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentAubObserverFixture(prepared));assertFalse(ack.nativeOk());
            assertEquals(CurrentAubObserverFixtureResult.Status.CLAIM_CONSUMED,CurrentAubObserverFixtureResult.decodeOutcome(ack).status());
            assertSame(ack,t.submitCurrentAubObserverFixture(prepared));assertThrows(IOException.class,()->t.prepareCurrentAubObserverFixture(before,before.validUntil()));assertEquals(1,source.fixtureWrites);
        }
    }
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets=new ArrayDeque<>();final String mode;boolean closed;int fixtureWrites;
        Replay(String mode,boolean capability)throws Exception {
            this.mode=mode;var hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",7)
                    .put("bridge_version","aub-observer-data").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256())
                    .put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            var caps=hello.putArray("capabilities");caps.add(CoreFrame.CAPABILITY);if(capability)caps.add(CurrentAubObserverFixture.CAPABILITY);
            packets.add(NativeWire.packet(StrictJson.canonical(hello)));
        }
        public void verify()throws IOException{if(closed)throw new IOException("Software DATA source closed");}
        public void verifyCoreControlWindowPolicy()throws IOException{verify();}
        public void awaitConnection(Instant until)throws IOException{verify();}
        public byte[] readPacket(Instant until)throws IOException{verify();if(packets.isEmpty())throw new IOException("DATA missing reply");return packets.removeFirst();}
        public void writePacket(byte[] packet,Instant until)throws IOException {
            verify();var request=NativeWire.decodeExecuteRequest(packet);byte[] body;boolean ok;
            try {
                if(request.step().equals(CoreFrame.STEP)){body=CoreFramePublicCodec.encode(CurrentAubObserverCppFrames.core()).bytes();ok=true;}
                else {
                    assertEquals(CurrentAubObserverFixture.STEP,request.step());fixtureWrites++;
                    if(mode.equals("lost-reply"))return;
                    String name=mode.equals("wrong-envelope")||mode.equals("wrong-owner")||mode.equals("wrong-core")||mode.equals("false-afterwrite")?"dispatched":mode;
                    var original=CurrentAubObserverCppFrames.response(name);body=original.result().token().orElseThrow().value();ok=original.nativeOk();
                    // Deliberately invalid Java DATA derived from the pinned positive, never described as another C++ producer.
                    if(mode.equals("wrong-owner")||mode.equals("wrong-core")||mode.equals("false-afterwrite")) {
                        var bad=NativeWire.object(NativeWire.parse(body));
                        if(mode.equals("wrong-owner"))((ObjectNode)bad.get("owner_witness")).put("connection_generation","8");
                        if(mode.equals("wrong-core"))((ObjectNode)bad.get("core_before")).put("date_raw",53144377);
                        if(mode.equals("false-afterwrite")){bad.put("status","unavailable").put("native_accepted",false).put("unavailable_reason","negative-data-afterwrite");ok=false;}
                        body=StrictJson.canonical(bad);
                    }
                }
            }catch(Exception e){throw new IOException("Actual pinned producer fixture unavailable",e);}
            var out=new ByteArrayOutputStream();out.writeBytes(("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+request.requestId()+"\",\"ok\":"+ok+",\"result\":").getBytes(StandardCharsets.UTF_8));out.writeBytes(body);
            if(mode.equals("wrong-envelope")&&!request.step().equals(CoreFrame.STEP))out.writeBytes(",\"unexpected\":true".getBytes(StandardCharsets.UTF_8));out.write('}');packets.add(NativeWire.packet(out.toByteArray()));
        }
        public void close(){closed=true;}
    }
}
