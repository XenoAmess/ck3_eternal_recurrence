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
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Local request/type boundary DATA. Actual C++ frame cases are added only from genuine producer originals. */
class NativeCurrentDjcSelectedCost26785313ProducerTest {
    static ObjectNode envelope(String name)throws IOException {
        try(var in=NativeCurrentDjcSelectedCost26785313ProducerTest.class.getResourceAsStream("/current-djc-selected-cost26785313-cpp-v1/"+name+".json")) {
            if(in==null)throw new IOException("Actual C++ selected-cost resource missing: "+name);return NativeWire.object(NativeWire.parse(in.readAllBytes()));
        }
    }
    static ObjectNode token(String name)throws IOException{return NativeWire.object(envelope(name).get("result"));}
    static CurrentDjcSelectedCostResult decode(ObjectNode n)throws IOException{return CurrentDjcSelectedCostResult.decode(new RawJson(StrictJson.canonical(n)));}
    static CoreFrame.Partial core(){return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,new CoreFrame.Prefix(53144328,1,true,0,true,true,777,true));}
    @Test void requestHasOnlyTheExactOriginalPrivateQueryClaimAndNoConfiguredCost()throws Exception {
        var request=CurrentDjcSelectedCost.request(core(),new NativeCharacterId(888),CurrentDjcTargetWarQueryResult.CasusBelliKey.DUCHY,NativeWire.UINT64_MAX,BigInteger.TWO);
        assertEquals(CurrentDjcSelectedCost.STEP,request.step());assertEquals(CurrentDjcSelectedCost.CAPABILITY,request.requiredCapability().orElseThrow());
        var fields=NativeWire.object(NativeWire.parse(request.additionalFields().bytes()));assertEquals(2,fields.size());assertTrue(fields.get("arguments").isObject()&&fields.get("arguments").isEmpty());
        var claim=fields.get("djc_selected_cost");assertEquals(11,claim.size());assertEquals(NativeWire.UINT64_MAX.toString(),claim.get("provider_generation").textValue());
        assertEquals("query_selected_cost",claim.get("action").textValue());assertEquals(8,claim.get("expected_core").size());
        for(String forbidden:Set.of("currency","costs","raw","scale","source","choice_token","tuple","permission"))assertFalse(claim.has(forbidden));
    }
    @Test void absentSelfForeignBuildUnpausedOrUnwitnessedLeaseCannotEncode() {
        var cb=CurrentDjcTargetWarQueryResult.CasusBelliKey.DUCHY;
        for(BigInteger n:List.of(BigInteger.ZERO,BigInteger.valueOf(-1),NativeWire.UINT64_MAX.add(BigInteger.ONE)))
            assertThrows(IllegalArgumentException.class,()->CurrentDjcSelectedCost.request(core(),new NativeCharacterId(888),cb,n,BigInteger.ONE));
        assertThrows(IllegalArgumentException.class,()->CurrentDjcSelectedCost.request(core(),new NativeCharacterId(777),cb,BigInteger.ONE,BigInteger.ONE));
        var unpaused=new CoreFrame.Partial(core().build(),new CoreFrame.Prefix(53144328,1,false,0,true,true,777,true));
        assertThrows(IllegalArgumentException.class,()->CurrentDjcSelectedCost.request(unpaused,new NativeCharacterId(888),cb,BigInteger.ONE,BigInteger.ONE));
    }
    @Test void rawSigned64LimitsRemainExactStringsWithNoScaleOrFormatting() {
        var max=new CurrentDjcSelectedCostResult.Cost(CurrentDjcSelectedCostResult.Currency.PIETY,"9223372036854775807");
        var min=new CurrentDjcSelectedCostResult.Cost(CurrentDjcSelectedCostResult.Currency.GOLD,"-9223372036854775808");
        assertEquals("9223372036854775807",max.raw());assertEquals("-9223372036854775808",min.raw());assertEquals("CFixedPoint",max.nativeType());
        for(String raw:List.of("-0","00","01","+1","1.0","1e2"," 1","9223372036854775808","-9223372036854775809"))
            assertThrows(IllegalArgumentException.class,()->new CurrentDjcSelectedCostResult.Cost(CurrentDjcSelectedCostResult.Currency.GOLD,raw),raw);
    }
    @Test void aRefusalCannotBeReplacedWithSyntheticZeroPrices() {
        assertDoesNotThrow(()->new CurrentDjcSelectedCostResult(CurrentDjcSelectedCostResult.Status.UNAVAILABLE,true,BigInteger.ZERO,BigInteger.ZERO,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),0,Optional.of("actual getter unavailable")));
        var zeros=List.of(new CurrentDjcSelectedCostResult.Cost(CurrentDjcSelectedCostResult.Currency.GOLD,"0"));
        assertThrows(IllegalArgumentException.class,()->new CurrentDjcSelectedCostResult(CurrentDjcSelectedCostResult.Status.UNAVAILABLE,true,BigInteger.ONE,BigInteger.TWO,Optional.empty(),Optional.empty(),Optional.empty(),Optional.of(zeros),0,Optional.of("actual getter unavailable")));
    }
    @Test void allEightActualCppResultsKeepTheirTrueOkAndNullRoles()throws Exception {
        for(String name:List.of("available-fullrange","available-disabled","unavailable","expired","stale-source","claim-consumed","indeterminate-cleanup","indeterminate-incomplete")) {
            var e=envelope(name);var r=decode(NativeWire.object(e.get("result")));assertEquals(e.get("ok").booleanValue(),r.nativeOk(),name);
            if(!r.nativeOk())assertTrue(r.source().isEmpty()&&r.costs().isEmpty(),name);
        }
    }
    @Test void genuineFullRangeValuesAndPrivateSourcePairKeepSignedAndOrderedDomains()throws Exception {
        var cost=decode(token("available-fullrange"));var ui=CurrentDjcDeclarationUiResult.decode(new RawJson(StrictJson.canonical(token("source-v23-query"))));
        assertTrue(cost.source().orElseThrow().matches(ui.source().orElseThrow()));assertEquals(ui.factsBefore(),cost.factsBefore());
        assertEquals(List.of("-9223372036854775808","-1","0","1","9223372036854775807"),cost.costs().orElseThrow().stream().map(CurrentDjcSelectedCostResult.Cost::raw).toList());
        assertEquals(List.of(-1,Integer.MIN_VALUE,-1),cost.source().orElseThrow().selected().extraConfigurationIds());
        assertEquals(NativeWire.UINT64_MAX,cost.providerGeneration());assertEquals(10,cost.nativeGetterCalls());
    }
    @Test void genuineDisabledWindowAndSelectedRowRemainPricesWithoutActionPermission()throws Exception {
        var r=decode(token("available-disabled"));assertTrue(r.nativeOk());assertFalse(r.source().orElseThrow().windowEnabled());assertFalse(r.source().orElseThrow().selected().sourceRowEnabled());
    }
    @Test void currencyOrderDuplicatesAndMissingGetterPassCannotBeNormalized()throws Exception {
        var a=token("available-fullrange");((ObjectNode)a.get("costs").get(0)).put("currency","gold");assertThrows(IOException.class,()->decode(a));
        var b=token("available-fullrange");b.put("native_getter_calls",9);assertThrows(IOException.class,()->decode(b));
        var c=token("available-fullrange");((com.fasterxml.jackson.databind.node.ArrayNode)c.get("costs")).remove(4);assertThrows(IOException.class,()->decode(c));
    }
    @Test void gettersCannotBeReinterpretedAsFormattedPricesActionsPaymentOrSave()throws Exception {
        for(String key:List.of("effect_attempted","native_returned","native_handled","payment_confirmed","physical_save_confirmed")) {
            var n=token("available-fullrange");n.put(key,true);assertThrows(IOException.class,()->decode(n),key);
        }
        var n=token("available-fullrange");n.put("formatted_text","100 piety");assertThrows(IOException.class,()->decode(n));
        var m=token("available-fullrange");m.put("scale",100000);assertThrows(IOException.class,()->decode(m));
        var x=token("available-fullrange");((ObjectNode)x.get("costs").get(0)).put("raw",1);assertThrows(IOException.class,()->decode(x));
    }
    @Test void missingTypedDeclarationOrPrivateMatchCannotBeBoughtByAvailableStatus()throws Exception {
        for(String key:List.of("source_matches_private_query","native_confirmation","interaction_definition_verified","resident_available","named_root_bound","window_visible")) {
            var n=token("available-fullrange");((ObjectNode)n.get("source")).put(key,false);assertThrows(IOException.class,()->decode(n),key);
        }
        var n=token("available-fullrange");((ObjectNode)n.get("source")).put("loaded_interface",3);assertThrows(IOException.class,()->decode(n));
    }
    @Test void exactFamilyKeysCannotBorrowV23DebitOrForgeLeaseClaimAndUnknownValues()throws Exception {
        for(String raw:List.of("01","-1","18446744073709551616")){var n=token("available-fullrange");n.put("query_sequence",raw);assertThrows(IOException.class,()->decode(n));}
        var n=token("available-fullrange");n.put("claim_sequence","1");assertThrows(IOException.class,()->decode(n));
        var m=token("available-fullrange");m.putNull("total_debit");assertThrows(IOException.class,()->decode(m));
        var q=envelope("request");assertEquals(CurrentDjcSelectedCost.STEP,q.get("step").textValue());assertEquals(11,q.get("djc_selected_cost").size());
    }
}
