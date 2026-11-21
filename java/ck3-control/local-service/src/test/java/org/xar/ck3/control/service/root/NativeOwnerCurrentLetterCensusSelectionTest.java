package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.CurrentLetter;
import org.xar.ck3.control.nativebridge.CurrentLetterResult;
import org.xar.ck3.control.nativebridge.CurrentLetterSet;
import org.xar.ck3.control.nativebridge.CurrentLetterSetResult;
import org.xar.ck3.control.nativebridge.CurrentLetterSetSource;
import org.xar.ck3.control.nativebridge.CurrentLetterSource;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Explicit Java DATA tests Main selection only; private Transport authority and live effects are separate. */
final class NativeOwnerCurrentLetterCensusSelectionTest {
    private static ObjectNode config(String mode) {
        var n=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v26").put("mode",mode)
                .put("overall_timeout_seconds",60).put("read_timeout_seconds",20).put("maximum_frames_per_operation",128);
        n.putObject("owner_descriptor").put("path","D:/letter-census-selection-data/owner.json").put("bytes",1).put("sha256","0".repeat(64));return n;
    }
    private static ObjectNode replyConfig() {return config("current_letter_set_reply_known_instance").put("instance_id",3);}
    private static CoreFrame.Prefix core(int date) {return new CoreFrame.Prefix(date,1,true,0,true,true,42,true);}
    private static CurrentLetterSource row(int instance,boolean visible,boolean known,String opening) {
        return new CurrentLetterSource(3,true,true,visible,true,Optional.of(instance),Optional.of(42),
                Optional.of(known?CurrentLetter.KNOWN_DEFINITION:"java_data_unknown"),Optional.of(opening),Optional.of("Java DATA description"),
                known?List.of(new CurrentLetterSource.Option(0,visible,"Java DATA fixed reply","",Optional.of(CurrentLetter.KNOWN_OPTION))):List.of(),visible&&known);
    }
    private static CurrentLetterSetSource census() {
        return new CurrentLetterSetSource(3,3,true,List.of(row(4,true,true,"Java DATA fourth"),row(2,true,true,"Java DATA second"),row(3,true,true,"Java DATA third")));
    }
    private static CurrentLetterSetResult frame(boolean dispatched,int provider,int query,int date,CurrentLetterSetSource source,int instance) {
        return new CurrentLetterSetResult(dispatched?CurrentLetterSet.Action.REPLY_KNOWN_INSTANCE:CurrentLetterSet.Action.QUERY_LETTERS,
                dispatched?CurrentLetterSetResult.Status.REPLY_DISPATCHED:CurrentLetterSetResult.Status.AVAILABLE,
                dispatched,dispatched,true,BigInteger.valueOf(provider),BigInteger.valueOf(query),dispatched?BigInteger.ONE:BigInteger.ZERO,
                Optional.of(core(date)),Optional.of(new CurrentLetterResult.OwnerWitness(BigInteger.ONE,BigInteger.TWO,BigInteger.valueOf(3),4)),
                Optional.of(source),Optional.empty(),dispatched?Optional.of(instance):Optional.empty());
    }
    private static CurrentLetterSetResult query() {return frame(false,1,2,1000,census(),0);}
    private static CurrentLetterSetResult reply(int provider,int query,int date,CurrentLetterSetSource source,int instance) {
        return frame(true,provider,query,date,source,instance);
    }
    @Test void explicitV26SeparatesCompleteCensusFromOneExplicitInstance() {
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_LETTER_SET_QUERY,NativeOwnerSnapshotMain268.observationMode(config("current_letter_set_query")));
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_LETTER_SET_REPLY_KNOWN_INSTANCE,NativeOwnerSnapshotMain268.observationMode(replyConfig()));
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.observationMode(replyConfig().put("instance_id",Integer.MAX_VALUE)));
        for(String mode:List.of("current_letter_reply_known","current_letter_set_reply","current_letter_set_query ",""))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config(mode)),mode);
    }
    @Test void actualInstanceIsRequiredOnlyForReplyAndHasStrictPositiveInt32Type() {
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("current_letter_set_reply_known_instance")));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("current_letter_set_query").put("instance_id",3)));
        for(var invalid:List.of(replyConfig().put("instance_id",0),replyConfig().put("instance_id",-1),replyConfig().put("instance_id",2147483648L),
                replyConfig().put("instance_id",true),replyConfig().put("instance_id","3"),replyConfig().put("instance_id",3.0)))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(invalid));
    }
    @Test void commonFieldsAndNoConfiguredAuthorityRemainStrict() {
        for(String field:List.of("mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation")) {
            var n=replyConfig();n.remove(field);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n),field);
        }
        for(String field:List.of("definition_key","option","authored_option_index","ordinal","native_token","recipient_character_id","target_character_id",
                "expected_core","provider_generation","query_sequence","known_reply_admissible","native_can_select","deadline","control_step","maximum_status_polls")) {
            var n=replyConfig();n.put(field,1);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n),field);
        }
    }
    @Test void oldV24AndV25ModesAndTheirFieldSetsAreUnchanged() {
        var old=config("current_letter_reply_known").put("schema","xar.native-owner-snapshot-config/v24");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_LETTER_REPLY_KNOWN,NativeOwnerSnapshotMain268.observationMode(old));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(old.deepCopy().put("instance_id",3)));
        for(String schema:List.of("xar.native-owner-snapshot-config/v24","xar.native-owner-snapshot-config/v25"))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(replyConfig().put("schema",schema)));
        var cost=config("current_djc_selected_cost").put("schema","xar.native-owner-snapshot-config/v25").put("target_character_id",17).put("cb_key","duchy_de_jure_greatwar");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_DJC_SELECTED_COST,NativeOwnerSnapshotMain268.observationMode(cost));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(cost.deepCopy().put("instance_id",3)));
    }
    @Test void explicitSelectionUsesActualIdRatherThanCensusPositionOrUniqueKnown()throws IOException {
        assertEquals(3,NativeOwnerSnapshotMain268.requireCurrentLetterInstance(query(),3).instanceId().orElseThrow());
        assertEquals(2,NativeOwnerSnapshotMain268.requireCurrentLetterInstance(query(),2).instanceId().orElseThrow());
        for(int missing:List.of(0,1,5))assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentLetterInstance(query(),missing));
    }
    @Test void completeMixedCensusIsNotFilteredAndSelectedHiddenUnknownDoNotFallback()throws IOException {
        var mixed=new CurrentLetterSetSource(3,3,true,List.of(row(4,true,true,"Java DATA known"),row(2,false,true,"Java DATA hidden"),row(3,true,false,"Java DATA unknown")));
        var q=frame(false,1,2,1000,mixed,0);
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentLetterSetQueryFrame(q,core(1000)));
        assertEquals(3,StrictJson.parse(q.encode().bytes(),1<<20).get("source").get("letters").size());
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentLetterInstance(q,2));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentLetterInstance(q,3));
        assertEquals(4,NativeOwnerSnapshotMain268.requireCurrentLetterInstance(q,4).instanceId().orElseThrow());
    }
    @Test void emptyCompleteCensusRemainsReadonlyAndCannotGrantReply() {
        var empty=frame(false,1,2,1000,new CurrentLetterSetSource(0,0,true,List.of()),0);
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentLetterSetQueryFrame(empty,core(1000)));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentLetterInstance(empty,3));
    }
    @Test void queryRoleRequiresOriginalCoreAndReadonlyCensus() {
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentLetterSetQueryFrame(query(),core(1000)));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentLetterSetQueryFrame(query(),core(1024)));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentLetterSetQueryFrame(reply(1,2,1000,census(),3),core(1000)));
    }
    @Test void callbackNeedsOriginalFullCensusCoreLeaseAndExactSelectedInstance() {
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentLetterSetReplyFrame(query(),reply(1,2,1000,census(),3),3));
        var changed=new CurrentLetterSetSource(3,3,true,List.of(row(4,true,true,"Java DATA changed unselected"),row(2,true,true,"Java DATA second"),row(3,true,true,"Java DATA third")));
        for(var invalid:List.of(reply(2,2,1000,census(),3),reply(1,3,1000,census(),3),reply(1,2,1024,census(),3),reply(1,2,1000,census(),2),reply(1,2,1000,changed,3),query()))
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentLetterSetReplyFrame(query(),invalid,3));
    }
    @Test void voidReplyStillMakesNoClosureNewDateOrPhysicalSaveClaim()throws IOException {
        var n=StrictJson.parse(reply(1,2,1000,census(),3).encode().bytes(),1<<20);
        assertEquals(3,n.get("instance_id").intValue());assertTrue(n.get("native_returned").booleanValue());
        for(String key:List.of("native_handled","letter_closed","new_date_observed","physical_save_confirmed"))assertFalse(n.get(key).booleanValue(),key);
    }
}
