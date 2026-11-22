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
class NativeCurrentCourtierChoicesTransportTest {
    static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    static NativeGameTransport transport(Replay r){return new NativeGameTransport(r,new NativePipeEndpoint.Config("\\\\.\\pipe\\courtier-choices-data","courtier-choices-data",GAME,"courtier-choices-session","courtier-choices-data",BUILD.executableSha256(),BUILD.coreFrameAdapterId()),64,32);}
    static NativeGameTransport.CoreReceived core(NativeGameTransport t)throws Exception{return assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(Instant.now().plusSeconds(20)));}
    static NativeGameTransport.CourtierChoicesReceived query(NativeGameTransport t)throws Exception{var c=core(t);return assertInstanceOf(NativeGameTransport.CourtierChoicesReceived.class,t.readCurrentCourtierChoices(c,NativeCurrentCourtierChoices26785313ProducerTest.product(),NativeCurrentCourtierChoices26785313ProducerTest.catalog(),c.validUntil()));}
    static NativeGameTransport.CourtierChoicesPrepared prepare(NativeGameTransport t,NativeGameTransport.CourtierChoicesReceived q)throws IOException{return t.prepareCurrentCourtierChoicesSelect(q.exactKey(NativeCurrentCourtierChoices26785313ProducerTest.key()));}
    @Test void executeUsesOriginalFixedProductControlDeadlineAndOneSubmission()throws Exception{
        var r=new Replay("capture-pair");try(var t=transport(r)){var q=query(t);var p=prepare(t,q);assertEquals(q.product(),p.product());assertEquals(q.catalog(),p.catalog());assertEquals(q.frame().source().orElseThrow().rows().stream().filter(row->row.key().equals(p.selected().key())).findFirst().orElseThrow(),p.selected().row());assertEquals(q.validUntil(),p.deadline());
            var req=NativeWire.decodeExecuteRequest(p.originalPacket().value());var fields=NativeWire.object(NativeWire.parse(req.normalizedAdditionalFields().value()));assertEquals(p.product().wire(),fields.get("courtier_choices").get("product").textValue());assertEquals(p.catalog().wire(),fields.get("courtier_choices").get("catalog").textValue());assertEquals(p.selected().choiceToken(),fields.get("courtier_choices").get("choice_token").textValue());assertEquals(p.deadline().toEpochMilli(),fields.get("core_control_deadline_unix_ms").longValue());
            var out=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentCourtierChoicesSelect(p));assertSame(out,t.submitCurrentCourtierChoicesSelect(p));assertEquals(CurrentCourtierChoicesResult.Status.CHOICE_DISPATCHED,CurrentCourtierChoicesResult.decodeOutcome(out).status());assertEquals(CurrentCourtierChoicesResult.decodeOutcome(out),p.latestFrame().orElseThrow());assertEquals(1,r.effectWrites);}
    }
    @Test void absentKnownEventOrNativeCanFalseCannotMintTheRequestedEffect()throws Exception {
        for(String mode:new String[]{"empty","shown-false","valid-false","incomplete-numeric"}){var r=new Replay(mode);try(var t=transport(r)){var q=query(t);assertThrows(IOException.class,()->prepare(t,q));assertEquals(0,r.effectWrites);}}
    }
    @Test void privateSourceCannotCrossReceiverOrMintAnotherFixedControl()throws Exception {
        var a=new Replay("known");var b=new Replay("known");try(var t=transport(a);var other=transport(b)){var q=query(t);assertThrows(IOException.class,()->prepare(other,q));var p=prepare(t,q);assertSame(p,prepare(t,q));assertEquals(q.product(),p.product());assertEquals(q.catalog(),p.catalog());assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,other.submitCurrentCourtierChoicesSelect(p));assertEquals(0,a.effectWrites);assertEquals(0,b.effectWrites);}
    }
    @Test void actualExecuteCapabilityIsRequiredEvenWhenTheSourceLooksAdmissible()throws Exception{
        var r=new Replay("missing-effects");try(var t=transport(r)){var q=query(t);assertTrue(q.exactKey(NativeCurrentCourtierChoices26785313ProducerTest.key()).row().executeAdmissible());assertThrows(IOException.class,()->prepare(t,q));assertEquals(0,r.effectWrites);}
    }
    @Test void extendingTheOriginalCoreDeadlineIsRejectedBeforeAQueryWrite()throws Exception {
        var r=new Replay("known");try(var t=transport(r)){var c=core(t);var out=t.readCurrentCourtierChoices(c,NativeCurrentCourtierChoices26785313ProducerTest.product(),NativeCurrentCourtierChoices26785313ProducerTest.catalog(),c.validUntil().plusMillis(1));assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,out.original());assertEquals(0,r.queries);assertEquals(0,r.effectWrites);}
    }
    @Test void lostEffectAcknowledgementIsStickyUnknownAndBlocksFurtherCoreEffects()throws Exception {
        var r=new Replay("lost");try(var t=transport(r)){var c=core(t);var q=assertInstanceOf(NativeGameTransport.CourtierChoicesReceived.class,t.readCurrentCourtierChoices(c,NativeCurrentCourtierChoices26785313ProducerTest.product(),NativeCurrentCourtierChoices26785313ProducerTest.catalog(),c.validUntil()));var p=prepare(t,q);var out=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentCourtierChoicesSelect(p));assertSame(out,t.submitCurrentCourtierChoicesSelect(p));assertSame(out,t.submitCoreNormalExit(c,c.validUntil()));assertEquals(1,r.effectWrites);}
    }
    @Test void changedReplyProductControlLeaseOrBeforeSourcePreservesAckAsUnknownWithoutReplay()throws Exception {
        for(String mode:new String[]{"wrong-product","wrong-lease","changed-source","wrong-catalog","changed-token","changed-configuration","changed-selected"}){var r=new Replay(mode);try(var t=transport(r)){var p=prepare(t,query(t));var out=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentCourtierChoicesSelect(p));assertTrue(t.originalIndeterminateCoreAcknowledgement(out.requestId()).isPresent());assertSame(out,t.submitCurrentCourtierChoicesSelect(p));assertEquals(1,r.effectWrites);}}
    }
    @Test void malformedReadonlyOwnerOrActualCanNeverGrantsAuthority()throws Exception {
        for(String mode:new String[]{"wrong-owner","missing-can"}){var r=new Replay(mode);try(var t=transport(r)){var c=core(t);var read=t.readCurrentCourtierChoices(c,NativeCurrentCourtierChoices26785313ProducerTest.product(),NativeCurrentCourtierChoices26785313ProducerTest.catalog(),c.validUntil());var out=assertInstanceOf(NativeActionPort.Unknown.class,read.original());assertTrue(t.originalIndeterminateCoreAcknowledgement(out.requestId()).isPresent());assertSame(out,t.submitCoreNormalExit(c,c.validUntil()));assertEquals(0,r.effectWrites);}}
    }
    @Test void knownZeroEffectRefusalRetainsOriginalLeaseProductControlAndSpentClaimWithoutRetry()throws Exception {
        var r=new Replay("early");try(var t=transport(r)){var q=query(t);var p=prepare(t,q);var out=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentCourtierChoicesSelect(p));var f=CurrentCourtierChoicesResult.decodeOutcome(out);assertFalse(f.successful());assertFalse(f.effectAttempted());assertFalse(f.nativeReturned());assertEquals(BigInteger.ONE,f.claimSequence());assertEquals(q.frame().providerGeneration(),f.providerGeneration());assertEquals(q.frame().querySequence(),f.querySequence());assertEquals(p.product(),f.product());assertEquals(p.catalog(),f.catalog());assertSame(out,t.submitCurrentCourtierChoicesSelect(p));assertEquals(1,r.effectWrites);}
    }
    @Test void cleanupUnknownOrRefusalClaimingAnEffectCannotMasqueradeAsKnownZeroEffect()throws Exception {
        for(String mode:new String[]{"indeterminate","bad-refusal"}){var r=new Replay(mode);try(var t=transport(r)){var p=prepare(t,query(t));var out=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentCourtierChoicesSelect(p));assertTrue(t.originalIndeterminateCoreAcknowledgement(out.requestId()).isPresent());assertSame(out,t.submitCurrentCourtierChoicesSelect(p));assertEquals(1,r.effectWrites);}}
    }
    static final class Replay implements NativePacketPort {
        final String mode;final ArrayDeque<byte[]> packets=new ArrayDeque<>();boolean closed;int queries,effectWrites;
        Replay(String mode)throws IOException{
            this.mode=mode;var f=NativeCurrentCourtierChoices26785313ProducerTest.frame("available");var h=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",42).put("connection_generation",f.owner().orElseThrow().connectionGeneration()).put("bridge_version","courtier-choices-data").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256()).put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            var caps=h.putArray("capabilities").add(CoreFrame.CAPABILITY).add(CurrentCourtierChoices.Action.QUERY_CHOICES.capability());if(!mode.equals("missing-effects"))caps.add(CurrentCourtierChoices.Action.SELECT_CHOICE.capability());packets.add(NativeWire.packet(StrictJson.canonical(h)));
        }
        public void verify()throws IOException{if(closed)throw new IOException("Courtier catalog DATA port closed");}public void verifyCoreControlWindowPolicy()throws IOException{verify();}public void awaitConnection(Instant until)throws IOException{verify();}
        public byte[] readPacket(Instant until)throws IOException{verify();if(packets.isEmpty())throw new IOException("Courtier catalog DATA response missing");return packets.removeFirst();}
        public void writePacket(byte[] packet,Instant until)throws IOException{
            verify();var request=NativeWire.decodeExecuteRequest(packet);ObjectNode token;boolean ok;
            if(request.step().equals(CoreFrame.STEP)){token=NativeWire.object(NativeWire.parse(CoreFramePublicCodec.encode(NativeCurrentCourtierChoices26785313ProducerTest.actualCore()).bytes()));ok=true;}
            else{
                var fields=NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value()));var claim=fields.get("courtier_choices");String action=claim.get("action").textValue();String role;assertEquals(NativeCurrentCourtierChoices26785313ProducerTest.product().wire(),claim.get("product").textValue());assertEquals(NativeCurrentCourtierChoices26785313ProducerTest.catalog().wire(),claim.get("catalog").textValue());
                if(mode.equals("capture-pair"))retainActualRequest(action,packet);
                if(action.equals("query_choices")){queries++;assertEquals("0",claim.get("provider_generation").textValue());role=mode.equals("empty")?"absent":mode.equals("shown-false")?"shown-false":mode.equals("valid-false")?"valid-false":"available";}
                else{effectWrites++;assertEquals(CurrentCourtierChoices.Action.SELECT_CHOICE.step(),request.step());assertFalse(claim.has("instance_id"));assertFalse(claim.has("target_threshold"));if(mode.equals("lost"))return;role=mode.equals("early")||mode.equals("bad-refusal")?"stale":mode.equals("indeterminate")?"indeterminate":"select";}
                var e=NativeCurrentCourtierChoices26785313ProducerTest.envelope(role);token=NativeWire.object(e.get("result"));ok=e.get("ok").booleanValue();
                if(action.equals("query_choices")){
                    var actualSource=NativeCurrentCourtierChoices26785313ProducerTest.source(token);
                    if(mode.equals("incomplete-numeric")){for(var row:actualSource.get("rows"))((ObjectNode)row).put("execute_admissible",false);((ObjectNode)actualSource.get("configuration")).putNull("cost");}
                    if(mode.equals("shown-false"))NativeCurrentCourtierChoices26785313ProducerTest.row(token).put("native_shown",false).put("execute_admissible",false);
                    if(mode.equals("valid-false"))NativeCurrentCourtierChoices26785313ProducerTest.row(token).put("native_valid",false).put("execute_admissible",false);
                    if(mode.equals("wrong-owner"))((ObjectNode)token.get("owner")).put("connection_generation","0");
                    if(mode.equals("missing-can"))NativeCurrentCourtierChoices26785313ProducerTest.row(token).putNull("native_valid");
                }else{
                    if(mode.equals("wrong-product"))token.put("product",NativeCurrentCourtierChoices26785313ProducerTest.product()==CurrentCourtierControls.Product.MAIN?"vivhite":"main");if(mode.equals("wrong-lease"))token.put("query_sequence","0");
                    if(mode.equals("changed-configuration"))((ObjectNode)NativeCurrentCourtierChoices26785313ProducerTest.source(token).get("configuration")).put("cost","1000001");if(mode.equals("changed-source"))NativeCurrentCourtierChoices26785313ProducerTest.source(token).put("window_enabled",false);if(mode.equals("wrong-catalog"))token.put("catalog",NativeCurrentCourtierChoices26785313ProducerTest.catalog()==CurrentCourtierChoices.Catalog.OTHER?"education":"other");if(mode.equals("changed-token"))token.put("choice_token","changed_token");if(mode.equals("changed-selected"))NativeCurrentCourtierChoices26785313ProducerTest.row(token).put("selected",!NativeCurrentCourtierChoices26785313ProducerTest.row(token).get("selected").booleanValue());
                    if(mode.equals("early"))token.put("claim_sequence","1");if(mode.equals("bad-refusal"))token.put("effect_attempted",true);
                }
            }
            var e=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",request.requestId()).put("ok",ok);e.set("result",token);packets.add(NativeWire.packet(StrictJson.canonical(e)));
        }
        public void close(){closed=true;}
        static void retainActualRequest(String action,byte[] packet)throws IOException{
            String folder=System.getProperty("xar.current267.courtier.choices.java.requests");if(folder==null)return;var p=java.nio.file.Path.of(folder).toAbsolutePath().normalize();if(!p.getRoot().toString().equalsIgnoreCase("D:\\"))throw new IOException("D request artifact root required");java.nio.file.Files.createDirectories(p);p=p.resolve(action+".request.json");if(!java.nio.file.Files.exists(p))java.nio.file.Files.write(p,java.util.Arrays.copyOfRange(packet,4,packet.length),java.nio.file.StandardOpenOption.CREATE_NEW);
        }
    }
}
