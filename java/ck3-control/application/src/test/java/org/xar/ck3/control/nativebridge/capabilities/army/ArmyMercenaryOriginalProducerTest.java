package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.finance.NativeMercenaryMarket;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;

/** Original Driver/Service market producer with synthetic endpoint data. No hiring, payment or live business credit. */
final class ArmyMercenaryOriginalProducerTest {
    static ObjectNode original() throws Exception {
        ArmyOriginalSourcePins.verify("ck3_autonomous_player/src/xar_autoplayer/bridge/player_mercenary_context.py","54acb5c62c90d10c600acd92d957dc86e738ddaa6520f3d2803694570179fe81");
        ArmyOriginalSourcePins.verify("ck3_autonomous_player/tests/unit/test_mercenary_query_mcp_result.py","01bff22ffb025c6d371bee1a77da9c56493d2c346ca84c75d286b8ae3842d5a6");
        ArmyOriginalSourcePins.verify("ck3_autonomous_player/tests/unit/test_mercenary_history_projection_v1.py","4a869af8cea60b52bb5e3dc2387518b09bc37f6c0883e5c69ea9f2c493fffce5");
        return BattleOriginalOracle.call("""
                import importlib.util,json
                path=root/'ck3_autonomous_player'/'tests'/'unit'/'test_mercenary_query_mcp_result.py'
                spec=importlib.util.spec_from_file_location('xar_market_original_fixture',path)
                module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
                case=module.MercenaryQueryMcpResultTests('test_registered_AUTO_keeps_complete_numbers_frame_and_hire_terms_without_pretty_copy')
                case.setUp()
                try:
                    print(json.dumps({'result':case.query,'snapshot':case.snapshot},allow_nan=False))
                finally:case.tearDown()
                """,ArmyJson.empty());
    }
    @Test void originalFullProducerPreservesUnsignedCompaniesTenCostsDebtAndCompleteComposition() throws Exception {
        var original=original();var payload=object(original.get("result").get("player_mercenary_context"));var snapshot=object(original.get("snapshot"));var observed=ArmyMercenaryContextCodec.decode(payload,snapshot);
        assertEquals(payload,observed.normalized());assertEquals(java.util.List.of(0L,2147483649L,4294967295L),observed.candidates().stream().map(ArmyMercenaryContextCodec.Candidate::companyId).toList());
        var company=observed.candidates().getFirst();assertEquals(NativeMercenaryMarket.Truth.TRUE,company.terms().canHire());assertEquals(NativeMercenaryMarket.Truth.FALSE,company.terms().canAfford());assertTrue(company.readiness().hireReady());
        assertEquals(BigInteger.valueOf(Long.MIN_VALUE),company.terms().costs().orElseThrow().get(1));assertEquals(BigInteger.valueOf(Long.MAX_VALUE),company.terms().costs().orElseThrow().get(2));assertTrue(company.composition().orElseThrow().status().available());
    }
    @Test void missingAndExplicitNullCompositionAndPartialAggregatesRetainDifferentMeaning() throws Exception {
        var original=original();var payload=(ObjectNode)original.get("result").get("player_mercenary_context");var snapshot=object(original.get("snapshot"));
        var missing=payload.deepCopy();((ObjectNode)missing.withArray("rows").get(0)).remove("composition_v1");var observed=ArmyMercenaryContextCodec.decode(object(missing),snapshot);assertTrue(observed.candidates().getFirst().composition().isEmpty());assertFalse(observed.candidates().getFirst().readiness().hireReady());
        var nullGroup=payload.deepCopy();((ObjectNode)nullGroup.withArray("rows").get(0)).putNull("composition_v1");assertThrows(IllegalArgumentException.class,()->ArmyMercenaryContextCodec.decode(object(nullGroup),snapshot));
        var partial=payload.deepCopy();var composition=(ObjectNode)partial.withArray("rows").get(0).get("composition_v1");composition.put("available",false).put("unavailable_reason","partial-native-regiments");
        for(String field:java.util.List.of("current_regiment_soldiers","maximum_regiment_soldiers","positive_siege_tier_current_soldiers","maximum_siege_tier_raw"))composition.putNull(field);
        assertFalse(ArmyMercenaryContextCodec.decode(object(partial),snapshot).candidates().getFirst().composition().orElseThrow().status().available());
        composition.put("current_regiment_soldiers",0);assertThrows(IllegalArgumentException.class,()->ArmyMercenaryContextCodec.decode(object(partial),snapshot));
    }
    @Test void wrongTypesSourceAndCompanyBacklinkFailAndExtraCopiedNativeFieldsSurvive() throws Exception {
        var original=original();var payload=(ObjectNode)original.get("result").get("player_mercenary_context");var snapshot=object(original.get("snapshot"));
        var bad=payload.deepCopy();((ObjectNode)bad.withArray("rows").get(0)).put("company_id",true);assertThrows(IllegalArgumentException.class,()->ArmyMercenaryContextCodec.decode(object(bad),snapshot));
        var backlink=payload.deepCopy();((ObjectNode)backlink.withArray("rows").get(0).get("composition_v1")).put("company_id",5);assertThrows(IllegalArgumentException.class,()->ArmyMercenaryContextCodec.decode(object(backlink),snapshot));
        var stale=payload.deepCopy().put("actor_character_id",1);assertThrows(IllegalArgumentException.class,()->ArmyMercenaryContextCodec.decode(object(stale),snapshot));
        var extension=payload.deepCopy();extension.putObject("copied_native_extension").put("raw",new BigInteger("18446744073709551615"));assertEquals(extension.get("copied_native_extension"),OpportunityJson.toNode(ArmyMercenaryContextCodec.decode(object(extension),snapshot).normalized()).get("copied_native_extension"));
    }
    private static OpportunityJson.Obj object(com.fasterxml.jackson.databind.JsonNode n){return DriverJson.object(ArmyJson.bytes(n),DriverJson.MAX_NATIVE_BYTES);}
}
