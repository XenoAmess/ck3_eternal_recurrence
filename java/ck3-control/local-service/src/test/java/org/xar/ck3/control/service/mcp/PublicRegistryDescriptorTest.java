package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.RegistryPublicProfile;
import org.xar.ck3.control.service.root.RootOriginalPublicTestInputs;
import org.xar.ck3.control.service.root.RootPublicCatalogCodec;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** Captured original descriptors and the same Registry public revision decoder used by both handlers. */
final class PublicRegistryDescriptorTest {
    private static final List<String> NAMES=List.of("ck3_search_entities_v1","ck3_query_turn_bundle_v1","ck3_query_campaign_root_context_v1");

    private static ToolDescriptor original(String name) throws Exception {
        return RootOriginalPublicTestInputs.tools().stream().filter(tool->tool.name().equals(name)).findFirst()
                .orElseThrow(()->new IllegalStateException("NOT_RUN_REQUIRED_ACTUAL_ORIGINAL_TOOL: "+name));
    }
    private static Arguments arguments(String body) {
        return new Arguments(Presence.VALUE,Optional.of(new org.xar.ck3.control.application.action.RawJson(McpJson.utf8(body))));
    }

    @Test void bothCapturedDescriptorsAcceptTheActualUnboundedPublicRevisionDecoder() throws Exception {
        String wide=BigInteger.ONE.shiftLeft(100).toString();
        for(String name:NAMES) {
            ToolDescriptor descriptor=RootPublicCatalogCodec.executableTool(original(name));
            for(String token:List.of("0","9007199254740991","\"0\"","\""+wide+"\"","\""+"9".repeat(4300)+"\"")) {
                Arguments value=arguments("{\"expected_revision\":"+token+"}");
                descriptor.validateArguments(value);
                var node=PublicDataJson.object(value.original().orElseThrow()).get("expected_revision");
                assertEquals(new BigInteger(node.isTextual()?node.textValue():node.asText()),RegistryPublicProfile.revision(node));
            }
            for(String body:List.of("{}","{\"expected_revision\":null}","{\"expected_revision\":true}",
                    "{\"expected_revision\":1.0}","{\"expected_revision\":-1}","{\"expected_revision\":9007199254740992}",
                    "{\"expected_revision\":\"01\"}","{\"expected_revision\":\"+1\"}",
                    "{\"expected_revision\":\"1\\n\"}","{\"expected_revision\":\""+"9".repeat(4301)+"\"}"))
                assertThrows(IllegalArgumentException.class,()->descriptor.validateArguments(arguments(body)),name+": "+body.substring(0,Math.min(body.length(),80)));
        }
    }

    @Test void migrationChangesOnlyTheDeclaredRevisionRoleAndRetainsOriginalOtherFields() throws Exception {
        for(String name:NAMES) {
            var before=PublicDataJson.object(original(name).original());
            var after=PublicDataJson.object(RootPublicCatalogCodec.executableTool(original(name)).original());
            ((com.fasterxml.jackson.databind.node.ObjectNode)before.path("inputSchema").path("properties")).remove("expected_revision");
            ((com.fasterxml.jackson.databind.node.ObjectNode)after.path("inputSchema").path("properties")).remove("expected_revision");
            assertEquals(before,after);
        }
        ToolDescriptor search=RootPublicCatalogCodec.executableTool(original("ck3_search_entities_v1"));
        search.validateArguments(arguments("{\"expected_revision\":\"1\",\"after_character_id\":1,\"limit\":50,\"relation_filter\":\"any\"}"));
        assertThrows(IllegalArgumentException.class,()->search.validateArguments(arguments(
                "{\"expected_revision\":\"1\",\"after_character_id\":\"1\"}")));
    }
}
