package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.CurrentLetterResult;
import org.xar.ck3.control.nativebridge.CurrentLydSource;
import org.xar.ck3.control.nativebridge.CurrentStockBookmark1070;
import org.xar.ck3.control.nativebridge.CurrentStockBookmark1070Source;
import org.xar.ck3.control.nativebridge.CurrentStockBookmark1070Result;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Pure DATA/config guards, never Native packets or runtime/ABI permission. */
final class NativeOwnerCurrentStockBookmark1070SelectionTest {
    private static ObjectNode config(boolean choose){
        var c=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v44").put("mode",choose?"current_stock_bookmark1070_choose_c":"current_stock_bookmark1070_query")
                .put("overall_timeout_seconds",120).put("read_timeout_seconds",20).put("maximum_frames_per_operation",128);
        c.putObject("owner_descriptor").put("path","D:/bookmark-DATA/owner.json").put("bytes",1).put("sha256","0".repeat(64));return c;
    }
    private static CoreFrame.Prefix prefix(int actor){return new CoreFrame.Prefix(53144328,2,true,0,true,true,actor,true);}
    private static CurrentLetterResult.OwnerWitness owner(long connection,long ticket){return new CurrentLetterResult.OwnerWitness(BigInteger.valueOf(connection),BigInteger.valueOf(ticket),BigInteger.valueOf(ticket+1),7);}
    private static CurrentLydSource.EventRow event(int id,int actor,String definition,boolean canC,boolean canOthers){
        var options=List.of(new CurrentLydSource.EventOption(2,canC,"actual c",canC?"":"actual disabled c",Optional.empty(),Optional.empty()),
                new CurrentLydSource.EventOption(0,canOthers,"actual a","",Optional.empty(),Optional.empty()),
                new CurrentLydSource.EventOption(1,canOthers,"actual b","",Optional.empty(),Optional.empty()));
        return new CurrentLydSource.EventRow(id,actor,3,definition," #P raw opening#!\u0015\n", "actual description",true,true,true,options);
    }
    private static CurrentLydSource.Events census(List<CurrentLydSource.EventRow> rows){return new CurrentLydSource.Events(true,rows.size(),rows);}
    private static CurrentStockBookmark1070Source bound(int actor,boolean canC,boolean canOthers){return new CurrentStockBookmark1070Source(census(List.of(event(1,actor,"bookmark.1070",canC,canOthers))),Optional.of(1),canC,true);}
    private static CurrentStockBookmark1070Source observed(List<CurrentLydSource.EventRow> rows){return new CurrentStockBookmark1070Source(census(rows),Optional.empty(),false,true);}
    private static CurrentStockBookmark1070Result query(CurrentStockBookmark1070Source source,int actor,long connection,long ticket){return new CurrentStockBookmark1070Result(
            CurrentStockBookmark1070.Action.QUERY,CurrentStockBookmark1070Result.Status.AVAILABLE,false,false,true,BigInteger.ONE,BigInteger.TWO,BigInteger.ZERO,
            Optional.of(prefix(actor)),Optional.of(owner(connection,ticket)),Optional.of(source),Optional.empty(),Optional.empty());}
    private static CurrentStockBookmark1070Result chosen(CurrentStockBookmark1070Result query,CurrentStockBookmark1070Source source,long connection){return new CurrentStockBookmark1070Result(
            CurrentStockBookmark1070.Action.SELECT_C,CurrentStockBookmark1070Result.Status.SELECTION_DISPATCHED,true,true,true,query.providerGeneration(),query.querySequence(),BigInteger.TEN,
            query.factsBefore(),Optional.of(owner(connection,900)),Optional.of(source),Optional.empty(),Optional.of(1));}

    @Test void ExactlyTwoCommonSixModesHaveTwoOrFiveSubmissions(){
        assertEquals(6,config(false).size());assertEquals(6,config(true).size());
        assertFalse(NativeOwnerSnapshotMain268.currentStockBookmark1070Config(config(false)).chooseC());
        assertTrue(NativeOwnerSnapshotMain268.currentStockBookmark1070Config(config(true)).chooseC());
        assertEquals(2,NativeOwnerSnapshotMain268.currentStockBookmark1070Config(config(false)).submissions());
        assertEquals(5,NativeOwnerSnapshotMain268.currentStockBookmark1070Config(config(true)).submissions());
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_STOCK_BOOKMARK1070,NativeOwnerSnapshotMain268.observationMode(config(true)));
        for(String mode:List.of("select_c","current_stock_bookmark1070_choose_c ","current_stock_bookmark1070_choose_C","current_lyd_choose_known_event_option",""))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config(true).put("mode",mode)));
    }
    @Test void MandatoryOwnerPinAndFiniteNumbersKeepActualJsonTypes(){
        for(String key:List.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation")){
            var c=config(false);c.remove(key);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentStockBookmark1070Config(c));
        }
        var bad=config(false);((ObjectNode)bad.get("owner_descriptor")).put("bytes",true);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentStockBookmark1070Config(bad));
        for(String key:List.of("overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation")){
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentStockBookmark1070Config(config(false).put(key,0)));
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentStockBookmark1070Config(config(false).put(key,"1")));
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentStockBookmark1070Config(config(false).put(key,true)));
        }
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentStockBookmark1070Config(config(false).put("read_timeout_seconds",61)));
    }
    @Test void NoCallerEventKeyIndexInstancePermissionOrOldModeBorrowing(){
        for(String key:List.of("event_key","event_role","option_key","option_index","instance_id","actor","text","expected_source_rite_id","provider_generation","query_sequence","claim_sequence","choice_token","native_can_select","action","phase","maximum_status_polls","checkpoint_archive_path")){
            var c=config(true);c.put(key,"borrowed");assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentStockBookmark1070Config(c));
        }
        for(String old:List.of("v37","v41","v42","v43"))assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config(true).put("schema","xar.native-owner-snapshot-config/"+old)));
    }
    @Test void CurrentPausedLivingCoreRetainsZeroAndNegativePackedActor()throws IOException{
        for(int actor:new int[]{0,-2,Integer.MIN_VALUE,Integer.MAX_VALUE})assertEquals(prefix(actor),NativeOwnerSnapshotMain268.requireCurrentStockBookmark1070Core(new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,prefix(actor))));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentStockBookmark1070Core(new CoreFrame.Partial(ExactCk3Build.CK3_12004,prefix(36423))));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentStockBookmark1070Core(new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,new CoreFrame.Prefix(53144328,2,false,0,true,true,36423,true))));
    }

    @Test void CompleteEmptyForeignCanFalseAndMultipleAreReadonlyAvailableData()throws IOException{
        for(var source:List.of(observed(List.of()),observed(List.of(event(1,36423,"other_actual.event",true,true))),bound(36423,false,true),
                observed(List.of(event(1,36423,"bookmark.1070",true,true),event(2,36423,"bookmark.1070",true,true))))){
            var q=query(source,36423,2,11);assertSame(source,NativeOwnerSnapshotMain268.requireCurrentStockBookmark1070QueryFrame(q,prefix(36423),BigInteger.TWO));
            assertEquals(BigInteger.ZERO,q.claimSequence());assertFalse(q.effectAttempted());assertFalse(q.nativeReturned());assertFalse(q.nativeHandled());
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentStockBookmark1070C(source,prefix(36423)));
        }
    }
    @Test void OnlyActualAuthoredCIsChosenIndependentOfArrayOrderAndOtherCanValues()throws IOException{
        for(int actor:new int[]{36423,0,-2}){
            var source=bound(actor,true,false);assertEquals(2,source.eventCensus().events().get(0).options().get(0).authoredOptionIndex());
            assertEquals(1,NativeOwnerSnapshotMain268.requireCurrentStockBookmark1070C(source,prefix(actor)));
            assertFalse(source.eventCensus().events().get(0).options().get(1).nativeCanSelect());
            assertFalse(source.eventCensus().events().get(0).options().get(2).nativeCanSelect());
        }
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentStockBookmark1070C(bound(40180,true,true),prefix(36423)));
        assertThrows(IllegalArgumentException.class,()->new CurrentStockBookmark1070Source(census(List.of(event(1,36423,"bookmark.1070",true,true))),Optional.of(1),true,false));
        assertThrows(IllegalArgumentException.class,()->new CurrentLydSource.Events(false,0,List.of()));
        assertThrows(IllegalArgumentException.class,()->census(List.of(event(1,36423,"bookmark.1070",true,true),event(1,36423,"bookmark.1070",true,true))));
    }
    @Test void OriginalQueryRequiresExactCoreRecipientAndActualConnection()throws IOException{
        var source=bound(36423,true,true);var q=query(source,36423,2,11);
        assertSame(source,NativeOwnerSnapshotMain268.requireCurrentStockBookmark1070QueryFrame(q,prefix(36423),BigInteger.TWO));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentStockBookmark1070QueryFrame(q,prefix(40180),BigInteger.TWO));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentStockBookmark1070QueryFrame(q,new CoreFrame.Prefix(53144352,2,true,0,true,true,36423,true),BigInteger.TWO));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentStockBookmark1070QueryFrame(q,prefix(36423),BigInteger.valueOf(3)));
        var unavailable=new CurrentStockBookmark1070Result(CurrentStockBookmark1070.Action.QUERY,CurrentStockBookmark1070Result.Status.UNAVAILABLE,false,false,true,
                BigInteger.ZERO,BigInteger.ZERO,BigInteger.ZERO,Optional.empty(),Optional.empty(),Optional.empty(),Optional.of("actual original refusal"),Optional.empty());
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentStockBookmark1070QueryFrame(unavailable,prefix(36423),BigInteger.TWO));
    }
    @Test void ThisVoidAckKeepsWholeBeforeSourceCoreLeaseAndMayUseNewTicket()throws IOException{
        var source=bound(36423,true,true);var q=query(source,36423,2,11);var ack=chosen(q,source,2);
        NativeOwnerSnapshotMain268.requireCurrentStockBookmark1070DispatchFrame(ack,q,1);
        assertTrue(ack.effectAttempted());assertTrue(ack.nativeReturned());assertFalse(ack.nativeHandled());assertFalse(ack.eventClosed());assertFalse(ack.newDateObserved());assertFalse(ack.physicalSaveConfirmed());
        assertNotEquals(q.owner().orElseThrow().ticketSequence(),ack.owner().orElseThrow().ticketSequence());
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentStockBookmark1070DispatchFrame(chosen(q,source,3),q,1));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentStockBookmark1070DispatchFrame(ack,q,2));
        var e=source.eventCensus().events().get(0);var changedRow=new CurrentLydSource.EventRow(e.instanceId(),e.recipientCharacterId(),e.authoredOptionCount(),e.definitionKey(),e.opening()+"changed",e.description(),e.namedRootBound(),e.windowVisible(),e.windowEnabled(),e.options());
        var changed=new CurrentStockBookmark1070Source(census(List.of(changedRow)),Optional.of(1),true,true);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentStockBookmark1070DispatchFrame(chosen(q,changed,2),q,1));
        var consumed=new CurrentStockBookmark1070Result(CurrentStockBookmark1070.Action.SELECT_C,CurrentStockBookmark1070Result.Status.CLAIM_CONSUMED,false,false,true,
                q.providerGeneration(),q.querySequence(),BigInteger.ZERO,q.factsBefore(),Optional.of(owner(2,1000)),Optional.of(source),Optional.of("actual known refusal"),Optional.of(1));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentStockBookmark1070DispatchFrame(consumed,q,1));
    }
    @Test void AbsenceUsesOriginalInstanceInCompleteCensusRatherThanNewFixedNull()throws IOException{
        var stillPresent=observed(List.of(event(1,36423,"other_actual.event",true,true)));
        assertTrue(stillPresent.fixedInstanceId().isEmpty());assertFalse(NativeOwnerSnapshotMain268.currentStockBookmark1070InstanceAbsent(stillPresent,1));
        assertTrue(NativeOwnerSnapshotMain268.currentStockBookmark1070InstanceAbsent(observed(List.of()),1));
        assertTrue(NativeOwnerSnapshotMain268.currentStockBookmark1070InstanceAbsent(observed(List.of(event(2,36423,"other_actual.event",true,true))),1));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.currentStockBookmark1070InstanceAbsent(stillPresent,0));
    }

    @Test void SummaryDoesNotInferEventClosureOrDateGateFromDispatchOrAbsence(){
        for(boolean choose:List.of(false,true)){
            var r=StrictJson.object();NativeOwnerSnapshotMain268.initializeCurrentStockBookmark1070Result(r,NativeOwnerSnapshotMain268.currentStockBookmark1070Config(config(choose)),"DATA-machine");
            for(String key:List.of("query_available","choice_callback_dispatched","native_returned","native_handled","independent_after_census_observed","event_closed","date_gate_cleared","new_date_observed","physical_save_confirmed"))assertFalse(r.get(key).booleanValue());
            for(String key:List.of("read_calls","query_calls","choice_calls","date_calls","save_calls"))assertEquals(0,r.get(key).intValue());
            assertTrue(r.get("original_instance_id").isNull());assertTrue(r.get("original_instance_absent").isNull());assertEquals("NOT_OBSERVED",r.get("original_instance_observation").textValue());
        }
    }
}
