package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.CurrentLetterResult;
import org.xar.ck3.control.nativebridge.CurrentRiteCreationBlockersSource;
import org.xar.ck3.control.nativebridge.CurrentRiteCreationBlockersResult;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Pure DATA/schema/consumer boundaries. No fabricated native packet or actual getter proof. */
final class NativeOwnerCurrentRiteCreationBlockersSelectionTest {
    private static ObjectNode config() {
        var c=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v43").put("mode","current_rite_creation_blockers")
                .put("overall_timeout_seconds",120).put("read_timeout_seconds",20).put("maximum_frames_per_operation",128).put("expected_source_rite_id",47);
        c.putObject("owner_descriptor").put("path","D:/blockers-DATA/owner.json").put("bytes",1).put("sha256","0".repeat(64));return c;
    }
    private static CoreFrame.Prefix prefix(int actor){return new CoreFrame.Prefix(53144328,2,true,0,true,true,actor,true);}
    private static CurrentLetterResult.OwnerWitness owner(long connection,long ticket){return new CurrentLetterResult.OwnerWitness(BigInteger.valueOf(connection),BigInteger.valueOf(ticket),BigInteger.valueOf(ticket+1),7);}
    private static CurrentRiteCreationBlockersSource source(long rite,int actor,String text,boolean can){return new CurrentRiteCreationBlockersSource(rite,actor,false,can,text,false,false,true);}
    private static CurrentRiteCreationBlockersResult frame(CurrentRiteCreationBlockersSource source,long connection,long ticket){return new CurrentRiteCreationBlockersResult(
            CurrentRiteCreationBlockersResult.Status.AVAILABLE,true,BigInteger.ONE,BigInteger.TWO,Optional.of(prefix(source.actorId())),Optional.of(owner(connection,ticket)),Optional.of(source),Optional.empty());}

    @Test void OnlyOneExactModeAndTwoReadonlySubmissions(){
        assertEquals(7,config().size());assertEquals(2,NativeOwnerSnapshotMain268.currentRiteCreationBlockersConfig(config()).submissions());
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_RITE_CREATION_BLOCKERS,NativeOwnerSnapshotMain268.observationMode(config()));
        for(String mode:List.of("query_blockers","current_rite_creation_blockers ","current_rite_creation_identity_query","current_rite_create_query",""))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config().put("mode",mode)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreationBlockersConfig(config().put("schema","xar.native-owner-snapshot-config/v42")));
    }
    @Test void SourceRiteGuardAndCommonFieldsAreMandatoryExactData(){
        for(String key:List.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation","expected_source_rite_id")){
            var c=config();c.remove(key);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreationBlockersConfig(c));
        }
        for(long id:new long[]{0,47,0xffff_fffeL})assertEquals(id,NativeOwnerSnapshotMain268.currentRiteCreationBlockersConfig(config().put("expected_source_rite_id",id)).sourceRiteId());
        for(long id:new long[]{-1,0xffff_ffffL,0x1_0000_0000L})assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreationBlockersConfig(config().put("expected_source_rite_id",id)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreationBlockersConfig(config().put("expected_source_rite_id",true)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreationBlockersConfig(config().put("expected_source_rite_id","47")));
        var bad=config();((ObjectNode)bad.get("owner_descriptor")).put("bytes",true);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreationBlockersConfig(bad));
        for(String key:List.of("overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation")){
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreationBlockersConfig(config().put(key,0)));
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreationBlockersConfig(config().put(key,"1")));
        }
    }
    @Test void NoBorrowedTextCreateKeysCallerPermissionsOrLeases(){
        for(String key:List.of("text","choice_token","choice_key","icon_name","action","native_can_create","provider_generation","query_sequence","claim_sequence","actor","expected_core","navigation_action","maximum_confirmation_polls","checkpoint_archive_path")){
            var c=config();c.put(key,"borrowed");assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteCreationBlockersConfig(c));
        }
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config().put("schema","xar.native-owner-snapshot-config/v41")));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config().put("schema","xar.native-owner-snapshot-config/v42")));
    }
    @Test void CurrentPausedLivingMapCoreRetainsPackedSignedActorData()throws IOException{
        for(int actor:new int[]{0,-2,Integer.MIN_VALUE,Integer.MAX_VALUE})assertEquals(prefix(actor),NativeOwnerSnapshotMain268.requireCurrentRiteCreationBlockersCore(new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,prefix(actor))));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRiteCreationBlockersCore(new CoreFrame.Partial(ExactCk3Build.CK3_12004,prefix(36423))));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRiteCreationBlockersCore(new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,new CoreFrame.Prefix(53144328,2,false,0,true,true,36423,true))));
    }
    @Test void FalseCanNotCreatingHiddenAndEmptyWhyAreSuccessfulData()throws IOException{
        var s=source(47,36423,"",false);var q=frame(s,2,11);
        assertSame(s,NativeOwnerSnapshotMain268.requireCurrentRiteCreationBlockersFrame(q,prefix(36423),47,BigInteger.TWO));
        assertTrue(q.successful());assertFalse(s.nativeCanCreate());assertFalse(s.isCreating());assertFalse(s.windowVisible());assertFalse(s.windowEnabled());assertEquals("",s.blockersText());
        var positive=source(47,36423,"actual text is independently DATA",true);
        assertTrue(NativeOwnerSnapshotMain268.requireCurrentRiteCreationBlockersFrame(frame(positive,2,12),prefix(36423),47,BigInteger.TWO).nativeCanCreate());
    }
    @Test void Read16384BytesNulRichtextAndNoNormalizationPreserved()throws IOException{
        for(String text:List.of(""," a\0b\u0015#P details#!\n\t ","x".repeat(16384),"\ud83d\ude00".repeat(4096),"e\u0301")){
            var s=source(47,36423,text,false);var observed=NativeOwnerSnapshotMain268.requireCurrentRiteCreationBlockersFrame(frame(s,2,21),prefix(36423),47,BigInteger.TWO);
            assertEquals(text,observed.blockersText());assertArrayEquals(text.getBytes(StandardCharsets.UTF_8),observed.blockersText().getBytes(StandardCharsets.UTF_8));
        }
        assertThrows(IllegalArgumentException.class,()->source(47,36423,"x".repeat(16385),false));
        assertThrows(IllegalArgumentException.class,()->source(47,36423,"\ud800",false));
        assertThrows(IllegalArgumentException.class,()->source(47,36423,"\udc00",false));
    }
    @Test void FullCoreRiteActorAndConnectionMustMatchOriginalQuery()throws IOException{
        var s=source(47,36423,"why",false);var q=frame(s,2,31);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRiteCreationBlockersFrame(q,prefix(36423),48,BigInteger.TWO));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRiteCreationBlockersFrame(q,prefix(40180),47,BigInteger.TWO));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRiteCreationBlockersFrame(q,new CoreFrame.Prefix(53144352,2,true,0,true,true,36423,true),47,BigInteger.TWO));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRiteCreationBlockersFrame(q,prefix(36423),47,BigInteger.valueOf(3)));
    }
    @Test void InformationalOwnerTicketsMayDifferButNeverBecomeMutationLease()throws IOException{
        var s=source(0,0,"CanCreate=true in text is not a permission",false);
        for(long ticket:new long[]{1,900}){
            var q=frame(s,2,ticket);assertSame(s,NativeOwnerSnapshotMain268.requireCurrentRiteCreationBlockersFrame(q,prefix(0),0,BigInteger.TWO));
            assertEquals(BigInteger.ZERO,q.claimSequence());assertFalse(q.effectAttempted());assertFalse(q.nativeReturned());assertFalse(q.nativeHandled());assertFalse(q.newDateObserved());assertFalse(q.physicalSaveConfirmed());assertFalse(s.nativeCanCreate());
        }
    }
    @Test void RefusalsAndMissingDoubleSamplesCannotBecomeFalseCanObservation(){
        for(var status:List.of(CurrentRiteCreationBlockersResult.Status.UNAVAILABLE,CurrentRiteCreationBlockersResult.Status.EXPIRED,CurrentRiteCreationBlockersResult.Status.STALE_SOURCE,CurrentRiteCreationBlockersResult.Status.INDETERMINATE)){
            var q=new CurrentRiteCreationBlockersResult(status,status!=CurrentRiteCreationBlockersResult.Status.INDETERMINATE,BigInteger.ZERO,BigInteger.ZERO,Optional.empty(),Optional.empty(),Optional.empty(),Optional.of("actual refusal"));
            assertFalse(q.successful());assertTrue(q.source().isEmpty());assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRiteCreationBlockersFrame(q,prefix(36423),47,BigInteger.TWO));
        }
        assertThrows(IllegalArgumentException.class,()->new CurrentRiteCreationBlockersSource(47,36423,false,false,"",false,false,false));
        assertThrows(IllegalArgumentException.class,()->source(47,-1,"",false));
    }
    @Test void SummaryNeverPromotesTextOrAvailableToCreateDateSaveOrRender(){
        var result=StrictJson.object();NativeOwnerSnapshotMain268.initializeCurrentRiteCreationBlockersResult(result,NativeOwnerSnapshotMain268.currentRiteCreationBlockersConfig(config()),"DATA-machine");
        for(String key:List.of("source_available","effect_attempted","native_returned","native_handled","create_authorized","new_date_observed","physical_save_confirmed","tooltip_render_observed"))assertFalse(result.get(key).booleanValue());
        for(String key:List.of("read_calls","query_calls","create_calls","accept_calls","date_calls","save_calls"))assertEquals(0,result.get(key).intValue());
        assertTrue(result.get("native_can_create").isNull());assertTrue(result.get("blockers_text").isNull());
    }
}
