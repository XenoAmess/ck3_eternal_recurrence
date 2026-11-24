package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;

/** Generated typed Java DATA port only. No C++ resource is read, altered, re-IDed or called genuine. */
final class NativeCurrentRmtmRemainingGuardTransportTest {
    private static final BigInteger Z=BigInteger.ZERO,O=BigInteger.ONE,T=BigInteger.TWO;
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    private static final int START=-240,SONG=-2,SUCCESSOR=42;
    private static NativeGameTransport transport(DataPort p){return new NativeGameTransport(p,new NativePipeEndpoint.Config("\\\\.\\pipe\\rmtm-generated-DATA","rmtm-data",GAME,"rmtm-DATA-session","rmtm-DATA",BUILD.executableSha256(),BUILD.coreFrameAdapterId()),128,512);}
    private static NativeGameTransport.CoreReceived core(NativeGameTransport t)throws Exception{return assertInstanceOf(NativeGameTransport.CoreReceived.class,t.readCoreFrameReceived(Instant.now().plusSeconds(30)));}
    private static NativeGameTransport.RmtmRoleReceived role(NativeGameTransport t,Instant original)throws Exception{var c=core(t);return assertInstanceOf(NativeGameTransport.RmtmRoleReceived.class,t.readCurrentRmtmRole(c,original==null?c.validUntil():original));}
    private static NativeActionPort.AckReceived ack(NativeActionPort.DispatchOutcome o){return assertInstanceOf(NativeActionPort.AckReceived.class,o);}
    private static NativeGameTransport.RmtmAdvancePrepared day(NativeGameTransport t)throws Exception{
        var p=t.prepareCurrentRmtmAdvance(role(t,null));var submit=ack(t.submitCurrentRmtmAdvance(p));assertSame(submit,t.submitCurrentRmtmAdvance(p));ack(t.queryCurrentRmtmOperation(p,p.deadline()));return p;
    }
    private static void epoch(NativeGameTransport t,NativeGameTransport.RmtmAdvancePrepared p)throws Exception{
        var q=role(t,p.deadline());var e=t.prepareCurrentRmtmEpoch(p,q);var out=ack(t.submitCurrentRmtmEpoch(e));assertSame(out,t.submitCurrentRmtmEpoch(e));
        assertEquals(O,e.latestFrame().orElseThrow().actorEpoch());assertEquals(5,e.latestFrame().orElseThrow().completedNaturalDays());assertFalse(e.latestFrame().orElseThrow().effectAttempted());
    }
    private static NativeGameTransport.RmtmDecisionReceived decision(NativeGameTransport t)throws Exception{var c=core(t);return assertInstanceOf(NativeGameTransport.RmtmDecisionReceived.class,t.readCurrentRmtmDecision(c,c.validUntil()));}
    private static NativeGameTransport.RmtmEventReceived event(NativeGameTransport t,CurrentRmtmEvent.Action a)throws Exception{var c=core(t);return assertInstanceOf(NativeGameTransport.RmtmEventReceived.class,t.readCurrentRmtmEvent(c,a,c.validUntil()));}
    private static NativeGameTransport.RmtmObservationReceived budget(NativeGameTransport t)throws Exception{var c=core(t);return assertInstanceOf(NativeGameTransport.RmtmObservationReceived.class,t.readCurrentRmtmObservation(c,CurrentRmtmObservation.Action.QUERY_BUDGET,Optional.empty(),Optional.empty(),c.validUntil()));}
    private static void decisionAction(NativeGameTransport t,NativeGameTransport.RmtmDecisionPurpose p,CurrentRmtmDecision.Action a)throws Exception{
        var prepared=t.prepareCurrentRmtmDecision(decision(t),a,p);var out=ack(t.submitCurrentRmtmDecision(prepared));assertSame(out,t.submitCurrentRmtmDecision(prepared));
    }
    private static void select(NativeGameTransport t,DataPort port,NativeGameTransport.RmtmDecisionPurpose purpose,CurrentRmtmDecision.DecisionKey key,boolean confirm)throws Exception{
        if(!port.listVisible)decisionAction(t,purpose,CurrentRmtmDecision.Action.OPEN_LIST);
        if(port.selected!=key)decisionAction(t,purpose,CurrentRmtmDecision.Action.OPEN_DETAIL);
        if(confirm)decisionAction(t,purpose,CurrentRmtmDecision.Action.CONFIRM);
    }

    @Test void zeroDayActualRoleCaptureAllowsThresholdButCallerCaseBoundAloneDoesNot()throws Exception{
        var a=new DataPort("known");try(var t=transport(a)){role(t,null);var q=decision(t);assertTrue(q.frame().source().orElseThrow().caseBound());
            var p=t.prepareCurrentRmtmDecision(q,CurrentRmtmDecision.Action.OPEN_LIST,NativeGameTransport.RmtmDecisionPurpose.PREPARE_FIFTY);ack(t.submitCurrentRmtmDecision(p));assertEquals(0,a.advances);assertEquals(1,a.decisionEffects);}
        var b=new DataPort("uncaptured");try(var t=transport(b)){var r=role(t,null);assertFalse(r.frame().source().orElseThrow().caseStartCaptured());var q=decision(t);assertTrue(q.frame().source().orElseThrow().caseBound());
            assertThrows(IOException.class,()->t.prepareCurrentRmtmDecision(q,CurrentRmtmDecision.Action.OPEN_LIST,NativeGameTransport.RmtmDecisionPurpose.PREPARE_FIFTY));assertEquals(0,b.effectWrites());}
    }
    @Test void d1Through4StaySongD5UsesFreshEpochOneAndFourteenDayCapIsIndependent()throws Exception{
        var p=new DataPort("known");try(var t=transport(p)){
            for(int n=1;n<=14;n++){var d=day(t);var f=d.latestFrame().orElseThrow();assertEquals(n,f.completedNaturalDays());assertEquals(START+24*n,d.targetDateRaw());
                if(n==5){assertEquals(CurrentRmtmActorTransitionResult.Status.TRANSITION_PENDING,f.status());epoch(t,d);}else assertEquals(CurrentRmtmActorTransitionResult.Status.COMPLETED_DAY,f.status());
                assertEquals(n<=5?Z:O,f.actorEpoch());if(n<=4)assertEquals(SONG,f.progress().orElseThrow().afterActorId());}
            assertThrows(IOException.class,()->t.prepareCurrentRmtmAdvance(role(t,null)));assertEquals(14,p.advances);assertEquals(1,p.epochs);
        }
    }
    @Test void pendingCannotBeSkippedAndForeignReceiverCannotImportItsEpoch()throws Exception{
        var a=new DataPort("known");var b=new DataPort("known");try(var t=transport(a);var foreign=transport(b)){
            for(int n=1;n<5;n++)day(t);var d=day(t);var after=role(t,d.deadline());assertTrue(after.frame().source().orElseThrow().executeTimeIdentityConfirmed().isEmpty());
            assertThrows(IOException.class,()->t.prepareCurrentRmtmAdvance(after));assertThrows(IOException.class,()->foreign.prepareCurrentRmtmEpoch(d,after));
            var e=t.prepareCurrentRmtmEpoch(d,after);ack(t.submitCurrentRmtmEpoch(e));assertEquals(1,a.epochs);assertEquals(0,b.effectWrites());
        }
    }
    @Test void foreignQueriesOldCoreAndExtendedDeadlineNeverCreateAnEffect()throws Exception{
        var a=new DataPort("known");var b=new DataPort("known");try(var t=transport(a);var foreign=transport(b)){
            var c=core(t);var q=assertInstanceOf(NativeGameTransport.RmtmRoleReceived.class,t.readCurrentRmtmRole(c,c.validUntil()));
            assertThrows(IOException.class,()->q.requireOriginal(t,q.validUntil().plusMillis(1)));assertThrows(IOException.class,()->foreign.prepareCurrentRmtmAdvance(q));
            assertInstanceOf(NativeGameTransport.RmtmRoleUnavailable.class,t.readCurrentRmtmRole(c,c.validUntil()));assertEquals(1,a.roleQueries);
            var newer=role(t,null);assertThrows(IOException.class,()->q.requireOriginal(t,q.validUntil()));var d=t.prepareCurrentRmtmAdvance(newer);
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,foreign.submitCurrentRmtmAdvance(d));assertEquals(0,b.effectWrites());
        }
    }
    @Test void originalOperationStatusKeepsArmSourceNullAndLostArmIsStickyIdempotentUnknown()throws Exception{
        var a=new DataPort("known");try(var t=transport(a)){var p=t.prepareCurrentRmtmAdvance(role(t,null));ack(t.submitCurrentRmtmAdvance(p));var original=p.latestFrame().orElseThrow();
            var actual=ack(t.queryCurrentRmtmOperation(p,p.deadline()));var after=CurrentRmtmActorTransitionResult.decodeOutcome(actual);assertTrue(after.source().isEmpty());assertEquals(original.factsBefore(),after.factsBefore());assertEquals(original.claimSequence(),after.claimSequence());
            assertEquals(original.ticketSequence(),after.ticketSequence());assertEquals(original.pumpEpoch(),after.pumpEpoch());var fields=NativeWire.parse(NativeWire.decodeExecuteRequest(actual.outbound().orElseThrow().originalPacket()).normalizedAdditionalFields().value());
            assertEquals(p.deadline().toEpochMilli(),fields.get("core_control_deadline_unix_ms").longValue());assertEquals(1,a.advances);}
        var lost=new DataPort("lost-arm");try(var t=transport(lost)){var p=t.prepareCurrentRmtmAdvance(role(t,null));var out=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentRmtmAdvance(p));assertSame(out,t.submitCurrentRmtmAdvance(p));assertTrue(p.originalUnknown());assertEquals(1,lost.advances);}
    }
    @Test void eachFixedEventChannelIsOncePerCaseAndIndependentAbsenceIsOnlyData()throws Exception{
        var port=new DataPort("known");try(var t=transport(port)){role(t,null);
            for(var action:List.of(CurrentRmtmEvent.Action.QUERY_CHAOS,CurrentRmtmEvent.Action.QUERY_SUMMARY)){
                var q=event(t,action);var p=t.prepareCurrentRmtmEventAck(q);var out=ack(t.submitCurrentRmtmEvent(p));assertSame(out,t.submitCurrentRmtmEvent(p));assertFalse(p.latestFrame().orElseThrow().eventClosed());
                assertTrue(t.currentRmtmEventAbsent(p,event(t,action)));port.eventPresent=true;port.instance++;
                assertThrows(IOException.class,()->t.prepareCurrentRmtmEventAck(event(t,action)));port.eventPresent=true;
            }assertEquals(2,port.eventEffects);
        }
    }
    @Test void budgetFalseToggleAndCancelRequireFreshTypedHiddenReadbackWithoutEnact()throws Exception{
        var port=new DataPort("known");try(var t=transport(port)){role(t,null);var q=budget(t);var open=t.prepareCurrentRmtmObservation(q,CurrentRmtmObservation.Action.OPEN_BUDGET);
            ack(t.submitCurrentRmtmObservation(open));assertFalse(open.latestFrame().orElseThrow().nativeHandled());var visible=budget(t);assertTrue(visible.frame().source().orElseThrow().budget().orElseThrow().visible());
            var cancel=t.prepareCurrentRmtmObservation(visible,CurrentRmtmObservation.Action.CANCEL_BUDGET);var out=ack(t.submitCurrentRmtmObservation(cancel));assertSame(out,t.submitCurrentRmtmObservation(cancel));assertTrue(t.currentRmtmObservationHidden(cancel,budget(t)));assertEquals(2,port.budgetEffects);
        }
    }
    @Test void fiftyFalseCanMustBeRetainedBeforeFiftyOneAndProductionConfirmationCannotReplay()throws Exception{
        var port=new DataPort("known");try(var t=transport(port)){role(t,null);
            assertThrows(IOException.class,()->t.prepareCurrentRmtmDecision(decision(t),CurrentRmtmDecision.Action.OPEN_LIST,NativeGameTransport.RmtmDecisionPurpose.PREPARE_FIFTYONE));
            select(t,port,NativeGameTransport.RmtmDecisionPurpose.PREPARE_FIFTY,CurrentRmtmDecision.DecisionKey.PREPARE_FIFTY,true);
            select(t,port,NativeGameTransport.RmtmDecisionPurpose.INSPECT_FIFTY,CurrentRmtmDecision.DecisionKey.RESTORE,false);var fifty=decision(t);assertFalse(fifty.frame().source().orElseThrow().nativeCanConfirm().orElseThrow());
            assertThrows(IOException.class,()->t.prepareCurrentRmtmDecision(fifty,CurrentRmtmDecision.Action.CONFIRM,NativeGameTransport.RmtmDecisionPurpose.INSPECT_FIFTY));t.retainCurrentRmtmFifty(fifty);
            select(t,port,NativeGameTransport.RmtmDecisionPurpose.PREPARE_FIFTYONE,CurrentRmtmDecision.DecisionKey.PREPARE_FIFTYONE,true);
            select(t,port,NativeGameTransport.RmtmDecisionPurpose.RESTORE_FIFTYONE,CurrentRmtmDecision.DecisionKey.RESTORE,true);
            assertThrows(IOException.class,()->t.prepareCurrentRmtmDecision(decision(t),CurrentRmtmDecision.Action.CONFIRM,NativeGameTransport.RmtmDecisionPurpose.RESTORE_FIFTYONE));assertEquals(1,port.restoreConfirms);assertEquals(0,port.advances);
        }
    }
    @Test void changedWholeDecisionBeforeSourceBecomesStickyUnknownWithoutAnotherWrite()throws Exception{
        var port=new DataPort("changed-decision-source");try(var t=transport(port)){role(t,null);var q=decision(t);var p=t.prepareCurrentRmtmDecision(q,CurrentRmtmDecision.Action.OPEN_LIST,NativeGameTransport.RmtmDecisionPurpose.PREPARE_FIFTY);
            var out=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentRmtmDecision(p));assertSame(out,t.submitCurrentRmtmDecision(p));assertTrue(t.originalIndeterminateCoreAcknowledgement(out.requestId()).isPresent());
            var c=core(t);assertInstanceOf(NativeGameTransport.RmtmDecisionUnavailable.class,t.readCurrentRmtmDecision(c,c.validUntil()));assertEquals(1,port.decisionEffects);
        }
    }

    // New tests opt into ordinary-event DATA only. Original nine tests never enable this flag.
    private static void reachPostSuccessionData(NativeGameTransport t,DataPort port)throws Exception {
        for(int n=1;n<=5;n++){
            var prepared=day(t);
            if(n==1)for(var channel:List.of(CurrentRmtmEvent.Action.QUERY_CHAOS,CurrentRmtmEvent.Action.QUERY_SUMMARY)){
                var q=event(t,channel);var fixed=t.prepareCurrentRmtmEventAck(q);ack(t.submitCurrentRmtmEvent(fixed));
                assertTrue(t.currentRmtmEventAbsent(fixed,event(t,channel)));port.eventPresent=true;port.instance++;
            }
            if(n==5)epoch(t,prepared);
        }
        port.postEvents=true;port.eventPresent=true;port.instance=71;
    }
    @Test void postEventPublicCaseBoundAndPendingCannotCreatePrivateSuccessorEpoch()throws Exception {
        var port=new DataPort("post-epoch-negative");port.postEvents=true;
        try(var t=transport(port)){
            role(t,null);var zero=event(t,CurrentRmtmEvent.Action.QUERY_SUMMARY);
            assertTrue(zero.frame().source().orElseThrow().caseBound());
            assertThrows(IOException.class,()->t.prepareCurrentRmtmPostSuccessionEvent(zero,port.instance));
            for(int n=1;n<=4;n++)day(t);
            var before=event(t,CurrentRmtmEvent.Action.QUERY_SUMMARY);
            assertThrows(IOException.class,()->t.prepareCurrentRmtmPostSuccessionEvent(before,port.instance));
            var fifth=day(t);assertEquals(CurrentRmtmActorTransitionResult.Status.TRANSITION_PENDING,fifth.latestFrame().orElseThrow().status());
            assertEquals(0,port.epochs);var c=core(t);
            var pending=t.readCurrentRmtmEvent(c,CurrentRmtmEvent.Action.QUERY_SUMMARY,c.validUntil());
            if(pending instanceof NativeGameTransport.RmtmEventReceived q){
                assertTrue(q.frame().source().orElseThrow().caseBound());
                assertThrows(IOException.class,()->t.prepareCurrentRmtmPostSuccessionEvent(q,port.instance));
            }else assertInstanceOf(NativeGameTransport.RmtmEventUnavailable.class,pending);
            assertEquals(0,port.postEventEffects);
        }
    }
    @Test void postEventConfirmedPrivateEpochAllowsDifferentInstancesButRetainsOnceAndIndependentAbsence()throws Exception {
        var port=new DataPort("post-known");try(var t=transport(port)){
            reachPostSuccessionData(t,port);assertEquals(1,port.epochs);assertEquals(2,port.eventEffects);
            for(int instance:List.of(71,72)){
                port.eventPresent=true;port.instance=instance;var q=event(t,CurrentRmtmEvent.Action.QUERY_SUMMARY);
                assertFalse(q.frame().source().orElseThrow().ackAdmissible());assertTrue(q.frame().source().orElseThrow().fixedInstanceId().isEmpty());
                assertEquals(2,CurrentRmtmEvent.postSuccessionChoice(q.frame().source().orElseThrow(),SUCCESSOR,instance).orElseThrow().authoredOptionIndex());
                var prepared=t.prepareCurrentRmtmPostSuccessionEvent(q,instance);var out=ack(t.submitCurrentRmtmEvent(prepared));
                assertSame(out,t.submitCurrentRmtmEvent(prepared));assertEquals(2,port.postSelectedAuthored);
                assertFalse(prepared.latestFrame().orElseThrow().eventClosed());assertFalse(prepared.latestFrame().orElseThrow().newDateObserved());
                assertTrue(t.currentRmtmEventAbsent(prepared,event(t,CurrentRmtmEvent.Action.QUERY_SUMMARY)));
                port.eventPresent=true;var same=event(t,CurrentRmtmEvent.Action.QUERY_SUMMARY);
                assertThrows(IOException.class,()->t.prepareCurrentRmtmPostSuccessionEvent(same,instance));
            }
            assertEquals(2,port.postEventEffects);assertEquals(4,port.eventEffects); // Old two ACKs stay spent; new action is not channel-once.
        }
    }
    @Test void postEventForeignReceivedOldQueryAndExpiredDeadlineHaveNoEffectWrite()throws Exception {
        var port=new DataPort("post-known");var other=new DataPort("post-foreign");
        try(var t=transport(port);var foreign=transport(other)){
            reachPostSuccessionData(t,port);var old=event(t,CurrentRmtmEvent.Action.QUERY_SUMMARY);
            assertThrows(IOException.class,()->foreign.prepareCurrentRmtmPostSuccessionEvent(old,71));
            var fresh=event(t,CurrentRmtmEvent.Action.QUERY_SUMMARY);
            assertThrows(IOException.class,()->t.prepareCurrentRmtmPostSuccessionEvent(old,71));
            var c=core(t);int writes=port.packetWrites;
            assertInstanceOf(NativeGameTransport.RmtmEventUnavailable.class,t.readCurrentRmtmEvent(c,CurrentRmtmEvent.Action.QUERY_SUMMARY,Instant.EPOCH));
            assertEquals(writes,port.packetWrites);assertEquals(0,port.postEventEffects);assertEquals(0,other.effectWrites());
            var actual=event(t,CurrentRmtmEvent.Action.QUERY_SUMMARY);var prepared=t.prepareCurrentRmtmPostSuccessionEvent(actual,71);
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,foreign.submitCurrentRmtmEvent(prepared));
            assertEquals(0,port.postEventEffects);assertEquals(0,other.effectWrites());assertNotNull(fresh);
        }
    }
    @Test void postEventLostOriginalResultIsStickyUnknownAndNeverWritesAgain()throws Exception {
        var port=new DataPort("lost-post-event");try(var t=transport(port)){
            reachPostSuccessionData(t,port);var q=event(t,CurrentRmtmEvent.Action.QUERY_SUMMARY);var prepared=t.prepareCurrentRmtmPostSuccessionEvent(q,71);
            var out=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentRmtmEvent(prepared));
            assertSame(out,t.submitCurrentRmtmEvent(prepared));assertEquals(1,port.postEventEffects);
            var c=core(t);port.eventPresent=true;port.instance=72;int writes=port.packetWrites;
            var after=assertInstanceOf(NativeGameTransport.RmtmEventUnavailable.class,t.readCurrentRmtmEvent(c,CurrentRmtmEvent.Action.QUERY_SUMMARY,c.validUntil()));
            assertSame(out,after.original());assertEquals(writes,port.packetWrites);assertEquals(1,port.postEventEffects);
        }
    }
    @Test void postEventLegalWholeSourceDriftBecomesUnknownWithoutClearingTheRetainedFailure()throws Exception {
        var port=new DataPort("changed-post-source");try(var t=transport(port)){
            reachPostSuccessionData(t,port);var q=event(t,CurrentRmtmEvent.Action.QUERY_SUMMARY);var prepared=t.prepareCurrentRmtmPostSuccessionEvent(q,71);
            var out=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentRmtmEvent(prepared));
            assertSame(out,t.submitCurrentRmtmEvent(prepared));assertEquals(1,port.postEventEffects);
            assertTrue(t.originalIndeterminateCoreAcknowledgement(out.requestId()).isPresent());
            var c=core(t);port.eventPresent=true;port.instance=72;int writes=port.packetWrites;
            assertInstanceOf(NativeGameTransport.RmtmEventUnavailable.class,t.readCurrentRmtmEvent(c,CurrentRmtmEvent.Action.QUERY_SUMMARY,c.validUntil()));
            assertEquals(writes,port.packetWrites);assertTrue(t.originalIndeterminateCoreAcknowledgement(out.requestId()).isPresent());
            assertEquals(1,port.postEventEffects);
        }
    }

    private static final class DataPort implements NativePacketPort {
        final String mode;final ArrayDeque<byte[]> packets=new ArrayDeque<>();boolean closed,pending,confirmed,opCompleted,listVisible,detailVisible,budgetVisible,eventPresent=true;
        int days,advances,epochs,roleQueries,decisionEffects,eventEffects,budgetEffects,percent,restoreConfirms,instance=10,querySequence;
        CurrentRmtmDecision.DecisionKey selected;CurrentRmtmActorTransitionSource roleBefore,opSource;CoreFrame.Prefix opCore;String operation;long opDeadline;BigInteger opProvider,opQuery;int opDay;
        CurrentRmtmDecisionSource decisionBefore;CurrentRmtmEventSource eventBefore;CurrentRmtmObservationSource observationBefore;
        boolean postEvents;int postEventEffects,postSelectedAuthored=-1,packetWrites;
        DataPort(String mode)throws IOException{this.mode=mode;var h=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",42).put("connection_generation",T)
                .put("bridge_version","rmtm-DATA").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256()).put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            var names=new java.util.LinkedHashSet<String>();names.add(CoreFrame.CAPABILITY);for(var a:CurrentRmtmActorTransition.Action.values())names.add(a.capability());for(var a:CurrentRmtmDecision.Action.values())names.add(a.capability());for(var a:CurrentRmtmEvent.Action.values())names.add(a.capability());for(var a:CurrentRmtmObservation.Action.values())names.add(a.capability());var caps=h.putArray("capabilities");names.forEach(caps::add);packets.add(NativeWire.packet(StrictJson.canonical(h)));}
        int actor(){return days>=5?SUCCESSOR:SONG;}int effectWrites(){return advances+epochs+decisionEffects+eventEffects+budgetEffects;}
        CoreFrame.Prefix current(){return new CoreFrame.Prefix(START+24*days,3,true,1,true,true,actor(),true);}
        BigInteger seq(){return BigInteger.valueOf(++querySequence);}BigInteger number(JsonNode n){return new BigInteger(n.asText());}
        CoreFrame.Prefix prefix(JsonNode n){return new CoreFrame.Prefix(n.get("date_raw").intValue(),n.get("speed").intValue(),n.get("paused").booleanValue(),n.get("local_player_id").intValue(),n.get("map_ready").booleanValue(),n.get("has_played_character").booleanValue(),n.get("played_character_id").intValue(),n.get("played_character_alive").booleanValue());}
        CurrentLetterResult.OwnerWitness owner(){return new CurrentLetterResult.OwnerWitness(T,BigInteger.valueOf(20),BigInteger.valueOf(30),7);}
        public void verify()throws IOException{if(closed)throw new IOException("Generated RMTM DATA port closed");}public void verifyCoreControlWindowPolicy()throws IOException{verify();}public void awaitConnection(Instant until)throws IOException{verify();}
        public byte[] readPacket(Instant until)throws IOException{verify();if(packets.isEmpty())throw new IOException("Generated DATA port deliberately has no response");return packets.removeFirst();}
        CurrentRmtmActorTransitionSource roleSource(){
            Optional<CurrentRmtmActorTransitionSource.Pending> p=Optional.empty();if(pending)p=Optional.of(new CurrentRmtmActorTransitionSource.Pending(operation,BigInteger.valueOf(advances),BigInteger.valueOf(advances),BigInteger.valueOf(opDeadline),SONG,SUCCESSOR,START+96,START+120,1,true,true,true));
            boolean captured=!mode.equals("uncaptured");return new CurrentRmtmActorTransitionSource(days>=5?CurrentRmtmActorTransitionSource.Role.SUCCESSOR:CurrentRmtmActorTransitionSource.Role.SONG,true,Optional.of(true),confirmed?O:Z,Optional.of(SONG),days>=5?Optional.of(SUCCESSOR):Optional.empty(),p,days,14,START,captured,Optional.empty(),true,true,captured&&!pending&&days<14,captured&&pending);
        }
        CurrentRmtmDecisionSource decisionSource(){boolean can=selected!=CurrentRmtmDecision.DecisionKey.RESTORE||percent!=50;var rows=new ArrayList<CurrentRmtmDecisionSource.Row>();
            for(var key:CurrentRmtmDecision.DecisionKey.values())rows.add(new CurrentRmtmDecisionSource.Row(key,listVisible&&selected!=key,detailVisible&&selected==key));
            return new CurrentRmtmDecisionSource(true,listVisible,true,detailVisible,detailVisible,detailVisible,false,!listVisible,true,false,detailVisible&&can,true,detailVisible,
                    detailVisible?Optional.of(can?"":"actual original50 why"):Optional.empty(),Optional.of(1),Optional.of(5),detailVisible?Optional.of(1):Optional.empty(),detailVisible?Optional.of(selected):Optional.empty(),detailVisible?Optional.of(can):Optional.empty(),rows);
        }
        // Explicit Java DATA fixture, never a C++/Native reply or actual popup claim.
        CurrentRmtmEventSource postEventSource(){
            List<CurrentLydSource.EventRow> rows=List.of();
            if(eventPresent){
                var options=List.of(new CurrentLydSource.EventOption(3,true,"first vector DATA option","",Optional.<String>empty(),Optional.<CurrentLyd.EventRole>empty()),
                        new CurrentLydSource.EventOption(0,false,"actual disabled DATA option","actual disabled reason",Optional.<String>empty(),Optional.<CurrentLyd.EventRole>empty()),
                        new CurrentLydSource.EventOption(2,true,"minimum authored available DATA option","",Optional.<String>empty(),Optional.<CurrentLyd.EventRole>empty()));
                rows=List.of(new CurrentLydSource.EventRow(instance,actor(),4,"java_data.post_succession_event","Java DATA ordinary opening","Java DATA ordinary description",true,true,true,options));
            }
            return new CurrentRmtmEventSource(new CurrentLydSource.Events(true,rows.size(),rows),Optional.empty(),true,false,true);
        }
        CurrentRmtmEventSource changedPostEventSource(CurrentRmtmEventSource original){
            var row=original.eventCensus().events().get(0);
            var changed=new CurrentLydSource.EventRow(row.instanceId(),row.recipientCharacterId(),row.authoredOptionCount(),row.definitionKey(),row.opening(),
                    row.description()+" valid changed wholeSource DATA",row.namedRootBound(),row.windowVisible(),row.windowEnabled(),row.options());
            return new CurrentRmtmEventSource(new CurrentLydSource.Events(true,1,List.of(changed)),Optional.empty(),true,false,true);
        }

        CurrentRmtmEventSource eventSource(CurrentRmtmEvent.Action action){if(postEvents)return postEventSource();List<CurrentLydSource.EventRow> rows=List.of();if(eventPresent){var option=new CurrentLydSource.EventOption(0,true,"actual generated DATA option","",Optional.empty(),Optional.empty());rows=List.of(new CurrentLydSource.EventRow(instance,actor(),1,action.definition(),"actual generated DATA opening","description",true,true,true,List.of(option)));}
            return new CurrentRmtmEventSource(new CurrentLydSource.Events(true,rows.size(),rows),eventPresent?Optional.of(instance):Optional.empty(),true,eventPresent,true);
        }
        CurrentRmtmObservationSource budgetSource(){var b=new CurrentRmtmObservationSource.Budget(budgetVisible,budgetVisible,budgetVisible,false,budgetVisible?Optional.of(actor()):Optional.empty(),budgetVisible?Optional.of(100L):Optional.empty(),budgetVisible?Optional.of(Integer.toUnsignedLong(actor())):Optional.empty(),!budgetVisible,budgetVisible,"my_realm_player",true);
            return new CurrentRmtmObservationSource(CurrentRmtmObservation.Kind.BUDGET,true,true,Optional.empty(),Optional.empty(),Optional.of(b),Optional.empty());}
        CurrentRmtmActorTransitionResult transition(CurrentRmtmActorTransition.Action a,String id,JsonNode c,long deadline){
            var expected=prefix(c.get("expected_core"));var provider=number(c.get("provider_generation"));var query=number(c.get("query_sequence"));var status=CurrentRmtmActorTransitionResult.Status.AVAILABLE;var epoch=confirmed?O:Z;int count=days;String op=c.get("operation_id").asText();boolean accepted=false,effect=false,returned=false;BigInteger claim=Z;Optional<CurrentRmtmActorTransitionSource> source=Optional.empty();Optional<CurrentRmtmActorTransitionResult.Progress> progress=Optional.empty();
            if(a==CurrentRmtmActorTransition.Action.QUERY_ROLE){roleQueries++;roleBefore=roleSource();source=Optional.of(roleBefore);provider=O;query=seq();}
            else if(a==CurrentRmtmActorTransition.Action.CONFIRM_EPOCH){epochs++;accepted=true;claim=BigInteger.valueOf(100+epochs);source=Optional.of(roleBefore);status=CurrentRmtmActorTransitionResult.Status.EPOCH_CONFIRMED;epoch=O;pending=false;confirmed=true;}
            else{
                if(a==CurrentRmtmActorTransition.Action.ADVANCE_DAY){advances++;operation=op;opDeadline=deadline;opCore=expected;opSource=roleBefore;opDay=days;opProvider=provider;opQuery=query;opCompleted=false;source=Optional.of(opSource);status=CurrentRmtmActorTransitionResult.Status.SUBMITTED;}
                else {if(!opCompleted){days=opDay+1;pending=days==5;opCompleted=true;}status=pending?CurrentRmtmActorTransitionResult.Status.TRANSITION_PENDING:CurrentRmtmActorTransitionResult.Status.COMPLETED_DAY;expected=opCore;provider=opProvider;query=opQuery;op=operation;deadline=opDeadline;}
                boolean exact=a==CurrentRmtmActorTransition.Action.QUERY_OPERATION;int after=exact?(days==5?SUCCESSOR:opCore.playedCharacterId()):-1;
                progress=Optional.of(new CurrentRmtmActorTransitionResult.Progress(BigInteger.valueOf(advances),opCore.dateRaw(),opCore.dateRaw()+24,exact?opCore.dateRaw()+24:opCore.dateRaw(),opCore.playedCharacterId(),after,exact?1:0,0,exact?0:-1,true,true,true,exact,exact&&pending,exact,!exact,false));
                accepted=effect=returned=true;claim=BigInteger.valueOf(advances);count=exact?opDay+1:opDay;epoch=opSource.actorEpoch();
            }
            return new CurrentRmtmActorTransitionResult(a,id,op,status,true,accepted,provider,query,claim,epoch,count,BigInteger.valueOf(deadline),T,BigInteger.valueOf(20),BigInteger.valueOf(30),7,Optional.of(expected),source,progress,effect,returned,true,Optional.empty());
        }
        public void writePacket(byte[] bytes,Instant until)throws IOException{
            verify();packetWrites++;var request=NativeWire.decodeExecuteRequest(bytes);ObjectNode result;
            if(request.step().equals(CoreFrame.STEP))result=NativeWire.object(NativeWire.parse(CoreFramePublicCodec.encode(new CoreFrame.Partial(BUILD,current())).bytes()));
            else{
                var f=NativeWire.parse(request.normalizedAdditionalFields().value());long deadline=f.get("core_control_deadline_unix_ms").longValue();
                if(f.has("rmtm_actor_transition")){var c=f.get("rmtm_actor_transition");var a=CurrentRmtmActorTransition.Action.parse(c.get("action").asText());var frame=transition(a,request.requestId(),c,deadline);if(mode.equals("lost-arm")&&a==CurrentRmtmActorTransition.Action.ADVANCE_DAY)return;result=NativeWire.object(NativeWire.parse(frame.encode().bytes()));}
                else if(f.has("rmtm_decision")){
                    var c=f.get("rmtm_decision");var a=CurrentRmtmDecision.Action.parse(c.get("action").asText());boolean query=a==CurrentRmtmDecision.Action.QUERY;var s=query?decisionSource():decisionBefore;
                    var provider=query?O:number(c.get("provider_generation"));var sequence=query?seq():number(c.get("query_sequence"));Optional<CurrentRmtmDecision.DecisionKey> key=c.get("decision_key").isNull()?Optional.empty():Optional.of(CurrentRmtmDecision.DecisionKey.parse(c.get("decision_key").asText()));
                    var status=CurrentRmtmDecisionResult.Status.AVAILABLE;
                    if(query)decisionBefore=s;else {decisionEffects++;if(a==CurrentRmtmDecision.Action.OPEN_LIST){listVisible=true;status=CurrentRmtmDecisionResult.Status.NAVIGATION_DISPATCHED;}
                        else if(a==CurrentRmtmDecision.Action.OPEN_DETAIL){selected=key.orElseThrow();detailVisible=true;status=CurrentRmtmDecisionResult.Status.SELECTION_DISPATCHED;}
                        else {status=CurrentRmtmDecisionResult.Status.CONFIRMATION_DISPATCHED;if(key.orElseThrow()==CurrentRmtmDecision.DecisionKey.PREPARE_FIFTY)percent=50;else if(key.orElseThrow()==CurrentRmtmDecision.DecisionKey.PREPARE_FIFTYONE)percent=51;else if(key.orElseThrow()==CurrentRmtmDecision.DecisionKey.RESTORE)restoreConfirms++;}
                        if(mode.equals("changed-decision-source"))s=new CurrentRmtmDecisionSource(s.listFound(),s.listVisible(),s.listEnabled(),s.detailFound(),s.detailVisible(),s.detailEnabled(),s.otherDecisionSelected(),s.openListAdmissible(),s.completeModelCensus(),s.blockedByVisibleModal(),s.confirmAdmissible(),s.caseBound(),s.confirmTooltipObserved(),s.confirmTooltip(),Optional.of(s.groupsCount().orElseThrow()+1),s.totalModelRows(),s.widgetState(),s.selectedDecisionKey(),s.nativeCanConfirm(),s.rows());}
                    var frame=new CurrentRmtmDecisionResult(a,status,!query,!query,false,true,provider,sequence,query?Z:BigInteger.valueOf(decisionEffects),Optional.of(prefix(c.get("expected_core"))),Optional.of(owner()),Optional.of(s),Optional.empty(),key);result=NativeWire.object(NativeWire.parse(frame.encode().bytes()));
                }else if(f.has("rmtm_event")){
                    var c=f.get("rmtm_event");var a=CurrentRmtmEvent.Action.parse(c.get("action").asText());boolean query=a.queryOnly();var s=query?eventSource(a):eventBefore;var fixed=query?Optional.<Integer>empty():Optional.of(c.get("instance_id").intValue());
                    if(query)eventBefore=s;else {eventEffects++;eventPresent=false;
                        if(postEvents&&a==CurrentRmtmEvent.Action.CHOOSE_POST_SUCCESSION_FIRST_AVAILABLE){
                            postEventEffects++;postSelectedAuthored=CurrentRmtmEvent.postSuccessionChoice(s,prefix(c.get("expected_core")).playedCharacterId(),fixed.orElseThrow()).orElseThrow(()->new IOException("New DATA port received no admitted actual choice")).authoredOptionIndex();
                            if(mode.equals("lost-post-event"))return;
                            if(mode.equals("changed-post-source"))s=changedPostEventSource(s);
                        }
                    }
                    var frame=new CurrentRmtmEventResult(a,query?CurrentRmtmEventResult.Status.AVAILABLE:CurrentRmtmEventResult.Status.SELECTION_DISPATCHED,!query,!query,true,query?O:number(c.get("provider_generation")),query?seq():number(c.get("query_sequence")),query?Z:BigInteger.valueOf(eventEffects),Optional.of(prefix(c.get("expected_core"))),Optional.of(owner()),Optional.of(s),Optional.empty(),fixed);result=NativeWire.object(NativeWire.parse(frame.encode().bytes()));
                }else if(f.has("rmtm_observation")){
                    var c=f.get("rmtm_observation");var a=CurrentRmtmObservation.Action.parse(c.get("action").asText());if(a.kind()!=CurrentRmtmObservation.Kind.BUDGET)throw new IOException("This finite generated DATA port has no nonbudget observation");
                    boolean query=a.queryOnly();var s=query?budgetSource():observationBefore;if(query)observationBefore=s;else {budgetEffects++;budgetVisible=a==CurrentRmtmObservation.Action.OPEN_BUDGET;}
                    var frame=new CurrentRmtmObservationResult(a,query?CurrentRmtmObservationResult.Status.AVAILABLE:CurrentRmtmObservationResult.Status.NAVIGATION_DISPATCHED,!query,!query,false,true,query?O:number(c.get("provider_generation")),query?seq():number(c.get("query_sequence")),query?Z:BigInteger.valueOf(budgetEffects),Optional.of(prefix(c.get("expected_core"))),Optional.of(owner()),Optional.of(s),Optional.empty());result=NativeWire.object(NativeWire.parse(frame.encode().bytes()));
                }else throw new IOException("No arbitrary step or other product exists in generated RMTM DATA port");
            }
            var envelope=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",request.requestId()).put("ok",true);envelope.set("result",result);packets.add(NativeWire.packet(StrictJson.canonical(envelope)));
        }
        public void close(){closed=true;}
    }
}
