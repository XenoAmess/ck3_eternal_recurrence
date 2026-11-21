package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
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
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;

/** Pinned actual C++ result tokens through real Core/transport/custody. Fresh ID envelopes are Java DATA. */
final class CurrentDjcQueryTransportTest {
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    private static final NativeCharacterId TARGET=new NativeCharacterId(39957);
    private static Instant deadline(){return Instant.now().plusSeconds(20);}
    private static NativeGameTransport transport(Replay r){return new NativeGameTransport(r,new NativePipeEndpoint.Config("\\\\.\\pipe\\djc-query-data","djc-query-data",GAME,"djc-query-session","djc-query-data",BUILD.executableSha256(),BUILD.coreFrameAdapterId()),16,12);}
    private static NativeGameTransport.CoreReceived core(NativeGameTransport t)throws Exception{return assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(deadline()));}
    @Test void actualCoreAndCppChoiceMintOnlySameReceiverReadonlyReceipt()throws Exception {
        var source=new Replay("choice",true);try(var t=transport(source)) {
            var before=core(t);var query=assertInstanceOf(NativeGameTransport.DjcTargetQueryReceived.class,t.readCurrentDjcTargetWars(before,TARGET,before.validUntil()));
            query.requireOriginal(t,query.validUntil());query.original().custody().orElseThrow().verify(query.original());
            assertArrayEquals(CurrentDjcQueryCppFrames.result("choice"),query.original().originalResultToken().orElseThrow().bytes());assertEquals(NativeWire.UINT64_MAX,query.frame().providerGeneration());
            assertEquals(1,source.queryWrites);assertEquals(0,source.effectWrites);
            var next=assertInstanceOf(NativeGameTransport.DjcTargetQueryReceived.class,t.readCurrentDjcTargetWars(before,TARGET,before.validUntil()));
            assertNotEquals(query.original().requestId(),next.original().requestId());assertThrows(IOException.class,()->query.requireOriginal(t,query.validUntil()));next.requireOriginal(t,next.validUntil());assertEquals(0,source.effectWrites);
        }
    }
    @Test void nativeFalseAvailabilityDoesNotBecomeAnOrdinaryWarRejectionOrSubmitPermission()throws Exception {
        var source=new Replay("blocked",true);try(var t=transport(source)){var before=core(t);var query=assertInstanceOf(NativeGameTransport.DjcTargetQueryReceived.class,t.readCurrentDjcTargetWars(before,TARGET,before.validUntil()));assertTrue(query.frame().available());assertFalse(query.frame().casusBelli().orElseThrow().getFirst().nativeAvailable().orElseThrow());assertEquals(0,source.effectWrites);}
        var unavailable=new Replay("unavailable",true);try(var t=transport(unavailable)){var before=core(t);var query=assertInstanceOf(NativeGameTransport.DjcTargetQueryUnavailable.class,t.readCurrentDjcTargetWars(before,TARGET,before.validUntil()));assertInstanceOf(NativeActionPort.AckReceived.class,query.original());assertEquals(1,unavailable.queryWrites);assertEquals(0,unavailable.effectWrites);}
    }
    @Test void indeterminateCleanupWrongCoreTargetOwnerAndMalformedAckBlockLaterEffects()throws Exception {
        for(String mode:new String[]{"indeterminate","incoherent","wrong-core","wrong-target","wrong-owner","wrong-envelope","lost-reply"}) {
            var source=new Replay(mode,true);try(var t=transport(source)) {
                var before=core(t);var read=assertInstanceOf(NativeGameTransport.DjcTargetQueryUnavailable.class,t.readCurrentDjcTargetWars(before,TARGET,before.validUntil()));
                var unknown=assertInstanceOf(NativeActionPort.Unknown.class,read.original());assertSame(unknown,t.submitCoreNormalExit(before,before.validUntil()));assertEquals(1,source.queryWrites);assertEquals(0,source.effectWrites);
                if(!mode.equals("lost-reply")&&!mode.equals("wrong-envelope"))assertTrue(t.originalIndeterminateCoreAcknowledgement(unknown.requestId()).isPresent());
            }
        }
    }
    @Test void missingCapabilityForeignCoreSelfAndExtendedDeadlineRefuseBeforeQueryWrite()throws Exception {
        var missing=new Replay("choice",false);try(var t=transport(missing)){var before=core(t);var r=t.readCurrentDjcTargetWars(before,TARGET,before.validUntil());assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,r.original());assertEquals(0,missing.queryWrites);}
        var a=new Replay("choice",true);var b=new Replay("choice",true);try(var t=transport(a);var other=transport(b)) {
            var before=core(t);assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,other.readCurrentDjcTargetWars(before,TARGET,before.validUntil()).original());
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.readCurrentDjcTargetWars(before,new NativeCharacterId(36423),before.validUntil()).original());
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.readCurrentDjcTargetWars(before,TARGET,before.validUntil().plusMillis(1)).original());assertEquals(0,a.queryWrites);assertEquals(0,b.queryWrites);
        }
    }
    @Test void privateReceiptCannotCrossReceiverOrExtendOriginalWindow()throws Exception {
        var a=new Replay("choice",true);var b=new Replay("choice",true);try(var t=transport(a);var other=transport(b)) {
            var before=core(t);var query=assertInstanceOf(NativeGameTransport.DjcTargetQueryReceived.class,t.readCurrentDjcTargetWars(before,TARGET,before.validUntil()));
            assertThrows(IOException.class,()->query.requireOriginal(other,query.validUntil()));assertThrows(IOException.class,()->query.requireOriginal(t,query.validUntil().plusMillis(1)));assertEquals(0,b.queryWrites);assertEquals(0,a.effectWrites);
        }
    }
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets=new ArrayDeque<>();final String mode;boolean closed;int queryWrites,effectWrites;
        Replay(String mode,boolean capability)throws IOException{
            this.mode=mode;var h=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",7).put("bridge_version","djc-query-data")
                    .put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256()).put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            var caps=h.putArray("capabilities");caps.add(CoreFrame.CAPABILITY);if(capability)caps.add(CurrentDjcTargetWarQuery.CAPABILITY);packets.add(NativeWire.packet(StrictJson.canonical(h)));
        }
        public void verify()throws IOException{if(closed)throw new IOException("DJC software DATA source closed");}
        public void verifyCoreControlWindowPolicy()throws IOException{verify();}
        public void awaitConnection(Instant until)throws IOException{verify();}
        public byte[] readPacket(Instant until)throws IOException{verify();if(packets.isEmpty())throw new IOException("DJC DATA missing reply");return packets.removeFirst();}
        public void writePacket(byte[] packet,Instant until)throws IOException {
            verify();var request=NativeWire.decodeExecuteRequest(packet);byte[] body;boolean ok;
            try {
                if(request.step().equals(CoreFrame.STEP)){body=CoreFramePublicCodec.encode(CurrentDjcQueryCppFrames.core()).bytes();ok=true;}
                else if(request.step().equals(CurrentDjcTargetWarQuery.STEP)) {
                    queryWrites++;assertEquals(39957,NativeWire.object(NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value())).get("djc_war_query")).get("target_character_id").intValue());
                    if(mode.equals("lost-reply"))return;
                    var reply=CurrentDjcQueryCppFrames.response(mode.startsWith("wrong-")?"choice":mode);body=reply.result().token().orElseThrow().value();ok=reply.nativeOk();
                    if(mode.equals("wrong-core")||mode.equals("wrong-target")||mode.equals("wrong-owner")) {
                        var n=NativeWire.object(NativeWire.parse(body));if(mode.equals("wrong-core"))((ObjectNode)n.get("core_before")).put("date_raw",53144329);
                        if(mode.equals("wrong-target"))n.put("target_character_id",40000);if(mode.equals("wrong-owner"))((ObjectNode)n.get("owner_witness")).put("connection_generation","8");body=StrictJson.canonical(n);
                    }
                } else {effectWrites++;throw new IOException("No effect is permitted in target-query DATA");}
            }catch(Exception bad){throw new IOException("Pinned actual C++ fixture could not be consumed",bad);}
            var out=new ByteArrayOutputStream();out.writeBytes(("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+request.requestId()+"\",\"ok\":"+ok+",\"result\":").getBytes(StandardCharsets.UTF_8));out.writeBytes(body);
            if(mode.equals("wrong-envelope")&&!request.step().equals(CoreFrame.STEP))out.writeBytes(",\"unexpected\":true".getBytes(StandardCharsets.UTF_8));out.write('}');packets.add(NativeWire.packet(out.toByteArray()));
        }
        public void close(){closed=true;}
    }
}
