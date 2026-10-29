package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.planning.sway.SwayDriverCodec;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.service.mcp.*;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory.ToolDescriptor;

/** Same mandatory actual SDK metadata as the runtime input, then the actual owner request codecs.
 * DATA request roundtrips grant no source, archive custody, action or gameplay qualification. */
final class PublicLateDescriptorConsumersTest {
    private static final String MAX="18446744073709551615";

    @Test void actualSwayDriverTargetAndReceiptMetadataAcceptOnlyDeclaredWideFields()throws Exception {
        var target=descriptor("ck3_query_active_scheme_sway_target_private_v1");
        var receipt=descriptor("ck3_query_active_scheme_sway_receipt_private_v1");
        for(String wide:List.of("1","9007199254740991","\""+MAX+"\"")) {
            var request=StrictJson.object().put("target_character_id",123);request.set("expected_revision",token(wide));
            target.validateArguments(arguments(request));var typed=SwayDriverCodec.decodeTarget(raw(request));
            var encoded=SwayDriverCodec.encode(typed);target.validateArguments(arguments(node(encoded)));
            assertEquals(typed,SwayDriverCodec.decodeTarget(encoded));assertTrue(node(encoded).get("target_character_id").isIntegralNumber());
            var actualReceipt=request.deepCopy().put("action_id","sway-fixture");actualReceipt.set("pre_capture_epoch",token(wide));
            receipt.validateArguments(arguments(actualReceipt));var parsed=SwayDriverCodec.decodeReceipt(raw(actualReceipt));
            var encodedReceipt=SwayDriverCodec.encode(parsed);receipt.validateArguments(arguments(node(encodedReceipt)));
            assertEquals(parsed,SwayDriverCodec.decodeReceipt(encodedReceipt));
        }
        var request=StrictJson.object().put("target_character_id",123).put("expected_revision",MAX);
        invalid(target,request,"expected_revision",SwayDriverCodec::decodeTarget,true);
        var actualReceipt=request.deepCopy().put("action_id","sway-fixture").put("pre_capture_epoch",MAX);
        invalid(receipt,actualReceipt,"pre_capture_epoch",SwayDriverCodec::decodeReceipt,true);
        var start=original("ck3_start_active_scheme_sway_private_v1");
        // The original opaque readback object is validated against its real archived quote by Sway's owner.
        // A descriptor overlay must not turn arbitrary nested fields into a claimed valid quote.
        assertSame(start,RootPublicCatalogCodec.executableTool(start));
    }

    @Test void actualArrangeMetadataPreservesTheSharedOptionalRevisionBranches()throws Exception {
        var descriptor=descriptor("ck3_arrange_marriage");
        for(String suffix:List.of("",",\"expected_revision\":null",",\"expected_revision\":0",",\"expected_revision\":9007199254740991",",\"expected_revision\":\""+MAX+"\"")) {
            var request=token("{\"choice_id\":\"501-502\""+suffix+"}");descriptor.validateArguments(arguments(request));
            var typed=MarriageArrangePublicCodec.decode(PublicBindings.present(raw(request)));
            var encoded=MarriageArrangePublicCodec.encodeRequest(typed);descriptor.validateArguments(arguments(node(encoded)));
            assertEquals(typed,MarriageArrangePublicCodec.decode(PublicBindings.present(encoded)));
        }
        invalid(descriptor,StrictJson.object().put("choice_id","501-502").put("expected_revision",MAX),"expected_revision",
                value->MarriageArrangePublicCodec.decode(PublicBindings.present(value)),false);
        assertThrows(IllegalArgumentException.class,()->MarriageArrangePublicCodec.decode(new PublicBindings.Missing()));
    }

    @Test void actualResolveEventMetadataRetainsMissingNullAndBoundedInstanceId()throws Exception {
        var descriptor=descriptor("ck3_resolve_active_event");
        for(String json:List.of("{}","{\"event_instance_id\":null,\"expected_revision\":null}","{\"event_instance_id\":7,\"expected_revision\":\"0\"}","{\"event_instance_id\":7,\"expected_revision\":\""+MAX+"\"}")) {
            var request=token(json);descriptor.validateArguments(arguments(request));
            var typed=EventResolutionPublicCodec.decode(PublicBindings.present(raw(request)));var encoded=EventResolutionPublicCodec.encodeRequest(typed);
            descriptor.validateArguments(arguments(node(encoded)));assertEquals(typed,EventResolutionPublicCodec.decode(PublicBindings.present(encoded)));
            if(node(encoded).hasNonNull("event_instance_id"))assertTrue(node(encoded).get("event_instance_id").isIntegralNumber());
        }
        invalid(descriptor,StrictJson.object().put("expected_revision",MAX),"expected_revision",value->EventResolutionPublicCodec.decode(PublicBindings.present(value)),false);
        var numeric=StrictJson.object().put("expected_revision",1);
        assertThrows(IllegalArgumentException.class,()->descriptor.validateArguments(arguments(numeric)));
        assertThrows(IllegalArgumentException.class,()->EventResolutionPublicCodec.decode(PublicBindings.present(raw(numeric))));
    }

    @Test void actualSettlementMetadataMatchesTheRealLifecycleRequestCodec()throws Exception {
        var descriptor=descriptor("ck3_settle_one_life");
        for(String json:List.of("{}","{\"expected_revision\":null}","{\"expected_revision\":\"0\"}","{\"expected_revision\":\""+MAX+"\"}")) {
            var request=token(json);descriptor.validateArguments(arguments(request));
            var typed=LifecyclePublicCodec.decodeRequest(PublicBindings.present(raw(request)));
            var encoded=LifecyclePublicCodec.encodeRequest(typed);
            assertInstanceOf(PublicBindings.Value.class,encoded);
            descriptor.validateArguments(arguments(node(((PublicBindings.Value)encoded).original())));
            assertEquals(typed,LifecyclePublicCodec.decodeRequest(encoded));
        }
        var numeric=StrictJson.object().put("expected_revision",1);
        assertThrows(IllegalArgumentException.class,()->descriptor.validateArguments(arguments(numeric)));
        assertThrows(IllegalArgumentException.class,()->LifecyclePublicCodec.decodeRequest(PublicBindings.present(raw(numeric))));
    }

    @Test void actualInteractionMetadataReachesTheThreeExactStringOnlyConsumers()throws Exception {
        for(String name:List.of("ck3_query_pending_character_interaction_context_v1","ck3_query_character_interaction_ordinary_v1","ck3_initiate_character_interaction_ordinary_v1")) {
            boolean pending=name.equals("ck3_query_pending_character_interaction_context_v1");var descriptor=descriptor(name);
            var request=StrictJson.object().put("expected_revision",MAX);
            if(pending)request.put("pending_interaction_id",-2);else request.put("interaction_key","marriage_interaction").put("recipient_id",123);
            descriptor.validateArguments(arguments(request));
            if(pending) {
                var typed=InteractionDirectPublicCodec.pendingRequest(PublicBindings.present(raw(request)));
                var encoded=InteractionDirectPublicCodec.encodeRequest(typed);descriptor.validateArguments(arguments(node(encoded)));
                assertEquals(typed,InteractionDirectPublicCodec.pendingRequest(PublicBindings.present(encoded)));
                assertTrue(node(encoded).get("pending_interaction_id").isIntegralNumber());
            } else {
                var typed=InteractionDirectPublicCodec.ordinaryRequest(PublicBindings.present(raw(request)));
                var encoded=InteractionDirectPublicCodec.encodeRequest(typed);descriptor.validateArguments(arguments(node(encoded)));
                assertEquals(typed,InteractionDirectPublicCodec.ordinaryRequest(PublicBindings.present(encoded)));
                assertTrue(node(encoded).get("recipient_id").isIntegralNumber());
            }
            Function<RawJson,?> consumer=value->pending?InteractionDirectPublicCodec.pendingRequest(PublicBindings.present(value)):InteractionDirectPublicCodec.ordinaryRequest(PublicBindings.present(value));
            invalid(descriptor,request,"expected_revision",consumer,false);
            for(String bad:List.of("null","0","1")) {
                var rejected=request.deepCopy();rejected.set("expected_revision",token(bad));
                assertThrows(IllegalArgumentException.class,()->descriptor.validateArguments(arguments(rejected)));
                assertThrows(IllegalArgumentException.class,()->consumer.apply(raw(rejected)));
            }
            var missing=request.deepCopy();missing.remove("expected_revision");
            assertThrows(IllegalArgumentException.class,()->descriptor.validateArguments(arguments(missing)));
            assertThrows(IllegalArgumentException.class,()->consumer.apply(raw(missing)));
        }
    }

    private static ToolDescriptor original(String name)throws Exception {
        return RootOriginalPublicTestInputs.tools().stream().filter(value->value.name().equals(name)).findFirst()
                .orElseThrow(()->new IllegalStateException("NOT_RUN_REQUIRED_ACTUAL_ORIGINAL_TOOL: "+name));
    }
    private static ToolDescriptor descriptor(String name)throws Exception{return RootPublicCatalogCodec.executableTool(original(name));}
    private static void invalid(ToolDescriptor descriptor,ObjectNode seed,String field,Function<RawJson,?> consumer,boolean positive) {
        var invalid=new java.util.ArrayList<>(List.of("true","1.0","9007199254740992","\"01\"","\"-1\"","\"+1\"","\"18446744073709551616\""));
        if(positive)invalid.add("\"0\"");
        for(String value:invalid) {
            var request=seed.deepCopy();request.set(field,token(value));
            assertThrows(IllegalArgumentException.class,()->descriptor.validateArguments(arguments(request)),field+"="+value);
            assertThrows(IllegalArgumentException.class,()->consumer.apply(raw(request)),field+"="+value);
        }
    }
    private static PublicMcpDirectory.Arguments arguments(JsonNode value){return new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,Optional.of(raw(value)));}
    private static RawJson raw(JsonNode value){return PublicDataJson.encode(value);}
    private static JsonNode node(RawJson value){return PublicDataJson.object(value);}
    private static JsonNode token(String value){return StrictJson.parse(value.getBytes(StandardCharsets.UTF_8));}
}
