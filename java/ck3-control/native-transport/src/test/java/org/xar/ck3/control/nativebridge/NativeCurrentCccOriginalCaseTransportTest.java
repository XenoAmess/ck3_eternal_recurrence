package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;

/** Explicit generated Java DATA port, separate from the three original-byte C++ producer qualifications. */
class NativeCurrentCccOriginalCaseTransportTest {
    static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    static final int START=53144328;
    static ObjectNode token(String family,String name)throws IOException{
        String prefix=switch(family){case "transition"->"current267-ccc-transition-cpp-a1126";case "event"->"current267-ccc-event-cpp-a1126";default->"current267-ccc-decision-cpp-a1126";};
        try(var in=NativeCurrentCccOriginalCaseTransportTest.class.getResourceAsStream("/"+prefix+"/"+name+".json")){
            if(in==null)throw new IOException("Original CCC DATA template absent");return NativeWire.object(NativeWire.parse(in.readAllBytes()).get("result"));
        }
    }
    static NativeGameTransport transport(Replay r){return new NativeGameTransport(r,new NativePipeEndpoint.Config("\\\\.\\pipe\\ccc-data","ccc-data",GAME,"ccc-data-session","ccc-data",BUILD.executableSha256(),BUILD.coreFrameAdapterId()),128,512);}
    static NativeGameTransport.CoreReceived core(NativeGameTransport t)throws Exception{var actual=t.readCoreFrameReceived(Instant.now().plusSeconds(30));return assertInstanceOf(NativeGameTransport.CoreReceived.class,actual,actual::toString);}
    static NativeGameTransport.CccRoleReceived role(NativeGameTransport t,Instant until)throws Exception{var c=core(t);var actual=t.readCurrentCccRole(c,until==null?c.validUntil():until);return assertInstanceOf(NativeGameTransport.CccRoleReceived.class,actual,actual::toString);}
    static NativeGameTransport.CccAdvancePrepared advance(NativeGameTransport t)throws Exception{
        var p=t.prepareCurrentCccAdvance(role(t,null));ack(t.submitCurrentCccAdvance(p));ack(t.queryCurrentCccOperation(p,p.deadline()));return p;
    }
    static NativeActionPort.AckReceived ack(NativeActionPort.DispatchOutcome o){return assertInstanceOf(NativeActionPort.AckReceived.class,o);}
    static void confirm(NativeGameTransport t,NativeGameTransport.CccAdvancePrepared p)throws Exception{
        var e=t.prepareCurrentCccEpoch(p,role(t,p.deadline()));ack(t.submitCurrentCccEpoch(e));assertEquals(BigInteger.ONE,e.latestFrame().orElseThrow().actorEpoch());
        assertEquals(BigInteger.ZERO,e.latestFrame().orElseThrow().source().orElseThrow().actorEpoch());
    }
    static void dayTwo(NativeGameTransport t)throws Exception{var first=advance(t);confirm(t,first);advance(t);}
    static NativeGameTransport.CccEventReceived events(NativeGameTransport t)throws Exception{var c=core(t);return assertInstanceOf(NativeGameTransport.CccEventReceived.class,t.readCurrentCccEvent(c,c.validUntil()));}
    static NativeGameTransport.CccDecisionReceived decision(NativeGameTransport t)throws Exception{var c=core(t);return assertInstanceOf(NativeGameTransport.CccDecisionReceived.class,t.readCurrentCccDecision(c,c.validUntil()));}
    static void tierFour(NativeGameTransport t)throws Exception{ack(t.submitCurrentCccEvent(t.prepareCurrentCccTierFour(events(t))));}
    static void decisionAction(NativeGameTransport t,CurrentCccDecision.Action a)throws Exception{ack(t.submitCurrentCccDecision(t.prepareCurrentCccDecision(decision(t),a)));}
    static void confirmedDecision(NativeGameTransport t)throws Exception{dayTwo(t);tierFour(t);advance(t);decisionAction(t,CurrentCccDecision.Action.OPEN_LIST);decisionAction(t,CurrentCccDecision.Action.OPEN_DETAIL);decisionAction(t,CurrentCccDecision.Action.CONFIRM);}

    @Test void thirteenOriginalDaysKeepEpochOneAndIndependentCountsWithoutNewReceiverAuthority()throws Exception{
        var r=new Replay("known");try(var t=transport(r)){var first=advance(t);assertEquals(CurrentCccActorTransitionResult.Status.TRANSITION_PENDING,first.latestFrame().orElseThrow().status());confirm(t,first);
            for(int day=2;day<=13;day++){var p=advance(t);var f=p.latestFrame().orElseThrow();assertEquals(CurrentCccActorTransitionResult.Status.COMPLETED_DAY,f.status());assertEquals(day,f.completedNaturalDays());assertEquals(BigInteger.ONE,f.actorEpoch());assertEquals(START+24*day,p.targetDateRaw());}
            assertThrows(IOException.class,()->t.prepareCurrentCccAdvance(role(t,null)));assertEquals(13,r.advanceWrites);assertEquals(1,r.epochWrites);assertFalse(first.originalUnknown());}
    }
    @Test void oneReceiverOriginalCaseRequiresActualTierFourHalfTaxConfirmAndNewCancelInstance()throws Exception{
        var r=new Replay("known");try(var t=transport(r)){confirmedDecision(t);var q=events(t);var p=t.prepareCurrentCccTemporaryCancel(q);var out=ack(t.submitCurrentCccEvent(p));assertSame(out,t.submitCurrentCccEvent(p));
            assertEquals(32,p.instanceId());assertFalse(p.latestFrame().orElseThrow().eventClosed());assertEquals(1,r.dWrites);assertEquals(1,r.fWrites);assertEquals(1,r.confirmWrites);
            var after=decision(t).frame().source().orElseThrow();assertTrue(after.cooldownExpiryDateRaw().isEmpty());assertFalse(after.cooldownReadbackComplete());assertEquals(List.of(false,false,false,false),after.corruptionTraits().orElseThrow());}
    }
    @Test void dataCaseBoundOrImportedEpochCannotCreatePrivateBusinessOrDateAuthority()throws Exception{
        var r=new Replay("imported-epoch");try(var t=transport(r)){var q=events(t);assertTrue(q.frame().source().orElseThrow().caseBound());assertThrows(IOException.class,()->t.prepareCurrentCccTierFour(q));
            assertThrows(IOException.class,()->t.prepareCurrentCccAdvance(role(t,null)));assertThrows(IOException.class,()->t.prepareCurrentCccDecision(decision(t),CurrentCccDecision.Action.CONFIRM));assertEquals(0,r.effectWrites());}
    }
    @Test void pendingRequiresIndependentFreshOfficialConfirmationAndCannotSkipToDayTwo()throws Exception{
        var r=new Replay("known");try(var t=transport(r)){var p=advance(t);var q=role(t,p.deadline());assertThrows(IOException.class,()->t.prepareCurrentCccAdvance(q));var eventCore=core(t);assertInstanceOf(NativeGameTransport.CccEventUnavailable.class,t.readCurrentCccEvent(eventCore,eventCore.validUntil()));assertEquals(0,r.epochWrites);}
    }
    @Test void foreignPreparationCannotCrossReceiverAndEveryOriginalSubmissionIsIdempotent()throws Exception{
        var a=new Replay("known");var b=new Replay("known");try(var t=transport(a);var other=transport(b)){var q=role(t,null);assertThrows(IOException.class,()->other.prepareCurrentCccAdvance(q));var p=t.prepareCurrentCccAdvance(q);
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,other.submitCurrentCccAdvance(p));var original=t.submitCurrentCccAdvance(p);assertSame(original,t.submitCurrentCccAdvance(p));assertEquals(1,a.advanceWrites);assertEquals(0,b.effectWrites());}
    }
    @Test void actualDayCountAndOriginalSongOfficialIdentitiesCannotSkipOneNaturalDay()throws Exception{
        var r=new Replay("count-skip");try(var t=transport(r)){var p=advance(t);confirm(t,p);assertThrows(IOException.class,()->t.prepareCurrentCccAdvance(role(t,null)));assertEquals(1,r.advanceWrites);}
    }
    @Test void originalOperationStatusPreservesBodyDeadlineSourceNullClaimAndArmFacts()throws Exception{
        var r=new Replay("known");try(var t=transport(r)){var p=t.prepareCurrentCccAdvance(role(t,null));ack(t.submitCurrentCccAdvance(p));var before=p.latestFrame().orElseThrow();var actual=ack(t.queryCurrentCccOperation(p,p.deadline()));var after=CurrentCccActorTransitionResult.decodeOutcome(actual);
            assertTrue(after.source().isEmpty());assertEquals(before.factsBefore(),after.factsBefore());assertEquals(before.claimSequence(),after.claimSequence());assertEquals(before.connectionGeneration(),after.connectionGeneration());
            var fields=NativeWire.parse(NativeWire.decodeExecuteRequest(actual.outbound().orElseThrow().originalPacket()).normalizedAdditionalFields().value());assertEquals(p.deadline().toEpochMilli(),fields.get("core_control_deadline_unix_ms").longValue());assertEquals(p.operationId(),fields.get("ccc_actor_transition").get("operation_id").textValue());assertEquals(1,r.advanceWrites);}
    }
    @Test void eventBeforeD2DecisionBeforeD3AndMissingHalfTaxCannotBeBypassed()throws Exception{
        var r=new Replay("known");try(var t=transport(r)){var p=advance(t);confirm(t,p);assertThrows(IOException.class,()->t.prepareCurrentCccTierFour(events(t)));advance(t);tierFour(t);assertThrows(IOException.class,()->t.prepareCurrentCccDecision(decision(t),CurrentCccDecision.Action.OPEN_LIST));}
        var noHalf=new Replay("not-half");try(var t=transport(noHalf)){dayTwo(t);tierFour(t);advance(t);decisionAction(t,CurrentCccDecision.Action.OPEN_LIST);decisionAction(t,CurrentCccDecision.Action.OPEN_DETAIL);assertThrows(IOException.class,()->t.prepareCurrentCccDecision(decision(t),CurrentCccDecision.Action.CONFIRM));assertEquals(0,noHalf.confirmWrites);}
    }
    @Test void cancelRequiresActualConfirmAndDifferentInstanceFromTheSpentTierFourEvent()throws Exception{
        var r=new Replay("known");try(var t=transport(r)){dayTwo(t);tierFour(t);assertThrows(IOException.class,()->t.prepareCurrentCccTemporaryCancel(events(t)));assertEquals(0,r.fWrites);}
        var same=new Replay("same-instance");try(var t=transport(same)){confirmedDecision(t);assertThrows(IOException.class,()->t.prepareCurrentCccTemporaryCancel(events(t)));assertEquals(0,same.fWrites);}
    }
    @Test void lostArmAndChangedImmutableBeforeSourceRemainUnknownAndAreNeverReplayed()throws Exception{
        var lost=new Replay("lost");try(var t=transport(lost)){var p=t.prepareCurrentCccAdvance(role(t,null));var out=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentCccAdvance(p));assertTrue(p.originalUnknown());assertSame(out,t.submitCurrentCccAdvance(p));assertEquals(1,lost.advanceWrites);}
        var changed=new Replay("changed-event-source");try(var t=transport(changed)){dayTwo(t);var p=t.prepareCurrentCccTierFour(events(t));var out=assertInstanceOf(NativeActionPort.Unknown.class,t.submitCurrentCccEvent(p));assertSame(out,t.submitCurrentCccEvent(p));assertTrue(t.originalIndeterminateCoreAcknowledgement(out.requestId()).isPresent());assertEquals(1,changed.dWrites);}
    }
    @Test void oldV17DateAndTedCannotBorrowAnEnteredCccCaseEvenAfterKnownConfirmation()throws Exception{
        var r=new Replay("known");try(var t=transport(r)){var p=advance(t);confirm(t,p);var c=core(t);assertThrows(IOException.class,()->t.prepareCurrentDateAdvance(c,c.validUntil()));assertInstanceOf(NativeGameTransport.TedRoleUnavailable.class,t.readCurrentTedRole(c,c.validUntil()));assertEquals(1,r.advanceWrites);}
    }
    @Test void consumedQueryAndFalseToggleDoNotInventAnotherClaimOrAppliedBusiness()throws Exception{
        var r=new Replay("known");try(var t=transport(r)){dayTwo(t);var q=events(t);var p=t.prepareCurrentCccTierFour(q);ack(t.submitCurrentCccEvent(p));assertThrows(IOException.class,()->q.requireOriginal(t,q.validUntil()));advance(t);
            var open=t.prepareCurrentCccDecision(decision(t),CurrentCccDecision.Action.OPEN_LIST);ack(t.submitCurrentCccDecision(open));assertFalse(open.latestFrame().orElseThrow().nativeHandled());assertFalse(open.latestFrame().orElseThrow().decisionApplied());assertEquals(1,r.listWrites);}
    }

    static void cancel(NativeGameTransport t)throws Exception{var q=events(t);ack(t.submitCurrentCccEvent(t.prepareCurrentCccTemporaryCancel(q)));}
    @Test void postCancelFreshAbsentCensusAllowsOnlyNewFixedNavigationAndPreservesFalseCanTooltip()throws Exception{
        var r=new Replay("post-cancel");try(var t=transport(r)){confirmedDecision(t);cancel(t);events(t);
            var q=decision(t);assertFalse(q.frame().source().orElseThrow().detailVisible());var open=t.prepareCurrentCccDecision(q,CurrentCccDecision.Action.OPEN_LIST);
            var original=ack(t.submitCurrentCccDecision(open));assertSame(original,t.submitCurrentCccDecision(open));decisionAction(t,CurrentCccDecision.Action.OPEN_DETAIL);
            var after=decision(t).frame().source().orElseThrow();assertFalse(after.nativeCanConfirm().orElseThrow());assertEquals("actual cooldown why",after.confirmTooltip().orElseThrow());
            assertTrue(after.cooldownExpiryDateRaw().isEmpty());assertFalse(after.cooldownReadbackComplete());assertEquals(2,r.listWrites);assertEquals(2,r.detailWrites);assertEquals(1,r.confirmWrites);assertEquals(1,r.fWrites);assertEquals(3,r.days);
            assertThrows(IOException.class,()->t.prepareCurrentCccDecision(decision(t),CurrentCccDecision.Action.CONFIRM));}
    }
    @Test void postConfirmBeforeCancelAndPostCancelWithoutIndependentCensusCannotNavigate()throws Exception{
        var r=new Replay("post-cancel");try(var t=transport(r)){confirmedDecision(t);assertThrows(IOException.class,()->t.prepareCurrentCccDecision(decision(t),CurrentCccDecision.Action.OPEN_LIST));
            cancel(t);assertThrows(IOException.class,()->t.prepareCurrentCccDecision(decision(t),CurrentCccDecision.Action.OPEN_LIST));assertEquals(1,r.listWrites);assertEquals(1,r.confirmWrites);}
    }
    @Test void stillPresentCancelledInstanceDoesNotAuthorizePostCaseNavigation()throws Exception{
        var r=new Replay("post-present");try(var t=transport(r)){confirmedDecision(t);cancel(t);events(t);
            assertThrows(IOException.class,()->t.prepareCurrentCccDecision(decision(t),CurrentCccDecision.Action.OPEN_LIST));assertEquals(1,r.listWrites);assertEquals(1,r.detailWrites);}
    }
    @Test void postCancelNavigationCannotUseAnotherNewIdAfterAnActualListAttempt()throws Exception{
        var r=new Replay("post-cancel");try(var t=transport(r)){confirmedDecision(t);cancel(t);events(t);decisionAction(t,CurrentCccDecision.Action.OPEN_LIST);r.decisionStage=0;
            assertThrows(IOException.class,()->t.prepareCurrentCccDecision(decision(t),CurrentCccDecision.Action.OPEN_LIST));assertEquals(2,r.listWrites);assertEquals(1,r.confirmWrites);}
    }
    @Test void postCancelObservedEmptyAndEmbeddedNulWhyAreCompleteDataNotInferredExpiry()throws Exception{
        for(String mode:List.of("post-empty","post-rich")){var r=new Replay(mode);try(var t=transport(r)){confirmedDecision(t);cancel(t);events(t);decisionAction(t,CurrentCccDecision.Action.OPEN_LIST);decisionAction(t,CurrentCccDecision.Action.OPEN_DETAIL);
            var s=decision(t).frame().source().orElseThrow();assertEquals(mode.equals("post-empty")?"":"actual\u0000cooldown\u0015\n",s.confirmTooltip().orElseThrow());assertFalse(s.nativeCanConfirm().orElseThrow());assertTrue(s.cooldownExpiryDateRaw().isEmpty());assertFalse(s.cooldownReadbackComplete());assertEquals(1,r.confirmWrites);}}
    }

    static final class Replay implements NativePacketPort {
        final String mode;final ArrayDeque<byte[]> packets=new ArrayDeque<>();boolean closed,pending,confirmed,dChosen,decisionConfirmed,cancelled;int days,advanceWrites,epochWrites,dWrites,fWrites,listWrites,detailWrites,confirmWrites,decisionStage;
        String operation;long originalDeadline;ObjectNode opCore,opBefore,roleBefore,eventBefore,decisionBefore;int opDay;
        Replay(String mode)throws IOException{this.mode=mode;if(mode.equals("imported-epoch")){confirmed=true;days=2;}
            var h=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",42).put("connection_generation",BigInteger.valueOf(2)).put("bridge_version","ccc-data").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256()).put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            var names=new java.util.LinkedHashSet<String>();names.add(CoreFrame.CAPABILITY);for(var a:CurrentCccActorTransition.Action.values())names.add(a.capability());for(var a:CurrentCccEvent.Action.values())names.add(a.capability());for(var a:CurrentCccDecision.Action.values())names.add(a.capability());var caps=h.putArray("capabilities");names.forEach(caps::add);packets.add(NativeWire.packet(StrictJson.canonical(h)));}
        int actor(){return days>0?44739:36423;}int effectWrites(){return advanceWrites+epochWrites+dWrites+fWrites+listWrites+detailWrites+confirmWrites;}
        CoreFrame.Prefix prefix(){return new CoreFrame.Prefix(START+24*days,3,true,1,true,true,actor(),true);}
        ObjectNode coreJson(){return StrictJson.object().put("date_raw",START+24*days).put("speed",3).put("paused",true).put("local_player_id",1).put("map_ready",true).put("has_played_character",true).put("played_character_id",actor()).put("played_character_alive",true);}
        public void verify()throws IOException{if(closed)throw new IOException("CCC Java DATA port closed");}public void verifyCoreControlWindowPolicy()throws IOException{verify();}public void awaitConnection(Instant until)throws IOException{verify();}
        public byte[] readPacket(Instant until)throws IOException{verify();if(packets.isEmpty())throw new IOException("CCC DATA response missing");return packets.removeFirst();}
        ObjectNode roleSource()throws IOException{
            var s=NativeWire.object(token("transition",confirmed?"query-epoch-one-source":pending?"query-pending-official-source":"query-song-source").get("source"));s.put("completed_natural_days",days).put("advance_admissible",!pending&&days<13);
            if(confirmed&&mode.equals("count-skip"))s.put("completed_natural_days",days+1);
            if(pending){var p=(ObjectNode)s.get("pending");p.put("operation_id",operation).put("original_deadline_unix_ms",originalDeadline).put("claim_sequence",Integer.toString(advanceWrites)).put("generation",Integer.toString(advanceWrites));}
            return s;
        }
        public void writePacket(byte[] packet,Instant until)throws IOException{
            verify();var req=NativeWire.decodeExecuteRequest(packet);ObjectNode result;boolean ok=true;
            if(req.step().equals(CoreFrame.STEP))result=NativeWire.object(NativeWire.parse(CoreFramePublicCodec.encode(new CoreFrame.Partial(BUILD,prefix())).bytes()));
            else{
                var fields=NativeWire.parse(req.normalizedAdditionalFields().value());
                if(fields.has("ccc_actor_transition")){
                    var c=(ObjectNode)fields.get("ccc_actor_transition");var action=CurrentCccActorTransition.Action.parse(c.get("action").textValue());long deadline=fields.get("core_control_deadline_unix_ms").longValue();
                    switch(action){
                        case QUERY_ROLE->{result=token("transition",confirmed?"query-epoch-one-source":pending?"query-pending-official-source":"query-song-source");roleBefore=roleSource();result.set("source",roleBefore);result.set("facts_before",coreJson());result.put("completed_natural_days",roleBefore.get("completed_natural_days").intValue());}
                        case ADVANCE_DAY->{advanceWrites++;operation=c.get("operation_id").textValue();originalDeadline=deadline;opDay=days;opCore=NativeWire.object(c.get("expected_core"));opBefore=roleBefore.deepCopy();if(mode.equals("lost"))return;
                            result=token("transition","submitted");result.set("source",opBefore);result.set("facts_before",opCore);result.put("actor_epoch",confirmed?"1":"0").put("completed_natural_days",days);progress(result,false);}
                        case QUERY_OPERATION->{days=opDay+1;pending=!confirmed;result=token("transition","transition-pending");result.set("facts_before",opCore);result.put("status",pending?"transition_pending":"completed_day").put("actor_epoch",confirmed?"1":"0").put("completed_natural_days",days);progress(result,true);}
                        case CONFIRM_EPOCH->{epochWrites++;result=token("transition","epoch-confirmed");result.set("source",roleBefore);result.set("facts_before",coreJson());confirmed=true;pending=false;}
                        default->throw new IOException("Unknown CCC DATA transition action");
                    }
                    result.put("action",action.wire()).put("request_id",req.requestId()).put("operation_id",c.get("operation_id").textValue()).put("deadline_unix_ms",deadline);
                    if(action!=CurrentCccActorTransition.Action.QUERY_ROLE)result.put("claim_sequence",Integer.toString(advanceWrites));
                    ok=result.get("ok").booleanValue();
                }else if(fields.has("ccc_event")){
                    var c=fields.get("ccc_event");var a=CurrentCccEvent.Action.parse(c.get("action").textValue());boolean later=decisionConfirmed;result=token("event",a==CurrentCccEvent.Action.QUERY?(later?"query-cancel-source":"query-original-source"):a==CurrentCccEvent.Action.SELECT_TIER_FOUR?"tier-four-dispatched":"cancel-dispatched");
                    if(a==CurrentCccEvent.Action.QUERY){eventBefore=NativeWire.object(result.get("source"));int instance=later&&!mode.equals("same-instance")?32:31;eventBefore.put("fixed_instance_id",instance);var row=(ObjectNode)eventBefore.get("event_census").get("events").get(0);row.put("instance_id",instance).put("recipient_character_id",actor());
                        if(cancelled&&mode.startsWith("post-")&&!mode.equals("post-present")){eventBefore.putNull("fixed_instance_id").put("select_d_admissible",false).put("select_f_admissible",false);var census=(ObjectNode)eventBefore.get("event_census");census.put("named_root_count",0);census.putArray("events");}result.set("source",eventBefore);}
                    else{result.set("source",eventBefore.deepCopy());result.put("instance_id",c.get("instance_id").intValue());if(a==CurrentCccEvent.Action.SELECT_TIER_FOUR){dWrites++;dChosen=true;if(mode.equals("changed-event-source"))((ObjectNode)result.get("source").get("event_census").get("events").get(0)).put("opening","different actual cached title");}else{fWrites++;cancelled=true;if(mode.startsWith("post-"))decisionStage=0;}}
                    result.set("facts_before",NativeWire.object(c.get("expected_core")));result.put("provider_generation","5").put("query_sequence",later?"8":"7");
                }else{
                    var c=fields.get("ccc_decision");var a=CurrentCccDecision.Action.parse(c.get("action").textValue());String q=decisionStage==0?"query-open-list-source":decisionStage==1?"query-open-detail-source":"query-confirm-source";
                    result=token("decision",a==CurrentCccDecision.Action.QUERY?q:a==CurrentCccDecision.Action.OPEN_LIST?"open-list-dispatched":a==CurrentCccDecision.Action.OPEN_DETAIL?"open-detail-dispatched":"confirm-dispatched");
                    if(a==CurrentCccDecision.Action.QUERY){decisionBefore=NativeWire.object(result.get("source"));if(mode.equals("not-half"))decisionBefore.put("fixture_tax_exact_half",false);if(cancelled){var ar=decisionBefore.putArray("corruption_traits");for(int i=0;i<4;i++)ar.add(false);
                        if(mode.startsWith("post-")&&decisionStage==2)decisionBefore.put("native_can_confirm",false).put("confirm_admissible",false).put("confirm_tooltip",mode.equals("post-empty")?"":mode.equals("post-rich")?"actual\u0000cooldown\u0015\n":"actual cooldown why");}result.set("source",decisionBefore);}
                    else{result.set("source",decisionBefore);if(a==CurrentCccDecision.Action.OPEN_LIST){listWrites++;decisionStage=1;result.put("native_handled",false);}else if(a==CurrentCccDecision.Action.OPEN_DETAIL){detailWrites++;decisionStage=2;}else{confirmWrites++;decisionConfirmed=true;}}
                    result.set("facts_before",NativeWire.object(c.get("expected_core")));
                }
            }
            var e=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",req.requestId()).put("ok",ok);e.set("result",result);packets.add(NativeWire.packet(StrictJson.canonical(e)));
        }
        void progress(ObjectNode result,boolean exact){var p=(ObjectNode)result.get("progress");p.put("generation",Integer.toString(advanceWrites)).put("starting_date_raw",START+24*opDay).put("target_date_raw",START+24*(opDay+1)).put("last_observed_date_raw",START+24*(exact?opDay+1:opDay)).put("before_actor_id",opCore.get("played_character_id").intValue()).put("after_actor_id",exact?44739:-1).put("completed_daily_ticks",exact?1:0).put("exact_day_confirmed",exact).put("transition_pending",exact&&!confirmed).put("shutdown_safe",exact).put("armed",!exact);}
        public void close(){closed=true;}
    }
}
