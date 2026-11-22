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

/** Positive tokens are original compiled C++ DATA; changed tokens are explicitly Java contract-negative DATA. */
class NativeCurrentCourtierControls26785313ProducerTest {
    static byte[] raw(String role)throws IOException{try(var in=NativeCurrentCourtierControls26785313ProducerTest.class.getResourceAsStream("/current267-courtier-controls-actual-cpp/"+role+".json")){if(in==null)throw new IOException("Actual C++ courtier resource absent: "+role);return in.readAllBytes();}}
    static ObjectNode envelope(String role)throws IOException{return NativeWire.object(NativeWire.parse(raw(role)));}
    static ObjectNode token(String role)throws IOException{return NativeWire.object(envelope(role).get("result"));}
    static CurrentCourtierControlsResult frame(String role)throws IOException{return changed(token(role));}
    static CurrentCourtierControlsResult changed(ObjectNode n)throws IOException{return CurrentCourtierControlsResult.decode(new RawJson(StrictJson.canonical(n)));}
    static ObjectNode source(ObjectNode n){return (ObjectNode)n.get("source");}
    static CoreFrame.Partial actualCore()throws IOException{return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,frame("available").factsBefore().orElseThrow());}
    static CurrentCourtierControls.Product product()throws IOException{return frame("available").product();}
    static CurrentCourtierControls.Control control()throws IOException{return frame("available").control();}
    @Test void actualCppResultsRoundtripExact27KeysWithoutInventingVoidPostconditions()throws Exception{
        var index=NativeWire.object(NativeWire.parse(raw("index")));for(var name:index.get("result_roles")){String role=name.textValue();var f=frame(role);assertEquals(f,CurrentCourtierControlsResult.decode(f.encode()));assertEquals(envelope(role).get("ok").booleanValue(),f.successful());}
        var n=StrictJson.parse(frame("execute").encode().bytes(),1<<20);assertEquals(27,n.size());for(String key:List.of("native_handled","creator_closed","courtier_created","age_changed","new_date_observed","physical_save_confirmed"))assertFalse(n.get(key).booleanValue(),key);
    }
    @Test void allEightFixedProductControlsEncodeOnlyExactElevenClaimFields()throws Exception{
        var f=frame("available");for(var product:CurrentCourtierControls.Product.values())for(var control:CurrentCourtierControls.Control.values())for(var action:CurrentCourtierControls.Action.values()){
            boolean query=action==CurrentCourtierControls.Action.QUERY_CONTROL;var r=CurrentCourtierControls.request(actualCore(),action,query?BigInteger.ZERO:f.providerGeneration(),query?BigInteger.ZERO:f.querySequence(),product,control);var n=NativeWire.object(NativeWire.parse(r.additionalFields().bytes()));assertEquals(2,n.size());assertEquals(0,n.get("arguments").size());var c=n.get("courtier_controls");assertEquals(11,c.size());assertEquals(product.wire(),c.get("product").textValue());assertEquals(control.wire(),c.get("control").textValue());assertEquals(action.step(),r.step());assertFalse(c.has("age"));assertFalse(c.has("actor"));assertFalse(c.has("instance_id"));}
        assertThrows(IllegalArgumentException.class,()->CurrentCourtierControls.request(actualCore(),CurrentCourtierControls.Action.EXECUTE_CONTROL,BigInteger.ZERO,BigInteger.ZERO,product(),control()));
    }
    @Test void fixedEnumParsersRejectKeysOrdinalsAndArbitraryScopeOrScripts()throws Exception{
        for(String value:List.of("MAIN","Main","xqol","0","other","main.confirm"))assertThrows(IOException.class,()->CurrentCourtierControls.Product.parse(value));
        for(String value:List.of("age","0","age_plus_2","execute","xar_custom_script"))assertThrows(IOException.class,()->CurrentCourtierControls.Control.parse(value));
        assertThrows(IOException.class,()->CurrentCourtierControls.Action.parse("query"));assertThrows(IOException.class,()->CurrentCourtierControls.Action.parse("execute"));
    }
    @Test void exactIdentityAndResultOrSourceFieldSetsCannotAcceptCallerAuthority()throws Exception{
        for(String key:List.of("schema","game_version","executable_sha256","backend","adapter_id")){var n=token("available");n.put(key,"wrong");reject(n);}
        var n=token("available");source(n).put("caller_can_execute",true);reject(n);n=token("available");n.put("ordinal",0);reject(n);n=token("available");source(n).put("schema","old");reject(n);
    }
    @Test void sourceProductAndControlMustMatchTheActualResultRatherThanItsCaption()throws Exception{
        var n=token("available");n.put("product",product()==CurrentCourtierControls.Product.MAIN?"vivhite":"main");reject(n);n=token("available");source(n).put("control",control()==CurrentCourtierControls.Control.CONFIRM?"cancel":"confirm");reject(n);
    }
    @Test void absentCreatorRequiresCompleteConfirmationInventoryAndUnobservedPredicates()throws Exception{
        var n=token("available");var s=source(n);s.put("creator_window_found",false).put("modal_found",false).put("panel_found",false).put("window_visible",false).put("window_enabled",false).put("execute_admissible",false).putNull("native_definition_found").putNull("native_shown").putNull("native_valid");
        assertFalse(changed(n).source().orElseThrow().creatorWindowFound());s.put("confirmation_layer_found",false);reject(n);s.put("confirmation_layer_found",true).put("native_shown",false);reject(n);
    }
    @Test void partiallyMaterializedCreatorCannotBecomeAnAvailableCompleteSource()throws Exception{
        for(String key:List.of("modal_found","panel_found")){var n=token("available");source(n).put("execute_admissible",false).put(key,false);reject(n);}var n=token("available");source(n).put("execute_admissible",false).putNull("native_definition_found");reject(n);
    }
    @Test void missingDefinitionKeepsShownAndValidNullAndNeverCallsScriptedGui()throws Exception{
        var n=token("available");source(n).put("native_definition_found",false).put("execute_admissible",false).putNull("native_shown").putNull("native_valid");assertFalse(changed(n).source().orElseThrow().nativeDefinitionFound().orElseThrow());source(n).put("native_valid",false);reject(n);
    }
    @Test void actualNegativeShownOrValidRemainReadableButNeverAdmitExecute()throws Exception{
        for(String key:List.of("native_shown","native_valid")){var n=token("available");source(n).put(key,false).put("execute_admissible",false);assertTrue(changed(n).successful());source(n).put("execute_admissible",true);reject(n);}
        var n=token("available");source(n).put("execute_admissible",false);assertFalse(changed(n).source().orElseThrow().executeAdmissible());
    }
    @Test void hiddenOrDisabledChainsDoNotAcquirePermissionFromOtherTrueFlags()throws Exception{
        for(String key:List.of("window_visible","window_enabled")){var n=token("available");source(n).put(key,false).put("execute_admissible",false);assertTrue(changed(n).successful());source(n).put("execute_admissible",true);reject(n);}
    }
    @Test void originalLeaseAndSpentClaimZeroEffectRefusalRemainKnownWithoutRetry()throws Exception{
        var n=token("stale");n.put("claim_sequence","1");var f=changed(n);assertFalse(f.successful());assertFalse(f.effectAttempted());assertFalse(f.nativeReturned());assertEquals(BigInteger.ONE,f.claimSequence());n.put("effect_attempted",true);reject(n);
        n=token("execute");n.put("query_sequence","0");reject(n);n=token("available");n.put("provider_generation","01");reject(n);
    }
    @Test void cleanupUnknownCoreOwnerRolesOrVoidPoststateClaimsCannotBecomeSuccess()throws Exception{
        var n=token("available");n.put("cleanup_known",false);reject(n);n=token("available");n.putNull("owner");reject(n);
        for(String key:List.of("native_handled","creator_closed","courtier_created","age_changed","new_date_observed","physical_save_confirmed")){n=token("execute");n.put(key,true);reject(n);}
        assertEquals(CurrentCourtierControlsResult.Status.INDETERMINATE,frame("indeterminate").status());
    }
    static void reject(ObjectNode n){assertThrows(IOException.class,()->changed(n));}
}
