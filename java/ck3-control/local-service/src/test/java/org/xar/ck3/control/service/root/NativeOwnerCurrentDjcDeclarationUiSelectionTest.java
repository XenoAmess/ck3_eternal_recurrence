package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.CurrentDjcDeclarationUiSource;
import org.xar.ck3.control.nativebridge.CurrentDjcTargetWarQueryResult.CasusBelliKey;

/** Configuration/selection DATA tests only. No synthetic token grants private Transport authority. */
final class NativeOwnerCurrentDjcDeclarationUiSelectionTest {
    private static ObjectNode query() {
        var n=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v23").put("mode","current_djc_declaration_ui")
                .put("target_character_id",39957).put("cb_key","kingdom_de_jure_greatwar")
                .put("overall_timeout_seconds",60).put("read_timeout_seconds",20).put("maximum_frames_per_operation",128);
        n.putObject("owner_descriptor").put("path","D:/djc-ui-selection-data/owner.json").put("bytes",1).put("sha256","0".repeat(64));return n;
    }
    private static ObjectNode submit() {
        var n=query().put("mode","current_djc_declaration_submit").put("maximum_warning_polls",8).put("warning_poll_interval_ms",100);
        var tuple=n.putObject("tuple_intent").put("claimant_character_id",-1);
        tuple.putArray("target_title_ids").add(240).add(-16777214).add(240);
        tuple.putArray("extra_configuration_ids").add(-1).add(6).add(6).add(Integer.MIN_VALUE);return n;
    }
    private static ObjectNode tuple(ObjectNode n){return (ObjectNode)n.get("tuple_intent");}
    private static NativeOwnerSnapshotMain268.DjcUiTupleIntent intent(){return NativeOwnerSnapshotMain268.currentDjcUiConfig(submit(),true).intent().orElseThrow();}
    private static CurrentDjcDeclarationUiSource.SelectedTuple observed(boolean enabled,List<Integer> titles,List<Integer> extra) {
        return new CurrentDjcDeclarationUiSource.SelectedTuple(CasusBelliKey.KINGDOM,Optional.empty(),titles,extra,enabled);
    }
    private static CurrentDjcDeclarationUiSource.Choice row(int token,CurrentDjcDeclarationUiSource.SelectedTuple tuple) {
        return new CurrentDjcDeclarationUiSource.Choice(BigInteger.valueOf(token),tuple);
    }
    @Test void queryAndSubmissionAreDifferentExactModes() {
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_DJC_DECLARATION_UI,NativeOwnerSnapshotMain268.observationMode(query()));
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_DJC_DECLARATION_SUBMIT,NativeOwnerSnapshotMain268.observationMode(submit()));
        var q=NativeOwnerSnapshotMain268.currentDjcUiConfig(query(),false);assertTrue(q.intent().isEmpty());assertEquals(0,q.maximumWarningPolls());
        for(String mode:new String[]{"declare-war","current_djc_target_war_query","current_succession_default_continue","current_rite_final_confirmation",""})
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(submit().put("mode",mode)),mode);
        for(String field:new String[]{"tuple_intent","maximum_warning_polls","warning_poll_interval_ms"}) {
            var n=query();n.set(field,submit().get(field));assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n),field);
            var missing=submit();missing.remove(field);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(missing),field);
        }
    }
    @Test void signedTargetAndOnlyThreeFixedCbKeysAreData() {
        assertEquals(Integer.MIN_VALUE,NativeOwnerSnapshotMain268.currentDjcUiConfig(query().put("target_character_id",Integer.MIN_VALUE),false).target().value());
        for(long bad:new long[]{-1,2147483648L,-2147483649L})assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(query().put("target_character_id",bad)));
        for(String cb:new String[]{"duchy_de_jure_greatwar","kingdom_de_jure_greatwar","empire_de_jure_greatwar"})assertDoesNotThrow(()->NativeOwnerSnapshotMain268.observationMode(query().put("cb_key",cb)));
        for(String cb:new String[]{"holy_war","KINGDOM_DE_JURE_GREATWAR","", "kingdom_de_jure_greatwar "})assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(query().put("cb_key",cb)));
        for(String key:new String[]{"target_character_id","cb_key","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation"}){var n=query();n.remove(key);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n),key);}
    }
    @Test void tuplesKeepSignedOrderDuplicatesAndAbsentClaimantWithoutPermissionBooleans() {
        var data=intent();assertTrue(data.claimant().isEmpty());assertEquals(List.of(240,-16777214,240),data.targetTitleIds());assertEquals(List.of(-1,6,6,Integer.MIN_VALUE),data.extraConfigurationIds());
        var n=submit();tuple(n).put("claimant_character_id",Integer.MIN_VALUE);
        assertEquals(new NativeCharacterId(Integer.MIN_VALUE),NativeOwnerSnapshotMain268.currentDjcUiConfig(n,true).intent().orElseThrow().claimant().orElseThrow());
        for(String forbidden:new String[]{"native_enabled","source_row_enabled","native_token","choice_token","choice_index","casus_belli_index","configuration_index","can_send"}) {
            var forged=submit();tuple(forged).put(forbidden,true);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(forged),forbidden);
        }
    }
    @Test void malformedOrOutsideTupleDomainIsRejected() {
        for(String key:new String[]{"claimant_character_id","target_title_ids","extra_configuration_ids"}){var n=submit();tuple(n).remove(key);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n),key);}
        for(JsonNode bad:List.of(StrictJson.object().putNull("v").get("v"),StrictJson.object().put("v",true).get("v"),StrictJson.object().put("v","4").get("v"),StrictJson.object().put("v",1.5).get("v"),StrictJson.object().put("v",2147483648L).get("v"))) {
            var n=submit();tuple(n).set("claimant_character_id",bad);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));
            var t=submit();tuple(t).putArray("target_title_ids").add(bad);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(t));
            var e=submit();tuple(e).putArray("extra_configuration_ids").add(bad);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(e));
        }
        var absent=submit();tuple(absent).putArray("target_title_ids").add(-1);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(absent));
        for(String key:new String[]{"target_title_ids","extra_configuration_ids"}) {
            var n=submit();tuple(n).put(key,"not-an-array");assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));
            var tooMany=submit();var array=tuple(tooMany).putArray(key);for(int i=0;i<10001;i++)array.add(2);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(tooMany));
        }
    }
    @Test void onlyTheUniqueActualEnabledRowIsRetained()throws IOException {
        var intended=intent();var actual=row(1,observed(true,intended.targetTitleIds(),intended.extraConfigurationIds()));
        var reordered=row(2,observed(true,List.of(-16777214,240,240),intended.extraConfigurationIds()));
        assertSame(actual,NativeOwnerSnapshotMain268.uniqueCurrentDjcRow(intended,List.of(reordered,actual)));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.uniqueCurrentDjcRow(intended,List.of(reordered)));
        var duplicateDisabled=row(3,observed(false,intended.targetTitleIds(),intended.extraConfigurationIds()));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.uniqueCurrentDjcRow(intended,List.of(actual,duplicateDisabled)));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.uniqueCurrentDjcRow(intended,List.of(duplicateDisabled)));
        assertFalse(NativeOwnerSnapshotMain268.currentDjcTupleMatches(intended,observed(true,List.of(240,-16777214),intended.extraConfigurationIds())));
        assertFalse(NativeOwnerSnapshotMain268.currentDjcTupleMatches(intended,observed(true,intended.targetTitleIds(),List.of(-1,6,Integer.MIN_VALUE,6))));
        assertFalse(NativeOwnerSnapshotMain268.currentDjcTupleMatches(intended,new CurrentDjcDeclarationUiSource.SelectedTuple(CasusBelliKey.KINGDOM,Optional.of(new NativeCharacterId(44)),intended.targetTitleIds(),intended.extraConfigurationIds(),true)));
    }
    @Test void callerCoreTokensLeaseOrdinalAndOutcomeCannotEnterEitherMode() {
        for(String key:new String[]{"expected_core","core","date_raw","played_character_id","provider_generation","query_sequence","claim_sequence","origin_claim_sequence","choice_token","choice_index","ordinal","source_row_enabled","native_enabled","ordinary_can_declare_war","native_can_send","native_can_accept","submitted","war_id","total_debit","deadline_unix_ms","operation_id","step","arguments","capability","window_name"}) {
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(query().put(key,"forged")),key);
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(submit().put(key,"forged")),key);
        }
    }
    @Test void warningWaitIsFiniteAndNotBorrowedByQueryMode() {
        for(int polls:new int[]{1,64})assertDoesNotThrow(()->NativeOwnerSnapshotMain268.observationMode(submit().put("maximum_warning_polls",polls)));
        for(int polls:new int[]{0,65,-1})assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(submit().put("maximum_warning_polls",polls)));
        for(int interval:new int[]{100,5000})assertDoesNotThrow(()->NativeOwnerSnapshotMain268.observationMode(submit().put("warning_poll_interval_ms",interval)));
        for(int interval:new int[]{99,5001,-1})assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(submit().put("warning_poll_interval_ms",interval)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(submit().put("maximum_warning_polls",1.5)));
    }
    @Test void v21AndV22StaySeparateAndNoOlderModeBorrowsTheNewIntent() {
        for(int version:new int[]{1,11,16,17,18,19,20,21,22})assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(submit().put("schema","xar.native-owner-snapshot-config/v"+version)));
        var oldQuery=query().put("schema","xar.native-owner-snapshot-config/v21").put("mode","current_djc_target_war_query");oldQuery.remove("cb_key");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_DJC_TARGET_QUERY,NativeOwnerSnapshotMain268.observationMode(oldQuery));
        var oldContinue=query().put("schema","xar.native-owner-snapshot-config/v22").put("mode","current_succession_default_continue");oldContinue.remove(List.of("target_character_id","cb_key"));
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_SUCCESSION_CONTINUE,NativeOwnerSnapshotMain268.observationMode(oldContinue));
    }
}
