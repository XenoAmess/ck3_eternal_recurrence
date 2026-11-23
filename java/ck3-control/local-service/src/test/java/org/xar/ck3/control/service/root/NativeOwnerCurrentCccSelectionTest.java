package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Pure typed DATA only: no Native packets, private Received/prepared instances or runtime authority. */
final class NativeOwnerCurrentCccSelectionTest {
    private static final BigInteger ONE=BigInteger.ONE,TWO=BigInteger.TWO,MAX=ONE.shiftLeft(64).subtract(ONE);
    private static final int START=53144328;
    private static ObjectNode config(String mode){var c=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v45").put("mode",mode)
            .put("overall_timeout_seconds",600).put("read_timeout_seconds",60).put("maximum_frames_per_operation",1024);
        c.putObject("owner_descriptor").put("path","D:/ccc-NoGame-DATA/owner.json").put("bytes",1).put("sha256","0".repeat(64));
        if(mode.equals("current_ccc_original_case_once"))c.put("maximum_status_polls",128).put("status_poll_delay_ms",500);return c;}
    private static CoreFrame.Prefix core(int day,int actor){return new CoreFrame.Prefix(START+day*24,3,true,1,true,true,actor,true);}
    private static CurrentLetterResult.OwnerWitness owner(int connection,int ticket){return new CurrentLetterResult.OwnerWitness(BigInteger.valueOf(connection),BigInteger.valueOf(ticket),BigInteger.valueOf(ticket+1),7);}
    private static CurrentCccActorTransitionSource source(int days,int song,int official,boolean advance){boolean first=days==0;return new CurrentCccActorTransitionSource(
            first?CurrentCccActorTransitionSource.Role.SONG:CurrentCccActorTransitionSource.Role.OFFICIAL,true,Optional.of(true),first?BigInteger.ZERO:ONE,
            Optional.of(song),first?Optional.empty():Optional.of(official),Optional.empty(),days,13,START,true,true,advance,false);}
    private static CurrentCccActorTransitionResult role(CurrentCccActorTransitionSource s,CoreFrame.Prefix p){return new CurrentCccActorTransitionResult(
            CurrentCccActorTransition.Action.QUERY_ROLE,"ccc-role","",CurrentCccActorTransitionResult.Status.AVAILABLE,true,false,ONE,TWO,BigInteger.ZERO,
            s.actorEpoch(),s.completedNaturalDays(),MAX,ONE,BigInteger.valueOf(5),BigInteger.valueOf(6),7,Optional.of(p),Optional.of(s),Optional.empty(),false,false,true,Optional.empty());}
    private static CurrentCccActorTransitionResult terminal(boolean first,int song,int official){int beforeDay=first?0:1;int actor=first?song:official;var before=core(beforeDay,actor);
        var p=new CurrentCccActorTransitionResult.Progress(ONE,before.dateRaw(),before.dateRaw()+24,before.dateRaw()+24,actor,official,1,0,0,true,true,true,true,first,true,false,false);
        return new CurrentCccActorTransitionResult(CurrentCccActorTransition.Action.ADVANCE_DAY,"ccc-day","ccc-op",first?CurrentCccActorTransitionResult.Status.TRANSITION_PENDING:CurrentCccActorTransitionResult.Status.COMPLETED_DAY,
                true,true,ONE,TWO,BigInteger.TEN,first?BigInteger.ZERO:ONE,beforeDay+1,MAX,ONE,BigInteger.valueOf(5),BigInteger.valueOf(6),7,
                Optional.of(before),Optional.of(source(beforeDay,song,official,true)),Optional.of(p),true,true,true,Optional.empty());}
    private static CurrentLydSource.EventRow event(int instance,int actor,String text){return new CurrentLydSource.EventRow(instance,actor,6,"xccc.1001",text,"raw description",true,true,true,
            List.of(new CurrentLydSource.EventOption(5,false,"other","actual why",Optional.empty(),Optional.empty()),new CurrentLydSource.EventOption(3,true,"actual .d","",Optional.empty(),Optional.empty()),
                    new CurrentLydSource.EventOption(4,true,"actual .f","",Optional.empty(),Optional.empty())));}
    private static CurrentCccEventSource events(int instance,int actor,String text){return new CurrentCccEventSource(new CurrentLydSource.Events(true,1,List.of(event(instance,actor,text))),Optional.of(instance),true,true,true,true);}
    private static CurrentCccEventResult query(CurrentCccEventSource s,CoreFrame.Prefix p){return new CurrentCccEventResult(CurrentCccEvent.Action.QUERY,CurrentCccEventResult.Status.AVAILABLE,false,false,true,
            ONE,TWO,BigInteger.ZERO,Optional.of(p),Optional.of(owner(1,5)),Optional.of(s),Optional.empty(),Optional.empty());}
    private static CurrentCccEventResult selected(CurrentCccEventResult q,CurrentCccEventSource actual,int instance){return new CurrentCccEventResult(CurrentCccEvent.Action.SELECT_TIER_FOUR,
            CurrentCccEventResult.Status.SELECTION_DISPATCHED,true,true,true,ONE,TWO,BigInteger.TEN,q.factsBefore(),Optional.of(owner(1,900)),Optional.of(actual),Optional.empty(),Optional.of(instance));}
    private static CurrentCccDecisionSource detail(boolean can,String why){return new CurrentCccDecisionSource(true,true,true,true,true,true,false,false,true,false,can,true,
            Optional.of(List.of(false,false,false,true)),Optional.of(true),Optional.of(true),true,Optional.of(why),Optional.empty(),false,Optional.of(1),Optional.of(1),Optional.of(1),
            Optional.of(CurrentCccDecision.DecisionKey.CORRUPTION_POLICY),Optional.of(can),List.of(new CurrentCccDecisionSource.Row(CurrentCccDecision.DecisionKey.CORRUPTION_POLICY,false,true)));}
    private static CurrentCccDecisionSource closedList(){return new CurrentCccDecisionSource(true,false,true,false,false,false,false,true,true,false,false,true,
            Optional.of(List.of(false,false,false,true)),Optional.of(true),Optional.of(true),false,Optional.empty(),Optional.empty(),false,Optional.of(1),Optional.of(1),Optional.empty(),Optional.empty(),Optional.empty(),
            List.of(new CurrentCccDecisionSource.Row(CurrentCccDecision.DecisionKey.CORRUPTION_POLICY,false,false)));}
    private static CurrentCccDecisionResult query(CurrentCccDecisionSource s,CoreFrame.Prefix p){return new CurrentCccDecisionResult(CurrentCccDecision.Action.QUERY,CurrentCccDecisionResult.Status.AVAILABLE,
            false,false,false,true,ONE,TWO,BigInteger.ZERO,Optional.of(p),Optional.of(owner(1,5)),Optional.of(s),Optional.empty(),Optional.empty());}
    private static CurrentCccDecisionResult decisionAck(CurrentCccDecisionResult q,CurrentCccDecisionSource s,boolean toggle,boolean handled){return new CurrentCccDecisionResult(
            toggle?CurrentCccDecision.Action.OPEN_LIST:CurrentCccDecision.Action.CONFIRM,toggle?CurrentCccDecisionResult.Status.NAVIGATION_DISPATCHED:CurrentCccDecisionResult.Status.CONFIRMATION_DISPATCHED,
            true,true,handled,true,ONE,TWO,BigInteger.TEN,q.factsBefore(),Optional.of(owner(1,900)),Optional.of(s),Optional.empty(),toggle?Optional.empty():Optional.of(CurrentCccDecision.DecisionKey.CORRUPTION_POLICY));}

    @Test void fourStrictModesHaveActualTwoOrBoundedThirteenDaySubmissionBudgets() throws IOException {
        for(String mode:List.of("current_ccc_query_role","current_ccc_query_event","current_ccc_query_decision")){
            var c=config(mode);assertEquals(6,c.size());assertTrue(NativeOwnerSnapshotMain268.currentCccConfig(c).queryOnly());assertEquals(2,NativeOwnerSnapshotMain268.currentCccConfig(c).submissions());
        }
        var c=config("current_ccc_original_case_once");assertEquals(8,c.size());assertEquals(1745,NativeOwnerSnapshotMain268.currentCccConfig(c).submissions());
        assertEquals(3409,NativeOwnerSnapshotMain268.currentCccConfig(c.put("maximum_status_polls",256)).submissions());
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_CCC,NativeOwnerSnapshotMain268.observationMode(c));
    }
    @Test void callerSelectorsWrongSchemasOwnerTypesAndUnboundedPollingAreRejected() throws IOException {
        for(String key:List.of("actor","days","maximum_natural_days","actor_epoch","operation_id","instance_id","decision_key","event_role","choice_token","expected_core","allow_actor_change","checkpoint_archive_path","save","status_poll_interval_ms"))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentCccConfig(config("current_ccc_original_case_once").put(key,1)));
        for(String key:List.of("maximum_status_polls","status_poll_delay_ms")){
            var missing=config("current_ccc_original_case_once");missing.remove(key);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentCccConfig(missing));
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentCccConfig(config("current_ccc_original_case_once").put(key,true)));
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentCccConfig(config("current_ccc_query_role").put(key,1)));
        }
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentCccConfig(config("current_ccc_original_case_once").put("maximum_status_polls",257)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentCccConfig(config("current_ccc_original_case_once").put("status_poll_delay_ms",1001)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentCccConfig(config("current_ccc_query_role").put("schema","xar.native-owner-snapshot-config/v38")));
        var bad=config("current_ccc_query_role");((ObjectNode)bad.get("owner_descriptor")).put("bytes",true);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentCccConfig(bad));
    }
    @Test void actualShownSongAndOfficialRolesPreserveSignedPackedActorData() throws IOException {
        for(int actor:List.of(0,-2)){
            var s=source(0,actor,42,true);var f=role(s,core(0,actor));
            assertEquals(s,NativeOwnerSnapshotMain268.requireCurrentCccPositiveRole(f,core(0,actor),CurrentCccActorTransitionSource.Role.SONG,BigInteger.ZERO,actor,-1,false,0,START));
        }
        var s=source(2,0,42,true);assertEquals(s,NativeOwnerSnapshotMain268.requireCurrentCccPositiveRole(role(s,core(2,42)),core(2,42),CurrentCccActorTransitionSource.Role.OFFICIAL,ONE,0,42,false,2,START));
    }
    @Test void frontierOneAndNaturalDayCountAreSeparateAndThirteenCannotAuthorizeFourteen() throws IOException {
        var s=source(2,0,42,true);var f=role(s,core(2,42));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCccPositiveRole(f,core(2,42),CurrentCccActorTransitionSource.Role.OFFICIAL,TWO,0,42,false,2,START));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCccPositiveRole(f,core(2,42),CurrentCccActorTransitionSource.Role.OFFICIAL,ONE,0,42,false,3,START));
        var atCap=source(13,0,42,false);NativeOwnerSnapshotMain268.requireCurrentCccRole(role(atCap,core(13,42)),core(13,42));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCccPositiveRole(role(atCap,core(13,42)),core(13,42),CurrentCccActorTransitionSource.Role.OFFICIAL,ONE,0,42,false,13,START));
        assertThrows(IllegalArgumentException.class,()->source(14,0,42,false));
    }
    @Test void exactPendingAndCompletedDayKeepOriginalOperationAndFullUint64Deadline() throws IOException {
        var d1=terminal(true,0,42);assertEquals(MAX,d1.deadlineUnixMs());NativeOwnerSnapshotMain268.requireCurrentCccDayTerminal(d1,core(0,0),"ccc-op",START+24,true,1);
        var d2=terminal(false,0,42);NativeOwnerSnapshotMain268.requireCurrentCccDayTerminal(d2,core(1,42),"ccc-op",START+48,false,2);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCccDayTerminal(d1,core(0,0),"foreign-op",START+24,true,1));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCccDayTerminal(d2,core(1,42),"ccc-op",START+48,false,3));
    }
    @Test void eventActionMayHaveNewTicketAndPumpOnSameOriginalConnection() throws IOException {
        var s=events(1,42,"raw\u0015\n");var q=query(s,core(2,42));var ack=selected(q,s,1);
        NativeOwnerSnapshotMain268.requireCurrentCccEventDispatch(ack,q,core(2,42),ONE,CurrentCccEvent.Action.SELECT_TIER_FOUR,1);
        assertFalse(ack.eventClosed());assertFalse(ack.nativeHandled());
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCccEventDispatch(ack,q,core(2,42),TWO,CurrentCccEvent.Action.SELECT_TIER_FOUR,1));
    }
    @Test void changedCompleteEventSourceOrFixedInstanceCannotBorrowOriginalAck() throws IOException {
        var q=query(events(1,42,"before"),core(2,42));var changed=selected(q,events(1,42,"same price changed actual text"),1);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCccEventDispatch(changed,q,core(2,42),ONE,CurrentCccEvent.Action.SELECT_TIER_FOUR,1));
        var other=selected(q,events(2,42,"before"),2);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCccEventDispatch(other,q,core(2,42),ONE,CurrentCccEvent.Action.SELECT_TIER_FOUR,2));
    }
    @Test void actualInstanceAbsenceRequiresCompleteCensusNotJustMissingFixedKey() throws IOException {
        var present=new CurrentCccEventSource(new CurrentLydSource.Events(true,1,List.of(event(1,42,"still there"))),Optional.empty(),false,false,false,true);
        assertFalse(NativeOwnerSnapshotMain268.currentCccInstanceAbsent(present,1));
        var absent=new CurrentCccEventSource(new CurrentLydSource.Events(true,0,List.of()),Optional.empty(),false,false,false,true);
        assertTrue(NativeOwnerSnapshotMain268.currentCccInstanceAbsent(absent,1));
    }
    @Test void actualToggleFalseAndTrueRemainKnownDispatchWithoutApplyCredit() throws IOException {
        var s=closedList();var q=query(s,core(3,42));
        for(boolean handled:List.of(false,true)){var ack=decisionAck(q,s,true,handled);NativeOwnerSnapshotMain268.requireCurrentCccDecisionDispatch(ack,q,core(3,42),ONE,CurrentCccDecision.Action.OPEN_LIST);assertEquals(handled,ack.nativeHandled());assertFalse(ack.decisionApplied());}
        var selected=detail(true,"actual why");var cq=query(selected,core(3,42));var changed=decisionAck(cq,detail(true,"changed actual why"),false,false);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCccDecisionDispatch(changed,cq,core(3,42),ONE,CurrentCccDecision.Action.CONFIRM));
    }
    @Test void actualFalseCanEmptyNulAndFullTooltipRemainDataWithNoGuessedExpiry() throws IOException {
        for(String why:List.of("","x".repeat(16384),"actual\u0000rich\u0015\n\t")){
            var s=detail(false,why);var q=query(s,core(3,42));assertEquals(s,NativeOwnerSnapshotMain268.requireCurrentCccDecisionQuery(q,core(3,42),ONE));
            assertEquals(why,s.confirmTooltip().orElseThrow());assertTrue(s.cooldownExpiryDateRaw().isEmpty());assertFalse(s.cooldownReadbackComplete());
            assertThrows(IllegalArgumentException.class,()->decisionAck(q,s,false,false));
        }
        assertThrows(IllegalArgumentException.class,()->detail(false,"x".repeat(16385)));
    }
}
