package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;

/** Genuine C++ result tokens in a NoGame packet port. Fresh outer IDs are explicit Java transport DATA. */
class NativeCurrentFullscreenEventTransportTest {
    static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    static NativeGameTransport transport(Replay r){return new NativeGameTransport(r,new NativePipeEndpoint.Config("\\\\.\\pipe\\fullscreen-data","fullscreen-data",GAME,"fullscreen-session","fullscreen-data",BUILD.executableSha256(),BUILD.coreFrameAdapterId()),64,32);}
    static NativeGameTransport.CoreReceived core(NativeGameTransport t)throws Exception{return assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(Instant.now().plusSeconds(20)));}
    static NativeGameTransport.FullscreenReceived query(NativeGameTransport t)throws Exception{var c=core(t);return assertInstanceOf(NativeGameTransport.FullscreenReceived.class,t.readCurrentFullscreenEvent(c,c.validUntil()));}
    @Test void fixedAcknowledgementUsesTheActualPrivateInstanceAndIsOnlySubmittedOnce()throws Exception {
        var r=new Replay("capture-pair");try(var t=transport(r)) {
            var q=query(t);var p=t.prepareCurrentFullscreenAcknowledgement(q);
            assertEquals(q.frame().source().orElseThrow(),p.selected());assertEquals(q.validUntil(),p.deadline());assertEquals(q.frame().source().orElseThrow().instanceId().orElseThrow(),p.instanceId());
            var request=NativeWire.decodeExecuteRequest(p.originalPacket().value());var fields=NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value()));
            assertEquals(p.deadline().toEpochMilli(),fields.get("core_control_deadline_unix_ms").longValue());assertEquals(p.instanceId(),fields.get("fullscreen_event").get("instance_id").intValue());
            var out=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentFullscreenAcknowledgement(p));assertSame(out,t.submitCurrentFullscreenAcknowledgement(p));
            assertEquals(CurrentFullscreenEventResult.Status.ACK_DISPATCHED,CurrentFullscreenEventResult.decodeOutcome(out).status());assertEquals(CurrentFullscreenEventResult.decodeOutcome(out),p.latestFrame().orElseThrow());assertEquals(1,r.ackWrites);
        }
    }
    @Test void anEmptyOrNonadmissibleActualSourceNeverMintsAnAcknowledgement()throws Exception {
        for(String mode:new String[]{"empty","nonadmissible","multiple"}){var r=new Replay(mode);try(var t=transport(r)){var q=query(t);assertThrows(IOException.class,()->t.prepareCurrentFullscreenAcknowledgement(q));assertEquals(0,r.ackWrites);}}
    }
    @Test void privateSourceAndPreparationCannotCrossReceiversOrBecomeASecondAction()throws Exception {
        var a=new Replay("known");var b=new Replay("known");try(var t=transport(a);var other=transport(b)) {
            var q=query(t);assertThrows(IOException.class,()->other.prepareCurrentFullscreenAcknowledgement(q));var p=t.prepareCurrentFullscreenAcknowledgement(q);assertSame(p,t.prepareCurrentFullscreenAcknowledgement(q));
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,other.submitCurrentFullscreenAcknowledgement(p));assertEquals(0,a.ackWrites);assertEquals(0,b.ackWrites);
        }
    }
    @Test void actualHelloCapabilityIsRequiredEvenWhenTheSourceLooksAdmissible()throws Exception {
        var r=new Replay("missing-ack");try(var t=transport(r)){var q=query(t);assertTrue(q.frame().source().orElseThrow().knownAckAdmissible());assertThrows(IOException.class,()->t.prepareCurrentFullscreenAcknowledgement(q));assertEquals(0,r.ackWrites);}
    }
    @Test void extendingTheOriginalCoreWindowIsRejectedBeforeAnyQueryWrite()throws Exception {
        var r=new Replay("known");try(var t=transport(r)){var c=core(t);var out=t.readCurrentFullscreenEvent(c,c.validUntil().plusMillis(1));assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,out.original());assertEquals(0,r.queries);assertEquals(0,r.ackWrites);}
    }
    @Test void aLostAcknowledgementIsStickyUnknownAndBlocksOtherCoreEffects()throws Exception {
        var r=new Replay("lost");try(var t=transport(r)){var c=core(t);var q=assertInstanceOf(NativeGameTransport.FullscreenReceived.class,t.readCurrentFullscreenEvent(c,c.validUntil()));var p=t.prepareCurrentFullscreenAcknowledgement(q);
            var out=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentFullscreenAcknowledgement(p));assertSame(out,t.submitCurrentFullscreenAcknowledgement(p));assertSame(out,t.submitCoreNormalExit(c,c.validUntil()));assertEquals(1,r.ackWrites);}
    }
    @Test void aChangedInstanceLeaseOrBeforeSourceRetainsTheActualAckAsUnknown()throws Exception {
        for(String mode:new String[]{"wrong-instance","wrong-lease","changed-source"}){var r=new Replay(mode);try(var t=transport(r)){var q=query(t);var p=t.prepareCurrentFullscreenAcknowledgement(q);var out=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentFullscreenAcknowledgement(p));assertTrue(t.originalIndeterminateCoreAcknowledgement(out.requestId()).isPresent());assertSame(out,t.submitCurrentFullscreenAcknowledgement(p));assertEquals(1,r.ackWrites);}}
    }
    @Test void malformedReadonlySourceOrOwnerDoesNotGrantAuthorityAndBlocksEffects()throws Exception {
        for(String mode:new String[]{"wrong-owner","missing-can"}){var r=new Replay(mode);try(var t=transport(r)){var c=core(t);var read=t.readCurrentFullscreenEvent(c,c.validUntil());var out=assertInstanceOf(NativeActionPort.Unknown.class,read.original());assertTrue(t.originalIndeterminateCoreAcknowledgement(out.requestId()).isPresent());assertSame(out,t.submitCoreNormalExit(c,c.validUntil()));assertEquals(0,r.ackWrites);}}
    }
    @Test void aLegalKnownZeroEffectRefusalKeepsTheLeaseInstanceAndSpentClaimWithoutRetry()throws Exception {
        var r=new Replay("early");try(var t=transport(r)){var q=query(t);var p=t.prepareCurrentFullscreenAcknowledgement(q);var out=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentFullscreenAcknowledgement(p));
            var f=CurrentFullscreenEventResult.decodeOutcome(out);assertFalse(f.successful());assertFalse(f.effectAttempted());assertFalse(f.nativeReturned());assertEquals(q.frame().providerGeneration(),f.providerGeneration());assertEquals(q.frame().querySequence(),f.querySequence());assertEquals(Optional.of(p.instanceId()),f.instanceId());assertSame(out,t.submitCurrentFullscreenAcknowledgement(p));assertEquals(1,r.ackWrites);}
    }
    @Test void cleanupUnknownOrARefusalThatClaimsAnEffectCannotBeDowngradedToKnownZeroEffect()throws Exception {
        for(String mode:new String[]{"indeterminate","bad-refusal"}){var r=new Replay(mode);try(var t=transport(r)){var q=query(t);var p=t.prepareCurrentFullscreenAcknowledgement(q);var out=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentFullscreenAcknowledgement(p));assertTrue(t.originalIndeterminateCoreAcknowledgement(out.requestId()).isPresent());assertSame(out,t.submitCurrentFullscreenAcknowledgement(p));assertEquals(1,r.ackWrites);}}
    }
    static final class Replay implements NativePacketPort {
        final String mode;final ArrayDeque<byte[]> packets=new ArrayDeque<>();boolean closed;int queries,ackWrites;
        Replay(String mode)throws IOException {
            this.mode=mode;var f=NativeCurrentFullscreenEvent26785313ProducerTest.frame("available");
            var h=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",42).put("connection_generation",f.owner().orElseThrow().connectionGeneration()).put("bridge_version","fullscreen-data")
                    .put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256()).put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            var caps=h.putArray("capabilities").add(CoreFrame.CAPABILITY).add(CurrentFullscreenEvent.Action.QUERY_FULLSCREEN.capability());if(!mode.equals("missing-ack"))caps.add(CurrentFullscreenEvent.Action.ACKNOWLEDGE_KNOWN.capability());packets.add(NativeWire.packet(StrictJson.canonical(h)));
        }
        public void verify()throws IOException{if(closed)throw new IOException("Fullscreen DATA port closed");}public void verifyCoreControlWindowPolicy()throws IOException{verify();}public void awaitConnection(Instant until)throws IOException{verify();}
        public byte[] readPacket(Instant until)throws IOException{verify();if(packets.isEmpty())throw new IOException("Fullscreen DATA response missing");return packets.removeFirst();}
        public void writePacket(byte[] packet,Instant until)throws IOException {
            verify();var request=NativeWire.decodeExecuteRequest(packet);ObjectNode token;boolean ok;
            if(request.step().equals(CoreFrame.STEP)){token=NativeWire.object(NativeWire.parse(CoreFramePublicCodec.encode(NativeCurrentFullscreenEvent26785313ProducerTest.actualCore()).bytes()));ok=true;}
            else {
                var fields=NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value()));var claim=fields.get("fullscreen_event");String action=claim.get("action").textValue();String role;
                if(mode.equals("capture-pair"))retainActualRequest(action,packet);
                if(action.equals("query_fullscreen")){queries++;assertTrue(claim.get("instance_id").isNull());role=mode.equals("empty")?"empty":"available";}
                else{ackWrites++;assertEquals(CurrentFullscreenEvent.Action.ACKNOWLEDGE_KNOWN.step(),request.step());assertEquals(NativeCurrentFullscreenEvent26785313ProducerTest.frame("ack").instanceId().orElseThrow(),claim.get("instance_id").intValue());if(mode.equals("lost"))return;role=mode.equals("early")||mode.equals("bad-refusal")?"early":mode.equals("indeterminate")?"indeterminate":"ack";}
                var e=NativeCurrentFullscreenEvent26785313ProducerTest.envelope(role);token=NativeWire.object(e.get("result"));ok=e.get("ok").booleanValue();
                if(action.equals("query_fullscreen")) {
                    if(mode.equals("wrong-owner"))((ObjectNode)token.get("owner")).put("connection_generation","0");
                    if(mode.equals("missing-can"))((ObjectNode)token.get("source").get("options").get(0)).putNull("native_can_select");
                    if(mode.equals("nonadmissible")){((ObjectNode)token.get("source")).put("known_ack_admissible",false);((ObjectNode)token.get("source").get("options").get(0)).put("native_can_select",false);}
                    if(mode.equals("multiple"))((ObjectNode)token.get("source")).put("splash_item_count",2).put("known_ack_admissible",false);
                } else {
                    if(mode.equals("wrong-instance"))token.put("instance_id",Integer.MAX_VALUE);
                    if(mode.equals("wrong-lease"))token.put("query_sequence","0");
                    if(mode.equals("changed-source"))((ObjectNode)token.get("source")).put("opening","explicit Java changed-source negative DATA");
                    if(mode.equals("bad-refusal"))token.put("effect_attempted",true);
                }
            }
            var e=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",request.requestId()).put("ok",ok);e.set("result",token);packets.add(NativeWire.packet(StrictJson.canonical(e)));
        }
        public void close(){closed=true;}
        private static void retainActualRequest(String action,byte[] packet)throws IOException {
            String folder=System.getProperty("xar.current267.fullscreen.java.requests");if(folder==null)return;
            var p=java.nio.file.Path.of(folder).toAbsolutePath().normalize();if(!p.getRoot().toString().equalsIgnoreCase("D:\\"))throw new IOException("D request artifact root required");
            java.nio.file.Files.createDirectories(p);p=p.resolve(action+".request.json");if(!java.nio.file.Files.exists(p))java.nio.file.Files.write(p,java.util.Arrays.copyOfRange(packet,4,packet.length),java.nio.file.StandardOpenOption.CREATE_NEW);
        }
    }
}
