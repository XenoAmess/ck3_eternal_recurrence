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
import org.xar.ck3.control.nativebridge.capabilities.registry.RiteDraftCostsFrameV2;
import org.xar.ck3.control.nativebridge.capabilities.registry.RiteDraftCostsFrameV2PublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.RiteDoctrineFrameV1;
import org.xar.ck3.control.nativebridge.capabilities.registry.RiteDoctrineFrameV1PublicCodec;

/** Real transport custody with genuine result tokens plus explicitly derived Java source DATA; no Game. */
final class NativeRiteDoctrineTransportTest {
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    private static Instant until(){return Instant.now().plusSeconds(25);}
    private static NativeGameTransport transport(Replay r){return new NativeGameTransport(r,new NativePipeEndpoint.Config("\\\\.\\pipe\\rite-doctrine-data","rite-doctrine-data",GAME,"rite-doctrine-session","rite-doctrine-data",BUILD.executableSha256(),BUILD.coreFrameAdapterId()),32,12);}
    private static NativeGameTransport.RiteDoctrineReceived query(NativeGameTransport t)throws Exception{
        var core=assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(until()));
        var draft=assertInstanceOf(NativeGameTransport.RiteDraftCostsReceived.class,t.readRiteDraftCostsReceived(core,152,core.validUntil()));
        return assertInstanceOf(NativeGameTransport.RiteDoctrineReceived.class,t.readRiteDoctrineReceived(draft,draft.validUntil()));
    }
    @Test void selectAndConfirmUseActualCoreDraftPrivateQueryAndExactlyOneClaim()throws Exception{
        for(var action:new RiteDoctrineFrameV1.Action[]{RiteDoctrineFrameV1.Action.SELECT_DYNASTIC,RiteDoctrineFrameV1.Action.CONFIRM_EDIT}){
            var replay=new Replay(action,"success");try(var t=transport(replay)){
                var query=query(t);var ack=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitRiteDoctrineAction(query,action,query.validUntil()));ack.custody().orElseThrow().verify(ack);
                assertEquals(action,RiteDoctrineFrameV1PublicCodec.decodeOutcome(ack).action());assertArrayEquals(RiteDoctrineCppFrames.result(action==RiteDoctrineFrameV1.Action.SELECT_DYNASTIC?"selected-SYNTHETIC-DATA.json":"confirmation-dispatched-SYNTHETIC-DATA.json").bytes(),ack.originalResultToken().orElseThrow().bytes());
                assertEquals(1,replay.effects);assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.submitRiteDoctrineAction(query,action,query.validUntil()));assertEquals(1,replay.effects);
            }
        }
    }
    @Test void foreignQueryCannotBuyAnEffectOnAnotherTransport()throws Exception{
        var a=new Replay(RiteDoctrineFrameV1.Action.SELECT_DYNASTIC,"success");var b=new Replay(RiteDoctrineFrameV1.Action.SELECT_DYNASTIC,"success");
        try(var t=transport(a);var other=transport(b)){var q=query(t);assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,other.submitRiteDoctrineAction(q,RiteDoctrineFrameV1.Action.SELECT_DYNASTIC,q.validUntil()));assertEquals(0,a.effects);assertEquals(0,b.effects);}
    }
    @Test void unresolvedPamAndUnselectedBeforeCannotBuySelectOrConfirm()throws Exception{
        for(String mode:new String[]{"pam","unselected"}){
            var replay=new Replay(RiteDoctrineFrameV1.Action.SELECT_DYNASTIC,mode);try(var t=transport(replay)){
                var q=query(t);var action=mode.equals("pam")?RiteDoctrineFrameV1.Action.SELECT_DYNASTIC:RiteDoctrineFrameV1.Action.CONFIRM_EDIT;
                assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.submitRiteDoctrineAction(q,action,q.validUntil()));assertEquals(0,replay.effects);
            }
        }
    }
    @Test void actualIndeterminateAckRemainsStickyAcrossLaterActions()throws Exception{
        var replay=new Replay(RiteDoctrineFrameV1.Action.SELECT_DYNASTIC,"indeterminate");try(var t=transport(replay)){
            var q=query(t);var unknown=assertInstanceOf(NativeActionPort.Unknown.class,t.submitRiteDoctrineAction(q,RiteDoctrineFrameV1.Action.SELECT_DYNASTIC,q.validUntil()));
            assertSame(unknown,t.submitRiteDoctrineAction(q,RiteDoctrineFrameV1.Action.CONFIRM_EDIT,q.validUntil()));assertTrue(t.originalIndeterminateCoreAcknowledgement(unknown.requestId()).isPresent());assertEquals(1,replay.effects);
        }
    }
    @Test void actualKnownEarlyRefusalIsAnOriginalFalseAckRatherThanUnknownReplay()throws Exception {
        var replay=new Replay(RiteDoctrineFrameV1.Action.SELECT_DYNASTIC,"early-unavailable");try(var t=transport(replay)){
            var q=query(t);var ack=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitRiteDoctrineAction(q,RiteDoctrineFrameV1.Action.SELECT_DYNASTIC,q.validUntil()));
            ack.custody().orElseThrow().verify(ack);assertFalse(ack.nativeOk());var frame=RiteDoctrineFrameV1PublicCodec.decodeOutcome(ack);assertEquals(RiteDoctrineFrameV1.Status.UNAVAILABLE,frame.status());assertFalse(frame.effectAttempted());
            assertArrayEquals(RiteDoctrineCppFrames.result("effect-early-unavailable-NoGame.json").bytes(),ack.originalResultToken().orElseThrow().bytes());assertTrue(t.originalIndeterminateCoreAcknowledgement(ack.requestId()).isEmpty());
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.submitRiteDoctrineAction(q,RiteDoctrineFrameV1.Action.SELECT_DYNASTIC,q.validUntil()));assertEquals(1,replay.effects);
        }
    }
    @Test void realDraftCostDriftRefusesQueryAuthorityWithoutAnyEffect()throws Exception{
        var replay=new Replay(RiteDoctrineFrameV1.Action.SELECT_DYNASTIC,"drift");try(var t=transport(replay)){
            var core=assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(until()));var draft=assertInstanceOf(NativeGameTransport.RiteDraftCostsReceived.class,t.readRiteDraftCostsReceived(core,152,core.validUntil()));
            assertInstanceOf(NativeGameTransport.RiteDoctrineReadUnavailable.class,t.readRiteDoctrineReceived(draft,draft.validUntil()));assertEquals(0,replay.effects);
        }
    }
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets=new ArrayDeque<>();final RiteDoctrineFrameV1.Action action;final String mode;boolean closed;int effects;
        Replay(RiteDoctrineFrameV1.Action action,String mode)throws IOException{
            this.action=action;this.mode=mode;
            var hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",7).put("bridge_version","rite-doctrine-data").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256()).put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);hello.putArray("capabilities").add(CoreFrame.CAPABILITY).add(RiteDoctrineFrameV1.CAPABILITY);packets.add(NativeWire.packet(StrictJson.canonical(hello)));
        }
        public void verify()throws IOException{if(closed)throw new IOException("Software source closed");}
        public void verifyCoreControlWindowPolicy()throws IOException{verify();}
        public void awaitConnection(Instant deadline)throws IOException{verify();}
        public byte[] readPacket(Instant deadline)throws IOException{verify();if(packets.isEmpty())throw new IOException("No original software packet");return packets.removeFirst();}
        private byte[] queryBody()throws Exception{
            if(mode.equals("pam"))return RiteDoctrineCppFrames.result("pam-unresolved-SYNTHETIC-DATA.json").bytes();
            if(action!=RiteDoctrineFrameV1.Action.CONFIRM_EDIT)return RiteDoctrineCppFrames.result("query-SYNTHETIC-DATA.json").bytes();
            // Explicit derived Java query DATA with the genuine confirmation's selected-before facts. It is not a C++ producer original.
            var row=NativeWire.object(NativeWire.parse(RiteDoctrineCppFrames.result("confirmation-dispatched-SYNTHETIC-DATA.json").bytes()));
            row.put("action","query").put("status","available").put("effect_attempted",false).put("native_returned",false).put("native_handled",false).put("post_selected_evaluated",false).put("post_selected",false).put("claim_sequence","0");return StrictJson.canonical(row);
        }
        public void writePacket(byte[] packet,Instant deadline)throws IOException{
            verify();var outgoing=NativeWire.decodeExecuteRequest(packet);byte[] body;boolean ok=true;
            try{
                var query=RiteDoctrineFrameV1.decode(new org.xar.ck3.control.application.action.RawJson(queryBody()));
                if(outgoing.step().equals(CoreFrame.STEP))body=CoreFramePublicCodec.encode(query.coreFrame()).bytes();
                else if(outgoing.step().equals(RiteDraftCostsFrameV2.STEP)){
                    var f=query.facts().orElseThrow();var core=(CoreFrame.Partial)query.coreFrame();
                    var draft=new RiteDraftCostsFrameV2.Partial(core,new RiteDraftCostsFrameV2.Draft(f.sourceRiteId(),core.prefix().playedCharacterId(),f.canEdit(),f.pietyCostRaw()+(mode.equals("drift")?1:0),f.pietyMissingSignedRaw(),f.pietyMissingSignedRaw()<=0),query.ownerWitness().orElseThrow());body=RiteDraftCostsFrameV2PublicCodec.encode(draft).bytes();
                }else{
                    assertEquals(RiteDoctrineFrameV1.STEP,outgoing.step());var request=RiteDoctrineFrameV1PublicCodec.decodeRequestPacket(packet);
                    if(request.action()==RiteDoctrineFrameV1.Action.QUERY)body=queryBody();else{
                        effects++;assertEquals(action,request.action());assertEquals(new BigInteger("18446744073709551615"),request.lease().orElseThrow().providerGeneration());
                        String file=mode.equals("early-unavailable")?"effect-early-unavailable-NoGame.json":mode.equals("indeterminate")?"indeterminate-SYNTHETIC-DATA.json":action==RiteDoctrineFrameV1.Action.CONFIRM_EDIT?"confirmation-dispatched-SYNTHETIC-DATA.json":"selected-SYNTHETIC-DATA.json";var actual=RiteDoctrineCppFrames.response(file);body=actual.result().token().orElseThrow().value();ok=actual.nativeOk();
                    }
                }
            }catch(Exception failure){throw new IOException("Pinned actual C++ contract or derived Java DATA unavailable",failure);}
            var result=new ByteArrayOutputStream();result.writeBytes(("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+outgoing.requestId()+"\",\"ok\":"+ok+",\"result\":").getBytes(StandardCharsets.UTF_8));result.writeBytes(body);result.write('}');packets.add(NativeWire.packet(result.toByteArray()));
        }
        public void close(){closed=true;}
    }
}
