package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.CurrentLetterResult;
import org.xar.ck3.control.nativebridge.CurrentLivingInventoryQuerySource;
import org.xar.ck3.control.nativebridge.CurrentLivingInventoryQueryResult;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Java DATA only, uncompiled/unexecuted Source. No native/genuine frames or private action grants. */
final class NativeOwnerCurrentLivingOriginalSelectionTest {
    private static final long TARGET=0x8000_0037L;
    private static final List<Long> MATERIALS=List.of(0L,0x1200_0038L,0x2200_0039L,0x3200_003aL);
    private static ObjectNode config(){var c=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v48").put("mode","current_living_original_case_once")
            .put("overall_timeout_seconds",300).put("read_timeout_seconds",30).put("maximum_frames_per_operation",1024);
        c.putObject("owner_descriptor").put("path","D:/living-data/owner.json").put("bytes",1).put("sha256","0".repeat(64));return c;}
    private static CoreFrame.Prefix core(int actor,int date){return new CoreFrame.Prefix(date,3,true,0,true,true,actor,true);}
    private static List<CurrentLivingInventoryQuerySource.Numeric> numbers(long level,long xp,long pending,long sequence){
        var out=new ArrayList<CurrentLivingInventoryQuerySource.Numeric>();for(long n:new long[]{level,xp,pending,sequence})out.add(new CurrentLivingInventoryQuerySource.Numeric(CurrentLivingInventoryQuerySource.NumericState.NUMERIC,1,Optional.of(Math.multiplyExact(n,100000L))));return out;
    }
    private static CurrentLivingInventoryQuerySource source(int actor,int consumed,long level,long xp,long sequence,boolean equipped){
        long owner=Integer.toUnsignedLong(actor);var artifacts=new ArrayList<CurrentLivingInventoryQuerySource.Artifact>();
        artifacts.add(new CurrentLivingInventoryQuerySource.Artifact(TARGET,owner,"sword",0,equipped,numbers(level,xp,0,sequence)));
        for(int n=consumed;n<4;n++)artifacts.add(new CurrentLivingInventoryQuerySource.Artifact(MATERIALS.get(n),owner,"sword",n,false,numbers(0,0,0,0)));
        var refs=new ArrayList<CurrentLivingInventoryQuerySource.Reference>();
        for(var role:CurrentLivingInventoryQuerySource.ReferenceRole.values()){
            if(role==CurrentLivingInventoryQuerySource.ReferenceRole.SELECTED_ARTIFACT)refs.add(new CurrentLivingInventoryQuerySource.Reference(role,CurrentLivingInventoryQuerySource.ReferenceState.ABSENT,0,Optional.empty()));
            else refs.add(new CurrentLivingInventoryQuerySource.Reference(role,CurrentLivingInventoryQuerySource.ReferenceState.ARTIFACT,36,Optional.of(role==CurrentLivingInventoryQuerySource.ReferenceRole.FIXTURE_TARGET?TARGET:MATERIALS.get(role.ordinal()-1))));
        }
        return new CurrentLivingInventoryQuerySource(owner,artifacts,List.of(new CurrentLivingInventoryQuerySource.Slot("weapon",equipped?Optional.of(TARGET):Optional.empty()),
                new CurrentLivingInventoryQuerySource.Slot("armor",Optional.empty())),Optional.of(0),refs,true,true);
    }
    private static CurrentLivingInventoryQuerySource withArtifacts(CurrentLivingInventoryQuerySource s,List<CurrentLivingInventoryQuerySource.Artifact>a){
        return new CurrentLivingInventoryQuerySource(s.actorFullId(),a,s.slots(),s.weaponSlot(),s.fixedReferences(),true,true);
    }
    private static CurrentLivingInventoryQueryResult available(CurrentLivingInventoryQuerySource s,int actor,int date,long conn){
        return new CurrentLivingInventoryQueryResult(CurrentLivingInventoryQueryResult.Status.AVAILABLE,true,BigInteger.ONE,BigInteger.TWO,Optional.of(core(actor,date)),
                Optional.of(new CurrentLetterResult.OwnerWitness(BigInteger.valueOf(conn),BigInteger.valueOf(7),BigInteger.valueOf(11),17)),Optional.of(s),Optional.empty());
    }
    @Test void strictV48CommonSixOnlyWithFiniteSubmissionUpperBound(){
        assertEquals(6,config().size());assertEquals(85,NativeOwnerSnapshotMain268.currentLivingOriginalConfig(config()).submissions());
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_LIVING_ORIGINAL,NativeOwnerSnapshotMain268.observationMode(config()));
        for(String field:List.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation")){
            var c=config();c.remove(field);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentLivingOriginalConfig(c));
        }
    }
    @Test void noCallerArtifactRoleIndexPhaseTokenOrForeignActionSchema(){
        for(String field:List.of("artifact_id","material_id","owner_id","target_character_id","decision_key","event_role","instance_id","slot","option_index","token","provider_generation","query_sequence","phase","days","save","force","maximum_status_polls")){
            var c=config().put(field,"borrowed");assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentLivingOriginalConfig(c));
        }
        for(String mode:List.of("current_living_inventory_query","current_living_original_case_once ","current_rmtm_original_case_once",""))assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentLivingOriginalConfig(config().put("mode",mode)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentLivingOriginalConfig(config().put("schema","xar.native-owner-snapshot-config/v47")));
    }
    @Test void scalarTimeoutBoundsRemainExactAndNoNewPollingFields(){
        assertEquals(85,NativeOwnerSnapshotMain268.currentLivingOriginalConfig(config().put("overall_timeout_seconds",600).put("read_timeout_seconds",60).put("maximum_frames_per_operation",65536)).submissions());
        for(String key:List.of("overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation")){
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentLivingOriginalConfig(config().put(key,0)));
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentLivingOriginalConfig(config().put(key,"1")));
        }
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentLivingOriginalConfig(config().put("overall_timeout_seconds",601)));
    }
    @Test void completeSameCoreConnectionAndSignedFullActorAreGuardsOnly()throws IOException{
        for(int actor:new int[]{0,-2,Integer.MIN_VALUE,36423}){
            var s=source(actor,0,1,92,0,false);var f=available(s,actor,0,3);
            assertSame(s,NativeOwnerSnapshotMain268.requireCurrentLivingInventoryFrame(f,core(actor,0),BigInteger.valueOf(3)));
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentLivingInventoryFrame(f,core(actor,24),BigInteger.valueOf(3)));
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentLivingInventoryFrame(f,core(actor,0),BigInteger.valueOf(4)));
        }
        NativeOwnerSnapshotMain268.requireCurrentLivingSameCore(core(36423,0),core(36423,0));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentLivingSameCore(core(36423,0),core(44132,0)));
        for(var status:List.of(CurrentLivingInventoryQueryResult.Status.UNAVAILABLE,CurrentLivingInventoryQueryResult.Status.EXPIRED,CurrentLivingInventoryQueryResult.Status.STALE_SOURCE,CurrentLivingInventoryQueryResult.Status.INDETERMINATE)){
            var refused=new CurrentLivingInventoryQueryResult(status,status!=CurrentLivingInventoryQueryResult.Status.INDETERMINATE,BigInteger.ZERO,BigInteger.ZERO,Optional.empty(),Optional.empty(),Optional.empty(),Optional.of("DATA refusal"));
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentLivingInventoryFrame(refused,core(36423,0),BigInteger.valueOf(3)));
        }
    }
    @Test void fixedActualReferencesBindFiveDistinctOwnedFullIdsIncludingZero()throws IOException{
        var s=source(36423,0,1,92,0,false);var b=NativeOwnerSnapshotMain268.currentLivingOriginalBindings(s);
        assertEquals(TARGET,b.target());assertEquals(MATERIALS,b.materials());
        var refs=new ArrayList<>(s.fixedReferences());refs.set(1,new CurrentLivingInventoryQuerySource.Reference(CurrentLivingInventoryQuerySource.ReferenceRole.FIXTURE_MATERIAL_COMMON,CurrentLivingInventoryQuerySource.ReferenceState.ARTIFACT,36,Optional.of(TARGET)));
        var duplicate=new CurrentLivingInventoryQuerySource(s.actorFullId(),s.artifacts(),s.slots(),s.weaponSlot(),refs,true,true);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.currentLivingOriginalBindings(duplicate));
    }
    @Test void staleConsumedReferenceRemainsDataWhileActualInventoryAbsenceIsRequired()throws IOException{
        var before=source(36423,0,1,92,0,true);var after=source(36423,1,2,72,1,true);
        assertEquals(0L,NativeOwnerSnapshotMain268.currentLivingReference(after,CurrentLivingInventoryQuerySource.ReferenceRole.FIXTURE_MATERIAL_COMMON));
        NativeOwnerSnapshotMain268.requireCurrentLivingConsumed(before,after,TARGET,0,1);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.currentLivingOriginalBindings(after));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentLivingConsumed(before,source(36423,0,2,72,1,true),TARGET,0,1));
    }
    @Test void canonicalWeaponSlotAndEquippedMustBothBeActual()throws IOException{
        NativeOwnerSnapshotMain268.requireCurrentLivingEquipped(source(36423,0,1,92,0,true),TARGET);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentLivingEquipped(source(36423,0,1,92,0,false),TARGET));
        var s=source(36423,0,1,92,0,true);
        var armorOnly=new CurrentLivingInventoryQuerySource(s.actorFullId(),s.artifacts(),List.of(new CurrentLivingInventoryQuerySource.Slot("weapon",Optional.empty()),new CurrentLivingInventoryQuerySource.Slot("armor",Optional.of(TARGET))),Optional.of(0),s.fixedReferences(),true,true);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentLivingEquipped(armorOnly,TARGET));
    }
    @Test void canceledReviewConservesActualRowsButNotUnrelatedPhysicalStorageOrder()throws IOException{
        var s=source(36423,0,1,92,0,true);var a=new ArrayList<>(s.artifacts());java.util.Collections.reverse(a);
        NativeOwnerSnapshotMain268.requireCurrentLivingCancelConserved(s,withArtifacts(s,a),TARGET,0);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentLivingCancelConserved(s,source(36423,0,1,93,0,true),TARGET,0));
        var changed=new ArrayList<>(s.artifacts());var m=changed.get(1);changed.set(1,new CurrentLivingInventoryQuerySource.Artifact(m.fullId(),m.ownerFullId(),m.typeKey(),m.rarityRaw()+1,false,m.numeric()));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentLivingCancelConserved(s,withArtifacts(s,changed),TARGET,0));
    }
    @Test void expectedNumericCheckpointsCompareObservedSigned64NeverCalculateAfterstate()throws IOException{
        long[] level={1,2,3,4,6},xp={92,72,72,272,572},seq={0,1,2,3,5};
        for(int stage=0;stage<5;stage++)NativeOwnerSnapshotMain268.requireCurrentLivingNumbers(source(36423,stage==0?0:stage,level[stage],xp[stage],seq[stage],true),TARGET,stage);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentLivingNumbers(source(36423,1,2,71,1,true),TARGET,1));
        var s=source(36423,0,1,92,0,true);var a=new ArrayList<>(s.artifacts());var old=a.get(0);var ns=new ArrayList<>(old.numeric());ns.set(0,new CurrentLivingInventoryQuerySource.Numeric(CurrentLivingInventoryQuerySource.NumericState.OTHER_KIND,36,Optional.empty()));
        a.set(0,new CurrentLivingInventoryQuerySource.Artifact(old.fullId(),old.ownerFullId(),old.typeKey(),old.rarityRaw(),old.equipped(),ns));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.currentLivingNumeric(a.get(0)));
    }
    @Test void summaryNeverGrantsNativeAppliedPixelsDietPreviewOrFiveSaveContract(){
        var r=StrictJson.object();NativeOwnerSnapshotMain268.initializeCurrentLivingOriginalResult(r,"living-data");
        for(String key:List.of("new_date_observed","physical_save_confirmed","cancel_conservation_observed","four_rarity_numeric_readbacks_observed","original_private_channel_completed","actual_preview_fulltext_archived","detail_getter_fulltext_archived","diet_flag_independently_observed","preview_number_independently_parsed","pixels_observed","original_five_save_png_contract_pass","wholeproduct_pass"))assertFalse(r.get(key).booleanValue());
        for(String key:List.of("date_calls","save_calls","entry_action_calls","ui_action_calls"))assertEquals(0,r.get(key).intValue());
    }
}
