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

/** Pure DATA fixtures only. No private Received/prepared object, native packet, Game or runtime qualification. */
final class NativeOwnerCurrentRmtmSelectionTest {
    private static final BigInteger Z=BigInteger.ZERO,O=BigInteger.ONE,T=BigInteger.TWO,MAX=O.shiftLeft(64).subtract(O);
    private static final int START=-240,SONG=-2,SUCCESSOR=42;
    private static ObjectNode config(String mode){var c=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v47").put("mode",mode)
            .put("overall_timeout_seconds",600).put("read_timeout_seconds",60).put("maximum_frames_per_operation",1024);
        c.putObject("owner_descriptor").put("path","D:/rmtm-NoGame-DATA/owner.json").put("bytes",1).put("sha256","0".repeat(64));
        if(mode.endsWith("_once"))c.put("maximum_status_polls",128).put("status_poll_delay_ms",500);return c;}
    private static CoreFrame.Prefix core(int days,int actor){return new CoreFrame.Prefix(START+days*24,3,true,1,true,true,actor,true);}
    private static CurrentLetterResult.OwnerWitness owner(int connection,int ticket){return new CurrentLetterResult.OwnerWitness(BigInteger.valueOf(connection),BigInteger.valueOf(ticket),BigInteger.valueOf(ticket+1),7);}
    private static CurrentRmtmActorTransitionSource source(int days,int song,int successor,boolean shown,boolean advance){boolean first=days<5;
        return new CurrentRmtmActorTransitionSource(first?CurrentRmtmActorTransitionSource.Role.SONG:CurrentRmtmActorTransitionSource.Role.SUCCESSOR,true,Optional.of(shown),first?Z:O,
                Optional.of(song),first?Optional.empty():Optional.of(successor),Optional.empty(),days,14,START,true,Optional.empty(),true,true,advance,false);}
    private static CurrentRmtmActorTransitionResult role(CurrentRmtmActorTransitionSource s,CoreFrame.Prefix p){return new CurrentRmtmActorTransitionResult(
            CurrentRmtmActorTransition.Action.QUERY_ROLE,"rmtm-role","",CurrentRmtmActorTransitionResult.Status.AVAILABLE,true,false,O,T,Z,
            s.actorEpoch(),s.completedNaturalDays(),MAX,O,BigInteger.valueOf(5),BigInteger.valueOf(6),7,Optional.of(p),Optional.of(s),Optional.empty(),false,false,true,Optional.empty());}
    private static CurrentRmtmActorTransitionResult terminal(int day){int beforeActor=day<=5?SONG:SUCCESSOR;int afterActor=day==5?SUCCESSOR:beforeActor;var p=core(day-1,beforeActor);
        var progress=new CurrentRmtmActorTransitionResult.Progress(O,p.dateRaw(),p.dateRaw()+24,p.dateRaw()+24,beforeActor,afterActor,1,0,0,true,true,true,true,day==5,true,false,false);
        return new CurrentRmtmActorTransitionResult(CurrentRmtmActorTransition.Action.ADVANCE_DAY,"rmtm-day","rmtm-op",
                day==5?CurrentRmtmActorTransitionResult.Status.TRANSITION_PENDING:CurrentRmtmActorTransitionResult.Status.COMPLETED_DAY,true,true,O,T,BigInteger.TEN,
                day<=5?Z:O,day,MAX,O,BigInteger.valueOf(5),BigInteger.valueOf(6),7,Optional.of(p),Optional.of(source(day-1,SONG,SUCCESSOR,true,true)),Optional.of(progress),true,true,true,Optional.empty());}
    private static CurrentRmtmTitleQuerySource physical(int actor,long holder,List<CurrentRmtmTitleQuerySource.Law> laws){return new CurrentRmtmTitleQuerySource(actor,0xffff_fffeL,
            Optional.of(new CurrentRmtmTitleQuerySource.CharacterRef(holder,true)),Optional.of(new CurrentRmtmTitleQuerySource.CharacterRef(0,true)),laws.size(),laws,1,true);}
    private static CurrentRmtmDecisionSource list(){return new CurrentRmtmDecisionSource(true,false,true,false,false,false,false,true,true,false,false,true,false,
            Optional.empty(),Optional.of(1),Optional.of(1),Optional.empty(),Optional.empty(),Optional.empty(),List.of(new CurrentRmtmDecisionSource.Row(CurrentRmtmDecision.DecisionKey.RESTORE,false,false)));}
    private static CurrentRmtmDecisionSource detail(boolean can,String why){return new CurrentRmtmDecisionSource(true,true,true,true,true,true,false,false,true,false,can,true,true,
            Optional.of(why),Optional.of(1),Optional.of(1),Optional.of(1),Optional.of(CurrentRmtmDecision.DecisionKey.RESTORE),Optional.of(can),List.of(new CurrentRmtmDecisionSource.Row(CurrentRmtmDecision.DecisionKey.RESTORE,false,true)));}
    private static CurrentRmtmDecisionResult query(CurrentRmtmDecisionSource s,CoreFrame.Prefix p){return new CurrentRmtmDecisionResult(CurrentRmtmDecision.Action.QUERY,CurrentRmtmDecisionResult.Status.AVAILABLE,
            false,false,false,true,O,T,Z,Optional.of(p),Optional.of(owner(1,5)),Optional.of(s),Optional.empty(),Optional.empty());}
    private static CurrentLydSource.EventRow event(int instance,int actor,CurrentRmtmEvent.Action action,String text){return new CurrentLydSource.EventRow(instance,actor,1,action.definition(),text,"actual description",true,true,true,
            List.of(new CurrentLydSource.EventOption(0,true,"actual one option","",Optional.empty(),Optional.empty())));}
    private static CurrentRmtmEventResult eventQuery(CurrentRmtmEvent.Action action,CurrentRmtmEventSource s,CoreFrame.Prefix p){return new CurrentRmtmEventResult(action,CurrentRmtmEventResult.Status.AVAILABLE,
            false,false,true,O,T,Z,Optional.of(p),Optional.of(owner(1,5)),Optional.of(s),Optional.empty(),Optional.empty());}
    private static CurrentRmtmObservationResult phase(CurrentRmtmObservation.Phase phase,int day,int actor,long title,long heir){
        var physical=new CurrentRmtmTitleQuerySource(actor,title,Optional.of(new CurrentRmtmTitleQuerySource.CharacterRef(Integer.toUnsignedLong(actor),true)),Optional.of(new CurrentRmtmTitleQuerySource.CharacterRef(heir,true)),0,List.of(),1,true);
        var s=new CurrentRmtmObservationSource(CurrentRmtmObservation.Kind.TITLE_PHASE,true,true,Optional.of(new CurrentRmtmObservationSource.TitlePhase(phase,physical,false,true,true,true)),Optional.empty(),Optional.empty(),Optional.empty());
        return new CurrentRmtmObservationResult(CurrentRmtmObservation.Action.QUERY_TITLE_PHASE,CurrentRmtmObservationResult.Status.AVAILABLE,false,false,false,true,O,T,Z,Optional.of(core(day,actor)),Optional.of(owner(1,5)),Optional.of(s),Optional.empty());
    }
    private static CurrentRmtmObservationResult withPhaseHeir(CurrentRmtmObservationResult original,Optional<CurrentRmtmTitleQuerySource.CharacterRef> heir){
        var s=original.source().orElseThrow();var p=s.titlePhase().orElseThrow();var old=p.physical();
        var physical=new CurrentRmtmTitleQuerySource(old.actorId(),old.fullTitleId(),old.holder(),heir,old.nativeLawCount(),old.physicalOwnLaws(),heir.isEmpty()?0:1,old.sampledTwice());
        var phase=new CurrentRmtmObservationSource.TitlePhase(p.phase(),physical,p.scriptOwnSingleHeir(),p.holderRealmSingleHeir(),p.witnessGuardBound(),p.witnessSampledTwice());
        var source=new CurrentRmtmObservationSource(s.kind(),s.caseBound(),s.sampledTwice(),Optional.of(phase),s.council(),s.budget(),s.offer());
        return new CurrentRmtmObservationResult(original.action(),original.status(),original.effectAttempted(),original.nativeReturned(),original.nativeHandled(),original.cleanupKnown(),original.providerGeneration(),original.querySequence(),original.claimSequence(),original.factsBefore(),original.owner(),Optional.of(source),original.unavailableReason());
    }
    private static CurrentRmtmObservationSource.Council council(int owner,int taskOffset,long lastIncumbent){
        var rows=new java.util.ArrayList<CurrentRmtmObservationSource.Seat>();for(int i=0;i<9;i++)rows.add(new CurrentRmtmObservationSource.Seat(CurrentRmtmObservationSource.COUNCIL_KEYS.get(i),taskOffset+i,
                Optional.of(i==8?lastIncumbent:1000L+i),Optional.of(true)));return new CurrentRmtmObservationSource.Council(owner,9,true,true,rows);
    }

    @Test void fourModesHaveStrictTwoOrActualBoundedOriginalAndThresholdSubmissionBudgets() throws IOException {
        for(String mode:List.of("current_rmtm_query_role","current_rmtm_query_decision")){
            var c=config(mode);assertEquals(6,c.size());assertEquals(2,NativeOwnerSnapshotMain268.currentRmtmConfig(c).submissions());
            assertTrue(NativeOwnerSnapshotMain268.currentRmtmConfig(c).queryOnly());assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_RMTM_REMAINING,NativeOwnerSnapshotMain268.observationMode(c));
        }
        assertEquals(594,NativeOwnerSnapshotMain268.currentRmtmConfig(config("current_rmtm_threshold_50_51_once")).submissions());
        assertEquals(1106,NativeOwnerSnapshotMain268.currentRmtmConfig(config("current_rmtm_threshold_50_51_once").put("maximum_status_polls",256)).submissions());
        var original=NativeOwnerSnapshotMain268.currentRmtmConfig(config("current_rmtm_original_case_once"));assertFalse(original.queryOnly());
        assertEquals(1301,original.submissions());assertEquals(2325,NativeOwnerSnapshotMain268.currentRmtmConfig(config("current_rmtm_original_case_once").put("maximum_status_polls",256)).submissions());
    }
    @Test void thresholdPrestateRequiresActualD4SongEpochZeroAndOriginalStart() throws IOException {
        var d4=core(4,SONG);var stopped=source(4,SONG,SUCCESSOR,true,false);var valid=role(stopped,d4);
        assertFalse(stopped.advanceAdmissible());assertFalse(stopped.confirmAdmissible());assertTrue(stopped.pending().isEmpty());
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentRmtmThresholdPrestate(valid,d4,SONG,START));
        // A still-readable advance permission is DATA here, not an additional UI prerequisite or a required false value.
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentRmtmThresholdPrestate(role(source(4,SONG,SUCCESSOR,true,true),d4),d4,SONG,START));
        for(int day:List.of(0,3,5)){
            var before=core(day,SONG);var actual=role(source(day,SONG,SUCCESSOR,true,false),before);
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmThresholdPrestate(actual,before,SONG,START));
        }
        var foreignCore=core(4,SUCCESSOR);var foreign=role(source(4,SUCCESSOR,SONG,true,false),foreignCore);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmThresholdPrestate(foreign,foreignCore,SONG,START));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmThresholdPrestate(valid,d4,SONG,START+24));
        for(String field:List.of("case_start_captured","runtime_ready","predecessor_resolved","native_shown")){
            var changed=stopped.encode();changed.put(field,false);var actual=role(CurrentRmtmActorTransitionSource.decode(changed),d4);
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmThresholdPrestate(actual,d4,SONG,START));
        }
        var noDefinition=stopped.encode();noDefinition.put("definition_found",false).putNull("native_shown");
        var undefined=role(CurrentRmtmActorTransitionSource.decode(noDefinition),d4);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmThresholdPrestate(undefined,d4,SONG,START));
        var wrongSourceClock=role(source(3,SONG,SUCCESSOR,true,false),d4);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmThresholdPrestate(wrongSourceClock,d4,SONG,START));
        var nextFrontier=new CurrentRmtmActorTransitionSource(CurrentRmtmActorTransitionSource.Role.SUCCESSOR,true,Optional.of(true),O,
                Optional.of(SONG),Optional.of(SUCCESSOR),Optional.empty(),4,14,START,true,Optional.empty(),true,true,false,false);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmThresholdPrestate(role(nextFrontier,d4),d4,SONG,START));
        var pending=new CurrentRmtmActorTransitionSource.Pending("rmtm-other-pending",BigInteger.TEN,O,MAX,SONG,SUCCESSOR,START+72,START+96,1,true,true,true);
        var unresolved=new CurrentRmtmActorTransitionSource(CurrentRmtmActorTransitionSource.Role.SUCCESSOR,true,Optional.of(true),Z,
                Optional.of(SONG),Optional.of(SUCCESSOR),Optional.of(pending),4,14,START,true,Optional.empty(),true,true,false,false);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmThresholdPrestate(role(unresolved,d4),d4,SONG,START));
        // Four observed days and role do not fabricate the original script checkpoint or actual decision Can.
    }
    @Test void thresholdD4UiBoundaryDoesNotGrantAdvanceOrConfirmEpoch() throws IOException {
        var d4=core(4,SONG);var actual=role(source(4,SONG,SUCCESSOR,true,false),d4);
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentRmtmThresholdPrestate(actual,d4,SONG,START));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmPositiveRole(actual,d4,
                CurrentRmtmActorTransitionSource.Role.SONG,Z,SONG,-1,false,4,START));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmPositiveRole(actual,d4,
                CurrentRmtmActorTransitionSource.Role.SONG,Z,SONG,-1,true,4,START));
    }

    @Test void CallerSelectorsBorrowedFieldsMalformedOwnerAndUnboundedPollingAreRejected() throws IOException {
        for(String key:List.of("actor","title_id","days","maximum_natural_days","phase","epoch","operation_id","decision_key","event_role","instance_id","claim_sequence","allow_actor_change","checkpoint_archive_path","status_poll_interval_ms"))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRmtmConfig(config("current_rmtm_original_case_once").put(key,1)));
        for(String key:List.of("maximum_status_polls","status_poll_delay_ms")){
            var missing=config("current_rmtm_original_case_once");missing.remove(key);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRmtmConfig(missing));
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRmtmConfig(config("current_rmtm_query_role").put(key,1)));
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRmtmConfig(config("current_rmtm_original_case_once").put(key,true)));
        }
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRmtmConfig(config("current_rmtm_original_case_once").put("maximum_status_polls",257)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRmtmConfig(config("current_rmtm_original_case_once").put("status_poll_delay_ms",1001)));
        var bad=config("current_rmtm_query_role");((ObjectNode)bad.get("owner_descriptor")).put("bytes",true);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRmtmConfig(bad));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRmtmConfig(config("current_rmtm_query_role").put("schema","xar.native-owner-snapshot-config/v45")));
    }
    @Test void actualSongZeroAndNegativePackedActorsAndNegativeDatesRemainData() throws IOException {
        for(int actor:List.of(0,-2)){
            var s=source(0,actor,SUCCESSOR,true,true);var p=core(0,actor);
            assertEquals(s,NativeOwnerSnapshotMain268.requireCurrentRmtmPositiveRole(role(s,p),p,CurrentRmtmActorTransitionSource.Role.SONG,Z,actor,-1,false,0,START));
        }
    }
    @Test void falseShownIsReadableDataAndNullableExecuteIdentityDoesNotReplacePendingCustody() throws IOException {
        var hidden=source(0,SONG,SUCCESSOR,false,false);var q=role(hidden,core(0,SONG));
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentRmtmRole(q,core(0,SONG)));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmPositiveRole(q,core(0,SONG),CurrentRmtmActorTransitionSource.Role.SONG,Z,SONG,-1,false,0,START));
        var p=new CurrentRmtmActorTransitionSource.Pending("rmtm-op",BigInteger.TEN,O,MAX,SONG,SUCCESSOR,START+96,START+120,1,true,true,true);
        var after=new CurrentRmtmActorTransitionSource(CurrentRmtmActorTransitionSource.Role.SUCCESSOR,true,Optional.of(true),Z,Optional.of(SONG),Optional.of(SUCCESSOR),Optional.of(p),5,14,START,true,Optional.empty(),true,true,false,true);
        assertEquals(after,NativeOwnerSnapshotMain268.requireCurrentRmtmPositiveRole(role(after,core(5,SUCCESSOR)),core(5,SUCCESSOR),CurrentRmtmActorTransitionSource.Role.SUCCESSOR,Z,SONG,SUCCESSOR,true,5,START));
        assertTrue(after.executeTimeIdentityConfirmed().isEmpty());
    }
    @Test void fourteenExactNaturalDaysUseOnlyD5PendingAndKeepEpochSeparateFromDayCount() throws IOException {
        for(int day=1;day<=14;day++){
            var f=terminal(day);var before=f.factsBefore().orElseThrow();int actualDay=day;
            assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentRmtmDayTerminal(f,before,"rmtm-op",before.dateRaw()+24,actualDay));
            assertEquals(day==5,f.progress().orElseThrow().transitionPending());assertEquals(day<=5?Z:O,f.actorEpoch());
        }
    }
    @Test void wrongOperationTargetDayAndActorSentinelCannotBecomeCompletedDay() throws IOException {
        var f=terminal(5);var before=f.factsBefore().orElseThrow();
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmDayTerminal(f,before,"other-op",before.dateRaw()+24,5));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmDayTerminal(f,before,"rmtm-op",before.dateRaw()+48,5));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmDayTerminal(f,before,"rmtm-op",before.dateRaw()+24,6));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmDayTerminal(terminal(14),core(13,SUCCESSOR),"rmtm-op",core(14,SUCCESSOR).dateRaw(),15));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.currentRmtmAfter(before,before.dateRaw()+24,-1));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.currentRmtmAfter(before,before.dateRaw()+48,SUCCESSOR));
    }
    @Test void physicalLawAndUsesOnlyExactTwoOriginalFormsAndRejectsConflicts() throws IOException {
        var empty=physical(SONG,0xffff_fffeL,List.of());
        assertEquals("realm_baseline",NativeOwnerSnapshotMain268.currentRmtmPhysicalLawForm(empty,false,true));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.currentRmtmPhysicalLawForm(empty,true,true));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.currentRmtmPhysicalLawForm(empty,false,false));
        var own=physical(SONG,0xffff_fffeL,List.of(new CurrentRmtmTitleQuerySource.Law(0,"single_heir_succession_law")));
        assertEquals("own_override",NativeOwnerSnapshotMain268.currentRmtmPhysicalLawForm(own,true,false));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.currentRmtmPhysicalLawForm(own,false,true));
        var conflict=physical(SONG,0xffff_fffeL,List.of(new CurrentRmtmTitleQuerySource.Law(0,"single_heir_succession_law"),new CurrentRmtmTitleQuerySource.Law(1,"other_law")));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.currentRmtmPhysicalLawForm(conflict,true,true));
        var d3=phase(CurrentRmtmObservation.Phase.D3,3,SONG,100,SUCCESSOR);var pre=phase(CurrentRmtmObservation.Phase.PREDEATH,4,SONG,100,SUCCESSOR);
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentRmtmTitlePhases(d3,pre,phase(CurrentRmtmObservation.Phase.POSTDEATH,7,SUCCESSOR,100,0)));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmTitlePhases(d3,pre,phase(CurrentRmtmObservation.Phase.POSTDEATH,7,SUCCESSOR,101,0)));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmTitlePhases(d3,phase(CurrentRmtmObservation.Phase.PREDEATH,4,SONG,100,43),phase(CurrentRmtmObservation.Phase.POSTDEATH,7,SUCCESSOR,100,0)));
        var postEmpty=withPhaseHeir(phase(CurrentRmtmObservation.Phase.POSTDEATH,7,SUCCESSOR,100,0),Optional.empty());
        assertEquals(0,postEmpty.source().orElseThrow().titlePhase().orElseThrow().physical().engineSuccessorCount());
        assertTrue(postEmpty.source().orElseThrow().titlePhase().orElseThrow().physical().physicalOwnLaws().isEmpty());
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentRmtmTitlePhases(d3,pre,postEmpty));
        var preAliveFalse=withPhaseHeir(pre,Optional.of(new CurrentRmtmTitleQuerySource.CharacterRef(SUCCESSOR,false)));
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentRmtmTitlePhases(d3,preAliveFalse,postEmpty));
        assertFalse(preAliveFalse.source().orElseThrow().titlePhase().orElseThrow().physical().engineCurrentHeir().orElseThrow().alive());
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmTitlePhases(withPhaseHeir(d3,Optional.empty()),pre,postEmpty));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmTitlePhases(d3,withPhaseHeir(pre,Optional.empty()),postEmpty));
        var self=Optional.of(new CurrentRmtmTitleQuerySource.CharacterRef(Integer.toUnsignedLong(SONG),true));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmTitlePhases(withPhaseHeir(d3,self),pre,postEmpty));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmTitlePhases(d3,withPhaseHeir(pre,self),postEmpty));
    }
    @Test void fullPackedPhysicalHolderDoesNotDropGenerationOrSignExtendSignedActor() throws IOException {
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentRmtmPhysicalHolder(physical(-2,0xffff_fffeL,List.of()),core(0,-2)));
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentRmtmPhysicalHolder(physical(0,0,List.of()),core(0,0)));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmPhysicalHolder(physical(-2,0x00ff_fffeL,List.of()),core(0,-2)));
        assertThrows(IllegalArgumentException.class,()->new CurrentRmtmTitleQuerySource.CharacterRef(0xffff_ffffL,true));
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentRmtmCouncilRetained(council(SONG,1,1008),council(SUCCESSOR,100,1008)));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmCouncilRetained(council(SONG,1,1008),council(SUCCESSOR,100,0x0100_03f0L)));
    }
    @Test void falseToggleAndEmptyOrNulTooltipRemainDataWithIndependentTickets() throws IOException {
        var before=core(0,SONG);var q=query(list(),before);
        for(boolean handled:List.of(false,true)){
            var f=new CurrentRmtmDecisionResult(CurrentRmtmDecision.Action.OPEN_LIST,CurrentRmtmDecisionResult.Status.NAVIGATION_DISPATCHED,true,true,handled,true,O,T,BigInteger.TEN,
                    Optional.of(before),Optional.of(owner(1,900)),q.source(),Optional.empty(),Optional.empty());
            assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentRmtmDecisionDispatch(f,q,before,O,CurrentRmtmDecision.Action.OPEN_LIST,CurrentRmtmDecision.DecisionKey.RESTORE));
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmDecisionDispatch(f,q,before,T,CurrentRmtmDecision.Action.OPEN_LIST,CurrentRmtmDecision.DecisionKey.RESTORE));
        }
        for(String text:List.of("","\u0000#weak actual why\u0015")){
            var s=NativeOwnerSnapshotMain268.requireCurrentRmtmDecisionQuery(query(detail(false,text),before),before,O);
            assertEquals(text,s.confirmTooltip().orElseThrow());assertFalse(s.nativeCanConfirm().orElseThrow());assertFalse(s.confirmAdmissible());
        }
        var budget=new CurrentRmtmObservationSource.Budget(false,false,false,false,Optional.empty(),Optional.empty(),Optional.empty(),true,false,"my_realm_player",true);
        var b=new CurrentRmtmObservationSource(CurrentRmtmObservation.Kind.BUDGET,true,true,Optional.empty(),Optional.empty(),Optional.of(budget),Optional.empty());
        var bq=new CurrentRmtmObservationResult(CurrentRmtmObservation.Action.QUERY_BUDGET,CurrentRmtmObservationResult.Status.AVAILABLE,false,false,false,true,O,T,Z,Optional.of(before),Optional.of(owner(1,5)),Optional.of(b),Optional.empty());
        assertEquals(b,NativeOwnerSnapshotMain268.requireCurrentRmtmObservationQuery(bq,CurrentRmtmObservation.Action.QUERY_BUDGET,before,O));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmObservationQuery(bq,CurrentRmtmObservation.Action.QUERY_OFFER,before,O));
    }
    @Test void fixedEventChannelAndWholeBeforeTextCannotBeBorrowedAcrossInstances() throws IOException {
        for(var action:List.of(CurrentRmtmEvent.Action.QUERY_SUMMARY,CurrentRmtmEvent.Action.QUERY_CHAOS)){
            var before=core(0,SONG);var s=new CurrentRmtmEventSource(new CurrentLydSource.Events(true,1,List.of(event(9,SONG,action,"actual title"))),Optional.of(9),true,true,true);var q=eventQuery(action,s,before);
            var f=new CurrentRmtmEventResult(action.ackAction(),CurrentRmtmEventResult.Status.SELECTION_DISPATCHED,true,true,true,O,T,BigInteger.TEN,Optional.of(before),Optional.of(owner(1,900)),Optional.of(s),Optional.empty(),Optional.of(9));
            assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentRmtmEventDispatch(f,q,before,O,9));assertFalse(f.eventClosed());
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmEventDispatch(f,q,before,O,10));
            var changed=new CurrentRmtmEventSource(new CurrentLydSource.Events(true,1,List.of(event(9,SONG,action,"same instance changed full title"))),Optional.of(9),true,true,true);
            var changedAck=new CurrentRmtmEventResult(action.ackAction(),CurrentRmtmEventResult.Status.SELECTION_DISPATCHED,true,true,true,O,T,BigInteger.TEN,Optional.of(before),Optional.of(owner(1,900)),Optional.of(changed),Optional.empty(),Optional.of(9));
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmEventDispatch(changedAck,q,before,O,9));
        }
    }
}
