package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Original compiled C++ tokens; all changed tokens below are explicit Java negative DATA. */
class NativeCurrentXqolPrompt26785313ProducerTest {
    static byte[] raw(String role)throws IOException{try(var in=NativeCurrentXqolPrompt26785313ProducerTest.class.getResourceAsStream("/current267-xqol-prompt-actual-cpp/"+role+".json")){if(in==null)throw new IOException("Actual C++ prompt resource absent: "+role);return in.readAllBytes();}}
    static ObjectNode envelope(String role)throws IOException{return NativeWire.object(NativeWire.parse(raw(role)));}
    static CurrentXqolPromptResult frame(String role)throws IOException{return changed(NativeWire.object(envelope(role).get("result")));}
    static CurrentXqolPromptResult changed(ObjectNode n)throws IOException{return CurrentXqolPromptResult.decode(new RawJson(StrictJson.canonical(n)));}
    static CoreFrame.Partial actualCore()throws IOException{return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,frame("available").factsBefore().orElseThrow());}
    static ObjectNode token(String role)throws IOException{return NativeWire.object(envelope(role).get("result"));}
    static ObjectNode source(ObjectNode n){return (ObjectNode)n.get("source");}
    static ObjectNode event(ObjectNode n){return (ObjectNode)n.get("source").get("event");}
    static ObjectNode option(ObjectNode n,int i){return (ObjectNode)event(n).get("options").get(i);}
    @Test void genuineResultsRoundtripTheExact25FieldsAndKeepAllPostEffectClaimsFalse()throws Exception {
        for(String role:List.of("available","confirm","cancel","empty","can-false","stale","expired","indeterminate")){var f=frame(role);assertEquals(f,CurrentXqolPromptResult.decode(f.encode()),role);assertEquals(envelope(role).get("ok").booleanValue(),f.successful());}
        for(String role:List.of("confirm","cancel")){var f=frame(role);assertTrue(f.effectAttempted());assertTrue(f.nativeReturned());assertEquals(frame("available").source(),f.source());assertEquals(frame("available").owner(),f.owner());var n=StrictJson.parse(f.encode().bytes(),1<<20);assertEquals(25,n.size());for(String k:List.of("native_handled","event_closed","conversion_applied","new_date_observed","physical_save_confirmed"))assertFalse(n.get(k).booleanValue(),k);}
    }
    @Test void threeFixedRequestEncodersMatchActualCppRequestRolesWithoutCallerAuthority()throws Exception {
        var q=frame("available");for(var a:CurrentXqolPrompt.Action.values()){
            boolean query=a==CurrentXqolPrompt.Action.QUERY_PROMPT;String role=query?"query-request":a==CurrentXqolPrompt.Action.CONFIRM_CONVERSION?"confirm-request":"cancel-request";
            var cpp=envelope(role);assertEquals(8,cpp.size());assertEquals(a.step(),cpp.get("step").textValue());assertEquals(0,cpp.get("arguments").size());
            var req=CurrentXqolPrompt.request(actualCore(),a,query?BigInteger.ZERO:q.providerGeneration(),query?BigInteger.ZERO:q.querySequence(),query?Optional.empty():Optional.of(q.source().orElseThrow().event().orElseThrow().instanceId()));
            var fields=NativeWire.object(NativeWire.parse(req.additionalFields().bytes()));assertEquals(Set.of("arguments","xqol_prompt"),names(fields));assertEquals(10,fields.get("xqol_prompt").size());assertEquals(a.wire(),fields.get("xqol_prompt").get("action").textValue());assertEquals(query,fields.get("xqol_prompt").get("instance_id").isNull());
        }
        assertThrows(IllegalArgumentException.class,()->CurrentXqolPrompt.request(actualCore(),CurrentXqolPrompt.Action.QUERY_PROMPT,BigInteger.ONE,BigInteger.ONE,Optional.empty()));
        assertThrows(IllegalArgumentException.class,()->CurrentXqolPrompt.request(actualCore(),CurrentXqolPrompt.Action.CANCEL_CONVERSION,BigInteger.ZERO,BigInteger.ZERO,Optional.of(1)));
    }
    @Test void exactSchemasBuildAndClosedResultKeySetAreRequired()throws Exception {
        for(String k:List.of("schema","game_version","executable_sha256","backend","adapter_id")){var n=token("available");n.put(k,"unqualified");reject(n);}
        for(String k:List.of("caller_can_select","ordinal","conversion_confirmed")){var n=token("available");n.put(k,true);reject(n);}
        var n=token("available");source(n).put("schema","old");reject(n);n=token("available");event(n).put("schema","old");reject(n);
    }
    @Test void absentFixedEventDoesNotPretendOtherResidentEventsAreEmpty()throws Exception {
        var f=frame("empty");var s=f.source().orElseThrow();assertTrue(s.event().isEmpty());assertTrue(s.authoredOptionCount().isEmpty());assertFalse(s.confirmAdmissible());assertFalse(s.cancelAdmissible());
        var n=token("empty");source(n).put("resident_count",3).put("named_root_count",2);assertTrue(changed(n).source().orElseThrow().event().isEmpty());source(n).put("authored_option_count",2);reject(n);
    }
    @Test void actualNativeCanFalseIsAValidReadonlyObservationWithoutConfirmAuthority()throws Exception {
        var f=frame("can-false");assertTrue(f.successful());assertFalse(f.source().orElseThrow().confirmAdmissible());
        var n=token("can-false");source(n).put("confirm_admissible",true);reject(n);n=token("available");option(n,0).putNull("native_can_select");reject(n);
    }
    @Test void optionMappingUsesActualAuthoredIndicesRatherThanDisplayedOrder()throws Exception {
        var n=token("available");var a=(com.fasterxml.jackson.databind.node.ArrayNode)event(n).get("options");var first=a.remove(0);a.add(first);assertTrue(changed(n).source().orElseThrow().confirmAdmissible());
        option(n,0).put("source_bound_option_key",CurrentXqolPrompt.CONFIRM_OPTION);reject(n);
    }
    @Test void censusCountsUniqueIndicesAndKnownDefinitionCannotBeInvented()throws Exception {
        var n=token("available");source(n).put("census_complete",false);reject(n);n=token("available");source(n).put("authored_option_count",1);reject(n);
        n=token("available");option(n,1).put("authored_option_index",0);reject(n);n=token("available");event(n).put("definition_key","other.1");reject(n);n=token("available");event(n).put("known_definition_verified",false);reject(n);
    }
    @Test void cachedTextKeepsEmptyOpeningAndRichtextWithoutInterpretingOrTrimming()throws Exception {
        var n=token("available");event(n).put("opening","").put("description","\u0015 exact ERROR:[scope] ");option(n,0).put("text","").put("disabled_reason","");var f=changed(n);assertEquals("\u0015 exact ERROR:[scope] ",CurrentXqolPromptResult.decode(f.encode()).source().orElseThrow().event().orElseThrow().description());event(n).put("description","x".repeat(16385));reject(n);
    }
    @Test void originalLeaseIsCanonicalUint64AndActionInstanceMustMatchItsSource()throws Exception {
        for(String s:List.of("01","-1","18446744073709551616")){var n=token("available");n.put("provider_generation",s);reject(n);}
        var n=token("confirm");n.put("instance_id",8);reject(n);n=token("available");n.put("query_sequence",1);reject(n);n=token("available");n.put("instance_id",7);reject(n);
    }
    @Test void knownZeroEffectRefusalMayRetainASpentClaimButNoCallback()throws Exception {
        var n=token("stale");n.put("claim_sequence","1");var f=changed(n);assertFalse(f.successful());assertFalse(f.effectAttempted());assertFalse(f.nativeReturned());assertEquals(BigInteger.ONE,f.claimSequence());n.put("effect_attempted",true);reject(n);
    }
    @Test void cleanupUnknownAndVoidCallbacksNeverGrantAppliedOrClosedPostconditions()throws Exception {
        var n=token("available");n.put("cleanup_known",false);reject(n);assertEquals(CurrentXqolPromptResult.Status.INDETERMINATE,frame("indeterminate").status());
        for(String k:List.of("native_handled","event_closed","conversion_applied","new_date_observed","physical_save_confirmed")){n=token("confirm");n.put(k,true);reject(n);}
    }
    @Test void currentRecipientCoreAndOwnerMustRemainActualAndCoherent()throws Exception {
        var n=token("available");event(n).put("recipient_character_id",123);reject(n);n=token("available");((ObjectNode)n.get("facts_before")).put("paused",false);reject(n);n=token("available");((ObjectNode)n.get("owner")).put("connection_generation","0");reject(n);n=token("cancel");n.put("action","confirm_conversion");reject(n);
    }
    static void reject(ObjectNode n){assertThrows(IOException.class,()->changed(n));}
    static Set<String> names(ObjectNode n){var keys=new java.util.HashSet<String>();n.fieldNames().forEachRemaining(keys::add);return Set.copyOf(keys);}
}
