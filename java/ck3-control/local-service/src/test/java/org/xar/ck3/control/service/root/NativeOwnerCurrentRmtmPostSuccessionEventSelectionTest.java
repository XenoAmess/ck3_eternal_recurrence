package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Self-owned Java DATA only: no private Receiver, native packet, genuine exchange or Game qualification. */
final class NativeOwnerCurrentRmtmPostSuccessionEventSelectionTest {
    private static final BigInteger Z=BigInteger.ZERO,O=BigInteger.ONE,T=BigInteger.TWO;
    private static final int START=-240,SONG=-2,ACTOR=0;
    private static CoreFrame.Prefix core(int days,int actor){return new CoreFrame.Prefix(START+24*days,3,true,1,true,true,actor,true);}
    private static CurrentLetterResult.OwnerWitness owner(int connection,int ticket){return new CurrentLetterResult.OwnerWitness(BigInteger.valueOf(connection),BigInteger.valueOf(ticket),BigInteger.valueOf(ticket+1),7);}
    private static CurrentLydSource.EventOption option(int index,boolean can,String text){return new CurrentLydSource.EventOption(index,can,text,"actual explanation DATA",Optional.empty(),Optional.empty());}
    private static CurrentLydSource.EventRow row(int instance,int actor,String definition,boolean visible,boolean enabled,List<CurrentLydSource.EventOption> options){return new CurrentLydSource.EventRow(
            instance,actor,4,definition,"actual opening","actual rich description"+(char)21+(char)0,true,visible,enabled,options);}
    private static CurrentLydSource.EventRow ordinary(int instance,int actor){return row(instance,actor,"ordinary.actual",true,true,List.of(option(3,true,"vector first"),option(0,false,"unavailable"),option(2,true,"actual minimum")));}
    private static CurrentRmtmEventSource source(CurrentLydSource.EventRow...rows){return new CurrentRmtmEventSource(new CurrentLydSource.Events(true,rows.length,List.of(rows)),Optional.empty(),true,false,true);}
    private static CurrentRmtmEventResult query(CurrentRmtmEventSource source,CoreFrame.Prefix core){return new CurrentRmtmEventResult(CurrentRmtmEvent.Action.QUERY_SUMMARY,
            CurrentRmtmEventResult.Status.AVAILABLE,false,false,true,O,T,Z,Optional.of(core),Optional.of(owner(1,5)),Optional.of(source),Optional.empty(),Optional.empty());}
    private static CurrentRmtmEventResult dispatched(CurrentRmtmEventSource source,CoreFrame.Prefix core,CurrentLetterResult.OwnerWitness owner,BigInteger provider,BigInteger sequence,int instance){return new CurrentRmtmEventResult(
            CurrentRmtmEvent.Action.CHOOSE_POST_SUCCESSION_FIRST_AVAILABLE,CurrentRmtmEventResult.Status.SELECTION_DISPATCHED,true,true,true,provider,sequence,BigInteger.TEN,
            Optional.of(core),Optional.of(owner),Optional.of(source),Optional.empty(),Optional.of(instance));}

    @Test void exactAdditionalBudgetKeepsQueriesThresholdAndStrictConfig() throws IOException {
        assertEquals(62,NativeOwnerSnapshotMain268.RMTM_POST_SUCCESSION_INSTANCE_LIMIT);
        assertEquals(189,NativeOwnerSnapshotMain268.RMTM_POST_SUCCESSION_ADDITIONAL_SUBMISSIONS);
        var c=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v47").put("mode","current_rmtm_original_case_once")
                .put("overall_timeout_seconds",600).put("read_timeout_seconds",60).put("maximum_frames_per_operation",65536).put("maximum_status_polls",128).put("status_poll_delay_ms",500);
        c.putObject("owner_descriptor").put("path","D:/rmtm-post-DATA/owner.json").put("bytes",1).put("sha256","0".repeat(64));
        assertEquals(1298,NativeOwnerSnapshotMain268.currentRmtmConfig(c).submissions());
        assertEquals(2322,NativeOwnerSnapshotMain268.currentRmtmConfig(c.deepCopy().put("maximum_status_polls",256)).submissions());
        assertEquals(594,NativeOwnerSnapshotMain268.currentRmtmConfig(c.deepCopy().put("mode","current_rmtm_threshold_50_51_once")).submissions());
        for(String forbidden:List.of("event_role","instance_id","option_index","event_key","actor_epoch","maximum_post_events"))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRmtmConfig(c.deepCopy().put(forbidden,1)));
    }
    @Test void successorBoundaryUsesExactSignedCoreAndOriginalDateNotCallerAuthority() throws IOException {
        for(int actor:List.of(0,-2))for(int day:List.of(5,6,7,14))
            assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentRmtmPostSuccessionBoundary(core(day,actor),42,actor,day,START));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmPostSuccessionBoundary(core(4,ACTOR),SONG,ACTOR,4,START));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmPostSuccessionBoundary(core(15,ACTOR),SONG,ACTOR,15,START));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmPostSuccessionBoundary(core(5,SONG),SONG,ACTOR,5,START));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmPostSuccessionBoundary(core(5,ACTOR),ACTOR,ACTOR,5,START));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmPostSuccessionBoundary(core(5,ACTOR),SONG,ACTOR,5,START+24));
        var running=new CoreFrame.Prefix(START+120,3,false,1,true,true,ACTOR,true);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmPostSuccessionBoundary(running,SONG,ACTOR,5,START));
    }
    @Test void actualEmptyCensusRemainsOnlyDataAndDoesNotNeedAnInventedChoice() throws IOException {
        var empty=source();assertTrue(NativeOwnerSnapshotMain268.currentRmtmFirstPostSuccessionChoice(empty,ACTOR).isEmpty());
        var unbound=new CurrentRmtmEventSource(empty.eventCensus(),Optional.empty(),false,false,true);
        assertTrue(NativeOwnerSnapshotMain268.currentRmtmFirstPostSuccessionChoice(unbound,ACTOR).isEmpty());
        var frame=query(empty,core(5,ACTOR));assertTrue(frame.successful());assertFalse(frame.eventClosed());assertFalse(frame.newDateObserved());assertFalse(frame.physicalSaveConfirmed());
    }
    @Test void multipleRowsUseFirstActualInstanceAndMinimumAuthoredEnabledOption() throws IOException {
        var census=source(ordinary(71,ACTOR),ordinary(72,ACTOR));
        var choice=NativeOwnerSnapshotMain268.currentRmtmFirstPostSuccessionChoice(census,ACTOR).orElseThrow();
        assertEquals(71,choice.instanceId());assertEquals(2,choice.authoredOptionIndex());
        assertFalse(census.ackAdmissible());assertTrue(census.fixedInstanceId().isEmpty());
        var sparse=source(row(73,ACTOR,"ordinary.sparse",true,true,List.of(option(3,true," "),option(1,false,"disabled"),option(0,true,""))));
        assertEquals(3,NativeOwnerSnapshotMain268.currentRmtmFirstPostSuccessionChoice(sparse,ACTOR).orElseThrow().authoredOptionIndex());
    }
    @Test void refusedOrForeignFirstRowNeverFallsBackToAnotherWindow() throws IOException {
        for(var first:List.of(ordinary(71,42),row(71,ACTOR,"ordinary.hidden",false,true,List.of(option(0,true,"choice"))),
                row(71,ACTOR,"ordinary.blocked",true,false,List.of(option(0,true,"choice"))),
                row(71,ACTOR,"ordinary.disabled",true,true,List.of(option(0,false,"disabled"))),
                row(71,ACTOR,"ordinary.empty",true,true,List.of(option(0,true,"")))))
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.currentRmtmFirstPostSuccessionChoice(source(first,ordinary(72,ACTOR)),ACTOR));
        var notBound=new CurrentRmtmEventSource(source(ordinary(71,ACTOR)).eventCensus(),Optional.empty(),false,false,true);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.currentRmtmFirstPostSuccessionChoice(notBound,ACTOR));
    }
    @Test void specializedDefinitionsAndKnownKeysAreNeverReclassifiedAsOrdinary() throws IOException {
        for(String definition:List.of("rmtm.1001","tgp_dynastic_cycle.0081","lyd.1","lyd.1000","lyd.1002","lyd.1032","ep3_laamps.0003",
                "bookmark.1070","gdp_guelph_ghibelline.0500","xqol.100","sxat.2","sxat.4","xccc.1001"))
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.currentRmtmFirstPostSuccessionChoice(source(row(71,ACTOR,definition,true,true,List.of(option(0,true,"actual choice")))),ACTOR));
        var key=new CurrentLydSource.EventOption(0,true,"actual named choice","",Optional.of("known_existing_key"),Optional.empty());
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.currentRmtmFirstPostSuccessionChoice(source(row(71,ACTOR,"ordinary.actual",true,true,List.of(key))),ACTOR));
    }
    @Test void retainedInstanceAndCommonEventCapacityCannotBeResetBetweenDays() throws IOException {
        var attempted=new HashSet<Integer>();assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentRmtmPostSuccessionCapacity(attempted,71));
        attempted.add(71);assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmPostSuccessionCapacity(attempted,71));
        for(int n=1;attempted.size()<62;n++)attempted.add(n);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmPostSuccessionCapacity(attempted,999));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmPostSuccessionCapacity(new HashSet<>(),0));
    }
    @Test void dispatchRetainsTheWholeOriginalSourceCoreAndLease() throws IOException {
        var source=source(ordinary(71,ACTOR));var core=core(5,ACTOR);var before=query(source,core);
        var result=dispatched(source,core,owner(1,9),O,T,71);
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentRmtmPostSuccessionDispatch(result,before,core,O,71));
        assertFalse(result.nativeHandled());assertFalse(result.eventClosed());assertFalse(result.newDateObserved());assertFalse(result.physicalSaveConfirmed());
        var changed=source(row(71,ACTOR,"ordinary.actual",true,true,List.of(option(0,true,"changed actual full text"))));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmPostSuccessionDispatch(dispatched(changed,core,owner(1,9),O,T,71),before,core,O,71));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmPostSuccessionDispatch(dispatched(source,core,owner(1,9),T,T,71),before,core,O,71));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmPostSuccessionDispatch(dispatched(source,core(6,ACTOR),owner(1,9),O,T,71),before,core,O,71));
    }
    @Test void independentTicketAndPumpMayChangeButConnectionAndInstanceMayNot() throws IOException {
        var source=source(ordinary(71,ACTOR),ordinary(72,ACTOR));var core=core(5,ACTOR);var before=query(source,core);
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentRmtmPostSuccessionDispatch(dispatched(source,core,owner(1,99),O,T,71),before,core,O,71));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmPostSuccessionDispatch(dispatched(source,core,owner(2,99),O,T,71),before,core,O,71));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmPostSuccessionDispatch(dispatched(source,core,owner(1,99),O,T,72),before,core,O,72));
    }
    @Test void knownRefusalAndUnknownNeverBecomeDispatchOrAfterstateCredit() throws IOException {
        var source=source(ordinary(71,ACTOR));var core=core(5,ACTOR);var before=query(source,core);
        for(var status:List.of(CurrentRmtmEventResult.Status.STALE_SOURCE,CurrentRmtmEventResult.Status.CLAIM_CONSUMED)){
            var refused=new CurrentRmtmEventResult(CurrentRmtmEvent.Action.CHOOSE_POST_SUCCESSION_FIRST_AVAILABLE,status,false,false,true,O,T,BigInteger.TEN,
                    Optional.of(core),Optional.of(owner(1,9)),Optional.of(source),Optional.of("original known refusal; no retry"),Optional.of(71));
            assertFalse(refused.successful());assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmPostSuccessionDispatch(refused,before,core,O,71));
        }
        var unknown=new CurrentRmtmEventResult(CurrentRmtmEvent.Action.CHOOSE_POST_SUCCESSION_FIRST_AVAILABLE,CurrentRmtmEventResult.Status.INDETERMINATE,false,false,false,O,T,BigInteger.TEN,
                Optional.of(core),Optional.of(owner(1,9)),Optional.empty(),Optional.of("actual completion unknown"),Optional.of(71));
        assertFalse(unknown.successful());assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmPostSuccessionDispatch(unknown,before,core,O,71));
    }
}
