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

/** NoGame packet port uses original C++ result tokens. Fresh envelope IDs and negative mutations are Java DATA. */
class NativeCurrentXqolThresholdTransportTest {
    static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    static NativeGameTransport transport(Replay r){return new NativeGameTransport(r,new NativePipeEndpoint.Config("\\\\.\\pipe\\xqol-threshold-data","xqol-threshold-data",GAME,"xqol-threshold-session","xqol-threshold-data",BUILD.executableSha256(),BUILD.coreFrameAdapterId()),64,32);}
    static NativeGameTransport.CoreReceived core(NativeGameTransport t)throws Exception{return assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(Instant.now().plusSeconds(20)));}
    static NativeGameTransport.XqolThresholdReceived query(NativeGameTransport t)throws Exception{var c=core(t);return assertInstanceOf(NativeGameTransport.XqolThresholdReceived.class,t.readCurrentXqolThreshold(c,NativeCurrentXqolThreshold26785313ProducerTest.target(),c.validUntil()));}
    static NativeGameTransport.XqolThresholdPrepared prepare(NativeGameTransport t,NativeGameTransport.XqolThresholdReceived q)throws IOException{return t.prepareCurrentXqolThresholdSet(q);}
    @Test void setUsesOriginalBoundTargetActualInstanceDeadlineAndOneSubmission()throws Exception{
        var r=new Replay("capture-pair");try(var t=transport(r)){var q=query(t);var p=prepare(t,q);assertEquals(q.targetThreshold(),p.targetThreshold());assertEquals(q.frame().source().orElseThrow(),p.selected());assertEquals(q.validUntil(),p.deadline());
            var req=NativeWire.decodeExecuteRequest(p.originalPacket().value());var fields=NativeWire.object(NativeWire.parse(req.normalizedAdditionalFields().value()));assertEquals(p.targetThreshold(),fields.get("xqol_threshold").get("target_threshold").intValue());assertEquals(p.deadline().toEpochMilli(),fields.get("core_control_deadline_unix_ms").longValue());
            var out=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentXqolThresholdSet(p));assertSame(out,t.submitCurrentXqolThresholdSet(p));assertEquals(CurrentXqolThresholdResult.Status.THRESHOLD_ROUTE_DISPATCHED,CurrentXqolThresholdResult.decodeOutcome(out).status());assertEquals(CurrentXqolThresholdResult.decodeOutcome(out),p.latestFrame().orElseThrow());assertEquals(1,r.effectWrites);}
    }
    @Test void absentKnownEventOrNativeCanFalseCannotMintTheRequestedEffect()throws Exception {
        for(String mode:new String[]{"empty","shown-false","valid-false"}){var r=new Replay(mode);try(var t=transport(r)){var q=query(t);assertThrows(IOException.class,()->prepare(t,q));assertEquals(0,r.effectWrites);}}
    }
    @Test void privateSourceCannotCrossReceiverOrMintAnotherTarget()throws Exception {
        var a=new Replay("known");var b=new Replay("known");try(var t=transport(a);var other=transport(b)){var q=query(t);assertThrows(IOException.class,()->prepare(other,q));var p=prepare(t,q);assertSame(p,prepare(t,q));assertEquals(q.targetThreshold(),p.targetThreshold());assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,other.submitCurrentXqolThresholdSet(p));assertEquals(0,a.effectWrites);assertEquals(0,b.effectWrites);}
    }
    @Test void actualSetCapabilityIsRequiredEvenWhenTheSourceLooksAdmissible()throws Exception{
        var r=new Replay("missing-effects");try(var t=transport(r)){var q=query(t);assertTrue(q.frame().source().orElseThrow().setAdmissible());assertThrows(IOException.class,()->prepare(t,q));assertEquals(0,r.effectWrites);}
    }
    @Test void extendingTheOriginalCoreDeadlineIsRejectedBeforeAQueryWrite()throws Exception {
        var r=new Replay("known");try(var t=transport(r)){var c=core(t);var out=t.readCurrentXqolThreshold(c,NativeCurrentXqolThreshold26785313ProducerTest.target(),c.validUntil().plusMillis(1));assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,out.original());assertEquals(0,r.queries);assertEquals(0,r.effectWrites);}
    }
    @Test void lostEffectAcknowledgementIsStickyUnknownAndBlocksFurtherCoreEffects()throws Exception {
        var r=new Replay("lost");try(var t=transport(r)){var c=core(t);var q=assertInstanceOf(NativeGameTransport.XqolThresholdReceived.class,t.readCurrentXqolThreshold(c,NativeCurrentXqolThreshold26785313ProducerTest.target(),c.validUntil()));var p=prepare(t,q);var out=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentXqolThresholdSet(p));assertSame(out,t.submitCurrentXqolThresholdSet(p));assertSame(out,t.submitCoreNormalExit(c,c.validUntil()));assertEquals(1,r.effectWrites);}
    }
    @Test void changedReplyInstanceLeaseOrBeforeSourcePreservesAckAsUnknownWithoutReplay()throws Exception {
        for(String mode:new String[]{"wrong-instance","wrong-lease","changed-source","wrong-target"}){var r=new Replay(mode);try(var t=transport(r)){var p=prepare(t,query(t));var out=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentXqolThresholdSet(p));assertTrue(t.originalIndeterminateCoreAcknowledgement(out.requestId()).isPresent());assertSame(out,t.submitCurrentXqolThresholdSet(p));assertEquals(1,r.effectWrites);}}
    }
    @Test void malformedReadonlyOwnerOrActualCanNeverGrantsAuthority()throws Exception {
        for(String mode:new String[]{"wrong-owner","missing-can"}){var r=new Replay(mode);try(var t=transport(r)){var c=core(t);var read=t.readCurrentXqolThreshold(c,NativeCurrentXqolThreshold26785313ProducerTest.target(),c.validUntil());var out=assertInstanceOf(NativeActionPort.Unknown.class,read.original());assertTrue(t.originalIndeterminateCoreAcknowledgement(out.requestId()).isPresent());assertSame(out,t.submitCoreNormalExit(c,c.validUntil()));assertEquals(0,r.effectWrites);}}
    }
    @Test void knownZeroEffectRefusalRetainsOriginalLeaseInstanceAndSpentClaimWithoutRetry()throws Exception {
        var r=new Replay("early");try(var t=transport(r)){var q=query(t);var p=prepare(t,q);var out=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentXqolThresholdSet(p));var f=CurrentXqolThresholdResult.decodeOutcome(out);assertFalse(f.successful());assertFalse(f.effectAttempted());assertFalse(f.nativeReturned());assertEquals(BigInteger.ONE,f.claimSequence());assertEquals(q.frame().providerGeneration(),f.providerGeneration());assertEquals(q.frame().querySequence(),f.querySequence());assertEquals(Optional.of(p.instanceId()),f.instanceId());assertSame(out,t.submitCurrentXqolThresholdSet(p));assertEquals(1,r.effectWrites);}
    }
    @Test void cleanupUnknownOrRefusalClaimingAnEffectCannotMasqueradeAsKnownZeroEffect()throws Exception {
        for(String mode:new String[]{"indeterminate","bad-refusal"}){var r=new Replay(mode);try(var t=transport(r)){var p=prepare(t,query(t));var out=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentXqolThresholdSet(p));assertTrue(t.originalIndeterminateCoreAcknowledgement(out.requestId()).isPresent());assertSame(out,t.submitCurrentXqolThresholdSet(p));assertEquals(1,r.effectWrites);}}
    }
    static final class Replay implements NativePacketPort {
        final String mode;final ArrayDeque<byte[]> packets=new ArrayDeque<>();boolean closed;int queries,effectWrites;
        Replay(String mode)throws IOException{
            this.mode=mode;var f=NativeCurrentXqolThreshold26785313ProducerTest.frame("available");var h=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",42).put("connection_generation",f.owner().orElseThrow().connectionGeneration()).put("bridge_version","xqol-threshold-data").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256()).put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            var caps=h.putArray("capabilities").add(CoreFrame.CAPABILITY).add(CurrentXqolThreshold.Action.QUERY_THRESHOLD.capability());if(!mode.equals("missing-effects"))caps.add(CurrentXqolThreshold.Action.SET_THRESHOLD.capability());packets.add(NativeWire.packet(StrictJson.canonical(h)));
        }
        public void verify()throws IOException{if(closed)throw new IOException("XQOL prompt DATA port closed");}public void verifyCoreControlWindowPolicy()throws IOException{verify();}public void awaitConnection(Instant until)throws IOException{verify();}
        public byte[] readPacket(Instant until)throws IOException{verify();if(packets.isEmpty())throw new IOException("XQOL prompt DATA response missing");return packets.removeFirst();}
        public void writePacket(byte[] packet,Instant until)throws IOException{
            verify();var request=NativeWire.decodeExecuteRequest(packet);ObjectNode token;boolean ok;
            if(request.step().equals(CoreFrame.STEP)){token=NativeWire.object(NativeWire.parse(CoreFramePublicCodec.encode(NativeCurrentXqolThreshold26785313ProducerTest.actualCore()).bytes()));ok=true;}
            else{
                var fields=NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value()));var claim=fields.get("xqol_threshold");String action=claim.get("action").textValue();String role;
                if(mode.equals("capture-pair"))retainActualRequest(action,packet);
                if(action.equals("query_threshold")){queries++;assertTrue(claim.get("instance_id").isNull());role=mode.equals("empty")?"empty":mode.equals("shown-false")?"shown-false":mode.equals("valid-false")?"valid-false":"available";}
                else{effectWrites++;assertEquals(CurrentXqolThreshold.Action.SET_THRESHOLD.step(),request.step());assertEquals(NativeCurrentXqolThreshold26785313ProducerTest.frame("set").instanceId().orElseThrow(),claim.get("instance_id").intValue());assertEquals(NativeCurrentXqolThreshold26785313ProducerTest.target(),claim.get("target_threshold").intValue());if(mode.equals("lost"))return;role=mode.equals("early")||mode.equals("bad-refusal")?"stale":mode.equals("indeterminate")?"indeterminate":"set";}
                var e=NativeCurrentXqolThreshold26785313ProducerTest.envelope(role);token=NativeWire.object(e.get("result"));ok=e.get("ok").booleanValue();
                if(action.equals("query_threshold")){
                    if(mode.equals("wrong-owner"))((ObjectNode)token.get("owner")).put("connection_generation","0");
                    if(mode.equals("missing-can"))NativeCurrentXqolThreshold26785313ProducerTest.source(token).putNull("native_valid");
                }else{
                    if(mode.equals("wrong-instance"))token.put("instance_id",Integer.MAX_VALUE);if(mode.equals("wrong-lease"))token.put("query_sequence","0");
                    if(mode.equals("changed-source"))NativeCurrentXqolThreshold26785313ProducerTest.event(token).put("opening","explicit Java negative before-source mutation");if(mode.equals("wrong-target"))NativeCurrentXqolThreshold26785313ProducerTest.source(token).put("target_threshold",NativeCurrentXqolThreshold26785313ProducerTest.target()==100?0:100);
                    if(mode.equals("early"))token.put("claim_sequence","1");if(mode.equals("bad-refusal"))token.put("effect_attempted",true);
                }
            }
            var e=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",request.requestId()).put("ok",ok);e.set("result",token);packets.add(NativeWire.packet(StrictJson.canonical(e)));
        }
        public void close(){closed=true;}
        static void retainActualRequest(String action,byte[] packet)throws IOException{
            String folder=System.getProperty("xar.current267.xqol.threshold.java.requests");if(folder==null)return;var p=java.nio.file.Path.of(folder).toAbsolutePath().normalize();if(!p.getRoot().toString().equalsIgnoreCase("D:\\"))throw new IOException("D request artifact root required");java.nio.file.Files.createDirectories(p);p=p.resolve(action+".request.json");if(!java.nio.file.Files.exists(p))java.nio.file.Files.write(p,java.util.Arrays.copyOfRange(packet,4,packet.length),java.nio.file.StandardOpenOption.CREATE_NEW);
        }
    }
}
