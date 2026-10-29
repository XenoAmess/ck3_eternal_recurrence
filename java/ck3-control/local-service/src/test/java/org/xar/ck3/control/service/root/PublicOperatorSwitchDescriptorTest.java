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
import org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory;

/** Mandatory original SDK metadata and the real operator request decoder; no switch is submitted. */
final class PublicOperatorSwitchDescriptorTest {
    @Test void exactOperatorRevisionProfileReachesTheSoleDecoderAndPreservesNumericCharacterIdentity()throws Exception {
        var original=RootOriginalPublicTestInputs.tools().stream().filter(value->value.name().equals("ck3_set_played_character_v1")).findFirst()
                .orElseThrow(()->new IllegalStateException("NOT_RUN_REQUIRED_ACTUAL_ORIGINAL_TOOL: ck3_set_played_character_v1"));
        var projected=RootPublicCatalogCodec.executableTool(original);
        var before=PublicDataJson.object(original.original()).get("inputSchema");var after=PublicDataJson.object(projected.original()).get("inputSchema");
        assertEquals(before.get("required"),after.get("required"));assertEquals(before.get("properties").get("character_id"),after.get("properties").get("character_id"));
        for(String revision:List.of("0","9007199254740991","\"18446744073709551615\"")) {
            var input=StrictJson.object().put("character_id",Integer.MAX_VALUE);input.set("expected_revision",token(revision));
            if(input.get("expected_revision").isIntegralNumber())original.validateArguments(arguments(input));
            else assertThrows(IllegalArgumentException.class,()->original.validateArguments(arguments(input)));
            projected.validateArguments(arguments(input));var typed=OperatorPlayerSwitch.decode(raw(input));
            var request=PublicDataJson.object(arguments(input).original().orElseThrow());
            assertEquals(typed,OperatorPlayerSwitch.decode(raw(request)));assertEquals(Integer.MAX_VALUE,typed.characterId());
            assertTrue(request.get("character_id").isIntegralNumber());
        }
        var maximum=StrictJson.object().put("character_id",1).put("expected_revision","18446744073709551615");
        assertEquals(new BigInteger("18446744073709551615"),OperatorPlayerSwitch.decode(raw(maximum)).expectedRevision());
        for(String bad:List.of("null","true","1.0","9007199254740992","\"01\"","\"-1\"","\"+1\"","\"18446744073709551616\"")) {
            var wrong=maximum.deepCopy();wrong.set("expected_revision",token(bad));
            assertThrows(IllegalArgumentException.class,()->projected.validateArguments(arguments(wrong)));
            assertThrows(IllegalArgumentException.class,()->OperatorPlayerSwitch.decode(raw(wrong)));
        }
        var missing=maximum.deepCopy();missing.remove("expected_revision");assertThrows(IllegalArgumentException.class,()->projected.validateArguments(arguments(missing)));
        assertThrows(IllegalArgumentException.class,()->OperatorPlayerSwitch.decode(raw(missing)));
        for(String bad:List.of("0","-1","2147483648","true","1.0","\"1\"","null")) {
            var wrong=maximum.deepCopy();wrong.set("character_id",token(bad));assertThrows(IllegalArgumentException.class,()->OperatorPlayerSwitch.decode(raw(wrong)));
        }
        assertThrows(IllegalArgumentException.class,()->OperatorPlayerSwitch.decode(raw(maximum.deepCopy().put("alias",1))));
    }
    private static JsonNode token(String json){return StrictJson.parse(json.getBytes(java.nio.charset.StandardCharsets.UTF_8));}
    private static RawJson raw(JsonNode value){return PublicDataJson.encode(value);}
    private static PublicMcpDirectory.Arguments arguments(JsonNode value){return new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,Optional.of(raw(value)));}
}
