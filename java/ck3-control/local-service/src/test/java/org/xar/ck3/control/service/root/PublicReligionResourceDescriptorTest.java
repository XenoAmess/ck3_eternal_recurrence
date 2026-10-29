package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionContract;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory.ToolDescriptor;

/** Mandatory actual SDK descriptors feed the production projection and sole Religion request codec.
 * This DATA boundary grants no current Root, readback custody, action permission or Native result. */
final class PublicReligionResourceDescriptorTest {
    private static final String CONVERT="ck3_convert_player_religion_private_v1";
    private static final String PILGRIMAGE="ck3_submit_player_pilgrimage_planner_v1";
    private record Carrier(String method,String field) { }
    private static final List<Carrier> CARRIERS=List.of(new Carrier(CONVERT,"max_piety_cost_raw"),
            new Carrier(PILGRIMAGE,"reserve_gold_raw"),new Carrier(PILGRIMAGE,"reserve_treasury_raw"),
            new Carrier(PILGRIMAGE,"reserve_piety_raw"),new Carrier(PILGRIMAGE,"reserve_barter_goods_raw"));

    @Test void allFiveCanonicalResourceCarriersReachTheSoleCodecAndReturnNativeIntegerOperands()throws Exception {
        for(var carrier:CARRIERS) {
            var original=original(carrier.method());var projected=RootPublicCatalogCodec.executableTool(original);
            for(String amount:List.of("0","9007199254740991","9223372036854775807")) {
                var input=input(carrier).put(carrier.field(),amount);
                assertThrows(IllegalArgumentException.class,()->original.validateArguments(arguments(input)));
                projected.validateArguments(arguments(input));
                var request=ReligionCodec.decode(carrier.method(),raw(input));var encoded=ReligionCodec.encode(request);
                projected.validateArguments(arguments(PublicDataJson.object(encoded)));
                assertEquals(request,ReligionCodec.decode(carrier.method(),encoded));
                var nativeOperand=ReligionCodec.nativeArguments(request).get(carrier.field());
                assertTrue(nativeOperand.isIntegralNumber());assertEquals(new BigInteger(amount),nativeOperand.bigIntegerValue());
                assertEquals(amount,PublicDataJson.object(encoded).get(carrier.field()).textValue());
            }
            var safe=input(carrier).put(carrier.field(),9007199254740991L);
            original.validateArguments(arguments(safe));projected.validateArguments(arguments(safe));
            var request=ReligionCodec.decode(carrier.method(),raw(safe));
            projected.validateArguments(arguments(PublicDataJson.object(ReligionCodec.encode(request))));
            var before=PublicDataJson.object(original.original()).get("inputSchema").get("properties");
            var after=PublicDataJson.object(projected.original()).get("inputSchema").get("properties");
            for(String field:carrier.method().equals(CONVERT)?List.of("target_rite_id","action_id"):List.of("operation","province_id","timeout_seconds"))
                assertEquals(before.get(field),after.get(field),"bounded selectors and ordinary fields retain the original schema");
        }
    }

    @Test void requiredConversionAndOptionalPilgrimageAmountsKeepPresenceAndRejectWrongDomains()throws Exception {
        for(var carrier:CARRIERS) {
            var projected=RootPublicCatalogCodec.executableTool(original(carrier.method()));var input=input(carrier);
            for(String bad:List.of("null","true","1.0","9007199254740992","\"01\"","\"+1\"","\"-1\"",
                    "\"9223372036854775808\"","\"18446744073709551615\"","\"1\\n\"")) {
                var wrong=input.deepCopy();wrong.set(carrier.field(),token(bad));
                assertThrows(IllegalArgumentException.class,()->projected.validateArguments(arguments(wrong)));
                assertThrows(IllegalArgumentException.class,()->ReligionCodec.decode(carrier.method(),raw(wrong)));
            }
            input.remove(carrier.field());
            if(carrier.method().equals(CONVERT)) {
                assertThrows(IllegalArgumentException.class,()->projected.validateArguments(arguments(input)));
                assertThrows(IllegalArgumentException.class,()->ReligionCodec.decode(carrier.method(),raw(input)));
            } else {
                projected.validateArguments(arguments(input));var request=ReligionCodec.decode(carrier.method(),raw(input));
                var field=java.util.Arrays.stream(ReligionContract.Field.values()).filter(value->value.wire().equals(carrier.field())).findFirst().orElseThrow();
                assertEquals(new ReligionContract.Absent(ReligionContract.Presence.MISSING),request.value(field));
                var encoded=ReligionCodec.encode(request);assertFalse(PublicDataJson.object(encoded).has(carrier.field()));
                projected.validateArguments(arguments(PublicDataJson.object(encoded)));
                assertEquals(request,ReligionCodec.decode(carrier.method(),encoded));
            }
        }
    }
    private static ObjectNode input(Carrier carrier) {
        var input=StrictJson.object().put("expected_revision",1).put(carrier.field(),0);
        if(carrier.method().equals(CONVERT))input.put("target_rite_id",1).put("action_id","schema-resource-1");
        else input.put("operation","start");
        return input;
    }
    private static ToolDescriptor original(String name)throws Exception {
        return RootOriginalPublicTestInputs.tools().stream().filter(value->value.name().equals(name)).findFirst()
                .orElseThrow(()->new IllegalStateException("NOT_RUN_REQUIRED_ACTUAL_ORIGINAL_TOOL: "+name));
    }
    private static JsonNode token(String json){return StrictJson.parse(json.getBytes(java.nio.charset.StandardCharsets.UTF_8));}
    private static RawJson raw(JsonNode value){return PublicDataJson.encode(value);}
    private static PublicMcpDirectory.Arguments arguments(JsonNode value){return new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,Optional.of(raw(value)));}
}
