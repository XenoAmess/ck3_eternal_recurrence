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

/** Genuine native serializer DATA; explicitly changed tokens are Java negative observations only. */
class NativeCurrentXqolThreshold26785313ProducerTest {
    static byte[] raw(String role)throws IOException{try(var in=NativeCurrentXqolThreshold26785313ProducerTest.class.getResourceAsStream("/current267-xqol-threshold-actual-cpp/"+role+".json")){if(in==null)throw new IOException("Actual C++ threshold resource absent: "+role);return in.readAllBytes();}}
    static ObjectNode envelope(String role)throws IOException{return NativeWire.object(NativeWire.parse(raw(role)));}
    static ObjectNode token(String role)throws IOException{return NativeWire.object(envelope(role).get("result"));}
    static CurrentXqolThresholdResult frame(String role)throws IOException{return changed(token(role));}
    static CurrentXqolThresholdResult changed(ObjectNode n)throws IOException{return CurrentXqolThresholdResult.decode(new RawJson(StrictJson.canonical(n)));}
    static CoreFrame.Partial actualCore()throws IOException{return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,frame("available").factsBefore().orElseThrow());}
    static int target()throws IOException{return frame("available").source().orElseThrow().targetThreshold();}
    static ObjectNode source(ObjectNode n){return (ObjectNode)n.get("source");}
    static ObjectNode prompt(ObjectNode n){return (ObjectNode)n.get("source").get("prompt");}
    static ObjectNode event(ObjectNode n){return (ObjectNode)prompt(n).get("event");}
    @Test void nineGenuineResultsRoundtrip26KeysAndAllPostconditionsStayFalse()throws Exception{
        for(String role:List.of("available","set","empty","shown-false","valid-false","stale","expired","consumed","indeterminate")){var f=frame(role);assertEquals(f,CurrentXqolThresholdResult.decode(f.encode()));assertEquals(envelope(role).get("ok").booleanValue(),f.successful());}
        var n=StrictJson.parse(frame("set").encode().bytes(),1<<20);assertEquals(26,n.size());for(String k:List.of("native_handled","threshold_applied","event_closed","conversion_applied","new_date_observed","physical_save_confirmed"))assertFalse(n.get(k).booleanValue(),k);
    }
    @Test void requestHasOnlyExactElevenFieldsAndTargetIsDataInteger0Through100()throws Exception{
        var q=frame("available");for(var a:CurrentXqolThreshold.Action.values()){boolean query=a==CurrentXqolThreshold.Action.QUERY_THRESHOLD;var cpp=envelope(query?"query-request":"set-request");assertEquals(8,cpp.size());assertEquals(a.step(),cpp.get("step").textValue());assertEquals(11,cpp.get("xqol_threshold").size());
            for(int value:new int[]{0,100}){var req=CurrentXqolThreshold.request(actualCore(),a,query?BigInteger.ZERO:q.providerGeneration(),query?BigInteger.ZERO:q.querySequence(),query?Optional.empty():q.source().orElseThrow().prompt().event().map(e->e.instanceId()),value);var fields=NativeWire.object(NativeWire.parse(req.additionalFields().bytes()));assertEquals(11,fields.get("xqol_threshold").size());assertEquals(value,fields.get("xqol_threshold").get("target_threshold").intValue());assertEquals(0,fields.get("arguments").size());}}
        for(int invalid:new int[]{-1,101,Integer.MAX_VALUE})assertThrows(IllegalArgumentException.class,()->CurrentXqolThreshold.request(actualCore(),CurrentXqolThreshold.Action.QUERY_THRESHOLD,BigInteger.ZERO,BigInteger.ZERO,Optional.empty(),invalid));
        assertThrows(IllegalArgumentException.class,()->CurrentXqolThreshold.request(actualCore(),CurrentXqolThreshold.Action.SET_THRESHOLD,BigInteger.ZERO,BigInteger.ZERO,Optional.of(1),50));
    }
    @Test void exactIdentitiesAndClosedResultAndSourceKeySetsRejectCallerAuthority()throws Exception{
        for(String k:List.of("schema","game_version","executable_sha256","backend","adapter_id")){var n=token("available");n.put(k,"wrong");reject(n);}
        var n=token("available");source(n).put("caller_valid",true);reject(n);n=token("available");source(n).put("schema","old");reject(n);n=token("available");prompt(n).put("schema","old");reject(n);
    }
    @Test void noKnownPromptKeepsAllScrollbarAndPredicateRolesUnobserved()throws Exception{
        var s=frame("empty").source().orElseThrow();assertTrue(s.prompt().event().isEmpty());assertTrue(s.observedValue().isEmpty());assertTrue(s.nativeShown().isEmpty());assertTrue(s.nativeValid().isEmpty());assertFalse(s.setAdmissible());
        var n=token("empty");source(n).put("value_bits_u32","0");reject(n);n=token("empty");source(n).put("native_shown",false);reject(n);
    }
    @Test void actualShownFalseAndValidFalseAreReadableButDoNotGrantSet()throws Exception{
        assertEquals(Optional.of(false),frame("shown-false").source().orElseThrow().nativeShown());assertEquals(Optional.of(false),frame("valid-false").source().orElseThrow().nativeValid());
        for(String role:List.of("shown-false","valid-false")){assertTrue(frame(role).successful());assertFalse(frame(role).source().orElseThrow().setAdmissible());var n=token(role);source(n).put("set_admissible",true);reject(n);}
        var n=token("available");source(n).put("native_fixed_route_found",false).put("set_admissible",false);reject(n);source(n).putNull("native_shown").putNull("native_valid");assertFalse(changed(n).source().orElseThrow().nativeFixedRouteFound());
    }
    @Test void bitStringsKeepExactUInt32PatternAndRejectNaNInfinityOrOutOfRangeValue()throws Exception{
        var s=frame("available").source().orElseThrow();assertEquals(s,CurrentXqolThresholdResult.decode(frame("available").encode()).source().orElseThrow());assertTrue(s.observedValue().filter(Float::isFinite).isPresent());
        for(String bad:List.of("01","-1","4294967296","2143289344","2139095040","3267887104")){var n=token("available");source(n).put("value_bits_u32",bad);reject(n);}var n=token("available");source(n).put("value_bits_u32",0);reject(n);
    }
    @Test void rangeAndStepRequireActualExactFloatPatternsWithoutSynthesizedDefaults()throws Exception{
        for(String k:List.of("minimum_bits_u32","maximum_bits_u32","step_bits_u32")){var n=token("available");source(n).putNull(k);reject(n);}
        var n=token("available");source(n).put("minimum_bits_u32","2147483648");reject(n);n=token("available");source(n).put("maximum_bits_u32","0");reject(n);n=token("available");source(n).put("step_bits_u32","0");reject(n);
    }
    @Test void sliderRouteAdmissionDoesNotBorrowTheSeparateConfirmOrCancelNativeCan()throws Exception{
        var n=token("available");var p=prompt(n);p.put("confirm_admissible",false).put("cancel_admissible",false);for(var o:event(n).get("options"))((ObjectNode)o).put("native_can_select",false);assertTrue(changed(n).source().orElseThrow().setAdmissible());
        source(n).put("set_admissible",false);assertFalse(changed(n).source().orElseThrow().setAdmissible());
    }
    @Test void targetAndMaterialScrollbarFlagsCannotBeInvented()throws Exception{
        for(String k:List.of("scrollbar_found","handle_found")){var n=token("available");source(n).put(k,false);reject(n);}var n=token("available");source(n).put("target_threshold",101);reject(n);n=token("available");source(n).put("target_threshold",50.5);var rawFloat=new RawJson(n.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));assertThrows(IOException.class,()->CurrentXqolThresholdResult.decode(rawFloat));
    }
    @Test void originalLeaseRecipientAndSameInstanceMustRemainCoherent()throws Exception{
        var n=token("available");n.put("provider_generation","01");reject(n);n=token("set");n.put("instance_id",Integer.MAX_VALUE);reject(n);n=token("available");event(n).put("recipient_character_id",123);reject(n);n=token("available");((ObjectNode)n.get("facts_before")).put("paused",false);reject(n);
    }
    @Test void knownZeroEffectRefusalCanSpendClaimButNeverBecomeACompletedThreshold()throws Exception{
        var n=token("stale");n.put("claim_sequence","1");var f=changed(n);assertFalse(f.successful());assertFalse(f.effectAttempted());assertFalse(f.nativeReturned());assertEquals(BigInteger.ONE,f.claimSequence());n.put("effect_attempted",true);reject(n);
    }
    @Test void cleanupUnknownOrVoidPoststateClaimsCannotBeAccepted()throws Exception{
        var n=token("available");n.put("cleanup_known",false);reject(n);assertEquals(CurrentXqolThresholdResult.Status.INDETERMINATE,frame("indeterminate").status());
        for(String k:List.of("native_handled","threshold_applied","event_closed","conversion_applied","new_date_observed","physical_save_confirmed")){n=token("set");n.put(k,true);reject(n);}
    }
    static void reject(ObjectNode n){assertThrows(IOException.class,()->changed(n));}
}
