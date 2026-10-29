package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.service.mcp.*;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** Sole supplied table and actual SDK descriptor consumer. No software Root/Core/Native proof is invented. */
final class RootRiteSuppliedRegistrationTest {
    private static final ExactRef SOURCE=new ExactRef("software-rite-public-source",1,"a".repeat(64));
    private static final String QUERY="ck3_query_player_rite_creation_action_context_v1";
    private static final String EXECUTE="ck3_execute_player_rite_creation_action_v1";
    private static final String COLLECT="ck3_collect_player_rite_creation_action_result_v1";
    private static Arguments arguments(String json) {
        return new Arguments(Presence.VALUE,Optional.of(new RawJson(json.getBytes(StandardCharsets.UTF_8))));
    }
    private static ToolCall call(String name,String json) {
        return new ToolCall(name,arguments(json),Optional.empty(),new McpCancellation());
    }
    @Test void registeringTheSoleTableNeverResolvesAnUncommittedCoreAndKeepsAllThreeOriginalTargets() {
        var resolves=new AtomicInteger();
        var bindings=RootMcpRiteCreation.suppliedMethods(SOURCE,()->{
            resolves.incrementAndGet();throw new IOException("actual Core not bound in this DATA-only regression");
        });
        assertEquals(0,resolves.get());assertEquals(Set.of(QUERY,EXECUTE,COLLECT),
                bindings.stream().map(McpExecutableDirectory.DirectBinding::name).collect(java.util.stream.Collectors.toSet()));
        for(var binding:bindings) {
            assertEquals(PublicMcpBindings.Kind.DRIVER_DIRECT,binding.kind());
            assertEquals(RootMcpRiteCreation.class.getName(),binding.target().actualClass());
            assertEquals(SOURCE,binding.target().implementationSource());
            assertEquals(RawJson.class,binding.resultType());
        }
        assertEquals(List.of("query","execute","collect"),bindings.stream().map(binding->binding.target().actualMethod()).toList());
    }
    @Test void requiredActualSdkDescriptorsReachTheSoleTypedDecoderBeforeCurrentRootResolution()throws Exception {
        var resolves=new AtomicInteger();
        var bindings=RootMcpRiteCreation.suppliedMethods(SOURCE,()->{
            resolves.incrementAndGet();throw new IOException("real Managed Root input required");
        });
        var tools=RootOriginalPublicTestInputs.tools();
        for(var binding:bindings) {
            String json=switch(binding.name()) {
                case QUERY -> "{\"expected_revision\":\"18446744073709551615\",\"expected_source_rite_id\":26}";
                case EXECUTE -> "{\"operation\":\"open_create_draft\",\"expected_revision\":\"18446744073709551615\",\"expected_source_rite_id\":26}";
                case COLLECT -> "{\"action_request_id\":\"rite-action-"+"1".repeat(32)+"\",\"timeout_seconds\":0}";
                default -> throw new AssertionError("unexpected direct route");
            };
            var descriptor=tools.stream().filter(row->row.name().equals(binding.name())).findFirst().orElseThrow(
                    ()->new AssertionError("mandatory actual conditional Rite SDK descriptor missing: "+binding.name()));
            var invocation=call(binding.name(),json);descriptor.validateArguments(invocation.arguments());
            assertThrows(UncheckedIOException.class,()->invoke(binding,invocation));
        }
        assertEquals(3,resolves.get(),"each actual route resolves once at invocation, never at registration");
    }
    @Test void wrongMissingNullAndUnknownFieldsNeverResolveRootOrBorrowPreviewAsAnAction() {
        var resolves=new AtomicInteger();
        var bindings=RootMcpRiteCreation.suppliedMethods(SOURCE,()->{
            resolves.incrementAndGet();throw new IOException("must not resolve");
        });
        for(var binding:bindings) {
            for(String json:List.of("{}","null","{\"expected_revision\":true}",
                    "{\"expected_revision\":null,\"expected_source_rite_id\":26}","{\"unexpected_alias\":1}"))
                assertThrows(IllegalArgumentException.class,()->binding.decoder().decode(call(binding.name(),json)));
        }
        var execute=bindings.stream().filter(binding->binding.name().equals(EXECUTE)).findFirst().orElseThrow();
        assertThrows(IllegalArgumentException.class,()->execute.decoder().decode(call(EXECUTE,
                "{\"operation\":\"preview\",\"expected_revision\":17,\"expected_source_rite_id\":26}")));
        assertEquals(0,resolves.get());
    }
    private static <Q,R> R invoke(McpExecutableDirectory.DirectBinding<Q,R> binding,ToolCall call)throws InterruptedException,ToolFailure,RpcFailure {
        return binding.actual().invoke(binding.decoder().decode(call));
    }
}
