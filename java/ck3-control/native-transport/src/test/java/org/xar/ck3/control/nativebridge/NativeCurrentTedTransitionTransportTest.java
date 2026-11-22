package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;

/** Generated Java DATA port. The producer class separately verifies all original C++ bytes and exact original exchanges. */
class NativeCurrentTedTransitionTransportTest {
    static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    static ObjectNode token(String name)throws IOException{
        try(var in=NativeCurrentTedTransitionTransportTest.class.getResourceAsStream("/current267-ted-cpp-a01/"+name+".json")){
            if(in==null)throw new IOException("Original TED template missing: "+name);return NativeWire.object(NativeWire.parse(in.readAllBytes()).get("result"));
        }
    }
    static CurrentTedActorTransitionResult frame(String name)throws IOException{return CurrentTedActorTransitionResult.decode(new RawJson(StrictJson.canonical(token(name))));}
    static NativeGameTransport transport(Replay r){return new NativeGameTransport(r,new NativePipeEndpoint.Config("\\\\.\\pipe\\ted-data","ted-data",GAME,"ted-data-session","ted-data",BUILD.executableSha256(),BUILD.coreFrameAdapterId()),1024,40);}
    static NativeGameTransport.CoreReceived core(NativeGameTransport t)throws Exception{return assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(Instant.now().plusSeconds(30)));}
    static NativeGameTransport.TedRoleReceived role(NativeGameTransport t,Instant until)throws Exception{var c=core(t);return assertInstanceOf(NativeGameTransport.TedRoleReceived.class,t.readCurrentTedRole(c,until==null?c.validUntil():until));}
    static NativeGameTransport.TedAdvancePrepared first(NativeGameTransport t)throws Exception{return t.prepareCurrentTedAdvance(role(t,null));}
    static void pending(NativeGameTransport t,NativeGameTransport.TedAdvancePrepared p)throws Exception{
        assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentTedAdvance(p));
        for(int i=0;i<3&&p.latestFrame().orElseThrow().status()!=CurrentTedActorTransitionResult.Status.TRANSITION_PENDING;i++)assertInstanceOf(NativeActionPort.AckReceived.class,t.queryCurrentTedOperation(p,p.deadline()));
        assertEquals(CurrentTedActorTransitionResult.Status.TRANSITION_PENDING,p.latestFrame().orElseThrow().status());
    }
    static NativeGameTransport.TedEpochPrepared confirm(NativeGameTransport t,NativeGameTransport.TedAdvancePrepared p)throws Exception{
        var after=role(t,p.deadline());var e=t.prepareCurrentTedEpoch(p,after);assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentTedEpoch(e));return e;
    }

    @Test void twoIndependentDaysRetainOriginalPendingAndPrivateConfirmedEpochWithoutResettingTheFirstClaim()throws Exception{
        var r=new Replay("known");try(var t=transport(r)){var p=first(t);var packet=NativeWire.decodeExecuteRequest(p.originalPacket().value());var body=NativeWire.parse(packet.normalizedAdditionalFields().value());assertEquals(11,body.get("ted_actor_transition").size());assertEquals(p.deadline().toEpochMilli(),body.get("core_control_deadline_unix_ms").longValue());
            pending(t,p);var original=p.latestFrame().orElseThrow();assertEquals(p.operationId(),original.operationId());assertTrue(original.source().isEmpty());assertTrue(original.effectAttempted());assertTrue(original.nativeReturned());
            var e=confirm(t,p);assertEquals(BigInteger.ONE,e.latestFrame().orElseThrow().actorEpoch());assertEquals(BigInteger.ZERO,e.latestFrame().orElseThrow().source().orElseThrow().actorEpoch());assertFalse(e.latestFrame().orElseThrow().effectAttempted());assertFalse(e.latestFrame().orElseThrow().nativeReturned());
            var q=role(t,null);var second=t.prepareCurrentTedAdvance(q);assertNotEquals(p.requestId(),second.requestId());assertNotEquals(p.operationId(),second.operationId());assertEquals(p.targetDateRaw()+24,second.targetDateRaw());
            assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentTedAdvance(second));assertInstanceOf(NativeActionPort.AckReceived.class,t.queryCurrentTedOperation(second,second.deadline()));assertEquals(CurrentTedActorTransitionResult.Status.COMPLETED_DAY,second.latestFrame().orElseThrow().status());assertEquals(BigInteger.TWO,second.latestFrame().orElseThrow().actorEpoch());
            assertEquals(second.targetDateRaw(),((CoreFrame.Partial)core(t).frame()).prefix().dateRaw());assertEquals(2,r.advanceWrites);assertEquals(1,r.epochWrites);assertEquals(original.claimSequence(),p.latestFrame().orElseThrow().claimSequence());}
    }
    @Test void originalAdvanceAndEpochPreparationsAreSingleSubmissionAndCannotCrossReceivers()throws Exception{
        var a=new Replay("known");var b=new Replay("known");try(var t=transport(a);var other=transport(b)){var q=role(t,null);assertThrows(IOException.class,()->other.prepareCurrentTedAdvance(q));var p=t.prepareCurrentTedAdvance(q);assertSame(p,t.prepareCurrentTedAdvance(q));assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,other.submitCurrentTedAdvance(p));
            var out=t.submitCurrentTedAdvance(p);assertSame(out,t.submitCurrentTedAdvance(p));while(p.latestFrame().orElseThrow().status()!=CurrentTedActorTransitionResult.Status.TRANSITION_PENDING)t.queryCurrentTedOperation(p,p.deadline());
            var after=role(t,p.deadline());var e=t.prepareCurrentTedEpoch(p,after);assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,other.submitCurrentTedEpoch(e));var ack=t.submitCurrentTedEpoch(e);assertSame(ack,t.submitCurrentTedEpoch(e));assertEquals(1,a.advanceWrites);assertEquals(1,a.epochWrites);assertEquals(0,b.advanceWrites+b.epochWrites);}
    }
    @Test void missingOrFalseActualRoleNeverGrantsDateAuthority()throws Exception{
        for(String mode:List.of("missing","false-role")){var r=new Replay(mode);try(var t=transport(r)){var q=role(t,null);assertFalse(q.frame().source().orElseThrow().advanceAdmissible());assertThrows(IOException.class,()->t.prepareCurrentTedAdvance(q));assertEquals(0,r.advanceWrites);}}
    }
    @Test void callerCannotSkipPendingConfirmationOrImportAnEpochFromAnotherReceiver()throws Exception{
        var r=new Replay("known");try(var t=transport(r)){var p=first(t);pending(t,p);var after=role(t,p.deadline());assertThrows(IOException.class,()->t.prepareCurrentTedAdvance(after));assertEquals(1,r.advanceWrites);}
        var x=new Replay("starts-at-epoch1");try(var t=transport(x)){var q=role(t,null);assertEquals(BigInteger.ONE,q.frame().actorEpoch());assertThrows(IOException.class,()->t.prepareCurrentTedAdvance(q));assertEquals(0,x.advanceWrites);}
    }
    @Test void pendingConfirmationRequiresIndependentLaterCoreWithExactActorDateAndOriginalDeadline()throws Exception{
        var r=new Replay("known");try(var t=transport(r)){var p=first(t);pending(t,p);var after=role(t,p.deadline());var e=t.prepareCurrentTedEpoch(p,after);assertEquals(after.validUntil(),e.deadline());assertFalse(e.deadline().isAfter(p.deadline()));
            var q=NativeWire.parse(NativeWire.decodeExecuteRequest(e.originalPacket().value()).normalizedAdditionalFields().value());assertEquals(p.operationId(),q.get("ted_actor_transition").get("operation_id").textValue());assertEquals(e.deadline().toEpochMilli(),q.get("core_control_deadline_unix_ms").longValue());assertEquals(1,r.advanceWrites);}
        var x=new Replay("wrong-after-core");try(var t=transport(x)){var p=first(t);pending(t,p);var c=core(t);var after=t.readCurrentTedRole(c,p.deadline());assertInstanceOf(NativeGameTransport.TedRoleUnavailable.class,after);assertEquals(0,x.epochWrites);}
    }
    @Test void statusReadKeepsOriginalArmBodyFactsFlagsAndNeverMintsAnotherSource()throws Exception{
        var r=new Replay("known");try(var t=transport(r)){var p=first(t);t.submitCurrentTedAdvance(p);var f=p.latestFrame().orElseThrow();var out=assertInstanceOf(NativeActionPort.AckReceived.class,t.queryCurrentTedOperation(p,p.deadline()));var s=CurrentTedActorTransitionResult.decodeOutcome(out);
            assertTrue(s.source().isEmpty());assertEquals(f.factsBefore(),s.factsBefore());assertEquals(f.claimSequence(),s.claimSequence());assertEquals(f.connectionGeneration(),s.connectionGeneration());assertTrue(s.accepted());assertTrue(s.effectAttempted());assertTrue(s.nativeReturned());
            var fields=NativeWire.parse(NativeWire.decodeExecuteRequest(out.outbound().orElseThrow().originalPacket()).normalizedAdditionalFields().value());assertEquals(p.deadline().toEpochMilli(),fields.get("core_control_deadline_unix_ms").longValue());assertEquals(p.operationId(),fields.get("ted_actor_transition").get("operation_id").textValue());assertEquals(1,r.advanceWrites);}
    }
    @Test void knownEarlySpentClaimRefusalIsNotReplayedAndCannotStartANewD1()throws Exception{
        var r=new Replay("refused");try(var t=transport(r)){var p=first(t);var ack=assertInstanceOf(NativeActionPort.AckReceived.class,t.submitCurrentTedAdvance(p));var f=CurrentTedActorTransitionResult.decodeOutcome(ack);assertFalse(f.ok());assertFalse(f.effectAttempted());assertTrue(f.claimSequence().signum()>0);assertSame(ack,t.submitCurrentTedAdvance(p));assertEquals(1,r.advanceWrites);var c=core(t);assertInstanceOf(NativeGameTransport.TedRoleUnavailable.class,t.readCurrentTedRole(c,c.validUntil()));assertEquals(1,r.advanceWrites);}
    }
    @Test void lostOrIndeterminateArmCannotBeUpgradedByALaterKnownStatusOrNewId()throws Exception{
        for(String mode:List.of("lost","indeterminate")){var r=new Replay(mode);try(var t=transport(r)){var p=first(t);var out=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentTedAdvance(p));assertTrue(p.originalUnknown());assertSame(out,t.submitCurrentTedAdvance(p));assertEquals(1,r.advanceWrites);
            if(!mode.equals("lost")){t.queryCurrentTedOperation(p,p.deadline());assertTrue(p.originalUnknown());var c=core(t);assertInstanceOf(NativeGameTransport.TedRoleUnavailable.class,t.readCurrentTedRole(c,p.deadline()));}assertEquals(0,r.epochWrites);}}
    }
    @Test void changedLeaseOperationOwnerOrImmutableBeforeSourceIsUnknownAfterOneWrite()throws Exception{
        for(String mode:List.of("wrong-lease","wrong-operation","wrong-owner","changed-source")){var r=new Replay(mode);try(var t=transport(r)){var p=first(t);var u=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentTedAdvance(p));assertTrue(t.originalIndeterminateCoreAcknowledgement(u.requestId()).isPresent());assertSame(u,t.submitCurrentTedAdvance(p));assertEquals(1,r.advanceWrites);}}
    }
    @Test void actualCapabilityAndOriginalCoreDeadlineAreRequiredBeforeTheFirstArm()throws Exception{
        var r=new Replay("missing-effects");try(var t=transport(r)){var q=role(t,null);assertThrows(IOException.class,()->t.prepareCurrentTedAdvance(q));assertEquals(0,r.advanceWrites);}
        var x=new Replay("known");try(var t=transport(x)){var c=core(t);assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,t.readCurrentTedRole(c,c.validUntil().plusMillis(1)).original());assertEquals(0,x.roleWrites);}
    }

    static final class Replay implements NativePacketPort {
        final String mode;final ArrayDeque<byte[]> packets=new ArrayDeque<>();boolean closed;int stage,advanceWrites,epochWrites,roleWrites,statusWrites;String firstOperation;long firstDeadline;
        Replay(String mode)throws IOException{
            this.mode=mode;if(mode.equals("starts-at-epoch1"))stage=3;var f=frame("song-query");var h=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",42).put("connection_generation",f.connectionGeneration()).put("bridge_version","ted-data").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256()).put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            var caps=h.putArray("capabilities").add(CoreFrame.CAPABILITY).add(CurrentTedActorTransition.Action.QUERY_ROLE.capability());if(!mode.equals("missing-effects"))caps.add(CurrentTedActorTransition.Action.ADVANCE_DAY.capability()).add(CurrentTedActorTransition.Action.CONFIRM_EPOCH.capability());packets.add(NativeWire.packet(StrictJson.canonical(h)));
        }
        public void verify()throws IOException{if(closed)throw new IOException("TED DATA port closed");}public void verifyCoreControlWindowPolicy()throws IOException{verify();}public void awaitConnection(Instant until)throws IOException{verify();}
        public byte[] readPacket(Instant until)throws IOException{verify();if(packets.isEmpty())throw new IOException("TED DATA response missing");return packets.removeFirst();}
        public void writePacket(byte[] packet,Instant until)throws IOException{
            verify();var req=NativeWire.decodeExecuteRequest(packet);ObjectNode result;boolean ok=true;
            if(req.step().equals(CoreFrame.STEP)){
                var f=stage>=5?frame("second-day-completed"):stage>=2?frame("recipient-pending-query"):frame("song-query");var prefix=f.factsBefore().orElseThrow();
                if(stage>=5)prefix=new CoreFrame.Prefix(f.progress().orElseThrow().targetDateRaw(),prefix.speed(),true,prefix.localPlayerId(),true,true,prefix.playedCharacterId(),true);
                if(mode.equals("wrong-after-core")&&stage>=2)prefix=new CoreFrame.Prefix(prefix.dateRaw(),prefix.speed(),true,prefix.localPlayerId(),true,true,prefix.playedCharacterId()==42?43:42,true);
                result=NativeWire.object(NativeWire.parse(CoreFramePublicCodec.encode(new CoreFrame.Partial(BUILD,prefix)).bytes()));
            }else{
                var fields=NativeWire.parse(req.normalizedAdditionalFields().value());var claim=fields.get("ted_actor_transition");var action=CurrentTedActorTransition.Action.parse(claim.get("action").textValue());String operation=claim.get("operation_id").textValue();long deadline=fields.get("core_control_deadline_unix_ms").longValue();retain(action,packet);
                switch(action){
                    case QUERY_ROLE->{roleWrites++;result=token(stage>=3?"recipient-epoch-query":stage>=2?"recipient-pending-query":mode.equals("missing")?"role-definition-missing":mode.equals("false-role")?"role-shown-false":"song-query");}
                    case ADVANCE_DAY->{advanceWrites++;boolean second=claim.get("actor_epoch").textValue().equals("1");if(!second){firstOperation=operation;firstDeadline=deadline;stage=1;}else stage=4;if(mode.equals("lost"))return;result=token(mode.equals("refused")?"advance-refused-spent-claim":mode.equals("indeterminate")?"advance-indeterminate":second?"second-advance-submitted":"advance-submitted");}
                    case QUERY_OPERATION->{statusWrites++;boolean second=claim.get("actor_epoch").textValue().equals("1");if(second){result=token("second-day-completed");stage=5;}else if(statusWrites==1){result=token("operation-running");}else{result=token("transition-pending");stage=2;}}
                    case CONFIRM_EPOCH->{epochWrites++;result=token("epoch-confirmed");stage=3;}
                    default->throw new IOException("Unknown TED DATA action");
                }
                // A newly generated Java DATA result for this software port, not altered files or a claim of original C++ exchange identity.
                result.put("request_id",req.requestId()).put("operation_id",operation).put("deadline_unix_ms",deadline);
                if(result.get("source").isObject()){
                    var pending=result.get("source").get("pending");if(pending.isObject())((ObjectNode)pending).put("operation_id",firstOperation).put("original_deadline_unix_ms",firstDeadline);
                }
                if(action==CurrentTedActorTransition.Action.ADVANCE_DAY){
                    if(mode.equals("wrong-lease"))result.put("query_sequence","1");if(mode.equals("wrong-operation"))result.put("operation_id","other-op");if(mode.equals("wrong-owner"))result.put("connection_generation",frame("song-query").connectionGeneration().subtract(BigInteger.ONE).toString());if(mode.equals("changed-source"))((ObjectNode)result.get("source")).put("predecessor_resolved",false).put("advance_admissible",false);
                }
                ok=result.get("ok").booleanValue();
            }
            var e=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",req.requestId()).put("ok",ok);e.set("result",result);packets.add(NativeWire.packet(StrictJson.canonical(e)));
        }
        static void retain(CurrentTedActorTransition.Action action,byte[] packet)throws IOException{String dir=System.getProperty("xar.current267.ted.java.requests");if(dir==null)return;var root=java.nio.file.Path.of(dir).toAbsolutePath().normalize();if(!root.getRoot().toString().equalsIgnoreCase("D:\\"))throw new IOException("D evidence root required");java.nio.file.Files.createDirectories(root);var path=root.resolve(action.wire()+".request.json");if(!java.nio.file.Files.exists(path))java.nio.file.Files.write(path,Arrays.copyOfRange(packet,4,packet.length),java.nio.file.StandardOpenOption.CREATE_NEW);}
        public void close(){closed=true;}
    }
}
