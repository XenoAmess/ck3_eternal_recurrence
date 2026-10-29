package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.service.mcp.McpCoverage;
import org.xar.ck3.control.service.mcp.McpExecutableDirectory;
import org.xar.ck3.control.service.mcp.PublicMcpBindings;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleBinding;
import static org.xar.ck3.control.service.root.RootSelectedRegistrationConfiguration.*;

/** Software producer -> shared admission serde -> real executable-directory consumer.
 * Fixture refs here are never published or presented as first-live originals. */
class RootPublicMcpAdmissionTest {
    @TempDir Path root;
    private ExactRef ref(String name){return new ExactRef(root.resolve(name).toString(),7,"2".repeat(64));}
    private static RawJson raw(String text){return new RawJson(text.getBytes(StandardCharsets.UTF_8));}
    private McpCoverage.Declaration declaration(String name){return new McpCoverage.Declaration(name,ref("mcp_server.py"),1,2,"fixture",List.of());}
    private PublicMcpDirectory.ToolDescriptor descriptor(String name) {
        return new PublicMcpDirectory.ToolDescriptor(name,raw("{\"name\":\""+name+"\",\"inputSchema\":{\"type\":\"object\",\"properties\":{},\"required\":[]}}"));
    }
    private List<PublicMcpDirectory.ResourceDescriptor> resources() {
        return List.of(resource("ck3://capabilities"),resource("ck3://state/current"));
    }
    private static PublicMcpDirectory.ResourceDescriptor resource(String uri) {
        return new PublicMcpDirectory.ResourceDescriptor(uri,raw("{\"uri\":\""+uri+"\",\"name\":\"fixture\"}"));
    }
    private RootPublicCatalogCodec.PublicCatalog original(List<String> names,McpCoverage.Admission prior) {
        var declarations=names.stream().map(this::declaration).toList();
        var decisions=names.stream().map(name->new McpCoverage.Decision(name,prior,ref("prior-producer.java"),"fixture prior label")).toList();
        return new RootPublicCatalogCodec.PublicCatalog(new McpCoverage.Catalog(declarations),decisions,names.stream().map(this::descriptor).toList(),resources());
    }
    private RootRuntimePublicCatalog.HandlerProducts handlers(PublicBindings registry,List<McpExecutableDirectory.DirectBinding<?,?>> direct) {
        return new RootRuntimePublicCatalog.HandlerProducts(registry,direct,List.of(),Optional.empty(),Optional.empty());
    }
    private void install(PublicBindings registry,PublicMethod method,ExactRef source,AtomicInteger invoked) {
        registry.register(method,String.class,RawJson.class,input->{invoked.incrementAndGet();return raw("{}");},
            arguments->"fixture",response->response,new PublicRoutes.Target(getClass().getName(),method.pythonName(),source),PublicRoutes.Status.IMPLEMENTED,"fixture actual typed callable");
    }
    @Test void actualBindingsProduceAdmissionConsumedByTheExistingExecutableDirectoryWithoutInvokingHandlers() {
        var source=ref("actual.java");var producer=ref("RootPublicMcpAdmission.java");var invoked=new AtomicInteger();
        var registry=new PublicBindings();install(registry,PublicMethod.CAPABILITIES,source,invoked);install(registry,PublicMethod.SNAPSHOT,source,invoked);
        var original=original(List.of("ck3_get_capabilities","ck3_take_snapshot"),McpCoverage.Admission.UNMIGRATED);
        var decisions=RootPublicMcpAdmission.derive(original,handlers(registry,List.of()),Set.of(),Set.of(source,producer),producer);
        assertTrue(decisions.stream().allMatch(row->row.admission()==McpCoverage.Admission.ADMITTED&&row.actualAdmissionProducer().equals(source)));
        var reopened=RootPublicCatalogCodec.decodeAdmission(RootPublicCatalogCodec.encodeAdmission(decisions));assertEquals(decisions,reopened);
        registry.freeze(Set.of(PublicMethod.CAPABILITIES,PublicMethod.SNAPSHOT));
        assertInstanceOf(McpExecutableDirectory.Complete.class,McpExecutableDirectory.assemble(original.catalog(),reopened,original.tools(),original.resources(),registry,List.of()));
        assertEquals(0,invoked.get(),"admission constructs and inspects callables; it must not run Native/Game work");
    }
    @Test void assembledDirectoryRetainsActualResultsFailuresAndResourcesWithoutCaptureCustody() throws Exception {
        var source=ref("actual.java");var producer=ref("RootPublicMcpAdmission.java");
        var calls=new AtomicInteger();var snapshotCalls=new AtomicInteger();
        var fail=new java.util.concurrent.atomic.AtomicBoolean();
        var originalFailure=new IllegalStateException("actual software service guard rejected");
        RawJson business=raw("{\"kept\":\"actual software result\"}");
        var registry=new PublicBindings();
        registry.register(PublicMethod.CAPABILITIES,String.class,RawJson.class,input->{
            calls.incrementAndGet();if(fail.get())throw originalFailure;return business;
        },arguments->"fixture",response->response,
            new PublicRoutes.Target(getClass().getName(),PublicMethod.CAPABILITIES.pythonName(),source),
            PublicRoutes.Status.IMPLEMENTED,"software fixture actual guarded callable");
        install(registry,PublicMethod.SNAPSHOT,source,snapshotCalls);
        var original=original(List.of("ck3_get_capabilities","ck3_take_snapshot"),McpCoverage.Admission.UNMIGRATED);
        var decisions=RootPublicMcpAdmission.derive(original,handlers(registry,List.of()),Set.of(),Set.of(source,producer),producer);
        var reopened=RootPublicCatalogCodec.decodeAdmission(RootPublicCatalogCodec.encodeAdmission(decisions));
        registry.freeze(Set.of(PublicMethod.CAPABILITIES,PublicMethod.SNAPSHOT));
        var assembled=assertInstanceOf(McpExecutableDirectory.Complete.class,McpExecutableDirectory.assemble(
            original.catalog(),reopened,original.tools(),original.resources(),registry,List.of()));
        var retained=RootOriginalMcpInvocationDirectory.bind(assembled);
        assertSame(assembled,retained);assertSame(assembled.directory(),retained.directory());
        var call=new PublicMcpDirectory.ToolCall("ck3_get_capabilities",
            new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.MISSING,Optional.empty()),
            Optional.empty(),new org.xar.ck3.control.service.mcp.McpCancellation());
        assertArrayEquals(PublicMcpDirectory.CallResult.fromBusinessJson(business).bytes(),retained.directory().invoke(call).bytes());
        assertEquals(1,calls.get());
        fail.set(true);
        assertSame(originalFailure,assertThrows(IllegalStateException.class,()->retained.directory().invoke(call)));
        assertEquals(2,calls.get(),"each requested invocation enters the original callable once");
        var read=new PublicMcpDirectory.ResourceCall("ck3://state/current",Optional.empty(),
            new org.xar.ck3.control.service.mcp.McpCancellation());
        assertArrayEquals(PublicMcpDirectory.ResourceResult.fromBusinessJson("ck3://state/current",raw("{}")).bytes(),
            retained.directory().read(read).bytes());
        assertEquals(1,snapshotCalls.get());assertEquals(2,calls.get());
    }
    @Test void oldAdmittedLabelsAndServiceEnumEntriesCannotSupplyAMissingTypedHandler() {
        var producer=ref("RootPublicMcpAdmission.java");var registry=new PublicBindings();
        var original=original(List.of("ck3_take_snapshot"),McpCoverage.Admission.ADMITTED);
        var result=RootPublicMcpAdmission.derive(original,handlers(registry,List.of()),Set.of(),Set.of(producer),producer);
        assertEquals(McpCoverage.Admission.UNMIGRATED,result.getFirst().admission());
        registry.freeze(Set.of());
        var partial=assertInstanceOf(McpExecutableDirectory.Partial.class,McpExecutableDirectory.assemble(original.catalog(),result,original.tools(),original.resources(),registry,List.of()));
        assertTrue(partial.missing().stream().anyMatch(row->row.identity().equals("ck3_take_snapshot")&&row.reason()==McpExecutableDirectory.MissingReason.ORIGINAL_UNMIGRATED));
    }
    @Test void typedDirectBindingsNeedSelectedSourcesAndCannotConflictWithAnActualService() {
        var source=ref("actual.java");var producer=ref("RootPublicMcpAdmission.java");var registry=new PublicBindings();
        var original=original(List.of("ck3_take_snapshot"),McpCoverage.Admission.UNMIGRATED);
        var direct=new McpExecutableDirectory.DirectBinding<>("ck3_take_snapshot",PublicMcpBindings.Kind.DRIVER_DIRECT,String.class,RawJson.class,
            input->raw("{}"),call->"fixture",PublicMcpDirectory.CallResult::fromBusinessJson,new PublicRoutes.Target("fixture","snapshot",source));
        assertThrows(IllegalArgumentException.class,()->RootPublicMcpAdmission.derive(original,handlers(registry,List.of(direct)),Set.of(),Set.of(producer),producer));
        install(registry,PublicMethod.SNAPSHOT,source,new AtomicInteger());
        assertThrows(IllegalArgumentException.class,()->RootPublicMcpAdmission.derive(original,handlers(registry,List.of(direct)),Set.of(),Set.of(source,producer),producer));
    }
    @Test void bootstrapKeepsRegisteredOrdinaryCallsUnmigratedAndOnlyExcludesTheActualAbsentFixtureBranches() {
        var refs=new ArrayList<SourceInput>();for(var role:SourceRole.values())refs.add(new SourceInput(role,ref(role==SourceRole.ORIGINAL_MCP_SERVER?"mcp_server.py":role.name()+".json")));
        var now=Instant.parse("2026-10-26T00:00:00Z");
        var configuration=new Configuration("software-admission-fixture",now,now.plusSeconds(3600),Intent.FRESH_ROBERT_1066_ALL_ORDINARY,
            ref("RootSelectedRegistrationConfiguration.java"),refs,new ConstructorKeywords(3,false,false,true,
                new SuccessionLifecycleBinding(SuccessionLifecycleBinding.Profile.ORDINARY_FROZEN_OFF,"prepared-environment-manifest","1".repeat(64))));
        var ordinary=declaration("ck3_take_snapshot");
        var robert=new McpCoverage.Declaration("ck3_submit_frontend_fixture_robert_start_v1",ref("mcp_server.py"),3,4,"fixture",List.of("fixture_binding is not None"));
        var scenario=new McpCoverage.Declaration("ck3_submit_frontend_fixture_scenario_start_v1",ref("mcp_server.py"),5,6,"fixture",List.of("isinstance(fixture_binding, dict) and fixture_binding.get(\"profile_id\") is not None"));
        var configurationRef=ref("selected-configuration.json");
        var encoded=RootPublicMcpAdmission.bootstrapDocument(new McpCoverage.Catalog(List.of(ordinary,robert,scenario)),Set.of(ordinary.name()),configuration,configurationRef,ref("RootPublicMcpAdmission.java"));
        var decisions=RootPublicCatalogCodec.decodeAdmission(encoded);
        assertEquals(McpCoverage.Admission.UNMIGRATED,decisions.getFirst().admission());
        assertTrue(decisions.subList(1,3).stream().allMatch(row->row.admission()==McpCoverage.Admission.EXCLUDED_BY_CURRENT_CONFIGURATION&&row.actualAdmissionProducer().equals(configurationRef)));
        assertEquals(decisions,RootPublicCatalogCodec.decodeAdmission(RootPublicCatalogCodec.encodeAdmission(decisions)));
        String malformed=new String(encoded.bytes(),StandardCharsets.UTF_8).replace("\"name\":\"ck3_take_snapshot\"","\"name\":false");
        assertThrows(IllegalArgumentException.class,()->RootPublicCatalogCodec.decodeAdmission(raw(malformed)));
    }
}
