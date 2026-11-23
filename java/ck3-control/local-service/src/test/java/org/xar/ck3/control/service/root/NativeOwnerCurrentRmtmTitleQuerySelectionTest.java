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
import org.xar.ck3.control.nativebridge.CurrentRmtmTitleQuerySource;
import org.xar.ck3.control.nativebridge.CurrentRmtmTitleQueryResult;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Unexecuted DATA/consumer draft. No Native frames, real Title source, phase or RMTM business proof. */
final class NativeOwnerCurrentRmtmTitleQuerySelectionTest {
    private static ObjectNode config(){var c=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v46").put("mode","current_rmtm_primary_title_query")
            .put("overall_timeout_seconds",120).put("read_timeout_seconds",20).put("maximum_frames_per_operation",128);
        c.putObject("owner_descriptor").put("path","D:/RMTM-DATA/owner.json").put("bytes",1).put("sha256","0".repeat(64));return c;}
    private static CoreFrame.Prefix core(int date,int actor){return new CoreFrame.Prefix(date,2,true,0,true,true,actor,true);}
    private static CurrentRmtmTitleQuerySource empty(int actor,long title){return new CurrentRmtmTitleQuerySource(actor,title,Optional.empty(),Optional.empty(),0,List.of(),0,true);}
    private static CurrentRmtmTitleQueryResult available(CurrentRmtmTitleQuerySource s,int date,long connection){return new CurrentRmtmTitleQueryResult(
            CurrentRmtmTitleQueryResult.Status.AVAILABLE,true,BigInteger.ONE,BigInteger.TWO,Optional.of(core(date,s.actorId())),
            Optional.of(new CurrentLetterResult.OwnerWitness(BigInteger.valueOf(connection),BigInteger.valueOf(3),BigInteger.valueOf(4),7)),Optional.of(s),Optional.empty());}
    @Test void onlyCommonSixAndExplicitV46ModeWithTwoReadonlySubmissions(){
        assertEquals(6,config().size());assertEquals(2,NativeOwnerSnapshotMain268.currentRmtmTitleQueryConfig(config()).submissions());
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_RMTM_TITLE_QUERY,NativeOwnerSnapshotMain268.observationMode(config()));
        for(String mode:List.of("query_primary_title","current_rmtm_primary_title_query ","current_ccc_query","current_rmtm_query",""))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config().put("mode",mode)));
        for(String schema:List.of("xar.native-owner-snapshot-config/v45","xar.native-owner-snapshot-config/v43"))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config().put("schema",schema)));
    }
    @Test void noCallerTitleSelectorPhaseLawOrBorrowedEpochLease(){
        for(String key:List.of("title_id","expected_full_title_id","expected_source_rite_id","role","phase","event","index","callback","provider_generation","query_sequence","CCC_epoch","actor_epoch","law_key","expected_core","date_calls","save_calls")){
            var c=config();c.put(key,"borrowed");assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRmtmTitleQueryConfig(c));
        }
        for(String key:List.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation")){
            var c=config();c.remove(key);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRmtmTitleQueryConfig(c));
        }
    }
    @Test void boundedTimeoutAndExactIntegerConfigRetainOldContracts(){
        assertEquals(2,NativeOwnerSnapshotMain268.currentRmtmTitleQueryConfig(config().put("overall_timeout_seconds",600).put("read_timeout_seconds",60).put("maximum_frames_per_operation",65536)).submissions());
        for(String key:List.of("overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation")){
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRmtmTitleQueryConfig(config().put(key,0)));
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRmtmTitleQueryConfig(config().put(key,"1")));
        }
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRmtmTitleQueryConfig(config().put("overall_timeout_seconds",601)));
    }
    @Test void dateZeroNegativeAndSignedActorRemainGuardsOnly()throws IOException{
        for(int date:new int[]{Integer.MIN_VALUE,-24,0,Integer.MAX_VALUE})for(int actor:new int[]{0,-2,Integer.MIN_VALUE,Integer.MAX_VALUE}){
            var p=core(date,actor);var s=empty(actor,0xffff_fffeL);var q=available(s,date,2);
            assertSame(s,NativeOwnerSnapshotMain268.requireCurrentRmtmTitleQueryFrame(q,p,BigInteger.TWO));
            assertEquals(p,NativeOwnerSnapshotMain268.requireCurrentRiteCreateCore(new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,p)));
        }
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRiteCreateCore(new CoreFrame.Partial(ExactCk3Build.CK3_12004,core(0,0))));
    }
    @Test void fullCoreAndSameConnectionMustMatchPrivateRead()throws IOException{
        var s=empty(36423,47);var q=available(s,0,2);assertSame(s,NativeOwnerSnapshotMain268.requireCurrentRmtmTitleQueryFrame(q,core(0,36423),BigInteger.TWO));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmTitleQueryFrame(q,core(24,36423),BigInteger.TWO));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmTitleQueryFrame(q,core(0,40180),BigInteger.TWO));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmTitleQueryFrame(q,core(0,36423),BigInteger.valueOf(3)));
    }
    @Test void emptyOwnArrayNullHolderAndDeadHeirAreReadDataNotPhaseEvidence()throws IOException{
        var s=empty(36423,0);assertTrue(NativeOwnerSnapshotMain268.requireCurrentRmtmTitleQueryFrame(available(s,0,2),core(0,36423),BigInteger.TWO).physicalOwnLaws().isEmpty());
        var dead=new CurrentRmtmTitleQuerySource(36423,0xffff_fffeL,Optional.empty(),Optional.of(new CurrentRmtmTitleQuerySource.CharacterRef(0x8000_0000L,false)),0,List.of(),1,true);
        assertFalse(NativeOwnerSnapshotMain268.requireCurrentRmtmTitleQueryFrame(available(dead,0,2),core(0,36423),BigInteger.TWO).engineCurrentHeir().orElseThrow().alive());
        assertThrows(IllegalArgumentException.class,()->new CurrentRmtmTitleQuerySource(36423,47,Optional.empty(),Optional.empty(),0,List.of(),0,false));
    }
    @Test void knownRefusalAndUnknownCannotBecomeKnownEmptySource(){
        for(var status:List.of(CurrentRmtmTitleQueryResult.Status.UNAVAILABLE,CurrentRmtmTitleQueryResult.Status.EXPIRED,CurrentRmtmTitleQueryResult.Status.STALE_SOURCE,CurrentRmtmTitleQueryResult.Status.INDETERMINATE)){
            var q=new CurrentRmtmTitleQueryResult(status,status!=CurrentRmtmTitleQueryResult.Status.INDETERMINATE,BigInteger.ZERO,BigInteger.ZERO,Optional.empty(),Optional.empty(),Optional.empty(),Optional.of(""));
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRmtmTitleQueryFrame(q,core(0,36423),BigInteger.TWO));assertTrue(q.source().isEmpty());
        }
    }
    @Test void summaryNeverGrantsRealmEffectiveRulesExecuteTimeHeirDateOrSave(){
        var result=StrictJson.object();NativeOwnerSnapshotMain268.initializeCurrentRmtmTitleQueryResult(result,"DATA-machine");
        for(String key:List.of("source_available","effect_attempted","native_returned","native_handled","effective_law_observed","realm_law_observed","rmtm_rules_confirmed","phase_control_authorized","execute_time_heir_witness","rmtm26_business_pass","new_date_observed","physical_save_confirmed"))assertFalse(result.get(key).booleanValue());
        for(String key:List.of("read_calls","query_calls","date_calls","save_calls"))assertEquals(0,result.get(key).intValue());
        assertFalse(result.has("expected_full_title_id"));assertFalse(result.has("actor_epoch"));
    }
}
