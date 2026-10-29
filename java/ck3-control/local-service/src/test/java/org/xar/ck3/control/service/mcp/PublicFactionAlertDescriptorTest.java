package org.xar.ck3.control.service.mcp;

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
import org.xar.ck3.control.nativebridge.capabilities.registry.FactionAlertReadService;
import org.xar.ck3.control.service.root.RootOriginalPublicTestInputs;
import org.xar.ck3.control.service.root.RootPublicCatalogCodec;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** The actual query producer already emits decimal text. Test its real next schema consumer;
 * no faction reply, Root, current frame or native success is fabricated for this request-only fix. */
public final class PublicFactionAlertDescriptorTest {
    private static final String NAME="ck3_query_player_faction_alerts_v1",MAX="18446744073709551615";
    @Test void theActualQueryProducerCanFeedItsCanonicalRevisionBackThroughTheOriginalSdkProjection()throws Exception {
        var original=original();byte[] before=original.original().bytes();var projected=RootPublicCatalogCodec.executableTool(original);
        for(String value:List.of("0","9","9007199254740991",MAX)) {
            var input=new FactionAlertReadService.Query(new BigInteger(value));RawJson encoded=FactionAlertReadService.encodeQuery(input);
            assertEquals(value,node(encoded).get("expected_revision").textValue());
            assertThrows(IllegalArgumentException.class,()->original.validateArguments(arguments(encoded)),"the old integer-only next consumer rejects even the real encoder's small string 9");
            projected.validateArguments(arguments(encoded));assertEquals(input,FactionAlertReadService.decodeQuery(encoded));
            if(input.expectedRevision().compareTo(BigInteger.valueOf(9007199254740991L))<=0) {
                RawJson numeric=raw(StrictJson.object().put("expected_revision",input.expectedRevision()));
                original.validateArguments(arguments(numeric));projected.validateArguments(arguments(numeric));
                assertEquals(input,FactionAlertReadService.decodeQuery(numeric));
                projected.validateArguments(arguments(FactionAlertReadService.encodeQuery(FactionAlertReadService.decodeQuery(numeric))));
            }
        }
        var old=node(original.original());var changed=node(projected.original());
        ((ObjectNode)old.get("inputSchema").get("properties")).remove("expected_revision");
        ((ObjectNode)changed.get("inputSchema").get("properties")).remove("expected_revision");assertEquals(old,changed);
        assertArrayEquals(before,original.original().bytes());
    }
    @Test void requiredNonNullSafeIntegerOrCanonicalUnsigned64StaysStrictAtBothActualBoundaries()throws Exception {
        var projected=RootPublicCatalogCodec.executableTool(original());
        for(String text:List.of("null","true","1.0","-1","9007199254740992",quoted("01"),quoted("+1"),quoted("-1"),quoted("18446744073709551616"),quoted(""))) {
            var value=StrictJson.object();value.set("expected_revision",StrictJson.parse(text.getBytes(java.nio.charset.StandardCharsets.UTF_8)));RawJson wrong=raw(value);
            assertThrows(IllegalArgumentException.class,()->projected.validateArguments(arguments(wrong)));
            assertThrows(IllegalArgumentException.class,()->FactionAlertReadService.decodeQuery(wrong));
        }
        RawJson missing=raw(StrictJson.object());assertThrows(IllegalArgumentException.class,()->projected.validateArguments(arguments(missing)));
        assertThrows(IllegalArgumentException.class,()->FactionAlertReadService.decodeQuery(missing));
        RawJson extra=raw(StrictJson.object().put("expected_revision","9").put("unknown",1));
        assertThrows(IllegalArgumentException.class,()->FactionAlertReadService.decodeQuery(extra));
    }
    private static String quoted(String value){return Character.toString((char)34)+value+(char)34;}
    private static ToolDescriptor original()throws Exception {return RootOriginalPublicTestInputs.tools().stream().filter(value->value.name().equals(NAME)).findFirst().orElseThrow(()->new IllegalStateException("NOT_RUN_REQUIRED_ACTUAL_ORIGINAL_TOOL: "+NAME));}
    private static ObjectNode node(RawJson value){return PublicDataJson.object(value);}
    private static RawJson raw(JsonNode value){return PublicDataJson.encode(value);}
    private static Arguments arguments(RawJson value){return new Arguments(Presence.VALUE,Optional.of(value));}
}
