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
class NativeCurrentCourtierControlsTransportTest {
    static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    static NativeGameTransport transport(Replay r){return new NativeGameTransport(r,new NativePipeEndpoint.Config("\\\\.\\pipe\\courtier-controls-data","courtier-controls-data",GAME,"courtier-controls-session","courtier-controls-data",BUILD.executableSha256(),BUILD.coreFrameAdapterId()),64,32);}
    static NativeGameTransport.CoreReceived core(NativeGameTransport t)throws Exception{return assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(Instant.now().plusSeconds(20)));}
    static NativeGameTransport.CourtierControlsReceived query(NativeGameTransport t)throws Exception{var c=core(t);return assertInstanceOf(NativeGameTransport.CourtierControlsReceived.class,t.readCurrentCourtierControls(c,NativeCurrentCourtierControls26785313ProducerTest.product(),NativeCurrentCourtierControls26785313ProducerTest.control(),c.validUntil()));}
    static NativeGameTransport.CourtierControlsPrepared prepare(NativeGameTransport t,NativeGameTransport.CourtierControlsReceived q)throws IOException{return t.prepareCurrentCourtierControlExecute(q);}
    @Test void executeUsesOriginalFixedProductControlDeadlineAndOneSubmission()throws Exception{
        var r=new Replay("capture-pair");try(var t=transport(r)){var q=query(t);var p=prepare(t,q);assertEquals(q.product(),p.product());assertEquals(q.control(),p.control());assertEquals(q.frame().source().orElseThrow(),p.selected());assertEquals(q.validUntil(),p.deadline());
            var req=NativeWire.decodeExecuteRequest(p.originalPacket().value());var fields=NativeWire.object(NativeWire.parse(req.normalizedAdditionalFields().value()));assertEquals(p.product().wire(),fields.get("courtier_controls").get("product").textValue());assertEquals(p.control().wire(),fields.get("courtier_controls").get("control").textValue());assertEquals(p.deadline().toEpochMilli(),fields.get("core_control_deadline_unix_ms").longValue());
            var out=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentCourtierControlExecute(p));assertSame(out,t.submitCurrentCourtierControlExecute(p));assertEquals(CurrentCourtierControlsResult.Status.CONTROL_DISPATCHED,CurrentCourtierControlsResult.decodeOutcome(out).status());assertEquals(CurrentCourtierControlsResult.decodeOutcome(out),p.latestFrame().orElseThrow());assertEquals(1,r.effectWrites);}
    }
    @Test void absentKnownEventOrNativeCanFalseCannotMintTheRequestedEffect()throws Exception {
        for(String mode:new String[]{"empty","shown-false","valid-false"}){var r=new Replay(mode);try(var t=transport(r)){var q=query(t);assertThrows(IOException.class,()->prepare(t,q));assertEquals(0,r.effectWrites);}}
    }
    @Test void privateSourceCannotCrossReceiverOrMintAnotherFixedControl()throws Exception {
        var a=new Replay("known");var b=new Replay("known");try(var t=transport(a);var other=transport(b)){var q=query(t);assertThrows(IOException.class,()->prepare(other,q));var p=prepare(t,q);assertSame(p,prepare(t,q));assertEquals(q.product(),p.product());assertEquals(q.control(),p.control());assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,other.submitCurrentCourtierControlExecute(p));assertEquals(0,a.effectWrites);assertEquals(0,b.effectWrites);}
    }
    @Test void actualExecuteCapabilityIsRequiredEvenWhenTheSourceLooksAdmissible()throws Exception{
        var r=new Replay("missing-effects");try(var t=transport(r)){var q=query(t);assertTrue(q.frame().source().orElseThrow().executeAdmissible());assertThrows(IOException.class,()->prepare(t,q));assertEquals(0,r.effectWrites);}
    }
    @Test void extendingTheOriginalCoreDeadlineIsRejectedBeforeAQueryWrite()throws Exception {
        var r=new Replay("known");try(var t=transport(r)){var c=core(t);var out=t.readCurrentCourtierControls(c,NativeCurrentCourtierControls26785313ProducerTest.product(),NativeCurrentCourtierControls26785313ProducerTest.control(),c.validUntil().plusMillis(1));assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,out.original());assertEquals(0,r.queries);assertEquals(0,r.effectWrites);}
    }
    @Test void lostEffectAcknowledgementIsStickyUnknownAndBlocksFurtherCoreEffects()throws Exception {
        var r=new Replay("lost");try(var t=transport(r)){var c=core(t);var q=assertInstanceOf(NativeGameTransport.CourtierControlsReceived.class,t.readCurrentCourtierControls(c,NativeCurrentCourtierControls26785313ProducerTest.product(),NativeCurrentCourtierControls26785313ProducerTest.control(),c.validUntil()));var p=prepare(t,q);var out=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentCourtierControlExecute(p));assertSame(out,t.submitCurrentCourtierControlExecute(p));assertSame(out,t.submitCoreNormalExit(c,c.validUntil()));assertEquals(1,r.effectWrites);}
    }
    @Test void changedReplyProductControlLeaseOrBeforeSourcePreservesAckAsUnknownWithoutReplay()throws Exception {
        for(String mode:new String[]{"wrong-product","wrong-lease","changed-source","wrong-control"}){var r=new Replay(mode);try(var t=transport(r)){var p=prepare(t,query(t));var out=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentCourtierControlExecute(p));assertTrue(t.originalIndeterminateCoreAcknowledgement(out.requestId()).isPresent());assertSame(out,t.submitCurrentCourtierControlExecute(p));assertEquals(1,r.effectWrites);}}
    }
    @Test void malformedReadonlyOwnerOrActualCanNeverGrantsAuthority()throws Exception {
        for(String mode:new String[]{"wrong-owner","missing-can"}){var r=new Replay(mode);try(var t=transport(r)){var c=core(t);var read=t.readCurrentCourtierControls(c,NativeCurrentCourtierControls26785313ProducerTest.product(),NativeCurrentCourtierControls26785313ProducerTest.control(),c.validUntil());var out=assertInstanceOf(NativeActionPort.Unknown.class,read.original());assertTrue(t.originalIndeterminateCoreAcknowledgement(out.requestId()).isPresent());assertSame(out,t.submitCoreNormalExit(c,c.validUntil()));assertEquals(0,r.effectWrites);}}
    }
    @Test void knownZeroEffectRefusalRetainsOriginalLeaseProductControlAndSpentClaimWithoutRetry()throws Exception {
        var r=new Replay("early");try(var t=transport(r)){var q=query(t);var p=prepare(t,q);var out=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentCourtierControlExecute(p));var f=CurrentCourtierControlsResult.decodeOutcome(out);assertFalse(f.successful());assertFalse(f.effectAttempted());assertFalse(f.nativeReturned());assertEquals(BigInteger.ONE,f.claimSequence());assertEquals(q.frame().providerGeneration(),f.providerGeneration());assertEquals(q.frame().querySequence(),f.querySequence());assertEquals(p.product(),f.product());assertEquals(p.control(),f.control());assertSame(out,t.submitCurrentCourtierControlExecute(p));assertEquals(1,r.effectWrites);}
    }
    @Test void cleanupUnknownOrRefusalClaimingAnEffectCannotMasqueradeAsKnownZeroEffect()throws Exception {
        for(String mode:new String[]{"indeterminate","bad-refusal"}){var r=new Replay(mode);try(var t=transport(r)){var p=prepare(t,query(t));var out=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentCourtierControlExecute(p));assertTrue(t.originalIndeterminateCoreAcknowledgement(out.requestId()).isPresent());assertSame(out,t.submitCurrentCourtierControlExecute(p));assertEquals(1,r.effectWrites);}}
    }
    static final class Replay implements NativePacketPort {
        final String mode;final ArrayDeque<byte[]> packets=new ArrayDeque<>();boolean closed;int queries,effectWrites;
        Replay(String mode)throws IOException{
            this.mode=mode;var f=NativeCurrentCourtierControls26785313ProducerTest.frame("available");var h=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",42).put("connection_generation",f.owner().orElseThrow().connectionGeneration()).put("bridge_version","courtier-controls-data").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256()).put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            var caps=h.putArray("capabilities").add(CoreFrame.CAPABILITY).add(CurrentCourtierControls.Action.QUERY_CONTROL.capability());if(!mode.equals("missing-effects"))caps.add(CurrentCourtierControls.Action.EXECUTE_CONTROL.capability());packets.add(NativeWire.packet(StrictJson.canonical(h)));
        }
        public void verify()throws IOException{if(closed)throw new IOException("Courtier control DATA port closed");}public void verifyCoreControlWindowPolicy()throws IOException{verify();}public void awaitConnection(Instant until)throws IOException{verify();}
        public byte[] readPacket(Instant until)throws IOException{verify();if(packets.isEmpty())throw new IOException("Courtier control DATA response missing");return packets.removeFirst();}
        public void writePacket(byte[] packet,Instant until)throws IOException{
            verify();var request=NativeWire.decodeExecuteRequest(packet);ObjectNode token;boolean ok;
            if(request.step().equals(CoreFrame.STEP)){token=NativeWire.object(NativeWire.parse(CoreFramePublicCodec.encode(NativeCurrentCourtierControls26785313ProducerTest.actualCore()).bytes()));ok=true;}
            else{
                var fields=NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value()));var claim=fields.get("courtier_controls");String action=claim.get("action").textValue();String role;assertEquals(NativeCurrentCourtierControls26785313ProducerTest.product().wire(),claim.get("product").textValue());assertEquals(NativeCurrentCourtierControls26785313ProducerTest.control().wire(),claim.get("control").textValue());
                if(mode.equals("capture-pair"))retainActualRequest(action,packet);
                if(action.equals("query_control")){queries++;assertEquals("0",claim.get("provider_generation").textValue());role="available";}
                else{effectWrites++;assertEquals(CurrentCourtierControls.Action.EXECUTE_CONTROL.step(),request.step());assertFalse(claim.has("instance_id"));assertFalse(claim.has("target_threshold"));if(mode.equals("lost"))return;role=mode.equals("early")||mode.equals("bad-refusal")?"stale":mode.equals("indeterminate")?"indeterminate":"execute";}
                var e=NativeCurrentCourtierControls26785313ProducerTest.envelope(role);token=NativeWire.object(e.get("result"));ok=e.get("ok").booleanValue();
                if(action.equals("query_control")){
                    var actualSource=NativeCurrentCourtierControls26785313ProducerTest.source(token);
                    if(mode.equals("empty"))actualSource.put("creator_window_found",false).put("modal_found",false).put("panel_found",false).put("window_visible",false).put("window_enabled",false).put("execute_admissible",false).putNull("native_definition_found").putNull("native_shown").putNull("native_valid");
                    if(mode.equals("shown-false"))actualSource.put("native_shown",false).put("execute_admissible",false);
                    if(mode.equals("valid-false"))actualSource.put("native_valid",false).put("execute_admissible",false);
                    if(mode.equals("wrong-owner"))((ObjectNode)token.get("owner")).put("connection_generation","0");
                    if(mode.equals("missing-can"))NativeCurrentCourtierControls26785313ProducerTest.source(token).putNull("native_valid");
                }else{
                    if(mode.equals("wrong-product"))token.put("product",NativeCurrentCourtierControls26785313ProducerTest.product()==CurrentCourtierControls.Product.MAIN?"vivhite":"main");if(mode.equals("wrong-lease"))token.put("query_sequence","0");
                    if(mode.equals("changed-source"))NativeCurrentCourtierControls26785313ProducerTest.source(token).put("window_enabled",false);if(mode.equals("wrong-control"))token.put("control",NativeCurrentCourtierControls26785313ProducerTest.control()==CurrentCourtierControls.Control.CONFIRM?"cancel":"confirm");
                    if(mode.equals("early"))token.put("claim_sequence","1");if(mode.equals("bad-refusal"))token.put("effect_attempted",true);
                }
            }
            var e=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",request.requestId()).put("ok",ok);e.set("result",token);packets.add(NativeWire.packet(StrictJson.canonical(e)));
        }
        public void close(){closed=true;}
        static void retainActualRequest(String action,byte[] packet)throws IOException{
            String folder=System.getProperty("xar.current267.courtier.controls.java.requests");if(folder==null)return;var p=java.nio.file.Path.of(folder).toAbsolutePath().normalize();if(!p.getRoot().toString().equalsIgnoreCase("D:\\"))throw new IOException("D request artifact root required");java.nio.file.Files.createDirectories(p);p=p.resolve(action+".request.json");if(!java.nio.file.Files.exists(p))java.nio.file.Files.write(p,java.util.Arrays.copyOfRange(packet,4,packet.length),java.nio.file.StandardOpenOption.CREATE_NEW);
        }
    }
}
