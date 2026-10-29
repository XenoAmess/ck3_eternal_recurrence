package org.xar.ck3.control.service.root;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.planning.finance.publicgift.FactionGiftPublicContract;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.service.mcp.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.finance.publicgift.FactionGiftPublicContract.*;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** Actual original descriptors and shared directory with software invocation port; no fake Root/native credit. */
final class RootDriverFactionPublicSupplierTest {
    private static final ExactRef SOURCE = new ExactRef("software/faction-public-source", 1, "1".repeat(64));
    private static RawJson raw(String value) { return new RawJson(value.getBytes(StandardCharsets.UTF_8)); }
    private static Arguments args(String value) { return new Arguments(Presence.VALUE, Optional.of(raw(value))); }
    private static ToolCall call(String name, String json) {
        return new ToolCall(name, args(json), Optional.empty(), new McpCancellation());
    }
    @Test void fiveOriginalDescriptorsBindFiveDistinctTypedSelectorsWithoutCallingFinanceAtInstall() throws Exception {
        AtomicInteger calls = new AtomicInteger();
        var bindings = RootDriverFactionPublicSupplier.bindings(SOURCE, request -> {
            calls.incrementAndGet(); throw new AssertionError("registration must not call a current Finance product");
        });
        PublicMcpDirectory directory = directory(bindings);
        Set<String> expected = java.util.Arrays.stream(Method.values()).map(Method::originalName)
                .collect(java.util.stream.Collectors.toSet());
        assertEquals(expected, directory.tools().stream().map(ToolDescriptor::name).collect(java.util.stream.Collectors.toSet()));
        assertEquals(0, calls.get());
        assertInstanceOf(CandidateQuery.class, RootDriverFactionPublicSupplier.decode(Method.CANDIDATE,
                args("{\"expected_revision\":56,\"same_frame_root\":{}}")));
        assertInstanceOf(Send.class, RootDriverFactionPublicSupplier.decode(Method.SEND,
                args("{\"expected_revision\":56,\"candidate\":{},\"checkpoint\":{}}")));
        assertInstanceOf(ReceiptQuery.class, RootDriverFactionPublicSupplier.decode(Method.RECEIPT,
                args("{\"expected_revision\":56,\"pending\":{}}")));
        assertInstanceOf(ColdRecoveryQuery.class, RootDriverFactionPublicSupplier.decode(Method.COLD_RECOVERY,
                args("{\"expected_revision\":56,\"pending\":{}}")));
        assertInstanceOf(ResolvedQuery.class, RootDriverFactionPublicSupplier.decode(Method.RESOLVED,
                args("{\"expected_revision\":56,\"request_id\":\"original-gift\"}")));
        assertEquals(0, calls.get());
    }
    @Test void originalPrivateRouteOffBranchPassesThroughTheActualDescriptorDecoderProducerAndCompleteEncoder() throws Exception {
        var observed = new ArrayList<Request>();
        var directory = directory(RootDriverFactionPublicSupplier.bindings(SOURCE, request -> {
            observed.add(request); assertInstanceOf(CandidateQuery.class, request);
            // Exact original faction_gift_private_transport_v1.py private-route-off business projection.
            return raw("{\"status\":\"private_route_off\",\"public_capability_advertised\":false,\"gift_submission_enabled\":false}");
        }));
        var result = StrictJson.parse(directory.invoke(call(Method.CANDIDATE.originalName(),
                "{\"expected_revision\":56,\"same_frame_root\":{}}")).bytes(), 1_048_576);
        assertEquals(1, observed.size());
        var request = assertInstanceOf(CandidateQuery.class, observed.getFirst());
        assertEquals(DEFAULT_RESERVE, request.minimumGoldReserveRaw());
        assertFalse(result.get("isError").booleanValue());
        assertEquals("complete", result.get("resultType").textValue());
        var business = result.get("structuredContent");
        assertEquals("private_route_off", business.get("status").textValue());
        assertFalse(business.get("gift_submission_enabled").booleanValue());
        assertFalse(business.get("public_capability_advertised").booleanValue());
        assertEquals(business, StrictJson.parse(result.get("content").get(0).get("text").textValue()
                .getBytes(StandardCharsets.UTF_8), 1_048_576));
    }
    @Test void invalidPublicArgumentsStopBeforeTheActualFinanceInvocationAndDoNotBecomeEmptyObjects() throws Exception {
        AtomicInteger calls = new AtomicInteger();
        var directory = directory(RootDriverFactionPublicSupplier.bindings(SOURCE, request -> {
            calls.incrementAndGet(); throw new AssertionError("invalid arguments reached Finance");
        }));
        for (String json : List.of("{\"expected_revision\":true,\"same_frame_root\":{}}",
                "{\"expected_revision\":56.0,\"same_frame_root\":{}}",
                "{\"expected_revision\":56,\"same_frame_root\":null}",
                "{\"expected_revision\":56,\"same_frame_root\":{},\"minimum_gold_reserve_raw\":null}",
                "{\"expected_revision\":56,\"same_frame_root\":{},\"force_send\":true}"))
            assertThrows(ToolFailure.class, () -> directory.invoke(call(Method.CANDIDATE.originalName(), json)));
        assertThrows(IllegalArgumentException.class, () -> RootDriverFactionPublicSupplier.decode(Method.RECEIPT,
                new Arguments(Presence.MISSING, Optional.empty())));
        assertThrows(IllegalArgumentException.class, () -> RootDriverFactionPublicSupplier.decode(Method.RECEIPT,
                new Arguments(Presence.NULL, Optional.of(raw("null")))));
        assertEquals(0, calls.get());
    }
    private static PublicMcpDirectory directory(List<McpExecutableDirectory.DirectBinding<?, ?>> bindings) throws Exception {
        Set<String> names = java.util.Arrays.stream(Method.values()).map(Method::originalName)
                .collect(java.util.stream.Collectors.toSet());
        McpCoverage.Catalog original = McpCoverage.readCatalog(resource("/mcp/original-tool-catalog.json"));
        var declarations = original.declarations().stream().filter(row -> names.contains(row.name())).toList();
        assertEquals(5, declarations.size(), "all five exact original declarations required");
        var catalog = new McpCoverage.Catalog(declarations);
        var decisions = declarations.stream().map(row -> new McpCoverage.Decision(row.name(), McpCoverage.Admission.ADMITTED,
                SOURCE, "software exact original Gift5 descriptor and invocation boundary only")).toList();
        var tools = RootOriginalPublicTestInputs.tools().stream().filter(row -> names.contains(row.name())).toList();
        assertEquals(5, tools.size(), "mandatory actual original MCP SDK descriptors missing");
        var registry = new PublicBindings(); registry.freeze(Set.of());
        var partial = assertInstanceOf(McpExecutableDirectory.Partial.class,
                McpExecutableDirectory.assemble(catalog, decisions, tools, List.of(), registry, bindings));
        return partial.softwareDirectory();
    }
    private static RawJson resource(String path) throws Exception {
        try (InputStream input = RootDriverFactionPublicSupplierTest.class.getResourceAsStream(path)) {
            assertNotNull(input, "mandatory original catalog missing: " + path);
            return new RawJson(input.readAllBytes());
        }
    }
}
