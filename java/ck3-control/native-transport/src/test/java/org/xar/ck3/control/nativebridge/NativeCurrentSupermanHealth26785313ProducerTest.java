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

/** Original compiled C++ tokens are positive DATA; all mutations below are Java negative contract DATA. */
class NativeCurrentSupermanHealth26785313ProducerTest {
    static byte[] raw(String role)throws IOException{try(var in=NativeCurrentSupermanHealth26785313ProducerTest.class.getResourceAsStream("/current267-superman-health-actual-cpp/"+role+".json")){if(in==null)throw new IOException("Actual C++ health resource absent: "+role);return in.readAllBytes();}}
    static ObjectNode envelope(String role)throws IOException{return NativeWire.object(NativeWire.parse(raw(role)));}
    static ObjectNode token(String role)throws IOException{return NativeWire.object(envelope(role).get("result"));}
    static ObjectNode source(ObjectNode token){return (ObjectNode)token.get("source");}
    static CurrentSupermanHealthResult changed(ObjectNode token)throws IOException{return CurrentSupermanHealthResult.decode(new RawJson(StrictJson.canonical(token)));}
    static CurrentSupermanHealthResult frame(String role)throws IOException{return changed(token(role));}
    static String queryRole(CurrentSupermanHealth.Phase p){return p==CurrentSupermanHealth.Phase.BASELINE?"baseline-query":"completed-query";}
    static String choiceRole(CurrentSupermanHealth.Phase p){return p==CurrentSupermanHealth.Phase.BASELINE?"baseline-choose":"completed-choose";}
    static CoreFrame.Partial actualCore(CurrentSupermanHealth.Phase p)throws IOException{return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,frame(queryRole(p)).factsBefore().orElseThrow());}
    static ObjectNode values(ObjectNode n){return (ObjectNode)source(n).get("characters").get(0).get("values");}
    static void reject(ObjectNode n){assertThrows(IOException.class,()->changed(n));}
    @Test void allActualCppTokensRoundtripExactTwentySixResultFields()throws Exception{
        for(var name:envelope("index").get("result_roles")){String role=name.textValue();var f=frame(role);assertEquals(f,CurrentSupermanHealthResult.decode(f.encode()));assertEquals(envelope(role).get("ok").booleanValue(),f.successful());assertEquals(26,NativeWire.parse(f.encode().bytes()).size());}
    }
    @Test void queryAndChoiceClaimsOnlyFixedPhaseAndTenFields()throws Exception{
        for(var phase:CurrentSupermanHealth.Phase.values())for(var action:CurrentSupermanHealth.Action.values()){
            var f=frame(queryRole(phase));boolean q=action==CurrentSupermanHealth.Action.QUERY_HEALTH;var r=CurrentSupermanHealth.request(actualCore(phase),action,q?BigInteger.ZERO:f.providerGeneration(),q?BigInteger.ZERO:f.querySequence(),phase);var n=NativeWire.parse(r.additionalFields().bytes());assertEquals(2,n.size());assertEquals(0,n.get("arguments").size());var c=n.get("superman_health");assertEquals(10,c.size());assertEquals(phase.wire(),c.get("phase").textValue());assertFalse(c.has("instance_id"));assertFalse(c.has("option_key"));assertFalse(c.has("character_id"));assertFalse(c.has("saved"));assertEquals(action.step(),r.step());}
        assertThrows(IllegalArgumentException.class,()->CurrentSupermanHealth.request(actualCore(CurrentSupermanHealth.Phase.BASELINE),CurrentSupermanHealth.Action.CHOOSE_KNOWN,BigInteger.ZERO,BigInteger.ZERO,CurrentSupermanHealth.Phase.BASELINE));
    }
    @Test void phaseAndActionRejectCallerKeysIndicesOrArbitraryScripts()throws Exception{
        for(String s:List.of("BASELINE","sxat.2","begin","0","done"))assertThrows(IOException.class,()->CurrentSupermanHealth.Phase.parse(s));
        for(String s:List.of("query","sxat_health_begin","select","execute_script"))assertThrows(IOException.class,()->CurrentSupermanHealth.Action.parse(s));
    }
    @Test void allFortyActualReferencesHaveExactCaseAndRoleOrder()throws Exception{
        var f=frame("baseline-query");var s=f.source().orElseThrow();assertEquals(40,s.referenceCount());assertEquals(f.factsBefore().orElseThrow().playedCharacterId(),s.characters().get(0).characterId());
        for(int i=0;i<40;i++){assertEquals(CurrentSupermanHealthSource.CASE_KEYS.get(i/2),s.characters().get(i).caseKey());assertEquals(i%2==0?CurrentSupermanHealthSource.Role.RECEIVER:CurrentSupermanHealthSource.Role.DONOR,s.characters().get(i).role());assertEquals(14,s.characters().get(i).values().size());}
    }
    @Test void missingPartialDuplicateOrReorderedReferenceCannotBecomeAvailable()throws Exception{
        var n=token("baseline-query");source(n).put("reference_count",39);reject(n);n=token("baseline-query");((com.fasterxml.jackson.databind.node.ArrayNode)source(n).get("characters")).remove(39);reject(n);
        n=token("baseline-query");((ObjectNode)source(n).get("characters").get(1)).put("character_id",source(n).get("characters").get(0).get("character_id").intValue());reject(n);
        n=token("baseline-query");((ObjectNode)source(n).get("characters").get(2)).put("case_key",CurrentSupermanHealthSource.CASE_KEYS.get(0));reject(n);
    }
    @Test void completeFullSignedIdsAllowZeroAndGenerationNegativeButNeverMinusOne()throws Exception{
        assertTrue(frame("baseline-query").source().orElseThrow().characters().stream().anyMatch(c->c.characterId()==0));
        for(int id:new int[]{Integer.MIN_VALUE,-2}){var n=token("baseline-query");((ObjectNode)source(n).get("characters").get(39)).put("character_id",id);assertTrue(changed(n).successful());}
        var n=token("baseline-query");((ObjectNode)source(n).get("characters").get(39)).put("character_id",-1);reject(n);
    }
    @Test void signedRawFourteenKeepExactBoundariesAndZeroWithoutScaleOrFloat()throws Exception{
        var n=token("baseline-query");values(n).put("sxad_health_value",Long.toString(Long.MIN_VALUE)).put("sxad_health_balance_value",Long.toString(Long.MAX_VALUE)).put("sxad_diplomacy_value","0");var f=changed(n);assertEquals(Long.MIN_VALUE,f.source().orElseThrow().characters().get(0).values().get("sxad_health_value").longValue());assertEquals(f,CurrentSupermanHealthResult.decode(f.encode()));
        for(String bad:List.of("-0","01","+1","1.0"," 1","9223372036854775808","-9223372036854775809")){n=token("baseline-query");values(n).put("sxad_health_value",bad);reject(n);}n=token("baseline-query");values(n).put("sxad_health_value",75);reject(n);
    }
    @Test void eachMissingNativeValueRejectsWholeSourceInsteadOfInventingZero()throws Exception{
        for(var key:CurrentSupermanHealthSource.VALUE_NAMES){var n=token("baseline-query");values(n).putNull(key);reject(n);n=token("baseline-query");values(n).remove(key);reject(n);}
    }
    @Test void schemaFieldSetsAndCoreActorOrPhaseNeverAcceptBorrowedPermission()throws Exception{
        var n=token("baseline-query");source(n).put("caller_saved",true);reject(n);n=token("baseline-query");n.put("ordinal",0);reject(n);n=token("baseline-query");source(n).put("phase","completed");reject(n);
        n=token("baseline-query");((ObjectNode)n.get("facts_before")).put("played_character_id",123456);reject(n);
        for(String key:List.of("schema","game_version","executable_sha256","adapter_id","backend")){n=token("baseline-query");n.put(key,"wrong");reject(n);}
    }
    @Test void fixedEventAbsenceIsNotAnEmptyGlobalEventManager()throws Exception{
        var n=token("absent");assertFalse(changed(n).source().orElseThrow().eventFound());source(n).put("named_root_count",3);assertFalse(changed(n).source().orElseThrow().eventFound());source(n).put("window_visible",true);reject(n);
    }
    @Test void phaseMarkerNativeCanAndWindowNegativesStayReadableWithoutMinting()throws Exception{
        for(String key:List.of("window_visible","window_enabled","named_root_bound")){var n=token("baseline-query");source(n).put("native_choice_admissible",false).put(key,false);assertTrue(changed(n).successful());source(n).put("native_choice_admissible",true);reject(n);}
        var n=token("baseline-query");source(n).put("native_choice_admissible",false).putNull("baseline_ready_raw");assertTrue(changed(n).successful());source(n).put("native_choice_admissible",true);reject(n);
        n=token("baseline-query");source(n).put("native_choice_admissible",false);((ObjectNode)source(n).get("options").get(0)).put("native_can_select",false);assertTrue(changed(n).successful());source(n).put("native_choice_admissible",true);reject(n);
    }
    @Test void eventAndSoleOptionMustBeActualReviewedPhaseAndRecipient()throws Exception{
        var n=token("baseline-query");source(n).put("definition_key","sxat.4");reject(n);n=token("baseline-query");source(n).put("recipient_character_id",123456);reject(n);
        n=token("baseline-query");((ObjectNode)source(n).get("options").get(0)).put("source_bound_option_key","arbitrary");reject(n);n=token("baseline-query");((ObjectNode)source(n).get("options").get(0)).put("authored_option_index",1);reject(n);
    }
    @Test void emptyUtf8TextAndActualRichtextArePreservedAndByteBounded()throws Exception{
        var n=token("baseline-query");source(n).put("opening","").put("description","\u0015actual rich text");((ObjectNode)source(n).get("options").get(0)).put("text","").put("disabled_reason","");assertEquals("",changed(n).source().orElseThrow().opening().orElseThrow());assertTrue(changed(n).source().orElseThrow().description().orElseThrow().startsWith("\u0015"));
        source(n).put("opening","界".repeat(5462));reject(n);
    }
    @Test void knownSpentClaimZeroEffectRetainsLeaseAndCannotTurnIntoDispatched()throws Exception{
        var n=token("stale");n.put("claim_sequence","1");var f=changed(n);assertFalse(f.successful());assertFalse(f.effectAttempted());assertFalse(f.nativeReturned());assertEquals(BigInteger.ONE,f.claimSequence());n.put("effect_attempted",true);reject(n);
        n=token("baseline-choose");n.put("query_sequence","0");reject(n);n=token("baseline-query");n.put("provider_generation","01");reject(n);
    }
    @Test void unknownCleanupOrMismatchedNullableRolesCannotForgeActualSource()throws Exception{
        var n=token("baseline-query");n.put("cleanup_known",false);reject(n);n=token("baseline-query");n.putNull("owner");reject(n);assertEquals(CurrentSupermanHealthResult.Status.INDETERMINATE,frame("indeterminate").status());
    }
    @Test void voidDispatchNeverProvesChangedHealthRenderDateSaveOrClosedEvent()throws Exception{
        for(String key:List.of("native_handled","event_closed","health_changed","trait_UI_rendered","new_date_observed","physical_save_confirmed")){var n=token("baseline-choose");n.put(key,true);reject(n);}
        var n=token("baseline-query");n.put("effect_attempted",true);reject(n);
    }
}
