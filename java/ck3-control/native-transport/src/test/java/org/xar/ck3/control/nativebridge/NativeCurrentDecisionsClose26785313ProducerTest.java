package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Original CPP frames remain untouched; changed tokens are explicitly Java contract-boundary DATA, never Native runtime evidence. */
class NativeCurrentDecisionsClose26785313ProducerTest {
    static byte[] raw(String role)throws IOException{try(var in=NativeCurrentDecisionsClose26785313ProducerTest.class.getResourceAsStream("/current267-decisions-close-actual-cpp/"+role+".json")){if(in==null)throw new IOException("Actual C++ decisions-close resource absent: "+role);return in.readAllBytes();}}
    static ObjectNode envelope(String role)throws IOException{return NativeWire.object(NativeWire.parse(raw(role)));}
    static ObjectNode token(String role)throws IOException{return NativeWire.object(envelope(role).get("result"));}
    static ObjectNode source(ObjectNode n){return (ObjectNode)n.get("source");}
    static CurrentDecisionsCloseResult frame(String role)throws IOException{return changed(token(role));}
    static CurrentDecisionsCloseResult changed(ObjectNode n)throws IOException{return CurrentDecisionsCloseResult.decode(new RawJson(StrictJson.canonical(n)));}
    static CoreFrame.Partial actualCore()throws IOException{return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,frame("available").factsBefore().orElseThrow());}
    @Test void genuineResultsRoundtripExact24KeysAndRetainOriginalNativeReturnBool()throws Exception{
        var index=NativeWire.object(NativeWire.parse(raw("index")));for(var name:index.get("result_roles")){String role=name.textValue();var f=frame(role);assertEquals(f,CurrentDecisionsCloseResult.decode(f.encode()));assertEquals(envelope(role).get("ok").booleanValue(),f.successful());}
        assertTrue(frame("close-true").nativeHandled());assertFalse(frame("close-false").nativeHandled());
        var n=StrictJson.parse(frame("close-true").encode().bytes(),1<<20);assertEquals(24,n.size());for(String key:List.of("panels_closed","new_date_observed","physical_save_confirmed"))assertFalse(n.get(key).booleanValue());
    }
    @Test void requestHasNineFieldsAndNoCallerKeyActorRootOrPermission()throws Exception{
        var f=frame("available");for(var action:CurrentDecisionsClose.Action.values()){boolean query=action==CurrentDecisionsClose.Action.QUERY_CLOSE;var r=CurrentDecisionsClose.request(actualCore(),action,query?BigInteger.ZERO:f.providerGeneration(),query?BigInteger.ZERO:f.querySequence());var n=NativeWire.object(NativeWire.parse(r.additionalFields().bytes()));assertEquals(2,n.size());assertEquals(0,n.get("arguments").size());assertEquals(9,n.get("decisions_close").size());assertEquals(action.step(),r.step());}
        assertThrows(IllegalArgumentException.class,()->CurrentDecisionsClose.request(actualCore(),CurrentDecisionsClose.Action.CLOSE_LIST,BigInteger.ZERO,BigInteger.ZERO));assertThrows(IOException.class,()->CurrentDecisionsClose.Action.parse("open_list"));assertThrows(IOException.class,()->CurrentDecisionsClose.Action.parse("close_all"));
    }
    @Test void exactIdentityAndClosedFieldsRejectLegacyOrCallerAuthority()throws Exception{
        for(String key:List.of("schema","game_version","executable_sha256","adapter_id","backend")){var n=token("available");n.put(key,"wrong");reject(n);}var n=token("available");n.put("caller_close_permission",true);reject(n);n=token("available");source(n).put("caller_widget",1);reject(n);
    }
    @Test void originalV28SourceEighteenAndRowThreeShapesRemainUnchanged()throws Exception{
        var n=token("available");var s=source(n);assertEquals(18,s.size());assertEquals(CurrentCuratedDecisions.SOURCE_SCHEMA,s.get("schema").textValue());for(var row:s.get("rows"))assertEquals(3,row.size());assertEquals(frame("available").source().orElseThrow(),CurrentCuratedDecisionsSource.decode(s));
        s.put("close_admissible",true);reject(n);
    }
    @Test void actualPublicListGatesDoNotReverseInferPrivateClosePermission()throws Exception{
        var n=token("available");n.put("close_admissible",false);var f=changed(n);assertTrue(f.successful());assertFalse(f.closeAdmissible());
        for(String key:List.of("list_found","list_visible","list_enabled")){n=token("available");source(n).put(key,false);reject(n);}
    }
    @Test void detailMustActuallyExistAndBeHiddenRatherThanClosedAsAnotherEffect()throws Exception{
        var n=token("available");source(n).put("detail_found",false);reject(n);n=token("available");source(n).put("detail_visible",true);reject(n);
    }
    @Test void incompleteCountsAndVisibleModalCannotAuthorizeTheFixedClose()throws Exception{
        var n=token("available");source(n).put("blocked_by_visible_modal",true);reject(n);n=token("available");source(n).put("complete_model_census",false).putNull("groups_count").putNull("total_model_rows").putArray("rows");reject(n);
    }
    @Test void completeSemanticCountsAreObservedDataWithoutHardCodedThirtySevenPolicy()throws Exception{
        var n=token("available");var s=source(n);s.put("groups_count",0).put("total_model_rows",0).putArray("rows");assertTrue(changed(n).closeAdmissible());n.put("close_admissible",false);assertTrue(changed(n).successful());
        s.put("complete_model_census",false).putNull("groups_count").putNull("total_model_rows");assertFalse(changed(n).source().orElseThrow().completeModelCensus());
    }
    @Test void nativeHandledFalseRemainsKnownDispatchAndNotAnUnknownOrClosedClaim()throws Exception{
        var f=frame("close-false");assertEquals(CurrentDecisionsCloseResult.Status.CLOSE_DISPATCHED,f.status());assertTrue(f.successful());assertTrue(f.effectAttempted());assertTrue(f.nativeReturned());assertFalse(f.nativeHandled());
        var n=token("close-true");n.put("native_returned",false);reject(n);
    }
    @Test void parsedCloseRefusalsKeepOriginalLeaseAndCanRetainSpentClaimZeroEffect()throws Exception{
        var n=token("stale");n.put("claim_sequence","1");var f=changed(n);assertFalse(f.successful());assertEquals(BigInteger.ONE,f.claimSequence());assertFalse(f.effectAttempted());n.put("query_sequence","0");reject(n);n=token("available");n.put("provider_generation","01");reject(n);
    }
    @Test void cleanupUnknownCannotAdvertiseSourceOrAnyCloseAdmission()throws Exception{
        var n=token("available");n.put("cleanup_known",false);reject(n);n=token("available");n.putNull("owner");reject(n);assertEquals(CurrentDecisionsCloseResult.Status.INDETERMINATE,frame("indeterminate").status());
    }
    @Test void queryClaimsAndPanelDateSavePostconditionsAreNeverSynthesized()throws Exception{
        var n=token("available");n.put("claim_sequence","1");reject(n);n=token("available");n.put("effect_attempted",true);reject(n);
        for(String key:List.of("panels_closed","new_date_observed","physical_save_confirmed")){n=token("close-true");n.put(key,true);reject(n);}
    }
    static void reject(ObjectNode n){assertThrows(IOException.class,()->changed(n));}
}
