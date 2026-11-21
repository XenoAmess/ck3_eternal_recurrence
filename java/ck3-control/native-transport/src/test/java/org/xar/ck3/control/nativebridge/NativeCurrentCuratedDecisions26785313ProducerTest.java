package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Final a07 actual C++ frames; every mutation below is explicit Java negative DATA. */
class NativeCurrentCuratedDecisions26785313ProducerTest {
    static byte[] raw(String role)throws IOException{try(var in=NativeCurrentCuratedDecisions26785313ProducerTest.class.getResourceAsStream("/current267-curated-decisions-actual-cpp/"+role+".json")){if(in==null)throw new IOException("Actual C++ frame absent: "+role);return in.readAllBytes();}}
    static ObjectNode envelope(String role)throws IOException{return NativeWire.object(NativeWire.parse(raw(role)));}
    static CurrentCuratedDecisionsResult frame(String role)throws IOException{return changed(NativeWire.object(envelope(role).get("result")));}
    static CurrentCuratedDecisionsResult changed(ObjectNode n)throws IOException{return CurrentCuratedDecisionsResult.decode(new RawJson(StrictJson.canonical(n)));}
    static CoreFrame.Partial actualCore()throws IOException{return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,frame("query.result").factsBefore().orElseThrow());}
    @Test void allNineActualResultTokensRoundtripWithoutAnAppliedDecisionOrSaveClaim()throws Exception{
        for(String role:List.of("query.result","open-list.result","open-detail.result","confirm.result","query-nav.result","query-can-false.result","stale-source.result","expired.result","indeterminate.result")){
            var f=frame(role);assertEquals(f,CurrentCuratedDecisionsResult.decode(f.encode()),role);var n=NativeWire.parse(f.encode().bytes());assertEquals(24,n.size());
            for(String key:List.of("decision_applied","new_date_observed","physical_save_confirmed"))assertFalse(n.get(key).booleanValue(),key);}
    }
    @Test void allFourGenuineRequestsAndJavaEncoderKeepTheTenExactClaimFields()throws Exception{
        for(var a:CurrentCuratedDecisions.Action.values()){
            String name=switch(a){case QUERY->"query";case OPEN_LIST->"open-list";case OPEN_DETAIL->"open-detail";case CONFIRM->"confirm";};
            var n=envelope(name+".request");assertEquals(8,n.size());assertEquals(a.step(),n.get("step").textValue());assertEquals(0,n.get("expected_revision").intValue());assertTrue(n.get("arguments").isEmpty());
            var original=frame(name+".result");boolean query=a==CurrentCuratedDecisions.Action.QUERY;
            var r=CurrentCuratedDecisions.request(actualCore(),a,query?BigInteger.ZERO:original.providerGeneration(),query?BigInteger.ZERO:original.querySequence(),original.decisionKey());
            var claim=NativeWire.parse(r.additionalFields().bytes()).get("curated_decisions");assertEquals(10,claim.size());assertEquals(8,claim.get("expected_core").size());assertEquals(a.wire(),claim.get("action").textValue());
        }
    }
    @Test void onlyTheNineReviewedKeysAndActionSpecificNullRolesCanBeEncoded()throws Exception{
        assertEquals(9,CurrentCuratedDecisions.DecisionKey.values().length);for(var key:CurrentCuratedDecisions.DecisionKey.values())assertSame(key,CurrentCuratedDecisions.DecisionKey.parse(key.wire()));
        for(String value:List.of("unknown_decision","0","xqol.100","xqol_mass_conversion_decision "))assertThrows(IOException.class,()->CurrentCuratedDecisions.DecisionKey.parse(value));
        assertThrows(IllegalArgumentException.class,()->CurrentCuratedDecisions.request(actualCore(),CurrentCuratedDecisions.Action.QUERY,BigInteger.ONE,BigInteger.ONE,Optional.empty()));
        assertThrows(IllegalArgumentException.class,()->CurrentCuratedDecisions.request(actualCore(),CurrentCuratedDecisions.Action.OPEN_LIST,BigInteger.ONE,BigInteger.ONE,Optional.of(CurrentCuratedDecisions.DecisionKey.MASS_CONVERSION)));
        assertThrows(IllegalArgumentException.class,()->CurrentCuratedDecisions.request(actualCore(),CurrentCuratedDecisions.Action.CONFIRM,BigInteger.ONE,BigInteger.ONE,Optional.empty()));
    }
    @Test void unmaterializedNavigationIsNotAnObservedEmptyModelCensus()throws Exception{
        var s=frame("query-nav.result").source().orElseThrow();assertFalse(s.completeModelCensus());assertTrue(s.groupsCount().isEmpty());assertTrue(s.totalModelRows().isEmpty());assertTrue(s.rows().isEmpty());assertTrue(s.openListAdmissible());
        var n=NativeWire.object(envelope("query-nav.result").get("result"));((ObjectNode)n.get("source")).put("groups_count",0);reject(n);
        n=NativeWire.object(envelope("query-nav.result").get("result"));((ObjectNode)n.get("source")).put("complete_model_census",true);reject(n);
    }
    @Test void nativeCanFalseIsAValidReadonlyFactAndNeverConfirmationAuthority()throws Exception{
        var f=frame("query-can-false.result");assertTrue(f.successful());var s=f.source().orElseThrow();assertEquals(Optional.of(false),s.nativeCanConfirm());assertFalse(s.confirmAdmissible());assertFalse(s.admits(CurrentCuratedDecisions.Action.CONFIRM,s.selectedDecisionKey()));
        var n=NativeWire.object(envelope("query-can-false.result").get("result"));((ObjectNode)n.get("source")).put("confirm_admissible",true);reject(n);
    }
    @Test void duplicateOrContradictoryActualRowsCannotMintAnAction()throws Exception{
        var n=NativeWire.object(envelope("query.result").get("result"));var rows=((ObjectNode)n.get("source")).withArray("rows");rows.add(rows.get(0).deepCopy());reject(n);
        n=NativeWire.object(envelope("query.result").get("result"));((ObjectNode)n.get("source").get("rows").get(0)).put("is_selected",true);reject(n);
        n=NativeWire.object(envelope("query.result").get("result"));((ObjectNode)n.get("source")).put("list_enabled",false);reject(n);
    }
    @Test void exactBuildSchemaAndExtraKeysAreNotCallerAuthority()throws Exception{
        for(String key:List.of("schema","game_version","executable_sha256","backend","adapter_id")){var n=NativeWire.object(envelope("query.result").get("result"));n.put(key,"wrong");reject(n);}
        for(String key:List.of("permission","index","caller_can_confirm")){var n=NativeWire.object(envelope("query.result").get("result"));n.put(key,true);reject(n);}
        var n=NativeWire.object(envelope("query.result").get("result"));n.put("addresses_redacted",false);reject(n);
    }
    @Test void privateLeasesRemainCanonicalUnsigned64Strings()throws Exception{
        for(String bad:List.of("01","-1","18446744073709551616")){var n=NativeWire.object(envelope("query.result").get("result"));n.put("provider_generation",bad);reject(n);}
        var n=NativeWire.object(envelope("query.result").get("result"));n.put("query_sequence",1);reject(n);
        n=NativeWire.object(envelope("query.result").get("result"));n.put("provider_generation","0");reject(n);
    }
    @Test void knownNavigationFalseAndVoidDispatchRemainDifferentFromAppliedBusiness()throws Exception{
        var n=NativeWire.object(envelope("open-list.result").get("result"));n.put("native_handled",false);var f=changed(n);assertTrue(f.successful());assertFalse(f.nativeHandled());assertTrue(f.nativeReturned());
        for(String role:List.of("open-detail.result","confirm.result")){n=NativeWire.object(envelope(role).get("result"));n.put("native_handled",true);reject(n);}
        n=NativeWire.object(envelope("confirm.result").get("result"));n.put("decision_applied",true);reject(n);
    }
    @Test void knownZeroEffectRefusalCanRetainAPositiveSpentClaimWithoutReplay()throws Exception{
        var n=NativeWire.object(envelope("stale-source.result").get("result"));n.put("claim_sequence","1");var f=changed(n);assertFalse(f.successful());assertFalse(f.effectAttempted());assertEquals(BigInteger.ONE,f.claimSequence());
        n.put("effect_attempted",true);reject(n);
    }
    @Test void cleanupUnknownCannotMasqueradeAsACurrentPrivateSource()throws Exception{
        var n=NativeWire.object(envelope("query.result").get("result"));n.put("cleanup_known",false);reject(n);
        var uncertain=frame("indeterminate.result");assertEquals(CurrentCuratedDecisionsResult.Status.INDETERMINATE,uncertain.status());assertFalse(uncertain.successful());
    }
    @Test void selectedConfirmationMustMatchTheActualFixedKeyAndNativeAdmission()throws Exception{
        var n=NativeWire.object(envelope("confirm.result").get("result"));n.put("decision_key",CurrentCuratedDecisions.DecisionKey.VIVHITE_CREATOR.wire());reject(n);
        n=NativeWire.object(envelope("confirm.result").get("result"));((ObjectNode)n.get("source")).put("native_can_confirm",false);reject(n);
        n=NativeWire.object(envelope("confirm.result").get("result"));((ObjectNode)n.get("source")).put("blocked_by_visible_modal",true);reject(n);
    }
    private static void reject(ObjectNode n){assertThrows(IOException.class,()->changed(n));}
}
