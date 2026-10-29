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
import org.xar.ck3.control.application.planning.sway.SwayObservationReads;
import org.xar.ck3.control.application.planning.sway.SwayPublicCodec;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.service.mcp.*;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory.ToolDescriptor;
import org.xar.ck3.control.wave2.military.combatwire.CombatRequest;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Actual original SDK descriptors -> schema -> sole typed consumers -> request wire.
 * Missing capture fails; no synthetic schemas or the historical ten-tool subset replace it. */
final class PublicReadDescriptorConsumersTest {
    private static final BigInteger MAX=StrictJson.UINT64_MAX;
    private static final ArmyCalls.Revision REVISION=new ArmyCalls.Revision(new Present<>(MAX));
    private static ToolDescriptor original(String name)throws Exception {
        return RootOriginalPublicTestInputs.tools().stream().filter(value->value.name().equals(name)).findFirst()
                .orElseThrow(()->new IllegalStateException("NOT_RUN_REQUIRED_ACTUAL_ORIGINAL_TOOL: "+name));
    }
    private static ToolDescriptor original(PublicMethod method)throws Exception {
        var matches=RootOriginalPublicTestInputs.tools().stream().filter(value->{
            try{return PublicMcpNativeAdapter.expectedServiceMethod(value.name())==method;}
            catch(IllegalArgumentException nonService){return false;}
        }).toList();
        assertEquals(1,matches.size(),"actual original service descriptor is missing or ambiguous: "+method);
        return matches.getFirst();
    }
    private static ToolDescriptor executable(String name)throws Exception {
        var original=original(name);var transformed=RootPublicCatalogCodec.executableTool(original);
        JsonNode before=node(original.original()),after=node(transformed.original());
        before.properties().forEach(entry->{if(!entry.getKey().equals("inputSchema"))assertEquals(entry.getValue(),after.get(entry.getKey()),entry.getKey());});
        var oldSchema=before.get("inputSchema");var newSchema=after.get("inputSchema");
        oldSchema.properties().forEach(entry->{if(!entry.getKey().equals("properties"))assertEquals(entry.getValue(),newSchema.get(entry.getKey()),entry.getKey());});
        oldSchema.get("properties").properties().forEach(entry->{if(!List.of("expected_revision","after_revision","expected_native_revision").contains(entry.getKey()))
            assertEquals(entry.getValue(),newSchema.get("properties").get(entry.getKey()),entry.getKey());});
        assertEquals(before,node(original.original()));return transformed;
    }
    @Test void actualSwayCompletionAndOpinionDescriptorsReachTheSharedCodec()throws Exception {
        for(var kind:List.of(SwayObservationReads.Kind.COMPLETION,SwayObservationReads.Kind.OPINION)) {
            var descriptor=executable(kind==SwayObservationReads.Kind.COMPLETION?"ck3_query_active_scheme_sway_completion_private_v1":"ck3_query_active_scheme_sway_outcome_opinion_private_v1");
            var request=StrictJson.object().put("target_character_id",123);
            if(kind==SwayObservationReads.Kind.COMPLETION)request.put("scheme_instance_id",16777217);
            for(String revision:List.of("1","9007199254740991","\"18446744073709551615\"")) {
                request.set("expected_revision",token(revision));descriptor.validateArguments(arguments(request));
                var decoded=SwayPublicCodec.decodeDirect(kind,raw(request));var encoded=SwayPublicCodec.encodeDirectRequest(decoded);
                descriptor.validateArguments(arguments(node(encoded)));assertEquals(decoded,SwayPublicCodec.decodeDirect(kind,encoded));
                assertTrue(node(encoded).get("target_character_id").isIntegralNumber());
                if(kind==SwayObservationReads.Kind.COMPLETION)assertTrue(node(encoded).get("scheme_instance_id").isIntegralNumber());
            }
            invalid(descriptor,request,"expected_revision",value->SwayPublicCodec.decodeDirect(kind,value));
            var zero=request.deepCopy().put("expected_revision",0);assertThrows(IllegalArgumentException.class,()->descriptor.validateArguments(arguments(zero)));
            var missing=request.deepCopy();missing.remove("expected_revision");assertThrows(IllegalArgumentException.class,()->descriptor.validateArguments(arguments(missing)));
            var nil=request.deepCopy().putNull("expected_revision");assertThrows(IllegalArgumentException.class,()->descriptor.validateArguments(arguments(nil)));
        }
    }
    @Test void actualCampaignRootMetadataReachesTheRealCodecAtFullWidthIncludingZero()throws Exception {
        var descriptor=executable("ck3_query_campaign_root_context_v1");
        for(String revision:List.of("0","9007199254740991","\"0\"","\"18446744073709551615\"")) {
            var request=StrictJson.object();request.set("expected_revision",token(revision));descriptor.validateArguments(arguments(request));
            var decoded=CampaignRootPublicCodec.decodeRequest(PublicBindings.present(raw(request)));var encoded=CampaignRootPublicCodec.encodeRequest(decoded);
            descriptor.validateArguments(arguments(node(encoded)));assertEquals(decoded,CampaignRootPublicCodec.decodeRequest(PublicBindings.present(encoded)));
        }
        invalid(descriptor,StrictJson.object().put("expected_revision",MAX.toString()),"expected_revision",value->CampaignRootPublicCodec.decodeRequest(PublicBindings.present(value)));
        assertThrows(IllegalArgumentException.class,()->descriptor.validateArguments(arguments(StrictJson.object())));
    }
    @Test void actualContactMetadataPreservesStringOnlyAndMissingVersusNull()throws Exception {
        for(boolean projected:List.of(true,false)) {
            var descriptor=executable(projected?"ck3_query_projected_contact_scope_v1":"ck3_query_actual_contact_scope");
            var request=StrictJson.object().put("subject_army_id",0).put("target_province_id",2).put("expected_revision",MAX.toString());
            if(projected)request.put("incoming_entry_province_id",1);
            descriptor.validateArguments(arguments(request));
            RawJson encoded=projected?ContactScopePublicCodec.encode(ContactScopePublicCodec.projected(PublicBindings.present(raw(request))))
                    :ContactScopePublicCodec.encode(ContactScopePublicCodec.actual(PublicBindings.present(raw(request))));
            descriptor.validateArguments(arguments(node(encoded)));assertTrue(node(encoded).get("subject_army_id").isIntegralNumber());
            var zero=request.deepCopy().put("expected_revision","0");descriptor.validateArguments(arguments(zero));
            if(projected)ContactScopePublicCodec.projected(PublicBindings.present(raw(zero)));else ContactScopePublicCodec.actual(PublicBindings.present(raw(zero)));
            var numeric=request.deepCopy().put("expected_revision",1);assertThrows(IllegalArgumentException.class,()->descriptor.validateArguments(arguments(numeric)));
            invalid(descriptor,request,"expected_revision",value->projected?ContactScopePublicCodec.projected(PublicBindings.present(value)):ContactScopePublicCodec.actual(PublicBindings.present(value)));
            var missing=request.deepCopy();missing.remove("expected_revision");var nil=request.deepCopy().putNull("expected_revision");
            if(projected){assertThrows(IllegalArgumentException.class,()->descriptor.validateArguments(arguments(missing)));assertThrows(IllegalArgumentException.class,()->descriptor.validateArguments(arguments(nil)));}
            else {
                descriptor.validateArguments(arguments(missing));descriptor.validateArguments(arguments(nil));
                var absent=ContactScopePublicCodec.actual(PublicBindings.present(raw(missing)));var explicitNull=ContactScopePublicCodec.actual(PublicBindings.present(raw(nil)));
                assertFalse(node(ContactScopePublicCodec.encode(absent)).has("expected_revision"));assertTrue(node(ContactScopePublicCodec.encode(explicitNull)).get("expected_revision").isNull());
            }
        }
    }
    @Test void allThirtyThreeOriginalArmyDescriptorsReachTheirCurrentSharedCodec()throws Exception {
        int originalCount=0;
        for(var method:RootArmySuppliedPublicProducts.METHODS) {
            // This disabled Service helper has no original MCP declaration; never invent a tool alias.
            if(method==PublicMethod.QUERY_WAR_TERMINATION_EXIT_TERMS)continue;
            originalCount++;
            var original=original(method);var descriptor=executable(original.name());
            var encoded=ArmyCallCodec.encode(armyInput(method));var request=(ObjectNode)node(encoded);
            descriptor.validateArguments(arguments(request));assertEquals(armyInput(method),ArmyCallCodec.decode(method,encoded));
            if(method==PublicMethod.WAR_STATE){assertSame(original,RootPublicCatalogCodec.executableTool(original));assertFalse(request.has("expected_revision"));continue;}
            assertTrue(request.get("expected_revision").isTextual());
            invalid(descriptor,request,"expected_revision",value->ArmyCallCodec.decode(method,value));
            var schema=node(descriptor.original()).get("inputSchema");boolean required=false;
            if(schema.has("required"))for(var field:schema.get("required"))required|=field.textValue().equals("expected_revision");
            var missing=request.deepCopy();missing.remove("expected_revision");var nil=request.deepCopy().putNull("expected_revision");
            if(required){assertThrows(IllegalArgumentException.class,()->descriptor.validateArguments(arguments(missing)));assertThrows(IllegalArgumentException.class,()->descriptor.validateArguments(arguments(nil)));}
            else {descriptor.validateArguments(arguments(missing));descriptor.validateArguments(arguments(nil));ArmyCallCodec.decode(method,raw(missing));ArmyCallCodec.decode(method,raw(nil));}
            var numeric=request.deepCopy().put("expected_revision",9007199254740991L);descriptor.validateArguments(arguments(numeric));ArmyCallCodec.decode(method,raw(numeric));
            if(method==PublicMethod.QUERY_WAR_ENTRY_ASSESSMENTS){assertTrue(request.has("target_character_ids"));assertFalse(request.has("target_province_ids"));}
            if(method==PublicMethod.QUERY_CURRENT_BATTLE_KNIGHT_V1){assertTrue(request.get("expected_native_revision").isTextual());assertTrue(request.get("expected_date_raw").isIntegralNumber());}
        }
        assertEquals(33,originalCount);
    }
    @Test void actualWaitMetadataUsesAfterRevisionAndKeepsTimeoutNumeric()throws Exception {
        var descriptor=executable("ck3_wait_for_change");
        for(String revision:List.of("0","18446744073709551615","18446744073709551616")) {
            var request=StrictJson.object().put("after_revision",revision).put("timeout_seconds",10.25);
            descriptor.validateArguments(arguments(request));var decoded=WaitForChangePublicCodec.decode(PublicBindings.present(raw(request)));
            var encoded=WaitForChangePublicCodec.encode(decoded);descriptor.validateArguments(arguments(node(encoded)));
            assertEquals(decoded,WaitForChangePublicCodec.decode(PublicBindings.present(encoded)));assertTrue(node(encoded).get("timeout_seconds").isNumber());
        }
        var request=StrictJson.object().put("after_revision","0");descriptor.validateArguments(arguments(request));
        WaitForChangePublicCodec.decode(PublicBindings.present(raw(request)));
        invalid(descriptor,request,"after_revision",value->WaitForChangePublicCodec.decode(PublicBindings.present(value)),false);
        var numeric=request.deepCopy().put("after_revision",0);assertThrows(IllegalArgumentException.class,()->descriptor.validateArguments(arguments(numeric)));
        var widest=request.deepCopy().put("after_revision","9".repeat(4300));descriptor.validateArguments(arguments(widest));
        WaitForChangePublicCodec.decode(PublicBindings.present(raw(widest)));
        var over=request.deepCopy().put("after_revision","9".repeat(4301));assertThrows(IllegalArgumentException.class,()->descriptor.validateArguments(arguments(over)));
        assertThrows(IllegalArgumentException.class,()->WaitForChangePublicCodec.decode(PublicBindings.present(raw(over))));
    }
    @Test void actualNextMetadataMatchesLifecycleDataWithoutAdmittingAnEndpoint()throws Exception {
        var descriptor=executable("ck3_start_next_episode");
        for(String json:List.of("{}","{\"expected_revision\":null}","{\"expected_revision\":\"0\"}","{\"expected_revision\":\"18446744073709551615\"}")) {
            var request=token(json);descriptor.validateArguments(arguments(request));var decoded=LifecyclePublicCodec.decodeRequest(PublicBindings.present(raw(request)));
            assertEquals(decoded,LifecyclePublicCodec.decodeRequest(LifecyclePublicCodec.encodeRequest(decoded)));
        }
        var request=StrictJson.object().put("expected_revision",1);assertThrows(IllegalArgumentException.class,()->descriptor.validateArguments(arguments(request)));
        // DATA contract only; no RootNextEpisodePublicProducts, Host transition or registration is constructed.
    }
    private static void invalid(ToolDescriptor descriptor,ObjectNode seed,String field,Function<RawJson,?> consumer) {
        invalid(descriptor,seed,field,consumer,true);
    }
    private static void invalid(ToolDescriptor descriptor,ObjectNode seed,String field,Function<RawJson,?> consumer,boolean uint64) {
        var badValues=new java.util.ArrayList<>(List.of("true","1.0","9007199254740992","\"01\"","\"-1\"","\"+1\"","\"1\\n\""));
        if(uint64)badValues.add("\"18446744073709551616\"");
        for(String bad:badValues) {
            var request=seed.deepCopy();request.set(field,token(bad));
            assertThrows(IllegalArgumentException.class,()->descriptor.validateArguments(arguments(request)),field+"="+bad);
            assertThrows(IllegalArgumentException.class,()->consumer.apply(raw(request)),field+"="+bad);
        }
    }
    // Small typed inputs match the supplied helper's finite roster; ArmyCallCodec.encode is the actual producer.
    private static ArmyCalls.Call armyInput(PublicMethod method) {
        return switch(method) {
            case WAR_STATE->new ArmyCalls.Empty();
            case QUERY_DECLARABLE_WARS,RAISE_TROOPS_DEFAULT,CLOSE_WAR_DECLARED_OVERVIEW_V1,CLOSE_WAR_RESULTS_WINDOW_V1->new ArmyCalls.Frame(method,REVISION);
            case QUERY_PLAYER_ORDINARY_HOLY_WAR_DECLARATION_CONTEXT_PRIVATE_V1,QUERY_PREWAR_FORCE_COALITION_COVERAGE_V1,QUERY_PREWAR_FORCE_COALITION_COVERAGE_V2,DECLARE_WAR->new ArmyCalls.Declaration(method,REVISION,"501-3--1");
            case QUERY_WAR_OCCUPATION_TARGETS_V1,QUERY_WAR_TERMINATION_OPTIONS,QUERY_OUTBOUND_WAR_WHITE_PEACE_STATUS,QUERY_WAR_TERMINATION_TERMS,QUERY_WAR_TERMINATION_EXIT_TERMS,ENFORCE_DEMANDS,SURRENDER_WAR,OFFER_WHITE_PEACE->new ArmyCalls.War(method,REVISION,BigInteger.valueOf(99));
            case QUERY_COMBAT_SIMULATION_INPUTS,QUERY_COMBAT_SIMULATION_INPUTS_V3->new ArmyCalls.Combat(method,REVISION,new CombatRequest(11,12,List.of(0),List.of(4),null),new Missing<>());
            case QUERY_WAR_ENTRY_ASSESSMENTS->new ArmyCalls.WarEntry(REVISION,List.of(new PositiveId(501)));
            case COLLECT_DECLARABLE_WARS_RESULT_V1->new ArmyCalls.Collect(REVISION,"fixture-declaration-request");
            case QUERY_CURRENT_BATTLE_KNIGHT_V1->new ArmyCalls.Knight(REVISION,new ArmyRequests.Knight(new PublicUnitId(0),new PositiveId(707),new PositiveId(8),new PositiveId(707),99,new PositiveId(4),new PositiveId(5),new PositiveId(11),24000,UInt64.positive(BigInteger.valueOf(41)),"native:41"));
            case QUERY_COMBAT_PHASE_EVENT_TRACE_V1->new ArmyCalls.CombatId(method,REVISION,new FullId(5));
            case QUERY_ARMY_STRENGTHS->new ArmyCalls.Strengths(REVISION,List.of(new PublicUnitId(0)),new Missing<>(),new Missing<>(),new Missing<>());
            case SUBMIT_CALL_ALLY_TO_WAR_PRIVATE_V1->new ArmyCalls.CallAlly(REVISION,new FullId(99),new FullId(501));
            case SUBMIT_REGULAR_MAA_CREATE_PRIVATE_V1->new ArmyCalls.CreateMaa(REVISION,3,"fixture-maa-one",new Missing<>());
            case MOVE_ARMY->new ArmyCalls.Move(REVISION,new PublicUnitId(0),new PositiveId(11));
            case START_ASSAULT,STOP_ASSAULT->new ArmyCalls.Siege(method,REVISION,new PositiveId(22));
            case DISBAND_ARMY->new ArmyCalls.Unit(method,REVISION,new PublicUnitId(0));
            case HIRE_MERCENARY_V1,HIRE_HOLY_ORDER_V1->new ArmyCalls.Hire(method,REVISION,new HireId(3));
            case ASSIGN_ARMY_COMMANDER_V1->new ArmyCalls.AssignCommander(REVISION,new PublicUnitId(0),new PublicUnitId(707));
            case SET_ARMY_GATHERING_RESEARCH_SAMPLING_V1->new ArmyCalls.Sampling(REVISION,false);
            default->throw new IllegalArgumentException("outside the actual supplied Army roster");
        };
    }
    private static PublicMcpDirectory.Arguments arguments(JsonNode value){return new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,Optional.of(raw(value)));}
    private static RawJson raw(JsonNode value){return PublicDataJson.encode(value);}
    private static JsonNode node(RawJson value){return PublicDataJson.object(value);}
    private static JsonNode token(String value){return StrictJson.parse(value.getBytes(StandardCharsets.UTF_8));}
}
