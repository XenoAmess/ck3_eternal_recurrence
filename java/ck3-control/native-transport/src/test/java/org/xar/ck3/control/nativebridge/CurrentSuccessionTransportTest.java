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
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;

/** Original C++ tokens with fresh Java DATA envelopes, through production transport. No Core request or live owner exists. */
final class CurrentSuccessionTransportTest {
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    private static Instant deadline(){return Instant.now().plusSeconds(20);}
    private static NativeGameTransport transport(Replay r){return new NativeGameTransport(r,new NativePipeEndpoint.Config("\\\\.\\pipe\\succession-data","succession-data",GAME,"succession-session","succession-data",BUILD.executableSha256(),BUILD.coreFrameAdapterId()),16,16);}
    private static NativeGameTransport.SuccessionReceived query(NativeGameTransport t)throws Exception{return assertInstanceOf(NativeGameTransport.SuccessionReceived.class,t.readCurrentSuccessionDefault(deadline()));}
    @Test void threeRealCppRelationsUseNoLivingCoreAndContinueExactlyOnce()throws Exception {
        for(String role:new String[]{"dead","assigned","unassigned"}) {
            var replay=new Replay(role,"dispatched",true,true);try(var t=transport(replay)) {
                var q=query(t);q.requireOriginal(t);var p=t.prepareCurrentSuccessionContinue(q);assertSame(p,t.prepareCurrentSuccessionContinue(q));assertEquals(q.validUntil(),p.deadline());
                var request=NativeWire.decodeExecuteRequest(p.originalPacket().value());assertEquals(CurrentSuccessionLifecycle.Action.CONTINUE_DEFAULT.step(),request.step());var f=NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value()));assertFalse(f.has("expected_core"));assertEquals(q.validUntil().toEpochMilli(),f.get("core_control_deadline_unix_ms").longValue());
                var ack=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentSuccessionContinue(p));ack.custody().orElseThrow().verify(ack);assertArrayEquals(p.originalPacket().value(),ack.outbound().orElseThrow().originalPacket());
                var frame=CurrentSuccessionLifecycleResult.decodeOutcome(ack);assertEquals(CurrentSuccessionLifecycleResult.Status.DISPATCHED,frame.status());assertTrue(frame.nativeReturned());
                assertSame(ack,t.submitCurrentSuccessionContinue(p));assertEquals(1,replay.effectWrites);assertEquals(0,replay.coreWrites);
                assertThrows(IOException.class,()->q.requireOriginal(t));var fresh=query(t);assertThrows(IOException.class,()->t.prepareCurrentSuccessionContinue(fresh));assertEquals(1,replay.effectWrites);
            }
        }
    }
    @Test void foreignMissingCapabilityAndUnavailableNeverWriteContinue()throws Exception {
        var a=new Replay("dead","dispatched",true,true);var b=new Replay("dead","dispatched",true,true);try(var t=transport(a);var other=transport(b)) {
            var q=query(t);assertThrows(IOException.class,()->other.prepareCurrentSuccessionContinue(q));var p=t.prepareCurrentSuccessionContinue(q);var refused=assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,other.submitCurrentSuccessionContinue(p));assertEquals(0,refused.proof().requestBytesWritten());assertEquals(0,b.effectWrites);
        }
        var missing=new Replay("dead","dispatched",true,false);try(var t=transport(missing)){var q=query(t);assertThrows(IOException.class,()->t.prepareCurrentSuccessionContinue(q));assertEquals(0,missing.effectWrites);}
        var unavailable=new Replay("unavailable","dispatched",true,true);try(var t=transport(unavailable)){var q=assertInstanceOf(NativeGameTransport.SuccessionUnavailable.class,t.readCurrentSuccessionDefault(deadline()));assertInstanceOf(NativeActionPort.AckReceived.class,q.original());assertEquals(0,unavailable.effectWrites);assertEquals(0,unavailable.coreWrites);}
        var noQueryCap=new Replay("dead","dispatched",false,true);try(var t=transport(noQueryCap)){var q=t.readCurrentSuccessionDefault(deadline());assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,q.original());assertEquals(0,noQueryCap.queryWrites);}
    }
    @Test void effectUnknownWrongLeaseOwnerSourceAndLostReplyRemainSticky()throws Exception {
        for(String effect:new String[]{"indeterminate","wrong-lease","wrong-owner","wrong-source","lost-reply"}) {
            var r=new Replay("dead",effect,true,true);try(var t=transport(r)){var q=query(t);var p=t.prepareCurrentSuccessionContinue(q);var unknown=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentSuccessionContinue(p));assertSame(unknown,t.submitCurrentSuccessionContinue(p));assertEquals(1,r.effectWrites);assertEquals(0,r.coreWrites);
                var later=assertInstanceOf(NativeGameTransport.SuccessionUnavailable.class,t.readCurrentSuccessionDefault(deadline()));assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,later.original());assertEquals(1,r.queryWrites);
                if(!effect.equals("lost-reply"))assertTrue(t.originalIndeterminateCoreAcknowledgement(unknown.requestId()).isPresent());}
        }
    }
    @Test void malformedOrForeignActualQueryCannotMintAPrivateLease()throws Exception {
        for(String mode:new String[]{"incoherent","wrong-owner","wrong-source","lost-reply"}) {
            var r=new Replay(mode,"dispatched",true,true);try(var t=transport(r)){var q=assertInstanceOf(NativeGameTransport.SuccessionUnavailable.class,t.readCurrentSuccessionDefault(deadline()));assertInstanceOf(NativeActionPort.Unknown.class,q.original());assertEquals(0,r.effectWrites);assertEquals(0,r.coreWrites);}
        }
    }
    @Test void laterDifferentActualPredecessorCanContinueButOriginalActorCannotReplay()throws Exception {
        var r=new Replay("dead","dispatched",true,true);try(var t=transport(r)) {
            var q=query(t);var p=t.prepareCurrentSuccessionContinue(q);assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentSuccessionContinue(p));
            r.nextPredecessor=true;var next=query(t);assertNotEquals(q.frame().source().orElseThrow().deadCharacter(),next.frame().source().orElseThrow().deadCharacter());
            var second=t.prepareCurrentSuccessionContinue(next);assertNotEquals(p.requestId(),second.requestId());assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentSuccessionContinue(second));assertEquals(2,r.effectWrites);assertEquals(0,r.coreWrites);
        }
    }
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets=new ArrayDeque<>();final String queryMode,effectMode;boolean closed,nextPredecessor;int queryWrites,effectWrites,coreWrites;
        Replay(String queryMode,String effectMode,boolean queryCap,boolean continueCap)throws IOException {
            this.queryMode=queryMode;this.effectMode=effectMode;var h=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",7).put("bridge_version","succession-data")
                    .put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256()).put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            var caps=h.putArray("capabilities");if(queryCap)caps.add(CurrentSuccessionLifecycle.Action.QUERY_DEFAULT.capability());if(continueCap)caps.add(CurrentSuccessionLifecycle.Action.CONTINUE_DEFAULT.capability());packets.add(NativeWire.packet(StrictJson.canonical(h)));
        }
        public void verify()throws IOException{if(closed)throw new IOException("Software DATA closed");}public void verifyCoreControlWindowPolicy()throws IOException{verify();}
        public void awaitConnection(Instant until)throws IOException{verify();}public byte[] readPacket(Instant until)throws IOException{verify();if(packets.isEmpty())throw new IOException("No DATA reply");return packets.removeFirst();}
        public void writePacket(byte[] packet,Instant until)throws IOException {
            verify();var req=NativeWire.decodeExecuteRequest(packet);boolean query=req.step().equals(CurrentSuccessionLifecycle.Action.QUERY_DEFAULT.step());
            if(!query&&!req.step().equals(CurrentSuccessionLifecycle.Action.CONTINUE_DEFAULT.step())){coreWrites++;throw new IOException("No Core/arbitrary operation exists in lifecycle DATA");}
            if(query)queryWrites++;else effectWrites++;String mode=query?queryMode:effectMode;if(mode.equals("lost-reply"))return;
            try {
                var original=CurrentSuccessionCppFrames.response(mode.startsWith("wrong-")?(query?"dead":"dispatched"):mode);byte[] body=original.result().token().orElseThrow().value();
                if(mode.startsWith("wrong-")||nextPredecessor) {
                    var n=NativeWire.object(NativeWire.parse(body));if(mode.equals("wrong-owner"))((ObjectNode)n.get("owner_witness")).put("connection_generation","8");
                    if(mode.equals("wrong-source"))((ObjectNode)n.get("source")).put("handler_source_verified",false);
                    if(mode.equals("wrong-lease"))n.put("provider_generation","1");
                    // Explicit derived Java DATA for a later different native-observed predecessor, never labelled C++ output.
                    if(nextPredecessor){var s=(ObjectNode)n.get("source");int dead=s.get("dead_character_id").intValue()+100;int heir=s.get("continue_character_id").intValue()+100;s.put("dead_character_id",dead).put("continue_character_id",heir);((ObjectNode)n.get("world_before")).put("played_character_id",dead);if(!query)n.put("claim_sequence","2");}
                    body=StrictJson.canonical(n);
                }
                var out=new ByteArrayOutputStream();out.writeBytes(("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+req.requestId()+"\",\"ok\":"+original.nativeOk()+",\"result\":").getBytes(StandardCharsets.UTF_8));out.writeBytes(body);out.write('}');packets.add(NativeWire.packet(out.toByteArray()));
            }catch(Exception bad){throw new IOException("Pinned CPP fixture unavailable",bad);}
        }
        public void close(){closed=true;}
    }
}
