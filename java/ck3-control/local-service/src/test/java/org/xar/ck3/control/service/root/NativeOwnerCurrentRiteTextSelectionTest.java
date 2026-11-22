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
import org.xar.ck3.control.nativebridge.CurrentRiteText;
import org.xar.ck3.control.nativebridge.CurrentRiteTextSource;
import org.xar.ck3.control.nativebridge.CurrentRiteTextResult;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Pure DATA/config boundaries, never Native frames or actual text-write proof. */
final class NativeOwnerCurrentRiteTextSelectionTest {
    private static ObjectNode config(String mode) {
        var c=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v42").put("mode",mode)
                .put("overall_timeout_seconds",120).put("read_timeout_seconds",20).put("maximum_frames_per_operation",1024).put("expected_source_rite_id",47);
        c.putObject("owner_descriptor").put("path","D:/rite-text-DATA/owner.json").put("bytes",1).put("sha256","0".repeat(64));
        if(!mode.equals("current_rite_text_query"))c.put("text","");return c;
    }
    private static ObjectNode query(){return config("current_rite_text_query");}
    private static ObjectNode name(){return config("current_rite_text_set_name");}
    private static ObjectNode description(){return config("current_rite_text_set_description");}
    private static CoreFrame.Prefix prefix(int actor){return new CoreFrame.Prefix(53144328,2,true,0,true,true,actor,true);}
    private static CurrentRiteTextSource source(int actor,boolean admissible,String name,String description){return new CurrentRiteTextSource(47,actor,admissible,name,description,true,admissible,!admissible,admissible);}
    private static CurrentLetterResult.OwnerWitness owner(long connection,long ticket){return new CurrentLetterResult.OwnerWitness(BigInteger.valueOf(connection),BigInteger.valueOf(ticket),BigInteger.valueOf(ticket+1),7);}
    private static CurrentRiteTextResult frame(CurrentRiteTextSource source,long connection,long ticket){return new CurrentRiteTextResult(CurrentRiteText.Action.QUERY,CurrentRiteTextResult.Status.AVAILABLE,false,false,true,
            BigInteger.ONE,BigInteger.TWO,BigInteger.ZERO,Optional.of(prefix(source.actorId())),Optional.of(owner(connection,ticket)),Optional.of(source),Optional.empty());}
    private static CurrentRiteTextResult dispatched(CurrentRiteTextResult query,CurrentRiteText.Action action,CurrentRiteTextSource source,long connection){return new CurrentRiteTextResult(action,CurrentRiteTextResult.Status.TEXT_DISPATCHED,true,true,true,
            query.providerGeneration(),query.querySequence(),BigInteger.TEN,query.factsBefore(),Optional.of(owner(connection,900)),Optional.of(source),Optional.empty());}

    @Test void onlyThreeExactModesHaveTwoOrFiveFiniteSubmissions(){
        assertEquals(7,query().size());assertEquals(8,name().size());
        assertEquals(CurrentRiteText.Action.QUERY,NativeOwnerSnapshotMain268.currentRiteTextConfig(query()).action());
        assertEquals(2,NativeOwnerSnapshotMain268.currentRiteTextConfig(query()).submissions());
        assertEquals(CurrentRiteText.Action.SET_NAME,NativeOwnerSnapshotMain268.currentRiteTextConfig(name()).action());
        assertEquals(CurrentRiteText.Action.SET_DESCRIPTION,NativeOwnerSnapshotMain268.currentRiteTextConfig(description()).action());
        assertEquals(5,NativeOwnerSnapshotMain268.currentRiteTextConfig(description()).submissions());
        for(String value:List.of("current_rite_text_set_name ","current_rite_create_query","set_name",""))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(name().put("mode",value)));
    }
    @Test void SetterTextIsRequiredTypedAndMayClearWhileQueryNeverAcceptsText(){
        assertEquals("",NativeOwnerSnapshotMain268.currentRiteTextConfig(name()).text());
        assertEquals("",NativeOwnerSnapshotMain268.currentRiteTextConfig(description()).text());
        var missing=name();missing.remove("text");assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteTextConfig(missing));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteTextConfig(name().putNull("text")));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteTextConfig(name().put("text",true)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteTextConfig(name().put("text",123)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteTextConfig(query().put("text","")));
    }
    @Test void UnicodeWriteBoundsCountScalarsAndExactUtf8WithoutNormalization(){
        String emoji="\ud83d\ude00";
        assertEquals(emoji.repeat(30),NativeOwnerSnapshotMain268.currentRiteTextConfig(name().put("text",emoji.repeat(30))).text());
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteTextConfig(name().put("text",emoji.repeat(31))));
        assertEquals(emoji.repeat(400),NativeOwnerSnapshotMain268.currentRiteTextConfig(description().put("text",emoji.repeat(400))).text());
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteTextConfig(description().put("text",emoji.repeat(401))));
        assertEquals("e\u0301".repeat(15),NativeOwnerSnapshotMain268.currentRiteTextConfig(name().put("text","e\u0301".repeat(15))).text());
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteTextConfig(name().put("text","e\u0301".repeat(16))));
        for(String bad:List.of("a\0b","a\u0015b","a\u007fb","\ud800","\udc00")) {
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteTextConfig(name().put("text",bad)));
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteTextConfig(description().put("text",bad)));
        }
        assertEquals("line\n\ttwo",NativeOwnerSnapshotMain268.currentRiteTextConfig(description().put("text","line\n\ttwo")).text());
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteTextConfig(name().put("text","line\n\ttwo")));
    }
    @Test void CommonFieldsOwnerPinAndExactRiteDataAreMandatory(){
        for(String field:List.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation","expected_source_rite_id")) {
            var c=query();c.remove(field);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteTextConfig(c));
        }
        var badOwner=query();((ObjectNode)badOwner.get("owner_descriptor")).put("bytes",true);
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteTextConfig(badOwner));
        for(long rite:new long[]{0,47,0xffff_fffeL})assertEquals(rite,NativeOwnerSnapshotMain268.currentRiteTextConfig(query().put("expected_source_rite_id",rite)).sourceRiteId());
        for(long rite:new long[]{-1,0xffff_ffffL,0x1_0000_0000L})assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteTextConfig(query().put("expected_source_rite_id",rite)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteTextConfig(query().put("expected_source_rite_id",true)));
        for(String field:List.of("overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation")) {
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteTextConfig(query().put(field,0)));
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteTextConfig(query().put(field,"1")));
        }
    }
    @Test void NoBorrowedPermissionsSelectorsSaveFieldsOrOldSchemaAliases(){
        for(String field:List.of("actor","action","key","ordinal","native_can_create","write_admissible","expected_core","lease","provider_generation","query_sequence","navigation_action","rite_action","checkpoint_archive_path","maximum_confirmation_polls","confirmation_poll_interval_ms","permission"))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteTextConfig(name().put(field,"forged")),field);
        for(String schema:List.of("xar.native-owner-snapshot-config/v41","xar.native-owner-snapshot-config/v18","xar.native-owner-snapshot-config/v40"))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(name().put("schema",schema)));
        var old=query().put("schema","xar.native-owner-snapshot-config/v41").put("mode","current_rite_create_query");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_RITE_CREATE,NativeOwnerSnapshotMain268.observationMode(old));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(old.put("text","")));
    }
    @Test void CoreMustBeCurrentPausedLocalLivingButRetainsPackedSignedIds()throws IOException{
        for(int actor:new int[]{0,-2,Integer.MIN_VALUE,Integer.MAX_VALUE})assertEquals(prefix(actor),NativeOwnerSnapshotMain268.requireCurrentRiteTextCore(new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,prefix(actor))));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRiteTextCore(new CoreFrame.Partial(ExactCk3Build.CK3_12004,prefix(36423))));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRiteTextCore(new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,new CoreFrame.Prefix(53144328,2,false,0,true,true,36423,true))));
        assertThrows(IllegalArgumentException.class,()->new CoreFrame.Prefix(53144328,0,true,0,true,true,36423,true));
        assertThrows(IllegalArgumentException.class,()->prefix(-1));
    }
    @Test void EmptyRichtextControlsAndRead4096AreActualDataNotWriteValidation()throws IOException{
        for(String actual:List.of("","a\0b\u0015\n\t","\ud83d\ude00".repeat(1024))) {
            var s=source(36423,false,actual,actual);var q=frame(s,9,20);
            assertEquals(s,NativeOwnerSnapshotMain268.requireCurrentRiteTextQueryFrame(q,prefix(36423),47,BigInteger.valueOf(9)));
            assertFalse(s.isCreating());assertTrue(s.blockedByUnrelatedModal());assertFalse(s.writeAdmissible());
        }
        assertThrows(IllegalArgumentException.class,()->source(36423,false,"x".repeat(4097),""));
        var q=frame(source(36423,true,"before","desc"),9,20);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRiteTextQueryFrame(q,prefix(36423),48,BigInteger.valueOf(9)));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRiteTextQueryFrame(q,prefix(36423),47,BigInteger.valueOf(10)));
    }
    @Test void VoidAckRetainsWholeBeforeSourceAndLeaseWithIndependentNewCustody()throws IOException{
        var s=source(36423,true,"before","before description");var q=frame(s,9,20);
        for(var action:List.of(CurrentRiteText.Action.SET_NAME,CurrentRiteText.Action.SET_DESCRIPTION)) {
            var done=dispatched(q,action,s,9);
            assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentRiteTextDispatchFrame(done,q,action));
            assertFalse(done.nativeHandled());assertFalse(done.textApplied());assertFalse(done.newDateObserved());assertFalse(done.physicalSaveConfirmed());
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRiteTextDispatchFrame(dispatched(q,action,s,10),q,action));
            var rebound=source(36423,true,"changed","before description");
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRiteTextDispatchFrame(dispatched(q,action,rebound,9),q,action));
        }
        var refused=new CurrentRiteTextResult(CurrentRiteText.Action.SET_NAME,CurrentRiteTextResult.Status.PREREQUISITE_REJECTED,false,false,true,BigInteger.ONE,BigInteger.TWO,BigInteger.TEN,Optional.empty(),Optional.empty(),Optional.empty(),Optional.of("known-DATA-refusal"));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentRiteTextDispatchFrame(refused,q,CurrentRiteText.Action.SET_NAME));
    }
    @Test void IndependentReadbackComparesOnlyRequestedExactUtf8AndDoesNotNormalize(){
        var fresh=source(36423,false," e\u0301 ","different actual after-description");
        assertTrue(NativeOwnerSnapshotMain268.currentRiteTextReadbackMatches(fresh,CurrentRiteText.Action.SET_NAME," e\u0301 "));
        assertFalse(NativeOwnerSnapshotMain268.currentRiteTextReadbackMatches(fresh,CurrentRiteText.Action.SET_NAME,"é"));
        assertFalse(NativeOwnerSnapshotMain268.currentRiteTextReadbackMatches(fresh,CurrentRiteText.Action.SET_NAME,"e\u0301"));
        assertTrue(NativeOwnerSnapshotMain268.currentRiteTextReadbackMatches(source(36423,false,"changed other name",""),CurrentRiteText.Action.SET_DESCRIPTION,""));
        assertFalse(NativeOwnerSnapshotMain268.currentRiteTextReadbackMatches(source(36423,false,"x","unchanged"),CurrentRiteText.Action.SET_DESCRIPTION,"new"));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentRiteTextReadbackMatches(fresh,CurrentRiteText.Action.QUERY,""));
    }
    @Test void SummaryDoesNotPromoteDispatchOrMatchToAppliedDateOrSave(){
        var result=StrictJson.object();var c=NativeOwnerSnapshotMain268.currentRiteTextConfig(name());
        NativeOwnerSnapshotMain268.initializeCurrentRiteTextResult(result,c,"DATA-machine","current_rite_text_set_name");
        for(String field:List.of("text_applied","new_date_observed","physical_save_confirmed","query_available","setter_callback_dispatched","readback_observed","native_returned","native_handled"))assertFalse(result.get(field).booleanValue(),field);
        for(String field:List.of("read_calls","query_calls","setter_calls","date_calls","save_calls"))assertEquals(0,result.get(field).intValue(),field);
        assertTrue(result.get("requested_field_exact_utf8_match").isNull());assertEquals("NOT_OBSERVED",result.get("readback_status").textValue());
    }
}
