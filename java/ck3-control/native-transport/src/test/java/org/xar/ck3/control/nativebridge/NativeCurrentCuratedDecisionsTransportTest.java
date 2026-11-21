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

/** Actual a07 tokens in a NoGame port. Fresh outer IDs and selected-query DATA are explicitly Java-owned. */
class NativeCurrentCuratedDecisionsTransportTest {
    static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    static NativeGameTransport transport(Replay r){return new NativeGameTransport(r,new NativePipeEndpoint.Config("\\\\.\\pipe\\curated-data","curated-data",GAME,"curated-session","curated-data",BUILD.executableSha256(),BUILD.coreFrameAdapterId()),64,32);}
    static NativeGameTransport.CoreReceived core(NativeGameTransport t)throws Exception{return assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(Instant.now().plusSeconds(20)));}
    static NativeGameTransport.CuratedDecisionReceived query(NativeGameTransport t)throws Exception{var c=core(t);return assertInstanceOf(NativeGameTransport.CuratedDecisionReceived.class,t.readCurrentCuratedDecisions(c,c.validUntil()));}
    static Optional<CurrentCuratedDecisions.DecisionKey> key(CurrentCuratedDecisions.Action a)throws Exception{return a==CurrentCuratedDecisions.Action.OPEN_LIST?Optional.empty():NativeCurrentCuratedDecisions26785313ProducerTest.frame(a==CurrentCuratedDecisions.Action.CONFIRM?"confirm.result":"open-detail.result").decisionKey();}
    @Test void threeFixedEffectsUseOriginalSourceDeadlineAndAreSubmittedOnlyOnce()throws Exception{
        for(var action:new CurrentCuratedDecisions.Action[]{CurrentCuratedDecisions.Action.OPEN_LIST,CurrentCuratedDecisions.Action.OPEN_DETAIL,CurrentCuratedDecisions.Action.CONFIRM}){
            var r=new Replay("capture",action);try(var t=transport(r)){var q=query(t);var p=t.prepareCurrentCuratedDecision(q,action,key(action));assertEquals(q.validUntil(),p.deadline());assertEquals(q.frame().source().orElseThrow(),p.selected());
                var wire=NativeWire.decodeExecuteRequest(p.originalPacket().value());var fields=NativeWire.parse(wire.normalizedAdditionalFields().value());assertEquals(p.deadline().toEpochMilli(),fields.get("core_control_deadline_unix_ms").longValue());
                var ack=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentCuratedDecision(p));assertSame(ack,t.submitCurrentCuratedDecision(p));assertEquals(CurrentCuratedDecisionsResult.dispatchedStatus(action),CurrentCuratedDecisionsResult.decodeOutcome(ack).status());assertEquals(CurrentCuratedDecisionsResult.decodeOutcome(ack),p.latestFrame().orElseThrow());assertEquals(1,r.effects);}
        }
    }
    @Test void actualNegativeCanOrMissingModelNeverAuthorizesConfirmationOrDetail()throws Exception{
        var r=new Replay("negative-can",CurrentCuratedDecisions.Action.CONFIRM);try(var t=transport(r)){var q=query(t);assertThrows(IOException.class,()->t.prepareCurrentCuratedDecision(q,r.action,key(r.action)));assertEquals(0,r.effects);}
        var next=new Replay("known",CurrentCuratedDecisions.Action.OPEN_LIST);try(var t=transport(next)){var q=query(t);assertFalse(q.frame().source().orElseThrow().completeModelCensus());assertThrows(IOException.class,()->t.prepareCurrentCuratedDecision(q,CurrentCuratedDecisions.Action.OPEN_DETAIL,Optional.of(CurrentCuratedDecisions.DecisionKey.MASS_CONVERSION)));assertEquals(0,next.effects);}
    }
    @Test void queryAndPreparationCannotCrossReceiversOrChangeThePreparedAction()throws Exception{
        var a=new Replay("known",CurrentCuratedDecisions.Action.OPEN_DETAIL);var b=new Replay("known",a.action);try(var t=transport(a);var other=transport(b)){var q=query(t);assertThrows(IOException.class,()->other.prepareCurrentCuratedDecision(q,a.action,key(a.action)));var p=t.prepareCurrentCuratedDecision(q,a.action,key(a.action));assertSame(p,t.prepareCurrentCuratedDecision(q,a.action,key(a.action)));assertThrows(IOException.class,()->t.prepareCurrentCuratedDecision(q,CurrentCuratedDecisions.Action.CONFIRM,key(a.action)));assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,other.submitCurrentCuratedDecision(p));assertEquals(0,a.effects);assertEquals(0,b.effects);}
    }
    @Test void capabilityAndOriginalCoreDeadlineAreRequiredBeforeAnyWrite()throws Exception{
        var r=new Replay("missing-cap",CurrentCuratedDecisions.Action.OPEN_DETAIL);try(var t=transport(r)){var q=query(t);assertThrows(IOException.class,()->t.prepareCurrentCuratedDecision(q,r.action,key(r.action)));assertEquals(0,r.effects);}
        var next=new Replay("known",CurrentCuratedDecisions.Action.OPEN_DETAIL);try(var t=transport(next)){var c=core(t);assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.readCurrentCuratedDecisions(c,c.validUntil().plusMillis(1)).original());assertEquals(0,next.queries);}
    }
    @Test void lostAcknowledgementIsStickyUnknownAndBlocksOtherCoreEffects()throws Exception{
        var r=new Replay("lost",CurrentCuratedDecisions.Action.OPEN_DETAIL);try(var t=transport(r)){var c=core(t);var q=assertInstanceOf(NativeGameTransport.CuratedDecisionReceived.class,t.readCurrentCuratedDecisions(c,c.validUntil()));var p=t.prepareCurrentCuratedDecision(q,r.action,key(r.action));var out=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentCuratedDecision(p));assertSame(out,t.submitCurrentCuratedDecision(p));assertSame(out,t.submitCoreNormalExit(c,c.validUntil()));assertEquals(1,r.effects);}
    }
    @Test void wrongLeaseKeyOrActualBeforeSourceRetainsTheAckAsUnknown()throws Exception{
        for(String mode:new String[]{"wrong-lease","wrong-key","changed-source"}){var r=new Replay(mode,CurrentCuratedDecisions.Action.OPEN_DETAIL);try(var t=transport(r)){var q=query(t);var p=t.prepareCurrentCuratedDecision(q,r.action,key(r.action));var out=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentCuratedDecision(p));assertTrue(t.originalIndeterminateCoreAcknowledgement(out.requestId()).isPresent());assertSame(out,t.submitCurrentCuratedDecision(p));assertEquals(1,r.effects);}}
    }
    @Test void malformedReadonlyOwnerOrSourceLocksEffectsInsteadOfMintingPrivateAuthority()throws Exception{
        for(String mode:new String[]{"wrong-owner","bad-source"}){var r=new Replay(mode,CurrentCuratedDecisions.Action.OPEN_DETAIL);try(var t=transport(r)){var c=core(t);var out=assertInstanceOf(NativeActionPort.Unknown.class,t.readCurrentCuratedDecisions(c,c.validUntil()).original());assertTrue(t.originalIndeterminateCoreAcknowledgement(out.requestId()).isPresent());assertSame(out,t.submitCoreNormalExit(c,c.validUntil()));assertEquals(0,r.effects);}}
    }
    @Test void knownZeroEffectSpentClaimRetainsOriginalKeyLeaseAndDoesNotReplay()throws Exception{
        var r=new Replay("refused",CurrentCuratedDecisions.Action.OPEN_DETAIL);try(var t=transport(r)){var q=query(t);var p=t.prepareCurrentCuratedDecision(q,r.action,key(r.action));var out=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentCuratedDecision(p));var f=CurrentCuratedDecisionsResult.decodeOutcome(out);assertFalse(f.successful());assertFalse(f.effectAttempted());assertEquals(BigInteger.ONE,f.claimSequence());assertEquals(q.frame().querySequence(),f.querySequence());assertEquals(p.decisionKey(),f.decisionKey());assertSame(out,t.submitCurrentCuratedDecision(p));assertEquals(1,r.effects);}
    }
    @Test void cleanupUnknownOrEffectfulRefusalCannotBeDowngradedToKnownZeroEffect()throws Exception{
        for(String mode:new String[]{"indeterminate","bad-refusal"}){var r=new Replay(mode,CurrentCuratedDecisions.Action.OPEN_DETAIL);try(var t=transport(r)){var q=query(t);var p=t.prepareCurrentCuratedDecision(q,r.action,key(r.action));var out=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentCuratedDecision(p));assertTrue(t.originalIndeterminateCoreAcknowledgement(out.requestId()).isPresent());assertSame(out,t.submitCurrentCuratedDecision(p));assertEquals(1,r.effects);}}
    }
    @Test void nativeOpenListFalseIsPreservedKnownDispatchWithoutAutomaticReopen()throws Exception{
        var r=new Replay("false-handled",CurrentCuratedDecisions.Action.OPEN_LIST);try(var t=transport(r)){var q=query(t);var p=t.prepareCurrentCuratedDecision(q,r.action,Optional.empty());var out=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentCuratedDecision(p));assertTrue(out.nativeOk());assertFalse(CurrentCuratedDecisionsResult.decodeOutcome(out).nativeHandled());assertSame(out,t.submitCurrentCuratedDecision(p));assertThrows(IOException.class,()->q.requireOriginal(t,q.validUntil()));assertEquals(1,r.effects);}
    }
    static final class Replay implements NativePacketPort {
        final String mode;final CurrentCuratedDecisions.Action action;final ArrayDeque<byte[]> packets=new ArrayDeque<>();boolean closed;int queries,effects;
        Replay(String mode,CurrentCuratedDecisions.Action action)throws IOException{this.mode=mode;this.action=action;var f=NativeCurrentCuratedDecisions26785313ProducerTest.frame("query.result");var h=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",42).put("connection_generation",f.owner().orElseThrow().connectionGeneration()).put("bridge_version","curated-data").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256()).put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);var caps=h.putArray("capabilities").add(CoreFrame.CAPABILITY).add(CurrentCuratedDecisions.Action.QUERY.capability());if(!mode.equals("missing-cap"))for(var a:CurrentCuratedDecisions.Action.values())if(a!=CurrentCuratedDecisions.Action.QUERY)caps.add(a.capability());packets.add(NativeWire.packet(StrictJson.canonical(h)));}
        public void verify()throws IOException{if(closed)throw new IOException("Curated DATA port closed");}public void verifyCoreControlWindowPolicy()throws IOException{verify();}public void awaitConnection(Instant until)throws IOException{verify();}
        public byte[] readPacket(Instant until)throws IOException{verify();if(packets.isEmpty())throw new IOException("Curated DATA response missing");return packets.removeFirst();}
        public void writePacket(byte[] packet,Instant until)throws IOException{verify();var request=NativeWire.decodeExecuteRequest(packet);ObjectNode token;boolean ok;
            if(request.step().equals(CoreFrame.STEP)){token=NativeWire.object(NativeWire.parse(CoreFramePublicCodec.encode(NativeCurrentCuratedDecisions26785313ProducerTest.actualCore()).bytes()));ok=true;}
            else{var claim=NativeWire.parse(request.normalizedAdditionalFields().value()).get("curated_decisions");String a=claim.get("action").textValue();if(mode.equals("capture"))retain(a,packet);boolean query=a.equals("query");String role;
                if(query){queries++;role=action==CurrentCuratedDecisions.Action.OPEN_LIST?"query-nav.result":mode.equals("negative-can")?"query-can-false.result":"query.result";}
                else{effects++;assertEquals(action.step(),request.step());if(mode.equals("lost"))return;role=mode.equals("refused")||mode.equals("bad-refusal")?"stale-source.result":mode.equals("indeterminate")?"indeterminate.result":switch(action){case OPEN_LIST->"open-list.result";case OPEN_DETAIL->"open-detail.result";case CONFIRM->"confirm.result";default->throw new IOException("Unexpected action");};}
                var e=NativeCurrentCuratedDecisions26785313ProducerTest.envelope(role);token=NativeWire.object(e.get("result"));ok=e.get("ok").booleanValue();
                if(query){
                    if(action==CurrentCuratedDecisions.Action.CONFIRM&&!mode.equals("negative-can")){
                        // Explicit Java transport DATA: preserve the genuine selected before-source,
                        // while making a readonly query envelope. This is not another C++ producer frame.
                        var selected=NativeCurrentCuratedDecisions26785313ProducerTest.envelope("confirm.result");token.set("source",selected.get("result").get("source").deepCopy());}
                    if(mode.equals("wrong-owner"))((ObjectNode)token.get("owner")).put("connection_generation","0");
                    if(mode.equals("bad-source"))((ObjectNode)token.get("source")).put("groups_count",-1);
                }else{
                    if(mode.equals("wrong-lease"))token.put("query_sequence","0");
                    if(mode.equals("wrong-key"))token.put("decision_key",CurrentCuratedDecisions.DecisionKey.VIVHITE_CREATOR.wire());
                    if(mode.equals("changed-source"))((ObjectNode)token.get("source")).put("widget_state",12345);
                    if(mode.equals("refused"))token.put("claim_sequence","1");
                    if(mode.equals("bad-refusal"))token.put("effect_attempted",true);
                    if(mode.equals("false-handled"))token.put("native_handled",false);
                }
            }
            var out=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",request.requestId()).put("ok",ok);out.set("result",token);packets.add(NativeWire.packet(StrictJson.canonical(out)));}
        public void close(){closed=true;}
        private static void retain(String action,byte[] packet)throws IOException{String dir=System.getProperty("xar.current267.curated.java.requests");if(dir==null)return;var p=java.nio.file.Path.of(dir).toAbsolutePath().normalize();if(!p.getRoot().toString().equalsIgnoreCase("D:\\"))throw new IOException("D request root required");java.nio.file.Files.createDirectories(p);p=p.resolve(action+".request.json");if(!java.nio.file.Files.exists(p))java.nio.file.Files.write(p,java.util.Arrays.copyOfRange(packet,4,packet.length),java.nio.file.StandardOpenOption.CREATE_NEW);}
    }
}
