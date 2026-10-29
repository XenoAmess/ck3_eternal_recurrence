package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.ritecreation.RiteCreationCodec;
import org.xar.ck3.control.application.ritecreation.RiteCreationContract;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernancePublicService;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory.ToolDescriptor;

/** Mandatory same actual SDK tools capture, not synthetic schemas or Native readiness. */
final class PublicRiteGovernanceDescriptorTest {
    private static ToolDescriptor original(String name)throws Exception {
        return RootOriginalPublicTestInputs.tools().stream().filter(value->value.name().equals(name)).findFirst().orElseThrow(
                ()->new IllegalStateException("NOT_RUN_REQUIRED_ACTUAL_ORIGINAL_TOOL: "+name));
    }
    @Test void actualRiteQueryAndExecuteSchemasReachTheSolePureRequestCodec()throws Exception {
        var source=new RiteCreationContract.SourceRite(0);
        var action=new RiteCreationContract.Execute(StrictJson.UINT64_MAX,source,new RiteCreationContract.OpenCreate());
        var executeWire=RiteCreationCodec.execution(action);
        var execute=RootPublicCatalogCodec.executableTool(original("ck3_execute_player_rite_creation_action_v1"));
        execute.validateArguments(arguments(node(executeWire)));assertEquals(action,RiteCreationCodec.execute(executeWire));
        var query=RootPublicCatalogCodec.executableTool(original("ck3_query_player_rite_creation_action_context_v1"));
        var queryWire=StrictJson.object().put("expected_revision",StrictJson.UINT64_MAX.toString()).put("expected_source_rite_id",0);
        query.validateArguments(arguments(queryWire));assertEquals(new RiteCreationContract.Query(StrictJson.UINT64_MAX,source),RiteCreationCodec.query(raw(queryWire)));
        for(boolean write:List.of(false,true)) {
            var descriptor=write?execute:query;var seed=write?(ObjectNode)node(executeWire):queryWire;
            for(String value:List.of("1","9007199254740991","\"18446744073709551615\"")) {
                var request=seed.deepCopy();request.set("expected_revision",token(value));descriptor.validateArguments(arguments(request));
                if(write){var decoded=RiteCreationCodec.execute(raw(request));descriptor.validateArguments(arguments(node(RiteCreationCodec.execution(decoded))));}
                else RiteCreationCodec.query(raw(request));
                assertTrue(request.get("expected_source_rite_id").isIntegralNumber());
            }
            rejected(descriptor,seed,"expected_revision",value->{if(write)RiteCreationCodec.execute(value);else RiteCreationCodec.query(value);return value;},true);
        }
        var collect=original("ck3_collect_player_rite_creation_action_result_v1");assertSame(collect,RootPublicCatalogCodec.executableTool(collect));
    }
    private record Case(String name,ObjectNode seed,List<String> roles,Function<RawJson,RawJson> roundTrip,boolean positive) { }
    @Test void actualGovernanceMetadataAndEveryRequestConsumerUseTheSameExactWidthRoles()throws Exception {
        String max=StrictJson.UINT64_MAX.toString();
        var council=StrictJson.object().put("expected_snapshot_id","native:41").put("public_revision",max).put("native_revision",max)
                .put("date_raw",24000).put("owner_character_id",1);
        var development=StrictJson.object().put("expected_revision",max);
        var change=StrictJson.object().put("councillor_character_id",1).put("target_county_title_id",2).put("expected_revision",max).put("replace_existing_task",false);
        var cases=List.of(new Case("ck3_query_council_composition_candidates_v1",council,List.of("public_revision","native_revision"),
                    value->GovernancePublicService.encodeCouncilRequest(GovernancePublicService.decodeCouncil(value)),true),
                new Case("ck3_query_steward_develop_county_candidates_v1",development,List.of("expected_revision"),
                    value->GovernancePublicService.encodeDevelopmentRequest(GovernancePublicService.decodeDevelopment(value)),false),
                new Case("ck3_change_steward_develop_county_task_v1",change,List.of("expected_revision"),
                    value->GovernancePublicService.encodeChangeRequest(GovernancePublicService.decodeChange(value)),true));
        for(var fixture:cases) {
            var original=original(fixture.name());var descriptor=RootPublicCatalogCodec.executableTool(original);
            var oldProperties=node(original.original()).get("inputSchema").get("properties");var newProperties=node(descriptor.original()).get("inputSchema").get("properties");
            oldProperties.properties().forEach(entry->{if(!fixture.roles().contains(entry.getKey()))assertEquals(entry.getValue(),newProperties.get(entry.getKey()));});
            descriptor.validateArguments(arguments(fixture.seed()));var wire=fixture.roundTrip().apply(raw(fixture.seed()));
            descriptor.validateArguments(arguments(node(wire)));assertEquals(node(wire),node(fixture.roundTrip().apply(wire)));
            for(String field:fixture.roles()) {
                var numeric=fixture.seed().deepCopy().put(field,9007199254740991L);descriptor.validateArguments(arguments(numeric));fixture.roundTrip().apply(raw(numeric));
                rejected(descriptor,fixture.seed(),field,fixture.roundTrip(),fixture.positive());
            }
        }
    }
    private static void rejected(ToolDescriptor descriptor,ObjectNode seed,String field,Function<RawJson,RawJson> consumer,boolean positive) {
        for(String value:List.of("null","true","1.0","9007199254740992","\"00\"","\"-1\"","\"18446744073709551616\"")) {
            var request=seed.deepCopy();request.set(field,token(value));
            assertThrows(IllegalArgumentException.class,()->descriptor.validateArguments(arguments(request)));assertThrows(IllegalArgumentException.class,()->consumer.apply(raw(request)));
        }
        var missing=seed.deepCopy();missing.remove(field);assertThrows(IllegalArgumentException.class,()->descriptor.validateArguments(arguments(missing)));
        var zero=seed.deepCopy().put(field,"0");
        if(positive){assertThrows(IllegalArgumentException.class,()->descriptor.validateArguments(arguments(zero)));assertThrows(IllegalArgumentException.class,()->consumer.apply(raw(zero)));}
        else {descriptor.validateArguments(arguments(zero));consumer.apply(raw(zero));}
    }
    private static PublicMcpDirectory.Arguments arguments(JsonNode value){return new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,Optional.of(raw(value)));}
    private static RawJson raw(JsonNode value){return PublicDataJson.encode(value);}
    private static JsonNode node(RawJson value){return PublicDataJson.object(value);}
    private static JsonNode token(String value){return StrictJson.parse(value.getBytes(StandardCharsets.UTF_8));}
}
