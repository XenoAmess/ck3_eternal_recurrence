package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Original compiled C++ resources only; explicit Java mutations below test refusal boundaries. */
class NativeCurrentCourtierChoices26785313ProducerTest {
    static byte[] raw(String role)throws IOException{try(var in=NativeCurrentCourtierChoices26785313ProducerTest.class.getResourceAsStream("/current267-courtier-choices-actual-cpp/"+role+".json")){if(in==null)throw new IOException("Actual C++ choices resource absent: "+role);return in.readAllBytes();}}
    static ObjectNode envelope(String role)throws IOException{return NativeWire.object(NativeWire.parse(raw(role)));}
    static ObjectNode token(String role)throws IOException{return NativeWire.object(envelope(role).get("result"));}
    static CurrentCourtierChoicesResult frame(String role)throws IOException{return changed(token(role));}
    static CurrentCourtierChoicesResult changed(ObjectNode n)throws IOException{return CurrentCourtierChoicesResult.decode(new RawJson(StrictJson.canonical(n)));}
    static ObjectNode source(ObjectNode n){return (ObjectNode)n.get("source");}
    static ObjectNode row(ObjectNode n)throws IOException{String token=frame("select").choiceToken();for(var row:source(n).get("rows"))if(row.get("choice_token").textValue().equals(token))return (ObjectNode)row;throw new IOException("Original selected opaque token absent from actual full model");}
    static String key()throws IOException{var f=frame("select");var matches=f.source().orElseThrow().rows().stream().filter(row->row.choiceToken().equals(f.choiceToken())).toList();if(matches.size()!=1)throw new IOException("Original dispatched token needs exactly one actual canonical row");return matches.getFirst().key();}
    static CoreFrame.Partial actualCore()throws IOException{return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,frame("available").factsBefore().orElseThrow());}
    static CurrentCourtierControls.Product product()throws IOException{return frame("available").product();}
    static CurrentCourtierChoices.Catalog catalog()throws IOException{return frame("available").catalog();}
    @Test void actualCppResultsRoundtripExact28KeysWithVoidPostconditionsAlwaysFalse()throws Exception{
        for(var name:NativeWire.object(NativeWire.parse(raw("index"))).get("result_roles")){String role=name.textValue();var f=frame(role);assertEquals(f,CurrentCourtierChoicesResult.decode(f.encode()));assertEquals(envelope(role).get("ok").booleanValue(),f.successful());}
        var n=StrictJson.parse(frame("select").encode().bytes(),1<<20);assertEquals(28,n.size());for(String key:List.of("native_handled","creator_closed","courtier_created","selection_changed","new_date_observed","physical_save_confirmed"))assertFalse(n.get(key).booleanValue(),key);
    }
    @Test void typedCataloguesAndProductsEncodeExactTwelveFieldsWithNoCallerScope()throws Exception{
        var f=frame("select");for(var product:CurrentCourtierControls.Product.values())for(var catalog:CurrentCourtierChoices.Catalog.values())for(var action:CurrentCourtierChoices.Action.values()){
            boolean query=action==CurrentCourtierChoices.Action.QUERY_CHOICES;var r=CurrentCourtierChoices.request(actualCore(),action,query?BigInteger.ZERO:f.providerGeneration(),query?BigInteger.ZERO:f.querySequence(),product,catalog,query?"":f.choiceToken());var n=NativeWire.object(NativeWire.parse(r.additionalFields().bytes()));assertEquals(2,n.size());assertEquals(0,n.get("arguments").size());var c=n.get("courtier_choices");assertEquals(12,c.size());assertEquals(product.wire(),c.get("product").textValue());assertEquals(catalog.wire(),c.get("catalog").textValue());assertEquals(query?"":f.choiceToken(),c.get("choice_token").textValue());assertEquals(action.step(),r.step());assertFalse(c.has("key"));assertFalse(c.has("ordinal"));assertFalse(c.has("scope"));}
    }
    @Test void queryAndSelectTokenLeaseRolesCannotBeInterchanged()throws Exception{
        var f=frame("select");assertThrows(IllegalArgumentException.class,()->CurrentCourtierChoices.request(actualCore(),CurrentCourtierChoices.Action.QUERY_CHOICES,BigInteger.ZERO,BigInteger.ZERO,product(),catalog(),f.choiceToken()));assertThrows(IllegalArgumentException.class,()->CurrentCourtierChoices.request(actualCore(),CurrentCourtierChoices.Action.SELECT_CHOICE,BigInteger.ZERO,BigInteger.ZERO,product(),catalog(),f.choiceToken()));assertThrows(IllegalArgumentException.class,()->CurrentCourtierChoices.request(actualCore(),CurrentCourtierChoices.Action.SELECT_CHOICE,f.providerGeneration(),f.querySequence(),product(),catalog(),""));
        var n=token("available");n.put("choice_token",f.choiceToken());reject(n);n=token("select");n.put("choice_token","");reject(n);
    }
    @Test void keyAndOpaqueTokenFollowTheirActualDistinctAsciiBounds()throws Exception{
        assertEquals("A".repeat(128),CurrentCourtierChoices.exactKey("A".repeat(128)));assertEquals("a_.-9".repeat(19),CurrentCourtierChoices.token("a_.-9".repeat(19)));
        for(String bad:List.of("","a ","汉","x/y","script:run","a".repeat(129)))assertThrows(IllegalArgumentException.class,()->CurrentCourtierChoices.exactKey(bad));for(String bad:List.of("","a ","x/y","a".repeat(97)))assertThrows(IllegalArgumentException.class,()->CurrentCourtierChoices.token(bad));
        for(String bad:List.of("0","trait","script:run","FAITH"))assertThrows(IOException.class,()->CurrentCourtierChoices.Catalog.parse(bad));
    }
    @Test void exactIdentitySourceRowAndResultShapesRejectExtraAuthority()throws Exception{
        for(String key:List.of("schema","game_version","executable_sha256","backend","adapter_id")){var n=token("available");n.put(key,"wrong");reject(n);}var n=token("available");source(n).put("caller_can_select",true);reject(n);n=token("available");row(n).put("ordinal",0);reject(n);n=token("available");n.put("key",key());reject(n);
    }
    @Test void sourceProductAndCatalogueCannotBeRelabelled()throws Exception{
        var n=token("available");n.put("product",product()==CurrentCourtierControls.Product.MAIN?"vivhite":"main");reject(n);n=token("available");source(n).put("catalog",catalog()==CurrentCourtierChoices.Catalog.FAITH?"culture":"faith");reject(n);
    }
    @Test void absentCreatorHasOnlyCompleteInventoryFalseNullAndEmptyRows()throws Exception{
        var n=token("absent");assertFalse(changed(n).source().orElseThrow().creatorWindowFound());source(n).put("confirmation_layer_found",false);reject(n);n=token("absent");source(n).put("catalog_count",0);reject(n);n=token("absent");source(n).put("model_available",true);reject(n);
    }
    @Test void presentPartialUnboundOrCountMismatchCannotFabricateCompleteEmptyModel()throws Exception{
        for(String key:List.of("modal_found","panel_found","model_available","complete_model")){var n=token("available");source(n).put(key,false);reject(n);}var n=token("available");source(n).putNull("catalog_count");reject(n);n=token("available");source(n).put("catalog_count",2049);reject(n);n=token("available");source(n).put("catalog_count",0);reject(n);n=token("available");source(n).putNull("configuration");reject(n);
    }
    @Test void actualCompleteZeroModelRemainsDistinctFromUnmaterialized()throws Exception{
        var n=token("available");source(n).put("catalog_count",0);source(n).putArray("rows");var s=changed(n).source().orElseThrow();assertTrue(s.completeModel());assertTrue(s.modelAvailable());assertEquals(0,s.catalogCount().orElseThrow().intValue());assertTrue(s.rows().isEmpty());
    }
    @Test void duplicateActualKeysOrTokensRejectTheEntireModel()throws Exception{
        for(boolean duplicateKey:List.of(true,false)){var n=token("available");var rows=(ArrayNode)source(n).get("rows");var extra=row(n).deepCopy();if(duplicateKey)extra.put("choice_token","new_unique_token");else extra.put("key","new_unique_key");rows.add(extra);source(n).put("catalog_count",rows.size());reject(n);}
    }
    @Test void actualFalseShownValidSelectedAndOneWayAdmissionArePreserved()throws Exception{
        for(String key:List.of("native_shown","native_valid")){var n=token("available");row(n).put(key,false).put("execute_admissible",false);assertTrue(changed(n).successful());row(n).put("execute_admissible",true);reject(n);}var n=token("available");row(n).put("selected",false).put("execute_admissible",false);assertFalse(changed(n).source().orElseThrow().rows().stream().filter(r->r.key().equals(keyUnchecked())).findFirst().orElseThrow().selected());
    }
    @Test void rawTenValuesKeepNullableSigned64AndMissingCannotAuthorizeSelection()throws Exception{
        var n=token("available");var values=(ObjectNode)source(n).get("configuration");values.put("age",Long.toString(Long.MIN_VALUE)).put("cost",Long.toString(Long.MAX_VALUE));var cfg=changed(n).source().orElseThrow().configuration().orElseThrow();assertEquals(Long.MIN_VALUE,cfg.age().orElseThrow().longValue());assertEquals(Long.MAX_VALUE,cfg.cost().orElseThrow().longValue());
        for(String field:List.of("age","female","diplomacy","martial","stewardship","intrigue","learning","prowess","same_house","cost")){n=token("available");((ObjectNode)source(n).get("configuration")).putNull(field);for(var r:source(n).get("rows"))((ObjectNode)r).put("execute_admissible",false);assertFalse(changed(n).source().orElseThrow().configuration().orElseThrow().complete());row(n).put("execute_admissible",true);reject(n);}
    }
    @Test void originalLeaseTokenAndPositiveSpentClaimRefusalDoNotBecomeEffects()throws Exception{
        var n=token("stale");n.put("claim_sequence","1");var f=changed(n);assertFalse(f.successful());assertFalse(f.effectAttempted());assertFalse(f.nativeReturned());assertEquals(BigInteger.ONE,f.claimSequence());n.put("effect_attempted",true);reject(n);n=token("select");n.put("query_sequence","0");reject(n);n=token("available");n.put("provider_generation","01");reject(n);
    }
    @Test void cleanupUnknownOwnerMismatchAndVoidPoststateClaimsNeverGrantAuthority()throws Exception{
        var n=token("available");n.put("cleanup_known",false);reject(n);n=token("available");n.putNull("owner");reject(n);for(String key:List.of("native_handled","creator_closed","courtier_created","selection_changed","new_date_observed","physical_save_confirmed")){n=token("select");n.put(key,true);reject(n);}assertEquals(CurrentCourtierChoicesResult.Status.INDETERMINATE,frame("indeterminate").status());
    }
    static String keyUnchecked(){try{return key();}catch(IOException e){throw new java.io.UncheckedIOException(e);}}
    static void reject(ObjectNode n){assertThrows(IOException.class,()->changed(n));}
}
