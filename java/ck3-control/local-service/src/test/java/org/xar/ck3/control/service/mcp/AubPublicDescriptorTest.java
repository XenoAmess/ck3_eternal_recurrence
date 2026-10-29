package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.capabilities.aub.AubOperations.PolicyKey;
import org.xar.ck3.control.service.root.RootPublicCatalogCodec;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** Exact schema-unit specimens feed all four actual request consumers; not a fresh original descriptor capture. */
final class AubPublicDescriptorTest {
    @Test void allFourActualRequestDecodersReceiveOnlySafeNumbersOrCanonicalUint64Text() {
        for(String name:List.of("ck3_query_aub_business_state_v1","ck3_query_aub_policy_options_v1",
                "ck3_select_aub_policy_option_v1","ck3_confirm_aub_policy_v1")) {
            var original=descriptor(name);var actual=RootPublicCatalogCodec.executableTool(original);
            for(String token:List.of("missing","null","0","9007199254740991","\"18446744073709551615\"")) {
                var row=arguments(name);if(!token.equals("missing"))row.set("expected_revision",McpJson.parse(token.getBytes(StandardCharsets.UTF_8)));
                var call=new Arguments(Presence.VALUE,Optional.of(new RawJson(McpJson.encode(row))));actual.validateArguments(call);
                RootMcpAubReads.Revision revision;
                if(name.equals("ck3_select_aub_policy_option_v1"))revision=RootMcpAubOperations.selection(call).revision();
                else if(name.equals("ck3_confirm_aub_policy_v1"))revision=RootMcpAubOperations.confirmation(call).revision();
                else revision=RootMcpAubOperations.query(call).revision();
                if(token.equals("missing"))assertInstanceOf(RootMcpAubReads.Missing.class,revision);
                else if(token.equals("null"))assertInstanceOf(RootMcpAubReads.NullValue.class,revision);
                else assertEquals(new BigInteger(token.replace("\"","")),revision.expected().orElseThrow());
                if(token.startsWith("\""))assertThrows(IllegalArgumentException.class,()->original.validateArguments(call));
            }
            for(String bad:List.of("true","1.0","-1","9007199254740992","\"01\"","\"+1\"","\"1\\n\"","\"18446744073709551616\"")) {
                var row=arguments(name);row.set("expected_revision",McpJson.parse(bad.getBytes(StandardCharsets.UTF_8)));
                var call=new Arguments(Presence.VALUE,Optional.of(new RawJson(McpJson.encode(row))));
                assertThrows(IllegalArgumentException.class,()->actual.validateArguments(call),name+bad);
                assertThrows(IllegalArgumentException.class,()->RootMcpAubReads.revision(row),name+bad);
            }
        }
    }
    private static com.fasterxml.jackson.databind.node.ObjectNode arguments(String name) {
        var row=McpJson.object();
        if(name.contains("select_")||name.contains("confirm_"))row.put("expected_selected_key",PolicyKey.TREASURY_PAUSE.wire());
        if(name.contains("select_"))row.put("desired_key",PolicyKey.TREASURY_CONTINUE.wire());
        return row;
    }
    private static ToolDescriptor descriptor(String name) {
        var row=McpJson.object().put("name",name);var schema=row.putObject("inputSchema").put("type","object").put("additionalProperties",false);
        var properties=schema.putObject("properties");var nullable=properties.putObject("expected_revision").putArray("anyOf");
        nullable.addObject().put("type","integer");nullable.addObject().put("type","null");
        var required=schema.putArray("required");
        for(String field:List.of("expected_selected_key","desired_key")) {
            if((field.equals("expected_selected_key")&&(name.contains("select_")||name.contains("confirm_")))
                    ||(field.equals("desired_key")&&name.contains("select_"))) {
                var values=properties.putObject(field).put("type","string").putArray("enum");
                for(PolicyKey key:PolicyKey.values())values.add(key.wire());required.add(field);
            }
        }
        return new ToolDescriptor(name,new RawJson(McpJson.encode(row)));
    }
}
