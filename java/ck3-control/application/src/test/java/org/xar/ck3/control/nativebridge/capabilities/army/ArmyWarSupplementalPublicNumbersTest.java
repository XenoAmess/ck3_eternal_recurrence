package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.OperationKey;

/** Public roles follow the actual C++ contract, not the Java storage primitive chosen by an older model. */
final class ArmyWarSupplementalPublicNumbersTest {
    @TempDir Path temporary;
    @Test void cppInt32DatesAndGameIdentitiesStayNumbersWhileRealWideRolesBecomeDecimal()throws Exception{
        ObjectNode row=find("original-driver-signed-resource-boundary");var selected=ArmyWarSupplementalReadTest.selected((ObjectNode)row.get("before"),new OperationKey(row.path("raw").path("step").textValue()));
        var observation=ArmyWarSupplementalReadCodec.normalizeBaseline(selected,json(row.get("raw")),json(row.get("before")),json(row.get("after")));
        var result=ArmyWarSupplementalReadCodec.object(ArmyWarSupplementalReadCodec.fullDriverResult(observation));
        var baseline=result.path("defender_de_jure_exit_terms_v1");assertTrue(baseline.path("date_raw").isIntegralNumber());assertEquals(53217264,baseline.path("date_raw").intValue());
        for(String key:java.util.List.of("war_id","primary_attacker_character_id","primary_defender_character_id"))assertTrue(baseline.get(key).isIntegralNumber(),key);
        assertTrue(baseline.path("target_title_ids").get(0).isIntegralNumber());var holder=baseline.path("target_title_holder_prestate").get(0);
        for(String key:java.util.List.of("title_id","holder_character_id","holder_immediate_liege_character_id"))assertTrue(holder.get(key).isIntegralNumber(),key);
        assertTrue(baseline.path("primary_resource_balances").get(0).path("character_id").isIntegralNumber());
        assertEquals(BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE).toString(),result.path("query_sequence").textValue());assertEquals("3",baseline.path("native_revision").textValue());
        assertEquals(Long.toString(Long.MIN_VALUE),baseline.path("primary_resource_balances").get(0).path("value").path("raw").textValue());
        assertEquals(Long.toString(Long.MAX_VALUE),baseline.path("primary_monthly_gold_income").get(0).path("value").path("raw").textValue());
    }
    @Test void historicalLongModelCannotLaunderOutOfNativeInt32IdOrDateAsDecimalAlias()throws Exception{
        ObjectNode row=find("original-driver-baseline");
        for(String mutation:java.util.List.of("holder","target","date")){
            ObjectNode raw=((ObjectNode)row.get("raw")).deepCopy(),before=((ObjectNode)row.get("before")).deepCopy(),after=((ObjectNode)row.get("after")).deepCopy();
            var baseline=(ObjectNode)raw.get("defender_de_jure_exit_terms_v1");BigInteger outside=BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.ONE);
            switch(mutation){
                case "holder"->((ObjectNode)baseline.path("target_title_holder_prestate").get(0)).put("holder_character_id",outside);
                case "target"->{baseline.putArray("target_title_ids").add(outside);((ObjectNode)baseline.path("target_title_holder_prestate").get(0)).put("title_id",outside);((ObjectNode)before.path("active_wars").get(0)).putArray("targeted_title_ids").add(outside);((ObjectNode)after.path("active_wars").get(0)).putArray("targeted_title_ids").add(outside);}
                case "date"->{baseline.put("date_raw",outside);before.put("date_raw",outside);after.put("date_raw",outside);}
                default->throw new AssertionError();
            }
            var selected=ArmyWarSupplementalReadTest.selected(before,new OperationKey(raw.path("step").textValue()));
            var normalized=ArmyWarSupplementalReadCodec.normalizeBaseline(selected,json(raw),json(before),json(after));
            assertThrows(IllegalArgumentException.class,()->ArmyWarSupplementalReadCodec.fullDriverResult(normalized),mutation);
        }
    }
    private ObjectNode find(String name)throws Exception{for(var row:ArmyWarSupplementalOriginalInputs.capture(temporary).get("cases"))if(name.equals(row.path("name").textValue()))return (ObjectNode)row;throw new AssertionError("actual original case absent: "+name);}
    private static org.xar.ck3.control.application.action.RawJson json(JsonNode node){return ArmyWarSupplementalReadCodec.json(node);}
}
