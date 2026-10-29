package org.xar.ck3.control.nativebridge.capabilities.frontendfixture;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData;

final class FixtureModelContractTest {
    private JsonNode oracle()throws Exception {try(var in=getClass().getResourceAsStream("/frontend-fixture/python-model-oracle04.json")){assertNotNull(in);return StrictJson.parse(in.readAllBytes(),1<<20);}}
    @Test void actualOriginalProducersPartialProbeUnavailableAndSelectedRemainDifferentTypedBranches()throws Exception {
        int probes=0;
        for(JsonNode row:oracle().get("cases")) {
            var kind=FrontendFixturePolicy.Kind.valueOf(row.get("kind").textValue());
            var source=new FrontendRulesData.Source(new FrontendRulesData.Binding(71,BigInteger.TWO),kind==FrontendFixturePolicy.Kind.SCENARIO?FrontendRulesData.Build.CK3_12004:FrontendRulesData.Build.CK3_12003);
            for(JsonNode original:row.get("probes")) {
                var value=FixtureModelContract.decode(new RawJson(StrictJson.canonical(original,65536)),source,BigInteger.valueOf(++probes),kind);
                assertArrayEquals(StrictJson.canonical(original,65536),value.original().bytes());
                if(original.has("status")&&original.get("status").textValue().equals("unavailable")) {
                    assertInstanceOf(FixtureModelContract.Unavailable.class,value.state());assertEquals("bm_1066_rags_to_riches",value.selectedBookmarkKey().orElseThrow());
                    assertThrows(IllegalArgumentException.class,value::probe);
                }else {
                    String key=kind==FrontendFixturePolicy.Kind.SCENARIO?FrontendFixturePolicy.SCENARIO_TARGET.characterNameKey():FrontendFixturePolicy.ROBERT_KEY;
                    value.probeTarget(key,kind==FrontendFixturePolicy.Kind.SCENARIO);
                    if(kind==FrontendFixturePolicy.Kind.ROBERT){assertInstanceOf(FixtureModelContract.Probe.class,value.state());assertThrows(IllegalArgumentException.class,()->value.selected(key,false,true));}
                    else {var selected=assertInstanceOf(FixtureModelContract.Selected.class,value.state());assertTrue(selected.originalDateQword().isEmpty(),"missing original qword must never be fabricated from low32 date");}
                }
            }
        }
        assertEquals(5,probes);
    }
    @Test void probeRejectsBooleanFloatAndUnboundTargetWithoutConstructingSelectedEvidence()throws Exception {
        JsonNode original=oracle().get("cases").get(0).get("probes").get(0);
        var source=new FrontendRulesData.Source(new FrontendRulesData.Binding(71,BigInteger.TWO),FrontendRulesData.Build.CK3_12003);
        for(String field:java.util.List.of("supported_1066_candidate_index","selected_character_index")) {
            for(JsonNode bad:java.util.List.of(com.fasterxml.jackson.databind.node.BooleanNode.TRUE,new com.fasterxml.jackson.databind.node.DoubleNode(1.0))) {
                ObjectNode changed=original.deepCopy();changed.set(field,bad);
                assertThrows(IllegalArgumentException.class,()->FixtureModelContract.decode(new RawJson(StrictJson.canonical(changed,65536)),source,BigInteger.ONE,FrontendFixturePolicy.Kind.ROBERT));
            }
        }
        ObjectNode partial=original.deepCopy();partial.put("accepted",true);
        assertThrows(IllegalArgumentException.class,()->FixtureModelContract.decode(new RawJson(StrictJson.canonical(partial,65536)),source,BigInteger.ONE,FrontendFixturePolicy.Kind.ROBERT));
    }
}
