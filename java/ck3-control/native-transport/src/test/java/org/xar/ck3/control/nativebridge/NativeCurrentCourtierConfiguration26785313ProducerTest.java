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
class NativeCurrentCourtierConfiguration26785313ProducerTest {
    static byte[] raw(String role)throws IOException{try(var in=NativeCurrentCourtierConfiguration26785313ProducerTest.class.getResourceAsStream("/current267-courtier-configuration-actual-cpp/"+role+".json")){if(in==null)throw new IOException("Actual C++ courtier resource absent: "+role);return in.readAllBytes();}}
    static ObjectNode envelope(String role)throws IOException{return NativeWire.object(NativeWire.parse(raw(role)));}
    static ObjectNode token(String role)throws IOException{return NativeWire.object(envelope(role).get("result"));}
    static CurrentCourtierConfigurationResult frame(String role)throws IOException{return changed(token(role));}
    static CurrentCourtierConfigurationResult changed(ObjectNode n)throws IOException{return CurrentCourtierConfigurationResult.decode(new RawJson(StrictJson.canonical(n)));}
    static ObjectNode source(ObjectNode n){return (ObjectNode)n.get("source");}
    static CoreFrame.Partial actualCore()throws IOException{return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,frame("available").factsBefore().orElseThrow());}
    static CurrentCourtierControls.Product product()throws IOException{return frame("available").product();}
    static CurrentCourtierConfiguration.Setting setting()throws IOException{return frame("available").setting();}
    @Test void actualCppResultsRoundtripExact27KeysWithoutInventingVoidPostconditions()throws Exception{
        var index=NativeWire.object(NativeWire.parse(raw("index")));for(var name:index.get("result_roles")){String role=name.textValue();var f=frame(role);assertEquals(f,CurrentCourtierConfigurationResult.decode(f.encode()));assertEquals(envelope(role).get("ok").booleanValue(),f.successful());}
        var n=StrictJson.parse(frame("execute").encode().bytes(),1<<20);assertEquals(27,n.size());for(String key:List.of("native_handled","creator_closed","courtier_created","age_changed","new_date_observed","physical_save_confirmed"))assertFalse(n.get(key).booleanValue(),key);
    }
    @Test void allEightFixedProductSettingsEncodeOnlyExactElevenClaimFields()throws Exception{
        var f=frame("available");for(var product:CurrentCourtierControls.Product.values())for(var setting:CurrentCourtierConfiguration.Setting.values())for(var action:CurrentCourtierConfiguration.Action.values()){
            boolean query=action==CurrentCourtierConfiguration.Action.QUERY_CONFIGURATION;var r=CurrentCourtierConfiguration.request(actualCore(),action,query?BigInteger.ZERO:f.providerGeneration(),query?BigInteger.ZERO:f.querySequence(),product,setting);var n=NativeWire.object(NativeWire.parse(r.additionalFields().bytes()));assertEquals(2,n.size());assertEquals(0,n.get("arguments").size());var c=n.get("courtier_configuration");assertEquals(11,c.size());assertEquals(product.wire(),c.get("product").textValue());assertEquals(setting.wire(),c.get("setting").textValue());assertEquals(action.step(),r.step());assertFalse(c.has("age"));assertFalse(c.has("actor"));assertFalse(c.has("instance_id"));}
        assertThrows(IllegalArgumentException.class,()->CurrentCourtierConfiguration.request(actualCore(),CurrentCourtierConfiguration.Action.EXECUTE_SETTING,BigInteger.ZERO,BigInteger.ZERO,product(),setting()));
    }
    @Test void fixedEnumParsersRejectKeysOrdinalsAndArbitraryScopeOrScripts()throws Exception{
        for(String value:List.of("MAIN","Main","xqol","0","other","main.confirm"))assertThrows(IOException.class,()->CurrentCourtierControls.Product.parse(value));
        for(String value:List.of("female","0","diplomacy_plus_20","set_age","xar_custom_script"))assertThrows(IOException.class,()->CurrentCourtierConfiguration.Setting.parse(value));
        assertThrows(IOException.class,()->CurrentCourtierConfiguration.Action.parse("query"));assertThrows(IOException.class,()->CurrentCourtierConfiguration.Action.parse("execute"));
    }
    @Test void exactIdentityAndResultOrSourceFieldSetsCannotAcceptCallerAuthority()throws Exception{
        for(String key:List.of("schema","game_version","executable_sha256","backend","adapter_id")){var n=token("available");n.put(key,"wrong");reject(n);}
        var n=token("available");source(n).put("caller_can_execute",true);reject(n);n=token("available");n.put("ordinal",0);reject(n);n=token("available");source(n).put("schema","old");reject(n);
    }
    @Test void sourceProductAndControlMustMatchTheActualResultRatherThanItsCaption()throws Exception{
        var n=token("available");n.put("product",product()==CurrentCourtierControls.Product.MAIN?"vivhite":"main");reject(n);n=token("available");source(n).put("setting",setting()==CurrentCourtierConfiguration.Setting.CHOOSE_FEMALE?"choose_same_house":"choose_female");reject(n);
    }
    @Test void absentCreatorRequiresCompleteConfirmationInventoryAndUnobservedPredicates()throws Exception{
        var n=token("absent");var s=source(n);
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
        assertEquals(CurrentCourtierConfigurationResult.Status.INDETERMINATE,frame("indeterminate").status());
    }
    @Test void rawSigned64ConfigurationRoundtripsWithoutScaleOrBooleanConversion()throws Exception{
        var n=token("available");var values=(ObjectNode)source(n).get("configuration");values.put("age",Long.toString(Long.MIN_VALUE)).put("female",Long.toString(Long.MAX_VALUE)).put("cost","0");
        var f=changed(n);var cfg=f.source().orElseThrow().configuration().orElseThrow();assertEquals(Long.MIN_VALUE,cfg.age().orElseThrow().longValue());assertEquals(Long.MAX_VALUE,cfg.female().orElseThrow().longValue());assertEquals(0L,cfg.cost().orElseThrow().longValue());assertEquals(f,CurrentCourtierConfigurationResult.decode(f.encode()));
        for(String invalid:List.of("-0","01","+1","1.0"," 1","9223372036854775808","-9223372036854775809")){var bad=token("available");((ObjectNode)source(bad).get("configuration")).put("age",invalid);reject(bad);}
        var bad=token("available");((ObjectNode)source(bad).get("configuration")).put("age",1);reject(bad);
    }
    @Test void missingNumericNeverBecomesZeroOrCompleteAndCannotAdmitExecute()throws Exception{
        for(String field:List.of("age","female","diplomacy","martial","stewardship","intrigue","learning","prowess","same_house","cost")){
            var n=token("available");var s=source(n);s.put("execute_admissible",false).put("numeric_complete",false);((ObjectNode)s.get("configuration")).putNull(field);var f=changed(n);assertFalse(f.source().orElseThrow().numericComplete());assertFalse(f.source().orElseThrow().configuration().orElseThrow().complete());
            s.put("numeric_complete",true);reject(n);s.put("numeric_complete",false).put("execute_admissible",true);reject(n);
        }
        var n=token("available");source(n).put("execute_admissible",false).put("numeric_complete",false);reject(n);
        n=token("available");source(n).put("execute_admissible",false).put("numeric_complete",false).putNull("configuration");reject(n);
    }
    static void reject(ObjectNode n){assertThrows(IOException.class,()->changed(n));}
}
