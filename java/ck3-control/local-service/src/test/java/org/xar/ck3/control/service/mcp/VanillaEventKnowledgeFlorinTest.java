package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.catalog.VanillaEventCatalog;
import org.xar.ck3.control.wave2.events.unhandledevent.SourceCompatibilityReview;

final class VanillaEventKnowledgeFlorinTest {
    @Test void allCurrentSourceRowsUseActualPublicDecoderHandlerAndEncoderWithoutExecutableContract() throws Exception {
        var catalog = VanillaEventCatalog.load(); var service = service(catalog);
        var binding = service.actualMethods(new ExactRef("fixture/source", 1, "a".repeat(64))).getFirst();
        var expectedFields = Set.of("schema", "schema_version", "status", "event_definition_key", "ck3_build",
                "ck3_exe_sha256", "contract", "analysis", "observations", "unavailable_reason");
        for (String key : SourceCompatibilityReview.load().events().keySet()) {
            var input = StrictJson.object().put("event_definition_key", key).put("ck3_build", "1.21.0");
            var call = new ToolCall(VanillaEventKnowledgeMethods.NAME, new Arguments(Presence.VALUE,
                    Optional.of(new RawJson(McpJson.encode(input)))), Optional.empty(), new McpCancellation());
            var result = McpJson.parse(invoke(binding, call).bytes()).get("structuredContent");
            var fields = new java.util.HashSet<String>(); result.fieldNames().forEachRemaining(fields::add);
            assertEquals(expectedFields, fields); assertEquals(key, result.get("event_definition_key").textValue());
            assertEquals("unavailable", result.get("status").textValue()); assertTrue(result.get("contract").isNull());
            assertTrue(result.get("observations").isNull()); assertEquals(SourceCompatibilityReview.EXE, result.get("ck3_exe_sha256").textValue());
            assertEquals("source_only", result.path("analysis").path("status").textValue());
            assertEquals("unqualified", result.path("analysis").path("native_binding_status").textValue());
            assertFalse(result.path("analysis").path("material_effects_verified").booleanValue());
        }
        assertFalse(catalog.supportedBuilds().contains("1.21.0"), "legacy Native-compatible catalog is deliberately unchanged");
    }

    @Test void originalDefaultAndUnknownCurrentKeysRemainExplicitAndUnavailable() throws Exception {
        var catalog = VanillaEventCatalog.load(); var service = service(catalog);
        var input = StrictJson.object().put("event_definition_key", "health.1015");
        assertEquals(catalog.currentBuild(), service.decode(new Arguments(Presence.VALUE,
                Optional.of(new RawJson(McpJson.encode(input))))).ck3Build());
        for (String key : new String[]{"", " ", "missing.99999", " health.1015 "}) {
            var result = McpJson.parse(service.query(new VanillaEventKnowledgeMethods.Request(key, "1.21.0")).original().bytes());
            assertEquals("unavailable", result.get("status").textValue()); assertTrue(result.get("analysis").isNull());
            assertTrue(result.get("contract").isNull()); assertEquals(key, result.get("event_definition_key").textValue());
        }
    }

    private static VanillaEventKnowledgeMethods service(VanillaEventCatalog catalog) {
        var row = StrictJson.object().put("name", VanillaEventKnowledgeMethods.NAME);
        var schema = row.putObject("inputSchema").put("type", "object");
        schema.putArray("required").add("event_definition_key");
        var properties = schema.putObject("properties");
        properties.putObject("event_definition_key").put("type", "string");
        properties.putObject("ck3_build").put("type", "string").put("default", catalog.currentBuild());
        return new VanillaEventKnowledgeMethods(catalog, new ToolDescriptor(VanillaEventKnowledgeMethods.NAME, new RawJson(McpJson.encode(row))));
    }
    private static <Q,R> CallResult invoke(McpExecutableDirectory.DirectBinding<Q,R> binding, ToolCall call) throws Exception {
        Q request = binding.decoder().decode(call); return binding.encoder().encode(binding.actual().invoke(request));
    }
}
