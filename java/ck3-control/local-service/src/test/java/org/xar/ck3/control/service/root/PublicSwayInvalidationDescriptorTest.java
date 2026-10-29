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
import org.xar.ck3.control.application.planning.sway.SwayPublicCodec;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory.ToolDescriptor;

/** Actual SDK metadata -> sole projection -> sole owner request codec. No live read, fake Root,
 * source permission or enablement is inferred from this DATA serialization boundary. */
final class PublicSwayInvalidationDescriptorTest {
    private static final String NAME="ck3_query_active_scheme_sway_completion_invalidation_reason_private_v1";
    private static final String MAX="18446744073709551615";
    @Test void fullWidthRevisionAndCursorPassActualProjectedMetadataAndTheOwnerCodec()throws Exception {
        var original=original();var projected=RootPublicCatalogCodec.executableTool(original);
        for(String revision:List.of("1","9007199254740991","\""+MAX+"\""))
            for(String sequence:List.of("0","9007199254740991","\""+MAX+"\"")) {
                var input=input();input.set("expected_revision",token(revision));input.set("after_sequence",token(sequence));
                if(input.get("expected_revision").isIntegralNumber()&&input.get("after_sequence").isIntegralNumber())original.validateArguments(arguments(input));
                projected.validateArguments(arguments(input));
                var request=SwayPublicCodec.decodeInvalidation(raw(input));var encoded=SwayPublicCodec.encodeInvalidationRequest(request);
                var roundtrip=PublicDataJson.object(encoded);projected.validateArguments(arguments(roundtrip));
                assertEquals(request,SwayPublicCodec.decodeInvalidation(encoded));
                assertEquals(request.expectedRevision().toString(),roundtrip.get("expected_revision").textValue());
                assertEquals(request.afterSequence().toString(),roundtrip.get("after_sequence").textValue());
                assertTrue(roundtrip.get("target_character_id").isIntegralNumber());assertTrue(roundtrip.get("scheme_instance_id").isIntegralNumber());
            }
        var wide=input().put("expected_revision",MAX).put("after_sequence",MAX);
        assertThrows(IllegalArgumentException.class,()->original.validateArguments(arguments(wide)));
        projected.validateArguments(arguments(wide));assertEquals(new BigInteger(MAX),SwayPublicCodec.decodeInvalidation(raw(wide)).afterSequence());
        var before=PublicDataJson.object(original.original()).get("inputSchema");var after=PublicDataJson.object(projected.original()).get("inputSchema");
        assertEquals(before.get("required"),after.get("required"));
        for(String field:List.of("target_character_id","scheme_instance_id"))assertEquals(before.get("properties").get(field),after.get("properties").get(field));
    }
    @Test void cursorDefaultAndStrictTypesArePreservedWithoutAddingAnEnablementOrGenerationArgument()throws Exception {
        var projected=RootPublicCatalogCodec.executableTool(original());var missing=input();missing.remove("after_sequence");
        projected.validateArguments(arguments(missing));var request=SwayPublicCodec.decodeInvalidation(raw(missing));assertEquals(BigInteger.ZERO,request.afterSequence());
        var encoded=SwayPublicCodec.encodeInvalidationRequest(request);assertEquals("0",PublicDataJson.object(encoded).get("after_sequence").textValue());
        projected.validateArguments(arguments(PublicDataJson.object(encoded)));assertEquals(request,SwayPublicCodec.decodeInvalidation(encoded));
        for(String field:List.of("expected_revision","after_sequence")) {
            for(String bad:List.of("null","true","1.0","9007199254740992","\"01\"","\"+1\"","\"-1\"","\"18446744073709551616\"","\"1\\n\"")) {
                var wrong=input();wrong.set(field,token(bad));
                assertThrows(IllegalArgumentException.class,()->projected.validateArguments(arguments(wrong)));
                assertThrows(IllegalArgumentException.class,()->SwayPublicCodec.decodeInvalidation(raw(wrong)));
            }
        }
        for(String bad:List.of("0","\"0\"")) {
            var wrong=input();wrong.set("expected_revision",token(bad));
            assertThrows(IllegalArgumentException.class,()->projected.validateArguments(arguments(wrong)));
            assertThrows(IllegalArgumentException.class,()->SwayPublicCodec.decodeInvalidation(raw(wrong)));
        }
        var noRevision=input();noRevision.remove("expected_revision");
        assertThrows(IllegalArgumentException.class,()->projected.validateArguments(arguments(noRevision)));
        assertThrows(IllegalArgumentException.class,()->SwayPublicCodec.decodeInvalidation(raw(noRevision)));
        for(String field:List.of("target_character_id","scheme_instance_id")) {
            var absent=input();absent.remove(field);
            assertThrows(IllegalArgumentException.class,()->projected.validateArguments(arguments(absent)));
            assertThrows(IllegalArgumentException.class,()->SwayPublicCodec.decodeInvalidation(raw(absent)));
            for(String bad:List.of("null","true","1.0","\"1\"")) {
                var wrong=input();wrong.set(field,token(bad));
                assertThrows(IllegalArgumentException.class,()->projected.validateArguments(arguments(wrong)));
                assertThrows(IllegalArgumentException.class,()->SwayPublicCodec.decodeInvalidation(raw(wrong)));
            }
        }
        for(String field:List.of("scheme_instance_generation","generation","enabled")) {
            var wrong=input().put(field,1);assertThrows(IllegalArgumentException.class,()->projected.validateArguments(arguments(wrong)));
            assertThrows(IllegalArgumentException.class,()->SwayPublicCodec.decodeInvalidation(raw(wrong)));
        }
        assertThrows(IllegalArgumentException.class,()->SwayPublicCodec.decodeInvalidation(raw(input().put("target_character_id",2147483648L))));
        assertThrows(IllegalArgumentException.class,()->SwayPublicCodec.decodeInvalidation(raw(input().put("scheme_instance_id",4294967295L))));
    }
    private static ObjectNode input(){return StrictJson.object().put("expected_revision",1).put("target_character_id",1).put("scheme_instance_id",1).put("after_sequence",0);}
    private static ToolDescriptor original()throws Exception {return RootOriginalPublicTestInputs.tools().stream().filter(value->value.name().equals(NAME)).findFirst().orElseThrow(()->new IllegalStateException("NOT_RUN_REQUIRED_ACTUAL_ORIGINAL_TOOL: "+NAME));}
    private static JsonNode token(String text){return StrictJson.parse(text.getBytes(java.nio.charset.StandardCharsets.UTF_8));}
    private static RawJson raw(JsonNode value){return PublicDataJson.encode(value);}
    private static PublicMcpDirectory.Arguments arguments(JsonNode value){return new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,Optional.of(raw(value)));}
}
