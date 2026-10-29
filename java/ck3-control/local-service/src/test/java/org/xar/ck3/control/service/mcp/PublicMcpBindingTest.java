package org.xar.ck3.control.service.mcp;

import com.fasterxml.jackson.databind.JsonNode;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.build.runtime.HostMode;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

final class PublicMcpBindingTest {
    record Query(String declarationId) { }
    static PublicMcpBindings oneAdmitted(String selected) throws Exception {
        var catalog = PublicMcpProtocolTest.catalog(); List<McpCoverage.Decision> decisions = new ArrayList<>();
        for (var declaration : catalog.declarations()) decisions.add(new McpCoverage.Decision(declaration.name(),
                selected.equals(declaration.name()) ? McpCoverage.Admission.ADMITTED : McpCoverage.Admission.UNMIGRATED,
                declaration.source(), "explicit software-only scope"));
        return new PublicMcpBindings(catalog, decisions);
    }
    static ToolDescriptor descriptor(String name) throws Exception {
        for (JsonNode row : PublicMcpProtocolTest.oracle().get("descriptors"))
            if (name.equals(row.path("name").textValue())) return new ToolDescriptor(name, new RawJson(McpJson.encode(row)));
        throw new IllegalArgumentException("missing original producer descriptor");
    }
    static ToolCall call(String name, String body) {
        return new ToolCall(name, new Arguments(Presence.VALUE, Optional.of(new RawJson(McpJson.utf8(body)))), Optional.empty(), new McpCancellation());
    }

    @Test void completeSourceInventoryIncludesManualAndImportedRegistrations() throws Exception {
        var catalog = PublicMcpProtocolTest.catalog();
        assertEquals(320, catalog.declarations().size());
        Set<String> names = catalog.declarations().stream().map(McpCoverage.Declaration::name).collect(java.util.stream.Collectors.toSet());
        assertTrue(names.containsAll(Set.of("ck3_query_army_strengths", "ck3_query_army_observer_research_sampling_v1",
                "ck3_set_army_observer_research_sampling_v1", "ck3_compare_army_private_auto_scalar_ab_v1")));
        for (JsonNode name : PublicMcpProtocolTest.oracle().get("baseline_tool_names")) assertTrue(names.contains(name.textValue()));
        assertEquals(194, PublicMcpProtocolTest.oracle().path("counts").path("baseline_installed_tools").intValue());
    }

    @Test void missingDecisionMissingImplementationAndSoftwareScopeCannotGrantRootInstallation() throws Exception {
        assertThrows(IllegalArgumentException.class, () -> new PublicMcpBindings(PublicMcpProtocolTest.catalog(), List.of()));
        PublicMcpBindings missing = oneAdmitted("ck3_get_capabilities");
        assertThrows(IllegalArgumentException.class, missing::freezeSoftwareScope);
        PublicMcpBindings software = PublicMcpProtocolTest.bindings(request -> new PublicMcpProtocolTest.Response(new RawJson(McpJson.utf8("{}"))));
        assertThrows(IllegalArgumentException.class, software::freeze);
        PublicMcpDirectory partial = software.freezeSoftwareScope();
        assertEquals(2, partial.tools().size()); assertEquals(2, partial.resources().size());
        PublicMcpHost host = new PublicMcpHost();
        assertThrows(IllegalArgumentException.class, () -> host.install(HostMode.MCP_STDIO, partial));
        assertTrue(host.current().isEmpty()); assertTrue(host.mode().isEmpty());
    }

    @Test void originalSchemaRejectsMissingWrongFieldBooleanFloatAndNumericBoundsBeforeMethod() throws Exception {
        String name = "ck3_query_prewar_force_coalition_coverage_v2"; PublicMcpBindings bindings = oneAdmitted(name);
        AtomicInteger invocations = new AtomicInteger();
        bindings.registerDirect(descriptor(name), PublicMcpBindings.Kind.APPLICATION_COMPOSITE, Query.class, RawJson.class,
                query -> { invocations.incrementAndGet(); return new RawJson(McpJson.utf8("{}")); },
                value -> new Query(McpJson.parse(value.arguments().original().orElseThrow().bytes()).get("declaration_id").textValue()),
                CallResult::fromBusinessJson, PublicMcpProtocolTest.target());
        var directory = bindings.freezeSoftwareScope();
        for (String arguments : List.of("{}", "{\"declarationId\":\"test\",\"expected_revision\":9}", "{\"declaration_id\":\"\",\"expected_revision\":1}",
                "{\"declaration_id\":\"test\",\"expected_revision\":true}", "{\"declaration_id\":\"test\",\"expected_revision\":1.0}",
                "{\"declaration_id\":\"test\",\"expected_revision\":0}", "{\"declaration_id\":\"test\",\"expected_revision\":18446744073709551616}"))
            assertThrows(ToolFailure.class, () -> directory.invoke(call(name, arguments)));
        assertEquals(0, invocations.get());
        directory.invoke(call(name, "{\"declaration_id\":\"test\",\"expected_revision\":9}")); assertEquals(1, invocations.get());
    }

    @Test void outputSchemaAndUnknownSchemaVocabularyDoNotSilentlyPass() throws Exception {
        var source = McpJson.object(McpJson.parse(descriptor("ck3_get_capabilities").original().bytes()));
        source.set("outputSchema", McpJson.parse(McpJson.utf8("{\"type\":\"object\",\"properties\":{\"status\":{\"type\":\"string\"}},\"required\":[\"status\"],\"additionalProperties\":false}")));
        ToolDescriptor strict = new ToolDescriptor("ck3_get_capabilities", new RawJson(McpJson.encode(source)));
        assertThrows(IllegalArgumentException.class, () -> strict.validateResult(CallResult.fromBusinessJson(new RawJson(McpJson.utf8("{}")))));
        strict.validateResult(CallResult.fromBusinessJson(new RawJson(McpJson.utf8("{\"status\":\"observed\"}"))));
        source.set("inputSchema", McpJson.parse(McpJson.utf8("{\"type\":\"object\",\"unevaluatedProperties\":false}")));
        assertThrows(IllegalArgumentException.class, () -> new ToolDescriptor("ck3_get_capabilities", new RawJson(McpJson.encode(source))));
        assertThrows(IllegalArgumentException.class, () -> new CallResult(McpJson.utf8("{\"content\":[{\"type\":\"image\"}]}")));
    }

    @Test void missingNullAndValueKeepTheSharedNativeBindingBranches() {
        assertInstanceOf(PublicBindings.Missing.class, PublicMcpNativeAdapter.arguments(new Arguments(Presence.MISSING, Optional.empty())));
        assertInstanceOf(PublicBindings.Null.class, PublicMcpNativeAdapter.arguments(new Arguments(Presence.NULL, Optional.of(new RawJson(McpJson.utf8("null"))))));
        RawJson value = new RawJson(McpJson.utf8("{\"FileID\":\"18446744073709551615\"}"));
        var actual = assertInstanceOf(PublicBindings.Value.class, PublicMcpNativeAdapter.arguments(new Arguments(Presence.VALUE, Optional.of(value))));
        assertEquals(value, actual.original());
    }

    @Test void rootMainRequiresTheExactInstalledModeAndRejectsApplicationArguments() {
        RootApplicationMain root = new RootApplicationMain(); root.host = new PublicMcpHost(); root.mode = HostMode.MCP_STDIO;
        assertEquals(64, root.run("untrusted-authority")); assertEquals(78, root.run());
    }

    @Test void unresolvedShutdownKeepsActualPendingOutcomeUntilCollected() throws Exception {
        CountDownLatch entered = new CountDownLatch(1), release = new CountDownLatch(1);
        var bindings = PublicMcpProtocolTest.bindings(request -> {
            entered.countDown(); assertTrue(release.await(3, TimeUnit.SECONDS)); return new PublicMcpProtocolTest.Response(new RawJson(McpJson.utf8("{}")));
        });
        var peer = new PublicMcpProtocolTest.Peer(bindings.freezeSoftwareScope());
        try {
            peer.initialize("2025-11-25");
            peer.send(PublicMcpProtocolTest.request("2025-11-25", "1", "tools/call", "\"name\":\"ck3_get_capabilities\""));
            assertTrue(entered.await(3, TimeUnit.SECONDS));
            var pending = peer.session.closeAndDrain(Duration.ZERO); assertFalse(pending.complete()); assertEquals(1, pending.unresolvedCalls());
            release.countDown(); assertFalse(peer.receive().path("result").path("isError").booleanValue());
        } finally { release.countDown(); peer.close(); }
    }
}
